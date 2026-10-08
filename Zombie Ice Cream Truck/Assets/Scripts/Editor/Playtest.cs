using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using Quantum;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.InputSystem.LowLevel;

// Headless play-test bot. Plays the gameplay scene through virtual keyboard and mouse devices (so the real input path
// is exercised), captures the full frame (game plus HUD) at marked steps, records frame sequences for GIFs, and logs
// the simulation state, then exits.
// Run: Unity -batchmode -projectPath <project> -executeMethod Playtest.Run -logFile <log>   (no -quit)
// PLAYTEST_SCENARIO: drive (default), kitchen, showcase (two players, roof shooting, run-overs, a crash), depot
// (auto-drives area 1 to the depot, buys an upgrade, rolls out).
public static class Playtest
{
    const string ScenePath = "Assets/QuantumUser/Scenes/QuantumGameScene.unity";
    static readonly string OutDir = Path.GetFullPath(Path.Combine(Application.dataPath, "../Library/CodexPlaytests"));

    struct Step
    {
        public string Name;
        public float Duration;
        public Vector3? WalkTo;
        public float? LookPitch;
        public float? LookYaw;
        public Key[] Keys;
        public bool Fire;
        public bool Wiggle;
        public bool Snap;
        public bool Aim;
        public bool AutoDrive;
        public bool Record;
        // World-space walk and look targets, recomputed every tick; null leaves that control alone.
        public Func<Frame, Vector3?> Target;
        public Func<Frame, Vector3?> LookAt;
        // Ends the step early once true; Duration becomes a timeout.
        public Func<Frame, bool> Done;
    }

    // PLAYTEST_SCENARIO=kitchen runs the ammo loop: scoop from the freezer, pack a pint, reload, throw a grenade.
    static readonly List<Step> KitchenSteps = new List<Step>
    {
        new Step { Name = "k01_start", Duration = 2.5f, Snap = true },
        new Step { Name = "to freezer", Duration = 3f, WalkTo = new Vector3(-0.05f, 0.8f, -2.2f) },
        new Step { Name = "face freezer", Duration = 1f, LookYaw = -90, LookPitch = 35, Keys = new[] { Key.Digit2 } },
        new Step { Name = "k02_freezer", Duration = 0.2f, Snap = true, LookYaw = -90, LookPitch = 35 },
        new Step { Name = "scoop", Duration = 6f, Fire = true, Wiggle = true },
        new Step { Name = "to counter", Duration = 3f, WalkTo = new Vector3(-0.05f, 0.8f, -1.0f) },
        new Step { Name = "face counter", Duration = 1f, LookYaw = -90, LookPitch = 40, Keys = new[] { Key.Digit4 } },
        new Step { Name = "k03_counter", Duration = 0.2f, Snap = true, LookYaw = -90, LookPitch = 40 },
        new Step { Name = "pack 1", Duration = 0.25f, Fire = true }, new Step { Name = "release", Duration = 0.2f },
        new Step { Name = "pack 2", Duration = 0.25f, Fire = true }, new Step { Name = "release", Duration = 0.2f },
        new Step { Name = "pack 3", Duration = 0.25f, Fire = true }, new Step { Name = "release", Duration = 0.2f },
        new Step { Name = "take pint", Duration = 0.3f, Keys = new[] { Key.E } },
        new Step { Name = "pistol", Duration = 0.3f, Keys = new[] { Key.Digit1 }, LookYaw = 0, LookPitch = 0 },
        new Step { Name = "shoot", Duration = 1.5f, Fire = true },
        new Step { Name = "reload", Duration = 0.3f, Keys = new[] { Key.R } },
        new Step { Name = "k04_reloaded", Duration = 0.5f, Snap = true },
        new Step { Name = "scoop again", Duration = 0.3f, Keys = new[] { Key.Digit2 }, LookYaw = -90, LookPitch = 35 },
        new Step { Name = "to freezer 2", Duration = 3f, WalkTo = new Vector3(-0.05f, 0.8f, -2.2f) },
        new Step { Name = "face freezer 2", Duration = 1f, LookYaw = -90, LookPitch = 35 },
        new Step { Name = "scoop 2", Duration = 3f, Fire = true, Wiggle = true },
        new Step { Name = "select scoops", Duration = 0.3f, Keys = new[] { Key.Digit4 }, LookYaw = 0, LookPitch = -10 },
        new Step { Name = "wind up throw", Duration = 0.8f, Keys = new[] { Key.Q } },
        new Step { Name = "throw", Duration = 2.5f, Record = true },
        new Step { Name = "k05_thrown", Duration = 0.2f, Snap = true },
    };

