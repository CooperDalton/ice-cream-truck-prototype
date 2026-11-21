using System.Collections.Generic;
using PurrNet;
using PurrNet.Transports;
using UnityEngine;

public struct PlayerNetState
{
    public double time;
    public byte mode;
    public Vector3 local; // truck-local feet position (always, also when outside)
    public Vector3 world; // world feet position (outside only)
    public float yaw; // truck-local while inside/driving, world while outside
    public float pitch;
}

public struct ShotHitMessage
{
    public double time;
    public int shotId;
    public Vector3 point;
}

public struct ShotMessage
{
    public double time;
    public int shotId;
    public byte mode;
    public Vector3 worldOrigin;
    public Vector3 worldVelocity;
    public Vector3 localDir; // truck-local aim direction when fired from inside
}

// Owner-authoritative player. While inside, the player's CharacterController walks in a static
// copy of the truck interior (InteriorOrigin), so the moving truck never makes them slide or
// jitter; the visual is placed at truck pose * interior position. Remote players are sampled at
// RenderTime and composed with the same displayed truck, so passengers stay glued to it.
public class PlayerAvatar : NetworkBehaviour, ITick
{
    public enum Mode : byte { Inside, Outside, Driving }

    [SerializeField] CharacterController controller;
    [SerializeField] Humanoid body;
    [SerializeField] Transform gun;
    [SerializeField] Transform muzzle;
    [SerializeField] Renderer[] tinted;

    public const float FloorY = 0.75f;
    public const float EyeHeight = 1.55f;
    public static readonly Vector3 SeatLocal = new Vector3(-0.55f, FloorY, TruckSim.Length * 0.5f - 1.15f);
    public static readonly Vector3 SeatStandLocal = new Vector3(0.2f, FloorY, TruckSim.Length * 0.5f - 1.6f);
    const float WalkSpeed = 3.5f;
    const float RunSpeed = 9.5f;
    const float ShotSpeed = 24f;
    const float FireInterval = 0.4f;

    readonly SnapshotBuffer<PlayerNetState> buffer = new SnapshotBuffer<PlayerNetState>(64);
    readonly List<ShotMessage> pendingShots = new List<ShotMessage>();
    // Shots go out unreliable and are sent twice, a tick apart, by the shooter and again by the
    // server: a lost reliable packet would arrive a resend later and the shot would be late.
    readonly List<ShotMessage> resend = new List<ShotMessage>();
    readonly List<(ShotMessage shot, double at)> relayResend = new List<(ShotMessage, double)>();
    readonly HashSet<int> serverSeenShots = new HashSet<int>();
    readonly HashSet<int> clientSeenShots = new HashSet<int>();
    readonly List<ShotHitMessage> hitResend = new List<ShotHitMessage>();
    readonly List<(ShotHitMessage hit, double at)> relayHitResend = new List<(ShotHitMessage, double)>();
    readonly HashSet<int> serverSeenHits = new HashSet<int>();
    const double ResendDelay = 0.034;

    // Owner state
    Mode mode;
    Vector3 local;
    float verticalSpeed;
    Vector3 carried;
    float nextFire;
    int shotCounter;
    bool sentSeatRequest;
    readonly Vector3[] posePos = new Vector3[Humanoid.BoneCount];
    readonly Quaternion[] poseRot = new Quaternion[Humanoid.BoneCount];
    float walkPhase;
    Vector3 lastVisualPos;
    float boardAllowedAt;
    PlayerNetState lastSent;
    bool hasLastSent;

    // Seat, board and unboard move the drawn body by up to a metre; ease that out.
    const float TransitionTime = 0.25f;
    bool hasVisual;
    Mode lastVisualMode;
    Vector3 lastDrawnLocal;
    Vector3 transitionOffset;
    bool transitionInTruck;
    double transitionStart = -10;

    public Mode CurrentMode => mode;
    public Mode DisplayedMode { get; private set; }
    public Vector3 DisplayWorld { get; private set; }
    public Vector3 DisplayLocal { get; private set; }
    public float DisplayYawWorld { get; private set; }
    public Vector3 MuzzlePosition => muzzle.position;
    public bool MovingInput { get; private set; }
    public Transform Muzzle => muzzle;

    static Color[] colors = { new Color(0.2f, 0.5f, 1f), new Color(1f, 0.55f, 0.1f), new Color(0.3f, 0.85f, 0.3f), new Color(0.85f, 0.3f, 0.85f) };

