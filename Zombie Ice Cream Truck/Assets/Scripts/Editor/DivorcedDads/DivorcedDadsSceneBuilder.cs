using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using Photon.Deterministic;
using Quantum;
using Quantum.Editor;
using UnityEditor;
using UnityEngine;
using Object = UnityEngine.Object;

// Builds the Divorced Dads mode from the PS1 art: entity prefabs, effect prefabs, the settings asset, the town and the
// scene (Assets/QuantumUser/Scenes/DivorcedDads.unity). Run from Tools > Divorced Dads > Build Scene, or headless with
// -executeMethod DivorcedDadsSceneBuilder.Build. Everything it creates is a normal editable asset; rerunning rebuilds it.
// Pivots and sockets are looked up by name here, at edit time only; runtime code gets serialized references.
public static partial class DivorcedDadsSceneBuilder
{
    const string Art = "Assets/Art/PS1";
    const string Characters = "Dads Characters";
    const string Items = "Dads Items";
    const string Town = "Dads Town";
    const string Audio = "Assets/Audio";
    const string PrefabFolder = "Assets/Prefabs/Dads";
    const string FxFolder = "Assets/Prefabs/Dads/FX";
    const string MaterialFolder = "Assets/Materials";
    const string ConfigFolder = "Assets/QuantumUser/Resources";
    const string ScenePath = "Assets/QuantumUser/Scenes/DivorcedDads.unity";
    const string ZombieScenePath = "Assets/QuantumUser/Scenes/QuantumGameScene.unity";
    const string Truck = "Ice Cream Truck";
    const int UiLayer = 5;

    static readonly string[] DadColors = { "Pink", "Blue", "Mint", "Yellow" };
    static readonly string[] KidLooks = { "Kid Stripes", "Kid Overalls", "Kid Hoodie", "Kid Dress" };
    // Indexed by Treat (None first).
    static readonly string[] Treats = { null, "Mud", "Strawberry", "Coffee", "Rocky Road", "Gold Leaf" };
    static readonly string[] Cones = { "Cone", "Waffle Cone", "Double Waffle Cone" };
    // The roof minigun stands on a platform this tall, scaled up from the weapon art.
    const float TurretRise = 0.8f;
    const float TurretScale = 1.5f;

    // The truck art drives on the right; this is America, so the Dads van mirrors the driving position to the left.
    static readonly string[] DriverSide = { "driver seat", "steering wheel", "steering column", "instruments", "pedal brake", "pedal gas" };
    // Truck art the Dads van does without: the zombie mode's stock (fixtures bring their own), the freezer's sliding glass
    // lids, the back door (it swings as a fixture of its own) and the roof hatch lid (the hatch is always open).
    static readonly string[] TruckDecor = { "freezer lid a", "freezer lid b", "rear door", "hatch lid", "freezer tub 1", "freezer tub 2", "freezer tub 3", "counter pint 1", "counter pint 3", "counter scoop", "counter tub", "churn tub", "rack pistol", "rack shotgun", "plow" };

    // Hand-measured from the truck art (h_truck.py layout), same as the zombie mode: floor top 0.75, ceiling 2.86,
    // roof 2.92, walls at x +-1.15, cab front z 2.35, bulkhead z 0.95 (1 m doorway), rear wall z -2.95 (0.9 m door),
    // serving window on -X.
    static readonly Vector3[] TruckBoxes =
    {
        new Vector3(0, 0.65f, -0.3f), new Vector3(1.15f, 0.1f, 2.65f),
        new Vector3(0, 0.3f, 0.2f), new Vector3(1f, 0.25f, 3.1f),
        new Vector3(0, 0.95f, 2.85f), new Vector3(1.1f, 0.5f, 0.5f),
        new Vector3(1.12f, 1.805f, -0.3f), new Vector3(0.03f, 1.055f, 2.65f),
        new Vector3(-1.12f, 1.805f, -2.225f), new Vector3(0.03f, 1.055f, 0.725f),
        new Vector3(-1.12f, 1.235f, -0.8f), new Vector3(0.03f, 0.485f, 0.7f),
        new Vector3(-1.12f, 2.705f, -0.8f), new Vector3(0.03f, 0.155f, 0.7f),
        new Vector3(-1.12f, 1.805f, 1.125f), new Vector3(0.03f, 1.055f, 1.225f),
        new Vector3(0, 1.805f, 2.32f), new Vector3(1.15f, 1.055f, 0.03f),
        new Vector3(-0.795f, 1.805f, 0.95f), new Vector3(0.295f, 1.055f, 0.025f),
        new Vector3(0.795f, 1.805f, 0.95f), new Vector3(0.295f, 1.055f, 0.025f),
        new Vector3(0, 2.68f, 0.95f), new Vector3(0.5f, 0.18f, 0.025f),
        new Vector3(-0.8f, 1.805f, -2.92f), new Vector3(0.35f, 1.055f, 0.03f),
        new Vector3(0.8f, 1.805f, -2.92f), new Vector3(0.35f, 1.055f, 0.03f),
        new Vector3(0, 2.755f, -2.92f), new Vector3(0.45f, 0.105f, 0.03f),
        new Vector3(0, 2.89f, 0.115f), new Vector3(1.15f, 0.03f, 2.235f),
        new Vector3(0, 2.89f, -2.835f), new Vector3(1.15f, 0.03f, 0.115f),
        new Vector3(-0.35f, 2.89f, -2.42f), new Vector3(0.8f, 0.03f, 0.3f),
        new Vector3(1.09f, 2.89f, -2.42f), new Vector3(0.06f, 0.03f, 0.3f),
        new Vector3(-1.12f, 3.2f, -0.3f), new Vector3(0.03f, 0.3f, 2.65f),
        new Vector3(1.12f, 3.2f, -0.3f), new Vector3(0.03f, 0.3f, 2.65f),
        new Vector3(0, 3.2f, 2.32f), new Vector3(1.15f, 0.3f, 0.03f),
        new Vector3(0, 3.2f, -2.92f), new Vector3(1.15f, 0.3f, 0.03f),
        // The rear step under the back door, solid down to the chassis bottom so nobody slips under it: dads step up onto
        // it, then into the kitchen.
        new Vector3(0, 0.2475f, -3.2f), new Vector3(0.475f, 0.1975f, 0.15f),
    };

