using System;
using System.Collections.Generic;
using PurrNet;
using PurrNet.Prediction;
using PurrNet.Transports;
using UnityEngine;

public struct LocalInput
{
    public Vector2 move;
    public float yaw; // look yaw: truck-relative while inside, world while outside
    public float pitch;
    public bool sprint;
    public bool fire;
    public bool interactPressed;
    public bool jumpPressed;
    public sbyte steer;
    public sbyte throttle;
}

// Owns startup, the shared clock and the registry of players. Every remote thing a machine
// shows is sampled at RenderTime, one timeline for the truck, players, NPCs and shots.
[DefaultExecutionOrder(-500)]
public class GameManager : MonoBehaviour
{
    public static GameManager Instance { get; private set; }

    // Remote data is shown InterpDelay behind the newest server time we could have. The delay
    // adapts to how late samples actually arrive (jitter on one or two hops, resends), so a
    // good connection stays responsive and a bad one stays smooth. One delay for everything
    // keeps the truck, players, NPCs and shots on one coherent timeline.
    public double InterpDelay { get; private set; } = 0.11;
    const double MinDelay = 0.08;
    const double MaxDelay = 0.35;
    // Grow fast (5% slow-motion) when samples arrive late, shrink slowly (1% fast-forward) and
    // only after a long calm window, so the delay does not drop just before the next burst.
    const double DelayGrow = 0.05;
    const double DelayShrink = 0.01;
    const double LatenessWindow = 10.0;
    readonly Queue<(double at, double lateness)> arrivals = new Queue<(double, double)>();

    // A/B switch for the soak tests: -worldOutside syncs outside players in world space only.
    public static readonly bool UseTruckFrameForOutside = !HasArg("-worldOutside");
    // Captures use a camera above the truck with the roof hidden, so sync problems are visible.
    public static readonly bool OverheadCamera = HasArg("-capture") || HasArg("-overhead");

    [SerializeField] NetworkManager network;
    [SerializeField] UDPTransport udp;
    [SerializeField] PredictionManager prediction;
    [SerializeField] ShotRelay shots;
    [SerializeField] Truck truck;
    [SerializeField] NpcManager npcs;
    [SerializeField] Transform interiorOrigin;
    [SerializeField] Camera mainCamera;
    [SerializeField] FrameLogger frameLogger;
    [SerializeField] BotBrain botBrain;
    [SerializeField] Projectile projectilePrefab;

    public Truck Truck => truck;
    public NpcManager Npcs => npcs;
    public Transform InteriorOrigin => interiorOrigin;
    public Camera MainCamera => mainCamera;
    public FrameLogger Log => frameLogger;
    public Projectile ProjectilePrefab => projectilePrefab;
    public NetworkManager Network => network;
    public ShotRelay Shots => shots;

    public bool IsServer => network.isServer;
    public PlayerID LocalPlayer => network.localPlayer;
    public PlayerAvatar LocalAvatar { get; private set; }
    public readonly Dictionary<PlayerID, PlayerAvatar> Avatars = new Dictionary<PlayerID, PlayerAvatar>();

    public LocalInput Input;
    public string Bot { get; private set; } = "";
    public string InstanceName { get; private set; } = "player";
    public int Seed { get; private set; } = 1;
    public double Duration { get; private set; } = 0;
    public double StartTime { get; private set; }

    readonly ClockMapper serverClock = new ClockMapper();
    readonly Dictionary<PlayerID, ClockMapper> ownerClocks = new Dictionary<PlayerID, ClockMapper>();

    // Newest server time whose data could have reached us (server: now).
    public double LatestServerTime { get; private set; }
    public double RenderTime { get; private set; }
    public double Now => Time.timeAsDouble;

    // PurrDiction tick numbers are the same on every machine. Tick T happened at server time
    // T / tickRate + TickOffset; the host measures the offset and sends it with NPC snapshots.
    public double TickOffset { get; private set; }
    public bool TickOffsetKnown { get; private set; }

    public event EventHandler<AvatarEventArgs> AvatarAdded;

    public class AvatarEventArgs : EventArgs
    {
        public PlayerAvatar Avatar;
    }

