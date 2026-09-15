using System;
using System.Collections.Generic;
using System.Linq;
using UnityEngine;
using Object = UnityEngine.Object;

// Run in Play Mode against a backed-up campaign. The operator restores the save afterward.
public static class TycoonPlaythroughChecks
{
    public static string Run()
    {
        var g = TycoonGameManager.Instance; var p = g.player; var h = g.hud;
        var passed = new List<string>();
        g.restartRequested = true; p.manualInput = true; g.enabled = false; g.tutorial.enabled = false;
        g.tutorial.progress.step = TycoonTutorial.Step.Complete; g.phase = TycoonGameManager.Phase.Preparation;
        foreach (var w in g.workers) { w.enabled = false; w.ResetTicket(); w.startDay = 999; }
        foreach (var a in g.actors.Where(a => !a.worker).ToArray()) { g.actors.Remove(a); Object.Destroy(a.gameObject); }
        foreach (var site in g.sites) { site.queue.Clear(); site.open = false; }
        h.ClosePanels(); p.inventory = new TycoonInventory(8); p.Select(0);
        var storage = new TycoonInventory(12);
        var serving = new TycoonItem(TycoonItem.Kind.Serving) { scoops = new[] { 0, 1, 2 }, toppings = 3 };
        storage.slots[0] = serving; h.OpenStorage(storage, "Shelf");
        Check(h.BeginInventoryDrag(0, true), "Shelf drag begins"); h.DropInventoryItem(3);
        Check(storage.slots[0] == null && p.inventory.slots[3] == serving, "Shelf to inventory keeps recipe");
        h.BeginInventoryDrag(3); h.DropInventoryItem(2, true);
        Check(storage.slots[2] == serving && (p.inventory.slots[3] == null || p.inventory.slots[3].kind == TycoonItem.Kind.None), "Inventory to shelf");
        h.BeginInventoryDrag(2, true); h.DropInventoryItem(5, true);
        Check(storage.slots[5] == serving && (storage.slots[2] == null || storage.slots[2].kind == TycoonItem.Kind.None), "Shelf rearranging");
        h.BeginInventoryDrag(5, true); h.EndInventoryDrag();
        Check(storage.slots[5] == serving, "Cancel keeps item");
        storage.slots[1] = new TycoonItem(TycoonItem.Kind.Bowls, 8); p.inventory.slots[0] = new TycoonItem(TycoonItem.Kind.Bowls, 10);
        h.BeginInventoryDrag(0); h.DropInventoryItem(1, true);
        Check(storage.slots[1].amount == 12 && p.inventory.slots[0].amount == 6, "Stack merge preserves overflow");
        p.inventory.slots[3] = serving; h.SendMessage("Update");
        Check(h.hotbar[3].scoops.All(i => i.gameObject.activeSelf) && h.hotbar[3].scoops[2].sprite == g.catalog.flavorIcons[2], "Filled hotbar shows all flavors");
        passed.Add("shelf drag both directions, rearrange, cancel, partial merge, three-scoop hotbar");
        h.ClosePanels(); p.inventory = new TycoonInventory(8); p.Select(0);
        p.customerTarget = null; p.looseTarget = null; p.workerTarget = null;
        foreach (var kind in new[] { TycoonPart.Kind.Supplier, TycoonPart.Kind.BusinessBoard, TycoonPart.Kind.Locker, TycoonPart.Kind.Shelf, TycoonPart.Kind.ColdStorage })
        {
            p.target = g.parts.First(t => t.kind == kind && t.installed); h.ClosePanels();
            p.Use(false); Check(!h.AnyPanel, kind + " ignores click");
            p.Use(true); Check(h.AnyPanel, kind + " opens with E");
        }
        h.ClosePanels(); passed.Add("E-only supply, upgrades, lockers and shelves");
        var table = g.parts.First(t => t.site == 0 && t.TableSurface && t.installed);
        var bowl = g.builder.CreateBowl(table, table.contentPoint.position, new TycoonItem(TycoonItem.Kind.Serving));
        var tool = new TycoonItem(TycoonItem.Kind.BasicScooper);
        for (int i = 0; i < 3; i++) { tool.loadedFlavor = i; Check(bowl.Deposit(tool, "Player"), "Deposit scoop " + i); }
        tool.loadedFlavor = 3; Check(!bowl.Deposit(tool, "Player") && tool.loadedFlavor == 3, "Fourth scoop rejected without consuming it");
        Check(bowl.contents.Matches(new TycoonOrder { flavors = new[] { 2, 0, 1 } }), "Three-scoop recipe matching"); bowl.RemoveBowl();
        g.sales = 30; var counts = new HashSet<int>();
        for (int i = 0; i < 1000; i++)
        {
            var order = g.GenerateOrder(0);
            Check(order.flavors.All(f => g.Parts(0, TycoonPart.Kind.Tub).Any(t => t.variant == f)), "Only installed flavors are offered");
            if (!order.cone) counts.Add(order.flavors.Length);
        }
        Check(counts.SetEquals(new[] { 1, 2, 3 }), "One, two and three-scoop bowls generated");
        Check(new TycoonOrder { flavors = new[] { 0 } }.Price(0) == 8, "Bowl base price is $8");
        passed.Add("three-scoop recipes, $8 base, no orders for unpacked flavor holders");
        var tub = g.Parts(0, TycoonPart.Kind.Tub).First(); tub.contents.amount = 24; tub.claimedBy = "";
        var durations = new List<float>(); p.target = tub;
        foreach (var kind in new[] { TycoonItem.Kind.BasicScooper, TycoonItem.Kind.ImprovedScooper, TycoonItem.Kind.ElectricScooper })
        {
            p.inventory.slots[0] = new TycoonItem(kind); p.Select(0); p.Use(false);
            int frames = 0;
            while (p.Scooping && frames < 500) { p.Gesture(new Vector2(0, frames % 2 == 0 ? 90 : -90), .02f); frames++; }
            Check(p.Held.loadedFlavor == tub.variant, kind + " scoops successfully"); durations.Add(frames * .02f);
        }
        Check(durations[0] > durations[1] && durations[1] > durations[2], "Scooper tiers have increasing speed");
        passed.Add("swipe gesture durations: " + string.Join(", ", durations.Select(d => d.ToString("0.00") + "s")));
        foreach (var l in g.looseItems.ToArray()) Object.Destroy(l.gameObject); g.looseItems.Clear();
        p.Teleport(g.supplier.position); g.cash = 1000;
        Check(g.PurchaseSupply(18) && g.cash == 997 && g.looseItems.Count == 1 && g.looseItems[0].item.amount == 12, "One $3 bowl stack");
        Check(g.PurchaseSupply(22) && g.looseItems.Last().item.kind == TycoonItem.Kind.ElectricScooper, "Electric scooper supply purchase");
        float cash = g.cash; Check(!g.BuyUpgrade(0, 0) && !g.BuyUpgrade(3, 0) && g.cash == cash, "Duplicate tool and waffle bundle removed");
        int partCount = g.parts.Count; Check(g.BuyUpgrade(12, 0), "Buy standalone waffle iron");
        var iron = g.parts.Last(); Check(g.parts.Count == partCount + 1 && iron.kind == TycoonPart.Kind.Iron && !iron.installed && iron.support == null, "Only the placeable iron delivered");
        Check(iron.transform.position.z < g.sites[0].origin.position.z - 3, "Equipment delivered behind shop");
        passed.Add("one-stack bowl purchase, electric purchase, standalone iron delivery, no duplicate upgrade sales");
        g.phase = TycoonGameManager.Phase.Trading;
        var far = Customer(g, g.sites[0].queuePoint.position + Vector3.forward * 10);
        var near = Customer(g, g.sites[0].queuePoint.position);
        near.JoinQueue(); Check(near.ReadyToOrder && !far.ReadyToOrder, "Nearby customer takes first available slot");
        Check(g.sites[0].queue.First(c => c.order.joinedQueue) == near, "Arrival determines queue order");
        float patience = far.order.patience; far.TickPatience(10); Check(far.order.patience == patience, "Approaching customer retains patience");
        far.agent.Warp(far.QueuePosition); far.JoinQueue(); Check(!far.ReadyToOrder, "Second arrival waits behind first");
        Check(near.TakeOrder(), "First arrival can order"); far.agent.Warp(far.QueuePosition); Check(far.ReadyToOrder, "Next customer advances immediately");
        near.Leave(); far.Leave(); passed.Add("arrival-based queue, stable ordering, no patience loss en route");
        g.phase = TycoonGameManager.Phase.Preparation; g.day = 2;
        var strawberry = g.parts.First(t => t.site == 0 && t.kind == TycoonPart.Kind.Tub && t.variant == 2);
        var mint = g.parts.First(t => t.site == 0 && t.kind == TycoonPart.Kind.Tub && t.variant == 3);
        g.tutorial.progress.step = TycoonTutorial.Step.InstallRewards; strawberry.installed = true; mint.installed = false;
        g.tutorial.Tick(); Check(g.tutorial.progress.step == TycoonTutorial.Step.InstallRewards, "Both holders required");
        mint.installed = true; strawberry.contents.amount = 24; mint.contents.amount = 0;
        g.tutorial.Tick(); Check(g.tutorial.progress.step == TycoonTutorial.Step.FillRewards, "Placement advances to filling");
        g.tutorial.Tick(); Check(g.tutorial.progress.step == TycoonTutorial.Step.FillRewards, "Both refills required");
        mint.contents.amount = 24; g.tutorial.Tick(); Check(g.tutorial.progress.step == TycoonTutorial.Step.Supplier, "Shopping starts after both fills");
        g.tutorial.progress.step = TycoonTutorial.Step.EquipScooper; p.inventory.slots[0] = new TycoonItem(TycoonItem.Kind.ImprovedScooper); p.Select(0);
        g.tutorial.Tick(); Check(g.tutorial.progress.step == TycoonTutorial.Step.ReopenDay, "Final open-shop guidance");
        var shelf = g.Parts(0, TycoonPart.Kind.Shelf).First(); shelf.storage.slots[0] = new TycoonItem(TycoonItem.Kind.Bowls, 12);
        foreach (var t in g.Parts(0, TycoonPart.Kind.Tub)) t.contents.amount = 24;
        g.OpenDay(); Check(g.sites[0].queue.Count == 1 && g.sites[0].queue[0].AtQueuePosition, "Day-two customer appears at opening");
        g.tutorial.Tick(); Check(!g.tutorial.Active, "Tutorial finishes after opening");
        passed.Add("two holders and refills gate shopping; reopening completes tutorial with immediate customer");
        return "PASS\n" + string.Join("\n", passed);
    }
    private static TycoonActor Customer(TycoonGameManager game, Vector3 point)
    {
        var actor = Object.Instantiate(game.catalog.customerPrefab, point, Quaternion.identity);
        actor.game = game; actor.site = 0; actor.enabled = false;
        actor.order = new TycoonOrder { id = game.nextId++, flavors = new[] { 0 } };
        game.sites[0].queue.Add(actor); game.actors.Add(actor); actor.agent.Warp(point);
        return actor;
    }
    private static void Check(bool condition, string message)
    {
        if (!condition) throw new Exception(message);
    }
}