    static readonly (Upgrade upgrade, int price)[] ShopStock =
    {
        (Upgrade.ScoopPistol, 30), (Upgrade.WaffleCone, 40), (Upgrade.MapleGrovePermit, 60), (Upgrade.Loudspeaker, 60),
        (Upgrade.DoubleWaffle, 90), (Upgrade.SundaeShotgun, 120), (Upgrade.HillsidePermit, 150), (Upgrade.Minigun, 200),
    };

    [MenuItem("Tools/Divorced Dads/Build Scene")]
    public static void Build()
    {
        Directory.CreateDirectory(PrefabFolder);
        Directory.CreateDirectory(FxFolder);
        // Opening the scene unloads unsaved in-memory assets, so it comes before anything is created.
        var scene = OpenScene();
        PlayerSettings.allowUnsafeCode = true;
        var truckModel = Model("Truck", Truck);
        ConfigureSprites();
        var fx = BuildEffects();

        var van = BuildVan(truckModel);
        var dads = DadColors.Select(c => BuildDad(c, fx)).ToArray();
        var npcs = new GameObject[Enum.GetValues(typeof(NpcKind)).Length];
        npcs[(int)NpcKind.Kid] = BuildNpc("Kid Stripes", false);
        npcs[(int)NpcKind.FatKid] = BuildNpc("Fat Kid", false);
        npcs[(int)NpcKind.LactoseKid] = BuildNpc("Lactose Kid", false);
        npcs[(int)NpcKind.DiabeticKid] = BuildNpc("Diabetic Kid", false);
        npcs[(int)NpcKind.RichKid] = BuildNpc("Rich Kid", false);
        npcs[(int)NpcKind.Cop] = BuildNpc("Cop", true);
        var looks = KidLooks.Select(k => k == "Kid Stripes" ? npcs[(int)NpcKind.Kid] : BuildNpc(k, false)).ToArray();
        var fixtures = BuildFixtures(truckModel);
        var loot = BuildLoot();
        var cash = BuildCash();
        var glob = BuildGlob();
        var gas = BuildGas(fx);
        // The simulation finds entity prototypes through the Quantum asset DB, which only lists new ones after a refresh.
        QuantumUnityDBUtilities.RefreshGlobalDB(true);

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
        controller = ReplaceAsset(controller, $"{ConfigFolder}/DadController.asset");

        var settings = ScriptableObject.CreateInstance<DadsSettings>();
        settings.VanPrototype = PrototypeFor(van);
        settings.DadPrototypes = dads.Select(PrototypeFor).ToArray();
        settings.NpcPrototypes = npcs.Select(PrototypeFor).ToArray();
        settings.KidLooks = looks.Select(PrototypeFor).ToArray();
        settings.FixturePrototypes = fixtures.Select(PrototypeFor).ToArray();
        settings.LootPrototypes = loot.Select(p => p == null ? default : PrototypeFor(p)).ToArray();
        settings.CashPrototype = PrototypeFor(cash);
        settings.GlobPrototype = PrototypeFor(glob);
        settings.GasPrototype = PrototypeFor(gas);
        settings.DadController = controller;
        FillVanLayout(settings, truckModel);
        settings.Npcs = new NpcStats[Enum.GetValues(typeof(NpcKind)).Length];
        settings.Npcs[(int)NpcKind.Kid] = Stats(3, 1.6f, 3.6f, 1.2f, 0.3f);
        settings.Npcs[(int)NpcKind.FatKid] = Stats(24, 1.3f, 4.2f, 1.6f, 0.55f);
        settings.Npcs[(int)NpcKind.LactoseKid] = Stats(3, 1.6f, 3.6f, 1.2f, 0.3f);
        settings.Npcs[(int)NpcKind.DiabeticKid] = Stats(3, 1.6f, 3.6f, 1.2f, 0.3f);
        settings.Npcs[(int)NpcKind.RichKid] = Stats(4, 1.5f, 3.4f, 1.25f, 0.3f);
        settings.Npcs[(int)NpcKind.Cop] = Stats(2, 2.2f, 4.6f, 1.85f, 0.35f);

        var town = BuildTown(settings);
        settings = ReplaceAsset(settings, $"{ConfigFolder}/DadsSettings.asset");
        BuildScene(scene, settings, fx, town);
        AssetDatabase.SaveAssets();
        Debug.Log("DivorcedDadsSceneBuilder: built the Divorced Dads scene");
    }

    static NpcStats Stats(int hunger, float walk, float run, float height, float radius)
    {
        return new NpcStats
        {
            Hunger = hunger, WalkSpeed = FP.FromFloat_UNSAFE(walk), RunSpeed = FP.FromFloat_UNSAFE(run),
            Height = FP.FromFloat_UNSAFE(height), Radius = FP.FromFloat_UNSAFE(radius),
        };
    }

    // ------------------------------------------------------------------------------------------------ entity prefabs

