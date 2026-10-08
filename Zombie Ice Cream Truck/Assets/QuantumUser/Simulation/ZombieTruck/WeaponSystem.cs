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
            if (survivor->Dead || survivor->Driving || survivor->Carried.Kind != ItemKind.None || !input->Fire.IsDown || survivor->FireCooldown > 0) return;
            var settings = f.FindAsset(f.RuntimeConfig.Settings);
            var player = filter.Link->Player;
            var aim = filter.Transform->Rotation * FPQuaternion.Euler(survivor->Pitch, 0, 0);

            if (survivor->TurretSeat > 0)
            {
                var truck = f.Unsafe.GetPointerSingleton<Truck>();
                if (truck->HopperRounds <= 0) return;
                truck->HopperRounds--;
                survivor->FireCooldown = FP._0_05 + FP._0_02;
                var truckTransform = f.Get<Transform3D>(f.GetSingletonEntityRef<Truck>());
                var muzzle = truckTransform.TransformPoint(settings.TurretMuzzles[survivor->TurretSeat - 1]);
                Shoot(f, player, ItemKind.None, truck->HopperFlavor, muzzle, Spread(f, aim, FP._1_50), 80, 1, false);
                return;
            }

            var gun = survivor->Hotbar.GetPointer(survivor->Selected);
            var spec = Inventory.Gun(gun->Kind);
            if (spec.Pellets > 0 && !spec.Harpoon && gun->Count <= 0 && input->Fire.WasPressed) f.Events.GunEmpty(player);
            if (spec.Pellets == 0 || (!spec.Harpoon && gun->Count <= 0)) return;
            survivor->FireCooldown = spec.Interval;
            if (!spec.Harpoon) gun->Count--;
            var eye = filter.Transform->Position + FPVector3.Up * settings.EyeHeight;

            if (spec.Launcher)
            {
                var projectile = f.Create(settings.ProjectilePrototype);
                var forward = aim * FPVector3.Forward;
                f.Unsafe.GetPointer<Transform3D>(projectile)->Teleport(f, eye + forward * FP._0_75);
                f.Add(projectile, new Projectile { Flavor = gun->Flavor, Velocity = forward * 26 + FPVector3.Up * 2, Owner = player, Radius = settings.GrenadeRadius });
                f.Events.ShotFired(player, gun->Kind, gun->Flavor, eye, eye + forward * 3);
                return;
            }
            if (spec.Harpoon)
            {
                Harpoon(f, player, filter.Transform->Position, eye, aim * FPVector3.Forward, spec);
                return;
            }
            for (int i = 0; i < spec.Pellets; i++)
            {
                Shoot(f, player, gun->Kind, gun->Flavor, eye, Spread(f, aim, spec.Spread), spec.Range, spec.Damage, spec.Pierce);
            }
        }

        static FPVector3 Spread(Frame f, FPQuaternion aim, FP degrees)
        {
            var yaw = f.RNG->Next(-degrees, degrees);
            var pitch = f.RNG->Next(-degrees, degrees);
            return aim * FPQuaternion.Euler(pitch, yaw, 0) * FPVector3.Forward;
        }

        static void Shoot(Frame f, PlayerRef player, ItemKind gun, Flavor flavor, FPVector3 origin, FPVector3 direction, FP range, Int32 damage, bool pierce)
        {
            var settings = f.FindAsset(f.RuntimeConfig.Settings);
            var end = origin + direction * range;
            if (pierce)
            {
                var hits = f.Physics3D.RaycastAll(origin, direction, range, -1, QueryOptions.HitAll);
                for (int i = 0; i < hits.Count; i++)
                {
                    HitEntity(f, hits[i].Entity, hits[i].Point, direction, damage, flavor, settings, player);
                }
                f.Events.ShotFired(player, gun, flavor, origin, end);
                return;
            }
            var hit = f.Physics3D.Raycast(origin, direction, range, -1, QueryOptions.HitAll);
            f.Events.ShotFired(player, gun, flavor, origin, hit.HasValue ? hit.Value.Point : end);
            if (hit.HasValue)
            {
                HitEntity(f, hit.Value.Entity, hit.Value.Point, direction, damage, flavor, settings, player);
            }
        }

        static void HitEntity(Frame f, EntityRef entity, FPVector3 point, FPVector3 direction, Int32 damage, Flavor flavor, ZombieTruckSettings settings, PlayerRef player)
        {
            if (!entity.IsValid || !f.Unsafe.TryGetPointer(entity, out Zombie* zombie)) return;
            var stats = settings.Zombies[(int)zombie->Kind];
            var headshot = point.Y - f.Unsafe.GetPointer<Transform3D>(entity)->Position.Y > stats.HeadHeight;
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
