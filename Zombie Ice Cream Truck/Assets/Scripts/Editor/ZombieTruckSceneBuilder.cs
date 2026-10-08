using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using Photon.Deterministic;
using Quantum;
using Quantum.Editor;
using UnityEditor;
using UnityEditor.Rendering.Universal.ShaderGUI;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.UI;
using Object = UnityEngine.Object;

// Builds the game from the PS1 art in Assets/Art/PS1: entity prefabs, effect prefabs, the settings assets and the
// gameplay scene. Run from Tools > Zombie Truck > Build Prototype Scene, or headless with
// -executeMethod ZombieTruckSceneBuilder.Build. Everything it creates is a normal editable asset; rerunning rebuilds it.
// Socket and pivot transforms are looked up by name here, at edit time only; runtime code gets serialized references.
public static class ZombieTruckSceneBuilder
{
    const string Art = "Assets/Art/PS1";
    const string Sprites = "Assets/Art/Sprites";
    const string Audio = "Assets/Audio";
    const string PrefabFolder = "Assets/Prefabs";
    const string MaterialFolder = "Assets/Materials";
    const string ConfigFolder = "Assets/QuantumUser/Resources";
    const string ScenePath = "Assets/QuantumUser/Scenes/QuantumGameScene.unity";
    const string Truck = "Ice Cream Truck";
    const int UiLayer = 5;

    static readonly string[] Flavors = { "Vanilla", "Chocolate", "Strawberry", "Mint" };
    static readonly string[] TruckDecor = { "freezer tub 1", "freezer tub 2", "freezer tub 3", "counter pint 1", "counter pint 3", "counter scoop", "counter tub", "churn tub", "rack pistol", "rack shotgun" };

    // Hand-measured from the truck art (h_truck.py layout): floor top 0.75, ceiling 2.86, roof 2.92, walls at x +-1.15,
    // cab front z 2.35, bulkhead z 0.95 (1 m doorway), rear wall z -2.95 (0.9 m door), serving window on -X.
    static readonly Vector3[] TruckBoxes =
    {
        new Vector3(0, 0.65f, -0.3f), new Vector3(1.15f, 0.1f, 2.65f),          // floor
        new Vector3(0, 0.3f, 0.2f), new Vector3(1f, 0.25f, 3.1f),               // chassis
        new Vector3(0, 0.95f, 2.85f), new Vector3(1.1f, 0.5f, 0.5f),            // hood
        new Vector3(1.12f, 1.805f, -0.3f), new Vector3(0.03f, 1.055f, 2.65f),   // +X wall
        new Vector3(-1.12f, 1.805f, -2.225f), new Vector3(0.03f, 1.055f, 0.725f), // -X wall behind the window
        new Vector3(-1.12f, 1.235f, -0.8f), new Vector3(0.03f, 0.485f, 0.7f),   // -X wall under the window
        new Vector3(-1.12f, 2.705f, -0.8f), new Vector3(0.03f, 0.155f, 0.7f),   // -X wall over the window
        new Vector3(-1.12f, 1.805f, 1.125f), new Vector3(0.03f, 1.055f, 1.225f), // -X wall ahead of the window
        new Vector3(0, 1.805f, 2.32f), new Vector3(1.15f, 1.055f, 0.03f),        // cab front
        new Vector3(-0.795f, 1.805f, 0.95f), new Vector3(0.295f, 1.055f, 0.025f), // bulkhead left of the doorway
        new Vector3(0.795f, 1.805f, 0.95f), new Vector3(0.295f, 1.055f, 0.025f),  // bulkhead right of the doorway
        new Vector3(0, 2.68f, 0.95f), new Vector3(0.5f, 0.18f, 0.025f),          // bulkhead over the doorway
        new Vector3(-0.8f, 1.805f, -2.92f), new Vector3(0.35f, 1.055f, 0.03f),   // rear wall left of the door
        new Vector3(0.8f, 1.805f, -2.92f), new Vector3(0.35f, 1.055f, 0.03f),    // rear wall right of the door
        new Vector3(0, 2.755f, -2.92f), new Vector3(0.45f, 0.105f, 0.03f),       // over the rear door
        new Vector3(0, 2.89f, 0.115f), new Vector3(1.15f, 0.03f, 2.235f),        // roof ahead of the hatch
        new Vector3(0, 2.89f, -2.835f), new Vector3(1.15f, 0.03f, 0.115f),       // roof behind the hatch
        new Vector3(-0.35f, 2.89f, -2.42f), new Vector3(0.8f, 0.03f, 0.3f),      // roof beside the hatch
        new Vector3(1.09f, 2.89f, -2.42f), new Vector3(0.06f, 0.03f, 0.3f),
        new Vector3(-1.12f, 3.2f, -0.3f), new Vector3(0.03f, 0.3f, 2.65f),       // roof railing
        new Vector3(1.12f, 3.2f, -0.3f), new Vector3(0.03f, 0.3f, 2.65f),
        new Vector3(0, 3.2f, 2.32f), new Vector3(1.15f, 0.3f, 0.03f),
        new Vector3(0, 3.2f, -2.92f), new Vector3(1.15f, 0.3f, 0.03f),
    };

    static readonly (UpgradeKind upgrade, int price)[] ShopStock =
    {
        (UpgradeKind.Plow, 60), (UpgradeKind.Spikes, 50), (UpgradeKind.Armor, 50), (UpgradeKind.Engine, 70),
        (UpgradeKind.Turret, 100), (UpgradeKind.SecondTurret, 150), (UpgradeKind.BigHopper, 60), (UpgradeKind.SecondScoop, 40),
    };

    // Reimports every PS1 model and texture, for when PS1ArtPostprocessor's material or texture rules change.
    [MenuItem("Tools/Zombie Truck/Reimport PS1 Art")]
    public static void ReimportArt()
    {
        AssetDatabase.ImportAsset(Art, ImportAssetOptions.ImportRecursive | ImportAssetOptions.ForceUpdate);
        Debug.Log("ZombieTruckSceneBuilder: reimported the PS1 art");
    }

    [MenuItem("Tools/Zombie Truck/Build Prototype Scene")]
    public static void Build()
    {
        Directory.CreateDirectory(PrefabFolder);
        Directory.CreateDirectory(MaterialFolder);
        PlayerSettings.allowUnsafeCode = true;
        var truckModel = Model("Truck", Truck);

        var fx = BuildEffects();
        var truckPrefab = BuildTruck(truckModel, fx);
        var survivors = new[] { "Pink", "Blue", "Mint", "Yellow" }.Select(BuildSurvivor).ToArray();
        var zombies = new[]
        {
            BuildZombie(fx, "Walker", "Walker", "Walker Worker", "Walker Mail Carrier", "Walker Granny"),
            BuildZombie(fx, "Sprinter", "Sprinter"),
            BuildZombie(fx, "Bloater", "Bloater"),
        };
        var items = BuildItems();
        var stations = BuildStations(truckModel);
        var chunks = BuildChunks();
        var projectile = BuildFlavored("Projectile", "Items", "Scoop Grenade {0}", 0.6f, true);

        var controller = ScriptableObject.CreateInstance<CharacterController3DConfig>();
        controller.Offset = new Vector3(0, 0.3f, 0).ToFPVector3();
        controller.Radius = FP.FromFloat_UNSAFE(0.25f);
        controller.MaxPenetration = FP.FromFloat_UNSAFE(0.05f);
        controller.PenetrationCorrection = FP.FromFloat_UNSAFE(0.5f);
        controller.Extent = FP.FromFloat_UNSAFE(0.1f);
        controller.MaxContacts = 2;
        controller.LayerMask = -1;
        controller.AirControl = true;
        controller.Acceleration = 30;
        controller.Braking = 12;
        controller.BaseJumpImpulse = FP.FromFloat_UNSAFE(5f);
        controller.MaxSpeed = 4;
        controller.Gravity = new FPVector3(0, -15, 0);
        controller.MaxSlope = 50;
        controller.MaxSlopeSpeed = 5;
        controller = ReplaceAsset(controller, $"{ConfigFolder}/SurvivorController.asset");

        var settings = ScriptableObject.CreateInstance<ZombieTruckSettings>();
        settings.TruckPrototype = PrototypeFor(truckPrefab);
        settings.SurvivorPrototypes = survivors.Select(PrototypeFor).ToArray();
        settings.ZombiePrototypes = zombies.Select(PrototypeFor).ToArray();
        settings.ItemPrototypes = items.Select(p => p == null ? default : PrototypeFor(p)).ToArray();
        settings.StationPrototypes = stations.Select(PrototypeFor).ToArray();
        settings.ChunkPrototypes = chunks.Select(PrototypeFor).ToArray();
        settings.ProjectilePrototype = PrototypeFor(projectile);
        settings.SurvivorController = controller;
        FillTruckLayout(settings, truckModel);
        FillChunkContents(settings);
        settings.Zombies = new[]
        {
            new ZombieStats { Health = 2, Speed = FP.FromFloat_UNSAFE(1.3f), Damage = 10, AttackInterval = 1, Reward = 5, HeadHeight = FP.FromFloat_UNSAFE(1.42f), HalfSize = new Vector3(0.3f, 0.88f, 0.3f).ToFPVector3() },
            new ZombieStats { Health = 1, Speed = FP.FromFloat_UNSAFE(5.2f), Damage = 8, AttackInterval = FP.FromFloat_UNSAFE(0.7f), Reward = 5, HeadHeight = FP.FromFloat_UNSAFE(1.2f), HalfSize = new Vector3(0.25f, 0.75f, 0.3f).ToFPVector3() },
            new ZombieStats { Health = 5, Speed = FP.FromFloat_UNSAFE(0.9f), Damage = 20, AttackInterval = FP.FromFloat_UNSAFE(1.4f), Reward = 15, HeadHeight = FP.FromFloat_UNSAFE(1.7f), HalfSize = new Vector3(0.75f, 1f, 0.6f).ToFPVector3() },
        };
        settings.StopChunks = new[] { 8, 16, 23 };
        settings.DepotParking = new Vector3(-14, 0, 1.5f).ToFPVector3();
        settings.DepotParkRadius = 6;
        FillChunkColliders(settings, chunks);
        settings = ReplaceAsset(settings, $"{ConfigFolder}/ZombieTruckSettings.asset");

        BuildScene(settings, fx);
        AssetDatabase.SaveAssets();
        Debug.Log("ZombieTruckSceneBuilder: built the game from the PS1 art");
    }

    // ------------------------------------------------------------------------------------------------ entity prefabs

    static GameObject BuildTruck(GameObject truckModel, Fx fx)
    {
        var root = EntityRoot("Truck");
        var model = Place(truckModel, root.transform, Vector3.zero, Quaternion.identity);
        foreach (var decor in TruckDecor) Child(model, $"{Truck} {decor}").gameObject.SetActive(false);
        var turretA = Place(Model("Weapons", "Soft Serve Minigun"), root.transform, Socket(model, "socket turret").position, Quaternion.identity);
        var turretB = new GameObject("Second Turret").transform;
        turretB.SetParent(root.transform, false);
        turretB.localPosition = Socket(model, "socket upgrade turret2").position;
        Place(Model("Truck", "Upgrade Second Turret Mount"), turretB, Vector3.zero, Quaternion.identity);
        Place(Model("Weapons", "Soft Serve Minigun"), turretB, new Vector3(0, 0.12f, 0), Quaternion.identity);
        var plow = Place(Model("Truck", "Upgrade Plow"), root.transform, Socket(model, "socket upgrade plow").position, Quaternion.identity);
        var bigPlow = Place(Model("Truck", "Upgrade Plow"), root.transform, Socket(model, "socket upgrade plow").position + Vector3.forward * 0.1f, Quaternion.identity);
        bigPlow.transform.localScale = new Vector3(1.2f, 1.25f, 1.2f);
        var view = root.AddComponent<TruckView>();
        Set(view,
            ("wheels", new[] { "wheel front +X", "wheel front -X", "wheel rear +X", "wheel rear -X" }.Select(n => (Object)Child(model, $"{Truck} {n}")).ToArray()),
            ("steeringPivots", new[] { "wheel front +X steer", "wheel front -X steer" }.Select(n => (Object)Child(model, $"{Truck} {n}")).ToArray()),
            ("basePlow", Child(model, $"{Truck} plow").gameObject),
            ("plowLevels", new Object[] { plow, bigPlow }),
            ("spikes", Place(Model("Truck", "Upgrade Side Spikes"), root.transform, Socket(model, "socket upgrade spikes").position, Quaternion.identity)),
            ("armor", Place(Model("Truck", "Upgrade Window Armor"), root.transform, Socket(model, "socket upgrade armor").position, Quaternion.identity)),
            ("engine", Place(Model("Truck", "Upgrade Exhaust Stacks"), root.transform, Socket(model, "socket upgrade engine").position, Quaternion.identity)),
            ("bigHopper", Place(Model("Truck", "Upgrade Big Hopper"), root.transform, Socket(model, "socket upgrade hopper").position, Quaternion.identity)),
            ("turretMounts", new Object[] { turretA, turretB.gameObject }),
            ("steeringWheel", Child(model, $"{Truck} steering wheel")),
            ("churnCrank", Child(model, $"{Truck} churn crank")),
            ("gaugeNeedle", Child(model, $"{Truck} gauge needle")),
            ("bellMallet", Child(model, $"{Truck} bell mallet")),
            ("engineSound", TruckAudio(root.transform, "Engine", "engine_loop", 4, 60, 0.6f)),
            ("music", TruckAudio(root.transform, "Music Box", "music_entertainer", 6, 80, 0.45f)),
            ("exhaust", TruckParticles(fx, root.transform, "Exhaust", new Vector3(0.8f, 0.35f, -3.05f), new Vector3(0, 0.3f, -1),
                new Layer { Row = FxRow.Smoke, Speed = new Vector2(1, 2), Size = new Vector2(0.25f, 0.4f), Life = new Vector2(1f, 1.6f), Gravity = -0.06f, Grow = 3, Color = new Color(0.55f, 0.52f, 0.6f), Cone = 15 })),
            ("engineStacks", new[] { -1, 1 }.Select(side => (Object)TruckParticles(fx, root.transform, $"Stack Flames {side}",
                Socket(model, "socket upgrade engine").position + new Vector3(side * 1.29f, 2.14f, -1.78f), Vector3.up,
                new Layer { Row = FxRow.Spark, Speed = new Vector2(2, 4), Size = new Vector2(0.2f, 0.35f), Life = new Vector2(0.15f, 0.3f), Gravity = -0.2f, Glow = true, Color = SparkOrange, Cone = 10 })).ToArray()),
            ("wheelDust", new[] { -1, 1 }.Select(side => (Object)TruckParticles(fx, root.transform, $"Wheel Dust {side}", new Vector3(side * 1f, 0.1f, -2.2f), new Vector3(0, 0.4f, -1),
                new Layer { Row = FxRow.Smoke, Speed = new Vector2(0.5f, 1.5f), Size = new Vector2(0.4f, 0.8f), Life = new Vector2(0.6f, 1f), Gravity = -0.02f, Grow = 2, Color = new Color(0.75f, 0.62f, 0.5f), Cone = 30 })).ToArray()),
            ("bloodTrails", new[] { -1, 1 }.Select(side => (Object)TruckParticles(fx, root.transform, $"Blood Trail {side}", new Vector3(side * 1f, 0.035f, -2f), Vector3.forward,
                new Layer { Speed = Vector2.zero, Size = new Vector2(0.3f, 0.5f), Life = new Vector2(10, 10), Gravity = 0, Flat = true, Color = Gore, Max = 400 })).ToArray()));
        return SavePrefab(root);
    }

