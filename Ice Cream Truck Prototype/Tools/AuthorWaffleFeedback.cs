using UnityEngine;
using UnityEngine.UI;
using UnityEditor;
using UnityEditor.SceneManagement;
public static class AuthorWaffleFeedback {
public static string Run(){
foreach(var name in new[]{"IceCreamPrototype","ParkRoute"}){
var scene=EditorSceneManager.OpenScene("Assets/Scenes/"+name+".unity");var r=PrototypeSceneReferences.Instance;
var indicator=r.waffle.GetComponentInChildren<WaffleIndicator>(true);
if(indicator.burnRing==null){var go=new GameObject("Burn timer",typeof(RectTransform),typeof(CanvasRenderer),typeof(Image));go.transform.SetParent(indicator.panel.transform,false);indicator.burnRing=go.GetComponent<Image>();}
var ring=indicator.burnRing;ring.sprite=indicator.ring.sprite;ring.rectTransform.sizeDelta=indicator.ring.rectTransform.sizeDelta*1.27f;ring.rectTransform.anchoredPosition=Vector2.zero;ring.type=Image.Type.Filled;ring.fillMethod=Image.FillMethod.Radial360;ring.fillOrigin=2;ring.fillClockwise=true;ring.raycastTarget=false;ring.color=new Color(.93f,.25f,.23f);ring.fillAmount=0;ring.gameObject.SetActive(false);
foreach(var collider in r.truck.GetComponentsInChildren<MeshCollider>(true))if(collider.name.StartsWith("WaffleStation_")){var surface=collider.GetComponent<PlacementSurface>();if(surface==null)surface=collider.gameObject.AddComponent<PlacementSurface>();surface.highlightRenderers=new Renderer[0];}
r.hud.quotaText.gameObject.SetActive(false);r.hud.quotaText.text="";r.hud.moneyText.text="$0/"+r.day.Quota;
var rect=r.hud.moneyText.rectTransform;rect.anchoredPosition=new Vector2(rect.anchoredPosition.x,0);rect.sizeDelta=new Vector2(190,50);
EditorSceneManager.MarkSceneDirty(scene);EditorSceneManager.SaveScene(scene);
}
EditorSceneManager.OpenScene("Assets/Scenes/IceCreamPrototype.unity");return "Authored outer burn rings, compact earnings and waffle worktop placement in both scenes.";
}}
