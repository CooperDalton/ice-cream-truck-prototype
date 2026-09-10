var g=TycoonGameManager.Instance;var p=g.player;g.hud.ClosePanels();p.manualInput=false;p.inventory.slots[0]=new TycoonItem(TycoonItem.Kind.ImprovedScooper);p.Select(0);
var tub=g.Parts(0,TycoonPart.Kind.Tub).Single(t=>t.variant==0);p.Teleport(tub.operatingPoint.position+UnityEngine.Vector3.back*.2f);p.transform.rotation=UnityEngine.Quaternion.identity;
var direction=tub.handTarget.position-p.view.transform.position;p.pitch=UnityEngine.Quaternion.LookRotation(direction).eulerAngles.x;p.view.transform.localRotation=UnityEngine.Quaternion.Euler(p.pitch,0,0);p.Aim();
return new {target=p.target==null?"none":p.target.kind.ToString(),stock=tub.contents.amount,pitch=p.pitch};