    static AudioSource TruckAudio(Transform parent, string name, string clip, float minDistance, float maxDistance, float volume)
    {
        var source = new GameObject(name).AddComponent<AudioSource>();
        source.transform.SetParent(parent, false);
        source.clip = AssetDatabase.LoadAssetAtPath<AudioClip>($"{Audio}/{clip}.wav");
        source.loop = true;
        source.playOnAwake = true;
        source.spatialBlend = 1;
        source.minDistance = minDistance;
        source.maxDistance = maxDistance;
        source.rolloffMode = AudioRolloffMode.Linear;
        source.dopplerLevel = 0;
        source.volume = volume;
        return source;
    }

    // A continuously emitting truck effect whose rate TruckView drives; it starts at zero.
    static ParticleSystem TruckParticles(Fx fx, Transform parent, string name, Vector3 position, Vector3 direction, Layer layer)
    {
        layer.Count = 0;
        layer.Loop = true;
        layer.Duration = 1;
        layer.Radius = 0.05f;
        var particles = AddLayer(fx, parent, name, layer);
        particles.transform.localPosition = position;
        particles.transform.localRotation = Quaternion.LookRotation(direction);
        return particles;
    }

    static GameObject BuildSurvivor(string color)
    {
        var root = EntityRoot($"Survivor {color}");
        var body = Place(Model("Characters", $"Player {color}"), root.transform, Vector3.zero, Quaternion.identity);
        Set(body.AddComponent<WalkCycle>(),
            ("legs", new Object[] { Child(body, $"Player {color} leg L"), Child(body, $"Player {color} leg R") }),
            ("arms", new Object[] { Child(body, $"Player {color} arm L") }));
        var ghost = Place(Model("Characters", "Spectator Ghost"), root.transform, Vector3.zero, Quaternion.identity);
        ghost.SetActive(false);
        Set(root.AddComponent<SurvivorView>(), ("body", body), ("ghost", ghost));
        return SavePrefab(root);
    }

    static GameObject BuildZombie(Fx fx, string name, params string[] variants)
    {
        var root = EntityRoot(name);
        var model = new GameObject("Model").transform;
        model.SetParent(root.transform, false);
        var view = root.AddComponent<ZombieView>();
        var serialized = new SerializedObject(view);
        var variantList = serialized.FindProperty("variants");
        variantList.arraySize = variants.Length;
        for (int i = 0; i < variants.Length; i++)
        {
            var instance = Place(Model("Zombies", variants[i]), model, Vector3.zero, Quaternion.identity);
            var entry = variantList.GetArrayElementAtIndex(i);
            entry.FindPropertyRelative("Root").objectReferenceValue = instance;
            var limbs = entry.FindPropertyRelative("Limbs");
            var limbNames = new[] { "arm L", "arm R" };
            limbs.arraySize = limbNames.Length;
            // The core zombie models name their pivots plainly ("arm L"); the outfit variants prefix the asset name.
            var prefix = variants[i] == name ? "" : variants[i] + " ";
            for (int l = 0; l < limbNames.Length; l++) limbs.GetArrayElementAtIndex(l).objectReferenceValue = Child(instance, prefix + limbNames[l]);
            entry.FindPropertyRelative("Head").objectReferenceValue = Child(instance, prefix + "head");
            var walk = instance.AddComponent<WalkCycle>();
            var walkSettings = new SerializedObject(walk);
            var legs = walkSettings.FindProperty("legs");
            legs.arraySize = 2;
            legs.GetArrayElementAtIndex(0).objectReferenceValue = Child(instance, prefix + "leg L");
            legs.GetArrayElementAtIndex(1).objectReferenceValue = Child(instance, prefix + "leg R");
            walkSettings.FindProperty("arms").arraySize = 0;
            walkSettings.FindProperty("strideLength").floatValue = name == "Sprinter" ? 2.2f : 0.8f;
            walkSettings.ApplyModifiedPropertiesWithoutUndo();
        }
        var ice = Primitive(PrimitiveType.Cube, root.transform, "Ice Block", new Vector3(0, 0.95f, 0.15f), new Vector3(0.9f, 1.95f, 0.9f),
            Material("Ice", new Color(0.55f, 1f, 0.92f, 0.45f), "Universal Render Pipeline/Unlit", true), false);
        ice.SetActive(false);
        serialized.FindProperty("model").objectReferenceValue = model;
        serialized.FindProperty("iceBlock").objectReferenceValue = ice;
        serialized.ApplyModifiedPropertiesWithoutUndo();
        var voice = new GameObject("Voice").AddComponent<AudioSource>();
        voice.transform.SetParent(root.transform, false);
        voice.transform.localPosition = Vector3.up * 1.5f;
        voice.playOnAwake = false;
        voice.spatialBlend = 1;
        voice.minDistance = 2;
        voice.maxDistance = 25;
        voice.rolloffMode = AudioRolloffMode.Linear;
        voice.dopplerLevel = 0;
        voice.volume = 0.7f;
        var groans = name == "Sprinter" ? new[] { "groan_sprinter", "groan_2" } : name == "Bloater" ? new[] { "groan_4", "groan_3" } : new[] { "groan_1", "groan_2", "groan_3", "groan_4" };
        Set(view, ("neckGeyserPrefab", fx.NeckGeyser), ("iceShatterPrefab", fx.IceShatter), ("voice", voice),
            ("groans", groans.Select(g => (Object)Clip(g)).ToArray()));
        return SavePrefab(root);
    }

    // One pickup prefab per ItemKind; pints, scoops and tubs carry one model per flavor.
    static GameObject[] BuildItems()
    {
        var prefabs = new GameObject[Enum.GetValues(typeof(ItemKind)).Length];
        var single = new Dictionary<ItemKind, (string category, string name)>
        {
            [ItemKind.ScoopPistol] = ("Weapons", "Scoop Pistol"),
            [ItemKind.SundaeShotgun] = ("Weapons", "Sundae Shotgun"),
            [ItemKind.SprinkleSMG] = ("Weapons", "Sprinkle SMG"),
            [ItemKind.LongSpoon] = ("Weapons", "Long Spoon"),
            [ItemKind.ConeLauncher] = ("Weapons", "Cone Launcher"),
            [ItemKind.BananaHarpoon] = ("Weapons", "Banana Split Harpoon"),
            [ItemKind.Scooper] = ("Weapons", "Scooper"),
            [ItemKind.SprinkleJar] = ("Weapons", "Sprinkle Jar"),
            [ItemKind.SecondScoop] = ("Items", "Second Scoop"),
            [ItemKind.MilkCrate] = ("Items", "Milk Crate"),
            [ItemKind.SugarSack] = ("Items", "Sugar Sack"),
            [ItemKind.CocoaBag] = ("Items", "Cocoa Bag"),
            [ItemKind.StrawberryBasket] = ("Items", "Strawberry Basket"),
            [ItemKind.MintBundle] = ("Items", "Mint Bundle"),
        };
        foreach (var pair in single)
        {
            var root = EntityRoot($"Item {pair.Key}");
            var model = Place(Model(pair.Value.category, pair.Value.name), root.transform, Vector3.zero, Quaternion.identity);
            model.transform.localPosition = Vector3.up * -LocalBounds(model.transform).min.y;
            prefabs[(int)pair.Key] = SavePrefab(root);
        }
        prefabs[(int)ItemKind.Pint] = BuildFlavored("Item Pint", "Items", "Pint {0} Full", 1, false);
        prefabs[(int)ItemKind.Scoop] = BuildFlavored("Item Scoop", "Items", "Scoop Grenade {0}", 1, false);
        prefabs[(int)ItemKind.Tub] = BuildFlavored("Item Tub", "Items", "Flavor Tub {0}", 1, false);
        return prefabs;
    }

    static GameObject BuildFlavored(string name, string category, string pattern, float scale, bool centered)
    {
        var root = EntityRoot(name);
        var view = root.AddComponent<FlavorVariants>();
        var serialized = new SerializedObject(view);
        var list = serialized.FindProperty("variants");
        list.arraySize = Flavors.Length;
        for (int i = 0; i < Flavors.Length; i++)
        {
            var model = Place(Model(category, string.Format(pattern, Flavors[i])), root.transform, Vector3.zero, Quaternion.identity);
            model.transform.localScale = Vector3.one * scale;
            var bounds = LocalBounds(model.transform);
            model.transform.localPosition = centered ? -bounds.center : Vector3.up * -bounds.min.y;
            model.SetActive(i == 0);
            list.GetArrayElementAtIndex(i).FindPropertyRelative("Flavor").enumValueIndex = i + 1;
            list.GetArrayElementAtIndex(i).FindPropertyRelative("Model").objectReferenceValue = model;
        }
        serialized.ApplyModifiedPropertiesWithoutUndo();
        return SavePrefab(root);
    }

    // Truck stations are drawn by the truck model itself; their entity views only show what is stored in them.
    static GameObject[] BuildStations(GameObject truckModel)
    {
        var prefabs = new GameObject[Enum.GetValues(typeof(StationKind)).Length];
        var truck = (GameObject)PrefabUtility.InstantiatePrefab(truckModel);
        prefabs[(int)StationKind.Churn] = BuildStation("Station Churn", null);
        prefabs[(int)StationKind.Freezer] = BuildStation("Station Freezer", (go, view) => SlotModels(view, truck, "freezer rack", "socket slot {0} freezer rack", Flavors.Select(f => (ItemKind.Tub, f, Model("Items", $"Flavor Tub {f}"))).ToArray()));
        prefabs[(int)StationKind.Counter] = BuildStation("Station Counter", (go, view) => SlotModels(view, truck, "scoop counter", "socket pint {0} scoop counter", Flavors.Select(f => (ItemKind.Pint, f, Model("Items", $"Pint {f} Full"))).ToArray()));
        var guns = new[] { (ItemKind.ScoopPistol, "Scoop Pistol"), (ItemKind.SundaeShotgun, "Sundae Shotgun"), (ItemKind.SprinkleSMG, "Sprinkle SMG"),
            (ItemKind.LongSpoon, "Long Spoon"), (ItemKind.ConeLauncher, "Cone Launcher"), (ItemKind.BananaHarpoon, "Banana Split Harpoon") };
        prefabs[(int)StationKind.GunRack] = BuildStation("Station Gun Rack", (go, view) => SlotModels(view, truck, "gun rack", "socket gun {0} gun rack", guns.Select(g => (g.Item1, (string)null, Model("Weapons", g.Item2))).ToArray()));
        prefabs[(int)StationKind.Hopper] = BuildStation("Station Hopper", null);
        prefabs[(int)StationKind.Bell] = BuildStation("Station Bell", null);
        prefabs[(int)StationKind.Turret] = BuildStation("Station Turret", null);
        prefabs[(int)StationKind.GunCrate] = BuildStation("Station Gun Crate", (go, view) =>
        {
            var crate = Place(Model("Items", "Gun Crate Closed"), go.transform, Vector3.zero, Quaternion.identity);
            Set(view, ("lid", Child(crate, "Gun Crate Closed lid hinge")));
        });
        prefabs[(int)StationKind.Shop] = BuildStation("Station Shop", (go, view) =>
        {
            Object.DestroyImmediate(view);
            var label = WorldText(go.transform, "Price Tag", new Vector3(0, 2.1f, 0), 0.04f, "UPGRADE\n$0");
            Set(go.AddComponent<ShopLabel>(), ("text", label));
            Place(Model("Items", "Tip Coin"), go.transform, new Vector3(0, 1.1f, 0), Quaternion.identity);
        });
        prefabs[(int)StationKind.DepotExit] = BuildStation("Station Depot Exit", (go, view) =>
        {
            Place(Model("Road", "Zombies Ahead Sign"), go.transform, Vector3.zero, Quaternion.Euler(0, 90, 0));
            WorldText(go.transform, "Label", new Vector3(0, 2.9f, 0), 0.08f, "NEXT AREA\nE");
        });
        Object.DestroyImmediate(truck);
        return prefabs;
    }

