using System;
using System.Collections.Generic;
using System.Linq;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using Object = UnityEngine.Object;

public static class AuthorNeighborhood
{
    private static Dictionary<string, Material> materials;
    public static string Run()
    {
        var r = PrototypeSceneReferences.Instance;
        materials = AssetDatabase.FindAssets("t:Material", new[] { "Assets/Art/Materials" })
            .Select(g => AssetDatabase.LoadAssetAtPath<Material>(AssetDatabase.GUIDToAssetPath(g)))
            .GroupBy(m => m.name).ToDictionary(g => g.Key, g => g.First());
        var model = AssetDatabase.LoadAssetAtPath<GameObject>("Assets/Art/NeighborhoodDetails.fbx");
        var sources = model.GetComponentsInChildren<Transform>(true).Where(t => t.name.EndsWith("_ROOT")).ToArray();
        var prefabs = new Dictionary<string, GameObject>();
        foreach (var source in sources)
        {
            var root = new GameObject(source.name);
            var visual = Object.Instantiate(source.gameObject, root.transform);
            visual.transform.localPosition = Vector3.zero;
            visual.transform.localRotation = source.rotation;
            visual.transform.localScale = source.lossyScale;
            foreach (var renderer in visual.GetComponentsInChildren<MeshRenderer>(true))
            {
                renderer.sharedMaterials = renderer.sharedMaterials.Select(ConvertMaterial).ToArray();
                renderer.gameObject.isStatic = true;
            }
            var renderers = root.GetComponentsInChildren<Renderer>();
            var bounds = renderers[0].bounds;
            foreach (var renderer in renderers) bounds.Encapsulate(renderer.bounds);
            if (source.name.StartsWith("Hill_"))
            {
                foreach (var filter in root.GetComponentsInChildren<MeshFilter>())
                {
                    filter.gameObject.layer = 11;
                    filter.gameObject.AddComponent<MeshCollider>().sharedMesh = filter.sharedMesh;
                }
            }
            else if (!source.name.StartsWith("Shrub_"))
            {
                root.layer = 10;
                var collider = root.AddComponent<BoxCollider>();
                bool tree = source.name.StartsWith("Tree_");
                collider.center = tree ? new Vector3(0, 1.5f, 0) : bounds.center;
                collider.size = tree ? new Vector3(.65f, 3, .65f) : bounds.size;
            }
            prefabs[source.name] = PrefabUtility.SaveAsPrefabAsset(root, "Assets/Prefabs/" + source.name + ".prefab");
            Object.DestroyImmediate(root);
        }
        var trees = r.world.trees.ToList();
        foreach (string name in new[] { "Tree_Slenderpoplar_ROOT", "Tree_Tieredpine_ROOT" })
        {
            var root = PrototypeSceneBuilder.ExtractModel(name, Vector3.zero);
            root.layer = 10;
            var collider = root.AddComponent<BoxCollider>();
            collider.center = new Vector3(0, 1.5f, 0); collider.size = new Vector3(.65f, 3, .65f);
            trees.Add(PrefabUtility.SaveAsPrefabAsset(root, "Assets/Prefabs/" + name + ".prefab"));
            Object.DestroyImmediate(root);
        }
        trees.AddRange(prefabs.Where(p => p.Key.StartsWith("Tree_")).Select(p => p.Value));
        r.world.trees = trees.Distinct().ToArray();
        r.world.houses = r.world.houses.Concat(prefabs.Where(p => p.Key.StartsWith("House_")).Select(p => p.Value)).Distinct().ToArray();
        r.world.rocks = prefabs.Where(p => p.Key.StartsWith("Rock_")).Select(p => p.Value).ToArray();
        r.world.shrubs = prefabs.Where(p => p.Key.StartsWith("Shrub_")).Select(p => p.Value).ToArray();
        r.world.hills = prefabs.Where(p => p.Key.StartsWith("Hill_")).Select(p => p.Value).ToArray();
        r.world.settings.junctionsPerSide = 9;
        r.world.settings.customerAreaSpacing = 96;
        r.world.settings.residentsPerHotspot = 6;
        RenderSettings.fogStartDistance = 140;
        RenderSettings.fogEndDistance = 430;
        r.player.view.farClipPlane = 600;
        EditorUtility.SetDirty(r.world.settings);
        EditorSceneManager.MarkSceneDirty(r.gameObject.scene);
        EditorSceneManager.SaveScene(r.gameObject.scene);
        AssetDatabase.SaveAssets();
        return "Saved 408m town: " + r.world.trees.Length + " tree variants, " + r.world.houses.Length + " house variants, " + r.world.rocks.Length + " rocks, " + r.world.shrubs.Length + " shrubs, " + r.world.hills.Length + " hills.";
    }
    private static Material ConvertMaterial(Material source)
    {
        if (materials.TryGetValue(source.name, out var material)) return material;
        material = new Material(Shader.Find("Universal Render Pipeline/Lit"));
        material.name = source.name;
        material.color = source.color;
        material.SetFloat("_Smoothness", .15f);
        AssetDatabase.CreateAsset(material, "Assets/Art/Materials/" + material.name + ".mat");
        materials.Add(material.name, material);
        return material;
    }
}
