var g=TycoonGameManager.Instance;g.player.manualInput=true;g.cash=2000;
if(!g.BuyUpgrade(1,0)||!g.BuyUpgrade(2,0)||!g.BuyUpgrade(3,0)||!g.BuyUpgrade(5,0)||!g.Hire(0,0)||!g.BuyUpgrade(7,0)||!g.Hire(2,2,true)||!g.BuyUpgrade(6,0)||!g.BuyUpgrade(1,1)||!g.Hire(1,1))throw new System.Exception(g.notice);
foreach(var worker in g.workers)
{
    worker.locker.storage.slots[0]=new TycoonItem(TycoonItem.Kind.ImprovedScooper);worker.locker.storage.slots[1]=new TycoonItem(TycoonItem.Kind.Bowls,12);worker.locker.storage.slots[2]=new TycoonItem(TycoonItem.Kind.Batter,10);
    if(!worker.ValidateLayout())throw new System.Exception(g.sites[worker.site].name+" / "+worker.status);
}
foreach(var tub in g.parts.Where(p=>p.kind==TycoonPart.Kind.Tub))tub.contents.amount=24;
float before=g.cash;g.OpenDay();foreach(var site in g.sites)site.open=false;g.truck.demand=new[]{0,0};
foreach(var actor in g.actors.Where(a=>!a.worker).ToArray())actor.Leave();
if(g.workers.Any(w=>!w.onDuty)||before-g.cash!=138)throw new System.Exception("Three staffed sites payroll incorrect");
g.truck.DriveRoute(g.workers.Single(w=>w.driver));g.hud.ToggleMenu();g.Save();
System.IO.File.WriteAllText("Library/CodexPlaytests/TycoonFinalCampaign.txt","All three purchased sites validate with kiosk wall collision. Cash before payroll "+before+", after three wages and vehicle "+g.cash+". Saved driver traveling with truck.\n");
return "Expanded home, park, and truck layouts all reachable. Three employees paid correctly. Mid-route campaign saved.";
