using System;
using System.Collections.Generic;
using System.Linq;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using Object=UnityEngine.Object;

public static class AuthorClosedHands
{
    static void Ellipsoid(List<CombineInstance> pieces,Vector3 center,Vector3 size)
    {
        var sphere=GameObject.CreatePrimitive(PrimitiveType.Sphere);
        pieces.Add(new CombineInstance{mesh=sphere.GetComponent<MeshFilter>().sharedMesh,transform=Matrix4x4.TRS(center,Quaternion.identity,size*2)});
        Object.DestroyImmediate(sphere);
    }
    static Mesh Grip(float radius,string name)
    {
        var pieces=new List<CombineInstance>();
        Ellipsoid(pieces,new Vector3(0,-.00025f,radius+.00005f),new Vector3(.00105f,.00075f,.00036f));
        for(int finger=0;finger<4;finger++)
        {
            float x=(finger-1.5f)*.00048f;
            var vertices=new List<Vector3>();var triangles=new List<int>();
            const int steps=20,sides=10;float thickness=.000235f;
            for(int ring=0;ring<=steps;ring++)
            {
                float angle=Mathf.Lerp(-35,230,ring/(float)steps)*Mathf.Deg2Rad;
                for(int side=0;side<sides;side++)
                {
                    float phi=side*2*Mathf.PI/sides;
                    vertices.Add(new Vector3(x+Mathf.Sin(phi)*thickness,Mathf.Sin(angle)*(radius+Mathf.Cos(phi)*thickness),Mathf.Cos(angle)*(radius+Mathf.Cos(phi)*thickness)));
                    if(ring==steps)continue;
                    int a=ring*sides+side,b=ring*sides+(side+1)%sides,c=a+sides,d=b+sides;
                    triangles.AddRange(new[]{a,b,c,b,d,c});
                }
            }
            var mesh=new Mesh();mesh.SetVertices(vertices);mesh.SetTriangles(triangles,0);mesh.RecalculateNormals();
            pieces.Add(new CombineInstance{mesh=mesh,transform=Matrix4x4.identity});
            foreach(float angle in new[]{-35f,230f})Ellipsoid(pieces,new Vector3(x,Mathf.Sin(angle*Mathf.Deg2Rad)*radius,Mathf.Cos(angle*Mathf.Deg2Rad)*radius),Vector3.one*thickness);
        }
        Ellipsoid(pieces,new Vector3(-.0008f,-radius*.6f,0),new Vector3(.00034f,.00032f,radius*.85f));
        var skin=new Mesh();skin.CombineMeshes(pieces.ToArray());
        var cuff=new List<CombineInstance>();Ellipsoid(cuff,new Vector3(0,-.00112f,radius+.00005f),new Vector3(.0008f,.00028f,.00039f));
        var meshResult=new Mesh();meshResult.CombineMeshes(new[]{new CombineInstance{mesh=skin,transform=Matrix4x4.identity},cuff[0]},false);
        meshResult.name=name;
        string path="Assets/Art/"+name+".asset";var existing=AssetDatabase.LoadAssetAtPath<Mesh>(path);
        if(existing==null)AssetDatabase.CreateAsset(meshResult,path);
        else{EditorUtility.CopySerialized(meshResult,existing);Object.DestroyImmediate(meshResult);meshResult=existing;EditorUtility.SetDirty(existing);}
        Object.DestroyImmediate(skin);
        return meshResult;
    }
    public static string Refine()
    {
        Grip(.0006f,"Handle grip");var wide=Grip(.00112f,"Bottle grip");var coneGrip=Grip(.00068f,"Cone grip");
        foreach(var path in new[]{"Assets/Scenes/IceCreamPrototype.unity","Assets/Scenes/ParkRoute.unity"})
        {
            var scene=EditorSceneManager.OpenScene(path);PrototypeSceneReferences.Instance.boombox.handMesh=wide;
            EditorSceneManager.MarkSceneDirty(scene);EditorSceneManager.SaveScene(scene);
        }
        AssetDatabase.SaveAssets();EditorSceneManager.OpenScene("Assets/Scenes/MainMenu.unity");return "Updated curved finger normals and boombox grip diameter";
    }
    public static string Build()
    {
        if(EditorApplication.isPlaying)throw new Exception("Stop Play Mode first");
        var small=Grip(.0006f,"Handle grip");var wide=Grip(.00112f,"Bottle grip");var coneGrip=Grip(.00068f,"Cone grip");
        var original=AssetDatabase.LoadAllAssetsAtPath("Assets/Art/Workshop.fbx").OfType<Mesh>().Single(m=>m.name=="FirstPersonMittens_Mesh");
        var left=Object.Instantiate(original);left.name="First person left hand";
        var weights=left.boneWeights;
        for(int sub=0;sub<left.subMeshCount;sub++)
        {
            var source=left.GetTriangles(sub);var result=new List<int>();
            for(int i=0;i<source.Length;i+=3)if(weights[source[i]].boneIndex0!=2)result.AddRange(new[]{source[i],source[i+1],source[i+2]});
            left.SetTriangles(result,sub);
        }
        AssetDatabase.CreateAsset(left,"Assets/Art/First person left hand.asset");
        foreach(var path in new[]{"Assets/Scenes/IceCreamPrototype.unity","Assets/Scenes/ParkRoute.unity"})
        {
            var scene=EditorSceneManager.OpenScene(path);var r=PrototypeSceneReferences.Instance;var pose=r.player.GetComponent<FloatingHands>();
            pose.openHandsMesh=original;pose.leftHandMesh=left;pose.handsRenderer.sharedMesh=original;
            var go=new GameObject("Closed right hand");go.transform.SetParent(pose.handGrip,false);
            pose.closedHand=go.AddComponent<MeshFilter>();pose.closedHand.sharedMesh=small;
            go.AddComponent<MeshRenderer>().sharedMaterials=pose.handsRenderer.sharedMaterials;go.SetActive(false);
            r.scooper.handMesh=small;r.batter.handMesh=wide;r.shaker.handMesh=wide;r.boombox.handMesh=wide;
            EditorSceneManager.MarkSceneDirty(scene);EditorSceneManager.SaveScene(scene);
        }
        var prefab=PrefabUtility.LoadPrefabContents("Assets/Prefabs/IceCreamCone.prefab");prefab.GetComponent<PickupItem>().handMesh=coneGrip;
        PrefabUtility.SaveAsPrefabAsset(prefab,"Assets/Prefabs/IceCreamCone.prefab");PrefabUtility.UnloadPrefabContents(prefab);
        AssetDatabase.DeleteAsset("Assets/Art/FirstPersonGripHands.asset");AssetDatabase.SaveAssets();EditorSceneManager.OpenScene("Assets/Scenes/MainMenu.unity");
        return "Authored rounded closed grips and retained the open supporting hand for trays.";
    }
}
