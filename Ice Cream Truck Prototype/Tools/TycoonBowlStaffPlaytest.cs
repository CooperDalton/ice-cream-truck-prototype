using System;
using System.Linq;
using UnityEngine;
using Object=UnityEngine.Object;

public static class TycoonBowlStaffPlaytest
{
    public static string Run()
    {
        var g=TycoonGameManager.Instance;g.restartRequested=true;g.player.manualInput=true;g.hud.ClosePanels();
        var table=g.parts.Single(p=>p.site==0&&p.kind==TycoonPart.Kind.Table);
        var bowls=g.parts.Where(p=>p.kind==TycoonPart.Kind.Bowl&&p.support==table).ToArray();
        Check(table.packed&&bowls.Length==2&&bowls.All(p=>!p.installed)&&bowls.Any(p=>p.contents.scoops.SequenceEqual(new[]{1})&&p.contents.toppings==2),"Packed bowls and recipe survive reload");
        var slot=Array.FindIndex(g.player.inventory.slots,i=>i!=null&&i.equipmentId==table.id);g.player.Select(slot);
        var position=table.transform.position;g.player.Teleport(position+Vector3.back*2);
        g.player.view.transform.rotation=Quaternion.LookRotation(position-g.player.view.transform.position);Physics.SyncTransforms();g.player.Aim();g.builder.AimPlacement(true);
        g.player.Use(false);Check(table.installed&&!table.packed&&bowls.All(p=>p.installed&&p.support==table),"Table and bowls unpack and rotate together");
        foreach(var c in g.actors.Where(c=>!c.worker).ToArray()){c.gameObject.SetActive(false);Object.Destroy(c.gameObject);g.actors.Remove(c);}foreach(var s in g.sites){s.open=false;s.queue.Clear();}
        var locker=g.AddPart(4,0,g.sites[0].origin.position+new Vector3(1.5f,0,-1.5f));
        locker.storage.slots[0]=new TycoonItem(TycoonItem.Kind.BasicScooper);locker.storage.slots[1]=new TycoonItem(TycoonItem.Kind.Bowls,12);locker.storage.slots[2]=new TycoonItem(TycoonItem.Kind.Topping,15,1);
        g.cash=500;g.Hire(0,0);var worker=g.workers.Last();worker.enabled=false;worker.actor.enabled=false;worker.onDuty=true;
        var tub=g.Parts(0,TycoonPart.Kind.Tub).First(p=>p.variant==0);tub.contents=new TycoonItem(TycoonItem.Kind.Tub,12,0);tub.claimedBy="";
        var customer=Object.Instantiate(g.catalog.customerPrefab,g.sites[0].pickupQueuePoint.position,Quaternion.identity);customer.game=g;customer.site=0;customer.enabled=false;
        customer.order=new TycoonOrder{id=g.nextId++,stage=TycoonOrder.Stage.Pickup,flavors=new[]{0},toppings=2,patience=120,patienceLimit=120};g.sites[0].queue.Add(customer);g.actors.Add(customer);customer.agent.Warp(customer.QueuePosition);
        g.phase=TycoonGameManager.Phase.Trading;g.clock=0;int beforeBowls=g.parts.Count(p=>p.kind==TycoonPart.Kind.Bowl);float money=g.cash;
        worker.Tick(0);Check(worker.prep.kind==TycoonPart.Kind.Bowl&&worker.prep.support.TableSurface,"Worker reserves bowl directly on table");
        for(int i=0;i<30&&!customer.leaving;i++)
        {
            Vector3 destination=worker.step==TycoonWorker.Step.Supplies?locker.operatingPoint.position:worker.step==TycoonWorker.Step.GoTub||worker.step==TycoonWorker.Step.Scoop?tub.operatingPoint.position:worker.step==TycoonWorker.Step.Serve?g.Parts(0,TycoonPart.Kind.ServingCounter).First().operatingPoint.position:worker.prep.operatingPoint.position;
            worker.actor.agent.Warp(destination);worker.Tick(10);
        }
        Check(customer.leaving&&g.cash>money&&worker.ticketId==-1,"Worker prepares and serves bowl: "+worker.status);
        Check(g.parts.Count(p=>p.kind==TycoonPart.Kind.Bowl)==beforeBowls,"Worker removes serving bowl after pickup");
        worker.onDuty=false;g.phase=TycoonGameManager.Phase.Preparation;g.Save();
        return "Packed table reloaded with two bowls and their recipes; placement restored and rotated all attachments. Staff reserved a table bowl, added vanilla and chocolate sauce, picked it up, served it, and removed the temporary bowl slot. Payment: "+(g.cash-money).ToString("0.00");
    }
    private static void Check(bool result,string message)
    {
        if(!result)throw new Exception(message);
    }
}
