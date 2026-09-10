var g=TycoonGameManager.Instance;g.restartRequested=true;g.player.manualInput=true;g.phase=TycoonGameManager.Phase.Preparation;
var bike=g.bike;var start=bike.transform.position;bike.Enter();
UnityEngine.Vector3[] route={new(-4,0,-7),new(5,0,-7),new(5,0,-12),new(29,0,-12),new(29,0,-21),new(29,0,-24)};
foreach(var point in route.Concat(route.Reverse()).Concat(new[]{start}))
{
    for(int i=0;i<250&&UnityEngine.Vector3.Distance(bike.transform.position,point)>.8f;i++)
    {
        bike.transform.rotation=UnityEngine.Quaternion.LookRotation(point-bike.transform.position);UnityEngine.Physics.SyncTransforms();bike.Drive(UnityEngine.Vector2.up,.05f);
    }
    if(UnityEngine.Vector3.Distance(bike.transform.position,point)>1)throw new System.Exception("Bicycle blocked on new town route at "+bike.transform.position+" going to "+point);
}
bike.Exit();
var roads=new[]{new UnityEngine.Vector3(12,1.8f,-12),new UnityEngine.Vector3(62,1.8f,-12),new UnityEngine.Vector3(64,1.8f,-12),new UnityEngine.Vector3(64,1.8f,46),new UnityEngine.Vector3(5,1.8f,46)};
var collisions=new System.Collections.Generic.List<string>();
for(int i=0;i<roads.Length-1;i++)
{
    var delta=roads[i+1]-roads[i];foreach(var hit in UnityEngine.Physics.SphereCastAll(roads[i],1.3f,delta.normalized,delta.magnitude,~0,UnityEngine.QueryTriggerInteraction.Ignore))if(hit.collider.transform.root.name=="Town districts")collisions.Add(hit.collider.name);
}
if(collisions.Count>0)throw new System.Exception("Scenery intersects truck route: "+string.Join(",",collisions));
System.IO.File.WriteAllText("Library/CodexPlaytests/TownVehicleAccess.txt","Bicycle drove from home along the streets to the supplier pickup and back. Truck route swept volume is clear of new scenery.\n");return "Supply trip and both truck stops remain accessible.";
