using System;
using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using UnityEngine;
using UnityEngine.AI;
using Object = UnityEngine.Object;

public static class TycoonOrderFlowPlaytest
{
    private static TycoonGameManager g;
    private static List<string> checks;
    public static string Run()
    {
        g = TycoonGameManager.Instance; checks = new List<string>();
        g.restartRequested = true; g.player.manualInput = true; g.hud.ClosePanels(); g.phase = TycoonGameManager.Phase.Trading; g.clock = 0;
        foreach (var site in g.sites) { site.open = false; site.queue.Clear(); }
        foreach (var w in g.workers) w.onDuty = false;
        foreach (var c in g.actors.Where(c=>!c.worker).ToArray()) { c.gameObject.SetActive(false); Object.Destroy(c.gameObject); g.actors.Remove(c); }
        g.player.inventory = new TycoonInventory(8); g.player.selected = 0;
        var customer = Spawn();
        HUD(); Check(g.hud.tickets.All(t=>!t.root.activeSelf), "Arriving customers do not create tickets");
        customer.TickPatience(1); Check(customer.order.patience == 89, "Greeting patience starts when customer reaches queue");
        Aim(customer); Check(g.player.customerTarget == customer && g.player.prompt == "E / take order", "Camera ray hits customer above register and offers E to take order");
        g.player.Use(false); Check(customer.order.stage == TycoonOrder.Stage.Ordering, "Left-click does not take orders");
        g.player.inventory.slots[0] = Serving(customer); g.player.customerTarget = null; g.player.target = g.Parts(0,TycoonPart.Kind.ServingCounter).First();
        float money = g.cash; g.player.Use(false); Check(g.cash == money && g.player.Held != null, "Cannot deliver an order before taking it");
        Aim(customer); g.player.Use(true); HUD();
        Check(customer.order.stage == TycoonOrder.Stage.Pickup && customer.order.patience == 120 && g.hud.tickets.Count(t=>t.root.activeSelf)==1, "E creates ticket, resets patience and switches to pickup queue");
        Check(!customer.ReadyForPickup && Vector3.Distance(customer.agent.destination,g.sites[0].pickupQueuePoint.position)<.1f, "Customer must walk to the separate pickup counter");
        g.player.customerTarget = null; g.player.target = g.Parts(0,TycoonPart.Kind.ServingCounter).First(); g.player.Use(false);
        Check(g.cash == money, "No delivery while customer is still walking to pickup");
        customer.agent.Warp(customer.QueuePosition);
        foreach (var row in new[] { new[] { 61f,2.4f },new[] {60f,2.4f},new[] {30f,1.2f},new[] {0f,0f} })
        {
            customer.order.patience = row[0]; HUD();
            Check(Mathf.Approximately(customer.order.Tip(0),row[1]) && g.hud.tickets[0].title.text=="6" && !g.hud.tickets[0].root.GetComponentsInChildren<UnityEngine.UI.Text>(true).Any(t=>t.text.Contains("tip")), "Patience "+row[0]+"/120 keeps $6 on ticket and hides the calculated $"+row[1]+" tip");
        }
        float previousTip = 2.4f;
        for(int seconds=120;seconds>=0;seconds--) { customer.order.patience=seconds; float tip=customer.order.Tip(0); if(tip>previousTip || tip<0 || tip>2.4f)throw new Exception("Tip outside bounds at "+seconds);previousTip=tip; }
        Check(true,"Tip is bounded and monotonically decreases over the complete 120-second timer");
        customer.TickPatience(200); Check(!customer.leaving && customer.order.patience==0, "Accepted order stays at pickup after patience reaches zero");
        g.player.inventory.slots[0] = new TycoonItem(TycoonItem.Kind.Serving){scoops=new[]{1}};
        g.player.Use(false); Check(g.cash==money && !customer.leaving, "Wrong recipe is rejected without money or item loss");
        g.player.inventory.slots[0] = Serving(customer); g.player.Use(false); HUD();
        Check(customer.leaving && g.player.Held==null && Mathf.Approximately(g.cash-money,6) && g.hud.salePopupBackground.color==customer.order.RewardColor, "Expired pickup pays full $6 base price and shows neutral zero-tip reward");
        foreach (var row in new[] { new[] {120f,8.4f}, new[] {50f,8f}, new[] {20f,6.8f} })
        {
            var c = Spawn(); c.TakeOrder(); c.agent.Warp(c.QueuePosition); c.order.patience=row[0];
            g.player.inventory.slots[0]=Serving(c); g.player.customerTarget=null; g.player.target=g.Parts(0,TycoonPart.Kind.ServingCounter).First();
            money=g.cash; g.player.Use(false); Check(c.leaving && Mathf.Approximately(g.cash-money,row[1]), "Delivery at "+row[0]+" seconds pays $"+row[1]);
        }
        var forgotten=Spawn(); int lost=g.sites[0].lostSales; forgotten.TickPatience(91); HUD();
        Check(forgotten.leaving && g.sites[0].lostSales==lost+1 && g.hud.tickets.All(t=>!t.root.activeSelf), "Ungreeted customer leaves and records one lost sale without a ticket");
        forgotten.TickPatience(91); Check(g.sites[0].lostSales==lost+1,"Expired greeting counts only once");
        var first=Spawn(); var second=Spawn(); second.agent.Warp(second.QueuePosition);
        Check(!second.ReadyToOrder && Vector3.Distance(first.QueuePosition,second.QueuePosition)>.8f,"Greeting queue prevents skipping ahead");
        first.TakeOrder(); Check(Vector3.Distance(second.QueuePosition,g.sites[0].queuePoint.position)<.01f,"Taking first order advances the greeting queue");
        first.agent.Warp(first.QueuePosition); second.agent.Warp(second.QueuePosition); second.TakeOrder(); second.agent.Warp(second.QueuePosition);
        Check(Vector3.Distance(first.QueuePosition,second.QueuePosition)>.8f,"Accepted customers occupy separate pickup queue slots");
        float remaining=first.order.patience; g.hud.menuOpen=true; first.TickPatience(10); g.hud.menuOpen=false;
        Check(first.order.patience==remaining,"Pause freezes patience");
        var roundtrip=JsonUtility.FromJson<TycoonOrder>(JsonUtility.ToJson(second.order));
        Check(roundtrip.stage==TycoonOrder.Stage.Pickup && roundtrip.startedWaiting && roundtrip.patienceLimit==120,"Order phase and timer survive serialization");
        g.player.inventory.slots[0]=Serving(first); Aim(first); money=g.cash; g.player.Use(true);
        Check(first.leaving && g.player.Held==null && g.cash>money,"E delivers the held matching order directly to a pickup customer");
        foreach(var s in g.sites.Select((site,index)=>new {site,index}))
        {
            var path=new NavMeshPath(); var filter=new NavMeshQueryFilter {agentTypeID=second.agent.agentTypeID,areaMask=NavMesh.AllAreas};
            if(s.index==2)continue;
            Check(NavMesh.CalculatePath(s.site.queuePoint.position,s.site.pickupQueuePoint.position,filter,path)&&path.status==NavMeshPathStatus.PathComplete,s.site.name+" has a complete register-to-pickup walking path");
            Check(NavMesh.CalculatePath(g.Parts(s.index,TycoonPart.Kind.ServingCounter).First().operatingPoint.position,s.site.registerOperatingPoint.position,filter,path)&&path.status==NavMeshPathStatus.PathComplete,s.site.name+" staff can reach register");
        }
        g.hud.ClosePanels(); HUD();
        return string.Join("\n",checks);
    }
    private static TycoonActor Spawn()
    {
        var c=Object.Instantiate(g.catalog.customerPrefab,g.sites[0].queuePoint.position,Quaternion.identity);
        c.game=g;c.site=0;c.order=new TycoonOrder {id=g.nextId++,flavors=new[]{0},patience=90,patienceLimit=90};c.enabled=false;
        g.sites[0].queue.Add(c);g.actors.Add(c);c.agent.Warp(c.QueuePosition);return c;
    }
    private static TycoonItem Serving(TycoonActor c)
    {
        return new TycoonItem(TycoonItem.Kind.Serving){cone=c.order.cone,scoops=(int[])c.order.flavors.Clone(),toppings=c.order.toppings};
    }
    private static void Aim(TycoonActor c)
    {
        var spot=c.order.stage==TycoonOrder.Stage.Ordering?g.sites[0].registerOperatingPoint.position:g.Parts(0,TycoonPart.Kind.ServingCounter).First().operatingPoint.position;
        g.player.Teleport(spot);g.player.view.transform.rotation=Quaternion.LookRotation(c.transform.position+Vector3.up*1.45f-g.player.view.transform.position);
        Physics.SyncTransforms();g.player.Aim();g.builder.AimPlacement(false);
    }
    private static void HUD()
    {
        typeof(TycoonHUD).GetMethod("Update",BindingFlags.Instance|BindingFlags.NonPublic).Invoke(g.hud,null);
        UnityEngine.Canvas.ForceUpdateCanvases();
    }
    private static void Check(bool condition,string message)
    {
        if(!condition)throw new Exception("FAIL: "+message+"\n"+string.Join("\n",checks));checks.Add("PASS: "+message);
    }
}
