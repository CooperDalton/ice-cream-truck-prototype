using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.AI;
using UnityEngine.EventSystems;
using UnityEngine.InputSystem.UI;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;
using UnityEngine.UI;
using Unity.AI.Navigation;
using Object = UnityEngine.Object;

public static class TycoonSceneBuilder
{
    private const string Root = "Assets/Art/Tycoon/";
    private static TycoonGameManager game;
    private static TycoonCatalogSO catalog;
    private static Dictionary<string, GameObject> models;
    private static Dictionary<string, Material> materials;
    private static Font font;
    private static Color plum = new Color(.20f, .16f, .25f), cream = new Color(1, .96f, .87f), mint = new Color(.45f, .77f, .67f), pink = new Color(.93f, .46f, .63f);
    [Serializable] private class Manifest { public Entry[] models; public MaterialEntry[] materials; }
    [Serializable] private class Entry { public string name, file; }
    [Serializable] private class MaterialEntry { public string name; public float[] color; }
    [MenuItem("Ice Cream/Build tycoon assets")]
    public static void BuildAssets()
    {
        Directory.CreateDirectory(Root + "Prefabs"); Directory.CreateDirectory(Root + "Materials"); Directory.CreateDirectory(Root + "Meshes");
        AssetDatabase.Refresh();
        var manifest = JsonUtility.FromJson<Manifest>(File.ReadAllText(Root + "Models.json"));
        materials = new Dictionary<string, Material>(); models = new Dictionary<string, GameObject>();
        foreach (var e in manifest.materials)
        {
            string safe = Safe(e.name); string path = Root + "Materials/" + safe + ".mat";
            var material = AssetDatabase.LoadAssetAtPath<Material>(path);
            if (material == null) { material = new Material(Shader.Find("Ice Cream/Toon")); AssetDatabase.CreateAsset(material, path); }
            material.SetColor("_BaseColor", new Color(e.color[0], e.color[1], e.color[2], 1).gamma);
            materials[e.name] = material; EditorUtility.SetDirty(material);
        }
        foreach (var entry in manifest.models)
        {
            var completed = AssetDatabase.LoadAssetAtPath<GameObject>(Root + "Prefabs/" + entry.file + ".prefab");
            if (completed != null) { models[entry.name] = completed; continue; }
            var fbx = AssetDatabase.LoadAssetAtPath<GameObject>(Root + "Models/" + entry.file + ".fbx");
            var root = new GameObject(entry.name); var copy = Object.Instantiate(fbx, root.transform);
            foreach (var r in copy.GetComponentsInChildren<Renderer>()) r.sharedMaterials = r.sharedMaterials.Select(m => materials[m.name]).ToArray();
            if (entry.name.StartsWith("Floating")) PrepareCharacter(root);
            else if (entry.name == "Waffle iron")
            {
                var lid = Point("Lid", root.transform, new Vector3(0, .17f, -.19f));
                foreach (var f in copy.GetComponentsInChildren<MeshFilter>().Where(f => f.name.StartsWith("LidPart_")).ToArray()) f.transform.SetParent(lid, true);
                Combine(lid.gameObject, entry.file + "_lid"); Combine(copy, entry.file);
            }
            else if (entry.name.EndsWith(" tub"))
            {
                var fill = Point("Fill", root.transform, Vector3.zero);
                foreach (var f in copy.GetComponentsInChildren<MeshFilter>().Where(f => f.name.Contains("Ice cream fill")).ToArray()) f.transform.SetParent(fill, true);
                Combine(fill.gameObject, entry.file + "_fill"); Combine(copy, entry.file);
                root.AddComponent<TycoonTubVisual>().fill = fill.GetComponentsInChildren<Renderer>();
            }
            else Combine(copy, entry.file);
            var prefab = PrefabUtility.SaveAsPrefabAsset(root, Root + "Prefabs/" + entry.file + ".prefab"); models[entry.name] = prefab; Object.DestroyImmediate(root);
        }
        catalog = AssetDatabase.LoadAssetAtPath<TycoonCatalogSO>(Root + "Catalog.asset");
        if (catalog == null) { catalog = ScriptableObject.CreateInstance<TycoonCatalogSO>(); AssetDatabase.CreateAsset(catalog, Root + "Catalog.asset"); }
        catalog.bowl = models["Empty bowl"]; catalog.cone = models["Empty waffle cone"]; catalog.basicScooper = models["Basic scooper"]; catalog.improvedScooper = models["One swipe scooper"];
        catalog.batter = models["Batter bottle"]; catalog.bowlPack = models["Bowl supply pack"]; catalog.batterPack = models["Batter refill carton"];
        catalog.flatWaffle = models["Flat baked waffle"];
        catalog.tubs = TycoonCatalogSO.FlavorNames.Select(n => models[n + " tub"]).ToArray(); catalog.scoops = TycoonCatalogSO.FlavorNames.Select(n => models[n + " scoop"]).ToArray();
        catalog.toppings = TycoonCatalogSO.ToppingNames.Select(n => models[n + " dispenser"]).ToArray(); catalog.toppingPacks = TycoonCatalogSO.ToppingNames.Select(n => models[n + " refill"]).ToArray(); catalog.toppingLayers = TycoonCatalogSO.ToppingNames.Select(n => models[n + " serving layer"]).ToArray();
        catalog.flavorMaterials = catalog.scoops.Select(p => p.GetComponentInChildren<Renderer>().sharedMaterial).ToArray();
        catalog.workerPrefab = ActorPrefab(true); catalog.customerPrefab = ActorPrefab(false);
        var loose = new GameObject("Loose supply"); var pickup = loose.AddComponent<TycoonLooseItem>(); pickup.body = loose.AddComponent<Rigidbody>(); pickup.body.mass = .3f;
        var collider = loose.AddComponent<BoxCollider>(); collider.center = new Vector3(0, .1f, 0); collider.size = new Vector3(.25f, .2f, .25f);
        pickup.visualRoot = Point("Visual", loose.transform, Vector3.zero);
        catalog.loosePrefab = PrefabUtility.SaveAsPrefabAsset(loose, Root + "Prefabs/LooseSupply.prefab").GetComponent<TycoonLooseItem>(); Object.DestroyImmediate(loose);
        catalog.partPrefabs = new[] {
            PartPrefab(0, TycoonPart.Kind.Table, "Prep table", new Vector2(2,1), false),
            PartPrefab(1, TycoonPart.Kind.Tub, "Vanilla tub", new Vector2(.5f,.5f), true),
            PartPrefab(2, TycoonPart.Kind.Prep, "Cone holder", new Vector2(.5f,.5f), true),
            PartPrefab(3, TycoonPart.Kind.Iron, "Waffle iron", new Vector2(.5f,.75f), true),
            PartPrefab(4, TycoonPart.Kind.Locker, "4 slot locker", new Vector2(1,.5f), false),
            PartPrefab(5, TycoonPart.Kind.ColdStorage, "4 slot cold rack", new Vector2(1,.5f), false),
            PartPrefab(6, TycoonPart.Kind.Sign, "Open closed sign", new Vector2(.5f,.5f), false),
            PartPrefab(7, TycoonPart.Kind.ServingCounter, "Service counter", new Vector2(2,1), false),
            PartPrefab(8, TycoonPart.Kind.Shelf, "Pickup shelf", new Vector2(1,.5f), false),
            PartPrefab(9, TycoonPart.Kind.Trash, "Tub transport lid", new Vector2(.5f,.5f), false) };
        EditorUtility.SetDirty(catalog); AssetDatabase.SaveAssets();
        Debug.Log("TYCOON_ASSETS_READY " + models.Count);
    }
    private static string Safe(string text)
    {
        return string.Concat(text.Select(c => char.IsLetterOrDigit(c) ? c : '_'));
    }
    public static void RebuildWaffle()
    {
        var root = new GameObject("Waffle iron");
        var fbx = AssetDatabase.LoadAssetAtPath<GameObject>(Root + "Models/Waffle_iron.fbx");
        var copy = Object.Instantiate(fbx, root.transform);
        foreach (var renderer in copy.GetComponentsInChildren<Renderer>()) renderer.sharedMaterials = renderer.sharedMaterials.Select(m => AssetDatabase.LoadAssetAtPath<Material>(Root + "Materials/" + Safe(m.name) + ".mat")).ToArray();
        var lid = Point("Lid", root.transform, new Vector3(0,.17f,-.19f));
        foreach (var filter in copy.GetComponentsInChildren<MeshFilter>().Where(f=>f.name.StartsWith("LidPart_")).ToArray()) filter.transform.SetParent(lid,true);
        Combine(lid.gameObject,"Waffle_iron_lid"); Combine(copy,"Waffle_iron");
        PrefabUtility.SaveAsPrefabAsset(root,Root+"Prefabs/Waffle_iron.prefab");Object.DestroyImmediate(root);AssetDatabase.SaveAssets();
    }
    internal static void Combine(GameObject root, string name)
    {
        var filters = root.GetComponentsInChildren<MeshFilter>();
        var groups = new Dictionary<Material, List<CombineInstance>>();
        foreach (var filter in filters)
        {
            var renderer = filter.GetComponent<MeshRenderer>();
            for (int i = 0; i < filter.sharedMesh.subMeshCount; i++)
            {
                var mat = renderer.sharedMaterials[Mathf.Min(i, renderer.sharedMaterials.Length - 1)];
                if (!groups.ContainsKey(mat)) groups.Add(mat, new List<CombineInstance>());
                groups[mat].Add(new CombineInstance { mesh = filter.sharedMesh, subMeshIndex = i, transform = root.transform.worldToLocalMatrix * filter.transform.localToWorldMatrix });
            }
        }
        int index = 0;
        foreach (var pair in groups)
        {
            var mesh = new Mesh { indexFormat = IndexFormat.UInt32 }; mesh.CombineMeshes(pair.Value.ToArray(), true, true);
            string path = Root + "Meshes/" + name + "_" + index + ".asset";
            var existing = AssetDatabase.LoadAssetAtPath<Mesh>(path);
            if (existing == null) AssetDatabase.CreateAsset(mesh, path); else { EditorUtility.CopySerialized(mesh, existing); Object.DestroyImmediate(mesh); mesh = existing; }
            var child = new GameObject("Surface " + index++); child.transform.SetParent(root.transform, false);
            child.AddComponent<MeshFilter>().sharedMesh = mesh; child.AddComponent<MeshRenderer>().sharedMaterial = pair.Key;
        }
        foreach (var f in filters) { Object.DestroyImmediate(f.GetComponent<MeshRenderer>()); Object.DestroyImmediate(f); }
        foreach (var t in root.GetComponentsInChildren<Transform>().Reverse().ToArray()) if (t != root.transform && t.childCount == 0 && t.GetComponent<MeshFilter>() == null) Object.DestroyImmediate(t.gameObject);
    }
    private static void PrepareCharacter(GameObject root)
    {
        var body = Point("Body", root.transform, Vector3.zero);
        var left = Point("Left hand", root.transform, new Vector3(-.55f,.8f,0));
        var right = Point("Right hand", root.transform, new Vector3(.55f,.8f,0));
        foreach (var f in root.GetComponentsInChildren<MeshFilter>().ToArray())
        {
            bool hand = f.name.Contains("Mitten") || f.name.Contains("fingertip") || f.name.Contains("Thumb");
            var parent = hand ? f.GetComponent<Renderer>().bounds.center.x > 0 ? right : left : body;
            f.transform.SetParent(parent, true);
        }
        Combine(body.gameObject, Safe(root.name) + "_body"); Combine(left.gameObject, Safe(root.name) + "_left"); Combine(right.gameObject, Safe(root.name) + "_right");
    }
    private static TycoonActor ActorPrefab(bool staff)
    {
        var root = new GameObject(staff ? "Floating employee" : "Floating customer"); var model = Object.Instantiate(models[staff ? "Floating Staff" : "Floating Customer"], root.transform);
        var actor = root.AddComponent<TycoonActor>(); actor.agent = root.AddComponent<NavMeshAgent>(); actor.agent.radius = .25f; actor.agent.height = 1.8f; actor.agent.speed = 1.5f; actor.agent.stoppingDistance = .12f; actor.agent.angularSpeed = 360;
        var nodes = model.GetComponentsInChildren<Transform>();
        actor.body = nodes.Single(t => t.name == "Body"); actor.leftHand = nodes.Single(t => t.name == "Left hand"); actor.rightHand = nodes.Single(t => t.name == "Right hand");
        actor.grip = Point("Grip", actor.rightHand, Vector3.zero); actor.worker = staff;
        if (staff) { var worker = root.AddComponent<TycoonWorker>(); worker.actor = actor; }
        var prefab = PrefabUtility.SaveAsPrefabAsset(root, Root + "Prefabs/" + (staff ? "Employee" : "Customer") + ".prefab"); Object.DestroyImmediate(root); return prefab.GetComponent<TycoonActor>();
    }
    private static TycoonPart PartPrefab(int index, TycoonPart.Kind kind, string visual, Vector2 size, bool top)
    {
        var root = new GameObject(kind.ToString()); var model = Object.Instantiate(models[visual], root.transform);
        var part = root.AddComponent<TycoonPart>(); part.kind = kind; part.catalogIndex = index; part.footprint = size; part.tabletop = top;
        part.operatingPoint = Point("Operate", root.transform, new Vector3(0, top ? -.94f : 0, -.9f));
        part.handTarget = Point("Hand target", root.transform, new Vector3(0, top ? .13f : 1, 0));
        part.contentPoint = Point("Contents", root.transform, new Vector3(0, kind == TycoonPart.Kind.Prep ? .10f : .15f, 0));
        part.lid = kind == TycoonPart.Kind.Iron ? model.GetComponentsInChildren<Transform>().Single(t => t.name == "Lid") : Point("No lid", root.transform, Vector3.zero);
        part.fillRenderers = kind == TycoonPart.Kind.Tub ? model.GetComponentsInChildren<Transform>().Single(t => t.name == "Fill").GetComponentsInChildren<Renderer>() : Array.Empty<Renderer>();
        if (kind == TycoonPart.Kind.Locker)
        {
            part.lockerModels = new[] { model, Object.Instantiate(models["8 slot locker"], root.transform), Object.Instantiate(models["12 slot locker"], root.transform) };
            part.lockerModels[1].SetActive(false); part.lockerModels[2].SetActive(false);
        }
        if (kind == TycoonPart.Kind.Tub) part.contents = new TycoonItem(TycoonItem.Kind.Tub, 12);
        if (kind == TycoonPart.Kind.Tub) part.tubModel = model;
        var box = root.AddComponent<BoxCollider>(); box.size = new Vector3(size.x, top ? .22f : 1, size.y); box.center = Vector3.up * (top ? .11f : .5f);
        if (!top && kind != TycoonPart.Kind.Sign)
        {
            var obstacle = root.AddComponent<NavMeshModifier>(); obstacle.overrideArea = true; obstacle.area = 1;
        }
        var prefab = PrefabUtility.SaveAsPrefabAsset(root, Root + "Prefabs/Part_" + index + ".prefab"); Object.DestroyImmediate(root); return prefab.GetComponent<TycoonPart>();
    }
    private static Transform Point(string name, Transform parent, Vector3 local)
    {
        var t = new GameObject(name).transform; t.SetParent(parent, false); t.localPosition = local; return t;
    }
    private static GameObject Model(string name, Vector3 position, Transform parent = null)
    {
        var model = (GameObject)PrefabUtility.InstantiatePrefab(AssetDatabase.LoadAssetAtPath<GameObject>(Root + "Prefabs/" + name.Replace(' ', '_') + ".prefab"));
        model.transform.SetParent(parent, false); model.transform.position = position; return model;
    }
    private static GameObject Block(string name, Vector3 position, Vector3 size, Color color, Transform parent = null)
    {
        var go = GameObject.CreatePrimitive(PrimitiveType.Cube); go.name = name; go.transform.SetParent(parent, false); go.transform.position = position; go.transform.localScale = size;
        string path = Root + "Materials/" + Safe(name) + ".mat";
        var mat = AssetDatabase.LoadAssetAtPath<Material>(path);
        if (mat == null) { mat = new Material(Shader.Find("Ice Cream/Toon")); mat.SetColor("_BaseColor", color); AssetDatabase.CreateAsset(mat, path); }
        go.GetComponent<Renderer>().sharedMaterial = mat; return go;
    }
    [MenuItem("Ice Cream/Build tycoon scene")]
    public static void BuildScene()
    {
        const string path = "Assets/Scenes/IceCreamTycoon.unity";
        if (File.Exists(path)) throw new InvalidOperationException("Tycoon scene already exists. Preserve it before rebuilding.");
        var previous = UnityEngine.SceneManagement.SceneManager.GetActiveScene();
        if (previous.isDirty && !string.IsNullOrEmpty(previous.path)) EditorSceneManager.SaveScene(previous);
        var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
        catalog = AssetDatabase.LoadAssetAtPath<TycoonCatalogSO>(Root + "Catalog.asset"); font = Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");
        var systems = new GameObject("Tycoon game"); game = systems.AddComponent<TycoonGameManager>(); game.catalog = catalog;
        game.navigation = systems.AddComponent<NavMeshSurface>(); game.navigation.useGeometry = NavMeshCollectGeometry.PhysicsColliders;
        game.sites = new[] { new TycoonGameManager.Site { name = "Home stand", owned = true }, new TycoonGameManager.Site { name = "Park stand" }, new TycoonGameManager.Site { name = "Ice cream truck" } };
        Vector3[] sites = { Vector3.zero, new Vector3(75,0,40), new Vector3(12,0,-12) };
        for (int i = 0; i < 3; i++) { game.sites[i].origin = Point(game.sites[i].name + " plot", null, sites[i]); game.sites[i].queuePoint = Point("Queue entrance", null, sites[i] + new Vector3(0,0,3)); }
        MakeEnvironment(); MakePlayer();
        SetupSite(0, true); SetupSite(1, false); SetupSite(2, false);
        game.supplier = Point("Supplier destination", null, new Vector3(32,0,-28)); game.pickupPoint = Point("Supplier pickup", null, new Vector3(29,1.6f,-25));
        Model("Supplier storefront", game.supplier.position); Model("Pickup shelf", new Vector3(29,0,-25));
        var supplier = Model("Supplier terminal", new Vector3(33,0,-24)); AddTarget(supplier, TycoonPart.Kind.Supplier, 0);
        game.truckStops = new[] { Point("Playground stop", null, new Vector3(62,0,-12)), Point("Residential stop", null, new Vector3(5,0,46)) };
        foreach (var stop in game.truckStops) Block("Selling stop", stop.position - Vector3.up * .015f, new Vector3(7,.04f,5), pink);
        game.bike = MakeVehicle(false, new Vector3(-4,0,-3)); game.truck = MakeVehicle(true, sites[2]); game.truck.gameObject.SetActive(false);
        game.builder = systems.AddComponent<TycoonBuilder>(); game.builder.game = game;
        game.builder.preview = Block("Equipment placement preview", Vector3.zero, Vector3.one, mint); Object.DestroyImmediate(game.builder.preview.GetComponent<Collider>());
        game.builder.previewRenderer = game.builder.preview.GetComponent<Renderer>(); game.builder.validMaterial = game.builder.previewRenderer.sharedMaterial;
        var invalid = new Material(Shader.Find("Ice Cream/Toon")); invalid.SetColor("_BaseColor", Color.red); AssetDatabase.CreateAsset(invalid, Root + "Materials/InvalidPlacement.mat"); game.builder.invalidMaterial = invalid; game.builder.preview.SetActive(false);
        MakeHUD();
        game.navigation.BuildNavMesh();
        EditorSceneManager.SaveScene(scene, path);
        var scenes = EditorBuildSettings.scenes.ToList(); scenes.RemoveAll(s => s.path == path); scenes.Insert(0, new EditorBuildSettingsScene(path, true)); EditorBuildSettings.scenes = scenes.ToArray();
        AssetDatabase.SaveAssets(); Debug.Log("TYCOON_SCENE_READY");
    }
    private static void MakeEnvironment()
    {
        Block("Town grass", new Vector3(30,-.15f,20), new Vector3(160,.3f,130), new Color(.64f,.78f,.56f));
        Block("Main street", new Vector3(30,.005f,-12), new Vector3(140,.03f,9), new Color(.36f,.35f,.41f));
        Block("Park street", new Vector3(64,.005f,22), new Vector3(9,.03f,68), new Color(.36f,.35f,.41f));
        Block("Residential street", new Vector3(30,.005f,46), new Vector3(75,.03f,9), new Color(.36f,.35f,.41f));
        Block("West street", new Vector3(5,.005f,17), new Vector3(9,.03f,58), new Color(.36f,.35f,.41f));
        for (int i = 0; i < 12; i++)
        {
            var position = new Vector3(-15 + i % 6 * 19,0,i < 6 ? -38 : 63);
            var house = Model(i % 2 == 0 ? "Neighborhood cottage 1" : "Neighborhood cottage 2", position);
            var c = house.AddComponent<BoxCollider>(); c.center = new Vector3(0,1.5f,0); c.size = new Vector3(5,3,4);
            Model("Round maple", position + new Vector3(5,0,3));
        }
        for (int i = 0; i < 14; i++) Model("Round maple", new Vector3(-22 + i * 9,0, i % 2 == 0 ? 28 : 55));
        game.spawnPoints = new[] { new Vector3(-12,0,-20), new Vector3(15,0,-35), new Vector3(38,0,-36), new Vector3(75,0,-24), new Vector3(92,0,22), new Vector3(90,0,59), new Vector3(36,0,60), new Vector3(-10,0,40) }.Select((p,i) => Point("Pedestrian entry " + i, null, p)).ToArray();
        var sun = new GameObject("Warm afternoon sunlight").AddComponent<Light>(); sun.type = LightType.Directional; sun.intensity = 1.6f; sun.color = new Color(1,.95f,.88f); sun.shadows = LightShadows.Soft; sun.transform.rotation = Quaternion.Euler(50,-35,0);
        RenderSettings.ambientMode = AmbientMode.Flat; RenderSettings.ambientLight = new Color(.72f,.75f,.87f); RenderSettings.fog = true; RenderSettings.fogColor = new Color(.76f,.87f,.91f); RenderSettings.fogMode = FogMode.Linear; RenderSettings.fogStartDistance = 90; RenderSettings.fogEndDistance = 180;
        var volume = new GameObject("Toon finishing").AddComponent<Volume>(); volume.isGlobal = true;
        var profile = ScriptableObject.CreateInstance<VolumeProfile>(); profile.Add<Bloom>().intensity.Override(.08f); var color = profile.Add<ColorAdjustments>(); color.saturation.Override(7); color.contrast.Override(4);
        AssetDatabase.CreateAsset(profile, Root + "ToonVolume.asset"); volume.sharedProfile = profile;
    }
    private static void SetupSite(int site, bool opening)
    {
        var origin = game.sites[site].origin.position;
        Block("Stand paving " + site, origin - Vector3.up * .01f, new Vector3(8,.04f,6), cream);
        if (site < 2) Model("Pop up canopy", origin + new Vector3(0,0,.5f));
        var table = PlacePart(0, site, origin + new Vector3(0,0,0));
        for (int i = 0; i < 2; i++)
        {
            var tub = PlacePart(1, site, origin + new Vector3(-.5f + i * .5f,.94f,0)); tub.variant = i; tub.contents = new TycoonItem(TycoonItem.Kind.Tub, opening ? 12 : 0, i);
            tub.support = table; tub.transform.SetParent(table.transform, true);
        }
        var prepTable = PlacePart(0, site, origin + new Vector3(-2,0,0));
        var prep = PlacePart(2, site, origin + new Vector3(-2,.94f,0)); prep.support = prepTable; prep.transform.SetParent(prepTable.transform, true);
        PlacePart(7, site, origin + new Vector3(0,0,2.3f)); PlacePart(6, site, origin + new Vector3(2.5f,0,1.5f));
        PlacePart(8, site, origin + new Vector3(-3,0,2)); PlacePart(5, site, origin + new Vector3(3,0,2));
        var business = Block("Business board " + site, origin + new Vector3(3,1,0), new Vector3(.5f,1,.1f), pink); AddTarget(business, TycoonPart.Kind.Plot, site);
    }
    private static TycoonPart PlacePart(int index, int site, Vector3 position)
    {
        var part = (GameObject)PrefabUtility.InstantiatePrefab(catalog.partPrefabs[index].gameObject); part.transform.position = position;
        var component = part.GetComponent<TycoonPart>(); component.game = game; component.site = site; component.id = game.nextId++; game.parts.Add(component); return component;
    }
    private static TycoonPart AddTarget(GameObject root, TycoonPart.Kind kind, int site)
    {
        var part = root.AddComponent<TycoonPart>(); part.kind = kind; part.site = site; part.id = game.nextId++; part.game = game;
        part.operatingPoint = Point("Operate", root.transform, new Vector3(0,0,-1)); part.handTarget = Point("Touch", root.transform, Vector3.up); part.contentPoint = part.handTarget; part.lid = part.handTarget; part.fillRenderers = Array.Empty<Renderer>();
        if (root.GetComponent<Collider>() == null) { var box = root.AddComponent<BoxCollider>(); box.size = new Vector3(1,1.5f,1); box.center = Vector3.up * .75f; }
        game.parts.Add(part); return part;
    }
    private static void MakePlayer()
    {
        var root = new GameObject("Player"); root.layer=2;root.transform.position = new Vector3(-1,0,-2.3f);
        var player = root.AddComponent<TycoonPlayer>(); game.player = player; player.game = game;
        player.controller = root.AddComponent<CharacterController>(); player.controller.height = 1.75f; player.controller.radius = .25f; player.controller.center = Vector3.up * .875f;
        player.view = new GameObject("Player view").AddComponent<Camera>(); player.view.transform.SetParent(root.transform, false); player.view.transform.localPosition = Vector3.up * 1.58f; player.view.transform.localRotation = Quaternion.Euler(18,0,0);
        player.view.nearClipPlane = .04f; player.view.farClipPlane = 220; player.view.fieldOfView = 72; player.view.backgroundColor = new Color(.75f,.87f,.94f); player.view.clearFlags = CameraClearFlags.SolidColor; player.view.tag = "MainCamera";
        player.view.gameObject.AddComponent<AudioListener>(); player.view.GetUniversalAdditionalCameraData().renderPostProcessing = true;
        player.grip = Point("Held item", player.view.transform, new Vector3(.24f,-.26f,.50f));
        var character = Object.Instantiate(catalog.workerPrefab.gameObject);
        var actor = character.GetComponent<TycoonActor>();
        player.leftHand = Object.Instantiate(actor.leftHand.gameObject, player.view.transform).transform; player.leftHand.localPosition = new Vector3(-.25f,-.29f,.49f);
        player.rightHand = Object.Instantiate(actor.rightHand.gameObject, player.view.transform).transform; player.rightHand.localPosition = new Vector3(.24f,-.29f,.49f);
        foreach (var hand in new[] { player.leftHand, player.rightHand })
        {
            var mesh = hand.GetComponentInChildren<MeshRenderer>();
            mesh.transform.localPosition -= hand.InverseTransformPoint(mesh.bounds.center);
        }
        Object.DestroyImmediate(character);
    }
    private static TycoonVehicle MakeVehicle(bool isTruck, Vector3 position)
    {
        var model = Model(isTruck ? "Ice cream truck" : "Delivery bike 4 cargo", position);
        var vehicle = model.AddComponent<TycoonVehicle>(); vehicle.game = game; vehicle.truck = isTruck;
        vehicle.interaction = AddTarget(model, isTruck ? TycoonPart.Kind.Truck : TycoonPart.Kind.Bike, isTruck ? 2 : 0);
        vehicle.cargo = new TycoonInventory(isTruck ? 12 : 4); vehicle.interaction.storage = vehicle.cargo;
        vehicle.seat = Point("Driver seat", model.transform, new Vector3(0,isTruck ? .6f : .4f,0)); vehicle.exit = Point("Exit", model.transform, new Vector3(-2,0,0)); vehicle.wheels = Array.Empty<Transform>();
        return vehicle;
    }
    private static RectTransform Rect(string name, Transform parent, Vector2 pos, Vector2 size)
    {
        var go = new GameObject(name, typeof(RectTransform)); var rect = go.GetComponent<RectTransform>(); rect.SetParent(parent, false); rect.sizeDelta = size; rect.anchoredPosition = pos; return rect;
    }
    private static Text Text(string name, Transform parent, Vector2 pos, Vector2 size, int fontSize, Color color, TextAnchor anchor = TextAnchor.MiddleLeft)
    {
        var text = Rect(name, parent, pos, size).gameObject.AddComponent<Text>(); text.font = font; text.fontSize = fontSize; text.color = color; text.text = name; text.alignment = anchor; text.raycastTarget = false; return text;
    }
    private static Image Panel(string name, Transform parent, Vector2 pos, Vector2 size, Color color)
    {
        var image = Rect(name, parent, pos, size).gameObject.AddComponent<Image>(); image.color = color; return image;
    }
    private static Button Button(string label, Transform parent, Vector2 pos, Vector2 size)
    {
        var image = Panel(label, parent, pos, size, mint); var button = image.gameObject.AddComponent<Button>(); button.targetGraphic = image;
        Text(label, image.transform, Vector2.zero, size - new Vector2(12,4), 16, plum, TextAnchor.MiddleCenter); return button;
    }
    private static Image Bar(string name, Transform parent, Vector2 pos, Vector2 size)
    {
        var background = Panel(name, parent, pos, size, new Color(.69f,.27f,.32f));
        var bar = Panel("Remaining", background.transform, Vector2.zero, size, mint); bar.type = Image.Type.Filled; bar.fillMethod = Image.FillMethod.Horizontal; return bar;
    }
    private static TycoonHUD.SlotView Slot(Transform parent, Vector2 pos, Vector2 size)
    {
        var frame = Panel("Item slot", parent, pos, size, plum); var button = frame.gameObject.AddComponent<Button>(); button.targetGraphic = frame;
        return new TycoonHUD.SlotView { button = button, frame = frame, label = Text("Empty", frame.transform, new Vector2(0,4), size - new Vector2(10,18), 14, cream, TextAnchor.MiddleCenter), bar = Bar("Supply", frame.transform, new Vector2(0,-size.y/2+7), new Vector2(size.x-12,5)) };
    }
    private static void MakeHUD()
    {
        var canvas = new GameObject("Tycoon HUD", typeof(RectTransform), typeof(Canvas), typeof(CanvasScaler), typeof(GraphicRaycaster)); canvas.GetComponent<Canvas>().renderMode = RenderMode.ScreenSpaceOverlay;
        var scaler = canvas.GetComponent<CanvasScaler>(); scaler.uiScaleMode = CanvasScaler.ScaleMode.ScaleWithScreenSize; scaler.referenceResolution = new Vector2(1600,900); scaler.screenMatchMode = CanvasScaler.ScreenMatchMode.Expand;
        var ui = canvas.AddComponent<TycoonHUD>(); ui.game = game; game.hud = ui;
        var events = new GameObject("UI input", typeof(EventSystem), typeof(InputSystemUIInputModule));
        Panel("Header", canvas.transform, new Vector2(0,415), new Vector2(1600,70), plum);
        ui.money = Text("Cash", canvas.transform, new Vector2(-420,420), new Vector2(690,45), 25, cream); ui.clock = Text("Clock", canvas.transform, new Vector2(400,420), new Vector2(550,45), 20, cream, TextAnchor.MiddleRight);
        ui.xpBar = Bar("Business XP", canvas.transform, new Vector2(0,383), new Vector2(1600,5));
        ui.notice = Text("Notice", canvas.transform, new Vector2(0,333), new Vector2(1000,66), 22, plum, TextAnchor.MiddleCenter);
        ui.prompt = Text("Interaction", canvas.transform, new Vector2(0,-270), new Vector2(960,70), 21, plum, TextAnchor.MiddleCenter);
        ui.heldLabel = Text("Held item", canvas.transform, new Vector2(0,-327), new Vector2(700,35), 19, plum, TextAnchor.MiddleCenter);
        ui.useBar = Bar("Preparation", canvas.transform, new Vector2(0,-302), new Vector2(220,6));
        ui.targetStockBar = Bar("Target stock", canvas.transform, new Vector2(0,-230), new Vector2(120,7));
        ui.reticle = Text("+", canvas.transform, Vector2.zero, new Vector2(40,40), 24, plum, TextAnchor.MiddleCenter).gameObject;
        ui.orders = Text("Orders", canvas.transform, new Vector2(574,72), new Vector2(385,445), 18, plum, TextAnchor.UpperLeft);
        ui.hotbar = Enumerable.Range(0,8).Select(i => Slot(canvas.transform, new Vector2(-406+i*116,-386), new Vector2(108,74))).ToArray();
        Text("WASD move   E interact   Tab inventory   Hold right-click to pack   M map   Q drop", canvas.transform, new Vector2(0,-438), new Vector2(1200,23), 16, plum, TextAnchor.MiddleCenter);
        var mini = Panel("Minimap", canvas.transform, new Vector2(-667,244), new Vector2(200,200), cream);
        Panel("Street", mini.transform, Vector2.zero, new Vector2(180,12), new Color(.6f,.6f,.65f));
        ui.miniMarker = Panel("You", mini.transform, Vector2.zero, new Vector2(10,10), pink).rectTransform;
        ui.waypointMarker = Panel("Destination", mini.transform, Vector2.zero, new Vector2(8,8), Color.yellow).rectTransform;
        ui.miniLocations = Enumerable.Range(0,6).Select(i => Panel("Place", mini.transform, Vector2.zero, new Vector2(7,7), plum).rectTransform).ToArray();
        ui.waypointText = Text("M / map", canvas.transform, new Vector2(-658,128), new Vector2(240,28), 16, plum, TextAnchor.MiddleCenter);
        ui.panel = Panel("Menu backdrop", canvas.transform, Vector2.zero, new Vector2(1160,720), cream).gameObject;
        ui.panelTitle = Text("Menu", ui.panel.transform, new Vector2(-70,308), new Vector2(960,52), 30, plum);
        ui.closeButton = Button("Close", ui.panel.transform, new Vector2(495,310), new Vector2(115,42));
        ui.panelText = Text("Details", ui.panel.transform, new Vector2(0,235), new Vector2(1080,84), 18, plum, TextAnchor.UpperLeft);
        ui.inventoryPanel = Rect("Inventory", ui.panel.transform, new Vector2(0,-45), new Vector2(1100,490)).gameObject;
        ui.playerSlots = Enumerable.Range(0,8).Select(i => Slot(ui.inventoryPanel.transform, new Vector2(-465 + i%4*155,120-i/4*100), new Vector2(145,90))).ToArray();
        ui.storageSlots = Enumerable.Range(0,12).Select(i => Slot(ui.inventoryPanel.transform, new Vector2(130 + i%3*145,150-i/3*90), new Vector2(135,80))).ToArray();
        ui.cargoButton = Button("Put carried package in storage", ui.inventoryPanel.transform, new Vector2(-245,-130), new Vector2(420,48));
        ui.shopPanel = Rect("Supplier products", ui.panel.transform, new Vector2(0,-60), new Vector2(1100,500)).gameObject;
        ui.supplyButtons = new Button[27];
        for (int i = 0; i < 27; i++)
        {
            string label = i < 12 ? TycoonCatalogSO.FlavorNames[i] + " tub / $" + TycoonCatalogSO.TubPrices[i] : i < 18 ? TycoonCatalogSO.ToppingNames[i-12] + " refill / $" + TycoonCatalogSO.RefillPrices[i-12] : i == 18 ? "Bowl pack / $6" : i == 19 ? "Batter refill / $12" : i == 20 ? "One-swipe scooper / $12" : TycoonCatalogSO.ToppingNames[i-21] + " container / $4";
            ui.supplyButtons[i] = Button(label, ui.shopPanel.transform, new Vector2(-420+i%4*280,190-i/4*55), new Vector2(264,47));
        }
        ui.businessPanel = Rect("Business controls", ui.panel.transform, new Vector2(0,-100), new Vector2(1100,410)).gameObject;
        string[] labels = { "One-swipe scooper / $12", "Small locker / $24", "Upgrade locker", "Waffle station / $90", "Bicycle cargo / $48", "Expand kiosk / $160", "Park stand / $250", "Ice cream truck / $600" };
        ui.upgradeButtons = labels.Select((s,i) => Button(s, ui.businessPanel.transform, new Vector2(-410+i%4*275,80-i/4*60), new Vector2(262,50))).ToArray();
        string[] hires = { "Rookie / $60 + $24 daily", "Experienced / $90 + $42 daily", "Expert / $140 + $66 daily", "Driver / $120 + $60 daily" };
        ui.hireButtons = hires.Select((s,i) => Button(s, ui.businessPanel.transform, new Vector2(-410+i%4*275,-80), new Vector2(262,60))).ToArray();
        ui.mapPanel = Rect("Town map", ui.panel.transform, new Vector2(-180,-80), new Vector2(500,490)).gameObject;
        Panel("Map ground", ui.mapPanel.transform, Vector2.zero, new Vector2(500,490), new Color(.72f,.83f,.66f));
        Panel("Map road", ui.mapPanel.transform, new Vector2(0,-120), new Vector2(470,26), plum);
        Panel("Map road", ui.mapPanel.transform, new Vector2(120,0), new Vector2(26,360), plum);
        ui.mapLocations = Enumerable.Range(0,6).Select(i => Panel("Location marker", ui.mapPanel.transform, Vector2.zero, new Vector2(12,12), pink).rectTransform).ToArray();
        ui.fullMarker = Panel("Player marker", ui.mapPanel.transform, Vector2.zero, new Vector2(13,13), cream).rectTransform;
        string[] places = { "Home stand", "Wholesale supplier", "Park stand", "Playground stop", "Residential stop", "Your bicycle" };
        ui.destinationButtons = places.Select((s,i) => Button(s, ui.mapPanel.transform, new Vector2(520,180-i*66), new Vector2(240,50))).ToArray();
        ui.menuPanel = Rect("Pause controls", ui.panel.transform, new Vector2(0,-120), new Vector2(900,320)).gameObject;
        ui.openButton = Button("Open shop", ui.menuPanel.transform, new Vector2(0,50), new Vector2(400,50));
        ui.saveButton = Button("Save game", ui.menuPanel.transform, new Vector2(0,-10), new Vector2(400,50));
        ui.nextButton = Button("Continue", ui.panel.transform, new Vector2(0,-260), new Vector2(400,50));
        ui.recoveryButton = Button("Supplier recovery job", ui.menuPanel.transform, new Vector2(0,-130), new Vector2(400,50));
        ui.panel.SetActive(false);
    }
}
