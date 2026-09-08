using System;
using System.Collections.Generic;
using UnityEngine;

public static class PrototypePlaytest
{
    static PrototypeSceneReferences r;
    static List<string> checks;
    static void Check(bool value,string message)
    {
        if(!value) throw new Exception("PLAYTEST FAILED: "+message);
        checks.Add(message);
    }
    static void Aim(Interactable target)
    {
        Vector3 pos = target.transform.position;
        r.player.controller.enabled=false;
        r.player.transform.position = new Vector3(Mathf.Clamp(pos.x + (target is IceCreamTub ? .65f : 0),-2.8f,.8f),.64f,target is Customer ? .60f : .10f);
        r.player.controller.enabled=true;
        Physics.SyncTransforms();
        Vector3 aim=target.GetComponent<Collider>().bounds.center;
        if(target is Customer) aim.y=1.85f;
        r.interaction.view.transform.LookAt(aim);
        Physics.SyncTransforms();
        r.interaction.ProcessInput(false,false,false,false,Vector2.zero,.02f);
        Check(r.interaction.Target==target,"Ray reaches "+target.name+" (hit "+(r.interaction.Target==null?"none":r.interaction.Target.name)+")");
    }
    static void Use(Interactable target)
    {
        Aim(target);r.interaction.ProcessInput(true,false,false,false,Vector2.zero,.02f);
    }
    static void Hold(Interactable target,int frames,bool move)
    {
        Aim(target);
        r.interaction.ProcessInput(true,true,false,false,Vector2.zero,.02f);
        for(int i=0;i<frames;i++) r.interaction.ProcessInput(false,true,false,false,move?new Vector2(0,i%2==0?20:-20):Vector2.zero,.02f);
        r.interaction.ProcessInput(false,false,true,false,Vector2.zero,.02f);
    }
    static void PutDown()
    {
        r.interaction.ProcessInput(false,false,false,true,Vector2.zero,.02f);
        Check(r.interaction.Held==null,"Tool returns to its home");
    }
    static IceCreamCone MakeCone()
    {
        if(!r.waffle.IsOpen) Use(r.waffle);
        Use(r.batter);Hold(r.waffle,90,false);Check(r.waffle.State==WaffleMaker.CookState.BatterReady,"Infinite batter fills waffle maker");PutDown();
        Use(r.waffle);Check(r.waffle.State==WaffleMaker.CookState.Cooking,"Closing filled iron starts cooking");
        r.waffle.Advance(r.day.settings.cookSeconds+.1f);Check(r.waffle.State==WaffleMaker.CookState.Ready,"Waffle becomes ready after cook duration");
        Use(r.waffle);Use(r.waffle);Check(r.interaction.Held is IceCreamCone,"Finished waffle becomes a held cone");
        var cone=(IceCreamCone)r.interaction.Held;Use(r.holders[2]);Check(r.holders[2].Occupant==cone,"Cone snaps into holder");return cone;
    }
    public static object Preparation()
    {
        r=PrototypeSceneReferences.Instance;checks=new List<string>();r.player.ManualInput=true;r.interaction.ManualInput=true;
        var cone=MakeCone();
        Use(r.scooper);Hold(r.tubs[0],70,false);Check(r.scooper.LoadedFlavor==null,"Holding without mouse movement cannot produce a scoop");
        for(int i=0;i<3;i++)
        {
            Hold(r.tubs[i],70,true);Check(r.scooper.LoadedFlavor==r.tubs[i].flavor,"Mouse gesture loads correct flavor "+i);
            Use(cone);Check(cone.Flavors.Count==i+1,"Cone accepts scoop "+(i+1));
        }
        Hold(r.tubs[0],70,true);Use(cone);Check(cone.Flavors.Count==3 && r.scooper.LoadedFlavor!=null,"Fourth scoop rejected without losing loaded scoop");
        PutDown();Use(r.shaker);Hold(cone,60,true);Check(cone.HasSprinkles,"Shake gesture adds visible sprinkles");PutDown();Use(cone);Check(r.interaction.Held==cone && r.holders[2].Occupant==null,"Three-scoop cone can be picked up and frees holder");
        return new {checks,flavors=cone.Flavors.Count,sprinkles=cone.HasSprinkles};
    }
    public static object ServeAndFailures()
    {
        r=PrototypeSceneReferences.Instance;checks=new List<string>();r.player.ManualInput=true;r.interaction.ManualInput=true;
        var cone=(IceCreamCone)r.interaction.Held;
        var customer=r.customers.Front ?? r.customers.SpawnCustomer();
        customer.Advance(20);
        Check(customer.Arrived || Vector3.Distance(customer.transform.position,r.customers.queuePoints[0].position)<.05f,"Customer walks to service queue");
        customer.Advance(.02f);
        int before=r.day.Earnings;
        Use(customer);Check(r.day.Earnings==before && r.interaction.Held==cone,"Wrong order is rejected without taking cone or paying");
        customer.Initialize(r.customers,new List<FlavorSO>(cone.Flavors),true);
        Use(customer);Check(r.interaction.Held==null && r.day.Earnings==before+12 && customer.Leaving,"Correct three-scoop order pays $12 and customer leaves");
        var one=MakeCone();Use(r.scooper);
        if(r.scooper.LoadedFlavor!=null) {Use(r.bin);Check(r.scooper.LoadedFlavor==null,"Discard bin empties loaded scooper");}
        Hold(r.tubs[1],70,true);Use(one);PutDown();Use(one);
        var next=r.customers.Front ?? r.customers.SpawnCustomer();next.Initialize(r.customers,new List<FlavorSO>{r.tubs[1].flavor},false);next.Advance(20);next.Advance(.02f);
        before=r.day.Earnings;Use(next);Check(r.day.Earnings==before+5,"One-scoop order pays $5");
        if(!r.waffle.IsOpen)Use(r.waffle);Use(r.batter);Hold(r.waffle,90,false);PutDown();Use(r.waffle);
        r.waffle.Advance(r.day.settings.cookSeconds+r.day.settings.burnGraceSeconds+.1f);Check(r.waffle.State==WaffleMaker.CookState.Burned,"Leaving waffle past grace time burns it");
        Use(r.waffle);Use(r.waffle);Check(r.waffle.State==WaffleMaker.CookState.Empty,"Burned waffle can be discarded and iron reused");
        var impatient=r.customers.Front ?? r.customers.SpawnCustomer();int lost=r.day.CustomersLost;impatient.Advance(r.day.settings.customerPatience+1);Check(impatient.Leaving && r.day.CustomersLost==lost+1,"Impatient customer leaves the queue");
        float elapsed=r.day.Elapsed;r.day.TogglePause();r.day.Advance(20);Check(r.day.Elapsed==elapsed && !r.day.CanPlay,"Pause freezes day and blocks interactions");r.day.TogglePause();
        return new {checks,earnings=r.day.Earnings,served=r.day.OrdersServed,lost=r.day.CustomersLost};
    }

