// Run in Edit Mode with unity command eval_file Tools/CheckGridEdges.cs.
if (EditorApplication.isPlaying) throw new Exception("Run grid checks in Edit Mode.");
var game = UnityEngine.SceneManagement.SceneManager.GetActiveScene().GetRootGameObjects().SelectMany(g => g.GetComponents<TycoonGameManager>()).Single();
int checks = 0;
foreach (int index in new[] { 0, 1, 2, 3, 4, 5, 7, 8, 10, 13 })
{
    var part = game.catalog.partPrefabs[index];
    float cell = part.tabletop ? .25f : .5f;
    foreach (float angle in new[] { 0f, 90f, 180f, 270f })
    foreach (var point in new[] { new Vector3(-2.73f, 0, -1.61f), new Vector3(.03f, 0, .27f), new Vector3(2.32f, 0, 1.79f) })
    {
        var rotation = Quaternion.Euler(0, angle, 0);
        var snapped = TycoonBuilder.SnapToGrid(point, part.footprint, rotation, cell);
        var size = rotation * new Vector3(part.footprint.x, 0, part.footprint.y);
        foreach (float edge in new[] { snapped.x - Mathf.Abs(size.x) / 2, snapped.x + Mathf.Abs(size.x) / 2, snapped.z - Mathf.Abs(size.z) / 2, snapped.z + Mathf.Abs(size.z) / 2 })
            if (Mathf.Abs(edge / cell - Mathf.Round(edge / cell)) > .0001f) throw new Exception("Edge off grid: " + index + " rotation " + angle);
        if ((TycoonBuilder.SnapToGrid(snapped, part.footprint, rotation, cell) - snapped).sqrMagnitude > .000001f) throw new Exception("Snap drifts");
        checks++;
    }
}
int[] indices = { 0, 10, 7, 1, 1, 8 };
for (int i = 0; i < indices.Length; i++)
{
    var spot = game.tutorial.placementSpots[i]; var grid = game.sites[0].origin;
    var local = grid.InverseTransformPoint(spot.position);
    if ((TycoonBuilder.SnapToGrid(local, game.catalog.partPrefabs[indices[i]].footprint, Quaternion.Inverse(grid.rotation) * spot.rotation, .5f) - local).sqrMagnitude > .000001f) throw new Exception("Tutorial target off grid: " + i);
    checks++;
}
var counter = game.catalog.placementPreviews[10].GetComponent<MeshFilter>().sharedMesh.bounds;
if (Mathf.Abs(counter.size.x - 1.5f) > .001f || Mathf.Abs(counter.size.z - 1) > .001f) throw new Exception("Register model does not fill its footprint");
return "PASS: " + checks + " rotated footprint and tutorial target checks; register model fills 3 x 2 cells.";
