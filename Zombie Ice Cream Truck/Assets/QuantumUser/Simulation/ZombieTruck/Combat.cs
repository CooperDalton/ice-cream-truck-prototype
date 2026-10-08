namespace Quantum
{
    using System;
    using Photon.Deterministic;

    // Damage, flavor effects, kills, explosions and survivor health.
    public static unsafe class Combat
    {
        // Flavor effects: chocolate tips money, mint freezes, strawberry splashes onto neighbours.
        public static void DamageZombie(Frame f, EntityRef entity, Zombie* zombie, Int32 damage, bool headshot, Flavor flavor,
            FPVector3 point, FPVector3 push, PlayerRef source)
        {
            if (zombie->State == ZombieState.Dead) return;
            var settings = f.FindAsset(f.RuntimeConfig.Settings);
            f.Events.ZombieHit(source, entity, point, headshot, flavor);
            if (flavor == Flavor.Chocolate)
            {
                f.Global->Money += settings.ChocolateTip;
                f.Events.TipEarned(point, settings.ChocolateTip);
            }
            if (flavor == Flavor.Mint)
            {
                zombie->FrozenTimer = settings.FreezeTime;
            }
            if (flavor == Flavor.Strawberry)
            {
                foreach (var other in f.Unsafe.GetComponentBlockIterator<Zombie>())
                {
                    if (other.Entity == entity || other.Component->State == ZombieState.Dead) continue;
                    var otherPosition = f.Unsafe.GetPointer<Transform3D>(other.Entity)->Position;
                    if ((otherPosition - point).SqrMagnitude > settings.SplashRadius * settings.SplashRadius) continue;
                    DamageZombie(f, other.Entity, other.Component, 1, false, Flavor.None, otherPosition + FPVector3.Up, push, source);
                }
            }
            zombie->Health -= headshot ? zombie->Health : damage;
            if (zombie->Health <= 0)
            {
                Kill(f, entity, zombie, push + FPVector3.Up * 3, headshot, false, flavor, source);
            }
        }

        public static void Kill(Frame f, EntityRef entity, Zombie* zombie, FPVector3 impulse, bool headshot, bool runOver, Flavor flavor, PlayerRef source)
        {
            var settings = f.FindAsset(f.RuntimeConfig.Settings);
            var position = f.Unsafe.GetPointer<Transform3D>(entity)->Position;
            zombie->State = ZombieState.Dead;
            zombie->Timer = 0;
            zombie->FrozenTimer = 0;
            zombie->Velocity = impulse;
            f.Remove<Attached>(entity);
            f.Remove<PhysicsCollider3D>(entity);
            var reward = settings.Zombies[(int)zombie->Kind].Reward + (flavor == Flavor.Chocolate ? settings.ChocolateTip * 2 : 0);
            f.Global->Money += reward;
            f.Global->Kills++;
            f.Events.ZombieKilled(source, entity, zombie->Kind, position, impulse, headshot, runOver, flavor, reward);
            if (zombie->Kind == ZombieKind.Bloater)
            {
                Explode(f, position + FPVector3.Up, settings.BloaterRadius, 5, Flavor.None, true, source);
            }
        }

        // Kills or damages zombies in range; bloater blasts also hurt survivors.
        public static void Explode(Frame f, FPVector3 position, FP radius, Int32 damage, Flavor flavor, bool bloater, PlayerRef source)
        {
            var settings = f.FindAsset(f.RuntimeConfig.Settings);
            f.Events.Explosion(position, radius, flavor, bloater);
            foreach (var pair in f.Unsafe.GetComponentBlockIterator<Zombie>())
            {
                if (pair.Component->State == ZombieState.Dead) continue;
                var zombiePosition = f.Unsafe.GetPointer<Transform3D>(pair.Entity)->Position;
                var offset = zombiePosition - position;
                if (offset.SqrMagnitude > radius * radius) continue;
                var push = offset.Normalized * 8;
                DamageZombie(f, pair.Entity, pair.Component, damage, false, flavor, zombiePosition + FPVector3.Up, push, source);
            }
            if (!bloater) return;
            foreach (var pair in f.Unsafe.GetComponentBlockIterator<Survivor>())
            {
                if (pair.Component->Dead) continue;
                var survivorPosition = f.Unsafe.GetPointer<Transform3D>(pair.Entity)->Position;
                var distance = (survivorPosition - position).Magnitude;
                if (distance > radius) continue;
                Hurt(f, pair.Entity, pair.Component, settings.BloaterPlayerDamage * (1 - distance / radius));
            }
        }

        public static void Hurt(Frame f, EntityRef entity, Survivor* survivor, FP amount)
        {
            if (survivor->Dead) return;
            var player = f.Get<PlayerLink>(entity).Player;
            survivor->Health -= amount;
            f.Events.SurvivorHurt(player, survivor->Health);
            if (survivor->Health > 0) return;
            survivor->Dead = true;
            survivor->Health = 0;
            survivor->TurretSeat = 0;
            var truck = f.Unsafe.GetPointerSingleton<Truck>();
            if (survivor->Driving) truck->Driver = PlayerRef.None;
            survivor->Driving = false;
            if (survivor->Carried.Kind != ItemKind.None)
            {
                var position = f.Unsafe.GetPointer<Transform3D>(entity)->Position;
                Inventory.SpawnPickup(f, survivor->Carried, position + FPVector3.Up, FPVector3.Up * 2, false);
                survivor->Carried = default;
            }
            f.Events.SurvivorDied(player);
        }

        public static void Revive(Frame f, EntityRef entity, Survivor* survivor, FPVector3 position)
        {
            var settings = f.FindAsset(f.RuntimeConfig.Settings);
            survivor->Dead = false;
            survivor->Health = settings.MaxHealth;
            f.Unsafe.GetPointer<Transform3D>(entity)->Teleport(f, position);
            f.Unsafe.GetPointer<CharacterController3D>(entity)->Velocity = FPVector3.Zero;
            f.Events.SurvivorRevived(f.Get<PlayerLink>(entity).Player);
        }
    }
}
