using System;
using System.Collections.Generic;
using System.Linq;
using UnityEngine;
using UnityEngine.EventSystems;

public static class TycoonShelfUIPlaytest
{
    public static string[] Run()
    {
        var game = TycoonGameManager.Instance;
        var hud = game.hud;
        var player = game.player;
        var shelf = game.Parts(0, TycoonPart.Kind.Shelf).First();
        var inventory = player.inventory; int selected = player.selected;
        var storage = shelf.storage; var target = player.target; var loose = player.looseTarget; var worker = player.workerTarget;
        var evidence = new List<string>();
        try
        {
            if (storage.slots.Length != 12) throw new Exception("Loaded shelf did not have 12 slots");
            player.inventory = new TycoonInventory(8);
            shelf.storage = new TycoonInventory(12);
            player.inventory.slots[0] = new TycoonItem(TycoonItem.Kind.BasicScooper);
            player.Select(0); player.target = shelf; player.looseTarget = null; player.workerTarget = null;
            player.Use(false);
            Refresh(hud);
            if (!hud.shelfPanel.activeSelf || hud.panel.activeSelf || hud.inventoryPanel.activeSelf || !hud.AnyPanel)
                throw new Exception("Shelf did not open its dedicated overlay");
            var pointer = new PointerEventData(EventSystem.current) { position = RectTransformUtility.WorldToScreenPoint(null, hud.hotbar[0].frame.rectTransform.position) };
            var hits = new List<RaycastResult>(); EventSystem.current.RaycastAll(pointer, hits);
            if (hits.Count == 0 || hits[0].gameObject != hud.hotbar[0].button.gameObject)
                throw new Exception("Shelf overlay blocked hotbar clicks");
            hud.hotbar[0].button.onClick.Invoke(); Refresh(hud);
            if (player.inventory.slots[0] != null || shelf.storage.slots[0].kind != TycoonItem.Kind.BasicScooper || !hud.shelfSlots[0].icon.gameObject.activeSelf)
                throw new Exception("Hotbar click did not store and display the item");
            hud.shelfSlots[0].button.onClick.Invoke(); Refresh(hud);
            if (shelf.storage.slots[0] != null || player.inventory.slots[0].kind != TycoonItem.Kind.BasicScooper)
                throw new Exception("Shelf click did not return the item");
            evidence.Add("Shelf opens above a raycast-accessible hotbar; clicking stores an item and clicking its shelf slot takes it back.");
            for (int i = 0; i < 12; i++) shelf.storage.slots[i] = new TycoonItem(TycoonItem.Kind.BasicScooper);
            Refresh(hud);
            if (hud.shelfSlots.Any(s => !s.icon.gameObject.activeSelf)) throw new Exception("Full 12-slot shelf did not display all items");
            hud.hotbar[0].button.onClick.Invoke();
            if (player.inventory.slots[0] == null || shelf.storage.slots.Any(i => i == null)) throw new Exception("Full shelf lost an item");
            for (int i = 0; i < 8; i++) player.inventory.slots[i] = new TycoonItem(TycoonItem.Kind.BasicScooper);
            hud.shelfSlots[0].button.onClick.Invoke();
            if (shelf.storage.slots[0] == null || player.inventory.slots.Any(i => i == null)) throw new Exception("Full hotbar lost a shelf item");
            evidence.Add("All 12 slots render; transfers into a full shelf or hotbar preserve every item.");
            shelf.storage.slots[0] = new TycoonItem(TycoonItem.Kind.Bowls, 10);
            player.inventory.slots[0] = new TycoonItem(TycoonItem.Kind.Bowls, 5);
            hud.hotbar[0].button.onClick.Invoke(); Refresh(hud);
            if (shelf.storage.slots[0].amount != 12 || player.inventory.slots[0].amount != 3 || hud.shelfSlots[0].label.text != "12")
                throw new Exception("Partial stack transfer lost items or displayed the wrong quantity");
            shelf.storage.slots[11] = null;
            hud.hotbar[0].button.onClick.Invoke();
            if (player.inventory.slots[0] != null || shelf.storage.slots[11].amount != 3) throw new Exception("The twelfth slot cannot receive items");
            evidence.Add("Stacking conserves quantities: 10 + 5 becomes 12 + 3; the remaining 3 can move into slot 12.");
            hud.shelfCloseButton.onClick.Invoke(); Refresh(hud);
            if (hud.AnyPanel) throw new Exception("Close did not dismiss shelf");
            hud.hotbar[2].button.onClick.Invoke();
            if (player.selected != 2) throw new Exception("Closing shelf did not restore hotbar selection");
            evidence.Add("Closing the shelf restores normal hotbar selection.");
            if (hud.tickets.Any(c => c.coin.sprite == null || c.title.text.Contains("$") || c.description.gameObject.activeSelf)) throw new Exception("Order cards still show redundant text or lack coin prices");
            return evidence.ToArray();
        }
        finally
        {
            hud.ClosePanels(); player.inventory = inventory; shelf.storage = storage;
            player.Select(selected); player.target = target; player.looseTarget = loose; player.workerTarget = worker;
        }
    }
    private static void Refresh(TycoonHUD hud)
    {
        typeof(TycoonHUD).GetMethod("Update", System.Reflection.BindingFlags.Instance | System.Reflection.BindingFlags.NonPublic).Invoke(hud, null);
        Canvas.ForceUpdateCanvases();
    }
}
