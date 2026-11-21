using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using Quantum;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.UI;
using Object = UnityEngine.Object;

// Stages the heist pitch screenshots in the game scene, so they go through its PS1 camera chain, lighting and HUD, from
// the PS1 art (Art/Tools/zombie-styles) and writes them to Library/CodexPlaytests/pitch/. The scene is reopened for
// every shot and never saved.
// Run: Tools > Zombie Truck > Capture Pitch Shots, or PitchShots.Capture("<shot>") for one shot. Tools > Zombie Truck >
// Capture Pitch Map renders a town from above with its icon positions; Art/Tools/zombie-styles/pitch_map.py draws the map.
public static class PitchShots
{
    const string ScenePath = "Assets/QuantumUser/Scenes/QuantumGameScene.unity";
    const string Art = "Assets/Art/PS1";
    const string Sprites = "Assets/Art/Sprites";
    const string OutDir = "Library/CodexPlaytests/pitch";
    const int Width = 1920;
    const int Height = 1080;
    const string Truck = "Ice Cream Truck";

    // The truck stands at the origin facing +Z with its serving window on the -X side, on a road along Z.
    static readonly (string name, Action<Shot> build)[] Shots =
    {
        ("01_serving_window", ServingWindow),
        ("02_police_chase", PoliceChase),
        ("03_cop_on_board", CopOnBoard),
        ("04_kevin", Kevin),
        ("05_harbor", Harbor),
        ("06_overview", Overview),
        ("07_shooting_kids", ShootingKids),
        ("08_scavenge", Scavenge),
        ("09_kitchen_crew", KitchenCrew),
        ("10_kids_in_the_road", KidsInTheRoad),
        ("11_slippery_cops", SlipperyCops),
        ("12_coop_chaos", CoopChaos),
        ("13_truck_upgrades", TruckUpgrades),
        ("14_weapon_stall", WeaponStall),
        ("15_run_over", RunOver),
    };

    static readonly string[] TownLeft = { "Houses", "Candy Shop", "Park", "Houses", "Diner", "Houses", "Apartments", "Houses" };
    static readonly string[] TownRight = { "Diner", "Houses", "Houses", "Apartments", "Park", "Houses", "Candy Shop", "Houses" };
    static readonly string[] RuralLeft = { "Meadow", "Forest", "Cornfield", "Meadow", "Forest", "Barn", "Forest", "Cornfield" };
    static readonly string[] RuralRight = { "Forest", "Cornfield", "Barn", "Forest", "Water Tower", "Meadow", "Forest", "Forest" };
    static readonly string[] CoastLeft = { "Houses", "Diner", "Park", "Candy Shop" };
    static readonly string[] CoastRight = { "Apartments", "Houses", "Diner", "Park" };

    class Shot
    {
        public Transform Root;
        public Camera Camera;
        public Light Sun;
        public GameHud Hud;
        public ViewModel ViewModel;
        public GameObject Environment;
    }

    [MenuItem("Tools/Zombie Truck/Capture Pitch Shots")]
    public static void CaptureAll()
    {
        foreach (var shot in Shots) Capture(shot.name);
    }

    public static void Capture(string name)
    {
        var build = Shots.First(s => s.name == name).build;
        var (shot, display) = Open();
        Hold(shot, ItemKind.None, Flavor.None);
        build(shot);

        shot.Camera.Render();
        Canvas.ForceUpdateCanvases();
        var target = RenderTexture.GetTemporary(Width, Height, 24);
        display.targetTexture = target;
        display.Render();
        display.targetTexture = null;
        Save(target, name);
        RenderTexture.ReleaseTemporary(target);
    }

    // The town on the area map, from the entrance to the town line, in road order. Chunks are 20 m long and curves turn the
    // road 90 degrees, as in Run.AddChunk.
    static readonly ChunkKind[] MapRoad =
    {
        ChunkKind.Straight, ChunkKind.School, ChunkKind.CurveRight, ChunkKind.Straight, ChunkKind.Junction, ChunkKind.Park, ChunkKind.Straight,
        ChunkKind.CurveLeft, ChunkKind.Straight, ChunkKind.Broken, ChunkKind.CurveRight, ChunkKind.Rural, ChunkKind.Rural, ChunkKind.Rural, ChunkKind.Rural,
    };
    static readonly string[] MapTown = { "Houses", "Diner", "Candy Shop", "Apartments", "Park", "Houses" };
    static readonly string[] MapRural = { "Barn", "Cornfield", "Water Tower", "Forest", "Meadow", "Forest" };

    // Everything on the area map: road chunk, position and facing in that chunk's frame (x to the right of the road, z
    // along it), the model standing there (null: icon only) and the icon pitch_map.py draws there ("kind" or
    // "kind detail"; null: model only).
    static readonly (int chunk, float x, float z, float turn, string category, string model, string icon)[] MapActors =
    {
        (1, 0, 0, 0, "Truck", Truck, "truck"),
        (1, -2.6f, -1, 90, "Characters", "Kid Pigtails", null),
        (1, -3.0f, 0.4f, 110, "Characters", "Kid Cap", null),
        (1, -2.8f, -2, 70, "Characters", "Kid Curly", null),
        (1, -3.8f, -0.5f, 95, "Characters", "Kid Hoodie", null),
        (1, -4.2f, -2.2f, 45, "Characters", "Kid Glasses", null),
        (1, -4, -1, 0, null, null, "kids 5"),
        (1, -6, 9, 150, "Characters", "Detective", "detective"),
        (1, -0.7f, -0.8f, 0, null, null, "aboard 1"),
        (1, 0.4f, -2, 0, null, null, "aboard 2"),
        (1, -10, 5, 120, "Characters", "Crew Carry Mint", "crew 3"),
        (0, 1.6f, -6, 0, "Vehicles", "Police Car", "patrol"),
        (4, -13, 0, 90, "Vehicles", "Police Car", "patrol"),
        (5, -8, -3, 90, "Characters", "Kid Pigtails", null),
        (5, -7, -1, 100, "Characters", "Kid Glasses", null),
        (5, -8.5f, 1.5f, 80, "Characters", "Kid Curly", null),
        (5, -7.5f, 3, 95, "Characters", "Kid Cap", null),
        (5, -7.8f, 0, 0, null, null, "kids 4"),
        (6, -4, 6, 200, "Characters", "Police Officer", "cop"),
        (12, 6, -9, 180, "Heist", "Town Line Sign", null),
        (12, 0, -10, 0, null, null, "townline"),
        (13, 6, 4, -100, "Vehicles", "Police Car", "parked"),
        (13, -2.5f, -3.5f, 180, "Characters", "Police Officer", "cop"),
        (14, 0, 6, 0, null, null, "exit"),
    };
    static readonly Vector2 MapMin = new Vector2(-35, -10);
    static readonly Vector2 MapMax = new Vector2(188, 129);
    const float MapPixelsPerMeter = 10f;

