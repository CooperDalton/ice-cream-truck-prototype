namespace Quantum
{
    using Photon.Deterministic;

    public unsafe class TruckSystem : SystemMainThread
    {
        public override void Update(Frame f)
        {
            var settings = f.FindAsset(f.RuntimeConfig.Settings);
            var entity = f.GetSingletonEntityRef<Truck>();
            var truck = f.Unsafe.GetPointer<Truck>(entity);
            var transform = f.Unsafe.GetPointer<Transform3D>(entity);
            var dt = f.DeltaTime;
            FPVector2 drive = default;
            if (truck->Driver.IsValid)
            {
                drive = f.GetPlayerInput(truck->Driver)->Move;
            }
            // On an empty tank the pedal only brakes.
            if (truck->Fuel <= 0 && drive.Y * truck->Speed >= 0)
            {
                drive.Y = 0;
            }

            if (drive.Y > 0)
            {
                truck->Speed += (truck->Speed < 0 ? settings.TruckBraking : settings.TruckAcceleration) * drive.Y * dt;
            }
            else if (drive.Y < 0)
            {
                truck->Speed += (truck->Speed > 0 ? settings.TruckBraking : settings.TruckAcceleration) * drive.Y * dt;
            }
            else
            {
                var rolling = FPMath.Min(FPMath.Abs(truck->Speed), FP._2 * dt);
                truck->Speed -= FPMath.Sign(truck->Speed) * rolling;
            }
            truck->Speed -= truck->Speed * settings.TruckDrag * dt;
            var maxSpeed = settings.TruckMaxSpeed + (truck->Engine ? settings.EngineBonusSpeed : 0)
                + (truck->FuelFlavor == Flavor.Coffee ? settings.CoffeeFuelBonusSpeed : 0);
            truck->Speed = FPMath.Clamp(truck->Speed, -settings.TruckReverseSpeed, maxSpeed);
            truck->Steer = FPMath.Lerp(truck->Steer, drive.X * settings.TruckMaxSteer, dt * 4);

            // Bicycle model: yaw rate follows speed and steering angle over the wheelbase.
            var yawDelta = truck->Speed * FPMath.Tan(truck->Steer * FP.Deg2Rad) / settings.TruckWheelbase * dt * FP.Rad2Deg;
            var oldPosition = transform->Position;
            var oldRotation = transform->Rotation;
            // Renormalized every tick: the small per-tick turns otherwise drift the quaternion off unit length, which
            // skews every TransformPoint against the truck (seats, stations and riders end up inside its colliders).
            transform->Rotation = (oldRotation * FPQuaternion.AngleAxis(yawDelta, FPVector3.Up)).Normalized;
            transform->Position += transform->Forward * truck->Speed * dt;
            if (truck->Fuel > 0)
            {
                truck->Fuel -= FPMath.Abs(truck->Speed) * dt / settings.MetersPerScoop;
                if (truck->Fuel <= 0)
                {
                    truck->Fuel = 0;
                    f.Events.OutOfFuel(transform->Position);
                }
            }

            // Buildings, roadside props, scenery blocks and the stations standing in the world (gun crates, shop pedestals,
            // the exit sign) stop the truck dead and bounce it back.
            var body = Shape3D.CreateBox(new FPVector3(settings.TruckHalfSize.X, FP._0_75, settings.TruckHalfSize.Z));
            var hits = f.Physics3D.OverlapShape(transform->Position + FPVector3.Up * FP._1_50, transform->Rotation, body, -1, QueryOptions.HitAll);
            for (int i = 0; i < hits.Count; i++)
            {
                var hit = hits[i].Entity;
                if (!hit.IsValid || !(f.Has<RoadChunk>(hit) || f.Has<Scenery>(hit) || (f.Has<Station>(hit) && !f.Has<Attached>(hit)))) continue;
                // Overlap hits carry no contact point, so the crash effects go on the bumper that hit.
                var bumper = oldPosition + transform->Forward * settings.TruckHalfSize.Z * FPMath.Sign(truck->Speed) + FPVector3.Up * FP._1_50;
                if (FPMath.Abs(truck->Speed) > settings.CrashMinSpeed)
                {
                    f.Events.TruckCrashed(bumper, truck->Speed);
                    ZombieSystem.Alert(f, bumper, settings.CrashNoise);
                }
                transform->Position = oldPosition;
                transform->Rotation = oldRotation;
                truck->Speed = -truck->Speed * settings.CrashBounce;
                yawDelta = 0;
                break;
            }
            var turn = transform->Rotation * FPQuaternion.Inverse(oldRotation);

            // Carry everyone standing on or inside the truck along with it.
            foreach (var rider in f.Unsafe.GetComponentBlockIterator<Survivor>())
            {
                if (rider.Component->Standing != entity)
                {
                    continue;
                }
                var riderTransform = f.Unsafe.GetPointer<Transform3D>(rider.Entity);
                riderTransform->Position = transform->Position + turn * (riderTransform->Position - oldPosition);
                riderTransform->Rotation = turn * riderTransform->Rotation;
                rider.Component->YawOffset += yawDelta;
            }
            foreach (var attached in f.Unsafe.GetComponentBlockIterator<Attached>())
            {
                var attachedTransform = f.Unsafe.GetPointer<Transform3D>(attached.Entity);
                attachedTransform->Position = transform->TransformPoint(attached.Component->LocalPosition);
                attachedTransform->Rotation = transform->Rotation * attached.Component->LocalRotation;
            }
        }
    }
}