    static GameObject BuildStation(string name, Action<GameObject, StationView> dress)
    {
        var root = EntityRoot(name);
        var view = root.AddComponent<StationView>();
        dress?.Invoke(root, view);
        return SavePrefab(root);
    }

    // Prepares one model per item/flavor at every slot socket, positioned relative to the station's pivot in the truck.
    static void SlotModels(StationView view, GameObject truck, string station, string socketPattern, (ItemKind kind, string flavor, GameObject model)[] options)
    {
        var pivot = Child(truck, $"{Truck} station {station}");
        var serialized = new SerializedObject(view);
        var slots = serialized.FindProperty("slots");
        slots.arraySize = 4;
        for (int s = 0; s < 4; s++)
        {
            var socket = Child(truck, $"{Truck} {string.Format(socketPattern, s + 1)}");
            var anchor = new GameObject($"Slot {s + 1}").transform;
            anchor.SetParent(view.transform, false);
            anchor.localPosition = Quaternion.Inverse(pivot.rotation) * (socket.position - pivot.position);
            anchor.localRotation = Quaternion.Inverse(pivot.rotation) * socket.rotation;
            var models = slots.GetArrayElementAtIndex(s).FindPropertyRelative("Models");
            models.arraySize = options.Length;
            for (int o = 0; o < options.Length; o++)
            {
                var model = Place(options[o].model, anchor, Vector3.zero, Quaternion.identity);
                model.SetActive(false);
                var entry = models.GetArrayElementAtIndex(o);
                entry.FindPropertyRelative("Kind").enumValueIndex = (int)options[o].kind;
                entry.FindPropertyRelative("Flavor").enumValueIndex = options[o].flavor == null ? 0 : Array.IndexOf(Flavors, options[o].flavor) + 1;
                entry.FindPropertyRelative("Model").objectReferenceValue = model;
            }
        }
        serialized.ApplyModifiedPropertiesWithoutUndo();
    }

    // Chunk order follows ChunkKind. Stops and the depot sit on the -X side of a straight, from the chunk edge outward.
    static GameObject[] BuildChunks()
    {
        var chunks = new (ChunkKind kind, string road, string setPiece, Vector3 offset)[]
        {
            (ChunkKind.Straight, "Town Straight", null, default),
            (ChunkKind.Rural, "Rural Straight", null, default),
            (ChunkKind.CurveLeft, "Curve Left", null, default),
            (ChunkKind.CurveRight, "Curve Left", null, default),
            (ChunkKind.Junction, "T Junction", null, default),
            (ChunkKind.Broken, "Broken Road", null, default),
            (ChunkKind.Dairy, "Rural Straight", "Dairy Farm Stop", new Vector3(-10, 0, 0)),
            (ChunkKind.GasStation, "Town Straight", "Gas Station Stop", new Vector3(-10, 0, 0)),
            (ChunkKind.Garden, "Rural Straight", "Garden Stop", new Vector3(-10, 0, 0)),
            (ChunkKind.Wreck, "Town Straight", "Gun Crate Wreck", new Vector3(-4.5f, 0, 0)),
            (ChunkKind.Depot, "Town Straight", "Depot", new Vector3(-10, 0, 0)),
        };
        var prefabs = new GameObject[chunks.Length];
        foreach (var chunk in chunks)
        {
            var root = EntityRoot($"Chunk {chunk.kind}");
            var road = Place(Model("Road", chunk.road), root.transform, Vector3.zero, Quaternion.identity);
            if (chunk.kind == ChunkKind.CurveRight) road.transform.localScale = new Vector3(-1, 1, 1);
            if (chunk.setPiece != null) Place(Model("Stops", chunk.setPiece), root.transform, chunk.offset, Quaternion.identity);
            prefabs[(int)chunk.kind] = SavePrefab(root);
        }
        return prefabs;
    }

    // ------------------------------------------------------------------------------------------------ settings data

    static void FillTruckLayout(ZombieTruckSettings settings, GameObject truckModel)
    {
        var truck = (GameObject)PrefabUtility.InstantiatePrefab(truckModel);
        var boxes = TruckBoxes.ToList();
        var bins = Child(truck, $"{Truck} station ingredient bins");
        var binBounds = LocalBounds(Place(Model("Truck", "Ingredient Bins"), null, Vector3.zero, Quaternion.identity).transform, true);
        boxes.Add(bins.position + bins.rotation * binBounds.center);
        boxes.Add(Abs(bins.rotation * binBounds.extents));
        settings.TruckColliders = new TruckBox[boxes.Count / 2];
        for (int i = 0; i < settings.TruckColliders.Length; i++)
        {
            settings.TruckColliders[i] = new TruckBox { Center = boxes[i * 2].ToFPVector3(), Extents = boxes[i * 2 + 1].ToFPVector3() };
        }
        settings.TruckHalfSize = new Vector3(1.3f, 0, 3.2f).ToFPVector3();
        settings.RoofHeight = FP.FromFloat_UNSAFE(2.92f);
        settings.DriverSeat = new Vector3(0.55f, 0.47f, 1.4f).ToFPVector3();
        settings.CabStand = new Vector3(0f, 0.8f, 1.5f).ToFPVector3();
        settings.LadderBottom = new Vector3(0.53f, 0.8f, -2.2f).ToFPVector3();
        settings.HatchTop = new Vector3(0.74f, 2.95f, -1.8f).ToFPVector3();
        settings.RearInside = new Vector3(0, 0.8f, -2.5f).ToFPVector3();
        settings.RearOutside = new Vector3(0, 0.05f, -3.6f).ToFPVector3();

        var turretSocket = Socket(truck, "socket turret").position;
        var turret2Socket = Socket(truck, "socket upgrade turret2").position + new Vector3(0, 0.12f, 0);
        var minigun = Place(Model("Weapons", "Soft Serve Minigun"), null, Vector3.zero, Quaternion.identity);
        var muzzle = Child(minigun, "Soft Serve Minigun socket muzzle").position;
        var turretBounds = LocalBounds(minigun.transform, true);
        settings.TurretStands = new[] { (turretSocket + new Vector3(0, -0.1f, -0.85f)).ToFPVector3(), (turret2Socket + new Vector3(0, -0.1f, -0.75f)).ToFPVector3() };
        settings.TurretMuzzles = new[] { (turretSocket + muzzle).ToFPVector3(), (turret2Socket + muzzle).ToFPVector3() };

        var placements = new List<Placement>
        {
            TruckStation(truck, StationKind.Churn, "churn", "Churn", 0),
            TruckStation(truck, StationKind.Freezer, "freezer rack", "Freezer Rack", 0),
            TruckStation(truck, StationKind.Counter, "scoop counter", "Scoop Counter", 0),
            TruckStation(truck, StationKind.GunRack, "gun rack", "Gun Rack", 0),
            TruckStation(truck, StationKind.Hopper, "hopper gauge", "Hopper Gauge", 0),
            TruckStation(truck, StationKind.Bell, "roof bell", "Roof Bell", 0),
            new Placement { Station = StationKind.Turret, IsStation = true, Count = 0, Position = turretSocket.ToFPVector3(), Center = turretBounds.center.ToFPVector3(), HalfSize = turretBounds.extents.ToFPVector3() },
            new Placement { Station = StationKind.Turret, IsStation = true, Count = 1, Position = turret2Socket.ToFPVector3(), Center = turretBounds.center.ToFPVector3(), HalfSize = turretBounds.extents.ToFPVector3() },
        };
        settings.TruckStations = placements.ToArray();
        Object.DestroyImmediate(minigun);
        Object.DestroyImmediate(bins.root.gameObject);
    }

    static Placement TruckStation(GameObject truck, StationKind kind, string pivotName, string model, int index)
    {
        var pivot = Child(truck, $"{Truck} station {pivotName}");
        var instance = Place(Model("Truck", model), null, Vector3.zero, Quaternion.identity);
        var bounds = LocalBounds(instance.transform, true);
        Object.DestroyImmediate(instance);
        return new Placement
        {
            IsStation = true, Station = kind, Count = index,
            Position = pivot.position.ToFPVector3(),
            Yaw = FP.FromFloat_UNSAFE(pivot.rotation.eulerAngles.y),
            Center = bounds.center.ToFPVector3(),
            HalfSize = bounds.extents.ToFPVector3(),
        };
    }

    // Pickups and gun crates at the supply stops, and the depot's shop pedestals and exit sign (chunk-local positions).
    static void FillChunkContents(ZombieTruckSettings settings)
    {
        var crateSize = new Vector3(0.42f, 0.25f, 0.23f);
        var contents = new List<Placement>
        {
            Pickup(ChunkKind.Dairy, ItemKind.MilkCrate, -12.3f, 0.2f),
            Pickup(ChunkKind.Dairy, ItemKind.MilkCrate, -12.3f, 1.3f),
            Station(ChunkKind.Dairy, StationKind.GunCrate, -12f, -2.5f, 0, crateSize),
            Pickup(ChunkKind.GasStation, ItemKind.SugarSack, -20.2f, -4.3f),
            Pickup(ChunkKind.GasStation, ItemKind.SugarSack, -20.2f, -3.1f),
            Pickup(ChunkKind.GasStation, ItemKind.CocoaBag, -19.2f, -3.7f),
            Station(ChunkKind.GasStation, StationKind.GunCrate, -18.5f, -1.5f, 0, crateSize),
            Pickup(ChunkKind.Garden, ItemKind.StrawberryBasket, -10.85f, -0.6f),
            Pickup(ChunkKind.Garden, ItemKind.MintBundle, -10.85f, 0.6f),
            Station(ChunkKind.Garden, StationKind.GunCrate, -11.5f, 3f, 0, crateSize),
            Station(ChunkKind.Wreck, StationKind.GunCrate, -5.8f, -3.5f, 15, crateSize),
            Station(ChunkKind.Depot, StationKind.DepotExit, -11f, -6f, 0, new Vector3(0.6f, 1.4f, 0.3f)),
        };
        for (int i = 0; i < ShopStock.Length; i++)
        {
            var pedestal = Station(ChunkKind.Depot, StationKind.Shop, -17.9f, 10f - i * 0.95f, 0, new Vector3(0.35f, 0.9f, 0.35f));
            pedestal.Upgrade = ShopStock[i].upgrade;
            pedestal.Price = ShopStock[i].price;
            contents.Add(pedestal);
        }
        settings.ChunkContents = contents.ToArray();
    }

    // Solid boxes for every chunk's buildings and props, found by rasterizing the art onto a 0.25 m floor grid: any
    // triangle passing through body height marks its cell solid. Cells over asphalt stay open so the truck smashes
    // through cones and barricades on the road, specks thinner than a lamp post are dropped, and the rest is merged into
    // boxes, leaving room around everything placed in the chunk. Writes a top-down check image per chunk to
    // Library/CodexPlaytests/colliders.
    const float ColliderCell = 0.25f;
    const float SolidFrom = 0.4f;
    const float SolidTo = 1.9f;
    const float ColliderHeight = 2.6f;

