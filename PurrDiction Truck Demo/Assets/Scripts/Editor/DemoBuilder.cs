using System.Collections.Generic;
using System.IO;
using PurrNet;
using PurrNet.Prediction;
using PurrNet.Transports;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

// Builds the whole throwaway demo (materials, prefabs, scene, PurrNet setup) and the Linux
// player. Batch: Unity -batchmode -projectPath . -executeMethod DemoBuilder.BuildAll -quit
public static class DemoBuilder
{
    const string ScenePath = "Assets/Scenes/Demo.unity";
    const string NetPrefabFolder = "Assets/Prefabs/Network";
    const string PredictedPrefabFolder = "Assets/Prefabs/Predicted";
    static readonly Dictionary<string, Material> materials = new Dictionary<string, Material>();

    [MenuItem("Tools/Truck Demo/Build Scene")]
    public static void BuildScene()
    {
        Directory.CreateDirectory("Assets/Materials");
        Directory.CreateDirectory("Assets/Scenes");
        Directory.CreateDirectory(NetPrefabFolder);
        Directory.CreateDirectory(PredictedPrefabFolder);
        Directory.CreateDirectory("Assets/Prefabs/Local");
        AssetDatabase.Refresh();
        materials.Clear();

        GameObject playerPrefab = BuildPlayerPrefab();
        BuildProjectilePrefab();
        NetworkPrefabs prefabs = AssetDatabase.LoadAssetAtPath<NetworkPrefabs>("Assets/Prefabs/NetworkPrefabs.asset");
        if (prefabs == null)
        {
            prefabs = ScriptableObject.CreateInstance<NetworkPrefabs>();
            AssetDatabase.CreateAsset(prefabs, "Assets/Prefabs/NetworkPrefabs.asset");
        }
        prefabs.folder = AssetDatabase.LoadAssetAtPath<DefaultAsset>(NetPrefabFolder);
        prefabs.Generate();
        EditorUtility.SetDirty(prefabs);
        PredictedPrefabs predictedPrefabs = AssetDatabase.LoadAssetAtPath<PredictedPrefabs>("Assets/Prefabs/PredictedPrefabs.asset");
        if (predictedPrefabs == null)
        {
            predictedPrefabs = ScriptableObject.CreateInstance<PredictedPrefabs>();
            AssetDatabase.CreateAsset(predictedPrefabs, "Assets/Prefabs/PredictedPrefabs.asset");
        }
        predictedPrefabs.folder = AssetDatabase.LoadAssetAtPath<DefaultAsset>(PredictedPrefabFolder);
        predictedPrefabs.Generate();
        EditorUtility.SetDirty(predictedPrefabs);

        var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);

        var lightGo = new GameObject("Sun");
        Light light = lightGo.AddComponent<Light>();
        light.type = LightType.Directional;
        light.intensity = 1.1f;
        light.shadows = LightShadows.Soft;
        lightGo.transform.rotation = Quaternion.Euler(50f, -30f, 0f);
        RenderSettings.ambientLight = new Color(0.55f, 0.58f, 0.65f);

        var camGo = new GameObject("Main Camera");
        camGo.tag = "MainCamera";
        Camera cam = camGo.AddComponent<Camera>();
        cam.nearClipPlane = 0.05f;
        cam.farClipPlane = 600f;
        cam.clearFlags = CameraClearFlags.SolidColor;
        cam.backgroundColor = new Color(0.55f, 0.75f, 0.95f);
        camGo.transform.position = new Vector3(0f, 40f, -60f);
        camGo.transform.rotation = Quaternion.Euler(30f, 0f, 0f);

        BuildTown();
        Transform interior = BuildInterior();
        Truck truck = BuildTruck(out Rigidbody truckBody);

