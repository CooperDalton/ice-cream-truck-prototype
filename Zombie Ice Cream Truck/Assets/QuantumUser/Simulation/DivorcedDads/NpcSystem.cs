namespace Quantum
{
    using System;
    using Photon.Deterministic;

    // Kids, the fat kid and cops. Kids hang around their yards until they hear the jingle, the horn or the bell, then
    // chase the van and line up at the serving window when it stops. Fed kids wander home happy (or bounce around on a
    // coffee high); at dusk everyone goes inside. Lactose kids blow up into gas clouds that scatter the queue. The fat
    // kid hears the van from across town, charges it and body-slams it, eating a tub each time. Cops patrol the
    // roads at night (or by day once the heat is up), chase dads on foot and ticket the van when it is parked.
    public unsafe class NpcSystem : SystemMainThread
    {
        public override void Update(Frame f)
        {
            var settings = f.FindAsset(f.RuntimeConfig.DadsSettings);
            var run = f.Unsafe.GetPointerSingleton<DadsRun>();
            var vanEntity = f.GetSingletonEntityRef<Van>();
            var van = f.Unsafe.GetPointer<Van>(vanEntity);
            var vanTransform = f.Get<Transform3D>(vanEntity);
            var dt = f.DeltaTime;
            if (run->Phase == DayPhase.Collection || run->Phase == DayPhase.Won || run->Phase == DayPhase.Repo) return;

            var call = van->Jingle ? (run->Loudspeaker ? settings.LoudspeakerRadius : settings.JingleRadius) : 0;
            if (van->Honk > 0) call = FPMath.Max(call, settings.HonkRadius);
            if (van->Bell > 0) call = FPMath.Max(call, settings.BellRadius);
            var evening = run->Phase == DayPhase.Dusk || run->Phase == DayPhase.Night;

            int kids = 0, cops = 0;
            foreach (var pair in f.Unsafe.GetComponentBlockIterator<Npc>())
            {
                var npc = pair.Component;
                var transform = f.Unsafe.GetPointer<Transform3D>(pair.Entity);
                var stats = settings.Npcs[(int)npc->Kind];
                if (npc->Kind == NpcKind.Cop) cops++;
                else if (npc->Kind != NpcKind.FatKid) kids++;
                var toVan = vanTransform.Position - transform->Position;
                toVan.Y = 0;
                var vanDistance = toVan.Magnitude;
                if (vanDistance > settings.DespawnRange && npc->State != NpcState.Chase)
                {
                    DadsGame.LeaveQueue(f, pair.Entity);
                    f.Destroy(pair.Entity);
                    continue;
                }
                npc->Timer -= dt;
                if (npc->State == NpcState.Tumble)
                {
                    Tumble(f, npc, transform, dt);
                    continue;
                }
                if (npc->Gassy > 0)
                {
                    npc->Gassy -= dt;
                    if (npc->Gassy <= 0) Fart(f, pair.Entity, npc, transform->Position, settings);
                }
                if (Gassed(f, transform->Position, out var cloud) && npc->Kind != NpcKind.LactoseKid && npc->State != NpcState.Flee)
                {
                    DadsGame.LeaveQueue(f, pair.Entity);
                    npc->State = NpcState.Flee;
                    npc->Goal = cloud;
                    npc->Timer = 3;
                }

                if (npc->Kind == NpcKind.Cop)
                {
                    Cop(f, pair.Entity, npc, transform, stats, settings, van, vanTransform, evening, call, dt);
                    continue;
                }
                var hears = run->Phase == DayPhase.Day && vanDistance < (npc->Kind == NpcKind.FatKid && call > 0 ? settings.FatKidHearing : call);
                if (npc->Kind == NpcKind.FatKid)
                {
                    FatKid(f, pair.Entity, npc, transform, stats, settings, van, vanTransform, hears, evening, dt);
                    continue;
                }
                Kid(f, pair.Entity, npc, transform, stats, settings, van, vanTransform, hears, evening, dt);
            }

            Clouds(f, settings, dt);
            Spawn(f, settings, run, vanTransform, kids, cops, dt);
        }

        static void Kid(Frame f, EntityRef entity, Npc* npc, Transform3D* transform, NpcStats stats, DadsSettings settings, Van* van,
            Transform3D vanTransform, bool hears, bool evening, FP dt)
        {
            var parked = FPMath.Abs(van->Speed) < 2;
            if (evening && npc->State != NpcState.Home && npc->State != NpcState.Flee)
            {
                DadsGame.LeaveQueue(f, entity);
                npc->State = NpcState.Home;
            }
            switch (npc->State)
            {
                case NpcState.Wander:
                    if (hears && npc->Fed < npc->Hunger)
                    {
                        npc->State = NpcState.Approach;
                        npc->Timer = 20;
                        break;
                    }
                    if (FollowPath(f, npc, transform, settings, false, stats.WalkSpeed, dt)) break;
                    if (npc->Timer <= 0)
                    {
                        npc->Goal = npc->Home + new FPVector3(f.RNG->Next(-4, 4), 0, f.RNG->Next(-4, 4));
                        npc->Timer = f.RNG->Next(3, 8);
                    }
                    Walk(f, transform, npc->Goal, stats.WalkSpeed, dt);
                    break;
                case NpcState.Approach:
                    if (hears) npc->Timer = 20;
                    if (npc->Timer <= 0)
                    {
                        npc->State = NpcState.Wander;
                        break;
                    }
                    if (FollowPath(f, npc, transform, settings, true, stats.RunSpeed, dt)) break;
                    var window = vanTransform.TransformPoint(settings.WindowOutside);
                    if (!parked)
                    {
                        // Running after a moving ice cream truck, aiming for its back door.
                        Walk(f, transform, vanTransform.TransformPoint(settings.RearOutside), stats.RunSpeed, dt);
                        break;
                    }
                    if ((window - transform->Position).SqrMagnitude < 25 && TakeSlot(f, entity, npc, van))
                    {
                        npc->State = NpcState.Queue;
                        npc->Timer = 75;
                        break;
                    }
                    Walk(f, transform, AroundVan(vanTransform, settings, transform->Position, window), stats.RunSpeed, dt);
                    break;
                case NpcState.Queue:
                    if (!parked || npc->Timer <= 0)
                    {
                        DadsGame.LeaveQueue(f, entity);
                        npc->State = npc->Timer <= 0 ? NpcState.Home : NpcState.Approach;
                        npc->Timer = 20;
                        break;
                    }
                    var spot = vanTransform.TransformPoint(settings.WindowOutside + FPVector3.Left * settings.QueueSpacing * npc->QueueSlot);
                    if (!Walk(f, transform, AroundVan(vanTransform, settings, transform->Position, spot), stats.WalkSpeed, dt)) Face(transform, vanTransform.Position);
                    break;
                case NpcState.Happy:
                    if (npc->Timer <= 0)
                    {
                        npc->State = NpcState.Home;
                        break;
                    }
                    if (!FollowPath(f, npc, transform, settings, false, stats.WalkSpeed, dt)) Walk(f, transform, npc->Home, stats.WalkSpeed, dt);
                    break;
                case NpcState.Hyper:
                    if (npc->Timer <= 0)
                    {
                        npc->State = NpcState.Happy;
                        npc->Timer = 4;
                        break;
                    }
                    // Laps on a coffee high: always turning, flat out.
                    var forward = transform->Rotation * FPQuaternion.Euler(0, 200 * dt, 0) * FPVector3.Forward;
                    Walk(f, transform, transform->Position + forward * 3, stats.RunSpeed * FP._1_50, dt);
                    break;
                case NpcState.Flee:
                    if (npc->Timer <= 0)
                    {
                        npc->State = npc->Fed >= npc->Hunger || evening ? NpcState.Home : NpcState.Wander;
                        break;
                    }
                    var away = transform->Position - npc->Goal;
                    away.Y = 0;
                    if (away.SqrMagnitude < FP._0_01) away = FPVector3.Forward;
                    Walk(f, transform, transform->Position + away.Normalized * 3, stats.RunSpeed, dt);
                    break;
                case NpcState.Home:
                    // Walks home (back through the yard gate) and goes inside.
                    if (FollowPath(f, npc, transform, settings, false, stats.WalkSpeed * FP._1_25, dt) && npc->Timer > -30) break;
                    if (!Walk(f, transform, npc->Home, stats.WalkSpeed * FP._1_25, dt) || npc->Timer < -30) f.Destroy(entity);
                    break;
            }
        }

        static void FatKid(Frame f, EntityRef entity, Npc* npc, Transform3D* transform, NpcStats stats, DadsSettings settings, Van* van,
            Transform3D vanTransform, bool hears, bool evening, FP dt)
        {
            npc->SlamCooldown -= dt;
            if (npc->State == NpcState.Happy || npc->State == NpcState.Hyper || npc->State == NpcState.Flee)
            {
                if (npc->State == NpcState.Flee && npc->Timer <= 0) npc->State = NpcState.Wander;
                else if (!FollowPath(f, npc, transform, settings, false, stats.WalkSpeed, dt)) Walk(f, transform, npc->Home, stats.WalkSpeed, dt);
                return;
            }
            if (evening && npc->State != NpcState.Home)
            {
                npc->State = NpcState.Home;
                npc->Timer = 0;
            }
            if (npc->State == NpcState.Home)
            {
                if (FollowPath(f, npc, transform, settings, false, stats.WalkSpeed, dt) && npc->Timer > -30) return;
                if (!Walk(f, transform, npc->Home, stats.WalkSpeed, dt) || npc->Timer < -30) f.Destroy(entity);
                return;
            }
            if (hears && npc->State != NpcState.Chase)
            {
                npc->State = NpcState.Chase;
                f.Events.FatKidArrived(entity, transform->Position);
            }
            if (npc->State != NpcState.Chase)
            {
                if (FollowPath(f, npc, transform, settings, false, stats.WalkSpeed, dt)) return;
                if (npc->Timer <= 0)
                {
                    npc->Goal = npc->Home + new FPVector3(f.RNG->Next(-3, 3), 0, f.RNG->Next(-3, 3));
                    npc->Timer = f.RNG->Next(4, 8);
                }
                Walk(f, transform, npc->Goal, stats.WalkSpeed, dt);
                return;
            }
            if (FollowPath(f, npc, transform, settings, true, stats.RunSpeed, dt)) return;
            var local = vanTransform.InverseTransformPoint(transform->Position);
            var half = settings.VanHalfSize;
            var touching = FPMath.Abs(local.X) < half.X + stats.Radius + FP._0_50 && FPMath.Abs(local.Z) < half.Z + stats.Radius + FP._0_50;
            if (!touching)
            {
                Walk(f, transform, vanTransform.Position, stats.RunSpeed, dt);
                return;
            }
            Face(transform, vanTransform.Position);
            if (npc->SlamCooldown > 0 || FPMath.Abs(van->Speed) > 4) return;
            npc->SlamCooldown = settings.FatKidSlamInterval;
            Slam(f, settings, van, vanTransform, transform->Position);
        }

        // Rocks the van, throws everyone off the roof or standing around it, and eats out of the fullest tub.
        static void Slam(Frame f, DadsSettings settings, Van* van, Transform3D vanTransform, FPVector3 from)
        {
            van->Shake = FP._0_75;
            Fixture* fullest = null;
            foreach (var pair in f.Unsafe.GetComponentBlockIterator<Fixture>())
            {
                if (pair.Component->Kind == FixtureKind.Tub && pair.Component->Count > 0 && (fullest == null || pair.Component->Count > fullest->Count)) fullest = pair.Component;
            }
            var stolen = 0;
            if (fullest != null)
            {
                stolen = Math.Min(fullest->Count, settings.FatKidBite);
                fullest->Count -= stolen;
                if (fullest->Count == 0) fullest->Treat = Treat.None;
            }
            var vanEntity = f.GetSingletonEntityRef<Van>();
            foreach (var pair in f.Unsafe.GetComponentBlockIterator<Dad>())
            {
                var dad = pair.Component;
                if (dad->Driving) continue;
                var position = f.Unsafe.GetPointer<Transform3D>(pair.Entity)->Position;
                var local = vanTransform.InverseTransformPoint(position);
                var onRoof = dad->Standing == vanEntity && local.Y > settings.RoofHeight - FP._0_50;
                var near = dad->Standing != vanEntity && (position - from).SqrMagnitude < 9;
                if (!onRoof && !near) continue;
                var away = position - from;
                away.Y = 0;
                DadsGame.KnockDad(f, pair.Entity, dad, away.Normalized * 6 + FPVector3.Up * 6);
            }
            f.Events.VanSlammed(from, stolen);
        }

        static void Cop(Frame f, EntityRef entity, Npc* npc, Transform3D* transform, NpcStats stats, DadsSettings settings, Van* van,
            Transform3D vanTransform, bool evening, FP call, FP dt)
        {
            var run = f.Unsafe.GetPointerSingleton<DadsRun>();
            var vanEntity = f.GetSingletonEntityRef<Van>();
            var onDuty = evening || run->Heat >= 2;
            switch (npc->State)
            {
                case NpcState.Break:
                case NpcState.Flee:
                    if (npc->Timer <= 0) npc->State = NpcState.Wander;
                    else if (npc->State == NpcState.Flee) Walk(f, transform, transform->Position + (transform->Position - npc->Goal).Normalized * 3, stats.RunSpeed, dt);
                    return;
                case NpcState.Chase:
                    var target = ChaseTarget(f, transform->Position, settings, vanEntity, out var targetDad);
                    var toVan = (vanTransform.Position - transform->Position).Magnitude;
                    // Big Dairy's lot is off limits: he has the cops paid off.
                    var safe = (target - settings.LotPark).SqrMagnitude < settings.LotRadius * settings.LotRadius;
                    if (!onDuty || safe || (!targetDad.IsValid && toVan > settings.CopNotice * 2))
                    {
                        npc->State = NpcState.Wander;
                        return;
                    }
                    if (targetDad.IsValid && (target - transform->Position).SqrMagnitude < settings.CopCatch * settings.CopCatch)
                    {
                        Bust(f, targetDad, settings, transform->Position);
                        npc->State = NpcState.Break;
                        npc->Timer = 8;
                        return;
                    }
                    var local = vanTransform.InverseTransformPoint(transform->Position);
                    var atVan = FPMath.Abs(local.X) < settings.VanHalfSize.X + FP._1_50 && FPMath.Abs(local.Z) < settings.VanHalfSize.Z + FP._1_50;
                    if (!targetDad.IsValid && atVan && FPMath.Abs(van->Speed) < FP._2 + FP._0_50)
                    {
                        var fine = Math.Min(run->Money, settings.TicketFine);
                        run->Money -= fine;
                        f.Events.Ticketed(fine, transform->Position);
                        npc->State = NpcState.Break;
                        npc->Timer = 15;
                        return;
                    }
                    Walk(f, transform, RoadStep(settings, transform->Position, target), stats.RunSpeed, dt);
                    return;
                default:
                    if (onDuty)
                    {
                        // Dads on foot nearby, a parked van, or an ice cream jingle playing after curfew (heard from even
                        // further away than the kids hear it) all get a cop's attention.
                        var seen = ChaseTarget(f, transform->Position, settings, vanEntity, out var seenDad);
                        var parked = FPMath.Abs(van->Speed) < 3;
                        var vanSqr = (vanTransform.Position - transform->Position).SqrMagnitude;
                        var heard = call > 0 && vanSqr < call * call * FP._1_50 * FP._1_50;
                        var inLot = (seen - settings.LotPark).SqrMagnitude < settings.LotRadius * settings.LotRadius;
                        if (inLot) heard = false;
                        if (!inLot && (((seen - transform->Position).SqrMagnitude < settings.CopNotice * settings.CopNotice && (seenDad.IsValid || parked)) || heard))
                        {
                            npc->State = NpcState.Chase;
                            f.Events.CopSpotted(entity, transform->Position);
                            return;
                        }
                    }
                    if (npc->Timer <= 0 || !Walk(f, transform, RoadStep(settings, transform->Position, npc->Goal), stats.WalkSpeed, dt))
                    {
                        // On duty they patrol the streets around the van; otherwise wherever they happen to be.
                        npc->Goal = Patrol(f, settings, onDuty ? vanTransform.Position : transform->Position);
                        npc->Timer = f.RNG->Next(6, 12);
                    }
                    return;
            }
        }

        // Where to run next to reach a target across town: straight there once close, otherwise along the roads. A
        // breadth-first search from the road cell nearest the target gives every road cell its hop count; the cop heads
        // for the closest-to-target cell among those around him, and from on top of it, for its next hop.
        static FPVector3 RoadStep(DadsSettings settings, FPVector3 from, FPVector3 target)
        {
            if ((target - from).SqrMagnitude < 225) return target;
            var spots = settings.RoadSpots;
            var count = spots.Length;
            var goal = 0;
            for (int i = 1; i < count; i++)
            {
                if ((spots[i].Position - target).SqrMagnitude < (spots[goal].Position - target).SqrMagnitude) goal = i;
            }
            var hops = stackalloc int[count];
            var toward = stackalloc int[count];
            var open = stackalloc int[count];
            for (int i = 0; i < count; i++) hops[i] = -1;
            hops[goal] = 0;
            toward[goal] = goal;
            int head = 0, tail = 0;
            open[tail++] = goal;
            while (head < tail)
            {
                var node = open[head++];
                for (int i = 0; i < count; i++)
                {
                    if (hops[i] >= 0) continue;
                    var gap = (spots[i].Position - spots[node].Position).SqrMagnitude;
                    if (gap > 441 || gap < 1) continue;
                    hops[i] = hops[node] + 1;
                    toward[i] = node;
                    open[tail++] = i;
                }
            }
            var best = -1;
            for (int i = 0; i < count; i++)
            {
                if (hops[i] < 0 || (spots[i].Position - from).SqrMagnitude > 484) continue;
                if (best < 0 || hops[i] < hops[best] || (hops[i] == hops[best] && (spots[i].Position - from).SqrMagnitude < (spots[best].Position - from).SqrMagnitude)) best = i;
            }
            if (best < 0) return target;
            if (best == goal) return target;
            return (spots[best].Position - from).SqrMagnitude < FP._6 ? spots[toward[best]].Position : spots[best].Position;
        }

        // The nearest dad on foot, or else the van.
        static FPVector3 ChaseTarget(Frame f, FPVector3 from, DadsSettings settings, EntityRef vanEntity, out EntityRef dad)
        {
            dad = EntityRef.None;
            var best = settings.CopNotice * settings.CopNotice;
            var target = f.Get<Transform3D>(vanEntity).Position;
            foreach (var pair in f.Unsafe.GetComponentBlockIterator<Dad>())
            {
                if (pair.Component->Standing == vanEntity || pair.Component->Busted > 0 || pair.Component->Driving || pair.Component->Turret) continue;
                var position = f.Unsafe.GetPointer<Transform3D>(pair.Entity)->Position;
                var distance = (position - from).SqrMagnitude;
                if (distance >= best) continue;
                best = distance;
                dad = pair.Entity;
                target = position;
            }
            return target;
        }

        static void Bust(Frame f, EntityRef entity, DadsSettings settings, FPVector3 copPosition)
        {
            var run = f.Unsafe.GetPointerSingleton<DadsRun>();
            var dad = f.Unsafe.GetPointer<Dad>(entity);
            var position = f.Unsafe.GetPointer<Transform3D>(entity)->Position;
            var away = position - copPosition;
            away.Y = 0;
            DadsGame.KnockDad(f, entity, dad, away.Normalized * 2 + FPVector3.Up * 3);
            dad->Busted = settings.BustedTime;
            dad->Knocked = settings.BustedTime;
            var fine = Math.Min(run->Money, settings.BustFine);
            run->Money -= fine;
            f.Events.DadBusted(dad->Player, fine, position);
        }

        static FPVector3 Patrol(Frame f, DadsSettings settings, FPVector3 from)
        {
            var best = from;
            for (int attempt = 0; attempt < 6; attempt++)
            {
                var spot = settings.RoadSpots[f.RNG->Next(0, settings.RoadSpots.Length)].Position;
                var distance = (spot - from).SqrMagnitude;
                if (distance < 1600 && distance > 25) return spot;
            }
            return best;
        }

        // Walks a kid along the planned path between their spot (leg 0) and the sidewalk outside their block (last leg),
        // outward or back in. Returns false once there is no more path to walk in that direction.
        static bool FollowPath(Frame f, Npc* npc, Transform3D* transform, DadsSettings settings, bool outward, FP speed, FP dt)
        {
            if (npc->Spot < 0) return false;
            var path = settings.KidSpots[npc->Spot].Path;
            if (outward ? npc->Leg >= path.Length : npc->Leg <= 0) return false;
            var waypoint = path[outward ? npc->Leg : npc->Leg - 1];
            if (!Walk(f, transform, waypoint, speed, dt) || (waypoint - transform->Position).SqrMagnitude < FP._0_50) npc->Leg += outward ? 1 : -1;
            return true;
        }

        // The serving window is on the van's -X side; kids on the other side walk around the nearer end first.
        static FPVector3 AroundVan(Transform3D van, DadsSettings settings, FPVector3 position, FPVector3 goal)
        {
            var half = settings.VanHalfSize;
            var local = van.InverseTransformPoint(position);
            if (local.X < -half.X) return goal;
            var end = local.Z < 0 ? -half.Z - 1 : half.Z + 1;
            return FPMath.Abs(local.Z) < half.Z + FP._0_50 ? van.TransformPoint(new FPVector3(local.X, 0, end)) : van.TransformPoint(new FPVector3(-half.X - 1, 0, end));
        }

        static bool TakeSlot(Frame f, EntityRef entity, Npc* npc, Van* van)
        {
            for (int i = 0; i < van->Queue.Length; i++)
            {
                var slot = van->Queue.GetPointer(i);
                if (slot->IsValid && f.Exists(*slot)) continue;
                *slot = entity;
                npc->QueueSlot = i;
                return true;
            }
            return false;
        }

        static void Tumble(Frame f, Npc* npc, Transform3D* transform, FP dt)
        {
            npc->Velocity += FPVector3.Down * 20 * dt;
            var next = transform->Position + npc->Velocity * dt;
            var side = new FPVector3(npc->Velocity.X, 0, npc->Velocity.Z) * dt;
            if (side != FPVector3.Zero && f.Physics3D.Raycast(transform->Position + FPVector3.Up * FP._0_50, side.Normalized, side.Magnitude + FP._0_25, -1, QueryOptions.HitStatics).HasValue)
            {
                npc->Velocity = new FPVector3(-npc->Velocity.X * FP._0_25, npc->Velocity.Y, -npc->Velocity.Z * FP._0_25);
                next = new FPVector3(transform->Position.X, next.Y, transform->Position.Z);
            }
            if (next.Y <= 0)
            {
                next.Y = 0;
                npc->Velocity = new FPVector3(npc->Velocity.X * FP._0_50, 0, npc->Velocity.Z * FP._0_50);
                if (npc->Velocity.SqrMagnitude < FP._0_25) npc->Velocity = FPVector3.Zero;
            }
            transform->Position = next;
            if (npc->Timer > 0 || next.Y > 0) return;
            // Up again: cops are mad now, fed kids carry on happily, kids the van clipped go home crying.
            npc->State = npc->Kind == NpcKind.Cop ? NpcState.Chase : npc->Fed >= npc->Hunger ? NpcState.Happy : NpcState.Home;
            npc->Timer = npc->State == NpcState.Happy ? 5 : 0;
        }

        static void Fart(Frame f, EntityRef entity, Npc* npc, FPVector3 position, DadsSettings settings)
        {
            var gas = f.Create(settings.GasPrototype);
            f.Unsafe.GetPointer<Transform3D>(gas)->Teleport(f, position);
            f.Add(gas, new Gas { Timer = settings.GasTime, Radius = settings.GasRadius });
            f.Events.GasReleased(position, settings.GasRadius);
            DadsGame.LeaveQueue(f, entity);
            npc->State = NpcState.Home;
        }

        static bool Gassed(Frame f, FPVector3 position, out FPVector3 center)
        {
            center = default;
            foreach (var pair in f.Unsafe.GetComponentBlockIterator<Gas>())
            {
                center = f.Unsafe.GetPointer<Transform3D>(pair.Entity)->Position;
                if ((position - center).SqrMagnitude < pair.Component->Radius * pair.Component->Radius) return true;
            }
            return false;
        }

        // Gas clouds linger, then clear; dads inside them cough.
        static void Clouds(Frame f, DadsSettings settings, FP dt)
        {
            foreach (var pair in f.Unsafe.GetComponentBlockIterator<Gas>())
            {
                pair.Component->Timer -= dt;
                if (pair.Component->Timer <= 0)
                {
                    f.Destroy(pair.Entity);
                    continue;
                }
                var center = f.Unsafe.GetPointer<Transform3D>(pair.Entity)->Position;
                var radius = pair.Component->Radius;
                foreach (var dad in f.Unsafe.GetComponentBlockIterator<Dad>())
                {
                    var position = f.Unsafe.GetPointer<Transform3D>(dad.Entity)->Position;
                    if ((position - center).SqrMagnitude < radius * radius) dad.Component->Coughing = FP._0_50;
                }
            }
        }

        // Walks toward a goal, sidestepping walls. Returns false once it has arrived.
        static bool Walk(Frame f, Transform3D* transform, FPVector3 goal, FP speed, FP dt)
        {
            var toGoal = goal - transform->Position;
            toGoal.Y = 0;
            var distance = toGoal.Magnitude;
            if (distance < FP._0_25) return false;
            var direction = toGoal / distance;
            var eye = transform->Position + FPVector3.Up * FP._0_75;
            if (f.Physics3D.Raycast(eye, direction, FP._1, -1, QueryOptions.HitStatics).HasValue)
            {
                var turned = false;
                for (int i = 2; i <= 7 && !turned; i++)
                {
                    var candidate = FPQuaternion.Euler(0, (i % 2 == 0 ? 1 : -1) * (i / 2) * 45, 0) * direction;
                    if (f.Physics3D.Raycast(eye, candidate, FP._1, -1, QueryOptions.HitStatics).HasValue) continue;
                    direction = candidate;
                    turned = true;
                }
                if (!turned) return true;
            }
            transform->Position += direction * FPMath.Min(speed * dt, distance);
            transform->Position.Y = 0;
            transform->Rotation = FPQuaternion.LookRotation(direction);
            return true;
        }

        static void Face(Transform3D* transform, FPVector3 point)
        {
            var toPoint = point - transform->Position;
            toPoint.Y = 0;
            if (toPoint.SqrMagnitude > FP._0_01) transform->Rotation = FPQuaternion.LookRotation(toPoint.Normalized);
        }

        static void Spawn(Frame f, DadsSettings settings, DadsRun* run, Transform3D van, int kids, int cops, FP dt)
        {
            run->SpawnTimer -= dt;
            run->CopTimer -= dt;
            if (run->Phase == DayPhase.Day && run->SpawnTimer <= 0 && kids < settings.KidCap)
            {
                run->SpawnTimer = settings.SpawnInterval;
                var spot = PickSpot(f, settings.KidSpots, run->Permits, van.Position, settings.SpawnMin, settings.SpawnMax);
                if (spot >= 0) SpawnKid(f, settings, spot, RollKind(f, settings.KidSpots[spot].District));
            }
            if (run->Phase == DayPhase.Day && !run->FatKidSpawned && run->Clock > FP._0_33)
            {
                var spot = PickSpot(f, settings.KidSpots, run->Permits, van.Position, 40, settings.SpawnMax);
                if (spot >= 0)
                {
                    run->FatKidSpawned = true;
                    SpawnKid(f, settings, spot, NpcKind.FatKid);
                }
            }
            var evening = run->Phase == DayPhase.Dusk || run->Phase == DayPhase.Night;
            var heat = FPMath.FloorToInt(run->Heat);
            var wanted = evening ? Math.Min(settings.MaxCops, 2 + heat + run->Day / 2) : run->Heat >= 2 ? Math.Min(settings.MaxCops, heat - 1) : 0;
            if (cops >= wanted || run->CopTimer > 0) return;
            run->CopTimer = 4;
            var road = PickSpot(f, settings.RoadSpots, run->Permits, van.Position, 35, 70);
            if (road >= 0) SpawnKid(f, settings, road, NpcKind.Cop);
        }

        static int PickSpot(Frame f, TownSpot[] spots, Int32 permits, FPVector3 near, FP min, FP max)
        {
            for (int attempt = 0; attempt < 8; attempt++)
            {
                var index = f.RNG->Next(0, spots.Length);
                var spot = spots[index];
                var distance = (spot.Position - near).SqrMagnitude;
                if (spot.District <= permits && distance >= min * min && distance <= max * max) return index;
            }
            return -1;
        }

        static NpcKind RollKind(Frame f, Int32 district)
        {
            var roll = f.RNG->Next();
            if (district == 2) return roll < FP._0_10 ? NpcKind.LactoseKid : roll < FP._0_20 ? NpcKind.DiabeticKid : roll < FP._0_75 ? NpcKind.RichKid : NpcKind.Kid;
            return roll < FP._0_10 + FP._0_02 ? NpcKind.LactoseKid : roll < FP._0_20 + FP._0_02 ? NpcKind.DiabeticKid : NpcKind.Kid;
        }

        // What a kid's thought bubble asks for: whatever their part of town can get. Lactose kids only ever want mud.
        static Treat RollWants(Frame f, NpcKind kind, Int32 district)
        {
            if (kind == NpcKind.LactoseKid) return Treat.Mud;
            var roll = f.RNG->Next(0, 3);
            switch (district)
            {
                case 0: return roll < 2 ? Treat.Mud : Treat.Strawberry;
                case 1: return roll == 0 ? Treat.Strawberry : roll == 1 ? Treat.Coffee : Treat.RockyRoad;
                default: return roll == 0 ? Treat.Coffee : roll == 1 ? Treat.RockyRoad : Treat.GoldLeaf;
            }
        }

        // Moving day's only customer: the dads' own kid, walking over from the ex's porch for a scoop of mud.
        public static void SpawnOwnKid(Frame f, DadsSettings settings)
        {
            var look = f.RNG->Next(0, settings.KidLooks.Length);
            var entity = f.Create(settings.KidLooks[look]);
            f.Unsafe.GetPointer<Transform3D>(entity)->Teleport(f, settings.TutorialKid);
            f.Add(entity, new Npc
            {
                Kind = NpcKind.Kid,
                Look = look,
                State = NpcState.Approach,
                Timer = 600,
                Home = settings.TutorialKid,
                Goal = settings.TutorialKid,
                Hunger = settings.Npcs[(int)NpcKind.Kid].Hunger,
                Wants = Treat.Mud,
                QueueSlot = -1,
                Spot = -1,
            });
        }

        // Kids appear at their hangout spot; cops at a road spot (index into RoadSpots instead).
        static void SpawnKid(Frame f, DadsSettings settings, int index, NpcKind kind)
        {
            var spot = kind == NpcKind.Cop ? settings.RoadSpots[index] : settings.KidSpots[index];
            var look = kind == NpcKind.Kid ? f.RNG->Next(0, settings.KidLooks.Length) : 0;
            var prototype = kind == NpcKind.Kid ? settings.KidLooks[look] : settings.NpcPrototypes[(int)kind];
            var entity = f.Create(prototype);
            f.Unsafe.GetPointer<Transform3D>(entity)->Teleport(f, spot.Position, FPQuaternion.Euler(0, f.RNG->Next(0, 360), 0));
            f.Add(entity, new Npc
            {
                Kind = kind,
                Look = look,
                District = spot.District,
                Home = spot.Position,
                Goal = spot.Position,
                Hunger = settings.Npcs[(int)kind].Hunger,
                Wants = kind == NpcKind.Cop ? Treat.None : RollWants(f, kind, spot.District),
                QueueSlot = -1,
                Spot = kind == NpcKind.Cop ? -1 : index,
            });
        }
    }
}
