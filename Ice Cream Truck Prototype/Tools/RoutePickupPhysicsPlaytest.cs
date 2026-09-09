using System;
using System.Linq;
using System.Threading.Tasks;
using UnityEngine;
using Object=UnityEngine.Object;
public static class RoutePickupPhysicsPlaytest
{
    public static async Task<string> Run()
    {
        var r=PrototypeSceneReferences.Instance;
        r.player.ManualInput=r.interaction.ManualInput=r.truck.ManualInput=true;
        r.route.ManualInput=true;
        r.route.ToggleMap();
        var tray=r.route.tray;
        var cone=Object.Instantiate(r.waffle.conePrefab);
        cone.Restore(new[]{r.route.stock.flavors[0]},false);
        tray.Store(cone);
        r.player.Teleport(null,new Vector3(-8,0,-5),Quaternion.identity);
        r.interaction.PickUp(tray);
        var start=tray.transform.position;
        r.interaction.ProcessInput(false,false,false,true,Vector2.zero,.02f);
        if(Vector3.Distance(start,tray.transform.position)>.01f||tray.body.isKinematic)throw new Exception("Tray did not physically drop");
        for(int i=0;i<150;i++)await Awaitable.FixedUpdateAsync();
        if(tray.pickupCollider.bounds.min.y<-.2f||tray.pickupCollider.bounds.min.y>.2f)throw new Exception("Tray did not land on ground");
        if(tray.Cones.Count!=1||cone.transform.parent!=tray.slots[0])throw new Exception("Stored cone lost during tray drop");
        r.player.view.transform.LookAt(tray.pickupCollider.bounds.center);
        r.interaction.ProcessInput(true,false,false,false,Vector2.zero,.02f);
        if(r.interaction.Held!=tray||!tray.body.isKinematic)throw new Exception("Could not pick tray back up");
        tray.Drop(r.interaction);
        r.player.Teleport(null,r.truck.transform.TransformPoint(new Vector3(-1.1f,0,3.4f)),Quaternion.identity);
        r.interaction.PickUp(r.batter);
        r.player.view.transform.LookAt(r.truck.transform.TransformPoint(new Vector3(-1.1f,1.46f,2.2f)));
        Physics.SyncTransforms();
        r.interaction.ProcessInput(false,false,false,false,Vector2.zero,.02f);
        if(!r.interaction.CanPlace)throw new Exception("Counter preview failed");
        r.interaction.ProcessInput(false,false,false,true,Vector2.zero,.02f);
        if(r.interaction.Held!=null||r.batter.body.isKinematic)throw new Exception("Physical counter placement failed");
        r.interaction.PickUp(cone,true);
        r.holders[0].Use(r.interaction);
        if(r.interaction.Held!=null||r.holders[0].Occupant!=cone||!cone.body.isKinematic)throw new Exception("Cone holder placement failed");
        return "PASS: Loaded tray drops from hand, lands, retains its cone, and can be picked up again. Q places batter on its counter preview with physics. Cone holders still secure cones.";
    }
}
