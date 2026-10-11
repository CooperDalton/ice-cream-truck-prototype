using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
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
// (auto-drives area 1 to the depot, buys an upgrade, rolls out), hotshop (scoops ice cream into the fuel intake, drives
// through the hot spots to Kevin's depot, talks to Kevin, plays the slots, buys from the stall, rolls out), melee (walks
// up to the nearest zombie with the starting cone and bonks it), scenery (walks into the nearest scenery
// building and logs how close it got to the middle of its biggest wall), offroad (steers the truck off the road at the
// nearest scenery building and logs where it stopped), tutorial (plays the first-run tutorial start to finish: milk and
// sugar into the churn, a tub into the freezer, scoops into the fuel intake, the practice zombie, the driver's seat).
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
        // Steers the truck at this world point with the throttle down.
        public Func<Frame, Vector3?> DriveTo;
        public bool Record;
        // World-space walk and look targets, recomputed every tick; null leaves that control alone.
        public Func<Frame, Vector3?> Target;
        public Func<Frame, Vector3?> LookAt;
        // Ends the step early once true; Duration becomes a timeout.
        public Func<Frame, bool> Done;
        // Checked when the step comes up; the step is skipped (no input at all) if false.
        public Func<Frame, bool> When;
    }

    // PLAYTEST_SCENARIO=freezer grabs scoops from the freezer with E, packs three into a pint and puts the other five
    // back with E as a part-full tub (the freezer prompt in the captures lists the tubs).
    static readonly List<Step> FreezerSteps = new List<Step>
    {
        new Step { Name = "settle", Duration = 2.5f },
        new Step { Name = "to freezer", Duration = 3f, WalkTo = new Vector3(-0.05f, 0.8f, -2.2f) },
        new Step { Name = "face freezer", Duration = 1f, LookYaw = -90, LookPitch = 35 },
        new Step { Name = "f01_before", Duration = 0.2f, Snap = true, LookYaw = -90, LookPitch = 35 },
        new Step { Name = "grab with E", Duration = 0.3f, Keys = new[] { Key.E } },
        new Step { Name = "f02_grabbed", Duration = 0.5f, Snap = true, LookYaw = -90, LookPitch = 35 },
        new Step { Name = "to counter", Duration = 3f, WalkTo = new Vector3(-0.05f, 0.8f, -1.0f) },
        new Step { Name = "face counter", Duration = 1f, LookYaw = -90, LookPitch = 40, Keys = new[] { Key.Digit4 } },
        new Step { Name = "pack 1", Duration = 0.25f, Fire = true }, new Step { Name = "release", Duration = 0.2f },
        new Step { Name = "pack 2", Duration = 0.25f, Fire = true }, new Step { Name = "release", Duration = 0.2f },
        new Step { Name = "pack 3", Duration = 0.25f, Fire = true }, new Step { Name = "release", Duration = 0.2f },
        new Step { Name = "back to freezer", Duration = 3f, WalkTo = new Vector3(-0.05f, 0.8f, -2.2f) },
        new Step { Name = "face freezer again", Duration = 1f, LookYaw = -90, LookPitch = 35 },
        new Step { Name = "put back with E", Duration = 0.3f, Keys = new[] { Key.E } },
        new Step { Name = "f03_put_back", Duration = 0.5f, Snap = true, LookYaw = -90, LookPitch = 35 },
    };

    // PLAYTEST_SCENARIO=kitchen runs the ammo loop: scoop from the freezer, pack a pint, reload, throw a grenade.
    static readonly List<Step> KitchenSteps = new List<Step>
    {
        new Step { Name = "k01_start", Duration = 2.5f, Snap = true },
        new Step { Name = "to freezer", Duration = 3f, WalkTo = new Vector3(-0.05f, 0.8f, -2.2f) },
        new Step { Name = "face freezer", Duration = 1f, LookYaw = -90, LookPitch = 35 },
        new Step { Name = "k02_freezer", Duration = 0.2f, Snap = true, LookYaw = -90, LookPitch = 35 },
        new Step { Name = "scoop", Duration = 1f, Fire = true },
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
        new Step { Name = "scoop again", Duration = 0.3f, LookYaw = -90, LookPitch = 35 },
        new Step { Name = "to freezer 2", Duration = 3f, WalkTo = new Vector3(-0.05f, 0.8f, -2.2f) },
        new Step { Name = "face freezer 2", Duration = 1f, LookYaw = -90, LookPitch = 35 },
        new Step { Name = "scoop 2", Duration = 1f, Fire = true },
        new Step { Name = "select scoops", Duration = 0.3f, Keys = new[] { Key.Digit4 }, LookYaw = 0, LookPitch = -10 },
        new Step { Name = "wind up throw", Duration = 0.8f, Keys = new[] { Key.Q } },
        new Step { Name = "throw", Duration = 2.5f, Record = true },
        new Step { Name = "k05_thrown", Duration = 0.2f, Snap = true },
    };

    static List<Step> DriveSteps() => new List<Step> { new Step { Name = "01_kitchen", Duration = 2.5f, Snap = true } }
        .Concat(ClimbUp()).Concat(new[]
    {
        new Step { Name = "02_roof", Duration = 0.5f, Snap = true, LookPitch = 10 },
        new Step { Name = "fire", Duration = 1.5f, Fire = true, LookPitch = 12 },
        new Step { Name = "03_roof_fired", Duration = 0.3f, Snap = true },
    }).Concat(ClimbDown()).Concat(new[]
    {
        new Step { Name = "to aisle", Duration = 3f, WalkTo = new Vector3(-0.1f, 0.8f, -1.3f) },
        new Step { Name = "to doorway", Duration = 4f, WalkTo = new Vector3(-0.1f, 0.8f, 0.6f) },
        new Step { Name = "to seat", Duration = 3f, WalkTo = new Vector3(-0.35f, 0.8f, 1.35f) },
        new Step { Name = "sit", Duration = 0.3f, Keys = new[] { Key.E } },
        new Step { Name = "04_driving", Duration = 1f, Snap = true, LookPitch = 0, LookYaw = 0 },
        new Step { Name = "drive", Duration = 4f, Keys = new[] { Key.W } },
        new Step { Name = "05_driving_fast", Duration = 0.2f, Keys = new[] { Key.W }, Snap = true },
        new Step { Name = "drive", Duration = 6f, Keys = new[] { Key.W } },
        new Step { Name = "06_driving_far", Duration = 0.2f, Keys = new[] { Key.W }, Snap = true },
        new Step { Name = "coast", Duration = 5f },
        new Step { Name = "leave seat", Duration = 0.3f, Keys = new[] { Key.E } },
        new Step { Name = "07_cab", Duration = 1f, Snap = true },
    }).ToList();

    // Out the rear door (opening it if shut) and down the ramp onto the road.
    static Step[] ExitBack()
    {
        return new[]
        {
            new Step { Name = "to back door", Duration = 3f, WalkTo = new Vector3(0f, 0.8f, -2.4f) },
            new Step { Name = "face door", Duration = 0.6f, LookAt = f => (Vector3?)f.Get<Transform3D>(f.GetSingletonEntityRef<Truck>()).TransformPoint(new Vector3(0, 1.6f, -2.95f).ToFPVector3()).ToUnityVector3(), When = f => !StationOpen(f, StationKind.RearDoor) },
            new Step { Name = "open door", Duration = 0.4f, Keys = new[] { Key.E }, LookAt = f => (Vector3?)f.Get<Transform3D>(f.GetSingletonEntityRef<Truck>()).TransformPoint(new Vector3(0, 1.6f, -2.95f).ToFPVector3()).ToUnityVector3(), When = f => !StationOpen(f, StationKind.RearDoor) },
            new Step { Name = "out the back", Duration = 4f, WalkTo = new Vector3(0f, 0.05f, -4.6f) },
        };
    }

    // From anywhere outside: round to the back, open the door if shut, and up the ramp into the kitchen.
    static Step[] EnterBack()
    {
        return new[]
        {
            new Step { Name = "to back of truck", Duration = 10f, Target = f => (Vector3?)f.Get<Transform3D>(f.GetSingletonEntityRef<Truck>()).TransformPoint(new Vector3(0, 0, -4.8f).ToFPVector3()).ToUnityVector3() },
            new Step { Name = "face door", Duration = 0.6f, LookAt = f => (Vector3?)f.Get<Transform3D>(f.GetSingletonEntityRef<Truck>()).TransformPoint(new Vector3(0, 1.4f, -2.95f).ToFPVector3()).ToUnityVector3(), When = f => !StationOpen(f, StationKind.RearDoor) },
            new Step { Name = "open door", Duration = 0.4f, Keys = new[] { Key.E }, LookAt = f => (Vector3?)f.Get<Transform3D>(f.GetSingletonEntityRef<Truck>()).TransformPoint(new Vector3(0, 1.4f, -2.95f).ToFPVector3()).ToUnityVector3(), When = f => !StationOpen(f, StationKind.RearDoor) },
            new Step { Name = "up the ramp", Duration = 4f, WalkTo = new Vector3(0f, 0.8f, -2.3f) },
        };
    }

    // From the kitchen: open the hatch if shut, grab the ladder and climb out onto the roof.
    static Step[] ClimbUp()
    {
        return new[]
        {
            new Step { Name = "to ladder", Duration = 3f, WalkTo = new Vector3(0.62f, 0.8f, -2.35f) },
            new Step { Name = "face hatch", Duration = 0.8f, LookAt = f => (Vector3?)f.Get<Transform3D>(f.GetSingletonEntityRef<Truck>()).TransformPoint(new Vector3(0.74f, 2.95f, -2.42f).ToFPVector3()).ToUnityVector3(), When = f => !StationOpen(f, StationKind.Hatch) },
            new Step { Name = "open hatch", Duration = 0.4f, Keys = new[] { Key.E }, LookAt = f => (Vector3?)f.Get<Transform3D>(f.GetSingletonEntityRef<Truck>()).TransformPoint(new Vector3(0.74f, 2.95f, -2.42f).ToFPVector3()).ToUnityVector3(), When = f => !StationOpen(f, StationKind.Hatch) },
            new Step { Name = "face ladder", Duration = 0.6f, LookYaw = 90, LookPitch = 0 },
            new Step { Name = "grab ladder", Duration = 0.3f, Keys = new[] { Key.E }, LookYaw = 90, LookPitch = 0 },
            new Step { Name = "climb", Duration = 5f, Keys = new[] { Key.W }, Done = f => !f.Get<Survivor>(input.LocalEntity).Climbing },
            new Step { Name = "settle", Duration = 0.5f, LookPitch = 10 },
        };
    }

    // From the roof: to the open hatch, grab the ladder and climb down into the kitchen.
    static Step[] ClimbDown()
    {
        return new[]
        {
            new Step { Name = "to hatch", Duration = 4f, WalkTo = new Vector3(0.74f, 2.95f, -1.75f) },
            new Step { Name = "grab ladder", Duration = 0.3f, Keys = new[] { Key.E }, LookPitch = 0 },
            new Step { Name = "climb down", Duration = 5f, Keys = new[] { Key.S }, Done = f => !f.Get<Survivor>(input.LocalEntity).Climbing },
            new Step { Name = "settle", Duration = 0.5f },
        };
    }

    static bool StationOpen(Frame frame, StationKind kind)
    {
        foreach (var pair in frame.GetComponentIterator<Station>())
        {
            if (pair.Component.Kind == kind) return pair.Component.Open;
        }
        throw new InvalidOperationException($"No {kind} station");
    }

    static readonly Step[] ToSeat =
    {
        new Step { Name = "to aisle", Duration = 3f, WalkTo = new Vector3(-0.1f, 0.8f, -1.3f) },
        new Step { Name = "to doorway", Duration = 4f, WalkTo = new Vector3(-0.1f, 0.8f, 0.6f) },
        new Step { Name = "to seat", Duration = 3f, WalkTo = new Vector3(-0.35f, 0.8f, 1.35f) },
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
        };
        steps.AddRange(ClimbUp());
        steps.AddRange(new[]
        {
            new Step { Name = "wait for zombies", Duration = 15f, LookAt = NearestZombie, Done = f => NearestZombie(f).HasValue && (NearestZombie(f).Value - Camera.main.transform.position).magnitude < 20 },
            new Step { Name = "s03_roof_aim", Duration = 0.6f, Snap = true, LookAt = NearestZombie, Aim = true },
            new Step { Name = "roof_fire", Duration = 5f, LookAt = NearestZombie, Fire = true, Record = true },
            new Step { Name = "s04_roof_after", Duration = 0.2f, Snap = true, LookAt = NearestZombie },
            new Step { Name = "reload", Duration = 0.5f, Keys = new[] { Key.R } },
            new Step { Name = "roof_fire2", Duration = 4f, LookAt = NearestZombie, Fire = true, Record = true },
        });
        steps.AddRange(ClimbDown());
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
        steps.AddRange(ExitBack());
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

    // Fuels the truck from the freezer, then drives through area 1's hot spots to the depot and shops at Kevin's stall.
    static unsafe List<Step> HotShopSteps()
    {
        var steps = new List<Step>
        {
            new Step { Name = "h00_start", Duration = 2f, Snap = true },
            new Step { Name = "to freezer", Duration = 3f, WalkTo = new Vector3(-0.05f, 0.8f, -2.2f) },
            new Step { Name = "face freezer", Duration = 1f, LookYaw = -90, LookPitch = 35 },
            new Step { Name = "scoop", Duration = 1f, Fire = true },
            new Step { Name = "to aisle", Duration = 3f, WalkTo = new Vector3(-0.1f, 0.8f, -1.3f) },
            new Step { Name = "to doorway", Duration = 4f, WalkTo = new Vector3(-0.1f, 0.8f, 0.6f) },
            new Step { Name = "to intake", Duration = 3f, WalkTo = new Vector3(0.2f, 0.8f, 1.35f) },
            new Step { Name = "select scoops", Duration = 0.6f, Keys = new[] { Key.Digit4 }, LookAt = f => Raised(StationOf(f, StationKind.FuelIntake), 0.9f) },
            new Step { Name = "h01_intake", Duration = 0.3f, Snap = true, LookAt = f => Raised(StationOf(f, StationKind.FuelIntake), 0.9f) },
            new Step { Name = "feed scoops", Duration = 0.3f, Keys = new[] { Key.E }, LookAt = f => Raised(StationOf(f, StationKind.FuelIntake), 0.9f) },
            new Step { Name = "select pint", Duration = 0.4f, Keys = new[] { Key.Digit2 }, LookAt = f => Raised(StationOf(f, StationKind.FuelIntake), 0.9f) },
            new Step { Name = "feed pint", Duration = 0.3f, Keys = new[] { Key.E }, LookAt = f => Raised(StationOf(f, StationKind.FuelIntake), 0.9f) },
            new Step { Name = "h02_fueled", Duration = 1f, Snap = true, LookAt = f => Raised(StationOf(f, StationKind.FuelIntake), 0.9f) },
            new Step { Name = "to seat", Duration = 3f, WalkTo = new Vector3(-0.35f, 0.8f, 1.35f) },
            new Step { Name = "sit", Duration = 0.3f, Keys = new[] { Key.E } },
            new Step { Name = "seated", Duration = 0.7f, LookPitch = 0, LookYaw = 0 },
            new Step { Name = "drive to hot spot", Duration = 120f, AutoDrive = true, Done = f => HotSpotTriggered(f) },
            new Step { Name = "horde", Duration = 1.5f, AutoDrive = true, LookYaw = -65, LookPitch = 5 },
            new Step { Name = "h03_horde", Duration = 0.2f, AutoDrive = true, Snap = true, LookYaw = -65, LookPitch = 5 },
            new Step { Name = "drive through", Duration = 6f, AutoDrive = true, Record = true },
            new Step { Name = "h04_after_horde", Duration = 0.2f, AutoDrive = true, Snap = true },
            new Step { Name = "drive to depot", Duration = 240f, AutoDrive = true, Done = f => f.Global->Phase == GamePhase.Depot },
            new Step { Name = "h05_parked", Duration = 1.5f, Snap = true },
            new Step { Name = "leave seat", Duration = 0.3f, Keys = new[] { Key.E } },
        };
        for (int i = 0; i < 5; i++) steps.Add(new Step { Name = $"settle {i}", Duration = 0.15f });
        steps.Add(new Step { Name = "to doorway", Duration = 4f, WalkTo = new Vector3(-0.1f, 0.8f, 0.6f) });
        steps.Add(new Step { Name = "to aisle", Duration = 4f, WalkTo = new Vector3(-0.1f, 0.8f, -1.3f) });
        steps.AddRange(ExitBack());
        steps.Add(new Step { Name = "settle", Duration = 0.7f });
        steps.Add(new Step { Name = "to kevin", Duration = 30f, Target = f => InFront(f, StationOf(f, StationKind.Shopkeeper), 2.2f), LookAt = f => Raised(StationOf(f, StationKind.Shopkeeper), 1.5f) });
        steps.Add(new Step { Name = "talk", Duration = 0.3f, Keys = new[] { Key.E }, LookAt = f => Raised(StationOf(f, StationKind.Shopkeeper), 1.5f) });
        steps.Add(new Step { Name = "h06_kevin", Duration = 1.2f, Snap = true, LookAt = f => Raised(StationOf(f, StationKind.Shopkeeper), 1.4f) });
        steps.Add(new Step { Name = "to slots", Duration = 15f, Target = f => InFront(f, StationOf(f, StationKind.SlotMachine), 1.3f), LookAt = f => Raised(StationOf(f, StationKind.SlotMachine), 1.25f) });
        steps.Add(new Step { Name = "pull", Duration = 0.3f, Keys = new[] { Key.E }, LookAt = f => Raised(StationOf(f, StationKind.SlotMachine), 1.25f) });
        steps.Add(new Step { Name = "h07_spinning", Duration = 0.7f, Snap = true, LookAt = f => Raised(StationOf(f, StationKind.SlotMachine), 1.25f) });
        steps.Add(new Step { Name = "h08_result", Duration = 2.2f, Snap = true, Record = true, LookAt = f => Raised(StationOf(f, StationKind.SlotMachine), 1.25f) });
        // Three brains on the slots let a zombie loose; deal with it first.
        steps.Add(new Step { Name = "pistol", Duration = 0.4f, Keys = new[] { Key.Digit1 } });
        steps.Add(new Step { Name = "defend", Duration = 15f, LookAt = NearestZombie, Fire = true, Done = f => !NearestZombie(f).HasValue });
        steps.Add(new Step { Name = "to stall", Duration = 20f, Target = f => InFront(f, AffordableStall(f), 1.1f), LookAt = f => Raised(AffordableStall(f), 0.3f) });
        steps.Add(new Step { Name = "h09_stall", Duration = 0.8f, Snap = true, LookAt = f => Raised(AffordableStall(f), 0.3f) });
        steps.Add(new Step { Name = "buy", Duration = 0.3f, Keys = new[] { Key.E }, LookAt = f => Raised(AffordableStall(f), 0.3f) });
        steps.Add(new Step { Name = "h10_bought", Duration = 1.5f, Snap = true });
        steps.Add(new Step { Name = "to road", Duration = 15f, Target = f => InFront(f, StationOf(f, StationKind.SlotMachine), 4f) });
        steps.Add(new Step { Name = "to exit", Duration = 40f, Target = f => Approach(f, StationOf(f, StationKind.DepotExit), 1.2f), LookAt = f => Raised(StationOf(f, StationKind.DepotExit), 1.2f) });
        steps.Add(new Step { Name = "roll out", Duration = 0.3f, Keys = new[] { Key.E }, LookAt = f => Raised(StationOf(f, StationKind.DepotExit), 1.2f) });
        steps.Add(new Step { Name = "h11_next_area", Duration = 2f, Snap = true });
        return steps;
    }

    // Steps out the back with the starting cone and bonks whatever zombie comes close first.
    static List<Step> MeleeSteps()
    {
        return ExitBack().Concat(new[]
        {
            new Step { Name = "cone", Duration = 0.5f, Keys = new[] { Key.Digit3 } },
            new Step { Name = "m01_cone", Duration = 0.3f, Snap = true, LookPitch = 0 },
            // Zombies up the road idle until they notice someone, so go to them.
            new Step { Name = "go to a zombie", Duration = 90f, Target = f => Approach(f, ClosestZombie(f), 1.5f), LookAt = NearestZombie, Done = f => NearestZombie(f).HasValue && (NearestZombie(f).Value - Camera.main.transform.position).magnitude < 3f },
            new Step { Name = "bonk", Duration = 4f, LookAt = NearestZombie, Fire = true, Record = true },
            new Step { Name = "m02_after", Duration = 0.2f, Snap = true, LookAt = NearestZombie },
        }).ToList();
    }

    static unsafe List<Step> TutorialSteps()
    {
        Func<Frame, Vector3?> churn = f => Raised(StationOf(f, StationKind.Churn), 0.9f);
        var steps = new List<Step> { new Step { Name = "t00_start", Duration = 2f, Snap = true } };
        foreach (var ingredient in new[] { ItemKind.MilkCrate, ItemKind.SugarSack })
        {
            steps.AddRange(ExitBack());
            steps.Add(new Step { Name = $"to {ingredient}", Duration = 10f, Target = f => Approach(f, PickupOf(f, ingredient), 1f), LookAt = f => Raised(PickupOf(f, ingredient), 0.2f) });
            steps.Add(new Step { Name = $"t01_{ingredient}", Duration = 0.3f, Snap = true, LookAt = f => Raised(PickupOf(f, ingredient), 0.2f) });
            steps.Add(new Step { Name = "pick up", Duration = 0.3f, Keys = new[] { Key.E }, LookAt = f => Raised(PickupOf(f, ingredient), 0.2f) });
            steps.AddRange(EnterBack());
            steps.Add(new Step { Name = "to churn", Duration = 4f, WalkTo = new Vector3(-0.1f, 0.8f, 0.4f) });
            steps.Add(new Step { Name = "face churn", Duration = 0.8f, LookAt = churn });
            steps.Add(new Step { Name = "into churn", Duration = 0.3f, Keys = new[] { Key.E }, LookAt = churn });
        }
        steps.Add(new Step { Name = "t02_churn", Duration = 0.3f, Snap = true, LookAt = churn });
        steps.Add(new Step { Name = "crank", Duration = 10f, Fire = true, Wiggle = true, LookAt = churn, Done = f => f.Global->Tutorial > TutorialStep.Crank });
        steps.Add(new Step { Name = "settle", Duration = 1.5f });
        steps.Add(new Step { Name = "t03_tub", Duration = 0.3f, Snap = true, LookAt = f => PickupOf(f, ItemKind.Tub) });
        steps.Add(new Step { Name = "take tub", Duration = 0.3f, Keys = new[] { Key.E }, LookAt = f => PickupOf(f, ItemKind.Tub) });
        steps.Add(new Step { Name = "to freezer", Duration = 4f, WalkTo = new Vector3(-0.05f, 0.8f, -2.2f) });
        steps.Add(new Step { Name = "face freezer", Duration = 1f, LookYaw = -90, LookPitch = 35 });
        steps.Add(new Step { Name = "tub in", Duration = 0.3f, Keys = new[] { Key.E }, LookYaw = -90, LookPitch = 35 });
        steps.Add(new Step { Name = "scoop", Duration = 1f, Fire = true, Done = f => f.Global->Tutorial > TutorialStep.Scoop });
        steps.Add(new Step { Name = "to aisle", Duration = 3f, WalkTo = new Vector3(-0.1f, 0.8f, -1.3f) });
        steps.Add(new Step { Name = "to doorway", Duration = 4f, WalkTo = new Vector3(-0.1f, 0.8f, 0.6f) });
        steps.Add(new Step { Name = "to intake", Duration = 3f, WalkTo = new Vector3(0.2f, 0.8f, 1.35f) });
        steps.Add(new Step { Name = "select scoops", Duration = 0.6f, Keys = new[] { Key.Digit4 }, LookAt = f => Raised(StationOf(f, StationKind.FuelIntake), 0.9f) });
        steps.Add(new Step { Name = "feed", Duration = 0.3f, Keys = new[] { Key.E }, LookAt = f => Raised(StationOf(f, StationKind.FuelIntake), 0.9f) });
        steps.Add(new Step { Name = "t04_fueled", Duration = 1f, Snap = true });
        steps.Add(new Step { Name = "to doorway", Duration = 4f, WalkTo = new Vector3(-0.1f, 0.8f, 0.6f) });
        steps.Add(new Step { Name = "to aisle", Duration = 4f, WalkTo = new Vector3(-0.1f, 0.8f, -1.3f) });
        steps.AddRange(ExitBack());
        steps.Add(new Step { Name = "cone", Duration = 0.5f, Keys = new[] { Key.Digit3 } });
        steps.Add(new Step { Name = "t05_zombie", Duration = 0.3f, Snap = true, LookAt = NearestZombie });
        steps.Add(new Step { Name = "wait for zombie", Duration = 30f, LookAt = NearestZombie, Done = f => NearestZombie(f).HasValue && (NearestZombie(f).Value - Camera.main.transform.position).magnitude < 2.5f });
        steps.Add(new Step { Name = "bonk", Duration = 8f, LookAt = NearestZombie, Fire = true, Record = true, Done = f => f.Global->Kills > 0 });
        steps.Add(new Step { Name = "t06_seat_next", Duration = 1f, Snap = true });
        steps.AddRange(EnterBack());
        steps.AddRange(ToSeat);
        steps.Add(new Step { Name = "t07_running", Duration = 3f, Snap = true });
        return steps;
    }

    // The pickup of this kind nearest the truck (stops and hot spots up the road hold the same items).
    static Vector3? PickupOf(Frame frame, ItemKind kind)
    {
        var truck = frame.Get<Transform3D>(frame.GetSingletonEntityRef<Truck>()).Position.ToUnityVector3();
        Vector3? best = null;
        foreach (var pair in frame.GetComponentIterator<Pickup>())
        {
            if (pair.Component.Item.Kind != kind) continue;
            var position = frame.Get<Transform3D>(pair.Entity).Position.ToUnityVector3();
            if (best.HasValue && (position - truck).sqrMagnitude >= (best.Value - truck).sqrMagnitude) continue;
            best = position;
        }
        return best;
    }

    // Walks forward standing, then crouches (C) and walks back crouched, logging the crouch flag and walking speed each way.
    static List<Step> CrouchSteps()
    {
        Func<string, Func<Frame, bool>> report = label => f =>
        {
            var survivor = f.Get<Survivor>(input.LocalEntity);
            var speed = f.Get<CharacterController3D>(input.LocalEntity).Velocity;
            Log($"{label}: crouching {survivor.Crouching} speed {new Vector2(speed.X.AsFloat, speed.Z.AsFloat).magnitude:F2} eye {Camera.main.transform.position.y - f.Get<Transform3D>(input.LocalEntity).Position.Y.AsFloat:F2}");
            return false;
        };
        return new List<Step>
        {
            new Step { Name = "c01_standing", Duration = 2f, Snap = true, LookYaw = 0, LookPitch = 0 },
            new Step { Name = "walk standing", Duration = 1.5f, Keys = new[] { Key.W }, Done = report("standing") },
            new Step { Name = "crouch", Duration = 0.6f, Keys = new[] { Key.C } },
            new Step { Name = "walk crouched", Duration = 1.5f, Keys = new[] { Key.C, Key.S }, Done = report("crouched") },
            new Step { Name = "c02_crouched", Duration = 0.2f, Snap = true, Keys = new[] { Key.C } },
        };
    }

    // Out the back to watch the zombies up the road idle (recorded), then close to about 20 m of the nearest one and fire
    // a shot into the air: the shot should wake the ones within earshot.
    static List<Step> ZombieSteps()
    {
        return ExitBack().Concat(new[]
        {
            new Step { Name = "clear of the truck", Duration = 6f, Target = f => (Vector3?)f.Get<Transform3D>(f.GetSingletonEntityRef<Truck>()).TransformPoint(new Vector3(-6, 0, -6).ToFPVector3()).ToUnityVector3() },
            new Step { Name = "wait for zombies", Duration = 20f, LookAt = NearestZombie },
            new Step { Name = "watch", Duration = 12f, LookAt = NearestZombie, Record = true },
            new Step { Name = "close in", Duration = 30f, Target = f => Approach(f, ClosestZombie(f), 20f), Done = f => (ClosestZombie(f).Value - f.Get<Transform3D>(input.LocalEntity).Position.ToUnityVector3()).magnitude < 21f },
            new Step { Name = "before the shot", Duration = 0.3f },
            new Step { Name = "shoot into the air", Duration = 0.6f, Fire = true, LookPitch = -40 },
            new Step { Name = "after the shot", Duration = 4f },
        }).ToList();
    }

    // Grabs the tutorial milk crate, walks sideways into the ramp from beside it (which used to slip players underneath),
    // then goes round the back and walks in, logging where it gets to every half second.
    static List<Step> DoorwaySteps()
    {
        var steps = ExitBack().ToList();
        steps.Add(new Step { Name = "to crate", Duration = 10f, Target = f => Approach(f, PickupOf(f, ItemKind.MilkCrate), 1f), LookAt = f => Raised(PickupOf(f, ItemKind.MilkCrate), 0.2f) });
        steps.Add(new Step { Name = "pick up", Duration = 0.3f, Keys = new[] { Key.E }, LookAt = f => Raised(PickupOf(f, ItemKind.MilkCrate), 0.2f) });
        // Come at the ramp from the side, the way that used to wedge players under it.
        steps.Add(new Step { Name = "beside the ramp", Duration = 6f, Target = f => (Vector3?)f.Get<Transform3D>(f.GetSingletonEntityRef<Truck>()).TransformPoint(new Vector3(-2.2f, 0, -3.4f).ToFPVector3()).ToUnityVector3() });
        for (int i = 0; i < 6; i++)
        {
            steps.Add(new Step { Name = $"across the ramp {i}", Duration = 0.5f, Target = f => (Vector3?)f.Get<Transform3D>(f.GetSingletonEntityRef<Truck>()).TransformPoint(new Vector3(0.5f, 0, -3.4f).ToFPVector3()).ToUnityVector3() });
        }
        steps.Add(new Step { Name = "d00_beside", Duration = 0.3f, Snap = true });
        steps.Add(new Step { Name = "round the back", Duration = 6f, Target = f => (Vector3?)f.Get<Transform3D>(f.GetSingletonEntityRef<Truck>()).TransformPoint(new Vector3(0, 0, -5f).ToFPVector3()).ToUnityVector3() });
        for (int i = 0; i < 8; i++)
        {
            steps.Add(new Step { Name = $"walk in {i}", Duration = 0.5f, Target = f => (Vector3?)f.Get<Transform3D>(f.GetSingletonEntityRef<Truck>()).TransformPoint(new Vector3(0, 0.8f, -1.8f).ToFPVector3()).ToUnityVector3() });
        }
        steps.Add(new Step { Name = "d01_in", Duration = 0.3f, Snap = true });
        return steps;
    }

    // Takes the wheel and right-clicks the music box off and on again.
    static List<Step> MusicSteps()
    {
        var steps = new List<Step>(ToSeat);
        steps.Add(new Step { Name = "music off", Duration = 0.3f, Aim = true });
        steps.Add(new Step { Name = "m01_music_off", Duration = 0.5f, Snap = true });
        steps.Add(new Step { Name = "music on", Duration = 0.3f, Aim = true });
        steps.Add(new Step { Name = "m02_music_on", Duration = 0.5f, Snap = true });
        return steps;
    }

    static List<Step> ScenerySteps()
    {
        return ExitBack().Concat(new[]
        {
            new Step { Name = "walk into building", Duration = 25f, Target = SceneryWall, LookAt = f => Raised(SceneryWall(f), 1.2f) },
            new Step { Name = "c01_blocked", Duration = 0.3f, Snap = true, LookAt = f => Raised(SceneryWall(f), 1.2f) },
            new Step { Name = "check", Duration = 0.1f, Done = f =>
            {
                var position = f.Get<Transform3D>(input.LocalEntity).Position.ToUnityVector3();
                var wall = SceneryWall(f).Value;
                Log($"survivor {position:F2} wall center {wall:F2} distance {(new Vector2(position.x, position.z) - new Vector2(wall.x, wall.z)).magnitude:F2}");
                return true;
            } },
        }).ToList();
    }

    static List<Step> OffroadSteps()
    {
        var steps = new List<Step>(ToSeat);
        steps.Add(new Step { Name = "o01_seated", Duration = 0.2f, Snap = true });
        steps.Add(new Step { Name = "drive at building", Duration = 12f, DriveTo = SceneryWall, Record = true });
        steps.Add(new Step { Name = "o02_after", Duration = 0.5f, Snap = true });
        steps.Add(new Step { Name = "check", Duration = 0.1f, Done = f =>
        {
            var truck = f.Get<Transform3D>(f.GetSingletonEntityRef<Truck>()).Position.ToUnityVector3();
            var wall = SceneryWall(f).Value;
            Log($"truck {truck:F2} wall center {wall:F2} distance {(new Vector2(truck.x, truck.z) - new Vector2(wall.x, wall.z)).magnitude:F2}");
            // The same overlap the truck's crash check runs, placed on the wall.
            var hits = f.Physics3D.OverlapShape((wall + Vector3.up * 1.5f).ToFPVector3(), Photon.Deterministic.FPQuaternion.Identity, Shape3D.CreateBox(Photon.Deterministic.FPVector3.One), -1, QueryOptions.HitAll);
            var scenery = 0;
            for (int i = 0; i < hits.Count; i++) scenery += hits[i].Entity.IsValid && f.Has<Scenery>(hits[i].Entity) ? 1 : 0;
            Log($"overlap at the wall: {hits.Count} hits, {scenery} on scenery");
            return true;
        } });
        return steps;
    }

    // Center of the biggest collider box of the scenery block nearest the truck, in world space at ground level.
    static unsafe Vector3? SceneryWall(Frame frame)
    {
        var settings = frame.FindAsset(frame.RuntimeConfig.Settings);
        var truck = frame.Get<Transform3D>(frame.GetSingletonEntityRef<Truck>()).Position.ToUnityVector3();
        Vector3? best = null;
        var bestDistance = float.MaxValue;
        foreach (var pair in frame.GetComponentIterator<Scenery>())
        {
            var transform = frame.Get<Transform3D>(pair.Entity);
            var distance = (transform.Position.ToUnityVector3() - truck).sqrMagnitude;
            if (distance >= bestDistance) continue;
            var biggest = settings.SceneryColliders.Where(b => b.Block == pair.Component.Block).OrderByDescending(b => (b.Extents.X * b.Extents.Z).AsFloat).First();
            bestDistance = distance;
            var center = transform.TransformPoint(biggest.Center).ToUnityVector3();
            best = new Vector3(center.x, 0, center.z);
        }
        return best;
    }

    // The living zombie nearest the local survivor at any distance.
    static Vector3? ClosestZombie(Frame frame)
    {
        var position = frame.Get<Transform3D>(input.LocalEntity).Position.ToUnityVector3();
        Vector3? best = null;
        foreach (var pair in frame.GetComponentIterator<Zombie>())
        {
            if (pair.Component.State == ZombieState.Dead) continue;
            var zombie = frame.Get<Transform3D>(pair.Entity).Position.ToUnityVector3();
            if (best.HasValue && (zombie - position).sqrMagnitude >= (best.Value - position).sqrMagnitude) continue;
            best = zombie;
        }
        return best;
    }

    // What the truck's body overlaps right now (the same query as its crash check), for the crash log.
    static unsafe string CrashedInto(Frame frame)
    {
        var settings = frame.FindAsset(frame.RuntimeConfig.Settings);
        var truckEntity = frame.GetSingletonEntityRef<Truck>();
        var truck = frame.Get<Transform3D>(truckEntity);
        var probe = truck.Position + truck.Forward * Photon.Deterministic.FP._0_50 + Photon.Deterministic.FPVector3.Up * Photon.Deterministic.FP._1_50;
        var body = Shape3D.CreateBox(new Photon.Deterministic.FPVector3(settings.TruckHalfSize.X, Photon.Deterministic.FP._0_75, settings.TruckHalfSize.Z));
        var hits = frame.Physics3D.OverlapShape(probe, truck.Rotation, body, -1, QueryOptions.HitAll);
        var found = new List<string>();
        for (int i = 0; i < hits.Count; i++)
        {
            var hit = hits[i].Entity;
            if (!hit.IsValid || hit == truckEntity) continue;
            if (frame.TryGet(hit, out RoadChunk chunk)) found.Add($"road chunk {chunk.Kind} #{chunk.Index}");
            else if (frame.TryGet(hit, out Scenery scenery)) found.Add($"scenery block {scenery.Block} at cell {scenery.CellX},{scenery.CellY}");
            else if (frame.TryGet(hit, out Station station) && !frame.Has<Attached>(hit)) found.Add($"station {station.Kind}");
        }
        return found.Count == 0 ? "nothing solid (zombie crowd?)" : string.Join(", ", found.Distinct());
    }

    static unsafe bool HotSpotTriggered(Frame frame)
    {
        foreach (var pair in frame.GetComponentIterator<RoadChunk>())
        {
            if (pair.Component.Triggered) return true;
        }
        return false;
    }

    // The cheapest affordable item stand on Kevin's stall (pedestals without an upgrade).
    static unsafe Vector3? AffordableStall(Frame frame)
    {
        Vector3? best = null;
        var bestPrice = int.MaxValue;
        foreach (var pair in frame.GetComponentIterator<Station>())
        {
            var station = pair.Component;
            if (station.Kind != StationKind.Shop || station.Upgrade != UpgradeKind.None || station.Slots[0].Kind == ItemKind.None) continue;
            if (station.Price > frame.Global->Money || station.Price >= bestPrice) continue;
            bestPrice = station.Price;
            best = frame.Get<Transform3D>(pair.Entity).Position.ToUnityVector3();
        }
        return best;
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

    // A spot `distance` in front of the station standing at `position` (stations face the people using them).
    static Vector3? InFront(Frame frame, Vector3? position, float distance)
    {
        if (!position.HasValue) return null;
        foreach (var pair in frame.GetComponentIterator<Station>())
        {
            var transform = frame.Get<Transform3D>(pair.Entity);
            var at = transform.Position.ToUnityVector3();
            if ((at - position.Value).sqrMagnitude < 0.01f) return at + transform.Forward.ToUnityVector3() * distance;
        }
        return null;
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
    static int whenChecked = -1;
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
    const string TutorialPrefKey = "ZombieTruck.Playtest.TutorialDone";

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
        // Every scenario but the tutorial ones (doorway uses the tutorial crate) starts on the road (unsaved; only
        // this play session).
        foreach (var root in scene.GetRootGameObjects())
        {
            if (root.TryGetComponent(out QuantumRunnerLocalDebug runner)) runner.RuntimeConfig.SkipTutorial = !new[] { "tutorial", "doorway", "tutorialskip" }.Contains(Environment.GetEnvironmentVariable("PLAYTEST_SCENARIO"));
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
        // The tutorial runs need it unplayed on this machine; the saved progress is put back when the run finishes.
        // tutorialskip plays as a returning player who has done it.
        var scenarioName = Environment.GetEnvironmentVariable("PLAYTEST_SCENARIO");
        if (scenarioName == "tutorial" || scenarioName == "doorway" || scenarioName == "tutorialskip")
        {
            SessionState.SetInt(TutorialPrefKey, PlayerPrefs.GetInt(TutorialProgress.DoneKey, 0));
            PlayerPrefs.SetInt(TutorialProgress.DoneKey, scenarioName == "tutorialskip" ? 1 : 0);
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
            steps = scenario == "kitchen" ? KitchenSteps : scenario == "freezer" ? FreezerSteps : scenario == "showcase" ? ShowcaseSteps() : scenario == "depot" ? DepotSteps() : scenario == "cab" ? CabSteps()
                : scenario == "hotshop" ? HotShopSteps() : scenario == "melee" ? MeleeSteps() : scenario == "scenery" ? ScenerySteps()
                : scenario == "offroad" ? OffroadSteps() : scenario == "tutorial" ? TutorialSteps() : scenario == "crouch" ? CrouchSteps() : scenario == "zombies" ? ZombieSteps() : scenario == "doorway" ? DoorwaySteps()
                : scenario == "tutorialskip" ? new List<Step> { new Step { Name = "x01_returning", Duration = 3f, Snap = true } }
                : scenario == "music" ? MusicSteps() : DriveSteps();
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
        // Checked once when the step comes up, before any of its input is sent.
        if (step.When != null && whenChecked != stepIndex)
        {
            whenChecked = stepIndex;
            if (!step.When(frame))
            {
                Log($"step '{step.Name}' skipped");
                stepIndex++;
                stepStart = now;
                if (stepIndex >= steps.Count) Finish("all steps done");
                return;
            }
        }
        // A crash bounces the truck backwards from speed, so a sudden sign flip at speed marks one.
        var truckSpeed = frame.GetSingleton<Truck>().Speed.AsFloat;
        if (lastTruckSpeed > 3 && truckSpeed < 0) Log($"truck crashed at {lastTruckSpeed:F1} m/s into {CrashedInto(frame)}");
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
            var driveTo = step.DriveTo?.Invoke(frame);
            if (driveTo.HasValue)
            {
                var truckForward = truck.Forward.ToUnityVector3();
                var toTarget = driveTo.Value - truck.Position.ToUnityVector3();
                var angle = Vector3.SignedAngle(new Vector3(truckForward.x, 0, truckForward.z), new Vector3(toTarget.x, 0, toTarget.z), Vector3.up);
                keys.Add(Key.W);
                if (angle > 3) keys.Add(Key.D);
                if (angle < -3) keys.Add(Key.A);
            }
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
        var idle = 0;
        foreach (var pair in frame.GetComponentIterator<Zombie>())
        {
            zombies++;
            if (pair.Component.State == ZombieState.Dead) dead++;
            if (pair.Component.State == ZombieState.Idle) idle++;
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
        return $"tick {frame.Number} tutorial {(frame.Global->Phase == GamePhase.Tutorial ? frame.Global->Tutorial.ToString() : "-")} truck {truckPosition:F1} speed {truck.Speed.AsFloat:F1} fuel {truck.Fuel.AsFloat:F1} {truck.FuelFlavor} music {(truck.MusicOff ? "off" : "on")} zombies {zombies} (dead {dead}, idle {idle}) chunks {chunks} kills {frame.Global->Kills} money {frame.Global->Money} phase {frame.Global->Phase} | {survivorText}";
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
        if (SessionState.GetInt(TutorialPrefKey, -1) >= 0)
        {
            PlayerPrefs.SetInt(TutorialProgress.DoneKey, SessionState.GetInt(TutorialPrefKey, 0));
            PlayerPrefs.Save();
        }
        EditorApplication.update -= Tick;
        SessionState.SetBool(ActiveKey, false);
        EditorApplication.Exit(0);
    }
}
