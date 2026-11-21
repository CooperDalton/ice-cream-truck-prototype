using System.Collections.Generic;
using PurrNet;
using PurrNet.Prediction;
using UnityEngine;

public struct PlayerInput : IPredictedData
{
    public sbyte moveX; // -100..100
    public sbyte moveY;
    public float yaw; // look yaw: truck-relative while inside, world while outside
    public float pitch;
    public bool sprint;
    // Presses are counted, not flagged: the host repeats the last input when one is missing,
    // and a repeated flag would press again (the seat toggled on and off).
    public byte interactPresses;
    public byte jumpPresses;

    public void Dispose() { }
}

public struct PlayerSimState : IPredictedData<PlayerSimState>
{
    public byte mode;
    public Vector3 local; // truck-local feet position (always, also when outside)
    public Vector3 world; // world feet position (outside only)
    public float yaw; // truck-local while inside/driving, world while outside
    public float pitch;
    public float verticalSpeed;
    public Vector3 carried;
    public float boardCooldown;
    public byte interactSeen;
    public byte jumpSeen;

    public void Dispose() { }
}

public struct ShotHitMessage
{
    public double time;
    public int shotId;
    public PlayerID shooter;
    public Vector3 point;
}

public struct ShotMessage
{
    public double time;
    public int shotId;
    public PlayerID shooter;
    public byte mode;
    public Vector3 worldOrigin;
    public Vector3 worldVelocity;
    public Vector3 localDir; // truck-local aim direction when fired from inside
}