    static GameObject BuildVan(GameObject truckModel)
    {
        var root = EntityRoot("Van");
        var model = Place(truckModel, root.transform, Vector3.zero, Quaternion.identity);
        foreach (var decor in TruckDecor) Child(model, $"{Truck} {decor}").gameObject.SetActive(false);
        // The churn's hopper is an open funnel modeled single-sided: draw both faces so its inside shows from above.
        var hopper = Child(model, $"{Truck} churn hopper").GetComponent<Renderer>();
        var twoSided = new Material(hopper.sharedMaterial) { name = "Dads Churn Hopper" };
        twoSided.SetFloat("_Cull", (float)UnityEngine.Rendering.CullMode.Off);
        hopper.sharedMaterial = ReplaceAsset(twoSided, $"{MaterialFolder}/Dads Churn Hopper.mat");
        foreach (var name in DriverSide)
        {
            var part = Child(model, $"{Truck} {name}");
            var center = part.parent.InverseTransformPoint(part.TransformPoint(LocalBounds(part).center));
            part.localPosition -= new Vector3(2 * center.x, 0, 0);
        }
        // The minigun, bigger, on a raised platform with a deck the gunner stands on behind it.
        var platform = new GameObject("Turret Platform").transform;
        platform.SetParent(model.transform, false);
        platform.position = Child(model, $"{Truck} socket turret").position;
        Primitive(PrimitiveType.Cylinder, platform, "Post", new Vector3(0, TurretRise / 2, 0), new Vector3(0.45f, TurretRise / 2, 0.45f), Material("Dads Pedestal", new Color(1f, 0.31f, 0.64f)), false);
        Primitive(PrimitiveType.Cylinder, platform, "Deck", new Vector3(0, TurretRise - 0.04f, -0.2f), new Vector3(1.8f, 0.04f, 1.8f), Material("Dads Turret Deck", new Color(0.22f, 0.95f, 0.76f)), false);
        var minigun = Place(Model("Weapons", "Soft Serve Minigun"), platform, new Vector3(0, TurretRise, 0), Quaternion.identity);
        minigun.transform.localScale = Vector3.one * TurretScale;
        var speaker = Place(Model(Items, "Loudspeaker"), model.transform, Child(model, $"{Truck} socket upgrade turret2").position + new Vector3(0.3f, 0, 0.4f), Quaternion.identity);
        var lights = new List<Object>();
        foreach (var side in new[] { -0.75f, 0.75f })
        {
            var beam = new GameObject($"Headlight {side}").AddComponent<Light>();
            beam.transform.SetParent(model.transform, false);
            beam.transform.localPosition = new Vector3(side, 1.1f, 3.3f);
            beam.transform.localRotation = Quaternion.Euler(12, 0, 0);
            beam.type = LightType.Spot;
            beam.range = 22;
            beam.spotAngle = 60;
            beam.intensity = 6;
            beam.color = new Color(1f, 0.93f, 0.75f);
            beam.gameObject.SetActive(false);
            lights.Add(beam.gameObject);
        }
        Set(root.AddComponent<VanView>(),
            ("body", model.transform),
            ("wheels", new[] { "wheel front +X", "wheel front -X", "wheel rear +X", "wheel rear -X" }.Select(n => (Object)Child(model, $"{Truck} {n}")).ToArray()),
            ("steeringPivots", new[] { "wheel front +X steer", "wheel front -X steer" }.Select(n => (Object)Child(model, $"{Truck} {n}")).ToArray()),
            ("steeringWheel", Child(model, $"{Truck} steering wheel")),
            ("churnCrank", Child(model, $"{Truck} churn crank")),
            ("gaugeNeedle", Child(model, $"{Truck} gauge needle")),
            ("bellMallet", Child(model, $"{Truck} bell mallet")),
            ("loudspeaker", speaker), ("minigun", platform.gameObject), ("minigunYaw", Child(minigun, "Soft Serve Minigun yaw")),
            ("minigunPitch", Child(minigun, "Soft Serve Minigun pitch")), ("minigunBarrels", Child(minigun, "Soft Serve Minigun barrels")),
            ("headlights", lights.ToArray()),
            ("engineSound", Loop(root.transform, "Engine", "engine_loop", 4, 60, 0.6f, true)),
            ("music", Loop(root.transform, "Jingle", "music_entertainer", 8, 70, 0.5f, false)),
            ("exhaust", Emitter(root.transform, "Exhaust", new Vector3(0.8f, 0.35f, -3.05f), new Vector3(0, 0.3f, -1),
                new Layer { Row = FxRow.Smoke, Speed = new Vector2(1, 2), Size = new Vector2(0.25f, 0.4f), Life = new Vector2(1f, 1.6f), Gravity = -0.06f, Grow = 3, Color = new Color(0.55f, 0.52f, 0.6f), Cone = 15 })),
            ("hoodSmoke", Emitter(root.transform, "Hood Smoke", new Vector3(0, 1.3f, 3.0f), new Vector3(0, 1, 0.3f),
                new Layer { Row = FxRow.Smoke, Speed = new Vector2(0.8f, 1.6f), Size = new Vector2(0.35f, 0.6f), Life = new Vector2(1.2f, 2f), Gravity = -0.08f, Grow = 3, Color = new Color(0.32f, 0.3f, 0.38f), Cone = 20 })),
            ("wheelDust", new[] { -1, 1 }.Select(side => (Object)Emitter(root.transform, $"Wheel Dust {side}", new Vector3(side * 1f, 0.1f, -2.2f), new Vector3(0, 0.4f, -1),
                new Layer { Row = FxRow.Smoke, Speed = new Vector2(0.5f, 1.5f), Size = new Vector2(0.4f, 0.8f), Life = new Vector2(0.6f, 1f), Gravity = -0.02f, Grow = 2, Color = new Color(0.75f, 0.62f, 0.5f), Cone = 30 })).ToArray()));
        return SavePrefab(root);
    }

    static AudioSource Loop(Transform parent, string name, string clip, float minDistance, float maxDistance, float volume, bool playOnAwake)
    {
        var source = new GameObject(name).AddComponent<AudioSource>();
        source.transform.SetParent(parent, false);
        source.clip = Clip(clip);
        source.loop = true;
        source.playOnAwake = playOnAwake;
        source.spatialBlend = 1;
        source.minDistance = minDistance;
        source.maxDistance = maxDistance;
        source.rolloffMode = AudioRolloffMode.Linear;
        source.dopplerLevel = 0;
        source.volume = volume;
        return source;
    }

    // A continuously emitting effect whose rate a view drives; it starts at zero.
    static ParticleSystem Emitter(Transform parent, string name, Vector3 position, Vector3 direction, Layer layer)
    {
        layer.Count = 0;
        layer.Loop = true;
        layer.Duration = 1;
        layer.Radius = Mathf.Max(layer.Radius, 0.05f);
        var particles = AddLayer(parent, name, layer);
        particles.transform.localPosition = position;
        particles.transform.localRotation = Quaternion.LookRotation(direction);
        return particles;
    }