    [MenuItem("Tools/Zombie Truck/Capture Pitch Map")]
    public static void CaptureMap()
    {
        var (shot, _) = Open();
        shot.ViewModel.gameObject.SetActive(false);
        RenderSettings.fog = false;
        var chunks = new List<(Vector3 center, float heading, ChunkKind kind)>();
        var end = new Vector3(0, 0, -10);
        var heading = 0f;
        foreach (var kind in MapRoad)
        {
            var rotation = Quaternion.Euler(0, heading, 0);
            var center = end + rotation * Vector3.forward * 10;
            Place(shot, Prefab($"Chunk {kind}"), center, heading);
            chunks.Add((center, heading, kind));
            var exit = kind == ChunkKind.CurveLeft ? Vector3.left : kind == ChunkKind.CurveRight ? Vector3.right : Vector3.forward;
            end = center + rotation * exit * 10;
            if (kind == ChunkKind.CurveLeft) heading -= 90;
            if (kind == ChunkKind.CurveRight) heading += 90;
        }
        MapScenery(shot, chunks);

        var width = Mathf.RoundToInt((MapMax.x - MapMin.x) * MapPixelsPerMeter);
        var height = Mathf.RoundToInt((MapMax.y - MapMin.y) * MapPixelsPerMeter);
        var camera = shot.Camera;
        var middle = (MapMin + MapMax) / 2;
        camera.transform.SetPositionAndRotation(new Vector3(middle.x, 120, middle.y), Quaternion.Euler(90, 0, 0));
        camera.orthographic = true;
        camera.orthographicSize = (MapMax.y - MapMin.y) / 2;
        camera.nearClipPlane = 1;
        camera.farClipPlane = 200;
        var target = RenderTexture.GetTemporary(width, height, 24);
        camera.targetTexture = target;
        camera.aspect = (float)width / height;

        var icons = new List<string>();
        foreach (var actor in MapActors)
        {
            var chunk = chunks[actor.chunk];
            var position = chunk.center + Quaternion.Euler(0, chunk.heading, 0) * new Vector3(actor.x, 0, actor.z);
            var yaw = chunk.heading + actor.turn;
            if (actor.model != null) Place(shot, Model(actor.category, actor.model), position, yaw);
            if (actor.icon == null) continue;
            var pixel = camera.WorldToViewportPoint(position);
            icons.Add(string.Format(CultureInfo.InvariantCulture, "  {{\"icon\": \"{0}\", \"x\": {1:F1}, \"y\": {2:F1}, \"yaw\": {3}}}",
                actor.icon, pixel.x * width, (1 - pixel.y) * height, Mathf.RoundToInt(Mathf.Repeat(yaw, 360))));
        }
        camera.Render();
        camera.targetTexture = null;
        Save(target, "map_base");
        RenderTexture.ReleaseTemporary(target);
        File.WriteAllText(Path.Combine(OutDir, "map_icons.json"),
            $"{{\"pixelsPerMeter\": {MapPixelsPerMeter.ToString(CultureInfo.InvariantCulture)},\n \"icons\": [\n{string.Join(",\n", icons)}\n]}}\n");
    }

    // Fills the grid cells within four cells of the road with scenery blocks facing the nearest road cell, like
    // Run.UpdateScenery: set pieces (school, park) spill into the cell on their chunk's left, and a junction's side road
    // leads into a side street there.
    static void MapScenery(Shot shot, List<(Vector3 center, float heading, ChunkKind kind)> chunks)
    {
        var road = chunks.Select(c => (x: Mathf.RoundToInt(c.center.x / 20), y: Mathf.RoundToInt(c.center.z / 20), c.kind)).ToList();
        var taken = new HashSet<(int, int)>(road.Select(r => (r.x, r.y)));
        var sideStreets = new Dictionary<(int, int), (int x, int y)>();
        for (int i = 0; i < chunks.Count; i++)
        {
            var left = Quaternion.Euler(0, chunks[i].heading, 0) * Vector3.left;
            var cell = (road[i].x + Mathf.RoundToInt(left.x), road[i].y + Mathf.RoundToInt(left.z));
            if (road[i].kind == ChunkKind.School || road[i].kind == ChunkKind.Park) taken.Add(cell);
            if (road[i].kind == ChunkKind.Junction) sideStreets[cell] = (road[i].x, road[i].y);
        }
        foreach (var cell in road)
        {
            for (int dx = -4; dx <= 4; dx++)
            {
                for (int dy = -4; dy <= 4; dy++)
                {
                    var target = (x: cell.x + dx, y: cell.y + dy);
                    if (!taken.Add(target)) continue;
                    string block;
                    (int x, int y) faces;
                    if (sideStreets.TryGetValue(target, out var junction))
                    {
                        block = "Side Street";
                        faces = junction;
                    }
                    else
                    {
                        var nearest = road.OrderBy(r => Math.Max(Math.Abs(r.x - target.x), Math.Abs(r.y - target.y)))
                            .ThenBy(r => Math.Abs(r.x - target.x) + Math.Abs(r.y - target.y)).First();
                        faces = (nearest.x, nearest.y);
                        var choices = nearest.kind == ChunkKind.Rural ? MapRural : MapTown;
                        var hash = target.x * 73856093 ^ target.y * 19349663;
                        block = choices[(hash % choices.Length + choices.Length) % choices.Length];
                    }
                    var toRoad = new Vector2(faces.x - target.x, faces.y - target.y);
                    var direction = Mathf.Abs(toRoad.x) > Mathf.Abs(toRoad.y) ? new Vector3(Mathf.Sign(toRoad.x), 0, 0) : new Vector3(0, 0, Mathf.Sign(toRoad.y));
                    Place(shot, Prefab($"Scenery {block}"), new Vector3(target.x * 20, 0, target.y * 20), Quaternion.LookRotation(direction).eulerAngles.y);
                }
            }
        }
    }