    static readonly List<Step> DriveSteps = new List<Step>
    {
        new Step { Name = "01_kitchen", Duration = 2.5f, Snap = true },
        new Step { Name = "ladder", Duration = 0.3f, Keys = new[] { Key.E } },
        new Step { Name = "settle", Duration = 1f, LookPitch = 10 },
        new Step { Name = "02_roof", Duration = 0.5f, Snap = true },
        new Step { Name = "fire", Duration = 1.5f, Fire = true, LookPitch = 12 },
        new Step { Name = "03_roof_fired", Duration = 0.3f, Snap = true },
        new Step { Name = "hatch", Duration = 0.3f, Keys = new[] { Key.E } },
        new Step { Name = "settle", Duration = 0.8f },
        new Step { Name = "to aisle", Duration = 3f, WalkTo = new Vector3(-0.1f, 0.8f, -1.3f) },
        new Step { Name = "to doorway", Duration = 4f, WalkTo = new Vector3(-0.1f, 0.8f, 0.6f) },
        new Step { Name = "to seat", Duration = 3f, WalkTo = new Vector3(0.35f, 0.8f, 1.35f) },
        new Step { Name = "sit", Duration = 0.3f, Keys = new[] { Key.E } },
        new Step { Name = "04_driving", Duration = 1f, Snap = true, LookPitch = 0, LookYaw = 0 },
        new Step { Name = "drive", Duration = 4f, Keys = new[] { Key.W } },
        new Step { Name = "05_driving_fast", Duration = 0.2f, Keys = new[] { Key.W }, Snap = true },
        new Step { Name = "drive", Duration = 6f, Keys = new[] { Key.W } },
        new Step { Name = "06_driving_far", Duration = 0.2f, Keys = new[] { Key.W }, Snap = true },
        new Step { Name = "coast", Duration = 5f },
        new Step { Name = "leave seat", Duration = 0.3f, Keys = new[] { Key.E } },
        new Step { Name = "07_cab", Duration = 1f, Snap = true },
    };

    static readonly Step[] ToSeat =
    {
        new Step { Name = "to aisle", Duration = 3f, WalkTo = new Vector3(-0.1f, 0.8f, -1.3f) },
        new Step { Name = "to doorway", Duration = 4f, WalkTo = new Vector3(-0.1f, 0.8f, 0.6f) },
        new Step { Name = "to seat", Duration = 3f, WalkTo = new Vector3(0.35f, 0.8f, 1.35f) },
        new Step { Name = "sit", Duration = 0.3f, Keys = new[] { Key.E } },
        new Step { Name = "seated", Duration = 0.7f, LookPitch = 0, LookYaw = 0 },
    };

    static List<Step> ShowcaseSteps()
    {
        var steps = new List<Step>
        {
            new Step { Name = "s01_kitchen", Duration = 2.5f, Snap = true, LookPitch = 5 },
            new Step { Name = "look at teammate", Duration = 1f, LookYaw = 75, LookPitch = 5 },
            new Step { Name = "s02_teammate", Duration = 0.2f, Snap = true, LookYaw = 75, LookPitch = 5 },
            new Step { Name = "to ladder", Duration = 3f, WalkTo = new Vector3(0.53f, 0.8f, -2.2f) },
            new Step { Name = "face ladder", Duration = 0.8f, LookYaw = 180, LookPitch = -20 },
            new Step { Name = "ladder", Duration = 0.3f, Keys = new[] { Key.E }, LookYaw = 180, LookPitch = -20 },
            new Step { Name = "settle", Duration = 1f, LookPitch = 10 },
            new Step { Name = "wait for zombies", Duration = 15f, LookAt = NearestZombie, Done = f => NearestZombie(f).HasValue && (NearestZombie(f).Value - Camera.main.transform.position).magnitude < 20 },
            new Step { Name = "s03_roof_aim", Duration = 0.6f, Snap = true, LookAt = NearestZombie, Aim = true },
            new Step { Name = "roof_fire", Duration = 5f, LookAt = NearestZombie, Fire = true, Record = true },
            new Step { Name = "s04_roof_after", Duration = 0.2f, Snap = true, LookAt = NearestZombie },
            new Step { Name = "reload", Duration = 0.5f, Keys = new[] { Key.R } },
            new Step { Name = "roof_fire2", Duration = 4f, LookAt = NearestZombie, Fire = true, Record = true },
            new Step { Name = "face hatch", Duration = 0.8f, LookYaw = 180, LookPitch = 70 },
            new Step { Name = "hatch", Duration = 0.3f, Keys = new[] { Key.E }, LookYaw = 180, LookPitch = 70 },
            new Step { Name = "settle", Duration = 0.8f },
        };
        steps.AddRange(ToSeat);
        steps.Add(new Step { Name = "drive", Duration = 14f, AutoDrive = true, Record = true });
        steps.Add(new Step { Name = "s05_driving", Duration = 0.2f, AutoDrive = true, Snap = true });
        steps.Add(new Step { Name = "crash", Duration = 4f, Keys = new[] { Key.W, Key.A }, Record = true });
        steps.Add(new Step { Name = "s06_after_crash", Duration = 0.5f, Snap = true });
        return steps;
    }

