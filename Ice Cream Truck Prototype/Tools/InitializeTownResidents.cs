var scene=UnityEngine.SceneManagement.SceneManager.GetActiveScene();var g=scene.GetRootGameObjects().SelectMany(o=>o.GetComponents<TycoonGameManager>()).Single();
var residents=scene.GetRootGameObjects().Single(o=>o.name=="Town residents").GetComponentsInChildren<TycoonTownWalker>();foreach(var walker in residents)walker.agent.enabled=false;
UnityEditor.SceneManagement.EditorSceneManager.SaveScene(scene);return "Residents activate after scene navigation and campaign restoration. Nav data asset: "+UnityEditor.AssetDatabase.GetAssetPath(g.navigation.navMeshData);