    static GameObject BuildDad(string color, Fx fx)
    {
        var name = $"Dad {color}";
        var root = EntityRoot(name);
        var pivot = new GameObject("Model").transform;
        pivot.SetParent(root.transform, false);
        var body = Place(Model(Characters, name), pivot, Vector3.zero, Quaternion.identity);
        Set(body.AddComponent<WalkCycle>(),
            ("legs", new Object[] { Child(body, $"{name} leg L"), Child(body, $"{name} leg R") }),
            ("arms", new Object[] { Child(body, $"{name} arm L") }));
        var hand = Child(body, $"{name} socket hand R");
        var chest = new GameObject("Chest").transform;
        chest.SetParent(body.transform, false);
        chest.localPosition = new Vector3(0, 1.05f, 0.35f);
        var held = HeldRig(hand, chest, Quaternion.identity, 1f);
        var head = Child(body, $"{name} head pivot");
        var cough = Emitter(head, "Cough", new Vector3(0, 0.15f, 0.15f), Vector3.forward,
            new Layer { Row = FxRow.Smoke, Speed = new Vector2(0.6f, 1.4f), Size = new Vector2(0.15f, 0.3f), Life = new Vector2(0.6f, 1f), Gravity = -0.05f, Grow = 2.5f, Color = new Color(0.6f, 0.85f, 0.3f), Cone = 25 });
        var frost = Primitive(PrimitiveType.Cube, head, "Frost", new Vector3(0, 0.15f, 0), new Vector3(0.38f, 0.42f, 0.38f), Material("Dads Ice", new Color(0.6f, 0.95f, 1f, 0.5f), "Universal Render Pipeline/Unlit", true), false);
        frost.SetActive(false);
        var cuffs = Primitive(PrimitiveType.Cube, hand, "Cuffs", Vector3.zero, new Vector3(0.12f, 0.06f, 0.06f), Material("Dads Steel", new Color(0.75f, 0.75f, 0.85f)), false);
        cuffs.SetActive(false);
        Set(root.AddComponent<DadView>(), ("model", pivot), ("held", held), ("cough", cough), ("frost", frost), ("cuffs", cuffs));
        return SavePrefab(root);
    }

    // Every holdable model at the hand (cones with their scoop stacks, guns) and the bulky ingredients: in front of the
    // chest, or (first person, handCarry set) upright in the right hand, gripped at the item's right-hand socket so the
    // visible hand is holding them.
    static HeldItems HeldRig(Transform hand, Transform chest, Quaternion gunAim, float bulkyScale, Quaternion? handCarry = null)
    {
        var rig = new GameObject("Held").transform;
        rig.SetParent(hand, false);
        var held = rig.gameObject.AddComponent<HeldItems>();
        var items = new List<(DadItem kind, GameObject model)>();
        foreach (var (kind, gun) in new[] { (DadItem.ScoopPistol, "Scoop Pistol"), (DadItem.SundaeShotgun, "Sundae Shotgun") })
        {
            var model = Place(Model("Weapons", gun), rig, Vector3.zero, gunAim);
            model.transform.localPosition = -(gunAim * Child(model, $"{gun} socket grip").localPosition);
            items.Add((kind, model));
        }
        foreach (var (kind, bulky) in new[] { (DadItem.MudBucket, "Mud Bucket"), (DadItem.StrawberryBasket, "Strawberry Basket"), (DadItem.IcedCoffee, "Iced Coffee"), (DadItem.NutSack, "Nut Sack"), (DadItem.GoldLeaf, "Gold Leaf") })
        {
            var category = kind == DadItem.StrawberryBasket ? "Items" : Items;
            var model = Place(Model(category, bulky), handCarry.HasValue ? rig : chest, Vector3.zero, handCarry ?? Quaternion.identity);
            model.transform.localScale = Vector3.one * bulkyScale;
            model.transform.localPosition = handCarry.HasValue
                ? -(handCarry.Value * Child(model, $"{bulky} socket hand R").localPosition * bulkyScale)
                : Vector3.down * 0.15f * bulkyScale;
            items.Add((kind, model));
        }
        var serialized = new SerializedObject(held);
        var itemList = serialized.FindProperty("items");
        itemList.arraySize = items.Count;
        for (int i = 0; i < items.Count; i++)
        {
            items[i].model.SetActive(false);
            itemList.GetArrayElementAtIndex(i).FindPropertyRelative("Kind").enumValueIndex = (int)items[i].kind;
            itemList.GetArrayElementAtIndex(i).FindPropertyRelative("Model").objectReferenceValue = items[i].model;
        }
        var coneList = serialized.FindProperty("cones");
        coneList.arraySize = Cones.Length;
        for (int c = 0; c < Cones.Length; c++)
        {
            var cone = Place(Model(Items, Cones[c]), rig, Vector3.zero, Quaternion.identity);
            cone.transform.localPosition = -Child(cone, $"{Cones[c]} socket hand").localPosition;
            cone.SetActive(false);
            var entry = coneList.GetArrayElementAtIndex(c);
            entry.FindPropertyRelative("Root").objectReferenceValue = cone;
            var slots = entry.FindPropertyRelative("Slots");
            slots.arraySize = 3;
            for (int s = 0; s < 3; s++)
            {
                var socket = Child(cone, $"{Cones[c]} socket scoop {s + 1}");
                var scoops = slots.GetArrayElementAtIndex(s).FindPropertyRelative("Scoops");
                scoops.arraySize = Treats.Length;
                for (int t = 1; t < Treats.Length; t++)
                {
                    var scoop = Place(Model(Items, $"Scoop {Treats[t]}"), socket, Vector3.zero, Quaternion.identity);
                    scoop.SetActive(false);
                    scoops.GetArrayElementAtIndex(t).objectReferenceValue = scoop;
                }
            }
        }
        serialized.ApplyModifiedPropertiesWithoutUndo();
        foreach (var renderer in rig.GetComponentsInChildren<Renderer>(true).Concat(chest.GetComponentsInChildren<Renderer>(true))) renderer.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
        return held;
    }

