using System.Collections.Generic;
using PurrNet;
using PurrNet.Transports;
using UnityEngine;

public struct TruckSnapshot
{
    public double time;
    public TruckState state;
    public bool hasDriver;
    public PlayerID driver;
    public int driverEpoch;
    public int ack;
}

// Server-authoritative truck. The host simulates it from the driver's input stream; the
// driving client predicts it with the same TruckSim code and reconciles against acked
// snapshots; everyone else shows it interpolated at RenderTime.
[DefaultExecutionOrder(-400)]
public class Truck : NetworkBehaviour, ITick
{
    public enum DisplayMode { Interpolated, Predicted, HostSim }

    [SerializeField] Rigidbody body;
    [SerializeField] Transform[] frontWheels;
    [SerializeField] GameObject[] roofParts;

    // Visual offset smoothing. Critically damped and velocity-continuous, so a correction that
    // lands while an earlier one (or the seat-change gap) is still easing out never jolts.
    public const float OffsetSmoothTime = 0.35f;
    const int InputRedundancy = 6;
    const int TargetInputBuffer = 2;

    readonly SnapshotBuffer<TruckSnapshot> buffer = new SnapshotBuffer<TruckSnapshot>(128);

    // Server
    TruckState serverState;
    PlayerID? serverDriver;
    int serverEpoch;
    readonly List<TruckInput> inputQueue = new List<TruckInput>();
    int lastQueuedSeq = -1;
    int ack = -1;
    bool primed;
    TruckInput lastInput;
    public int StarvedSteps { get; private set; }

    // Every machine's view of who drives
    bool hasDriver;
    PlayerID driver;
    int driverEpoch;

    // Driving client
    bool predicting;
    TruckState predicted;
    int nextSeq;
    readonly List<(int seq, TruckInput input, TruckState after)> history = new List<(int, TruckInput, TruckState)>();
    readonly List<TruckInput> sendWindow = new List<TruckInput>();

    Vector3 offsetPos;
    float offsetYaw;
    Vector3 offsetVel;
    float offsetYawVel;
    DisplayMode lastMode;
    bool hasDisplayed;
    Vector3 lastDisplayVelocity;
    float lastDisplayYawRate;

    public DisplayMode Mode { get; private set; }
    public Vector3 DisplayPosition { get; private set; }
    public Quaternion DisplayRotation { get; private set; }
    public float DisplayYaw { get; private set; }
    public Vector3 DisplayVelocity { get; private set; }
    public float DisplaySteer { get; private set; }
    public float DisplayYawRate => lastDisplayYawRate;
    public bool DisplayCrashing { get; private set; }
    public bool Ready => isServer || buffer.Count > 0;
    public bool HasDriver => hasDriver;
    public PlayerID Driver => driver;
    public bool LocalIsDriver => hasDriver && GameManager.Instance.LocalPlayer == driver;
    public TruckState ServerState => serverState;
    public double LastCorrection { get; private set; }

    void Awake()
    {
        foreach (GameObject part in roofParts)
        {
            part.SetActive(!GameManager.OverheadCamera);
        }
    }

    protected override void OnSpawned(bool asServer)
    {
        if (asServer)
        {
            serverState = new TruckState
            {
                pos = new Vector2(TownLayout.RoadCenter(1), TownLayout.RoadCenter(0)),
                yaw = 90f,
                speed = TruckSim.CruiseSpeed,
            };
        }
    }

    // ---- Seat ----

    [ServerRpc(requireOwnership: false)]
    public void RequestSeat(RPCInfo info = default)
    {
        if (serverDriver.HasValue)
        {
            return;
        }
        SetDriver(info.sender);
    }

    [ServerRpc(requireOwnership: false)]
    public void LeaveSeat(RPCInfo info = default)
    {
        if (serverDriver.HasValue && serverDriver.Value == info.sender)
        {
            SetDriver(null);
        }
    }

    public void ServerDriverLeft(PlayerID player)
    {
        if (serverDriver.HasValue && serverDriver.Value == player)
        {
            SetDriver(null);
        }
    }

    void SetDriver(PlayerID? player)
    {
        serverDriver = player;
        serverEpoch++;
        inputQueue.Clear();
        lastQueuedSeq = -1;
        ack = -1;
        primed = false;
        lastInput = default;
        DriverChanged(player.HasValue, player ?? default, serverEpoch);
    }

