using UnityEngine;

// Scripted input for soak tests. Writes GameManager.Input like a human would, so the whole
// game path (prediction, sends, hits) is exercised. Roles come from -bot:
//   driver  takes the seat and drives the test loop; leaves it at -leaveAt seconds
//   rammer  like driver, but steers into kids ahead of the truck
//   gunner  stands at the serving window and shoots the nearest kid
//   runner  hops out the back, runs after the truck and re-boards; takes the seat at -driveAt
[DefaultExecutionOrder(-450)]
public class BotBrain : MonoBehaviour
{
    float readyAt = -1f;
    float leaveAt;
    float driveAt;
    bool interactSent;
    string state = "start";
    float stateSince;

    static readonly Vector2[] Route =
    {
        new Vector2(TownLayout.RoadCenter(0), TownLayout.RoadCenter(0)),
        new Vector2(TownLayout.RoadCenter(3), TownLayout.RoadCenter(0)),
        new Vector2(TownLayout.RoadCenter(3), TownLayout.RoadCenter(3)),
        new Vector2(TownLayout.RoadCenter(0), TownLayout.RoadCenter(3)),
    };

    void Start()
    {
        leaveAt = float.Parse(GameManager.Arg("-leaveAt", "100000"), System.Globalization.CultureInfo.InvariantCulture);
        driveAt = float.Parse(GameManager.Arg("-driveAt", "100000"), System.Globalization.CultureInfo.InvariantCulture);
    }

    void SetState(string next, float t)
    {
        state = next;
        stateSince = t;
        interactSent = false;
        GameManager.Instance.Log.Event("bot", "{\"state\":\"" + next + "\"}");
    }

    void Update()
    {
        GameManager gm = GameManager.Instance;
        ref LocalInput input = ref gm.Input;
        input.interactPressed = false;
        input.jumpPressed = false;
        input.fire = false;
        input.move = Vector2.zero;
        input.steer = 0;
        input.throttle = 0;
        PlayerAvatar me = gm.LocalAvatar;
        if (me == null || !gm.ClockReady || !gm.Truck.Ready)
        {
            return;
        }
        if (readyAt < 0f)
        {
            readyAt = Time.time;
        }
        float t = Time.time - readyAt;
        Truck truck = gm.Truck;
        string role = gm.Bot;

        if (state == "start")
        {
            SetState(role == "driver" || role == "rammer" ? "toSeat" : role == "runner" ? "ride" : "toWindow", t);
        }

        switch (state)
        {
            case "toSeat":
                if (me.CurrentMode == PlayerAvatar.Mode.Outside)
                {
                    ChaseRearDoor(ref input, me, truck);
                    break;
                }
                if (me.CurrentMode == PlayerAvatar.Mode.Driving)
                {
                    SetState("drive", t);
                    break;
                }
                if (WalkInside(ref input, me, PlayerAvatar.SeatLocal, 0.6f) && !interactSent && !truck.HasDriver)
                {
                    input.interactPressed = true;
                    interactSent = true;
                }
                if (interactSent && t - stateSince > 3f)
                {
                    interactSent = false;
                    stateSince = t;
                }
                break;
            case "drive":
                Drive(ref input, truck, t);
                if (t > leaveAt && role == "driver")
                {
                    input.interactPressed = true;
                    SetState("toWindow", t);
                    leaveAt = float.MaxValue;
                }
                break;
            case "toWindow":
                if (me.CurrentMode == PlayerAvatar.Mode.Outside)
                {
                    ChaseRearDoor(ref input, me, truck);
                    break;
                }
                int slot = (int)(me.OwnerId.id.value % 2);
                Vector3 window = new Vector3(TruckSim.Width * 0.5f - 0.55f, PlayerAvatar.FloorY, -0.4f - slot * 1.3f);
                if (WalkInside(ref input, me, window, 0.25f))
                {
                    Shoot(ref input, me, truck, t);
                }
                if (role == "runner" && t > driveAt)
                {
                    SetState("toSeat", t);
                }
                break;
            case "ride":
                if (t - stateSince > 12f)
                {
                    SetState("exit", t);
                }
                if (t > driveAt)
                {
                    SetState("toSeat", t);
                }
                break;
            case "exit":
                if (me.CurrentMode == PlayerAvatar.Mode.Outside)
                {
                    SetState("alongside", t);
                    break;
                }
                WalkInside(ref input, me, new Vector3(0f, PlayerAvatar.FloorY, -TruckSim.Length * 0.5f - 1f), 0.05f);
                break;
            case "alongside":
                // Fall behind for a few seconds, then sprint back aboard.
                input.yaw = truck.DisplayYaw;
                input.move = new Vector2(0f, 1f);
                input.sprint = false;
                if (t - stateSince > 2.5f)
                {
                    SetState("chase", t);
                }
                break;
            case "chase":
                if (me.CurrentMode != PlayerAvatar.Mode.Outside)
                {
                    SetState(t > driveAt ? "toSeat" : "ride", t);
                    break;
                }
                ChaseRearDoor(ref input, me, truck);
                break;
        }
    }