    // Opens the game scene for staging: drops the gameplay objects and finds the camera, display camera, sun, HUD and
    // view model.
    static (Shot shot, Camera display) Open()
    {
        var scene = EditorSceneManager.OpenScene(ScenePath, OpenSceneMode.Single);
        var shot = new Shot { Root = new GameObject("Pitch Shot").transform };
        Camera display = null;
        foreach (var root in scene.GetRootGameObjects())
        {
            if (root.name == "Gameplay") Object.DestroyImmediate(root);
            else if (root.name == "Environment") shot.Environment = root;
            else if (root.name == "Display Camera") display = root.GetComponent<Camera>();
            else if (root.TryGetComponent(out FirstPersonCamera firstPerson)) shot.Camera = root.GetComponent<Camera>();
            else if (root.TryGetComponent(out Light light)) shot.Sun = light;
            else if (root.TryGetComponent(out GameHud hud)) shot.Hud = hud;
        }
        shot.ViewModel = shot.Camera.GetComponentInChildren<ViewModel>(true);
        return (shot, display);
    }

    static void Save(RenderTexture target, string name)
    {
        var previous = RenderTexture.active;
        RenderTexture.active = target;
        var texture = new Texture2D(target.width, target.height, TextureFormat.RGB24, false);
        texture.ReadPixels(new Rect(0, 0, target.width, target.height), 0, 0);
        texture.Apply();
        RenderTexture.active = previous;
        Directory.CreateDirectory(OutDir);
        File.WriteAllBytes(Path.Combine(OutDir, name + ".png"), texture.EncodeToPNG());
        Object.DestroyImmediate(texture);
        Debug.Log($"PitchShots: wrote {name}");
    }

    // ------------------------------------------------------------------------------------------------ shots

    // Characters face +Z as imported, so yaw 90 faces +X (toward the truck's serving window from the sidewalk).
    static void ServingWindow(Shot shot)
    {
        Street(shot, -3, 4, TownLeft, TownRight);
        TruckAt(shot, Vector3.zero, 0);
        KidCrowd(shot);
        Hold(shot, ItemKind.PlainCone, Flavor.None);
        Look(shot, new Vector3(-0.8f, 2.4f, -0.8f), new Vector3(-4, 0.6f, -0.8f), 75);
        Hud(shot, 340, 500, "TOWN 2", 0, "MAPLEWOOD: MAKE $500 FOR KEVIN", "<color=#ffe14a>E</color>  serve cone  +$5", 100, 0,
            ("PlainCone", 1), ("WaffleCone", 1), ("PintStrawberry", 3), ("ScoopVanilla", 6));
    }

    static void PoliceChase(Shot shot)
    {
        Street(shot, -4, 3, TownLeft, TownRight);
        TruckAt(shot, Vector3.zero, 0);
        Place(shot, Model("Characters", "Crew Throw"), new Vector3(0.95f, 2.92f, -2.1f), 170);
        var cone = Place(shot, Model("Weapons", "Waffle Cone"), new Vector3(-0.3f, 3.5f, -5), 0);
        cone.transform.rotation = Quaternion.Euler(-60, 170, 30);
        PoliceCar(shot, new Vector3(-1.2f, 0, -7.5f), 4);
        PoliceCar(shot, new Vector3(2.1f, 0, -12.5f), -6);
        Hold(shot, ItemKind.WaffleCone, Flavor.None);
        Look(shot, new Vector3(-0.4f, 4.75f, 0), new Vector3(0, 0.8f, -12), 75);
        Hud(shot, 215, 500, "TOWN 2", 48, "POLICE IN PURSUIT", null, 85, 1,
            ("PlainCone", 1), ("WaffleCone", 4), ("PintStrawberry", 3), ("ScoopVanilla", 6));
    }

    static void CopOnBoard(Shot shot)
    {
        Street(shot, -3, 4, TownLeft, TownRight);
        var truck = TruckAt(shot, Vector3.zero, 0);
        var tub = Child(truck, $"{Truck} freezer tub 2");
        tub.gameObject.SetActive(false);
        Place(shot, Model("Heist", "Flavor Tub Rocky Road Diamond"), tub.position, 90);
        Child(truck, $"{Truck} rear door").localRotation *= Quaternion.Euler(0, -105, 0);
        Place(shot, Model("Characters", "Police Officer Climb"), new Vector3(-0.1f, 0.3f, -3.5f), 0);
        PoliceCar(shot, new Vector3(-1.8f, 0, -10), 10);
        Hold(shot, ItemKind.PlainCone, Flavor.None);
        Look(shot, new Vector3(0.25f, 2.2f, -0.9f), new Vector3(-0.35f, 1.45f, -2.8f), 75);
        Hud(shot, 410, 500, "TOWN 2", 0, "COP ON BOARD: PROTECT THE DIAMOND", "<color=#ffe14a>CLICK</color>  bonk", 64, 0,
            ("PlainCone", 1), ("WaffleCone", 1), ("PintStrawberry", 3), ("ScoopVanilla", 6));
    }

