// Run with unity command eval_file Tools/CheckTabletopOccupancy.cs in Edit Mode.
if (EditorApplication.isPlaying) throw new Exception("Run the occupancy check in Edit Mode.");
var scene = UnityEditor.SceneManagement.EditorSceneManager.NewPreviewScene();
try
{
    var root = new GameObject("Tabletop occupancy check");
    root.SetActive(false);
    UnityEngine.SceneManagement.SceneManager.MoveGameObjectToScene(root, scene);
    var game = root.AddComponent<TycoonGameManager>();
    game.tutorial = root.AddComponent<TycoonTutorial>();
    var builder = root.AddComponent<TycoonBuilder>();
    builder.game = game;
    game.sites = new[] { new TycoonGameManager.Site { origin = root.transform, owned = true } };
    var table = UnityEngine.Object.Instantiate(AssetDatabase.LoadAssetAtPath<TycoonPart>("Assets/Art/Tycoon/Prefabs/Part_0.prefab"), root.transform);
    var holder = UnityEngine.Object.Instantiate(AssetDatabase.LoadAssetAtPath<TycoonPart>("Assets/Art/Tycoon/Prefabs/Part_2.prefab"), root.transform);
    var bowl = UnityEngine.Object.Instantiate(AssetDatabase.LoadAssetAtPath<TycoonPart>("Assets/Art/Tycoon/Prefabs/Part_13.prefab"), table.transform);
    bowl.support = table;
    game.parts.Add(bowl);
    int checks = 0;
    foreach (float angle in new[] { 0f, 90f, 180f, 270f })
    {
        table.transform.localRotation = Quaternion.Euler(0, angle, 0);
        bowl.transform.localPosition = new Vector3(-.125f, table.surfaceHeight, -.125f);
        bowl.transform.localRotation = Quaternion.identity;
        var rotation = table.transform.rotation;
        foreach (var offset in new[] { Vector3.right, Vector3.left, Vector3.forward, Vector3.back })
        {
            var position = table.transform.TransformPoint(bowl.transform.localPosition + offset * .25f);
            if (!builder.CanPlace(holder, position, rotation, table, out var reason))
                throw new Exception("Adjacent cell rejected at table rotation " + angle + ", offset " + offset + ": " + reason);
            checks++;
        }
        if (builder.CanPlace(holder, bowl.transform.position, rotation, table, out _))
            throw new Exception("Holder was allowed to overlap the bowl.");
        checks++;
        var edge = new Vector3(table.footprint.x / 2 - .125f, table.surfaceHeight, table.footprint.y / 2 - .125f);
        if (!builder.CanPlace(holder, table.transform.TransformPoint(edge), rotation, table, out var edgeReason))
            throw new Exception("Last tabletop cell rejected: " + edgeReason);
        checks++;
        if (builder.CanPlace(holder, table.transform.TransformPoint(edge + Vector3.right * .25f), rotation, table, out _))
            throw new Exception("Holder was allowed outside the tabletop.");
        checks++;
    }
    return checks + " checks passed: adjacent cells, occupied cell, and tabletop edges at four rotations.";
}
finally
{
    UnityEditor.SceneManagement.EditorSceneManager.ClosePreviewScene(scene);
}
