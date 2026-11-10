using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using Photon.Deterministic;
using Quantum;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.InputSystem.LowLevel;

// Play-test bot for Divorced Dads. Plays the scene through virtual keyboard and mouse devices (so the real input path
// is exercised), captures the full frame (game plus HUD) at marked steps, records frame sequences for GIFs, logs the
// simulation state and then leaves play mode (or quits in batch mode). Audio is muted for the whole run.
// In an open editor: DadsPlaytest.Run("serve"). Headless: Unity -batchmode -projectPath <project>
// -executeMethod DadsPlaytest.RunFromCommandLine -logFile <log> with PLAYTEST_SCENARIO set (no -quit).
// Scenarios: tour (aerial views of the town), serve (day one: load a cone, drive out, jingle, serve the queue, shove
// kids at the window), shop (spend at the lot, gather mud, churn it), night (short day: dusk, curfew, cops, clock out),
// tutorial (moving day from the trailer yard to the first drive out of Big Dairy's lot; every other scenario skips it),
// turret (buys the minigun, loads its hopper, climbs up to it and fires down the road), lamps (drives out of the lot and mows down a street lamp), ladder (a jump under the kitchen ceiling, up the ladder onto the roof, back down through the hatch, out the back door
// and in again). The pitch_* scenarios take 1920x1080 shots for the pitch deck, the outside ones from a camera around
// the van with the HUD hidden: pitch_day (mud, churn, the drive out, kids at the window, serving, running kids over
// until a cop shows up), pitch_gear (every upgrade, the upgraded van, the roof minigun), pitch_night (the scoop pistol,
// the sugar curfew cop, getting busted), pitch_crew (four dads in the kitchen, wide views of the town). pitch_redo and
// pitch_dusk restage the heist pitch screenshots with three dads, the bot walking the other two around: the kitchen
// crew, the crowd at the window from above, shooting kids, the upgraded van, a cop chasing the van seen from its roof
// and from behind the cop, a cop at the back door, and two dads heading off down the street at dusk. pitch_cars drives
// the van through The Flats with two police cars (the heist pitch's model, placed by the bot) on its tail. pitch_gang
// (day 5, so the dusk cops come in numbers) shoots ice cream at a pack of cops on foot: for the snaps the three cops'
// models are moved into a pack running at us and the front one is thrown into a tumble (view-only; in the game a cop hit
// with ice cream just goes on break). pitch_coast builds the heist pitch's harbor (dock, water, yacht, lighthouse) past
// the west edge of The Flats and, at sunset, walks the other two dads down the dock to the yacht.
public static class DadsPlaytest
{
    const string ScenePath = "Assets/QuantumUser/Scenes/DivorcedDads.unity";
    const string ScenarioKey = "DivorcedDads.Playtest.Scenario";
    static readonly string OutDir = Path.GetFullPath(Path.Combine(Application.dataPath, "../Library/CodexPlaytests/dads"));

    struct Step
    {
        public string Name;
        public float Duration;
        public Func<Frame, Vector3?> Target;
        public Func<Frame, Vector3?> LookAt;
        public float? LookPitch;
        public Key[] Keys;
        public bool Fire;
        public bool Aim;
        public bool Snap;
        public bool Record;
        public Func<Frame, Vector3?> DriveTo;
        public bool Ram;
        // Walks these points in order (then Target, if any).
        public Func<Frame, Vector3[]> Route;
        public Func<Frame, bool> Done;
        // Skips the step entirely (no keys pressed) when true as it starts.
        public Func<Frame, bool> Skip;
        public Vector3? CameraAt;
        public Vector3? CameraLook;
        // A camera away from the dad (position, look-at point), while the bot keeps playing: the HUD is hidden and the
        // local dad's body shown.
        public Func<Frame, Vector3[]> Shot;
        // The Shot camera stands in for the dad's eyes: HUD and first-person arms stay, his body stays hidden.
        public bool Fps;
        // What the other local players do during the step (index 0 is local slot 1); null leaves them standing.
        public Func<Frame, Puppet?[]> Crew;
        // Two police cars (view-only props; Divorced Dads has no police cars) trail the van along its recent path.
        public bool CopCars;
        // Poses the scene just before the snap (view-only).
        public Action<Frame> Stage;
    }

    struct Puppet
    {
        public Vector3? Walk;
        public Vector3? Look;
        public bool Interact;
        public bool Fire;
        // Keeps walking at Walk even when there (up a ladder).
        public bool Push;
    }

    // ------------------------------------------------------------------------------------------------ scenarios

    static List<Step> Tour()
    {
        var steps = new List<Step> { new Step { Name = "t00_kitchen", Duration = 3f, Snap = true } };
        var spots = new (string name, Vector3 at, Vector3 look)[]
        {
            ("t01_flats", new Vector3(-215, 45, -95), new Vector3(-215, 0, 0)),
            ("t02_maple", new Vector3(0, 55, -110), new Vector3(0, 0, 0)),
            ("t03_hillside", new Vector3(215, 45, -95), new Vector3(215, 0, 0)),
            ("t04_overview", new Vector3(0, 160, -220), new Vector3(0, 0, 10)),
        };
        foreach (var spot in spots) steps.Add(new Step { Name = spot.name, Duration = 1f, Snap = true, CameraAt = spot.at, CameraLook = spot.look });
        steps.Add(new Step { Name = "t05_lot", Duration = 1f, Snap = true, CameraAt = null, LookPitch = 5 });
        return steps;
    }

    static List<Step> Serve()
    {
        var steps = new List<Step>
        {
            new Step { Name = "s00_start", Duration = 4f, Snap = true, LookPitch = 0 },
            new Step { Name = "to freezer", Duration = 4f, Target = f => VanPoint(f, new Vector3(-0.15f, 0.8f, -2.3f)) },
            new Step { Name = "face tub", Duration = 1f, LookAt = f => Tub(f, 0), Keys = new[] { Key.Digit1 } },
            new Step { Name = "plop", Duration = 0.2f, Fire = true, LookAt = f => Tub(f, 0) },
            new Step { Name = "release", Duration = 0.4f, LookAt = f => Tub(f, 0) },
            new Step { Name = "s01_loaded", Duration = 0.3f, Snap = true, LookAt = f => Tub(f, 0) },
        };
        steps.AddRange(ToSeat());
        steps.Add(new Step { Name = "drive out", Duration = 60f, DriveTo = f => Flats(f), Record = true, Done = f => Arrived(f, Flats(f), 6) });
        steps.Add(new Step { Name = "brake", Duration = 4f, Keys = new[] { Key.S }, Done = f => Mathf.Abs(f.GetSingleton<Van>().Speed.AsFloat) < 0.3f });
        steps.Add(new Step { Name = "s02_parked", Duration = 0.5f, Snap = true });
        steps.Add(new Step { Name = "jingle on", Duration = 0.3f, Aim = true });
        steps.Add(new Step { Name = "wait for kids", Duration = 40f, Done = f => QueueCount(f) >= 2 });
        steps.Add(new Step { Name = "s03_queue", Duration = 0.3f, Snap = true });
        steps.Add(new Step { Name = "leave seat", Duration = 0.3f, Keys = new[] { Key.E } });
        for (int i = 0; i < 4; i++) steps.Add(new Step { Name = $"settle {i}", Duration = 0.15f });
        steps.Add(new Step { Name = "to doorway", Duration = 4f, Target = f => VanPoint(f, new Vector3(-0.1f, 0.8f, 0.6f)) });
        steps.Add(new Step { Name = "to window", Duration = 4f, Target = f => VanPoint(f, new Vector3(-0.25f, 0.8f, -0.8f)) });
        steps.Add(new Step { Name = "s04_window", Duration = 0.8f, Snap = true, LookAt = f => QueueFace(f) });
        steps.Add(new Step { Name = "shove", Duration = 0.25f, Fire = true, LookAt = f => QueueFace(f), Record = true });
        steps.Add(new Step { Name = "shove after", Duration = 1.6f, LookAt = f => QueueFace(f), Record = true });
        steps.Add(new Step { Name = "s05_shoved", Duration = 0.2f, Snap = true });
        // Reload the cone at the freezer and serve the next kid, a few times.
        for (int round = 0; round < 3; round++)
        {
            steps.Add(new Step { Name = $"to freezer {round}", Duration = 4f, Target = f => VanPoint(f, new Vector3(-0.15f, 0.8f, -2.3f)) });
            steps.Add(new Step { Name = $"face tub {round}", Duration = 0.8f, LookAt = f => Tub(f, FullestTub(f)) });
            steps.Add(new Step { Name = $"plop {round}", Duration = 0.2f, Fire = true, LookAt = f => Tub(f, FullestTub(f)) });
            steps.Add(new Step { Name = $"release {round}", Duration = 0.3f, LookAt = f => Tub(f, FullestTub(f)) });
            steps.Add(new Step { Name = $"back to window {round}", Duration = 4f, Target = f => VanPoint(f, new Vector3(-0.25f, 0.8f, -0.8f)) });
            steps.Add(new Step { Name = $"aim {round}", Duration = 0.8f, LookAt = f => QueueFace(f) });
            steps.Add(new Step { Name = $"shove {round}", Duration = 0.25f, Fire = true, LookAt = f => QueueFace(f) });
            steps.Add(new Step { Name = $"after {round}", Duration = 2f, LookAt = f => QueueFace(f) });
        }
        steps.Add(new Step { Name = "s06_served", Duration = 0.3f, Snap = true, LookPitch = 0 });
        return steps;
    }

    static List<Step> Shop()
    {
        var steps = new List<Step>
        {
            new Step { Name = "p00_start", Duration = 3f, Snap = true },
        };
        steps.AddRange(GetOut());
        steps.AddRange(new[]
        {
            new Step { Name = "to shop", Duration = 20f, Target = f => Approach(f, Fixture(f, FixtureKind.Shop, 0), 1.1f), LookAt = f => Raised(Fixture(f, FixtureKind.Shop, 0), 0.9f) },
            new Step { Name = "p01_shop", Duration = 0.8f, Snap = true, LookAt = f => Raised(Fixture(f, FixtureKind.Shop, 0), 0.9f) },
            new Step { Name = "buy", Duration = 0.3f, Keys = new[] { Key.E }, LookAt = f => Raised(Fixture(f, FixtureKind.Shop, 0), 0.9f) },
            new Step { Name = "p02_bought", Duration = 1.2f, Snap = true },
            new Step { Name = "to collector", Duration = 20f, Target = f => Approach(f, Fixture(f, FixtureKind.Collector, -1), 2.2f), LookAt = f => Raised(Fixture(f, FixtureKind.Collector, -1), 1.6f) },
            new Step { Name = "p03_big_dairy", Duration = 1f, Snap = true, LookAt = f => Raised(Fixture(f, FixtureKind.Collector, -1), 1.6f) },
            new Step { Name = "to mud", Duration = 40f, Target = f => Approach(f, Fixture(f, FixtureKind.MudPuddle, -1), 1.2f), LookAt = f => Fixture(f, FixtureKind.MudPuddle, -1) },
            new Step { Name = "grab mud", Duration = 0.3f, Keys = new[] { Key.E }, LookAt = f => Fixture(f, FixtureKind.MudPuddle, -1) },
            new Step { Name = "p04_mud", Duration = 0.8f, Snap = true, LookPitch = 0 },
            new Step { Name = "back to van", Duration = 40f, Target = f => VanPoint(f, new Vector3(0, 0.05f, -3.9f)) },
        });
        steps.AddRange(Enter());
        steps.AddRange(new[]
        {
            new Step { Name = "to churn", Duration = 5f, Target = f => VanPoint(f, new Vector3(-0.05f, 0.8f, 0.4f)) },
            new Step { Name = "face churn", Duration = 0.8f, LookAt = f => Fixture(f, FixtureKind.Churn, -1) + Vector3.up * 1.2f },
            new Step { Name = "churn", Duration = 0.3f, Keys = new[] { Key.E }, LookAt = f => Fixture(f, FixtureKind.Churn, -1) + Vector3.up * 1.2f },
            new Step { Name = "p05_churning", Duration = 0.5f, Snap = true },
            new Step { Name = "wait churn", Duration = 2.5f },
            new Step { Name = "p06_churned", Duration = 0.3f, Snap = true },
            // Backing away from the churn walks under the hopper gauge, which once dropped dads through the van floor.
            new Step { Name = "back up", Duration = 1.5f, Keys = new[] { Key.S }, LookAt = f => Fixture(f, FixtureKind.Churn, -1) + Vector3.up * 1.2f },
            new Step { Name = "p07_backed_up", Duration = 1f, Snap = true },
            new Step { Name = "jump under gauge", Duration = 0.15f, Keys = new[] { Key.Space } },
            new Step { Name = "land under gauge", Duration = 1f },
        });
        return steps;
    }

    static List<Step> Night()
    {
        var steps = new List<Step> { new Step { Name = "n00_start", Duration = 3f, Snap = true } };
        steps.AddRange(ToSeat());
        steps.Add(new Step { Name = "drive out", Duration = 60f, DriveTo = f => Flats(f), Done = f => Arrived(f, Flats(f), 6) });
        steps.Add(new Step { Name = "jingle", Duration = 0.3f, Aim = true });
        steps.Add(new Step { Name = "wait for dusk", Duration = 60f, Keys = new[] { Key.S }, Done = f => f.GetSingleton<DadsRun>().Phase == DayPhase.Dusk });
        steps.Add(new Step { Name = "n01_dusk", Duration = 0.5f, Snap = true });
        steps.Add(new Step { Name = "wait for night", Duration = 60f, Keys = new[] { Key.S }, Done = f => f.GetSingleton<DadsRun>().Phase == DayPhase.Night });
        steps.Add(new Step { Name = "n02_night", Duration = 4f, Snap = true, Record = true });
        steps.Add(new Step { Name = "drive home", Duration = 90f, DriveTo = f => LotEntrance(f), Done = f => Arrived(f, LotEntrance(f), 6), Record = true });
        steps.Add(new Step { Name = "into lot", Duration = 20f, DriveTo = f => Park(f), Done = f => Arrived(f, Park(f), 4) });
        steps.Add(new Step { Name = "stop", Duration = 4f, Keys = new[] { Key.S }, Done = f => Mathf.Abs(f.GetSingleton<Van>().Speed.AsFloat) < 0.3f });
        steps.Add(new Step { Name = "n03_home", Duration = 0.5f, Snap = true });
        steps.Add(new Step { Name = "leave seat", Duration = 0.3f, Keys = new[] { Key.E } });
        for (int i = 0; i < 4; i++) steps.Add(new Step { Name = $"settle {i}", Duration = 0.15f });
        steps.Add(new Step { Name = "to doorway", Duration = 4f, Target = f => VanPoint(f, new Vector3(-0.1f, 0.8f, 0.6f)) });
        steps.AddRange(GetOut());
        steps.Add(new Step { Name = "to clock", Duration = 30f, Target = f => Approach(f, Fixture(f, FixtureKind.TimeClock, -1), 1.1f), LookAt = f => Raised(Fixture(f, FixtureKind.TimeClock, -1), 1.3f) });
        steps.Add(new Step { Name = "clock out", Duration = 0.3f, Keys = new[] { Key.E }, LookAt = f => Raised(Fixture(f, FixtureKind.TimeClock, -1), 1.3f) });
        steps.Add(new Step { Name = "n04_collection", Duration = 2.5f, Snap = true });
        steps.Add(new Step { Name = "wait next day", Duration = 15f, Done = f => f.GetSingleton<DadsRun>().Phase == DayPhase.Morning });
        steps.Add(new Step { Name = "n05_next_morning", Duration = 2f, Snap = true });
        return steps;
    }

    // Fixed camera shots of The Flats: the lot's shop signs and the three trailer-lot strawberry patches.
    static List<Step> Flats()
    {
        return new List<Step>
        {
            new Step { Name = "f00_start", Duration = 9f },
            new Step { Name = "f01_shops", Duration = 1f, Snap = true, CameraAt = new Vector3(-232f, 2.4f, -21f), CameraLook = new Vector3(-225f, 1.7f, -22f) },
            new Step { Name = "f02_patch_a", Duration = 1f, Snap = true, CameraAt = new Vector3(-249f, 3f, 29f), CameraLook = new Vector3(-249f, 0.3f, 35f) },
            new Step { Name = "f03_patch_b", Duration = 1f, Snap = true, CameraAt = new Vector3(-174f, 3f, -42f), CameraLook = new Vector3(-174f, 0.3f, -36f) },
            new Step { Name = "f04_patch_c", Duration = 1f, Snap = true, CameraAt = new Vector3(-172f, 3f, 20f), CameraLook = new Vector3(-172f, 0.3f, 26f) },
        };
    }

    static List<Step> Turret()
    {
        var steps = new List<Step> { new Step { Name = "g00_start", Duration = 9f } };
        steps.AddRange(GetOut());
        steps.Add(new Step { Name = "to minigun shop", Duration = 25f, Target = f => Approach(f, Fixture(f, FixtureKind.Shop, 7), 1.1f), LookAt = f => Raised(Fixture(f, FixtureKind.Shop, 7), 0.9f) });
        steps.Add(new Step { Name = "face shop", Duration = 0.6f, LookAt = f => Raised(Fixture(f, FixtureKind.Shop, 7), 0.9f) });
        steps.Add(new Step { Name = "buy minigun", Duration = 0.3f, Keys = new[] { Key.E }, LookAt = f => Raised(Fixture(f, FixtureKind.Shop, 7), 0.9f) });
        steps.AddRange(GetIn());
        steps.Add(new Step { Name = "to hopper", Duration = 5f, Target = f => Approach(f, Fixture(f, FixtureKind.Hopper, -1), 0.9f) });
        steps.Add(new Step { Name = "face hopper", Duration = 0.8f, LookAt = f => Raised(Fixture(f, FixtureKind.Hopper, -1), 1.3f) });
        steps.Add(new Step { Name = "load hopper", Duration = 0.3f, Keys = new[] { Key.E }, LookAt = f => Raised(Fixture(f, FixtureKind.Hopper, -1), 1.3f) });
        steps.Add(new Step { Name = "to ladder", Duration = 5f, Target = f => VanPoint(f, new Vector3(0.72f, 0.8f, -2.42f)) });
        steps.Add(new Step { Name = "face ladder", Duration = 0.8f, LookAt = f => VanPoint(f, new Vector3(2.5f, 2.2f, -2.42f)) });
        steps.Add(new Step { Name = "climb out", Duration = 4f, Keys = new[] { Key.W }, LookPitch = 0, Done = f => !Me(f).Climbing && LocalOfDad(f).y > 2.5f });
        steps.Add(new Step { Name = "to turret", Duration = 6f, Target = f => Approach(f, Fixture(f, FixtureKind.Turret, -1), 1.6f), LookAt = f => Raised(Fixture(f, FixtureKind.Turret, -1), 1.3f) });
        steps.Add(new Step { Name = "face turret", Duration = 0.6f, LookAt = f => Raised(Fixture(f, FixtureKind.Turret, -1), 1.3f) });
        steps.Add(new Step { Name = "man turret", Duration = 0.3f, Keys = new[] { Key.E }, LookAt = f => Raised(Fixture(f, FixtureKind.Turret, -1), 1.3f) });
        steps.Add(new Step { Name = "g01_manned", Duration = 1.5f, Snap = true, LookAt = f => VanPoint(f, new Vector3(4f, 0f, 22f)) });
        steps.Add(new Step { Name = "fire", Duration = 1.5f, Fire = true, LookAt = f => VanPoint(f, new Vector3(4f, 0f, 22f)), Record = true });
        steps.Add(new Step { Name = "g02_fired", Duration = 0.4f, Snap = true, LookAt = f => VanPoint(f, new Vector3(4f, 0f, 22f)) });
        steps.Add(new Step { Name = "swing", Duration = 1.2f, LookAt = f => VanPoint(f, new Vector3(-20f, 2f, 5f)), Record = true });
        steps.Add(new Step { Name = "fire side", Duration = 1f, Fire = true, LookAt = f => VanPoint(f, new Vector3(-20f, 2f, 5f)), Record = true });
        steps.Add(new Step { Name = "g03_side", Duration = 0.4f, Snap = true, LookAt = f => VanPoint(f, new Vector3(-20f, 2f, 5f)) });
        return steps;
    }

