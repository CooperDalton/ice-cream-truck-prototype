using System.Linq;
using UnityEngine;
using UnityEditor;
using UnityEditor.SceneManagement;

public static class AuthorPickupPhysics
{
    public static string Run()
    {
        int authored = 0;
        foreach (string sceneName in new[] { "IceCreamPrototype", "ParkRoute" })
        {
            var scene = EditorSceneManager.OpenScene("Assets/Scenes/" + sceneName + ".unity");
            var r = PrototypeSceneReferences.Instance;
            var items = new[] { r.batter, r.shaker, r.scooper, (PickupItem)r.boombox }.ToList();
            if (sceneName == "ParkRoute") items.Add(r.route.tray);
            foreach (var item in items) { AddBody(item); authored++; }
            string conePath = AssetDatabase.GetAssetPath(r.waffle.conePrefab);
            var cone = PrefabUtility.LoadPrefabContents(conePath);
            try
            {
                AddBody(cone.GetComponent<IceCreamCone>());
                PrefabUtility.SaveAsPrefabAsset(cone, conePath);
            }
            finally { PrefabUtility.UnloadPrefabContents(cone); }
            var panel = sceneName == "ParkRoute" ? r.route.hud.pausePanel : r.hud.pausePanel;
            foreach (var text in panel.GetComponentsInChildren<UnityEngine.UI.Text>(true))
                text.text = text.text.Replace("Right click returns the item in your hand.", "Right click drops the item from your hand.");
            EditorSceneManager.MarkSceneDirty(scene);
            EditorSceneManager.SaveScene(scene);
        }
        return "Authored physics for " + authored + " scene items and cone prefabs in both modes.";
    }
    private static void AddBody(PickupItem item)
    {
        foreach (var collider in item.GetComponentsInChildren<MeshCollider>(true)) collider.convex = true;
        var body = item.GetComponent<Rigidbody>();
        if (body == null) body = item.gameObject.AddComponent<Rigidbody>();
        item.body = body;
        body.mass = item.kind == PickupItem.ItemKind.Boombox ? 2 : item.kind == PickupItem.ItemKind.Cone ? .15f : .4f;
        body.useGravity = true;
        body.isKinematic = true;
        body.angularDamping = .3f;
        body.collisionDetectionMode = CollisionDetectionMode.ContinuousSpeculative;
        body.maxDepenetrationVelocity = 2;
        item.pickupCollider.isTrigger = false;
        EditorUtility.SetDirty(item);
    }
}