    static unsafe List<Step> DepotSteps()
    {
        var steps = new List<Step> { new Step { Name = "d00_start", Duration = 2f, Snap = true } };
        steps.AddRange(ToSeat);
        steps.Add(new Step { Name = "drive to depot", Duration = 200f, AutoDrive = true, Done = f => f.Global->Phase == GamePhase.Depot });
        steps.Add(new Step { Name = "d01_parked", Duration = 1.5f, Snap = true });
        steps.Add(new Step { Name = "leave seat", Duration = 0.3f, Keys = new[] { Key.E } });
        for (int i = 0; i < 5; i++) steps.Add(new Step { Name = $"settle {i}", Duration = 0.15f });
        steps.Add(new Step { Name = "to doorway", Duration = 4f, WalkTo = new Vector3(-0.1f, 0.8f, 0.6f) });
        steps.Add(new Step { Name = "to aisle", Duration = 4f, WalkTo = new Vector3(-0.1f, 0.8f, -1.3f) });
        steps.Add(new Step { Name = "to back door", Duration = 3f, WalkTo = new Vector3(0f, 0.8f, -2.4f) });
        steps.Add(new Step { Name = "get out", Duration = 0.3f, Keys = new[] { Key.E } });
        steps.Add(new Step { Name = "settle", Duration = 0.7f });
        steps.Add(new Step { Name = "to shop", Duration = 20f, Target = f => Approach(f, AffordableShop(f), 1.1f), LookAt = f => Raised(AffordableShop(f), 0.9f) });
        steps.Add(new Step { Name = "d02_shop", Duration = 0.8f, Snap = true, LookAt = f => Raised(AffordableShop(f), 0.9f) });
        steps.Add(new Step { Name = "buy", Duration = 0.3f, Keys = new[] { Key.E }, LookAt = f => Raised(AffordableShop(f), 0.9f) });
        steps.Add(new Step { Name = "d03_bought", Duration = 1f, Snap = true });
        steps.Add(new Step { Name = "to exit", Duration = 20f, Target = f => Approach(f, StationOf(f, StationKind.DepotExit), 1.2f), LookAt = f => Raised(StationOf(f, StationKind.DepotExit), 1.2f) });
        steps.Add(new Step { Name = "d04_exit", Duration = 0.5f, Snap = true, LookAt = f => Raised(StationOf(f, StationKind.DepotExit), 1.2f) });
        steps.Add(new Step { Name = "roll out", Duration = 0.3f, Keys = new[] { Key.E }, LookAt = f => Raised(StationOf(f, StationKind.DepotExit), 1.2f) });
        steps.Add(new Step { Name = "d05_next_area", Duration = 2f, Snap = true });
        return steps;
    }

    // Sits down, drives a little, stops, gets up and walks back through the kitchen and out the back door.
    static List<Step> CabSteps()
    {
        var steps = new List<Step>(ToSeat);
        steps.Add(new Step { Name = "drive", Duration = 3f, Keys = new[] { Key.W, Key.A } });
        steps.Add(new Step { Name = "brake", Duration = 4f, Keys = new[] { Key.S }, Done = f => Mathf.Abs(f.GetSingleton<Truck>().Speed.AsFloat) < 0.3f });
        steps.Add(new Step { Name = "leave seat", Duration = 0.3f, Keys = new[] { Key.E } });
        for (int i = 0; i < 6; i++) steps.Add(new Step { Name = $"settle {i}", Duration = 0.15f });
        steps.Add(new Step { Name = "to doorway", Duration = 4f, WalkTo = new Vector3(-0.1f, 0.8f, 0.6f) });
        steps.Add(new Step { Name = "to aisle", Duration = 4f, WalkTo = new Vector3(-0.1f, 0.8f, -1.3f) });
        steps.Add(new Step { Name = "c01_aisle", Duration = 0.2f, Snap = true });
        return steps;
    }