    static GameObject BuildNpc(string name, bool cop)
    {
        var root = EntityRoot(name);
        var pivot = new GameObject("Model").transform;
        pivot.SetParent(root.transform, false);
        var body = Place(Model(Characters, name), pivot, Vector3.zero, Quaternion.identity);
        Set(body.AddComponent<WalkCycle>(),
            ("legs", new Object[] { Child(body, $"{name} leg L"), Child(body, $"{name} leg R") }),
            ("arms", new Object[] { Child(body, $"{name} arm L") }),
            ("strideLength", name == "Fat Kid" ? 0.6f : 0.75f));

        var anchor = new GameObject("Bubble").transform;
        anchor.SetParent(Child(body, $"{name} socket bubble"), false);
        var bubbleModel = Place(Model(Items, "Thought Bubble"), anchor, Vector3.zero, Quaternion.Euler(0, 180, 0));
        var icon = Child(bubbleModel, "Thought Bubble socket icon");
        var bubbleScoops = new Object[Treats.Length];
        for (int t = 1; t < Treats.Length; t++)
        {
            var scoop = Place(Model(Items, $"Scoop {Treats[t]}"), icon, new Vector3(0, -0.1f, 0), Quaternion.identity);
            scoop.transform.localScale = Vector3.one * 2.6f;
            scoop.SetActive(false);
            bubbleScoops[t] = scoop;
        }
        anchor.gameObject.SetActive(false);

        var mouth = cop ? Child(body, $"{name} head pivot") : Child(body, $"{name} socket mouth");
        var cream = Primitive(PrimitiveType.Sphere, mouth, "Face Cream", cop ? new Vector3(0, 0.12f, 0.12f) : new Vector3(0, -0.01f, 0.03f),
            new Vector3(0.16f, 0.1f, 0.08f), Material("Dads Cream", Color.white), false);
        cream.SetActive(false);
        var hand = Child(body, $"{name} socket hand R");
        var treatCones = new Object[Treats.Length];
        for (int t = 1; t < Treats.Length; t++)
        {
            var cone = Place(Model(Items, "Cone"), hand, Vector3.zero, Quaternion.identity);
            cone.transform.localPosition = -Child(cone, "Cone socket hand").localPosition;
            Place(Model(Items, $"Scoop {Treats[t]}"), Child(cone, "Cone socket scoop 1"), Vector3.zero, Quaternion.identity);
            cone.SetActive(false);
            treatCones[t] = cone;
        }
        Set(root.AddComponent<NpcView>(), ("model", pivot), ("bubble", anchor.gameObject), ("bubbleScoops", bubbleScoops),
            ("faceCream", cream.GetComponent<Renderer>()), ("treatCones", treatCones));
        if (cop)
        {
            var hat = Child(body, $"{name} head pivot");
            var red = Primitive(PrimitiveType.Cube, hat, "Siren Red", new Vector3(-0.06f, 0.36f, 0), Vector3.one * 0.07f, Material("Dads Siren Red", new Color(1f, 0.15f, 0.2f), "Universal Render Pipeline/Unlit"), false);
            var blue = Primitive(PrimitiveType.Cube, hat, "Siren Blue", new Vector3(0.06f, 0.36f, 0), Vector3.one * 0.07f, Material("Dads Siren Blue", new Color(0.2f, 0.4f, 1f), "Universal Render Pipeline/Unlit"), false);
            red.SetActive(false);
            blue.SetActive(false);
            Set(root.AddComponent<CopLight>(), ("red", red), ("blue", blue));
        }
        return SavePrefab(root);
    }

