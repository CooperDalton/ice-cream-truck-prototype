using System;
using System.Linq;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.UI;

public static class SimplifyRouteHUD
{
    public static string Run()
    {
        if (UnityEditor.EditorApplication.isPlaying) throw new Exception("Stop Play Mode before editing the scene.");
        var original = UnityEngine.SceneManagement.SceneManager.GetActiveScene();
        if (original.isDirty) EditorSceneManager.SaveScene(original);
        var scene = EditorSceneManager.OpenScene("Assets/Scenes/ParkRoute.unity");
        var r = PrototypeSceneReferences.Instance;
        var h = r.route.hud;
        h.clock.gameObject.SetActive(false);
        h.nextStop.gameObject.SetActive(false);
        var card = h.GetComponentsInChildren<Image>(true).Single(i => i.name == "Route clock card");
        card.gameObject.SetActive(false);
        var instructions = r.hud.GetComponentsInChildren<Text>(true).Single(t => t.name == "Instructions");
        instructions.gameObject.SetActive(false);
        EditorSceneManager.MarkSceneDirty(scene);
        EditorSceneManager.SaveScene(scene);
        if (h.clock.gameObject.activeSelf || h.nextStop.gameObject.activeSelf || card.gameObject.activeSelf || instructions.gameObject.activeSelf)
            throw new Exception("Removed route UI is still active.");
        return "Saved ParkRoute: clock, departure countdown, card background and legacy waffle tutorial inactive. Map and stock UI retained.";
    }
}