    static void FillChunkColliders(ZombieTruckSettings settings, GameObject[] chunks)
    {
        var boxes = new List<ChunkBox>();
        Directory.CreateDirectory("Library/CodexPlaytests/colliders");
        for (int kind = 0; kind < chunks.Length; kind++)
        {
            var instance = (GameObject)PrefabUtility.InstantiatePrefab(chunks[kind]);
            var triangles = new List<Vector3>();
            var onRoad = new List<bool>();
            // Only the road model itself counts as asphalt; the stops' ground pads sit at the same height.
            var roadModel = instance.transform.GetChild(0);
            foreach (var filter in instance.GetComponentsInChildren<MeshFilter>())
            {
                var mesh = filter.sharedMesh;
                if (!mesh.isReadable) throw new InvalidOperationException($"{mesh.name} is not readable; run Tools > Zombie Truck > Reimport PS1 Art");
                var toRoot = instance.transform.worldToLocalMatrix * filter.transform.localToWorldMatrix;
                var vertices = mesh.vertices;
                var isRoad = filter.transform.IsChildOf(roadModel);
                foreach (var index in mesh.triangles)
                {
                    triangles.Add(toRoot.MultiplyPoint3x4(vertices[index]));
                    onRoad.Add(isRoad);
                }
            }
            Object.DestroyImmediate(instance);

            var min = new Vector2(triangles.Min(v => v.x), triangles.Min(v => v.z));
            var width = Mathf.CeilToInt((triangles.Max(v => v.x) - min.x) / ColliderCell) + 1;
            var depth = Mathf.CeilToInt((triangles.Max(v => v.z) - min.y) / ColliderCell) + 1;
            var solid = new bool[width, depth];
            var road = new bool[width, depth];
            for (int t = 0; t < triangles.Count; t += 3)
            {
                var a = triangles[t];
                var b = triangles[t + 1];
                var c = triangles[t + 2];
                var low = Mathf.Min(a.y, b.y, c.y);
                var high = Mathf.Max(a.y, b.y, c.y);
                var asphalt = onRoad[t] && high < 0.02f && low > -0.02f;
                if (!asphalt && (high < SolidFrom || low > SolidTo)) continue;
                var steps = Mathf.Max(1, Mathf.CeilToInt(Mathf.Max((b - a).magnitude, (c - a).magnitude, (c - b).magnitude) / (ColliderCell * 0.4f)));
                for (int i = 0; i <= steps; i++)
                {
                    for (int j = 0; j <= steps - i; j++)
                    {
                        var p = a + (b - a) * (i / (float)steps) + (c - a) * (j / (float)steps);
                        // Interpolated points can land a hair outside the vertex bounds.
                        var x = Mathf.Clamp(Mathf.FloorToInt((p.x - min.x) / ColliderCell), 0, width - 1);
                        var z = Mathf.Clamp(Mathf.FloorToInt((p.z - min.y) / ColliderCell), 0, depth - 1);
                        if (asphalt) road[x, z] = true;
                        else if (p.y >= SolidFrom && p.y <= SolidTo) solid[x, z] = true;
                    }
                }
            }
            for (int x = 0; x < width; x++)
            {
                for (int z = 0; z < depth; z++) solid[x, z] &= !road[x, z];
            }
            // Placed items and stations stay reachable: their own colliders replace the art around them.
            foreach (var placement in settings.ChunkContents.Where(p => (int)p.Chunk == kind))
            {
                var position = placement.Position.ToUnityVector3();
                var radius = placement.IsStation ? 1.2f : 0.6f;
                for (int x = 0; x < width; x++)
                {
                    for (int z = 0; z < depth; z++)
                    {
                        var cell = new Vector2(min.x + (x + 0.5f) * ColliderCell, min.y + (z + 0.5f) * ColliderCell);
                        if ((cell - new Vector2(position.x, position.z)).sqrMagnitude < radius * radius) solid[x, z] = false;
                    }
                }
            }
            DropSpecks(solid, 3);

            var owner = new int[width, depth];
            var count = 0;
            for (int z = 0; z < depth; z++)
            {
                for (int x = 0; x < width; x++)
                {
                    if (!solid[x, z] || owner[x, z] != 0) continue;
                    var x1 = x;
                    while (x1 + 1 < width && solid[x1 + 1, z] && owner[x1 + 1, z] == 0) x1++;
                    var z1 = z;
                    while (z1 + 1 < depth && Enumerable.Range(x, x1 - x + 1).All(cx => solid[cx, z1 + 1] && owner[cx, z1 + 1] == 0)) z1++;
                    count++;
                    for (int cz = z; cz <= z1; cz++)
                    {
                        for (int cx = x; cx <= x1; cx++) owner[cx, cz] = count;
                    }
                    var size = new Vector3((x1 - x + 1) * ColliderCell, ColliderHeight, (z1 - z + 1) * ColliderCell);
                    var center = new Vector3(min.x + x * ColliderCell + size.x / 2, ColliderHeight / 2, min.y + z * ColliderCell + size.z / 2);
                    boxes.Add(new ChunkBox { Chunk = (ChunkKind)kind, Center = center.ToFPVector3(), Extents = (size / 2).ToFPVector3() });
                }
            }

            var placements = settings.ChunkContents.Where(p => (int)p.Chunk == kind).Select(p => p.Position.ToUnityVector3()).ToList();
            foreach (var position in placements)
            {
                var cell = new Vector2Int(Mathf.FloorToInt((position.x - min.x) / ColliderCell), Mathf.FloorToInt((position.z - min.y) / ColliderCell));
                if (owner[cell.x, cell.y] != 0) Debug.LogWarning($"ZombieTruckSceneBuilder: {(ChunkKind)kind} has something placed inside a solid cell at {position}");
            }
            if (kind == (int)ChunkKind.Depot) placements.Add(settings.DepotParking.ToUnityVector3());
            WriteColliderImage((ChunkKind)kind, owner, road, min, placements);
            Debug.Log($"ZombieTruckSceneBuilder: {(ChunkKind)kind} collider boxes: {count}");
        }
        settings.ChunkColliders = boxes.ToArray();
    }

    static void DropSpecks(bool[,] solid, int minCells)
    {
        var width = solid.GetLength(0);
        var depth = solid.GetLength(1);
        var seen = new bool[width, depth];
        for (int x = 0; x < width; x++)
        {
            for (int z = 0; z < depth; z++)
            {
                if (!solid[x, z] || seen[x, z]) continue;
                var island = new List<Vector2Int>();
                var open = new Stack<Vector2Int>();
                open.Push(new Vector2Int(x, z));
                seen[x, z] = true;
                while (open.Count > 0)
                {
                    var cell = open.Pop();
                    island.Add(cell);
                    foreach (var step in new[] { Vector2Int.left, Vector2Int.right, Vector2Int.up, Vector2Int.down })
                    {
                        var next = cell + step;
                        if (next.x < 0 || next.y < 0 || next.x >= width || next.y >= depth || !solid[next.x, next.y] || seen[next.x, next.y]) continue;
                        seen[next.x, next.y] = true;
                        open.Push(next);
                    }
                }
                if (island.Count >= minCells) continue;
                foreach (var cell in island) solid[cell.x, cell.y] = false;
            }
        }
    }

    // Top-down view, +Z up the image: asphalt grey, each collider box its own color, placements as white squares.
    static void WriteColliderImage(ChunkKind kind, int[,] owner, bool[,] road, Vector2 min, List<Vector3> placements)
    {
        const int scale = 4;
        var width = owner.GetLength(0);
        var depth = owner.GetLength(1);
        var image = new Texture2D(width * scale, depth * scale);
        var pixels = new Color32[width * scale * depth * scale];
        for (int x = 0; x < width; x++)
        {
            for (int z = 0; z < depth; z++)
            {
                var id = owner[x, z];
                var color = id != 0 ? (Color32)Color.HSVToRGB(id * 0.618f % 1f, 0.7f, 0.95f) : road[x, z] ? new Color32(70, 70, 80, 255) : new Color32(30, 60, 30, 255);
                for (int px = 0; px < scale; px++)
                {
                    for (int pz = 0; pz < scale; pz++) pixels[(z * scale + pz) * width * scale + x * scale + px] = color;
                }
            }
        }
        foreach (var position in placements)
        {
            var cx = Mathf.FloorToInt((position.x - min.x) / ColliderCell) * scale;
            var cz = Mathf.FloorToInt((position.z - min.y) / ColliderCell) * scale;
            for (int px = -3; px <= 3 + scale; px++)
            {
                for (int pz = -3; pz <= 3 + scale; pz++)
                {
                    var ix = cx + px;
                    var iz = cz + pz;
                    if (ix >= 0 && iz >= 0 && ix < width * scale && iz < depth * scale) pixels[iz * width * scale + ix] = new Color32(255, 255, 255, 255);
                }
            }
        }
        image.SetPixels32(pixels);
        File.WriteAllBytes($"Library/CodexPlaytests/colliders/{kind}.png", image.EncodeToPNG());
        Object.DestroyImmediate(image);
    }

    static Placement Pickup(ChunkKind chunk, ItemKind item, float x, float z)
    {
        return new Placement { Chunk = chunk, Item = item, Count = 1, Position = new Vector3(x, 0.05f, z).ToFPVector3() };
    }

    static Placement Station(ChunkKind chunk, StationKind kind, float x, float z, float yaw, Vector3 halfSize)
    {
        return new Placement
        {
            Chunk = chunk, IsStation = true, Station = kind, Position = new Vector3(x, 0, z).ToFPVector3(), Yaw = FP.FromFloat_UNSAFE(yaw),
            Center = new Vector3(0, halfSize.y, 0).ToFPVector3(), HalfSize = halfSize.ToFPVector3(),
        };
    }

    // ------------------------------------------------------------------------------------------------ effects

    static GameObject[] BuildGibs()
    {
        var gibs = Place(Model("FX", "Zombie Gibs"), null, Vector3.zero, Quaternion.identity);
        var prefabs = new List<GameObject>();
        foreach (Transform piece in gibs.transform)
        {
            var root = new GameObject($"Gib {prefabs.Count + 1}");
            var copy = Object.Instantiate(piece.gameObject, root.transform);
            copy.transform.localPosition = -LocalBounds(copy.transform).center;
            var bounds = LocalBounds(root.transform);
            var collider = root.AddComponent<BoxCollider>();
            collider.center = bounds.center;
            collider.size = Vector3.Max(bounds.size, Vector3.one * 0.05f);
            root.AddComponent<Rigidbody>().mass = 0.3f;
            prefabs.Add(SavePrefab(root, $"{PrefabFolder}/FX"));
        }
        Object.DestroyImmediate(gibs);
        return prefabs.ToArray();
    }

    // Rows of Assets/Art/Sprites/fx_atlas.png, top to bottom (drawn by Art/Tools/zombie-styles/fx_sprites.py).
    enum FxRow { Blob, Star, Smoke, Sprinkle, Spark, Drop, Ring, Shard }

    static readonly Color Gore = new Color(0.78f, 0.04f, 0.2f);
    static readonly Color DarkGore = new Color(0.45f, 0.02f, 0.12f);
    static readonly Color SmokeWhite = new Color(0.95f, 0.92f, 1f);
    static readonly Color SparkYellow = new Color(1f, 0.85f, 0.3f);
    static readonly Color SparkOrange = new Color(1f, 0.5f, 0.15f);
    static readonly Color Ice = new Color(0.75f, 1f, 0.95f);

    class Fx
    {
        public Material Solid, Glow;
        public FxBurst Hit, Kill, Headshot, NeckGeyser, IceShatter, Bloater, Crash, Confetti;
        public FxBurst[] Explosions;
        public GameObject[] Gibs;
    }

    // One particle layer of an effect. The defaults describe a short burst of goo blobs falling under gravity.
    class Layer
    {
        public FxRow Row = FxRow.Blob;
        public int Count = 10;
        public Vector2 Speed = new Vector2(2, 5);
        public Vector2 Size = new Vector2(0.1f, 0.2f);
        public Vector2 Life = new Vector2(0.5f, 1f);
        public float Gravity = 1.5f;
        public Color Color = Color.white;
        public bool Glow, Stretch, Flat, Collide, Rainbow, Loop;
        public float Radius = 0.15f;
        public float Cone = -1;     // cone half-angle pointing up; negative emits in all directions
        public float Grow;          // > 0: grows to this multiple of its start size (smoke, rings); 0: holds, then shrinks away
        public float Rate;          // continuous emission per second (0 = burst only)
        public float Duration = 0.1f;
        public int Max = 1000;
    }

