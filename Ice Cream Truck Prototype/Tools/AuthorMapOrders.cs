using System;
using System.Linq;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.UI;
using Object=UnityEngine.Object;

public static class AuthorMapOrders
{
    static readonly Color Ink=new Color(.14f,.27f,.26f),Cream=new Color(1,.98f,.92f);
    static Font font;
    static Sprite panel;
    static RectTransform Rect(Transform parent,string name,Vector2 point,Vector2 size)
    {
        var rect=new GameObject(name,typeof(RectTransform)).GetComponent<RectTransform>();
        rect.SetParent(parent,false);rect.anchoredPosition=point;rect.sizeDelta=size;return rect;
    }
    static Text Label(Transform parent,string name,Vector2 point,Vector2 size,int fontSize)
    {
        var text=Rect(parent,name,point,size).gameObject.AddComponent<Text>();text.font=font;text.fontSize=fontSize;
        text.color=Ink;text.alignment=TextAnchor.MiddleCenter;text.raycastTarget=false;return text;
    }
    static Image Picture(Transform parent,string name,Vector2 point,Vector2 size)
    {
        var image=Rect(parent,name,point,size).gameObject.AddComponent<Image>();image.raycastTarget=false;image.preserveAspect=true;return image;
    }
    public static string Apply()
    {
        if(EditorApplication.isPlaying)throw new Exception("Stop Play Mode first");
        var scene=EditorSceneManager.OpenScene("Assets/Scenes/ParkRoute.unity");var r=PrototypeSceneReferences.Instance;var h=r.route.hud;
        font=h.heading.font;panel=h.map.GetComponent<Image>().sprite;
        h.map.anchoredPosition=new Vector2(0,58);h.map.sizeDelta=new Vector2(1530,530);
        h.mapMin=new Vector2(-40,-50);h.mapMax=new Vector2(210,115);
        var lines=h.map.GetComponentsInChildren<Image>(true).Where(i=>i.name=="Route line").ToArray();
        for(int i=0;i<lines.Length;i++)
        {
            Vector2 a=h.MapPosition(r.route.path[i].position),b=h.MapPosition(r.route.path[i+1].position),delta=b-a;
            lines[i].rectTransform.anchoredPosition=(a+b)/2;lines[i].rectTransform.sizeDelta=new Vector2(delta.magnitude,16);
        }
        foreach(var text in h.map.GetComponentsInChildren<Text>(true))
        {
            if(text.name=="North")text.rectTransform.anchoredPosition=new Vector2(-720,235);
            else if(text.name=="Start")text.rectTransform.anchoredPosition=h.MapPosition(r.route.path[0].position)+Vector2.down*31;
            else if(text.name=="Exit")text.rectTransform.anchoredPosition=h.MapPosition(r.route.path[3].position)+Vector2.up*31;
        }
        for(int i=0;i<h.pointButtons.Length;i++)((RectTransform)h.pointButtons[i].transform).anchoredPosition=h.MapPosition(BuildPosition(r.route,r.route.points[i].distance));
        h.truckMarker.anchoredPosition=h.MapPosition(r.route.path[0].position);
        h.crowdCards=new RouteHUD.CrowdCard[h.hotspotButtons.Length];
        for(int i=0;i<h.hotspotButtons.Length;i++)
        {
            var button=h.hotspotButtons[i];Object.DestroyImmediate(button.GetComponentInChildren<Text>().gameObject);
            var rect=(RectTransform)button.transform;var world=r.route.hotspots[i].transform.position;
            rect.anchoredPosition=h.MapPosition(world)+Vector2.up*(world.z<0?-40:world.z>60?34:40);
            if(i==2)rect.anchoredPosition+=Vector2.left*80;
            rect.sizeDelta=new Vector2(196,108);button.GetComponent<Image>().color=Cream;
            var card=new RouteHUD.CrowdCard();h.crowdCards[i]=card;
            card.title=Label(rect,"Location",new Vector2(0,35),new Vector2(182,25),18);card.title.fontStyle=FontStyle.Bold;
            var row=Rect(rect,"Recipe",new Vector2(0,1),new Vector2(180,44));
            var order=new RouteHUD.OrderRow{root=row.gameObject};card.orders=new[]{order};
            var layout=row.gameObject.AddComponent<HorizontalLayoutGroup>();layout.childAlignment=TextAnchor.MiddleCenter;
            layout.childControlWidth=layout.childControlHeight=true;layout.childForceExpandWidth=layout.childForceExpandHeight=false;layout.spacing=1;
            order.flavors=new Image[3];
            for(int j=0;j<3;j++)
            {
                order.flavors[j]=Picture(row,"Scoop "+j,Vector2.zero,new Vector2(44,44));
                var size=order.flavors[j].gameObject.AddComponent<LayoutElement>();size.preferredWidth=size.preferredHeight=44;
            }
            var sprinkles=Rect(row,"Sprinkles",Vector2.zero,new Vector2(44,44));order.sprinkles=sprinkles.gameObject;
            var sprinkleSize=sprinkles.gameObject.AddComponent<LayoutElement>();sprinkleSize.preferredWidth=sprinkleSize.preferredHeight=44;
            var colors=new[]{new Color(.94f,.35f,.5f),new Color(.33f,.66f,.48f),new Color(1,.76f,.25f),new Color(.55f,.4f,.7f)};
            for(int j=0;j<12;j++)
            {
                var bit=Picture(sprinkles,"Sprinkle "+j,new Vector2(-14+j%4*9,-13+j/4*12),new Vector2(3,8));
                bit.preserveAspect=false;bit.color=colors[j%4];bit.rectTransform.localRotation=Quaternion.Euler(0,0,j%2==0?30:-30);
            }
            order.quantityPrice=Label(rect,"Quantity and price",new Vector2(0,-34),new Vector2(182,27),20);
        }
        h.mapBackground=h.map.gameObject.AddComponent<Button>();h.mapBackground.targetGraphic=h.map.GetComponent<Image>();
        h.map.GetComponent<Image>().raycastTarget=true;h.mapBackground.transition=Selectable.Transition.None;
        h.detailPopup=(RectTransform)h.detailTitle.transform.parent;h.detailPopup.SetParent(h.map,false);
        h.detailPopup.sizeDelta=new Vector2(350,300);h.detailPopup.anchoredPosition=Vector2.zero;
        h.detailPopup.GetComponent<Image>().raycastTarget=true;
        foreach(var child in h.detailPopup.GetComponentsInChildren<Transform>(true).Where(t=>t.name=="Recipe"||t.name.StartsWith("Flavor ")).ToArray())Object.DestroyImmediate(child.gameObject);
        h.detailTitle.rectTransform.anchoredPosition=new Vector2(-15,118);h.detailTitle.rectTransform.sizeDelta=new Vector2(276,35);h.detailTitle.fontSize=24;
        h.detailStats.rectTransform.anchoredPosition=new Vector2(0,65);h.detailStats.rectTransform.sizeDelta=new Vector2(302,56);h.detailStats.fontSize=19;
        h.detailNeeds.rectTransform.anchoredPosition=new Vector2(0,-42);h.detailNeeds.rectTransform.sizeDelta=new Vector2(302,132);h.detailNeeds.fontSize=18;
        h.detailBehavior.rectTransform.anchoredPosition=new Vector2(0,-126);h.detailBehavior.rectTransform.sizeDelta=new Vector2(302,26);h.detailBehavior.fontSize=17;
        var close=Picture(h.detailPopup,"Close",new Vector2(146,120),new Vector2(36,36));close.color=new Color(.87f,.93f,.84f);close.sprite=panel;close.type=Image.Type.Sliced;close.raycastTarget=true;
        h.closeDetail=close.gameObject.AddComponent<Button>();h.closeDetail.targetGraphic=close;
        Label(close.transform,"Label",Vector2.zero,new Vector2(36,36),23).text="×";
        h.detailPopup.gameObject.SetActive(false);
        ((RectTransform)h.unpack.transform.parent).anchoredPosition=new Vector2(-300,-307);
        h.deliveryText.rectTransform.anchoredPosition=new Vector2(482,-310);
        EditorSceneManager.MarkSceneDirty(scene);EditorSceneManager.SaveScene(scene);EditorSceneManager.OpenScene("Assets/Scenes/MainMenu.unity");
        return "Saved six map order cards and a dismissible details popup.";
    }
    static Vector3 BuildPosition(RouteGameManager route,float distance)
    {
        for(int i=1;i<route.path.Length;i++)
        {
            float length=Vector3.Distance(route.path[i-1].position,route.path[i].position);
            if(distance<=length)return Vector3.Lerp(route.path[i-1].position,route.path[i].position,distance/length);
            distance-=length;
        }
        return route.path[route.path.Length-1].position;
    }
}