    static Vector3? NearestZombie(Frame frame)
    {
        var eye = Camera.main.transform.position;
        Vector3? best = null;
        foreach (var pair in frame.GetComponentIterator<Zombie>())
        {
            if (pair.Component.State == ZombieState.Dead) continue;
            var head = frame.Get<Transform3D>(pair.Entity).Position.ToUnityVector3() + Vector3.up * 1.35f;
            if ((head - eye).magnitude > 35 || (best.HasValue && (head - eye).sqrMagnitude > (best.Value - eye).sqrMagnitude)) continue;
            best = head;
        }
        return best;
    }

    static unsafe Vector3? AffordableShop(Frame frame)
    {
        Vector3? best = null;
        var bestPrice = int.MaxValue;
        foreach (var pair in frame.GetComponentIterator<Station>())
        {
            var station = pair.Component;
            if (station.Kind != StationKind.Shop || station.Price > frame.Global->Money || station.Price >= bestPrice) continue;
            bestPrice = station.Price;
            best = frame.Get<Transform3D>(pair.Entity).Position.ToUnityVector3();
        }
        return best;
    }

    static Vector3? StationOf(Frame frame, StationKind kind)
    {
        foreach (var pair in frame.GetComponentIterator<Station>())
        {
            if (pair.Component.Kind == kind) return frame.Get<Transform3D>(pair.Entity).Position.ToUnityVector3();
        }
        return null;
    }

    static Vector3? Raised(Vector3? point, float height)
    {
        return point.HasValue ? point.Value + Vector3.up * height : (Vector3?)null;
    }

    // A spot `distance` short of the target on the line from the local survivor.
    static Vector3? Approach(Frame frame, Vector3? target, float distance)
    {
        if (!target.HasValue) return null;
        var position = frame.Get<Transform3D>(input.LocalEntity).Position.ToUnityVector3();
        var away = position - target.Value;
        away.y = 0;
        return target.Value + away.normalized * distance;
    }

