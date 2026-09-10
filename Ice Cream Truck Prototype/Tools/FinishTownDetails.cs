var scene=UnityEngine.SceneManagement.SceneManager.GetActiveScene();
var g=scene.GetRootGameObjects().SelectMany(o=>o.GetComponents<TycoonGameManager>()).Single();var ui=g.hud;
var town=scene.GetRootGameObjects().Single(o=>o.name=="Town districts");
var centers=ui.roadCenters.ToList();var markers=ui.miniRoads.ToList();
foreach(var model in town.GetComponentsInChildren<UnityEngine.BoxCollider>().Where(c=>c.name.Contains("house")||c.name.Contains("cottage")||c.name.Contains("bakery")||c.name.Contains("cafe")||c.name.Contains("shop")))
{
    var bounds=model.bounds;var point=bounds.center;var size=new UnityEngine.Vector2(bounds.size.x,bounds.size.z);
    foreach(bool mini in new[]{false,true})
    {
        var obj=new UnityEngine.GameObject("Building footprint",typeof(UnityEngine.RectTransform),typeof(UnityEngine.UI.Image));var rect=obj.GetComponent<UnityEngine.RectTransform>();rect.SetParent(mini?ui.miniMarker.parent:ui.mapContent,false);rect.SetAsFirstSibling();
        obj.GetComponent<UnityEngine.UI.Image>().color=new UnityEngine.Color(.65f,.48f,.51f);obj.GetComponent<UnityEngine.UI.Image>().raycastTarget=false;
        if(mini){rect.sizeDelta=size/120*185;centers.Add(point);markers.Add(rect);}
        else{rect.anchoredPosition=new UnityEngine.Vector2((point.x-30)/130,(point.z-20)/110)*470;rect.sizeDelta=new UnityEngine.Vector2(size.x/130,size.y/110)*470;}
    }
}
ui.roadCenters=centers.ToArray();ui.miniRoads=markers.ToArray();
var residents=new UnityEngine.GameObject("Town residents");
UnityEngine.Vector3[][] routes={
    new[]{new UnityEngine.Vector3(13,0,12),new UnityEngine.Vector3(27,0,12),new UnityEngine.Vector3(27,0,28),new UnityEngine.Vector3(13,0,28)},
    new[]{new UnityEngine.Vector3(41,0,12),new UnityEngine.Vector3(55,0,12),new UnityEngine.Vector3(55,0,28),new UnityEngine.Vector3(41,0,28)},
    new[]{new UnityEngine.Vector3(72,0,13),new UnityEngine.Vector3(94,0,18),new UnityEngine.Vector3(94,0,31),new UnityEngine.Vector3(72,0,31)},
    new[]{new UnityEngine.Vector3(-3,0,12),new UnityEngine.Vector3(-3,0,20),new UnityEngine.Vector3(-3,0,32),new UnityEngine.Vector3(-3,0,40)}
};
var filter=new UnityEngine.AI.NavMeshQueryFilter{agentTypeID=g.navigation.agentTypeID,areaMask=UnityEngine.AI.NavMesh.AllAreas};
for(int r=0;r<routes.Length;r++)for(int i=0;i<3;i++)
{
    var actor=UnityEngine.Object.Instantiate(g.catalog.customerPrefab,residents.transform);actor.name="Resident "+r+" "+i;
    var walker=actor.gameObject.AddComponent<TycoonTownWalker>();walker.game=g;walker.agent=actor.agent;walker.body=actor.body;walker.stops=routes[r];walker.next=(i+1)%4;
    var point=routes[r][i];if(!UnityEngine.AI.NavMesh.SamplePosition(point,out var hit,2,filter))throw new System.Exception("Resident route off navigation: "+point);
    actor.transform.position=hit.position;walker.agent.speed=1.0f+i*.15f;walker.agent.enabled=false;UnityEngine.Object.DestroyImmediate(actor);
}
UnityEditor.SceneManagement.EditorSceneManager.SaveScene(scene);return "Authored building footprints on both maps and twelve town residents.";