    // The debug menu: open it with P, then cash, a full freezer, every upgrade and skipping the morning.
    static List<Step> DebugMenu()
    {
        var steps = new List<Step> { new Step { Name = "d00_start", Duration = 9f }, new Step { Name = "open menu", Duration = 0.2f, Keys = new[] { Key.P } } };
        steps.Add(new Step { Name = "release", Duration = 0.2f });
        foreach (var key in new[] { Key.Digit1, Key.Digit3, Key.Digit4, Key.Digit5, Key.Digit7 })
        {
            steps.Add(new Step { Name = $"cheat {key}", Duration = 0.2f, Keys = new[] { key } });
            steps.Add(new Step { Name = $"after {key}", Duration = 0.3f });
        }
        steps.Add(new Step { Name = "d01_cheated", Duration = 0.5f, Snap = true });
        steps.Add(new Step { Name = "to gauge", Duration = 5f, Target = f => Approach(f, Fixture(f, FixtureKind.Hopper, -1), 1.2f) });
        steps.Add(new Step { Name = "d02_full_gauge", Duration = 1f, Snap = true, LookAt = f => Raised(Fixture(f, FixtureKind.Hopper, -1), 1.5f) });
        return steps;
    }

    static List<Step> Lamps()
    {
        var steps = new List<Step> { new Step { Name = "a00_start", Duration = 3f } };
        steps.AddRange(ToSeat());
        steps.Add(new Step { Name = "drive out", Duration = 60f, DriveTo = f => Flats(f), Done = f => Arrived(f, Flats(f), 8) });
        steps.Add(new Step { Name = "ram lamp", Duration = 25f, DriveTo = f => LampNear(f, Flats(f)), Ram = true, Record = true, Done = f => f.GetSingleton<Van>().Damage > 0 });
        steps.Add(new Step { Name = "a01_felled", Duration = 1.2f, Snap = true, LookPitch = 0, Record = true });
        steps.Add(new Step { Name = "stop", Duration = 3f, Keys = new[] { Key.S }, Done = f => Mathf.Abs(f.GetSingleton<Van>().Speed.AsFloat) < 0.3f });
        steps.Add(new Step { Name = "a02_after", Duration = 0.5f, Snap = true });
        return steps;
    }

    // The standing street lamp closest to a point.
    static Vector3 LampNear(Frame frame, Vector3 point)
    {
        var best = point;
        var bestDistance = float.MaxValue;
        foreach (var pair in frame.GetComponentIterator<Quantum.Fixture>())
        {
            if (pair.Component.Kind != FixtureKind.LampPost || pair.Component.Open) continue;
            var position = frame.Get<Transform3D>(pair.Entity).Position.ToUnityVector3();
            if ((position - point).sqrMagnitude >= bestDistance) continue;
            bestDistance = (position - point).sqrMagnitude;
            best = position;
        }
        return best;
    }

    static List<Step> Ladder()
    {
        var ladder = new Vector3(0.72f, 0.8f, -2.42f);
        var wall = new Vector3(2.5f, 2.2f, -2.42f);
        var hatch = new Vector3(0.74f, 3f, -2.42f);
        var steps = new List<Step>
        {
            new Step { Name = "l00_start", Duration = 3f, Snap = true, LookPitch = 0 },
            new Step { Name = "jump", Duration = 0.15f, Keys = new[] { Key.Space }, LookPitch = -30 },
            new Step { Name = "l00_jump_peak", Duration = 0.25f, Snap = true, LookPitch = -30 },
            new Step { Name = "land", Duration = 1f, LookPitch = 0 },
            new Step { Name = "to ladder", Duration = 4f, Target = f => VanPoint(f, ladder) },
            new Step { Name = "face ladder", Duration = 0.8f, LookAt = f => VanPoint(f, wall) },
            new Step { Name = "l01_ladder", Duration = 0.3f, Snap = true, LookAt = f => VanPoint(f, hatch) },
            new Step { Name = "climb out", Duration = 4f, Keys = new[] { Key.W }, LookPitch = 0, Done = f => !Me(f).Climbing && LocalOfDad(f).y > 2.5f, Record = true },
            new Step { Name = "l02_roof", Duration = 1f, Snap = true, LookPitch = 15 },
            new Step { Name = "into hatch", Duration = 6f, Target = f => VanPoint(f, hatch), LookPitch = 60, Done = f => Me(f).Climbing, Record = true },
            new Step { Name = "climb down", Duration = 4f, Keys = new[] { Key.W }, LookPitch = 60, Done = f => !Me(f).Climbing, Record = true },
            new Step { Name = "l03_back_down", Duration = 0.5f, Snap = true, LookPitch = 0 },
        };
        steps.AddRange(GetOut());
        steps.Add(new Step { Name = "l04_outside", Duration = 0.8f, Snap = true, LookAt = f => VanPoint(f, new Vector3(0f, 1.4f, -2f)) });
        // Back in from the side: along the back of the van onto the rear step, then through the door.
        steps.Add(new Step { Name = "to side of step", Duration = 6f, Target = f => VanPoint(f, new Vector3(1.6f, 0.05f, -3.2f)) });
        steps.Add(new Step { Name = "onto step sideways", Duration = 4f, Target = f => VanPoint(f, new Vector3(0f, 0.05f, -3.2f)), Record = true });
        steps.Add(new Step { Name = "l04_on_step", Duration = 0.5f, Snap = true, LookAt = f => VanPoint(f, new Vector3(0f, 1.4f, -2f)) });
        steps.AddRange(Enter());
        steps.Add(new Step { Name = "l05_back_in", Duration = 0.5f, Snap = true, LookPitch = 0 });
        return steps;
    }

    static Dad Me(Frame frame)
    {
        return frame.Get<Dad>(input.LocalEntity);
    }

    // Moving day: mud from the puddle into the churn, a cone for the kid, strawberries and nuts churned, then the wheel.
    static List<Step> Tutorial()
    {
        var steps = new List<Step>
        {
            new Step { Name = "u00_start", Duration = 3f, Snap = true, LookPitch = 5 },
            new Step { Name = "u01_lessons", Duration = 7f, Snap = true, LookPitch = 5 },
            new Step { Name = "to mud", Duration = 20f, Target = f => Approach(f, Fixture(f, FixtureKind.MudPuddle, -1), 1.2f), LookAt = f => Fixture(f, FixtureKind.MudPuddle, -1) },
            new Step { Name = "face mud", Duration = 0.6f, LookAt = f => Fixture(f, FixtureKind.MudPuddle, -1) },
            new Step { Name = "grab mud", Duration = 0.3f, Keys = new[] { Key.E }, LookAt = f => Fixture(f, FixtureKind.MudPuddle, -1) },
            new Step { Name = "u02_mud", Duration = 1f, Snap = true, LookPitch = 5 },
        };
        steps.AddRange(YardIn());
        steps.AddRange(Churn("u03_churned"));
        steps.Add(new Step { Name = "to freezer", Duration = 4f, Target = f => VanPoint(f, new Vector3(-0.15f, 0.8f, -2.3f)) });
        steps.Add(new Step { Name = "face tub", Duration = 1f, LookAt = f => Tub(f, TubOf(f, Treat.Mud)), Keys = new[] { Key.Digit1 } });
        steps.Add(new Step { Name = "plop", Duration = 0.2f, Fire = true, LookAt = f => Tub(f, TubOf(f, Treat.Mud)) });
        steps.Add(new Step { Name = "release", Duration = 0.4f, LookAt = f => Tub(f, TubOf(f, Treat.Mud)) });
        steps.Add(new Step { Name = "u04_scooped", Duration = 0.5f, Snap = true });
        steps.Add(new Step { Name = "to window", Duration = 4f, Target = f => VanPoint(f, new Vector3(-0.25f, 0.8f, -0.8f)) });
        steps.Add(new Step { Name = "wait for kid", Duration = 40f, LookAt = f => QueueFace(f), Done = f => QueueCount(f) >= 1, Record = true });
        steps.Add(new Step { Name = "kid walks up", Duration = 8f, LookAt = f => QueueFace(f), Done = f => KidAtWindow(f), Record = true });
        steps.Add(new Step { Name = "u05_kid", Duration = 0.5f, Snap = true, LookAt = f => QueueFace(f) });
        steps.Add(new Step { Name = "shove", Duration = 0.25f, Fire = true, LookAt = f => QueueFace(f), Record = true });
        steps.Add(new Step { Name = "shove after", Duration = 2.5f, LookAt = f => QueueFace(f), Record = true });
        steps.Add(new Step { Name = "u06_served", Duration = 0.3f, Snap = true });
        steps.AddRange(GetOut());
        steps.Add(new Step { Name = "to patch", Duration = 30f, Target = f => Approach(f, Fixture(f, FixtureKind.StrawberryPatch, -1), 1.1f), LookAt = f => Fixture(f, FixtureKind.StrawberryPatch, -1) });
        steps.Add(new Step { Name = "face patch", Duration = 0.6f, LookAt = f => Fixture(f, FixtureKind.StrawberryPatch, -1) });
        steps.Add(new Step { Name = "pick", Duration = 0.3f, Keys = new[] { Key.E }, LookAt = f => Fixture(f, FixtureKind.StrawberryPatch, -1) });
        steps.Add(new Step { Name = "u07_berries", Duration = 0.8f, Snap = true, LookPitch = 5 });
        steps.AddRange(YardIn());
        steps.AddRange(Churn("u08_berries_churned"));
        steps.AddRange(GetOut());
        steps.Add(new Step { Name = "to tree", Duration = 30f, Target = f => Approach(f, Fixture(f, FixtureKind.NutTree, -1), 1.4f), LookAt = f => Raised(Fixture(f, FixtureKind.NutTree, -1), 1.2f) });
        for (int i = 0; i < 5; i++)
        {
            steps.Add(new Step { Name = $"shake {i}", Duration = 0.25f, Keys = new[] { Key.E }, LookAt = f => Raised(Fixture(f, FixtureKind.NutTree, -1), 1.2f) });
            steps.Add(new Step { Name = $"shake release {i}", Duration = 0.25f, LookAt = f => Raised(Fixture(f, FixtureKind.NutTree, -1), 1.2f) });
        }
        steps.Add(new Step { Name = "u09_nuts", Duration = 2f, Snap = true, LookAt = f => NearestLoot(f) });
        steps.Add(new Step { Name = "to sack", Duration = 10f, Target = f => Approach(f, NearestLoot(f), 1f), LookAt = f => NearestLoot(f) });
        steps.Add(new Step { Name = "face sack", Duration = 0.6f, LookAt = f => NearestLoot(f) });
        steps.Add(new Step { Name = "pick up", Duration = 0.3f, Keys = new[] { Key.E }, LookAt = f => NearestLoot(f) });
        steps.AddRange(YardIn());
        steps.AddRange(Churn("u10_nuts_churned"));
        steps.Add(new Step { Name = "u11_stocked", Duration = 1f, Snap = true, LookPitch = 5 });
        steps.AddRange(ToSeat());
        steps.Add(new Step { Name = "to the lot", Duration = 1.2f, Record = true });
        steps.Add(new Step { Name = "u12_lot", Duration = 3f, Snap = true, LookPitch = 0 });
        steps.Add(new Step { Name = "drive out", Duration = 60f, DriveTo = f => Flats(f), Done = f => Arrived(f, Flats(f), 6) });
        steps.Add(new Step { Name = "u13_day", Duration = 0.5f, Snap = true });
        return steps;
    }

    // From the yard into the back of the truck, past its yard-side rear corner (the serving window faces the yard).
    static IEnumerable<Step> YardIn()
    {
        yield return new Step { Name = "to corner", Duration = 30f, Target = f => VanPoint(f, new Vector3(-2.4f, 0.05f, -4.4f)) };
        yield return new Step { Name = "to rear", Duration = 10f, Target = f => VanPoint(f, new Vector3(0, 0.05f, -3.9f)) };
        foreach (var step in Enter()) yield return step;
    }

    static IEnumerable<Step> Churn(string snap)
    {
        yield return new Step { Name = "to churn", Duration = 5f, Target = f => VanPoint(f, new Vector3(-0.05f, 0.8f, 0.4f)) };
        yield return new Step { Name = "face churn", Duration = 0.8f, LookAt = f => Fixture(f, FixtureKind.Churn, -1) + Vector3.up * 1.2f };
        yield return new Step { Name = "churn", Duration = 0.3f, Keys = new[] { Key.E }, LookAt = f => Fixture(f, FixtureKind.Churn, -1) + Vector3.up * 1.2f };
        yield return new Step { Name = "wait churn", Duration = 2.5f };
        yield return new Step { Name = snap, Duration = 0.5f, Snap = true };
    }

    // Maple Grove: buy the permit and a pistol, drive through the gate to the park, ram the nut tree, churn rocky road,
    // load the pistol with it and shoot the queue.
    static List<Step> Maple()
    {
        var steps = new List<Step> { new Step { Name = "m00_start", Duration = 3f } };
        steps.AddRange(GetOut());
        foreach (var shop in new[] { 2, 0 })
        {
            steps.Add(new Step { Name = $"to shop {shop}", Duration = 20f, Target = f => Fixture(f, FixtureKind.Shop, shop) + new Vector3(1.2f, 0, 0), LookAt = f => Raised(Fixture(f, FixtureKind.Shop, shop), 0.9f) });
            steps.Add(new Step { Name = $"face shop {shop}", Duration = 0.6f, LookAt = f => Raised(Fixture(f, FixtureKind.Shop, shop), 0.9f) });
            steps.Add(new Step { Name = $"buy {shop}", Duration = 0.3f, Keys = new[] { Key.E }, LookAt = f => Raised(Fixture(f, FixtureKind.Shop, shop), 0.9f) });
            steps.Add(new Step { Name = $"after buy {shop}", Duration = 0.6f });
        }
        steps.AddRange(GetIn());
        steps.Add(new Step { Name = "to rack", Duration = 5f, Target = f => VanPoint(f, new Vector3(0.25f, 0.8f, -1.6f)), Keys = new[] { Key.Digit2 } });
        steps.Add(new Step { Name = "face rack", Duration = 0.8f, LookAt = f => Fixture(f, FixtureKind.GunRack, -1) + Vector3.up * 1f });
        steps.Add(new Step { Name = "take gun", Duration = 0.3f, Keys = new[] { Key.E }, LookAt = f => Fixture(f, FixtureKind.GunRack, -1) + Vector3.up * 1f });
        steps.Add(new Step { Name = "m01_armed", Duration = 0.5f, Snap = true });
        steps.AddRange(ToSeat());
        steps.Add(new Step { Name = "drive to park", Duration = 120f, DriveTo = f => NearestRoad(f, Fixture(f, FixtureKind.NutTree, -1)), Done = f => Arrived(f, NearestRoad(f, Fixture(f, FixtureKind.NutTree, -1)), 7), Record = true });
        steps.Add(new Step { Name = "m02_maple", Duration = 0.5f, Snap = true });
        steps.Add(new Step { Name = "ram tree", Duration = 25f, DriveTo = f => Fixture(f, FixtureKind.NutTree, -1), Ram = true, Record = true, Done = f => Count<Loot>(f) > 0 });
        steps.Add(new Step { Name = "stop", Duration = 3f, Keys = new[] { Key.S }, Done = f => Mathf.Abs(f.GetSingleton<Van>().Speed.AsFloat) < 0.3f });
        steps.Add(new Step { Name = "m03_rammed", Duration = 1.5f, Snap = true });
        steps.Add(new Step { Name = "leave seat", Duration = 0.3f, Keys = new[] { Key.E } });
        for (int i = 0; i < 4; i++) steps.Add(new Step { Name = $"settle {i}", Duration = 0.15f });
        steps.Add(new Step { Name = "to doorway", Duration = 4f, Target = f => VanPoint(f, new Vector3(-0.1f, 0.8f, 0.6f)) });
        steps.AddRange(GetOut());
        // Around the van's side: straight ahead would lead back in through the open back door.
        steps.Add(new Step { Name = "to nuts", Duration = 30f, Route = f => new[] { VanPoint(f, new Vector3(2.6f, 0.05f, -3.9f)).Value, VanPoint(f, new Vector3(2.6f, 0.05f, 4.2f)).Value },
            Target = f => Approach(f, NearestLoot(f), 0.9f), LookAt = f => NearestLoot(f) });
        steps.Add(new Step { Name = "face nuts", Duration = 0.8f, LookAt = f => NearestLoot(f) + Vector3.up * 0.2f });
        steps.Add(new Step { Name = "grab nuts", Duration = 0.3f, Keys = new[] { Key.E }, LookAt = f => NearestLoot(f) + Vector3.up * 0.2f });
        steps.Add(new Step { Name = "m04_nuts", Duration = 0.6f, Snap = true, LookPitch = 0 });
        steps.AddRange(GetIn());
        steps.Add(new Step { Name = "to churn", Duration = 5f, Target = f => VanPoint(f, new Vector3(-0.05f, 0.8f, 0.4f)) });
        steps.Add(new Step { Name = "face churn", Duration = 0.8f, LookAt = f => Fixture(f, FixtureKind.Churn, -1) + Vector3.up * 1.2f });
        steps.Add(new Step { Name = "churn", Duration = 0.3f, Keys = new[] { Key.E }, LookAt = f => Fixture(f, FixtureKind.Churn, -1) + Vector3.up * 1.2f });
        steps.Add(new Step { Name = "wait churn", Duration = 2.5f });
        steps.Add(new Step { Name = "to freezer", Duration = 4f, Target = f => VanPoint(f, new Vector3(-0.15f, 0.8f, -2.3f)), Keys = new[] { Key.Digit2 } });
        steps.Add(new Step { Name = "face rocky", Duration = 0.8f, LookAt = f => Tub(f, TubOf(f, Treat.RockyRoad)) });
        steps.Add(new Step { Name = "refill", Duration = 0.3f, Keys = new[] { Key.E }, LookAt = f => Tub(f, TubOf(f, Treat.RockyRoad)) });
        steps.Add(new Step { Name = "m05_loaded", Duration = 0.5f, Snap = true });
        steps.Add(new Step { Name = "to aisle", Duration = 3f, Target = f => VanPoint(f, new Vector3(-0.1f, 0.8f, -1.3f)) });
        steps.Add(new Step { Name = "to doorway", Duration = 4f, Target = f => VanPoint(f, new Vector3(-0.1f, 0.8f, 0.6f)) });
        steps.Add(new Step { Name = "to seat", Duration = 3f, Target = f => VanPoint(f, new Vector3(-0.35f, 0.8f, 1.35f)) });
        steps.Add(new Step { Name = "sit", Duration = 0.3f, Keys = new[] { Key.E } });
        steps.Add(new Step { Name = "jingle", Duration = 0.3f, Aim = true });
        steps.Add(new Step { Name = "wait for kids", Duration = 45f, Done = f => QueueCount(f) >= 3 });
        steps.Add(new Step { Name = "leave seat 2", Duration = 0.3f, Keys = new[] { Key.E } });
        for (int i = 0; i < 4; i++) steps.Add(new Step { Name = $"settle b{i}", Duration = 0.15f });
        steps.Add(new Step { Name = "to doorway 2", Duration = 4f, Target = f => VanPoint(f, new Vector3(-0.1f, 0.8f, 0.6f)) });
        steps.Add(new Step { Name = "to window", Duration = 4f, Target = f => VanPoint(f, new Vector3(-0.25f, 0.8f, -0.8f)) });
        steps.Add(new Step { Name = "aim", Duration = 0.8f, LookAt = f => QueueFace(f) });
        steps.Add(new Step { Name = "shoot", Duration = 3f, Fire = true, LookAt = f => QueueFace(f), Record = true });
        steps.Add(new Step { Name = "m06_shot", Duration = 1.5f, Snap = true, LookAt = f => QueueFace(f) });
        return steps;
    }

