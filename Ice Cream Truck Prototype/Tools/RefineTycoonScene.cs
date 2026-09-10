var scene=UnityEngine.SceneManagement.SceneManager.GetActiveScene();
var game=scene.GetRootGameObjects().SelectMany(o=>o.GetComponents<TycoonGameManager>()).Single();
foreach(var counter in game.parts.Where(p=>p.kind==TycoonPart.Kind.ServingCounter)) counter.transform.position=game.sites[counter.site].origin.position+new UnityEngine.Vector3(0,0,2.3f);
foreach(var site in game.sites) site.queuePoint.position=site.origin.position+new UnityEngine.Vector3(0,0,3.5f);
game.navigation.BuildNavMesh();
UnityEditor.SceneManagement.EditorSceneManager.SaveScene(scene);
return "Widened serving aisle and rebaked navigation.";
