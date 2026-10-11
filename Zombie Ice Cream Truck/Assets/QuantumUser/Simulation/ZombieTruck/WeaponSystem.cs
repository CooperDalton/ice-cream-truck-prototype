namespace Quantum
{
    using System;
    using Photon.Deterministic;

    public unsafe class WeaponSystem : SystemMainThreadFilter<WeaponSystem.Filter>
    {
        public struct Filter
        {
            public EntityRef Entity;
            public Transform3D* Transform;
            public Survivor* Survivor;
            public PlayerLink* Link;
        }

        public override void Update(Frame f, ref Filter filter)
        {
            var survivor = filter.Survivor;
            survivor->FireCooldown -= f.DeltaTime;
            var input = f.GetPlayerInput(filter.Link->Player);
            if (survivor->Dead || survivor->Driving || !input->Fire.IsDown || survivor->FireCooldown > 0) return;
            var settings = f.FindAsset(f.RuntimeConfig.Settings);
            var player = filter.Link->Player;
            var aim = filter.Transform->Rotation * FPQuaternion.Euler(survivor->Pitch, 0, 0);

            if (survivor->TurretSeat > 0)
            {
                var truck = f.Unsafe.GetPointerSingleton<Truck>();
                if (truck->HopperRounds <= 0) return;
                truck->HopperRounds--;
                survivor->FireCooldown = FP._0_05 + FP._0_02;
                ZombieSystem.Alert(f, filter.Transform->Position, settings.GunshotNoise);
                var truckTransform = f.Get<Transform3D>(f.GetSingletonEntityRef<Truck>());
                var muzzle = truckTransform.TransformPoint(settings.TurretMuzzles[survivor->TurretSeat - 1]);
                Shoot(f, player, ItemKind.None, truck->HopperFlavor, muzzle, Spread(f, aim, FP._1_50), 80, 1, false, true);
                return;
            }

            // A click aimed at a truck station within reach works the station instead of firing.
            var target = survivor->LookTarget;
            if (target.IsValid && f.Has<Station>(target) && f.Has<Attached>(target)) return;

            var gun = survivor->Hotbar.GetPointer(survivor->Selected);
            var spec = Inventory.Gun(gun->Kind);
            var eye = filter.Transform->Position + FPVector3.Up * (survivor->Crouching ? settings.CrouchEyeHeight : settings.EyeHeight);
            if (spec.Melee)
            {
                survivor->FireCooldown = spec.Interval;
                Swing(f, player, gun, spec, eye, aim * FPVector3.Forward);
                return;
            }
            if (spec.Pellets > 0 && !spec.Harpoon && gun->Count <= 0 && input->Fire.WasPressed) f.Events.GunEmpty(player);
            if (spec.Pellets == 0 || (!spec.Harpoon && gun->Count <= 0)) return;
            survivor->FireCooldown = spec.Interval;
            if (!spec.Harpoon) gun->Count--;
            ZombieSystem.Alert(f, eye, settings.GunshotNoise);

            if (spec.Launcher || spec.Rocket)
            {
                var projectile = f.Create(settings.ProjectilePrototype);
                var forward = aim * FPVector3.Forward;
                f.Unsafe.GetPointer<Transform3D>(projectile)->Teleport(f, eye + forward * FP._0_75);
                f.Add(projectile, spec.Rocket
                    ? new Projectile { Flavor = gun->Flavor, Velocity = forward * 40, Owner = player, Radius = settings.BazookaRadius, Damage = spec.Damage, Rocket = true }
                    : new Projectile { Flavor = gun->Flavor, Velocity = forward * 26 + FPVector3.Up * 2, Owner = player, Radius = settings.GrenadeRadius, Damage = 3 });
                f.Events.ShotFired(player, gun->Kind, gun->Flavor, eye, eye + forward * 3);
                return;
            }
            if (spec.Harpoon)
            {
                Harpoon(f, player, filter.Transform->Position, eye, aim * FPVector3.Forward, spec);
                return;
            }
            if (spec.Jackpot)
            {
                Jackpot(f, player, gun->Flavor, eye, aim, settings);
                return;
            }
            for (int i = 0; i < spec.Pellets; i++)
            {
                Shoot(f, player, gun->Kind, gun->Flavor, eye, Spread(f, aim, spec.Spread), spec.Range, spec.Damage, spec.Pierce, !spec.Hose);
            }
        }

        // A cone swing hits the nearest zombies in front, up to the cone's cleave (coffee hits everything in reach). Each
        // swing that connects eats one bite of the scoop; an empty cone still bonks for 1.
        static void Swing(Frame f, PlayerRef player, Item* cone, GunSpec spec, FPVector3 eye, FPVector3 forward)
        {
            var fresh = cone->Count > 0;
            var flavor = fresh ? cone->Flavor : Flavor.None;
            var damage = fresh ? spec.Damage : 1;
            var cleave = flavor == Flavor.Coffee ? 8 : spec.Cleave;
            var struck = stackalloc EntityRef[8];
            var hits = 0;
            while (hits < cleave)
            {
                var best = EntityRef.None;
                var bestDistance = (spec.Range + FP._0_50) * (spec.Range + FP._0_50);
                foreach (var pair in f.Unsafe.GetComponentBlockIterator<Zombie>())
                {
                    if (pair.Component->State == ZombieState.Dead) continue;
                    var already = false;
                    for (int i = 0; i < hits; i++) already |= struck[i] == pair.Entity;
                    if (already) continue;
                    var offset = f.Unsafe.GetPointer<Transform3D>(pair.Entity)->Position + FPVector3.Up - eye;
                    var distance = offset.SqrMagnitude;
                    if (distance >= bestDistance || FPVector3.Dot(offset.Normalized, forward) < FP._0_50) continue;
                    bestDistance = distance;
                    best = pair.Entity;
                }
                if (!best.IsValid) break;
                struck[hits++] = best;
                var point = f.Unsafe.GetPointer<Transform3D>(best)->Position + FPVector3.Up;
                Combat.DamageZombie(f, best, f.Unsafe.GetPointer<Zombie>(best), damage, false, flavor, point, forward * 6 + FPVector3.Up * 2, player);
            }
            if (hits > 0 && fresh) cone->Count--;
            f.Events.MeleeSwung(player, cone->Kind, flavor, hits > 0);
        }

        // Every Jackpot Blaster shot spins: mostly a weak single shot, sometimes a shotgun spread, and now and then a
        // jackpot that blows up wherever it lands.
        static void Jackpot(Frame f, PlayerRef player, Flavor flavor, FPVector3 eye, FPQuaternion aim, ZombieTruckSettings settings)
        {
            var roll = f.RNG->Next();
            var tier = roll < settings.JackpotChance ? 2 : roll < settings.JackpotChance + settings.JackpotSpreadChance ? 1 : 0;
            var forward = aim * FPVector3.Forward;
            if (tier == 2)
            {
                var hit = f.Physics3D.Raycast(eye, forward, 60, -1, QueryOptions.HitAll);
                var point = hit.HasValue ? hit.Value.Point : eye + forward * 60;
                f.Events.ShotFired(player, ItemKind.JackpotBlaster, flavor, eye, point);
                Combat.Explode(f, point, settings.JackpotRadius, 8, flavor, false, player);
                f.Events.JackpotShot(player, tier, point);
                return;
            }
            var pellets = tier == 1 ? 6 : 1;
            for (int i = 0; i < pellets; i++)
            {
                Shoot(f, player, ItemKind.JackpotBlaster, flavor, eye, Spread(f, aim, tier == 1 ? 6 : 2), 50, tier == 1 ? 2 : 1, false, true);
            }
            f.Events.JackpotShot(player, tier, eye + forward * 2);
        }

        static FPVector3 Spread(Frame f, FPQuaternion aim, FP degrees)
        {
            var yaw = f.RNG->Next(-degrees, degrees);
            var pitch = f.RNG->Next(-degrees, degrees);
            return aim * FPQuaternion.Euler(pitch, yaw, 0) * FPVector3.Forward;
        }

        // Coffee shots pierce like the long spoon.
        static void Shoot(Frame f, PlayerRef player, ItemKind gun, Flavor flavor, FPVector3 origin, FPVector3 direction, FP range, Int32 damage, bool pierce, bool headshots)
        {
            var settings = f.FindAsset(f.RuntimeConfig.Settings);
            var end = origin + direction * range;
            if (pierce || flavor == Flavor.Coffee)
            {
                var hits = f.Physics3D.RaycastAll(origin, direction, range, -1, QueryOptions.HitAll);
                for (int i = 0; i < hits.Count; i++)
                {
                    HitEntity(f, hits[i].Entity, hits[i].Point, direction, damage, flavor, settings, player, headshots);
                }
                f.Events.ShotFired(player, gun, flavor, origin, end);
                return;
            }
            var hit = f.Physics3D.Raycast(origin, direction, range, -1, QueryOptions.HitAll);
            f.Events.ShotFired(player, gun, flavor, origin, hit.HasValue ? hit.Value.Point : end);
            if (hit.HasValue)
            {
                HitEntity(f, hit.Value.Entity, hit.Value.Point, direction, damage, flavor, settings, player, headshots);
            }
        }

        static void HitEntity(Frame f, EntityRef entity, FPVector3 point, FPVector3 direction, Int32 damage, Flavor flavor, ZombieTruckSettings settings, PlayerRef player, bool headshots)
        {
            if (!entity.IsValid || !f.Unsafe.TryGetPointer(entity, out Zombie* zombie)) return;
            var stats = settings.Zombies[(int)zombie->Kind];
            var headshot = headshots && point.Y - f.Unsafe.GetPointer<Transform3D>(entity)->Position.Y > stats.HeadHeight;
            Combat.DamageZombie(f, entity, zombie, damage, headshot, flavor, point, direction * 5, player);
        }

        // The harpoon yanks whatever it spears toward the shooter: supply crates, guns, or a zombie.
        static void Harpoon(Frame f, PlayerRef player, FPVector3 position, FPVector3 eye, FPVector3 direction, GunSpec spec)
        {
            var hit = f.Physics3D.Raycast(eye, direction, spec.Range, -1, QueryOptions.HitAll);
            f.Events.ShotFired(player, ItemKind.BananaHarpoon, Flavor.None, eye, hit.HasValue ? hit.Value.Point : eye + direction * spec.Range);
            if (!hit.HasValue) return;
            var entity = hit.Value.Entity;
            var pull = (position - hit.Value.Point);
            var velocity = pull.Normalized * FPMath.Min(pull.Magnitude * 2, 25) + FPVector3.Up * 4;
            if (f.Unsafe.TryGetPointer(entity, out Pickup* pickup))
            {
                pickup->Velocity = velocity;
                pickup->Resting = false;
                f.Remove<Attached>(entity);
                return;
            }
            if (f.Unsafe.TryGetPointer(entity, out Zombie* zombie))
            {
                Combat.DamageZombie(f, entity, zombie, spec.Damage, false, Flavor.None, hit.Value.Point, velocity, player);
            }
        }
    }
}
