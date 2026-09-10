UnityEditor.AssetDatabase.Refresh();
var paths = System.IO.Directory.GetFiles("Assets/Art/Tycoon/Models", "*.fbx");
var results = new System.Collections.Generic.List<object>();
foreach (var path in paths)
{
    var model = UnityEditor.AssetDatabase.LoadAssetAtPath<UnityEngine.GameObject>(path);
    foreach (var r in model.GetComponentsInChildren<UnityEngine.MeshRenderer>())
        if (r.sharedMaterials.Any(m => m.name == "Lit")) results.Add(new { path, r.name, vertices = r.GetComponent<UnityEngine.MeshFilter>().sharedMesh.vertexCount });
}
return results;
