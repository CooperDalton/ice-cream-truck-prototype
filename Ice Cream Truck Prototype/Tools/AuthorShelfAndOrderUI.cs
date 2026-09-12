using System;
using System.Linq;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.UI;
using Object = UnityEngine.Object;

public static class AuthorShelfAndOrderUI
{
    private static readonly Color Ink = new Color(.24f, .20f, .29f);
    private static readonly Color Muted = new Color(.49f, .43f, .40f);
    private static readonly Color Mint = new Color(.43f, .72f, .64f);
    private static Sprite paper, coin;
    private static Font font;

    public static string Build()
    {
        if (EditorApplication.isPlaying) throw new Exception("Stop Play Mode before authoring UI");
        var scene = UnityEngine.SceneManagement.SceneManager.GetActiveScene();
        var game = scene.GetRootGameObjects()[0].GetComponent<TycoonGameManager>();
        var hud = game.hud;
        paper = hud.moneyDisplay.parent.GetComponent<Image>().sprite;
        coin = hud.moneyDisplay.GetChild(0).GetComponent<Image>().sprite;
        font = hud.money.font;
        Undo.RegisterFullObjectHierarchyUndo(hud.gameObject, "Restyle shelf and order cards");
        if (hud.shelfPanel != null) Object.DestroyImmediate(hud.shelfPanel);
        var overlay = CreateImage("Shelf overlay", hud.transform, Vector2.zero, Vector2.zero, new Color(.12f,.10f,.16f,.56f));
        overlay.rectTransform.anchorMin = Vector2.zero; overlay.rectTransform.anchorMax = Vector2.one;
        overlay.rectTransform.sizeDelta = Vector2.zero; overlay.raycastTarget = true;
        overlay.transform.SetSiblingIndex(hud.hotbar[0].frame.transform.GetSiblingIndex());
        hud.shelfPanel = overlay.gameObject;
        var window = CreateImage("Shelf window", overlay.transform, new Vector2(0,70), new Vector2(760,400), new Color(1,.97f,.90f), paper);
        window.raycastTarget = true;
        CreateText("Shelf title", window.transform, new Vector2(-220,174), new Vector2(260,42), "Shelf", 32, Ink);
        hud.shelfCloseButton = CreateButton("Close shelf", window.transform, new Vector2(302,174), new Vector2(92,38), "Close");
        CreateImage("Shelf divider", window.transform, new Vector2(0,135), new Vector2(696,1), new Color(.48f,.40f,.32f,.18f));
        hud.shelfSlots = new TycoonHUD.SlotView[TycoonPart.ShelfCapacity];
        for (int i = 0; i < hud.shelfSlots.Length; i++)
        {
            var position = new Vector2(-280 + i % 6 * 112, 63 - i / 6 * 112);
            CreateImage("Slot surround " + (i + 1), window.transform, position, new Vector2(100,100), new Color(.65f,.77f,.69f,.45f), paper);
            var frame = CreateImage("Shelf slot " + (i + 1), window.transform, position, new Vector2(96,96), Color.white, paper);
            frame.raycastTarget = true;
            var button = frame.gameObject.AddComponent<Button>(); button.targetGraphic = frame; button.transition = Selectable.Transition.ColorTint;
            var colors = button.colors; colors.highlightedColor = new Color(.81f,.94f,.87f); colors.pressedColor = Mint; button.colors = colors;
            var icon = CreateImage("Item", frame.transform, new Vector2(0,7), new Vector2(70,70), Color.white); icon.preserveAspect = true;
            var count = CreateText("Quantity", frame.transform, new Vector2(12,-26), new Vector2(54,26), "", 19, Ink); count.alignment = TextAnchor.MiddleRight;
            var track = CreateImage("Supply track", frame.transform, new Vector2(0,-39), new Vector2(66,4), new Color(.37f,.33f,.29f,.13f));
            var fill = CreateImage("Supply", track.transform, Vector2.zero, new Vector2(66,4), Mint);
            fill.sprite = hud.hotbar[0].bar.sprite; fill.type = Image.Type.Filled; fill.fillMethod = Image.FillMethod.Horizontal; fill.fillOrigin = 0;
            hud.shelfSlots[i] = new TycoonHUD.SlotView { button = button, frame = frame, icon = icon, label = count, bar = fill };
            icon.gameObject.SetActive(false); track.gameObject.SetActive(false);
        }
        hud.shelfStatus = CreateText("Shelf status", window.transform, new Vector2(0,-154), new Vector2(696,30), "", 18, Muted);
        hud.shelfStatus.alignment = TextAnchor.MiddleCenter;
        foreach (var slot in hud.hotbar.Concat(hud.playerSlots).Concat(hud.storageSlots))
        {
            slot.label.rectTransform.anchoredPosition = new Vector2(8,-20);
            slot.label.rectTransform.sizeDelta = new Vector2(40,22);
            slot.label.fontSize = 15; slot.label.color = Ink; slot.label.alignment = TextAnchor.MiddleRight;
            slot.label.transform.SetAsLastSibling();
        }
        for (int i = 0; i < hud.tickets.Length; i++)
        {
            var card = hud.tickets[i];
            var rect = (RectTransform)card.root.transform;
            rect.anchorMin = rect.anchorMax = rect.pivot = Vector2.one;
            rect.anchoredPosition = new Vector2(-24,-120-i*140); rect.sizeDelta = new Vector2(330,124);
            var background = card.root.GetComponent<Image>(); background.sprite = paper; background.type = Image.Type.Sliced; background.color = new Color(1,.97f,.90f); background.raycastTarget = false;
            card.description.text = ""; card.description.gameObject.SetActive(false);
            card.title.fontSize = 24; card.title.color = Ink; card.title.alignment = TextAnchor.MiddleRight; card.title.text = "6";
            Place(card.title.rectTransform, new Vector2(112,36), new Vector2(62,32));
            if (card.coin == null) card.coin = CreateImage("Order coin", rect, Vector2.zero, new Vector2(24,24), Color.white, coin);
            Place(card.coin.rectTransform, new Vector2(67,36), new Vector2(24,24)); card.coin.preserveAspect = true;
            var price = card.coin.transform.parent == rect ? new GameObject("Price", typeof(RectTransform), typeof(HorizontalLayoutGroup), typeof(ContentSizeFitter)).GetComponent<RectTransform>() : (RectTransform)card.coin.transform.parent;
            price.SetParent(rect, false); Place(price, new Vector2(144,36), new Vector2(80,32)); price.pivot = new Vector2(1,.5f);
            var priceLayout = price.GetComponent<HorizontalLayoutGroup>(); priceLayout.spacing = 7; priceLayout.childAlignment = TextAnchor.MiddleRight;
            priceLayout.childControlWidth = true; priceLayout.childControlHeight = false; priceLayout.childForceExpandWidth = priceLayout.childForceExpandHeight = false;
            price.GetComponent<ContentSizeFitter>().horizontalFit = ContentSizeFitter.FitMode.PreferredSize;
            card.coin.transform.SetParent(price, false); card.title.transform.SetParent(price, false);
            var coinSize = card.coin.GetComponent<LayoutElement>(); if (coinSize == null) coinSize = card.coin.gameObject.AddComponent<LayoutElement>(); coinSize.preferredWidth = 24;
            if (card.ingredients == null) card.ingredients = new GameObject("Ingredients", typeof(RectTransform), typeof(HorizontalLayoutGroup)).GetComponent<RectTransform>();
            card.ingredients.SetParent(rect, false); Place(card.ingredients, new Vector2(0,-17), new Vector2(294,66));
            var layout = card.ingredients.GetComponent<HorizontalLayoutGroup>(); layout.spacing = 3; layout.childAlignment = TextAnchor.MiddleLeft;
            layout.childControlWidth = layout.childControlHeight = false; layout.childForceExpandWidth = layout.childForceExpandHeight = false;
            foreach (var picture in new[] { card.container }.Concat(card.flavors).Concat(card.toppings))
            {
                picture.transform.SetParent(card.ingredients, false); picture.rectTransform.sizeDelta = new Vector2(56,62); picture.preserveAspect = true; picture.raycastTarget = false;
            }
            card.root.SetActive(false);
        }
        foreach (var shelf in game.parts.Where(p => p.kind == TycoonPart.Kind.Shelf)) Array.Resize(ref shelf.storage.slots, TycoonPart.ShelfCapacity);
        var prefabPath = AssetDatabase.GetAssetPath(game.catalog.partPrefabs.Single(p => p.kind == TycoonPart.Kind.Shelf));
        var prefab = PrefabUtility.LoadPrefabContents(prefabPath);
        try
        {
            Array.Resize(ref prefab.GetComponent<TycoonPart>().storage.slots, TycoonPart.ShelfCapacity);
            PrefabUtility.SaveAsPrefabAsset(prefab, prefabPath);
        }
        finally { PrefabUtility.UnloadPrefabContents(prefab); }
        hud.shelfPanel.SetActive(false);
        EditorUtility.SetDirty(hud); EditorSceneManager.MarkSceneDirty(scene); EditorSceneManager.SaveScene(scene);
        return "Authored shelf overlay, 12 clickable slots, hotbar quantities, and compact order cards with coin prices.";
    }

