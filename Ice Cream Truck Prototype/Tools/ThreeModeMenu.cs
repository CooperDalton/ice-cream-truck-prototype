using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using UnityEditor;
using UnityEditor.Events;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.SceneManagement;
using UnityEngine.UI;

public static class ThreeModeMenu
{
    public static string Apply()
    {
        if (UnityEngine.SceneManagement.SceneManager.GetActiveScene().isDirty)
            throw new InvalidOperationException("Save the open scene before updating the mode menu.");
        var scene = EditorSceneManager.OpenScene("Assets/Scenes/MainMenu.unity");
        GlobalObjectId.TryParse("GlobalObjectId_V1-2-8543112568d0346838e5966a086fd866-649090835-0", out var id);
        var menu = (GameModeMenu)GlobalObjectId.GlobalObjectIdentifierToObjectSlow(id);
        var freeCard = (RectTransform)menu.freeDriveButton.transform.parent;
        var routeCard = (RectTransform)menu.parkRouteButton.transform.parent;
        RectTransform tycoonCard;
        if (menu.tycoonButton == null)
        {
            tycoonCard = UnityEngine.Object.Instantiate(freeCard, freeCard.parent);
            tycoonCard.name = "Tycoon card";
            menu.tycoonButton = tycoonCard.GetChild(2).GetComponent<Button>();
            menu.tycoonButton.name = "Play Tycoon";
            menu.tycoonButton.onClick = new Button.ButtonClickedEvent();
            UnityEventTools.AddPersistentListener(menu.tycoonButton.onClick, menu.Tycoon);
        }
        else tycoonCard = (RectTransform)menu.tycoonButton.transform.parent;
        tycoonCard.GetComponent<Image>().color = new Color(.98f, .90f, .66f);
        tycoonCard.GetChild(1).GetComponent<Text>().text = "Tycoon";
        tycoonCard.GetChild(0).GetComponent<Image>().sprite = AssetDatabase.LoadAssetAtPath<Sprite>("Assets/Art/OrderPictures/Chocolate.png");
        var cards = new[] { tycoonCard, freeCard, routeCard };
        for (int i = 0; i < cards.Length; i++)
        {
            cards[i].sizeDelta = new Vector2(430, 330);
            cards[i].anchoredPosition = new Vector2((i - 1) * 470, -50);
            cards[i].GetChild(1).GetComponent<RectTransform>().sizeDelta = new Vector2(390, 69);
        }
        var scenes = EditorBuildSettings.scenes.ToList();
        scenes.RemoveAll(s => s.path == "Assets/Scenes/MainMenu.unity");
        scenes.Insert(0, new EditorBuildSettingsScene("Assets/Scenes/MainMenu.unity", true));
        EditorBuildSettings.scenes = scenes.ToArray();
        EditorSceneManager.playModeStartScene = AssetDatabase.LoadAssetAtPath<SceneAsset>(scene.path);
        EditorSceneManager.MarkSceneDirty(scene);
        EditorSceneManager.SaveScene(scene);
        AssetDatabase.SaveAssets();
        return "MainMenu launches first with Tycoon, Free drive, and Park route buttons.";
    }

    public static async Task<string> Verify()
    {
        var checks = new List<string>();
        var expectedScenes = new[] { "IceCreamPrototype", "ParkRoute", "IceCreamTycoon" };
        if (EditorBuildSettings.scenes.First(s => s.enabled).path != "Assets/Scenes/MainMenu.unity")
            throw new Exception("MainMenu must be the first build scene.");
        for (int i = 0; i < expectedScenes.Length; i++)
        {
            for (int frame = 0; frame < 10; frame++) await Awaitable.NextFrameAsync();
            if (SceneManager.GetActiveScene().name != "MainMenu" || Time.timeScale != 1)
                throw new Exception("Expected the home screen with normal time.");
            var menu = GameModeMenu.Instance;
            var buttons = new[] { menu.freeDriveButton, menu.parkRouteButton, menu.tycoonButton };
            Canvas.ForceUpdateCanvases();
            if (i == 0) ScreenCapture.CaptureScreenshot("Library/CodexPlaytests/three-mode-menu.png");
            var button = buttons[i];
            var pointer = new PointerEventData(EventSystem.current)
            {
                position = RectTransformUtility.WorldToScreenPoint(null, button.transform.position),
                button = PointerEventData.InputButton.Left
            };
            var hits = new List<RaycastResult>();
            EventSystem.current.RaycastAll(pointer, hits);
            if (hits.Count == 0 || hits[0].gameObject != button.gameObject)
                throw new Exception("Pointer cannot reach " + button.name);
            ExecuteEvents.Execute(button.gameObject, pointer, ExecuteEvents.pointerClickHandler);
            for (int frame = 0; frame < 15; frame++) await Awaitable.NextFrameAsync();
            if (SceneManager.GetActiveScene().name != expectedScenes[i])
                throw new Exception(button.name + " loaded the wrong scene.");
            checks.Add("Pointer click loaded " + expectedScenes[i]);
            if (i == 0 && PrototypeSceneReferences.Instance.truck.automaticRoute)
                throw new Exception("Free drive must use manual driving.");
            if (i == 1 && !PrototypeSceneReferences.Instance.route.MapOpen)
                throw new Exception("Park route must open route planning.");
            if (i < 2) PrototypeSceneReferences.Instance.GetComponent<GameModeMenu>().ReturnToMenu();
        }
        var game = TycoonGameManager.Instance;
        game.restartRequested = true;
        if (game.day != 1 || game.level != 1 || game.cash != 100)
            throw new Exception("Tycoon did not start with a fresh campaign.");
        checks.Add("Tycoon starts on day 1, level 1, with $100.");
        string result = string.Join("\n", checks);
        System.IO.File.WriteAllText("Library/CodexPlaytests/three-mode-menu.txt", result);
        return result;
    }
}