    bool registered;
    public PlayerID OwnerId { get; private set; }

    // PlayerSpawner gives ownership right after spawning, so set up once the owner is known.
    protected override void OnOwnerChanged(PlayerID? oldOwner, PlayerID? newOwner, bool asServer)
    {
        if (registered || !newOwner.HasValue)
        {
            return;
        }
        registered = true;
        OwnerId = newOwner.Value;
        GameManager.Instance.RegisterAvatar(this);
        Color c = colors[(int)(newOwner.Value.id.value % (ulong)colors.Length)];
        foreach (Renderer r in tinted)
        {
            r.material.color = c;
        }
        body.SetSimulating(false);
        if (isOwner)
        {
            mode = Mode.Inside;
            int slot = (int)(newOwner.Value.id.value % 4);
            local = new Vector3(-0.5f + (slot % 2) * 1.0f, FloorY, -1.6f + (slot / 2) * 1.2f);
            SetInside(local);
            GameManager.Instance.Input.yaw = slot % 2 == 0 ? -90f : 90f;
        }
        else
        {
            controller.enabled = false;
        }
    }

    protected override void OnDespawned()
    {
        if (!registered)
        {
            return;
        }
        GameManager.Instance.UnregisterAvatar(this);
        if (isServer)
        {
            GameManager.Instance.Truck.ServerDriverLeft(OwnerId);
        }
    }

    void SetInside(Vector3 truckLocal)
    {
        controller.enabled = false;
        gameObject.layer = LayerMask.NameToLayer("InteriorPlayer");
        transform.position = GameManager.Instance.InteriorOrigin.position + truckLocal;
        controller.enabled = true;
        local = truckLocal;
    }

    void SetOutside(Vector3 world)
    {
        controller.enabled = false;
        gameObject.layer = LayerMask.NameToLayer("Player");
        transform.position = world;
        controller.enabled = true;
    }

    void Update()
    {
        if (!registered || !isOwner || !GameManager.Instance.ClockReady || !GameManager.Instance.Truck.Ready)
        {
            return;
        }
        Truck truck = GameManager.Instance.Truck;
        LocalInput input = GameManager.Instance.Input;
        float dt = Time.deltaTime;
        MovingInput = input.move.sqrMagnitude > 0.01f;

        if (mode == Mode.Inside && truck.LocalIsDriver)
        {
            mode = Mode.Driving;
            sentSeatRequest = false;
            local = SeatLocal;
            SetInside(local);
            GameManager.Instance.Log.Event("seat", "{}");
        }
        else if (mode == Mode.Driving && !truck.LocalIsDriver)
        {
            mode = Mode.Inside;
            SetInside(SeatStandLocal);
            GameManager.Instance.Log.Event("unseat", "{}");
        }

        if (input.interactPressed)
        {
            if (mode == Mode.Driving)
            {
                truck.LeaveSeat();
            }
            else if (mode == Mode.Inside && !truck.HasDriver && !sentSeatRequest && (local - SeatLocal).magnitude < 1.4f)
            {
                sentSeatRequest = true;
                truck.RequestSeat();
            }
        }

        if (mode == Mode.Inside)
        {
            UpdateInside(input, dt, truck);
        }
        else if (mode == Mode.Outside)
        {
            UpdateOutside(input, dt, truck);
        }

        if (input.fire && Time.time >= nextFire && mode != Mode.Driving)
        {
            nextFire = Time.time + FireInterval;
            // Place the visual first so the shot leaves the gun exactly where it is drawn.
            PlaceVisual();
            Fire(truck);
        }
    }

    void UpdateInside(LocalInput input, float dt, Truck truck)
    {
        Vector3 move = Quaternion.Euler(0f, input.yaw, 0f) * new Vector3(input.move.x, 0f, input.move.y);
        verticalSpeed = controller.isGrounded ? -1f : verticalSpeed - 20f * dt;
        if (input.jumpPressed && controller.isGrounded)
        {
            verticalSpeed = 5f;
        }
        controller.Move((move * WalkSpeed + Vector3.up * verticalSpeed) * dt);
        local = transform.position - GameManager.Instance.InteriorOrigin.position;

        // Walking out of the open rear door drops the player onto the road with the truck's speed.
        if (local.z < -TruckSim.Length * 0.5f - 0.15f)
        {
            Vector3 world = truck.LocalToWorld(local);
            carried = truck.DisplayVelocity + truck.DisplayRotation * (move * WalkSpeed);
            mode = Mode.Outside;
            boardAllowedAt = Time.time + 0.75f;
            GameManager.Instance.Input.yaw = input.yaw + truck.DisplayYaw;
            SetOutside(world);
            GameManager.Instance.Log.Event("unboard", "{}");
        }
    }

