using System;
using PurrNet;
using PurrNet.Prediction;
using UnityEngine;

// The truck runs on PurrDiction. The host simulates it, the driver (the identity's owner)
// predicts it from its own input, and every other client predicts it too with the driver's
// last known input, so players running next to it collide with the present truck.
// What a screen draws is separate from what it simulates. Passengers draw the host's confirmed
// states at RenderTime, on the shared timeline with players, NPCs and shots. The driver draws
// its own prediction. Taking or leaving the wheel moves the drawn moment between the two by
// running the drawn truck up to CatchUpRate faster or slower than real time, so it never jumps.
[DefaultExecutionOrder(-400)]
public class Truck : PredictedIdentity<TruckInput, TruckState>
{
    public enum DisplayMode { Interpolated, Predicted, HostSim, CatchUp }

    [SerializeField] Rigidbody body;
    [SerializeField] Transform[] frontWheels;
    [SerializeField] GameObject[] roofParts;

    // Visual offset smoothing for prediction corrections. Critically damped and
    // velocity-continuous, so a correction landing while another is easing out never jolts.
    public const float OffsetSmoothTime = 0.35f;
    // How much faster or slower than real time the drawn truck may run while it moves between
    // the shared past (passengers) and the predicted present (driver).
    const double CatchUpRate = 0.15;

    // Both buffers are keyed by tick number (exact), not by time.
    // Host-confirmed states (the host adds its own every tick).
    readonly SnapshotBuffer<TruckState> confirmed = new SnapshotBuffer<TruckState>(256);
    // This machine's predictions, replaced whenever a replay changes them.
    readonly SnapshotBuffer<TruckState> predicted = new SnapshotBuffer<TruckState>(256);
    ulong lastConfirmedTick;

    // The drawn moment, in (fractional) ticks.
    double displayTick;
    bool hasDisplayed;
    Vector3 offsetPos;
    float offsetYaw;
    Vector3 offsetVel;
    float offsetYawVel;
    TruckState beforeRollback;
    float lastDisplayYawRate;

    public DisplayMode Mode { get; private set; }
    public Vector3 DisplayPosition { get; private set; }
    public Quaternion DisplayRotation { get; private set; }
    public float DisplayYaw { get; private set; }
    public Vector3 DisplayVelocity { get; private set; }
    public float DisplaySteer { get; private set; }
    public float DisplayYawRate => lastDisplayYawRate;
    public bool DisplayCrashing { get; private set; }
    public bool Ready => confirmed.Count > 0;
    public bool HasDriver => owner.HasValue;
    public bool LocalIsDriver => isOwner;
    public TruckState ServerState => currentState;

    void Awake()
    {
        foreach (GameObject part in roofParts)
        {
            part.SetActive(!GameManager.OverheadCamera);
        }
    }

    protected override void LateAwake()
    {
        predictionManager.onStartingToRollback += OnStartingToRollback;
        predictionManager.onRollbackFinished += OnRollbackFinished;
    }

    protected override void OnDestroy()
    {
        base.OnDestroy();
        predictionManager.onStartingToRollback -= OnStartingToRollback;
        predictionManager.onRollbackFinished -= OnRollbackFinished;
    }

    protected override TruckState GetInitialState()
    {
        return new TruckState
        {
            pos = new Vector2(TownLayout.RoadCenter(1), TownLayout.RoadCenter(0)),
            yaw = 90f,
            speed = TruckSim.CruiseSpeed,
        };
    }

    protected override void GetFinalInput(ref TruckInput input)
    {
        input.steer = GameManager.Instance.Input.steer;
        input.throttle = GameManager.Instance.Input.throttle;
    }

    protected override void Simulate(TruckInput input, ref TruckState state, float delta)
    {
        state = TruckSim.Step(state, input, delta);
    }

    public override void PostSimulate()
    {
        GameManager gm = GameManager.Instance;
        // The state after simulating tick T is the state at the start of T + 1, which is how
        // PurrDiction labels verified states and the view tick.
        ulong tick = predictionManager.localTickInContext;
        if (predictionManager.isServer)
        {
            gm.NoteServerTick(tick);
            confirmed.Add(tick + 1, currentState);
        }
        else
        {
            predicted.Put(tick + 1, currentState);
        }
    }

    public override void OnViewOwnerChanged(PlayerID? oldOwner, PlayerID? newOwner)
    {
        GameManager.Instance.Log.Event("driver", "{\"has\":" + (newOwner.HasValue ? 1 : 0) + ",\"id\":" + (newOwner.HasValue ? newOwner.Value.id.value : 0) + "}");
    }

    // A replay can change the predicted states the driver is drawing. Keep the drawn truck
    // where it was and ease the difference out.
    void OnStartingToRollback()
    {
        if (hasDisplayed)
        {
            beforeRollback = Sample(displayTick);
        }
    }

    void OnRollbackFinished()
    {
        if (!hasDisplayed)
        {
            return;
        }
        TruckState after = Sample(displayTick);
        Vector2 shift = beforeRollback.pos - after.pos;
        float yawShift = Mathf.DeltaAngle(after.yaw, beforeRollback.yaw);
        if (shift.sqrMagnitude < 1e-8f && Mathf.Abs(yawShift) < 1e-4f)
        {
            return;
        }
        offsetPos += new Vector3(shift.x, 0f, shift.y);
        offsetYaw += yawShift;
        GameManager.Instance.Log.Event("correction", "{\"dist\":" + FrameLogger.F(shift.magnitude) + ",\"yaw\":" + FrameLogger.F(yawShift) + "}");
    }