    static void Kevin(Shot shot)
    {
        Street(shot, -3, 4, RuralLeft, RuralRight, "Chunk Rural");
        var shack = Place(shot, Model("Heist", "Bait Shack"), new Vector3(-8, 0, 6.5f), 135);
        Place(shot, Model("Characters", "Forger Kevin"), Child(shack, "Bait Shack socket shopkeeper").position, 135);
        TruckAt(shot, new Vector3(-2.8f, 0, 13), 0);
        Place(shot, Model("Heist", "Town Line Sign"), new Vector3(-6, 0, 22), 180);
        Place(shot, Model("Heist", "Police Roadblock"), new Vector3(0, 0, 46), 180);
        PoliceCar(shot, new Vector3(4, 0, 49), -100);
        Look(shot, new Vector3(-4.6f, 1.65f, 3.2f), new Vector3(-7.6f, 1.55f, 6.4f), 75);
        Hud(shot, 560, 500, "TOWN 2", 0, "TOWN LINE: PAY KEVIN TO GET THROUGH",
            "<color=#ffe14a>E</color>  pay quota  $500  (new plates + papers)\n<color=#ffe14a>1</color>  bigger freezer  $40", 100, 0,
            ("PlainCone", 1), ("WaffleCone", 1), ("PintStrawberry", 1), ("ScoopVanilla", 2));
    }

    static void Harbor(Shot shot)
    {
        Sunset(shot);
        Street(shot, -3, 0, CoastLeft, CoastRight);
        TruckAt(shot, Vector3.zero, 0);
        Place(shot, Model("Vehicles", "Harbor Water"), new Vector3(0, -1, 40), 0);
        var dock = Place(shot, Model("Vehicles", "Harbor Dock"), new Vector3(0, 0, 9), 0);
        var mooring = Child(dock, "Harbor Dock socket yacht");
        Place(shot, Model("Vehicles", "Yacht"), mooring.position, mooring.eulerAngles.y);
        Place(shot, Model("Vehicles", "Lighthouse"), new Vector3(-55, -1, 75), 0);
        Place(shot, Model("Characters", "Diamond Buyer"), new Vector3(1.2f, 0, mooring.position.z - 1.5f), 180);
        var pink = Place(shot, Model("Characters", "Crew Carry Pink"), new Vector3(-0.45f, 0, 16.5f), 0);
        var mint = Place(shot, Model("Characters", "Crew Carry Mint"), new Vector3(0.45f, 0, 16.5f), 0);
        var carry = (Child(pink, "Crew Carry Pink socket carry").position + Child(mint, "Crew Carry Mint socket carry").position) / 2;
        Place(shot, Model("Heist", "Flavor Tub Rocky Road Diamond"), carry + Vector3.down * 0.15f, 30);
        shot.ViewModel.gameObject.SetActive(false);
        Look(shot, new Vector3(0.6f, 2.1f, 12.5f), new Vector3(-0.6f, 1.2f, 30), 75);
        Hud(shot, 1240, 0, "THE COAST", 0, "DELIVER THE DIAMOND", null, 100, 0,
            ("PlainCone", 1), ("WaffleCone", 1), ("PintStrawberry", 2), ("ScoopVanilla", 4));
    }

    // A wide look at a serving stop with a patrol car pulling up, without the HUD.
    static void Overview(Shot shot)
    {
        Street(shot, -3, 4, TownLeft, TownRight);
        TruckAt(shot, Vector3.zero, 0);
        KidCrowd(shot);
        PoliceCar(shot, new Vector3(-1.4f, 0, 12), 175);
        Place(shot, Model("Characters", "Police Officer Run"), new Vector3(-1.9f, 0, 7.5f), 195);
        shot.Hud.gameObject.SetActive(false);
        shot.ViewModel.gameObject.SetActive(false);
        Look(shot, new Vector3(-9, 6, -8), new Vector3(-1.5f, 1.0f, 2.5f), 60);
    }

    // The shotgun serving the crowd at the window: scoops in flight, splats on the kids and their tips flying up.
    static void ShootingKids(Shot shot)
    {
        Street(shot, -3, 4, TownLeft, TownRight);
        TruckAt(shot, Vector3.zero, 0);
        KidCrowd(shot);
        foreach (var (flavor, position) in new[] { ("Strawberry", new Vector3(-2.75f, 1.0f, -1.3f)), ("Vanilla", new Vector3(-3.05f, 1.05f, 0.2f)), ("Chocolate", new Vector3(-3.05f, 0.95f, -2.4f)) })
        {
            Place(shot, Model("FX", $"{flavor} Splat Burst"), position, 90);
            Place(shot, Model("FX", "Hit Star"), position + Vector3.up * 0.35f, 90);
        }
        Place(shot, Model("FX", "Strawberry Scoop Bullet"), new Vector3(-2.0f, 1.55f, -1.05f), 90);
        Place(shot, Model("FX", "Vanilla Scoop Bullet"), new Vector3(-2.3f, 1.4f, -0.3f), 90);
        Place(shot, Model("FX", "Chocolate Scoop Bullet"), new Vector3(-1.8f, 1.7f, -1.7f), 90);
        foreach (var position in new[] { new Vector3(-2.8f, 1.7f, -1.1f), new Vector3(-3.1f, 1.9f, 0.4f), new Vector3(-3.1f, 1.6f, -2.2f) })
        {
            Place(shot, Model("Items", "Tip Coin"), position, 30);
        }
        Hold(shot, ItemKind.SundaeShotgun, Flavor.None);
        Look(shot, new Vector3(-0.8f, 2.4f, -0.8f), new Vector3(-4, 0.6f, -0.8f), 75);
        Hud(shot, 385, 500, "TOWN 2", 0, "SERVE THE CROWD", "<color=#ffe14a>+$5  +$5  +$5</color>", 100, 0,
            ("SundaeShotgun", 1), ("WaffleCone", 1), ("PintStrawberry", 3), ("ScoopVanilla", 6));
    }