    // Hillside: buy everything, bring a bucket of mud, weigh down the vault's pressure plate with it, steal the gold
    // leaf, churn it, load the shotgun with gold and shoot the rich kids.
    static List<Step> Chaos()
    {
        var steps = new List<Step> { new Step { Name = "c00_start", Duration = 3f } };
        steps.AddRange(GetOut());
        foreach (var shop in new[] { 2, 6, 5, 7, 3, 1, 4 })
        {
            steps.Add(new Step { Name = $"to shop {shop}", Duration = 20f, Target = f => Fixture(f, FixtureKind.Shop, shop) + new Vector3(1.2f, 0, 0), LookAt = f => Raised(Fixture(f, FixtureKind.Shop, shop), 0.9f) });
            steps.Add(new Step { Name = $"face shop {shop}", Duration = 0.6f, LookAt = f => Raised(Fixture(f, FixtureKind.Shop, shop), 0.9f) });
            steps.Add(new Step { Name = $"buy {shop}", Duration = 0.3f, Keys = new[] { Key.E }, LookAt = f => Raised(Fixture(f, FixtureKind.Shop, shop), 0.9f) });
            steps.Add(new Step { Name = $"after buy {shop}", Duration = 0.5f });
        }
        steps.Add(new Step { Name = "c01_shopped", Duration = 0.5f, Snap = true });
        steps.Add(new Step { Name = "to mud", Duration = 30f, Target = f => Approach(f, Fixture(f, FixtureKind.MudPuddle, -1), 1.2f), LookAt = f => Fixture(f, FixtureKind.MudPuddle, -1) });
        steps.Add(new Step { Name = "grab mud", Duration = 0.3f, Keys = new[] { Key.E }, LookAt = f => Fixture(f, FixtureKind.MudPuddle, -1) });
        steps.AddRange(GetIn());
        steps.Add(new Step { Name = "drop mud", Duration = 0.3f, Keys = new[] { Key.Q }, LookPitch = 30 });
        steps.Add(new Step { Name = "settle drop", Duration = 1f });
        steps.Add(new Step { Name = "to rack", Duration = 5f, Target = f => VanPoint(f, new Vector3(0.25f, 0.8f, -1.6f)), Keys = new[] { Key.Digit2 } });
        steps.Add(new Step { Name = "face rack", Duration = 0.8f, LookAt = f => Fixture(f, FixtureKind.GunRack, -1) + Vector3.up * 1f });
        steps.Add(new Step { Name = "take shotgun", Duration = 0.3f, Keys = new[] { Key.E }, LookAt = f => Fixture(f, FixtureKind.GunRack, -1) + Vector3.up * 1f });
        steps.AddRange(ToSeat());
        steps.Add(new Step { Name = "drive to hillside", Duration = 150f, DriveTo = f => NearestRoad(f, Fixture(f, FixtureKind.Vault, -1)), Done = f => Arrived(f, NearestRoad(f, Fixture(f, FixtureKind.Vault, -1)), 7), Record = true });
        steps.Add(new Step { Name = "stop", Duration = 4f, Keys = new[] { Key.S }, Done = f => Mathf.Abs(f.GetSingleton<Van>().Speed.AsFloat) < 0.3f });
        steps.Add(new Step { Name = "c02_hillside", Duration = 0.5f, Snap = true });
        steps.Add(new Step { Name = "leave seat", Duration = 0.3f, Keys = new[] { Key.E } });
        for (int i = 0; i < 4; i++) steps.Add(new Step { Name = $"settle {i}", Duration = 0.15f });
        steps.Add(new Step { Name = "to doorway", Duration = 4f, Target = f => VanPoint(f, new Vector3(-0.1f, 0.8f, 0.6f)) });
        steps.Add(new Step { Name = "to bucket", Duration = 8f, Target = f => Approach(f, NearestLoot(f), 0.8f), LookAt = f => NearestLoot(f) });
        steps.Add(new Step { Name = "face bucket", Duration = 0.8f, LookAt = f => NearestLoot(f) + Vector3.up * 0.2f });
        steps.Add(new Step { Name = "grab bucket", Duration = 0.3f, Keys = new[] { Key.E }, LookAt = f => NearestLoot(f) + Vector3.up * 0.2f });
        steps.AddRange(GetOut());
        steps.Add(new Step { Name = "to plate", Duration = 60f, Route = f => RouteInto(f, Fixture(f, FixtureKind.Plate, -1)), Target = f => Fixture(f, FixtureKind.Plate, -1), Record = true });
        steps.Add(new Step { Name = "c03_plate", Duration = 0.5f, Snap = true, LookAt = f => Fixture(f, FixtureKind.Vault, -1) + Vector3.up });
        steps.Add(new Step { Name = "drop on plate", Duration = 0.3f, Keys = new[] { Key.Q }, LookPitch = 85 });
        steps.Add(new Step { Name = "wait vault", Duration = 2.5f });
        steps.Add(new Step { Name = "to vault", Duration = 20f, Target = f => Approach(f, Fixture(f, FixtureKind.Vault, -1), 1.3f), LookAt = f => Fixture(f, FixtureKind.Vault, -1) + Vector3.up * 1.2f });
        steps.Add(new Step { Name = "c04_vault", Duration = 0.8f, Snap = true, LookAt = f => Fixture(f, FixtureKind.Vault, -1) + Vector3.up * 1.2f });
        steps.Add(new Step { Name = "grab gold", Duration = 0.3f, Keys = new[] { Key.E }, LookAt = f => Fixture(f, FixtureKind.Vault, -1) + Vector3.up * 1.2f });
        steps.Add(new Step { Name = "c05_gold", Duration = 0.5f, Snap = true, LookPitch = 0 });
        steps.Add(new Step { Name = "leave block", Duration = 40f, Route = f => RouteInto(f, Fixture(f, FixtureKind.Plate, -1)).Reverse().ToArray(), Target = f => RouteInto(f, Fixture(f, FixtureKind.Plate, -1))[0] });
        steps.AddRange(GetIn());
        steps.Add(new Step { Name = "to churn", Duration = 5f, Target = f => VanPoint(f, new Vector3(-0.05f, 0.8f, 0.4f)) });
        steps.Add(new Step { Name = "face churn", Duration = 0.8f, LookAt = f => Fixture(f, FixtureKind.Churn, -1) + Vector3.up * 1.2f });
        steps.Add(new Step { Name = "churn", Duration = 0.3f, Keys = new[] { Key.E }, LookAt = f => Fixture(f, FixtureKind.Churn, -1) + Vector3.up * 1.2f });
        steps.Add(new Step { Name = "wait churn", Duration = 2.5f });
        steps.Add(new Step { Name = "to freezer", Duration = 4f, Target = f => VanPoint(f, new Vector3(-0.15f, 0.8f, -2.3f)), Keys = new[] { Key.Digit2 } });
        steps.Add(new Step { Name = "face gold", Duration = 0.8f, LookAt = f => Tub(f, TubOf(f, Treat.GoldLeaf)) });
        steps.Add(new Step { Name = "refill", Duration = 0.3f, Keys = new[] { Key.E }, LookAt = f => Tub(f, TubOf(f, Treat.GoldLeaf)) });
        steps.Add(new Step { Name = "c06_gold_shotgun", Duration = 0.5f, Snap = true });
        steps.Add(new Step { Name = "to bell", Duration = 0.1f });
        steps.AddRange(ToSeat());
        steps.Add(new Step { Name = "jingle", Duration = 0.3f, Aim = true });
        steps.Add(new Step { Name = "honk", Duration = 0.3f, Fire = true });
        steps.Add(new Step { Name = "wait for kids", Duration = 50f, Done = f => QueueCount(f) >= 3 });
        steps.Add(new Step { Name = "c07_queue", Duration = 0.3f, Snap = true });
        steps.Add(new Step { Name = "leave seat 2", Duration = 0.3f, Keys = new[] { Key.E } });
        for (int i = 0; i < 4; i++) steps.Add(new Step { Name = $"settle b{i}", Duration = 0.15f });
        steps.Add(new Step { Name = "to doorway 2", Duration = 4f, Target = f => VanPoint(f, new Vector3(-0.1f, 0.8f, 0.6f)) });
        steps.Add(new Step { Name = "to window", Duration = 4f, Target = f => VanPoint(f, new Vector3(-0.25f, 0.8f, -0.8f)) });
        steps.Add(new Step { Name = "aim", Duration = 0.8f, LookAt = f => QueueFace(f) });
        steps.Add(new Step { Name = "shoot", Duration = 4f, Fire = true, LookAt = f => QueueFace(f), Record = true });
        steps.Add(new Step { Name = "c08_shot", Duration = 1.5f, Snap = true, LookAt = f => QueueFace(f) });
        return steps;
    }

    // Checks that an item dropped in the van rides along with it.
    static List<Step> Ride()
    {
        var steps = new List<Step> { new Step { Name = "r00_start", Duration = 2f } };
        steps.AddRange(GetOut());
        steps.Add(new Step { Name = "to mud", Duration = 30f, Target = f => Approach(f, Fixture(f, FixtureKind.MudPuddle, -1), 1.2f), LookAt = f => Fixture(f, FixtureKind.MudPuddle, -1) });
        steps.Add(new Step { Name = "grab mud", Duration = 0.3f, Keys = new[] { Key.E }, LookAt = f => Fixture(f, FixtureKind.MudPuddle, -1) });
        steps.AddRange(GetIn());
        steps.Add(new Step { Name = "face front", Duration = 0.8f, LookAt = f => VanPoint(f, new Vector3(0, 0.8f, 0)) });
        steps.Add(new Step { Name = "drop mud", Duration = 0.3f, Keys = new[] { Key.Q }, LookAt = f => VanPoint(f, new Vector3(0, 0.8f, 0)) });
        steps.Add(new Step { Name = "settle drop", Duration = 1.5f, Snap = true });
        steps.AddRange(ToSeat());
        steps.Add(new Step { Name = "drive a", Duration = 8f, DriveTo = f => Flats(f) });
        steps.Add(new Step { Name = "drive b", Duration = 8f, DriveTo = f => Flats(f) });
        steps.Add(new Step { Name = "drive c", Duration = 8f, DriveTo = f => Flats(f) });
        return steps;
    }

    // The last day: a teammate in the kitchen, a drive out and straight back, clocking out with the cash for the final
    // installment, and the win card.
    static List<Step> Finale()
    {
        var steps = new List<Step>
        {
            new Step { Name = "f00_start", Duration = 7.5f, Snap = true },
            new Step { Name = "look at teammate", Duration = 1f, LookAt = f => Teammate(f) + Vector3.up * 1.4f },
            new Step { Name = "f01_teammate", Duration = 0.3f, Snap = true, LookAt = f => Teammate(f) + Vector3.up * 1.4f },
        };
        steps.AddRange(ToSeat());
        steps.Add(new Step { Name = "drive out", Duration = 60f, DriveTo = f => Flats(f), Done = f => Arrived(f, Flats(f), 6) });
        steps.Add(new Step { Name = "jingle", Duration = 0.3f, Aim = true });
        steps.Add(new Step { Name = "wait for kids", Duration = 40f, Done = f => QueueCount(f) >= 3, Keys = new[] { Key.S } });
        steps.Add(new Step { Name = "leave seat", Duration = 0.3f, Keys = new[] { Key.E } });
        for (int i = 0; i < 4; i++) steps.Add(new Step { Name = $"settle {i}", Duration = 0.15f });
        steps.Add(new Step { Name = "to doorway", Duration = 4f, Target = f => VanPoint(f, new Vector3(-0.1f, 0.8f, 0.6f)) });
        steps.Add(new Step { Name = "to window", Duration = 4f, Target = f => VanPoint(f, new Vector3(-0.25f, 0.8f, -0.8f)) });
        steps.Add(new Step { Name = "f02_kids", Duration = 1f, Snap = true, LookAt = f => QueueFace(f) });
        steps.Add(new Step { Name = "to doorway 2", Duration = 4f, Target = f => VanPoint(f, new Vector3(-0.1f, 0.8f, 0.6f)) });
        steps.Add(new Step { Name = "to seat", Duration = 3f, Target = f => VanPoint(f, new Vector3(-0.35f, 0.8f, 1.35f)) });
        steps.Add(new Step { Name = "sit", Duration = 0.3f, Keys = new[] { Key.E } });
        steps.Add(new Step { Name = "drive home", Duration = 90f, DriveTo = f => LotEntrance(f), Done = f => Arrived(f, LotEntrance(f), 6) });
        steps.Add(new Step { Name = "into lot", Duration = 20f, DriveTo = f => Park(f), Done = f => Arrived(f, Park(f), 4) });
        steps.Add(new Step { Name = "stop", Duration = 4f, Keys = new[] { Key.S }, Done = f => Mathf.Abs(f.GetSingleton<Van>().Speed.AsFloat) < 0.3f });
        steps.Add(new Step { Name = "leave seat 2", Duration = 0.3f, Keys = new[] { Key.E } });
        for (int i = 0; i < 4; i++) steps.Add(new Step { Name = $"settle b{i}", Duration = 0.15f });
        steps.Add(new Step { Name = "to doorway 3", Duration = 4f, Target = f => VanPoint(f, new Vector3(-0.1f, 0.8f, 0.6f)) });
        steps.AddRange(GetOut());
        steps.Add(new Step { Name = "to clock", Duration = 30f, Target = f => Approach(f, Fixture(f, FixtureKind.TimeClock, -1), 1.1f), LookAt = f => Raised(Fixture(f, FixtureKind.TimeClock, -1), 1.3f) });
        steps.Add(new Step { Name = "face clock", Duration = 0.6f, LookAt = f => Raised(Fixture(f, FixtureKind.TimeClock, -1), 1.3f) });
        steps.Add(new Step { Name = "clock out", Duration = 0.3f, Keys = new[] { Key.E }, LookAt = f => Raised(Fixture(f, FixtureKind.TimeClock, -1), 1.3f) });
        steps.Add(new Step { Name = "f03_paid", Duration = 2.5f, Snap = true });
        steps.Add(new Step { Name = "wait win", Duration = 10f, Done = f => f.GetSingleton<DadsRun>().Phase == DayPhase.Won });
        steps.Add(new Step { Name = "f04_won", Duration = 2f, Snap = true });
        return steps;
    }

    // The sugar curfew: wait out the day with the jingle on, step out at night and get chased down by a cop.
    static List<Step> Cops()
    {
        var steps = new List<Step> { new Step { Name = "o00_start", Duration = 2f } };
        steps.AddRange(ToSeat());
        steps.Add(new Step { Name = "drive out", Duration = 60f, DriveTo = f => Flats(f), Done = f => Arrived(f, Flats(f), 6) });
        steps.Add(new Step { Name = "jingle", Duration = 0.3f, Aim = true });
        steps.Add(new Step { Name = "wait for night", Duration = 90f, Keys = new[] { Key.S }, Done = f => f.GetSingleton<DadsRun>().Phase == DayPhase.Night });
        steps.Add(new Step { Name = "leave seat", Duration = 0.3f, Keys = new[] { Key.E } });
        for (int i = 0; i < 4; i++) steps.Add(new Step { Name = $"settle {i}", Duration = 0.15f });
        steps.Add(new Step { Name = "to doorway", Duration = 4f, Target = f => VanPoint(f, new Vector3(-0.1f, 0.8f, 0.6f)) });
        steps.AddRange(GetOut());
        steps.Add(new Step { Name = "wait for cop", Duration = 60f, LookAt = f => NearestCop(f), Done = f => NearestCop(f).HasValue && (NearestCop(f).Value - Camera.main.transform.position).magnitude < 12 });
        steps.Add(new Step { Name = "o01_cop", Duration = 0.3f, Snap = true, LookAt = f => NearestCop(f) });
        steps.Add(new Step { Name = "wait for bust", Duration = 30f, LookAt = f => NearestCop(f), Record = true, Done = f => f.Get<Dad>(input.LocalEntity).Busted > 0 });
        steps.Add(new Step { Name = "o02_busted", Duration = 1f, Snap = true });
        steps.Add(new Step { Name = "after bust", Duration = 3f, Record = true });
        steps.Add(new Step { Name = "o03_back_in_van", Duration = 0.5f, Snap = true });
        return steps;
    }


    // ------------------------------------------------------------------------------------------------ pitch deck shots

    static List<Step> PitchStart(string name)
    {
        return new List<Step>
        {
            new Step { Name = name, Duration = 9f },
            new Step { Name = "hide controls", Duration = 0.2f, Keys = new[] { Key.F1 } },
            new Step { Name = "release f1", Duration = 0.2f },
        };
    }

    static Func<Frame, Vector3[]> VanShot(Vector3 at, Vector3 look)
    {
        return f => new[] { VanPoint(f, at).Value, VanPoint(f, look).Value };
    }