    void UpdateOutside(LocalInput input, float dt, Truck truck)
    {
        Vector3 move = Quaternion.Euler(0f, input.yaw, 0f) * new Vector3(input.move.x, 0f, input.move.y);
        float speed = input.sprint ? RunSpeed : WalkSpeed;
        verticalSpeed = controller.isGrounded ? -1f : verticalSpeed - 20f * dt;
        if (controller.isGrounded)
        {
            carried = Vector3.MoveTowards(carried, Vector3.zero, 14f * dt);
        }
        controller.Move((move * speed + carried + Vector3.up * verticalSpeed) * dt);

        Vector3 rel = truck.WorldToLocal(transform.position);
        // Running into the open rear door boards the truck. The zone reaches into the cargo
        // box so a player who drifted in during the hop-off cooldown still boards.
        if (Time.time >= boardAllowedAt && rel.z > -TruckSim.Length * 0.5f - 0.6f && rel.z < -TruckSim.Length * 0.5f + 1.5f && Mathf.Abs(rel.x) < 0.95f && rel.y < 1.6f)
        {
            mode = Mode.Inside;
            GameManager.Instance.Input.yaw = input.yaw - truck.DisplayYaw;
            // Land clear of the interior walls, or the controller depenetrates 10 cm next frame.
            float maxX = TruckSim.Width * 0.5f - 0.1f - controller.radius - 0.03f;
            SetInside(new Vector3(Mathf.Clamp(rel.x, -maxX, maxX), FloorY + 0.03f, Mathf.Max(rel.z, -TruckSim.Length * 0.5f + 0.5f)));
            GameManager.Instance.Log.Event("board", "{}");
            return;
        }

        // The truck is a moving solid box (cargo box plus hood): push the player out along the
        // shallowest side, softly. The player takes on the truck surface's speed, and any extra
        // overlap (running into a corner that is swinging round) resolves over a few frames
        // instead of one 25 cm pop.
        float hx = TruckSim.Width * 0.5f + 0.35f;
        float zMin = -TruckSim.Length * 0.5f - 0.35f;
        float zMax = TruckSim.Length * 0.5f + 1.05f;
        if (Mathf.Abs(rel.x) < hx && rel.z > zMin && rel.z < zMax && rel.y < 2.8f)
        {
            float px = hx - Mathf.Abs(rel.x);
            float pBack = rel.z - zMin;
            float pFront = zMax - rel.z;
            if (px < pBack && px < pFront)
            {
                rel.x = Mathf.Sign(rel.x) * hx;
            }
            else
            {
                rel.z = pBack < pFront ? zMin : zMax;
            }
            Vector3 correction = truck.LocalToWorld(rel) - transform.position;
            correction.y = 0f;
            float depth = correction.magnitude;
            Vector3 normal = correction / Mathf.Max(depth, 0.0001f);
            Vector3 arm = transform.position - truck.DisplayPosition;
            Vector3 surface = truck.DisplayVelocity + Vector3.Cross(Vector3.up * (truck.DisplayYawRate * Mathf.Deg2Rad), arm);
            float surfaceSpeed = Mathf.Max(0f, Vector3.Dot(surface, normal));
            carried += normal * Mathf.Max(0f, surfaceSpeed - Vector3.Dot(carried, normal));
            controller.enabled = false;
            transform.position += normal * Mathf.Min(depth, surfaceSpeed * dt + 0.02f);
            controller.enabled = true;
        }
    }

