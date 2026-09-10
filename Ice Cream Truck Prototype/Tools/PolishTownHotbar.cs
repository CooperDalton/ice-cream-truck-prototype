var scene=UnityEngine.SceneManagement.SceneManager.GetActiveScene();var g=scene.GetRootGameObjects().SelectMany(o=>o.GetComponents<TycoonGameManager>()).Single();var ui=g.hud;
foreach(var slot in ui.hotbar.Concat(ui.playerSlots).Concat(ui.storageSlots))
{
    slot.bar.rectTransform.anchorMin=UnityEngine.Vector2.zero;slot.bar.rectTransform.anchorMax=UnityEngine.Vector2.one;slot.bar.rectTransform.anchoredPosition=UnityEngine.Vector2.zero;slot.bar.rectTransform.sizeDelta=UnityEngine.Vector2.zero;
}
for(int i=0;i<8;i++)
{
    var slot=ui.hotbar[i];slot.frame.rectTransform.sizeDelta=new UnityEngine.Vector2(94,94);slot.frame.rectTransform.anchoredPosition=new UnityEngine.Vector2((i-3.5f)*104,-382);slot.icon.rectTransform.sizeDelta=new UnityEngine.Vector2(72,72);
    ((UnityEngine.RectTransform)slot.bar.transform.parent).anchoredPosition=new UnityEngine.Vector2(0,-37);
}
UnityEditor.SceneManagement.EditorSceneManager.SaveScene(scene);return "Enlarged item icons and kept supply bars inside the illustrated outlines.";
