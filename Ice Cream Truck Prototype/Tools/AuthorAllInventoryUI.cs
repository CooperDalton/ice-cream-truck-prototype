using System;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.UI;
using Object=UnityEngine.Object;

public static class AuthorAllInventoryUI
{
    private static TycoonHUD hud;
    private static Font font;
    private static Sprite paper;
    private static readonly Color Ink=new Color(.24f,.20f,.29f),Mint=new Color(.43f,.72f,.64f);
    public static string Build()
    {
        if(EditorApplication.isPlaying)throw new Exception("Stop Play Mode before authoring UI");
        var scene=UnityEngine.SceneManagement.SceneManager.GetActiveScene();hud=scene.GetRootGameObjects()[0].GetComponent<TycoonGameManager>().hud;
        font=hud.money.font;paper=hud.moneyDisplay.parent.GetComponent<Image>().sprite;
        Undo.RegisterFullObjectHierarchyUndo(hud.gameObject,"Unify inventory screens");
        // Preserve the existing locker button and its authored references while replacing the overlay.
        hud.assignLockerButton.transform.SetParent(hud.transform,false);
        Object.DestroyImmediate(hud.shelfPanel);
        var overlay=Picture("Storage overlay",hud.transform,Vector2.zero,Vector2.zero,new Color(.12f,.10f,.16f,.56f));
        overlay.rectTransform.anchorMin=Vector2.zero;overlay.rectTransform.anchorMax=Vector2.one;overlay.raycastTarget=true;
        overlay.transform.SetSiblingIndex(hud.hotbar[0].frame.transform.GetSiblingIndex());hud.shelfPanel=overlay.gameObject;
        hud.storageViews=new[]{Window(overlay.transform,4,false),Window(overlay.transform,8,false),Window(overlay.transform,12,false)};
        hud.employeeStorageView=Window(overlay.transform,8,true);
        hud.shelfSlots=hud.storageViews[2].slots;hud.shelfCloseButton=hud.storageViews[2].close;hud.shelfStatus=hud.storageViews[2].status;
        hud.shelfPanel.SetActive(false);EditorUtility.SetDirty(hud);EditorSceneManager.MarkSceneDirty(scene);EditorSceneManager.SaveScene(scene);
        return "Authored matching four-, eight-, and twelve-slot storage panels plus employee inventory with locker controls.";
    }
    private static TycoonHUD.StorageView Window(Transform parent,int count,bool employee)
    {
        float width=employee?620:count==12?760:536,height=employee?498:count==4?252:364;
        var card=Picture(employee?"Employee inventory":count+"-slot storage",parent,new Vector2(0,70),new Vector2(width,height),new Color(1,.97f,.90f),paper);card.raycastTarget=true;
        var result=new TycoonHUD.StorageView{root=card.gameObject,slots=new TycoonHUD.SlotView[count]};
        result.title=Label("Title",card.transform,new Vector2(-46,height/2-34),new Vector2(width-156,42),32,"Storage");
        var close=Object.Instantiate(hud.inventoryCloseButton,card.transform);close.name="Close storage";Place((RectTransform)close.transform,new Vector2(width/2-78,height/2-34),new Vector2(92,38));result.close=close;
        float gridTop=employee?38:count==4?-8:48;
        Picture("Divider",card.transform,new Vector2(0,gridTop+65),new Vector2(width-64,1),new Color(.48f,.40f,.32f,.18f));
        int columns=count==12?6:4;
        for(int i=0;i<count;i++)
        {
            var position=new Vector2(-(columns-1)*56+i%columns*112,gridTop-i/columns*112);
            Picture("Slot surround "+i,card.transform,position,new Vector2(100,100),new Color(.65f,.77f,.69f,.45f),paper);
            var frame=Picture("Slot "+i,card.transform,position,new Vector2(96,96),Color.white,paper);frame.raycastTarget=true;
            var button=frame.gameObject.AddComponent<Button>();button.targetGraphic=frame;var colors=button.colors;colors.highlightedColor=new Color(.81f,.94f,.87f);colors.pressedColor=Mint;button.colors=colors;
            var icon=Picture("Item",frame.transform,new Vector2(0,7),new Vector2(70,70),Color.white);icon.preserveAspect=true;
            var quantity=Label("Quantity",frame.transform,new Vector2(12,-26),new Vector2(54,26),19,"");quantity.alignment=TextAnchor.MiddleRight;
            var track=Picture("Supply track",frame.transform,new Vector2(0,-39),new Vector2(66,4),new Color(.37f,.33f,.29f,.13f));
            var fill=Picture("Supply",track.transform,Vector2.zero,new Vector2(66,4),Mint,hud.hotbar[0].bar.sprite);fill.type=Image.Type.Filled;fill.fillMethod=Image.FillMethod.Horizontal;fill.fillOrigin=0;
            result.slots[i]=new TycoonHUD.SlotView{button=button,frame=frame,icon=icon,label=quantity,bar=fill};icon.gameObject.SetActive(false);track.gameObject.SetActive(false);
        }
        result.status=Label("Transfer status",card.transform,new Vector2(0,employee?-157:-height/2+26),new Vector2(width-64,26),17,"");result.status.alignment=TextAnchor.MiddleCenter;
        if(employee)
        {
            hud.employeeDetails=Label("Employee details",card.transform,new Vector2(0,156),new Vector2(width-64,74),17,"");
            hud.assignLockerButton.transform.SetParent(card.transform,false);Place((RectTransform)hud.assignLockerButton.transform,new Vector2(0,-203),new Vector2(220,38));
            var image=hud.assignLockerButton.GetComponent<Image>();image.sprite=paper;image.type=Image.Type.Sliced;image.color=Mint;
            var caption=hud.assignLockerButton.GetComponentInChildren<Text>();caption.text="Change locker";caption.fontSize=17;caption.color=Ink;
        }
        card.gameObject.SetActive(false);return result;
    }
    private static void Place(RectTransform rect,Vector2 position,Vector2 size)
    {
        rect.anchorMin=rect.anchorMax=rect.pivot=new Vector2(.5f,.5f);rect.anchoredPosition=position;rect.sizeDelta=size;
    }
    private static Image Picture(string name,Transform parent,Vector2 position,Vector2 size,Color color,Sprite sprite=null)
    {
        var image=new GameObject(name,typeof(RectTransform),typeof(Image)).GetComponent<Image>();image.transform.SetParent(parent,false);Place(image.rectTransform,position,size);image.color=color;image.sprite=sprite;image.type=sprite==null?Image.Type.Simple:Image.Type.Sliced;image.raycastTarget=false;return image;
    }
    private static Text Label(string name,Transform parent,Vector2 position,Vector2 size,int sizeInPoints,string value)
    {
        var label=new GameObject(name,typeof(RectTransform),typeof(Text)).GetComponent<Text>();label.transform.SetParent(parent,false);Place(label.rectTransform,position,size);label.font=font;label.fontSize=sizeInPoints;label.color=Ink;label.text=value;label.alignment=TextAnchor.MiddleLeft;label.raycastTarget=false;return label;
    }
}