    void Fire(Truck truck)
    {
        LocalInput input = GameManager.Instance.Input;
        Quaternion aimLocal = Quaternion.Euler(input.pitch, input.yaw, 0f);
        Vector3 localDir = aimLocal * Vector3.forward;
        Vector3 worldDir;
        Vector3 inherited;
        if (mode == Mode.Outside)
        {
            worldDir = localDir;
            inherited = controller.velocity;
        }
        else
        {
            worldDir = truck.DisplayRotation * localDir;
            inherited = truck.DisplayVelocity;
        }
        var shot = new ShotMessage
        {
            time = GameManager.Instance.Now,
            shotId = (int)(OwnerId.id.value << 20) | shotCounter++,
            mode = (byte)mode,
            worldOrigin = muzzle.position,
            worldVelocity = worldDir * ShotSpeed + inherited,
            localDir = localDir,
        };
        Projectile p = Instantiate(GameManager.Instance.ProjectilePrefab);
        p.Launch(shot, true, muzzle.position, shot.worldVelocity, 0f);
        GameManager.Instance.Log.Event("fire", "{\"id\":" + shot.shotId + ",\"pos\":" + FrameLogger.V(muzzle.position) + "}");
        SendShot(shot);
        resend.Add(shot);
    }

    [ServerRpc(Channel.Unreliable)]
    void SendShot(ShotMessage shot, RPCInfo info = default)
    {
        if (!serverSeenShots.Add(shot.shotId))
        {
            return;
        }
        shot.time = GameManager.Instance.ServerStamp(info.sender, shot.time);
        RelayShot(shot);
        relayResend.Add((shot, GameManager.Instance.Now));
    }

    [ObserversRpc(Channel.Unreliable, excludeOwner: true)]
    void RelayShot(ShotMessage shot)
    {
        if (clientSeenShots.Add(shot.shotId))
        {
            pendingShots.Add(shot);
        }
    }

    // The shooter's hit point, so every cosmetic copy splats where the real shot landed. Sent
    // like shots (unreliable, twice): it has to arrive before the timeline reaches it.
    public void ReportShotHit(int shotId, Vector3 point)
    {
        var hit = new ShotHitMessage { time = GameManager.Instance.Now, shotId = shotId, point = point };
        SendShotHit(hit);
        hitResend.Add(hit);
    }

    [ServerRpc(Channel.Unreliable)]
    void SendShotHit(ShotHitMessage hit, RPCInfo info = default)
    {
        if (!serverSeenHits.Add(hit.shotId))
        {
            return;
        }
        hit.time = GameManager.Instance.ServerStamp(info.sender, hit.time);
        RelayShotHit(hit);
        relayHitResend.Add((hit, GameManager.Instance.Now));
    }

    [ObserversRpc(Channel.Unreliable, excludeOwner: true)]
    void RelayShotHit(ShotHitMessage hit)
    {
        if (Projectile.Cosmetic.TryGetValue(hit.shotId, out Projectile p))
        {
            p.ScheduleSplat(hit.point, hit.time);
        }
    }

    public void OnTick(float delta)
    {
        double now = GameManager.Instance.Now;
        for (int i = relayHitResend.Count - 1; i >= 0; i--)
        {
            if (now - relayHitResend[i].at >= ResendDelay)
            {
                RelayShotHit(relayHitResend[i].hit);
                relayHitResend.RemoveAt(i);
            }
        }
        for (int i = relayResend.Count - 1; i >= 0; i--)
        {
            if (now - relayResend[i].at >= ResendDelay)
            {
                RelayShot(relayResend[i].shot);
                relayResend.RemoveAt(i);
            }
        }
        if (!registered || !isOwner)
        {
            return;
        }
        for (int i = resend.Count - 1; i >= 0; i--)
        {
            if (now - resend[i].time >= ResendDelay)
            {
                SendShot(resend[i]);
                resend.RemoveAt(i);
            }
        }
        for (int i = hitResend.Count - 1; i >= 0; i--)
        {
            if (now - hitResend[i].time >= ResendDelay)
            {
                SendShotHit(hitResend[i]);
                hitResend.RemoveAt(i);
            }
        }
        Truck truck = GameManager.Instance.Truck;
        if (!truck.Ready || !GameManager.Instance.ClockReady)
        {
            return;
        }
        var state = new PlayerNetState
        {
            time = GameManager.Instance.Now,
            mode = (byte)mode,
            local = mode == Mode.Outside ? truck.WorldToLocal(transform.position) : local,
            world = mode == Mode.Outside ? transform.position : Vector3.zero,
            yaw = GameManager.Instance.Input.yaw,
            pitch = GameManager.Instance.Input.pitch,
        };
        // Each packet repeats the previous state: this stream crosses two lossy hops (owner to
        // host to observer), and one lost packet otherwise leaves a hole in the timeline.
        SendState(state, hasLastSent ? lastSent : state);
        lastSent = state;
        hasLastSent = true;
    }

