using System;
using System.Linq;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

public static class TycoonHitboxAuthoring
{
    [MenuItem("Ice Cream/Fit equipment hitboxes")]
    public static void Build()
    {
        if (EditorApplication.isPlaying) throw new InvalidOperationException("Stop Play Mode before editing hitboxes.");
        var catalog = AssetDatabase.LoadAssetAtPath<TycoonCatalogSO>("Assets/Art/Tycoon/Catalog.asset");
        foreach (int index in new[] { 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12 })
        {
            var path = AssetDatabase.GetAssetPath(catalog.partPrefabs[index]);
            var root = PrefabUtility.LoadPrefabContents(path);
            try
            {
                FitPart(root.GetComponent<TycoonPart>());
                PrefabUtility.SaveAsPrefabAsset(root, path);
            }
            finally { PrefabUtility.UnloadPrefabContents(root); }
        }
        var scene = UnityEngine.SceneManagement.SceneManager.GetActiveScene();
        var game = scene.GetRootGameObjects().SelectMany(g => g.GetComponents<TycoonGameManager>()).Single();
        foreach (var part in game.parts.Where(p => new[] { 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12 }.Contains(p.catalogIndex))) FitPart(part);
        game.navigation.BuildNavMesh();
        EditorSceneManager.MarkSceneDirty(scene); EditorSceneManager.SaveScene(scene); AssetDatabase.SaveAssets();
    }

    private static void FitPart(TycoonPart part)
    {
        var filters = part.GetComponentsInChildren<MeshFilter>(true);
        if (part.kind == TycoonPart.Kind.Locker)
        {
            // Each upgraded model enables its own collider with its visuals.
            var original = part.GetComponent<BoxCollider>();
            if (original != null) UnityEngine.Object.DestroyImmediate(original);
            foreach (var model in part.lockerModels) Fit(model.transform, model.GetComponentsInChildren<MeshFilter>(true));
        }
        else if (part.kind == TycoonPart.Kind.Iron)
        {
            Fit(part.transform, filters.Where(f => !f.transform.IsChildOf(part.lid)).ToArray());
            Fit(part.lid, part.lid.GetComponentsInChildren<MeshFilter>(true));
        }
        else if (part.kind == TycoonPart.Kind.ServingCounter || part.kind == TycoonPart.Kind.Register)
        {
            // Keep the tabletop collider at counter height; the raised sign needs its own box.
            foreach (Transform child in part.transform)
                if (child != part.transform.GetChild(0) && child.GetComponentsInChildren<MeshFilter>(true).Length > 0)
                    Fit(child, child.GetComponentsInChildren<MeshFilter>(true));
        }
        else if (part.kind == TycoonPart.Kind.BusinessBoard)
        {
            foreach (var filter in filters) Fit(filter.transform, new[] { filter });
        }
        else Fit(part.transform, filters);
    }

    private static void Fit(Transform target, MeshFilter[] filters)
    {
        var points = filters.Where(f => f.sharedMesh != null).SelectMany(f => f.sharedMesh.vertices.Select(v => target.InverseTransformPoint(f.transform.TransformPoint(v)))).ToArray();
        var bounds = new Bounds(points[0], Vector3.zero);
        foreach (var point in points) bounds.Encapsulate(point);
        var box = target.GetComponent<BoxCollider>();
        if (box == null) box = target.gameObject.AddComponent<BoxCollider>();
        box.center = bounds.center;
        box.size = Vector3.Max(bounds.size, Vector3.one * .04f);
        EditorUtility.SetDirty(box);
    }
}
