// Run in Edit Mode with unity command eval_file Tools/AuthorGridEdges.cs.
if (EditorApplication.isPlaying) throw new Exception("Stop Play Mode before authoring grid edges.");
var scene = UnityEngine.SceneManagement.SceneManager.GetActiveScene();
var game = scene.GetRootGameObjects().SelectMany(g => g.GetComponents<TycoonGameManager>()).Single();
var path = AssetDatabase.GetAssetPath(game.catalog.partPrefabs[10]);
var prefab = PrefabUtility.LoadPrefabContents(path);
try
{
    var part = prefab.GetComponent<TycoonPart>();
    part.footprint = new Vector2(1.5f, 1);
    part.transform.GetChild(0).localScale = new Vector3(.75f, 1, 1);
    var collider = part.GetComponent<BoxCollider>();
    collider.size = new Vector3(1.5f, collider.size.y, 1);
    PrefabUtility.SaveAsPrefabAsset(prefab, path);
}
finally { PrefabUtility.UnloadPrefabContents(prefab); }
var source = game.catalog.partPrefabs[10].transform;
var pieces = source.GetComponentsInChildren<MeshFilter>().SelectMany(f => Enumerable.Range(0, f.sharedMesh.subMeshCount).Select(i => new CombineInstance { mesh = f.sharedMesh, subMeshIndex = i, transform = source.worldToLocalMatrix * f.transform.localToWorldMatrix })).ToArray();
var mesh = game.catalog.placementPreviews[10].GetComponent<MeshFilter>().sharedMesh;
mesh.Clear(); mesh.CombineMeshes(pieces, true, true); EditorUtility.SetDirty(mesh);
// Keep existing authored guidance and move only its placement targets.
int[] indices = { 0, 10, 7, 1, 1, 8 };
var tableBefore = game.tutorial.placementSpots[0].position;
for (int i = 0; i < indices.Length; i++)
{
    var spot = game.tutorial.placementSpots[i];
    var grid = game.sites[0].origin;
    spot.position = grid.TransformPoint(TycoonBuilder.SnapToGrid(grid.InverseTransformPoint(spot.position), game.catalog.partPrefabs[indices[i]].footprint, Quaternion.Inverse(grid.rotation) * spot.rotation, .5f));
}
game.tutorial.bowlSpot.position += game.tutorial.placementSpots[0].position - tableBefore;
foreach (var part in game.parts.Where(p => p.catalogIndex == 10))
{
    part.footprint = new Vector2(1.5f, 1);
    part.transform.GetChild(0).localScale = new Vector3(.75f, 1, 1);
    var collider = part.GetComponent<BoxCollider>();
    collider.size = new Vector3(1.5f, collider.size.y, 1);
    EditorUtility.SetDirty(part);
}
UnityEditor.SceneManagement.EditorSceneManager.MarkSceneDirty(scene); UnityEditor.SceneManagement.EditorSceneManager.SaveScene(scene); AssetDatabase.SaveAssets();
return "Register footprint and preview are 1.5 x 1; tutorial targets aligned.";

