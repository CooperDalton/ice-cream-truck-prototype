using System;
using System.Linq;
using UnityEngine;
using Object = UnityEngine.Object;

// Disposable Play Mode fixture: back up the campaign before running, then restore it.
public static class TycoonEmployeeFeedbackChecks
{
    public static string Run()
    {
        var g = TycoonGameManager.Instance; var h = g.hud; var p = g.player;
        g.restartRequested = true; g.enabled = false; g.tutorial.enabled = false;
        g.tutorial.progress.step = TycoonTutorial.Step.Complete; g.phase = TycoonGameManager.Phase.Trading;
        h.ClosePanels(); h.menuOpen = false; p.manualInput = true;
        foreach (var worker in g.workers) { worker.enabled = false; worker.ResetTicket(); }
        foreach (var actor in g.actors.Where(a => !a.worker).ToArray()) { g.actors.Remove(actor); Object.Destroy(actor.gameObject); }
        foreach (var site in g.sites) site.queue.Clear();
        var w = g.workers.First(); w.onDuty = true; w.locker.storage = new TycoonInventory(8);
        w.inventory = new TycoonInventory(8); p.inventory = new TycoonInventory(8);
        var c = Object.Instantiate(g.catalog.customerPrefab, g.sites[0].pickupQueuePoint.position, Quaternion.identity);
        c.game = g; c.site = 0; c.enabled = false;
        c.order = new TycoonOrder { id = g.nextId++, flavors = new[] { 0 }, toppings = 1, stage = TycoonOrder.Stage.Pickup, joinedQueue = true, owner = w.Owner };
        g.sites[0].queue.Add(c); g.actors.Add(c);
        w.ticketId = c.order.id; w.site = 0; w.scoopIndex = 0; w.toppingIndex = 0;
        w.prep = g.builder.ReserveBowl(0); w.prep.contents = new TycoonItem(TycoonItem.Kind.Serving); w.prep.Claim(w.Owner);
        w.step = TycoonWorker.Step.GoTub; w.Tick(0);
        Check(w.Blocked && w.status.Contains("scooper") && w.step == TycoonWorker.Step.Restock, "Missing scooper explains how to resume");
        h.OpenEmployee(w); h.SendMessage("Update");
        Check(h.employeeStorageView.slots.All(s => s.button.interactable) && h.employeeDetails.text.Contains(w.status), "Live inventory enabled and reason displayed");
        var loaded = new TycoonItem(TycoonItem.Kind.ImprovedScooper) { loadedFlavor = 0 };
        p.inventory.slots[0] = loaded;
        h.BeginInventoryDrag(0); h.DropInventoryItem(0, true); w.Tick(0);
        Check(w.step == TycoonWorker.Step.Deposit, "New loaded scooper resumes existing order");
        h.BeginInventoryDrag(0, true); h.DropInventoryItem(0);
        Check(p.inventory.slots[0] == loaded && loaded.loadedFlavor == 0 && w.prep.contents.scoops.Length == 0 && w.step == TycoonWorker.Step.Restock, "Removing loaded scooper preserves transferred scoop and pauses deposit");
        var electric = new TycoonItem(TycoonItem.Kind.ElectricScooper) { loadedFlavor = 0 };
        p.inventory.slots[1] = electric; h.BeginInventoryDrag(1); h.DropInventoryItem(1, true); w.Tick(0);
        Stand(w, w.prep.operatingPoint.position); w.Tick(1);
        Check(w.prep.contents.scoops.SequenceEqual(new[] { 0 }) && electric.loadedFlavor == -1, "Replacement electric scooper deposits exactly once");
        w.Tick(0); Check(w.Blocked && w.status.Contains("Need"), "Missing topping explains requirement");
        var topping = new TycoonItem(TycoonItem.Kind.Topping, 1, 0);
        p.inventory.slots[2] = topping; h.BeginInventoryDrag(2); h.DropInventoryItem(2, true);
        Stand(w, w.prep.operatingPoint.position); w.Tick(.1f);
        Check(topping.amount == 0 && w.prep.contents.pendingTopping == 0, "Topping starts and charges once");
        h.BeginInventoryDrag(2, true); h.DropInventoryItem(2);
        Check(w.step == TycoonWorker.Step.Restock && w.prep.contents.pendingTopping == 0, "Removing topping interrupts animation without losing applied ingredient");
        h.BeginInventoryDrag(2); h.DropInventoryItem(3, true);
        Stand(w, w.prep.operatingPoint.position); w.Tick(2);
        Check(w.prep.contents.toppings == 1 && topping.amount == 0, "Returning empty bottle finishes already-paid topping without charging twice");
        w.Tick(0); w.Tick(1);
        Check(w.step == TycoonWorker.Step.Serve && w.carrying.Matches(c.order), "Interrupted order completes with exact recipe");
        var counter = g.Parts(0, TycoonPart.Kind.ServingCounter).First();
        Stand(w, counter.operatingPoint.position); c.agent.Warp(c.QueuePosition); c.agent.ResetPath();
        int sales = g.sales; w.Tick(1);
        Check(g.sales == sales + 1 && w.step == TycoonWorker.Step.Idle, "Completed order is sold and employee becomes available");
        var stale = new TycoonItem(TycoonItem.Kind.Batter, 4); w.inventory.slots[5] = stale;
        h.BeginInventoryDrag(5, true); var replacement = new TycoonItem(TycoonItem.Kind.Bowls, 7); w.inventory.slots[5] = replacement;
        h.DropInventoryItem(5);
        Check(w.inventory.slots[5] == replacement && (p.inventory.slots[5] == null || p.inventory.slots[5].kind == TycoonItem.Kind.None), "Drag never transfers an item that replaced its source");
        c = Object.Instantiate(g.catalog.customerPrefab, g.sites[0].pickupQueuePoint.position, Quaternion.identity);
        c.game = g; c.site = 0; c.enabled = false;
        c.order = new TycoonOrder { id = g.nextId++, flavors = new[] { 6 }, owner = w.Owner };
        g.sites[0].queue.Add(c); g.actors.Add(c); w.ticketId = c.order.id; w.scoopIndex = 0;
        w.prep = g.builder.ReserveBowl(0); w.prep.contents = new TycoonItem(TycoonItem.Kind.Serving); w.prep.Claim(w.Owner);
        w.step = TycoonWorker.Step.GoTub; w.Tick(0);
        Check(w.Blocked && w.status.Contains("Coffee") && w.status.Contains("holder"), "Unplaced Coffee holder explains original blockage");
        h.SendMessage("Update");
        Check(h.employeeDetails.text.Contains("Coffee") && h.employeeDetails.text.Contains("size=21"), "Missing equipment reason is prominent in employee panel");
        w.inventory = new TycoonInventory(8); w.inventory.slots = Enumerable.Range(0, 8).Select(i => new TycoonItem(TycoonItem.Kind.Batter, 10)).ToArray();
        w.locker.storage.slots[0] = new TycoonItem(TycoonItem.Kind.ElectricScooper);
        w.Tick(0); Check(w.Blocked && w.status.Contains("Inventory full"), "Full inventory explains why locker collection cannot proceed");
        w.inventory.slots[0] = null; Stand(w, w.locker.operatingPoint.position); w.Tick(0);
        Check(w.inventory.slots.Any(i => i != null && i.Tool) && w.step == TycoonWorker.Step.GoTub, "Freeing a slot lets employee collect replacement tool");
        var retained = w.prep.contents; c.Leave(); w.Tick(0);
        Check(w.step == TycoonWorker.Step.Idle && w.ticketId == -1 && w.prep.contents == retained && w.prep.claimedBy == "", "Cancelled customer releases work and preserves serving");
        c = Object.Instantiate(g.catalog.customerPrefab, g.sites[0].pickupQueuePoint.position, Quaternion.identity);
        c.game = g; c.site = 0; c.enabled = false;
        c.order = new TycoonOrder { id = g.nextId++, flavors = new[] { 0 }, cone = true, owner = w.Owner };
        g.sites[0].queue.Add(c); g.actors.Add(c); w.ticketId = c.order.id;
        w.inventory = new TycoonInventory(8); w.locker.storage = new TycoonInventory(8);
        w.iron = g.parts.First(part => part.site == 0 && part.kind == TycoonPart.Kind.Iron);
        w.iron.operatingPoint.position = w.locker.operatingPoint.position; w.iron.ironStage = 0; w.iron.claimedBy = w.Owner;
        var batter = new TycoonItem(TycoonItem.Kind.Batter, 1); w.inventory.slots[0] = batter;
        w.step = TycoonWorker.Step.Pour; w.progress = 0; Stand(w, w.iron.operatingPoint.position); w.Tick(.1f);
        Check(batter.amount == 0 && w.iron.ironStage == 5, "Batter is charged when pouring starts");
        h.OpenEmployee(w); h.BeginInventoryDrag(0, true); h.DropInventoryItem(6);
        Check(w.step == TycoonWorker.Step.Restock && w.Blocked, "Removing batter interrupts pouring");
        h.BeginInventoryDrag(6); h.DropInventoryItem(0, true);
        var standingPoint = w.iron.operatingPoint.position;
        w.iron.operatingPoint.position = new Vector3(10000, 0, 10000); w.Tick(0); w.Tick(3);
        Check(w.Blocked && w.status.Contains("blocked"), "Unreachable work point explains blocked path");
        w.iron.operatingPoint.position = standingPoint; Stand(w, standingPoint); w.Tick(2);
        Check(w.step == TycoonWorker.Step.Close && w.iron.ironStage == 1 && batter.amount == 0, "Pour resumes after path and bottle are restored without charging twice");
        h.ClosePanels();
        return "PASS: live slot controls; missing supply reason; loaded scooper removal; replacement electric scooper; topping interruption with no duplicate consumption; exact recipe sold; stale drag rejected; Coffee holder reason; full inventory; locker replacement; order cancellation; batter interruption; blocked path recovery.";
    }
    private static void Stand(TycoonWorker worker, Vector3 point)
    {
        Check(worker.actor.agent.Warp(point), "Fixture destination is walkable"); worker.actor.agent.ResetPath();
    }
    private static void Check(bool value, string message)
    {
        if (!value) throw new InvalidOperationException(message);
    }
}