    // Follows the road centerline: waypoints at each chunk's exit, plus the middle of the arc on curves, steering for
    // the first one at least 8 m ahead and holding a cruising speed. Parks in the depot lot once the depot chunk is
    // next, and backs out for a moment whenever it gets stuck against something.
    static unsafe void AutoDrive(Frame frame, List<Key> keys)
    {
        var settings = frame.FindAsset(frame.RuntimeConfig.Settings);
        var truck = frame.GetSingleton<Truck>();
        var transform = frame.Get<Transform3D>(frame.GetSingletonEntityRef<Truck>());
        var position = transform.Position.ToUnityVector3();
        var forward = transform.Forward.ToUnityVector3();
        var global = frame.Global;
        var now = EditorApplication.timeSinceStartup;
        var speed = truck.Speed.AsFloat;
        // Stuck means barely moving for two seconds (a crash bounce keeps the speed jittering, so position is the test).
        if (lastMoving == 0 || (position - lastMovingPosition).magnitude > 1 || backingUntil > now)
        {
            lastMoving = now;
            lastMovingPosition = position;
        }
        if (now - lastMoving > 2) backingUntil = now + 1.5f;
        if (backingUntil > now)
        {
            keys.Add(Key.S);
            return;
        }

        Vector3? target = null;
        var park = false;
        var turningIn = false;
        if (frame.Exists(global->DepotChunk) && global->TruckChunk >= frame.Get<RoadChunk>(global->DepotChunk).Index - 1)
        {
            // Stay on the road until alongside the lot, then turn into it and stop at the parking spot.
            var depot = frame.Get<Transform3D>(global->DepotChunk);
            var local = depot.InverseTransformPoint(transform.Position).ToUnityVector3();
            var onRoad = local.z < -1 && local.x > -5;
            target = depot.TransformPoint((onRoad ? new Vector3(0, 0, 4) : settings.DepotParking.ToUnityVector3()).ToFPVector3()).ToUnityVector3();
            park = !onRoad;
            turningIn = onRoad;
        }
        for (int index = global->TruckChunk; index <= global->TruckChunk + 2 && !target.HasValue; index++)
        {
            foreach (var pair in frame.GetComponentIterator<RoadChunk>())
            {
                if (pair.Component.Index != index) continue;
                var chunk = frame.Get<Transform3D>(pair.Entity);
                var kind = pair.Component.Kind;
                var side = kind == ChunkKind.CurveLeft ? -1 : kind == ChunkKind.CurveRight ? 1 : 0;
                var waypoints = side == 0 ? new[] { new Vector3(0, 0, 10) } : new[] { new Vector3(side * 2.93f, 0, -2.93f), new Vector3(side * 10, 0, 0) };
                foreach (var waypoint in waypoints)
                {
                    var world = chunk.TransformPoint(waypoint.ToFPVector3()).ToUnityVector3();
                    var ahead = world - position;
                    if (target.HasValue || ahead.magnitude < 8 || Vector3.Dot(ahead, forward) < 0) continue;
                    target = world;
                }
            }
        }
        if (!target.HasValue) return;
        var offset = target.Value - position;
        offset.y = 0;
        var angle = Vector3.SignedAngle(forward, offset, Vector3.up);
        if (angle > 3) keys.Add(Key.D);
        if (angle < -3) keys.Add(Key.A);
        var cruise = park ? Mathf.Clamp(offset.magnitude * 0.5f - 1f, 0, 6) : turningIn ? 6 : Mathf.Abs(angle) > 20 ? 8 : 14;
        if (speed < cruise - 0.5f) keys.Add(Key.W);
        else if (speed > cruise + 1.5f) keys.Add(Key.S);
        if (now - lastDriveLogTime > 1)
        {
            lastDriveLogTime = now;
            Log($"drive pos {position:F1} target {target.Value:F1} chunk {global->TruckChunk} angle {angle:F0} speed {speed:F1} keys {string.Join(",", keys)}");
        }
    }

    static double lastMoving;
    static Vector3 lastMovingPosition;
    static double backingUntil;
    static double lastDriveLogTime;

    static List<Step> steps;
    static double start;
    static int stepIndex;
    static double stepStart;
    static Keyboard keyboard;
    static Mouse mouse;
    static SurvivorInput input;
    static readonly StringBuilder log = new StringBuilder();
    static Camera display;
    static float lastTruckSpeed;
    static double lastRecord;
    static int recordIndex;

    const string ActiveKey = "ZombieTruck.Playtest.Active";

    public static void Run()
    {
        Directory.CreateDirectory(OutDir);
        var scene = EditorSceneManager.OpenScene(ScenePath);
        foreach (var root in scene.GetRootGameObjects())
        {
            if (root.name != "Gameplay") continue;
            var serialized = new SerializedObject(root.GetComponentInChildren<SurvivorInput>());
            serialized.FindProperty("requireCursorLock").boolValue = false;
            serialized.ApplyModifiedPropertiesWithoutUndo();
        }
        // The showcase adds an idle second local player so the run has a teammate (unsaved; only this play session).
        if (Environment.GetEnvironmentVariable("PLAYTEST_SCENARIO") == "showcase")
        {
            foreach (var root in scene.GetRootGameObjects())
            {
                if (!root.TryGetComponent(out QuantumRunnerLocalDebug runner)) continue;
                runner.LocalPlayers = new[] { new RuntimePlayer { PlayerNickname = "Player 1" }, new RuntimePlayer { PlayerNickname = "Player 2" } };
            }
        }
        SessionState.SetBool(ActiveKey, true);
        EditorApplication.EnterPlaymode();
    }

    // Entering play mode reloads scripts, which drops static state and event hooks; pick the run back up afterwards.
    [InitializeOnLoadMethod]
    static void Resume()
    {
        if (!SessionState.GetBool(ActiveKey, false)) return;
        // No Game view has focus in batch mode, so route device input to play mode regardless of focus.
        InputSystem.settings.editorInputBehaviorInPlayMode = InputSettings.EditorInputBehaviorInPlayMode.AllDeviceInputAlwaysGoesToGameView;
        InputSystem.settings.backgroundBehavior = InputSettings.BackgroundBehavior.IgnoreFocus;
        keyboard = InputSystem.AddDevice<Keyboard>();
        mouse = InputSystem.AddDevice<Mouse>();
        EditorApplication.update += Tick;
    }

