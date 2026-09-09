using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.UI;

public static class AuthorCrowdControls
{
    public static string Run()
    {
        foreach (string name in new[] { "IceCreamPrototype", "ParkRoute" })
        {
            var scene = EditorSceneManager.OpenScene("Assets/Scenes/" + name + ".unity");
            var r = PrototypeSceneReferences.Instance;
            r.boombox.settings.boomboxAttractionRadius = 55;
            r.boombox.settings.customerQueueRadius = 12;
            r.boombox.settings.residentSpreadRadius = 9;
            r.boombox.music.maxDistance = 55;
            EditorUtility.SetDirty(r.boombox.settings);
            foreach (var root in scene.GetRootGameObjects())
            foreach (var label in root.GetComponentsInChildren<Text>(true))
            {
                label.text = label.text.Replace("Right click drops", "Q drops").Replace("Q switches music", "B switches music");
                if (name == "IceCreamPrototype" && label.text == "Q") label.text = "B";
            }
            EditorSceneManager.MarkSceneDirty(scene);
            EditorSceneManager.SaveScene(scene);
        }
        AssetDatabase.SaveAssets();
        EditorSceneManager.OpenScene("Assets/Scenes/IceCreamPrototype.unity");
        return "Saved Q drop / B music instructions in both scenes and wider crowd attraction settings.";
    }
}