    static IEnumerable<Step> LoadCone(string suffix)
    {
        yield return new Step { Name = "to freezer " + suffix, Duration = 4f, Target = f => VanPoint(f, new Vector3(-0.15f, 0.8f, -2.3f)) };
        yield return new Step { Name = "face tub " + suffix, Duration = 0.8f, LookAt = f => Tub(f, FullestTub(f)), Keys = new[] { Key.Digit1 } };
        yield return new Step { Name = "plop " + suffix, Duration = 0.2f, Fire = true, LookAt = f => Tub(f, FullestTub(f)) };
        yield return new Step { Name = "release " + suffix, Duration = 0.4f, LookAt = f => Tub(f, FullestTub(f)) };
    }

    static List<Step> PitchDay()
    {
        var steps = PitchStart("x00_start");
        steps.AddRange(GetOut());
        steps.Add(new Step { Name = "to mud", Duration = 40f, Target = f => Approach(f, Fixture(f, FixtureKind.MudPuddle, -1), 1.2f), LookAt = f => Fixture(f, FixtureKind.MudPuddle, -1) });
        steps.Add(new Step { Name = "grab mud", Duration = 0.3f, Keys = new[] { Key.E }, LookAt = f => Fixture(f, FixtureKind.MudPuddle, -1) });
        steps.Add(new Step { Name = "x01_mud", Duration = 0.8f, Snap = true, LookPitch = 15 });
        steps.Add(new Step { Name = "back to van", Duration = 40f, Target = f => VanPoint(f, new Vector3(0, 0.05f, -3.9f)) });
        steps.AddRange(Enter());
        steps.Add(new Step { Name = "to churn", Duration = 5f, Target = f => VanPoint(f, new Vector3(-0.05f, 0.8f, 0.4f)) });
        steps.Add(new Step { Name = "face churn", Duration = 0.8f, LookAt = f => Fixture(f, FixtureKind.Churn, -1) + Vector3.up * 1.2f });
        steps.Add(new Step { Name = "churn", Duration = 0.3f, Keys = new[] { Key.E }, LookAt = f => Fixture(f, FixtureKind.Churn, -1) + Vector3.up * 1.2f });
        steps.Add(new Step { Name = "x02_churning", Duration = 0.6f, Snap = true, LookAt = f => Fixture(f, FixtureKind.Churn, -1) + Vector3.up * 1.1f });
        steps.Add(new Step { Name = "x03_churn_inside", Duration = 0.4f, Snap = true, Shot = VanShot(new Vector3(0.7f, 2.1f, -1.4f), new Vector3(-0.2f, 1.1f, 0.6f)) });
        steps.Add(new Step { Name = "wait churn", Duration = 2.5f });
        steps.AddRange(LoadCone("a"));
        steps.AddRange(ToSeat());
        steps.Add(new Step { Name = "drive a", Duration = 4f, DriveTo = f => Flats(f) });
        steps.Add(new Step { Name = "x04_getaway", Duration = 1f, Snap = true, DriveTo = f => Flats(f), Shot = VanShot(new Vector3(-4.5f, 3f, -9f), new Vector3(0, 1.2f, 3f)) });
        steps.Add(new Step { Name = "drive b", Duration = 2f, DriveTo = f => Flats(f) });
        steps.Add(new Step { Name = "x05_getaway_front", Duration = 1f, Snap = true, DriveTo = f => Flats(f), Shot = VanShot(new Vector3(-3.5f, 2.2f, 10f), new Vector3(0, 1.4f, 0)) });
        steps.Add(new Step { Name = "drive out", Duration = 60f, DriveTo = f => Flats(f), Done = f => Arrived(f, Flats(f), 6) });
        steps.Add(new Step { Name = "brake", Duration = 4f, Keys = new[] { Key.S }, Done = f => Mathf.Abs(f.GetSingleton<Van>().Speed.AsFloat) < 0.3f });
        steps.Add(new Step { Name = "jingle on", Duration = 0.3f, Aim = true });
        steps.Add(new Step { Name = "wait for kids", Duration = 50f, Done = f => QueueCount(f) >= 3 });
        steps.Add(new Step { Name = "x06_kids", Duration = 0.6f, Snap = true, Shot = VanShot(new Vector3(-8f, 2.6f, 3f), new Vector3(-2f, 1.1f, -1.5f)) });
        steps.Add(new Step { Name = "x07_kids_back", Duration = 0.4f, Snap = true, Shot = VanShot(new Vector3(-6f, 2.2f, -8f), new Vector3(-2f, 1.1f, 0)) });
        steps.Add(new Step { Name = "leave seat", Duration = 0.3f, Keys = new[] { Key.E } });
        for (int i = 0; i < 4; i++) steps.Add(new Step { Name = $"settle {i}", Duration = 0.15f });
        steps.Add(new Step { Name = "to doorway", Duration = 4f, Target = f => VanPoint(f, new Vector3(-0.1f, 0.8f, 0.6f)) });
        steps.Add(new Step { Name = "to window", Duration = 4f, Target = f => VanPoint(f, new Vector3(-0.25f, 0.8f, -0.8f)) });
        steps.Add(new Step { Name = "x08_window", Duration = 0.8f, Snap = true, LookAt = f => QueueFace(f) });
        steps.Add(new Step { Name = "shove", Duration = 0.25f, Fire = true, LookAt = f => QueueFace(f) });
        steps.Add(new Step { Name = "x09_served", Duration = 0.35f, Snap = true, LookAt = f => QueueFace(f) });
        steps.Add(new Step { Name = "x10_served_outside", Duration = 0.3f, Snap = true, Shot = VanShot(new Vector3(-6f, 1.9f, 1.5f), new Vector3(-2.4f, 1.2f, -1f)) });
        for (int round = 0; round < 2; round++)
        {
            steps.AddRange(LoadCone($"b{round}"));
            steps.Add(new Step { Name = $"back to window {round}", Duration = 4f, Target = f => VanPoint(f, new Vector3(-0.25f, 0.8f, -0.8f)) });
            steps.Add(new Step { Name = $"aim {round}", Duration = 0.8f, LookAt = f => QueueFace(f) });
            steps.Add(new Step { Name = $"shove {round}", Duration = 0.25f, Fire = true, LookAt = f => QueueFace(f) });
            steps.Add(new Step { Name = $"x1{round + 1}_served_outside", Duration = 0.25f, Snap = true, Shot = VanShot(new Vector3(-4.5f, 1.7f, 2f), new Vector3(-2.4f, 1.3f, -1f)) });
            steps.Add(new Step { Name = $"x1{round + 3}_served", Duration = 0.2f, Snap = true, LookAt = f => QueueFace(f) });
        }
        steps.Add(new Step { Name = "x15_kitchen", Duration = 0.5f, Snap = true, Shot = VanShot(new Vector3(0.6f, 2.0f, -2.25f), new Vector3(-0.5f, 1.0f, 0.8f)) });
        steps.Add(new Step { Name = "to doorway 2", Duration = 4f, Target = f => VanPoint(f, new Vector3(-0.1f, 0.8f, 0.6f)) });
        steps.Add(new Step { Name = "to seat", Duration = 3f, Target = f => VanPoint(f, new Vector3(-0.35f, 0.8f, 1.35f)) });
        steps.Add(new Step { Name = "sit", Duration = 0.3f, Keys = new[] { Key.E } });
        var chase = VanShot(new Vector3(4.5f, 3.5f, -7f), new Vector3(0, 1f, 6f));
        steps.Add(new Step { Name = "ram kid", Duration = 40f, DriveTo = f => NearestKid(f), Ram = true, Done = f => Tumbling(f) > 0 });
        steps.Add(new Step { Name = "x16_hit_kid", Duration = 0.3f, Snap = true, DriveTo = f => NearestKid(f), Ram = true, Shot = chase });
        steps.Add(new Step { Name = "x17_hit_kid_after", Duration = 0.4f, Snap = true, DriveTo = f => NearestKid(f), Ram = true, Shot = VanShot(new Vector3(-5f, 2.5f, 9f), new Vector3(0, 1f, 2f)) });
        steps.Add(new Step { Name = "ram more", Duration = 90f, DriveTo = f => NearestKid(f), Ram = true, Done = f => f.GetSingleton<DadsRun>().Heat >= 2 });
        steps.Add(new Step { Name = "wait for cop", Duration = 60f, Keys = new[] { Key.S }, Done = f => CopToVan(f) < 14 });
        steps.Add(new Step { Name = "x18_cop", Duration = 0.4f, Snap = true, Keys = new[] { Key.S }, Shot = CopShot(5f) });
        steps.Add(new Step { Name = "wait closer", Duration = 1.5f, Keys = new[] { Key.S } });
        steps.Add(new Step { Name = "x19_cop_close", Duration = 0.4f, Snap = true, Keys = new[] { Key.S }, Shot = CopShot(3.5f) });
        steps.Add(new Step { Name = "x20_cop_driver", Duration = 0.4f, Snap = true, LookAt = f => NearestCop(f) });
        return steps;
    }

    static List<Step> PitchGear()
    {
        var steps = PitchStart("y00_start");
        steps.AddRange(GetOut());
        foreach (var shop in new[] { 2, 6, 5, 7, 3, 1, 4 })
        {
            steps.Add(new Step { Name = $"to shop {shop}", Duration = 20f, Target = f => Fixture(f, FixtureKind.Shop, shop) + new Vector3(1.2f, 0, 0), LookAt = f => Raised(Fixture(f, FixtureKind.Shop, shop), 0.9f) });
            steps.Add(new Step { Name = $"face shop {shop}", Duration = 0.6f, LookAt = f => Raised(Fixture(f, FixtureKind.Shop, shop), 0.9f) });
            if (shop == 3) steps.Add(new Step { Name = "y01_shop", Duration = 0.3f, Snap = true, LookAt = f => Raised(Fixture(f, FixtureKind.Shop, 3), 0.9f) });
            steps.Add(new Step { Name = $"buy {shop}", Duration = 0.3f, Keys = new[] { Key.E }, LookAt = f => Raised(Fixture(f, FixtureKind.Shop, shop), 0.9f) });
            steps.Add(new Step { Name = $"after buy {shop}", Duration = 0.5f });
        }
        steps.Add(new Step { Name = "y02_shops", Duration = 0.4f, Snap = true, Shot = f => new[] { new Vector3(-232f, 2.4f, -21f), new Vector3(-225f, 1.7f, -22f) } });
        steps.Add(new Step { Name = "y03_upgraded", Duration = 0.4f, Snap = true, Shot = VanShot(new Vector3(-7f, 3.2f, 7f), new Vector3(0, 1.6f, -0.5f)) });
        steps.Add(new Step { Name = "y04_upgraded_back", Duration = 0.4f, Snap = true, Shot = VanShot(new Vector3(6f, 3.8f, -8f), new Vector3(0, 2f, 0)) });
        steps.AddRange(GetIn());
        steps.Add(new Step { Name = "to hopper", Duration = 5f, Target = f => Approach(f, Fixture(f, FixtureKind.Hopper, -1), 0.9f) });
        steps.Add(new Step { Name = "face hopper", Duration = 0.8f, LookAt = f => Raised(Fixture(f, FixtureKind.Hopper, -1), 1.3f) });
        steps.Add(new Step { Name = "load hopper", Duration = 0.3f, Keys = new[] { Key.E }, LookAt = f => Raised(Fixture(f, FixtureKind.Hopper, -1), 1.3f) });
        steps.Add(new Step { Name = "to ladder", Duration = 5f, Target = f => VanPoint(f, new Vector3(0.72f, 0.8f, -2.42f)) });
        steps.Add(new Step { Name = "face ladder", Duration = 0.8f, LookAt = f => VanPoint(f, new Vector3(2.5f, 2.2f, -2.42f)) });
        steps.Add(new Step { Name = "climb out", Duration = 4f, Keys = new[] { Key.W }, LookPitch = 0, Done = f => !Me(f).Climbing && LocalOfDad(f).y > 2.5f });
        steps.Add(new Step { Name = "to turret", Duration = 6f, Target = f => Approach(f, Fixture(f, FixtureKind.Turret, -1), 1.6f), LookAt = f => Raised(Fixture(f, FixtureKind.Turret, -1), 1.3f) });
        steps.Add(new Step { Name = "face turret", Duration = 0.6f, LookAt = f => Raised(Fixture(f, FixtureKind.Turret, -1), 1.3f) });
        steps.Add(new Step { Name = "man turret", Duration = 0.3f, Keys = new[] { Key.E }, LookAt = f => Raised(Fixture(f, FixtureKind.Turret, -1), 1.3f) });
        steps.Add(new Step { Name = "aim turret", Duration = 1.5f, LookAt = f => VanPoint(f, new Vector3(4f, 0f, 22f)) });
        steps.Add(new Step { Name = "fire", Duration = 1.2f, Fire = true, LookAt = f => VanPoint(f, new Vector3(4f, 0f, 22f)) });
        steps.Add(new Step { Name = "y05_minigun", Duration = 0.3f, Snap = true, Fire = true, LookAt = f => VanPoint(f, new Vector3(4f, 0f, 22f)) });
        steps.Add(new Step { Name = "y06_minigun_outside", Duration = 0.4f, Snap = true, Fire = true, Shot = VanShot(new Vector3(-6f, 3.6f, 6f), new Vector3(0, 3f, -1f)) });
        steps.Add(new Step { Name = "y07_minigun_side", Duration = 0.4f, Snap = true, Fire = true, Shot = VanShot(new Vector3(7f, 2.5f, 9f), new Vector3(0, 2.6f, 0)) });
        return steps;
    }

    static List<Step> PitchNight()
    {
        var steps = PitchStart("z00_start");
        steps.AddRange(GetOut());
        steps.Add(new Step { Name = "to pistol shop", Duration = 20f, Target = f => Fixture(f, FixtureKind.Shop, 0) + new Vector3(1.2f, 0, 0), LookAt = f => Raised(Fixture(f, FixtureKind.Shop, 0), 0.9f) });
        steps.Add(new Step { Name = "face pistol shop", Duration = 0.6f, LookAt = f => Raised(Fixture(f, FixtureKind.Shop, 0), 0.9f) });
        steps.Add(new Step { Name = "buy pistol", Duration = 0.3f, Keys = new[] { Key.E }, LookAt = f => Raised(Fixture(f, FixtureKind.Shop, 0), 0.9f) });
        steps.Add(new Step { Name = "after buy", Duration = 0.6f });
        steps.AddRange(GetIn());
        steps.Add(new Step { Name = "to rack", Duration = 5f, Target = f => VanPoint(f, new Vector3(0.25f, 0.8f, -1.6f)), Keys = new[] { Key.Digit2 } });
        steps.Add(new Step { Name = "face rack", Duration = 0.8f, LookAt = f => Fixture(f, FixtureKind.GunRack, -1) + Vector3.up * 1f });
        steps.Add(new Step { Name = "take gun", Duration = 0.3f, Keys = new[] { Key.E }, LookAt = f => Fixture(f, FixtureKind.GunRack, -1) + Vector3.up * 1f });
        steps.Add(new Step { Name = "z01_armed", Duration = 0.5f, Snap = true, LookPitch = 5 });
        steps.AddRange(ToSeat());
        steps.Add(new Step { Name = "drive out", Duration = 60f, DriveTo = f => Flats(f), Done = f => Arrived(f, Flats(f), 6) });
        steps.Add(new Step { Name = "jingle", Duration = 0.3f, Aim = true });
        steps.Add(new Step { Name = "wait for night", Duration = 90f, Keys = new[] { Key.S }, Done = f => f.GetSingleton<DadsRun>().Phase == DayPhase.Night });
        steps.Add(new Step { Name = "z02_night_van", Duration = 0.4f, Snap = true, Shot = VanShot(new Vector3(-7f, 3f, 7f), new Vector3(0, 1.4f, 0)) });
        steps.Add(new Step { Name = "leave seat", Duration = 0.3f, Keys = new[] { Key.E } });
        for (int i = 0; i < 4; i++) steps.Add(new Step { Name = $"settle {i}", Duration = 0.15f });
        steps.Add(new Step { Name = "to doorway", Duration = 4f, Target = f => VanPoint(f, new Vector3(-0.1f, 0.8f, 0.6f)) });
        steps.AddRange(GetOut());
        steps.Add(new Step { Name = "pick gun", Duration = 0.2f, Keys = new[] { Key.Digit2 } });
        steps.Add(new Step { Name = "wait for cop", Duration = 60f, LookAt = f => NearestCop(f), Done = f => NearestCop(f).HasValue && (NearestCop(f).Value - Camera.main.transform.position).magnitude < 14 });
        steps.Add(new Step { Name = "z03_cop", Duration = 0.3f, Snap = true, LookAt = f => NearestCop(f) });
        steps.Add(new Step { Name = "z04_cop_outside", Duration = 0.3f, Snap = true, Shot = DadShot() });
        steps.Add(new Step { Name = "shoot cop", Duration = 1.2f, Fire = true, Aim = true, LookAt = f => NearestCop(f) });
        steps.Add(new Step { Name = "z05_splat", Duration = 0.3f, Snap = true, Fire = true, Aim = true, LookAt = f => NearestCop(f) });
        steps.Add(new Step { Name = "z06_splat_outside", Duration = 0.3f, Snap = true, Fire = true, Shot = DadShot() });
        steps.Add(new Step { Name = "wait for bust", Duration = 30f, LookAt = f => NearestCop(f), Done = f => f.Get<Dad>(input.LocalEntity).Busted > 0 });
        steps.Add(new Step { Name = "z07_busted", Duration = 1.2f, Snap = true });
        steps.Add(new Step { Name = "z08_busted_outside", Duration = 0.3f, Snap = true, Shot = DadShot() });
        return steps;
    }

    // Four dads at the lot: the kitchen from the back and a few wide views of the town.
    static List<Step> PitchCrew()
    {
        var steps = PitchStart("w00_start");
        steps.Add(new Step { Name = "w01_kitchen", Duration = 0.5f, Snap = true, Shot = VanShot(new Vector3(0.6f, 2.0f, -2.25f), new Vector3(-0.4f, 1.0f, 1.0f)) });
        steps.Add(new Step { Name = "w02_kitchen_front", Duration = 0.5f, Snap = true, Shot = VanShot(new Vector3(-0.6f, 2.0f, 1.0f), new Vector3(0.3f, 1.0f, -2.2f)) });
        steps.Add(new Step { Name = "w03_lot", Duration = 0.5f, Snap = true, Shot = VanShot(new Vector3(-9f, 4f, 9f), new Vector3(0, 1.5f, 0)) });
        var vistas = new (string name, Vector3 at, Vector3 look)[]
        {
            ("w04_vista_flats", new Vector3(-150f, 22f, -120f), new Vector3(-215f, 0, -10f)),
            ("w05_vista_maple", new Vector3(-40f, 25f, -100f), new Vector3(10f, 0, 0)),
            ("w06_vista_hillside", new Vector3(150f, 30f, -120f), new Vector3(215f, 5f, 0)),
            ("w07_street_maple", new Vector3(-12f, 7f, -45f), new Vector3(8f, 1f, 5f)),
        };
        foreach (var vista in vistas) steps.Add(new Step { Name = vista.name, Duration = 0.6f, Snap = true, Shot = f => new[] { vista.at, vista.look } });
        return steps;
    }