    // Clients read the confirmed state at each newly applied server frame. PurrDiction stores a
    // verified state only when it changed, so the frame's tick is the one to stamp it with.
    void PollConfirmed()
    {
        ulong tick = predictionManager.verifiedServerTick;
        if (tick <= lastConfirmedTick || !TryGetLatestVerifiedState(out _, out TruckState state))
        {
            return;
        }
        lastConfirmedTick = tick;
        GameManager gm = GameManager.Instance;
        double time = gm.TickTime(tick);
        gm.ObserveServerTime(time);
        gm.NoteArrival(time);
        confirmed.Add(tick, state);
    }

    TruckState Sample(double tick)
    {
        bool usePredicted = !predictionManager.isServer && predicted.Count > 1 && tick > confirmed.NewestTime;
        SnapshotBuffer<TruckState> source = usePredicted ? predicted : confirmed;
        source.Sample(tick, out TruckState a, out TruckState b, out float t);
        if (t > 1f)
        {
            GameManager.Instance.Log.Underrun(usePredicted ? "truck_predicted" : "truck", t);
            t = Mathf.Min(t, 2f);
        }
        return new TruckState
        {
            pos = Vector2.LerpUnclamped(a.pos, b.pos, t),
            yaw = a.yaw + Mathf.DeltaAngle(a.yaw, b.yaw) * t,
            speed = Mathf.Lerp(a.speed, b.speed, t),
            steer = Mathf.Lerp(a.steer, b.steer, t),
            crashTimer = Mathf.Max(a.crashTimer, b.crashTimer),
        };
    }

    protected override void Update()
    {
        base.Update();
        // predictionManager is set when the network spawns it, after the scene starts.
        if (predictionManager && !predictionManager.isServer && GameManager.Instance.ClockReady)
        {
            PollConfirmed();
        }
    }

    // After PredictionManager's Update, so the view tick is this frame's.
    void LateUpdate()
    {
        GameManager gm = GameManager.Instance;
        if (!Ready || !gm.ClockReady)
        {
            return;
        }
        // The driver draws its newest prediction, between the last two ticks by how far the
        // network clock is into the next one. PurrNet paces the client's ticks smoothly to keep
        // the prediction lead, so this moves evenly (PurrDiction's own view tick holds and then
        // jumps a tick when the pacing changes).
        bool driving = isOwner;
        int rate = predictionManager.tickRate;
        double target = driving
            ? predictionManager.localTick - 1 + gm.Network.tickModule.floatingPoint
            : gm.TickAt(gm.RenderTime);
        if (!hasDisplayed)
        {
            displayTick = target;
        }
        else
        {
            displayTick += Time.deltaTime * rate;
            double step = CatchUpRate * Time.deltaTime * rate;
            displayTick += Math.Clamp(target - displayTick, -step, step);
        }
        bool caughtUp = Math.Abs(target - displayTick) < 0.002 * rate;
        DisplayMode mode = !caughtUp ? DisplayMode.CatchUp : !driving ? DisplayMode.Interpolated : predictionManager.isServer ? DisplayMode.HostSim : DisplayMode.Predicted;
        if (hasDisplayed && mode != Mode)
        {
            gm.Log.Event("truck_mode", "{\"mode\":" + (int)mode + ",\"gap\":" + FrameLogger.F((float)((target - displayTick) / rate)) + "}");
        }
        Mode = mode;

        TruckState s = Sample(displayTick);
        hasDisplayed = true;
        offsetPos = Vector3.SmoothDamp(offsetPos, Vector3.zero, ref offsetVel, OffsetSmoothTime);
        offsetYaw = Mathf.SmoothDamp(offsetYaw, 0f, ref offsetYawVel, OffsetSmoothTime);
        float newYaw = s.yaw + offsetYaw;
        Vector3 newPos = new Vector3(s.pos.x, 0f, s.pos.y) + offsetPos;
        float frameDt = Mathf.Max(Time.deltaTime, 0.0001f);
        lastDisplayYawRate = Mathf.DeltaAngle(DisplayYaw, newYaw) / frameDt;
        DisplayYaw = newYaw;
        DisplayPosition = newPos;
        DisplayRotation = Quaternion.Euler(0f, DisplayYaw, 0f);
        DisplayVelocity = Forward3(s.yaw) * s.speed;
        DisplaySteer = s.steer;
        DisplayCrashing = s.crashTimer > 0f;
        transform.SetPositionAndRotation(DisplayPosition, DisplayRotation);
        foreach (Transform wheel in frontWheels)
        {
            wheel.localRotation = Quaternion.Euler(0f, s.steer, 0f);
        }
        // The machine that draws the truck in the present decides run-overs: the driver, or the
        // host when nobody drives.
        if (driving || predictionManager.isServer && !owner.HasValue)
        {
            gm.Npcs.CheckRunOvers(DisplayPosition, DisplayYaw, DisplayVelocity);
        }
    }

    // Collision body for ragdolls, at the drawn truck.
    void FixedUpdate()
    {
        if (hasDisplayed)
        {
            body.MovePosition(DisplayPosition);
            body.MoveRotation(DisplayRotation);
        }
    }

    public static Vector3 Forward3(float yaw)
    {
        Vector2 f = TruckSim.Forward(yaw);
        return new Vector3(f.x, 0f, f.y);
    }

    public Vector3 LocalToWorld(Vector3 local)
    {
        return DisplayPosition + DisplayRotation * local;
    }

    public Vector3 WorldToLocal(Vector3 world)
    {
        return Quaternion.Inverse(DisplayRotation) * (world - DisplayPosition);
    }
}
