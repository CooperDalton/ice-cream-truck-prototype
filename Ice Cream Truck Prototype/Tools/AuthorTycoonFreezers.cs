var scene=UnityEngine.SceneManagement.SceneManager.GetActiveScene();
var g=scene.GetRootGameObjects().SelectMany(o=>o.GetComponents<TycoonGameManager>()).Single();
g.catalog.flatWaffle=UnityEditor.AssetDatabase.LoadAssetAtPath<UnityEngine.GameObject>("Assets/Art/Tycoon/Prefabs/Flat_baked_waffle.prefab");
var cooled=UnityEditor.AssetDatabase.LoadAssetAtPath<UnityEngine.GameObject>("Assets/Art/Tycoon/Prefabs/1_well_cooled_module.prefab");
string prefabPath=UnityEditor.AssetDatabase.GetAssetPath(g.catalog.partPrefabs[1]);var prefab=UnityEditor.PrefabUtility.LoadPrefabContents(prefabPath);
var p=prefab.GetComponent<TycoonPart>();p.tabletop=false;p.contents.amount=0;p.tubModel.transform.localPosition=UnityEngine.Vector3.up*.722f;p.operatingPoint.localPosition=new UnityEngine.Vector3(0,0,-.9f);p.handTarget.localPosition=new UnityEngine.Vector3(0,.9f,0);
var box=p.GetComponent<UnityEngine.BoxCollider>();box.center=new UnityEngine.Vector3(0,.475f,0);box.size=new UnityEngine.Vector3(.5f,.95f,.5f);
UnityEngine.Object.Instantiate(cooled,prefab.transform);
UnityEditor.PrefabUtility.SaveAsPrefabAsset(prefab,prefabPath);UnityEditor.PrefabUtility.UnloadPrefabContents(prefab);
var tubs=g.parts.Where(t=>t.kind==TycoonPart.Kind.Tub).ToArray();var supports=tubs.Where(t=>t.support!=null).Select(t=>t.support).Distinct().ToArray();
foreach(var tub in tubs)
{
    tub.transform.SetParent(null,true);tub.transform.position=new UnityEngine.Vector3(tub.transform.position.x,0,tub.transform.position.z);tub.support=null;tub.tabletop=false;
    tub.operatingPoint.localPosition=new UnityEngine.Vector3(0,0,-.9f);tub.handTarget.localPosition=new UnityEngine.Vector3(0,.9f,0);tub.tubModel.transform.localPosition=UnityEngine.Vector3.up*.722f;
    var collider=tub.GetComponent<UnityEngine.BoxCollider>();collider.center=new UnityEngine.Vector3(0,.475f,0);collider.size=new UnityEngine.Vector3(.5f,.95f,.5f);
}
foreach(var support in supports){g.parts.Remove(support);UnityEngine.Object.DestroyImmediate(support.gameObject);}
UnityEditor.EditorUtility.SetDirty(g.catalog);g.navigation.BuildNavMesh();UnityEditor.SceneManagement.EditorSceneManager.SaveScene(scene);UnityEditor.AssetDatabase.SaveAssets();
return "Installed cooled floor modules with separate refillable tubs; level rewards arrive as parts for grid placement.";
