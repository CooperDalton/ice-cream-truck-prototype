var scene=UnityEngine.SceneManagement.SceneManager.GetActiveScene();var g=scene.GetRootGameObjects().SelectMany(o=>o.GetComponents<TycoonGameManager>()).Single();
var locker=g.parts.Single(p=>p.site==2&&p.kind==TycoonPart.Kind.Locker);locker.transform.localPosition=new UnityEngine.Vector3(0,.58f,-1.2f);locker.transform.localRotation=UnityEngine.Quaternion.Euler(0,180,0);
UnityEditor.PrefabUtility.RecordPrefabInstancePropertyModifications(locker.transform);UnityEditor.EditorUtility.SetDirty(locker.transform);
g.navigation.BuildNavMesh();UnityEditor.SceneManagement.EditorSceneManager.SaveScene(scene);return "Saved reachable truck locker position.";
