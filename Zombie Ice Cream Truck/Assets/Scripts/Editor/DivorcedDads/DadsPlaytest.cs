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
// lamps (drives out of the lot and mows down a street lamp), ladder (a jump under the kitchen ceiling, up the ladder onto the roof, back down through the hatch, out the back door
// and in again).
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
        if (scenario == "chaos") settings.StartingMoney = 1500;
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
        if (scenario == "night" || scenario == "cops") settings.DayLength = FP.FromFloat_UNSAFE(45);
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
            steps = scenario == "tour" ? Tour() : scenario == "shop" ? Shop() : scenario == "night" ? Night() : scenario == "maple" ? Maple() : scenario == "chaos" ? Chaos() : scenario == "ride" ? Ride() : scenario == "finale" ? Finale() : scenario == "cops" ? Cops() : scenario == "tutorial" ? Tutorial() : scenario == "ladder" ? Ladder() : scenario == "lamps" ? Lamps() : scenario == "flats" ? Flats() : Serve();
            Log($"play mode started: {scenario}");
        }
        if (now - start > 420)
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
            }
        }
        var frame = game.Frames.Predicted;
        var step = steps[stepIndex];
        var keys = new List<Key>(step.Keys ?? Array.Empty<Key>());
        var mouseDelta = Vector2.zero;
        var eyeCamera = DadsCamera.Instance;
        eyeCamera.enabled = !step.CameraAt.HasValue;
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
        if (step.Snap) Capture(System.IO.Path.Combine(OutDir, step.Name + ".png"), 1280, 720);
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
        return $"fps {1f / Time.smoothDeltaTime:F0} tick {frame.Number} {run.Phase} lesson {run.Lesson} day {run.Day} clock {run.Clock.AsFloat:F2} money {run.Money} debt {run.Debt} due {run.Due} fed {run.KidsFed} heat {run.Heat.AsFloat:F1} | van {vanPosition:F1} speed {van.Speed.AsFloat:F1} damage {van.Damage.AsFloat:F2} jingle {van.Jingle} queue {QueueCount(frame)} | kids {kids} ({string.Join(",", states.Select(p => p.Key + ":" + p.Value))}, nearest {nearest:F0}m) cops {cops} {fedText} tubs {tubs} | {dadText}";
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
        if (Application.isBatchMode) EditorApplication.Exit(0);
        else EditorApplication.ExitPlaymode();
    }
}
