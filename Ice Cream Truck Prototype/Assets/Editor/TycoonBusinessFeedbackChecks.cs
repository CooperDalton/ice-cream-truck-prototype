using System;
using System.Linq;
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.UI;

// Disposable Play Mode fixture: back up the campaign before running, then restore it.
public static class TycoonBusinessFeedbackChecks
{
    public static async System.Threading.Tasks.Task<string> Run()
    {
        var game = TycoonGameManager.Instance; var hud = game.hud;
        game.restartRequested = true; game.enabled = false; game.tutorial.enabled = false;
        game.player.manualInput = true; game.level = 7; game.cash = 5000;
        game.phase = TycoonGameManager.Phase.Preparation;
        game.sites[0].owned = true; game.sites[0].expanded = false; game.sites[2].owned = false;
        foreach (var existingWorker in game.workers) UnityEngine.Object.Destroy(existingWorker.gameObject);
        game.workers.Clear();
        foreach (var part in game.parts.Where(p => p.site == 0 && p.kind == TycoonPart.Kind.Locker)) part.installed = false;
        hud.OpenBusiness(0);
        await System.Threading.Tasks.Task.Delay(150);

        Click(hud.hireButtons[0]);
        Check(game.workers.Count == 0 && game.cash == 5000, "Hiring without a placed locker does not charge");
        Message(hud, "Buy and place a staff locker first.");
        Click(hud.upgradeButtons[7]);
        Check(!game.sites[2].owned && game.cash == 5000, "Truck prerequisites do not charge");
        Message(hud, "Expand the home kiosk and hire an employee first.");
        Click(hud.hireButtons[3]);
        Message(hud, "Buy the truck before hiring a driver.");

        Click(hud.upgradeButtons[1]);
        var locker = game.parts.Last(p => p.site == 0 && p.kind == TycoonPart.Kind.Locker);
        Check(!locker.installed && game.cash == 4976, "Purchased locker is delivered for placement");
        Message(hud, "4-slot locker delivered behind the shop.");
        Click(hud.hireButtons[0]);
        Check(game.workers.Count == 0 && game.cash == 4976, "Unplaced locker does not permit hiring");
        Message(hud, "Buy and place a staff locker first.");
        locker.transform.position = game.sites[0].origin.position + new Vector3(-2, 0, 0);
        locker.installed = true;
        Click(hud.hireButtons[0]);
        Check(game.workers.Count == 1 && game.workers[0].locker == locker && game.cash == 4916, "Hiring succeeds with a placed locker and charges once");
        Message(hud, "Employee hired.");
        Click(hud.upgradeButtons[7]);
        Check(!game.sites[2].owned && game.cash == 4916, "Truck still requires expansion");
        Message(hud, "Expand the home kiosk and hire an employee first.");
        Click(hud.upgradeButtons[5]);
        Check(game.sites[0].expanded && game.cash == 4756, "Home expansion succeeds");
        Click(hud.upgradeButtons[7]);
        Check(game.sites[2].owned && game.truck.gameObject.activeSelf && game.cash == 4156, "Truck purchase activates the truck and charges once");
        Message(hud, "Truck purchased.");
        Click(hud.upgradeButtons[7]);
        Check(game.cash == 4156, "Duplicate truck purchase does not charge");
        Message(hud, "You already own the truck.");
        var existingLockers = game.parts.Where(p => p.kind == TycoonPart.Kind.Locker).Select(p => new { part = p, slots = p.storage.slots.Length }).ToArray();
        for (int choice = 1; choice <= 3; choice++)
        {
            int count = game.parts.Count; float cash = game.cash;
            Click(hud.upgradeButtons[choice]);
            var purchased = game.parts.Last(); int capacity = choice * 4;
            Check(game.parts.Count == count + 1 && purchased.storage.slots.Length == capacity && !purchased.installed, "Each locker purchase delivers a separate " + capacity + "-slot locker");
            Check(game.cash == cash - new[] { 24, 48, 88 }[choice - 1], "Correct locker price");
            Check(existingLockers.All(p => p.part.storage.slots.Length == p.slots), "Purchases never upgrade existing lockers");
            purchased.RefreshLocker();
            Check(purchased.lockerModels.Count(m => m.activeSelf) == 1 && purchased.lockerModels[choice - 1].activeSelf, "Correct locker model");
            Check(game.catalog.placementPreviews[purchased.catalogIndex].GetComponent<MeshFilter>().sharedMesh.vertexCount > 0, "Locker has a placement preview");
            Check(game.catalog.Label(new TycoonItem(TycoonItem.Kind.Equipment, 1, purchased.catalogIndex)).Contains(capacity + "-slot"), "Packed locker label identifies capacity");
        }
        Check(!hud.upgradeButtons[10].gameObject.activeSelf, "Cold storage removed from shop");
        Click(hud.upgradeButtons[13]);
        var shelf = game.parts.Last(); shelf.installed = true;
        Check(shelf.kind == TycoonPart.Kind.Shelf && shelf.storage.slots.Length == 12, "Shelf supplies twelve slots");
        shelf.transform.position = game.sites[0].origin.position + new Vector3(2, 0, -1);
        game.navigation.BuildNavMesh();
        var worker = game.workers[0]; worker.enabled = false;
        var customer = UnityEngine.Object.Instantiate(game.catalog.customerPrefab, game.sites[0].queuePoint.position, Quaternion.identity);
        customer.game = game; customer.site = 0; customer.enabled = false;
        customer.order = new TycoonOrder { id = game.nextId++, flavors = new[] { 0 } };
        game.sites[0].queue.Add(customer); game.actors.Add(customer); worker.ticketId = customer.order.id;
        worker.target = game.parts.First(p => p.site == 0 && p.kind == TycoonPart.Kind.Tub);
        worker.target.contents.amount = 18;
        worker.target.operatingPoint.position = shelf.operatingPoint.position;
        foreach (var other in game.Parts(0, TycoonPart.Kind.Shelf)) other.storage = new TycoonInventory(12);
        shelf.storage.slots[0] = new TycoonItem(TycoonItem.Kind.Tub, 12, worker.target.variant);
        worker.inventory = new TycoonInventory(8); worker.neededSupply = TycoonItem.Kind.Tub;
        worker.neededVariant = worker.target.variant; worker.resumeStep = TycoonWorker.Step.Refill; worker.step = TycoonWorker.Step.Restock;
        Check(worker.actor.agent.Warp(shelf.operatingPoint.position), "Shelf access point is walkable"); worker.actor.agent.ResetPath();
        worker.Tick(0);
        Check(worker.step == TycoonWorker.Step.Refill && shelf.storage.slots[0] == null && worker.inventory.slots[0].amount == 12, "Worker collects spare tub from shelf");
        worker.Tick(1);
        Check(worker.step == TycoonWorker.Step.ReturnRefill && worker.target.contents.amount == 24 && worker.inventory.slots[0].amount == 6, "Worker refills holder without losing leftover stock");
        foreach (var other in game.Parts(0, TycoonPart.Kind.Shelf).Where(p => p != shelf)) other.installed = false;
        worker.Tick(1);
        Check(worker.step == TycoonWorker.Step.GoTub && shelf.storage.slots[0].amount == 6 && worker.inventory.slots[0] == null, "Worker returns leftover tub to shelf");
        return "PASS: business feedback; hiring and truck requirements; three separate locker purchases, prices, models, previews and labels; shelf refill collection and leftover return.";
    }

    private static void Click(Button button)
    {
        Canvas.ForceUpdateCanvases();
        var point = RectTransformUtility.WorldToScreenPoint(null, button.transform.TransformPoint(((RectTransform)button.transform).rect.center));
        var pointer = new PointerEventData(EventSystem.current) { position = point, button = PointerEventData.InputButton.Left };
        var hits = new System.Collections.Generic.List<RaycastResult>();
        EventSystem.current.RaycastAll(pointer, hits);
        Check(hits.Count > 0 && hits[0].gameObject.GetComponentInParent<Button>() == button, "UI ray reaches " + button.name);
        ExecuteEvents.Execute(button.gameObject, pointer, ExecuteEvents.pointerClickHandler);
    }

    private static void Message(TycoonHUD hud, string expected)
    {
        for (int i = 0; i < 3; i++) hud.SendMessage("Update");
        Check(hud.panelText.gameObject.activeInHierarchy && hud.panelText.text.Contains(expected), "Feedback survives HUD updates: " + expected);
    }

    private static void Check(bool value, string message)
    {
        if (!value) throw new InvalidOperationException(message);
    }
}
