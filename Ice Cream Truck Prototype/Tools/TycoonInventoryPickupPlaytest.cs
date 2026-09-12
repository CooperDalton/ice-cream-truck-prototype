using System;
using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using UnityEngine;

public static class TycoonInventoryPickupPlaytest
{
    public static string[] Run()
    {
        var g = TycoonGameManager.Instance;
        var p = g.player;
        var h = g.hud;
        var evidence = new List<string>();
        g.restartRequested = true; p.manualInput = true;
        h.menuOpen = false; h.ClosePanels(); g.phase = TycoonGameManager.Phase.Trading;
        foreach (var s in g.sites) s.open = false;
        foreach (var w in g.workers) w.onDuty = false;
        p.customerTarget = null; p.workerTarget = null; p.looseTarget = null;
        p.inventory = new TycoonInventory(8);
        p.inventory.slots[0] = new TycoonItem(TycoonItem.Kind.BasicScooper);
        p.Select(0); h.ToggleInventory();
        Check(h.personalInventoryPanel.activeSelf && !h.inventoryPanel.activeSelf && h.inventorySlots.Length == 8, "Dedicated inventory layout");
        h.inventorySlots[0].button.onClick.Invoke();
        h.inventorySlots[7].button.onClick.Invoke();
        Check(p.selected == 7 && p.inventory.slots[0] == null && p.Held.Tool, "Inventory move selects destination");
        h.inventoryCloseButton.onClick.Invoke(); Check(!h.AnyPanel, "Inventory close");
        evidence.Add("Inventory opens its compact eight-slot panel; clicking item then slot moves it and selects the destination; Close dismisses it.");
        var prep = g.Parts(0, TycoonPart.Kind.Prep).First();
        prep.claimedBy = ""; prep.contents = new TycoonItem(TycoonItem.Kind.Serving) { scoops = new[] { 0 } };
        p.target = prep; p.Use(true);
        Check(p.selected == 0 && p.Held.kind == TycoonItem.Kind.Serving && prep.contents == null, "Prepared bowl pickup selects receiving slot");
        p.inventory.slots[3] = new TycoonItem(TycoonItem.Kind.Bowls, 10);
        Check(p.PickUp(new TycoonItem(TycoonItem.Kind.Bowls, 2)) && p.selected == 3 && p.Held.amount == 12, "Merged pickup selects stack");
        for (int i = 0; i < 8; i++) p.inventory.slots[i] = new TycoonItem(TycoonItem.Kind.BasicScooper);
        p.Select(5);
        Check(!p.PickUp(new TycoonItem(TycoonItem.Kind.Serving)) && p.selected == 5, "Failed pickup retains selection");
        p.inventory.slots[2] = new TycoonItem(TycoonItem.Kind.Bowls, 10);
        var bowls = new TycoonItem(TycoonItem.Kind.Bowls, 5);
        Check(!p.PickUp(bowls) && bowls.amount == 3 && p.selected == 2 && p.Held.amount == 12, "Partial pickup conserves and selects");
        evidence.Add("E on a prepared bowl selects its new slot; stack pickups select their receiving stack; full inventory preserves selection and partial transfers conserve quantities.");
        p.inventory = new TycoonInventory(8); p.Select(7);
        var shelf = g.Parts(0, TycoonPart.Kind.Shelf).First();
        shelf.storage.slots[0] = new TycoonItem(TycoonItem.Kind.Bowls, 3);
        h.OpenStorage(shelf.storage, "Shelf", true); h.shelfSlots[0].button.onClick.Invoke();
        Check(p.selected == 0 && p.Held.amount == 3 && shelf.storage.slots[0] == null, "Shelf pickup selects slot");
        h.ClosePanels(); evidence.Add("Clicking a shelf item retrieves it and immediately selects it.");
        var fixtures = g.parts.Where(x => x.site == 0 && x.installed && !x.tabletop && x.kind != TycoonPart.Kind.Plot && x.kind != TycoonPart.Kind.Supplier && x.kind != TycoonPart.Kind.Truck && x.kind != TycoonPart.Kind.Bike).ToArray();
        foreach (var part in fixtures)
        {
            p.inventory = new TycoonInventory(8); p.Select(7);
            var children = g.parts.Where(x => x != part && x.transform.IsChildOf(part.transform)).ToArray();
            var position = part.transform.position; var rotation = part.transform.rotation; var support = part.support;
            foreach (var child in children) child.claimedBy = "";
            part.claimedBy = "";
            Check(g.builder.CanPack(part, out var why), part.kind + " packable: " + why);
            g.builder.HoldPickup(part, false, 0); g.builder.HoldPickup(part, true, 1.1f);
            Check(part.packed && p.selected == 0 && p.Held.equipmentId == part.id && children.All(x => !x.installed), part.kind + " pack");
            Check(g.builder.CanPlace(part, position, rotation, support, out why), part.kind + " placement: " + why);
            Set(g.builder, "selected", part); Set(g.builder, "support", support); Set(g.builder, "proposed", position); Set(g.builder, "rotation", rotation); Set(g.builder, "valid", true);
            g.builder.PlaceHeld();
            Check(!part.packed && part.installed && children.All(x => x.installed && x.transform.IsChildOf(part.transform)) && p.Held == null, part.kind + " placement preserves children");
            evidence.Add(part.kind + " packs into the selected hotbar slot and places with " + children.Length + " attached equipment pieces preserved.");
        }
        var register = g.Parts(0, TycoonPart.Kind.Register).Single();
        var queueBefore = g.sites[0].queuePoint.position;
        var destination = register.transform.position + Vector3.left * .5f;
        Check(g.builder.CanPlace(register, destination, register.transform.rotation, null, out var placementReason), "Moved counter fits: " + placementReason);
        register.transform.position = destination;
        Check(g.sites[0].queuePoint == register.queuePoint && Vector3.Distance(g.sites[0].queuePoint.position, queueBefore + Vector3.left * .5f) < .001f, "Queue follows moved counter");
        g.Save();
        System.IO.File.WriteAllText("/tmp/tycoon-inventory-test-register.txt", register.id + ":" + register.transform.position.x);
        h.menuOpen = true;
        evidence.Add("Customer queue point follows the moved order counter; changed fixture state saved for reload verification.");
        return evidence.ToArray();
    }
    private static void Check(bool result, string message)
    {
        if (!result) throw new Exception(message);
    }
    private static void Set(object target, string name, object value)
    {
        target.GetType().GetField(name, BindingFlags.NonPublic | BindingFlags.Instance).SetValue(target, value);
    }
}