    // One prefab per FixtureKind. Kitchen fixtures are drawn by the truck model itself; their views only show contents.
    static GameObject[] BuildFixtures(GameObject truckModel)
    {
        var prefabs = new GameObject[Enum.GetValues(typeof(FixtureKind)).Length];
        var truck = (GameObject)PrefabUtility.InstantiatePrefab(truckModel);
        foreach (var kind in new[] { FixtureKind.Churn, FixtureKind.ConeCounter, FixtureKind.Hopper, FixtureKind.Bell, FixtureKind.Turret })
        {
            prefabs[(int)kind] = BuildFixture(kind, null);
        }
        prefabs[(int)FixtureKind.CoffeeTable] = BuildFixture(FixtureKind.CoffeeTable, root =>
        {
            var cups = Place(Model(Items, "Iced Coffee"), root.transform, Vector3.zero, Quaternion.identity);
            Set(root.AddComponent<RestockView>(), ("stock", cups));
        });
        prefabs[(int)FixtureKind.Tub] = BuildFixture(FixtureKind.Tub, root =>
        {
            var tubs = new Object[Treats.Length];
            var view = root.AddComponent<TubView>();
            var serialized = new SerializedObject(view);
            var fills = serialized.FindProperty("fills");
            fills.arraySize = Treats.Length;
            for (int t = 1; t < Treats.Length; t++)
            {
                var name = $"Flavor Tub {Treats[t]}";
                var tub = Place(Model(Items, name), root.transform, new Vector3(0, -0.02f, 0), Quaternion.Euler(0, 90, 0));
                tub.transform.localScale = Vector3.one * 0.85f;
                tub.SetActive(false);
                tubs[t] = tub;
                // The surface pieces of the art (h_dads_items.build_tub): the ice cream dome, the swirl and the toppings.
                var surface = new[] { $"{name} ice cream", $"{name} swirl", $"{name} top" };
                var parts = tub.GetComponentsInChildren<Transform>(true)
                    .Where(c => surface.Any(c.name.StartsWith) && !surface.Any(c.parent.name.StartsWith)).ToArray();
                var list = fills.GetArrayElementAtIndex(t).FindPropertyRelative("Parts");
                list.arraySize = parts.Length;
                for (int i = 0; i < parts.Length; i++) list.GetArrayElementAtIndex(i).objectReferenceValue = parts[i];
            }
            serialized.ApplyModifiedPropertiesWithoutUndo();
            Set(view, ("tubs", tubs));
        });
        prefabs[(int)FixtureKind.GunRack] = BuildFixture(FixtureKind.GunRack, root =>
        {
            var pivot = Child(truck, $"{Truck} station gun rack");
            var view = root.AddComponent<RackView>();
            var serialized = new SerializedObject(view);
            var slots = serialized.FindProperty("slots");
            slots.arraySize = 4;
            for (int s = 0; s < 4; s++)
            {
                var socket = Child(truck, $"{Truck} socket gun {s + 1} gun rack");
                var anchor = new GameObject($"Slot {s + 1}").transform;
                anchor.SetParent(root.transform, false);
                anchor.localPosition = Quaternion.Inverse(pivot.rotation) * (socket.position - pivot.position);
                anchor.localRotation = Quaternion.Inverse(pivot.rotation) * socket.rotation;
                var pistol = Place(Model("Weapons", "Scoop Pistol"), anchor, Vector3.zero, Quaternion.identity);
                var shotgun = Place(Model("Weapons", "Sundae Shotgun"), anchor, Vector3.zero, Quaternion.identity);
                pistol.SetActive(false);
                shotgun.SetActive(false);
                slots.GetArrayElementAtIndex(s).FindPropertyRelative("Pistol").objectReferenceValue = pistol;
                slots.GetArrayElementAtIndex(s).FindPropertyRelative("Shotgun").objectReferenceValue = shotgun;
            }
            serialized.ApplyModifiedPropertiesWithoutUndo();
        });
        prefabs[(int)FixtureKind.Shop] = BuildFixture(FixtureKind.Shop, root =>
        {
            Primitive(PrimitiveType.Cylinder, root.transform, "Pedestal", new Vector3(0, 0.45f, 0), new Vector3(0.6f, 0.45f, 0.6f), Material("Dads Pedestal", new Color(1f, 0.31f, 0.64f)), false);
            // What each pedestal sells, about half a meter across, turning above it. Permits show the gate they open.
            var display = new GameObject("Display").transform;
            display.SetParent(root.transform, false);
            display.localPosition = new Vector3(0, 1.2f, 0);
            var models = new (Upgrade upgrade, string category, string name)[]
            {
                (Upgrade.ScoopPistol, "Weapons", "Scoop Pistol"), (Upgrade.SundaeShotgun, "Weapons", "Sundae Shotgun"),
                (Upgrade.Minigun, "Weapons", "Soft Serve Minigun"), (Upgrade.WaffleCone, Items, "Waffle Cone"),
                (Upgrade.DoubleWaffle, Items, "Double Waffle Cone"), (Upgrade.Loudspeaker, Items, "Loudspeaker"),
                (Upgrade.MapleGrovePermit, Items, "Gate"), (Upgrade.HillsidePermit, Items, "Gate"),
            };
            var items = new Object[Enum.GetValues(typeof(Upgrade)).Length];
            foreach (var (upgrade, category, name) in models)
            {
                var item = Place(Model(category, name), display, Vector3.zero, Quaternion.identity);
                var bounds = LocalBounds(item.transform);
                var scale = 0.5f / Mathf.Max(bounds.size.x, bounds.size.y, bounds.size.z);
                item.transform.localScale = Vector3.one * scale;
                item.transform.localPosition = -bounds.center * scale;
                item.SetActive(false);
                items[(int)upgrade] = item;
            }
            var label = WorldText(root.transform, "Price Tag", new Vector3(0, 1.9f, 0), 0.06f, "UPGRADE\n$0");
            Primitive(PrimitiveType.Quad, label.transform, "Backing", new Vector3(0, 0, 0.02f), new Vector3(2.4f, 0.95f, 1), Material("Dads Label Backing", new Color(0.1f, 0.06f, 0.2f, 0.85f), "Universal Render Pipeline/Unlit", true), false);
            Set(root.AddComponent<ShopTag>(), ("text", label), ("display", display), ("items", items));
        });
        prefabs[(int)FixtureKind.Collector] = BuildFixture(FixtureKind.Collector, root =>
        {
            var pivot = new GameObject("Model").transform;
            pivot.SetParent(root.transform, false);
            Place(Model(Characters, "Big Dairy"), pivot, Vector3.zero, Quaternion.identity);
            var speech = WorldText(root.transform, "Speech", new Vector3(0, 2.6f, 0), 0.05f, "You got my money?");
            Set(root.AddComponent<CollectorView>(), ("model", pivot), ("speech", speech));
        });
        prefabs[(int)FixtureKind.TimeClock] = BuildFixture(FixtureKind.TimeClock, root =>
        {
            Primitive(PrimitiveType.Cube, root.transform, "Post", new Vector3(0, 0.6f, 0), new Vector3(0.12f, 1.2f, 0.12f), Material("Dads Steel", new Color(0.75f, 0.75f, 0.85f)), false);
            Primitive(PrimitiveType.Cube, root.transform, "Clock", new Vector3(0, 1.35f, 0), new Vector3(0.45f, 0.55f, 0.25f), Material("Dads Clock", new Color(1f, 0.88f, 0.29f)), false);
            Primitive(PrimitiveType.Cube, root.transform, "Card Slot", new Vector3(0, 1.45f, 0.13f), new Vector3(0.3f, 0.05f, 0.02f), Material("Dads Ink", new Color(0.1f, 0.06f, 0.2f)), false);
            var label = WorldText(root.transform, "Label", new Vector3(0, 2.1f, 0), 0.05f, "CLOCK OUT");
            Set(root.AddComponent<TimeClockView>(), ("label", label));
        });
        prefabs[(int)FixtureKind.MudPuddle] = BuildFixture(FixtureKind.MudPuddle, root => Place(Model(Items, "Mud Puddle"), root.transform, Vector3.zero, Quaternion.identity));
        prefabs[(int)FixtureKind.StrawberryPatch] = BuildFixture(FixtureKind.StrawberryPatch, root =>
        {
            var patch = Place(Model(Items, "Strawberry Patch"), root.transform, Vector3.zero, Quaternion.identity);
            Set(root.AddComponent<RestockView>(), ("stock", Child(patch, "Strawberry Patch berries").gameObject));
        });
        prefabs[(int)FixtureKind.NutTree] = BuildFixture(FixtureKind.NutTree, root =>
        {
            var tree = Place(Model(Items, "Nut Tree"), root.transform, Vector3.zero, Quaternion.identity);
            Set(root.AddComponent<TreeView>(), ("canopy", Child(tree, "Nut Tree canopy")));
        });
        prefabs[(int)FixtureKind.Vault] = BuildFixture(FixtureKind.Vault, root =>
        {
            var vault = Place(Model(Items, "Vault"), root.transform, Vector3.zero, Quaternion.identity);
            Set(root.AddComponent<HingeView>(), ("part", Child(vault, "Vault door")), ("openEuler", new Vector3(0, -105, 0)), ("speed", 2.5f));
        });
        prefabs[(int)FixtureKind.Plate] = BuildFixture(FixtureKind.Plate, root =>
        {
            var plate = Place(Model(Items, "Pressure Plate"), root.transform, Vector3.zero, Quaternion.identity);
            Set(root.AddComponent<HingeView>(), ("part", Child(plate, "Pressure Plate plate")), ("openOffset", new Vector3(0, -0.06f, 0)), ("speed", 12f));
        });
        prefabs[(int)FixtureKind.Gate] = BuildFixture(FixtureKind.Gate, root =>
        {
            var gate = Place(Model(Items, "Gate"), root.transform, Vector3.zero, Quaternion.identity);
            Set(root.AddComponent<HingeView>(), ("part", Child(gate, "Gate arm")), ("openEuler", new Vector3(0, 0, -80)), ("speed", 2f));
        });
        prefabs[(int)FixtureKind.LampPost] = BuildFixture(FixtureKind.LampPost, root =>
        {
            var pole = new GameObject("Pole").transform;
            pole.SetParent(root.transform, false);
            var model = Place(Model("Road", "Street Lamp"), pole, Vector3.zero, Quaternion.identity);
            Set(root.AddComponent<LampView>(), ("pole", pole), ("lamp", StreetLight(Child(model, "Street Lamp socket light"))));
        });
        prefabs[(int)FixtureKind.RearDoor] = BuildFixture(FixtureKind.RearDoor, root =>
        {
            // The truck art's back door, hinge at the fixture's origin, swinging out when opened.
            var copy = Object.Instantiate(truckModel);
            var door = Child(copy, $"{Truck} rear door");
            door.SetParent(root.transform, false);
            door.localPosition = Vector3.zero;
            Object.DestroyImmediate(copy);
            Set(root.AddComponent<HingeView>(), ("part", door), ("openEuler", new Vector3(0, -100, 0)), ("speed", 6f));
        });
        Object.DestroyImmediate(truck);
        return prefabs;
    }

