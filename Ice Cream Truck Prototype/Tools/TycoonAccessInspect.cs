var g=TycoonGameManager.Instance;var messages=new System.Collections.Generic.List<string>();
foreach(var p in g.parts.Where(p=>p.site==0&&p.kind==TycoonPart.Kind.ServingCounter))
{
    UnityEngine.AI.NavMesh.SamplePosition(p.operatingPoint.position,out var near,2,UnityEngine.AI.NavMesh.AllAreas);
    var path=new UnityEngine.AI.NavMeshPath();bool ok=UnityEngine.AI.NavMesh.CalculatePath(g.workers[0].transform.position,near.position,UnityEngine.AI.NavMesh.AllAreas,path);
    messages.Add(p.kind+" root="+p.transform.position+" target="+p.operatingPoint.position+" nearest="+near.position+" distance="+near.distance+" path="+ok+" "+path.status+" bounds="+p.GetComponent<UnityEngine.BoxCollider>().bounds);
}
return messages;