    void Awake()
    {
        Instance = this;
        Application.targetFrameRate = 60;
        QualitySettings.vSyncCount = 0;
        AudioListener.volume = 0f;

        int world = LayerMask.NameToLayer("World");
        int truckLayer = LayerMask.NameToLayer("Truck");
        int interior = LayerMask.NameToLayer("Interior");
        int interiorPlayer = LayerMask.NameToLayer("InteriorPlayer");
        int ragdoll = LayerMask.NameToLayer("Ragdoll");
        int player = LayerMask.NameToLayer("Player");
        for (int i = 0; i < 32; i++)
        {
            Physics.IgnoreLayerCollision(interior, i, i != interiorPlayer);
            Physics.IgnoreLayerCollision(interiorPlayer, i, i != interior);
        }
        Physics.IgnoreLayerCollision(player, ragdoll, true);
        Physics.IgnoreLayerCollision(player, player, true);
        Physics.IgnoreLayerCollision(world, world, true);
        Physics.IgnoreLayerCollision(truckLayer, world, true);
        // CharacterController depenetration from a moving kinematic box pops the player up to
        // 20 cm in a frame; PlayerAvatar pushes players out of the truck itself instead.
        Physics.IgnoreLayerCollision(player, truckLayer, true);

        string role = Arg("-role", "");
        Bot = Arg("-bot", "");
        InstanceName = Arg("-name", role == "" ? "player" : role);
        Seed = int.Parse(Arg("-seed", "1"));
        Duration = double.Parse(Arg("-duration", "0"), System.Globalization.CultureInfo.InvariantCulture);
        udp.serverPort = ushort.Parse(Arg("-port", "7777"));
        udp.address = Arg("-address", "127.0.0.1");
        botBrain.enabled = Bot != "";
    }

    void Start()
    {
        // The transport sets itself up in its own Awake, so start the network here.
        string role = Arg("-role", "");
        if (role == "host")
        {
            network.StartHost();
        }
        else if (role == "client")
        {
            network.StartClient();
        }
        StartTime = Now;
        if (Arg("-out", "") != "")
        {
            frameLogger.Open(Arg("-out", ""));
        }
    }

    public static string Arg(string name, string fallback)
    {
        string[] args = Environment.GetCommandLineArgs();
        for (int i = 0; i < args.Length - 1; i++)
        {
            if (args[i] == name)
            {
                return args[i + 1];
            }
        }
        return fallback;
    }

    public static bool HasArg(string name)
    {
        return Array.IndexOf(Environment.GetCommandLineArgs(), name) >= 0;
    }

    public void ObserveServerTime(double serverTime)
    {
        if (!IsServer)
        {
            serverClock.Observe(serverTime, Now);
        }
    }

    // Server: maps a timestamp from an owner's clock onto the server timeline. All data one
    // owner sends (its state, shots, ragdoll frames) shares this mapping, so it stays in sync.
    public double ServerStamp(PlayerID owner, double ownerTime)
    {
        if (!ownerClocks.TryGetValue(owner, out ClockMapper mapper))
        {
            mapper = new ClockMapper();
            ownerClocks[owner] = mapper;
        }
        mapper.Observe(ownerTime, Now);
        return mapper.ToLocal(ownerTime);
    }

    // For redundant copies: they arrive with the next packet, so observing their delay would
    // only add a late sample to the clock filter.
    public double ServerStampNoObserve(PlayerID owner, double ownerTime)
    {
        return ownerClocks[owner].ToLocal(ownerTime);
    }

    public double TickTime(double tick)
    {
        return tick / prediction.tickRate + TickOffset;
    }

    // Host, while simulating tick: PurrNet runs ticks on a fixed schedule (lastTickTime, in
    // unscaled time), so the tick's moment on our clock is exact, not the frame it ran in.
    public void NoteServerTick(ulong tick)
    {
        double tickMoment = Now - (Time.unscaledTimeAsDouble - network.tickModule.lastTickTime);
        TickOffset = tickMoment - (double)tick / prediction.tickRate;
        TickOffsetKnown = true;
    }

    public double TickAt(double serverTime)
    {
        return (serverTime - TickOffset) * prediction.tickRate;
    }

