using PurrNet.Prediction;
using UnityEngine;

public struct TruckInput : IPredictedData
{
    public sbyte steer; // -100..100
    public sbyte throttle; // -100..100

    public void Dispose() { }
}

public struct TruckState : IPredictedData<TruckState>
{
    public Vector2 pos; // world x, z
    public float yaw; // degrees, 0 = +z
    public float speed;
    public float steer; // wheel angle, degrees
    public float crashTimer;

    public void Dispose() { }
}

// Kinematic bicycle model with OBB-vs-AABB building collision. Pure math with no physics
// queries, so the server and the predicting driver run the exact same code and replaying
// inputs after a correction is cheap.
public static class TruckSim
{
    public const float Length = 6.4f;
    public const float Width = 2.6f;
    public const float Wheelbase = 3.6f;
    public const float MinSpeed = 3.5f;
    public const float CruiseSpeed = 7f;
    public const float MaxSpeed = 12f;
    public const float Accel = 2.5f;
    public const float MaxSteer = 32f;
    public const float SteerRate = 70f;

    public static TruckState Step(TruckState s, TruckInput input, float dt)
    {
        float steerInput = input.steer / 100f;
        float throttleInput = input.throttle / 100f;
        float targetSteer = steerInput * MaxSteer;
        s.steer = Mathf.MoveTowards(s.steer, targetSteer, SteerRate * dt);

        // The brakes don't work: the truck never drops below MinSpeed.
        float targetSpeed = throttleInput >= 0f
            ? Mathf.Lerp(CruiseSpeed, MaxSpeed, throttleInput)
            : Mathf.Lerp(CruiseSpeed, MinSpeed, -throttleInput);
        if (s.crashTimer > 0f)
        {
            s.crashTimer -= dt;
            targetSpeed = MinSpeed;
        }
        s.speed = Mathf.MoveTowards(s.speed, targetSpeed, Accel * dt);

        float yawRate = s.speed * Mathf.Tan(s.steer * Mathf.Deg2Rad) / Wheelbase * Mathf.Rad2Deg;
        s.yaw = Mathf.Repeat(s.yaw + yawRate * dt, 360f);
        s.pos += Forward(s.yaw) * (s.speed * dt);

        foreach (Rect building in TownLayout.Buildings)
        {
            if (PushOut(ref s, building))
            {
                if (s.crashTimer <= 0f)
                {
                    s.speed = MinSpeed;
                }
                s.crashTimer = 1.2f;
            }
        }
        return s;
    }

    public static Vector2 Forward(float yaw)
    {
        float r = yaw * Mathf.Deg2Rad;
        return new Vector2(Mathf.Sin(r), Mathf.Cos(r));
    }

    // Separating-axis test between the truck's oriented box and an axis-aligned building.
    // Pushes the truck out along the axis of least penetration.
    static bool PushOut(ref TruckState s, Rect box)
    {
        Vector2 f = Forward(s.yaw);
        Vector2 r = new Vector2(f.y, -f.x);
        Vector2 half = new Vector2(Width * 0.5f, Length * 0.5f);
        Vector2 boxHalf = box.size * 0.5f;
        Vector2 delta = box.center - s.pos;
        if (delta.magnitude > half.magnitude + boxHalf.magnitude)
        {
            return false;
        }

        Vector2[] axes = { Vector2.right, Vector2.up, r, f };
        float best = float.MaxValue;
        Vector2 bestAxis = Vector2.zero;
        foreach (Vector2 axis in axes)
        {
            float truckExtent = half.x * Mathf.Abs(Vector2.Dot(r, axis)) + half.y * Mathf.Abs(Vector2.Dot(f, axis));
            float boxExtent = boxHalf.x * Mathf.Abs(axis.x) + boxHalf.y * Mathf.Abs(axis.y);
            float distance = Vector2.Dot(delta, axis);
            float overlap = truckExtent + boxExtent - Mathf.Abs(distance);
            if (overlap <= 0f)
            {
                return false;
            }
            if (overlap < best)
            {
                best = overlap;
                bestAxis = distance > 0f ? -axis : axis;
            }
        }
        s.pos += bestAxis * best;
        return true;
    }
}
