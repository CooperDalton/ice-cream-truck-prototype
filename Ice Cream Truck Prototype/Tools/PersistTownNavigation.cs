var scene=UnityEngine.SceneManagement.SceneManager.GetActiveScene();var g=scene.GetRootGameObjects().SelectMany(o=>o.GetComponents<TycoonGameManager>()).Single();
string path="Assets/Art/Tycoon/TownNavigation.asset";
UnityEditor.AssetDatabase.CreateAsset(g.navigation.navMeshData,path);UnityEditor.EditorUtility.SetDirty(g.navigation);UnityEditor.SceneManagement.EditorSceneManager.SaveScene(scene);UnityEditor.AssetDatabase.SaveAssets();return "Persisted the baked town navigation for fresh standalone campaigns.";
