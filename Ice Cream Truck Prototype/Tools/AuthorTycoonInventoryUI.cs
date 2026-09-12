using System;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.UI;
using Object = UnityEngine.Object;

public static class AuthorTycoonInventoryUI
{
    public static string Build()
    {
        if (EditorApplication.isPlaying) throw new Exception("Stop Play Mode before authoring inventory UI");
        var scene = UnityEngine.SceneManagement.SceneManager.GetActiveScene();
        var hud = scene.GetRootGameObjects()[0].GetComponent<TycoonGameManager>().hud;
        var paper = hud.moneyDisplay.parent.GetComponent<Image>().sprite;
        var font = hud.money.font;
        var ink = new Color(.24f,.20f,.29f);
        var mint = new Color(.43f,.72f,.64f);
        Undo.RegisterFullObjectHierarchyUndo(hud.gameObject,"Restyle inventory");
        if (hud.personalInventoryPanel != null) Object.DestroyImmediate(hud.personalInventoryPanel);
        var overlay = CreateImage("Inventory overlay",hud.transform,Vector2.zero,Vector2.zero,new Color(.12f,.10f,.16f,.56f));
        overlay.rectTransform.anchorMin = Vector2.zero; overlay.rectTransform.anchorMax = Vector2.one; overlay.raycastTarget = true;
        overlay.transform.SetSiblingIndex(hud.hotbar[0].frame.transform.GetSiblingIndex());
        hud.personalInventoryPanel = overlay.gameObject;
        var window = CreateImage("Inventory window",overlay.transform,new Vector2(0,70),new Vector2(536,340),new Color(1,.97f,.90f),paper);
        window.raycastTarget = true;
        var title = Object.Instantiate(hud.panelTitle,window.transform); title.name = "Inventory title"; title.text = "Inventory"; title.fontSize = 32;
        Place(title.rectTransform,new Vector2(-116,138),new Vector2(240,42)); title.color = ink; title.raycastTarget = false;
        var close = Object.Instantiate(hud.shelfCloseButton,window.transform); close.name = "Close inventory";
        Place((RectTransform)close.transform,new Vector2(190,138),new Vector2(92,38)); hud.inventoryCloseButton = close;
        CreateImage("Divider",window.transform,new Vector2(0,104),new Vector2(472,1),new Color(.48f,.40f,.32f,.18f));
        hud.inventorySlots = new TycoonHUD.SlotView[8];
        for (int i = 0; i < hud.inventorySlots.Length; i++)
        {
            var position = new Vector2(-168+i%4*112,32-i/4*112);
            CreateImage("Slot surround " + (i+1),window.transform,position,new Vector2(100,100),new Color(.65f,.77f,.69f,.45f),paper);
            var frame = CreateImage("Inventory slot " + (i+1),window.transform,position,new Vector2(96,96),Color.white,paper); frame.raycastTarget = true;
            var button = frame.gameObject.AddComponent<Button>(); button.targetGraphic = frame;
            var colors = button.colors; colors.highlightedColor = new Color(.81f,.94f,.87f); colors.pressedColor = mint; button.colors = colors;
            var icon = CreateImage("Item",frame.transform,new Vector2(0,7),new Vector2(70,70),Color.white); icon.preserveAspect = true;
            var count = new GameObject("Quantity",typeof(RectTransform),typeof(Text)).GetComponent<Text>(); count.transform.SetParent(frame.transform,false);
            Place(count.rectTransform,new Vector2(12,-26),new Vector2(54,26)); count.font = font; count.fontSize = 19; count.color = ink; count.alignment = TextAnchor.MiddleRight; count.raycastTarget = false;
            var track = CreateImage("Supply track",frame.transform,new Vector2(0,-39),new Vector2(66,4),new Color(.37f,.33f,.29f,.13f));
            var fill = CreateImage("Supply",track.transform,Vector2.zero,new Vector2(66,4),mint,hud.hotbar[0].bar.sprite);
            fill.type = Image.Type.Filled; fill.fillMethod = Image.FillMethod.Horizontal; fill.fillOrigin = 0;
            hud.inventorySlots[i] = new TycoonHUD.SlotView {button=button,frame=frame,icon=icon,label=count,bar=fill};
            icon.gameObject.SetActive(false); track.gameObject.SetActive(false);
        }
        hud.personalInventoryPanel.SetActive(false); EditorUtility.SetDirty(hud);
        EditorSceneManager.MarkSceneDirty(scene); EditorSceneManager.SaveScene(scene);
        return "Authored compact inventory with eight centered slots matching shelf styling.";
    }
    private static void Place(RectTransform rect, Vector2 position, Vector2 size)
    {
        rect.anchorMin = rect.anchorMax = rect.pivot = new Vector2(.5f,.5f);
        rect.anchoredPosition = position; rect.sizeDelta = size;
    }
    private static Image CreateImage(string name,Transform parent,Vector2 position,Vector2 size,Color color,Sprite sprite=null)
    {
        var image = new GameObject(name,typeof(RectTransform),typeof(Image)).GetComponent<Image>(); image.transform.SetParent(parent,false);
        Place(image.rectTransform,position,size); image.color=color; image.sprite=sprite; image.type=sprite==null?Image.Type.Simple:Image.Type.Sliced; image.raycastTarget=false;
        return image;
    }
}
