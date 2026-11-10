namespace Quantum
{
    using Photon.Deterministic;

    // Flies ice cream globs until they splat on a kid, a cop, a dad (brain freeze), the nut tree or the scenery; moves
    // dropped items until they land (sticking to the van if they land on it); and flies lunch money to the nearest dad.
    public unsafe class GlobSystem : SystemMainThread
    {
        public override void Update(Frame f)
        {
            var settings = f.FindAsset(f.RuntimeConfig.DadsSettings);
            var dt = f.DeltaTime;
            Globs(f, settings, dt);
            Loots(f, dt);
            Cashes(f, settings, dt);
        }

        static void Globs(Frame f, DadsSettings settings, FP dt)
        {
            foreach (var pair in f.Unsafe.GetComponentBlockIterator<Glob>())
            {
                var glob = pair.Component;
                var transform = f.Unsafe.GetPointer<Transform3D>(pair.Entity);
                glob->Age += dt;
                glob->Velocity += FPVector3.Down * settings.GlobGravity * dt;
                var step = glob->Velocity * dt;
                var next = transform->Position + step;
                if (HitCharacter(f, settings, pair.Entity, glob, next))
                {
                    f.Destroy(pair.Entity);
                    continue;
                }
                var hit = f.Physics3D.Raycast(transform->Position, step.Normalized, step.Magnitude, -1, QueryOptions.HitSolids);
                // Shots leaving the van pass its own sill, counter and window frame, so dads can serve kids from the window.
                var ownVan = hit.HasValue && (hit.Value.Entity == f.GetSingletonEntityRef<Van>() || (hit.Value.Entity.IsValid && f.Has<Riding>(hit.Value.Entity)));
                if (ownVan && glob->Age < FP._0_10) hit = null;
                if (hit.HasValue)
                {
                    var target = hit.Value.Entity;
                    if (target.IsValid && f.Unsafe.TryGetPointer(target, out Fixture* tree) && tree->Kind == FixtureKind.NutTree) DadsGame.ShakeTree(f, target, tree, 1);
                    f.Events.GlobSplat(hit.Value.Point, hit.Value.Normal, glob->Treat, target);
                    f.Destroy(pair.Entity);
                    continue;
                }
                if (next.Y < 0 || glob->Age > 4)
                {
                    f.Events.GlobSplat(new FPVector3(next.X, 0, next.Z), FPVector3.Up, glob->Treat, EntityRef.None);
                    f.Destroy(pair.Entity);
                    continue;
                }
                transform->Position = next;
                transform->Rotation = FPQuaternion.LookRotation(glob->Velocity.Normalized);
            }
        }

        // Kids and cops are vertical capsules; dads other than the shooter get brain freeze.
        static bool HitCharacter(Frame f, DadsSettings settings, EntityRef entity, Glob* glob, FPVector3 point)
        {
            foreach (var pair in f.Unsafe.GetComponentBlockIterator<Npc>())
            {
                var stats = settings.Npcs[(int)pair.Component->Kind];
                var position = f.Unsafe.GetPointer<Transform3D>(pair.Entity)->Position;
                var offset = point - position;
                var reach = stats.Radius + settings.GlobRadius * FP._0_50;
                if (offset.Y < 0 || offset.Y > stats.Height + FP._0_20 || offset.X * offset.X + offset.Z * offset.Z > reach * reach) continue;
                f.Events.GlobSplat(point, -glob->Velocity.Normalized, glob->Treat, pair.Entity);
                DadsGame.Feed(f, pair.Entity, pair.Component, glob->Treat, glob->Bites, point, false);
                return true;
            }
            foreach (var pair in f.Unsafe.GetComponentBlockIterator<Dad>())
            {
                if (pair.Component->Player == glob->Owner || glob->Age < FP._0_10) continue;
                var offset = point - f.Unsafe.GetPointer<Transform3D>(pair.Entity)->Position;
                if (offset.Y < 0 || offset.Y > 2 || offset.X * offset.X + offset.Z * offset.Z > FP._0_20) continue;
                pair.Component->Frozen = settings.FrozenTime;
                f.Events.GlobSplat(point, -glob->Velocity.Normalized, glob->Treat, pair.Entity);
                f.Events.BrainFreeze(pair.Component->Player, glob->Treat);
                return true;
            }
            return false;
        }

        static void Loots(Frame f, FP dt)
        {
            var vanEntity = f.GetSingletonEntityRef<Van>();
            var van = f.Get<Transform3D>(vanEntity);
            foreach (var pair in f.Unsafe.GetComponentBlockIterator<Loot>())
            {
                var loot = pair.Component;
                if (loot->Resting) continue;
                var transform = f.Unsafe.GetPointer<Transform3D>(pair.Entity);
                loot->Velocity += FPVector3.Down * 20 * dt;
                var step = loot->Velocity * dt;
                // Falling items land on the scenery and the van's floor, never on kitchen fixtures (they would wedge).
                Physics3D.Hit3D? hit = null;
                var hits = f.Physics3D.RaycastAll(transform->Position, step.Normalized, step.Magnitude + FP._0_05, -1, QueryOptions.HitSolids | QueryOptions.ComputeDetailedInfo);
                for (int i = 0; i < hits.Count; i++)
                {
                    if (!hits[i].IsStatic && hits[i].Entity != vanEntity) continue;
                    if (hit.HasValue && (hits[i].Point - transform->Position).SqrMagnitude >= (hit.Value.Point - transform->Position).SqrMagnitude) continue;
                    hit = hits[i];
                }
                if (!hit.HasValue)
                {
                    transform->Position += step;
                    if (transform->Position.Y < -10) f.Destroy(pair.Entity);
                    continue;
                }
                if (FPVector3.Dot(hit.Value.Normal, FPVector3.Up) < FP._0_50)
                {
                    // Glancing off a wall (or a fixture box): step back out of it, reflect and lose most of the speed.
                    var normal = hit.Value.Normal;
                    transform->Position = hit.Value.Point + normal * FP._0_10;
                    loot->Velocity = (loot->Velocity - normal * 2 * FPVector3.Dot(loot->Velocity, normal)) * FP._0_25;
                    continue;
                }
                transform->Position = hit.Value.Point;
                loot->Velocity = FPVector3.Zero;
                loot->Resting = true;
                var onVan = hit.Value.Entity == vanEntity;
                if (!onVan) continue;
                f.Add(pair.Entity, new Riding
                {
                    LocalPosition = van.InverseTransformPoint(transform->Position),
                    LocalRotation = FPQuaternion.Inverse(van.Rotation) * transform->Rotation,
                });
            }
        }

        static void Cashes(Frame f, DadsSettings settings, FP dt)
        {
            var run = f.Unsafe.GetPointerSingleton<DadsRun>();
            foreach (var pair in f.Unsafe.GetComponentBlockIterator<Cash>())
            {
                var cash = pair.Component;
                var transform = f.Unsafe.GetPointer<Transform3D>(pair.Entity);
                cash->Age += dt;
                if (cash->Age > settings.CashLifetime)
                {
                    f.Destroy(pair.Entity);
                    continue;
                }
                // After a moment in the air it homes in on the nearest dad in range, through walls and windows.
                var target = EntityRef.None;
                var nearest = settings.CashMagnetRange * settings.CashMagnetRange;
                var chest = FPVector3.Zero;
                if (cash->Age > FP._0_75)
                {
                    foreach (var dad in f.Unsafe.GetComponentBlockIterator<Dad>())
                    {
                        if (dad.Component->Busted > 0) continue;
                        var point = f.Unsafe.GetPointer<Transform3D>(dad.Entity)->Position + FPVector3.Up;
                        var distance = (point - transform->Position).SqrMagnitude;
                        if (distance >= nearest) continue;
                        nearest = distance;
                        target = dad.Entity;
                        chest = point;
                    }
                }
                if (target.IsValid)
                {
                    var toChest = chest - transform->Position;
                    if (toChest.SqrMagnitude < FP._0_50)
                    {
                        run->Money += cash->Amount;
                        f.Events.CashCollected(f.Get<Dad>(target).Player, cash->Amount, transform->Position);
                        f.Destroy(pair.Entity);
                        continue;
                    }
                    cash->Resting = false;
                    cash->Velocity = toChest.Normalized * FPMath.Min(14, 4 + cash->Age * 6);
                    transform->Position += cash->Velocity * dt;
                    continue;
                }
                if (cash->Resting) continue;
                cash->Velocity += FPVector3.Down * 15 * dt;
                var next = transform->Position + cash->Velocity * dt;
                if (next.Y <= 0)
                {
                    next.Y = 0;
                    cash->Velocity = FPVector3.Zero;
                    cash->Resting = true;
                }
                transform->Position = next;
            }
        }
    }
}