    // Two of the crew sneaking milk and sugar out of the candy shop back to the truck while a cop on the corner looks the other way.
    static void Scavenge(Shot shot)
    {
        Street(shot, -3, 0, TownLeft, TownRight);
        Street(shot, 2, 4, TownLeft, TownRight);
        Place(shot, Prefab("Chunk Straight"), new Vector3(0, 0, 20), 0);
        Place(shot, Prefab("Scenery Houses"), new Vector3(20, 0, 20), -90);
        Place(shot, Model("Road", "Candy Shop"), new Vector3(-13, 0, 20), 180);
        TruckAt(shot, new Vector3(0, 0, 28), 0);
        var mint = Place(shot, Model("Characters", "Crew Carry Mint"), new Vector3(-4.9f, 0, 19.6f), 25);
        Place(shot, Model("Items", "Milk Crate"), Child(mint, "Crew Carry Mint socket carry").position, 25);
        var pink = Place(shot, Model("Characters", "Crew Carry Pink"), new Vector3(-6.4f, 0, 18.2f), 35);
        Place(shot, Model("Items", "Sugar Sack"), Child(pink, "Crew Carry Pink socket carry").position, 35);
        Place(shot, Model("Items", "Milk Crate"), new Vector3(-8.5f, 0, 18.8f), 10);
        Place(shot, Model("Items", "Milk Crate"), new Vector3(-8.5f, 0.32f, 18.8f), 30);
        Place(shot, Model("Items", "Sugar Sack"), new Vector3(-8.6f, 0, 18.1f), 0);
        Place(shot, Model("Characters", "Police Officer"), new Vector3(-6.2f, 0, 14), 200);
        Place(shot, Model("Characters", "Detective"), new Vector3(-6.5f, 0, 32), 20);
        shot.Hud.gameObject.SetActive(false);
        shot.ViewModel.gameObject.SetActive(false);
        Look(shot, new Vector3(-1.5f, 5f, 10), new Vector3(-8, 1.0f, 22), 60);
    }

    // The kitchen from the back door: one of the crew loading the ingredient bins, another at the hopper, ingredients on the floor.
    static void KitchenCrew(Shot shot)
    {
        Street(shot, -3, 4, TownLeft, TownRight);
        var truck = TruckAt(shot, Vector3.zero, 0);
        Place(shot, Model("Characters", "Player Pink"), Child(truck, $"{Truck} socket use point ingredient bins").position + new Vector3(0.15f, 0, 0), 90);
        Place(shot, Model("Characters", "Player Yellow"), Child(truck, $"{Truck} socket use point hopper gauge").position, -90);
        Place(shot, Model("Items", "Milk Crate"), new Vector3(0.45f, 0.75f, -1.2f), 15);
        Place(shot, Model("Items", "Sugar Sack"), new Vector3(0.5f, 0.75f, -0.75f), -10);
        Place(shot, Model("Items", "Strawberry Basket"), new Vector3(-0.25f, 0.75f, -1.6f), 40);
        Hold(shot, ItemKind.None, Flavor.None);
        Look(shot, new Vector3(-0.35f, 2.3f, -2.7f), new Vector3(0.25f, 1.3f, 1), 75);
        Hud(shot, 120, 500, "TOWN 2", 0, "MILK + SUGAR + STRAWBERRY: CRANK THE CHURN", "<color=#ffe14a>E</color>  load the churn", 100, 2,
            ("PlainCone", 1), ("WaffleCone", 1), ("PintStrawberry", 3), ("ScoopVanilla", 6));
    }

    // From the driver's seat: kids in the road in front of the truck and a patrol car coming up the road behind them.
    static void KidsInTheRoad(Shot shot)
    {
        Street(shot, -2, 5, TownLeft, TownRight);
        var truck = TruckAt(shot, Vector3.zero, 0);
        Place(shot, Model("Characters", "Kid Pigtails"), new Vector3(-1.4f, 0, 4.9f), 190);
        Place(shot, Model("Characters", "Kid Cap"), new Vector3(-0.2f, 0, 5.4f), 170);
        Place(shot, Model("Characters", "Kid Curly"), new Vector3(0.9f, 0, 4.7f), 200);
        Place(shot, Model("Characters", "Kid Hoodie"), new Vector3(-0.8f, 0, 6.4f), 175);
        Place(shot, Model("Characters", "Kid Glasses"), new Vector3(1.8f, 0, 5.9f), 215);
        Place(shot, Model("Characters", "Kid Cap"), new Vector3(-2.4f, 0, 6.1f), 160);
        PoliceCar(shot, new Vector3(1.6f, 0, 42), 180);
        Hold(shot, ItemKind.None, Flavor.None);
        var seat = Child(truck, $"{Truck} socket seat").position;
        Look(shot, seat + new Vector3(0, 0.85f, 0), new Vector3(-0.2f, 1.2f, 14), 75);
        Hud(shot, 290, 500, "TOWN 2", 0, "KIDS IN THE ROAD: SERVE THEM OR STAY STUCK", null, 100, 0,
            ("PlainCone", 1), ("WaffleCone", 1), ("PintStrawberry", 3), ("ScoopVanilla", 6));
    }

