using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using Object=UnityEngine.Object;

public static class TycoonTownAuthoring
{
    [Serializable] private class Manifest { public Entry[] models; public Mat[] materials; }
    [Serializable] private class Entry { public string name; public float[] footprint; }
    [Serializable] private class Mat { public string name; public float[] color; }
    private const string Root="Assets/Art/Tycoon/";
    private static Dictionary<string,GameObject> prefabs;
    private static Transform district;
    private static TycoonGameManager game;
    private static int placed;

    public static void Import()
    {
        var manifest=JsonUtility.FromJson<Manifest>(File.ReadAllText(Root+"Town/TownModels.json"));
        var materials=new Dictionary<string,Material>();
        foreach(var entry in manifest.materials)
        {
            string name=string.Concat(entry.name.Select(c=>char.IsLetterOrDigit(c)?c:'_'));
            string path=Root+"Materials/"+name+".mat";var material=AssetDatabase.LoadAssetAtPath<Material>(path);
            if(material==null){material=new Material(Shader.Find("Ice Cream/Toon"));AssetDatabase.CreateAsset(material,path);}
            material.SetColor("_BaseColor",new Color(entry.color[0],entry.color[1],entry.color[2],1).gamma);materials.Add(entry.name,material);
        }
        foreach(var entry in manifest.models)
        {
            var root=new GameObject(entry.name);var fbx=AssetDatabase.LoadAssetAtPath<GameObject>(Root+"Town/"+entry.name+".fbx");
            var model=Object.Instantiate(fbx,root.transform);
            foreach(var renderer in model.GetComponentsInChildren<Renderer>())renderer.sharedMaterials=renderer.sharedMaterials.Select(m=>materials[m.name]).ToArray();
            TycoonSceneBuilder.Combine(model,"Town_"+entry.name);
            if(!entry.name.Contains("Sidewalk")&&!entry.name.Contains("Curb"))
            {
                var renderers=root.GetComponentsInChildren<Renderer>();var bounds=renderers[0].bounds;foreach(var renderer in renderers)bounds.Encapsulate(renderer.bounds);
                var box=root.AddComponent<BoxCollider>();box.center=bounds.center;box.size=bounds.size;
                if(entry.name.Contains("tree")){box.center=new Vector3(0,1.5f,0);box.size=new Vector3(.6f,3,.6f);}
                if(entry.name.Contains("house")||entry.name.Contains("cottage")||entry.name.Contains("bakery")||entry.name.Contains("cafe")||entry.name.Contains("shop")){box.center=new Vector3(0,bounds.size.y*.45f,0);box.size=new Vector3(entry.footprint[0],bounds.size.y*.9f,entry.footprint[1]);}
            }
            PrefabUtility.SaveAsPrefabAsset(root,Root+"Prefabs/Town_"+entry.name+".prefab");Object.DestroyImmediate(root);
        }
        AssetDatabase.SaveAssets();
    }
    public static void Populate()
    {
        var scene=UnityEngine.SceneManagement.SceneManager.GetActiveScene();game=scene.GetRootGameObjects().SelectMany(o=>o.GetComponents<TycoonGameManager>()).Single();
        if(scene.GetRootGameObjects().Any(o=>o.name=="Town districts"))throw new InvalidOperationException("Town districts already exist. Edit the authored layout instead of appending it twice.");
        EditorSceneManager.SaveScene(scene);
        File.Copy(scene.path,"Library/CodexPlaytests/BeforeTown.unity",true);
        prefabs=JsonUtility.FromJson<Manifest>(File.ReadAllText(Root+"Town/TownModels.json")).models.ToDictionary(e=>e.name,e=>AssetDatabase.LoadAssetAtPath<GameObject>(Root+"Prefabs/Town_"+e.name+".prefab"));
        var town=new GameObject("Town districts");placed=0;
        Group(town,"Streets and sidewalks");
        for(float x=-34;x<=98;x+=4)
            foreach(float z in new[]{-18f,-6f}){Put("Sidewalk_slab",x,z,0,-.10f);Put("Curb_section",x,z+(z<-12?1:-1),0,-.10f);}
        for(float z=-2;z<=46;z+=4)
            foreach(float x in new[]{-1f,11f,58f,70f})
            {
                if(x==-1&&z<6)continue;
                Put("Sidewalk_slab",x,z,90,-.10f);Put("Curb_section",x+(x==11||x==70?-1:1),z,90,-.10f);
            }
        for(float x=14;x<=58;x+=4)foreach(float z in new[]{40f,52f})Put("Sidewalk_slab",x,z,0,-.10f);
        for(float x=-26;x<93;x+=12)foreach(float z in new[]{-19.5f,-4.5f}){Put("Street_lantern",x,z);if(x%24<0)Put("Flower_planter",x+2,z);}
        for(float z=10;z<=38;z+=12)foreach(float x in new[]{-2.5f,12.5f,56.5f,71.5f})Put("Street_lantern",x,z);
        for(float x=-27;x<93;x+=7)Paint("Road dash",new Vector3(x,.028f,-12),new Vector3(2,.008f,.10f),new Color(.93f,.85f,.62f));
        for(float z=-1;z<40;z+=7)foreach(float x in new[]{5f,64f})Paint("Road dash",new Vector3(x,.028f,z),new Vector3(.1f,.008f,2),new Color(.93f,.85f,.62f));
        foreach(float x in new[]{5f,39f,64f})for(int i=0;i<7;i++)Paint("Crosswalk",new Vector3(x,.029f,-15+i),new Vector3(2.7f,.008f,.5f),new Color(.97f,.92f,.79f));

        Group(town,"Home neighborhood");
        string[] houses={"Porch_cottage","Dormer_house","Lemon_house","Brick_townhouse"};
        for(int i=0;i<5;i++)
        {
            float z=5+i*10;Put(houses[i%4],-13,z,90);Garden(-13,z,90);
            if(i<4){Put(houses[(i+2)%4],-28,z+2,90);Garden(-28,z+2,90);}
        }
        Put("Garden_cafe",-15,-4,90);Put("Park_bench",-7,5,90);Put("Flower_planter",-6.5f,7,90);Put("Street_bin",-5,6);
        for(float z=10;z<48;z+=10){Put("Willow_tree",-21,z);Put("Cypress_tree",-7,z+4);}
        for(float x=-30;x<3;x+=8)Put("Willow_tree",x,-27);

        Group(town,"Market street");
        string[] shops={"Corner_bakery","Garden_cafe","Seaside_shop"};
        float[] shopXs={-22,-12,-2,9,19,45,55,77,87};
        for(int i=0;i<shopXs.Length;i++)
        {
            float x=shopXs[i];Put(shops[i%3],x,-25,0);Put("Flower_planter",x-3.7f,-21);Put("Street_bin",x+3.7f,-21);
            if(i%2==0){Put("Picnic_table",x,-20.1f);Put("Parked_hatchback",x+3.5f,-31,90);}
        }
        for(float x=26;x<=38;x+=4)for(float z=-22;z<=-18;z+=2)Put("Sidewalk_slab",x,z,0,-.10f);
        Put("Parked_van",39,-29);Put("Street_lantern",26,-22);Put("Street_lantern",38,-22);
        Put("Bus_shelter",-29,-20);Put("Street_bin",-32,-20);

        Group(town,"Town square");
        for(float x=16;x<=52;x+=4)for(float z=12;z<=28;z+=2)Put("Sidewalk_slab",x,z,0,-.10f);
        Put("Plaza_fountain",34,20);Put("Garden_cafe",22,4);Put("Corner_bakery",32,4);Put("Seaside_shop",43,4);
        for(int i=0;i<4;i++){Put(houses[(i+1)%4],20+i*9,35,180);Garden(20+i*9,35,180);}
        foreach(float x in new[]{19f,49f})foreach(float z in new[]{15f,25f})
        {
            Put("Willow_tree",x,z);Put("Flower_planter",x,z+2.3f);Put("Park_bench",x+(x<34?2.7f:-2.7f),z,x<34?90:-90);
        }
        foreach(float x in new[]{28f,40f})foreach(float z in new[]{14f,26f})Put("Park_bench",x,z,z<20?0:180);
        Put("Picnic_table",25,20);Put("Picnic_table",44,20);Put("Street_bin",30,27);Put("Street_bin",39,13);
        for(float z=12;z<=28;z+=4){Put("Sidewalk_slab",13,z,90,-.10f);Put("Sidewalk_slab",55,z,90,-.10f);}

        Group(town,"Park and playground");
        Paint("Playground sand",new Vector3(83,.015f,3),new Vector3(21,.02f,14),new Color(.86f,.77f,.57f));
        Put("Playground_swing",79,3);Put("Playground_slide",86,3,90);Put("Park_bench",76,-3);Put("Park_bench",88,9,180);
        Put("Park_gazebo",85,29);Put("Park_entry_arch",72,18,90);
        for(float x=74;x<=94;x+=4)Put("Sidewalk_slab",x,18,0,-.10f);
        for(float z=10;z<=34;z+=4)Put("Sidewalk_slab",85,z,90,-.10f);
        foreach(float x in new[]{78f,92f})foreach(float z in new[]{15f,23f})Put("Picnic_table",x,z);
        for(int i=0;i<10;i++)
        {
            float z=-1+i*6;Put(i%2==0?"Willow_tree":"Cypress_tree",99,z);Put("Hedge_section",96,z,90);
        }
        foreach(var p in new[]{new Vector2(73,9),new Vector2(76,29),new Vector2(91,34),new Vector2(87,45),new Vector2(91,-4)}){Put("Willow_tree",p.x,p.y);Put("Garden_rocks",p.x+2,p.y+1);}
        Put("Flower_planter",81,36,90);Put("Park_bench",83,40,-90);Put("Street_bin",81,43);Put("Street_lantern",70,35);Put("Street_lantern",81,46);

        Group(town,"Residential gardens");
        for(int i=0;i<7;i++)
        {
            float x=-22+i*16;Put(houses[i%4],x,72,180);Garden(x,72,180);
            if(i<6){Put("Hedge_section",x+7,58,90);Put("Willow_tree",x+8,68);Put("Parked_hatchback",x+5,58);}
        }
        for(float x=-16;x<95;x+=8)Put("Flower_planter",x,54);
        Group(town,"Town boundary groves");
        for(int i=0;i<28;i++)
        {
            float x=-43+i*5.4f;Put(i%3==0?"Cypress_tree":"Willow_tree",x,-42,0,0,1.1f+i%3*.18f);Put("Willow_tree",x,81,0,0,1.3f);
        }
        for(float z=-34;z<79;z+=7){Put("Willow_tree",-43,z,0,0,1.4f);Put("Cypress_tree",106,z,0,0,1.7f);}
        foreach(var r in town.GetComponentsInChildren<Renderer>())r.gameObject.isStatic=true;
        game.navigation.BuildNavMesh();EditorSceneManager.SaveScene(scene);AssetDatabase.SaveAssets();
        File.WriteAllText("Library/CodexPlaytests/TownPopulation.txt",placed+" modeled scenery instances across seven districts.\n");
        Debug.Log("TOWN_POPULATED "+placed);
    }
    private static void Group(GameObject town,string name)
    {
        district=new GameObject(name).transform;district.SetParent(town.transform,false);
    }
    private static GameObject Put(string name,float x,float z,float yaw=0,float y=0,float scale=1)
    {
        var obj=(GameObject)PrefabUtility.InstantiatePrefab(prefabs[name],district);obj.transform.localPosition=new Vector3(x,y,z);obj.transform.localRotation=Quaternion.Euler(0,yaw,0);obj.transform.localScale=Vector3.one*scale;placed++;return obj;
    }
    private static void Garden(float x,float z,float yaw)
    {
        var rotation=Quaternion.Euler(0,yaw,0);
        foreach(float side in new[]{-1f,1f})
        {
            var p=new Vector3(x,0,z)+rotation*new Vector3(side*4.4f,0,0);Put("Picket_fence",p.x,p.z,yaw+90);
            p=new Vector3(x,0,z)+rotation*new Vector3(side*3,0,4.3f);Put("Flower_planter",p.x,p.z,yaw);
        }
    }
    private static void Paint(string name,Vector3 point,Vector3 size,Color color)
    {
        var obj=GameObject.CreatePrimitive(PrimitiveType.Cube);obj.name=name;obj.transform.SetParent(district,false);obj.transform.position=point;obj.transform.localScale=size;Object.DestroyImmediate(obj.GetComponent<Collider>());
        string path=Root+"Materials/Town_"+name.Replace(' ','_')+".mat";var material=AssetDatabase.LoadAssetAtPath<Material>(path);
        if(material==null){material=new Material(Shader.Find("Ice Cream/Toon"));material.SetColor("_BaseColor",color);AssetDatabase.CreateAsset(material,path);}obj.GetComponent<Renderer>().sharedMaterial=material;
    }
}
