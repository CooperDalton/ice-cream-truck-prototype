using System;
using System.Collections.Generic;
using System.Linq;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;
using Object = UnityEngine.Object;

public static class AuthorTycoonPlacement
{
    private const string Folder = "Assets/Art/Tycoon/Placement";
    public static string Build()
    {
        if (EditorApplication.isPlaying) throw new Exception("Stop Play Mode before authoring placement assets");
        var scene = UnityEngine.SceneManagement.SceneManager.GetActiveScene();
        var g = scene.GetRootGameObjects()[0].GetComponent<TycoonGameManager>();
        var b = g.builder; var catalog = g.catalog;
        if (!AssetDatabase.IsValidFolder(Folder)) AssetDatabase.CreateFolder("Assets/Art/Tycoon", "Placement");
        b.validMaterial = Material("Valid", "Ice Cream/Placement Ghost", new Color(1,1,1,.72f));
        b.invalidMaterial = Material("Invalid", "Ice Cream/Placement Ghost", new Color(1,.12f,.12f,.65f));
        var gridMaterial = Material("Grid", "Ice Cream/Placement Grid", Color.white);
        var bowlVisual = new GameObject("Bowl visual");
        var model = Object.Instantiate(catalog.bowl,bowlVisual.transform); model.transform.localPosition=Vector3.zero; model.transform.localRotation=Quaternion.identity;
        var bowlMesh = Bake(bowlVisual);
        float bowlBottom = bowlMesh.bounds.min.y;
        Object.DestroyImmediate(bowlMesh);
        model.transform.localPosition = Vector3.down * bowlBottom;
        int bowlIndex = Array.FindIndex(catalog.partPrefabs,p=>p.kind==TycoonPart.Kind.Bowl);
        if (bowlIndex < 0)
        {
            bowlIndex=catalog.partPrefabs.Length;Array.Resize(ref catalog.partPrefabs,bowlIndex+1);Array.Resize(ref catalog.equipmentIcons,bowlIndex+1);
            var root=new GameObject("Tabletop bowl");var part=root.AddComponent<TycoonPart>();part.kind=TycoonPart.Kind.Bowl;part.catalogIndex=bowlIndex;part.tabletop=true;part.footprint=new Vector2(.25f,.25f);
            part.contentPoint=Point(root.transform,"Contents",Vector3.down*bowlBottom);
            part.handTarget=Point(root.transform,"Hand target",new Vector3(0,.1f,0));part.operatingPoint=Point(root.transform,"Operating point",new Vector3(0,-.94f,-.9f));
            var box=root.AddComponent<BoxCollider>();box.center=new Vector3(0,.065f,0);box.size=new Vector3(.22f,.13f,.22f);
            var prefab=PrefabUtility.SaveAsPrefabAsset(root,"Assets/Art/Tycoon/Prefabs/Part_"+bowlIndex+".prefab");catalog.partPrefabs[bowlIndex]=prefab.GetComponent<TycoonPart>();catalog.equipmentIcons[bowlIndex]=catalog.bowlIcon;Object.DestroyImmediate(root);
        }
        b.bowlPrefab=catalog.partPrefabs[bowlIndex];catalog.placementPreviews=new GameObject[catalog.partPrefabs.Length];
        var evidence=new List<string>();
        for(int i=0;i<catalog.partPrefabs.Length;i++)
        {
            var part=catalog.partPrefabs[i];
            var mesh=Bake(i==bowlIndex?bowlVisual:part.gameObject);
            string meshPath=Folder+"/Mesh_"+i+".asset";
            var existing=AssetDatabase.LoadAssetAtPath<Mesh>(meshPath);
            if(existing==null)AssetDatabase.CreateAsset(mesh,meshPath);else{EditorUtility.CopySerialized(mesh,existing);Object.DestroyImmediate(mesh);mesh=existing;}
            var ghost=new GameObject(part.kind+" preview");ghost.layer=2;
            ghost.AddComponent<MeshFilter>().sharedMesh=mesh;var renderer=ghost.AddComponent<MeshRenderer>();renderer.sharedMaterial=b.validMaterial;renderer.shadowCastingMode=ShadowCastingMode.Off;renderer.receiveShadows=false;
            catalog.placementPreviews[i]=PrefabUtility.SaveAsPrefabAsset(ghost,Folder+"/Preview_"+i+".prefab");Object.DestroyImmediate(ghost);
            evidence.Add(i+" "+part.kind+" "+mesh.vertexCount+" vertices, bounds "+mesh.bounds);
        }
        Object.DestroyImmediate(bowlVisual);
        Object.DestroyImmediate(b.preview);b.preview=new GameObject("Placement model preview");b.preview.layer=2;b.preview.SetActive(false);b.previewRenderer=null;
        if(b.gridRenderer!=null)Object.DestroyImmediate(b.gridRenderer.gameObject);
        var grid=new GameObject("Surface placement grid");grid.layer=2;
        var plane=new Mesh {name="Placement grid"};plane.vertices=new[]{new Vector3(-.5f,0,-.5f),new Vector3(.5f,0,-.5f),new Vector3(.5f,0,.5f),new Vector3(-.5f,0,.5f)};
        plane.uv=new[]{Vector2.zero,Vector2.right,Vector2.one,Vector2.up};plane.triangles=new[]{0,2,1,0,3,2};plane.RecalculateNormals();plane.RecalculateBounds();
        var oldPlane=AssetDatabase.LoadAssetAtPath<Mesh>(Folder+"/Grid.asset");if(oldPlane==null)AssetDatabase.CreateAsset(plane,Folder+"/Grid.asset");else{EditorUtility.CopySerialized(plane,oldPlane);Object.DestroyImmediate(plane);plane=oldPlane;}
        grid.AddComponent<MeshFilter>().sharedMesh=plane;b.gridRenderer=grid.AddComponent<MeshRenderer>();b.gridRenderer.sharedMaterial=gridMaterial;b.gridRenderer.shadowCastingMode=ShadowCastingMode.Off;b.gridRenderer.receiveShadows=false;grid.SetActive(false);
        EditorUtility.SetDirty(b);EditorUtility.SetDirty(catalog);AssetDatabase.SaveAssets();EditorSceneManager.MarkSceneDirty(scene);EditorSceneManager.SaveScene(scene);
        return string.Join("\n",evidence);
    }
    private static Mesh Bake(GameObject source,bool signs=true)
    {
        var pieces=new List<CombineInstance>();
        foreach(var filter in source.GetComponentsInChildren<MeshFilter>())
        {
            if(!filter.GetComponent<MeshRenderer>().enabled)continue;
            for(int sub=0;sub<filter.sharedMesh.subMeshCount;sub++)pieces.Add(new CombineInstance{mesh=filter.sharedMesh,subMeshIndex=sub,transform=source.transform.worldToLocalMatrix*filter.transform.localToWorldMatrix});
        }
        var temporary=new List<Mesh>();
        if(signs)foreach(var face in source.GetComponentsInChildren<UnityEngine.UI.Image>())
        {
            var corners=new Vector3[4];face.rectTransform.GetWorldCorners(corners);
            for(int i=0;i<4;i++)corners[i]=source.transform.InverseTransformPoint(corners[i]);
            var quad=new Mesh();quad.vertices=corners;quad.triangles=new[]{0,1,2,0,2,3,2,1,0,3,2,0};quad.normals=Enumerable.Repeat(Vector3.Cross(corners[1]-corners[0],corners[2]-corners[0]).normalized,4).ToArray();temporary.Add(quad);
            pieces.Add(new CombineInstance{mesh=quad,transform=Matrix4x4.identity});
        }
        var mesh=new Mesh {indexFormat=IndexFormat.UInt32};mesh.CombineMeshes(pieces.ToArray(),true,true);mesh.RecalculateBounds();
        foreach(var temporaryMesh in temporary)Object.DestroyImmediate(temporaryMesh);
        return mesh;
    }
    private static Material Material(string name,string shader,Color color)
    {
        string path=Folder+"/"+name+".mat";var material=AssetDatabase.LoadAssetAtPath<Material>(path);
        if(material==null){material=new Material(Shader.Find(shader));AssetDatabase.CreateAsset(material,path);}else material.shader=Shader.Find(shader);
        if(material.HasProperty("_BaseColor"))material.SetColor("_BaseColor",color);EditorUtility.SetDirty(material);return material;
    }
    private static Transform Point(Transform parent,string name,Vector3 position)
    {
        var point=new GameObject(name).transform;point.SetParent(parent,false);point.localPosition=position;return point;
    }
}