    [ServerRpc(Channel.Unreliable)]
    void SendState(PlayerNetState state, PlayerNetState previous, RPCInfo info = default)
    {
        state.time = GameManager.Instance.ServerStamp(info.sender, state.time);
        previous.time = GameManager.Instance.ServerStampNoObserve(info.sender, previous.time);
        if (!isOwner)
        {
            GameManager.Instance.NoteArrival(state.time);
            buffer.Add(previous.time, previous);
            buffer.Add(state.time, state);
        }
        RelayState(state, previous);
    }

    [ObserversRpc(Channel.Unreliable, excludeOwner: true)]
    void RelayState(PlayerNetState state, PlayerNetState previous)
    {
        if (isServer)
        {
            return;
        }
        GameManager.Instance.NoteArrival(state.time);
        buffer.Add(previous.time, previous);
        buffer.Add(state.time, state);
    }

    // Outside players near the truck are shown relative to the truck, far ones relative to the
    // world. Owners place themselves against the truck they see, which is a different moment of
    // the truck's path than observers draw, so pure world positions put a runner next to the
    // truck metres off on other screens and snap them when they board.
    public static float TruckFrameWeight(Vector3 local)
    {
        float dx = Mathf.Max(0f, Mathf.Abs(local.x) - TruckSim.Width * 0.5f);
        float dz = Mathf.Max(0f, Mathf.Abs(local.z) - TruckSim.Length * 0.5f);
        float d = Mathf.Sqrt(dx * dx + dz * dz);
        return GameManager.UseTruckFrameForOutside ? 1f - Mathf.Clamp01((d - 3f) / 6f) : 0f;
    }

    Vector3 StateWorld(PlayerNetState s, Truck truck, out float yawWorld)
    {
        if (s.mode == (byte)Mode.Outside)
        {
            yawWorld = s.yaw;
            float w = TruckFrameWeight(s.local);
            return Vector3.Lerp(s.world, truck.LocalToWorld(s.local), w);
        }
        yawWorld = s.yaw + truck.DisplayYaw;
        return truck.LocalToWorld(s.local);
    }

    void LateUpdate()
    {
        if (!registered || !GameManager.Instance.ClockReady || !GameManager.Instance.Truck.Ready)
        {
            return;
        }
        if (isOwner)
        {
            PlaceVisual();
            PlaceCamera();
            return;
        }
        if (buffer.Count == 0)
        {
            return;
        }
        Truck truck = GameManager.Instance.Truck;
        double renderTime = GameManager.Instance.RenderTime;
        buffer.Sample(renderTime, out PlayerNetState a, out PlayerNetState b, out float t);
        if (t > 1f)
        {
            // Briefly run on along the last motion instead of freezing and then jumping.
            GameManager.Instance.Log.Underrun("player", t);
            t = Mathf.Min(t, 2.5f);
        }
        if (a.mode != b.mode)
        {
            // A mode change is a jump in the truck frame (step up into the door, sit down);
            // interpolating across it squeezes the jump into one send interval. Hold the old
            // sample and let the transition ease handle the jump when the bracket moves on.
            b = a;
            t = 0f;
        }
        Vector3 wa = StateWorld(a, truck, out float ya);
        Vector3 wb = StateWorld(b, truck, out float yb);
        Vector3 world = Vector3.LerpUnclamped(wa, wb, t);
        float yaw = ya + Mathf.DeltaAngle(ya, yb) * t;
        float pitch = Mathf.Lerp(a.pitch, b.pitch, t);
        DisplayedMode = (Mode)a.mode;
        DisplayLocal = Vector3.Lerp(a.local, b.local, t);
        SetVisual(world, yaw, pitch);

        for (int i = pendingShots.Count - 1; i >= 0; i--)
        {
            ShotMessage shot = pendingShots[i];
            if (shot.time > renderTime)
            {
                continue;
            }
            pendingShots.RemoveAt(i);
            // The shot leaves this avatar's gun as drawn here, with the velocity of the truck
            // as drawn here, then converges onto the shooter's own trajectory.
            Vector3 velocity = shot.mode == (byte)Mode.Outside
                ? shot.worldVelocity
                : truck.DisplayRotation * shot.localDir * ShotSpeed + truck.DisplayVelocity;
            // A shot that reached us after its moment starts part-way along, so it still lands
            // in step with the ragdoll it causes.
            float late = (float)(renderTime - shot.time);
            Projectile p = Instantiate(GameManager.Instance.ProjectilePrefab);
            p.Launch(shot, false, muzzle.position, velocity, late > 0.02f ? late : 0f);
            GameManager.Instance.Log.Event("shot_seen", "{\"id\":" + shot.shotId + ",\"pos\":" + FrameLogger.V(muzzle.position) + ",\"late\":" + FrameLogger.F((float)(renderTime - shot.time)) + "}");
        }
    }

