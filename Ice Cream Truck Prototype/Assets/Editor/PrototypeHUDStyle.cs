using System.IO;
using System.Linq;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.UI;

public static class PrototypeHUDStyle
{
    private static readonly Color cream = new Color(1, .98f, .92f);
    private static readonly Color ink = new Color(.16f, .27f, .26f);
    private static readonly Color mint = new Color(.22f, .64f, .49f);
    private static readonly Color coral = new Color(.9f, .39f, .43f);
    private static readonly Color gold = new Color(1, .75f, .27f);
    private static Sprite panelSprite, circleSprite;

    [MenuItem("Ice Cream/Apply illustrated HUD style")]
    public static void Apply()
    {
        var r = PrototypeSceneReferences.Instance;
        var h = r.hud;
        if (EditorApplication.isPlaying) throw new System.InvalidOperationException("Stop Play Mode before styling the HUD.");
        if (h.dayText != null) throw new System.InvalidOperationException("HUD style is already authored. Edit the scene's UI objects directly.");
        Directory.CreateDirectory("Assets/Art/UI");
        panelSprite = Shape("Soft panel", 0);
        circleSprite = Shape("Circle", 1);
        var ring = Shape("Ring", 2);
        var status = (RectTransform)h.clockText.transform.parent;
        status.anchorMin = status.anchorMax = new Vector2(0, 1);
        status.anchoredPosition = new Vector2(315, -77);
        status.sizeDelta = new Vector2(590, 110);
        status.GetComponent<Image>().color = Color.clear;
        Card(status, "Clock card", new Vector2(-150, 0), new Vector2(280, 106));
        Card(status, "Earnings card", new Vector2(145, 0), new Vector2(290, 106));
        h.dayText = status.GetComponentsInChildren<Text>(true).Single(t => t.name == "Title");
        Label(h.dayText, new Vector2(-128, 25), new Vector2(160, 24), 16, mint, TextAnchor.MiddleLeft);
        Label(h.clockText, new Vector2(-116, -10), new Vector2(184, 42), 30, ink, TextAnchor.MiddleLeft);
        Label(h.moneyText, new Vector2(175, 15), new Vector2(180, 40), 32, ink, TextAnchor.MiddleLeft);
        h.quotaText = NewLabel(status, "Daily goal", new Vector2(175, -18), new Vector2(180, 28), 17, ink);
        var face = Picture(status, "Clock icon", new Vector2(-248, 0), new Vector2(57, 57), mint, circleSprite);
        Picture(face.transform, "Clock face", Vector2.zero, new Vector2(44, 44), cream, circleSprite);
        var hour = Picture(face.transform, "Hour hand", new Vector2(-5, 2), new Vector2(16, 5), ink, panelSprite);
        hour.transform.localRotation = Quaternion.Euler(0, 0, -28);
        Picture(face.transform, "Minute hand", new Vector2(0, 9), new Vector2(5, 21), ink, panelSprite);
        Picture(face.transform, "Clock pin", Vector2.zero, new Vector2(7, 7), ink, circleSprite);
        Coin(status, new Vector2(40, 7), 58);
        var track = Picture(status, "Goal track", new Vector2(145, -40), new Vector2(250, 8), new Color(.84f, .91f, .82f), panelSprite);
        h.quotaFill.transform.SetParent(track.transform, false);
        h.quotaFill.rectTransform.anchoredPosition = Vector2.zero;
        h.quotaFill.rectTransform.sizeDelta = track.rectTransform.sizeDelta;
        h.quotaFill.sprite = panelSprite;
        h.quotaFill.color = mint;
        h.quotaFill.type = Image.Type.Filled;
        h.quotaFill.fillMethod = Image.FillMethod.Horizontal;
        StylePause(h);
        StyleResults(h);
        var waffle = r.waffle.GetComponentInChildren<WaffleIndicator>(true);
        waffle.ring.sprite = ring;
        waffle.panel.GetComponent<Image>().sprite = ring;
        foreach (var prefab in r.customers.customerPrefabs)
        {
            string path = AssetDatabase.GetAssetPath(prefab);
            var go = PrefabUtility.LoadPrefabContents(path);
            try
            {
                var bubble = go.GetComponentInChildren<OrderBubble>(true);
                bubble.panel.GetComponent<Image>().sprite = circleSprite;
                foreach (var picture in bubble.tail.GetComponentsInChildren<Image>()) picture.sprite = circleSprite;
                PrefabUtility.SaveAsPrefabAsset(go, path);
            }
            finally { PrefabUtility.UnloadPrefabContents(go); }
        }
        EditorUtility.SetDirty(h);
        EditorSceneManager.MarkSceneDirty(r.gameObject.scene);
        EditorSceneManager.SaveScene(r.gameObject.scene);
        AssetDatabase.SaveAssets();
    }
    private static void StylePause(PrototypeHUD h)
    {
        h.pausePanel.GetComponent<Image>().color = new Color(.14f, .28f, .27f, .52f);
        var title = h.pausePanel.GetComponentsInChildren<Text>(true).Single(t => t.name == "Title");
        var instructions = h.pausePanel.GetComponentsInChildren<Text>(true).Single(t => t.name == "Instructions");
        var card = Card(h.pausePanel.transform, "Pause card", Vector2.zero, new Vector2(760, 620));
        var badge = Picture(card.transform, "Pause badge", new Vector2(0, 226), new Vector2(68, 68), new Color(.8f, .92f, .82f), circleSprite);
        Picture(badge.transform, "Pause left", new Vector2(-9, 0), new Vector2(10, 27), mint, panelSprite);
        Picture(badge.transform, "Pause right", new Vector2(9, 0), new Vector2(10, 27), mint, panelSprite);
        title.transform.SetParent(card.transform, false); title.text = "Taking a break";
        Label(title, new Vector2(0, 155), new Vector2(650, 66), 42, ink, TextAnchor.MiddleCenter);
        instructions.transform.SetParent(card.transform, false);
        instructions.text = "Open the iron. Pour batter. Close and cook.\nPlace your cone, scoop flavors, add sprinkles, then serve.\n\nWASD to move  •  Mouse to look\nE to use  •  Right click to put down\nHold + move up/down to scoop or shake\nE on the seat to drive  •  E on the rear door to open  •  Q for music";
        Label(instructions, new Vector2(0, 4), new Vector2(660, 234), 22, ink, TextAnchor.MiddleCenter);
        instructions.fontStyle = FontStyle.Normal;
        StyleButton(h.resumeButton, card.transform, new Vector2(0, -169), "Back to the truck", mint);
        StyleButton(h.restartButton, card.transform, new Vector2(0, -241), "Restart day", coral);
    }
    private static void StyleResults(PrototypeHUD h)
    {
        h.resultPanel.GetComponent<Image>().color = new Color(.14f, .28f, .27f, .52f);
        var card = Card(h.resultPanel.transform, "Day results card", Vector2.zero, new Vector2(760, 610));
        Coin(card.transform, new Vector2(0, 219), 76);
        h.resultTitleText = NewLabel(card.transform, "Result title", new Vector2(0, 139), new Vector2(680, 65), 38, ink);
        h.resultTitleText.alignment = TextAnchor.MiddleCenter;
        h.resultText.transform.SetParent(card.transform, false);
        Label(h.resultText, new Vector2(0, -5), new Vector2(650, 215), 25, ink, TextAnchor.MiddleCenter);
        h.resultText.fontStyle = FontStyle.Normal;
        StyleButton(h.retryButton, card.transform, new Vector2(0, -221), "Next day", coral);
    }
    private static void StyleButton(Button button, Transform parent, Vector2 position, string caption, Color color)
    {
        button.transform.SetParent(parent, false);
        var image = button.GetComponent<Image>(); image.sprite = panelSprite; image.type = Image.Type.Sliced; image.color = color;
        image.rectTransform.anchoredPosition = position; image.rectTransform.sizeDelta = new Vector2(310, 56);
        var text = button.GetComponentInChildren<Text>(); text.text = caption;
        Label(text, Vector2.zero, new Vector2(292, 50), 23, cream, TextAnchor.MiddleCenter);
        var colors = button.colors; colors.normalColor = Color.white; colors.highlightedColor = new Color(1, .94f, .82f); colors.pressedColor = new Color(.77f,.85f,.79f); button.colors = colors;
    }
    private static Image Card(Transform parent, string name, Vector2 position, Vector2 size)
    {
        var shadow = Picture(parent, name + " shadow", position + Vector2.down * 5, size, new Color(.13f,.35f,.29f,.18f), panelSprite);
        shadow.transform.SetAsFirstSibling();
        var card = Picture(parent, name, position, size, cream, panelSprite);
        card.transform.SetSiblingIndex(1);
        return card;
    }
    private static void Coin(Transform parent, Vector2 position, float size)
    {
        var coin = Picture(parent, "Coin icon", position, Vector2.one * size, gold, circleSprite);
        Picture(coin.transform, "Coin center", Vector2.zero, Vector2.one * size * .76f, new Color(1, .87f, .43f), circleSprite);
        var symbol = NewLabel(coin.transform, "Coin symbol", Vector2.zero, Vector2.one * size, Mathf.RoundToInt(size * .55f), new Color(.64f,.38f,.13f));
        symbol.alignment = TextAnchor.MiddleCenter; symbol.text = "$";
    }
    private static Text NewLabel(Transform parent, string name, Vector2 position, Vector2 size, int fontSize, Color color)
    {
        var go = new GameObject(name, typeof(RectTransform), typeof(Text)); go.transform.SetParent(parent, false);
        var text = go.GetComponent<Text>(); text.font = Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");
        Label(text, position, size, fontSize, color, TextAnchor.MiddleLeft);
        return text;
    }
    private static void Label(Text text, Vector2 position, Vector2 size, int fontSize, Color color, TextAnchor alignment)
    {
        text.rectTransform.anchorMin = text.rectTransform.anchorMax = new Vector2(.5f,.5f);
        text.rectTransform.anchoredPosition = position; text.rectTransform.sizeDelta = size;
        text.fontSize = fontSize; text.fontStyle = FontStyle.Bold; text.color = color; text.alignment = alignment; text.raycastTarget = false;
    }
    private static Image Picture(Transform parent, string name, Vector2 position, Vector2 size, Color color, Sprite sprite)
    {
        var go = new GameObject(name, typeof(RectTransform), typeof(Image)); go.transform.SetParent(parent, false);
        var image = go.GetComponent<Image>(); image.rectTransform.anchoredPosition = position; image.rectTransform.sizeDelta = size;
        image.color = color; image.sprite = sprite; image.type = sprite == panelSprite ? Image.Type.Sliced : Image.Type.Simple; image.raycastTarget = false;
        return image;
    }
    private static Sprite Shape(string name, int kind)
    {
        const int size = 128;
        var texture = new Texture2D(size, size, TextureFormat.RGBA32, false);
        for (int y = 0; y < size; y++) for (int x = 0; x < size; x++)
        {
            var point = new Vector2(x + .5f - size / 2f, y + .5f - size / 2f);
            float distance = kind == 0 ? new Vector2(Mathf.Max(Mathf.Abs(point.x) - 40, 0), Mathf.Max(Mathf.Abs(point.y) - 40, 0)).magnitude - 24 :
                kind == 1 ? point.magnitude - 63 : Mathf.Abs(point.magnitude - 55) - 4;
            texture.SetPixel(x, y, new Color(1, 1, 1, Mathf.Clamp01(.5f - distance)));
        }
        texture.Apply();
        string path = "Assets/Art/UI/" + name + ".png";
        File.WriteAllBytes(path, texture.EncodeToPNG()); Object.DestroyImmediate(texture);
        AssetDatabase.ImportAsset(path);
        var importer = (TextureImporter)AssetImporter.GetAtPath(path);
        importer.textureType = TextureImporterType.Sprite; importer.spriteImportMode = SpriteImportMode.Single;
        importer.spriteBorder = kind == 0 ? Vector4.one * 24 : Vector4.zero;
        importer.alphaIsTransparency = true; importer.mipmapEnabled = false; importer.textureCompression = TextureImporterCompression.Uncompressed;
        importer.SaveAndReimport();
        return AssetDatabase.LoadAllAssetsAtPath(path).OfType<Sprite>().Single();
    }
}