    static void Tick()
    {
        if (!EditorApplication.isPlaying) return;
        var now = EditorApplication.timeSinceStartup;
        if (start == 0)
        {
            start = now;
            stepStart = now;
            var scenario = Environment.GetEnvironmentVariable("PLAYTEST_SCENARIO");
            steps = scenario == "kitchen" ? KitchenSteps : scenario == "showcase" ? ShowcaseSteps() : scenario == "depot" ? DepotSteps() : scenario == "cab" ? CabSteps() : DriveSteps;
            Log("play mode started");
        }
        if (now - start > 360)
        {
            Finish("timed out");
            return;
        }
        var game = QuantumRunner.Default?.Game;
        if (game == null || game.Frames.Predicted == null) return;
        Cursor.lockState = CursorLockMode.Locked;

        var step = steps[stepIndex];
        var keys = new List<Key>(step.Keys ?? Array.Empty<Key>());
        var mouseDelta = Vector2.zero;
        if (input == null)
        {
            foreach (var root in UnityEngine.SceneManagement.SceneManager.GetActiveScene().GetRootGameObjects())
            {
                if (root.name == "Gameplay") input = root.GetComponentInChildren<SurvivorInput>();
            }
        }
        var frame = game.Frames.Predicted;
        // A crash bounces the truck backwards from speed, so a sudden sign flip at speed marks one.
        var truckSpeed = frame.GetSingleton<Truck>().Speed.AsFloat;
        if (lastTruckSpeed > 3 && truckSpeed < 0) Log($"truck crashed at {lastTruckSpeed:F1} m/s");
        lastTruckSpeed = truckSpeed;
        if (input.LocalEntity.IsValid)
        {
            var survivor = frame.Get<Survivor>(input.LocalEntity);
            var position = frame.Get<Transform3D>(input.LocalEntity).Position.ToUnityVector3();
            var truck = frame.Get<Transform3D>(frame.GetSingletonEntityRef<Truck>());
            var currentYaw = input.Yaw + survivor.YawOffset.AsFloat;
            var desiredYaw = currentYaw;
            var walkTarget = step.WalkTo.HasValue ? truck.TransformPoint(step.WalkTo.Value.ToFPVector3()).ToUnityVector3() : step.Target?.Invoke(frame);
            if (walkTarget.HasValue)
            {
                var offset = walkTarget.Value - position;
                offset.y = 0;
                desiredYaw = Mathf.Atan2(offset.x, offset.z) * Mathf.Rad2Deg;
                if (offset.magnitude > 0.3f) keys.Add(Key.W);
                else stepStart = now - step.Duration;
            }
            var desiredPitch = step.LookPitch;
            var lookAt = step.LookAt?.Invoke(frame);
            // While walking somewhere the bot faces where it walks and only looks at its target once it arrives.
            if (lookAt.HasValue && !keys.Contains(Key.W))
            {
                var eye = Camera.main.transform.position;
                var look = lookAt.Value - eye;
                desiredYaw = Mathf.Atan2(look.x, look.z) * Mathf.Rad2Deg;
                desiredPitch = -Mathf.Atan2(look.y, new Vector2(look.x, look.z).magnitude) * Mathf.Rad2Deg;
            }
            if (step.LookYaw.HasValue) desiredYaw = truck.Rotation.ToUnityQuaternion().eulerAngles.y + step.LookYaw.Value;
            if (step.AutoDrive) AutoDrive(frame, keys);
            if (step.Done != null && step.Done(frame)) stepStart = now - step.Duration;
            var yawError = Mathf.DeltaAngle(currentYaw, desiredYaw);
            var pitchError = desiredPitch.HasValue ? desiredPitch.Value - input.Pitch : 0;
            mouseDelta = new Vector2(yawError, -pitchError) / 0.12f * 0.5f;
            if (step.Wiggle) mouseDelta = new Vector2(0, frame.Number % 2 == 0 ? 60 : -60);
        }
        InputSystem.QueueStateEvent(keyboard, new KeyboardState(keys.ToArray()));
        var mouseState = new MouseState { delta = mouseDelta };
        if (step.Fire) mouseState = mouseState.WithButton(UnityEngine.InputSystem.LowLevel.MouseButton.Left);
        if (step.Aim) mouseState = mouseState.WithButton(UnityEngine.InputSystem.LowLevel.MouseButton.Right);
        InputSystem.QueueStateEvent(mouse, mouseState);
        if (step.Record && now - lastRecord > 0.08)
        {
            lastRecord = now;
            Directory.CreateDirectory(Path.Combine(OutDir, "frames", step.Name));
            Capture(Path.Combine(OutDir, "frames", step.Name, $"{recordIndex++:D4}.png"), 640, 360);
        }

        if (now - stepStart < step.Duration) return;
        if (step.Snap) Snap(step.Name);
        Log($"step '{step.Name}' done: {State(frame, input)}");
        stepIndex++;
        stepStart = now;
        if (stepIndex >= steps.Count) Finish("all steps done");
    }

