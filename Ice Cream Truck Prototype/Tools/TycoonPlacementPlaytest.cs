using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using UnityEngine;

public static class TycoonPlacementPlaytest
{
    private static TycoonGameManager g;
    private static void Check(bool passed,string message)
    {
        if(!passed)throw new Exception(message);
    }
    private static void Aim(Vector3 position,Vector3 from)
    {
        g.player.Teleport(from);g.player.view.transform.rotation=Quaternion.LookRotation(position-g.player.view.transform.position);
        Physics.SyncTransforms();g.player.Aim();g.builder.AimPlacement(false);
    }
    public static async Task<string[]> Run()
    {
        g=TycoonGameManager.Instance;g.restartRequested=true;g.player.manualInput=true;g.hud.ClosePanels();g.phase=TycoonGameManager.Phase.Preparation;
        foreach(var worker in g.workers)worker.onDuty=false;
        var b=g.builder;var p=g.player;var log=new List<string>();
        Check(g.catalog.placementPreviews.All(x=>x.GetComponent<MeshFilter>().sharedMesh.vertexCount>0&&x.GetComponentsInChildren<Collider>(true).Length==0),"All models need nonblocking mesh previews");
        Check(b.validMaterial.GetColor("_BaseColor").a<1&&b.invalidMaterial.GetColor("_BaseColor").a<1,"Ghost materials transparent");
        var part=g.AddPart(2,0,g.sites[0].origin.position+Vector3.left*6);part.installed=false;part.packed=true;part.gameObject.SetActive(false);
        p.inventory=new TycoonInventory(8);p.PickUp(new TycoonItem(TycoonItem.Kind.Equipment,1,2){equipmentId=part.id});
        var ground=g.sites[0].origin.position+new Vector3(0,0,-1.5f);var from=ground+Vector3.back*1.5f;
        Aim(ground,from);
        Check(b.preview.activeSelf&&!b.gridRenderer.gameObject.activeSelf&&b.preview.transform.position.y<.1f,"Tabletop item must not create floating grid");
        Check(b.preview.GetComponentsInChildren<Renderer>().All(r=>r.sharedMaterial==b.invalidMaterial),"Invalid ghost red");
        await Task.Delay(100);ScreenCapture.CaptureScreenshot("Library/CodexPlaytests/PlacementInvalidGround.png");await Task.Delay(100);
        var table=g.Parts(0,TycoonPart.Kind.Table).First();
        var top=table.transform.TransformPoint(new Vector3(.5f,table.surfaceHeight,0));
        Aim(top,table.transform.position+new Vector3(.5f,0,-1.7f));
        Check(b.preview.activeSelf&&b.gridRenderer.gameObject.activeSelf&&Mathf.Abs(b.gridRenderer.transform.position.y-top.y-.008f)<.001f,"Grid sits on actual table surface");
        Check(b.preview.GetComponentsInChildren<Renderer>().All(r=>r.sharedMaterial==b.validMaterial),"Valid holder ghost white: "+p.prompt);
        Check(p.grip.GetComponentsInChildren<MeshRenderer>().All(r=>!r.gameObject.activeInHierarchy),"Carried equipment must not block preview");
        await Task.Delay(100);ScreenCapture.CaptureScreenshot("Library/CodexPlaytests/PlacementTablePreview.png");await Task.Delay(100);
        b.AimPlacement(true);p.Use(false);
        Check(part.installed&&!part.packed&&part.support==table&&Mathf.Abs(part.transform.position.y-top.y)<.001f,"Place holder onto table");
        log.Add("All 14 equipment/bowl previews have geometry and no colliders. Tabletop placement shows a red model on the ground without a floating grid, and a white model plus grid on a valid table.");
        var tub=g.AddPart(1,0,g.sites[0].origin.position+Vector3.left*7);tub.installed=false;tub.packed=true;tub.gameObject.SetActive(false);
        p.PickUp(new TycoonItem(TycoonItem.Kind.Equipment,1,1){equipmentId=tub.id});Aim(ground,from);
        Check(b.gridRenderer.gameObject.activeSelf&&b.preview.GetComponentsInChildren<Renderer>().All(r=>r.sharedMaterial==b.validMaterial),"Ground grid and valid tub preview: "+p.prompt);
        Check(Mathf.Abs(b.gridRenderer.transform.position.y-g.sites[0].origin.position.y-.035f)<.001f,"Ground grid flush with floor");
        await Task.Delay(100);ScreenCapture.CaptureScreenshot("Library/CodexPlaytests/PlacementGroundPreview.png");await Task.Delay(100);
        p.Use(false);Check(tub.installed&&p.Held==null,"Ground placement succeeds");
        log.Add("Ground furniture shows its full translucent model over a white floor grid, then places at the preview position.");
        p.PickUp(new TycoonItem(TycoonItem.Kind.Bowls,4));
        var bowlSpot=table.transform.TransformPoint(new Vector3(-.5f,table.surfaceHeight,-.25f));
        Aim(bowlSpot,table.transform.position+new Vector3(-.5f,0,-1.7f));p.Use(false);
        var bowl=g.Parts(0,TycoonPart.Kind.Bowl).Single();
        Check(p.Held.amount==3&&bowl.contents.kind==TycoonItem.Kind.Serving&&!bowl.contents.cone&&bowl.support==table,"One bowl directly on table");
        Aim(bowlSpot,table.transform.position+new Vector3(-.5f,0,-1.7f));
        Check(b.preview.GetComponentsInChildren<Renderer>().All(r=>r.sharedMaterial==b.invalidMaterial),"Occupied bowl cell is red");
        p.Use(false);Check(p.Held.amount==3&&g.Parts(0,TycoonPart.Kind.Bowl).Count()==1,"Blocked placement consumes nothing");
        var secondSpot=table.transform.TransformPoint(new Vector3(-.75f,table.surfaceHeight,-.25f));
        Aim(secondSpot,table.transform.position+new Vector3(-.75f,0,-1.7f));p.Use(false);
        Check(g.Parts(0,TycoonPart.Kind.Bowl).Count()==2&&p.Held.amount==2,"Multiple separate bowls");
        p.inventory.slots[1]=new TycoonItem(TycoonItem.Kind.BasicScooper){loadedFlavor=1};p.Select(1);p.customerTarget=null;p.looseTarget=null;p.workerTarget=null;p.target=bowl;p.Use(false);
        Check(bowl.contents.scoops.SequenceEqual(new[]{1})&&p.Held.loadedFlavor==-1,"Scoop goes into free-standing bowl");
        p.inventory.slots[2]=new TycoonItem(TycoonItem.Kind.Topping,4,1);p.Select(2);p.Use(false);p.Gesture(new Vector2(0,20),1.6f);
        Check(bowl.contents.toppings==2&&p.Held.amount==3,"Topping goes into free-standing bowl");
        p.CancelGesture();b.AimPlacement(false);bowl.RefreshVisual();
        await Task.Delay(100);ScreenCapture.CaptureScreenshot("Library/CodexPlaytests/TabletopBowls.png");await Task.Delay(100);
        int id=bowl.id;p.target=bowl;p.Use(true);
        Check(p.Held.kind==TycoonItem.Kind.Serving&&p.Held.scoops[0]==1&&p.Held.toppings==2&&!g.parts.Any(x=>x.id==id),"Take bowl selects serving and removes its table slot");
        var returnSpot=table.transform.TransformPoint(new Vector3(-.5f,table.surfaceHeight,-.25f));Aim(returnSpot,table.transform.position+new Vector3(-.5f,0,-1.7f));p.Use(false);
        Check(g.Parts(0,TycoonPart.Kind.Bowl).Any(x=>x.contents.scoops.Length==1&&x.contents.toppings==2),"Completed bowl can be put back on table");
        log.Add("Each click places one bowl. Two bowls coexist; overlap is rejected without consuming stock. Scoops and toppings work directly in the bowl; E picks it up and auto-selects it; placing it again preserves its recipe.");
        p.inventory.slots[4]=new TycoonItem(TycoonItem.Kind.Cone);p.Select(4);Aim(returnSpot,table.transform.position+new Vector3(-.5f,0,-1.7f));
        Check(!b.preview.activeSelf&&!b.gridRenderer.gameObject.activeSelf,"Cone has no free-table placement");
        p.target=part;p.customerTarget=null;p.Use(false);Check(part.contents!=null&&part.contents.cone,"Cone still requires holder");
        log.Add("Cones have no tabletop placement preview and still go into the cone holder.");
        g.Save();return log.ToArray();
    }
}
