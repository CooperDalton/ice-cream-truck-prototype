using System.Linq;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.UI;

public static class PauseMenuBuilder
{
    private static readonly Color Ink = new Color(.18f, .29f, .28f);
    private static readonly Color Mint = new Color(.34f, .67f, .57f);
    private static Sprite panelSprite;
    private static Font font;

    [MenuItem("Tools/Prototype/Update pause menus")]
    public static void Build()
    {
        panelSprite = AssetDatabase.LoadAssetAtPath<Sprite>("Assets/Art/UI/Soft panel.png");
        foreach (string sceneName in new[] { "IceCreamPrototype", "ParkRoute" })
        {
            var scene = EditorSceneManager.OpenScene("Assets/Scenes/" + sceneName + ".unity");
            var r = PrototypeSceneReferences.Instance;
            bool route = sceneName == "ParkRoute";
            var panel = route ? r.hud.routeHUD.pausePanel : r.hud.pausePanel;
            var title = panel.GetComponentsInChildren<Text>(true).Single(t => t.text == "Taking a break");
            font = title.font;
            var card = (RectTransform)title.transform.parent;
            var buttons = panel.GetComponentsInChildren<Button>(true);
            title.transform.SetParent(panel.transform, false);
            foreach (var button in buttons) button.transform.SetParent(panel.transform, false);
            foreach (Transform child in card.Cast<Transform>().ToArray()) Object.DestroyImmediate(child.gameObject);
            card.anchoredPosition = new Vector2(375, 0);
            card.sizeDelta = new Vector2(470, 700);
            foreach (var shadow in panel.GetComponentsInChildren<Image>(true).Where(i => i.name == "Pause card shadow").ToArray()) Object.DestroyImmediate(shadow.gameObject);
            title.transform.SetParent(card, false);
            title.rectTransform.anchoredPosition = new Vector2(0, 260);
            title.rectTransform.sizeDelta = new Vector2(430, 65);
            title.fontSize = 34;
            for (int i = 0; i < buttons.Length; i++)
            {
                buttons[i].transform.SetParent(card, false);
                ((RectTransform)buttons[i].transform).anchoredPosition = new Vector2(0, -115 - i * 76);
            }
            Label(card, "Settings", "SETTINGS", new Vector2(0, 198), new Vector2(380, 35), 18);
            Label(card, "Sensitivity label", "Mouse sensitivity", new Vector2(-35, 152), new Vector2(300, 40), 24);
            var value = Label(card, "Sensitivity value", "1.0x", new Vector2(160, 152), new Vector2(70, 40), 22);
            var track = Picture(card, "Mouse sensitivity", new Vector2(0, 116), new Vector2(360, 24), new Color(.83f, .87f, .8f));
            var slider = track.gameObject.AddComponent<Slider>();
            var handle = Picture(track.transform, "Handle", Vector2.zero, new Vector2(26, 38), Mint);
            slider.handleRect = handle.rectTransform;
            slider.targetGraphic = handle;
            slider.minValue = .01f;
            slider.maxValue = .5f;
            slider.value = r.player.settings.mouseSensitivity;
            var settings = card.gameObject.GetComponent<PauseSettings>();
            if (settings == null) settings = card.gameObject.AddComponent<PauseSettings>();
            settings.player = r.player;
            settings.sensitivity = slider;
            settings.sensitivityValue = value;
            settings.musicVolume = VolumeSlider(card, "Music", 59, out settings.musicValue);
            settings.effectsVolume = VolumeSlider(card, "Sound effects", -24, out settings.effectsValue);

            var oldHelp = panel.GetComponentsInChildren<Image>(true).SingleOrDefault(i => i.name == "Quick guide");
            if (oldHelp != null) Object.DestroyImmediate(oldHelp.gameObject);
            var help = Picture(panel.transform, "Quick guide", new Vector2(-260, 0), new Vector2(750, 700), new Color(1, .98f, .92f));
            Label(help.transform, "Guide title", "A little help behind the counter", new Vector2(0, 287), new Vector2(680, 50), 30);
            Row(help.transform, 0, "CLICK", "Bake a cone", "Click to open / close the iron with batter in hand.\nHold left click to pour. Close the lid to cook.", "Assets/Art/OrderCone.png");
            Row(help.transform, 1, "HOLD", "Scoop & sprinkle", "Hold left click and move the mouse up / down\nto scoop ice cream or shake sprinkles.", "Assets/Art/OrderScoop.png");
            Row(help.transform, 2, "CLICK", "Finish & serve", "Click to pick up tools, place cones, or serve.\nQ places on a green preview, or drops from your hand.", "Assets/Art/OrderPictures/Strawberry.png");
            Row(help.transform, 3, "E", "Use the truck", route ? "E opens the rear door. Carry cones on the tray.\nBoard the truck to bank the cash you earned outside." : "E opens doors or takes the driver seat.\nPark, then press E to stand up.", null);
            Row(help.transform, 4, route ? "M / R" : "CLICK", route ? "Plan & rescue" : "Music on the road", route ? "M opens the map and stock shop. R calls a rescue stop.\nThe map stays live; this pause menu stops the clocks." : "Click to pick up the boombox and start its music.\nQ puts it down. The music keeps attracting people.", null);
            EditorSceneManager.MarkSceneDirty(scene);
            EditorSceneManager.SaveScene(scene);
        }
    }

