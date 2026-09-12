using System;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.UI;
using Object = UnityEngine.Object;

public static class AuthorTycoonDaySummary
{
    private static Font font;
    private static Sprite paper;
    private static readonly Color Ink = new Color(.24f,.20f,.29f), Mint = new Color(.43f,.72f,.64f);
    public static string Build()
    {
        if (EditorApplication.isPlaying) throw new Exception("Stop Play Mode before authoring");
        var scene = UnityEngine.SceneManagement.SceneManager.GetActiveScene();
        var game = scene.GetRootGameObjects()[0].GetComponent<TycoonGameManager>();
        var hud = game.hud;
        font = hud.money.font; paper = hud.moneyDisplay.parent.GetComponent<Image>().sprite;
        Undo.RegisterFullObjectHierarchyUndo(hud.gameObject, "Author day summary");
        if (hud.daySummary != null) Object.DestroyImmediate(hud.daySummary.gameObject);
        var overlay = Picture("Day summary", hud.transform, Vector2.zero, Vector2.zero, new Color(.12f,.10f,.16f,.72f));
        overlay.rectTransform.anchorMin = Vector2.zero; overlay.rectTransform.anchorMax = Vector2.one; overlay.raycastTarget = true;
        var summary = overlay.gameObject.AddComponent<TycoonDaySummary>(); summary.game = game; hud.daySummary = summary;
        var window = Picture("Summary card", overlay.transform, Vector2.zero, new Vector2(640,390),new Color(1,.97f,.90f), paper);
        window.raycastTarget = true; summary.window = window.rectTransform;
        summary.title = Label("Title",window.transform,new Vector2(0,-40),new Vector2(568,44),32,"Day complete");
        string[] labels = { "Sales", "Wages & vehicle", "Cash balance", "Missed orders" };
        var values = new Text[4];
        for (int i=0;i<4;i++)
        {
            var tile = Picture(labels[i],window.transform,new Vector2(-216+i*144,-114),new Vector2(136,84),new Color(.91f,.93f,.85f),paper); Top(tile.rectTransform);
            var label = Label("Label",tile.transform,new Vector2(0,-20),new Vector2(124,22),15,labels[i]); label.alignment=TextAnchor.MiddleCenter;
            values[i] = Label("Value",tile.transform,new Vector2(i<3?9:0,-54),new Vector2(i<3?96:124,30),24,"0"); values[i].alignment=TextAnchor.MiddleCenter;
            if(i<3)
            {
                var coin=Picture("Coin",tile.transform,new Vector2(-48,-54),new Vector2(22,22),Color.white,hud.tickets[0].coin.sprite);
                coin.type=Image.Type.Simple;coin.preserveAspect=true;Top(coin.rectTransform);
            }
        }
        summary.sales=values[0];summary.costs=values[1];summary.cash=values[2];summary.missed=values[3];
        var divider=Picture("Divider",window.transform,new Vector2(0,-174),new Vector2(568,1),new Color(.48f,.40f,.32f,.18f));Top(divider.rectTransform);
        summary.level=Label("Animated level",window.transform,new Vector2(-142,-205),new Vector2(284,34),24,"Level 1");
        summary.earnedXP=Label("Earned XP",window.transform,new Vector2(142,-205),new Vector2(284,34),26,"+0 XP");summary.earnedXP.alignment=TextAnchor.MiddleRight;summary.earnedXP.color=new Color(.61f,.27f,.40f);
        var track=Picture("XP track",window.transform,new Vector2(0,-241),new Vector2(568,12),new Color(.86f,.84f,.76f),paper);Top(track.rectTransform);
        summary.xpFill=Picture("Animated XP",track.transform,Vector2.zero,new Vector2(568,12),new Color(.77f,.37f,.51f),hud.xpBar.sprite);
        summary.xpFill.type=Image.Type.Filled;summary.xpFill.fillMethod=Image.FillMethod.Horizontal;summary.xpFill.fillOrigin=0;
        summary.progress=Label("XP progress",window.transform,new Vector2(0,-265),new Vector2(568,24),16,"0 / 60 XP");summary.progress.alignment=TextAnchor.MiddleRight;
        var unlockRoot=new GameObject("Unlock reveal",typeof(RectTransform),typeof(CanvasGroup));unlockRoot.transform.SetParent(window.transform,false);
        var root=(RectTransform)unlockRoot.transform;root.anchorMin=root.anchorMax=root.pivot=new Vector2(.5f,1);root.anchoredPosition=new Vector2(0,-300);root.sizeDelta=new Vector2(568,236);
        summary.unlockGroup=unlockRoot.GetComponent<CanvasGroup>();
        summary.unlockTitle=Label("Unlock title",root,new Vector2(0,-8),new Vector2(568,28),21,"Unlocked");
        var viewport=new GameObject("Ingredients viewport",typeof(RectTransform),typeof(RectMask2D),typeof(Image),typeof(ScrollRect));viewport.transform.SetParent(root,false);
        var view=(RectTransform)viewport.transform;view.anchorMin=view.anchorMax=view.pivot=new Vector2(.5f,1);view.anchoredPosition=new Vector2(0,-34);view.sizeDelta=new Vector2(568,176);
        viewport.GetComponent<Image>().color=Color.clear;
        var content=new GameObject("Ingredients",typeof(RectTransform),typeof(GridLayoutGroup));content.transform.SetParent(view,false);
        summary.unlockContent=(RectTransform)content.transform;summary.unlockContent.anchorMin=summary.unlockContent.anchorMax=summary.unlockContent.pivot=new Vector2(.5f,1);summary.unlockContent.sizeDelta=new Vector2(568,92);
        var grid=content.GetComponent<GridLayoutGroup>();grid.cellSize=new Vector2(136,84);grid.spacing=new Vector2(8,8);grid.constraint=GridLayoutGroup.Constraint.FixedColumnCount;grid.constraintCount=4;
        summary.unlockScroll=viewport.GetComponent<ScrollRect>();summary.unlockScroll.viewport=view;summary.unlockScroll.content=summary.unlockContent;summary.unlockScroll.horizontal=false;summary.unlockScroll.movementType=ScrollRect.MovementType.Clamped;summary.unlockScroll.scrollSensitivity=24;
        summary.unlocks=new TycoonDaySummary.UnlockView[16];
        for(int i=0;i<16;i++)
        {
            var card=Picture("Ingredient "+i,content.transform,Vector2.zero,new Vector2(136,84),new Color(.92f,.94f,.87f),paper);
            var icon=Picture("Icon",card.transform,new Vector2(0,10),new Vector2(58,50),Color.white);icon.preserveAspect=true;
            var label=Label("Name",card.transform,new Vector2(0,-66),new Vector2(128,30),16,"");label.alignment=TextAnchor.MiddleCenter;
            summary.unlocks[i]=new TycoonDaySummary.UnlockView {root=card.gameObject,icon=icon,label=label};
        }
        var button=Object.Instantiate(hud.inventoryCloseButton,window.transform);button.name="Start next day";
        var buttonRect=(RectTransform)button.transform;buttonRect.anchorMin=buttonRect.anchorMax=new Vector2(.5f,0);buttonRect.anchoredPosition=new Vector2(0,51);buttonRect.sizeDelta=new Vector2(568,46);
        button.GetComponentInChildren<Text>().text="Next day";button.GetComponentInChildren<Text>().fontSize=20;summary.continueButton=button;
        hud.xpBar.transform.parent.gameObject.SetActive(false);
        summary.gameObject.SetActive(false);EditorUtility.SetDirty(hud);EditorUtility.SetDirty(summary);
        EditorSceneManager.MarkSceneDirty(scene);EditorSceneManager.SaveScene(scene);
        return "Authored compact day summary, animated XP bar, and scrollable ingredient reveal. Daytime XP bar hidden.";
    }
    private static void Top(RectTransform rect)
    {
        rect.anchorMin=rect.anchorMax=new Vector2(.5f,1);
    }
    private static Text Label(string name,Transform parent,Vector2 position,Vector2 size,int fontSize,string value)
    {
        var text=new GameObject(name,typeof(RectTransform),typeof(Text)).GetComponent<Text>();text.transform.SetParent(parent,false);
        Top(text.rectTransform);text.rectTransform.anchoredPosition=position;text.rectTransform.sizeDelta=size;
        text.font=font;text.fontSize=fontSize;text.color=Ink;text.text=value;text.alignment=TextAnchor.MiddleLeft;text.raycastTarget=false;
        return text;
    }
    private static Image Picture(string name,Transform parent,Vector2 position,Vector2 size,Color color,Sprite sprite=null)
    {
        var image=new GameObject(name,typeof(RectTransform),typeof(Image)).GetComponent<Image>();image.transform.SetParent(parent,false);
        image.rectTransform.anchorMin=image.rectTransform.anchorMax=new Vector2(.5f,.5f);image.rectTransform.anchoredPosition=position;image.rectTransform.sizeDelta=size;
        image.color=color;image.sprite=sprite;image.type=sprite==null?Image.Type.Simple:Image.Type.Sliced;image.raycastTarget=false;
        return image;
    }
}
