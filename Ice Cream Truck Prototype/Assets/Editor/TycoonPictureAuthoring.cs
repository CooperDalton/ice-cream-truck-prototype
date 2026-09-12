using System;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.UI;
using Object=UnityEngine.Object;

public static class TycoonPictureAuthoring
{
    private const string Folder="Assets/Art/Tycoon/Icons/";
    public static void Apply()
    {
        var scene=UnityEngine.SceneManagement.SceneManager.GetActiveScene();var game=scene.GetRootGameObjects().SelectMany(o=>o.GetComponents<TycoonGameManager>()).Single();var catalog=game.catalog;var ui=game.hud;
        Directory.CreateDirectory(Folder);AssetDatabase.Refresh();
        catalog.bowlIcon=Render(catalog.bowl,"Bowl");catalog.coneIcon=Render(catalog.cone,"Cone");catalog.basicIcon=Render(catalog.basicScooper,"BasicScooper");catalog.improvedIcon=Render(catalog.improvedScooper,"ImprovedScooper");catalog.batterIcon=Render(catalog.batter,"Batter");catalog.bowlPackIcon=Render(catalog.bowlPack,"BowlPack");catalog.batterPackIcon=Render(catalog.batterPack,"BatterPack");
        catalog.flavorIcons=catalog.scoops.Select((p,i)=>Render(p,"Flavor"+i)).ToArray();catalog.toppingIcons=catalog.toppings.Select((p,i)=>Render(p,"Topping"+i)).ToArray();
        ApplyTubIcons(catalog);
        foreach(var slot in ui.hotbar.Concat(ui.playerSlots).Concat(ui.storageSlots))
        {
            var rect=slot.frame.rectTransform;slot.icon=Image("Item picture",rect,new Vector2(0,10),new Vector2(54,42),Color.white);slot.icon.preserveAspect=true;
            slot.label.rectTransform.anchoredPosition=new Vector2(0,-rect.sizeDelta.y/2+21);slot.label.rectTransform.sizeDelta=new Vector2(rect.sizeDelta.x-8,24);slot.label.fontSize=12;
        }
        ui.orders.gameObject.SetActive(false);ui.tickets=new TycoonHUD.OrderView[3];
        for(int i=0;i<3;i++)
        {
            var panel=Image("Order card",ui.transform,new Vector2(575,220-i*165),new Vector2(375,150),new Color(1,.97f,.89f,.95f));
            ui.tickets[i]=new TycoonHUD.OrderView{root=panel.gameObject,title=Text(ui.panelText,"Order",panel.transform,new Vector2(0,54),new Vector2(350,26),18),description=Text(ui.panelText,"Ingredients",panel.transform,new Vector2(0,-46),new Vector2(350,46),14),container=Image("Container",panel.transform,new Vector2(-137,10),new Vector2(58,58),Color.white)};
            ui.tickets[i].description.text = ""; ui.tickets[i].description.gameObject.SetActive(false);
            ui.tickets[i].flavors=Enumerable.Range(0,2).Select(j=>Image("Flavor",panel.transform,new Vector2(-70+j*60,10),new Vector2(56,56),Color.white)).ToArray();
            ui.tickets[i].toppings=Enumerable.Range(0,2).Select(j=>Image("Topping",panel.transform,new Vector2(60+j*65,10),new Vector2(56,56),Color.white)).ToArray();
        }
        ui.panel.transform.SetAsLastSibling();EditorUtility.SetDirty(catalog);EditorSceneManager.SaveScene(scene);AssetDatabase.SaveAssets();
    }
    public static void ApplyTubIcons(TycoonCatalogSO catalog)
    {
        catalog.tubIcons=catalog.tubs.Select((p,i)=>Render(p,"Tub"+i,1.3f)).ToArray();
        EditorUtility.SetDirty(catalog);AssetDatabase.SaveAssets();
    }
    private static Sprite Render(GameObject prefab,string name,float elevation=.6f)
    {
        string path=Folder+name+".png";var root=Object.Instantiate(prefab,new Vector3(0,200,0),Quaternion.Euler(0,180,0));
        foreach(var t in root.GetComponentsInChildren<Transform>())t.gameObject.layer=31;
        var renderers=root.GetComponentsInChildren<Renderer>();var bounds=renderers[0].bounds;foreach(var r in renderers)bounds.Encapsulate(r.bounds);
        var camera=new GameObject("Icon camera").AddComponent<Camera>();camera.cullingMask=1<<31;camera.clearFlags=CameraClearFlags.SolidColor;camera.backgroundColor=Color.clear;camera.orthographic=true;camera.orthographicSize=bounds.extents.magnitude*1.08f;camera.nearClipPlane=.01f;camera.farClipPlane=20;
        camera.transform.position=bounds.center+new Vector3(.7f,elevation,1).normalized*3;camera.transform.LookAt(bounds.center);
        var target=new RenderTexture(128,128,24);camera.targetTexture=target;camera.Render();var previous=RenderTexture.active;RenderTexture.active=target;
        var texture=new Texture2D(128,128,TextureFormat.RGBA32,false);texture.ReadPixels(new Rect(0,0,128,128),0,0);texture.Apply();File.WriteAllBytes(path,texture.EncodeToPNG());RenderTexture.active=previous;
        camera.targetTexture=null;Object.DestroyImmediate(target);Object.DestroyImmediate(texture);Object.DestroyImmediate(camera.gameObject);Object.DestroyImmediate(root);
        AssetDatabase.ImportAsset(path);var importer=(TextureImporter)AssetImporter.GetAtPath(path);importer.textureType=TextureImporterType.Sprite;importer.spriteImportMode=SpriteImportMode.Single;importer.alphaIsTransparency=true;importer.SaveAndReimport();return AssetDatabase.LoadAssetAtPath<Sprite>(path);
    }
    private static Image Image(string name,Transform parent,Vector2 position,Vector2 size,Color color)
    {
        var go=new GameObject(name,typeof(RectTransform),typeof(Image));var image=go.GetComponent<Image>();image.transform.SetParent(parent,false);image.rectTransform.anchoredPosition=position;image.rectTransform.sizeDelta=size;image.color=color;image.raycastTarget=false;image.preserveAspect=true;return image;
    }
    private static Text Text(Text source,string name,Transform parent,Vector2 position,Vector2 size,int fontSize)
    {
        var text=Object.Instantiate(source,parent);text.name=name;text.rectTransform.anchoredPosition=position;text.rectTransform.sizeDelta=size;text.fontSize=fontSize;text.alignment=TextAnchor.MiddleLeft;return text;
    }
}
