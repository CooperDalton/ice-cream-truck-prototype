using System;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.UI;
using Object = UnityEngine.Object;

public static class TycoonTutorialAuthoring
{
    private const string Folder = "Assets/Art/Tycoon/Tutorial";
    private static readonly Color Yellow = new Color(1, .84f, .25f);
    private static Font font;
    private static Sprite panel;

    [MenuItem("Ice Cream/Author visual tutorial")]
    public static void Build()
    {
        if (EditorApplication.isPlaying) throw new InvalidOperationException("Stop Play Mode before authoring the tutorial.");
        var scene = UnityEngine.SceneManagement.SceneManager.GetActiveScene();
        var game = scene.GetRootGameObjects()[0].GetComponent<TycoonGameManager>();
        if (game.tutorial != null)
        {
            Object.DestroyImmediate(game.tutorial.uiRoot);
            Object.DestroyImmediate(game.tutorial.gameObject);
        }
        Directory.CreateDirectory(Folder); AssetDatabase.Refresh();
        font = game.hud.money.font; panel = game.hud.salePopupBackground.sprite;
        var outline = SpriteAsset("Highlight", false);
        var arrow = SpriteAsset("Arrow", true);
        var ghostMaterial = MaterialAsset("Placement target", new Color(.2f, .92f, 1, .42f));
        var focusMaterial = MaterialAsset("Object highlight", new Color(1, .85f, .2f, .3f));
        var root = new GameObject("Visual tutorial"); root.transform.SetParent(game.transform, false);
        var tutorial = root.AddComponent<TycoonTutorial>(); game.tutorial = tutorial; tutorial.game = game;
        tutorial.playerSpawn = Point("Player start", root.transform, game.sites[0].origin.TransformPoint(new Vector3(0, 0, -2.4f)));
        Vector3[] positions = {
            new Vector3(-1, 0, 0), new Vector3(2.75f, 0, 2.5f), new Vector3(-1.5f, 0, 2.5f),
            new Vector3(.25f, 0, .25f), new Vector3(.75f, 0, .25f), new Vector3(-3.5f, 0, .25f)
        };
        int[] prefabs = { 0, 10, 7, 1, 1, 8 };
        for (int i = 0; i < positions.Length; i++)
            positions[i] = TycoonBuilder.SnapToGrid(positions[i], game.catalog.partPrefabs[prefabs[i]].footprint, Quaternion.identity, .5f);
        tutorial.placementSpots = new Transform[6]; tutorial.placementGhosts = new GameObject[6];
        for (int i = 0; i < 6; i++)
        {
            var spot = Point("Placement " + (i + 1), root.transform, game.sites[0].origin.TransformPoint(positions[i]));
            spot.rotation = game.sites[0].origin.rotation; tutorial.placementSpots[i] = spot;
            tutorial.placementGhosts[i] = Ghost(game.catalog.placementPreviews[prefabs[i]], spot, ghostMaterial);
        }
        tutorial.bowlSpot = Point("Bowl placement", root.transform, game.sites[0].origin.TransformPoint(positions[0] + new Vector3(.375f, .94f, .125f)));
        tutorial.bowlGhost = Ghost(game.catalog.placementPreviews[game.builder.bowlPrefab.catalogIndex], tutorial.bowlSpot, ghostMaterial);
        var focus = new GameObject("Highlighted object", typeof(MeshFilter), typeof(MeshRenderer)); focus.transform.SetParent(root.transform, false);
        tutorial.focusMesh = focus.GetComponent<MeshFilter>(); focus.GetComponent<MeshRenderer>().sharedMaterial = focusMaterial;
        focus.GetComponent<MeshRenderer>().shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
        focus.GetComponent<MeshRenderer>().receiveShadows = false; focus.SetActive(false);
        var ui = new GameObject("Tutorial guidance", typeof(RectTransform), typeof(CanvasGroup)); ui.transform.SetParent(game.hud.transform, false);
        var rect = (RectTransform)ui.transform; rect.anchorMin = Vector2.zero; rect.anchorMax = Vector2.one; rect.sizeDelta = Vector2.zero;
        ui.GetComponent<CanvasGroup>().blocksRaycasts = false; ui.GetComponent<CanvasGroup>().interactable = false; tutorial.uiRoot = ui;
        tutorial.slotHighlight = Picture("Inventory slot highlight", ui.transform, Vector2.zero, new Vector2(108, 108), Yellow, outline).rectTransform;
        tutorial.buttonHighlight = Picture("Button highlight", ui.transform, Vector2.zero, new Vector2(200, 60), Yellow, outline).rectTransform;
        var cue = new GameObject("Target cue", typeof(RectTransform)); cue.transform.SetParent(ui.transform, false);
        tutorial.worldCue = (RectTransform)cue.transform; tutorial.worldCue.sizeDelta = new Vector2(48, 58);
        var pointer = Picture("Direction arrow", cue.transform, Vector2.zero, new Vector2(44, 54), Yellow, arrow);
        pointer.type = Image.Type.Simple; tutorial.worldArrow = pointer.rectTransform;
        var shadow = pointer.gameObject.AddComponent<Shadow>(); shadow.effectColor = new Color(.12f, .1f, .17f, .8f); shadow.effectDistance = new Vector2(2, -3);
        var instruction = Picture("Next action", ui.transform, new Vector2(0, 145), new Vector2(300, 72), new Color(.16f, .13f, .21f, .92f), panel);
        instruction.rectTransform.anchorMin = instruction.rectTransform.anchorMax = new Vector2(.5f, 0);
        tutorial.instructionPanel = instruction.rectTransform;
        tutorial.itemIcon = Picture("Item", instruction.transform, new Vector2(-109, 0), new Vector2(48, 48), Color.white, game.catalog.bowlIcon);
        tutorial.itemIcon.type = Image.Type.Simple; tutorial.itemIcon.preserveAspect = true;
        var key = Picture("Input key", instruction.transform, new Vector2(-43, 0), new Vector2(64, 42), new Color(1, .97f, .85f), panel);
        tutorial.input = Label("Input", key.transform, Vector2.zero, new Vector2(60, 38), 21, new Color(.2f, .16f, .24f));
        tutorial.caption = Label("Action", instruction.transform, new Vector2(67, 0), new Vector2(140, 44), 23, Color.white);
        var swipe = new GameObject("Swipe motion", typeof(RectTransform)); swipe.transform.SetParent(instruction.transform, false);
        tutorial.swipeHint = (RectTransform)swipe.transform; tutorial.swipeHint.sizeDelta = new Vector2(28, 60);
        var up = Picture("Swipe up", swipe.transform, new Vector2(0, 16), new Vector2(20, 24), Yellow, arrow); up.type = Image.Type.Simple; up.transform.localRotation = Quaternion.Euler(0, 0, 180);
        Picture("Swipe down", swipe.transform, new Vector2(0, -16), new Vector2(20, 24), Yellow, arrow).type = Image.Type.Simple;
        ui.SetActive(false);
        AddNavigation();
        EditorUtility.SetDirty(game); EditorUtility.SetDirty(tutorial);
        EditorSceneManager.MarkSceneDirty(scene); EditorSceneManager.SaveScene(scene); AssetDatabase.SaveAssets();
    }
    [MenuItem("Ice Cream/Author tutorial supply route")]
    public static void AddNavigation()
    {
        var scene = UnityEngine.SceneManagement.SceneManager.GetActiveScene();
        var game = scene.GetRootGameObjects()[0].GetComponent<TycoonGameManager>();
        var tutorial = game.tutorial;
        font = game.hud.money.font; panel = game.hud.salePopupBackground.sprite;
        if (tutorial.destinationPanel == null)
        {
            var card = Picture("Destination", tutorial.uiRoot.transform, new Vector2(0, 145), new Vector2(230, 60), new Color(.16f, .13f, .21f, .92f), panel);
            tutorial.destinationPanel = card.rectTransform;
            card.rectTransform.anchorMin = card.rectTransform.anchorMax = new Vector2(.5f, 0);
            tutorial.destinationCaption = Label("Destination text", card.transform, Vector2.zero, new Vector2(210, 50), 23, Color.white);
            card.gameObject.SetActive(false);
        }
        if (tutorial.supplyRoute != null) Object.DestroyImmediate(tutorial.supplyRoute);
        tutorial.supplyRoute = new GameObject("Street arrows to supplies");
        tutorial.supplyRoute.transform.SetParent(tutorial.transform, false);
        var routeMaterial = MaterialAsset("Supply route", new Color(1, .82f, .12f, 1));
        routeMaterial.shader = Shader.Find("Universal Render Pipeline/Unlit"); routeMaterial.SetFloat("_Cull", 0);
        tutorial.supplyDestination = game.parts.Single(p => p.kind == TycoonPart.Kind.Supplier).transform;
        string meshPath = Folder + "/Supply arrow.asset";
        var mesh = AssetDatabase.LoadAssetAtPath<Mesh>(meshPath);
        if (mesh == null) { mesh = new Mesh { name = "Ground direction arrow" }; AssetDatabase.CreateAsset(mesh, meshPath); }
        mesh.Clear();
        mesh.vertices = new[] { new Vector3(-.16f,0,-.65f), new Vector3(.16f,0,-.65f), new Vector3(.16f,0,0), new Vector3(.48f,0,0), new Vector3(0,0,.75f), new Vector3(-.48f,0,0), new Vector3(-.16f,0,0) };
        mesh.triangles = new[] { 0,6,1, 1,6,2, 6,5,4, 6,4,2, 2,4,3 };
        mesh.RecalculateNormals(); mesh.RecalculateBounds(); EditorUtility.SetDirty(mesh);
        float streetZ = game.hud.roadCenters[0].z;
        var end = tutorial.supplyDestination.position + Vector3.forward * .8f;
        var entrance = game.supplier.position + Vector3.forward * 2.4f;
        // Start inside the shop's clear aisle, between the pickup and order counters.
        var shopStart = game.sites[0].origin.TransformPoint(new Vector3(.75f, 0, .75f));
        var points = new[] { shopStart, new Vector3(shopStart.x,0,streetZ), new Vector3(entrance.x,0,streetZ), entrance, end };
        var arrows = new System.Collections.Generic.List<Transform>();
        for (int segment = 0; segment < points.Length - 1; segment++)
        {
            var direction = (points[segment + 1] - points[segment]).normalized;
            float distance = Vector3.Distance(points[segment], points[segment + 1]);
            int count = Mathf.CeilToInt(distance / 2.4f);
            for (int i = 0; i < count; i++)
            {
                var arrow = new GameObject("Street arrow " + (arrows.Count + 1), typeof(MeshFilter), typeof(MeshRenderer));
                arrow.transform.SetParent(tutorial.supplyRoute.transform, false);
                var position = points[segment] + direction * ((i + .5f) * distance / count);
                if (Physics.Raycast(position + Vector3.up * 3, Vector3.down, out var ground, 6)) position.y = ground.point.y;
                arrow.transform.SetPositionAndRotation(position + Vector3.up * .06f, Quaternion.LookRotation(direction));
                arrow.GetComponent<MeshFilter>().sharedMesh = mesh;
                var renderer = arrow.GetComponent<MeshRenderer>(); renderer.sharedMaterial = routeMaterial;
                renderer.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off; renderer.receiveShadows = false;
                arrows.Add(arrow.transform);
            }
        }
        tutorial.supplyRouteArrows = arrows.ToArray(); tutorial.supplyRoute.SetActive(false);
        EditorUtility.SetDirty(tutorial); EditorSceneManager.MarkSceneDirty(scene); EditorSceneManager.SaveScene(scene); AssetDatabase.SaveAssets();
    }
    private static Transform Point(string name, Transform parent, Vector3 position)
    {
        var point = new GameObject(name).transform; point.SetParent(parent, false); point.position = position;
        return point;
    }
    private static GameObject Ghost(GameObject prefab, Transform parent, Material material)
    {
        var ghost = (GameObject)PrefabUtility.InstantiatePrefab(prefab, parent);
        ghost.transform.localPosition = Vector3.zero; ghost.transform.localRotation = Quaternion.identity;
        foreach (var renderer in ghost.GetComponentsInChildren<Renderer>()) renderer.sharedMaterial = material;
        ghost.SetActive(false); return ghost;
    }
    private static Image Picture(string name, Transform parent, Vector2 position, Vector2 size, Color color, Sprite sprite)
    {
        var image = new GameObject(name, typeof(RectTransform), typeof(Image)).GetComponent<Image>(); image.transform.SetParent(parent, false);
        image.rectTransform.anchoredPosition = position; image.rectTransform.sizeDelta = size; image.color = color;
        image.sprite = sprite; image.type = Image.Type.Sliced; image.raycastTarget = false; return image;
    }
    private static Text Label(string name, Transform parent, Vector2 position, Vector2 size, int fontSize, Color color)
    {
        var text = new GameObject(name, typeof(RectTransform), typeof(Text)).GetComponent<Text>(); text.transform.SetParent(parent, false);
        text.rectTransform.anchoredPosition = position; text.rectTransform.sizeDelta = size; text.font = font;
        text.fontSize = fontSize; text.color = color; text.alignment = TextAnchor.MiddleCenter; text.raycastTarget = false; return text;
    }
    private static Material MaterialAsset(string name, Color color)
    {
        string path = Folder + "/" + name + ".mat";
        var material = AssetDatabase.LoadAssetAtPath<Material>(path);
        if (material == null) { material = new Material(Shader.Find("Ice Cream/Placement Ghost")); AssetDatabase.CreateAsset(material, path); }
        material.SetColor("_BaseColor", color); EditorUtility.SetDirty(material); return material;
    }
    private static Sprite SpriteAsset(string name, bool arrow)
    {
        var texture = new Texture2D(64, 64, TextureFormat.RGBA32, false);
        for (int y = 0; y < 64; y++) for (int x = 0; x < 64; x++)
        {
            float dx = Mathf.Abs(x - 31.5f), dy = Mathf.Abs(y - 31.5f);
            bool painted;
            if (arrow) painted = y < 34 ? dx < y * .8f : dx < 9;
            else
            {
                float outer = new Vector2(Mathf.Max(0, dx - 20), Mathf.Max(0, dy - 20)).magnitude;
                painted = outer <= 11 && (dx > 27 || dy > 27 || outer >= 7);
            }
            texture.SetPixel(x, y, painted ? Color.white : Color.clear);
        }
        texture.Apply(); string path = Folder + "/" + name + ".png"; File.WriteAllBytes(path, texture.EncodeToPNG()); Object.DestroyImmediate(texture);
        AssetDatabase.ImportAsset(path); var importer = (TextureImporter)AssetImporter.GetAtPath(path);
        importer.textureType = TextureImporterType.Sprite; importer.spriteImportMode = SpriteImportMode.Single;
        importer.alphaIsTransparency = true; importer.mipmapEnabled = false; importer.spriteBorder = arrow ? Vector4.zero : new Vector4(14, 14, 14, 14);
        importer.SaveAndReimport(); return AssetDatabase.LoadAssetAtPath<Sprite>(path);
    }
}
