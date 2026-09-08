using System.Linq;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

public static class PrototypeVisualPolish
{
    [MenuItem("Ice Cream/Apply prototype visual polish")]
    public static void Apply()
    {
        var r=PrototypeSceneReferences.Instance;
        var hands=r.interaction.rightHand;
        hands.localPosition=new Vector3(0,-.28f,.55f);
        var pose=r.player.GetComponent<FloatingHands>();
        if(pose==null) pose=r.player.gameObject.AddComponent<FloatingHands>();
        pose.interaction=r.interaction;pose.view=r.player.view.transform;
        var bones=hands.GetComponentsInChildren<Transform>().ToDictionary(t=>t.name,t=>t);
        pose.leftHandBone=bones["Hand_L"];pose.rightHandBone=bones["Hand_R"];
        var conePath="Assets/Prefabs/IceCreamCone.prefab";
        var coneGO=PrefabUtility.LoadPrefabContents(conePath);var cone=coneGO.GetComponent<IceCreamCone>();
        var filter=cone.scoopVisuals[0].GetComponentInChildren<MeshFilter>();
        var clean=Object.Instantiate(filter.sharedMesh);clean.name="Plain ice cream scoop";clean.subMeshCount=1;
        AssetDatabase.CreateAsset(clean,"Assets/Art/PlainScoop.asset");
        for(int i=0;i<3;i++)
        {
            cone.scoopVisuals[i].GetComponentInChildren<MeshFilter>().sharedMesh=clean;
            cone.scoopRenderers[i].sharedMaterials=new[]{cone.scoopRenderers[i].sharedMaterial};
            cone.scoopVisuals[i].transform.localPosition=new Vector3(0,.201f+i*.105f,0);
            cone.toppingVisuals[i].transform.localPosition=new Vector3(0,-i*.015f,0);
        }
        PrototypeConeCollision.Configure(cone);
        PrefabUtility.SaveAsPrefabAsset(coneGO,conePath);PrefabUtility.UnloadPrefabContents(coneGO);
        r.scooper.loadedScoop.GetComponentInChildren<MeshFilter>().sharedMesh=clean;
        r.scooper.loadedScoopRenderer.sharedMaterials=new[]{r.scooper.loadedScoopRenderer.sharedMaterial};
        foreach(var prefab in r.customers.customerPrefabs)
        {
            string path=AssetDatabase.GetAssetPath(prefab);var go=PrefabUtility.LoadPrefabContents(path);go.GetComponent<Customer>().interactionCollider=go.GetComponent<Collider>();PrefabUtility.SaveAsPrefabAsset(go,path);PrefabUtility.UnloadPrefabContents(go);
        }
        EditorSceneManager.MarkSceneDirty(r.gameObject.scene);EditorSceneManager.SaveScene(r.gameObject.scene);AssetDatabase.SaveAssets();
    }
}