    // Behind the chase: ice cream splats on the road, one patrol car spun out into a hydrant, the truck getting away.
    static void SlipperyCops(Shot shot)
    {
        Street(shot, -4, 3, TownLeft, TownRight);
        TruckAt(shot, new Vector3(0.6f, 0, 6), 0);
        Place(shot, Model("Characters", "Crew Throw"), new Vector3(1.55f, 2.92f, 3.9f), 170);
        foreach (var (flavor, position) in new[] { ("Vanilla", new Vector3(-0.6f, 0.02f, -2)), ("Strawberry", new Vector3(1.2f, 0.02f, -3.5f)), ("Mint", new Vector3(-1.4f, 0.02f, -5)), ("Chocolate", new Vector3(0.5f, 0.02f, -6.2f)), ("Vanilla", new Vector3(2.1f, 0.02f, -1)) })
        {
            var decal = Place(shot, Model("FX", $"{flavor} Splat Decal"), position, position.x * 40);
            decal.transform.localScale = Vector3.one * 4;
        }
        PoliceCar(shot, new Vector3(-4.6f, 0, -6.5f), 70);
        Place(shot, Model("Road", "Fire Hydrant"), new Vector3(-6.2f, 0, -5.4f), 0);
        Place(shot, Model("FX", "Smoke Puff Large"), new Vector3(-5.8f, 1.2f, -5.6f), 0);
        Place(shot, Model("FX", "Hit Star"), new Vector3(-5.6f, 1.9f, -5.2f), 0);
        PoliceCar(shot, new Vector3(1.4f, 0, -15), -25);
        shot.Hud.gameObject.SetActive(false);
        shot.ViewModel.gameObject.SetActive(false);
        Look(shot, new Vector3(4.5f, 3.4f, -19), new Vector3(-0.8f, 0.8f, -3), 60);
    }

    // Every job at once: kids at the window, a gunner on the roof, the crew hauling milk to the back door, a cop closing in.
    static void CoopChaos(Shot shot)
    {
        Street(shot, -3, 4, TownLeft, TownRight);
        var truck = TruckAt(shot, Vector3.zero, 0);
        Child(truck, $"{Truck} rear door").localRotation *= Quaternion.Euler(0, -105, 0);
        KidCrowd(shot);
        Place(shot, Model("Characters", "Crew Throw"), new Vector3(0.6f, 2.92f, -1.6f), 200);
        var mint = Place(shot, Model("Characters", "Crew Carry Mint"), new Vector3(-1.3f, 0, -6.2f), 10);
        Place(shot, Model("Items", "Milk Crate"), Child(mint, "Crew Carry Mint socket carry").position, 10);
        var pink = Place(shot, Model("Characters", "Crew Carry Pink"), new Vector3(0.6f, 0, -7.4f), -5);
        Place(shot, Model("Items", "Sugar Sack"), Child(pink, "Crew Carry Pink socket carry").position, -5);
        PoliceCar(shot, new Vector3(1.8f, 0, -16), 15);
        Place(shot, Model("Characters", "Police Officer Run"), new Vector3(-1.8f, 0, -12.5f), 10);
        Place(shot, Model("FX", "Strawberry Splat Burst"), new Vector3(-2.75f, 1.0f, -1.3f), 90);
        shot.Hud.gameObject.SetActive(false);
        shot.ViewModel.gameObject.SetActive(false);
        Look(shot, new Vector3(-8, 5.5f, -11), new Vector3(-0.8f, 0.8f, -2), 60);
    }

    // The truck kitted out with every upgrade Kevin sells.
    static void TruckUpgrades(Shot shot)
    {
        Street(shot, -3, 4, RuralLeft, RuralRight, "Chunk Rural");
        var truck = TruckAt(shot, Vector3.zero, 0);
        foreach (var (upgrade, socket) in new[] { ("Plow", "plow"), ("Side Spikes", "spikes"), ("Window Armor", "armor"), ("Exhaust Stacks", "engine"), ("Big Hopper", "hopper"), ("Sundae Tank", "tank"), ("Second Turret Mount", "turret2") })
        {
            Place(shot, Model("Truck", $"Upgrade {upgrade}"), Child(truck, $"{Truck} socket upgrade {socket}").position, 0);
        }
        Place(shot, Model("Weapons", "Soft Serve Minigun"), Child(truck, $"{Truck} socket turret").position, 0);
        shot.Hud.gameObject.SetActive(false);
        shot.ViewModel.gameObject.SetActive(false);
        Look(shot, new Vector3(-4.8f, 2.0f, 7), new Vector3(0, 1.5f, 0), 60);
    }

    // Kevin's stall in the depot at the town line: guns on the stands, first person, about to buy the minigun.
    static void WeaponStall(Shot shot)
    {
        Street(shot, -3, -1, RuralLeft, RuralRight, "Chunk Rural");
        Street(shot, 1, 4, RuralLeft, RuralRight, "Chunk Rural");
        var depot = Place(shot, Prefab("Chunk Depot"), Vector3.zero, 0);
        Place(shot, Prefab($"Scenery {RuralLeft[3]}"), new Vector3(-20, 0, 0), 90);
        Place(shot, Model("Shop", "Shopkeeper Kevin"), Child(depot, "Kevin's Stall socket kevin").position, -90);
        var weapons = new[] { "Sundae Shotgun", "Soft Serve Minigun", "Sprinkle SMG" };
        for (int i = 0; i < weapons.Length; i++) Place(shot, Model("Weapons", weapons[i]), Child(depot, $"Kevin's Stall socket weapon {i + 1}").position, 90);
        TruckAt(shot, new Vector3(-1.5f, 0, -4), 0);
        Hold(shot, ItemKind.ScoopPistol, Flavor.None);
        var first = Child(depot, "Kevin's Stall socket weapon 1").position;
        var middle = Child(depot, "Kevin's Stall socket weapon 2").position;
        Look(shot, first + new Vector3(-1.0f, 0.9f, 1.4f), middle + new Vector3(0.2f, 0.1f, -0.6f), 75);
        Hud(shot, 640, 0, "TOWN LINE", 0, "KEVIN'S: SPEND WHAT'S LEFT OVER THE QUOTA", "<color=#ffe14a>E</color>  buy Soft Serve Minigun  $240", 100, 0,
            ("ScoopPistol", 1), ("WaffleCone", 1), ("PintStrawberry", 2), ("ScoopVanilla", 4));
    }

