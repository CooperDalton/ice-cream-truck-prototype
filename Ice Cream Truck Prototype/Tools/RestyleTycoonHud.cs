var scene=UnityEngine.SceneManagement.SceneManager.GetActiveScene();
var g=scene.GetRootGameObjects().SelectMany(o=>o.GetComponents<TycoonGameManager>()).Single();var ui=g.hud;
string path="Assets/Art/Tycoon/UI/ScoopSlotOutline.png";
var importer=(UnityEditor.TextureImporter)UnityEditor.AssetImporter.GetAtPath(path);importer.textureType=UnityEditor.TextureImporterType.Sprite;importer.spriteImportMode=UnityEditor.SpriteImportMode.Single;importer.alphaIsTransparency=true;importer.mipmapEnabled=false;importer.maxTextureSize=512;importer.textureCompression=UnityEditor.TextureImporterCompression.Uncompressed;importer.SaveAndReimport();
var sprite=UnityEditor.AssetDatabase.LoadAssetAtPath<UnityEngine.Sprite>(path);
foreach(var text in new[]{ui.notice,ui.prompt,ui.heldLabel,ui.waypointText,ui.orders})text.gameObject.SetActive(false);
foreach(var text in ui.GetComponentsInChildren<UnityEngine.UI.Text>(true).Where(t=>t.text.StartsWith("WASD move")))text.gameObject.SetActive(false);
foreach(var slot in ui.hotbar.Concat(ui.playerSlots).Concat(ui.storageSlots))
{
    slot.label.gameObject.SetActive(false);slot.frame.sprite=sprite;slot.frame.type=UnityEngine.UI.Image.Type.Simple;slot.frame.preserveAspect=true;slot.frame.color=UnityEngine.Color.white;
    slot.button.transition=UnityEngine.UI.Selectable.Transition.None;
    slot.icon.rectTransform.anchoredPosition=UnityEngine.Vector2.zero;slot.icon.rectTransform.sizeDelta=new UnityEngine.Vector2(62,62);slot.icon.preserveAspect=true;
    var bar=(UnityEngine.RectTransform)slot.bar.transform.parent;bar.anchoredPosition=new UnityEngine.Vector2(0,-32);bar.sizeDelta=new UnityEngine.Vector2(47,4);
}
for(int i=0;i<8;i++)
{
    var slot=ui.hotbar[i];slot.frame.rectTransform.sizeDelta=new UnityEngine.Vector2(78,78);slot.frame.rectTransform.anchoredPosition=new UnityEngine.Vector2((i-3.5f)*88,-385);slot.icon.rectTransform.sizeDelta=new UnityEngine.Vector2(55,55);
}
foreach(var card in ui.tickets)
{
    card.description.gameObject.SetActive(false);card.root.GetComponent<UnityEngine.UI.Image>().color=new UnityEngine.Color(1,.96f,.86f,.88f);
    var rect=(UnityEngine.RectTransform)card.root.transform;rect.sizeDelta=new UnityEngine.Vector2(300,95);
    card.title.rectTransform.anchoredPosition=new UnityEngine.Vector2(105,24);card.title.rectTransform.sizeDelta=new UnityEngine.Vector2(80,30);card.title.alignment=UnityEngine.TextAnchor.MiddleRight;
    card.container.rectTransform.anchoredPosition=new UnityEngine.Vector2(-112,0);card.container.rectTransform.sizeDelta=new UnityEngine.Vector2(50,50);
    for(int i=0;i<2;i++){card.flavors[i].rectTransform.anchoredPosition=new UnityEngine.Vector2(-58+i*50,0);card.flavors[i].rectTransform.sizeDelta=new UnityEngine.Vector2(46,46);card.toppings[i].rectTransform.anchoredPosition=new UnityEngine.Vector2(43+i*40,-10);card.toppings[i].rectTransform.sizeDelta=new UnityEngine.Vector2(36,40);}
}
for(int i=0;i<ui.tickets.Length;i++)((UnityEngine.RectTransform)ui.tickets[i].root.transform).anchoredPosition=new UnityEngine.Vector2(630,280-i*110);
var header=ui.GetComponentsInChildren<UnityEngine.UI.Image>(true).Single(i=>i.name=="Header");header.color=UnityEngine.Color.clear;
ui.money.rectTransform.anchoredPosition=new UnityEngine.Vector2(-650,420);ui.money.rectTransform.sizeDelta=new UnityEngine.Vector2(235,42);ui.money.color=new UnityEngine.Color(.23f,.19f,.29f);ui.money.fontSize=27;
ui.clock.color=ui.money.color;
ui.dayValue=UnityEngine.Object.Instantiate(ui.money,ui.transform);ui.dayValue.name="Day value";ui.dayValue.rectTransform.anchoredPosition=new UnityEngine.Vector2(-480,420);ui.dayValue.rectTransform.sizeDelta=new UnityEngine.Vector2(60,42);
ui.levelValue=UnityEngine.Object.Instantiate(ui.dayValue,ui.transform);ui.levelValue.name="Level value";ui.levelValue.rectTransform.anchoredPosition=new UnityEngine.Vector2(-382,420);
foreach(var pair in new[]{new{symbol="☀",x=-532f},new{symbol="★",x=-430f}})
{
    var icon=UnityEngine.Object.Instantiate(ui.dayValue,ui.transform);icon.name="Status symbol";icon.text=pair.symbol;icon.rectTransform.anchoredPosition=new UnityEngine.Vector2(pair.x,420);icon.rectTransform.sizeDelta=new UnityEngine.Vector2(40,42);icon.color=new UnityEngine.Color(.78f,.47f,.28f);
}
ui.xpBar.transform.parent.GetComponent<UnityEngine.RectTransform>().sizeDelta=new UnityEngine.Vector2(110,4);ui.xpBar.transform.parent.GetComponent<UnityEngine.RectTransform>().anchoredPosition=new UnityEngine.Vector2(-400,393);
ui.panel.transform.SetAsLastSibling();UnityEditor.SceneManagement.EditorSceneManager.SaveScene(scene);UnityEditor.AssetDatabase.SaveAssets();return "Authored illustrated inventory frames, icon-only slots and recipe cards, and removed tutorial HUD text.";