    static unsafe string State(Frame frame, SurvivorInput input)
    {
        var truck = frame.GetSingleton<Truck>();
        var truckPosition = frame.Get<Transform3D>(frame.GetSingletonEntityRef<Truck>()).Position.ToUnityVector3();
        var zombies = 0;
        var dead = 0;
        foreach (var pair in frame.GetComponentIterator<Zombie>())
        {
            zombies++;
            if (pair.Component.State == ZombieState.Dead) dead++;
        }
        var chunks = 0;
        foreach (var unused in frame.GetComponentIterator<RoadChunk>()) chunks++;
        var survivorText = "";
        if (input.LocalEntity.IsValid)
        {
            var survivor = frame.Get<Survivor>(input.LocalEntity);
            var position = frame.Get<Transform3D>(input.LocalEntity).Position.ToUnityVector3();
            var local = Quaternion.Inverse(frame.Get<Transform3D>(frame.GetSingletonEntityRef<Truck>()).Rotation.ToUnityQuaternion()) * (position - truckPosition);
            var hotbar = "";
            for (int i = 0; i < survivor.Hotbar.Length; i++)
            {
                var item = survivor.Hotbar[i];
                if (item.Kind != ItemKind.None) hotbar += $"[{i + 1}:{item.Kind} {item.Flavor} {item.Count}]";
            }
            survivorText = $"survivor local {local:F2} hp {survivor.Health.AsFloat:F0} driving {survivor.Driving} onTruck {survivor.Standing == frame.GetSingletonEntityRef<Truck>()} selected {survivor.Selected + 1} work {survivor.WorkProgress.AsFloat:F2} hotbar {hotbar}";
        }
        return $"tick {frame.Number} truck {truckPosition:F1} speed {truck.Speed.AsFloat:F1} zombies {zombies} (dead {dead}) chunks {chunks} kills {frame.Global->Kills} money {frame.Global->Money} phase {frame.Global->Phase} | {survivorText}";
    }

    static void Snap(string name)
    {
        Capture(Path.Combine(OutDir, name + ".png"), 1280, 720);
    }

    // Renders the PS1 game camera, then the display camera (dithered game image plus HUD) into a texture of the given size.
    static void Capture(string path, int width, int height)
    {
        Camera.main.Render();
        if (display == null)
        {
            foreach (var root in UnityEngine.SceneManagement.SceneManager.GetActiveScene().GetRootGameObjects())
            {
                if (root.name == "Display Camera") display = root.GetComponent<Camera>();
            }
        }
        var target = RenderTexture.GetTemporary(width, height, 24);
        display.targetTexture = target;
        display.Render();
        display.targetTexture = null;
        var previous = RenderTexture.active;
        RenderTexture.active = target;
        var texture = new Texture2D(width, height, TextureFormat.RGB24, false);
        texture.ReadPixels(new Rect(0, 0, width, height), 0, 0);
        texture.Apply();
        RenderTexture.active = previous;
        RenderTexture.ReleaseTemporary(target);
        File.WriteAllBytes(path, texture.EncodeToPNG());
        UnityEngine.Object.DestroyImmediate(texture);
    }

    static void Log(string message)
    {
        var line = $"[Playtest] {message}";
        Debug.Log(line);
        log.AppendLine(line);
    }

    static void Finish(string reason)
    {
        Log("finished: " + reason);
        File.WriteAllText(Path.Combine(OutDir, "playtest.txt"), log.ToString());
        EditorApplication.update -= Tick;
        SessionState.SetBool(ActiveKey, false);
        EditorApplication.Exit(0);
    }
}