    private static Slider VolumeSlider(Transform parent, string name, float y, out Text value)
    {
        Label(parent, name + " label", name, new Vector2(-35, y), new Vector2(300, 35), 24);
        value = Label(parent, name + " value", "100%", new Vector2(160, y), new Vector2(75, 35), 22);
        var track = Picture(parent, name + " volume", new Vector2(0, y - 35), new Vector2(360, 24), new Color(.83f, .87f, .8f));
        var slider = track.gameObject.AddComponent<Slider>();
        var handle = Picture(track.transform, "Handle", Vector2.zero, new Vector2(26, 32), Mint);
        slider.handleRect = handle.rectTransform;
        slider.targetGraphic = handle;
        slider.value = 1;
        return slider;
    }

    private static void Row(Transform parent, int index, string key, string title, string body, string iconPath)
    {
        float y = 181 - index * 108;
        var badge = Picture(parent, title + " icon", new Vector2(-308, y), new Vector2(72, 78), new Color(.87f, .93f, .85f));
        if (iconPath != null)
        {
            var icon = Picture(badge.transform, "Illustration", new Vector2(0, 8), new Vector2(46, 46), Color.white);
            icon.sprite = AssetDatabase.LoadAssetAtPath<Sprite>(iconPath);
            if (iconPath.EndsWith("OrderCone.png")) icon.color = new Color(.78f, .49f, .23f);
            if (iconPath.EndsWith("OrderScoop.png")) icon.color = Mint;
            icon.preserveAspect = true;
            Label(badge.transform, "Input", key, new Vector2(0, -25), new Vector2(70, 20), 12);
        }
        else Label(badge.transform, "Key", key, Vector2.zero, new Vector2(72, 50), 24);
        var heading = Label(parent, title, title, new Vector2(40, y + 25), new Vector2(560, 32), 24);
        heading.alignment = TextAnchor.MiddleLeft;
        var text = Label(parent, title + " details", body, new Vector2(40, y - 16), new Vector2(560, 55), 18);
        text.alignment = TextAnchor.MiddleLeft;
    }

    private static Image Picture(Transform parent, string name, Vector2 position, Vector2 size, Color color)
    {
        var go = new GameObject(name, typeof(RectTransform), typeof(CanvasRenderer), typeof(Image));
        go.transform.SetParent(parent, false);
        var image = go.GetComponent<Image>();
        image.rectTransform.anchoredPosition = position;
        image.rectTransform.sizeDelta = size;
        image.sprite = panelSprite;
        image.type = Image.Type.Sliced;
        image.color = color;
        return image;
    }

    private static Text Label(Transform parent, string name, string content, Vector2 position, Vector2 size, int fontSize)
    {
        var go = new GameObject(name, typeof(RectTransform), typeof(CanvasRenderer), typeof(Text));
        go.transform.SetParent(parent, false);
        var text = go.GetComponent<Text>();
        text.rectTransform.anchoredPosition = position;
        text.rectTransform.sizeDelta = size;
        text.font = font;
        text.fontSize = fontSize;
        text.text = content;
        text.color = Ink;
        text.alignment = TextAnchor.MiddleCenter;
        text.raycastTarget = false;
        return text;
    }
}