    static GameObject BuildFixture(FixtureKind kind, Action<GameObject> dress)
    {
        var root = EntityRoot($"Fixture {kind}");
        dress?.Invoke(root);
        return SavePrefab(root);
    }

    // One pickup prefab per DadItem.
    static GameObject[] BuildLoot()
    {
        var prefabs = new GameObject[Enum.GetValues(typeof(DadItem)).Length];
        var models = new Dictionary<DadItem, (string category, string name)>
        {
            [DadItem.Cone] = (Items, "Cone"),
            [DadItem.ScoopPistol] = ("Weapons", "Scoop Pistol"),
            [DadItem.SundaeShotgun] = ("Weapons", "Sundae Shotgun"),
            [DadItem.MudBucket] = (Items, "Mud Bucket"),
            [DadItem.StrawberryBasket] = ("Items", "Strawberry Basket"),
            [DadItem.IcedCoffee] = (Items, "Iced Coffee"),
            [DadItem.NutSack] = (Items, "Nut Sack"),
            [DadItem.GoldLeaf] = (Items, "Gold Leaf"),
        };
        foreach (var pair in models)
        {
            var root = EntityRoot($"Loot {pair.Key}");
            var model = Place(Model(pair.Value.category, pair.Value.name), root.transform, Vector3.zero, Quaternion.identity);
            if (pair.Key == DadItem.Cone) model.transform.localScale = Vector3.one * 2;
            model.transform.localPosition = Vector3.up * -LocalBounds(model.transform).min.y * model.transform.localScale.y;
            prefabs[(int)pair.Key] = SavePrefab(root);
        }
        return prefabs;
    }

    static GameObject BuildCash()
    {
        var root = EntityRoot("Cash");
        var pivot = new GameObject("Model").transform;
        pivot.SetParent(root.transform, false);
        var money = Place(Model(Items, "Lunch Money"), pivot, Vector3.zero, Quaternion.identity);
        money.transform.localScale = Vector3.one * 2.2f;
        Set(root.AddComponent<CashView>(), ("model", pivot));
        return SavePrefab(root);
    }

    static GameObject BuildGlob()
    {
        var root = EntityRoot("Glob");
        var variants = new Object[Treats.Length];
        for (int t = 1; t < Treats.Length; t++)
        {
            var scoop = Place(Model(Items, $"Scoop {Treats[t]}"), root.transform, Vector3.zero, Quaternion.identity);
            scoop.transform.localScale = Vector3.one * 2.2f;
            scoop.transform.localPosition = -LocalBounds(scoop.transform).center * 2.2f;
            scoop.SetActive(t == 1);
            variants[t] = scoop;
        }
        Set(root.AddComponent<TreatVariants>(), ("variants", variants));
        return SavePrefab(root);
    }

    static GameObject BuildGas(Fx fx)
    {
        var root = EntityRoot("Gas");
        var puffs = AddLayer(root.transform, "Puffs", new Layer
        {
            Row = FxRow.Smoke, Count = 25, Rate = 40, Loop = true, Duration = 1, Speed = new Vector2(0.2f, 0.8f), Size = new Vector2(1.2f, 2.2f),
            Life = new Vector2(1.5f, 2.5f), Gravity = -0.02f, Grow = 1.6f, Color = new Color(0.55f, 0.8f, 0.25f, 1f), Radius = 3f, Max = 300,
        });
        Set(root.AddComponent<GasView>(), ("puffs", puffs), ("hiss", Loop(root.transform, "Hiss", "Dads/gas_hiss_loop", 2, 20, 0.5f, false)));
        return SavePrefab(root);
    }

    // ------------------------------------------------------------------------------------------------ settings data

