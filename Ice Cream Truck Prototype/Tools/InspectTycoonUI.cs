var scene=UnityEngine.SceneManagement.SceneManager.GetActiveScene();
var g=scene.GetRootGameObjects().SelectMany(o=>o.GetComponents<TycoonGameManager>()).Single();
var text=g.hud.money; var r=text.rectTransform;
return new { text.text,text.enabled,active=text.gameObject.activeInHierarchy,font=text.font.name,scale=r.lossyScale,pos=r.position,anchorMin=r.anchorMin,anchorMax=r.anchorMax,rect=r.rect,canvas=g.hud.GetComponent<UnityEngine.Canvas>().renderMode,slots=g.player.inventory.slots.Select(i=>i==null?"null":i.kind.ToString()).ToArray() };