// Server-authoritative player on PurrDiction, predicted by its owner. While inside, the
// CharacterController walks in a static copy of the truck interior (InteriorOrigin), so the
// moving truck never makes them slide or jitter; the visual is placed at drawn truck pose *
// interior position. Remote players are drawn from host-confirmed states at RenderTime and
// composed with the same drawn truck, so passengers stay glued to it.
public class PlayerAvatar : PredictedIdentity<PlayerInput, PlayerSimState>
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

    // Host-confirmed states keyed by tick number.
    readonly SnapshotBuffer<PlayerSimState> confirmed = new SnapshotBuffer<PlayerSimState>(64);
    ulong lastConfirmedTick;
    ulong lastFrameTick;
    // Owner: its own predictions keyed by tick, replaced when a replay changes them.
    readonly SnapshotBuffer<PlayerSimState> predicted = new SnapshotBuffer<PlayerSimState>(128);
    // Owner: a replay that moves the drawn player is eased out. Truck-relative and world
    // positions are corrected separately: a runner next to the truck is drawn relative to it,
    // and a corrected truck prediction moves that relative position.
    const float CorrectionSmoothTime = 0.2f;
    PlayerSimState beforeRollback;
    Vector3 localCorrection;
    Vector3 localCorrectionVel;
    Vector3 worldCorrection;
    Vector3 worldCorrectionVel;
    bool hasOwnSample;
    public readonly List<ShotMessage> PendingShots = new List<ShotMessage>();

    float nextFire;
    int shotCounter;
    byte interactPresses;
    byte jumpPresses;
    readonly Vector3[] posePos = new Vector3[Humanoid.BoneCount];
    readonly Quaternion[] poseRot = new Quaternion[Humanoid.BoneCount];
    float walkPhase;
    Vector3 lastVisualPos;
    Mode lastPredictedMode;

    // Seat, board and unboard move the drawn body by up to a metre; ease that out.
    const float TransitionTime = 0.25f;
    bool hasVisual;
    Mode lastVisualMode;
    Vector3 lastDrawnLocal;
    Vector3 transitionOffset;
    bool transitionInTruck;
    double transitionStart = -10;

    public Mode CurrentMode => (Mode)currentState.mode;
    // The owner learns it owns this player from a server frame, a tick before it predicts it.
    bool HasOwnPrediction => predictionManager.isServer ? confirmed.Count > 0 : predicted.Count > 0;
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

    // ---- Simulation (host and owner) ----

    protected override void SimulationStart()
    {
        int slot = (int)(owner.Value.id.value % 4);
        ref PlayerSimState s = ref currentState;
        s.mode = (byte)Mode.Inside;
        s.local = new Vector3(-0.5f + (slot % 2) * 1.0f, FloorY, -1.6f + (slot / 2) * 1.2f);
        s.yaw = slot % 2 == 0 ? -90f : 90f;
        SetUnityState(s);
    }

    protected override void GetFinalInput(ref PlayerInput input)
    {
        LocalInput local = GameManager.Instance.Input;
        input.moveX = (sbyte)Mathf.RoundToInt(Mathf.Clamp(local.move.x, -1f, 1f) * 100f);
        input.moveY = (sbyte)Mathf.RoundToInt(Mathf.Clamp(local.move.y, -1f, 1f) * 100f);
        input.yaw = local.yaw;
        input.pitch = local.pitch;
        input.sprint = local.sprint;
        input.interactPresses = interactPresses;
        input.jumpPresses = jumpPresses;
    }

    // Every frame: button presses between two ticks must not be lost.
    protected override void UpdateInput(ref PlayerInput input)
    {
        if (GameManager.Instance.Input.interactPressed)
        {
            interactPresses++;
        }
        if (GameManager.Instance.Input.jumpPressed)
        {
            jumpPresses++;
        }
    }

    // A count ahead of the last one seen is a new press. A repeated input carries the same
    // count, and a default input (none received yet) counts behind, so neither presses.
    static bool Pressed(byte presses, ref byte seen)
    {
        byte ahead = (byte)(presses - seen);
        if (ahead == 0 || ahead >= 128)
        {
            return false;
        }
        seen = presses;
        return true;
    }

    protected override void SetUnityState(PlayerSimState s)
    {
        controller.enabled = false;
        if (s.mode == (byte)Mode.Outside)
        {
            gameObject.layer = LayerMask.NameToLayer("Player");
            transform.position = s.world;
        }
        else
        {
            gameObject.layer = LayerMask.NameToLayer("InteriorPlayer");
            transform.position = GameManager.Instance.InteriorOrigin.position + s.local;
        }
        controller.enabled = true;
    }

    protected override void GetUnityState(ref PlayerSimState s)
    {
        if (s.mode == (byte)Mode.Outside)
        {
            s.world = transform.position;
        }
        else
        {
            s.local = transform.position - GameManager.Instance.InteriorOrigin.position;
        }
    }

    protected override void Simulate(PlayerInput input, ref PlayerSimState s, float dt)
    {
        Truck truck = GameManager.Instance.Truck;
        bool interact = Pressed(input.interactPresses, ref s.interactSeen);
        bool jump = Pressed(input.jumpPresses, ref s.jumpSeen);
        s.yaw = input.yaw;
        s.pitch = input.pitch;
        s.boardCooldown = Mathf.Max(0f, s.boardCooldown - dt);
        Vector3 move = Quaternion.Euler(0f, input.yaw, 0f) * new Vector3(input.moveX / 100f, 0f, input.moveY / 100f);

        if (s.mode == (byte)Mode.Driving)
        {
            bool stillDriving = truck.IsOwner(owner.Value);
            if (interact || !stillDriving)
            {
                if (stillDriving)
                {
                    predictionManager.SetOwnership(truck.rootObjectId, null);
                }
                s.mode = (byte)Mode.Inside;
                s.local = SeatStandLocal;
                SetUnityState(s);
            }
            return;
        }
        if (s.mode == (byte)Mode.Inside)
        {
            if (interact && !truck.owner.HasValue && (s.local - SeatLocal).magnitude < 1.4f)
            {
                predictionManager.SetOwnership(truck.rootObjectId, owner);
                s.mode = (byte)Mode.Driving;
                s.local = SeatLocal;
                SetUnityState(s);
                return;
            }
            SimulateInside(jump, ref s, move, dt, truck.currentState);
            return;
        }
        SimulateOutside(input, ref s, move, dt, truck.currentState);
    }

    void SimulateInside(bool jump, ref PlayerSimState s, Vector3 move, float dt, TruckState truck)
    {
        s.verticalSpeed = controller.isGrounded ? -1f : s.verticalSpeed - 20f * dt;
        if (jump && controller.isGrounded)
        {
            s.verticalSpeed = 5f;
        }
        controller.Move((move * WalkSpeed + Vector3.up * s.verticalSpeed) * dt);
        s.local = transform.position - GameManager.Instance.InteriorOrigin.position;

        // Walking out of the open rear door drops the player onto the road with the truck's speed.
        if (s.local.z < -TruckSim.Length * 0.5f - 0.15f)
        {
            Quaternion truckRot = Quaternion.Euler(0f, truck.yaw, 0f);
            s.world = new Vector3(truck.pos.x, 0f, truck.pos.y) + truckRot * s.local;
            s.carried = Truck.Forward3(truck.yaw) * truck.speed + truckRot * (move * WalkSpeed);
            s.mode = (byte)Mode.Outside;
            s.boardCooldown = 0.75f;
            SetUnityState(s);
        }
    }

    void SimulateOutside(PlayerInput input, ref PlayerSimState s, Vector3 move, float dt, TruckState truck)
    {
        Vector3 truckPos = new Vector3(truck.pos.x, 0f, truck.pos.y);
        Quaternion truckRot = Quaternion.Euler(0f, truck.yaw, 0f);
        Quaternion toLocal = Quaternion.Inverse(truckRot);
        float speed = input.sprint ? RunSpeed : WalkSpeed;
        s.verticalSpeed = controller.isGrounded ? -1f : s.verticalSpeed - 20f * dt;
        if (controller.isGrounded)
        {
            s.carried = Vector3.MoveTowards(s.carried, Vector3.zero, 14f * dt);
        }
        controller.Move((move * speed + s.carried + Vector3.up * s.verticalSpeed) * dt);

        Vector3 rel = toLocal * (transform.position - truckPos);
        // Running into the open rear door boards the truck. The zone reaches into the cargo
        // box so a player who drifted in during the hop-off cooldown still boards.
        if (s.boardCooldown <= 0f && rel.z > -TruckSim.Length * 0.5f - 0.6f && rel.z < -TruckSim.Length * 0.5f + 1.5f && Mathf.Abs(rel.x) < 0.95f && rel.y < 1.6f)
        {
            // Land clear of the interior walls, or the controller depenetrates 10 cm next tick.
            float maxX = TruckSim.Width * 0.5f - 0.1f - controller.radius - 0.03f;
            s.mode = (byte)Mode.Inside;
            s.local = new Vector3(Mathf.Clamp(rel.x, -maxX, maxX), FloorY + 0.03f, Mathf.Max(rel.z, -TruckSim.Length * 0.5f + 0.5f));
            SetUnityState(s);
            return;
        }

        // The truck is a moving solid box (cargo box plus hood): push the player out along the
        // shallowest side, softly. The player takes on the truck surface's speed, and any extra
        // overlap (running into a corner that is swinging round) resolves over a few ticks
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
            Vector3 correction = truckPos + truckRot * rel - transform.position;
            correction.y = 0f;
            float depth = correction.magnitude;
            Vector3 normal = correction / Mathf.Max(depth, 0.0001f);
            float yawRate = truck.speed * Mathf.Tan(truck.steer * Mathf.Deg2Rad) / TruckSim.Wheelbase;
            Vector3 surface = Truck.Forward3(truck.yaw) * truck.speed + Vector3.Cross(Vector3.up * yawRate, transform.position - truckPos);
            float surfaceSpeed = Mathf.Max(0f, Vector3.Dot(surface, normal));
            s.carried += normal * Mathf.Max(0f, surfaceSpeed - Vector3.Dot(s.carried, normal));
            controller.enabled = false;
            transform.position += normal * Mathf.Min(depth, surfaceSpeed * dt + 0.02f);
            controller.enabled = true;
        }
        s.world = transform.position;
        s.local = toLocal * (s.world - truckPos);
    }

    // Host: keep confirmed states for drawing remote players at RenderTime. Owner: keep its
    // predictions. The state after tick T is labelled T + 1, as PurrDiction does.
    public override void PostSimulate()
    {
        ulong label = predictionManager.localTickInContext + 1;
        if (predictionManager.isServer)
        {
            confirmed.Add(label, currentState);
        }
        else if (isOwner)
        {
            predicted.Put(label, currentState);
        }
    }

    protected override void LateAwake()
    {
        predictionManager.onStartingToRollback += OnStartingToRollback;
        predictionManager.onRollbackFinished += OnRollbackFinished;
    }

    void OnStartingToRollback()
    {
        if (hasOwnSample)
        {
            beforeRollback = SampleOwn();
        }
    }

    void OnRollbackFinished()
    {
        if (!hasOwnSample)
        {
            return;
        }
        PlayerSimState after = SampleOwn();
        if (after.mode != beforeRollback.mode)
        {
            return;
        }
        Vector3 localShift = beforeRollback.local - after.local;
        Vector3 worldShift = after.mode == (byte)Mode.Outside ? beforeRollback.world - after.world : Vector3.zero;
        if (localShift.sqrMagnitude < 1e-8f && worldShift.sqrMagnitude < 1e-8f)
        {
            return;
        }
        localCorrection += localShift;
        worldCorrection += worldShift;
        GameManager.Instance.Log.Event("player_correction", "{\"mode\":" + after.mode + ",\"local\":" + FrameLogger.F(localShift.magnitude) + ",\"dist\":" + FrameLogger.F(worldShift.magnitude) + "}");
    }

    // The owner's newest prediction, between the last two ticks by how far the network clock is
    // into the next one (as the truck's driver view: PurrDiction's view tick stalls and jumps
    // when PurrNet adjusts the client's tick pace).
    PlayerSimState SampleOwn()
    {
        double tick = predictionManager.localTick - 1 + GameManager.Instance.Network.tickModule.floatingPoint;
        SnapshotBuffer<PlayerSimState> source = predictionManager.isServer ? confirmed : predicted;
        source.Sample(tick, out PlayerSimState a, out PlayerSimState b, out float t);
        return Interpolate(a, b, Mathf.Min(t, 1f));
    }

    // ---- View ----

    // PurrDiction's view sample between two ticks. Across a mode change hold the earlier tick:
    // the jump is eased by SetVisual's transition instead.
    protected override PlayerSimState Interpolate(PlayerSimState from, PlayerSimState to, float t)
    {
        if (from.mode != to.mode)
        {
            return t < 1f ? from : to;
        }
        from.local = Vector3.Lerp(from.local, to.local, t);
        from.world = Vector3.Lerp(from.world, to.world, t);
        from.yaw += Mathf.DeltaAngle(from.yaw, to.yaw) * t;
        from.pitch = Mathf.Lerp(from.pitch, to.pitch, t);
        return from;
    }

    // Spawning gives ownership right after creating, so set up once the owner is known.
    public override void OnViewOwnerChanged(PlayerID? oldOwner, PlayerID? newOwner)
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
            int slot = (int)(newOwner.Value.id.value % 4);
            GameManager.Instance.Input.yaw = slot % 2 == 0 ? -90f : 90f;
            lastPredictedMode = CurrentMode;
        }
    }

    protected override void OnDestroy()
    {
        base.OnDestroy();
        predictionManager.onStartingToRollback -= OnStartingToRollback;
        predictionManager.onRollbackFinished -= OnRollbackFinished;
        if (registered)
        {
            GameManager.Instance.UnregisterAvatar(this);
        }
    }

    protected override void Update()
    {
        base.Update();
        if (!registered || !GameManager.Instance.ClockReady || !GameManager.Instance.Truck.Ready)
        {
            return;
        }
        if (!isOwner)
        {
            if (!predictionManager.isServer)
            {
                PollConfirmed();
            }
            return;
        }
        if (!HasOwnPrediction)
        {
            return;
        }
        GameManager gm = GameManager.Instance;
        Truck truck = gm.Truck;
        MovingInput = gm.Input.move.sqrMagnitude > 0.01f;

        // Look yaw is in the frame the player is in; convert it when the prediction changes frame.
        Mode predictedMode = CurrentMode;
        if (predictedMode != lastPredictedMode)
        {
            float truckYaw = truck.currentState.yaw;
            if (lastPredictedMode == Mode.Outside)
            {
                gm.Input.yaw -= truckYaw;
            }
            else if (predictedMode == Mode.Outside)
            {
                gm.Input.yaw += truckYaw;
            }
            gm.Log.Event(predictedMode == Mode.Driving ? "seat" : lastPredictedMode == Mode.Driving ? "unseat" : predictedMode == Mode.Outside ? "unboard" : "board", "{}");
            lastPredictedMode = predictedMode;
        }

        if (gm.Input.fire && Time.time >= nextFire && predictedMode != Mode.Driving)
        {
            nextFire = Time.time + FireInterval;
            // Place the visual first so the shot leaves the gun exactly where it is drawn.
            PlaceOwnVisual();
            Fire(truck);
        }
    }

    // Each confirmed state at the tick PurrDiction stored it for. A state that did not change
    // is not sent or stored again, so lastFrameTick (the newest applied server frame) says how
    // long the newest one is known to hold.
    void PollConfirmed()
    {
        ulong frameTick = predictionManager.verifiedServerTick;
        if (TryGetLatestVerifiedState(out ulong tick, out PlayerSimState state) && tick > lastConfirmedTick)
        {
            // The previous state held through the previous frame. Without this sample a player
            // who stood still and starts walking would be drawn creeping over the whole idle time.
            if (confirmed.Count > 0 && lastFrameTick > lastConfirmedTick && lastFrameTick < tick)
            {
                confirmed.Add(lastFrameTick, confirmed.Newest);
            }
            lastConfirmedTick = tick;
            confirmed.Add(tick, state);
        }
        lastFrameTick = frameTick;
    }

    void Fire(Truck truck)
    {
        LocalInput input = GameManager.Instance.Input;
        Quaternion aimLocal = Quaternion.Euler(input.pitch, input.yaw, 0f);
        Vector3 localDir = aimLocal * Vector3.forward;
        Vector3 worldDir;
        Vector3 inherited;
        Mode mode = CurrentMode;
        if (mode == Mode.Outside)
        {
            worldDir = localDir;
            inherited = currentState.carried;
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
            shooter = OwnerId,
            mode = (byte)mode,
            worldOrigin = muzzle.position,
            worldVelocity = worldDir * ShotSpeed + inherited,
            localDir = localDir,
        };
        Projectile p = Instantiate(GameManager.Instance.ProjectilePrefab);
        p.Launch(shot, true, muzzle.position, shot.worldVelocity, 0f);
        GameManager.Instance.Log.Event("fire", "{\"id\":" + shot.shotId + ",\"pos\":" + FrameLogger.V(muzzle.position) + "}");
        GameManager.Instance.Shots.Fire(shot);
    }

    // Outside players near the truck are shown relative to the truck, far ones relative to the
    // world. A player's state is placed against the truck at the same tick, which is a different
    // moment of the truck's path than the one this screen draws, so pure world positions put a
    // runner next to the truck metres off and snap them when they board.
    public static float TruckFrameWeight(Vector3 local)
    {
        float dx = Mathf.Max(0f, Mathf.Abs(local.x) - TruckSim.Width * 0.5f);
        float dz = Mathf.Max(0f, Mathf.Abs(local.z) - TruckSim.Length * 0.5f);
        float d = Mathf.Sqrt(dx * dx + dz * dz);
        return GameManager.UseTruckFrameForOutside ? 1f - Mathf.Clamp01((d - 3f) / 6f) : 0f;
    }

    Vector3 StateWorld(PlayerSimState s, Truck truck, out float yawWorld)
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
            if (HasOwnPrediction)
            {
                PlaceOwnVisual();
                PlaceCamera();
            }
            return;
        }
        if (confirmed.Count == 0)
        {
            return;
        }
        Truck truck = GameManager.Instance.Truck;
        double renderTime = GameManager.Instance.RenderTime;
        double renderTick = GameManager.Instance.TickAt(renderTime);
        confirmed.Sample(renderTick, out PlayerSimState a, out PlayerSimState b, out float t);
        if (t > 1f && (predictionManager.isServer || lastConfirmedTick < lastFrameTick))
        {
            // Unchanged since the newest stored state: hold it.
            t = 1f;
        }
        else if (t > 1f)
        {
            // Briefly run on along the last motion instead of freezing and then jumping.
            GameManager.Instance.Log.Underrun("player", t);
            t = Mathf.Min(t, 2.5f);
        }
        if (a.mode != b.mode)
        {
            // A mode change is a jump in the truck frame (step up into the door, sit down);
            // interpolating across it squeezes the jump into one sample interval. Hold the old
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
        SetVisual(world, yaw, pitch);

        for (int i = PendingShots.Count - 1; i >= 0; i--)
        {
            ShotMessage shot = PendingShots[i];
            if (shot.time > renderTime)
            {
                continue;
            }
            PendingShots.RemoveAt(i);
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
            GameManager.Instance.Log.Event("shot_seen", "{\"id\":" + shot.shotId + ",\"pos\":" + FrameLogger.V(muzzle.position) + ",\"late\":" + FrameLogger.F(late) + "}");
        }
    }

    // The owner draws its own prediction. Look direction comes straight from the mouse, in the
    // frame of the predicted mode.
    void PlaceOwnVisual()
    {
        Truck truck = GameManager.Instance.Truck;
        LocalInput input = GameManager.Instance.Input;
        PlayerSimState v = SampleOwn();
        hasOwnSample = true;
        if (v.mode != (byte)DisplayedMode)
        {
            localCorrection = Vector3.zero;
            localCorrectionVel = Vector3.zero;
            worldCorrection = Vector3.zero;
            worldCorrectionVel = Vector3.zero;
        }
        localCorrection = Vector3.SmoothDamp(localCorrection, Vector3.zero, ref localCorrectionVel, CorrectionSmoothTime);
        worldCorrection = Vector3.SmoothDamp(worldCorrection, Vector3.zero, ref worldCorrectionVel, CorrectionSmoothTime);
        DisplayedMode = (Mode)v.mode;
        Vector3 local = v.local + localCorrection;
        Vector3 world = v.mode == (byte)Mode.Outside
            ? Vector3.Lerp(v.world + worldCorrection, truck.LocalToWorld(local), TruckFrameWeight(local))
            : truck.LocalToWorld(local);
        float yawWorld = CurrentMode == Mode.Outside ? input.yaw : input.yaw + truck.DisplayYaw;
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
        Quaternion look = CurrentMode == Mode.Outside
            ? Quaternion.Euler(input.pitch, input.yaw, 0f)
            : truck.DisplayRotation * Quaternion.Euler(input.pitch, input.yaw, 0f);
        cam.transform.SetPositionAndRotation(DisplayWorld + Vector3.up * EyeHeight, look);
    }
}
