var model = UnityEditor.AssetDatabase.LoadAssetAtPath<UnityEngine.GameObject>("Assets/Art/Workshop.fbx");
var list = new System.Collections.Generic.List<object>();
foreach(var t in model.GetComponentsInChildren<UnityEngine.Transform>(true)) {
 if(t.name.EndsWith("ROOT") || t.name.Contains("HINGE") || t.name.Contains("SOCKET")) list.Add(new {name=t.name,parent=t.parent==null?"":t.parent.name,pos=t.position.ToString("F3"),rot=t.eulerAngles.ToString("F1"),scale=t.lossyScale.ToString("F2")});
}
return list;
