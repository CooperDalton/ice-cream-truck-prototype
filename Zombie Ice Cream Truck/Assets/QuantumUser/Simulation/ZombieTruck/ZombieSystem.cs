namespace Quantum
{
    using System;
    using Photon.Deterministic;

    public unsafe class ZombieSystem : SystemMainThread
    {
        public override void Update(Frame f)
        {
            var settings = f.FindAsset(f.RuntimeConfig.Settings);
            var truckEntity = f.GetSingletonEntityRef<Truck>();
            var truck = f.Unsafe.GetPointer<Truck>(truckEntity);
            var truckTransform = f.Get<Transform3D>(truckEntity);
            var halfSize = settings.TruckHalfSize;
            var dt = f.DeltaTime;
            int alive = 0;

            foreach (var pair in f.Unsafe.GetComponentBlockIterator<Zombie>())
            {
                var zombie = pair.Component;
                var transform = f.Unsafe.GetPointer<Transform3D>(pair.Entity);
                var stats = settings.Zombies[(int)zombie->Kind];
                if (zombie->State == ZombieState.Dead)
                {
                    zombie->Timer += dt;
                    zombie->Velocity += FPVector3.Down * 20 * dt;
                    transform->Position += zombie->Velocity * dt;
                    if (transform->Position.Y < 0)
                    {
                        transform->Position.Y = 0;
                        zombie->Velocity = new FPVector3(zombie->Velocity.X * FP._0_50, -zombie->Velocity.Y * FP._0_25, zombie->Velocity.Z * FP._0_50);
                    }
                    if (zombie->Timer > settings.CorpseTime) f.Destroy(pair.Entity);
                    continue;
                }
                alive++;

                if (zombie->State == ZombieState.Climbing)
                {
                    zombie->Timer -= dt;
                    if (zombie->Timer > 0) continue;
                    var attached = f.Unsafe.GetPointer<Attached>(pair.Entity);
                    zombie->State = ZombieState.OnTruck;
                    attached->LocalPosition = new FPVector3(FPMath.Clamp(attached->LocalPosition.X, -FP._0_75, FP._0_75), settings.RoofHeight,
                        FPMath.Clamp(attached->LocalPosition.Z, -halfSize.Z + 1, halfSize.Z - 1));
                    continue;
                }
                if (zombie->State == ZombieState.OnTruck)
                {
                    if (zombie->FrozenTimer > 0)
                    {
                        zombie->FrozenTimer -= dt;
                        continue;
                    }
                    var attached = f.Unsafe.GetPointer<Attached>(pair.Entity);
                    var goal = attached->LocalPosition;
                    var bestRoof = FP.MaxValue;
                    foreach (var survivor in f.Unsafe.GetComponentBlockIterator<Survivor>())
                    {
                        if (survivor.Component->Dead) continue;
                        var survivorLocal = truckTransform.InverseTransformPoint(f.Unsafe.GetPointer<Transform3D>(survivor.Entity)->Position);
                        if (survivorLocal.Y < settings.RoofHeight - 1) continue;
                        var distance = (survivorLocal - attached->LocalPosition).SqrMagnitude;
                        if (distance >= bestRoof) continue;
                        bestRoof = distance;
                        goal = survivorLocal;
                    }
                    var step = goal - attached->LocalPosition;
                    step.Y = 0;
                    if (step.SqrMagnitude > FP._0_50)
                    {
                        attached->LocalPosition += step.Normalized * stats.Speed * FP._0_50 * dt;
                        attached->LocalRotation = FPQuaternion.LookRotation(step.Normalized);
                    }
                    Attack(f, zombie, transform->Position, stats, dt);
                    continue;
                }

                var local = truckTransform.InverseTransformPoint(transform->Position);
                if (local.Z < 0 && local.SqrMagnitude > settings.DespawnBehind * settings.DespawnBehind)
                {
                    f.Destroy(pair.Entity);
                    continue;
                }
                var absSpeed = FPMath.Abs(truck->Speed);
                if (FPMath.Abs(local.X) < halfSize.X && FPMath.Abs(local.Z) < halfSize.Z)
                {
                    var impulse = truckTransform.Forward * truck->Speed * FP._1_25 + FPVector3.Up * absSpeed * FP._0_50
                        + truckTransform.Right * FPMath.Sign(local.X) * 3;
                    var runOverSpeed = settings.RunOverSpeed - truck->PlowLevel * FP._1_50;
                    if (zombie->FrozenTimer > 0 && absSpeed > 2)
                    {
                        Combat.Kill(f, pair.Entity, zombie, impulse, false, true, Flavor.Mint, truck->Driver);
                        continue;
                    }
                    if (zombie->Kind == ZombieKind.Bloater && absSpeed >= settings.RunOverSpeed)
                    {
                        truck->Speed *= 1 - settings.BloaterSlowdown;
                        Combat.Kill(f, pair.Entity, zombie, impulse, false, true, Flavor.None, truck->Driver);
                        continue;
                    }
                    if (zombie->Kind != ZombieKind.Bloater && absSpeed >= runOverSpeed)
                    {
                        Combat.Kill(f, pair.Entity, zombie, impulse, false, true, Flavor.None, truck->Driver);
                        truck->Speed -= FPMath.Sign(truck->Speed) * settings.RunOverSlowdown;
                        continue;
                    }
                    if (truck->Spikes && zombie->Kind != ZombieKind.Bloater && FPMath.Abs(local.X) > halfSize.X - FP._0_50)
                    {
                        Combat.Kill(f, pair.Entity, zombie, truckTransform.Right * FPMath.Sign(local.X) * 6 + FPVector3.Up * 3, false, true, Flavor.None, truck->Driver);
                        continue;
                    }
                    // Too slow to run it over: the zombie gets shoved aside and drags on the truck.
                    local.X = FPMath.Sign(local.X) * halfSize.X;
                    var shoved = truckTransform.TransformPoint(local);
                    transform->Position = new FPVector3(shoved.X, 0, shoved.Z);
                    truck->Speed -= truck->Speed * settings.CrowdSlowdown * (truck->Armor ? FP._0_50 : FP._1) * dt;
                }
                if (zombie->FrozenTimer > 0)
                {
                    zombie->FrozenTimer -= dt;
                    continue;
                }

                if (zombie->Kind == ZombieKind.Sprinter && !truck->Spikes && absSpeed < settings.ClimbMaxSpeed
                    && FPMath.Abs(local.Z) < halfSize.Z - FP._0_50 && FPMath.Abs(local.X) < halfSize.X + FP._0_75)
                {
                    zombie->State = ZombieState.Climbing;
                    zombie->Timer = FP._1_25;
                    var side = new FPVector3(FPMath.Sign(local.X) * halfSize.X, FP._0_50, local.Z);
                    f.Add(pair.Entity, new Attached { LocalPosition = side, LocalRotation = FPQuaternion.LookRotation(new FPVector3(-FPMath.Sign(local.X), 0, 0)) });
                    continue;
                }

                var target = truckTransform.Position;
                FP best = 900;
                foreach (var survivor in f.Unsafe.GetComponentBlockIterator<Survivor>())
                {
                    if (survivor.Component->Dead || survivor.Component->Standing == truckEntity) continue;
                    var survivorPosition = f.Unsafe.GetPointer<Transform3D>(survivor.Entity)->Position;
                    var distance = (survivorPosition - transform->Position).SqrMagnitude;
                    if (distance >= best) continue;
                    best = distance;
                    target = survivorPosition;
                }
                var toTarget = target - transform->Position;
                toTarget.Y = 0;
                if (toTarget.SqrMagnitude > FP._0_50)
                {
                    var direction = toTarget.Normalized;
                    transform->Position += direction * stats.Speed * dt;
                    transform->Rotation = FPQuaternion.LookRotation(direction);
                }
                Attack(f, zombie, transform->Position, stats, dt);
            }

            Spawn(f, settings, alive, truckTransform);
        }

        static void Attack(Frame f, Zombie* zombie, FPVector3 position, ZombieStats stats, FP dt)
        {
            zombie->AttackCooldown -= dt;
            if (zombie->AttackCooldown > 0) return;
            foreach (var survivor in f.Unsafe.GetComponentBlockIterator<Survivor>())
            {
                if (survivor.Component->Dead) continue;
                var offset = f.Unsafe.GetPointer<Transform3D>(survivor.Entity)->Position - position;
                if (FPMath.Abs(offset.Y) > FP._1_50 || offset.X * offset.X + offset.Z * offset.Z > FP._1_25 * FP._1_25) continue;
                Combat.Hurt(f, survivor.Entity, survivor.Component, stats.Damage);
                zombie->AttackCooldown = stats.AttackInterval;
                return;
            }
        }

        // Spawns on a random road chunk ahead of the truck; later areas spawn faster and mix in more sprinters and bloaters.
        static void Spawn(Frame f, ZombieTruckSettings settings, int alive, Transform3D truck)
        {
            var global = f.Global;
            global->SpawnTimer -= f.DeltaTime;
            if (global->Phase != GamePhase.Driving || global->SpawnTimer > 0 || alive >= settings.MaxZombies) return;
            global->SpawnTimer = FPMath.Max(FP._0_25, settings.SpawnInterval - (global->Area - 1) * settings.SpawnIntervalPerArea);
            var targetIndex = global->TruckChunk + f.RNG->Next(2, settings.ChunksAhead);
            var chunk = EntityRef.None;
            foreach (var pair in f.Unsafe.GetComponentBlockIterator<RoadChunk>())
            {
                if (pair.Component->Index == targetIndex && pair.Component->Kind != ChunkKind.Depot) chunk = pair.Entity;
            }
            if (!chunk.IsValid) return;
            var chunkTransform = f.Get<Transform3D>(chunk);
            var offset = new FPVector3(f.RNG->Next(-settings.SpawnHalfWidth, settings.SpawnHalfWidth), 0, f.RNG->Next(-8, 8));
            var position = chunkTransform.TransformPoint(offset);
            position.Y = 0;

            var bloater = settings.BloaterChance * global->Area;
            var sprinter = settings.SprinterChance + (global->Area - 1) * settings.ChancePerArea;
            var roll = f.RNG->Next();
            var kind = roll < bloater ? ZombieKind.Bloater : roll < bloater + sprinter ? ZombieKind.Sprinter : ZombieKind.Walker;
            var stats = settings.Zombies[(int)kind];
            var entity = f.Create(settings.ZombiePrototypes[(int)kind]);
            var facing = truck.Position - position;
            facing.Y = 0;
            f.Unsafe.GetPointer<Transform3D>(entity)->Teleport(f, position, FPQuaternion.LookRotation(facing.Normalized));
            f.Add(entity, new Zombie { Kind = kind, Health = stats.Health });
            var shape = Shape3D.CreateBox(stats.HalfSize, new FPVector3(0, stats.HalfSize.Y, 0));
            f.Add(entity, PhysicsCollider3D.Create(f, shape, null, true));
        }
    }
}