        var npcRoot = new GameObject("NPCs");
        var npcList = new List<Npc>();
        for (int i = 0; i < 20; i++)
        {
            bool cop = i >= 16;
            Color shirt = cop ? new Color(0.1f, 0.15f, 0.45f) : Color.HSVToRGB(i * 0.13f % 1f, 0.6f, 0.95f);
            GameObject go = BuildHumanoid((cop ? "Cop " : "Kid ") + i, cop ? 1.15f : 0.8f, shirt, true);
            go.transform.SetParent(npcRoot.transform);
            go.transform.position = new Vector3(i * 1.5f, 0f, -200f);
            Npc npc = go.AddComponent<Npc>();
            Set(npc, "body", go.GetComponent<Humanoid>());
            SetBool(npc, "isCop", cop);
            npcList.Add(npc);
        }
        var npcManagerGo = new GameObject("NpcManager");
        NpcManager npcManager = npcManagerGo.AddComponent<NpcManager>();
        SetArray(npcManager, "npcs", npcList.ToArray());

        var netGo = new GameObject("Network");
        NetworkManager nm = netGo.AddComponent<NetworkManager>();
        UDPTransport udp = netGo.GetComponent<UDPTransport>();
        if (udp == null)
        {
            udp = netGo.AddComponent<UDPTransport>();
        }
        var nmSo = new SerializedObject(nm);
        nmSo.FindProperty("_networkRules").objectReferenceValue = AssetDatabase.LoadAssetAtPath<NetworkRules>("Packages/dev.purrnet.purrnet/Defaults/NetworkRules/ServerOwner.asset");
        nmSo.FindProperty("_networkPrefabs").objectReferenceValue = prefabs;
        nmSo.FindProperty("_transport").objectReferenceValue = udp;
        // PurrDiction simulates at the network tick rate.
        nmSo.FindProperty("_tickRate").intValue = 60;
        nmSo.FindProperty("_startServerFlags").intValue = 0;
        nmSo.FindProperty("_startClientFlags").intValue = 0;
        nmSo.ApplyModifiedPropertiesWithoutUndo();
        netGo.AddComponent<StatisticsManager>();

        // No physics provider: ragdolls are local Unity physics, never rolled back, so Unity
        // keeps stepping physics itself. Server frames at 30 Hz, like the old truck snapshots.
        var predictionGo = new GameObject("Prediction");
        PredictionManager prediction = predictionGo.AddComponent<PredictionManager>();
        var predSo = new SerializedObject(prediction);
        predSo.FindProperty("_physicsProvider").intValue = 0;
        predSo.FindProperty("_updateViewMode").intValue = (int)UpdateViewMode.Update;
        predSo.FindProperty("_builtInSystems").intValue = (int)(BuiltInSystems.Time | BuiltInSystems.Hierarchy | BuiltInSystems.Players | BuiltInSystems.Random);
        predSo.FindProperty("_predictedPrefabs").objectReferenceValue = predictedPrefabs;
        predSo.FindProperty("_serverUpdateRate").intValue = 30;
        predSo.ApplyModifiedPropertiesWithoutUndo();
        var spawnerGo = new GameObject("PredictedPlayerSpawner");
        PredictedPlayerSpawner spawner = spawnerGo.AddComponent<PredictedPlayerSpawner>();
        Set(spawner, "_playerPrefab", playerPrefab);
        var shotsGo = new GameObject("Shots");
        ShotRelay shots = shotsGo.AddComponent<ShotRelay>();

        var gameGo = new GameObject("Game");
        GameManager gm = gameGo.AddComponent<GameManager>();
        BotBrain bot = gameGo.AddComponent<BotBrain>();
        FrameLogger logger = gameGo.AddComponent<FrameLogger>();
        Set(logger, "captureCamera", cam);
        Set(gm, "network", nm);
        Set(gm, "udp", udp);
        Set(gm, "prediction", prediction);
        Set(gm, "shots", shots);
        Set(gm, "truck", truck);
        Set(gm, "npcs", npcManager);
        Set(gm, "interiorOrigin", interior);
        Set(gm, "mainCamera", cam);
        Set(gm, "frameLogger", logger);
        Set(gm, "botBrain", bot);
        Set(gm, "projectilePrefab", AssetDatabase.LoadAssetAtPath<Projectile>("Assets/Prefabs/Local/IceCream.prefab"));

