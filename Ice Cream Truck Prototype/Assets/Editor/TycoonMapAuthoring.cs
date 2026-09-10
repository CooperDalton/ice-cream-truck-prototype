using System.Linq;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.UI;
using Object=UnityEngine.Object;

public static class TycoonMapAuthoring
{
    public static void Apply()
    {
        var scene=UnityEngine.SceneManagement.SceneManager.GetActiveScene();var game=scene.GetRootGameObjects().SelectMany(o=>o.GetComponents<TycoonGameManager>()).Single();var ui=game.hud;
        var mini=(RectTransform)ui.miniMarker.parent;
        foreach(var image in ui.mapPanel.GetComponentsInChildren<Image>(true).Where(i=>i.name=="Map road"||i.name=="Map ground").ToArray())Object.DestroyImmediate(image.gameObject);
        foreach(var image in mini.GetComponentsInChildren<Image>(true).Where(i=>i.name=="Street").ToArray())Object.DestroyImmediate(image.gameObject);
        mini.gameObject.AddComponent<RectMask2D>();
        var viewport=Rect("Map viewport",ui.mapPanel.transform,Vector2.zero,new Vector2(500,490));viewport.gameObject.AddComponent<RectMask2D>();var background=viewport.gameObject.AddComponent<Image>();background.color=new Color(.72f,.83f,.66f);background.raycastTarget=false;
        viewport.SetAsFirstSibling();ui.mapContent=Rect("Map contents",viewport,Vector2.zero,new Vector2(500,490));
        ui.roadCenters=new[]{new Vector3(30,0,-12),new Vector3(64,0,22),new Vector3(30,0,46),new Vector3(5,0,17)};
        Vector2[] sizes={new Vector2(140,9),new Vector2(9,68),new Vector2(75,9),new Vector2(9,58)};ui.miniRoads=new RectTransform[4];
        for(int i=0;i<4;i++)
        {
            var center=ui.roadCenters[i];var road=Rect("Street",ui.mapContent,new Vector2((center.x-30)/130,(center.z-20)/110)*470,new Vector2(sizes[i].x/130,sizes[i].y/110)*470);var image=road.gameObject.AddComponent<Image>();image.color=new Color(.38f,.36f,.43f);image.raycastTarget=false;
            var small=Rect("Street",mini,Vector2.zero,sizes[i]/120*185);small.SetAsFirstSibling();var smallImage=small.gameObject.AddComponent<Image>();smallImage.color=image.color;smallImage.raycastTarget=false;ui.miniRoads[i]=small;
        }
        ui.mapButtons=new Button[ui.mapLocations.Length];
        for(int i=0;i<ui.mapLocations.Length;i++)
        {
            ui.mapLocations[i].SetParent(ui.mapContent,false);var image=ui.mapLocations[i].GetComponent<Image>();image.raycastTarget=true;ui.mapLocations[i].sizeDelta=new Vector2(18,18);ui.mapButtons[i]=image.gameObject.AddComponent<Button>();ui.mapButtons[i].targetGraphic=image;
            ui.destinationButtons[i].GetComponentInChildren<Text>().color=new Color(1,.97f,.9f);
        }
        ui.fullMarker.SetParent(ui.mapContent,false);ui.miniMarker.SetAsLastSibling();
        foreach(var marker in new[]{ui.miniMarker,ui.fullMarker})
        {
            marker.GetComponent<Image>().color=Color.clear;var text=Object.Instantiate(ui.waypointText,marker);text.rectTransform.anchoredPosition=Vector2.zero;text.rectTransform.sizeDelta=new Vector2(24,24);text.text="▲";text.fontSize=18;text.color=new Color(.95f,.28f,.5f);text.alignment=TextAnchor.MiddleCenter;
        }
        EditorSceneManager.SaveScene(scene);AssetDatabase.SaveAssets();
    }
    private static RectTransform Rect(string name,Transform parent,Vector2 point,Vector2 size)
    {
        var rect=new GameObject(name,typeof(RectTransform)).GetComponent<RectTransform>();rect.SetParent(parent,false);rect.anchoredPosition=point;rect.sizeDelta=size;return rect;
    }
}