    static Fx BuildEffects()
    {
        ConfigureSprites();
        var fx = new Fx { Solid = FxMaterial("FX Atlas", false), Glow = FxMaterial("FX Atlas Glow", true) };
        fx.Hit = FxPrefab("Hit Burst", 2.5f, root =>
        {
            AddLayer(fx, root, "Gore", new Layer { Count = 6, Speed = new Vector2(2, 4), Size = new Vector2(0.08f, 0.16f), Color = Gore, Collide = true });
            AddLayer(fx, root, "Sparks", new Layer { Row = FxRow.Spark, Count = 6, Speed = new Vector2(2, 5), Size = new Vector2(0.12f, 0.25f), Life = new Vector2(0.12f, 0.25f), Gravity = 0, Glow = true, Color = SparkYellow });
            AddModel(root, "Hit Star", 0.18f, 1.3f, false, true, new Vector3(0, 0, 500), 0.6f);
            return new[]
            {
                AddLayer(fx, root, "Blobs", new Layer { Count = 20, Speed = new Vector2(2, 6), Size = new Vector2(0.1f, 0.24f), Collide = true }),
                AddLayer(fx, root, "Drops", new Layer { Row = FxRow.Drop, Count = 10, Speed = new Vector2(3, 7), Size = new Vector2(0.06f, 0.12f), Gravity = 2, Stretch = true }),
            };
        });
        fx.Kill = FxPrefab("Kill Burst", 3f, root =>
        {
            var tinted = new[]
            {
                AddLayer(fx, root, "Blobs", new Layer { Count = 50, Speed = new Vector2(4, 10), Size = new Vector2(0.18f, 0.4f), Life = new Vector2(0.9f, 1.5f), Collide = true, Cone = 70, Radius = 0.3f }),
                AddLayer(fx, root, "Drops", new Layer { Row = FxRow.Drop, Count = 30, Speed = new Vector2(5, 11), Size = new Vector2(0.08f, 0.15f), Gravity = 2, Stretch = true, Cone = 60, Radius = 0.3f }),
            };
            AddLayer(fx, root, "Gore Blobs", new Layer { Count = 45, Speed = new Vector2(3, 9), Size = new Vector2(0.14f, 0.32f), Life = new Vector2(0.9f, 1.5f), Color = Gore, Collide = true, Cone = 70, Radius = 0.3f });
            AddLayer(fx, root, "Gore Drops", new Layer { Row = FxRow.Drop, Count = 20, Speed = new Vector2(4, 9), Size = new Vector2(0.08f, 0.14f), Gravity = 2, Stretch = true, Color = DarkGore });
            AddLayer(fx, root, "Confetti", new Layer { Row = FxRow.Sprinkle, Count = 45, Speed = new Vector2(4, 9), Size = new Vector2(0.12f, 0.2f), Life = new Vector2(1.2f, 2f), Gravity = 1, Rainbow = true, Collide = true, Cone = 60 });
            AddLayer(fx, root, "Puff", new Layer { Row = FxRow.Smoke, Count = 6, Speed = new Vector2(0.5f, 1.5f), Size = new Vector2(0.5f, 0.9f), Life = new Vector2(0.4f, 0.7f), Gravity = -0.1f, Color = new Color(1f, 0.85f, 0.9f), Grow = 2, Radius = 0.4f });
            AddLayer(fx, root, "Flash", new Layer { Row = FxRow.Star, Count = 1, Speed = Vector2.zero, Size = new Vector2(1.6f, 1.6f), Life = new Vector2(0.08f, 0.08f), Gravity = 0, Glow = true, Color = SparkYellow, Radius = 0 });
            AddModel(root, "Blood Splat Burst", 0.3f, 1.1f, false, false, Vector3.zero, 0.8f);
            return tinted;
        });
        fx.Headshot = FxPrefab("Headshot Burst", 3f, root =>
        {
            AddModel(root, "Headshot Star", 0.55f, 1.6f, false, true, new Vector3(0, 0, 540), 1.2f);
            AddLayer(fx, root, "Sparks", new Layer { Row = FxRow.Spark, Count = 20, Speed = new Vector2(4, 9), Size = new Vector2(0.15f, 0.3f), Life = new Vector2(0.2f, 0.4f), Gravity = 0.5f, Glow = true, Stretch = true, Color = SparkYellow });
            AddLayer(fx, root, "Gore Fountain", new Layer { Count = 30, Speed = new Vector2(6, 11), Size = new Vector2(0.12f, 0.28f), Life = new Vector2(1f, 1.6f), Color = Gore, Cone = 25, Collide = true });
            AddLayer(fx, root, "Confetti", new Layer { Row = FxRow.Sprinkle, Count = 25, Speed = new Vector2(4, 9), Size = new Vector2(0.12f, 0.2f), Life = new Vector2(1f, 1.6f), Gravity = 1, Rainbow = true, Cone = 40 });
            return new[] { AddLayer(fx, root, "Flavor", new Layer { Count = 15, Speed = new Vector2(4, 8), Size = new Vector2(0.12f, 0.25f), Cone = 35, Collide = true }) };
        });
        fx.NeckGeyser = FxPrefab("Neck Geyser", 3.5f, root => new[]
        {
            AddLayer(fx, root, "Spray", new Layer { Row = FxRow.Drop, Count = 0, Rate = 70, Duration = 1.4f, Speed = new Vector2(4, 7), Size = new Vector2(0.07f, 0.13f), Life = new Vector2(0.6f, 1f), Gravity = 2, Stretch = true, Cone = 12, Radius = 0.05f }),
            AddLayer(fx, root, "Gobs", new Layer { Count = 0, Rate = 25, Duration = 1.4f, Speed = new Vector2(3, 6), Size = new Vector2(0.1f, 0.2f), Life = new Vector2(0.8f, 1.2f), Cone = 20, Radius = 0.05f, Collide = true }),
        });
        fx.IceShatter = FxPrefab("Ice Shatter", 2.5f, root =>
        {
            AddLayer(fx, root, "Glints", new Layer { Row = FxRow.Star, Count = 12, Speed = new Vector2(1, 3), Size = new Vector2(0.1f, 0.2f), Life = new Vector2(0.3f, 0.6f), Gravity = 0, Glow = true });
            AddLayer(fx, root, "Mist", new Layer { Row = FxRow.Smoke, Count = 6, Speed = new Vector2(0.5f, 1.5f), Size = new Vector2(0.5f, 0.9f), Life = new Vector2(0.6f, 1f), Gravity = -0.05f, Grow = 2, Color = Ice, Radius = 0.4f });
            return new[] { AddLayer(fx, root, "Shards", new Layer { Row = FxRow.Shard, Count = 30, Speed = new Vector2(3, 7), Size = new Vector2(0.12f, 0.3f), Gravity = 2, Color = Ice, Collide = true, Radius = 0.4f }) };
        });
        var flavorModels = new[] { "Sprinkle Shrapnel Spray", "Vanilla Splat Burst", "Chocolate Splat Burst", "Strawberry Splash Burst", "Mint Freeze Burst" };
        fx.Explosions = new FxBurst[flavorModels.Length];
        for (int f = 0; f < flavorModels.Length; f++)
        {
            var flavor = f;
            fx.Explosions[f] = FxPrefab($"Explosion {(Flavor)f}", 3f, root =>
            {
                AddLayer(fx, root, "Flash", new Layer { Row = FxRow.Star, Count = 1, Speed = Vector2.zero, Size = new Vector2(8, 8), Life = new Vector2(0.12f, 0.12f), Gravity = 0, Glow = true, Color = SparkYellow, Radius = 0 });
                AddLayer(fx, root, "Confetti", new Layer { Row = FxRow.Sprinkle, Count = 80, Speed = new Vector2(6, 14), Size = new Vector2(0.15f, 0.25f), Life = new Vector2(1.5f, 2.5f), Gravity = 1, Rainbow = true, Collide = true, Cone = 65, Radius = 0.5f });
                AddLayer(fx, root, "Smoke", new Layer { Row = FxRow.Smoke, Count = 18, Speed = new Vector2(1.5f, 4), Size = new Vector2(1.4f, 2.4f), Life = new Vector2(1.2f, 2.2f), Gravity = -0.1f, Grow = 2.2f, Color = SmokeWhite, Radius = 1f });
                AddLayer(fx, root, "Sparks", new Layer { Row = FxRow.Spark, Count = 30, Speed = new Vector2(8, 16), Size = new Vector2(0.2f, 0.4f), Life = new Vector2(0.2f, 0.45f), Gravity = 1, Glow = true, Stretch = true, Color = SparkYellow, Radius = 0.5f });
                AddModel(root, "Scoop Grenade Blast", 0.45f, 1.15f, false, false, new Vector3(0, 90, 0), 1f);
                AddModel(root, "Shockwave Ring", 0.5f, 1.2f, true, false, Vector3.zero, 1.1f);
                AddModel(root, flavorModels[flavor], 0.6f, 1.2f, false, false, new Vector3(0, 60, 0), 1.2f);
                if (flavor == (int)Flavor.Mint) AddLayer(fx, root, "Ice", new Layer { Row = FxRow.Shard, Count = 40, Speed = new Vector2(4, 9), Size = new Vector2(0.15f, 0.35f), Gravity = 1.5f, Color = Ice, Collide = true, Radius = 0.6f });
                return new[]
                {
                    AddLayer(fx, root, "Blobs", new Layer { Count = 100, Speed = new Vector2(6, 15), Size = new Vector2(0.3f, 0.6f), Life = new Vector2(1f, 1.8f), Collide = true, Cone = 70, Radius = 0.6f }),
                    AddLayer(fx, root, "Drops", new Layer { Row = FxRow.Drop, Count = 50, Speed = new Vector2(8, 16), Size = new Vector2(0.12f, 0.24f), Gravity = 2, Stretch = true, Cone = 65, Radius = 0.6f }),
                    AddLayer(fx, root, "Fireball", new Layer { Row = FxRow.Smoke, Count = 14, Speed = new Vector2(2, 5), Size = new Vector2(1.2f, 2f), Life = new Vector2(0.25f, 0.45f), Gravity = -0.3f, Glow = true, Grow = 1.8f, Radius = 0.8f }),
                    AddLayer(fx, root, "Ring", new Layer { Row = FxRow.Ring, Count = 1, Speed = Vector2.zero, Size = new Vector2(7, 7), Life = new Vector2(0.35f, 0.35f), Gravity = 0, Glow = true, Flat = true, Grow = 20, Radius = 0 }),
                };
            });
        }
        fx.Bloater = FxPrefab("Bloater Burst", 3.5f, root =>
        {
            AddLayer(fx, root, "Flash", new Layer { Row = FxRow.Star, Count = 1, Speed = Vector2.zero, Size = new Vector2(6, 6), Life = new Vector2(0.12f, 0.12f), Gravity = 0, Glow = true, Color = new Color(0.8f, 1f, 0.4f), Radius = 0 });
            AddLayer(fx, root, "Stink", new Layer { Row = FxRow.Smoke, Count = 20, Speed = new Vector2(1, 3), Size = new Vector2(1f, 2f), Life = new Vector2(1.2f, 2.2f), Gravity = -0.05f, Grow = 2.5f, Color = new Color(0.55f, 0.75f, 0.35f), Radius = 1f });
            AddLayer(fx, root, "Confetti", new Layer { Row = FxRow.Sprinkle, Count = 40, Speed = new Vector2(5, 12), Size = new Vector2(0.15f, 0.25f), Life = new Vector2(1.2f, 2f), Gravity = 1, Rainbow = true, Collide = true, Radius = 0.5f });
            AddModel(root, "Bloater Pop Blast", 0.6f, 1.1f, false, false, new Vector3(0, 45, 0), 1f);
            AddModel(root, "Shockwave Ring", 0.55f, 1.4f, true, false, Vector3.zero, 1.2f);
            return new[]
            {
                AddLayer(fx, root, "Blobs", new Layer { Count = 140, Speed = new Vector2(6, 16), Size = new Vector2(0.35f, 0.7f), Life = new Vector2(1.2f, 2f), Collide = true, Cone = 75, Radius = 0.8f }),
                AddLayer(fx, root, "Drops", new Layer { Row = FxRow.Drop, Count = 70, Speed = new Vector2(8, 16), Size = new Vector2(0.12f, 0.25f), Gravity = 2, Stretch = true, Cone = 70, Radius = 0.8f }),
                AddLayer(fx, root, "Ring", new Layer { Row = FxRow.Ring, Count = 1, Speed = Vector2.zero, Size = new Vector2(9, 9), Life = new Vector2(0.4f, 0.4f), Gravity = 0, Glow = true, Flat = true, Grow = 20, Radius = 0 }),
            };
        });
        fx.Crash = FxPrefab("Crash Burst", 3f, root =>
        {
            AddLayer(fx, root, "Sparks", new Layer { Row = FxRow.Spark, Count = 40, Speed = new Vector2(5, 12), Size = new Vector2(0.15f, 0.3f), Life = new Vector2(0.2f, 0.5f), Gravity = 1, Glow = true, Stretch = true, Color = SparkOrange, Radius = 0.5f });
            AddLayer(fx, root, "Glass", new Layer { Row = FxRow.Shard, Count = 25, Speed = new Vector2(3, 8), Size = new Vector2(0.1f, 0.25f), Gravity = 2, Color = new Color(0.7f, 0.9f, 1f), Collide = true, Radius = 0.5f });
            AddLayer(fx, root, "Debris", new Layer { Row = FxRow.Shard, Count = 15, Speed = new Vector2(3, 7), Size = new Vector2(0.15f, 0.3f), Gravity = 2.5f, Color = new Color(0.35f, 0.3f, 0.4f), Collide = true, Radius = 0.5f });
            AddLayer(fx, root, "Smoke", new Layer { Row = FxRow.Smoke, Count = 10, Speed = new Vector2(0.5f, 2f), Size = new Vector2(0.8f, 1.4f), Life = new Vector2(1f, 1.8f), Gravity = -0.06f, Grow = 2.5f, Color = new Color(0.3f, 0.27f, 0.35f), Radius = 0.8f });
            return new ParticleSystem[0];
        });
        fx.Confetti = FxPrefab("Confetti Burst", 3f, root =>
        {
            AddLayer(fx, root, "Sprinkles", new Layer { Row = FxRow.Sprinkle, Count = 80, Speed = new Vector2(5, 10), Size = new Vector2(0.12f, 0.2f), Life = new Vector2(1.5f, 2.5f), Gravity = 0.8f, Rainbow = true, Cone = 35, Collide = true });
            return new[] { AddLayer(fx, root, "Stars", new Layer { Row = FxRow.Star, Count = 15, Speed = new Vector2(2, 5), Size = new Vector2(0.2f, 0.35f), Life = new Vector2(0.4f, 0.8f), Gravity = 0, Glow = true }) };
        });
        fx.Gibs = BuildGibs();
        return fx;
    }

    // Point-filtered pixel sprites: the particle atlas as a texture, the HUD overlays as UI sprites.
    static void ConfigureSprites()
    {
        foreach (var path in Directory.GetFiles(Sprites, "*.png"))
        {
            var importer = (TextureImporter)AssetImporter.GetAtPath(path.Replace('\\', '/'));
            var atlas = path.EndsWith("fx_atlas.png");
            importer.textureType = atlas ? TextureImporterType.Default : TextureImporterType.Sprite;
            importer.spriteImportMode = SpriteImportMode.Single;
            importer.filterMode = FilterMode.Point;
            importer.mipmapEnabled = false;
            importer.textureCompression = TextureImporterCompression.Uncompressed;
            importer.alphaIsTransparency = true;
            importer.wrapMode = TextureWrapMode.Clamp;
            importer.SaveAndReimport();
        }
    }

    static Material FxMaterial(string name, bool glow)
    {
        var path = $"{MaterialFolder}/{name}.mat";
        var material = AssetDatabase.LoadAssetAtPath<Material>(path);
        if (material == null)
        {
            material = new Material(Shader.Find("Universal Render Pipeline/Particles/Unlit"));
            AssetDatabase.CreateAsset(material, path);
        }
        material.SetTexture("_BaseMap", AssetDatabase.LoadAssetAtPath<Texture2D>($"{Sprites}/fx_atlas.png"));
        material.SetColor("_BaseColor", Color.white);
        // Solid particles are alpha-clipped pixel shapes that sort like geometry; glow particles add light on top.
        material.SetFloat("_Surface", glow ? (float)BaseShaderGUI.SurfaceType.Transparent : (float)BaseShaderGUI.SurfaceType.Opaque);
        material.SetFloat("_Blend", glow ? (float)BaseShaderGUI.BlendMode.Additive : (float)BaseShaderGUI.BlendMode.Alpha);
        material.SetFloat("_AlphaClip", glow ? 0f : 1f);
        material.SetFloat("_Cutoff", 0.5f);
        material.SetFloat("_Cull", (float)BaseShaderGUI.RenderFace.Both);
        BaseShaderGUI.SetMaterialKeywords(material, null, ParticleGUI.SetMaterialKeywords);
        EditorUtility.SetDirty(material);
        return material;
    }

