var scene=UnityEngine.SceneManagement.SceneManager.GetActiveScene();
var g=scene.GetRootGameObjects().SelectMany(o=>o.GetComponents<TycoonGameManager>()).Single();
foreach(var prefab in g.catalog.tubs)
{
    string path=UnityEditor.AssetDatabase.GetAssetPath(prefab);var root=UnityEditor.PrefabUtility.LoadPrefabContents(path);
    var visual=root.GetComponent<TycoonTubVisual>()??root.AddComponent<TycoonTubVisual>();
    visual.fill=root.GetComponentsInChildren<UnityEngine.Transform>().Single(t=>t.name=="Fill").GetComponentsInChildren<UnityEngine.Renderer>();
    UnityEditor.PrefabUtility.SaveAsPrefabAsset(root,path);UnityEditor.PrefabUtility.UnloadPrefabContents(root);
}
string partPath=UnityEditor.AssetDatabase.GetAssetPath(g.catalog.partPrefabs[1]);
var partRoot=UnityEditor.PrefabUtility.LoadPrefabContents(partPath);var component=partRoot.GetComponent<TycoonPart>();
component.tubModel=component.fillRenderers[0].transform.parent.parent.gameObject;
UnityEditor.PrefabUtility.SaveAsPrefabAsset(partRoot,partPath);UnityEditor.PrefabUtility.UnloadPrefabContents(partRoot);
foreach(var tub in g.Parts(0,TycoonPart.Kind.Tub).Concat(g.Parts(1,TycoonPart.Kind.Tub)).Concat(g.Parts(2,TycoonPart.Kind.Tub)))tub.tubModel=tub.fillRenderers[0].transform.parent.parent.gameObject;
var bar=UnityEngine.Object.Instantiate(g.hud.useBar.transform.parent.gameObject,g.hud.useBar.transform.parent.parent);
bar.name="Target stock";bar.GetComponent<UnityEngine.RectTransform>().anchoredPosition=new UnityEngine.Vector2(0,-230);
g.hud.targetStockBar=bar.GetComponentsInChildren<UnityEngine.UI.Image>().Single(i=>i.type==UnityEngine.UI.Image.Type.Filled);
UnityEditor.SceneManagement.EditorSceneManager.SaveScene(scene);UnityEditor.AssetDatabase.SaveAssets();
return "Authored flavor-specific tub fill references and target supply bar.";
