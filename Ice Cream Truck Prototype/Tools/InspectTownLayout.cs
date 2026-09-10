var s=UnityEngine.SceneManagement.SceneManager.GetActiveScene();
var g=s.GetRootGameObjects().SelectMany(o=>o.GetComponents<TycoonGameManager>()).Single();
return string.Join("\n",g.sites.Select(t=>t.name+" "+t.origin.position+" "+t.plotSize))+"\n"+string.Join("\n",s.GetRootGameObjects().Where(o=>o.GetComponent<Renderer>()!=null||o.name.Contains("cottage")||o.name.Contains("Supplier")).Select(o=>o.name+" "+o.transform.position+" "+o.transform.localScale));
