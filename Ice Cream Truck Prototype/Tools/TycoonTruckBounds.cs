var scene=UnityEngine.SceneManagement.SceneManager.GetActiveScene();
var g=scene.GetRootGameObjects().SelectMany(o=>o.GetComponents<TycoonGameManager>()).Single();
var renderers=g.truck.GetComponentsInChildren<UnityEngine.Renderer>(true);var bounds=renderers[0].bounds;
foreach(var r in renderers)bounds.Encapsulate(r.bounds);
return "Truck position="+g.truck.transform.position+" bounds="+bounds+" player="+g.player.transform.position;
