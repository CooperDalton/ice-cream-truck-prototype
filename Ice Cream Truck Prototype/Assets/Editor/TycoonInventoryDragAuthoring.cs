using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.UI;

public static class TycoonInventoryDragAuthoring
{
    [MenuItem("Ice Cream/Author inventory dragging")]
    public static void Build()
    {
        var scene = UnityEngine.SceneManagement.SceneManager.GetActiveScene();
        var hud = scene.GetRootGameObjects()[0].GetComponent<TycoonGameManager>().hud;
        Undo.RegisterFullObjectHierarchyUndo(hud.gameObject, "Add inventory dragging");
        foreach (var slots in new[] { hud.inventorySlots, hud.hotbar, hud.playerSlots })
            for (int i = 0; i < slots.Length; i++)
            {
                var slot = slots[i];
                var drag = slot.button.GetComponent<TycoonInventorySlot>();
                if (drag == null) drag = slot.button.gameObject.AddComponent<TycoonInventorySlot>();
                drag.hud = hud; drag.button = slot.button; drag.index = i;
            }
        if (hud.inventoryDragIcon == null)
        {
            var root = new GameObject("Dragged inventory item", typeof(RectTransform), typeof(Image));
            root.transform.SetParent(hud.transform, false);
            hud.inventoryDragIcon = root.GetComponent<Image>();
        }
        var icon = hud.inventoryDragIcon;
        icon.rectTransform.anchorMin = icon.rectTransform.anchorMax = new Vector2(.5f, .5f);
        icon.rectTransform.sizeDelta = new Vector2(64, 64);
        icon.preserveAspect = true; icon.raycastTarget = false;
        icon.color = new Color(1, 1, 1, .9f);
        icon.gameObject.SetActive(false);
        EditorUtility.SetDirty(hud); EditorSceneManager.MarkSceneDirty(scene); EditorSceneManager.SaveScene(scene);
    }
}