    static FxBurst FxPrefab(string name, float lifetime, Func<Transform, ParticleSystem[]> build)
    {
        var root = new GameObject(name);
        var tinted = build(root.transform);
        Set(root.AddComponent<FxBurst>(), ("tinted", tinted.Cast<Object>().ToArray()), ("lifetime", lifetime));
        return SavePrefab(root, $"{PrefabFolder}/FX").GetComponent<FxBurst>();
    }

    static ParticleSystem AddLayer(Fx fx, Transform parent, string name, Layer layer)
    {
        var go = new GameObject(name);
        go.transform.SetParent(parent, false);
        // Cone shapes emit along local +Z; turn them to spray upward.
        if (layer.Cone >= 0) go.transform.localRotation = Quaternion.Euler(-90, 0, 0);
        var particles = go.AddComponent<ParticleSystem>();
        particles.Stop(true, ParticleSystemStopBehavior.StopEmittingAndClear);
        var main = particles.main;
        main.duration = layer.Duration;
        main.loop = layer.Loop;
        main.startLifetime = new ParticleSystem.MinMaxCurve(layer.Life.x, layer.Life.y);
        main.startSpeed = new ParticleSystem.MinMaxCurve(layer.Speed.x, layer.Speed.y);
        main.startSize = new ParticleSystem.MinMaxCurve(layer.Size.x, layer.Size.y);
        main.startRotation = new ParticleSystem.MinMaxCurve(0, Mathf.PI * 2);
        main.startColor = layer.Rainbow ? new ParticleSystem.MinMaxGradient(Rainbow()) { mode = ParticleSystemGradientMode.RandomColor } : new ParticleSystem.MinMaxGradient(layer.Color);
        main.gravityModifier = layer.Gravity;
        main.simulationSpace = ParticleSystemSimulationSpace.World;
        main.scalingMode = ParticleSystemScalingMode.Hierarchy;
        main.maxParticles = layer.Max;
        var emission = particles.emission;
        emission.rateOverTime = layer.Rate;
        emission.SetBursts(layer.Count > 0 ? new[] { new ParticleSystem.Burst(0, (short)layer.Count) } : new ParticleSystem.Burst[0]);
        var shape = particles.shape;
        shape.shapeType = layer.Cone >= 0 ? ParticleSystemShapeType.Cone : ParticleSystemShapeType.Sphere;
        shape.angle = Mathf.Max(layer.Cone, 0);
        shape.radius = Mathf.Max(layer.Radius, 0.0001f);
        var size = particles.sizeOverLifetime;
        size.enabled = true;
        size.size = layer.Grow > 0
            ? new ParticleSystem.MinMaxCurve(1, new AnimationCurve(new Keyframe(0, 1 / layer.Grow), new Keyframe(1, 1)))
            : new ParticleSystem.MinMaxCurve(1, new AnimationCurve(new Keyframe(0, 1), new Keyframe(0.75f, 1), new Keyframe(1, 0)));
        if (layer.Grow > 0) main.startSize = new ParticleSystem.MinMaxCurve(layer.Size.x * layer.Grow, layer.Size.y * layer.Grow);
        var sheet = particles.textureSheetAnimation;
        sheet.enabled = true;
        sheet.mode = ParticleSystemAnimationMode.Grid;
        sheet.numTilesX = 8;
        sheet.numTilesY = 8;
        sheet.animation = ParticleSystemAnimationType.SingleRow;
        sheet.rowMode = ParticleSystemAnimationRowMode.Custom;
        sheet.rowIndex = (int)layer.Row;
        // A random but fixed frame of the row per particle.
        sheet.frameOverTime = new ParticleSystem.MinMaxCurve(0f, 0.999f);
        if (layer.Collide)
        {
            var collision = particles.collision;
            collision.enabled = true;
            collision.type = ParticleSystemCollisionType.World;
            collision.mode = ParticleSystemCollisionMode.Collision3D;
            collision.dampen = 0.7f;
            collision.bounce = 0.15f;
            collision.radiusScale = 0.5f;
            collision.quality = ParticleSystemCollisionQuality.Medium;
        }
        var renderer = go.GetComponent<ParticleSystemRenderer>();
        renderer.sharedMaterial = layer.Glow ? fx.Glow : fx.Solid;
        renderer.renderMode = layer.Flat ? ParticleSystemRenderMode.HorizontalBillboard : layer.Stretch ? ParticleSystemRenderMode.Stretch : ParticleSystemRenderMode.Billboard;
        renderer.velocityScale = 0.06f;
        renderer.lengthScale = 1.5f;
        renderer.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
        renderer.receiveShadows = false;
        return particles;
    }

    static Gradient Rainbow()
    {
        var gradient = new Gradient();
        gradient.SetKeys(
            new[] { new GradientColorKey(new Color(1f, 0.31f, 0.64f), 0), new GradientColorKey(new Color(1f, 0.88f, 0.29f), 0.25f),
                new GradientColorKey(new Color(0.22f, 0.95f, 0.76f), 0.5f), new GradientColorKey(new Color(0.18f, 0.53f, 1f), 0.75f), new GradientColorKey(Color.white, 1) },
            new[] { new GradientAlphaKey(1, 0), new GradientAlphaKey(1, 1) });
        gradient.mode = GradientMode.Fixed;
        return gradient;
    }

    // An FX model that pops in and out (or spreads out flat, for rings).
    static void AddModel(Transform parent, string model, float duration, float overshoot, bool ring, bool faceCamera, Vector3 spin, float scale)
    {
        var instance = Place(Model("FX", model), parent, Vector3.zero, Quaternion.identity);
        instance.transform.localScale = Vector3.one * scale;
        foreach (var renderer in instance.GetComponentsInChildren<Renderer>()) renderer.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
        Set(instance.AddComponent<FxExpand>(), ("duration", duration), ("overshoot", overshoot), ("ring", ring), ("faceCamera", faceCamera), ("spin", spin));
    }

    static GameObject ModelPrefab(string name, string category, string model)
    {
        var root = new GameObject(name);
        Place(Model(category, model), root.transform, Vector3.zero, Quaternion.identity);
        return SavePrefab(root, $"{PrefabFolder}/FX");
    }

    // ------------------------------------------------------------------------------------------------ scene

    static void BuildScene(ZombieTruckSettings settings, Fx fx)
    {
        var scene = EditorSceneManager.OpenScene(ScenePath);
        foreach (var root in scene.GetRootGameObjects())
        {
            if (new[] { "QuantumDebugInput", "Environment", "Gameplay", "HUD", "Screen", "Display Camera" }.Contains(root.name)) Object.DestroyImmediate(root);
        }
        QuantumEntityViewUpdater viewUpdater = null;
        QuantumRunnerLocalDebug runner = null;
        QuantumMapData mapData = null;
        Camera camera = null;
        Light sun = null;
        foreach (var root in scene.GetRootGameObjects())
        {
            if (root.TryGetComponent(out QuantumEntityViewUpdater foundUpdater)) viewUpdater = foundUpdater;
            if (root.TryGetComponent(out QuantumRunnerLocalDebug foundRunner)) runner = foundRunner;
            if (root.TryGetComponent(out QuantumMapData foundMap)) mapData = foundMap;
            if (root.TryGetComponent(out Camera foundCamera)) camera = foundCamera;
            if (root.TryGetComponent(out Light foundLight)) sun = foundLight;
        }

        var environment = new GameObject("Environment").transform;
        var ground = Primitive(PrimitiveType.Cube, environment, "Ground Collider", new Vector3(0, -0.5f, 0), new Vector3(4000, 1, 4000), Material("Grass", new Color(0.2f, 0.14f, 0.32f)), true);
        ground.GetComponent<Renderer>().enabled = false;
        var groundCollider = ground.AddComponent<QuantumStaticBoxCollider3D>();
        groundCollider.SourceCollider = ground.GetComponent<BoxCollider>();
        Primitive(PrimitiveType.Cube, environment, "Ground", new Vector3(0, -0.1f, 0), new Vector3(4000, 0.1f, 4000), Material("Grass", new Color(0.2f, 0.14f, 0.32f)), false);
        sun.color = new Color(1f, 0.9f, 0.82f);
        sun.intensity = 1.3f;
        sun.transform.rotation = Quaternion.Euler(48, -35, 0);
        RenderSettings.ambientMode = UnityEngine.Rendering.AmbientMode.Flat;
        RenderSettings.ambientLight = new Color(0.42f, 0.36f, 0.6f);
        RenderSettings.fog = true;
        RenderSettings.fogColor = new Color(0.106f, 0.063f, 0.2f);
        RenderSettings.fogMode = FogMode.Linear;
        RenderSettings.fogStartDistance = 35;
        RenderSettings.fogEndDistance = 150;

        var gameplay = new GameObject("Gameplay").transform;
        var input = new GameObject("Survivor Input").AddComponent<SurvivorInput>();
        input.transform.SetParent(gameplay, false);
        // The game renders into a small point-filtered texture shown full screen through the dither shader.
        var lowRes = new RenderTexture(480, 270, 24) { filterMode = FilterMode.Point, name = "PS1 Screen" };
        lowRes = ReplaceAsset(lowRes, "Assets/Art/PS1 Screen.renderTexture");
        camera.targetTexture = lowRes;
        camera.nearClipPlane = 0.05f;
        camera.fieldOfView = 75;
        camera.clearFlags = CameraClearFlags.SolidColor;
        camera.backgroundColor = RenderSettings.fogColor;
        if (!camera.TryGetComponent(out FirstPersonCamera firstPerson)) firstPerson = camera.gameObject.AddComponent<FirstPersonCamera>();
        Set(firstPerson, ("viewUpdater", viewUpdater), ("input", input), ("eye", camera));
        foreach (Transform child in camera.transform) Object.DestroyImmediate(child.gameObject);
        BuildViewModel(camera, input);
        var display = new GameObject("Display Camera").AddComponent<Camera>();
        display.cullingMask = 1 << UiLayer;
        display.nearClipPlane = 0.1f;
        camera.cullingMask = ~(1 << UiLayer);
        display.clearFlags = CameraClearFlags.SolidColor;
        display.backgroundColor = Color.black;
        display.depth = -10;
        var screen = Canvas("Screen", 0, display, 1f);
        var image = new GameObject("PS1 Image", typeof(RectTransform), typeof(RawImage)).GetComponent<RawImage>();
        image.transform.SetParent(screen.transform, false);
        Stretch(image.rectTransform);
        image.texture = lowRes;
        var ditherMaterial = AssetDatabase.LoadAssetAtPath<Material>($"{MaterialFolder}/PS1 Dither.mat");
        if (ditherMaterial == null)
        {
            ditherMaterial = new Material(Shader.Find("ZombieTruck/PS1 Dither"));
            AssetDatabase.CreateAsset(ditherMaterial, $"{MaterialFolder}/PS1 Dither.mat");
        }
        image.material = ditherMaterial;
        image.raycastTarget = false;

        var hud = BuildHud(input, display);
        foreach (var child in screen.GetComponentsInChildren<Transform>(true).Concat(hud.GetComponentsInChildren<Transform>(true))) child.gameObject.layer = UiLayer;
        BuildCombatEffects(gameplay, fx, viewUpdater, firstPerson, hud);
        BuildAudio(gameplay, camera.transform, viewUpdater);

        runner.RuntimeConfig.Settings = settings;
        runner.MaxPlayerCount = 4;
        runner.LocalPlayers = new[] { new RuntimePlayer { PlayerNickname = "Player 1" } };
        EditorUtility.SetDirty(runner);

        QuantumMapDataBaker.BakeMapData(mapData, true);
        EditorUtility.SetDirty(mapData);
        EditorSceneManager.MarkSceneDirty(scene);
        EditorSceneManager.SaveScene(scene);
        SetUpOnlineMenu(runner.RuntimeConfig);
    }

