using System;
using System.Linq;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.UI;
using Object = UnityEngine.Object;

public static class TycoonSupplyMenuAuthoring
{
    private static readonly Color Ink = new Color(.2f,.18f,.25f);
    private static Font font;
    private static Sprite paper;

    [MenuItem("Ice Cream/Author supply category cards")]
    public static void Build()
    {
        if (EditorApplication.isPlaying) throw new InvalidOperationException("Stop Play Mode before editing the supplies menu.");
        var scene=UnityEngine.SceneManagement.SceneManager.GetActiveScene();
        var game=scene.GetRootGameObjects().SelectMany(g=>g.GetComponents<TycoonGameManager>()).Single();
        var hud=game.hud; var catalog=game.catalog;
        font=hud.panelTitle.font; paper=hud.salePopupBackground.sprite;
        foreach(var button in hud.supplyButtons) button.transform.SetParent(hud.shopPanel.transform,false);
        foreach(Transform child in hud.shopPanel.transform.Cast<Transform>().ToArray())
            if(!hud.supplyButtons.Any(b=>b.transform==child)) Object.DestroyImmediate(child.gameObject);
        if (hud.supplyButtons.Length == 22)
        {
            Array.Resize(ref hud.supplyButtons, 23);
            hud.supplyButtons[22] = Object.Instantiate(hud.supplyButtons[20], hud.shopPanel.transform);
        }
        hud.supplyCategoryButtons=new Button[4];hud.supplyCategoryPanels=new GameObject[4];
        hud.supplyLocks=new GameObject[23];hud.supplyCardContents=new CanvasGroup[23];
        string[] categories={"Ice Cream","Toppings","Supplies","Tools"};
        int[][] products={Enumerable.Range(0,12).ToArray(),Enumerable.Range(12,6).ToArray(),new[]{18,19},new[]{21,20,22}};
        for(int category=0;category<4;category++)
        {
            var tab=Picture(categories[category],hud.shopPanel.transform,new Vector2(-411+category*274,220),new Vector2(260,48),new Color(.85f,.89f,.78f));
            tab.raycastTarget=true;
            var tabButton=tab.gameObject.AddComponent<Button>();tabButton.targetGraphic=tab;
            Text("Category",tab.transform,Vector2.zero,new Vector2(246,42),categories[category],23);
            hud.supplyCategoryButtons[category]=tabButton;
            var group=new GameObject(categories[category]+" products",typeof(RectTransform));group.transform.SetParent(hud.shopPanel.transform,false);
            ((RectTransform)group.transform).sizeDelta=new Vector2(1100,450);hud.supplyCategoryPanels[category]=group;
            for(int slot=0;slot<products[category].Length;slot++)
            {
                int product=products[category][slot];var button=hud.supplyButtons[product];
                button.transform.SetParent(group.transform,false);
                foreach(Transform child in button.transform.Cast<Transform>().ToArray())Object.DestroyImmediate(child.gameObject);
                bool large=category>=2;
                var rect=(RectTransform)button.transform;rect.anchorMin=rect.anchorMax=rect.pivot=new Vector2(.5f,.5f);
                rect.localScale=Vector3.one;rect.sizeDelta=large?new Vector2(260,240):new Vector2(168,176);
                rect.anchoredPosition=large?new Vector2(-(products[category].Length-1)*145+slot*290,0):new Vector2(-455+slot%6*182,category==0?85-slot/6*190:0);
                var background=button.GetComponent<Image>();background.sprite=paper;background.type=Image.Type.Sliced;background.color=new Color(.88f,.92f,.82f);
                button.targetGraphic=background;var colors=button.colors;colors.normalColor=Color.white;colors.highlightedColor=new Color(.8f,1,.86f);colors.pressedColor=new Color(.57f,.84f,.68f);colors.disabledColor=new Color(.93f,.93f,.89f);button.colors=colors;
                var content=new GameObject("Product",typeof(RectTransform),typeof(CanvasGroup));content.transform.SetParent(button.transform,false);
                ((RectTransform)content.transform).sizeDelta=rect.sizeDelta;hud.supplyCardContents[product]=content.GetComponent<CanvasGroup>();
                Sprite icon=product<12?catalog.tubIcons[product]:product<18?catalog.toppingIcons[product-12]:product==18?catalog.bowlPackIcon:product==19?catalog.batterIcon:product==20?catalog.improvedIcon:product==22?catalog.electricIcon:catalog.basicIcon;
                var picture=Picture("Icon",content.transform,new Vector2(0,large?30:29),Vector2.one*(large?144:92),Color.white,icon);
                picture.type=Image.Type.Simple;picture.preserveAspect=true;
                string name=product<12?TycoonCatalogSO.FlavorNames[product]:product<18?TycoonCatalogSO.ToppingNames[product-12]:product==18?"12 bowls · 1 stack":product==19?"Batter · 1 bottle":product==20?"High quality scooper":product==22?"Electric scooper":"Basic scooper";
                float price=product<12?TycoonCatalogSO.TubPrices[product]:product<18?TycoonCatalogSO.RefillPrices[product-12]:product==18?3:product==19||product==21?6:product==22?36:12;
                button.name=name+" supply card";
                Text("Name",content.transform,new Vector2(0,large?-58:-30),new Vector2(rect.sizeDelta.x-12,28),name,large?23:19);
                Text("Price",content.transform,new Vector2(0,large?-94:-62),new Vector2(rect.sizeDelta.x-12,30),"$"+price.ToString("0.##"),large?26:23).fontStyle=FontStyle.Bold;
                int level=product<12?(product<2?1:product<4?2:product<8?4:6):product<18?(product<14?3:product<16?5:7):1;
                var badge=Picture("Unlock level",button.transform,new Vector2(rect.sizeDelta.x/2-34,rect.sizeDelta.y/2-17),new Vector2(62,26),new Color(.8f,.83f,.73f));
                Text("Level",badge.transform,Vector2.zero,new Vector2(60,24),"Lv "+level,16);
                hud.supplyLocks[product]=badge.gameObject;badge.gameObject.SetActive(false);
            }
        }
        hud.SelectSupplyCategory(0);
        EditorUtility.SetDirty(hud);EditorSceneManager.MarkSceneDirty(scene);EditorSceneManager.SaveScene(scene);AssetDatabase.SaveAssets();
    }
    private static Image Picture(string name,Transform parent,Vector2 position,Vector2 size,Color color,Sprite sprite=null)
    {
        var go=new GameObject(name,typeof(RectTransform),typeof(Image));go.transform.SetParent(parent,false);
        var image=go.GetComponent<Image>();image.rectTransform.anchoredPosition=position;image.rectTransform.sizeDelta=size;
        image.color=color;image.sprite=sprite==null?paper:sprite;image.type=Image.Type.Sliced;image.raycastTarget=false;return image;
    }
    private static Text Text(string name,Transform parent,Vector2 position,Vector2 size,string value,int fontSize)
    {
        var go=new GameObject(name,typeof(RectTransform),typeof(Text));go.transform.SetParent(parent,false);
        var text=go.GetComponent<Text>();text.rectTransform.anchoredPosition=position;text.rectTransform.sizeDelta=size;text.font=font;text.fontSize=fontSize;
        text.text=value;text.color=Ink;text.alignment=TextAnchor.MiddleCenter;text.raycastTarget=false;return text;
    }
}
