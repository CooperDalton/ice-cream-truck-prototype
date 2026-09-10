var scene=UnityEngine.SceneManagement.SceneManager.GetActiveScene();var g=scene.GetRootGameObjects().SelectMany(o=>o.GetComponents<TycoonGameManager>()).Single();
g.player.gameObject.layer=2;g.navigation.layerMask=~(1<<2);g.navigation.BuildNavMesh();
UnityEditor.SceneManagement.EditorSceneManager.SaveScene(scene);return "Player capsule excluded from interaction rays and navigation geometry.";
