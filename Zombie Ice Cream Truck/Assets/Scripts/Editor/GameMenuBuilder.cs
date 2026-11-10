using System.Linq;
using UnityEditor;
using UnityEditor.Events;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.InputSystem.UI;
using UnityEngine.SceneManagement;
using UnityEngine.UI;

// Builds the main menu scene (Tools > Build Main Menu) in the game's candy pixel style: single player or multiplayer
// (GameMenu), and puts it first in the build so builds open on it.
public static class GameMenuBuilder
{
    const string ScenePath = "Assets/Scenes/MainMenu.unity";
    const string Sprites = "Assets/Art/Sprites/DadsHUD";
    const string GameName = "Big Milk Strikes Back";
    const string GameScene = "Assets/QuantumUser/Scenes/DivorcedDads.unity";
    static readonly Color Ink = new Color(0.11f, 0.06f, 0.2f);

    [MenuItem("Tools/Build Main Menu")]
    public static void Build()
    {
        EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
        var camera = new GameObject("Camera").AddComponent<Camera>();
        camera.clearFlags = CameraClearFlags.SolidColor;
        camera.backgroundColor = Ink;
        new GameObject("Event System", typeof(EventSystem), typeof(InputSystemUIInputModule));
        var canvasObject = new GameObject("Menu", typeof(Canvas), typeof(CanvasScaler), typeof(GraphicRaycaster));
        var canvas = canvasObject.GetComponent<Canvas>();
        canvas.renderMode = RenderMode.ScreenSpaceCamera;
        canvas.worldCamera = camera;
        canvas.planeDistance = 1;
        var scaler = canvasObject.GetComponent<CanvasScaler>();
        scaler.uiScaleMode = CanvasScaler.ScaleMode.ScaleWithScreenSize;
        scaler.referenceResolution = new Vector2(1280, 720);
        var root = canvasObject.transform;
        var title = AssetDatabase.LoadAssetAtPath<Font>("Assets/Art/Fonts/PressStart2P-Regular.ttf");
        var menu = canvasObject.AddComponent<GameMenu>();

        var banner = Frame(root, "Banner", "banner", new Vector2(0, 250), new Vector2(900, 48), Image.Type.Tiled);
        Label(banner.transform, "Title", title, 28, Color.white, Vector2.zero, GameName.ToUpper());

        var single = Button(root, "Single Player", title, 18, new Vector2(-240, -20), new Vector2(420, 140), "SINGLE PLAYER");
        UnityEventTools.AddBoolPersistentListener(single.onClick, menu.Play, false);
        var multi = Button(root, "Multiplayer", title, 18, new Vector2(240, -20), new Vector2(420, 140), "MULTIPLAYER");
        UnityEventTools.AddBoolPersistentListener(multi.onClick, menu.Play, true);

        var serialized = new SerializedObject(menu);
        serialized.FindProperty("gameName").stringValue = GameName;
        serialized.FindProperty("gameScene").stringValue = GameScene;
        serialized.ApplyModifiedPropertiesWithoutUndo();

        System.IO.Directory.CreateDirectory("Assets/Scenes");
        EditorSceneManager.SaveScene(SceneManager.GetActiveScene(), ScenePath);
        EditorBuildSettings.scenes = new[] { new EditorBuildSettingsScene(ScenePath, true) }
            .Concat(EditorBuildSettings.scenes.Where(s => s.path != ScenePath)).ToArray();
        Debug.Log("GameMenuBuilder: built the main menu");
    }

    // A nine-slice HUD frame (drawn twice its pixel size, like the in-game HUD) centered at a position.
    static Image Frame(Transform parent, string name, string sprite, Vector2 position, Vector2 size, Image.Type type)
    {
        var image = new GameObject(name, typeof(RectTransform), typeof(Image)).GetComponent<Image>();
        image.transform.SetParent(parent, false);
        image.rectTransform.anchoredPosition = position;
        image.rectTransform.sizeDelta = size;
        image.sprite = AssetDatabase.LoadAssetAtPath<Sprite>($"{Sprites}/{sprite}.png");
        image.type = type;
        image.pixelsPerUnitMultiplier = 0.5f;
        return image;
    }

    static Text Label(Transform parent, string name, Font font, int size, Color color, Vector2 position, string text)
    {
        var label = new GameObject(name, typeof(RectTransform), typeof(Text), typeof(Outline)).GetComponent<Text>();
        label.transform.SetParent(parent, false);
        label.rectTransform.anchoredPosition = position;
        label.rectTransform.sizeDelta = new Vector2(1000, 80);
        label.font = font;
        label.fontSize = size;
        label.color = color;
        label.alignment = TextAnchor.MiddleCenter;
        label.horizontalOverflow = HorizontalWrapMode.Overflow;
        label.raycastTarget = false;
        label.text = text;
        label.GetComponent<Outline>().effectColor = Ink;
        return label;
    }

    static Button Button(Transform parent, string name, Font font, int size, Vector2 position, Vector2 boxSize, string text)
    {
        var frame = Frame(parent, name, "panel", position, boxSize, Image.Type.Sliced);
        var button = frame.gameObject.AddComponent<Button>();
        var colors = button.colors;
        colors.highlightedColor = new Color(1f, 0.75f, 0.9f);
        colors.pressedColor = new Color(0.8f, 0.6f, 1f);
        button.colors = colors;
        var label = Label(frame.transform, "Label", font, size, Color.white, Vector2.zero, text);
        label.rectTransform.sizeDelta = boxSize - new Vector2(24, 24);
        label.horizontalOverflow = HorizontalWrapMode.Wrap;
        label.lineSpacing = 1.6f;
        return button;
    }
}
