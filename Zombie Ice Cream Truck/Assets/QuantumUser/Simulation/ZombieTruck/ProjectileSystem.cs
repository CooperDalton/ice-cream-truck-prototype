namespace Quantum
{
    using System;
    using Photon.Deterministic;

    // Moves thrown and dropped items until they land (sticking to the truck if they land on it) and flies scoop grenades
    // until they hit something or pass close to a zombie.
    public unsafe class ProjectileSystem : SystemMainThread
    {
        public override void Update(Frame f)
        {
            var settings = f.FindAsset(f.RuntimeConfig.Settings);
            var dt = f.DeltaTime;
            var truckEntity = f.GetSingletonEntityRef<Truck>();
            var truck = f.Get<Transform3D>(truckEntity);

            foreach (var pair in f.Unsafe.GetComponentBlockIterator<Pickup>())
            {
                var pickup = pair.Component;
                var transform = f.Unsafe.GetPointer<Transform3D>(pair.Entity);
                if (pickup->Resting)
                {
                    var far = (transform->Position - truck.Position).SqrMagnitude > settings.DespawnBehind * settings.DespawnBehind * 4;
                    if (far && !f.Has<ChunkOwned>(pair.Entity)) f.Destroy(pair.Entity);
                    continue;
                }
                pickup->Velocity += FPVector3.Down * 20 * dt;
                var step = pickup->Velocity * dt;
                var hit = f.Physics3D.Raycast(transform->Position, step.Normalized, step.Magnitude + FP._0_05, -1, QueryOptions.HitSolids);
                if (!hit.HasValue)
                {
                    transform->Position += step;
                    if (transform->Position.Y < -10) f.Destroy(pair.Entity);
                    continue;
                }
                if (FPVector3.Dot(hit.Value.Normal, FPVector3.Up) < FP._0_50)
                {
                    // Glancing off a wall: reflect and lose most of the speed.
                    var normal = hit.Value.Normal;
                    pickup->Velocity = (pickup->Velocity - normal * 2 * FPVector3.Dot(pickup->Velocity, normal)) * FP._0_25;
                    continue;
                }
                transform->Position = hit.Value.Point;
                pickup->Velocity = FPVector3.Zero;
                pickup->Resting = true;
                if (hit.Value.Entity == truckEntity || (hit.Value.Entity.IsValid && f.Has<Attached>(hit.Value.Entity)))
                {
                    f.Add(pair.Entity, new Attached
                    {
                        LocalPosition = truck.InverseTransformPoint(transform->Position),
                        LocalRotation = FPQuaternion.Inverse(truck.Rotation) * transform->Rotation,
                    });
                }
            }

            foreach (var pair in f.Unsafe.GetComponentBlockIterator<Projectile>())
            {
                var projectile = pair.Component;
                var transform = f.Unsafe.GetPointer<Transform3D>(pair.Entity);
                projectile->Age += dt;
                projectile->Velocity += FPVector3.Down * 12 * dt;
                var step = projectile->Velocity * dt;
                var hit = f.Physics3D.Raycast(transform->Position, step.Normalized, step.Magnitude, -1, QueryOptions.HitSolids);
                var exploded = hit.HasValue || projectile->Age > 6;
                var position = hit.HasValue ? hit.Value.Point : transform->Position + step;
                foreach (var zombie in f.Unsafe.GetComponentBlockIterator<Zombie>())
                {
                    if (exploded || zombie.Component->State == ZombieState.Dead) continue;
                    var zombieCenter = f.Unsafe.GetPointer<Transform3D>(zombie.Entity)->Position + FPVector3.Up;
                    exploded = (zombieCenter - position).SqrMagnitude < 1;
                }
                transform->Position = position;
                if (!exploded) continue;
                Combat.Explode(f, position, projectile->Radius, 3, projectile->Flavor, false, projectile->Owner);
                f.Destroy(pair.Entity);
            }
        }
    }
}
