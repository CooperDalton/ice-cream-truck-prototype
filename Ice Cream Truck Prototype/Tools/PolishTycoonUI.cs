var scene=UnityEngine.SceneManagement.SceneManager.GetActiveScene();
var g=scene.GetRootGameObjects().SelectMany(o=>o.GetComponents<TycoonGameManager>()).Single();
const string path="Assets/Art/Tycoon/BarPixel.asset";
var texture=UnityEditor.AssetDatabase.LoadAssetAtPath<UnityEngine.Texture2D>(path);
UnityEngine.Sprite sprite;
if(texture==null)
{
    texture=new UnityEngine.Texture2D(2,2);texture.SetPixels(new[]{UnityEngine.Color.white,UnityEngine.Color.white,UnityEngine.Color.white,UnityEngine.Color.white});texture.Apply();
    UnityEditor.AssetDatabase.CreateAsset(texture,path);sprite=UnityEngine.Sprite.Create(texture,new UnityEngine.Rect(0,0,2,2),new UnityEngine.Vector2(.5f,.5f));UnityEditor.AssetDatabase.AddObjectToAsset(sprite,texture);
}
else sprite=UnityEditor.AssetDatabase.LoadAllAssetsAtPath(path).OfType<UnityEngine.Sprite>().Single();
foreach(var bar in g.hud.GetComponentsInChildren<UnityEngine.UI.Image>(true).Where(i=>i.type==UnityEngine.UI.Image.Type.Filled))bar.sprite=sprite;
var profile=UnityEditor.AssetDatabase.LoadAssetAtPath<UnityEngine.Rendering.VolumeProfile>("Assets/Art/Tycoon/ToonVolume.asset");
profile.components.RemoveAll(c=>c==null);
if(profile.components.Count==0)
{
    var bloom=profile.Add<UnityEngine.Rendering.Universal.Bloom>();bloom.intensity.Override(.08f);UnityEditor.AssetDatabase.AddObjectToAsset(bloom,profile);
    var color=profile.Add<UnityEngine.Rendering.Universal.ColorAdjustments>();color.saturation.Override(7);color.contrast.Override(4);UnityEditor.AssetDatabase.AddObjectToAsset(color,profile);
}
g.player.view.GetComponent<UnityEngine.Rendering.Universal.UniversalAdditionalCameraData>().antialiasing=UnityEngine.Rendering.Universal.AntialiasingMode.SubpixelMorphologicalAntiAliasing;
UnityEditor.EditorUtility.SetDirty(profile);UnityEditor.AssetDatabase.SaveAssets();UnityEditor.SceneManagement.EditorSceneManager.SaveScene(scene);
return "Supply bars now have a fillable sprite; post-processing components saved as profile subassets.";