    // ------------------------------------------------------------------------------------------------ restaged heist shots

    static List<Step> PitchRedo()
    {
        var steps = PitchStart("r00_start");
        steps.AddRange(GetOut());
        foreach (var shop in new[] { 2, 6, 5, 7, 3, 1, 4 })
        {
            steps.Add(new Step { Name = $"to shop {shop}", Duration = 20f, Target = f => Fixture(f, FixtureKind.Shop, shop) + new Vector3(1.2f, 0, 0), LookAt = f => Raised(Fixture(f, FixtureKind.Shop, shop), 0.9f) });
            steps.Add(new Step { Name = $"face shop {shop}", Duration = 0.6f, LookAt = f => Raised(Fixture(f, FixtureKind.Shop, shop), 0.9f) });
            steps.Add(new Step { Name = $"buy {shop}", Duration = 0.3f, Keys = new[] { Key.E }, LookAt = f => Raised(Fixture(f, FixtureKind.Shop, shop), 0.9f) });
            steps.Add(new Step { Name = $"after buy {shop}", Duration = 0.5f });
        }
        steps.AddRange(GetIn());
        steps.Add(new Step { Name = "to rack", Duration = 5f, Target = f => VanPoint(f, new Vector3(0.25f, 0.8f, -1.6f)), Keys = new[] { Key.Digit2 } });
        steps.Add(new Step { Name = "face rack", Duration = 0.8f, LookAt = f => Fixture(f, FixtureKind.GunRack, -1) + Vector3.up * 1f });
        steps.Add(new Step { Name = "take gun", Duration = 0.3f, Keys = new[] { Key.E }, LookAt = f => Fixture(f, FixtureKind.GunRack, -1) + Vector3.up * 1f });
        steps.AddRange(ToSeat());
        steps.Add(new Step { Name = "drive out", Duration = 60f, DriveTo = f => Flats(f), Done = f => Arrived(f, Flats(f), 6) });
        steps.Add(new Step { Name = "brake", Duration = 4f, Keys = new[] { Key.S }, Done = f => Mathf.Abs(f.GetSingleton<Van>().Speed.AsFloat) < 0.3f });
        steps.Add(new Step { Name = "jingle on", Duration = 0.3f, Aim = true });
        steps.Add(new Step { Name = "r01_truck_upgrades", Duration = 0.5f, Snap = true, Shot = VanShot(new Vector3(-3.4f, 1.4f, 7.5f), new Vector3(0.3f, 1.8f, 0)) });
        // The kitchen crew: one dad at the churn, one at the counter, seen from the back of the van.
        Func<Frame, Puppet?[]> kitchen = f => new Puppet?[]
        {
            new Puppet { Walk = VanPoint(f, new Vector3(-0.05f, 0.8f, 0.4f)), Look = Fixture(f, FixtureKind.Churn, -1) + Vector3.up * 1.1f },
            new Puppet { Walk = VanPoint(f, new Vector3(0.35f, 0.8f, -0.5f)), Look = VanPoint(f, new Vector3(1.2f, 1.2f, -0.5f)) },
        };
        steps.Add(new Step { Name = "leave seat", Duration = 0.3f, Keys = new[] { Key.E } });
        for (int i = 0; i < 4; i++) steps.Add(new Step { Name = $"settle {i}", Duration = 0.15f });
        steps.Add(new Step { Name = "to doorway", Duration = 4f, Target = f => VanPoint(f, new Vector3(-0.1f, 0.8f, 0.6f)) });
        steps.Add(new Step { Name = "to back", Duration = 5f, Target = f => VanPoint(f, new Vector3(0f, 0.8f, -2.3f)) });
        steps.Add(new Step { Name = "look forward", Duration = 3f, LookAt = f => VanPoint(f, new Vector3(-0.1f, 1.3f, 1f)), Crew = kitchen });
        steps.Add(new Step { Name = "r02_kitchen_crew", Duration = 0.3f, Snap = true, LookAt = f => VanPoint(f, new Vector3(-0.1f, 1.3f, 1f)), Crew = kitchen });
        // Everyone to their job: one dad out on the sidewalk, one up the ladder onto the roof, us at the window.
        Func<Frame, Puppet?[]> jobs = f => new Puppet?[] { OutTo(f, 1, new Vector3(-4.2f, 0.05f, -4.5f), new Vector3(-2f, 1f, 3f)), UpTo(f, 2, new Vector3(-0.45f, 0, -2.6f), VanPoint(f, new Vector3(-6f, 0f, 2f)).Value) };
        steps.Add(new Step { Name = "face door", Duration = 0.8f, LookAt = f => VanPoint(f, new Vector3(0f, 1.4f, -4f)), Crew = jobs });
        steps.Add(new Step { Name = "open door", Duration = 0.3f, Keys = new[] { Key.E }, LookAt = f => VanPoint(f, new Vector3(0f, 1.4f, -4f)), Skip = f => DoorOpen(f), Crew = jobs });
        steps.Add(new Step { Name = "let them out", Duration = 6f, LookAt = f => VanPoint(f, new Vector3(0f, 1.4f, -4f)), Crew = jobs });
        steps.Add(new Step { Name = "to window", Duration = 6f, Target = f => VanPoint(f, new Vector3(-0.25f, 0.8f, -0.8f)), Crew = jobs });
        steps.Add(new Step { Name = "climb up", Duration = 8f, LookAt = f => QueueFace(f), Crew = jobs, Done = f => LocalOf(f, Puppeteer(f, 2)).y > 2.5f && QueueCount(f) >= 3 });
        steps.Add(new Step { Name = "r03_overview", Duration = 0.4f, Snap = true, LookAt = f => QueueFace(f), Crew = jobs, Shot = VanShot(new Vector3(-8.5f, 5.5f, 5.5f), new Vector3(0.3f, 0.6f, -1.5f)) });
        steps.Add(new Step { Name = "r04_coop", Duration = 0.4f, Snap = true, LookAt = f => QueueFace(f), Crew = jobs, Shot = VanShot(new Vector3(-11.5f, 7f, 7.5f), new Vector3(0.3f, 0.4f, -2f)) });
        steps.Add(new Step { Name = "aim", Duration = 0.8f, Aim = true, LookAt = f => QueueFace(f), Crew = jobs });
        steps.Add(new Step { Name = "shoot", Duration = 0.9f, Fire = true, LookAt = f => QueueFace(f), Crew = jobs });
        steps.Add(new Step { Name = "r05_shooting_kids", Duration = 0.2f, Snap = true, Fire = true, LookAt = f => QueueFace(f), Crew = jobs, Fps = true, Shot = WindowShot() });
        steps.Add(new Step { Name = "r06_shooting_kids_b", Duration = 0.6f, Snap = true, Fire = true, LookAt = f => QueueFace(f), Crew = jobs, Fps = true, Shot = WindowShot() });
        // Run kids over until the cops come; the roof dad rides along.
        Func<Frame, Puppet?[]> roof = f => new Puppet?[] { null, UpTo(f, 2, new Vector3(-0.45f, 0, -2.6f), NearestCop(f) ?? VanPoint(f, new Vector3(0, 2f, -20f)).Value) };
        steps.Add(new Step { Name = "to doorway 2", Duration = 4f, Target = f => VanPoint(f, new Vector3(-0.1f, 0.8f, 0.6f)), Crew = roof });
        steps.Add(new Step { Name = "to seat", Duration = 3f, Target = f => VanPoint(f, new Vector3(-0.35f, 0.8f, 1.35f)), Crew = roof });
        steps.Add(new Step { Name = "sit", Duration = 0.3f, Keys = new[] { Key.E }, Crew = roof });
        steps.Add(new Step { Name = "jingle off", Duration = 0.3f, Aim = true, Crew = roof });
        steps.Add(new Step { Name = "ram kids", Duration = 120f, DriveTo = f => NearestKid(f), Ram = true, Crew = roof, Done = f => f.GetSingleton<DadsRun>().Heat >= 2 });
        steps.Add(new Step { Name = "wait for cop", Duration = 60f, Keys = new[] { Key.S }, Crew = roof, Done = f => CopToVan(f) < 16 });
        steps.Add(new Step { Name = "r07_police_chase", Duration = 0.3f, Snap = true, Keys = new[] { Key.S }, Crew = roof, Fps = true, Shot = RoofShot() });
        steps.Add(new Step { Name = "r08_behind_cop", Duration = 0.3f, Snap = true, Keys = new[] { Key.S }, Crew = roof, Shot = CopShot(5f, 2.6f) });
        steps.Add(new Step { Name = "wait closer", Duration = 1.2f, Keys = new[] { Key.S }, Crew = roof });
        steps.Add(new Step { Name = "r09_police_chase_b", Duration = 0.3f, Snap = true, Crew = roof, Fps = true, Shot = RoofShot() });
        steps.Add(new Step { Name = "r10_behind_cop_b", Duration = 0.3f, Snap = true, Crew = roof, Shot = CopShot(4f, 2f) });
        // A cop at the back door: we stand behind the van and he comes for us; the camera looks out from the kitchen.
        steps.Add(new Step { Name = "leave seat 2", Duration = 0.3f, Keys = new[] { Key.E } });
        for (int i = 0; i < 4; i++) steps.Add(new Step { Name = $"settle b{i}", Duration = 0.15f });
        steps.Add(new Step { Name = "to doorway 3", Duration = 4f, Target = f => VanPoint(f, new Vector3(-0.1f, 0.8f, 0.6f)) });
        steps.AddRange(GetOut());
        steps.Add(new Step { Name = "wait at back", Duration = 40f, LookAt = f => VanPoint(f, new Vector3(0, 1.4f, -20f)), Done = f => CopInDoorway(f) });
        var doorView = VanShot(new Vector3(0.1f, 2.0f, 0.6f), new Vector3(0f, 1.3f, -6f));
        steps.Add(new Step { Name = "r11_cop_on_board", Duration = 0.2f, Snap = true, Fps = true, Shot = doorView });
        steps.Add(new Step { Name = "wait door", Duration = 0.8f });
        steps.Add(new Step { Name = "r12_cop_on_board_b", Duration = 0.2f, Snap = true, Fps = true, Shot = doorView });
        return steps;
    }

    // A curfew cop coming for us at the back door, seen from inside the kitchen: wait out the day, then stand a few
    // steps behind the open back door.
    static List<Step> PitchSearch()
    {
        var steps = PitchStart("v00_start");
        steps.AddRange(ToSeat());
        steps.Add(new Step { Name = "drive out", Duration = 60f, DriveTo = f => Flats(f), Done = f => Arrived(f, Flats(f), 8) });
        // The cops come to the jingle.
        steps.Add(new Step { Name = "jingle", Duration = 0.3f, Aim = true });
        steps.Add(new Step { Name = "wait for night", Duration = 90f, Keys = new[] { Key.S }, Done = f => f.GetSingleton<DadsRun>().Phase == DayPhase.Night });
        steps.Add(new Step { Name = "leave seat", Duration = 0.3f, Keys = new[] { Key.E } });
        for (int i = 0; i < 4; i++) steps.Add(new Step { Name = $"settle {i}", Duration = 0.15f });
        steps.Add(new Step { Name = "to doorway", Duration = 4f, Target = f => VanPoint(f, new Vector3(-0.1f, 0.8f, 0.6f)) });
        steps.AddRange(GetOut());
        steps.Add(new Step { Name = "back off", Duration = 5f, Target = f => VanPoint(f, new Vector3(0.1f, 0.05f, -6.5f)) });
        var doorView = VanShot(new Vector3(0.05f, 2.0f, 0.2f), new Vector3(0f, 1.2f, -6.5f));
        steps.Add(new Step { Name = "wait for cop", Duration = 90f, LookAt = f => VanPoint(f, new Vector3(0, 1.4f, -20f)), Done = f => CopInDoorway(f), Fps = true, Shot = doorView });
        steps.Add(new Step { Name = "v01_cop_door", Duration = 0.2f, Snap = true, Fps = true, Shot = doorView });
        steps.Add(new Step { Name = "closer", Duration = 0.5f, Fps = true, Shot = doorView });
        steps.Add(new Step { Name = "v02_cop_door", Duration = 0.2f, Snap = true, Fps = true, Shot = doorView });
        steps.Add(new Step { Name = "closer 2", Duration = 0.5f, Fps = true, Shot = doorView });
        steps.Add(new Step { Name = "v03_cop_door", Duration = 0.2f, Snap = true, Fps = true, Shot = doorView });
        return steps;
    }




    static List<Step> PitchCoast()
    {
        var steps = PitchStart("c00_start");
        steps.AddRange(ToSeat());
        steps.Add(new Step { Name = "drive out", Duration = 60f, DriveTo = f => Flats(f), Done = f => Arrived(f, Flats(f), 6) });
        steps.Add(new Step { Name = "brake", Duration = 4f, Keys = new[] { Key.S }, Done = f => Mathf.Abs(f.GetSingleton<Van>().Speed.AsFloat) < 0.3f });
        steps.Add(new Step { Name = "build harbor", Duration = 0.1f, Stage = BuildHarbor });
        steps.Add(new Step { Name = "wait for evening", Duration = 200f, Done = f => f.GetSingleton<DadsRun>().Clock >= FP._0_50 + FP._0_10 + FP._0_05 - FP._0_02 });
        steps.Add(new Step { Name = "leave seat", Duration = 0.3f, Keys = new[] { Key.E } });
        for (int i = 0; i < 4; i++) steps.Add(new Step { Name = $"settle {i}", Duration = 0.15f });
        steps.Add(new Step { Name = "to doorway", Duration = 4f, Target = f => VanPoint(f, new Vector3(-0.1f, 0.8f, 0.6f)) });
        steps.Add(new Step { Name = "to back door", Duration = 5f, Target = f => VanPoint(f, new Vector3(0f, 0.8f, -1.6f)) });
        steps.Add(new Step { Name = "face door", Duration = 0.8f, LookAt = f => VanPoint(f, new Vector3(0f, 1.4f, -4f)) });
        steps.Add(new Step { Name = "open door", Duration = 0.3f, Keys = new[] { Key.E }, LookAt = f => VanPoint(f, new Vector3(0f, 1.4f, -4f)), Skip = f => DoorOpen(f) });
        // Back in the driver's seat, out of the way of the churn's prompt.
        steps.Add(new Step { Name = "to doorway 2", Duration = 4f, Target = f => VanPoint(f, new Vector3(-0.1f, 0.8f, 0.6f)) });
        steps.Add(new Step { Name = "to seat", Duration = 3f, Target = f => VanPoint(f, new Vector3(-0.35f, 0.8f, 1.35f)) });
        steps.Add(new Step { Name = "sit", Duration = 0.3f, Keys = new[] { Key.E } });
        // The town's edge stops the dads short of the dock, so they walk up to it and their models are posed on the deck.
        Func<Frame, Puppet?[]> walk = f => new Puppet?[] { DockWalk(f, 1, -0.45f), DockWalk(f, 2, 0.45f) };
        steps.Add(new Step { Name = "walk to the dock", Duration = 6f, Crew = walk });
        var eye = DockShot(new Vector3(0.5f, 2.0f, 3.5f), new Vector3(-0.8f, 1.3f, 30f));
        steps.Add(new Step { Name = "c01_coast", Duration = 0.1f, Snap = true, Crew = walk, Fps = true, Shot = eye, Stage = LiftOntoDock });
        steps.Add(new Step { Name = "c02_coast_wide", Duration = 0.1f, Snap = true, Crew = walk, Shot = DockShot(new Vector3(-16f, 7f, 36f), new Vector3(1f, 0.5f, 9f)), Stage = LiftOntoDock });
        steps.Add(new Step { Name = "c03_coast_side", Duration = 0.1f, Snap = true, Crew = walk, Shot = DockShot(new Vector3(9f, 3.2f, 24f), new Vector3(-1f, 1.2f, 10f)), Stage = LiftOntoDock });
        steps.Add(new Step { Name = "c04_coast_close", Duration = 0.1f, Snap = true, Crew = walk, Fps = true, Shot = DockShot(new Vector3(0.4f, 2.0f, 5.5f), new Vector3(-0.8f, 1.3f, 30f)), Stage = LiftOntoDock });
        return steps;
    }

    // The dock's root (the land end of its deck, which stands 1 m above the water) and its heading (out to sea).
    static Vector3 harborRoot;
    static Quaternion harborHeading;
    const float DockHeight = 1f;

    // Lays the harbor past the town's west edge, level with the parked van: water to the horizon at ground level, the
    // dock heading out west, the yacht at its mooring and the lighthouse out on the water to the left.
    static void BuildHarbor(Frame frame)
    {
        var van = VanPoint(frame, Vector3.zero).Value;
        harborHeading = Quaternion.LookRotation(Vector3.left);
        harborRoot = new Vector3(van.x - 12f, DockHeight, van.z);
        GameObject Spawn(string model, Vector3 position, Quaternion rotation) =>
            UnityEngine.Object.Instantiate(AssetDatabase.LoadAssetAtPath<GameObject>($"Assets/Art/PS1/Vehicles/{model}.fbx"), position, rotation);
        for (int i = 0; i < 5; i++)
        {
            for (int j = -2; j <= 2; j++) Spawn("Harbor Water", new Vector3(harborRoot.x + 1f - 40f - 80f * i, 0, harborRoot.z + 80f * j), Quaternion.identity);
        }
        Spawn("Harbor Dock", harborRoot, harborHeading);
        Spawn("Yacht", harborRoot + harborHeading * new Vector3(-4.65f, -DockHeight, 19f), harborHeading);
        Spawn("Lighthouse", harborRoot + harborHeading * new Vector3(-55f, -DockHeight, 75f), harborHeading);
    }

    static Func<Frame, Vector3[]> DockShot(Vector3 at, Vector3 look)
    {
        return f => new[] { harborRoot + harborHeading * at, harborRoot + harborHeading * look };
    }

    // How far a local player's dad is along the dock.
    static float AlongDock(Frame frame, int slot)
    {
        var position = frame.Get<Transform3D>(Puppeteer(frame, slot)).Position.ToUnityVector3();
        return (Quaternion.Inverse(harborHeading) * (position - harborRoot)).z;
    }

    // Out of the van and down the dock (side: metres right of its middle), towards the yacht.
    static Puppet DockWalk(Frame frame, int slot, float side)
    {
        var van = frame.Get<Transform3D>(frame.GetSingletonEntityRef<Van>());
        Vector3 Local(Vector3 world) => van.InverseTransformPoint(world.ToFPVector3()).ToUnityVector3();
        var goal = harborRoot + harborHeading * new Vector3(side, -DockHeight, 24f);
        var face = harborRoot + harborHeading * new Vector3(side, 0, 40f);
        return OutTo(frame, slot, Local(goal), Local(face));
    }

