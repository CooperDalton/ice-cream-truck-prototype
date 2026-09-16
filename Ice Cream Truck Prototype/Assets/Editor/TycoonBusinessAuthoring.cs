using System.Linq;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using Object=UnityEngine.Object;

public static class TycoonBusinessAuthoring
{
    public static Sprite ExpansionIcon(TycoonGameManager.Site site)
    {
        var preview = new GameObject("Expanded shop preview");
        try
        {
            var canopy = Object.Instantiate(site.canopy, preview.transform);
            canopy.transform.localPosition = Vector3.zero; canopy.transform.localRotation = Quaternion.identity;
            canopy.SetActive(true);
            var floor = Object.Instantiate(site.paving.gameObject, preview.transform).transform;
            floor.localPosition = new Vector3(0, -.01f, -1); floor.localRotation = Quaternion.identity;
            floor.localScale = new Vector3(8, .04f, 8);
            return TycoonPictureAuthoring.Render(preview, "UpgradeKiosk");
        }
        finally { Object.DestroyImmediate(preview); }
    }

    [MenuItem("Ice Cream/Update expansion and movable bin")]
    public static void UpdateExpansionAndBin()
    {
        var scene = UnityEngine.SceneManagement.SceneManager.GetActiveScene();
        var game = scene.GetRootGameObjects()[0].GetComponent<TycoonGameManager>();
        game.RefreshBusinessModels();
        ExpansionIcon(game.sites[0]);
        var button = game.hud.upgradeButtons[5];
        button.GetComponentsInChildren<UnityEngine.UI.Text>(true).Single(t => t.text == "Expand shop" || t.text == "Expand shop · 4 rows").text = "Expand shop · 4 rows";
        var bin = game.catalog.partPrefabs[9];
        var mesh = AssetDatabase.LoadAssetAtPath<Mesh>("Assets/Art/Tycoon/Placement/Mesh_9.asset");
        var pieces = bin.GetComponentsInChildren<MeshFilter>().SelectMany(f => Enumerable.Range(0, f.sharedMesh.subMeshCount).Select(i => new CombineInstance
        { mesh = f.sharedMesh, subMeshIndex = i, transform = bin.transform.worldToLocalMatrix * f.transform.localToWorldMatrix })).ToArray();
        mesh.Clear(); mesh.CombineMeshes(pieces); EditorUtility.SetDirty(mesh);
        TycoonPictureAuthoring.Render(bin.gameObject, "Equipment9");
        game.navigation.BuildNavMesh();
        EditorUtility.SetDirty(game); AssetDatabase.SaveAssets();
        EditorSceneManager.MarkSceneDirty(scene); EditorSceneManager.SaveScene(scene);
    }

    public static void Apply()
    {
        var scene=UnityEngine.SceneManagement.SceneManager.GetActiveScene();var roots=scene.GetRootGameObjects();var game=roots.SelectMany(o=>o.GetComponents<TycoonGameManager>()).Single();
        var canopy=AssetDatabase.LoadAssetAtPath<GameObject>("Assets/Art/Tycoon/Prefabs/Pop_up_canopy.prefab");
        for(int i=0;i<2;i++)
        {
            var site=game.sites[i];site.canopy=roots.Where(o=>PrefabUtility.GetCorrespondingObjectFromSource(o)==canopy).OrderBy(o=>Vector3.Distance(o.transform.position,site.origin.position)).First();
            site.paving=roots.Single(o=>o.name=="Stand paving "+i).transform;
        }
        var bike=game.bike;PrefabUtility.UnpackPrefabInstance(bike.gameObject,PrefabUnpackMode.Completely,InteractionMode.AutomatedAction);
        foreach(var renderer in bike.GetComponentsInChildren<Renderer>(true).ToArray())Object.DestroyImmediate(renderer.gameObject);
        bike.smallCargoModel=Object.Instantiate(AssetDatabase.LoadAssetAtPath<GameObject>("Assets/Art/Tycoon/Prefabs/Delivery_bike_4_cargo.prefab"),bike.transform);
        bike.largeCargoModel=Object.Instantiate(AssetDatabase.LoadAssetAtPath<GameObject>("Assets/Art/Tycoon/Prefabs/Delivery_bike_8_cargo.prefab"),bike.transform);bike.largeCargoModel.SetActive(false);
        var signPath=AssetDatabase.GetAssetPath(game.catalog.partPrefabs[6]);var sign=PrefabUtility.LoadPrefabContents(signPath);var part=sign.GetComponent<TycoonPart>();part.signModel=sign.transform.GetChild(0);
        PrefabUtility.SaveAsPrefabAsset(sign,signPath);PrefabUtility.UnloadPrefabContents(sign);
        game.feedback=game.gameObject.AddComponent<AudioSource>();game.feedback.playOnAwake=false;game.feedback.spatialBlend=0;
        game.saleSound=AssetDatabase.LoadAssetAtPath<AudioClip>("Assets/Audio/Tycoon/Sale.wav");game.scoopSound=AssetDatabase.LoadAssetAtPath<AudioClip>("Assets/Audio/Tycoon/Scoop.wav");game.depositSound=AssetDatabase.LoadAssetAtPath<AudioClip>("Assets/Audio/Tycoon/Deposit.wav");game.upgradeSound=AssetDatabase.LoadAssetAtPath<AudioClip>("Assets/Audio/Tycoon/Upgrade.wav");game.daySound=AssetDatabase.LoadAssetAtPath<AudioClip>("Assets/Audio/Tycoon/Day.wav");
        game.RefreshBusinessModels();EditorSceneManager.SaveScene(scene);AssetDatabase.SaveAssets();
    }
}
