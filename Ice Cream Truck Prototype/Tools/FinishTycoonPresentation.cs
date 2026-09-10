var scene=UnityEngine.SceneManagement.SceneManager.GetActiveScene();var g=scene.GetRootGameObjects().SelectMany(o=>o.GetComponents<TycoonGameManager>()).Single();var ui=g.hud;
ui.panel.transform.SetAsLastSibling();ui.resultsText=UnityEngine.Object.Instantiate(ui.panelText,ui.panel.transform);ui.resultsText.name="Day results";ui.resultsText.rectTransform.anchoredPosition=new UnityEngine.Vector2(0,125);ui.resultsText.rectTransform.sizeDelta=new UnityEngine.Vector2(1080,275);ui.resultsText.fontSize=23;ui.resultsText.gameObject.SetActive(false);
foreach(var site in g.sites.Take(2))
{
    UnityEngine.Vector3[] points={new UnityEngine.Vector3(0,.53f,1.46f),new UnityEngine.Vector3(-1.95f,.6f,0),new UnityEngine.Vector3(1.95f,.6f,.63f)};
    UnityEngine.Vector3[] sizes={new UnityEngine.Vector3(4,.89f,.09f),new UnityEngine.Vector3(.1f,1.05f,2.9f),new UnityEngine.Vector3(.1f,1.05f,1.6f)};
    for(int i=0;i<3;i++){var wall=new UnityEngine.GameObject("Kiosk wall collision");wall.transform.SetParent(site.kiosk.transform,false);wall.transform.localPosition=points[i];wall.AddComponent<UnityEngine.BoxCollider>().size=sizes[i];}
}
UnityEditor.PlayerSettings.defaultScreenWidth=1440;UnityEditor.PlayerSettings.defaultScreenHeight=900;UnityEditor.PlayerSettings.fullScreenMode=UnityEngine.FullScreenMode.Windowed;UnityEditor.PlayerSettings.resizableWindow=true;
UnityEditor.SceneManagement.EditorSceneManager.SaveScene(scene);UnityEditor.AssetDatabase.SaveAssets();return "Saved full day results, menu draw order, kiosk wall collision, and windowed player settings.";
