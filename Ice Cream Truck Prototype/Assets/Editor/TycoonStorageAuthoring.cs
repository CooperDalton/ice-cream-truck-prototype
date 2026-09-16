using System;
using System.Linq;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.UI;
using Object = UnityEngine.Object;

public static class TycoonStorageAuthoring
{
    [MenuItem("Ice Cream/Author separate lockers and shelves")]
    public static void Build()
    {
        if (EditorApplication.isPlaying) throw new InvalidOperationException("Stop Play Mode before authoring storage.");
        var scene = UnityEngine.SceneManagement.SceneManager.GetActiveScene();
        var game = scene.GetRootGameObjects()[0].GetComponent<TycoonGameManager>();
        var catalog = game.catalog; var hud = game.hud;
        Array.Resize(ref catalog.partPrefabs, 16);
        Array.Resize(ref catalog.equipmentIcons, 16);
        Array.Resize(ref catalog.placementPreviews, 16);
        for (int i = 14; i <= 15; i++)
        {
            var root = PrefabUtility.LoadPrefabContents(AssetDatabase.GetAssetPath(catalog.partPrefabs[4]));
            try
            {
                var part = root.GetComponent<TycoonPart>(); part.catalogIndex = i;
                part.storage = new TycoonInventory(i == 14 ? 8 : 12); part.RefreshLocker();
                root.name = part.storage.slots.Length + "-slot locker";
                catalog.partPrefabs[i] = PrefabUtility.SaveAsPrefabAsset(root, "Assets/Art/Tycoon/Prefabs/Part_" + i + ".prefab").GetComponent<TycoonPart>();
                catalog.equipmentIcons[i] = TycoonPictureAuthoring.Render(root, "Locker" + part.storage.slots.Length);
                var pieces = root.GetComponentsInChildren<MeshFilter>().SelectMany(f => Enumerable.Range(0, f.sharedMesh.subMeshCount).Select(sub => new CombineInstance
                    { mesh = f.sharedMesh, subMeshIndex = sub, transform = root.transform.worldToLocalMatrix * f.transform.localToWorldMatrix })).ToArray();
                string meshPath = "Assets/Art/Tycoon/Placement/Mesh_" + i + ".asset";
                var mesh = AssetDatabase.LoadAssetAtPath<Mesh>(meshPath);
                if (mesh == null) { mesh = new Mesh(); AssetDatabase.CreateAsset(mesh, meshPath); }
                mesh.Clear(); mesh.indexFormat = UnityEngine.Rendering.IndexFormat.UInt32;
                mesh.CombineMeshes(pieces); mesh.RecalculateBounds(); EditorUtility.SetDirty(mesh);
                var preview = new GameObject(root.name + " preview"); preview.layer = 2;
                preview.AddComponent<MeshFilter>().sharedMesh = mesh;
                var renderer = preview.AddComponent<MeshRenderer>(); renderer.sharedMaterial = game.builder.validMaterial;
                renderer.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off; renderer.receiveShadows = false;
                catalog.placementPreviews[i] = PrefabUtility.SaveAsPrefabAsset(preview, "Assets/Art/Tycoon/Placement/Preview_" + i + ".prefab");
                Object.DestroyImmediate(preview);
            }
            finally { PrefabUtility.UnloadPrefabContents(root); }
        }

        foreach (var old in game.parts.Where(p => (int)p.kind == 5).ToArray())
        {
            var root = (GameObject)PrefabUtility.InstantiatePrefab(catalog.partPrefabs[8].gameObject);
            root.transform.SetParent(old.transform.parent, false);
            root.transform.SetPositionAndRotation(old.transform.position, old.transform.rotation);
            var shelf = root.GetComponent<TycoonPart>(); shelf.game = game; shelf.site = old.site; shelf.id = old.id;
            shelf.installed = old.installed; shelf.packed = old.packed; shelf.storage = old.storage;
            Array.Resize(ref shelf.storage.slots, TycoonPart.ShelfCapacity);
            game.parts[game.parts.IndexOf(old)] = shelf;
            PrefabUtility.RecordPrefabInstancePropertyModifications(shelf);
            PrefabUtility.RecordPrefabInstancePropertyModifications(shelf.transform);
            Object.DestroyImmediate(old.gameObject);
        }
        catalog.partPrefabs[5] = catalog.partPrefabs[8];
        catalog.equipmentIcons[5] = catalog.equipmentIcons[8];
        catalog.placementPreviews[5] = catalog.placementPreviews[8];
        foreach (var locker in game.parts.Where(p => p.kind == TycoonPart.Kind.Locker && p.storage.slots.Length > 4))
        {
            locker.catalogIndex = locker.storage.slots.Length == 8 ? 14 : 15;
            PrefabUtility.RecordPrefabInstancePropertyModifications(locker);
        }

        Object.DestroyImmediate(hud.upgradeButtons[3].gameObject);
        hud.upgradeButtons[3] = Object.Instantiate(hud.upgradeButtons[1], hud.businessPanel.transform);
        hud.upgradeButtons[3].onClick = new Button.ButtonClickedEvent();
        int[] active = { 1, 2, 3, 4, 5, 6, 7, 8, 9, 11, 12, 13 };
        string[] names = { "4-slot locker", "8-slot locker", "12-slot locker", "Bike cargo", "Expand shop · 4 rows", "Park stand", "Ice cream truck", "Table", "Cone holder", "Tub holder", "Waffle iron", "Shelf · 12 slots" };
        string[] prices = { "$24", "$48", "$88", "$48", "$160", "$250", "$600", "$24", "$12", "$18", "$48", "$20" };
        hud.upgradeButtons[0].gameObject.SetActive(false); hud.upgradeButtons[10].gameObject.SetActive(false);
        for (int i = 0; i < active.Length; i++)
        {
            var button = hud.upgradeButtons[active[i]]; button.name = names[i]; button.gameObject.SetActive(true);
            var rect = (RectTransform)button.transform; rect.anchoredPosition = new Vector2(-455 + i % 6 * 182, 125 - i / 6 * 165);
            var labels = button.GetComponentsInChildren<Text>(); labels[0].text = names[i]; labels[1].text = prices[i];
            if (i < 3) button.transform.GetChild(0).GetComponent<Image>().sprite = catalog.equipmentIcons[new[] { 4, 14, 15 }[i]];
        }
        game.navigation.BuildNavMesh(); EditorUtility.SetDirty(catalog); EditorUtility.SetDirty(game); EditorUtility.SetDirty(hud);
        AssetDatabase.SaveAssets(); EditorSceneManager.MarkSceneDirty(scene); EditorSceneManager.SaveScene(scene);
    }
}
