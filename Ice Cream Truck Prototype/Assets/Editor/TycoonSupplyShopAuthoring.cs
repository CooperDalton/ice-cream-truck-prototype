using System;
using System.Collections.Generic;
using System.Linq;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using Object = UnityEngine.Object;

public static class TycoonSupplyShopAuthoring
{
    private const string Folder = "Assets/Art/Tycoon/";
    [MenuItem("Ice Cream/Author walk-in supplier and hanging signs")]
    public static void Build()
    {
        if (EditorApplication.isPlaying) throw new InvalidOperationException("Stop Play Mode before authoring the supplier.");
        var scene = UnityEngine.SceneManagement.SceneManager.GetActiveScene();
        var game = scene.GetRootGameObjects()[0].GetComponent<TycoonGameManager>();
        var shop = Model("Supplier_storefront");
        Box(shop, new Vector3(0,.10f,0), new Vector3(6,.2f,4));
        Box(shop, new Vector3(0,1.75f,-1.94f), new Vector3(6,3.3f,.12f));
        foreach (float x in new[] {-2.94f,2.94f}) Box(shop, new Vector3(x,1.75f,0), new Vector3(.12f,3.3f,4));
        foreach (float x in new[] {-2.55f,2.55f}) Box(shop, new Vector3(x,1.75f,1.94f), new Vector3(.9f,3.3f,.15f));
        Box(shop, new Vector3(0,3.05f,1.94f), new Vector3(6,.7f,.15f));
        Box(shop, new Vector3(-1.65f,.69f,0), new Vector3(2.05f,.96f,1.45f));
        var shopPrefab = PrefabUtility.SaveAsPrefabAsset(shop, Folder + "Prefabs/Supplier_storefront.prefab"); Object.DestroyImmediate(shop);
        Object.DestroyImmediate(game.supplierBuilding);
        game.supplierBuilding = (GameObject)PrefabUtility.InstantiatePrefab(shopPrefab);
        game.supplierBuilding.transform.position = game.supplier.position;
        var terminal = game.parts.Single(p => p.kind == TycoonPart.Kind.Supplier);
        terminal.transform.SetPositionAndRotation(game.supplier.position + new Vector3(1.5f,.2f,.65f), Quaternion.identity);
        terminal.operatingPoint.localPosition = new Vector3(0,-.2f,1);
        game.pickupPoint.position = game.supplier.position + new Vector3(-1.65f,1.18f,0);
        foreach (var old in game.supplyPickupPoints ?? Array.Empty<Transform>()) Object.DestroyImmediate(old.gameObject);
        var pickups = new List<Transform>();
        for (int z=0; z<2; z++) for (int x=0; x<3; x++)
        {
            var point = new GameObject("Collection spot " + (pickups.Count + 1)).transform;
            point.SetParent(game.pickupPoint, false); point.localPosition = new Vector3((x-1)*.61f,0,(z-.5f)*.62f);
            pickups.Add(point);
        }
        game.supplyPickupPoints = pickups.ToArray();

        var signModel = Model("Open_closed_sign");
        var signPrefab = PrefabUtility.SaveAsPrefabAsset(signModel, Folder + "Prefabs/Open_closed_sign.prefab"); Object.DestroyImmediate(signModel);
        const string signPath = Folder + "Prefabs/Part_6.prefab";
        var signRoot = PrefabUtility.LoadPrefabContents(signPath);
        var sign = signRoot.GetComponent<TycoonPart>();
        Object.DestroyImmediate(sign.signModel.gameObject);
        sign.signModel = ((GameObject)PrefabUtility.InstantiatePrefab(signPrefab, signRoot.transform)).transform;
        var collider = signRoot.GetComponent<BoxCollider>(); collider.center = Vector3.zero; collider.size = new Vector3(1.24f,.62f,.18f);
        var labels = new List<TextMesh>();
        for (int side=0; side<2; side++)
        {
            var label = new GameObject(side==0 ? "Street face" : "Shop face", typeof(TextMesh)).GetComponent<TextMesh>();
            label.transform.SetParent(sign.signModel, false);
            label.transform.localPosition = new Vector3(0,0,side==0 ? .087f : -.087f);
            label.transform.localRotation = Quaternion.Euler(0,side==0 ? 180 : 0,0);
            label.text = "CLOSED"; label.font = game.hud.money.font; label.fontSize = 80; label.characterSize = .03f;
            label.anchor = TextAnchor.MiddleCenter; label.alignment = TextAlignment.Center;
            label.color = new Color(.25f,.2f,.29f); label.GetComponent<Renderer>().sharedMaterial = label.font.material;
            labels.Add(label);
        }
        sign.signLabels = labels.ToArray(); PrefabUtility.SaveAsPrefabAsset(signRoot, signPath); PrefabUtility.UnloadPrefabContents(signRoot);
        for (int i=0; i<game.sites.Length; i++)
        {
            var site = game.sites[i];
            if (site.signMount == null) { site.signMount = new GameObject("Hanging sign mount " + i).transform; site.signMount.SetParent(site.origin,false); }
            site.signMount.localPosition = new Vector3(-2.8f,1.88f,3.11f);
            foreach (var installed in game.parts.Where(p=>p.site==i && p.kind==TycoonPart.Kind.Sign))
                installed.transform.SetPositionAndRotation(site.signMount.position, site.signMount.rotation);
        }
        game.hud.openButton.gameObject.SetActive(false);
        EditorUtility.SetDirty(game); EditorSceneManager.MarkSceneDirty(scene); EditorSceneManager.SaveScene(scene);
        game.navigation.BuildNavMesh(); TycoonTutorialAuthoring.AddNavigation();
        AssetDatabase.SaveAssets(); EditorSceneManager.SaveScene(scene);
    }
    private static void Box(GameObject root, Vector3 center, Vector3 size)
    {
        var box = root.AddComponent<BoxCollider>();
        box.center = center; box.size = size;
    }
    private static GameObject Model(string name)
    {
        AssetDatabase.ImportAsset(Folder + "Models/" + name + ".fbx", ImportAssetOptions.ForceSynchronousImport);
        var model = AssetDatabase.LoadAssetAtPath<GameObject>(Folder + "Models/" + name + ".fbx");
        var root = new GameObject(name);
        var groups = new Dictionary<Material,List<CombineInstance>>();
        foreach (var filter in model.GetComponentsInChildren<MeshFilter>(true))
        {
            var materials = filter.GetComponent<Renderer>().sharedMaterials;
            for (int i=0; i<filter.sharedMesh.subMeshCount; i++)
            {
                var source = materials[i]; var safe = string.Concat(source.name.Select(c=>char.IsLetterOrDigit(c)?c:'_'));
                string path = Folder + "Materials/" + safe + ".mat";
                var material = AssetDatabase.LoadAssetAtPath<Material>(path);
                if (material == null) { material = new Material(Shader.Find("Ice Cream/Toon")); material.SetColor("_BaseColor", source.color); AssetDatabase.CreateAsset(material,path); }
                if (!groups.ContainsKey(material)) groups[material] = new List<CombineInstance>();
                groups[material].Add(new CombineInstance {mesh=filter.sharedMesh, subMeshIndex=i, transform=filter.transform.localToWorldMatrix});
            }
        }
        foreach (var group in groups)
        {
            string path = Folder + "Meshes/" + name + "_" + group.Key.name + ".asset";
            var mesh = AssetDatabase.LoadAssetAtPath<Mesh>(path);
            if (mesh == null) { mesh = new Mesh(); AssetDatabase.CreateAsset(mesh,path); }
            mesh.Clear(); mesh.indexFormat = UnityEngine.Rendering.IndexFormat.UInt32; mesh.CombineMeshes(group.Value.ToArray()); EditorUtility.SetDirty(mesh);
            var piece = new GameObject(group.Key.name,typeof(MeshFilter),typeof(MeshRenderer)); piece.transform.SetParent(root.transform,false);
            piece.GetComponent<MeshFilter>().sharedMesh = mesh; piece.GetComponent<Renderer>().sharedMaterial = group.Key;
        }
        return root;
    }
}
