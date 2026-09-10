var scene=UnityEngine.SceneManagement.SceneManager.GetActiveScene();
var g=scene.GetRootGameObjects().SelectMany(o=>o.GetComponents<TycoonGameManager>()).Single();
g.hud.GetComponent<UnityEngine.UI.CanvasScaler>().screenMatchMode=UnityEngine.UI.CanvasScaler.ScreenMatchMode.Expand;
var reticle=g.hud.GetComponentsInChildren<UnityEngine.UI.Text>(true).Single(t=>t.name=="+");
reticle.rectTransform.sizeDelta=new UnityEngine.Vector2(40,40);g.hud.reticle=reticle.gameObject;
UnityEditor.SceneManagement.EditorSceneManager.SaveScene(scene);return "HUD keeps the entire authored layout visible at narrower and wider window ratios.";