    // Low in front of the plow as the truck ploughs through kids, who go flying; a patrol car flips its lights on.
    static void RunOver(Shot shot)
    {
        Street(shot, -3, 4, TownLeft, TownRight);
        var truck = TruckAt(shot, Vector3.zero, 0);
        Place(shot, Model("Truck", "Upgrade Plow"), Child(truck, $"{Truck} socket upgrade plow").position, 0);
        foreach (var (kid, position, spin) in new[] { ("Kid Cap", new Vector3(-0.6f, 2.2f, 5.0f), new Vector3(-70, 20, 30)), ("Kid Curly", new Vector3(1.3f, 1.4f, 4.6f), new Vector3(-40, -30, -60)), ("Kid Glasses", new Vector3(-2.2f, 0.9f, 4.4f), new Vector3(-20, 60, 80)) })
        {
            var flying = Place(shot, Model("Characters", kid), position, 0);
            flying.transform.rotation = Quaternion.Euler(spin);
            Place(shot, Model("FX", "Hit Star"), position + Vector3.up * 0.6f, 0);
        }
        Place(shot, Model("Characters", "Kid Pigtails"), new Vector3(3.4f, 0, 4.2f), 230);
        Place(shot, Model("FX", "Shockwave Ring"), new Vector3(0, 0.1f, 4.4f), 0);
        PoliceCar(shot, new Vector3(-6.5f, 0, 22), 150);
        shot.Hud.gameObject.SetActive(false);
        shot.ViewModel.gameObject.SetActive(false);
        Look(shot, new Vector3(2.0f, 1.1f, 8.6f), new Vector3(-0.3f, 1.6f, 2), 70);
    }

    // Kids pressing up to the serving window, a detective watching from the back.
    static void KidCrowd(Shot shot)
    {
        Place(shot, Model("Characters", "Kid Pigtails"), new Vector3(-2.7f, 0, -1.35f), 80);
        Place(shot, Model("Characters", "Kid Cap"), new Vector3(-3.0f, 0, 0.2f), 110);
        Place(shot, Model("Characters", "Kid Curly"), new Vector3(-3.0f, 0, -2.4f), 65);
        Place(shot, Model("Characters", "Kid Hoodie"), new Vector3(-3.8f, 0, -0.4f), 95);
        Place(shot, Model("Characters", "Kid Glasses"), new Vector3(-4.3f, 0, -2.3f), 45);
        Place(shot, Model("Characters", "Detective"), new Vector3(-3.6f, 0, 2.4f), 125);
    }

    // ------------------------------------------------------------------------------------------------ staging

    // Road chunks from chunk index first to last (20 m each along Z) with a scenery block on each side facing the road.
    static void Street(Shot shot, int first, int last, string[] left, string[] right, string chunk = "Chunk Straight")
    {
        for (int i = first; i <= last; i++)
        {
            Place(shot, Prefab(chunk), new Vector3(0, 0, i * 20), 0);
            Place(shot, Prefab($"Scenery {left[i - first]}"), new Vector3(-20, 0, i * 20), 90);
            Place(shot, Prefab($"Scenery {right[i - first]}"), new Vector3(20, 0, i * 20), -90);
        }
    }

    // The truck model with its kitchen stocked, without the gun rack.
    static GameObject TruckAt(Shot shot, Vector3 position, float yaw)
    {
        var truck = Place(shot, Model("Truck", Truck), position, yaw);
        Child(truck, $"{Truck} station gun rack").gameObject.SetActive(false);
        return truck;
    }

    // A patrol car with its light bar lighting up the road red and blue.
    static void PoliceCar(Shot shot, Vector3 position, float yaw)
    {
        var car = Place(shot, Model("Vehicles", "Police Car"), position, yaw);
        foreach (var (side, color) in new[] { (0.45f, new Color(1f, 0.1f, 0.2f)), (-0.45f, new Color(0.2f, 0.35f, 1f)) })
        {
            var light = new GameObject("Light Bar").AddComponent<Light>();
            light.transform.SetParent(car.transform, false);
            light.transform.localPosition = new Vector3(side, 2.1f, 0);
            light.type = LightType.Point;
            light.color = color;
            light.range = 12;
            light.intensity = 14;
        }
    }

    // Low orange sun, pink sky and warm fog for the coast.
    static void Sunset(Shot shot)
    {
        var sky = new Color(0.98f, 0.5f, 0.45f);
        shot.Camera.backgroundColor = sky;
        RenderSettings.fogColor = sky;
        RenderSettings.fogStartDistance = 60;
        RenderSettings.ambientLight = new Color(0.62f, 0.42f, 0.55f);
        shot.Sun.color = new Color(1f, 0.62f, 0.38f);
        shot.Sun.intensity = 1.1f;
        shot.Sun.transform.rotation = Quaternion.Euler(14, 200, 0);
        shot.Environment.SetActive(false);
        // A gradient sky card and a low sun behind the harbor.
        var gradient = new Texture2D(1, 4) { filterMode = FilterMode.Bilinear, wrapMode = TextureWrapMode.Clamp };
        gradient.SetPixels(new[] { new Color(1f, 0.62f, 0.36f), sky, new Color(0.62f, 0.32f, 0.62f), new Color(0.24f, 0.14f, 0.42f) });
        gradient.Apply();
        var card = GameObject.CreatePrimitive(PrimitiveType.Quad);
        card.transform.SetParent(shot.Root, false);
        card.transform.SetPositionAndRotation(new Vector3(0, 150, 260), Quaternion.identity);
        card.transform.localScale = new Vector3(1200, 400, 1);
        card.GetComponent<Renderer>().sharedMaterial = new Material(Shader.Find("Universal Render Pipeline/Unlit")) { mainTexture = gradient };
        var sun = GameObject.CreatePrimitive(PrimitiveType.Sphere);
        sun.transform.SetParent(shot.Root, false);
        sun.transform.SetPositionAndRotation(new Vector3(-30, 9, 250), Quaternion.identity);
        sun.transform.localScale = Vector3.one * 26;
        var sunMaterial = new Material(Shader.Find("Universal Render Pipeline/Unlit"));
        sunMaterial.SetColor("_BaseColor", new Color(1f, 0.9f, 0.45f));
        sun.GetComponent<Renderer>().sharedMaterial = sunMaterial;
        RenderSettings.fogEndDistance = 600;
    }

