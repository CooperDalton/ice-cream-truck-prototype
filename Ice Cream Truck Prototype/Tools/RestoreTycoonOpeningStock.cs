var scene=UnityEngine.SceneManagement.SceneManager.GetActiveScene();
var g=scene.GetRootGameObjects().SelectMany(o=>o.GetComponents<TycoonGameManager>()).Single();
foreach(var tub in g.parts.Where(p=>p.kind==TycoonPart.Kind.Tub)){tub.contents.amount=tub.site==0?12:0;UnityEditor.PrefabUtility.RecordPrefabInstancePropertyModifications(tub);UnityEditor.EditorUtility.SetDirty(tub);}
UnityEditor.SceneManagement.EditorSceneManager.SaveScene(scene);
return "Opening home tubs contain twelve portions each; purchased sites start empty.";
