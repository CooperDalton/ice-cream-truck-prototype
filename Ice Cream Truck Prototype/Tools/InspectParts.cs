var model = UnityEditor.AssetDatabase.LoadAssetAtPath<UnityEngine.GameObject>("Assets/Art/Workshop.fbx");
var output = new System.Collections.Generic.List<object>();
foreach(var t in model.GetComponentsInChildren<UnityEngine.Transform>(true)) {
 if(t.parent!=null && (t.parent.name=="IceCreamTruck_ROOT" || t.name.Contains("Tub_") || t.name.Contains("IceCream_") || t.name.Contains("TruckPrep") || t.name.Contains("ConeShell") || t.name.Contains("Scoop01") || t.name.Contains("Hand_R") || t.name.Contains("Body"))) {
 var rs=t.GetComponentsInChildren<UnityEngine.Renderer>(true); var b=new UnityEngine.Bounds(t.position,UnityEngine.Vector3.zero); foreach(var r in rs)b.Encapsulate(r.bounds);
 output.Add(new {name=t.name,parent=t.parent.name,position=t.position.ToString("F3"),bounds=b.ToString("F3")});
 }
}
return output;
