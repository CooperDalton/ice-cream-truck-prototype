using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Threading.Tasks;
using UnityEditor;
using UnityEngine;
using Object=UnityEngine.Object;

public static class VisualConsistencyPlaytest
{
    static PrototypeSceneReferences r;
    static List<string> checks;
    static void Check(bool condition,string message)
    {
        if(!condition)throw new Exception("VISUAL CHECK FAILED: "+message);
        checks.Add(message);
    }
    static async Task Frames(int count=5)
    {
        for(int i=0;i<count;i++)await Awaitable.NextFrameAsync();
    }
    static async Task Shot(string name)
    {
        await Frames();ScreenCapture.CaptureScreenshot("Library/CodexPlaytests/"+name+".png");await Frames();
    }
    static void Manual()
    {
        r=PrototypeSceneReferences.Instance;
        r.player.ManualInput=r.interaction.ManualInput=r.truck.ManualInput=true;
        if(r.route!=null)r.route.ManualInput=true;
    }
    static string Report(string name)
    {
        string report="PASS "+checks.Count+" checks\n"+string.Join("\n",checks);
        File.WriteAllText("Library/CodexPlaytests/"+name+".txt",report);EditorApplication.isPaused=true;return report;
    }
    public static async Task<string> Hands()
    {
        checks=new List<string>();EditorApplication.isPaused=false;await Frames();
        GameModeMenu.Instance.FreeDrive();await Frames(12);Manual();
        r.player.Teleport(r.truck.transform,r.truck.kitchen.position,r.truck.kitchen.rotation);
        var cone=Object.Instantiate(r.waffle.conePrefab);cone.Restore(new[]{r.tubs[3].flavor},false);
        foreach(var item in new PickupItem[]{r.scooper,r.batter,r.shaker,cone,r.boombox})
        {
            Check(r.interaction.PickUp(item),"Picked up "+item.displayName);await Frames();
            Check(Vector3.Distance(r.player.GetComponent<FloatingHands>().handGrip.position,item.grip.position)<.001f,"Hand contacts "+item.displayName+" grip within 1 mm");
            Check(Quaternion.Angle(r.player.GetComponent<FloatingHands>().handGrip.rotation,item.grip.rotation)<.1f,"Hand rotation follows "+item.displayName+" grip");
            Check(r.player.GetComponent<FloatingHands>().closedHand.gameObject.activeSelf,"Fingers curl around "+item.displayName);
            await Shot("grip-"+item.kind.ToString().ToLower());
            if(item==cone){r.interaction.Release();Object.Destroy(cone.gameObject);}else item.ReturnHome(r.interaction);
        }
        await Frames();Check(!r.player.GetComponent<FloatingHands>().closedHand.gameObject.activeSelf,"Empty hand returns to open pose");
        r.interaction.PickUp(r.scooper);
        var tub=r.tubs[3];Vector3 pos=tub.transform.position;
        r.player.Teleport(r.truck.transform,new Vector3(pos.x+.65f,.64f,.1f),r.truck.transform.rotation);
        r.player.view.transform.LookAt(tub.GetComponent<Collider>().bounds.center);Physics.SyncTransforms();
        r.interaction.ProcessInput(false,false,false,false,Vector2.zero,.02f);
        Check(r.interaction.Target==tub,"Scoop ray reaches mint tub");
        await Frames();Vector3 hand=r.player.GetComponent<FloatingHands>().handGrip.position;
        for(int i=0;i<10;i++){r.interaction.ProcessInput(false,true,false,false,new Vector2(0,i%2==0?20:-20),.02f);await Frames(1);}
        Check(r.interaction.Scooping&&tub.Progress>.1f,"Mouse strokes start scoop gesture");
        Check(Vector3.Distance(hand,r.player.GetComponent<FloatingHands>().handGrip.position)>.1f,"Hand reaches out with the scooper");
        Check(Vector3.Distance(r.player.GetComponent<FloatingHands>().handGrip.position,r.scooper.grip.position)<.001f,"Hand stays attached during the scoop stroke");
        Check(Vector3.Distance(r.scooper.loadedScoop.transform.position,tub.ScoopPosition)<.001f,"Scooper bowl follows tub path despite its new carry rotation");
        await Shot("grip-scooping");
        r.interaction.ProcessInput(false,false,true,true,Vector2.zero,.02f);await Frames();
        Check(r.interaction.Held==null&&!r.interaction.Gesturing&&!r.player.GetComponent<FloatingHands>().closedHand.gameObject.activeSelf,"Release returns tool and opens hand");
        return Report("grip-verification");
    }
    public static async Task<string> Flavors()
    {
        checks=new List<string>();EditorApplication.isPaused=false;Manual();
        var chunky=new HashSet<string>{"Chocolate","Mint","Cookie cream","Cherry","Peach"};
        foreach(var tub in r.tubs)
        {
            var f=tub.flavor;bool chunks=chunky.Contains(f.displayName);
            Check((f.chunkMaterial!=null)==chunks&&f.scoopMesh.subMeshCount==(chunks?2:1),f.displayName+" has the intended plain/chunky scoop");
            var bits=tub.GetComponentsInChildren<MeshRenderer>(true).Where(m=>m.name=="Flavor chunks").ToArray();
            Check(bits.Length==(chunks?1:0)&&(!chunks||bits[0].sharedMaterial==f.chunkMaterial),f.displayName+" tub agrees with its scoop chunks");
            r.scooper.PreviewScoop(f,.3f);
            Check(r.scooper.loadedScoopFilter.sharedMesh==f.scoopMesh&&r.scooper.loadedScoopRenderer.sharedMaterials.Length==(chunks?2:1),f.displayName+" partial scoop uses the same visual");
            r.scooper.LoadScoop(f);
            var cone=Object.Instantiate(r.waffle.conePrefab);cone.Restore(new[]{f},false);
            Check(cone.scoopFilters[0].sharedMesh==f.scoopMesh&&cone.scoopRenderers[0].sharedMaterials.Length==(chunks?2:1),f.displayName+" cone retains its plain/chunky visual");
            Check(f.orderPicture!=null,f.displayName+" has an order icon");Object.Destroy(cone.gameObject);
        }
        r.scooper.EmptyScoop();
        for(int i=0;i<6;i++)
        {
            var holder=r.holders[i];var cone=Object.Instantiate(r.waffle.conePrefab,holder.socket.position,holder.socket.rotation,holder.socket.parent);
            cone.Restore(new[]{r.tubs[new[]{1,7,0,6,9,3}[i]].flavor},false);holder.Occupant=cone;cone.Holder=holder;
        }
        r.player.Teleport(r.truck.transform,new Vector3(-1.35f,.64f,.25f),r.truck.transform.rotation);
        r.player.view.transform.LookAt(new Vector3(-1.35f,1.45f,-1.25f));
        await Shot("flavor-cues-game");return Report("flavor-visual-verification");
    }
    public static async Task<string> Tray()
    {
        checks=new List<string>();EditorApplication.isPaused=false;Manual();r.GetComponent<GameModeMenu>().ParkRoute();await Frames(12);Manual();r.route.ToggleMap();
        r.interaction.PickUp(r.route.tray);
        for(int i=0;i<3;i++){var cone=Object.Instantiate(r.waffle.conePrefab);cone.Restore(new[]{r.route.stock.flavors[i]},false);r.route.tray.Store(cone);}
        await Frames();Check(Vector3.Distance(r.player.GetComponent<FloatingHands>().handGrip.position,r.route.tray.grip.position)<.001f,"Palm supports the tray grip");
        Check(!r.player.GetComponent<FloatingHands>().closedHand.gameObject.activeSelf,"Tray uses an open supporting palm");await Shot("grip-tray");
        return Report("tray-grip-verification");
    }
}