    [ObserversRpc]
    void DriverChanged(bool has, PlayerID player, int epoch)
    {
        hasDriver = has;
        driver = player;
        driverEpoch = epoch;
        bool shouldPredict = has && player == GameManager.Instance.LocalPlayer && !isServer;
        if (shouldPredict && !predicting)
        {
            // The host coasts with neutral input until our first input reaches it (one round
            // trip plus its input buffer). Coast our copy just as far so our input 0 lands on
            // the same state, otherwise the first ack corrects us by about a metre.
            TruckSnapshot newest = buffer.Newest;
            double firstInputAt = GameManager.Instance.LatestServerTime + networkManager.tickModule.rtt + TargetInputBuffer * Time.fixedDeltaTime;
            int coastSteps = Mathf.Max(0, Mathf.RoundToInt((float)((firstInputAt - newest.time) / Time.fixedDeltaTime)));
            predicted = newest.state;
            for (int i = 0; i < coastSteps; i++)
            {
                predicted = TruckSim.Step(predicted, default, Time.fixedDeltaTime);
            }
            nextSeq = 0;
            history.Clear();
            sendWindow.Clear();
        }
        predicting = shouldPredict;
        GameManager.Instance.Log.Event("driver", "{\"has\":" + (has ? 1 : 0) + ",\"id\":" + player.id + ",\"epoch\":" + epoch + "}");
    }

    // ---- Input ----

    [ServerRpc(Channel.Unreliable, requireOwnership: false)]
    void SendInputs(int epoch, TruckInput[] inputs, RPCInfo info = default)
    {
        if (!serverDriver.HasValue || serverDriver.Value != info.sender || epoch != serverEpoch)
        {
            return;
        }
        foreach (TruckInput input in inputs)
        {
            if (input.seq > lastQueuedSeq)
            {
                inputQueue.Add(input);
                lastQueuedSeq = input.seq;
            }
        }
    }

    TruckInput NextServerInput()
    {
        if (!serverDriver.HasValue)
        {
            return default;
        }
        if (serverDriver.Value == GameManager.Instance.LocalPlayer)
        {
            return LocalInput();
        }
        if (!primed)
        {
            if (inputQueue.Count < TargetInputBuffer)
            {
                return lastInput;
            }
            primed = true;
        }
        if (inputQueue.Count == 0)
        {
            StarvedSteps++;
            return lastInput;
        }
        // Drain one extra input when the buffer grows, so input latency stays bounded.
        if (inputQueue.Count > TargetInputBuffer + 2)
        {
            inputQueue.RemoveAt(0);
        }
        lastInput = inputQueue[0];
        inputQueue.RemoveAt(0);
        ack = lastInput.seq;
        return lastInput;
    }

    TruckInput LocalInput()
    {
        LocalInput input = GameManager.Instance.Input;
        return new TruckInput { seq = nextSeq++, steer = input.steer, throttle = input.throttle };
    }

    void FixedUpdate()
    {
        if (!isSpawned)
        {
            return;
        }
        float dt = Time.fixedDeltaTime;
        if (isServer)
        {
            serverState = TruckSim.Step(serverState, NextServerInput(), dt);
            buffer.Add(Time.timeAsDouble, MakeSnapshot(Time.timeAsDouble));
        }
        else if (predicting)
        {
            TruckInput input = LocalInput();
            predicted = TruckSim.Step(predicted, input, dt);
            history.Add((input.seq, input, predicted));
            sendWindow.Add(input);
            if (sendWindow.Count > InputRedundancy)
            {
                sendWindow.RemoveAt(0);
            }
            SendInputs(driverEpoch, sendWindow.ToArray());
        }

        if (Ready && GameManager.Instance.ClockReady)
        {
            TruckState s = Pose(GameManager.Instance.LatestServerTimeAt(Time.timeAsDouble) - GameManager.Instance.InterpDelay, 0f);
            Vector3 pos = new Vector3(s.pos.x, 0f, s.pos.y) + offsetPos;
            float yaw = s.yaw + offsetYaw;
            body.MovePosition(pos);
            body.MoveRotation(Quaternion.Euler(0f, yaw, 0f));
            if (LocalDecidesRunOvers)
            {
                GameManager.Instance.Npcs.CheckRunOvers(pos, yaw, Forward3(yaw) * s.speed);
            }
        }
    }

    // The machine that sees the truck in the present decides run-overs: the driver, or the
    // host when it drives or nobody does.
    bool LocalDecidesRunOvers => predicting || (isServer && (!serverDriver.HasValue || serverDriver.Value == GameManager.Instance.LocalPlayer));

    TruckSnapshot MakeSnapshot(double time)
    {
        return new TruckSnapshot
        {
            time = time,
            state = serverState,
            hasDriver = serverDriver.HasValue,
            driver = serverDriver ?? default,
            driverEpoch = serverEpoch,
            ack = ack,
        };
    }

    public void OnTick(float delta)
    {
        if (isServer)
        {
            ReceiveSnapshot(MakeSnapshot(Time.timeAsDouble));
        }
    }

    [ObserversRpc(Channel.Unreliable)]
    void ReceiveSnapshot(TruckSnapshot snap)
    {
        if (isServer)
        {
            return;
        }
        GameManager.Instance.ObserveServerTime(snap.time);
        GameManager.Instance.NoteArrival(snap.time);
        buffer.Add(snap.time, snap);
        if (predicting && snap.driverEpoch == driverEpoch && snap.ack >= 0)
        {
            Reconcile(snap.ack, snap.state);
        }
    }

