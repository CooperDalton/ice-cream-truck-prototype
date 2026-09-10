var g=TycoonGameManager.Instance;var filter=new UnityEngine.AI.NavMeshQueryFilter{agentTypeID=g.navigation.agentTypeID,areaMask=UnityEngine.AI.NavMesh.AllAreas};
var results=new System.Collections.Generic.List<string>();
foreach(var p in g.parts.Where(p=>p.installed&&p.site<2&&p.operatingPoint!=null&&p.kind!=TycoonPart.Kind.Plot))
{
    var start=g.sites[p.site].queuePoint.position;var end=p.operatingPoint.position;var path=new UnityEngine.AI.NavMeshPath();
    bool ok=UnityEngine.AI.NavMesh.SamplePosition(start,out var a,2,filter)&&UnityEngine.AI.NavMesh.SamplePosition(end,out var b,.4f,filter)&&UnityEngine.AI.NavMesh.CalculatePath(a.position,b.position,filter,path)&&path.status==UnityEngine.AI.NavMeshPathStatus.PathComplete;
    results.Add(p.site+" / "+p.kind+" "+end+" "+ok);
}
var scene=UnityEngine.SceneManagement.SceneManager.GetActiveScene();var walkers=scene.GetRootGameObjects().Single(o=>o.name=="Town residents").GetComponentsInChildren<TycoonTownWalker>();
foreach(var walker in walkers)results.Add(walker.name+" "+walker.agent.pathStatus+" moving "+walker.agent.velocity.magnitude.ToString("0.00"));
System.IO.File.WriteAllLines("Library/CodexPlaytests/TownNavigation.txt",results);return string.Join("\n",results);