    // Poses the two walking dads' models side by side on the deck, a few steps ahead of the camera, heading for the yacht.
    static void LiftOntoDock(Frame frame)
    {
        var viewUpdater = (QuantumEntityViewUpdater)new SerializedObject(DadsCamera.Instance).FindProperty("viewUpdater").objectReferenceValue;
        var spots = new[] { new Vector3(-0.5f, 0, 8.6f), new Vector3(0.5f, 0, 8.2f) };
        for (int slot = 1; slot <= 2; slot++)
        {
            viewUpdater.GetView(Puppeteer(frame, slot)).transform.SetPositionAndRotation(harborRoot + harborHeading * spots[slot - 1], harborHeading);
        }
    }

    static List<Step> PitchGang()
    {
        var steps = PitchStart("g00_start");
        steps.AddRange(GetOut());
        steps.Add(new Step { Name = "to pistol shop", Duration = 20f, Target = f => Fixture(f, FixtureKind.Shop, 0) + new Vector3(1.2f, 0, 0), LookAt = f => Raised(Fixture(f, FixtureKind.Shop, 0), 0.9f) });
        steps.Add(new Step { Name = "face pistol shop", Duration = 0.6f, LookAt = f => Raised(Fixture(f, FixtureKind.Shop, 0), 0.9f) });
        steps.Add(new Step { Name = "buy pistol", Duration = 0.3f, Keys = new[] { Key.E }, LookAt = f => Raised(Fixture(f, FixtureKind.Shop, 0), 0.9f) });
        steps.Add(new Step { Name = "after buy", Duration = 0.6f });
        steps.AddRange(GetIn());
        steps.Add(new Step { Name = "to rack", Duration = 5f, Target = f => VanPoint(f, new Vector3(0.25f, 0.8f, -1.6f)), Keys = new[] { Key.Digit2 } });
        steps.Add(new Step { Name = "face rack", Duration = 0.8f, LookAt = f => Fixture(f, FixtureKind.GunRack, -1) + Vector3.up * 1f });
        steps.Add(new Step { Name = "take gun", Duration = 0.3f, Keys = new[] { Key.E }, LookAt = f => Fixture(f, FixtureKind.GunRack, -1) + Vector3.up * 1f });
        steps.AddRange(ToSeat());
        steps.Add(new Step { Name = "drive out", Duration = 60f, DriveTo = f => Flats(f), Done = f => Arrived(f, Flats(f), 6) });
        steps.Add(new Step { Name = "brake", Duration = 4f, Keys = new[] { Key.S }, Done = f => Mathf.Abs(f.GetSingleton<Van>().Speed.AsFloat) < 0.3f });
        steps.Add(new Step { Name = "wait for evening", Duration = 400f, Done = f => f.GetSingleton<DadsRun>().Clock >= FP._0_50 + FP._0_10 + FP._0_05 + FP._0_02 });
        steps.Add(new Step { Name = "leave seat", Duration = 0.3f, Keys = new[] { Key.E } });
        for (int i = 0; i < 4; i++) steps.Add(new Step { Name = $"settle {i}", Duration = 0.15f });
        steps.Add(new Step { Name = "to doorway", Duration = 4f, Target = f => VanPoint(f, new Vector3(-0.1f, 0.8f, 0.6f)) });
        // Wait inside at the back door (a cop on the road busts us), then step out once three cops are about.
        steps.Add(new Step { Name = "to back door", Duration = 5f, Target = f => VanPoint(f, new Vector3(0f, 0.8f, -2.4f)) });
        steps.Add(new Step { Name = "face door", Duration = 0.8f, LookAt = f => VanPoint(f, new Vector3(0f, 1.4f, -6f)) });
        steps.Add(new Step { Name = "open door", Duration = 0.3f, Keys = new[] { Key.E }, LookAt = f => VanPoint(f, new Vector3(0f, 1.4f, -6f)), Skip = f => DoorOpen(f) });
        steps.Add(new Step { Name = "pick gun", Duration = 0.2f, Keys = new[] { Key.Digit2 } });
        Func<Frame, Vector3?> downRoad = f => VanPoint(f, new Vector3(0.3f, 1.1f, -30f));
        steps.Add(new Step { Name = "wait for cops", Duration = 120f, LookAt = downRoad, Done = f => CopCount(f) >= 3 });
        steps.Add(new Step { Name = "step out", Duration = 2.5f, Target = f => VanPoint(f, new Vector3(0.2f, 0.05f, -5.2f)) });
        steps.Add(new Step { Name = "aim", Duration = 0.5f, Aim = true, LookAt = downRoad });
        steps.Add(new Step { Name = "shoot", Duration = 0.45f, Fire = true, Aim = true, LookAt = downRoad });
        steps.Add(new Step { Name = "g01_gang", Duration = 0.05f, Snap = true, Fire = true, Aim = true, LookAt = downRoad, Stage = StageGang });
        steps.Add(new Step { Name = "g02_gang_outside", Duration = 0.05f, Snap = true, Fire = true, Shot = GangShot(), Stage = StageGang });
        steps.Add(new Step { Name = "shoot more", Duration = 0.25f, Fire = true, LookAt = downRoad });
        steps.Add(new Step { Name = "g03_gang_b", Duration = 0.05f, Snap = true, Fire = true, LookAt = downRoad, Stage = StageGang });
        steps.Add(new Step { Name = "g04_gang_outside_b", Duration = 0.05f, Snap = true, Fire = true, Shot = GangShot(), Stage = StageGang });
        return steps;
    }

    static int CopCount(Frame frame)
    {
        var count = 0;
        foreach (var pair in frame.GetComponentIterator<Npc>())
        {
            if (pair.Component.Kind == NpcKind.Cop) count++;
        }
        return count;
    }

    // Spots ahead of us (forward, right) for the pack, the first one thrown into the air.
    static readonly Vector2[] PackSpots = { new Vector2(5.2f, -1.1f), new Vector2(6.8f, 1.2f), new Vector2(8.3f, -2.6f) };

    // Moves three cops' models into a pack running at us down the road, the front one tumbling backwards.
    static void StageGang(Frame frame)
    {
        var viewUpdater = (QuantumEntityViewUpdater)new SerializedObject(DadsCamera.Instance).FindProperty("viewUpdater").objectReferenceValue;
        var dad = frame.Get<Transform3D>(input.LocalEntity).Position.ToUnityVector3();
        var forward = Quaternion.Euler(0, input.Yaw + frame.Get<Dad>(input.LocalEntity).YawOffset.AsFloat, 0) * Vector3.forward;
        var right = Vector3.Cross(Vector3.up, forward);
        var index = 0;
        foreach (var pair in frame.GetComponentIterator<Npc>())
        {
            if (pair.Component.Kind != NpcKind.Cop || index >= PackSpots.Length) continue;
            var spot = dad + forward * PackSpots[index].x + right * PackSpots[index].y;
            var view = viewUpdater.GetView(pair.Entity).transform;
            if (index == 0) view.SetPositionAndRotation(spot + Vector3.up * 1.5f, Quaternion.LookRotation(-forward) * Quaternion.Euler(-64f, 0, 26f));
            else view.SetPositionAndRotation(spot, Quaternion.LookRotation(-forward + right * (index == 1 ? 0.15f : -0.15f)));
            index++;
        }
    }

    // From the side and a little behind us, framing us and the pack ahead.
    static Func<Frame, Vector3[]> GangShot()
    {
        return f =>
        {
            var dad = f.Get<Transform3D>(input.LocalEntity).Position.ToUnityVector3() + Vector3.up;
            var forward = Quaternion.Euler(0, input.Yaw + f.Get<Dad>(input.LocalEntity).YawOffset.AsFloat, 0) * Vector3.forward;
            var right = Vector3.Cross(Vector3.up, forward);
            return new[] { dad + forward * 2.5f + right * 5f + Vector3.up * 1.2f, dad + forward * 4.5f };
        };
    }

    // Two police cars chasing the van down the road, seen from behind them, beside them and from up ahead.
    static List<Step> PitchCars()
    {
        var steps = PitchStart("k00_start");
        steps.AddRange(ToSeat());
        steps.Add(new Step { Name = "drive a", Duration = 8f, DriveTo = f => FarFlats(f), CopCars = true });
        steps.Add(new Step { Name = "k01_behind", Duration = 0.3f, Snap = true, DriveTo = f => FarFlats(f), CopCars = true, Shot = f => BehindCars(6f, 2.6f) });
        steps.Add(new Step { Name = "drive b", Duration = 1.5f, DriveTo = f => FarFlats(f), CopCars = true });
        steps.Add(new Step { Name = "k02_behind_low", Duration = 0.3f, Snap = true, DriveTo = f => FarFlats(f), CopCars = true, Shot = f => BehindCars(4.5f, 1.6f) });
        steps.Add(new Step { Name = "drive c", Duration = 1.5f, DriveTo = f => FarFlats(f), CopCars = true });
        steps.Add(new Step { Name = "k03_ahead", Duration = 0.3f, Snap = true, DriveTo = f => FarFlats(f), CopCars = true, Shot = VanShot(new Vector3(-4.5f, 2.2f, 9f), new Vector3(0, 1f, -8f)) });
        steps.Add(new Step { Name = "drive d", Duration = 1.5f, DriveTo = f => FarFlats(f), CopCars = true });
        steps.Add(new Step { Name = "k04_side", Duration = 0.3f, Snap = true, DriveTo = f => FarFlats(f), CopCars = true, Shot = VanShot(new Vector3(-9f, 4f, -4f), new Vector3(0, 0.8f, -7f)) });
        steps.Add(new Step { Name = "drive e", Duration = 1.5f, DriveTo = f => FarFlats(f), CopCars = true });
        steps.Add(new Step { Name = "k05_high", Duration = 0.3f, Snap = true, DriveTo = f => FarFlats(f), CopCars = true, Shot = VanShot(new Vector3(-7f, 9f, -18f), new Vector3(0, 0, -4f)) });
        steps.Add(new Step { Name = "drive f", Duration = 1.5f, DriveTo = f => FarFlats(f), CopCars = true });
        steps.Add(new Step { Name = "k06_behind_b", Duration = 0.3f, Snap = true, DriveTo = f => FarFlats(f), CopCars = true, Shot = f => BehindCars(6f, 2.6f) });
        return steps;
    }

    // The Flats road spot farthest from Big Dairy's lot.
    static Vector3 FarFlats(Frame frame)
    {
        var settings = frame.FindAsset(frame.RuntimeConfig.DadsSettings);
        var entrance = LotEntrance(frame);
        return settings.RoadSpots.Where(s => s.District == 0).Select(s => s.Position.ToUnityVector3()).OrderByDescending(p => (p - entrance).sqrMagnitude).First();
    }

    // Puts the two police cars where the van was 1.1 s and 2 s ago, the second one a lane over.
    static void PlaceCopCars()
    {
        if (copCars == null)
        {
            var model = AssetDatabase.LoadAssetAtPath<GameObject>("Assets/Art/PS1/Vehicles/Police Car.fbx");
            copCars = new[] { UnityEngine.Object.Instantiate(model), UnityEngine.Object.Instantiate(model) };
        }
        for (int i = 0; i < copCars.Length; i++)
        {
            var at = Time.time - (i == 0 ? 1.1f : 2f);
            var sample = vanTrail.LastOrDefault(t => t.time <= at);
            if (sample.time == 0) sample = vanTrail[0];
            var rotation = Quaternion.Euler(0, sample.yaw, 0);
            copCars[i].transform.SetPositionAndRotation(sample.position + rotation * Vector3.right * (i == 0 ? 0.6f : -1.8f), rotation);
            copCars[i].SetActive(true);
        }
    }

    // From behind and above the rear police car, looking past both at the van.
    static Vector3[] BehindCars(float back, float height)
    {
        var rear = copCars[1].transform;
        var front = copCars[0].transform;
        return new[] { rear.position - rear.forward * back + Vector3.up * height + rear.right * 0.8f, Vector3.Lerp(front.position, front.position + front.forward * 10f, 0.6f) + Vector3.up * 1f };
    }

    // Two dads walk off down the sidewalk at dusk, seen from behind them.
    static List<Step> PitchDusk()
    {
        var steps = PitchStart("u00_start");
        steps.AddRange(ToSeat());
        steps.Add(new Step { Name = "drive out", Duration = 60f, DriveTo = f => Flats(f), Done = f => Arrived(f, Flats(f), 6) });
        steps.Add(new Step { Name = "brake", Duration = 4f, Keys = new[] { Key.S }, Done = f => Mathf.Abs(f.GetSingleton<Van>().Speed.AsFloat) < 0.3f });
        steps.Add(new Step { Name = "wait for evening", Duration = 200f, Done = f => f.GetSingleton<DadsRun>().Clock >= FP._0_50 + FP._0_10 + FP._0_05 });
        steps.Add(new Step { Name = "leave seat", Duration = 0.3f, Keys = new[] { Key.E } });
        for (int i = 0; i < 4; i++) steps.Add(new Step { Name = $"settle {i}", Duration = 0.15f });
        steps.Add(new Step { Name = "to doorway", Duration = 4f, Target = f => VanPoint(f, new Vector3(-0.1f, 0.8f, 0.6f)) });
        steps.AddRange(GetOut());
        Func<Frame, Puppet?[]> stroll = f => new Puppet?[]
        {
            OutTo(f, 1, new Vector3(-3.6f, 0.05f, 14f), new Vector3(-3.6f, 1.5f, 40f)),
            OutTo(f, 2, new Vector3(-5f, 0.05f, 13f), new Vector3(-5f, 1.5f, 40f)),
        };
        steps.Add(new Step { Name = "to sidewalk", Duration = 8f, Target = f => VanPoint(f, new Vector3(-4.3f, 0.05f, -5f)), Crew = stroll });
        steps.Add(new Step { Name = "follow", Duration = 20f, LookAt = f => VanPoint(f, new Vector3(-4.3f, 1.4f, 12f)), Crew = stroll, Done = f => LocalOf(f, Puppeteer(f, 1)).z > -1.5f && LocalOf(f, Puppeteer(f, 2)).z > -2f });
        steps.Add(new Step { Name = "u01_dusk_walk", Duration = 0.2f, Snap = true, LookAt = f => VanPoint(f, new Vector3(-4.3f, 1.4f, 12f)), Crew = stroll });
        steps.Add(new Step { Name = "walk on", Duration = 0.8f, LookAt = f => VanPoint(f, new Vector3(-4.3f, 1.4f, 14f)), Crew = stroll });
        steps.Add(new Step { Name = "u02_dusk_walk_b", Duration = 0.2f, Snap = true, LookAt = f => VanPoint(f, new Vector3(-4.3f, 1.4f, 14f)), Crew = stroll });
        steps.Add(new Step { Name = "wait for dusk", Duration = 40f, LookAt = f => VanPoint(f, new Vector3(-4.3f, 1.4f, 14f)), Crew = stroll, Done = f => f.GetSingleton<DadsRun>().Phase == DayPhase.Dusk });
        steps.Add(new Step { Name = "u03_dusk", Duration = 1f, Snap = true, LookAt = f => VanPoint(f, new Vector3(-4.3f, 1.4f, 14f)), Crew = stroll });
        return steps;
    }

    // The local player's dad in a local slot (0 is ours).
    static EntityRef Puppeteer(Frame frame, int slot)
    {
        QuantumRunner.Default.Game.Session.TryGetLocalPlayer(slot, out var player);
        foreach (var pair in frame.GetComponentIterator<Dad>())
        {
            if (pair.Component.Player == player) return pair.Entity;
        }
        return EntityRef.None;
    }

    static Vector3 LocalOf(Frame frame, EntityRef entity)
    {
        var van = frame.Get<Transform3D>(frame.GetSingletonEntityRef<Van>());
        return van.InverseTransformPoint(frame.Get<Transform3D>(entity).Position).ToUnityVector3();
    }

    // Out of the van through the back door, then to a spot (van local), facing a point (van local).
    static Puppet OutTo(Frame frame, int slot, Vector3 spot, Vector3 face)
    {
        var local = LocalOf(frame, Puppeteer(frame, slot));
        var inside = local.y > 0.5f && Mathf.Abs(local.x) < 1.3f && local.z > -3.2f;
        var walk = inside && local.z > -2.1f ? new Vector3(0, 0.8f, -2.35f) : inside ? new Vector3(0, 0.05f, -4.4f) : spot;
        // Behind the van with the spot past its side: step out sideways first instead of walking into the bodywork.
        if (!inside && local.z < -2.4f && Mathf.Abs(local.x) < 2.4f && spot.z > -2.4f) walk = new Vector3(Mathf.Sign(spot.x) * 2.9f, 0.05f, local.z);
        return new Puppet { Walk = VanPoint(frame, walk), Look = VanPoint(frame, face) };
    }

    // Up the ladder at the back of the kitchen onto the roof, then to a spot (van local x, z) facing a world point.
    static Puppet UpTo(Frame frame, int slot, Vector3 spot, Vector3 face)
    {
        var local = LocalOf(frame, Puppeteer(frame, slot));
        if (local.y > 2.5f) return new Puppet { Walk = VanPoint(frame, new Vector3(spot.x, local.y, spot.z)), Look = face };
        var ladderFoot = VanPoint(frame, new Vector3(0.72f, 0.8f, -2.42f)).Value;
        var atFoot = new Vector2(ladderFoot.x - frame.Get<Transform3D>(Puppeteer(frame, slot)).Position.X.AsFloat, ladderFoot.z - frame.Get<Transform3D>(Puppeteer(frame, slot)).Position.Z.AsFloat).magnitude < 0.35f;
        var climbing = frame.Get<Dad>(Puppeteer(frame, slot)).Climbing;
        if (!atFoot && !climbing) return new Puppet { Walk = ladderFoot };
        return new Puppet { Walk = VanPoint(frame, new Vector3(2.5f, 2.2f, -2.42f)), Push = true };
    }

    static Quantum.Input PuppetInput(Frame frame, int slot, Puppet puppet)
    {
        var entity = Puppeteer(frame, slot);
        var dad = frame.Get<Dad>(entity);
        var eye = frame.Get<Transform3D>(entity).Position.ToUnityVector3() + Vector3.up * 1.5f;
        var result = new Quantum.Input { Slot = 1, Interact = puppet.Interact, Fire = puppet.Fire };
        var face = puppet.Look;
        if (puppet.Walk.HasValue)
        {
            var offset = puppet.Walk.Value - eye;
            offset.y = 0;
            if (offset.magnitude > 0.3f || puppet.Push)
            {
                result.Move = new Vector2(0, 1).ToFPVector2();
                face = puppet.Walk.Value + Vector3.up * 1.5f;
            }
        }
        if (face.HasValue)
        {
            var look = face.Value - eye;
            result.Yaw = FP.FromFloat_UNSAFE(Mathf.Atan2(look.x, look.z) * Mathf.Rad2Deg - dad.YawOffset.AsFloat);
            result.Pitch = FP.FromFloat_UNSAFE(-Mathf.Atan2(look.y, new Vector2(look.x, look.z).magnitude) * Mathf.Rad2Deg);
        }
        return result;
    }