    static void BuildCombatEffects(Transform gameplay, Fx fx, QuantumEntityViewUpdater viewUpdater, FirstPersonCamera firstPerson, GameHud hud)
    {
        var effects = new GameObject("Combat Effects").AddComponent<CombatEffects>();
        effects.transform.SetParent(gameplay, false);
        var tracer = new GameObject("Tracer").AddComponent<LineRenderer>();
        tracer.sharedMaterial = Material("Tracer", Color.white, "Universal Render Pipeline/Particles/Unlit", false);
        tracer.widthMultiplier = 0.04f;
        tracer.positionCount = 2;
        tracer.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
        var tracerPrefab = SavePrefab(tracer.gameObject, $"{PrefabFolder}/FX").GetComponent<LineRenderer>();
        var popup = new GameObject("Popup");
        var popupText = WorldText(popup.transform, "Text", Vector3.zero, 0.07f, "+$5");
        Set(popup.AddComponent<Popup>(), ("text", popupText));
        var popupPrefab = SavePrefab(popup, $"{PrefabFolder}/FX").GetComponent<Popup>();
        var flashes = new[]
        {
            (ItemKind.ScoopPistol, "Pistol Muzzle Flash", 1.5f), (ItemKind.SundaeShotgun, "Shotgun Muzzle Flash", 5f), (ItemKind.SprinkleSMG, "SMG Muzzle Flash", 0.8f),
            (ItemKind.LongSpoon, "Pistol Muzzle Flash", 6f), (ItemKind.ConeLauncher, "Shotgun Muzzle Flash", 4f), (ItemKind.BananaHarpoon, "Pistol Muzzle Flash", 2.5f),
            (ItemKind.None, "Minigun Muzzle Flash", 0.4f),
        };
        var serializedEffects = new SerializedObject(effects);
        var flashList = serializedEffects.FindProperty("muzzleFlashes");
        flashList.arraySize = flashes.Length;
        for (int i = 0; i < flashes.Length; i++)
        {
            var entry = flashList.GetArrayElementAtIndex(i);
            entry.FindPropertyRelative("Gun").enumValueIndex = (int)flashes[i].Item1;
            entry.FindPropertyRelative("Prefab").objectReferenceValue = ModelPrefab(flashes[i].Item2, "FX", flashes[i].Item2);
            entry.FindPropertyRelative("Kick").floatValue = flashes[i].Item3;
        }
        serializedEffects.ApplyModifiedPropertiesWithoutUndo();

        // Persistent world-space systems the effects emit into one particle at a time.
        var splats = AddLayer(fx, gameplay, "Ground Splats", new Layer { Count = 0, Loop = true, Duration = 1, Speed = Vector2.zero, Size = new Vector2(0.5f, 1f), Life = new Vector2(25, 25), Gravity = 0, Flat = true, Max = 800 });
        var casings = AddLayer(fx, gameplay, "Casings", new Layer { Row = FxRow.Sprinkle, Count = 0, Loop = true, Duration = 1, Life = new Vector2(1.5f, 1.5f), Gravity = 2, Collide = true, Max = 300 });
        var smoke = AddLayer(fx, gameplay, "Muzzle Smoke", new Layer { Row = FxRow.Smoke, Count = 0, Loop = true, Duration = 1, Life = new Vector2(0.6f, 0.6f), Gravity = -0.05f, Grow = 3, Max = 200 });
        Set(effects,
            ("viewUpdater", viewUpdater), ("cameraRig", firstPerson), ("hud", hud),
            ("tracerPrefab", tracerPrefab), ("hitBurst", fx.Hit), ("killBurst", fx.Kill), ("headshotBurst", fx.Headshot),
            ("shatterBurst", fx.IceShatter), ("explosionBursts", fx.Explosions.Cast<Object>().ToArray()), ("bloaterBurst", fx.Bloater),
            ("crashBurst", fx.Crash), ("confettiBurst", fx.Confetti), ("gibPrefabs", fx.Gibs.Cast<Object>().ToArray()),
            ("groundSplats", splats), ("casings", casings), ("smoke", smoke), ("popupPrefab", popupPrefab));
    }

    static void BuildAudio(Transform gameplay, Transform listener, QuantumEntityViewUpdater viewUpdater)
    {
        var oneShot = new GameObject("One Shot Sound").AddComponent<AudioSource>();
        oneShot.playOnAwake = false;
        oneShot.spatialBlend = 1;
        oneShot.minDistance = 3;
        oneShot.maxDistance = 70;
        oneShot.rolloffMode = AudioRolloffMode.Linear;
        oneShot.dopplerLevel = 0;
        var oneShotPrefab = SavePrefab(oneShot.gameObject, $"{PrefabFolder}/FX").GetComponent<AudioSource>();
        var audio = new GameObject("Game Audio").AddComponent<GameAudio>();
        audio.transform.SetParent(gameplay, false);
        var guns = new[]
        {
            (ItemKind.ScoopPistol, "gun_pistol"), (ItemKind.SundaeShotgun, "gun_shotgun"), (ItemKind.SprinkleSMG, "gun_smg"), (ItemKind.LongSpoon, "gun_sniper"),
            (ItemKind.ConeLauncher, "gun_launcher"), (ItemKind.BananaHarpoon, "gun_harpoon"), (ItemKind.None, "gun_minigun"),
        };
        var serialized = new SerializedObject(audio);
        var gunList = serialized.FindProperty("gunSounds");
        gunList.arraySize = guns.Length;
        for (int i = 0; i < guns.Length; i++)
        {
            gunList.GetArrayElementAtIndex(i).FindPropertyRelative("Gun").enumValueIndex = (int)guns[i].Item1;
            gunList.GetArrayElementAtIndex(i).FindPropertyRelative("Clip").objectReferenceValue = Clip(guns[i].Item2);
        }
        serialized.ApplyModifiedPropertiesWithoutUndo();
        Set(audio, ("oneShotPrefab", oneShotPrefab), ("listener", listener), ("viewUpdater", viewUpdater),
            ("hits", new Object[] { Clip("hit_1"), Clip("hit_2"), Clip("hit_3") }),
            ("headshot", Clip("headshot")), ("kill", Clip("kill")), ("explosion", Clip("explosion")), ("bloaterPop", Clip("bloater_pop")),
            ("freeze", Clip("freeze")), ("iceShatter", Clip("ice_shatter")), ("crash", Clip("crash")), ("hurt", Clip("hurt")), ("snarl", Clip("snarl")),
            ("death", Clip("death")), ("revive", Clip("revive")), ("wipe", Clip("wipe")), ("depot", Clip("depot")), ("bell", Clip("bell")),
            ("pickup", Clip("pickup")), ("kaching", Clip("kaching")), ("tip", Clip("tip")), ("crank", Clip("crank")), ("scoop", Clip("scoop")),
            ("reload", Clip("gun_reload")), ("empty", Clip("gun_empty")), ("thrown", Clip("throw")));
    }

    static AudioClip Clip(string name)
    {
        var path = $"{Audio}/{name}.wav";
        var clip = AssetDatabase.LoadAssetAtPath<AudioClip>(path);
        if (clip == null) throw new FileNotFoundException($"Missing sound {path} (run Art/Tools/zombie-styles/sfx_synth.py)");
        return clip;
    }

    // The Quantum sample menu (quick play, regions, party codes) starts online games of the gameplay scene.
    // Online play only needs an App ID in Assets/QuantumUser/Resources/PhotonServerSettings.asset.
    static void SetUpOnlineMenu(RuntimeConfig runtimeConfig)
    {
        var sceneInfo = AssetDatabase.LoadAssetAtPath<QuantumMenuSceneInfo>($"{ConfigFolder}/QuantumMapSceneInfo.asset");
        sceneInfo.Name = "Zombie Ice Cream Truck";
        sceneInfo.RuntimeConfig = runtimeConfig;
        EditorUtility.SetDirty(sceneInfo);
        var menuConfig = new SerializedObject(AssetDatabase.LoadAssetAtPath<Object>("Assets/Photon/QuantumMenu/QuantumMenuConfig.asset"));
        menuConfig.FindProperty("_maxPlayers").intValue = 4;
        menuConfig.ApplyModifiedPropertiesWithoutUndo();
        EditorBuildSettings.scenes = new[]
        {
            new EditorBuildSettingsScene("Assets/Photon/QuantumMenu/QuantumSampleMenu.unity", true),
            new EditorBuildSettingsScene(ScenePath, true),
        };
    }

    static void BuildViewModel(Camera camera, SurvivorInput input)
    {
        var root = new GameObject("View Model").transform;
        root.SetParent(camera.transform, false);
        var sway = new GameObject("Sway").transform;
        sway.SetParent(root, false);
        var recoil = new GameObject("Recoil").transform;
        recoil.SetParent(sway, false);
        // The arms sit a little lower and wider than their modelled pose so the guns read as held at the hip.
        var arms = Place(Model("Characters", "First-Person Arms"), recoil, Vector3.zero, Quaternion.identity);
        arms.transform.localPosition = -Child(arms, "First-Person Arms socket camera").localPosition + new Vector3(0.09f, -0.13f, 0.04f);
        var hand = Child(arms, "First-Person Arms socket hand R");
        var handPosition = recoil.InverseTransformPoint(hand.position);
        // Guns hang from the right hand by their grip, angled in toward the crosshair so their side stays readable.
        var aim = Quaternion.LookRotation(new Vector3(0, 0, 6) - handPosition);
        var held = new List<(ItemKind kind, Flavor flavor, GameObject model)>();
        var handItems = new (ItemKind kind, string category, string name, string grip)[]
        {
            (ItemKind.ScoopPistol, "Weapons", "Scoop Pistol", "socket grip"),
            (ItemKind.SundaeShotgun, "Weapons", "Sundae Shotgun", "socket grip"),
            (ItemKind.SprinkleSMG, "Weapons", "Sprinkle SMG", "socket grip"),
            (ItemKind.LongSpoon, "Weapons", "Long Spoon", "socket grip"),
            (ItemKind.ConeLauncher, "Weapons", "Cone Launcher", "socket grip"),
            (ItemKind.BananaHarpoon, "Weapons", "Banana Split Harpoon", "socket grip"),
            (ItemKind.Scooper, "Weapons", "Scooper", "socket hand"),
            (ItemKind.SprinkleJar, "Weapons", "Sprinkle Jar", "socket hand"),
            (ItemKind.SecondScoop, "Items", "Second Scoop", "socket hand"),
        };
        var flavoredItems = new (ItemKind kind, string pattern)[] { (ItemKind.Pint, "Pint {0} Full"), (ItemKind.Scoop, "Scoop Grenade {0}") };
        var handModels = handItems.Select(i => (i.kind, Flavor.None, i.category, i.name, i.grip)).ToList();
        foreach (var item in flavoredItems)
        {
            for (int f = 0; f < Flavors.Length; f++) handModels.Add((item.kind, (Flavor)(f + 1), "Items", string.Format(item.pattern, Flavors[f]), "socket hand"));
        }
        foreach (var item in handModels)
        {
            GameObject model;
            if (item.grip == "socket grip")
            {
                model = Place(Model(item.category, item.name), recoil, Vector3.zero, aim);
                model.transform.localPosition = handPosition - aim * Child(model, $"{item.name} socket grip").localPosition;
            }
            else
            {
                model = Place(Model(item.category, item.name), hand, Vector3.zero, Quaternion.identity);
                var grip = model.GetComponentsInChildren<Transform>(true).FirstOrDefault(t => t.name == $"{item.name} {item.grip}");
                if (grip != null) model.transform.localPosition = -grip.localPosition;
            }
            foreach (var renderer in model.GetComponentsInChildren<Renderer>()) renderer.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            held.Add((item.kind, item.Item2, model));
        }
        var bulky = new List<(ItemKind kind, Flavor flavor, string name)>
        {
            (ItemKind.MilkCrate, Flavor.None, "Milk Crate"), (ItemKind.SugarSack, Flavor.None, "Sugar Sack"), (ItemKind.CocoaBag, Flavor.None, "Cocoa Bag"),
            (ItemKind.StrawberryBasket, Flavor.None, "Strawberry Basket"), (ItemKind.MintBundle, Flavor.None, "Mint Bundle"),
        };
        for (int f = 0; f < Flavors.Length; f++) bulky.Add((ItemKind.Tub, (Flavor)(f + 1), $"Flavor Tub {Flavors[f]}"));
        foreach (var item in bulky)
        {
            var model = Place(Model("Items", item.name), recoil, new Vector3(0, -0.55f, 0.75f), Quaternion.identity);
            model.transform.localScale = Vector3.one * 0.85f;
            held.Add((item.kind, item.flavor, model));
        }
        var viewModel = root.gameObject.AddComponent<ViewModel>();
        var serialized = new SerializedObject(viewModel);
        serialized.FindProperty("input").objectReferenceValue = input;
        serialized.FindProperty("arms").objectReferenceValue = recoil.gameObject;
        serialized.FindProperty("recoilPivot").objectReferenceValue = recoil;
        serialized.FindProperty("sway").objectReferenceValue = sway;
        serialized.FindProperty("aimOffset").vector3Value = new Vector3(-0.22f, -0.045f, -0.06f);
        var models = serialized.FindProperty("models");
        models.arraySize = held.Count;
        for (int i = 0; i < held.Count; i++)
        {
            held[i].model.SetActive(false);
            models.GetArrayElementAtIndex(i).FindPropertyRelative("Kind").enumValueIndex = (int)held[i].kind;
            models.GetArrayElementAtIndex(i).FindPropertyRelative("Flavor").enumValueIndex = (int)held[i].flavor;
            models.GetArrayElementAtIndex(i).FindPropertyRelative("Model").objectReferenceValue = held[i].model;
        }
        serialized.ApplyModifiedPropertiesWithoutUndo();
    }