    void PlaceVisual()
    {
        Truck truck = GameManager.Instance.Truck;
        LocalInput input = GameManager.Instance.Input;
        Vector3 world;
        float yawWorld;
        if (mode == Mode.Outside)
        {
            world = transform.position;
            yawWorld = input.yaw;
            DisplayLocal = truck.WorldToLocal(world);
        }
        else
        {
            world = truck.LocalToWorld(local);
            yawWorld = input.yaw + truck.DisplayYaw;
            DisplayLocal = local;
        }
        DisplayedMode = mode;
        SetVisual(world, yawWorld, input.pitch);
    }

    void SetVisual(Vector3 world, float yawWorld, float pitch)
    {
        Truck truck = GameManager.Instance.Truck;
        if (hasVisual && DisplayedMode != lastVisualMode)
        {
            transitionInTruck = DisplayedMode != Mode.Outside;
            transitionOffset = transitionInTruck
                ? lastDrawnLocal - truck.WorldToLocal(world)
                : truck.LocalToWorld(lastDrawnLocal) - world;
            transitionStart = GameManager.Instance.Now;
            GameManager.Instance.Log.Event("transition", "{\"id\":" + OwnerId.id.value + ",\"to\":" + (int)DisplayedMode + ",\"gap\":" + FrameLogger.F(transitionOffset.magnitude) + "}");
        }
        hasVisual = true;
        lastVisualMode = DisplayedMode;
        float u = Mathf.Clamp01((float)((GameManager.Instance.Now - transitionStart) / TransitionTime));
        float k = 1f - u * u * (3f - 2f * u);
        world += transitionInTruck ? truck.DisplayRotation * (transitionOffset * k) : transitionOffset * k;
        lastDrawnLocal = truck.WorldToLocal(world);
        DisplayLocal = lastDrawnLocal;
        Vector3 rel = DisplayedMode == Mode.Outside ? world : truck.WorldToLocal(world);
        float moved = (rel - lastVisualPos).magnitude;
        lastVisualPos = rel;
        float stride = Mathf.Clamp01(moved / Mathf.Max(Time.deltaTime, 0.001f) / WalkSpeed);
        walkPhase += moved * 4.2f;
        if (DisplayedMode == Mode.Driving)
        {
            stride = 0f;
        }
        body.StandPose(world, yawWorld, walkPhase, stride, posePos, poseRot);
        body.Apply(posePos, poseRot);
        // Gun follows the look direction.
        gun.SetPositionAndRotation(posePos[1] + Quaternion.Euler(0f, yawWorld, 0f) * new Vector3(0.28f, 0.32f, 0.2f), Quaternion.Euler(pitch, yawWorld, 0f));
        DisplayWorld = world;
        DisplayYawWorld = yawWorld;
    }

    void PlaceCamera()
    {
        Camera cam = GameManager.Instance.MainCamera;
        LocalInput input = GameManager.Instance.Input;
        Truck truck = GameManager.Instance.Truck;
        if (GameManager.OverheadCamera)
        {
            Vector3 target = truck.LocalToWorld(new Vector3(0f, 1f, 1f));
            cam.transform.position = truck.LocalToWorld(new Vector3(-7f, 13f, -9f));
            cam.transform.rotation = Quaternion.LookRotation(target - cam.transform.position, Vector3.up);
            return;
        }
        Quaternion look = mode == Mode.Outside
            ? Quaternion.Euler(input.pitch, input.yaw, 0f)
            : truck.DisplayRotation * Quaternion.Euler(input.pitch, input.yaw, 0f);
        cam.transform.SetPositionAndRotation(DisplayWorld + Vector3.up * EyeHeight, look);
    }
}