    static void FillVanLayout(DadsSettings settings, GameObject truckModel)
    {
        var truck = (GameObject)PrefabUtility.InstantiatePrefab(truckModel);
        var boxes = TruckBoxes.ToList();
        var bins = Child(truck, $"{Truck} station ingredient bins");
        var binBounds = LocalBounds(Place(Model("Truck", "Ingredient Bins"), null, Vector3.zero, Quaternion.identity).transform, true);
        boxes.Add(bins.position + bins.rotation * binBounds.center);
        var binExtents = bins.rotation * binBounds.extents;
        boxes.Add(new Vector3(Mathf.Abs(binExtents.x), Mathf.Abs(binExtents.y), Mathf.Abs(binExtents.z)));
        settings.VanColliders = new DadsBox[boxes.Count / 2];
        for (int i = 0; i < settings.VanColliders.Length; i++)
        {
            settings.VanColliders[i] = new DadsBox { Center = boxes[i * 2].ToFPVector3(), Extents = boxes[i * 2 + 1].ToFPVector3() };
        }
        settings.VanHalfSize = new Vector3(1.3f, 0, 3.2f).ToFPVector3();
        settings.RoofHeight = FP.FromFloat_UNSAFE(2.92f);
        settings.DriverSeat = new Vector3(-0.55f, 0.47f, 1.4f).ToFPVector3();
        settings.CabStand = new Vector3(0f, 0.8f, 1.5f).ToFPVector3();
        // Under the middle of the roof hatch, on the kitchen floor.
        settings.Ladder = new Vector3(0.72f, 0.75f, -2.42f).ToFPVector3();
        settings.HatchTop = new Vector3(0.74f, 2.95f, -1.8f).ToFPVector3();
        settings.RearInside = new Vector3(0, 0.8f, -2.5f).ToFPVector3();
        settings.RearOutside = new Vector3(0, 0.05f, -3.6f).ToFPVector3();
        var window = Child(truck, $"{Truck} socket serving window").position;
        // Far enough out that a kid's face shows over the counter from inside.
        settings.WindowOutside = new Vector3(window.x - 2.2f, 0, window.z).ToFPVector3();

        var turretSocket = Child(truck, $"{Truck} socket turret").position;
        var minigun = Place(Model("Weapons", "Soft Serve Minigun"), null, Vector3.zero, Quaternion.identity);
        var pitchPivot = Child(minigun, "Soft Serve Minigun pitch").position * TurretScale;
        var muzzle = Child(minigun, "Soft Serve Minigun socket muzzle").position * TurretScale;
        var turretBounds = LocalBounds(minigun.transform, true);
        var gunBase = turretSocket + Vector3.up * TurretRise;
        settings.TurretBase = gunBase.ToFPVector3();
        settings.TurretPivot = (gunBase + pitchPivot).ToFPVector3();
        settings.TurretGunner = new Vector3(0, 0, -0.8f).ToFPVector3();
        // Over the gun's right shoulder, clear of its hopper, looking along its barrels.
        settings.TurretEye = new Vector3(0.55f, 0.85f, -1.5f).ToFPVector3();
        settings.TurretMuzzle = (muzzle - pitchPivot).ToFPVector3();
        // Platform and gun in one box (E target from the roof, and what dads bump into up there).
        var turretTop = TurretRise + turretBounds.max.y * TurretScale;
        var turretCenter = new Vector3(0, turretTop / 2, turretBounds.center.z * TurretScale);
        var turretHalf = new Vector3(Mathf.Max(0.5f, turretBounds.extents.x * TurretScale), turretTop / 2, turretBounds.extents.z * TurretScale);

        var placements = new List<FixturePlacement>
        {
            VanFixture(truck, FixtureKind.Churn, "churn", "Churn"),
            VanFixture(truck, FixtureKind.ConeCounter, "scoop counter", "Scoop Counter"),
            VanFixture(truck, FixtureKind.GunRack, "gun rack", "Gun Rack"),
            VanFixture(truck, FixtureKind.Hopper, "hopper gauge", "Hopper Gauge"),
            VanFixture(truck, FixtureKind.Bell, "roof bell", "Roof Bell"),
            // Hinged at the art's pivot, filling the 0.9 x 1.85 m doorway toward -X.
            new FixturePlacement
            {
                Kind = FixtureKind.RearDoor, Position = Child(truck, $"{Truck} rear door").position.ToFPVector3(),
                Center = new Vector3(-0.45f, 0.925f, 0).ToFPVector3(), HalfSize = new Vector3(0.45f, 0.925f, 0.04f).ToFPVector3(),
            },
            new FixturePlacement { Kind = FixtureKind.Turret, Position = turretSocket.ToFPVector3(), Center = turretCenter.ToFPVector3(), HalfSize = turretHalf.ToFPVector3() },
        };
        // Four tubs in the freezer rack; their boxes are as deep as the rack so they also stop dads walking into it.
        for (int i = 0; i < 4; i++)
        {
            var slot = Child(truck, $"{Truck} socket slot {i + 1} freezer rack").position;
            placements.Add(new FixturePlacement
            {
                Kind = FixtureKind.Tub, Index = i, Position = new Vector3(slot.x, slot.y, slot.z).ToFPVector3(),
                Center = new Vector3(0, -0.3f, 0).ToFPVector3(), HalfSize = new Vector3(0.26f, 0.42f, 0.14f).ToFPVector3(),
            });
        }
        settings.VanFixtures = placements.ToArray();
        Object.DestroyImmediate(bins.root.gameObject);
    }

    static FixturePlacement VanFixture(GameObject truck, FixtureKind kind, string pivotName, string model)
    {
        var pivot = Child(truck, $"{Truck} station {pivotName}");
        var instance = Place(Model("Truck", model), null, Vector3.zero, Quaternion.identity);
        var bounds = LocalBounds(instance.transform, true);
        return new FixturePlacement
        {
            Kind = kind,
            Position = pivot.position.ToFPVector3(),
            Yaw = FP.FromFloat_UNSAFE(pivot.rotation.eulerAngles.y),
            Center = bounds.center.ToFPVector3(),
            HalfSize = bounds.extents.ToFPVector3(),
        };
    }
}
