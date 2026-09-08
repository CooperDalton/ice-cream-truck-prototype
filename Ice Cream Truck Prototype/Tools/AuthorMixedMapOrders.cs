using System;
using System.Linq;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.UI;
using Object=UnityEngine.Object;

public static class AuthorMixedMapOrders
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
        h.map.anchoredPosition=new Vector2(0,15);h.map.sizeDelta=new Vector2(1530,600);
        h.mapMin=new Vector2(-40,-60);h.mapMax=new Vector2(210,125);
        var lines=h.map.GetComponentsInChildren<Image>(true).Where(i=>i.name=="Route line").ToArray();
        for(int i=0;i<lines.Length;i++)
        {
            Vector2 a=h.MapPosition(r.route.path[i].position),b=h.MapPosition(r.route.path[i+1].position),delta=b-a;
            lines[i].rectTransform.anchoredPosition=(a+b)/2;lines[i].rectTransform.sizeDelta=new Vector2(delta.magnitude,16);
        }
        foreach(var text in h.map.GetComponentsInChildren<Text>(true))
        {
            if(text.name=="North")text.rectTransform.anchoredPosition=new Vector2(-720,270);
            else if(text.name=="Start")text.rectTransform.anchoredPosition=h.MapPosition(r.route.path[0].position)+Vector2.down*31;
            else if(text.name=="Exit")text.rectTransform.anchoredPosition=h.MapPosition(r.route.path[3].position)+Vector2.up*31;
        }
        for(int i=0;i<h.pointButtons.Length;i++)((RectTransform)h.pointButtons[i].transform).anchoredPosition=h.MapPosition(BuildPosition(r.route,r.route.points[i].distance));
        h.truckMarker.anchoredPosition=h.MapPosition(r.route.path[0].position);
        h.crowdCards=new RouteHUD.CrowdCard[h.hotspotButtons.Length];
        for(int i=0;i<h.hotspotButtons.Length;i++)
        {
            var rect=(RectTransform)h.hotspotButtons[i].transform;
            foreach(Transform child in rect.Cast<Transform>().ToArray())Object.DestroyImmediate(child.gameObject);
            var world=r.route.hotspots[i].transform.position;
            rect.anchoredPosition=h.MapPosition(world)+Vector2.up*(world.z<0?-57:world.z>60?49:56);
            if(i==2)rect.anchoredPosition+=Vector2.left*120;
            rect.sizeDelta=new Vector2(272,140);
            var card=new RouteHUD.CrowdCard();h.crowdCards[i]=card;
            card.title=Label(rect,"Location",new Vector2(0,54),new Vector2(250,24),18);card.title.fontStyle=FontStyle.Bold;
            var list=Rect(rect,"Orders",new Vector2(0,-15),new Vector2(250,108));
            var stack=list.gameObject.AddComponent<VerticalLayoutGroup>();stack.childAlignment=TextAnchor.MiddleCenter;
            stack.childControlWidth=stack.childControlHeight=true;stack.childForceExpandWidth=stack.childForceExpandHeight=false;stack.spacing=2;
            card.orders=new RouteHUD.OrderRow[3];
            for(int orderIndex=0;orderIndex<3;orderIndex++)
            {
                var row=Rect(list,"Order "+orderIndex,Vector2.zero,new Vector2(250,34));
                var rowSize=row.gameObject.AddComponent<LayoutElement>();rowSize.preferredWidth=250;rowSize.preferredHeight=34;
                var data=new RouteHUD.OrderRow{root=row.gameObject};card.orders[orderIndex]=data;
                var icons=Rect(row,"Recipe",new Vector2(-59,0),new Vector2(126,32));
                var layout=icons.gameObject.AddComponent<HorizontalLayoutGroup>();layout.childAlignment=TextAnchor.MiddleLeft;
                layout.childControlWidth=layout.childControlHeight=true;layout.childForceExpandWidth=layout.childForceExpandHeight=false;layout.spacing=2;
                data.flavors=new Image[3];
                for(int j=0;j<3;j++)
                {
                    data.flavors[j]=Picture(icons,"Scoop "+j,Vector2.zero,new Vector2(30,30));
                    var size=data.flavors[j].gameObject.AddComponent<LayoutElement>();size.preferredWidth=size.preferredHeight=30;
                }
                var sprinkles=Rect(icons,"Sprinkles",Vector2.zero,new Vector2(30,30));data.sprinkles=sprinkles.gameObject;
                var sprinkleSize=sprinkles.gameObject.AddComponent<LayoutElement>();sprinkleSize.preferredWidth=sprinkleSize.preferredHeight=30;
                var colors=new[]{new Color(.94f,.35f,.5f),new Color(.33f,.66f,.48f),new Color(1,.76f,.25f),new Color(.55f,.4f,.7f)};
                for(int j=0;j<12;j++)
                {
                    var bit=Picture(sprinkles,"Sprinkle "+j,new Vector2(-10+j%4*7,-9+j/4*9),new Vector2(2,6));
                    bit.preserveAspect=false;bit.color=colors[j%4];bit.rectTransform.localRotation=Quaternion.Euler(0,0,j%2==0?30:-30);
                }
                data.quantityPrice=Label(row,"Quantity and price",new Vector2(68,0),new Vector2(108,32),18);
            }
        }
        var shop=(RectTransform)h.unpack.transform.parent;shop.anchoredPosition=new Vector2(-300,-362);shop.sizeDelta=new Vector2(930,138);
        h.deliveryText.rectTransform.anchoredPosition=new Vector2(482,-355);
        h.detailPopup.gameObject.SetActive(false);h.detailPopup.SetAsLastSibling();
        EditorSceneManager.MarkSceneDirty(scene);EditorSceneManager.SaveScene(scene);EditorSceneManager.OpenScene("Assets/Scenes/MainMenu.unity");
        return "Saved three authored recipe rows at each map location.";
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