        EditorSceneManager.SaveScene(scene, ScenePath);
        EditorBuildSettings.scenes = new[] { new EditorBuildSettingsScene(ScenePath, true) };
        AssetDatabase.SaveAssets();
        Debug.Log("DemoBuilder: scene built with " + prefabs.prefabs.Count + " network prefabs");
    }

    [MenuItem("Tools/Truck Demo/Build Player")]
    public static void BuildPlayer()
    {
        var options = new BuildPlayerOptions
        {
            scenes = new[] { ScenePath },
            locationPathName = "Build/TruckDemo.x86_64",
            target = BuildTarget.StandaloneLinux64,
            options = BuildOptions.None,
        };
        var report = BuildPipeline.BuildPlayer(options);
        Debug.Log("DemoBuilder: build " + report.summary.result + " in " + report.summary.totalTime);
        if (report.summary.result != UnityEditor.Build.Reporting.BuildResult.Succeeded)
        {
            EditorApplication.Exit(1);
        }
    }

    public static void BuildAll()
    {
        BuildScene();
        BuildPlayer();
    }

    // ---------------- helpers ----------------

    static Material Mat(string name, Color color)
    {
        if (materials.TryGetValue(name, out Material m))
        {
            return m;
        }
        string path = "Assets/Materials/" + name + ".mat";
        m = AssetDatabase.LoadAssetAtPath<Material>(path);
        if (m == null)
        {
            m = new Material(Shader.Find("Standard"));
            AssetDatabase.CreateAsset(m, path);
        }
        m.color = color;
        EditorUtility.SetDirty(m);
        materials[name] = m;
        return m;
    }

    static void Set(Object target, string field, Object value)
    {
        var so = new SerializedObject(target);
        so.FindProperty(field).objectReferenceValue = value;
        so.ApplyModifiedPropertiesWithoutUndo();
    }

    static void SetBool(Object target, string field, bool value)
    {
        var so = new SerializedObject(target);
        so.FindProperty(field).boolValue = value;
        so.ApplyModifiedPropertiesWithoutUndo();
    }

    static void SetFloat(Object target, string field, float value)
    {
        var so = new SerializedObject(target);
        so.FindProperty(field).floatValue = value;
        so.ApplyModifiedPropertiesWithoutUndo();
    }

    static void SetArray(Object target, string field, Object[] values)
    {
        var so = new SerializedObject(target);
        SerializedProperty p = so.FindProperty(field);
        p.arraySize = values.Length;
        for (int i = 0; i < values.Length; i++)
        {
            p.GetArrayElementAtIndex(i).objectReferenceValue = values[i];
        }
        so.ApplyModifiedPropertiesWithoutUndo();
    }

    // Visual-only box (no collider).
    static GameObject VisualBox(string name, Transform parent, Vector3 center, Vector3 size, Material m, PrimitiveType type = PrimitiveType.Cube)
    {
        GameObject go = GameObject.CreatePrimitive(type);
        go.name = name;
        Object.DestroyImmediate(go.GetComponent<Collider>());
        go.transform.SetParent(parent, false);
        go.transform.localPosition = center;
        go.transform.localScale = size;
        go.GetComponent<Renderer>().sharedMaterial = m;
        return go;
    }

    static GameObject SolidBox(string name, Transform parent, Vector3 center, Vector3 size, Material m, int layer)
    {
        GameObject go = GameObject.CreatePrimitive(PrimitiveType.Cube);
        go.name = name;
        go.transform.SetParent(parent, false);
        go.transform.localPosition = center;
        go.transform.localScale = size;
        go.layer = layer;
        go.isStatic = true;
        if (m != null)
        {
            go.GetComponent<Renderer>().sharedMaterial = m;
        }
        else
        {
            Object.DestroyImmediate(go.GetComponent<MeshRenderer>());
        }
        return go;
    }

    static void BuildTown()
    {
        int world = LayerMask.NameToLayer("World");
        var root = new GameObject("Town").transform;
        float e = TownLayout.Extent;
        SolidBox("Ground", root, new Vector3(0f, -0.5f, 0f), new Vector3(e + 40f, 1f, e + 40f), Mat("Road", new Color(0.32f, 0.33f, 0.36f)), world);
        var rng = new System.Random(7);
        for (int i = 0; i < TownLayout.Buildings.Count; i++)
        {
            Rect r = TownLayout.Buildings[i];
            bool wall = i >= TownLayout.Blocks * TownLayout.Blocks;
            float h = wall ? 3f : 6f + (float)rng.NextDouble() * 10f;
            Color c = wall ? new Color(0.5f, 0.45f, 0.4f) : Color.HSVToRGB((float)rng.NextDouble(), 0.25f, 0.85f);
            SolidBox(wall ? "Wall" : "House", root, new Vector3(r.center.x, h * 0.5f, r.center.y), new Vector3(r.width, h, r.height),
                Mat(wall ? "Wall" : "House" + (i % 6), c), world);
            if (!wall)
            {
                // Sidewalk ring (visual).
                float s = TownLayout.Sidewalk;
                VisualBox("Sidewalk", root, new Vector3(r.center.x, 0.02f, r.center.y), new Vector3(r.width + s * 2f, 0.04f, r.height + s * 2f),
                    Mat("Sidewalk", new Color(0.7f, 0.7f, 0.68f)));
            }
        }
    }

    // Static copy of the truck's cargo box far below the town. Inside players walk here.
    static Transform BuildInterior()
    {
        int interior = LayerMask.NameToLayer("Interior");
        var root = new GameObject("Interior Pocket").transform;
        root.position = new Vector3(0f, -200f, 0f);
        float w = TruckSim.Width;
        float l = TruckSim.Length;
        float f = PlayerAvatar.FloorY;
        SolidBox("Floor", root, new Vector3(0f, f - 0.25f, 0f), new Vector3(w, 0.5f, l), null, interior);
        SolidBox("Left", root, new Vector3(-w * 0.5f + 0.05f, f + 1.2f, 0f), new Vector3(0.1f, 2.4f, l), null, interior);
        SolidBox("Right", root, new Vector3(w * 0.5f - 0.05f, f + 1.2f, 0f), new Vector3(0.1f, 2.4f, l), null, interior);
        SolidBox("Front", root, new Vector3(0f, f + 1.2f, l * 0.5f - 0.05f), new Vector3(w, 2.4f, 0.1f), null, interior);
        SolidBox("Roof", root, new Vector3(0f, f + 2.35f, 0f), new Vector3(w, 0.1f, l), null, interior);
        SolidBox("Counter", root, new Vector3(w * 0.5f - 0.25f, f + 0.5f, 1.4f), new Vector3(0.4f, 1f, 1.4f), null, interior);
        return root;
    }

    static Truck BuildTruck(out Rigidbody body)
    {
        float w = TruckSim.Width;
        float l = TruckSim.Length;
        float f = PlayerAvatar.FloorY;
        var root = new GameObject("Truck");
        Material white = Mat("TruckWhite", new Color(0.95f, 0.95f, 0.97f));
        Material pink = Mat("TruckPink", new Color(1f, 0.55f, 0.75f));
        Material dark = Mat("Tyre", new Color(0.1f, 0.1f, 0.1f));
        Material glass = Mat("Glass", new Color(0.4f, 0.6f, 0.75f));
        Transform t = root.transform;
        VisualBox("Floor", t, new Vector3(0f, f - 0.2f, 0f), new Vector3(w, 0.4f, l), Mat("TruckFloor", new Color(0.55f, 0.4f, 0.3f)));
        VisualBox("Skirt", t, new Vector3(0f, 0.55f, 0f), new Vector3(w - 0.1f, 0.3f, l - 0.2f), pink);
        // Side walls with serving windows (visual only, so players can see out).
        foreach (float side in new[] { -1f, 1f })
        {
            float x = side * (w * 0.5f - 0.05f);
            VisualBox("WallLow", t, new Vector3(x, f + 0.55f, 0f), new Vector3(0.1f, 1.1f, l), white);
            VisualBox("WallTop", t, new Vector3(x, f + 2.2f, 0f), new Vector3(0.1f, 0.4f, l), pink);
            VisualBox("PillarFront", t, new Vector3(x, f + 1.5f, l * 0.5f - 0.6f), new Vector3(0.1f, 1f, 1.2f), white);
            VisualBox("PillarBack", t, new Vector3(x, f + 1.5f, -l * 0.5f + 0.5f), new Vector3(0.1f, 1f, 1f), white);
        }
        VisualBox("Front", t, new Vector3(0f, f + 1.2f, l * 0.5f - 0.05f), new Vector3(w, 2.4f, 0.1f), white);
        GameObject roof = VisualBox("Roof", t, new Vector3(0f, f + 2.45f, 0f), new Vector3(w + 0.1f, 0.12f, l + 0.1f), pink);
        GameObject cone = VisualBox("Cone", t, new Vector3(0f, f + 2.9f, 0.5f), new Vector3(0.6f, 0.8f, 0.6f), Mat("Cone", new Color(0.95f, 0.75f, 0.45f)), PrimitiveType.Capsule);
        VisualBox("Hood", t, new Vector3(0f, 1.0f, l * 0.5f + 0.7f), new Vector3(w - 0.2f, 1.0f, 1.4f), white);
        VisualBox("Windshield", t, new Vector3(0f, f + 1.4f, l * 0.5f + 0.02f), new Vector3(w - 0.4f, 0.7f, 0.05f), glass);
        var frontWheels = new List<Transform>();
        foreach (float side in new[] { -1f, 1f })
        {
            foreach (float z in new[] { -l * 0.5f + 1.1f, l * 0.5f + 0.5f })
            {
                var pivot = new GameObject("WheelPivot").transform;
                pivot.SetParent(t, false);
                pivot.localPosition = new Vector3(side * (w * 0.5f - 0.15f), 0.45f, z);
                GameObject wheel = VisualBox("Wheel", pivot, Vector3.zero, new Vector3(0.9f, 0.18f, 0.9f), dark, PrimitiveType.Cylinder);
                wheel.transform.localRotation = Quaternion.Euler(0f, 0f, 90f);
                if (z > 0f)
                {
                    frontWheels.Add(pivot);
                }
            }
        }
        Truck truck = root.AddComponent<Truck>();

        // Collision body for ragdolls and players outside. Follows the drawn truck.
        var bodyGo = new GameObject("TruckBody");
        bodyGo.layer = LayerMask.NameToLayer("Truck");
        body = bodyGo.AddComponent<Rigidbody>();
        body.isKinematic = true;
        body.interpolation = RigidbodyInterpolation.None;
        var box = bodyGo.AddComponent<BoxCollider>();
        box.center = new Vector3(0f, 1.6f, 0.35f);
        box.size = new Vector3(w, 2.9f, l + 0.7f);
        var truckSo = new SerializedObject(truck);
        truckSo.FindProperty("_predictionPolicy").intValue = (int)PredictionPolicy.FullPrediction;
        truckSo.FindProperty("_repeatInputFactor").floatValue = 4f;
        truckSo.ApplyModifiedPropertiesWithoutUndo();
        Set(truck, "body", body);
        SetArray(truck, "frontWheels", frontWheels.ToArray());
        SetArray(truck, "roofParts", new Object[] { roof, cone });
        return truck;
    }

    struct BoneDef
    {
        public string name;
        public Vector3 local;
        public Vector3 size; // box size, or (radius, length, 0) for capsules
        public Vector3 center;
        public bool capsule;
        public bool sphere;
        public float mass;
    }

    // 11-bone primitive humanoid. Index order matches Humanoid.Parent.
    static GameObject BuildHumanoid(string name, float scale, Color shirt, bool physical)
    {
        var defs = new[]
        {
            new BoneDef { name = "Pelvis", local = new Vector3(0f, 0.95f, 0f), size = new Vector3(0.34f, 0.2f, 0.22f), mass = 10f },
            new BoneDef { name = "Chest", local = new Vector3(0f, 0.1f, 0f), size = new Vector3(0.38f, 0.42f, 0.24f), center = new Vector3(0f, 0.21f, 0f), mass = 12f },
            new BoneDef { name = "Head", local = new Vector3(0f, 0.46f, 0f), size = new Vector3(0.15f, 0f, 0f), center = new Vector3(0f, 0.14f, 0f), sphere = true, mass = 4f },
            new BoneDef { name = "ArmL", local = new Vector3(-0.25f, 0.38f, 0f), size = new Vector3(0.06f, 0.3f, 0f), center = new Vector3(0f, -0.15f, 0f), capsule = true, mass = 2f },
            new BoneDef { name = "ForearmL", local = new Vector3(0f, -0.3f, 0f), size = new Vector3(0.055f, 0.28f, 0f), center = new Vector3(0f, -0.14f, 0f), capsule = true, mass = 1.5f },
            new BoneDef { name = "ArmR", local = new Vector3(0.25f, 0.38f, 0f), size = new Vector3(0.06f, 0.3f, 0f), center = new Vector3(0f, -0.15f, 0f), capsule = true, mass = 2f },
            new BoneDef { name = "ForearmR", local = new Vector3(0f, -0.3f, 0f), size = new Vector3(0.055f, 0.28f, 0f), center = new Vector3(0f, -0.14f, 0f), capsule = true, mass = 1.5f },
            new BoneDef { name = "ThighL", local = new Vector3(-0.1f, -0.06f, 0f), size = new Vector3(0.075f, 0.44f, 0f), center = new Vector3(0f, -0.22f, 0f), capsule = true, mass = 5f },
            new BoneDef { name = "ShinL", local = new Vector3(0f, -0.44f, 0f), size = new Vector3(0.065f, 0.45f, 0f), center = new Vector3(0f, -0.225f, 0f), capsule = true, mass = 3.5f },
            new BoneDef { name = "ThighR", local = new Vector3(0.1f, -0.06f, 0f), size = new Vector3(0.075f, 0.44f, 0f), center = new Vector3(0f, -0.22f, 0f), capsule = true, mass = 5f },
            new BoneDef { name = "ShinR", local = new Vector3(0f, -0.44f, 0f), size = new Vector3(0.065f, 0.45f, 0f), center = new Vector3(0f, -0.225f, 0f), capsule = true, mass = 3.5f },
        };
        var root = new GameObject(name);
        var bones = new Rigidbody[Humanoid.BoneCount];
        Material skin = Mat("Skin", new Color(1f, 0.8f, 0.65f));
        Material shirtMat = Mat("Shirt" + ColorUtility.ToHtmlStringRGB(shirt), shirt);
        Material pants = Mat("Pants", new Color(0.25f, 0.25f, 0.3f));
        for (int i = 0; i < defs.Length; i++)
        {
            BoneDef d = defs[i];
            var go = new GameObject(d.name);
            Transform parent = Humanoid.Parent[i] < 0 ? root.transform : bones[Humanoid.Parent[i]].transform;
            go.transform.SetParent(parent, false);
            go.transform.localPosition = d.local * scale;
            Rigidbody rb = go.AddComponent<Rigidbody>();
            rb.isKinematic = true;
            rb.mass = d.mass * scale * scale * scale;
            rb.collisionDetectionMode = CollisionDetectionMode.ContinuousSpeculative;
            rb.solverIterations = 12;
            rb.linearDamping = 0.05f;
            rb.angularDamping = 0.6f;
            bones[i] = rb;
            Material m = i == 2 || i == 4 || i == 6 ? skin : i >= 7 ? pants : shirtMat;
            Vector3 c = d.center * scale;
            if (d.sphere)
            {
                VisualBox("Mesh", go.transform, c, Vector3.one * d.size.x * 2f * scale, m, PrimitiveType.Sphere);
                if (physical)
                {
                    var col = go.AddComponent<SphereCollider>();
                    col.center = c;
                    col.radius = d.size.x * scale;
                }
            }
            else if (d.capsule)
            {
                VisualBox("Mesh", go.transform, c, new Vector3(d.size.x * 2f, d.size.y * 0.5f + d.size.x, d.size.x * 2f) * scale, m, PrimitiveType.Capsule);
                if (physical)
                {
                    var col = go.AddComponent<CapsuleCollider>();
                    col.center = c;
                    col.radius = d.size.x * scale;
                    col.height = (d.size.y + d.size.x * 2f) * scale;
                    col.direction = 1;
                }
            }
            else
            {
                VisualBox("Mesh", go.transform, c, d.size * scale, m);
                if (physical)
                {
                    var col = go.AddComponent<BoxCollider>();
                    col.center = c;
                    col.size = d.size * scale;
                }
            }
            if (physical && i > 0)
            {
                var joint = go.AddComponent<CharacterJoint>();
                joint.connectedBody = bones[Humanoid.Parent[i]];
                joint.axis = Vector3.right;
                joint.swingAxis = Vector3.forward;
                bool knee = i == 8 || i == 10;
                bool elbow = i == 4 || i == 6;
                joint.lowTwistLimit = new SoftJointLimit { limit = knee ? -120f : elbow ? -5f : -40f };
                joint.highTwistLimit = new SoftJointLimit { limit = knee ? 5f : elbow ? 120f : 40f };
                joint.swing1Limit = new SoftJointLimit { limit = knee || elbow ? 5f : i == 2 ? 30f : 60f };
                joint.swing2Limit = new SoftJointLimit { limit = knee || elbow ? 5f : i == 2 ? 30f : 45f };
                joint.enableProjection = true;
            }
        }
        Humanoid h = root.AddComponent<Humanoid>();
        SetArray(h, "bones", bones);
        SetFloat(h, "height", scale);
        return root;
    }

    static GameObject BuildPlayerPrefab()
    {
        GameObject root = BuildHumanoid("Player", 1f, Color.white, false);
        // Humanoid sits on the visual; the root carries the controller.
        var player = new GameObject("Player");
        root.name = "Visual";
        root.transform.SetParent(player.transform, false);
        var cc = player.AddComponent<CharacterController>();
        cc.center = new Vector3(0f, 0.9f, 0f);
        cc.height = 1.8f;
        cc.radius = 0.32f;
        cc.stepOffset = 0.35f;
        cc.skinWidth = 0.03f;
        var gun = new GameObject("Gun").transform;
        gun.SetParent(root.transform, false);
        VisualBox("Barrel", gun, new Vector3(0f, 0f, 0.25f), new Vector3(0.12f, 0.12f, 0.55f), Mat("Gun", new Color(0.3f, 0.9f, 0.9f)));
        VisualBox("Scoop", gun, new Vector3(0f, 0.12f, 0.05f), new Vector3(0.22f, 0.22f, 0.22f), Mat("Scoop", new Color(1f, 0.9f, 0.95f)), PrimitiveType.Sphere);
        var muzzle = new GameObject("Muzzle").transform;
        muzzle.SetParent(gun, false);
        muzzle.localPosition = new Vector3(0f, 0f, 0.55f);
        PlayerAvatar avatar = player.AddComponent<PlayerAvatar>();
        Set(avatar, "controller", cc);
        Set(avatar, "body", root.GetComponent<Humanoid>());
        Set(avatar, "gun", gun);
        Set(avatar, "muzzle", muzzle);
        var tinted = new List<Object>();
        foreach (Transform bone in root.GetComponentsInChildren<Transform>())
        {
            if (bone.name == "Mesh" && (bone.parent.name == "Chest" || bone.parent.name == "Pelvis" || bone.parent.name.StartsWith("Arm")))
            {
                tinted.Add(bone.GetComponent<Renderer>());
            }
        }
        SetArray(avatar, "tinted", tinted.ToArray());
        var avatarSo = new SerializedObject(avatar);
        avatarSo.FindProperty("_predictionPolicy").intValue = (int)PredictionPolicy.PredictedIfOwned;
        avatarSo.ApplyModifiedPropertiesWithoutUndo();
        AssetDatabase.DeleteAsset(NetPrefabFolder + "/Player.prefab");
        GameObject prefab = PrefabUtility.SaveAsPrefabAsset(player, PredictedPrefabFolder + "/Player.prefab");
        Object.DestroyImmediate(player);
        return prefab;
    }

    static void BuildProjectilePrefab()
    {
        GameObject go = GameObject.CreatePrimitive(PrimitiveType.Sphere);
        go.name = "IceCream";
        Object.DestroyImmediate(go.GetComponent<Collider>());
        go.transform.localScale = Vector3.one * 0.26f;
        go.GetComponent<Renderer>().sharedMaterial = Mat("IceCream", new Color(1f, 0.7f, 0.85f));
        go.AddComponent<Projectile>();
        PrefabUtility.SaveAsPrefabAsset(go, "Assets/Prefabs/Local/IceCream.prefab");
        Object.DestroyImmediate(go);
    }
}