    static void Look(Shot shot, Vector3 eye, Vector3 target, float fieldOfView)
    {
        shot.Camera.transform.SetPositionAndRotation(eye, Quaternion.LookRotation(target - eye));
        shot.Camera.fieldOfView = fieldOfView;
    }

    // Shows the held model for the item in the first-person view model (ItemKind.None: empty hands).
    static void Hold(Shot shot, ItemKind kind, Flavor flavor)
    {
        var models = new SerializedObject(shot.ViewModel).FindProperty("models");
        for (int i = 0; i < models.arraySize; i++)
        {
            var entry = models.GetArrayElementAtIndex(i);
            var model = (GameObject)entry.FindPropertyRelative("Model").objectReferenceValue;
            model.SetActive(entry.FindPropertyRelative("Kind").enumValueIndex == (int)kind && entry.FindPropertyRelative("Flavor").enumValueIndex == (int)flavor);
        }
    }

    // Fills the HUD: money and the town quota top left, town and speed top right, the banner and prompt when given,
    // health, and the hotbar slots as (icon sprite under Icons/, count) with the selected slot framed.
    static void Hud(Shot shot, int money, int quota, string town, int speed, string banner, string prompt, int health, int selected, params (string icon, int count)[] slots)
    {
        var hud = new SerializedObject(shot.Hud);
        Text Text(string field) => (Text)hud.FindProperty(field).objectReferenceValue;
        GameObject Panel(string field) => (GameObject)hud.FindProperty(field).objectReferenceValue;

        Text("moneyText").text = $"${money}";
        // The kills panel becomes the quota panel (hidden for quota 0).
        var quotaText = Text("killsText");
        var quotaPanel = (RectTransform)quotaText.transform.parent;
        quotaPanel.gameObject.SetActive(quota > 0);
        quotaPanel.sizeDelta = new Vector2(236, 50);
        quotaPanel.GetComponentsInChildren<Image>().First(i => i.transform != quotaPanel).sprite = Sprite("Icons/Coin");
        quotaText.text = $"QUOTA ${quota}";
        quotaText.color = new Color(1f, 0.88f, 0.29f);
        Text("areaText").text = town;
        Text("speedText").text = $"{speed} MPH";
        Text("fuelText").transform.parent.gameObject.SetActive(false);
        Panel("ammoPanel").SetActive(false);
        Panel("controlsPanel").SetActive(false);
        Child(shot.Hud.gameObject, "Help Hint").gameObject.SetActive(false);
        Panel("phaseBanner").SetActive(banner != null);
        Text("phaseText").text = banner;
        Panel("promptPanel").SetActive(prompt != null);
        Text("promptText").text = prompt;
        ((Image)hud.FindProperty("healthFill").objectReferenceValue).fillAmount = health / 100f;
        Text("healthText").text = health.ToString();
        Text("selectedName").text = "";
        var icons = hud.FindProperty("slotIcons");
        for (int i = 0; i < icons.arraySize; i++)
        {
            var icon = (Image)icons.GetArrayElementAtIndex(i).objectReferenceValue;
            var filled = i < slots.Length && slots[i].icon != null;
            icon.enabled = filled;
            if (filled) icon.sprite = Sprite($"Icons/{slots[i].icon}");
            ((Text)hud.FindProperty("slotCounts").GetArrayElementAtIndex(i).objectReferenceValue).text = filled && slots[i].count > 1 ? slots[i].count.ToString() : "";
            ((GameObject)hud.FindProperty("slotSelected").GetArrayElementAtIndex(i).objectReferenceValue).SetActive(i == selected);
        }
    }

    static GameObject Model(string category, string name)
    {
        var path = $"{Art}/{category}/{name}.fbx";
        var model = AssetDatabase.LoadAssetAtPath<GameObject>(path);
        if (model == null) throw new FileNotFoundException($"Missing PS1 model {path}");
        return model;
    }

    static GameObject Prefab(string name)
    {
        var path = $"Assets/Prefabs/{name}.prefab";
        var prefab = AssetDatabase.LoadAssetAtPath<GameObject>(path);
        if (prefab == null) throw new FileNotFoundException($"Missing prefab {path}");
        return prefab;
    }

    static Sprite Sprite(string name)
    {
        var path = $"{Sprites}/{name}.png";
        var sprite = AssetDatabase.LoadAssetAtPath<Sprite>(path);
        if (sprite == null) throw new FileNotFoundException($"Missing sprite {path}");
        return sprite;
    }

    static GameObject Place(Shot shot, GameObject asset, Vector3 position, float yaw, Transform parent = null)
    {
        var instance = (GameObject)PrefabUtility.InstantiatePrefab(asset, parent == null ? shot.Root : parent);
        instance.transform.SetPositionAndRotation(position, Quaternion.Euler(0, yaw, 0));
        return instance;
    }

    static Transform Child(GameObject root, string name)
    {
        var child = root.GetComponentsInChildren<Transform>(true).FirstOrDefault(t => t.name == name);
        if (child == null) throw new InvalidOperationException($"{root.name} has no child named '{name}'");
        return child;
    }
}
