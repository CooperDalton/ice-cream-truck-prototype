var g=TycoonGameManager.Instance;var p=g.player;p.Aim();
var hits=UnityEngine.Physics.RaycastAll(p.view.transform.position,p.view.transform.forward,4);
return hits.Select(h=>"Hit "+h.collider.name+" "+h.distance+" "+h.collider.bounds).Concat(g.Parts(0,TycoonPart.Kind.Tub).Select(t=>"Tub "+t.variant+" "+t.GetComponent<UnityEngine.BoxCollider>().bounds)).ToArray();
