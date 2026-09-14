using System;
using System.Linq;
using System.Threading.Tasks;
using UnityEngine;

// Run against a backed-up campaign. Restores are handled by the test operator.
public static class TycoonLevelRewardPlaytest
{
    public static string Result { get; private set; } = "Not started";
    public static async void Start()
    {
        Result="Running";
        try
        {
            var game=TycoonGameManager.Instance;await Task.Delay(150);
            while(game.loadingCampaign)await Task.Delay(100);
            var player=game.player;var tutorial=game.tutorial;
            player.manualInput=true;game.restartRequested=true;
            game.cash=0;game.level=1;game.day=1;game.xp=60;game.phase=TycoonGameManager.Phase.Trading;
            tutorial.progress.step=TycoonTutorial.Step.FinishDay;tutorial.progress.rewardDeliverySeen=false;
            game.CloseDay();
            Check(game.level==2 && game.cash==0,"Level-up succeeds with no money");
            Check(game.parts.Count(p=>p.rewardDelivery)==2,"Tutorial level 2 delivers Strawberry and Mint holders");
            Check(game.looseItems.Count(l=>l.levelReward && l.item.kind==TycoonItem.Kind.Tub && l.item.amount==24)==2,"Each flavor includes one full 24-scoop tub");
            game.NextDay();game.hud.ClosePanels();game.hud.daySummary.gameObject.SetActive(false);await Task.Delay(150);
            game.Save();TycoonSave.Load(game);
            while(game.loadingCampaign)await Task.Delay(100);
            player.manualInput=true;tutorial.SendMessage("LateUpdate");
            Check(game.parts.Count(p=>p.rewardDelivery)==2 && game.looseItems.Count(l=>l.levelReward)==2,"Pending rewards survive reload without duplicates");
            Check(tutorial.focusMesh.gameObject.activeSelf && tutorial.caption.text=="New flavors","First delivery has a highlight and E prompt");
            var holder=game.parts.Single(p=>p.rewardDelivery && p.variant==2);
            for(int i=0;i<player.inventory.slots.Length;i++)player.inventory.slots[i]=new TycoonItem(TycoonItem.Kind.BasicScooper);
            holder.CollectReward(player);
            Check(holder.rewardDelivery && !tutorial.progress.rewardDeliverySeen,"Full inventory leaves the reward and highlight waiting");
            player.inventory=new TycoonInventory(8);player.Select(0);
            player.Teleport(holder.transform.position+Vector3.forward*1.6f);player.view.transform.LookAt(holder.transform.position+Vector3.up*.8f);Physics.SyncTransforms();player.Aim();
            Check(player.target==holder,"Player can aim at the delivered holder");player.Use(true);
            Check(holder.packed && !holder.rewardDelivery && player.Held.kind==TycoonItem.Kind.Equipment,"E collects holder into inventory");
            Check(tutorial.progress.rewardDeliverySeen,"First collection dismisses the delivery guide");
            var place=game.sites[0].origin.TransformPoint(new Vector3(2.25f,0,-1.75f));
            player.Teleport(place+Vector3.back*1.2f);player.view.transform.LookAt(place);Physics.SyncTransforms();player.Aim();game.builder.AimPlacement(false);player.Use(false);
            Check(holder.installed && !holder.packed && Vector3.Distance(holder.transform.position,place)<.05f,"Reward holder can be placed during day-two onboarding");
            var refill=game.looseItems.Single(l=>l.levelReward && l.item.variant==2);
            refill.Collect(player);player.target=holder;player.customerTarget=null;player.looseTarget=null;player.Use(false);
            Check(holder.contents.amount==24 && game.cash==0,"Free tub fills the placed holder without spending money");
            tutorial.progress.step=TycoonTutorial.Step.Complete;game.phase=TycoonGameManager.Phase.Trading;game.xp=300;game.CloseDay();
            Check(game.level==4 && game.parts.Count(p=>p.rewardDelivery && p.variant>=4)==4,"Later flavor unlocks deliver every new holder");
            Check(game.looseItems.Count(l=>l.levelReward && l.item.kind==TycoonItem.Kind.Tub && l.item.variant>=4 && l.item.amount==24)==4,"Later unlocks include a full tub per flavor");
            Check(game.looseItems.Count(l=>l.levelReward && l.item.kind==TycoonItem.Kind.Topping && l.item.amount==30)==2,"New toppings arrive at base with full supplies");
            int count=game.parts.Count+game.looseItems.Count;game.CloseDay();
            Check(game.parts.Count+game.looseItems.Count==count,"Repeated day close does not duplicate rewards");
            game.phase=TycoonGameManager.Phase.Preparation;tutorial.SendMessage("LateUpdate");
            Check(!tutorial.uiRoot.activeSelf,"Later deliveries do not repeat the first-time guide");
            Result="PASS: free tutorial and later rewards, full inventory, pickup, placement, refill, reload and one-time guidance.";
        }
        catch(Exception exception){Result="FAIL: "+exception;}
    }
    private static void Check(bool condition,string message)
    {
        if(!condition)throw new Exception(message);
        Debug.Log("Reward check: "+message);
    }
}
