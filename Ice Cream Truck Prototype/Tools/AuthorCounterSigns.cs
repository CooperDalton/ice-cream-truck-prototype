using System;
using System.Collections.Generic;
using System.Linq;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using Object = UnityEngine.Object;

public static class AuthorCounterSigns
{
    private const string Folder="Assets/Art/Tycoon/Signs/";
    public static string[] Build()
    {
        if(EditorApplication.isPlaying)throw new Exception("Stop Play Mode before authoring signs");
        var scene=UnityEngine.SceneManagement.SceneManager.GetActiveScene();
        var g=scene.GetRootGameObjects()[0].GetComponent<TycoonGameManager>();
        var colors=new Dictionary<string,Color>{{"SignCream",new Color(.98f,.93f,.80f)},{"SignMint",new Color(.38f,.69f,.59f)},{"SignInk",new Color(.22f,.18f,.27f)}};
        var materials=new Dictionary<string,Material>();
        foreach(var pair in colors)
        {
            string path=Folder+pair.Key+".mat";var material=AssetDatabase.LoadAssetAtPath<Material>(path);
            if(material==null){material=new Material(Shader.Find("Ice Cream/Toon"));AssetDatabase.CreateAsset(material,path);}
            material.SetColor("_BaseColor",pair.Value);EditorUtility.SetDirty(material);materials.Add(pair.Key,material);
        }
        var models=new Dictionary<string,GameObject>();
        foreach(string label in new[]{"Order","Pickup"})
        {
            string path=Folder+label+"Sign.fbx";var importer=(ModelImporter)AssetImporter.GetAtPath(path);
            importer.isReadable=true;importer.importCameras=false;importer.importLights=false;importer.importAnimation=false;importer.SaveAndReimport();
            var root=new GameObject(label+" countertop sign");
            var model=(GameObject)PrefabUtility.InstantiatePrefab(AssetDatabase.LoadAssetAtPath<GameObject>(path),root.transform);
            foreach(var renderer in model.GetComponentsInChildren<MeshRenderer>())renderer.sharedMaterials=renderer.sharedMaterials.Select(m=>materials[m.name]).ToArray();
            models.Add(label,PrefabUtility.SaveAsPrefabAsset(root,Folder+label+"Sign.prefab"));Object.DestroyImmediate(root);
        }
        var evidence=new List<string>();
        foreach(int index in new[]{7,10,11})
        {
            string path=AssetDatabase.GetAssetPath(g.catalog.partPrefabs[index]);var root=PrefabUtility.LoadPrefabContents(path);
            try
            {
                foreach(var sign in root.GetComponentsInChildren<TycoonStationSign>(true))Object.DestroyImmediate(sign.gameObject);
                // Re-running the authoring step replaces the existing model prefab instance.
                foreach(Transform child in root.transform.Cast<Transform>().ToArray())if(models.Values.Contains(PrefabUtility.GetCorrespondingObjectFromOriginalSource(child.gameObject)))Object.DestroyImmediate(child.gameObject);
                string label=index==7?"Pickup":"Order";
                var model=(GameObject)PrefabUtility.InstantiatePrefab(models[label],root.transform);
                model.transform.localPosition=new Vector3(index==7?.35f:0,1,0);
                if(index==11){var box=root.GetComponent<BoxCollider>();box.center=new Vector3(0,1.1625f,0);box.size=new Vector3(.76f,.325f,.19f);}
                PrefabUtility.SaveAsPrefabAsset(root,path);evidence.Add(label+" sign authored on part "+index);
            }
            finally{PrefabUtility.UnloadPrefabContents(root);}
        }
        foreach(var part in g.parts.Where(p=>p.catalogIndex==7||p.catalogIndex==10||p.catalogIndex==11))
        {
            foreach(var sign in part.GetComponentsInChildren<TycoonStationSign>(true))Object.DestroyImmediate(sign.gameObject);
            var signs=part.transform.Cast<Transform>().Where(t=>models.Values.Contains(PrefabUtility.GetCorrespondingObjectFromOriginalSource(t.gameObject))).ToArray();
            foreach(var duplicate in signs.Skip(1))Object.DestroyImmediate(duplicate.gameObject);
            if(signs.Length==0)
            {
                var model=(GameObject)PrefabUtility.InstantiatePrefab(models[part.catalogIndex==7?"Pickup":"Order"],part.transform);
                model.transform.localPosition=new Vector3(part.catalogIndex==7?.35f:0,1,0);
            }
        }
        AssetDatabase.SaveAssets();EditorSceneManager.MarkSceneDirty(scene);EditorSceneManager.SaveScene(scene);return evidence.ToArray();
    }
}