    // Walks toward a truck-local spot. Returns true when there.
    bool WalkInside(ref LocalInput input, PlayerAvatar me, Vector3 target, float tolerance)
    {
        Vector3 d = target - me.DisplayLocal;
        d.y = 0f;
        if (d.magnitude < tolerance)
        {
            return true;
        }
        Vector3 inYawFrame = Quaternion.Euler(0f, -input.yaw, 0f) * d.normalized;
        input.move = new Vector2(inYawFrame.x, inYawFrame.z);
        return false;
    }

    void ChaseRearDoor(ref LocalInput input, PlayerAvatar me, Truck truck)
    {
        Vector3 door = truck.LocalToWorld(new Vector3(0f, 0f, -TruckSim.Length * 0.5f - 0.2f)) + truck.DisplayVelocity * 0.25f;
        Vector3 d = door - me.DisplayWorld;
        d.y = 0f;
        input.yaw = Mathf.Atan2(d.x, d.z) * Mathf.Rad2Deg;
        input.move = new Vector2(0f, 1f);
        input.sprint = true;
    }

    void Drive(ref LocalInput input, Truck truck, float t)
    {
        Vector2 p = new Vector2(truck.DisplayPosition.x, truck.DisplayPosition.z);
        // Pure pursuit on the closest route segment.
        int best = 0;
        float bestD = float.MaxValue;
        for (int i = 0; i < Route.Length; i++)
        {
            Vector2 a = Route[i];
            Vector2 b = Route[(i + 1) % Route.Length];
            Vector2 ab = b - a;
            float u = Mathf.Clamp01(Vector2.Dot(p - a, ab) / ab.sqrMagnitude);
            float d = (a + ab * u - p).magnitude;
            if (d < bestD)
            {
                bestD = d;
                best = i;
            }
        }
        Vector2 sa = Route[best];
        Vector2 sb = Route[(best + 1) % Route.Length];
        Vector2 dir = (sb - sa).normalized;
        float along = Vector2.Dot(p - sa, dir) + 14f;
        float segLength = (sb - sa).magnitude;
        Vector2 look = along < segLength ? sa + dir * along : sb + (Route[(best + 2) % Route.Length] - sb).normalized * (along - segLength);
        Vector2 to = look - p;
        float targetYaw = Mathf.Atan2(to.x, to.y) * Mathf.Rad2Deg;
        if (GameManager.Instance.Bot == "rammer")
        {
            Vector3 fwd = Truck.Forward3(truck.DisplayYaw);
            float best2 = 30f;
            foreach (Npc npc in GameManager.Instance.Npcs.All)
            {
                Vector3 d = npc.DisplayRoot - truck.DisplayPosition;
                if (npc.Showing == Npc.Show.Walk && d.magnitude < best2 && Vector3.Dot(d.normalized, fwd) > 0.6f && d.magnitude > 5f)
                {
                    best2 = d.magnitude;
                    targetYaw = Mathf.Atan2(d.x, d.z) * Mathf.Rad2Deg;
                }
            }
        }
        float diff = Mathf.DeltaAngle(truck.DisplayYaw, targetYaw);
        // Keyboard-style steering: full left, none or full right, like a human on WASD.
        input.steer = (sbyte)(diff > 4f ? 100 : diff < -4f ? -100 : 0);
        input.throttle = (sbyte)Mathf.RoundToInt(-40f + 40f * Mathf.Sin(t * 0.35f));
    }

    void Shoot(ref LocalInput input, PlayerAvatar me, Truck truck, float t)
    {
        Npc target = null;
        float bestD = 26f;
        foreach (Npc npc in GameManager.Instance.Npcs.All)
        {
            if (npc.Showing != Npc.Show.Walk)
            {
                continue;
            }
            float d = (npc.Pelvis - me.Muzzle.position).magnitude;
            if (d < bestD && d > 2.5f && truck.WorldToLocal(npc.Pelvis).x > 0f)
            {
                bestD = d;
                target = npc;
            }
        }
        if (target == null)
        {
            input.yaw = Mathf.MoveTowardsAngle(input.yaw, 90f, 180f * Time.deltaTime);
            input.pitch = Mathf.MoveTowards(input.pitch, 0f, 60f * Time.deltaTime);
            return;
        }
        // Aim in the truck frame: compensate for gravity and for the truck's own velocity.
        Vector3 to = target.Pelvis + target.DisplayVelocity * (bestD / 24f) - me.Muzzle.position;
        float flight = to.magnitude / 24f;
        to += Vector3.up * (0.5f * 9.81f * flight * flight);
        to -= truck.DisplayVelocity * flight;
        Vector3 local = Quaternion.Inverse(truck.DisplayRotation) * to;
        float yaw = Mathf.Atan2(local.x, local.z) * Mathf.Rad2Deg;
        float pitch = -Mathf.Atan2(local.y, new Vector2(local.x, local.z).magnitude) * Mathf.Rad2Deg;
        input.yaw = Mathf.MoveTowardsAngle(input.yaw, yaw, 360f * Time.deltaTime);
        input.pitch = Mathf.MoveTowards(input.pitch, pitch, 180f * Time.deltaTime);
        input.fire = Mathf.Abs(Mathf.DeltaAngle(input.yaw, yaw)) < 3f;
    }
}
