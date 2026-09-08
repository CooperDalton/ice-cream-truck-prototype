using System;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.UI;
using Object = UnityEngine.Object;

public static class PrototypeExpansionBuilder
{
    static Font font;
    static Sprite circle, coneSprite;
    static Material grassMaterial;
    [MenuItem("Ice Cream/Add driving and neighborhood")]
    public static void Apply()
    {
        var r = PrototypeSceneReferences.Instance;
        if (r.truck != null) throw new InvalidOperationException("Expansion already authored. Edit its serialized objects directly.");
        font = Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");
        circle = Icon("OrderScoop", false); coneSprite = Icon("OrderCone", true);
        grassMaterial = AssetDatabase.LoadAssetAtPath<Material>("Assets/Art/Materials/Town kit • Grass.mat");
        var originalRoots = r.gameObject.scene.GetRootGameObjects();
        var sunlight = originalRoots.Single(o => o.name == "Afternoon sunlight").GetComponent<Light>();
        var body = originalRoots.Single(o => o.name == "IceCreamTruck");
        var root = new GameObject("Drivable truck");
        var truck = root.AddComponent<TruckController>(); r.truck = truck;
        truck.settings = r.day.settings; truck.day = r.day; truck.player = r.player; truck.customers = r.customers;
        foreach (var go in originalRoots)
        {
            if (go.name.StartsWith("Road_") || go.name.StartsWith("House_") || go.name.StartsWith("Tree_") || go.name == "Park_Cell" || go.name == "Neighborhood ground")
            { Object.DestroyImmediate(go); continue; }
            if (go == r.gameObject || go == r.hud.gameObject || go.name == "UI input" || go.name == "Afternoon sunlight" || go == r.player.gameObject) continue;
            go.transform.SetParent(root.transform, true);
        }
        foreach (var collider in root.GetComponentsInChildren<Collider>(true)) collider.gameObject.layer = 9;
        r.player.transform.SetParent(root.transform, true);
        r.player.truck = truck; r.interaction.truck = truck; r.hud.truck = truck;
        var parts = body.GetComponentsInChildren<Transform>(true).ToDictionary(t => t.name, t => t);
        Vector3 seat = parts["DriverSeat_SOCKET"].position; seat.y = .68f;
        truck.driver = Point(root.transform, "Driver feet", seat, Quaternion.Euler(0, 90, 0));
        truck.kitchen = Point(root.transform, "Kitchen entry", new Vector3(-1.1f, .68f, .05f), Quaternion.Euler(0, 180, 0));
        truck.steeringWheel = parts["SteeringWheel_ROOT"];
        truck.wheels = parts.Values.Where(t => t.name.EndsWith("Wheel_AXLE")).ToArray();
        var seatTarget = new GameObject("Drive the truck"); seatTarget.transform.SetParent(root.transform, false);
        seatTarget.transform.position = truck.steeringWheel.position;
        var seatAction = seatTarget.AddComponent<TruckSeat>(); seatAction.truck = truck;
        seatAction.highlightRenderers = truck.steeringWheel.GetComponentsInChildren<Renderer>();
        seatTarget.AddComponent<BoxCollider>().size = new Vector3(.6f, .6f, .6f);
        r.day.sun = sunlight;
        foreach (var point in r.customers.queuePoints) point.localPosition = new Vector3(point.localPosition.x, 0, 3.15f);
        r.day.settings.secondsPerGameMinute = 12;
        EditorUtility.SetDirty(r.day.settings);
        r.hud.drivingText = Text(r.hud.transform, "Driving controls", new Vector2(0, 285), new Vector2(1100, 35), 20);
        r.hud.resultsButtonText = r.hud.retryButton.GetComponentInChildren<Text>();
        r.hud.clockText.fontSize = 21;
        var controls = r.hud.GetComponentsInChildren<Text>(true).Single(t => t.name == "Controls");
        controls.text = "WASD Walk / drive   Mouse Look   Space Jump / brake\nE Grab / use   Right click Put down   Q Music\nE Driver seat / rear door   Esc Pause";
        var instructions = r.hud.pausePanel.GetComponentsInChildren<Text>(true).Single(t => t.name == "Instructions");
        instructions.text = "E on the seat to drive. WASD to steer, Space to brake. E to stand.\nE opens the rear door. Walk through it. Space to jump.\nPark near people, or carry the boombox and press Q.\nMatch the front customer's picture, then press E to serve.\nIngredients are unlimited. Meet the daily quota by 6 PM.";
        CreateWorld(r);
        CreateBoombox(r);
        r.customers.truck = truck; r.customers.world = r.world; r.customers.boombox = r.boombox; r.customers.view = r.player.view;
        foreach (var prefab in r.customers.customerPrefabs) AddOrderBubble(prefab);
        RefineDrivingView();
        EditorSceneManager.MarkSceneDirty(r.gameObject.scene);
        EditorSceneManager.SaveScene(r.gameObject.scene);
        AssetDatabase.SaveAssets();
    }
    [MenuItem("Ice Cream/Refine driving view")]
    public static void RefineDrivingView()
    {
        var r = PrototypeSceneReferences.Instance;
        foreach (var point in r.customers.queuePoints) point.localPosition = new Vector3(point.localPosition.x, 0, 3.15f);
        r.truck.collisionCenter = new Vector3(.1f, 1.5f, .35f);
        r.truck.collisionHalfSize = new Vector3(3.8f, 1.2f, 2.3f);
        var text = r.hud.drivingText.rectTransform;
        text.anchorMin = text.anchorMax = new Vector2(.5f, 0); text.anchoredPosition = new Vector2(0, 145);
        text.SetSiblingIndex(r.hud.pausePanel.transform.GetSiblingIndex());
        foreach (var material in r.truck.GetComponentsInChildren<Renderer>(true).SelectMany(v => v.sharedMaterials).Distinct().Where(m => m.name.StartsWith("Windows •")))
        {
            material.SetFloat("_Surface", 1); material.SetFloat("_Blend", 0); material.SetFloat("_ZWrite", 0);
            material.SetFloat("_SrcBlend", (float)UnityEngine.Rendering.BlendMode.SrcAlpha);
            material.SetFloat("_DstBlend", (float)UnityEngine.Rendering.BlendMode.OneMinusSrcAlpha);
            material.SetColor("_BaseColor", new Color(.7f, .87f, .95f, .12f));
            material.EnableKeyword("_SURFACE_TYPE_TRANSPARENT"); material.DisableKeyword("_ALPHAPREMULTIPLY_ON");
            material.SetOverrideTag("RenderType", "Transparent"); material.renderQueue = 3000;
            material.SetShaderPassEnabled("ShadowCaster", false); EditorUtility.SetDirty(material);
        }
        foreach (var prefab in r.customers.customerPrefabs)
        {
            string path = AssetDatabase.GetAssetPath(prefab); var go = PrefabUtility.LoadPrefabContents(path);
            try
            {
                var customer = go.GetComponent<Customer>();
                if (customer.servingStep == null)
                {
                    var step = GameObject.CreatePrimitive(PrimitiveType.Cube); step.name = "Child serving step";
                    Object.DestroyImmediate(step.GetComponent<Collider>()); step.transform.SetParent(go.transform, false);
                    step.transform.localPosition = new Vector3(0, .2f, 0); step.transform.localScale = new Vector3(.7f, .4f, .65f);
                    step.GetComponent<Renderer>().sharedMaterial = AssetDatabase.LoadAssetAtPath<Material>("Assets/Art/Materials/Enamel • mint.003.mat");
                    customer.servingStep = step; step.SetActive(false);
                }
                foreach (var bubble in go.GetComponentsInChildren<OrderBubble>(true))
                {
                    bubble.transform.localPosition = new Vector3(0, 2.15f, 0); bubble.transform.localScale = Vector3.one * .0022f;
                }
                PrefabUtility.SaveAsPrefabAsset(go, path);
            }
            finally { PrefabUtility.UnloadPrefabContents(go); }
        }
        EditorSceneManager.MarkSceneDirty(r.gameObject.scene); EditorSceneManager.SaveScene(r.gameObject.scene); AssetDatabase.SaveAssets();
    }
    static Transform Point(Transform parent, string name, Vector3 position, Quaternion rotation)
    {
        var t = new GameObject(name).transform; t.SetParent(parent, false); t.SetPositionAndRotation(position, rotation); return t;
    }
    static Bounds BoundsOf(GameObject go)
    {
        var renderers = go.GetComponentsInChildren<Renderer>(true);
        var bounds = renderers[0].bounds;
        foreach (var renderer in renderers) bounds.Encapsulate(renderer.bounds);
        return bounds;
    }
    static GameObject Save(GameObject go, string name)
    {
        var prefab = PrefabUtility.SaveAsPrefabAsset(go, "Assets/Prefabs/" + name + ".prefab"); Object.DestroyImmediate(go); return prefab;
    }
    static void GroundCollision(GameObject go)
    {
        foreach (var filter in go.GetComponentsInChildren<MeshFilter>(true))
        {
            filter.gameObject.layer = 11;
            var collider = filter.gameObject.AddComponent<MeshCollider>(); collider.sharedMesh = filter.sharedMesh;
        }
    }
    static void BoxObstacle(GameObject root, Bounds bounds)
    {
        var go = new GameObject("Obstacle"); go.layer = 10; go.transform.SetParent(root.transform, true);
        go.transform.position = bounds.center; go.AddComponent<BoxCollider>().size = bounds.size;
    }
    static void CreateWorld(PrototypeSceneReferences r)
    {
        var world = r.gameObject.AddComponent<WorldGenerator>(); r.world = world; world.settings = r.day.settings;
        world.generatedRoot = new GameObject("Generated neighborhood").transform;
        string[] roads = { "Road_Straight_ROOT", "Road_Corner_ROOT", "Road_TJunction_ROOT", "Road_Crossroads_ROOT", "Road_DeadEnd_ROOT" };
        int[] masks = { 5, 12, 13, 15, 1 };
        world.roads = new WorldGenerator.RoadPrefab[roads.Length];
        for (int i = 0; i < roads.Length; i++)
        {
            var go = PrototypeSceneBuilder.ExtractModel(roads[i], Vector3.zero); GroundCollision(go);
            world.roads[i] = new WorldGenerator.RoadPrefab { prefab = Save(go, roads[i]), ports = masks[i] };
        }
        var grass = GameObject.CreatePrimitive(PrimitiveType.Cube); grass.name = "Grass cell"; grass.layer = 11;
        grass.transform.localScale = new Vector3(24, .16f, 24); grass.GetComponent<Renderer>().sharedMaterial = grassMaterial;
        world.grass = Save(grass, "GrassCell");
        var boundary = GameObject.CreatePrimitive(PrimitiveType.Cube); boundary.name = "Town boundary"; boundary.layer = 10;
        boundary.GetComponent<Renderer>().sharedMaterial = grassMaterial; world.boundary = Save(boundary, "TownBoundary");
        var park = PrototypeSceneBuilder.ExtractModel("Park_Cell_ROOT", Vector3.zero); GroundCollision(park);
        foreach (var renderer in park.GetComponentsInChildren<Renderer>())
        {
            var b = renderer.bounds;
            if (b.size.y > .5f && b.size.x < 8 && b.size.z < 8) BoxObstacle(park, b);
        }
        world.park = Save(park, "ParkCell");
        string[] homes = { "House_Cottage_ROOT", "House_Townhouse_ROOT", "House_Bungalow_ROOT", "House_Family_ROOT" };
        world.houses = homes.Select(name => {
            var go = PrototypeSceneBuilder.ExtractModel(name, Vector3.zero); BoxObstacle(go, BoundsOf(go)); return Save(go, name);
        }).ToArray();
        string[] trees = { "Tree_Broadoak_ROOT", "Tree_Roundmaple_ROOT" };
        world.trees = trees.Select(name => {
            var go = PrototypeSceneBuilder.ExtractModel(name, Vector3.zero);
            BoxObstacle(go, new Bounds(new Vector3(0, 1.5f, 0), new Vector3(.7f, 3, .7f))); return Save(go, name);
        }).ToArray();
    }
    static void CreateBoombox(PrototypeSceneReferences r)
    {
        var go = PrototypeSceneBuilder.ExtractModel("Boombox_ROOT", new Vector3(-2.8f, .75f, .8f));
        go.transform.SetParent(r.truck.transform, true);
        var box = go.AddComponent<Boombox>(); r.boombox = box; box.settings = r.day.settings; box.player = r.interaction; box.truck = r.truck;
        box.kind = PickupItem.ItemKind.Boombox; box.displayName = "boombox"; box.highlightRenderers = go.GetComponentsInChildren<Renderer>();
        var bounds = BoundsOf(go); var collider = go.AddComponent<BoxCollider>(); collider.center = go.transform.InverseTransformPoint(bounds.center); collider.size = bounds.size;
        box.pickupCollider = collider;
        box.home = Point(r.truck.transform, "Boombox home", go.transform.position, go.transform.rotation);
        box.heldOffset = new Vector3(0, -.15f, .12f);
        box.music = go.AddComponent<AudioSource>(); box.music.loop = true; box.music.playOnAwake = false; box.music.spatialBlend = 1;
        box.music.minDistance = 3; box.music.maxDistance = r.day.settings.boomboxAttractionRadius; box.music.rolloffMode = AudioRolloffMode.Linear;
        const string path = "Assets/Audio/Boombox.wav";
        const int sampleRate = 22050; int length = sampleRate * 8;
        int[] melody = { 0, 4, 7, 12, 7, 4, 2, 5, 9, 12, 9, 5, 4, 7, 11, 7 };
        using (var writer = new BinaryWriter(File.Create(path)))
        {
            writer.Write(System.Text.Encoding.ASCII.GetBytes("RIFF")); writer.Write(36 + length * 2); writer.Write(System.Text.Encoding.ASCII.GetBytes("WAVEfmt "));
            writer.Write(16); writer.Write((short)1); writer.Write((short)1); writer.Write(sampleRate); writer.Write(sampleRate * 2); writer.Write((short)2); writer.Write((short)16);
            writer.Write(System.Text.Encoding.ASCII.GetBytes("data")); writer.Write(length * 2);
            for (int i = 0; i < length; i++)
            {
                float time = i / (float)sampleRate, beat = time % .5f;
                float hz = 261.63f * Mathf.Pow(2, melody[(int)(time * 2) % melody.Length] / 12f);
                float sample = Mathf.Sin(time * hz * Mathf.PI * 2) * Mathf.Exp(-beat * 8) * .25f * Mathf.Min(1, beat * 100);
                writer.Write((short)(sample * short.MaxValue));
            }
        }
        AssetDatabase.ImportAsset(path); box.music.clip = AssetDatabase.LoadAssetAtPath<AudioClip>(path);
    }
    static Sprite Icon(string name, bool cone)
    {
        const int size = 64; var texture = new Texture2D(size, size, TextureFormat.RGBA32, false);
        for (int y = 0; y < size; y++) for (int x = 0; x < size; x++)
        {
            float px = (x + .5f) / size, py = (y + .5f) / size;
            bool inside = cone ? Mathf.Abs(px - .5f) < py * .46f : Vector2.Distance(new Vector2(px, py), new Vector2(.5f, .5f)) < .49f;
            texture.SetPixel(x, y, inside ? Color.white : Color.clear);
        }
        texture.Apply(); string path = "Assets/Art/" + name + ".png"; File.WriteAllBytes(path, texture.EncodeToPNG()); Object.DestroyImmediate(texture);
        AssetDatabase.ImportAsset(path); var importer = (TextureImporter)AssetImporter.GetAtPath(path);
        importer.textureType = TextureImporterType.Sprite; importer.spriteImportMode = SpriteImportMode.Single; importer.alphaIsTransparency = true; importer.SaveAndReimport();
        return AssetDatabase.LoadAssetAtPath<Sprite>(path);
    }
    static RectTransform Rect(Transform parent, string name, Vector2 position, Vector2 size)
    {
        var rt = new GameObject(name, typeof(RectTransform)).GetComponent<RectTransform>(); rt.SetParent(parent, false);
        rt.anchorMin = rt.anchorMax = new Vector2(.5f, .5f); rt.anchoredPosition = position; rt.sizeDelta = size; return rt;
    }
    static Image Image(Transform parent, string name, Vector2 position, Vector2 size, Color color, Sprite sprite = null)
    {
        var image = Rect(parent, name, position, size).gameObject.AddComponent<Image>(); image.color = color; image.sprite = sprite; image.raycastTarget = false; return image;
    }
    static Text Text(Transform parent, string name, Vector2 position, Vector2 size, int fontSize)
    {
        var text = Rect(parent, name, position, size).gameObject.AddComponent<Text>(); text.font = font; text.fontSize = fontSize;
        text.color = Color.white; text.alignment = TextAnchor.MiddleCenter; text.raycastTarget = false; return text;
    }
    static void AddOrderBubble(Customer prefab)
    {
        string path = AssetDatabase.GetAssetPath(prefab); var go = PrefabUtility.LoadPrefabContents(path); var customer = go.GetComponent<Customer>();
        try
        {
            var canvas = new GameObject("Picture order", typeof(RectTransform), typeof(Canvas));
            canvas.GetComponent<Canvas>().renderMode = RenderMode.WorldSpace; canvas.transform.SetParent(go.transform, false);
            canvas.transform.localPosition = new Vector3(0, 2.15f, 0); canvas.transform.localScale = Vector3.one * .0022f;
            ((RectTransform)canvas.transform).sizeDelta = new Vector2(330, 290);
            var bubble = canvas.AddComponent<OrderBubble>(); bubble.customer = customer;
            var panel = Image(canvas.transform, "Order card", Vector2.zero, new Vector2(330, 290), new Color(.12f, .1f, .17f, .97f)); bubble.panel = panel.gameObject;
            Text(panel.transform, "Title", new Vector2(0, 125), new Vector2(310, 28), 22).text = "MY ORDER";
            Image(panel.transform, "Cone", new Vector2(0, -37), new Vector2(70, 85), new Color(.86f, .59f, .27f), coneSprite);
            bubble.scoops = new Image[3];
            for (int i = 0; i < 3; i++) bubble.scoops[i] = Image(panel.transform, "Scoop " + (i + 1), new Vector2(0, 12 + i * 35), new Vector2(77, 58), Color.white, circle);
            bubble.sprinkles = Rect(panel.transform, "Sprinkles", new Vector2(0, 12), new Vector2(75, 50)).gameObject;
            for (int i = 0; i < 10; i++)
            {
                var sprinkle = Image(bubble.sprinkles.transform, "Sprinkle", new Vector2(-25 + i % 5 * 12, -5 + i / 5 * 15), new Vector2(8, 3), Color.HSVToRGB(i / 10f, .75f, 1));
                sprinkle.transform.localRotation = Quaternion.Euler(0, 0, i * 47);
            }
            bubble.flavors = Text(panel.transform, "Flavor names", new Vector2(0, -99), new Vector2(310, 65), 17);
            bubble.patience = Image(panel.transform, "Patience", new Vector2(0, -138), new Vector2(300, 5), new Color(.4f, .85f, .65f), circle);
            bubble.patience.type = UnityEngine.UI.Image.Type.Filled; bubble.patience.fillMethod = UnityEngine.UI.Image.FillMethod.Horizontal;
            panel.gameObject.SetActive(false);
            PrefabUtility.SaveAsPrefabAsset(go, path);
        }
        finally { PrefabUtility.UnloadPrefabContents(go); }
    }
}
