using System.Linq;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.UI;
using Object=UnityEngine.Object;

public static class TrimRouteMap
{
    public static string Apply()
    {
        var scene=EditorSceneManager.OpenScene("Assets/Scenes/ParkRoute.unity");
        var h=PrototypeSceneReferences.Instance.route.hud;
        foreach(var text in h.planPanel.GetComponentsInChildren<Text>(true))
        {
            if(new[]{"Planning hint","Map legend","Planning rules"}.Contains(text.name))Object.DestroyImmediate(text.gameObject);
            else if(text.name=="Shop title")text.text="STOCK";
        }
        h.budget.rectTransform.anchoredPosition=new Vector2(-294,365);
        h.map.anchoredPosition=new Vector2(-300,90);
        ((RectTransform)h.unpack.transform.parent).anchoredPosition=new Vector2(-300,-250);
        var card=(RectTransform)h.detailTitle.transform.parent;
        card.anchoredPosition=new Vector2(482,93);card.sizeDelta=new Vector2(548,460);
        h.detailTitle.rectTransform.anchoredPosition=new Vector2(0,187);
        h.detailStats.rectTransform.anchoredPosition=new Vector2(0,120);h.detailStats.rectTransform.sizeDelta=new Vector2(488,72);
        h.detailNeeds.rectTransform.anchoredPosition=new Vector2(0,-112);
        h.detailBehavior.rectTransform.anchoredPosition=new Vector2(0,-204);h.detailBehavior.rectTransform.sizeDelta=new Vector2(488,30);
        h.deliveryText.rectTransform.anchoredPosition=new Vector2(482,-235);
        EditorSceneManager.MarkSceneDirty(scene);EditorSceneManager.SaveScene(scene);
        return "Removed the map's instruction text and compacted its layout.";
    }
}
