var g=TycoonGameManager.Instance;g.player.manualInput=true;
g.CloseDay();g.NextDay();g.cash=2000;g.level=3;g.sites[0].expanded=true;
g.BuyUpgrade(1,0);g.Hire(0,0);
if(!g.BuyUpgrade(7,0))throw new System.Exception(g.notice);
foreach(var tub in g.Parts(2,TycoonPart.Kind.Tub))tub.contents.amount=24;
var locker=g.Parts(2,TycoonPart.Kind.Locker).Single();
locker.storage.slots[0]=new TycoonItem(TycoonItem.Kind.ImprovedScooper);
locker.storage.slots[1]=new TycoonItem(TycoonItem.Kind.Bowls,12);
locker.storage.slots[2]=new TycoonItem(TycoonItem.Kind.Batter,10);
locker.storage.slots[3]=new TycoonItem(TycoonItem.Kind.Topping,15,0);
locker.storage.slots[4]=new TycoonItem(TycoonItem.Kind.Topping,15,1);
g.Hire(2,2,true);
var driver=g.workers.Single(w=>w.driver);
var filter=new UnityEngine.AI.NavMeshQueryFilter{agentTypeID=driver.actor.agent.agentTypeID,areaMask=UnityEngine.AI.NavMesh.AllAreas};
var evidence=new System.Collections.Generic.List<string>();
foreach(var part in g.parts.Where(p=>p.site==2&&p.installed&&p.kind!=TycoonPart.Kind.Truck))
{
    bool found=UnityEngine.AI.NavMesh.SamplePosition(part.operatingPoint.position,out var hit,.3f,filter);
    var path=new UnityEngine.AI.NavMeshPath();bool reachable=found&&UnityEngine.AI.NavMesh.CalculatePath(driver.transform.position,hit.position,filter,path);
    evidence.Add(part.kind+" operator="+part.operatingPoint.position+" sampled="+found+" reachable="+reachable+" path="+path.status);
}
evidence.Add("Layout="+driver.ValidateLayout()+" / "+driver.status);
g.player.Teleport(g.truck.transform.position+new UnityEngine.Vector3(-6,0,4));g.player.transform.rotation=UnityEngine.Quaternion.Euler(0,115,0);g.player.view.transform.localRotation=UnityEngine.Quaternion.Euler(5,0,0);
UnityEngine.ScreenCapture.CaptureScreenshot("Library/CodexPlaytests/TycoonTruckFitted.png");
return evidence;
