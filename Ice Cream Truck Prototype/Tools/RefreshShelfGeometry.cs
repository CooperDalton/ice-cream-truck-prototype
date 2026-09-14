// Run after exporting the shelf without its label: unity command eval_file Tools/RefreshShelfGeometry.cs.
if (EditorApplication.isPlaying) throw new Exception("Stop Play Mode before refreshing shelf geometry.");
const string modelPath="Assets/Art/Tycoon/Models/Pickup_shelf.fbx";
AssetDatabase.ImportAsset(modelPath,ImportAssetOptions.ForceSynchronousImport);
var source=AssetDatabase.LoadAssetAtPath<GameObject>(modelPath);
if (source.GetComponentsInChildren<MeshFilter>().Any(f=>f.name.StartsWith("Rack name"))) throw new Exception("Shelf export still contains the label.");
var catalog=AssetDatabase.LoadAssetAtPath<TycoonCatalogSO>("Assets/Art/Tycoon/Catalog.asset");
var shelf=catalog.partPrefabs[8];
foreach (var target in shelf.GetComponentsInChildren<MeshFilter>())
{
    var material=target.GetComponent<Renderer>().sharedMaterial;
    var pieces=new System.Collections.Generic.List<CombineInstance>();
    foreach (var filter in source.GetComponentsInChildren<MeshFilter>())
    {
        var materials=filter.GetComponent<Renderer>().sharedMaterials;
        for(int i=0;i<materials.Length;i++)
        {
            var name=string.Concat(materials[i].name.Select(c=>char.IsLetterOrDigit(c)?c:'_'));
            if(name==material.name) pieces.Add(new CombineInstance {mesh=filter.sharedMesh,subMeshIndex=i,transform=target.transform.worldToLocalMatrix*filter.transform.localToWorldMatrix});
        }
    }
    if(pieces.Count==0) throw new Exception("No shelf geometry for "+material.name);
    target.sharedMesh.Clear(); target.sharedMesh.CombineMeshes(pieces.ToArray(),true,true); EditorUtility.SetDirty(target.sharedMesh);
}
var preview=catalog.placementPreviews[8].GetComponent<MeshFilter>().sharedMesh;
var combined=shelf.GetComponentsInChildren<MeshFilter>().Select(f=>new CombineInstance {mesh=f.sharedMesh,transform=shelf.transform.worldToLocalMatrix*f.transform.localToWorldMatrix}).ToArray();
preview.Clear(); preview.CombineMeshes(combined,true,true); EditorUtility.SetDirty(preview);
AssetDatabase.SaveAssets();
return "Shelf and placement preview refreshed without PICKUP lettering.";
