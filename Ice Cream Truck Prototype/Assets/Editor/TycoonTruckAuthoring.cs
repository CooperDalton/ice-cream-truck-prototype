using System;
using System.Linq;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using Object = UnityEngine.Object;

public static class TycoonTruckAuthoring
{
    private const string Root = "Assets/Art/Tycoon/";
    public static void Build()
    {
        var scene = UnityEngine.SceneManagement.SceneManager.GetActiveScene();
        var game = scene.GetRootGameObjects().SelectMany(o => o.GetComponents<TycoonGameManager>()).Single();
        var truck = game.truck;
        PrefabUtility.UnpackPrefabInstance(truck.gameObject, PrefabUnpackMode.Completely, InteractionMode.AutomatedAction);
        foreach (var part in game.parts.Where(p => p.site == 2 && p != truck.interaction)) part.transform.SetParent(null,true);
        foreach (var part in game.parts.Where(p => p.site == 2 && p != truck.interaction).ToArray())
        { game.parts.Remove(part); Object.DestroyImmediate(part.gameObject); }
        foreach (var renderer in truck.GetComponentsInChildren<Renderer>(true).ToArray()) Object.DestroyImmediate(renderer.gameObject);
        Object.DestroyImmediate(truck.GetComponent<BoxCollider>());
        var shell = Object.Instantiate(AssetDatabase.LoadAssetAtPath<GameObject>(Root + "Models/Truck_shell.fbx"), truck.transform);
        shell.name = "Toon truck shell";
        foreach (var renderer in shell.GetComponentsInChildren<Renderer>()) renderer.sharedMaterials = renderer.sharedMaterials.Select(m => AssetDatabase.LoadAssetAtPath<Material>(Root + "Materials/" + string.Concat(m.name.Select(c => char.IsLetterOrDigit(c) ? c : '_')) + ".mat")).ToArray();
        var wheelMeshes = shell.GetComponentsInChildren<MeshFilter>().Where(f => f.name.Contains("Wheel_AXLE")).ToArray();
        truck.wheels = new Transform[wheelMeshes.Length];
        for (int i = 0; i < wheelMeshes.Length; i++)
        {
            var filter = wheelMeshes[i]; var wheel = new GameObject("Wheel " + i).transform; wheel.SetParent(truck.transform, false); wheel.position = filter.GetComponent<Renderer>().bounds.center;
            filter.transform.SetParent(wheel, true); TycoonSceneBuilder.Combine(wheel.gameObject, "TruckWheel_" + i); truck.wheels[i] = wheel;
        }
        TycoonSceneBuilder.Combine(shell, "TruckShell");
        truck.seat.localPosition = new Vector3(1.65f,.60f,1.05f); truck.seat.localRotation = Quaternion.Euler(0,90,0);
        truck.exit.localPosition = new Vector3(1.7f,0,2.7f);
        truck.kitchenEntry = Point("Kitchen entry", truck.transform, new Vector3(-2.5f,.60f,0));
        Collider(truck.transform,"Kitchen floor",new Vector3(-1.45f,.51f,0),new Vector3(4.3f,.14f,3.4f));
        Collider(truck.transform,"Closed side wall",new Vector3(-1.45f,2,-1.78f),new Vector3(4.3f,3,.15f));
        Collider(truck.transform,"Service wall",new Vector3(-1.45f,1,1.78f),new Vector3(4.3f,1,.15f));
        Collider(truck.transform,"Cabin partition",new Vector3(.75f,1.9f,0),new Vector3(.15f,2.6f,3.4f));
        Collider(truck.transform,"Cabin interaction",new Vector3(2,1.3f,0),new Vector3(2.3f,2.6f,3.6f));
        Collider(truck.transform,"Rear left wall",new Vector3(-3.6f,1.8f,-1.22f),new Vector3(.14f,2.5f,.95f));
        Collider(truck.transform,"Rear right wall",new Vector3(-3.6f,1.8f,1.22f),new Vector3(.14f,2.5f,.95f));
        var ramp = Collider(truck.transform,"Rear loading ramp",new Vector3(-4.15f,.25f,0),new Vector3(1.3f,.12f,1.5f)); ramp.transform.localRotation = Quaternion.Euler(0,0,24);
        game.sites[2].origin.SetParent(truck.transform,false); game.sites[2].origin.localPosition = new Vector3(-1.5f,.58f,0); game.sites[2].plotSize = new Vector2(4,3.2f);
        game.sites[2].queuePoint.SetParent(truck.transform,false); game.sites[2].queuePoint.localPosition = new Vector3(-1.5f,0,3);
        for (int i = 0; i < 4; i++)
        {
            var tub = Part(game,1,new Vector3(-2.25f+i*.5f,.58f,-1.25f)); tub.transform.localRotation = Quaternion.Euler(0,180,0); tub.variant = i; tub.contents = new TycoonItem(TycoonItem.Kind.Tub,0,i);
        }
        var table = Part(game,7,new Vector3(-1.5f,.58f,1.1f));
        var prep = Part(game,2,new Vector3(-2,1.52f,1.1f)); prep.support = table; prep.transform.SetParent(table.transform,true);
        var iron = Part(game,3,new Vector3(-.9f,1.52f,1.1f)); iron.support = table; iron.transform.SetParent(table.transform,true);
        var locker = Part(game,4,new Vector3(0,.58f,-1.2f)); locker.transform.localRotation = Quaternion.Euler(0,180,0); locker.storage = new TycoonInventory(8); locker.RefreshLocker();
        var cold = Part(game,5,new Vector3(-3.15f,.58f,-.85f)); cold.transform.localRotation = Quaternion.Euler(0,-90,0);
        var sign = Part(game,6,new Vector3(-.05f,.58f,1.25f));
        truck.gameObject.SetActive(false); game.navigation.BuildNavMesh();
        EditorSceneManager.SaveScene(scene); AssetDatabase.SaveAssets();
        Debug.Log("TYCOON_TRUCK_FITTED");
    }
    private static TycoonPart Part(TycoonGameManager game,int index,Vector3 local)
    {
        var root = (GameObject)PrefabUtility.InstantiatePrefab(game.catalog.partPrefabs[index].gameObject);
        root.transform.SetParent(game.truck.transform,false); root.transform.localPosition = local;
        var part = root.GetComponent<TycoonPart>(); part.game = game; part.site = 2; part.id = game.nextId++; game.parts.Add(part); return part;
    }
    private static Transform Point(string name,Transform parent,Vector3 local)
    {
        var point = new GameObject(name).transform; point.SetParent(parent,false); point.localPosition = local; return point;
    }
    private static BoxCollider Collider(Transform parent,string name,Vector3 local,Vector3 size)
    {
        var point = Point(name,parent,local); var collider = point.gameObject.AddComponent<BoxCollider>(); collider.size = size; return collider;
    }
}
