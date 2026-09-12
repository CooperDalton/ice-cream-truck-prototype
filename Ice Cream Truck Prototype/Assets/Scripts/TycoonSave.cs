using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using UnityEngine;
using Object = UnityEngine.Object;

public static class TycoonSave
{
    [Serializable] private class Data
    {
        public float cash, xp, clock, salesToday, wagesToday;
        public int day, level, sales, nextId, phase;
        public bool completed, truckOperating, routeComplete;
        public int[] truckDemand;
        public int travelStage;
        public string results;
        public Vector3 playerPosition, bikePosition, truckPosition;
        public Quaternion bikeRotation, truckRotation;
        public Quaternion playerRotation;
        public float playerPitch;
        public int selected, truckStop;
        public TycoonInventory player, bike, truck;
        public SiteData[] sites;
        public PartData[] parts;
        public WorkerData[] workers;
        public CustomerData[] customers;
        public LooseData[] loose;
    }
    [Serializable] private class SiteData { public bool owned, open, expanded; public Vector2 size; public float revenue, spawn; public int lost, demand; }
    [Serializable] private class PartData
    {
        public int id, prefab, site, variant, support, ironStage;
        public bool installed, packed;
        public Vector3 position; public Quaternion rotation;
        public TycoonInventory storage; public TycoonItem contents; public string owner; public float cook, pour;
    }
    [Serializable] private class WorkerData
    {
        public int id, tier, site, startDay, ticket, scoop, topping, step, locker, prep, iron, target;
        public bool onDuty, driver;
        public float progress;
        public Vector3 position;
        public TycoonInventory inventory;
        public TycoonItem carrying;
    }
    [Serializable] private class CustomerData { public int site; public TycoonOrder order; public Vector3 position; }
    [Serializable] private class LooseData { public TycoonItem item; public Vector3 position; }
    public static void Write(TycoonGameManager game)
    {
        var d = new Data { cash = game.cash, xp = game.xp, clock = game.clock, salesToday = game.salesToday, wagesToday = game.wagesToday, day = game.day, level = game.level, sales = game.sales, nextId = game.nextId, phase = (int)game.phase, completed = game.completed, results = game.results,
            playerPosition = game.player.transform.position, playerRotation = game.player.transform.rotation, playerPitch = game.player.pitch, selected = game.player.selected, player = game.player.inventory,
            bikePosition = game.bike.transform.position, bikeRotation = game.bike.transform.rotation, bike = game.bike.cargo,
            truckPosition = game.truck.transform.position, truckRotation = game.truck.transform.rotation, truck = game.truck.cargo, truckStop = game.truck.routeStop, truckOperating = game.truck.operatingToday, routeComplete = game.truck.routeComplete, truckDemand = game.truck.demand, travelStage = game.truck.travelStage };
        d.sites = game.sites.Select(s => new SiteData { owned = s.owned, open = s.open, expanded = s.expanded, size = s.plotSize, revenue = s.revenue, spawn = s.spawnTimer, lost = s.lostSales, demand = s.stopDemand }).ToArray();
        d.parts = game.parts.Where(p => p.kind != TycoonPart.Kind.Bike && p.kind != TycoonPart.Kind.Truck && p.kind != TycoonPart.Kind.Supplier && p.kind != TycoonPart.Kind.Plot).Select(p => new PartData { id = p.id, prefab = p.catalogIndex, site = p.site, variant = p.variant, installed = p.installed, packed = p.packed, support = p.support == null ? 0 : p.support.id, position = p.transform.position, rotation = p.transform.rotation, storage = p.storage, contents = p.contents, owner = p.claimedBy, cook = p.cookTime, pour = p.pourProgress, ironStage = p.ironStage }).ToArray();
        d.workers = game.workers.Select(w => new WorkerData { id = w.employeeId, tier = w.tier, site = w.site, startDay = w.startDay, ticket = w.ticketId, scoop = w.scoopIndex, topping = w.toppingIndex, step = (int)w.step, locker = w.locker.id, prep = w.prep == null ? 0 : w.prep.id, iron = w.iron == null ? 0 : w.iron.id, target = w.target == null ? 0 : w.target.id, onDuty = w.onDuty, driver = w.driver, progress = w.progress, position = w.transform.position, inventory = w.inventory, carrying = w.carrying }).ToArray();
        d.customers = game.actors.Where(a => !a.worker && !a.leaving).Select(a => new CustomerData { site = a.site, order = a.order, position = a.transform.position }).ToArray();
        d.loose = game.looseItems.Where(l => l != null).Select(l => new LooseData { item = l.item, position = l.transform.position }).ToArray();
        string temp = TycoonGameManager.SavePath + ".tmp";
        File.WriteAllText(temp, JsonUtility.ToJson(d, true));
        if (File.Exists(TycoonGameManager.SavePath)) File.Replace(temp, TycoonGameManager.SavePath, TycoonGameManager.SavePath + ".bak");
        else File.Move(temp, TycoonGameManager.SavePath);
    }
    public static void Load(TycoonGameManager game)
    {
        game.loadingCampaign = true;
        var d = JsonUtility.FromJson<Data>(File.ReadAllText(TycoonGameManager.SavePath));
        game.cash = d.cash; game.xp = d.xp; game.clock = d.clock; game.salesToday = d.salesToday; game.wagesToday = d.wagesToday;
        game.day = d.day; game.level = d.level; game.sales = d.sales; game.nextId = d.nextId; game.phase = (TycoonGameManager.Phase)d.phase; game.completed = d.completed; game.results = d.results;
        game.player.inventory = d.player; game.player.selected = d.selected; game.player.Teleport(d.playerPosition);
        game.player.transform.rotation = d.playerRotation; game.player.pitch = d.playerPitch; game.player.view.transform.localRotation = Quaternion.Euler(d.playerPitch,0,0);
        game.bike.cargo = d.bike; game.bike.interaction.storage = d.bike; game.bike.transform.SetPositionAndRotation(d.bikePosition, d.bikeRotation);
        game.truck.cargo = d.truck; game.truck.interaction.storage = d.truck; game.truck.transform.SetPositionAndRotation(d.truckPosition, d.truckRotation); game.truck.routeStop = d.truckStop;
        game.truck.operatingToday = d.truckOperating; game.truck.routeComplete = d.routeComplete; game.truck.demand = d.truckDemand; game.truck.travelStage = d.travelStage;
        for (int i = 0; i < d.sites.Length; i++)
        {
            var s = game.sites[i]; var saved = d.sites[i];
            s.owned = saved.owned; s.open = saved.open; s.expanded = saved.expanded; s.plotSize = saved.size;
            s.revenue = saved.revenue; s.spawnTimer = saved.spawn; s.lostSales = saved.lost; s.stopDemand = saved.demand;
        }
        foreach (var part in game.parts.ToArray())
        {
            if (part.kind == TycoonPart.Kind.Bike || part.kind == TycoonPart.Kind.Truck || part.kind == TycoonPart.Kind.Supplier || part.kind == TycoonPart.Kind.Plot) continue;
            game.parts.Remove(part); Object.Destroy(part.gameObject);
        }
        var map = new Dictionary<int, TycoonPart>();
        foreach (var p in d.parts)
        {
            var part = game.AddPart(p.prefab, p.site, p.position); part.id = p.id; part.transform.rotation = p.rotation;
            part.variant = p.variant; part.storage = p.storage; part.contents = p.contents != null && p.contents.kind != TycoonItem.Kind.None ? p.contents : null; part.claimedBy = p.owner == "Player" ? "" : p.owner; part.cookTime = p.cook; part.pourProgress = p.pour; part.ironStage = p.ironStage; part.installed = p.installed; part.packed = p.packed; part.gameObject.SetActive(!p.packed); map.Add(p.id, part);
            if (part.kind == TycoonPart.Kind.Shelf) Array.Resize(ref part.storage.slots, TycoonPart.ShelfCapacity);
        }
        foreach (var p in d.parts) if (p.support != 0)
        {
            map[p.id].support = map[p.support]; map[p.id].transform.SetParent(map[p.support].transform, true);
            if (map[p.id].kind == TycoonPart.Kind.Bowl) map[p.id].operatingPoint.position = map[p.support].operatingPoint.position;
        }
        foreach (var worker in game.workers) Object.Destroy(worker.gameObject);
        game.workers.Clear(); game.actors.Clear();
        foreach (var w in d.workers)
        {
            var actor = Object.Instantiate(game.catalog.workerPrefab, w.position, Quaternion.identity); actor.game = game; actor.site = w.site; actor.worker = true;
            var worker = actor.GetComponent<TycoonWorker>(); worker.game = game; worker.actor = actor; worker.site = w.site; worker.tier = w.tier; worker.employeeId = w.id;
            worker.startDay = w.startDay; worker.ticketId = w.ticket; worker.scoopIndex = w.scoop; worker.toppingIndex = w.topping; worker.step = (TycoonWorker.Step)w.step;
            worker.locker = map[w.locker]; worker.prep = w.prep == 0 ? null : map[w.prep]; worker.iron = w.iron == 0 ? null : map[w.iron]; worker.target = w.target == 0 ? null : map[w.target];
            worker.onDuty = w.onDuty; worker.driver = w.driver; worker.progress = w.progress; worker.inventory = w.inventory; worker.carrying = w.carrying;
            game.workers.Add(worker); game.actors.Add(actor);
        }
        foreach (var c in d.customers)
        {
            var actor = Object.Instantiate(game.catalog.customerPrefab, c.position, Quaternion.identity); actor.game = game; actor.site = c.site; actor.order = c.order;
            game.sites[c.site].queue.Add(actor); game.actors.Add(actor);
        }
        foreach (var loose in game.looseItems.ToArray()) Object.Destroy(loose.gameObject);
        foreach (var loose in d.loose) game.Deliver(loose.item, loose.position);
        game.nextId = d.nextId; game.truck.gameObject.SetActive(game.sites[2].owned);
        game.StartCoroutine(RestoreNavigation(game));
        game.notice = "Campaign restored.";
    }
    private static System.Collections.IEnumerator RestoreNavigation(TycoonGameManager game)
    {
        yield return null;
        game.navigation.BuildNavMesh();
        foreach (var worker in game.workers)
        {
            worker.actor.agent.Warp(worker.driver && !game.truck.AtStop ? game.truck.kitchenEntry.position : worker.transform.position);
            worker.actor.Hold(worker.carrying != null && worker.carrying.kind != TycoonItem.Kind.None ? worker.carrying : worker.inventory.slots.FirstOrDefault(i => i != null && i.Tool));
        }
        game.loadingCampaign = false;
    }
}
