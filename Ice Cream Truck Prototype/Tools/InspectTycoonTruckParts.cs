var model=UnityEditor.AssetDatabase.LoadAssetAtPath<UnityEngine.GameObject>("Assets/Art/Tycoon/Models/Ice_cream_truck.fbx");
return model.GetComponentsInChildren<UnityEngine.Renderer>().Where(r=>new[]{"floor","counter","seat","tub","door","steer","wheel"}.Any(term=>r.name.ToLowerInvariant().Contains(term))).Select(r=>r.name+" "+r.bounds).Take(85).ToArray();