    private static void Place(RectTransform rect, Vector2 position, Vector2 size)
    {
        rect.anchorMin = rect.anchorMax = rect.pivot = new Vector2(.5f,.5f);
        rect.anchoredPosition = position; rect.sizeDelta = size;
    }
    private static Image CreateImage(string name, Transform parent, Vector2 position, Vector2 size, Color color, Sprite sprite = null)
    {
        var image = new GameObject(name, typeof(RectTransform), typeof(Image)).GetComponent<Image>();
        image.transform.SetParent(parent, false); Place(image.rectTransform, position, size);
        image.sprite = sprite; image.type = sprite == null ? UnityEngine.UI.Image.Type.Simple : UnityEngine.UI.Image.Type.Sliced;
        image.color = color; image.raycastTarget = false;
        return image;
    }
    private static Text CreateText(string name, Transform parent, Vector2 position, Vector2 size, string value, int fontSize, Color color)
    {
        var text = new GameObject(name, typeof(RectTransform), typeof(Text)).GetComponent<Text>();
        text.transform.SetParent(parent, false); Place(text.rectTransform, position, size);
        text.font = font; text.fontSize = fontSize; text.text = value; text.color = color; text.alignment = TextAnchor.MiddleLeft; text.raycastTarget = false;
        return text;
    }
    private static Button CreateButton(string name, Transform parent, Vector2 position, Vector2 size, string label)
    {
        var image = CreateImage(name, parent, position, size, Mint, paper); image.raycastTarget = true;
        var button = image.gameObject.AddComponent<Button>(); button.targetGraphic = image;
        var text = CreateText("Label", image.transform, Vector2.zero, size, label, 17, Ink); text.alignment = TextAnchor.MiddleCenter;
        return button;
    }
}
