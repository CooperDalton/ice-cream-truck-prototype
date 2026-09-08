using System.Linq;
using System.IO;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.UI;

public static class PrototypeSceneRefinement
{
    [MenuItem("Ice Cream/Apply interaction refinements")]
    public static void Apply()
    {
        var r=PrototypeSceneReferences.Instance;
        foreach(var holder in r.holders)
        {
            var b=holder.highlightRenderers[0].bounds;
            foreach(var renderer in holder.highlightRenderers)b.Encapsulate(renderer.bounds);
            var c=holder.GetComponent<BoxCollider>();c.center=holder.transform.InverseTransformPoint(new Vector3(b.center.x,b.min.y+.07f,b.center.z));c.size=new Vector3(.13f,.14f,.13f);
        }
        r.interaction.rightHand.localPosition=new Vector3(0,-.45f,.55f);r.interaction.rightHand.localScale=Vector3.one*.5f;
        r.hud.GetComponent<CanvasScaler>().matchWidthOrHeight=0;
        var importer=(TextureImporter)AssetImporter.GetAtPath("Assets/Art/ProgressRing.png");importer.textureType=TextureImporterType.Sprite;importer.spriteImportMode=SpriteImportMode.Single;importer.SaveAndReimport();
        r.hud.progressRing.sprite=AssetDatabase.LoadAllAssetsAtPath("Assets/Art/ProgressRing.png").OfType<Sprite>().Single();
        var texture=new Texture2D(2,2);texture.SetPixels(new[]{Color.white,Color.white,Color.white,Color.white});texture.Apply();File.WriteAllBytes("Assets/Art/UIWhite.png",texture.EncodeToPNG());Object.DestroyImmediate(texture);AssetDatabase.ImportAsset("Assets/Art/UIWhite.png");
        var white=(TextureImporter)AssetImporter.GetAtPath("Assets/Art/UIWhite.png");white.textureType=TextureImporterType.Sprite;white.spriteImportMode=SpriteImportMode.Single;white.SaveAndReimport();
        var sprite=AssetDatabase.LoadAllAssetsAtPath("Assets/Art/UIWhite.png").OfType<Sprite>().Single();r.hud.quotaFill.sprite=sprite;r.hud.patienceFill.sprite=sprite;
        PlayerSettings.runInBackground=true;
        EditorSceneManager.MarkSceneDirty(r.gameObject.scene);EditorSceneManager.SaveScene(r.gameObject.scene);AssetDatabase.SaveAssets();
    }
}
