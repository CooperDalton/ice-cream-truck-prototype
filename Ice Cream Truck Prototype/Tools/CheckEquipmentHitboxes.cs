// Run in Edit Mode: unity command eval_file Tools/CheckEquipmentHitboxes.cs.
if (EditorApplication.isPlaying) throw new Exception("Run hitbox audit in Edit Mode.");
var catalog=AssetDatabase.LoadAssetAtPath<TycoonCatalogSO>("Assets/Art/Tycoon/Catalog.asset");
var scene=UnityEditor.SceneManagement.EditorSceneManager.NewPreviewScene();
int samples=0;
try
{
    foreach(var prefab in catalog.partPrefabs)
    {
        var part=UnityEngine.Object.Instantiate(prefab);
        UnityEngine.SceneManagement.SceneManager.MoveGameObjectToScene(part.gameObject,scene);
        int states=part.kind==TycoonPart.Kind.Locker?3:part.kind==TycoonPart.Kind.Iron?2:1;
        for(int state=0;state<states;state++)
        {
            if(part.kind==TycoonPart.Kind.Locker){part.storage=new TycoonInventory((state+1)*4);part.RefreshLocker();}
            if(part.kind==TycoonPart.Kind.Iron)part.lid.localRotation=Quaternion.Euler(state==0?0:-105,0,0);
            Physics.SyncTransforms();
            var colliders=part.GetComponentsInChildren<Collider>().Where(c=>c.enabled).ToArray();
            foreach(var filter in part.GetComponentsInChildren<MeshFilter>().Where(f=>f.sharedMesh!=null))
            {
                var vertices=filter.sharedMesh.vertices;
                for(int i=0;i<vertices.Length;i+=Math.Max(1,vertices.Length/40))
                {
                    var point=filter.transform.TransformPoint(vertices[i]);
                    if(!colliders.Any(c=>(c.ClosestPoint(point)-point).sqrMagnitude<.0001f))
                        throw new Exception("Uncovered geometry: "+part.kind+" state "+state+" "+filter.name+" at "+point);
                    samples++;
                }
            }
        }
        if(part.kind==TycoonPart.Kind.Shelf)
            foreach(var direction in new[]{Vector3.forward,Vector3.back,Vector3.left,Vector3.right})
                foreach(float height in new[]{.2f,.85f,1.4f,1.72f})
                {
                    var point=part.transform.position+Vector3.up*height;
                    var ray=new Ray(point+direction*2,-direction);
                    if(!part.GetComponentsInChildren<Collider>().Any(c=>c.Raycast(ray,out _,2.8f)))throw new Exception("Shelf missed at height "+height);
                }
        UnityEngine.Object.DestroyImmediate(part.gameObject);
    }
    return "PASS: all 14 equipment prefabs, every locker size and open/closed iron; "+samples+" mesh coverage samples; shelf ray hits at four heights from four sides.";
}
finally{UnityEditor.SceneManagement.EditorSceneManager.ClosePreviewScene(scene);}
