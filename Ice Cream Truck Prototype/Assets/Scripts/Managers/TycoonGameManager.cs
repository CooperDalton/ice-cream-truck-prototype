using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using UnityEngine;
using Unity.AI.Navigation;

public class TycoonGameManager : MonoBehaviour
{
    public enum Phase { Preparation, Trading, Results }
    [Serializable]
    public class Site
    {
        public string name;
        public bool owned, open, expanded;
        public Transform origin, queuePoint, pickupQueuePoint, registerOperatingPoint, signMount;
        public GameObject canopy, registerCounter;
        public Transform paving;
        public Vector2 plotSize = new Vector2(8, 6);
        public Vector3 PlotOffset => expanded ? Vector3.back : Vector3.zero;
        public float revenue, spawnTimer = 5;
        public int lostSales, stopDemand = 7;
        [NonSerialized] public List<TycoonActor> queue = new List<TycoonActor>();
    }
    public static TycoonGameManager Instance { get; private set; }
    public TycoonCatalogSO catalog;
    public TycoonPlayer player;
    public TycoonHUD hud;
    public TycoonBuilder builder;
    public TycoonTutorial tutorial;
    public TycoonVehicle bike, truck;
    public NavMeshSurface navigation;
    public AudioSource feedback;
    public AudioClip saleSound, scoopSound, depositSound, upgradeSound, daySound;
    public Site[] sites;
    public Transform[] spawnPoints, truckStops;
    public Transform supplier, pickupPoint;
    public Transform rewardDeliveryOrigin;
    public Transform[] supplyPickupPoints;
    public GameObject supplierBuilding;
    public List<TycoonPart> parts = new List<TycoonPart>();
    public List<TycoonWorker> workers = new List<TycoonWorker>();
    public List<TycoonActor> actors = new List<TycoonActor>();
    public List<TycoonLooseItem> looseItems = new List<TycoonLooseItem>();
    public Phase phase;
    public float cash, xp, clock, salesToday, wagesToday;
    public float orderPatience = 90, deliveryPatience = 120;
    public int day = 1, level = 1, sales, nextId = 1;
    public bool Paused => loadingCampaign || hud.adminMenu.panel.activeSelf || hud.menuOpen || phase == Phase.Results;
    public int FlavorCount => level >= 6 ? 12 : level >= 4 ? 8 : level >= 2 ? 4 : 2;
    public int ToppingCount => level >= 7 ? 6 : level >= 5 ? 4 : level >= 3 ? 2 : 0;
    public string notice = "Open your stand to meet the first customer.";
    public string results;
    public bool completed;
    [NonSerialized] public bool restartRequested;
    [NonSerialized] public bool loadingCampaign;
    public static string SavePath => Path.Combine(Application.persistentDataPath, "tycoon-campaign.json");
    public class SaleEventArgs : EventArgs { public float amount, tip; public int site; public Color color; }
    public event EventHandler<SaleEventArgs> SaleCompleted;
    private void Awake()
    {
        Instance = this;
        foreach (var part in parts) part.game = this;
    }
    private void Start()
    {
        Application.runInBackground = true;
        if (File.Exists(SavePath)) TycoonSave.Load(this);
        else
        {
            tutorial.BeginNewGame();
        }
        RefreshBusinessModels(); player.RefreshHeld();
    }
    private void Update()
    {
        Time.timeScale = Paused ? 0 : 1;
        if (Paused || phase != Phase.Trading) return;
        if (tutorial.FirstDay) return;
        clock += Time.deltaTime;
        foreach (var site in sites)
        {
            if (!site.owned || !site.open) continue;
            site.spawnTimer -= Time.deltaTime;
            if (site.spawnTimer <= 0 && clock < 480) Spawn(Array.IndexOf(sites, site));
        }
        if (clock >= 480 && (workers.All(w => w.ticketId < 0) || clock >= 540)) CloseDay();
    }
    public IEnumerable<TycoonPart> Parts(int site, TycoonPart.Kind kind)
    {
        return parts.Where(p => p.site == site && p.kind == kind && p.installed);
    }
    public bool Spend(float amount)
    {
        if (cash < amount) { notice = "You need $" + (amount - cash).ToString("0.##") + " more."; return false; }
        cash -= amount; return true;
    }
    public void OpenDay()
    {
        if (phase != Phase.Preparation) return;
        if (!tutorial.CanOpen) { notice = "Follow the highlight"; return; }
        clock = 0; salesToday = 0; wagesToday = 0; phase = Phase.Trading;
        foreach (var site in sites) { site.revenue = 0; site.lostSales = 0; site.spawnTimer = 5; site.stopDemand = 7; }
        foreach (var worker in workers)
        {
            worker.onDuty = worker.startDay <= day && cash >= worker.Wage + (worker.driver ? 12 : 0);
            if (worker.onDuty) { cash -= worker.Wage; wagesToday += worker.Wage; }
        }
        truck.BeginDay();
        if (sites[2].owned && cash >= 12) { cash -= 12; wagesToday += 12; truck.operatingToday = true; }
        sites[0].open = true; sites[1].open = sites[1].owned && workers.Any(w => w.site == 1 && w.onDuty); sites[2].open = truck.AtStop && truck.operatingToday;
        notice = "Open for business.";
        if (tutorial.FirstDay) tutorial.SpawnCustomer(); else Spawn(0, true);
        Save();
    }
    public void CloseDay()
    {
        if (phase != Phase.Trading) return;
        phase = Phase.Results;
        foreach (var worker in workers) if (worker.driver) truck.ReleaseDriver(worker);
        foreach (var actor in actors.ToArray()) if (!actor.worker && !actor.leaving) actor.Leave();
        foreach (var site in sites) site.open = false;
        tutorial.PrepareDayEnd();
        int previous = level;
        while (level < 7 && xp >= TycoonCatalogSO.Thresholds[level]) { level++; Reward(level); }
        results = "Day " + day + " complete\nSales $" + salesToday.ToString("0.##") + "\nWages and vehicle $" + wagesToday.ToString("0.##") + "\nCash $" + cash.ToString("0.##") + "\nLost sales " + sites.Sum(s => s.lostSales);
        if (level > previous) results += "\nBusiness level " + level + ": new ingredients unlocked.";
        if (!completed && sites.All(s => s.owned) && workers.Any(w => w.site == 0 && w.onDuty) && workers.Any(w => w.site == 1 && w.onDuty) && workers.Any(w => w.driver && w.onDuty))
        { completed = true; results += "\nYour ice cream business runs across the town! Continue expanding your layout or keep trading."; }
        Save();
        feedback.PlayOneShot(daySound,.5f);
    }
    public void NextDay()
    {
        day++; phase = Phase.Preparation; clock = 0;
        foreach (var worker in workers) { worker.onDuty = false; worker.ResetTicket(); }
        tutorial.BeginShopping();
        notice = "Preparation time. Stock supplies and check staff before opening."; hud.menuOpen = false; Save();
    }
    private void Reward(int newLevel)
    {
        int first = newLevel == 2 ? 2 : newLevel == 4 ? 4 : 8;
        int count = newLevel == 2 ? 2 : 4;
        if (newLevel == 2 || newLevel == 4 || newLevel == 6)
        {
            for (int i = first; i < first + count; i++)
            {
                int slot = i - 2;
                var position = rewardDeliveryOrigin.TransformPoint(new Vector3(slot % 2 * 1.2f, 0, -slot / 2 * 1.2f));
                var tub = AddPart(1, 0, position);
                tub.variant = i; tub.contents = new TycoonItem(TycoonItem.Kind.Tub, 0, i); tub.installed = false; tub.rewardDelivery = true;
                Deliver(new TycoonItem(TycoonItem.Kind.Tub, 24, i), position + rewardDeliveryOrigin.right * .6f + Vector3.up * .03f, levelReward: true);
            }
            notice = "New flavors delivered to your base.";
        }
        else
        {
            int start = newLevel == 3 ? 0 : newLevel == 5 ? 2 : 4;
            for (int i = start; i < start + 2; i++) Deliver(new TycoonItem(TycoonItem.Kind.Topping, 30, i), rewardDeliveryOrigin.TransformPoint(new Vector3(i % 2 * .6f, .03f, -6 - i / 2 * .6f)), levelReward: true);
        }
    }
    public TycoonPart AddPart(int index, int site, Vector3 position)
    {
        var part = Instantiate(catalog.partPrefabs[index], position, Quaternion.identity);
        part.game = this; part.site = site; part.id = nextId++;
        if (site == 2) part.transform.SetParent(truck.transform, true);
        parts.Add(part);
        if (part.kind == TycoonPart.Kind.Register) { sites[site].registerCounter = part.gameObject; sites[site].queuePoint = part.queuePoint; sites[site].registerOperatingPoint = part.operatingPoint; }
        if (part.kind == TycoonPart.Kind.ServingCounter)
        {
            if (site == 2) part.queuePoint.localPosition = new Vector3(.65f,-.58f,1.2f);
            sites[site].pickupQueuePoint = part.queuePoint;
        }
        return part;
    }
    public void Deliver(TycoonItem item, Vector3 point, int supplySlot = -1, bool levelReward = false)
    {
        var loose = Instantiate(catalog.loosePrefab, point, Quaternion.identity);
        loose.game = this; loose.item = item; loose.supplySlot = supplySlot; loose.levelReward = levelReward;
        loose.body.isKinematic = supplySlot >= 0 || levelReward;
        looseItems.Add(loose);
    }
    public bool PurchaseSupply(int product)
    {
        if (Vector3.Distance(player.transform.position, supplier.position) > 8) { notice = "Visit the wholesale supplier to buy supplies."; return false; }
        TycoonItem item; float price;
        if (product < 12) { if (product >= FlavorCount) return false; item = new TycoonItem(TycoonItem.Kind.Tub, 24, product); price = TycoonCatalogSO.TubPrices[product]; }
        else if (product < 18) { int v = product - 12; if (v >= ToppingCount) return false; item = new TycoonItem(TycoonItem.Kind.Topping, 30, v); price = TycoonCatalogSO.RefillPrices[v]; }
        else if (product == 18) { item = new TycoonItem(TycoonItem.Kind.Bowls, 12); price = 3; }
        else if (product == 19) { item = new TycoonItem(TycoonItem.Kind.Batter, 10); price = 6; }
        else if (product == 20) { item = new TycoonItem(TycoonItem.Kind.ImprovedScooper); price = 12; }
        else if (product == 21) { item = new TycoonItem(TycoonItem.Kind.BasicScooper); price = 6; }
        else if (product == 22) { item = new TycoonItem(TycoonItem.Kind.ElectricScooper); price = 36; }
        else return false;
        var available = Enumerable.Range(0, supplyPickupPoints.Length).Where(i => !looseItems.Any(l => l.supplySlot == i)).ToArray();
        int stacks = Mathf.CeilToInt((float)item.amount / item.Capacity);
        if (available.Length < stacks) { notice = "Collect items from the counter to make room. You have not been charged."; return false; }
        if (!Spend(price)) return false;
        int delivery = 0;
        for (int remaining = item.amount; remaining > 0;)
        {
            var stack = item.Copy(); stack.amount = Mathf.Min(remaining, item.Capacity);
            remaining -= stack.amount;
            int slot = available[delivery++];
            Deliver(stack, supplyPickupPoints[slot].position, slot);
        }
        notice = "Ready on the collection counter.";
        tutorial.Purchased(product);
        Save();
        return true;
    }
    private void DeliverEquipment(int index, int site)
    {
        var delivery = site == 0 ? rewardDeliveryOrigin : sites[site].origin;
        for (int slot = 0; ; slot++)
        {
            var point = delivery.TransformPoint(new Vector3(slot % 4 * 1.4f, 0, -slot / 4 * 1.4f));
            if (parts.Any(p => !p.packed && Vector3.Distance(p.transform.position, point) < 1.2f) || looseItems.Any(l => Vector3.Distance(l.transform.position, point) < 1.2f)) continue;
            var part = AddPart(index, site, point); part.installed = false;
            return;
        }
    }
    public bool BuyUpgrade(int choice, int site)
    {
        if (!sites[site].owned && choice != 6) { notice = "Purchase this location first."; return false; }
        if (choice == 0)
        {
            notice = "Buy scoopers from the supply shop."; return false;
        }
        if (choice >= 1 && choice <= 3)
        {
            if (!Spend(new[] { 24, 48, 88 }[choice - 1])) return false;
            DeliverEquipment(new[] { 4, 14, 15 }[choice - 1], site);
            notice = (choice * 4) + "-slot locker delivered behind the shop. Place it before hiring an employee.";
        }
        if (choice == 4)
        {
            if (bike.cargo.slots.Length == 8) { notice = "Bicycle cargo is already upgraded."; return false; }
            if (!Spend(48)) return false;
            Array.Resize(ref bike.cargo.slots, 8);
            notice = "Bicycle cargo upgraded to 8 slots.";
        }
        if (choice == 5)
        {
            if (sites[site].expanded) { notice = "This shop is already expanded."; return false; }
            if (!Spend(160)) return false;
            sites[site].expanded = true;
            DeliverEquipment(0, site); DeliverEquipment(8, site);
            notice="Shop expanded four rows backward. Place the extra table and shelf in the new space.";
        }
        if (choice == 6)
        {
            if (sites[1].owned) { notice = "You already own the park stand."; return false; }
            if (!Spend(250)) return false;
            sites[1].owned = true; Deliver(new TycoonItem(TycoonItem.Kind.ImprovedScooper), sites[1].origin.position + Vector3.up);
            notice = "Park stand purchased. Stock it before opening.";
        }
        if (choice == 7)
        {
            if (sites[2].owned) { notice = "You already own the truck."; return false; }
            if (!sites[0].expanded || workers.Count == 0) { notice = "Expand the home kiosk and hire an employee first."; return false; }
            if (!Spend(600)) return false;
            sites[2].owned = true; truck.gameObject.SetActive(true);
            foreach (var part in parts.Where(p => p.site == 2)) part.gameObject.SetActive(true);
            notice = "Truck purchased. Stock its kitchen and cargo before the next day.";
        }
        if (choice == 10) { notice = "Use a shelf for spare supplies."; return false; }
        if (choice >= 8)
        {
            int index = choice - 8;
            if (!Spend(new[] { 24,12,36,18,48,20 }[index])) return false;
            DeliverEquipment(new[] { 0,2,5,1,3,8 }[index], site); notice = "Furniture delivered behind the shop. Hold right-click to pack it, then select it to place.";
        }
        RefreshBusinessModels(); navigation.BuildNavMesh(); feedback.PlayOneShot(upgradeSound,.45f); return true;
    }
    public bool Hire(int tier, int site, bool driver = false)
    {
        if (driver && !sites[2].owned) { notice = "Buy the truck before hiring a driver."; return false; }
        if (!sites[site].owned) { notice = "Purchase this location before hiring an employee."; return false; }
        if (driver && workers.Any(w => w.driver)) { notice = "The truck already has a driver."; return false; }
        var locker = Parts(site, TycoonPart.Kind.Locker).FirstOrDefault();
        if (locker == null) { notice = "Buy and place a staff locker first."; return false; }
        if (!Spend(driver ? 120 : new[] { 60, 90, 140 }[tier])) return false;
        var actor = Instantiate(catalog.workerPrefab, site == 2 ? truck.kitchenEntry.position : sites[site].origin.position + new Vector3(0, 0, -2), Quaternion.identity);
        actor.game = this; actor.site = site; actor.worker = true;
        var worker = actor.GetComponent<TycoonWorker>(); worker.game = this; worker.actor = actor; worker.site = site;
        worker.employeeId = nextId++; worker.tier = tier; worker.locker = locker; worker.driver = driver;
        worker.startDay = phase == Phase.Trading ? day + 1 : day;
        workers.Add(worker); actors.Add(actor); notice = "Employee hired. Put a scooper and supplies into the assigned locker."; return true;
    }
    public void Pay(TycoonActor customer, TycoonItem serving)
    {
        if (!customer.ReadyForPickup) throw new InvalidOperationException("Customer has not reached pickup");
        if (!serving.Matches(customer.order)) throw new InvalidOperationException("Wrong recipe");
        float price = customer.order.Price(customer.site), tip = customer.order.Tip(customer.site);
        float amount = price + tip;
        cash += amount; xp += amount; salesToday += amount; sales++; sites[customer.site].revenue += amount;
        SaleCompleted?.Invoke(this, new SaleEventArgs { amount = amount, tip = tip, site = customer.site, color = customer.order.RewardColor });
        feedback.PlayOneShot(saleSound,.35f);
        customer.Leave(); notice = "+$" + price.ToString("0.##") + " + $" + tip.ToString("0.00") + " tip";
        if (sales == 1) sites[0].spawnTimer = 3;
    }
    public TycoonOrder GenerateOrder(int site)
    {
        int[] flavors = Parts(site, TycoonPart.Kind.Tub).Select(p => p.variant).Where(v => v < FlavorCount).Distinct().ToArray();
        if (flavors.Length == 0) flavors = new[] { 0 };
        bool tutorial = site == 0 && sales < 2;
        bool cone = !tutorial && Parts(site, TycoonPart.Kind.Iron).Any() && Parts(site, TycoonPart.Kind.Prep).Any() && UnityEngine.Random.value < .45f;
        int scoops = sales < 6 ? 1 : UnityEngine.Random.Range(1, cone ? 3 : 4);
        var order = new TycoonOrder { id = nextId++, flavors = new int[scoops], patience = orderPatience, patienceLimit = orderPatience };
        for (int i = 0; i < scoops; i++) order.flavors[i] = tutorial && flavors.Contains(sales) ? sales : flavors[UnityEngine.Random.Range(0, flavors.Length)];
        order.cone = cone;
        if (ToppingCount > 0 && !tutorial && UnityEngine.Random.value < .6f)
        {
            order.toppings |= 1 << UnityEngine.Random.Range(0, ToppingCount);
            if (ToppingCount > 2 && UnityEngine.Random.value < .3f) order.toppings |= 1 << UnityEngine.Random.Range(0, ToppingCount);
        }
        return order;
    }
    private void Spawn(int site, bool opening = false)
    {
        var business = sites[site];
        if (site == 0 && sales == 0 && business.queue.Count > 0) { business.spawnTimer = 2; return; }
        business.spawnTimer = (site == 0 ? business.expanded ? 10 : 14 : 16) * UnityEngine.Random.Range(.8f, 1.2f);
        if (business.queue.Count >= (business.expanded ? 6 : 4) || actors.Count >= 24 || (site == 2 && (!truck.AtStop || truck.demand[truck.routeStop] <= 0))) return;
        var point = spawnPoints.OrderBy(p => Vector3.Distance(p.position, business.queuePoint.position)).FirstOrDefault(p => { var v = player.view.WorldToViewportPoint(p.position); return v.z < 0 || v.x < 0 || v.x > 1 || v.y < 0 || v.y > 1; });
        if (point == null && !opening) { business.spawnTimer = 2; return; }
        Vector3 position = opening ? business.queuePoint.position : site == 0 && sales < 2 ? business.queuePoint.position + Vector3.right * 4 : point.position;
        if (!UnityEngine.AI.NavMesh.SamplePosition(position, out var spawn, 2, UnityEngine.AI.NavMesh.AllAreas)) return;
        position = spawn.position;
        if (!Parts(site, TycoonPart.Kind.Tub).Any()) return;
        var order = GenerateOrder(site);
        foreach (int flavor in order.flavors)
        {
            int needed = order.flavors.Count(f => f == flavor) + business.queue.Sum(a => a.order.flavors.Count(f => f == flavor));
            if (Stock(site, TycoonItem.Kind.Tub, flavor) < needed)
            { business.lostSales++; notice = business.name + " lost a sale: " + TycoonCatalogSO.FlavorNames[flavor] + " is out of stock."; return; }
        }
        bool available = order.cone ? Stock(site, TycoonItem.Kind.Batter, 0) > business.queue.Count(a => a.order.cone) : Stock(site, TycoonItem.Kind.Bowls, 0) > business.queue.Count(a => !a.order.cone);
        for (int i = 0; i < ToppingCount; i++) if ((order.toppings & (1 << i)) != 0) available &= Stock(site, TycoonItem.Kind.Topping, i) > business.queue.Count(a => (a.order.toppings & (1 << i)) != 0);
        if (!available) { business.lostSales++; notice = business.name + " lost a sale: restock bowls, batter, or toppings."; return; }
        var actor = Instantiate(catalog.customerPrefab, position, Quaternion.identity);
        actor.game = this; actor.site = site; actor.order = order;
        business.queue.Add(actor); actors.Add(actor); if (site == 2) { truck.demand[truck.routeStop]--; business.stopDemand = truck.demand[truck.routeStop]; }
    }
    public int Stock(int site, TycoonItem.Kind kind, int variant)
    {
        var items = parts.Where(p => p.site == site && p.installed).SelectMany(p => p.storage.slots.Concat(new[] { p.contents }))
            .Concat(workers.Where(w => w.site == site).SelectMany(w => w.inventory.slots));
        if (Vector3.Distance(player.transform.position, sites[site].origin.position) < 12) items = items.Concat(player.inventory.slots);
        return items.Where(i => i != null && i.kind == kind && i.variant == variant).Sum(i => i.amount);
    }
    public void Save()
    {
        TycoonSave.Write(this);
    }
    public void RefreshBusinessModels()
    {
        for (int i=0;i<2;i++)
        {
            sites[i].canopy.SetActive(true);
            sites[i].plotSize = new Vector2(8, sites[i].expanded ? 8 : 6);
            sites[i].paving.position = sites[i].origin.TransformPoint(sites[i].PlotOffset + Vector3.down * .01f);
            sites[i].paving.localScale = new Vector3(sites[i].plotSize.x,.04f,sites[i].plotSize.y);
        }
        bike.smallCargoModel.SetActive(bike.cargo.slots.Length==4); bike.largeCargoModel.SetActive(bike.cargo.slots.Length==8);
    }
    public void PreparationSound(AudioClip clip,Vector3 position)
    {
        float volume=Mathf.Clamp01(1-Vector3.Distance(player.transform.position,position)/8);
        if(volume>0)feedback.PlayOneShot(clip,volume*.3f);
    }
    private void OnApplicationQuit()
    {
        if (!restartRequested) Save(); Time.timeScale = 1;
    }
}
