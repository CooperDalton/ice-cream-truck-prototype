using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Threading.Tasks;
using UnityEngine;
using Object=UnityEngine.Object;
public static class PickupPhysicsPlaytest
{
    static List<string> checks;
    static PrototypeSceneReferences r;
    public static async Task<string> Run()
    {
        r=PrototypeSceneReferences.Instance;checks=new List<string>();
        r.player.ManualInput=r.interaction.ManualInput=r.truck.ManualInput=r.customers.ManualInput=true;
        r.day.enabled=false;
        var cone=Object.Instantiate(r.waffle.conePrefab);
        var items=new[]{r.batter,r.shaker,r.scooper,(PickupItem)r.boombox,cone};
        int index=0;
        foreach(var item in items)
        {
            r.player.Teleport(null,new Vector3(-8+index++*1.5f,0,-7),Quaternion.Euler(0,180,0));
            Check(r.interaction.PickUp(item),item.name+" picked up");
            var handPosition=item.transform.position;
            r.interaction.ProcessInput(false,false,false,true,Vector2.zero,.02f);
            Check(r.interaction.Held==null && !item.body.isKinematic && item.pickupCollider.enabled,item.name+" right click enables physics");
            Check(Vector3.Distance(handPosition,item.transform.position)<.01f,item.name+" releases at hand position");
            await Steps(12);
            Check(item.transform.position.y<handPosition.y-.05f,item.name+" falls under gravity");
            await Steps(130);
            Check(item.pickupCollider.bounds.min.y>-.12f && item.pickupCollider.bounds.min.y<.2f,item.name+" rests on ground at "+item.pickupCollider.bounds.min.y.ToString("F3"));
            r.player.view.transform.LookAt(item.pickupCollider.bounds.center);
            r.interaction.ProcessInput(true,false,false,false,Vector2.zero,.02f);
            Check(r.interaction.Held==item && item.body.isKinematic,item.name+" is picked up where it landed");
            item.Drop(r.interaction);
            await Steps(30);
        }
        r.interaction.PickUp(r.batter);
        r.batter.Drop(r.interaction);
        r.day.TogglePause();await Steps(2);
        var paused=r.batter.transform.position;
        await Steps(30);
        Check(r.batter.body.isKinematic && Vector3.Distance(paused,r.batter.transform.position)<.001f,"Pause freezes a falling item");
        r.day.TogglePause();await Steps(12);
        Check(!r.batter.body.isKinematic && r.batter.transform.position.y<paused.y-.05f,"Resume continues the fall");
        r.interaction.PickUp(r.shaker);
        r.player.Teleport(r.truck.transform,r.truck.kitchen.position,r.truck.kitchen.rotation);
        var inside=r.shaker.transform.position;
        r.shaker.Drop(r.interaction);
        await Steps(150);
        Check(r.shaker.pickupCollider.bounds.min.y>.45f,"Shaker lands on truck floor or counter");
        Check(r.shaker.transform.parent==r.truck.transform,"Loose shaker remains in truck's moving frame");
        Vector3 local=r.truck.transform.InverseTransformPoint(r.shaker.transform.position);
        for(int i=0;i<50;i++)
        {
            r.truck.FollowRoute(r.truck.transform.position+Vector3.right*.1f,r.truck.transform.rotation,5);
            Physics.SyncTransforms();await Steps(1);
        }
        r.truck.FollowRoute(r.truck.transform.position,r.truck.transform.rotation,0);
        Check(Vector3.Distance(local,r.truck.transform.InverseTransformPoint(r.shaker.transform.position))<.3f,"Dropped shaker travels with truck for five metres");
        string report=string.Join("\n",checks);Directory.CreateDirectory("Library/CodexPlaytests");File.WriteAllText("Library/CodexPlaytests/pickup-physics.txt",report);
        return report;
    }
    static async Task Steps(int count)
    {
        for(int i=0;i<count;i++)await Awaitable.FixedUpdateAsync();
    }
    static void Check(bool pass,string message)
    {
        if(!pass)throw new Exception(message);
        checks.Add("PASS: "+message);
    }
}
