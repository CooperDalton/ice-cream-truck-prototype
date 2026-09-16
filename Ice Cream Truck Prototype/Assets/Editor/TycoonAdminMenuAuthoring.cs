using System;
using System.Linq;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.UI;

public static class TycoonAdminMenuAuthoring
{
    private static Font font;
    [MenuItem("Ice Cream/Author admin menu")]
    public static void Build()
    {
        if (EditorApplication.isPlaying) throw new InvalidOperationException("Stop Play Mode before authoring the admin menu.");
        var scene = UnityEngine.SceneManagement.SceneManager.GetActiveScene();
        var game = scene.GetRootGameObjects().SelectMany(root => root.GetComponents<TycoonGameManager>()).Single();
        var hud = game.hud;
        if (hud.adminMenu != null) throw new InvalidOperationException("The admin menu is already authored.");
        font = hud.panelTitle.font;
        var menu = hud.gameObject.AddComponent<TycoonAdminMenu>();
        menu.game = game; hud.adminMenu = menu;
        var overlay = new GameObject("Admin menu", typeof(RectTransform), typeof(Image));
        overlay.transform.SetParent(hud.panel.transform.parent, false);
        var rect = (RectTransform)overlay.transform;
        rect.anchorMin = Vector2.zero; rect.anchorMax = Vector2.one; rect.sizeDelta = Vector2.zero;
        overlay.GetComponent<Image>().color = new Color(0, 0, 0, .65f);
        menu.panel = overlay;
        var card = Box("Admin card", overlay.transform, Vector2.zero, new Vector2(620, 510), new Color(.94f, .94f, .88f));
        Label(card.transform, new Vector2(0, 212), new Vector2(570, 42), "Debug / Admin", 30);
        menu.summary = Label(card.transform, new Vector2(0, 169), new Vector2(570, 32), "", 21);
        Label(card.transform, new Vector2(-180, 108), new Vector2(160, 38), "Level (1–7)", 21);
        menu.levelInput = Field(card.transform, new Vector2(-20, 108), "1", InputField.ContentType.IntegerNumber);
        menu.setLevelButton = Button(card.transform, new Vector2(178, 108), "Set level", 170);
        Label(card.transform, new Vector2(-180, 42), new Vector2(160, 38), "Cash amount", 21);
        menu.cashInput = Field(card.transform, new Vector2(-20, 42), "1000", InputField.ContentType.DecimalNumber);
        menu.addCashButton = Button(card.transform, new Vector2(178, 42), "Add cash", 170);
        menu.setCashButton = Button(card.transform, new Vector2(178, -18), "Set cash", 170);
        menu.skipTutorialButton = Button(card.transform, new Vector2(-145, -84), "Skip tutorial", 270);
        menu.finishDayButton = Button(card.transform, new Vector2(145, -84), "Finish day", 270);
        menu.status = Label(card.transform, new Vector2(0, -145), new Vector2(570, 64), "", 18);
        menu.closeButton = Button(card.transform, new Vector2(0, -211), "Close (P / Esc)", 270);
        overlay.SetActive(false);
        EditorUtility.SetDirty(hud); EditorUtility.SetDirty(menu);
        EditorSceneManager.MarkSceneDirty(scene); EditorSceneManager.SaveScene(scene);
        AssetDatabase.SaveAssets();
    }

    private static Image Box(string name, Transform parent, Vector2 position, Vector2 size, Color color)
    {
        var go = new GameObject(name, typeof(RectTransform), typeof(Image));
        go.transform.SetParent(parent, false);
        var image = go.GetComponent<Image>();
        image.rectTransform.anchoredPosition = position; image.rectTransform.sizeDelta = size; image.color = color;
        return image;
    }

    private static Text Label(Transform parent, Vector2 position, Vector2 size, string value, int fontSize)
    {
        var go = new GameObject("Label", typeof(RectTransform), typeof(Text));
        go.transform.SetParent(parent, false);
        var text = go.GetComponent<Text>();
        text.rectTransform.anchoredPosition = position; text.rectTransform.sizeDelta = size;
        text.font = font; text.fontSize = fontSize; text.text = value;
        text.color = new Color(.16f, .2f, .23f); text.alignment = TextAnchor.MiddleCenter; text.raycastTarget = false;
        return text;
    }

    private static Button Button(Transform parent, Vector2 position, string caption, float width)
    {
        var image = Box(caption, parent, position, new Vector2(width, 46), new Color(.66f, .82f, .73f));
        var button = image.gameObject.AddComponent<Button>(); button.targetGraphic = image;
        Label(image.transform, Vector2.zero, new Vector2(width - 12, 42), caption, 21);
        return button;
    }

    private static InputField Field(Transform parent, Vector2 position, string value, InputField.ContentType type)
    {
        var image = Box("Input", parent, position, new Vector2(130, 46), Color.white);
        var field = image.gameObject.AddComponent<InputField>(); field.targetGraphic = image;
        field.textComponent = Label(image.transform, Vector2.zero, new Vector2(116, 42), value, 21);
        field.contentType = type; field.characterLimit = 10; field.text = value;
        return field;
    }
}
