using System;
using System.IO;
using System.Linq;
using System.Reflection;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using Object=UnityEngine.Object;

public static class MakeTycoonFixturesMovable
{
    public static string Build()
    {
        if(EditorApplication.isPlaying)throw new Exception("Stop Play Mode first");
        var scene=UnityEngine.SceneManagement.SceneManager.GetActiveScene();var g=scene.GetRootGameObjects()[0].GetComponent<TycoonGameManager>();
        var catalog=g.catalog;int first=catalog.partPrefabs.Length;
        if(catalog.partPrefabs.Any(p=>p.kind==TycoonPart.Kind.Register))throw new Exception("Movable register prefabs already authored");
        Array.Resize(ref catalog.partPrefabs,first+2);Array.Resize(ref catalog.equipmentIcons,first+2);
        for(int variant=0;variant<2;variant++)
        {
            int source=variant==0?0:2;
            var root=Object.Instantiate(g.sites[source].registerCounter);root.name=variant==0?"Order counter":"Truck order station";
            root.transform.SetParent(null,true);root.transform.SetPositionAndRotation(Vector3.zero,Quaternion.identity);
            var part=root.AddComponent<TycoonPart>();part.kind=TycoonPart.Kind.Register;part.catalogIndex=first+variant;
            part.footprint=variant==0?new Vector2(1.3f,.8f):new Vector2(.6f,.3f);
            part.operatingPoint=root.transform.GetChild(variant==0?1:0);
            part.handTarget=Point("Hand target",root.transform,Vector3.up);part.contentPoint=part.handTarget;part.lid=part.handTarget;part.fillRenderers=Array.Empty<Renderer>();
            part.queuePoint=Point("Customer queue",root.transform,new Vector3(0,variant==0?0:-.58f,1.2f));
            if(variant==1){var collider=root.AddComponent<BoxCollider>();collider.center=new Vector3(0,1.13f,0);collider.size=new Vector3(.6f,.3f,.3f);}
            string path="Assets/Art/Tycoon/Prefabs/Part_"+(first+variant)+".prefab";
            catalog.partPrefabs[first+variant]=PrefabUtility.SaveAsPrefabAsset(root,path).GetComponent<TycoonPart>();Object.DestroyImmediate(root);
        }
        var counterPath=AssetDatabase.GetAssetPath(catalog.partPrefabs[7]);var counterRoot=PrefabUtility.LoadPrefabContents(counterPath);
        try
        {
            var p=counterRoot.GetComponent<TycoonPart>();p.queuePoint=Point("Customer queue",counterRoot.transform,new Vector3(0,0,1.2f));
            PrefabUtility.SaveAsPrefabAsset(counterRoot,counterPath);
        }
        finally{PrefabUtility.UnloadPrefabContents(counterRoot);}
        var fixtures=new System.Collections.Generic.List<string>();
        for(int i=0;i<3;i++)
        {
            var site=g.sites[i];var pickup=g.Parts(i,TycoonPart.Kind.ServingCounter).First();
            var oldRegister=site.registerCounter;var oldQueue=site.queuePoint;var oldPickup=site.pickupQueuePoint;
            var rotation=oldRegister.transform.rotation;
            var position=i==2?oldRegister.transform.position:pickup.transform.position-pickup.transform.right*1.8f;
            Object.DestroyImmediate(oldRegister);
            if(oldQueue!=null)Object.DestroyImmediate(oldQueue.gameObject);
            if(oldPickup!=null)Object.DestroyImmediate(oldPickup.gameObject);
            var go=(GameObject)PrefabUtility.InstantiatePrefab(catalog.partPrefabs[first+(i==2?1:0)].gameObject);
            go.transform.SetParent(i==2?g.truck.transform:null,true);go.transform.SetPositionAndRotation(position,rotation);
            var p=go.GetComponent<TycoonPart>();p.game=g;p.site=i;p.id=g.nextId++;g.parts.Add(p);
            site.registerCounter=go;site.queuePoint=p.queuePoint;site.registerOperatingPoint=p.operatingPoint;
            site.pickupQueuePoint=pickup.queuePoint;
            if(i==2)pickup.queuePoint.localPosition=new Vector3(.65f,-.58f,1.2f);
            PrefabUtility.RecordPrefabInstancePropertyModifications(pickup.queuePoint);
            fixtures.Add(Snapshot(p));
        }
        var render=typeof(TycoonPictureAuthoring).GetMethod("Render",BindingFlags.Static|BindingFlags.NonPublic);
        catalog.equipmentIcons[first]=(Sprite)render.Invoke(null,new object[]{catalog.partPrefabs[first].gameObject,"Equipment"+first,.6f});
        catalog.equipmentIcons[first+1]=catalog.equipmentIcons[first];
        File.WriteAllText("/tmp/tycoon-movable-registers.json","{\"parts\":["+string.Join(",",fixtures)+"]}");
        EditorUtility.SetDirty(catalog);EditorUtility.SetDirty(g);AssetDatabase.SaveAssets();g.navigation.BuildNavMesh();
        EditorSceneManager.MarkSceneDirty(scene);EditorSceneManager.SaveScene(scene);
        return "Registered both order station prefabs and attached customer queues to their movable counters.";
    }
    public static string BusinessBoards()
    {
        if(EditorApplication.isPlaying)throw new Exception("Stop Play Mode first");
        var scene=UnityEngine.SceneManagement.SceneManager.GetActiveScene();var g=scene.GetRootGameObjects()[0].GetComponent<TycoonGameManager>();
        var boards=g.parts.Where(p=>p.kind==TycoonPart.Kind.Plot).ToArray();int index=Array.FindIndex(g.catalog.partPrefabs,p=>p.kind==TycoonPart.Kind.BusinessBoard);if(index<0)index=g.catalog.partPrefabs.Length;
        var root=new GameObject("Business board");var visual=Object.Instantiate(boards[0].gameObject,root.transform);
        Object.DestroyImmediate(visual.GetComponent<TycoonPart>());visual.transform.localPosition=Vector3.up;visual.transform.localRotation=Quaternion.identity;
        var part=root.AddComponent<TycoonPart>();part.kind=TycoonPart.Kind.BusinessBoard;part.catalogIndex=index;part.footprint=new Vector2(.5f,.5f);
        part.operatingPoint=Point("Operate",root.transform,new Vector3(0,0,-.9f));part.handTarget=Point("Hand target",root.transform,Vector3.up);
        part.contentPoint=part.handTarget;part.lid=part.handTarget;part.fillRenderers=Array.Empty<Renderer>();
        Array.Resize(ref g.catalog.partPrefabs,index+1);Array.Resize(ref g.catalog.equipmentIcons,index+1);
        g.catalog.partPrefabs[index]=PrefabUtility.SaveAsPrefabAsset(root,"Assets/Art/Tycoon/Prefabs/Part_"+index+".prefab").GetComponent<TycoonPart>();Object.DestroyImmediate(root);
        var saved=new System.Collections.Generic.List<string>();
        foreach(var old in boards)
        {
            var go=(GameObject)PrefabUtility.InstantiatePrefab(g.catalog.partPrefabs[index].gameObject);go.transform.SetParent(old.transform.parent,true);
            go.transform.SetPositionAndRotation(old.transform.position-Vector3.up,old.transform.rotation);
            var p=go.GetComponent<TycoonPart>();p.id=old.id;p.site=old.site;p.game=g;g.parts.Remove(old);g.parts.Add(p);Object.DestroyImmediate(old.gameObject);
            saved.Add(Snapshot(p));
        }
        File.WriteAllText("/tmp/tycoon-movable-boards.json","{\"parts\":["+string.Join(",",saved)+"]}");
        var render=typeof(TycoonPictureAuthoring).GetMethod("Render",BindingFlags.Static|BindingFlags.NonPublic);
        g.catalog.equipmentIcons[index]=(Sprite)render.Invoke(null,new object[]{g.catalog.partPrefabs[index].gameObject,"Equipment"+index,.6f});
        EditorUtility.SetDirty(g.catalog);EditorUtility.SetDirty(g);AssetDatabase.SaveAssets();g.navigation.BuildNavMesh();
        EditorSceneManager.MarkSceneDirty(scene);EditorSceneManager.SaveScene(scene);return "Business boards are movable fixtures.";
    }
    public static string ExportRegisters()
    {
        var g=UnityEngine.SceneManagement.SceneManager.GetActiveScene().GetRootGameObjects()[0].GetComponent<TycoonGameManager>();
        File.WriteAllText("/tmp/tycoon-movable-registers.json","{\"parts\":["+string.Join(",",g.parts.Where(p=>p.kind==TycoonPart.Kind.Register).Select(Snapshot))+"]}");
        return "Exported movable register poses.";
    }
    private static string Snapshot(TycoonPart p)
    {
        string pose="\"position\":"+JsonUtility.ToJson(p.transform.position)+",\"rotation\":"+JsonUtility.ToJson(p.transform.rotation);
        return "{\"prefab\":"+p.catalogIndex+",\"site\":"+p.site+",\"installed\":true,\"owner\":\"\",\"storage\":{\"slots\":[null,null,null,null]},"+pose+"}";
    }
    private static Transform Point(string name,Transform parent,Vector3 position)
    {
        var point=new GameObject(name).transform;point.SetParent(parent,false);point.localPosition=position;return point;
    }
}
