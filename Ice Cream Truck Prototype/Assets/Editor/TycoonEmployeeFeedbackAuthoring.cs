using System;
using System.Linq;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using Object = UnityEngine.Object;

public static class TycoonEmployeeFeedbackAuthoring
{
    public static void Apply()
    {
        if (EditorApplication.isPlaying) throw new InvalidOperationException("Stop Play Mode before authoring.");
        var scene = UnityEngine.SceneManagement.SceneManager.GetActiveScene();
        var game = scene.GetRootGameObjects().SelectMany(o => o.GetComponents<TycoonGameManager>()).Single();
        var board = game.parts.Single(p => p.site == 0 && p.kind == TycoonPart.Kind.BusinessBoard);
        Undo.RecordObject(board.transform, "Move upgrades outside property");
        board.transform.SetPositionAndRotation(game.sites[0].origin.TransformPoint(new Vector3(3, 0, -3.8f)), Quaternion.Euler(0, 180, 0));
        PrefabUtility.RecordPrefabInstancePropertyModifications(board.transform);
        var details = game.hud.employeeDetails;
        details.supportRichText = true; details.fontSize = 16;
        details.rectTransform.sizeDelta = new Vector2(556, 96);
        details.rectTransform.anchoredPosition = new Vector2(0, 146);
        EditorUtility.SetDirty(details); EditorUtility.SetDirty(details.rectTransform);
        game.navigation.BuildNavMesh();
        EditorSceneManager.MarkSceneDirty(scene); EditorSceneManager.SaveScene(scene);
        AssetDatabase.SaveAssets();
    }
    public static void ImportBin()
    {
        const string root = "Assets/Art/Tycoon/";
        AssetDatabase.ImportAsset(root + "Town/Street_bin.fbx", ImportAssetOptions.ForceUpdate);
        var model = Object.Instantiate(AssetDatabase.LoadAssetAtPath<GameObject>(root + "Town/Street_bin.fbx"));
        try
        {
            var prefab = AssetDatabase.LoadAssetAtPath<GameObject>(root + "Prefabs/Town_Street_bin.prefab");
            foreach (var target in prefab.GetComponentsInChildren<MeshFilter>())
            {
                string material = target.GetComponent<Renderer>().sharedMaterial.name;
                var sources = model.GetComponentsInChildren<MeshFilter>().Where(f => string.Concat(f.GetComponent<Renderer>().sharedMaterial.name.Select(c => char.IsLetterOrDigit(c) ? c : '_')) == material).ToArray();
                if (sources.Length == 0) throw new InvalidOperationException("No bin geometry for " + material);
                var mesh = new Mesh { name = System.IO.Path.GetFileNameWithoutExtension(AssetDatabase.GetAssetPath(target.sharedMesh)) };
                mesh.CombineMeshes(sources.Select(f => new CombineInstance { mesh = f.sharedMesh, transform = model.transform.worldToLocalMatrix * f.transform.localToWorldMatrix }).ToArray());
                EditorUtility.CopySerialized(mesh, target.sharedMesh);
                // CopySerialized leaves the old graphics buffer alive in an open Editor.
                target.sharedMesh.vertices = mesh.vertices; target.sharedMesh.normals = mesh.normals;
                target.sharedMesh.triangles = mesh.triangles; target.sharedMesh.UploadMeshData(false);
                EditorUtility.SetDirty(target.sharedMesh);
                Object.DestroyImmediate(mesh);
            }
            AssetDatabase.SaveAssets();
        }
        finally { Object.DestroyImmediate(model); }
    }
}