    // The nearest cop is behind the van, in line with the open back door and close to it.
    static bool CopInDoorway(Frame frame)
    {
        var cop = NearestCop(frame);
        if (!cop.HasValue) return false;
        var van = frame.Get<Transform3D>(frame.GetSingletonEntityRef<Van>());
        var local = van.InverseTransformPoint(cop.Value.ToFPVector3()).ToUnityVector3();
        return local.z < -3.5f && local.z > -8f && Mathf.Abs(local.x) < 0.3f * (-2.6f - local.z) + 0.2f;
    }

    // Our eyes leaning over the serving counter, looking down at the kid at the front of the line.
    static Func<Frame, Vector3[]> WindowShot()
    {
        return f => new[] { VanPoint(f, new Vector3(-0.75f, 2.0f, -0.85f)).Value, QueueFace(f).Value + Vector3.down * 0.35f };
    }

    // Our eyes on the van roof, looking back at the nearest cop.
    static Func<Frame, Vector3[]> RoofShot()
    {
        return f =>
        {
            // From the end of the roof facing the cop, so the turret in the middle stays behind us.
            var cop = NearestCop(f) ?? VanPoint(f, new Vector3(0, 1f, -20f)).Value;
            var van = f.Get<Transform3D>(f.GetSingletonEntityRef<Van>());
            var ahead = van.InverseTransformPoint(cop.ToFPVector3()).ToUnityVector3().z > 0;
            var at = VanPoint(f, new Vector3(0.45f, 4.1f, ahead ? 1.4f : -2.3f)).Value;
            return new[] { at, cop + Vector3.down * 0.4f };
        };
    }

    static Vector3 NearestKid(Frame frame)
    {
        var from = VanPoint(frame, Vector3.zero).Value;
        var best = from + Vector3.forward * 30;
        var bestDistance = float.MaxValue;
        foreach (var pair in frame.GetComponentIterator<Npc>())
        {
            var npc = pair.Component;
            if (npc.Kind == NpcKind.Cop || npc.Kind == NpcKind.FatKid || npc.State == NpcState.Tumble || npc.State == NpcState.Home) continue;
            var position = frame.Get<Transform3D>(pair.Entity).Position.ToUnityVector3();
            if ((position - from).sqrMagnitude >= bestDistance) continue;
            bestDistance = (position - from).sqrMagnitude;
            best = position;
        }
        return best;
    }

    static int Tumbling(Frame frame)
    {
        var count = 0;
        foreach (var pair in frame.GetComponentIterator<Npc>())
        {
            if (pair.Component.Kind != NpcKind.Cop && pair.Component.State == NpcState.Tumble) count++;
        }
        return count;
    }

    static float CopToVan(Frame frame)
    {
        var van = VanPoint(frame, Vector3.zero).Value;
        var best = float.MaxValue;
        foreach (var pair in frame.GetComponentIterator<Npc>())
        {
            if (pair.Component.Kind == NpcKind.Cop) best = Mathf.Min(best, (frame.Get<Transform3D>(pair.Entity).Position.ToUnityVector3() - van).magnitude);
        }
        return best;
    }

    // From behind the nearest cop, looking past him at the van.
    static Func<Frame, Vector3[]> CopShot(float back, float height = 1.6f)
    {
        return f =>
        {
            var van = VanPoint(f, new Vector3(0, 1.2f, 0)).Value;
            var cop = NearestCop(f) ?? van + Vector3.forward * 10;
            var away = cop - van;
            away.y = 0;
            return new[] { cop + away.normalized * back + Vector3.up * height, Vector3.Lerp(cop, van, 0.5f) };
        };
    }

    // From the side of the local dad and the nearest cop, framing both.
    static Func<Frame, Vector3[]> DadShot()
    {
        return f =>
        {
            var dad = f.Get<Transform3D>(input.LocalEntity).Position.ToUnityVector3() + Vector3.up;
            var cop = NearestCop(f) ?? dad + Vector3.forward * 6;
            var between = Vector3.Lerp(dad, cop, 0.5f);
            var across = Vector3.Cross(cop - dad, Vector3.up);
            across.y = 0;
            return new[] { between + across.normalized * Mathf.Max(5f, (cop - dad).magnitude) + Vector3.up * 2f, between };
        };
    }

    static Vector3? NearestCop(Frame frame)
    {
        var from = frame.Get<Transform3D>(input.LocalEntity).Position.ToUnityVector3();
        Vector3? best = null;
        foreach (var pair in frame.GetComponentIterator<Npc>())
        {
            if (pair.Component.Kind != NpcKind.Cop) continue;
            var position = frame.Get<Transform3D>(pair.Entity).Position.ToUnityVector3() + Vector3.up * 1.5f;
            if (best.HasValue && (position - from).sqrMagnitude >= (best.Value - from).sqrMagnitude) continue;
            best = position;
        }
        return best;
    }

    static Vector3 Teammate(Frame frame)
    {
        foreach (var pair in frame.GetComponentIterator<Dad>())
        {
            if (pair.Entity != input.LocalEntity) return frame.Get<Transform3D>(pair.Entity).Position.ToUnityVector3();
        }
        return Vector3.zero;
    }

    static IEnumerable<Step> GetOut()
    {
        yield return new Step { Name = "to back door", Duration = 5f, Target = f => VanPoint(f, new Vector3(0f, 0.8f, -2.45f)) };
        yield return new Step { Name = "face door", Duration = 0.8f, LookAt = f => VanPoint(f, new Vector3(0f, 1.4f, -4f)) };
        yield return new Step { Name = "open door", Duration = 0.3f, Keys = new[] { Key.E }, LookAt = f => VanPoint(f, new Vector3(0f, 1.4f, -4f)), Skip = f => DoorOpen(f) };
        yield return new Step { Name = "step out", Duration = 5f, Target = f => VanPoint(f, new Vector3(0, 0.05f, -4.2f)) };
    }

    // From behind the van: open the back door if it is shut and walk up the step into the kitchen.
    static IEnumerable<Step> Enter()
    {
        yield return new Step { Name = "face van", Duration = 0.8f, LookAt = f => VanPoint(f, new Vector3(0f, 1.2f, -2f)) };
        yield return new Step { Name = "open door", Duration = 0.3f, Keys = new[] { Key.E }, LookAt = f => VanPoint(f, new Vector3(0f, 1.2f, -2f)), Skip = f => DoorOpen(f) };
        yield return new Step { Name = "walk in", Duration = 5f, Target = f => VanPoint(f, new Vector3(0, 0.8f, -2.3f)) };
        yield return new Step { Name = "settle in", Duration = 0.4f };
    }

    static bool DoorOpen(Frame frame)
    {
        foreach (var pair in frame.GetComponentIterator<Quantum.Fixture>())
        {
            if (pair.Component.Kind == FixtureKind.RearDoor) return pair.Component.Open;
        }
        return false;
    }

    static IEnumerable<Step> GetIn()
    {
        // Around the van's right side so the bot never walks into its bumper.
        yield return new Step { Name = "to side", Duration = 30f, Target = f => VanPoint(f, new Vector3(2.6f, 0.05f, Mathf.Clamp(LocalOfDad(f).z, -4f, 4f))) };
        yield return new Step { Name = "to corner", Duration = 10f, Target = f => VanPoint(f, new Vector3(2.4f, 0.05f, -4.4f)) };
        yield return new Step { Name = "to rear", Duration = 10f, Target = f => VanPoint(f, new Vector3(0, 0.05f, -3.9f)) };
        foreach (var step in Enter()) yield return step;
    }

    // From the sidewalk into a block along the planned path of the spot nearest to the goal (reversed).
    static Vector3[] RouteInto(Frame frame, Vector3 goal)
    {
        var settings = frame.FindAsset(frame.RuntimeConfig.DadsSettings);
        var spot = settings.PuzzleRoutes.Concat(settings.KidSpots).OrderBy(k => (k.Position.ToUnityVector3() - goal).sqrMagnitude).First();
        return spot.Path.Reverse().Select(p => p.ToUnityVector3()).Append(spot.Position.ToUnityVector3()).ToArray();
    }

    static Vector3 LocalOfDad(Frame frame)
    {
        var van = frame.Get<Transform3D>(frame.GetSingletonEntityRef<Van>());
        return van.InverseTransformPoint(frame.Get<Transform3D>(input.LocalEntity).Position).ToUnityVector3();
    }

    static Vector3 NearestRoad(Frame frame, Vector3 to)
    {
        var settings = frame.FindAsset(frame.RuntimeConfig.DadsSettings);
        return settings.RoadSpots.Select(s => s.Position.ToUnityVector3()).OrderBy(p => (p - to).sqrMagnitude).First();
    }

    static int Count<T>(Frame frame) where T : unmanaged, IComponent
    {
        var count = 0;
        foreach (var unused in frame.GetComponentIterator<T>()) count++;
        return count;
    }

    static Vector3 NearestLoot(Frame frame)
    {
        var from = frame.Get<Transform3D>(input.LocalEntity).Position.ToUnityVector3();
        var best = from;
        var bestDistance = float.MaxValue;
        foreach (var pair in frame.GetComponentIterator<Loot>())
        {
            var position = frame.Get<Transform3D>(pair.Entity).Position.ToUnityVector3();
            if ((position - from).sqrMagnitude >= bestDistance) continue;
            bestDistance = (position - from).sqrMagnitude;
            best = position;
        }
        return best;
    }

    static int TubOf(Frame frame, Treat treat)
    {
        foreach (var pair in frame.GetComponentIterator<Quantum.Fixture>())
        {
            if (pair.Component.Kind == FixtureKind.Tub && pair.Component.Treat == treat) return pair.Component.Index;
        }
        return 0;
    }

    static IEnumerable<Step> ToSeat()
    {
        yield return new Step { Name = "to aisle", Duration = 3f, Target = f => VanPoint(f, new Vector3(-0.1f, 0.8f, -1.3f)) };
        yield return new Step { Name = "to doorway", Duration = 4f, Target = f => VanPoint(f, new Vector3(-0.1f, 0.8f, 0.6f)) };
        yield return new Step { Name = "to seat", Duration = 3f, Target = f => VanPoint(f, new Vector3(-0.35f, 0.8f, 1.35f)) };
        yield return new Step { Name = "sit", Duration = 0.3f, Keys = new[] { Key.E } };
        yield return new Step { Name = "seated", Duration = 0.7f, LookPitch = 0 };
    }

    // ------------------------------------------------------------------------------------------------ world queries

    static Vector3? VanPoint(Frame frame, Vector3 local)
    {
        return frame.Get<Transform3D>(frame.GetSingletonEntityRef<Van>()).TransformPoint(local.ToFPVector3()).ToUnityVector3();
    }

    static Vector3? Tub(Frame frame, int index)
    {
        foreach (var pair in frame.GetComponentIterator<Fixture>())
        {
            if (pair.Component.Kind == FixtureKind.Tub && pair.Component.Index == index) return frame.Get<Transform3D>(pair.Entity).Position.ToUnityVector3();
        }
        return null;
    }

    static int FullestTub(Frame frame)
    {
        var best = 0;
        var count = -1;
        foreach (var pair in frame.GetComponentIterator<Fixture>())
        {
            if (pair.Component.Kind != FixtureKind.Tub || pair.Component.Count <= count) continue;
            count = pair.Component.Count;
            best = pair.Component.Index;
        }
        return best;
    }

    // The fixture of a kind (with this index, or the nearest one when index is -1). Outside the tutorial the walled-off
    // tutorial yard's puddle, patch and tree don't count.
    static Vector3 Fixture(Frame frame, FixtureKind kind, int index)
    {
        var from = frame.Get<Transform3D>(input.LocalEntity).Position.ToUnityVector3();
        var yard = frame.FindAsset(frame.RuntimeConfig.DadsSettings).TutorialPark.ToUnityVector3();
        var tutorial = frame.GetSingleton<DadsRun>().Phase == DayPhase.Tutorial;
        var best = Vector3.zero;
        var bestDistance = float.MaxValue;
        foreach (var pair in frame.GetComponentIterator<Quantum.Fixture>())
        {
            if (pair.Component.Kind != kind || (index >= 0 && pair.Component.Index != index)) continue;
            var position = frame.Get<Transform3D>(pair.Entity).Position.ToUnityVector3();
            if (!tutorial && (position - yard).sqrMagnitude < 60 * 60) continue;
            var distance = (position - from).sqrMagnitude;
            if (distance >= bestDistance) continue;
            bestDistance = distance;
            best = position;
        }
        return best;
    }

    static int QueueCount(Frame frame)
    {
        var queue = frame.GetSingleton<Van>().Queue;
        var count = 0;
        for (int i = 0; i < queue.Length; i++)
        {
            if (queue[i].IsValid && frame.Exists(queue[i])) count++;
        }
        return count;
    }

    // The first kid in line has reached their spot at the serving window.
    static bool KidAtWindow(Frame frame)
    {
        var settings = frame.FindAsset(frame.RuntimeConfig.DadsSettings);
        var spot = VanPoint(frame, settings.WindowOutside.ToUnityVector3()).Value;
        var face = QueueFace(frame).Value;
        return new Vector2(face.x - spot.x, face.z - spot.z).magnitude < 0.4f;
    }

    static Vector3? QueueFace(Frame frame)
    {
        var queue = frame.GetSingleton<Van>().Queue;
        for (int i = 0; i < queue.Length; i++)
        {
            if (!queue[i].IsValid || !frame.Exists(queue[i])) continue;
            return frame.Get<Transform3D>(queue[i]).Position.ToUnityVector3() + Vector3.up * 0.9f;
        }
        return VanPoint(frame, new Vector3(-2.2f, 1f, -0.8f));
    }

    static Vector3? Raised(Vector3 point, float height)
    {
        return point + Vector3.up * height;
    }

    // A spot `distance` short of the target on the line from the local dad.
    static Vector3? Approach(Frame frame, Vector3 target, float distance)
    {
        var position = frame.Get<Transform3D>(input.LocalEntity).Position.ToUnityVector3();
        var away = position - target;
        away.y = 0;
        return target + away.normalized * distance;
    }

    static Vector3 Park(Frame frame)
    {
        return frame.FindAsset(frame.RuntimeConfig.DadsSettings).LotPark.ToUnityVector3();
    }

    static Vector3 LotEntrance(Frame frame)
    {
        var settings = frame.FindAsset(frame.RuntimeConfig.DadsSettings);
        return Park(frame) + Quaternion.Euler(0, settings.LotYaw.AsFloat, 0) * Vector3.forward * 22;
    }

    // A road spot in The Flats about 40 m from the lot entrance.
    static Vector3 Flats(Frame frame)
    {
        var settings = frame.FindAsset(frame.RuntimeConfig.DadsSettings);
        var entrance = LotEntrance(frame);
        return settings.RoadSpots.Where(s => s.District == 0).Select(s => s.Position.ToUnityVector3())
            .OrderBy(p => Mathf.Abs((p - entrance).magnitude - 40)).First();
    }

    static bool Arrived(Frame frame, Vector3 target, float radius)
    {
        var van = frame.Get<Transform3D>(frame.GetSingletonEntityRef<Van>()).Position.ToUnityVector3();
        return new Vector2(van.x - target.x, van.z - target.z).magnitude < radius;
    }

    // Drives along the road grid: a breadth-first path over the road cell centers, steering for the next one, with the
    // lot entrance as the way in and out of Big Dairy's lot. Backs up for a moment whenever it gets stuck.
    static void Drive(Frame frame, Vector3 target, List<Key> keys, bool ram)
    {
        var settings = frame.FindAsset(frame.RuntimeConfig.DadsSettings);
        var van = frame.Get<Transform3D>(frame.GetSingletonEntityRef<Van>());
        var position = van.Position.ToUnityVector3();
        var forward = van.Forward.ToUnityVector3();
        var speed = frame.GetSingleton<Van>().Speed.AsFloat;
        var now = EditorApplication.timeSinceStartup;
        if (lastMoving == 0 || (position - lastMovingPosition).magnitude > 1 || backingUntil > now)
        {
            lastMoving = now;
            lastMovingPosition = position;
        }
        if (now - lastMoving > 2.5f) backingUntil = now + 1.5f;
        if (backingUntil > now)
        {
            keys.Add(Key.S);
            return;
        }
        var nodes = settings.RoadSpots.Select(s => s.Position.ToUnityVector3()).ToList();
        var entrance = LotEntrance(frame);
        var inLot = (position - Park(frame)).magnitude < 18;
        Vector3 next;
        if (inLot && (target - Park(frame)).magnitude > 18) next = entrance;
        else
        {
            var from = nodes.OrderBy(n => (n - position).sqrMagnitude).First();
            var to = nodes.OrderBy(n => (n - target).sqrMagnitude).First();
            var path = RoadPath(nodes, from, to);
            next = target;
            foreach (var node in path.Append(target))
            {
                var ahead = node - position;
                ahead.y = 0;
                if (ahead.magnitude < 7 || (Vector3.Dot(ahead, forward) < 0 && ahead.magnitude < 14)) continue;
                next = node;
                break;
            }
        }
        var offset = next - position;
        offset.y = 0;
        var angle = Vector3.SignedAngle(forward, offset, Vector3.up);
        if (angle > 4) keys.Add(Key.D);
        if (angle < -4) keys.Add(Key.A);
        var remaining = new Vector2(target.x - position.x, target.z - position.z).magnitude;
        var cruise = ram ? 8 : Mathf.Min(Mathf.Abs(angle) > 25 ? 5 : 11, remaining * 0.6f + 1);
        if (speed < cruise - 0.5f) keys.Add(Key.W);
        else if (speed > cruise + 1.5f) keys.Add(Key.S);
    }

    static List<Vector3> RoadPath(List<Vector3> nodes, Vector3 from, Vector3 to)
    {
        var previous = new Dictionary<Vector3, Vector3> { [from] = from };
        var open = new Queue<Vector3>();
        open.Enqueue(from);
        while (open.Count > 0)
        {
            var node = open.Dequeue();
            if (node == to) break;
            foreach (var neighbour in nodes.Where(n => (n - node).sqrMagnitude < 21 * 21 && (n - node).sqrMagnitude > 1))
            {
                if (previous.ContainsKey(neighbour)) continue;
                previous[neighbour] = node;
                open.Enqueue(neighbour);
            }
        }
        var path = new List<Vector3>();
        if (!previous.ContainsKey(to)) return path;
        for (var node = to; node != from; node = previous[node]) path.Add(node);
        path.Reverse();
        return path;
    }

    static double lastMoving;
    static Vector3 lastMovingPosition;
    static double backingUntil;

