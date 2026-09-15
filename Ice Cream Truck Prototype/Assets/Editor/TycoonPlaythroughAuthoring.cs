using System;
using System.Linq;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.UI;
using Object = UnityEngine.Object;

public static class TycoonPlaythroughAuthoring
{
    [MenuItem("Ice Cream/Apply playthrough improvements")]
    public static void Apply()
    {
        if (EditorApplication.isPlaying) throw new InvalidOperationException("Stop Play Mode before authoring.");
        var scene = UnityEngine.SceneManagement.SceneManager.GetActiveScene();
        var game = scene.GetRootGameObjects()[0].GetComponent<TycoonGameManager>();
        var hud = game.hud; var catalog = game.catalog;
        Undo.RegisterFullObjectHierarchyUndo(hud.gameObject, "Playthrough UI");
        game.rewardDeliveryOrigin.position = game.sites[0].origin.TransformPoint(new Vector3(-2.5f, 0, -4.5f));
        var board = game.parts.Single(p => p.site == 0 && p.kind == TycoonPart.Kind.BusinessBoard);
        board.transform.SetPositionAndRotation(game.sites[0].origin.TransformPoint(new Vector3(3, 0, -2.5f)), Quaternion.identity);
        if (!game.parts.Any(p => p.site == 0 && p.kind == TycoonPart.Kind.Trash))
        {
            var trash = (GameObject)PrefabUtility.InstantiatePrefab(catalog.partPrefabs[9].gameObject);
            var part = trash.GetComponent<TycoonPart>(); part.game = game; part.site = 0; part.id = -1;
            trash.transform.position = game.sites[0].origin.TransformPoint(new Vector3(-3.5f, 0, -2.5f));
            game.parts.Add(part);
        }
        var binPath = AssetDatabase.GetAssetPath(catalog.partPrefabs[9]);
        var bin = PrefabUtility.LoadPrefabContents(binPath);
        Object.DestroyImmediate(bin.transform.GetChild(0).gameObject);
        var binModel = (GameObject)PrefabUtility.InstantiatePrefab(AssetDatabase.LoadAssetAtPath<GameObject>("Assets/Art/Tycoon/Prefabs/Town_Street_bin.prefab"), bin.transform);
        binModel.transform.SetAsFirstSibling();
        var hitbox = bin.GetComponent<BoxCollider>(); hitbox.center = new Vector3(0, .4f, 0); hitbox.size = new Vector3(.55f, .8f, .55f);
        PrefabUtility.SaveAsPrefabAsset(bin, binPath); PrefabUtility.UnloadPrefabContents(bin);
        var sceneBin = game.parts.Single(p => p.site == 0 && p.kind == TycoonPart.Kind.Trash);
        sceneBin.game = game; sceneBin.site = 0;
        sceneBin.id = -1;
        sceneBin.transform.position = game.sites[0].origin.TransformPoint(new Vector3(-3.5f, 0, -2.5f));
        PrefabUtility.RecordPrefabInstancePropertyModifications(sceneBin);
        PrefabUtility.RecordPrefabInstancePropertyModifications(sceneBin.transform);
        if (catalog.electricScooper == null)
        {
            var electric = Object.Instantiate(catalog.improvedScooper); electric.name = "Electric scooper";
            var material = new Material(electric.GetComponentsInChildren<Renderer>()[0].sharedMaterial);
            material.SetColor("_BaseColor", new Color(.18f, .65f, .72f));
            AssetDatabase.CreateAsset(material, "Assets/Art/Tycoon/ElectricScooper.mat");
            foreach (var renderer in electric.GetComponentsInChildren<Renderer>()) renderer.sharedMaterial = material;
            catalog.electricScooper = PrefabUtility.SaveAsPrefabAsset(electric, "Assets/Art/Tycoon/Prefabs/ElectricScooper.prefab");
            Object.DestroyImmediate(electric);
        }
        var electricMaterial = AssetDatabase.LoadAssetAtPath<Material>("Assets/Art/Tycoon/ElectricScooper.mat");
        electricMaterial.SetColor("_BaseColor", new Color(.18f, .65f, .72f)); EditorUtility.SetDirty(electricMaterial);
        catalog.electricIcon = TycoonPictureAuthoring.Render(catalog.electricScooper, "ElectricScooper");
        foreach (var slot in hud.hotbar.Concat(hud.playerSlots).Concat(hud.storageSlots).Concat(hud.inventorySlots).Concat(hud.storageViews.SelectMany(v => v.slots)).Concat(hud.employeeStorageView.slots))
        {
            if (slot.scoops != null && slot.scoops.Length > 0) continue;
            slot.scoops = new Image[3];
            for (int i = 0; i < slot.scoops.Length; i++)
            {
                var scoop = Picture("Serving scoop " + (i + 1), slot.icon.transform, catalog.flavorIcons[0], new Vector2((i - 1) * 10, 8 + i * 4), new Vector2(25, 25));
                slot.scoops[i] = scoop; scoop.gameObject.SetActive(false);
            }
        }
        foreach (var ticket in hud.tickets)
        {
            if (ticket.flavors.Length == 3) continue;
            Array.Resize(ref ticket.flavors, 3);
            ticket.flavors[2] = Object.Instantiate(ticket.flavors[1], ticket.flavors[1].transform.parent);
            ticket.flavors[2].name = "Third scoop";
            ticket.flavors[2].transform.SetSiblingIndex(ticket.flavors[1].transform.GetSiblingIndex() + 1);
        }
        var coin = hud.tickets[0].coin.sprite;
        if (hud.salePopupTipCoin == null) hud.salePopupTipCoin = Picture("Tip coin", hud.salePopupTipBackground.transform, coin, new Vector2(-83, 0), new Vector2(28, 28));
        hud.salePopupTip.rectTransform.anchoredPosition = new Vector2(15, 0);
        hud.salePopupTip.rectTransform.sizeDelta = new Vector2(164, 34);
        hud.employeeDetails.rectTransform.sizeDelta = new Vector2(556, 96);
        hud.employeeDetails.rectTransform.anchoredPosition = new Vector2(0, 146);
        hud.employeeDetails.fontSize = 16;
        var active = new[] { 1, 2, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13 };
        hud.upgradeButtons[0].gameObject.SetActive(false); hud.upgradeButtons[3].gameObject.SetActive(false);
        string[] names = { "Locker", "Locker capacity", "Bike cargo", "Expand shop", "Park stand", "Ice cream truck", "Table", "Cone holder", "Cold storage", "Tub holder", "Waffle iron", "Shelf" };
        string[] prices = { "$24", "$48 / $88", "$48", "$160", "$250", "$600", "$24", "$12", "$36", "$18", "$48", "$20" };
        int[] icons = { 4, 4, 8, 0, 6, 7, 0, 2, 5, 1, 3, 8 };
        var businessIcons = icons.Select(i => catalog.equipmentIcons[i]).ToArray();
        businessIcons[2] = TycoonPictureAuthoring.Render(game.bike.smallCargoModel, "UpgradeBike");
        businessIcons[3] = TycoonPictureAuthoring.Render(game.sites[0].kiosk, "UpgradeKiosk");
        businessIcons[4] = TycoonPictureAuthoring.Render(game.sites[1].canopy, "UpgradePark");
        businessIcons[5] = TycoonPictureAuthoring.Render(game.truck.gameObject, "UpgradeTruck");
        var panelRect = (RectTransform)hud.businessPanel.transform;
        panelRect.anchoredPosition = new Vector2(0, -25); panelRect.sizeDelta = new Vector2(1100, 460);
        for (int i = 0; i < active.Length; i++)
        {
            var button = hud.upgradeButtons[active[i]]; var rect = (RectTransform)button.transform;
            foreach (Transform child in button.transform.Cast<Transform>().ToArray()) Object.DestroyImmediate(child.gameObject);
            rect.anchoredPosition = new Vector2(-455 + i % 6 * 182, 125 - i / 6 * 165); rect.sizeDelta = new Vector2(168, 152);
            var background = button.GetComponent<Image>(); background.sprite = hud.salePopupBackground.sprite;
            background.type = Image.Type.Sliced; background.color = new Color(.88f, .92f, .82f);
            Picture("Equipment", rect, businessIcons[i], new Vector2(0, 28), new Vector2(76, 64));
            Label(hud.panelText, rect, names[i], new Vector2(0, -25), new Vector2(160, 26), 18);
            Label(hud.panelText, rect, prices[i], new Vector2(0, -54), new Vector2(160, 28), 21);
        }
        for (int i = 0; i < hud.hireButtons.Length; i++)
        {
            var rect = (RectTransform)hud.hireButtons[i].transform;
            rect.anchoredPosition = new Vector2(-411 + i * 274, -187); rect.sizeDelta = new Vector2(262, 58);
        }
        TycoonInventoryDragAuthoring.Build(); TycoonSupplyMenuAuthoring.Build();
        game.navigation.BuildNavMesh();
        EditorUtility.SetDirty(catalog); EditorUtility.SetDirty(game); EditorUtility.SetDirty(hud);
        EditorSceneManager.MarkSceneDirty(scene); EditorSceneManager.SaveScene(scene); AssetDatabase.SaveAssets();
    }
    private static Image Picture(string name, Transform parent, Sprite sprite, Vector2 position, Vector2 size)
    {
        var go = new GameObject(name, typeof(RectTransform), typeof(Image)); go.transform.SetParent(parent, false);
        var image = go.GetComponent<Image>(); image.sprite = sprite; image.preserveAspect = true; image.raycastTarget = false;
        image.rectTransform.anchoredPosition = position; image.rectTransform.sizeDelta = size;
        return image;
    }
    private static void Label(Text template, Transform parent, string value, Vector2 position, Vector2 size, int fontSize)
    {
        var text = Object.Instantiate(template, parent); text.name = value; text.text = value; text.fontSize = fontSize;
        text.rectTransform.anchoredPosition = position; text.rectTransform.sizeDelta = size;
        text.alignment = TextAnchor.MiddleCenter; text.raycastTarget = false;
    }
}
