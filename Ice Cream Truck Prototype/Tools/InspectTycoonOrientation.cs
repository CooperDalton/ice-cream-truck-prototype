var path="Assets/Art/Tycoon/Models/Vanilla_tub.fbx";
var model=UnityEditor.AssetDatabase.LoadAssetAtPath<UnityEngine.GameObject>(path);
return model.GetComponentsInChildren<UnityEngine.Renderer>().Select(r=>r.name+" "+r.bounds.center).ToArray();
