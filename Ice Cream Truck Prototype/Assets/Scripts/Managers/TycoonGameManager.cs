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
        public Transform origin, queuePoint;
        public GameObject canopy, kiosk;
        public Transform paving;
        public Vector2 plotSize = new Vector2(8, 6);
        public float revenue, spawnTimer = 5;
        public int lostSales, stopDemand = 7;
        [NonSerialized] public List<TycoonActor> queue = new List<TycoonActor>();
    }
    public static TycoonGameManager Instance { get; private set; }
    public TycoonCatalogSO catalog;
    public TycoonPlayer player;
    public TycoonHUD hud;
    public TycoonBuilder builder;
    public TycoonVehicle bike, truck;
    public NavMeshSurface navigation;
    public AudioSource feedback;
    public AudioClip saleSound, scoopSound, depositSound, upgradeSound, daySound;
    public Site[] sites;
    public Transform[] spawnPoints, truckStops;
    public Transform supplier, pickupPoint;
    public List<TycoonPart> parts = new List<TycoonPart>();
    public List<TycoonWorker> workers = new List<TycoonWorker>();
    public List<TycoonActor> actors = new List<TycoonActor>();
    public List<TycoonLooseItem> looseItems = new List<TycoonLooseItem>();
    public Phase phase;
    public float cash, xp, clock, salesToday, wagesToday;
    public int day = 1, level = 1, sales, nextId = 1;
    public bool Paused => loadingCampaign || hud.menuOpen || builder.active || phase == Phase.Results;
    public int FlavorCount => level >= 6 ? 12 : level >= 4 ? 8 : level >= 2 ? 4 : 2;
    public int ToppingCount => level >= 7 ? 6 : level >= 5 ? 4 : level >= 3 ? 2 : 0;
    public string notice = "Open your stand to meet the first customer.";
    public string results;
    public bool completed;
    [NonSerialized] public bool restartRequested;
    [NonSerialized] public bool loadingCampaign;
    public static string SavePath => Path.Combine(Application.persistentDataPath, "tycoon-campaign.json");
    public class SaleEventArgs : EventArgs { public float amount; public int site; }
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
            player.inventory.slots[0] = new TycoonItem(TycoonItem.Kind.BasicScooper);
            player.inventory.slots[1] = new TycoonItem(TycoonItem.Kind.Bowls, 12);
            foreach (var tub in Parts(0, TycoonPart.Kind.Tub)) tub.contents = new TycoonItem(TycoonItem.Kind.Tub,12,tub.variant);
            Parts(0, TycoonPart.Kind.Shelf).First().storage.slots[0] = new TycoonItem(TycoonItem.Kind.Bowls, 4);
        }
        RefreshBusinessModels(); player.RefreshHeld();
    }
    private void Update()
    {
        Time.timeScale = Paused ? 0 : 1;
        if (Paused || phase != Phase.Trading) return;
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
        foreach (var worker in workers)
        {
            if (worker.startDay <= day && cash >= worker.Wage && !worker.ValidateLayout()) { notice = worker.status; return; }
        }
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
        notice = "Open for business."; if (sales < 2) Spawn(0); Save();
    }
    public void CloseDay()
    {
        if (phase != Phase.Trading) return;
        phase = Phase.Results;
        foreach (var worker in workers) if (worker.driver) truck.ReleaseDriver(worker);
        foreach (var actor in actors.ToArray()) if (!actor.worker && !actor.leaving) actor.Leave();
        foreach (var site in sites) site.open = false;
        int previous = level;
        while (level < 7 && xp >= TycoonCatalogSO.Thresholds[level]) { level++; Reward(level); }
        results = "Day " + day + " complete\nSales $" + salesToday.ToString("0.##") + "\nWages and vehicle $" + wagesToday.ToString("0.##") + "\nCash $" + cash.ToString("0.##") + "\nLost sales " + sites.Sum(s => s.lostSales);
        if (level > previous) results += "\nBusiness level " + level + ": new ingredients delivered at home.";
        if (!completed && sites.All(s => s.owned) && workers.Any(w => w.site == 0 && w.onDuty) && workers.Any(w => w.site == 1 && w.onDuty) && workers.Any(w => w.driver && w.onDuty))
        { completed = true; results += "\nYour ice cream business runs across the town! Continue expanding your layout or keep trading."; }
        Save();
        feedback.PlayOneShot(daySound,.5f);
    }
    public void NextDay()
    {
        day++; phase = Phase.Preparation; clock = 0;
        foreach (var worker in workers) { worker.onDuty = false; worker.ResetTicket(); }
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
                var tub = AddPart(1, 0, sites[0].origin.position + new Vector3(-5 + (i % 4) * .6f, 0, -4 - i / 4));
                tub.variant = i; tub.contents = new TycoonItem(TycoonItem.Kind.Tub, 0, i); tub.installed = false;
                Deliver(new TycoonItem(TycoonItem.Kind.Tub, 24, i), sites[0].origin.position + new Vector3(3, .4f, -2 + (i - first) * .5f));
            }
            notice = "New flavor tubs delivered. Install their supplies before opening.";
        }
        else
        {
            int start = newLevel == 3 ? 0 : newLevel == 5 ? 2 : 4;
            for (int i = start; i < start + 2; i++) Deliver(new TycoonItem(TycoonItem.Kind.Topping, 15, i), sites[0].origin.position + new Vector3(3, .5f, -1 + i * .3f));
        }
    }
    public TycoonPart AddPart(int index, int site, Vector3 position)
    {
        var part = Instantiate(catalog.partPrefabs[index], position, Quaternion.identity);
        part.game = this; part.site = site; part.id = nextId++;
        if (site == 2) part.transform.SetParent(truck.transform, true);
        parts.Add(part); return part;
    }
    public void Deliver(TycoonItem item, Vector3 point)
    {
        var loose = Instantiate(catalog.loosePrefab, point, Quaternion.identity);
        loose.game = this; loose.item = item; looseItems.Add(loose);
    }
    public bool PurchaseSupply(int product)
    {
        if (Vector3.Distance(player.transform.position, supplier.position) > 8) { notice = "Visit the wholesale supplier to buy supplies."; return false; }
        TycoonItem item; float price;
        if (product < 12) { if (product >= FlavorCount) return false; item = new TycoonItem(TycoonItem.Kind.Tub, 24, product); price = TycoonCatalogSO.TubPrices[product]; }
        else if (product < 18) { int v = product - 12; if (v >= ToppingCount) return false; item = new TycoonItem(TycoonItem.Kind.ToppingPack, 30, v); price = TycoonCatalogSO.RefillPrices[v]; }
        else if (product == 18) { item = new TycoonItem(TycoonItem.Kind.BowlPack, 30); price = 6; }
        else if (product == 19) { item = new TycoonItem(TycoonItem.Kind.BatterPack, 20); price = 12; }
        else if (product == 20) { item = new TycoonItem(TycoonItem.Kind.ImprovedScooper); price = 12; }
        else if (product < 27) { int v = product - 21; if (v >= ToppingCount) return false; item = new TycoonItem(TycoonItem.Kind.Topping, 0, v); price = 4; }
        else if (product == 27) { item = new TycoonItem(TycoonItem.Kind.Batter,0); price = 4; }
        else { item = new TycoonItem(TycoonItem.Kind.BasicScooper); price = 6; }
        if (!Spend(price)) return false;
        Deliver(item, pickupPoint.position + Vector3.up * .4f + UnityEngine.Random.insideUnitSphere * .1f);
        notice = "Purchase ready on the supplier pickup shelf."; return true;
    }
    public bool BuyUpgrade(int choice, int site)
    {
        if (!sites[site].owned && choice != 6) { notice = "Purchase this location first."; return false; }
        var origin = sites[site].origin.position;
        if (choice == 0)
        {
            if (!Spend(12)) return false;
            Deliver(new TycoonItem(TycoonItem.Kind.ImprovedScooper), origin + new Vector3(.6f, 1.2f, 0));
        }
        if (choice == 1)
        {
            if (!Spend(24)) return false;
            AddPart(4, site, origin + new Vector3(3, 0, -2)).transform.rotation = Quaternion.Euler(0,180,0);
        }
        if (choice == 2)
        {
            var locker = Parts(site, TycoonPart.Kind.Locker).FirstOrDefault(p => p.storage.slots.Length < 12);
            if (locker == null) { notice = "Place a locker first."; return false; }
            if (!Spend(locker.storage.slots.Length == 4 ? 48 : 88)) return false;
            Array.Resize(ref locker.storage.slots, locker.storage.slots.Length + 4); locker.RefreshLocker();
        }
        if (choice == 3)
        {
            if (Parts(site, TycoonPart.Kind.Iron).Any()) { notice = "Waffle equipment is already installed."; return false; }
            if (!Spend(90)) return false;
            var table = AddPart(0, site, origin + new Vector3(2, 0, 0));
            var iron = AddPart(3, site, table.transform.position + new Vector3(0, .94f, 0)); iron.support = table; iron.transform.SetParent(table.transform, true);
            Deliver(new TycoonItem(TycoonItem.Kind.Batter, 0), origin + new Vector3(2, 1.2f, -.4f));
            Deliver(new TycoonItem(TycoonItem.Kind.BatterPack, 20), origin + new Vector3(2, 1.2f, .4f));
        }
        if (choice == 4)
        {
            if (bike.cargo.slots.Length == 8 || !Spend(48)) return false;
            Array.Resize(ref bike.cargo.slots, 8);
        }
        if (choice == 5)
        {
            if (sites[site].expanded || !Spend(160)) return false;
            sites[site].expanded = true; sites[site].plotSize.x += 2;
            AddPart(0, site, origin + new Vector3(-6, 0, 0)).installed=false; AddPart(5, site, origin + new Vector3(-6, 0, 2)).installed=false;
            notice="Kiosk expanded. Place the extra table and cold rack delivered beside the plot.";
        }
        if (choice == 6)
        {
            if (sites[1].owned || !Spend(250)) return false;
            sites[1].owned = true; Deliver(new TycoonItem(TycoonItem.Kind.ImprovedScooper), sites[1].origin.position + Vector3.up);
        }
        if (choice == 7)
        {
            if (sites[2].owned) return false;
            if (!sites[0].expanded || workers.Count == 0) { notice = "Expand the home kiosk and hire an employee first."; return false; }
            if (!Spend(600)) return false;
            sites[2].owned = true; truck.gameObject.SetActive(true);
            foreach (var part in parts.Where(p => p.site == 2)) part.gameObject.SetActive(true);
            notice = "Truck purchased. Stock its kitchen and cargo before the next day.";
        }
        if (choice >= 8)
        {
            int index = choice - 8;
            if (!Spend(new[] { 24,12,36,18,48,20 }[index])) return false;
            var part = AddPart(new[] { 0,2,5,1,3,8 }[index],site,origin + new Vector3(-5,0,-3));
            part.installed = false; notice = "Furniture delivered beside the plot. Press B to place it.";
        }
        RefreshBusinessModels(); navigation.BuildNavMesh(); feedback.PlayOneShot(upgradeSound,.45f); return true;
    }
    public bool Hire(int tier, int site, bool driver = false)
    {
        if (!sites[site].owned || (driver && !sites[2].owned)) return false;
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
        if (!serving.Matches(customer.order)) throw new InvalidOperationException("Wrong recipe");
        float amount = customer.order.Price(customer.site);
        cash += amount; xp += amount; salesToday += amount; sales++; sites[customer.site].revenue += amount;
        SaleCompleted?.Invoke(this, new SaleEventArgs { amount = amount, site = customer.site });
        feedback.PlayOneShot(saleSound,.35f);
        customer.Leave(); notice = "+$" + amount.ToString("0.##") + (sales == 2 ? " / You can buy the one-swipe scooper!" : " / Thank you!");
        if (sales == 1) sites[0].spawnTimer = 3;
    }
    public TycoonOrder GenerateOrder(int site)
    {
        int[] flavors = site == 0 ? Enumerable.Range(0, FlavorCount).ToArray() : Parts(site, TycoonPart.Kind.Tub).Select(p => p.variant).Where(v => v < FlavorCount).Distinct().Take(4).ToArray();
        if (flavors.Length == 0) flavors = new[] { 0 };
        bool tutorial = site == 0 && sales < 2;
        int scoops = sales < 6 ? 1 : site == 2 || UnityEngine.Random.value > .7f ? 2 : 1;
        var order = new TycoonOrder { id = nextId++, flavors = new int[scoops], patience = sales < 6 ? 120 : 90 };
        for (int i = 0; i < scoops; i++) order.flavors[i] = tutorial ? sales : flavors[UnityEngine.Random.Range(0, flavors.Length)];
        order.cone = !tutorial && Parts(site, TycoonPart.Kind.Iron).Any() && UnityEngine.Random.value < .45f;
        if (ToppingCount > 0 && !tutorial && UnityEngine.Random.value < .6f)
        {
            order.toppings |= 1 << UnityEngine.Random.Range(0, ToppingCount);
            if (ToppingCount > 2 && UnityEngine.Random.value < .3f) order.toppings |= 1 << UnityEngine.Random.Range(0, ToppingCount);
        }
        return order;
    }
    private void Spawn(int site)
    {
        var business = sites[site];
        if (site == 0 && sales == 0 && business.queue.Count > 0) { business.spawnTimer = 2; return; }
        business.spawnTimer = (site == 0 ? business.expanded ? 10 : 14 : 16) * UnityEngine.Random.Range(.8f, 1.2f);
        if (business.queue.Count >= (business.expanded ? 6 : 4) || actors.Count >= 24 || (site == 2 && (!truck.AtStop || truck.demand[truck.routeStop] <= 0))) return;
        var point = spawnPoints.OrderBy(p => Vector3.Distance(p.position, business.queuePoint.position)).FirstOrDefault(p => { var v = player.view.WorldToViewportPoint(p.position); return v.z < 0 || v.x < 0 || v.x > 1 || v.y < 0 || v.y > 1; });
        if (point == null) { business.spawnTimer = 2; return; }
        Vector3 position = site == 0 && sales < 2 ? business.queuePoint.position + Vector3.right * 4 : point.position;
        var order = GenerateOrder(site);
        foreach (int flavor in order.flavors)
        {
            int needed = order.flavors.Count(f => f == flavor) + business.queue.Sum(a => a.order.flavors.Count(f => f == flavor));
            if (Stock(site, TycoonItem.Kind.Tub, flavor) < needed)
            { business.lostSales++; notice = business.name + " lost a sale: " + TycoonCatalogSO.FlavorNames[flavor] + " is out of stock."; return; }
        }
        bool available = order.cone ? Stock(site, TycoonItem.Kind.Batter, 0) + Stock(site, TycoonItem.Kind.BatterPack, 0) > business.queue.Count(a => a.order.cone) : Stock(site, TycoonItem.Kind.Bowls, 0) + Stock(site, TycoonItem.Kind.BowlPack, 0) > business.queue.Count(a => !a.order.cone);
        for (int i = 0; i < ToppingCount; i++) if ((order.toppings & (1 << i)) != 0) available &= Stock(site, TycoonItem.Kind.Topping, i) + Stock(site, TycoonItem.Kind.ToppingPack, i) > business.queue.Count(a => (a.order.toppings & (1 << i)) != 0);
        if (!available) { business.lostSales++; notice = business.name + " lost a sale: refill packaging, batter, or toppings."; return; }
        var actor = Instantiate(catalog.customerPrefab, position, Quaternion.identity);
        actor.game = this; actor.site = site; actor.order = order;
        business.queue.Add(actor); actors.Add(actor); if (site == 2) { truck.demand[truck.routeStop]--; business.stopDemand = truck.demand[truck.routeStop]; }
    }
    public int Stock(int site, TycoonItem.Kind kind, int variant)
    {
        var items = parts.Where(p => p.site == site && p.installed).SelectMany(p => p.storage.slots.Concat(new[] { p.contents }))
            .Concat(workers.Where(w => w.site == site).SelectMany(w => w.inventory.slots));
        if (Vector3.Distance(player.transform.position, sites[site].origin.position) < 12) items = items.Concat(player.inventory.slots).Concat(new[] { player.cargo });
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
            sites[i].canopy.SetActive(!sites[i].expanded); sites[i].kiosk.SetActive(sites[i].expanded);
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