    void Reconcile(int ackSeq, TruckState server)
    {
        int index = history.FindIndex(h => h.seq == ackSeq);
        if (index < 0)
        {
            return;
        }
        TruckState mine = history[index].after;
        float error = (mine.pos - server.pos).magnitude + Mathf.Abs(Mathf.DeltaAngle(mine.yaw, server.yaw)) * 0.05f
            + Mathf.Abs(mine.speed - server.speed) * 0.1f;
        history.RemoveRange(0, index + 1);
        if (error < 0.0005f)
        {
            return;
        }
        TruckState s = server;
        for (int i = 0; i < history.Count; i++)
        {
            s = TruckSim.Step(s, history[i].input, Time.fixedDeltaTime);
            history[i] = (history[i].seq, history[i].input, s);
        }
        Vector2 shift = predicted.pos - s.pos;
        float yawShift = Mathf.DeltaAngle(s.yaw, predicted.yaw);
        offsetPos += new Vector3(shift.x, 0f, shift.y);
        offsetYaw += yawShift;
        predicted = s;
        LastCorrection = shift.magnitude;
        GameManager.Instance.Log.Event("correction", "{\"dist\":" + FrameLogger.F(shift.magnitude) + ",\"yaw\":" + FrameLogger.F(yawShift) + "}");
    }

    // Truck state to draw. Locally simulated modes add the partial step since the last fixed
    // update using the input the next step will use, so steering shows the same frame.
    TruckState Pose(double renderTime, float partial)
    {
        if (predicting)
        {
            Mode = DisplayMode.Predicted;
            return partial > 0f ? TruckSim.Step(predicted, PreviewInput(), partial) : predicted;
        }
        if (isServer && serverDriver.HasValue && serverDriver.Value == GameManager.Instance.LocalPlayer)
        {
            Mode = DisplayMode.HostSim;
            return partial > 0f ? TruckSim.Step(serverState, PreviewInput(), partial) : serverState;
        }
        Mode = DisplayMode.Interpolated;
        buffer.Sample(renderTime, out TruckSnapshot sa, out TruckSnapshot sb, out float t);
        if (t > 1f)
        {
            GameManager.Instance.Log.Underrun("truck", t);
            t = Mathf.Min(t, 2f);
        }
        TruckState a = sa.state;
        TruckState b = sb.state;
        return new TruckState
        {
            pos = Vector2.LerpUnclamped(a.pos, b.pos, t),
            yaw = a.yaw + Mathf.DeltaAngle(a.yaw, b.yaw) * t,
            speed = Mathf.Lerp(a.speed, b.speed, t),
            steer = Mathf.Lerp(a.steer, b.steer, t),
            crashTimer = Mathf.Max(a.crashTimer, b.crashTimer),
        };
    }

    TruckInput PreviewInput()
    {
        LocalInput input = GameManager.Instance.Input;
        return new TruckInput { seq = nextSeq, steer = input.steer, throttle = input.throttle };
    }

    void Update()
    {
        if (!isSpawned || !Ready || !GameManager.Instance.ClockReady)
        {
            return;
        }
        float partial = Mathf.Max(0f, (float)(Time.timeAsDouble - Time.fixedTimeAsDouble));
        TruckState s = Pose(GameManager.Instance.RenderTime, partial);
        Vector3 pos = new Vector3(s.pos.x, 0f, s.pos.y);
        if (hasDisplayed && Mode != lastMode)
        {
            // Switching between predicted (present) and interpolated (past) views moves the
            // truck by its speed times the time gap; ease it out instead of snapping.
            // Continue last frame's motion so the switch frame does not stall.
            offsetPos = DisplayPosition + lastDisplayVelocity * Time.deltaTime - pos;
            offsetYaw = Mathf.DeltaAngle(s.yaw, DisplayYaw + lastDisplayYawRate * Time.deltaTime);
            GameManager.Instance.Log.Event("truck_mode", "{\"mode\":" + (int)Mode + ",\"gap\":" + FrameLogger.F(offsetPos.magnitude) + "}");
        }
        lastMode = Mode;
        hasDisplayed = true;
        offsetPos = Vector3.SmoothDamp(offsetPos, Vector3.zero, ref offsetVel, OffsetSmoothTime);
        offsetYaw = Mathf.SmoothDamp(offsetYaw, 0f, ref offsetYawVel, OffsetSmoothTime);
        float newYaw = s.yaw + offsetYaw;
        Vector3 newPos = pos + offsetPos;
        float frameDt = Mathf.Max(Time.deltaTime, 0.0001f);
        lastDisplayVelocity = (newPos - DisplayPosition) / frameDt;
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