    // ------------------------------------------------------------------------------------------------ runner

    static List<Step> steps;
    static double start;
    static int stepIndex;
    static double stepStart;
    static Keyboard keyboard;
    static Mouse mouse;
    static DadsInput input;
    static Camera display;
    static Canvas hud;
    static bool outsideShot;
    static readonly Quantum.Input[] crewInputs = new Quantum.Input[4];
    static GameObject[] copCars;
    static readonly List<(float time, Vector3 position, float yaw)> vanTrail = new List<(float, Vector3, float)>();
    static readonly StringBuilder log = new StringBuilder();
    static double lastRecord;
    static int routeIndex;
    static int recordIndex;

    public static void RunFromCommandLine()
    {
        Run(Environment.GetEnvironmentVariable("PLAYTEST_SCENARIO") ?? "serve");
    }

    public static void Run(string scenario)
    {
        Directory.CreateDirectory(OutDir);
        EditorUtility.audioMasterMute = true;
        var scene = EditorSceneManager.OpenScene(ScenePath);
        foreach (var root in scene.GetRootGameObjects())
        {
            if (root.name != "Gameplay") continue;
            var serialized = new SerializedObject(root.GetComponentInChildren<DadsInput>());
            serialized.FindProperty("requireCursorLock").boolValue = false;
            serialized.ApplyModifiedPropertiesWithoutUndo();
        }
        // Scenario shortcuts live on the settings asset for this play session only; Finish puts them back.
        var settings = AssetDatabase.LoadAssetAtPath<DadsSettings>("Assets/QuantumUser/Resources/DadsSettings.asset");
        SessionState.SetString("DivorcedDads.Playtest.Restore", JsonUtility.ToJson(new Shortcuts { Money = settings.StartingMoney, DayLength = settings.DayLength.AsFloat, Day = settings.StartingDay, Tutorial = settings.Tutorial }));
        settings.Tutorial = scenario == "tutorial";
        // The tutorial scenario plays moving day even if this machine has been through it; Finish puts the flag back.
        SessionState.SetInt("DivorcedDads.Playtest.TutorialPlayed", PlayerPrefs.GetInt(TutorialMemory.PlayedKey, 0));
        PlayerPrefs.SetInt(TutorialMemory.PlayedKey, 0);
        if (scenario == "shop") settings.StartingMoney = 200;
        if (scenario == "maple") settings.StartingMoney = 400;
        if (scenario == "chaos" || scenario == "turret") settings.StartingMoney = 1500;
        if (scenario == "finale")
        {
            settings.StartingMoney = 500;
            settings.StartingDay = settings.Dues.Length;
            settings.DayLength = FP.FromFloat_UNSAFE(240);
            // A second, idle local player so there is a teammate to look at (unsaved; only this play session).
            foreach (var root in scene.GetRootGameObjects())
            {
                if (root.TryGetComponent(out QuantumRunnerLocalDebug runner)) runner.LocalPlayers = new[] { new RuntimePlayer { PlayerNickname = "Dad 1" }, new RuntimePlayer { PlayerNickname = "Dad 2" } };
            }
        }
        if (scenario == "night" || scenario == "cops" || scenario == "pitch_night" || scenario == "pitch_search") settings.DayLength = FP.FromFloat_UNSAFE(45);
        if (scenario == "pitch_gear") settings.StartingMoney = 1500;
        if (scenario == "pitch_night") settings.StartingMoney = 400;
        if (scenario == "pitch_redo") settings.StartingMoney = 1500;
        if (scenario == "pitch_gang")
        {
            settings.StartingMoney = 400;
            settings.StartingDay = 5;
            settings.DayLength = FP.FromFloat_UNSAFE(400);
        }
        if (scenario == "pitch_dusk" || scenario == "pitch_coast") settings.DayLength = FP.FromFloat_UNSAFE(200);
        if (scenario == "pitch_crew" || scenario == "pitch_redo" || scenario == "pitch_dusk" || scenario == "pitch_coast")
        {
            foreach (var root in scene.GetRootGameObjects())
            {
                if (root.TryGetComponent(out QuantumRunnerLocalDebug runner))
                    runner.LocalPlayers = Enumerable.Range(1, scenario == "pitch_crew" ? 4 : 3).Select(i => new RuntimePlayer { PlayerNickname = "Dad " + i }).ToArray();
            }
        }
        SessionState.SetString(ScenarioKey, scenario);
        EditorApplication.EnterPlaymode();
    }

    [Serializable]
    struct Shortcuts
    {
        public int Money;
        public float DayLength;
        public int Day;
        public bool Tutorial;
    }

    // Entering play mode reloads scripts, which drops static state and event hooks; pick the run back up afterwards.
    [InitializeOnLoadMethod]
    static void Resume()
    {
        if (SessionState.GetString(ScenarioKey, "") == "") return;
        AudioListener.volume = 0;
        // No Game view has focus in batch mode or a background editor, so route device input to play mode regardless.
        InputSystem.settings.editorInputBehaviorInPlayMode = InputSettings.EditorInputBehaviorInPlayMode.AllDeviceInputAlwaysGoesToGameView;
        InputSystem.settings.backgroundBehavior = InputSettings.BackgroundBehavior.IgnoreFocus;
        keyboard = InputSystem.AddDevice<Keyboard>();
        mouse = InputSystem.AddDevice<Mouse>();
        EditorApplication.update += Tick;
    }

    static void Tick()
    {
        if (!EditorApplication.isPlaying) return;
        AudioListener.volume = 0;
        var now = EditorApplication.timeSinceStartup;
        var scenario = SessionState.GetString(ScenarioKey, "");
        if (start == 0)
        {
            start = now;
            stepStart = now;
            steps = scenario == "tour" ? Tour() : scenario == "shop" ? Shop() : scenario == "night" ? Night() : scenario == "maple" ? Maple() : scenario == "chaos" ? Chaos() : scenario == "ride" ? Ride() : scenario == "finale" ? Finale() : scenario == "cops" ? Cops() : scenario == "tutorial" ? Tutorial() : scenario == "ladder" ? Ladder() : scenario == "lamps" ? Lamps() : scenario == "flats" ? Flats() : scenario == "turret" ? Turret() : scenario == "debug" ? DebugMenu() : scenario == "pitch_day" ? PitchDay() : scenario == "pitch_gear" ? PitchGear() : scenario == "pitch_night" ? PitchNight() : scenario == "pitch_crew" ? PitchCrew() : scenario == "pitch_redo" ? PitchRedo() : scenario == "pitch_dusk" ? PitchDusk() : scenario == "pitch_search" ? PitchSearch() : scenario == "pitch_cars" ? PitchCars() : scenario == "pitch_gang" ? PitchGang() : scenario == "pitch_coast" ? PitchCoast() : Serve();
            Log($"play mode started: {scenario}");
        }
        if (now - start > (scenario.StartsWith("pitch") ? 900 : 420))
        {
            Finish("timed out");
            return;
        }
        var game = QuantumRunner.Default?.Game;
        if (game == null || game.Frames.Predicted == null) return;
        if (input == null)
        {
            foreach (var root in UnityEngine.SceneManagement.SceneManager.GetActiveScene().GetRootGameObjects())
            {
                if (root.name == "Gameplay") input = root.GetComponentInChildren<DadsInput>();
                if (root.name == "Display Camera") display = root.GetComponent<Camera>();
                if (root.name == "HUD") hud = root.GetComponent<Canvas>();
            }
        }
        var frame = game.Frames.Predicted;
        var step = steps[stepIndex];
        var keys = new List<Key>(step.Keys ?? Array.Empty<Key>());
        var mouseDelta = Vector2.zero;
        var eyeCamera = DadsCamera.Instance;
        var vanTransform = frame.Get<Transform3D>(frame.GetSingletonEntityRef<Van>());
        vanTrail.Add((Time.time, vanTransform.Position.ToUnityVector3(), vanTransform.Rotation.ToUnityQuaternion().eulerAngles.y));
        if (step.CopCars) PlaceCopCars();
        else if (copCars != null) foreach (var car in copCars) car.SetActive(false);
        var shot = step.Shot?.Invoke(frame);
        var crew = step.Crew?.Invoke(frame);
        for (int slot = 1; slot < crewInputs.Length; slot++)
        {
            var puppet = crew != null && slot - 1 < crew.Length ? crew[slot - 1] : null;
            crewInputs[slot] = puppet.HasValue ? PuppetInput(frame, slot, puppet.Value) : new Quantum.Input();
        }
        DadsInput.BotInput = slot => crewInputs[slot];
        eyeCamera.enabled = !step.CameraAt.HasValue && shot == null;
        if (step.CameraAt.HasValue) eyeCamera.transform.SetPositionAndRotation(step.CameraAt.Value, Quaternion.LookRotation(step.CameraLook.Value - step.CameraAt.Value));
        if (input.LocalEntity.IsValid && !step.CameraAt.HasValue)
        {
            var dad = frame.Get<Dad>(input.LocalEntity);
            var position = frame.Get<Transform3D>(input.LocalEntity).Position.ToUnityVector3();
            var currentYaw = input.Yaw + dad.YawOffset.AsFloat;
            var desiredYaw = currentYaw;
            var walkTarget = step.Target?.Invoke(frame);
            if (step.Route != null)
            {
                var route = step.Route(frame);
                while (routeIndex < route.Length && new Vector2(route[routeIndex].x - position.x, route[routeIndex].z - position.z).magnitude < 0.6f) routeIndex++;
                if (routeIndex < route.Length) walkTarget = route[routeIndex];
            }
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
            if (lookAt.HasValue && !keys.Contains(Key.W))
            {
                var look = lookAt.Value - eyeCamera.transform.position;
                desiredYaw = Mathf.Atan2(look.x, look.z) * Mathf.Rad2Deg;
                desiredPitch = -Mathf.Atan2(look.y, new Vector2(look.x, look.z).magnitude) * Mathf.Rad2Deg;
            }
            if (step.DriveTo != null)
            {
                Drive(frame, step.DriveTo(frame).Value, keys, step.Ram);
                desiredYaw = frame.Get<Transform3D>(frame.GetSingletonEntityRef<Van>()).Rotation.ToUnityQuaternion().eulerAngles.y;
                desiredPitch = 0;
            }
            var yawError = Mathf.DeltaAngle(currentYaw, desiredYaw);
            var pitchError = desiredPitch.HasValue ? desiredPitch.Value - input.Pitch : 0;
            mouseDelta = new Vector2(yawError, -pitchError) / 0.12f * 0.5f;
        }
        if (shot != null) eyeCamera.transform.SetPositionAndRotation(shot[0], Quaternion.LookRotation(shot[1] - shot[0]));
        if ((shot != null && !step.Fps) != outsideShot)
        {
            // DadsCamera hides our own body in first person; show it (and drop the HUD) while the camera is outside.
            outsideShot = shot != null && !step.Fps;
            hud.enabled = !outsideShot;
            if (outsideShot) eyeCamera.GetComponent<Camera>().fieldOfView = 50;
            eyeCamera.GetComponentInChildren<DadsViewModel>(true).gameObject.SetActive(!outsideShot);
            var viewUpdater = (QuantumEntityViewUpdater)new SerializedObject(eyeCamera).FindProperty("viewUpdater").objectReferenceValue;
            foreach (var renderer in viewUpdater.GetView(input.LocalEntity).GetComponentsInChildren<Renderer>(true)) renderer.enabled = outsideShot;
        }
        if (step.Done != null && step.Done(frame)) stepStart = now - step.Duration;
        InputSystem.QueueStateEvent(keyboard, new KeyboardState(keys.ToArray()));
        var mouseState = new MouseState { delta = mouseDelta };
        if (step.Fire) mouseState = mouseState.WithButton(MouseButton.Left);
        if (step.Aim) mouseState = mouseState.WithButton(MouseButton.Right);
        InputSystem.QueueStateEvent(mouse, mouseState);
        if (step.Record && now - lastRecord > 0.1)
        {
            lastRecord = now;
            Directory.CreateDirectory(System.IO.Path.Combine(OutDir, "frames", step.Name));
            Capture(System.IO.Path.Combine(OutDir, "frames", step.Name, $"{recordIndex++:D4}.png"), 640, 360);
        }

        if (now - stepStart < step.Duration) return;
        if (step.Snap && crew != null) Log($"crew local positions: {string.Join(" ", Enumerable.Range(1, crew.Length).Select(i => LocalOf(frame, Puppeteer(frame, i)).ToString("F1")))}");
        step.Stage?.Invoke(frame);
        if (step.Snap && scenario.StartsWith("pitch")) Capture(System.IO.Path.Combine(OutDir, step.Name + ".png"), 1920, 1080);
        else if (step.Snap) Capture(System.IO.Path.Combine(OutDir, step.Name + ".png"), 1280, 720);
        Log($"step '{step.Name}' done: {State(frame)}");
        stepIndex++;
        while (stepIndex < steps.Count && steps[stepIndex].Skip != null && steps[stepIndex].Skip(frame))
        {
            Log($"step '{steps[stepIndex].Name}' skipped");
            stepIndex++;
        }
        stepStart = now;
        routeIndex = 0;
        if (stepIndex >= steps.Count) Finish("all steps done");
    }

    static string State(Frame frame)
    {
        var run = frame.GetSingleton<DadsRun>();
        var van = frame.GetSingleton<Van>();
        var vanPosition = frame.Get<Transform3D>(frame.GetSingletonEntityRef<Van>()).Position.ToUnityVector3();
        var kids = 0;
        var cops = 0;
        var states = new Dictionary<NpcState, int>();
        var fedText = "";
        var nearest = float.MaxValue;
        foreach (var pair in frame.GetComponentIterator<Npc>())
        {
            if (pair.Component.Kind == NpcKind.Cop) cops++;
            else kids++;
            states[pair.Component.State] = states.TryGetValue(pair.Component.State, out var n) ? n + 1 : 1;
            if (pair.Component.Fed > 0 || pair.Component.State == NpcState.Queue) fedText += $"[{pair.Component.Kind} {pair.Component.State} fed {pair.Component.Fed}/{pair.Component.Hunger} wants {pair.Component.Wants}]";
            nearest = Mathf.Min(nearest, (frame.Get<Transform3D>(pair.Entity).Position.ToUnityVector3() - vanPosition).magnitude);
        }
        var tubs = "";
        foreach (var pair in frame.GetComponentIterator<Loot>())
        {
            var local = frame.Get<Transform3D>(frame.GetSingletonEntityRef<Van>()).InverseTransformPoint(frame.Get<Transform3D>(pair.Entity).Position).ToUnityVector3();
            tubs += $"<loot {pair.Component.Item.Kind} vanLocal {local:F1} resting {pair.Component.Resting} riding {frame.Has<Riding>(pair.Entity)}>";
        }
        foreach (var pair in frame.GetComponentIterator<Quantum.Fixture>())
        {
            if (pair.Component.Kind == FixtureKind.Tub) tubs += $"[{pair.Component.Treat} {pair.Component.Count}]";
        }
        var dadText = "";
        if (input.LocalEntity.IsValid)
        {
            var dad = frame.Get<Dad>(input.LocalEntity);
            var position = frame.Get<Transform3D>(input.LocalEntity).Position.ToUnityVector3();
            var hotbar = "";
            for (int i = 0; i < dad.Hotbar.Length; i++)
            {
                var item = dad.Hotbar[i];
                if (item.Kind != DadItem.None) hotbar += $"[{i + 1}:{item.Kind} {item.Count} {item.Scoops[0]}]";
            }
            var facing = frame.Get<Transform3D>(input.LocalEntity).Rotation.ToUnityQuaternion().eulerAngles.y;
            var vanYaw = frame.Get<Transform3D>(frame.GetSingletonEntityRef<Van>()).Rotation.ToUnityQuaternion().eulerAngles.y;
            var toQueue = QueueFace(frame).Value - position;
            dadText = $"yaw {facing:F0} van {vanYaw:F0} queueDir {Mathf.Atan2(toQueue.x, toQueue.z) * Mathf.Rad2Deg:F0} inputYaw {input.Yaw:F0} offset {dad.YawOffset.AsFloat:F0} | dad {position:F1} local {LocalOfDad(frame):F2} climbing {dad.Climbing} driving {dad.Driving} onVan {dad.Standing == frame.GetSingletonEntityRef<Van>()} hotbar {hotbar}";
        }
        return $"fps {1f / Time.smoothDeltaTime:F0} tick {frame.Number} {run.Phase} lesson {run.Lesson} day {run.Day} clock {run.Clock.AsFloat:F2} money {run.Money} debt {run.Debt} due {run.Due} fed {run.KidsFed} heat {run.Heat.AsFloat:F1} | van {vanPosition:F1} speed {van.Speed.AsFloat:F1} damage {van.Damage.AsFloat:F2} hopper {van.HopperRounds} upgrades pistol {run.Pistol} shotgun {run.Shotgun} cone {run.ConeSize} speaker {run.Loudspeaker} minigun {run.Minigun} permits {run.Permits} jingle {van.Jingle} queue {QueueCount(frame)} | kids {kids} ({string.Join(",", states.Select(p => p.Key + ":" + p.Value))}, nearest {nearest:F0}m) cops {cops} {fedText} tubs {tubs} | {dadText}";
    }

    // Renders the PS1 game camera, then the display camera (dithered game image plus HUD) into a texture of the given size.
    static void Capture(string path, int width, int height)
    {
        DadsCamera.Instance.GetComponent<Camera>().Render();
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
        var line = $"[DadsPlaytest] {message}";
        Debug.Log(line);
        log.AppendLine(line);
    }

    static void Finish(string reason)
    {
        Log("finished: " + reason);
        File.WriteAllText(System.IO.Path.Combine(OutDir, $"playtest_{SessionState.GetString(ScenarioKey, "")}.txt"), log.ToString());
        log.Clear();
        EditorApplication.update -= Tick;
        SessionState.SetString(ScenarioKey, "");
        var restore = JsonUtility.FromJson<Shortcuts>(SessionState.GetString("DivorcedDads.Playtest.Restore", "{}"));
        var settings = AssetDatabase.LoadAssetAtPath<DadsSettings>("Assets/QuantumUser/Resources/DadsSettings.asset");
        settings.StartingMoney = restore.Money;
        settings.DayLength = FP.FromFloat_UNSAFE(restore.DayLength);
        settings.StartingDay = restore.Day;
        settings.Tutorial = restore.Tutorial;
        PlayerPrefs.SetInt(TutorialMemory.PlayedKey, SessionState.GetInt("DivorcedDads.Playtest.TutorialPlayed", 0));
        InputSystem.RemoveDevice(keyboard);
        InputSystem.RemoveDevice(mouse);
        start = 0;
        stepIndex = 0;
        input = null;
        outsideShot = false;
        DadsInput.BotInput = null;
        copCars = null;
        vanTrail.Clear();
        if (Application.isBatchMode) EditorApplication.Exit(0);
        else EditorApplication.ExitPlaymode();
    }
}
