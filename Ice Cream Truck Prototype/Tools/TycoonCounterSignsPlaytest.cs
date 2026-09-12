using System;
using System.Linq;
using System.Threading.Tasks;
using UnityEngine;

public static class TycoonCounterSignsPlaytest
{
    public static async Task<string[]> Run()
    {
        var g=TycoonGameManager.Instance;var p=g.player;g.restartRequested=true;p.manualInput=true;g.hud.ClosePanels();g.phase=TycoonGameManager.Phase.Preparation;
        var parts=g.parts.Where(x=>x.catalogIndex==7||x.catalogIndex==10||x.catalogIndex==11).ToArray();
        foreach(var part in parts)
        {
            if(part.GetComponentsInChildren<Canvas>(true).Length>0||part.GetComponentsInChildren<TycoonStationSign>(true).Length>0)throw new Exception("Floating UI remains on "+part.name);
            var sign=part.transform.Cast<Transform>().Single(t=>t.name=="OrderSign"||t.name=="PickupSign");
            var bounds=new Bounds(sign.position,Vector3.zero);foreach(var renderer in sign.GetComponentsInChildren<MeshRenderer>())bounds.Encapsulate(renderer.bounds);
            if(Mathf.Abs(bounds.min.y-part.transform.position.y-1)>.005f||Mathf.Abs(bounds.size.y-.325f)>.005f)throw new Exception("Incorrect sign height: "+bounds);
        }
        var pickup=g.Parts(0,TycoonPart.Kind.ServingCounter).First();var order=g.Parts(0,TycoonPart.Kind.Register).First();
        var signTransform=pickup.transform.Cast<Transform>().Single(t=>t.name=="OrderSign"||t.name=="PickupSign");var rotation=signTransform.rotation;
        var midpoint=(pickup.transform.position+order.transform.position)*.5f;
        for(int side=0;side<2;side++)
        {
            p.Teleport(midpoint+pickup.transform.forward*(side==0?-2.6f:2.6f));
            p.view.transform.rotation=Quaternion.LookRotation(midpoint+Vector3.up*1.15f-p.view.transform.position);
            await Task.Delay(150);ScreenCapture.CaptureScreenshot("Library/CodexPlaytests/CounterSigns"+(side==0?"Staff":"Customer")+".png");await Task.Delay(100);
            if(Quaternion.Angle(rotation,signTransform.rotation)>.01f)throw new Exception("Sign rotates with camera");
        }
        if(Mathf.Abs(pickup.surfaceHeight-1)>.001f)throw new Exception("Sign changed countertop placement height");
        foreach(int i in new[]{7,10,11})if(g.catalog.placementPreviews[i].GetComponent<MeshFilter>().sharedMesh.bounds.max.y<1.32f)throw new Exception("Sign missing from preview");
        g.hud.menuOpen=true;
        return new[]{parts.Length+" order/pickup fixtures have physical mesh signs with bases flush to their counters.","Signs stay fixed when viewed from opposite sides; both sides captured.","Placement previews include the signs and countertop placement height remains 1m."};
    }
}
