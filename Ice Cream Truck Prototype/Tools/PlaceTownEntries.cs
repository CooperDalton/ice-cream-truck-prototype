var scene=UnityEngine.SceneManagement.SceneManager.GetActiveScene();var g=scene.GetRootGameObjects().SelectMany(o=>o.GetComponents<TycoonGameManager>()).Single();
UnityEngine.Vector3[] points={new(-9,0,-19),new(15,0,-19),new(37,0,-20),new(71,0,-20),new(94,0,18),new(94,0,52),new(38,0,53),new(-3,0,38)};
var filter=new UnityEngine.AI.NavMeshQueryFilter{agentTypeID=g.navigation.agentTypeID,areaMask=UnityEngine.AI.NavMesh.AllAreas};
for(int i=0;i<points.Length;i++)
{
    if(!UnityEngine.AI.NavMesh.SamplePosition(points[i],out var hit,.5f,filter))throw new System.Exception("Entry is blocked: "+points[i]);
    foreach(var site in g.sites.Take(2))
    {
        var path=new UnityEngine.AI.NavMeshPath();if(!UnityEngine.AI.NavMesh.CalculatePath(hit.position,site.queuePoint.position,filter,path)||path.status!=UnityEngine.AI.NavMeshPathStatus.PathComplete)throw new System.Exception("Entry cannot reach "+site.name);
    }
    g.spawnPoints[i].position=hit.position;
}
UnityEditor.SceneManagement.EditorSceneManager.SaveScene(scene);return "All eight customer entries reach both stands without spawning inside the new buildings.";
