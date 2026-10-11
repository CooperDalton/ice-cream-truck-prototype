namespace Quantum
{
    using Photon.Deterministic;

    // Drives the van, stops it against buildings, closed gates and solid fixtures (ramming the nut tree shakes it, lamp
    // posts go down at speed and dent the van, which slows it),
    // carries everyone and everything riding it, and bowls over kids, cops and dads it hits at speed. The fat kid is
    // the exception: he stops the van like a wall.
    public unsafe class VanSystem : SystemMainThread
    {
        public override void Update(Frame f)
        {
            var settings = f.FindAsset(f.RuntimeConfig.DadsSettings);
            var entity = f.GetSingletonEntityRef<Van>();
            var van = f.Unsafe.GetPointer<Van>(entity);
            var run = f.Unsafe.GetPointerSingleton<DadsRun>();
            var transform = f.Unsafe.GetPointer<Transform3D>(entity);
            var dt = f.DeltaTime;
            van->Honk = FPMath.Max(0, van->Honk - dt);
            van->Bell = FPMath.Max(0, van->Bell - dt);
            van->BellCooldown = FPMath.Max(0, van->BellCooldown - dt);
            van->Shake = FPMath.Max(0, van->Shake - dt);
            FPVector2 drive = default;
            var stopped = run->Phase == DayPhase.Collection || run->Phase == DayPhase.Won || run->Phase == DayPhase.Repo;
            if (van->Driver.IsValid && !stopped) drive = f.GetPlayerInput(van->Driver)->Move;

            if (drive.Y > 0)
            {
                van->Speed += (van->Speed < 0 ? settings.VanBraking : settings.VanAcceleration) * drive.Y * dt;
            }
            else if (drive.Y < 0)
            {
                van->Speed += (van->Speed > 0 ? settings.VanBraking : settings.VanAcceleration) * drive.Y * dt;
            }
            else
            {
                var rolling = FPMath.Min(FPMath.Abs(van->Speed), (stopped ? 10 : 2) * dt);
                van->Speed -= FPMath.Sign(van->Speed) * rolling;
            }
            van->Speed -= van->Speed * settings.VanDrag * dt;
            van->Speed = FPMath.Clamp(van->Speed, -settings.VanReverseSpeed, settings.VanMaxSpeed * (1 - van->Damage * settings.DamageSlowdown));
            van->Steer = FPMath.Lerp(van->Steer, drive.X * settings.VanMaxSteer, dt * 4);

            // Bicycle model: yaw rate follows speed and steering angle over the wheelbase.
            var yawDelta = van->Speed * FPMath.Tan(van->Steer * FP.Deg2Rad) / settings.VanWheelbase * dt * FP.Rad2Deg;
            var oldPosition = transform->Position;
            var oldRotation = transform->Rotation;
            // Renormalized every tick so the small per-tick turns never drift the quaternion off unit length.
            transform->Rotation = (oldRotation * FPQuaternion.AngleAxis(yawDelta, FPVector3.Up)).Normalized;
            transform->Position += transform->Forward * van->Speed * dt;

            var body = Shape3D.CreateBox(new FPVector3(settings.VanHalfSize.X, FP._0_75, settings.VanHalfSize.Z));
            var hits = f.Physics3D.OverlapShape(transform->Position + FPVector3.Up * FP._1_50, transform->Rotation, body, -1, QueryOptions.HitAll);
            for (int i = 0; i < hits.Count; i++)
            {
                var hit = hits[i];
                var solidFixture = hit.Entity.IsValid && f.Has<Fixture>(hit.Entity) && !f.Has<Riding>(hit.Entity) && !hit.IsTrigger;
                if (!hit.IsStatic && !solidFixture) continue;
                if (solidFixture && f.Unsafe.GetPointer<Fixture>(hit.Entity)->Kind == FixtureKind.LampPost && FPMath.Abs(van->Speed) >= settings.LampBreakSpeed)
                {
                    // Mowed down: the post falls, the van loses some speed and takes a dent.
                    f.Unsafe.GetPointer<Fixture>(hit.Entity)->Open = true;
                    f.Unsafe.GetPointer<PhysicsCollider3D>(hit.Entity)->Enabled = false;
                    van->Speed *= FP._0_75;
                    van->Damage = FPMath.Min(1, van->Damage + settings.LampDamage);
                    van->Shake = FP._0_20;
                    f.Events.LampFelled(hit.Entity, f.Get<Transform3D>(hit.Entity).Position);
                    continue;
                }
                var bumper = oldPosition + transform->Forward * settings.VanHalfSize.Z * FPMath.Sign(van->Speed) + FPVector3.Up * FP._1_50;
                if (FPMath.Abs(van->Speed) > settings.CrashMinSpeed) f.Events.VanCrashed(bumper, van->Speed);
                if (solidFixture && FPMath.Abs(van->Speed) > 4)
                {
                    var tree = f.Unsafe.GetPointer<Fixture>(hit.Entity);
                    if (tree->Kind == FixtureKind.NutTree) DadsGame.ShakeTree(f, hit.Entity, tree, 5);
                }
                transform->Position = oldPosition;
                transform->Rotation = oldRotation;
                van->Speed = -van->Speed * settings.CrashBounce;
                yawDelta = 0;
                break;
            }
            var turn = transform->Rotation * FPQuaternion.Inverse(oldRotation);

            foreach (var rider in f.Unsafe.GetComponentBlockIterator<Dad>())
            {
                if (rider.Component->Standing != entity) continue;
                var riderTransform = f.Unsafe.GetPointer<Transform3D>(rider.Entity);
                riderTransform->Position = transform->Position + turn * (riderTransform->Position - oldPosition);
                riderTransform->Rotation = turn * riderTransform->Rotation;
                rider.Component->YawOffset += yawDelta;
            }
            foreach (var riding in f.Unsafe.GetComponentBlockIterator<Riding>())
            {
                var ridingTransform = f.Unsafe.GetPointer<Transform3D>(riding.Entity);
                ridingTransform->Position = transform->TransformPoint(riding.Component->LocalPosition);
                ridingTransform->Rotation = transform->Rotation * riding.Component->LocalRotation;
            }

            HitNpcs(f, settings, van, *transform);
            HitDads(f, settings, van, *transform, entity);
        }

        static void HitNpcs(Frame f, DadsSettings settings, Van* van, Transform3D transform)
        {
            var run = f.Unsafe.GetPointerSingleton<DadsRun>();
            var half = settings.VanHalfSize;
            var absSpeed = FPMath.Abs(van->Speed);
            foreach (var pair in f.Unsafe.GetComponentBlockIterator<Npc>())
            {
                var npc = pair.Component;
                if (npc->State == NpcState.Tumble) continue;
                var npcTransform = f.Unsafe.GetPointer<Transform3D>(pair.Entity);
                var radius = settings.Npcs[(int)npc->Kind].Radius;
                var local = transform.InverseTransformPoint(npcTransform->Position);
                if (FPMath.Abs(local.X) >= half.X + radius || FPMath.Abs(local.Z) >= half.Z + radius) continue;
                if (npc->Kind == NpcKind.FatKid && absSpeed > settings.CrashMinSpeed)
                {
                    f.Events.VanCrashed(transform.TransformPoint(new FPVector3(0, FP._1_50, half.Z * FPMath.Sign(van->Speed))), van->Speed);
                    van->Speed = -van->Speed * settings.CrashBounce;
                    continue;
                }
                if (npc->Kind != NpcKind.FatKid && absSpeed >= settings.KnockSpeed)
                {
                    var fling = transform.Forward * van->Speed * FP._1_10 + FPVector3.Up * (3 + absSpeed * FP._0_33) + transform.Right * FPMath.Sign(local.X) * 2;
                    DadsGame.KnockNpc(f, pair.Entity, npc, fling);
                    run->Heat += npc->Kind == NpcKind.Cop ? 2 : FP._0_50;
                    van->Speed -= FPMath.Sign(van->Speed) * FP._0_50;
                    continue;
                }
                // Too slow to bowl them over: they get nudged aside.
                local.X = FPMath.Sign(local.X) * (half.X + radius);
                var shoved = transform.TransformPoint(local);
                npcTransform->Position = new FPVector3(shoved.X, npcTransform->Position.Y, shoved.Z);
            }
        }

        static void HitDads(Frame f, DadsSettings settings, Van* van, Transform3D transform, EntityRef vanEntity)
        {
            var half = settings.VanHalfSize;
            var absSpeed = FPMath.Abs(van->Speed);
            if (absSpeed < settings.KnockSpeed) return;
            foreach (var pair in f.Unsafe.GetComponentBlockIterator<Dad>())
            {
                var dad = pair.Component;
                if (dad->Standing == vanEntity || dad->Knocked > 0 || dad->Driving || dad->Turret) continue;
                var position = f.Unsafe.GetPointer<Transform3D>(pair.Entity)->Position;
                var local = transform.InverseTransformPoint(position);
                if (FPMath.Abs(local.X) >= half.X + FP._0_25 || FPMath.Abs(local.Z) >= half.Z + FP._0_25 || local.Y > 1) continue;
                var fling = transform.Forward * van->Speed + FPVector3.Up * (5 + absSpeed * FP._0_33) + transform.Right * FPMath.Sign(local.X) * 3;
                DadsGame.KnockDad(f, pair.Entity, dad, fling);
            }
        }
    }
}