    public void SetTickOffset(double offset)
    {
        TickOffset = offset;
        TickOffsetKnown = true;
    }

    public double LatestServerTimeAt(double localTime)
    {
        if (IsServer)
        {
            return localTime;
        }
        return serverClock.ToRemote(localTime);
    }

    public bool ClockReady => (IsServer || serverClock.Initialized) && TickOffsetKnown;

    // Every timeline sample from the network reports how far behind the newest server time it
    // arrived. The render delay must exceed the worst recent lateness plus one send interval.
    public void NoteArrival(double sampleTime)
    {
        if (ClockReady)
        {
            arrivals.Enqueue((Now, LatestServerTimeAt(Now) - sampleTime));
        }
    }

    void AdaptDelay()
    {
        while (arrivals.Count > 0 && arrivals.Peek().at < Now - LatenessWindow)
        {
            arrivals.Dequeue();
        }
        double worst = 0;
        foreach (var a in arrivals)
        {
            worst = Math.Max(worst, a.lateness);
        }
        double target = Math.Min(MaxDelay, Math.Max(MinDelay, worst + 1.0 / 30.0 + 0.015));
        InterpDelay += Math.Max(-DelayShrink * Time.deltaTime, Math.Min(DelayGrow * Time.deltaTime, target - InterpDelay));
    }

    void Update()
    {
        if (Duration > 0 && Now - StartTime > Duration)
        {
            frameLogger.Close();
            Application.Quit();
        }
        if (!ClockReady)
        {
            return;
        }
        LatestServerTime = LatestServerTimeAt(Now);
        AdaptDelay();
        RenderTime = LatestServerTime - InterpDelay;
        if (Bot == "")
        {
            ReadHumanInput();
        }
    }

    void ReadHumanInput()
    {
        Input.move = new Vector2(UnityEngine.Input.GetAxisRaw("Horizontal"), UnityEngine.Input.GetAxisRaw("Vertical"));
        Input.yaw += UnityEngine.Input.GetAxis("Mouse X") * 2.5f;
        Input.pitch = Mathf.Clamp(Input.pitch - UnityEngine.Input.GetAxis("Mouse Y") * 2.5f, -80f, 80f);
        Input.sprint = UnityEngine.Input.GetKey(KeyCode.LeftShift);
        Input.fire = UnityEngine.Input.GetMouseButton(0);
        Input.interactPressed = UnityEngine.Input.GetKeyDown(KeyCode.E);
        Input.jumpPressed = UnityEngine.Input.GetKeyDown(KeyCode.Space);
        Input.steer = (sbyte)(Mathf.RoundToInt(Input.move.x) * 100);
        Input.throttle = (sbyte)(Mathf.RoundToInt(Input.move.y) * 100);
        if (UnityEngine.Input.GetMouseButtonDown(0))
        {
            Cursor.lockState = CursorLockMode.Locked;
        }
    }

    public void RegisterAvatar(PlayerAvatar avatar)
    {
        Avatars[avatar.OwnerId] = avatar;
        if (avatar.isOwner)
        {
            LocalAvatar = avatar;
        }
        AvatarAdded?.Invoke(this, new AvatarEventArgs { Avatar = avatar });
    }

    public void UnregisterAvatar(PlayerAvatar avatar)
    {
        Avatars.Remove(avatar.OwnerId);
    }

    void OnGUI()
    {
        if (Bot != "")
        {
            return;
        }
        if (!network.isServer && !network.isClient)
        {
            GUILayout.BeginArea(new Rect(20, 20, 260, 200));
            GUILayout.Label("Ice Cream Truck netcode demo");
            if (GUILayout.Button("Host (port " + udp.serverPort + ")"))
            {
                network.StartHost();
            }
            udp.address = GUILayout.TextField(udp.address);
            if (GUILayout.Button("Join"))
            {
                network.StartClient();
            }
            GUILayout.EndArea();
            return;
        }
        GUILayout.Label("WASD move/steer, mouse look, LMB shoot, E seat/board, Shift sprint");
        GUILayout.Label("RTT " + (network.tickModule.rtt * 1000).ToString("0") + " ms, render delay " + (InterpDelay * 1000).ToString("0") + " ms");
    }
}
