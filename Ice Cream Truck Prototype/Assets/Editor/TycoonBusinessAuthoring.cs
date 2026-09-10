using System.Linq;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using Object=UnityEngine.Object;

public static class TycoonBusinessAuthoring
{
    public static void Apply()
    {
        var scene=UnityEngine.SceneManagement.SceneManager.GetActiveScene();var roots=scene.GetRootGameObjects();var game=roots.SelectMany(o=>o.GetComponents<TycoonGameManager>()).Single();
        var canopy=AssetDatabase.LoadAssetAtPath<GameObject>("Assets/Art/Tycoon/Prefabs/Pop_up_canopy.prefab");
        for(int i=0;i<2;i++)
        {
            var site=game.sites[i];site.canopy=roots.Where(o=>PrefabUtility.GetCorrespondingObjectFromSource(o)==canopy).OrderBy(o=>Vector3.Distance(o.transform.position,site.origin.position)).First();
            site.paving=roots.Single(o=>o.name=="Stand paving "+i).transform;
            site.kiosk=(GameObject)PrefabUtility.InstantiatePrefab(AssetDatabase.LoadAssetAtPath<GameObject>("Assets/Art/Tycoon/Prefabs/Expanded_kiosk_shell.prefab"));
            site.kiosk.transform.position=site.origin.position+new Vector3(0,-.16f,0);site.kiosk.transform.localScale=new Vector3(2.5f,1,2);
            var rear=new GameObject("Kiosk back collision");rear.transform.SetParent(site.kiosk.transform,false);rear.transform.localPosition=new Vector3(0,1.37f,-1.45f);var box=rear.AddComponent<BoxCollider>();box.size=new Vector3(4,.0f+2.58f,.1f);
            site.kiosk.SetActive(false);
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
