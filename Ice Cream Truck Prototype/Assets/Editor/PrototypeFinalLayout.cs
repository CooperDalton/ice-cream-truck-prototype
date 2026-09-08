using System.Linq;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.UI;

public static class PrototypeFinalLayout
{
    private static void Anchor(RectTransform rect,Vector2 anchor,Vector2 offset)
    {
        rect.anchorMin=rect.anchorMax=anchor;rect.anchoredPosition=offset;
    }
    [MenuItem("Ice Cream/Apply final prototype layout")]
    public static void Apply()
    {
        var r=PrototypeSceneReferences.Instance;var h=r.hud;
        Anchor((RectTransform)h.clockText.transform.parent,new Vector2(0,1),new Vector2(265,-74));
        Anchor((RectTransform)h.orderText.transform.parent,new Vector2(1,1),new Vector2(-245,-141));
        Anchor(h.waffleText.rectTransform,new Vector2(0,1),new Vector2(245,-158));
        Anchor((RectTransform)h.promptText.transform.parent,new Vector2(.5f,0),new Vector2(0,121));
        Anchor(h.heldText.rectTransform,new Vector2(.5f,0),new Vector2(0,63));
        Anchor(h.messageText.rectTransform,new Vector2(.5f,0),new Vector2(0,222));
        var labels=h.GetComponentsInChildren<Text>(true).GroupBy(t=>t.name).ToDictionary(g=>g.Key,g=>g.First());
        Anchor(labels["Controls"].rectTransform,new Vector2(0,0),new Vector2(295,43));
        foreach(var panel in new[]{h.pausePanel,h.resultPanel})
        {
            var rect=(RectTransform)panel.transform;rect.anchorMin=Vector2.zero;rect.anchorMax=Vector2.one;rect.offsetMin=rect.offsetMax=Vector2.zero;
        }
        r.player.view.transform.localRotation=Quaternion.Euler(24,0,0);
        var playerSO=new SerializedObject(r.player);playerSO.FindProperty("pitch").floatValue=24;playerSO.ApplyModifiedPropertiesWithoutUndo();
        var stream=r.waffle.GetComponent<LineRenderer>();if(stream==null)stream=r.waffle.gameObject.AddComponent<LineRenderer>();
        stream.positionCount=2;stream.startWidth=stream.endWidth=.014f;stream.useWorldSpace=true;stream.numCapVertices=3;stream.sharedMaterial=AssetDatabase.LoadAssetAtPath<Material>("Assets/Art/Materials/Enamel • warm cream.mat");stream.enabled=false;r.waffle.pourStream=stream;
        EditorSceneManager.MarkSceneDirty(r.gameObject.scene);EditorSceneManager.SaveScene(r.gameObject.scene);AssetDatabase.SaveAssets();
    }
}