    static GameHud BuildHud(SurvivorInput input, Camera display)
    {
        var canvas = Canvas("HUD", 10, display, 0.5f);
        var font = Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");
        var splats = new Object[6];
        for (int i = 0; i < splats.Length; i++)
        {
            var splat = HudImage(canvas.transform, $"Screen Splat {i + 1}", $"screen_splat_{i % 4 + 1}", new Vector2(0.5f, 0.5f), new Vector2(300, 300));
            splat.color = Color.clear;
            splats[i] = splat;
        }
        var vignette = HudImage(canvas.transform, "Low Health Vignette", "vignette", new Vector2(0.5f, 0.5f), Vector2.zero);
        Stretch(vignette.rectTransform);
        vignette.color = Color.clear;
        var hurt = new GameObject("Hurt Flash", typeof(RectTransform), typeof(Image)).GetComponent<Image>();
        hurt.transform.SetParent(canvas.transform, false);
        Stretch(hurt.rectTransform);
        hurt.color = Color.clear;
        hurt.raycastTarget = false;
        var hitMarker = HudImage(canvas.transform, "Hit Marker", "hitmarker", new Vector2(0.5f, 0.5f), new Vector2(40, 40));
        hitMarker.color = Color.clear;
        var money = HudText(canvas.transform, "Money", font, new Vector2(0, 1), new Vector2(24, -18), TextAnchor.UpperLeft, 34, new Color(1f, 0.88f, 0.29f));
        var kills = HudText(canvas.transform, "Kills", font, new Vector2(0, 1), new Vector2(24, -60), TextAnchor.UpperLeft, 22, Color.white);
        var area = HudText(canvas.transform, "Area", font, new Vector2(1, 1), new Vector2(-24, -18), TextAnchor.UpperRight, 26, new Color(0.7f, 0.55f, 1f));
        var speed = HudText(canvas.transform, "Speed", font, new Vector2(1, 0), new Vector2(-24, 120), TextAnchor.LowerRight, 28, new Color(0.22f, 0.95f, 0.76f));
        var ammo = HudText(canvas.transform, "Ammo", font, new Vector2(1, 0), new Vector2(-24, 84), TextAnchor.LowerRight, 26, Color.white);
        var carried = HudText(canvas.transform, "Carried", font, new Vector2(0.5f, 0), new Vector2(0, 150), TextAnchor.LowerCenter, 20, new Color(1f, 0.88f, 0.29f));
        var prompt = HudText(canvas.transform, "Prompt", font, new Vector2(0.5f, 0.5f), new Vector2(0, -70), TextAnchor.UpperCenter, 20, Color.white);
        var phase = HudText(canvas.transform, "Phase", font, new Vector2(0.5f, 1), new Vector2(0, -70), TextAnchor.UpperCenter, 28, new Color(1f, 0.31f, 0.64f));
        HudText(canvas.transform, "Crosshair", font, new Vector2(0.5f, 0.5f), Vector2.zero, TextAnchor.MiddleCenter, 26, Color.white).text = "+";
        HudText(canvas.transform, "Controls", font, new Vector2(0, 0), new Vector2(24, 18), TextAnchor.LowerLeft, 14, new Color(1, 1, 1, 0.6f)).text =
            "WASD move  SHIFT sprint  SPACE jump  CLICK use/shoot  R reload  E interact  Q drop (hold to throw)  1-6 / wheel hotbar";

        var healthBack = new GameObject("Health", typeof(RectTransform), typeof(Image)).GetComponent<Image>();
        healthBack.transform.SetParent(canvas.transform, false);
        healthBack.rectTransform.anchorMin = healthBack.rectTransform.anchorMax = healthBack.rectTransform.pivot = new Vector2(0, 0);
        healthBack.rectTransform.anchoredPosition = new Vector2(24, 50);
        healthBack.rectTransform.sizeDelta = new Vector2(260, 18);
        healthBack.color = new Color(0.1f, 0.06f, 0.2f, 0.8f);
        var fill = new GameObject("Fill", typeof(RectTransform), typeof(Image)).GetComponent<Image>();
        fill.transform.SetParent(healthBack.transform, false);
        Stretch(fill.rectTransform);
        fill.sprite = AssetDatabase.GetBuiltinExtraResource<Sprite>("UI/Skin/UISprite.psd");
        fill.type = Image.Type.Filled;
        fill.fillMethod = Image.FillMethod.Horizontal;
        fill.color = new Color(1f, 0.31f, 0.64f);

        var slotTexts = new Object[6];
        var slotFrames = new Object[6];
        for (int i = 0; i < 6; i++)
        {
            var frame = new GameObject($"Slot {i + 1}", typeof(RectTransform), typeof(Image)).GetComponent<Image>();
            frame.transform.SetParent(canvas.transform, false);
            frame.rectTransform.anchorMin = frame.rectTransform.anchorMax = frame.rectTransform.pivot = new Vector2(0.5f, 0);
            frame.rectTransform.anchoredPosition = new Vector2((i - 2.5f) * 128, 20);
            frame.rectTransform.sizeDelta = new Vector2(120, 64);
            frame.raycastTarget = false;
            var text = HudText(frame.transform, "Label", font, new Vector2(0.5f, 0.5f), Vector2.zero, TextAnchor.MiddleCenter, 13, Color.white);
            text.rectTransform.sizeDelta = new Vector2(116, 60);
            slotTexts[i] = text;
            slotFrames[i] = frame;
        }
        var hud = canvas.gameObject.AddComponent<GameHud>();
        Set(hud,
            ("input", input), ("moneyText", money), ("killsText", kills), ("speedText", speed), ("areaText", area), ("ammoText", ammo),
            ("carriedText", carried), ("promptText", prompt), ("phaseText", phase), ("healthFill", fill), ("hurtFlash", hurt),
            ("slotTexts", slotTexts), ("slotFrames", slotFrames), ("hitMarker", hitMarker), ("screenSplats", splats), ("vignette", vignette));
        return hud;
    }

    static Image HudImage(Transform parent, string name, string sprite, Vector2 anchor, Vector2 size)
    {
        var image = new GameObject(name, typeof(RectTransform), typeof(Image)).GetComponent<Image>();
        image.transform.SetParent(parent, false);
        image.rectTransform.anchorMin = image.rectTransform.anchorMax = image.rectTransform.pivot = anchor;
        image.rectTransform.sizeDelta = size;
        image.sprite = AssetDatabase.LoadAssetAtPath<Sprite>($"{Sprites}/{sprite}.png");
        image.raycastTarget = false;
        return image;
    }

    // ------------------------------------------------------------------------------------------------ helpers

    static GameObject Model(string category, string name)
    {
        var path = $"{Art}/{category}/{name}.fbx";
        var model = AssetDatabase.LoadAssetAtPath<GameObject>(path);
        if (model == null) throw new FileNotFoundException($"Missing PS1 model {path}");
        return model;
    }

    static GameObject Place(GameObject model, Transform parent, Vector3 position, Quaternion rotation)
    {
        var instance = (GameObject)PrefabUtility.InstantiatePrefab(model, parent);
        instance.transform.localPosition = position;
        instance.transform.localRotation = rotation;
        return instance;
    }

    static Transform Child(GameObject root, string name)
    {
        var child = root.GetComponentsInChildren<Transform>(true).FirstOrDefault(t => t.name == name);
        if (child == null) throw new InvalidOperationException($"{root.name} has no child named '{name}'");
        return child;
    }

    static Transform Socket(GameObject truck, string socket)
    {
        return Child(truck, $"{Truck} {socket}");
    }

    // Combined renderer bounds in the space of the given root (optionally destroying the root afterwards).
    static Bounds LocalBounds(Transform root, bool destroy = false)
    {
        var bounds = new Bounds();
        var first = true;
        foreach (var filter in root.GetComponentsInChildren<MeshFilter>(true))
        {
            var mesh = filter.sharedMesh.bounds;
            for (int corner = 0; corner < 8; corner++)
            {
                var local = mesh.center + Vector3.Scale(mesh.extents, new Vector3((corner & 1) != 0 ? 1 : -1, (corner & 2) != 0 ? 1 : -1, (corner & 4) != 0 ? 1 : -1));
                var point = root.InverseTransformPoint(filter.transform.TransformPoint(local));
                if (first) bounds = new Bounds(point, Vector3.zero);
                else bounds.Encapsulate(point);
                first = false;
            }
        }
        if (destroy) Object.DestroyImmediate(root.gameObject);
        return bounds;
    }

    static Vector3 Abs(Vector3 v)
    {
        return new Vector3(Mathf.Abs(v.x), Mathf.Abs(v.y), Mathf.Abs(v.z));
    }

    static GameObject EntityRoot(string name)
    {
        var root = new GameObject(name);
        root.AddComponent<QuantumEntityPrototype>().TransformMode = QuantumEntityPrototypeTransformMode.Transform3D;
        root.AddComponent<QuantumEntityView>();
        return root;
    }

    static GameObject SavePrefab(GameObject root, string folder = PrefabFolder)
    {
        Directory.CreateDirectory(folder);
        var path = $"{folder}/{root.name}.prefab";
        var prefab = PrefabUtility.SaveAsPrefabAsset(root, path);
        Object.DestroyImmediate(root);
        if (prefab.GetComponent<QuantumEntityPrototype>() != null)
        {
            QuantumAssetObjectPostprocessor.TryCreateOrUpdatePrototypeAssetForPrefab(path, out var prototypePath);
            AssetDatabase.ImportAsset(prototypePath, ImportAssetOptions.ForceSynchronousImport);
        }
        return prefab;
    }

    static AssetRef<EntityPrototype> PrototypeFor(GameObject prefab)
    {
        var path = QuantumEntityPrototypeAssetObjectImporter.GetPathForPrefab(AssetDatabase.GetAssetPath(prefab));
        return AssetDatabase.LoadAssetAtPath<EntityPrototype>(path);
    }

    static T ReplaceAsset<T>(T asset, string path) where T : Object
    {
        var existing = AssetDatabase.LoadAssetAtPath<T>(path);
        if (existing == null)
        {
            AssetDatabase.CreateAsset(asset, path);
            AssetDatabase.ImportAsset(path, ImportAssetOptions.ForceSynchronousImport);
            return AssetDatabase.LoadAssetAtPath<T>(path);
        }
        // Keep the existing asset and copy the new values into it. CopySerialized would also copy the new instance's
        // empty Quantum identifier, so the existing one is put back to keep references to it valid.
        var identifier = existing is AssetObject quantumAsset ? quantumAsset.Identifier : default;
        EditorUtility.CopySerialized(asset, existing);
        if (existing is AssetObject restored) restored.Identifier = identifier;
        EditorUtility.SetDirty(existing);
        return existing;
    }

    static Material Material(string name, Color color, string shader = "Universal Render Pipeline/Lit", bool transparent = false)
    {
        var path = $"{MaterialFolder}/{name}.mat";
        var material = AssetDatabase.LoadAssetAtPath<Material>(path);
        if (material == null)
        {
            material = new Material(Shader.Find(shader));
            AssetDatabase.CreateAsset(material, path);
        }
        material.SetColor("_BaseColor", color);
        if (transparent)
        {
            material.SetFloat("_Surface", 1);
            material.SetFloat("_Blend", 0);
            material.SetOverrideTag("RenderType", "Transparent");
            material.renderQueue = (int)UnityEngine.Rendering.RenderQueue.Transparent;
            material.SetInt("_SrcBlend", (int)UnityEngine.Rendering.BlendMode.SrcAlpha);
            material.SetInt("_DstBlend", (int)UnityEngine.Rendering.BlendMode.OneMinusSrcAlpha);
            material.SetInt("_ZWrite", 0);
            material.EnableKeyword("_SURFACE_TYPE_TRANSPARENT");
        }
        EditorUtility.SetDirty(material);
        return material;
    }

    static GameObject Primitive(PrimitiveType type, Transform parent, string name, Vector3 position, Vector3 size, Material material, bool keepCollider)
    {
        var go = GameObject.CreatePrimitive(type);
        go.name = name;
        if (!keepCollider) Object.DestroyImmediate(go.GetComponent<Collider>());
        go.transform.SetParent(parent, false);
        go.transform.localPosition = position;
        go.transform.localScale = size;
        go.GetComponent<Renderer>().sharedMaterial = material;
        return go;
    }

    static TextMesh WorldText(Transform parent, string name, Vector3 position, float size, string text)
    {
        var go = new GameObject(name);
        go.transform.SetParent(parent, false);
        go.transform.localPosition = position;
        var mesh = go.AddComponent<TextMesh>();
        mesh.text = text;
        mesh.characterSize = size;
        mesh.fontSize = 48;
        mesh.anchor = TextAnchor.MiddleCenter;
        mesh.alignment = TextAlignment.Center;
        mesh.fontStyle = FontStyle.Bold;
        mesh.font = Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");
        go.GetComponent<MeshRenderer>().sharedMaterial = mesh.font.material;
        return mesh;
    }

    // Screen-space canvases drawn by the display camera on the UI layer, so a camera render captures the whole frame.
    static Canvas Canvas(string name, int order, Camera display, float distance)
    {
        var go = new GameObject(name, typeof(Canvas), typeof(CanvasScaler));
        var canvas = go.GetComponent<Canvas>();
        canvas.renderMode = RenderMode.ScreenSpaceCamera;
        canvas.worldCamera = display;
        canvas.planeDistance = distance;
        canvas.sortingOrder = order;
        var scaler = go.GetComponent<CanvasScaler>();
        scaler.uiScaleMode = CanvasScaler.ScaleMode.ScaleWithScreenSize;
        scaler.referenceResolution = new Vector2(1280, 720);
        return canvas;
    }

    static void Stretch(RectTransform rect)
    {
        rect.anchorMin = Vector2.zero;
        rect.anchorMax = Vector2.one;
        rect.offsetMin = rect.offsetMax = Vector2.zero;
    }

    static Text HudText(Transform parent, string name, Font font, Vector2 anchor, Vector2 position, TextAnchor alignment, int size, Color color)
    {
        var rect = new GameObject(name, typeof(RectTransform), typeof(Text), typeof(Outline)).GetComponent<RectTransform>();
        rect.SetParent(parent, false);
        rect.anchorMin = rect.anchorMax = rect.pivot = anchor;
        rect.anchoredPosition = position;
        rect.sizeDelta = new Vector2(900, 80);
        var text = rect.GetComponent<Text>();
        text.font = font;
        text.fontSize = size;
        text.fontStyle = FontStyle.Bold;
        text.alignment = alignment;
        text.color = color;
        text.raycastTarget = false;
        rect.GetComponent<Outline>().effectColor = new Color(0.1f, 0.06f, 0.2f);
        return text;
    }

    static void Set(Object target, params (string field, object value)[] values)
    {
        var serialized = new SerializedObject(target);
        foreach (var (field, value) in values)
        {
            var property = serialized.FindProperty(field);
            switch (value)
            {
                case Object[] array:
                    property.arraySize = array.Length;
                    for (int i = 0; i < array.Length; i++) property.GetArrayElementAtIndex(i).objectReferenceValue = array[i];
                    break;
                case float number: property.floatValue = number; break;
                case bool flag: property.boolValue = flag; break;
                case Vector3 vector: property.vector3Value = vector; break;
                default: property.objectReferenceValue = (Object)value; break;
            }
        }
        serialized.ApplyModifiedPropertiesWithoutUndo();
    }
}