    public static object TwoScoopsMovementAndClosing()
    {
        r=PrototypeSceneReferences.Instance;checks=new List<string>();r.player.ManualInput=true;r.interaction.ManualInput=true;
        var two=MakeCone();Use(r.scooper);
        for(int i=0;i<2;i++){Hold(r.tubs[i],70,true);Use(two);}PutDown();Use(two);
        var customer=r.customers.Front ?? r.customers.SpawnCustomer();customer.Initialize(r.customers,new List<FlavorSO>(two.Flavors),false);customer.Advance(20);customer.Advance(.02f);
        int before=r.day.Earnings;Use(customer);Check(r.day.Earnings==before+8,"Two-scoop order pays $8");
        r.player.controller.enabled=false;r.player.transform.SetPositionAndRotation(new Vector3(9,.3f,6),Quaternion.identity);r.player.controller.enabled=true;
        Physics.SyncTransforms();Vector3 start=r.player.transform.position;float min=10,max=0;
        for(int i=0;i<90;i++){r.player.Move(Vector2.up,Vector2.zero,.02f);if(i>15){min=Mathf.Min(min,r.player.view.transform.localPosition.y);max=Mathf.Max(max,r.player.view.transform.localPosition.y);}}
        Check(Vector3.Distance(start,r.player.transform.position)>3,"Walking moves character through colliders");
        Check(max-min>.01f,"Grounded walking produces head bob");
        bool bob=r.day.settings.headBob;r.day.settings.headBob=false;
        for(int i=0;i<60;i++)r.player.Move(Vector2.up,Vector2.zero,.02f);
        Check(Mathf.Abs(r.player.view.transform.localPosition.y-1.55f)<.001f,"Head bob can be disabled in settings");r.day.settings.headBob=bob;
        r.day.Advance(r.day.settings.dayDurationSeconds-r.day.Elapsed-.1f);Check(r.day.Phase==DayManager.DayPhase.Open,"Day remains open just before 6 PM");
        r.day.Advance(.11f);Check(r.day.Phase==DayManager.DayPhase.Closed && Mathf.Abs(r.day.Hour-18)<.001f,"Day ends at exactly 6 PM");
        before=r.day.Earnings;Check(!r.day.RecordSale(100) && r.day.Earnings==before,"No payments accepted after closing");
        var testSettings=UnityEngine.Object.Instantiate(r.day.settings);testSettings.quota=10;
        var go=new GameObject("Quota success test");var success=go.AddComponent<DayManager>();success.settings=testSettings;success.RecordSale(10);success.Advance(testSettings.dayDurationSeconds);
        Check(success.Phase==DayManager.DayPhase.Closed && success.Earnings>=success.settings.quota,"Meeting an editable quota succeeds at closing");UnityEngine.Object.Destroy(go);UnityEngine.Object.Destroy(testSettings);
        return new{checks,bobRange=max-min,earnings=r.day.Earnings,hour=r.day.Hour};
    }

}
