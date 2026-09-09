using System.Linq;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.UI;

public static class PrototypeWorldUIBuilder
{
    [MenuItem("Ice Cream/Apply scoop and world UI")]
    public static void Apply()
    {
        var r = PrototypeSceneReferences.Instance;
        if (EditorApplication.isPlaying) throw new System.InvalidOperationException("Stop Play Mode before authoring the scene.");
        foreach (var tub in r.tubs)
        {
            if (tub.scoopTop == null)
            {
                var bounds = tub.GetComponent<Collider>().bounds;
                tub.scoopTop = Point(tub.transform, "Scoop top", bounds.center + new Vector3(0, .08f, -.10f));
                tub.scoopBottom = Point(tub.transform, "Scoop bottom", bounds.center + new Vector3(0, .08f, .10f));
            }
            EditorUtility.SetDirty(tub);
        }
        var h = r.hud;
        h.promptText.transform.parent.gameObject.SetActive(false);
        h.heldText.gameObject.SetActive(false);
        h.messageText.gameObject.SetActive(false);
        h.orderText.transform.parent.gameObject.SetActive(false);
        h.waffleText.gameObject.SetActive(false);
        h.drivingText.gameObject.SetActive(false);
        h.progressRing.gameObject.SetActive(false);
        foreach (var text in h.GetComponentsInChildren<Text>(true).Where(t => t.name == "Controls")) text.gameObject.SetActive(false);
        if (r.waffle.GetComponentInChildren<WaffleIndicator>(true) == null) AddWaffleIndicator(r);
        foreach (var flavor in r.customers.flavors)
        {
            string path = "Assets/Art/OrderPictures/" + flavor.displayName + ".png";
            var importer = (TextureImporter)AssetImporter.GetAtPath(path);
            importer.textureType = TextureImporterType.Sprite;
            importer.spriteImportMode = SpriteImportMode.Single;
            importer.mipmapEnabled = false;
            importer.maxTextureSize = 256;
            importer.textureCompression = TextureImporterCompression.Uncompressed;
            importer.SaveAndReimport();
            flavor.orderPicture = AssetDatabase.LoadAllAssetsAtPath(path).OfType<Sprite>().Single();
            EditorUtility.SetDirty(flavor);
        }
        foreach (var prefab in r.customers.customerPrefabs) UpdateOrderBubble(prefab);
        EditorSceneManager.MarkSceneDirty(r.gameObject.scene);
        EditorSceneManager.SaveScene(r.gameObject.scene);
        AssetDatabase.SaveAssets();
    }
    private static Transform Point(Transform parent, string name, Vector3 position)
    {
        var point = new GameObject(name).transform;
        point.SetParent(parent, false);
        point.SetPositionAndRotation(position, parent.rotation * Quaternion.Euler(0, -90, 0));
        return point;
    }
    private static Image Picture(Transform parent, string name, Vector2 position, Vector2 size, Color color, Sprite sprite)
    {
        var go = new GameObject(name, typeof(RectTransform), typeof(Image));
        go.transform.SetParent(parent, false);
        var image = go.GetComponent<Image>();
        image.rectTransform.anchoredPosition = position;
        image.rectTransform.sizeDelta = size;
        image.color = color;
        image.sprite = sprite;
        image.raycastTarget = false;
        return image;
    }
    private static void AddWaffleIndicator(PrototypeSceneReferences r)
    {
        var go = new GameObject("Waffle progress", typeof(RectTransform), typeof(Canvas), typeof(WaffleIndicator));
        go.transform.SetParent(r.waffle.transform, false);
        go.transform.position = r.waffle.GetComponent<Collider>().bounds.center + Vector3.up * .48f;
        go.transform.localScale = Vector3.one * .003f;
        var indicator = go.GetComponent<WaffleIndicator>();
        indicator.waffle = r.waffle; indicator.player = r.interaction;
        indicator.canvas = go.GetComponent<Canvas>(); indicator.canvas.renderMode = RenderMode.WorldSpace;
        indicator.canvas.worldCamera = r.player.view;
        ((RectTransform)go.transform).sizeDelta = new Vector2(90, 90);
        var background = Picture(go.transform, "Progress background", Vector2.zero, new Vector2(90, 90), new Color(.12f,.1f,.17f,.9f), r.hud.progressRing.sprite);
        indicator.panel = background.gameObject;
        indicator.ring = Picture(background.transform, "Progress", Vector2.zero, new Vector2(90, 90), Color.white, r.hud.progressRing.sprite);
        indicator.ring.type = Image.Type.Filled; indicator.ring.fillMethod = Image.FillMethod.Radial360; indicator.ring.fillOrigin = 2;
        indicator.burnRing = Picture(background.transform, "Burn timer", Vector2.zero, new Vector2(112, 112), new Color(.93f, .25f, .23f), r.hud.progressRing.sprite);
        indicator.burnRing.type = Image.Type.Filled; indicator.burnRing.fillMethod = Image.FillMethod.Radial360; indicator.burnRing.fillOrigin = 2;
        indicator.clickIcon = Picture(background.transform, "Mouse", Vector2.zero, new Vector2(19, 29), Color.white, AssetDatabase.GetBuiltinExtraResource<Sprite>("UI/Skin/UISprite.psd"));
        indicator.clickIcon.type = Image.Type.Sliced;
        Picture(indicator.clickIcon.transform, "Left button", new Vector2(-4, 6), new Vector2(5, 9), new Color(.3f,.8f,.52f), null);
        Picture(indicator.clickIcon.transform, "Button divider", new Vector2(0, 6), new Vector2(1, 12), new Color(.12f,.1f,.17f), null);
        indicator.useKey = Picture(background.transform, "E key", Vector2.zero, new Vector2(25, 27), new Color(1, .98f, .91f), AssetDatabase.LoadAssetAtPath<Sprite>("Assets/Art/UI/Soft panel.png")).gameObject;
        var label = new GameObject("Letter", typeof(RectTransform), typeof(Text)).GetComponent<Text>();
        label.transform.SetParent(indicator.useKey.transform, false);
        label.rectTransform.sizeDelta = new Vector2(25, 27);
        label.font = Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");
        label.fontSize = 20; label.fontStyle = FontStyle.Bold; label.alignment = TextAnchor.MiddleCenter;
        label.color = new Color(.15f, .3f, .3f); label.text = "E"; label.raycastTarget = false;
    }
    private static void UpdateOrderBubble(Customer prefab)
    {
        string path = AssetDatabase.GetAssetPath(prefab);
        var go = PrefabUtility.LoadPrefabContents(path);
        try
        {
            var bubble = go.GetComponentInChildren<OrderBubble>(true);
            var panel = bubble.panel.GetComponent<Image>();
            panel.color = Color.white;
            var circle = AssetDatabase.LoadAllAssetsAtPath("Assets/Art/OrderScoop.png").OfType<Sprite>().Single();
            panel.sprite = circle;
            panel.type = Image.Type.Simple;
            panel.rectTransform.sizeDelta = new Vector2(240, 360);
            if (bubble.tail == null)
            {
                bubble.tail = Picture(panel.transform, "Thought bubble tail", new Vector2(0, -193), new Vector2(20, 20), Color.white, circle).gameObject;
                Picture(bubble.tail.transform, "Small bubble", new Vector2(-8, -23), new Vector2(10, 10), Color.white, circle);
            }
            bubble.transform.localScale = Vector3.one * .0022f;
            var serialized = new SerializedObject(bubble);
            serialized.FindProperty("childHeight").floatValue = 2.45f;
            serialized.FindProperty("adultHeight").floatValue = 2.65f;
            serialized.ApplyModifiedPropertiesWithoutUndo();
            foreach (var label in bubble.GetComponentsInChildren<Text>(true)) label.gameObject.SetActive(false);
            for (int i = 0; i < bubble.scoops.Length; i++)
            {
                var image = bubble.scoops[i];
                image.rectTransform.anchoredPosition = new Vector2(0, -65 + i * 85);
                image.rectTransform.sizeDelta = new Vector2(96, 96);
                image.preserveAspect = true;
                image.color = Color.white;
            }
            var cone = bubble.panel.GetComponentsInChildren<Image>(true).Single(i => i.name == "Cone");
            cone.rectTransform.anchoredPosition = new Vector2(0, -125);
            cone.rectTransform.sizeDelta = new Vector2(43, 49);
            bubble.patience.rectTransform.anchoredPosition = new Vector2(0, -158);
            bubble.patience.rectTransform.sizeDelta = new Vector2(84, 5);
            var layout = panel.GetComponent<VerticalLayoutGroup>();
            if (layout == null) layout = panel.gameObject.AddComponent<VerticalLayoutGroup>();
            layout.padding = new RectOffset(30, 30, 20, 30);
            layout.spacing = -10;
            layout.childAlignment = TextAnchor.UpperCenter;
            layout.childControlWidth = layout.childControlHeight = false;
            layout.childForceExpandWidth = layout.childForceExpandHeight = false;
            var fitter = panel.GetComponent<ContentSizeFitter>();
            if (fitter == null) fitter = panel.gameObject.AddComponent<ContentSizeFitter>();
            fitter.verticalFit = ContentSizeFitter.FitMode.PreferredSize;
            for (int i = 0; i < bubble.scoops.Length; i++) bubble.scoops[i].transform.SetSiblingIndex(0);
            cone.transform.SetSiblingIndex(3);
            foreach (var decoration in new[] {bubble.sprinkles, bubble.tail, bubble.patience.gameObject})
            {
                var element = decoration.GetComponent<LayoutElement>();
                if (element == null) element = decoration.AddComponent<LayoutElement>();
                element.ignoreLayout = true;
            }
            var tailRect = (RectTransform)bubble.tail.transform;
            tailRect.anchorMin = tailRect.anchorMax = new Vector2(.5f, 0);
            tailRect.anchoredPosition = new Vector2(0, -13);
            bubble.patience.rectTransform.anchorMin = bubble.patience.rectTransform.anchorMax = new Vector2(.5f, 0);
            bubble.patience.rectTransform.anchoredPosition = new Vector2(0, 18);
            bubble.sprinkles.transform.SetAsLastSibling();
            PrefabUtility.SaveAsPrefabAsset(go, path);
        }
        finally { PrefabUtility.UnloadPrefabContents(go); }
    }
}
