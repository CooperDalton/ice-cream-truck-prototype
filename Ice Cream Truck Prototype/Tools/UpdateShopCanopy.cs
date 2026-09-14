// Run after exporting the canopy: unity command eval_file Tools/UpdateShopCanopy.cs
if (EditorApplication.isPlaying) throw new Exception("Stop Play Mode before updating the canopy.");
const string folder = "Assets/Art/Tycoon/";
AssetDatabase.ImportAsset(folder + "Models/Pop_up_canopy.fbx", ImportAssetOptions.ForceSynchronousImport);
var model = AssetDatabase.LoadAssetAtPath<GameObject>(folder + "Models/Pop_up_canopy.fbx");
var prefab = AssetDatabase.LoadAssetAtPath<GameObject>(folder + "Prefabs/Pop_up_canopy.prefab");
var groups = new System.Collections.Generic.Dictionary<Material, System.Collections.Generic.List<CombineInstance>>();
foreach (var filter in model.GetComponentsInChildren<MeshFilter>(true))
{
    var materials = filter.GetComponent<Renderer>().sharedMaterials;
    for (int i = 0; i < filter.sharedMesh.subMeshCount; i++)
    {
        var name = string.Concat(materials[i].name.Select(c => char.IsLetterOrDigit(c) ? c : '_'));
        var material = AssetDatabase.LoadAssetAtPath<Material>(folder + "Materials/" + name + ".mat");
        if (!groups.ContainsKey(material)) groups.Add(material, new System.Collections.Generic.List<CombineInstance>());
        groups[material].Add(new CombineInstance {
            mesh = filter.sharedMesh, subMeshIndex = i,
            transform = model.transform.worldToLocalMatrix * filter.transform.localToWorldMatrix
        });
    }
}
foreach (var filter in prefab.GetComponentsInChildren<MeshFilter>(true))
{
    var mesh = filter.sharedMesh;
    mesh.Clear();
    mesh.indexFormat = UnityEngine.Rendering.IndexFormat.UInt32;
    mesh.CombineMeshes(groups[filter.GetComponent<Renderer>().sharedMaterial].ToArray(), true, true);
    EditorUtility.SetDirty(mesh);
    AssetDatabase.SaveAssetIfDirty(mesh);
}
var scene = UnityEngine.SceneManagement.SceneManager.GetActiveScene();
var game = scene.GetRootGameObjects()[0].GetComponent<TycoonGameManager>();
var results = new System.Collections.Generic.List<string>();
foreach (var site in game.sites.Take(2))
{
    Undo.RecordObject(site.canopy.transform, "Center shop canopy");
    site.canopy.transform.SetPositionAndRotation(site.origin.position, site.origin.rotation);
    PrefabUtility.RecordPrefabInstancePropertyModifications(site.canopy.transform);
    var bounds = new Bounds();
    bool first = true;
    foreach (var filter in site.canopy.GetComponentsInChildren<MeshFilter>(true))
        foreach (var vertex in filter.sharedMesh.vertices)
        {
            var point = site.origin.InverseTransformPoint(filter.transform.TransformPoint(vertex));
            if (first) { bounds = new Bounds(point, Vector3.zero); first = false; }
            else bounds.Encapsulate(point);
        }
    if (bounds.min.x > -site.plotSize.x / 2 || bounds.max.x < site.plotSize.x / 2 ||
        bounds.min.z > -site.plotSize.y / 2 || bounds.max.z < site.plotSize.y / 2)
        throw new Exception(site.name + " canopy does not cover the plot: " + bounds);
    results.Add(site.name + ": plot " + site.plotSize + ", canopy bounds " + bounds);
}
UnityEditor.SceneManagement.EditorSceneManager.MarkSceneDirty(scene);
UnityEditor.SceneManagement.EditorSceneManager.SaveScene(scene);
return results.ToArray();
