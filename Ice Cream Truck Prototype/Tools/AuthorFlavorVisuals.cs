using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using Object = UnityEngine.Object;

public static class AuthorFlavorVisuals
{
    const string Folder = "Assets/Art/FlavorVisuals";
    static readonly string[] Chunky = { "Chocolate", "Mint", "Cookie cream", "Cherry", "Peach" };
    static void Save(Mesh mesh, string name)
    {
        mesh.name = name;
        AssetDatabase.CreateAsset(mesh, Folder + "/" + name + ".asset");
    }
    static Material Material(string name, string hex)
    {
        var material = new Material(Shader.Find("Universal Render Pipeline/Lit"));
        material.name = name;
        ColorUtility.TryParseHtmlString(hex, out var color);
        material.SetColor("_BaseColor", color); material.SetFloat("_Smoothness", .18f);
        AssetDatabase.CreateAsset(material, Folder + "/" + name + ".mat");
        return material;
    }
    static float Hit(Mesh mesh, Vector3 origin, Vector3 direction)
    {
        var vertices = mesh.vertices; var triangles = mesh.triangles;
        float closest = float.PositiveInfinity;
        for (int i = 0; i < triangles.Length; i += 3)
        {
            Vector3 a=vertices[triangles[i]], e1=vertices[triangles[i+1]]-a, e2=vertices[triangles[i+2]]-a;
            Vector3 h=Vector3.Cross(direction,e2); float determinant=Vector3.Dot(e1,h);
            if(Mathf.Abs(determinant)<1e-14f) continue;
            float inverse=1/determinant; Vector3 s=origin-a;
            float u=inverse*Vector3.Dot(s,h); if(u<0 || u>1) continue;
            Vector3 q=Vector3.Cross(s,e1); float v=inverse*Vector3.Dot(direction,q);
            if(v<0 || u+v>1) continue;
            float t=inverse*Vector3.Dot(e2,q); if(t>=0) closest=Mathf.Min(closest,t);
        }
        if(float.IsPositiveInfinity(closest)) throw new Exception("Chunk ray missed " + mesh.name);
        return closest;
    }
    static void Chip(List<Vector3> vertices, List<int> triangles, Vector3 center, Quaternion rotation, Vector3 size)
    {
        Vector3[] corners={new Vector3(-.5f,0,0),new Vector3(.5f,0,0),new Vector3(0,-.5f,0),new Vector3(0,.5f,0),new Vector3(.08f,.04f,.5f),new Vector3(-.08f,-.04f,-.5f)};
        int[] faces={0,2,4,2,1,4,1,3,4,3,0,4,2,0,5,1,2,5,3,1,5,0,3,5};
        for(int i=0;i<faces.Length;i++)
        {
            triangles.Add(vertices.Count);
            vertices.Add(center+rotation*Vector3.Scale(corners[faces[i]],size));
        }
    }
    static Mesh Mesh(List<Vector3> vertices,List<int> triangles)
    {
        var mesh=new Mesh();mesh.SetVertices(vertices);mesh.SetTriangles(triangles,0);
        mesh.RecalculateNormals();mesh.RecalculateBounds();return mesh;
    }
    static Mesh Scoop(Mesh plain)
    {
        var vertices=new List<Vector3>();var triangles=new List<int>();
        for(int i=0;i<32;i++)
        {
            float z=.98f-i*1.65f/31, angle=i*2.399963f, radius=Mathf.Sqrt(1-z*z);
            var direction=new Vector3(Mathf.Cos(angle)*radius,Mathf.Sin(angle)*radius,z);
            Vector3 point=plain.bounds.center+direction*Hit(plain,plain.bounds.center,direction);
            float size=.00022f*(.85f+.3f*(i%5)/4);
            Chip(vertices,triangles,point-direction*.00001f,Quaternion.FromToRotation(Vector3.forward,direction)*Quaternion.Euler(0,0,i*53),new Vector3(size,size*.8f,size*.55f));
        }
        var chips=Mesh(vertices,triangles);var result=new Mesh();
        result.CombineMeshes(new[]{new CombineInstance {mesh=plain,transform=Matrix4x4.identity},new CombineInstance {mesh=chips,transform=Matrix4x4.identity}},false);
        Object.DestroyImmediate(chips);return result;
    }
    static Mesh TubChunks(Mesh fill)
    {
        var vertices=new List<Vector3>();var triangles=new List<int>();var random=new System.Random(42);
        for(int y=0;y<4;y++) for(int x=0;x<5;x++)
        {
            float xx=Mathf.Lerp(fill.bounds.min.x*.83f,fill.bounds.max.x*.83f,(x+.15f+.7f*(float)random.NextDouble())/5);
            float yy=Mathf.Lerp(fill.bounds.min.y*.83f,fill.bounds.max.y*.83f,(y+.15f+.7f*(float)random.NextDouble())/4);
            Vector3 origin=new Vector3(xx,yy,fill.bounds.max.z+.001f);
            Vector3 point=origin-Vector3.forward*Hit(fill,origin,Vector3.back);
            float size=.00023f*(.8f+.35f*(float)random.NextDouble());
            Chip(vertices,triangles,point+Vector3.forward*.00001f,Quaternion.Euler(0,0,(float)random.NextDouble()*360),new Vector3(size,size*.75f,size*.6f));
        }
        return Mesh(vertices,triangles);
    }
    public static string RefineChunks()
    {
        var mesh=Scoop(AssetDatabase.LoadAssetAtPath<Mesh>("Assets/Art/PlainScoop.asset"));
        var saved=AssetDatabase.LoadAssetAtPath<Mesh>(Folder+"/ChunkyScoop.asset");
        EditorUtility.CopySerialized(mesh,saved);saved.name="ChunkyScoop";EditorUtility.SetDirty(saved);
        AssetDatabase.SaveAssets();Object.DestroyImmediate(mesh);return "Enlarged scoop chunks";
    }
    public static string Build()
    {
        if(EditorApplication.isPlaying) throw new Exception("Stop Play Mode first");
        Directory.CreateDirectory(Folder);AssetDatabase.Refresh();
        var plain=AssetDatabase.LoadAssetAtPath<Mesh>("Assets/Art/PlainScoop.asset");
        var scoop=Scoop(plain);Save(scoop,"ChunkyScoop");
        var chocolate=Material("Chocolate chunks","#30201A");
        var cherry=Material("Cherry pieces","#921C3D");
        var peach=Material("Peach pieces","#DF713C");
        foreach(var guid in AssetDatabase.FindAssets("t:FlavorSO",new[]{"Assets/Settings"}))
        {
            var f=AssetDatabase.LoadAssetAtPath<FlavorSO>(AssetDatabase.GUIDToAssetPath(guid));
            f.chunkMaterial=Chunky.Contains(f.displayName)?f.displayName=="Cherry"?cherry:f.displayName=="Peach"?peach:chocolate:null;
            f.scoopMesh=f.chunkMaterial==null?plain:scoop;EditorUtility.SetDirty(f);
        }
        var cone=PrefabUtility.LoadPrefabContents("Assets/Prefabs/IceCreamCone.prefab");
        var coneScript=cone.GetComponent<IceCreamCone>();
        coneScript.scoopFilters=coneScript.scoopRenderers.Select(r=>r.GetComponent<MeshFilter>()).ToArray();
        PrefabUtility.SaveAsPrefabAsset(cone,"Assets/Prefabs/IceCreamCone.prefab");PrefabUtility.UnloadPrefabContents(cone);
        foreach(var path in new[]{"Assets/Scenes/IceCreamPrototype.unity","Assets/Scenes/ParkRoute.unity"})
        {
            var scene=EditorSceneManager.OpenScene(path);var r=PrototypeSceneReferences.Instance;
            r.scooper.loadedScoopFilter=r.scooper.loadedScoopRenderer.GetComponent<MeshFilter>();
            foreach(var tub in r.tubs)
            {
                if(tub.flavor.chunkMaterial==null)continue;
                var filters=tub.GetComponentsInChildren<MeshFilter>();
                var fill=filters.Single(f=>f.name.StartsWith("IceCream_Fill"));
                var shell=filters.Single(f=>f!=fill);
                if(shell.sharedMesh.subMeshCount>1)
                {
                    string shellPath=Folder+"/"+tub.flavor.displayName+" tub shell.asset";
                    var clean=AssetDatabase.LoadAssetAtPath<Mesh>(shellPath);
                    if(clean==null){clean=Object.Instantiate(shell.sharedMesh);clean.subMeshCount=1;Save(clean,tub.flavor.displayName+" tub shell");}
                    shell.sharedMesh=clean;
                    var shellRenderer=shell.GetComponent<MeshRenderer>();shellRenderer.sharedMaterials=new[]{shellRenderer.sharedMaterials[0]};
                }
                string chunksPath=Folder+"/"+tub.flavor.displayName+" tub chunks.asset";
                var chunks=AssetDatabase.LoadAssetAtPath<Mesh>(chunksPath);
                if(chunks==null){chunks=TubChunks(fill.sharedMesh);Save(chunks,tub.flavor.displayName+" tub chunks");}
                var go=new GameObject("Flavor chunks");go.transform.SetParent(fill.transform,false);
                go.AddComponent<MeshFilter>().sharedMesh=chunks;go.AddComponent<MeshRenderer>().sharedMaterial=tub.flavor.chunkMaterial;
            }
            EditorSceneManager.MarkSceneDirty(scene);EditorSceneManager.SaveScene(scene);
        }
        AssetDatabase.SaveAssets();EditorSceneManager.OpenScene("Assets/Scenes/MainMenu.unity");
        return "Authored five chunky flavors, seven plain flavors, shared scoop visuals, and matching chunks in both scenes.";
    }
}
