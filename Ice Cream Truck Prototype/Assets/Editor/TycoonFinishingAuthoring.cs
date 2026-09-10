using System;
using System.Linq;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.UI;
using Object = UnityEngine.Object;

public static class TycoonFinishingAuthoring
{
    public static void Apply()
    {
        var scene = UnityEngine.SceneManagement.SceneManager.GetActiveScene();
        var game = scene.GetRootGameObjects().SelectMany(o => o.GetComponents<TycoonGameManager>()).Single(); var ui = game.hud;
        ui.assignLockerButton = Button(ui.cargoButton,"Assign next locker",ui.inventoryPanel.transform,new Vector2(-245,-190),new Vector2(420,48));
        ui.newGameButton = Button(ui.saveButton,"New campaign",ui.menuPanel.transform,new Vector2(-270,-70),new Vector2(230,46));
        ui.quitButton = Button(ui.saveButton,"Save and quit",ui.menuPanel.transform,new Vector2(270,-70),new Vector2(230,46));
        var upgrades = ui.upgradeButtons.ToList();
        foreach (var label in new[] { "Prep table / $24", "Serving holder / $12", "Cold rack / $36", "Cooled tub module / $18", "Waffle iron / $48", "Supply shelf / $20" }) upgrades.Add(Button(ui.upgradeButtons[0],label,ui.businessPanel.transform,Vector2.zero,new Vector2(262,48)));
        ui.upgradeButtons = upgrades.ToArray();
        for (int i = 0; i < upgrades.Count; i++) upgrades[i].GetComponent<RectTransform>().anchoredPosition = new Vector2(-410+i%4*275,210-i/4*56);
        foreach (var button in ui.hireButtons) { var r=button.GetComponent<RectTransform>();r.anchoredPosition=new Vector2(r.anchoredPosition.x,-75); }
        var supplies = ui.supplyButtons.ToList(); supplies.Add(Button(ui.supplyButtons[0],"Batter bottle / $4",ui.shopPanel.transform,Vector2.zero,new Vector2(264,43))); supplies.Add(Button(ui.supplyButtons[0],"Basic scooper / $6",ui.shopPanel.transform,Vector2.zero,new Vector2(264,43)));
        ui.supplyButtons = supplies.ToArray();
        for (int i=0;i<supplies.Count;i++) { var r=supplies[i].GetComponent<RectTransform>();r.anchoredPosition=new Vector2(-420+i%4*280,200-i/4*51);r.sizeDelta=new Vector2(264,43); }
        string workerPath=AssetDatabase.GetAssetPath(game.catalog.workerPrefab);var worker=PrefabUtility.LoadPrefabContents(workerPath);
        var collider=worker.AddComponent<CapsuleCollider>();collider.center=Vector3.up*.9f;collider.height=1.65f;collider.radius=.28f;
        PrefabUtility.SaveAsPrefabAsset(worker,workerPath);PrefabUtility.UnloadPrefabContents(worker);
        foreach (int index in new[]{3,4,5})
        {
            string path=AssetDatabase.GetAssetPath(game.catalog.partPrefabs[index]);var root=PrefabUtility.LoadPrefabContents(path);var part=root.GetComponent<TycoonPart>();
            if(index==4) foreach(var model in part.lockerModels)model.transform.localRotation=Quaternion.Euler(0,180,0);
            else if(index==3)part.lid.parent.localRotation=Quaternion.Euler(0,180,0);
            else foreach(var child in root.GetComponentsInChildren<Renderer>())child.transform.localRotation=Quaternion.Euler(0,180,0)*child.transform.localRotation;
            PrefabUtility.SaveAsPrefabAsset(root,path);PrefabUtility.UnloadPrefabContents(root);
        }
        for(int i=0;i<ui.mapLocations.Length;i++)
        {
            Color color=new[]{new Color(.2f,.55f,.45f),new Color(.6f,.3f,.65f),new Color(.85f,.5f,.18f),new Color(.85f,.3f,.45f),new Color(.4f,.4f,.8f),new Color(.2f,.5f,.7f)}[i];
            ui.mapLocations[i].GetComponent<Image>().color=color;ui.miniLocations[i].GetComponent<Image>().color=color;
            ui.destinationButtons[i].targetGraphic.color=color;
        }
        EditorSceneManager.SaveScene(scene);AssetDatabase.SaveAssets();
    }
    private static Button Button(Button source,string label,Transform parent,Vector2 position,Vector2 size)
    {
        var copy=Object.Instantiate(source,parent);copy.name=label;copy.onClick=new Button.ButtonClickedEvent();copy.GetComponentInChildren<Text>().text=label;
        var rect=copy.GetComponent<RectTransform>();rect.anchoredPosition=position;rect.sizeDelta=size;return copy;
    }
}
