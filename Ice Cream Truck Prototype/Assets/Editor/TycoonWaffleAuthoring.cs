using System;
using System.Linq;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.SceneManagement;

public static class TycoonWaffleAuthoring
{
    [MenuItem("Ice Cream/Apply tycoon waffle feedback")]
    public static void Apply()
    {
        if (EditorApplication.isPlaying) throw new InvalidOperationException("Stop Play Mode before authoring waffle feedback.");
        var scene = SceneManager.GetActiveScene();
        var game = scene.GetRootGameObjects()[0].GetComponent<TycoonGameManager>();
        var sourceScene = EditorSceneManager.OpenPreviewScene("Assets/Scenes/IceCreamPrototype.unity");
        string path = AssetDatabase.GetAssetPath(game.catalog.partPrefabs[3]);
        var root = PrefabUtility.LoadPrefabContents(path);
        try
        {
            var source = sourceScene.GetRootGameObjects()[0].GetComponent<PrototypeSceneReferences>();
            var iron = root.GetComponent<TycoonPart>();
            if (iron.waffleFeedback != null) UnityEngine.Object.DestroyImmediate(iron.waffleFeedback.gameObject);
            var feedback = new GameObject("Waffle feedback").AddComponent<TycoonWaffleFeedback>();
            feedback.transform.SetParent(iron.transform, false);
            iron.waffleFeedback = feedback; feedback.part = iron;
            feedback.lidAnimationSpeed = source.waffle.settings.lidAnimationSpeed;
            feedback.rawBatter = UnityEngine.Object.Instantiate(source.waffle.rawBatter, feedback.transform).transform;
            feedback.rawBatter.name = "Raw batter";
            feedback.rawBatter.SetLocalPositionAndRotation(iron.contentPoint.localPosition + Vector3.up * .025f, Quaternion.identity);
            feedback.rawBatter.localScale = Vector3.one;
            feedback.rawBatter.gameObject.SetActive(false);
            feedback.cookedWaffle = (GameObject)PrefabUtility.InstantiatePrefab(game.catalog.flatWaffle, feedback.transform);
            feedback.cookedWaffle.transform.localPosition = iron.contentPoint.localPosition;
            feedback.waffleRenderers = feedback.cookedWaffle.GetComponentsInChildren<Renderer>();
            feedback.cookedMaterials = feedback.waffleRenderers.Select(r => r.sharedMaterial).ToArray();
            feedback.burnedMaterial = source.waffle.burnedMaterial;
            feedback.cookedWaffle.SetActive(false);
            feedback.pourStream = feedback.gameObject.AddComponent<LineRenderer>();
            EditorUtility.CopySerialized(source.waffle.pourStream, feedback.pourStream);
            feedback.pourStream.enabled = false;
            feedback.pourSound = source.interaction.pourSound;
            feedback.actionSound = source.interaction.actionSound;
            feedback.readySound = source.interaction.readySound;

            var originalIndicator = source.waffle.GetComponentInChildren<WaffleIndicator>(true);
            var indicator = UnityEngine.Object.Instantiate(originalIndicator, feedback.transform);
            indicator.name = "Waffle progress";
            indicator.transform.SetLocalPositionAndRotation(new Vector3(0, .64f, 0), Quaternion.identity);
            feedback.canvas = indicator.canvas; feedback.canvas.worldCamera = null;
            feedback.panel = indicator.panel; feedback.ring = indicator.ring; feedback.burnRing = indicator.burnRing;
            feedback.clickIcon = indicator.clickIcon.gameObject; feedback.useKey = indicator.useKey;
            feedback.panel.SetActive(false);
            UnityEngine.Object.DestroyImmediate(indicator);
            PrefabUtility.SaveAsPrefabAsset(root, path);

            foreach (var placed in game.parts.Where(p => p.kind == TycoonPart.Kind.Iron))
            {
                if (placed.waffleFeedback != null) UnityEngine.Object.DestroyImmediate(placed.waffleFeedback.gameObject);
                placed.waffleFeedback = UnityEngine.Object.Instantiate(feedback, placed.transform);
                placed.waffleFeedback.name = "Waffle feedback";
                placed.waffleFeedback.part = placed;
                EditorUtility.SetDirty(placed);
            }
            EditorSceneManager.MarkSceneDirty(scene);
            EditorSceneManager.SaveScene(scene);
            AssetDatabase.SaveAssets();
        }
        finally
        {
            PrefabUtility.UnloadPrefabContents(root);
            EditorSceneManager.ClosePreviewScene(sourceScene);
        }
    }
}
