using System;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.SceneManagement;

[DefaultExecutionOrder(-100)]
public class RouteGameManager : MonoBehaviour
{
    public enum RoutePhase { Planning, Running, Results }
    public enum RouteControl { None, Slow, Stop }
    [Serializable] public class RoutePoint
    {
        public string label;
        public float distance;
        public RouteControl control;
        [NonSerialized] public bool used;
    }
    public class Delivery
    {
        public int ingredient, quantity, stop;
        public float readyAt;
        public bool delivered;
    }
    public class SavedCone
    {
        public FlavorSO[] flavors;
        public bool sprinkles;
    }
    public DayManager day;
    public TruckController truck;
    public PlayerController player;
    public PlayerInteraction interaction;
    public RouteStock stock;
    public RouteHUD hud;
    public WorldGenerator navigation;
    public ServingTray tray;
    public WaffleMaker waffle;
    public ConeHolder[] holders;
    public Transform[] queuePoints;
    public Transform[] path;
    public RoutePoint[] points;
    public RouteHotspot[] hotspots;
    public GameObject cashPouch;
    public float cruiseSpeed = 1.5f, slowSpeed = .6f, slowRadius = 14, stopDuration = 40, deliverySeconds = 45;
    public int stopBudget = 2, slowBudget = 2;
    public RoutePhase Phase { get; private set; }
    public bool MapOpen { get; private set; } = true;
    public bool CanPlay => Phase != RoutePhase.Results && !MapOpen;
    public bool Stopped => Phase == RoutePhase.Running && StopRemaining > 0;
    public float Clock { get; private set; }
    public float Distance { get; private set; }
    public float Length { get; private set; }
    public float StopRemaining { get; private set; }
    public int CurrentStop { get; private set; } = -1;
    public int Bank { get; private set; }
    public int BankedToday { get; private set; }
    public int CarriedCash { get; private set; }
    public int Served { get; private set; }
    public int LostCash { get; private set; }
    public int LostCones { get; private set; }
    public int LostIngredients { get; private set; }
    public int WastedStock { get; set; }
    public int EmergencyStops { get; private set; }
    public int Goal => 50 + (DayNumber - 1) * 10;
    public bool LeftBehind { get; private set; }
    public bool ManualInput { get; set; }
    public List<RouteCustomer> WindowQueue { get; private set; } = new List<RouteCustomer>();
    public List<Delivery> Deliveries { get; private set; } = new List<Delivery>();
    public static int DayNumber { get; private set; } = 1;
    private static int savedBank = 75, reserve;
    private static int[] savedStock = { 4, 4, 2, 2, 2 };
    private static List<SavedCone> savedCones = new List<SavedCone>();
    private float queueTimer;
    private bool wasInside = true;

    [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.SubsystemRegistration)]
    public static void BeginRun()
    {
        DayNumber = 1; savedBank = 75; reserve = 0;
        savedStock = new[] { 4, 4, 2, 2, 2 }; savedCones.Clear();
    }
    private void Awake()
    {
        for (int i = 1; i < path.Length; i++) Length += Vector3.Distance(path[i - 1].position, path[i].position);
        Bank = savedBank; EmergencyStops = 1 + reserve;
        stock.amounts = (int[])savedStock.Clone();
        ConfigureHotspots();
    }
    private void Start()
    {
        foreach (var hotspot in hotspots) if (hotspot.gameObject.activeSelf) hotspot.Spawn();
        for (int i = 0; i < savedCones.Count; i++)
        {
            var cone = Instantiate(waffle.conePrefab);
            cone.Restore(savedCones[i].flavors, savedCones[i].sprinkles);
            if (i < holders.Length)
            {
                cone.transform.SetParent(holders[i].socket.parent, false);
                cone.transform.SetPositionAndRotation(holders[i].socket.position, holders[i].socket.rotation);
                holders[i].Occupant = cone; cone.Holder = holders[i];
            }
            else if (tray.Cones.Count < tray.slots.Length) tray.Store(cone);
            else interaction.PickUp(cone, restoring: true);
        }
        Cursor.lockState = CursorLockMode.None; Cursor.visible = true;
        cashPouch.SetActive(false);
        hud.RefreshPlan();
    }
    private void Update()
    {
        if (!ManualInput)
        {
            if (Keyboard.current.mKey.wasPressedThisFrame && !day.Paused) ToggleMap();
            if (Keyboard.current.rKey.wasPressedThisFrame && !MapOpen && !day.Paused) EmergencyStop();
            Advance(Time.deltaTime);
        }
    }
    private void ConfigureHotspots()
    {
        var random = new System.Random(830 + DayNumber);
        for (int i = 0; i < hotspots.Length; i++)
        {
            var h = hotspots[i]; h.gameObject.SetActive(DayNumber > 1 || i != 2 && i != 4);
            h.kind = (RouteHotspot.CrowdKind)(DayNumber == 1 ? i % 2 : i % (DayNumber == 2 ? 3 : 4));
            h.displayName = h.kind == RouteHotspot.CrowdKind.Birthday ? "Birthday party" : h.kind == RouteHotspot.CrowdKind.Playground ? "Playground" : h.kind == RouteHotspot.CrowdKind.Sports ? "Sports field" : "Picnic grove";
            int customerCount = 4 + Mathf.Min(3, DayNumber - 1) + random.Next(2);
            if (h.kind == RouteHotspot.CrowdKind.Sports) customerCount += 2;
            if (h.kind == RouteHotspot.CrowdKind.Picnic) customerCount -= 2;
            int groups = DayNumber == 1 ? 2 : 3;
            h.orders = new RouteHotspot.Order[groups];
            int firstFlavor = h.kind == RouteHotspot.CrowdKind.Birthday ? 2 : h.kind == RouteHotspot.CrowdKind.Playground ? (i / 2) % 2 : 0;
            for (int orderIndex = 0; orderIndex < groups; orderIndex++)
            {
                int scoops = h.kind == RouteHotspot.CrowdKind.Picnic ? (orderIndex == 1 ? 2 : 3) : h.kind == RouteHotspot.CrowdKind.Sports || DayNumber > 1 && orderIndex == 2 ? 2 : 1;
                bool sprinkles = h.kind == RouteHotspot.CrowdKind.Birthday && orderIndex == 0 || h.kind == RouteHotspot.CrowdKind.Picnic && orderIndex != 1 || DayNumber > 1 && orderIndex == 2;
                var recipe = new FlavorSO[scoops];
                for (int scoop = 0; scoop < scoops; scoop++) recipe[scoop] = stock.flavors[(firstFlavor + orderIndex + (scoop == 0 ? 0 : random.Next(stock.flavors.Length))) % stock.flavors.Length];
                int basePrice = h.kind == RouteHotspot.CrowdKind.Picnic ? 11 : h.kind == RouteHotspot.CrowdKind.Sports ? 9 : 7;
                h.orders[orderIndex] = new RouteHotspot.Order
                {
                    recipe = recipe, sprinkles = sprinkles,
                    quantity = customerCount / groups + (orderIndex < customerCount % groups ? 1 : 0),
                    price = basePrice + (scoops - 1) * 3 + (sprinkles ? 2 : 0)
                };
            }
            float baseTime = h.routeDistance / cruiseSpeed;
            h.opensAt = Mathf.Max(0, baseTime - (DayNumber == 1 ? 70 : 20));
            h.closesAt = baseTime + (h.kind == RouteHotspot.CrowdKind.Birthday ? 120 : h.kind == RouteHotspot.CrowdKind.Sports ? 65 : 230) + (DayNumber == 1 ? 70 : 0);
        }
    }
    public void ToggleMap()
    {
        if (Phase == RoutePhase.Results) return;
        MapOpen = !MapOpen;
        Cursor.lockState = MapOpen ? CursorLockMode.None : CursorLockMode.Locked;
        Cursor.visible = MapOpen;
        hud.RefreshPlan();
    }
    public void CyclePoint(int index)
    {
        if (Phase != RoutePhase.Planning) return;
        var old = points[index].control;
        for (int step = 1; step <= 3; step++)
        {
            var next = (RouteControl)(((int)old + step) % 3);
            if (next == RouteControl.None || Count(next) - (old == next ? 1 : 0) < (next == RouteControl.Stop ? stopBudget : slowBudget))
            { points[index].control = next; break; }
        }
        hud.RefreshPlan();
    }
    public int Count(RouteControl control)
    {
        int count = 0; foreach (var point in points) if (point.control == control) count++;
        return count;
    }
    public float ArrivalAt(float distance)
    {
        float time = distance / cruiseSpeed;
        foreach (var point in points)
        {
            if (point.control == RouteControl.Stop && point.distance < distance) time += stopDuration;
            if (point.control == RouteControl.Slow)
            {
                float overlap = Mathf.Max(0, Mathf.Min(distance, point.distance + slowRadius) - Mathf.Max(0, point.distance - slowRadius));
                time += overlap * (1 / slowSpeed - 1 / cruiseSpeed);
            }
        }
        return time;
    }
    public void StartRoute()
    {
        if (Phase != RoutePhase.Planning) return;
        if (!truck.InsideTruck) { hud.Flash("Board the truck before starting the route."); return; }
        Phase = RoutePhase.Running; MapOpen = false;
        Cursor.lockState = CursorLockMode.Locked; Cursor.visible = false;
        hud.Flash("Route started. Bank your cash before the park exit.");
        hud.RefreshPlan();
    }
    public Vector3 PositionAt(float distance)
    {
        for (int i = 1; i < path.Length; i++)
        {
            float segment = Vector3.Distance(path[i - 1].position, path[i].position);
            if (distance <= segment) return Vector3.Lerp(path[i - 1].position, path[i].position, distance / segment);
            distance -= segment;
        }
        return path[path.Length - 1].position;
    }
    public void Advance(float dt)
    {
        if (Phase != RoutePhase.Running || day.Paused) return;
        Clock += dt;
        float speed = 0;
        if (StopRemaining > 0)
        {
            StopRemaining = Mathf.Max(0, StopRemaining - dt);
            if (StopRemaining == 0) { WindowQueue.Clear(); CurrentStop = -1; hud.Flash("Truck departing. Get back aboard!"); }
        }
        else
        {
            speed = cruiseSpeed;
            foreach (var point in points) if (point.control == RouteControl.Slow && Mathf.Abs(Distance - point.distance) < slowRadius) speed = slowSpeed;
            float next = Mathf.Min(Length, Distance + speed * dt);
            for (int i = 0; i < points.Length; i++)
                if (points[i].control == RouteControl.Stop && !points[i].used && points[i].distance >= Distance && points[i].distance <= next)
                {
                    next = points[i].distance; points[i].used = true; CurrentStop = i; StopRemaining = stopDuration; speed = 0;
                    ReceiveDeliveries(i); hud.Flash("Stop " + points[i].label + ": " + (int)stopDuration + " seconds to serve and return."); break;
                }
            Distance = next;
        }
        Vector3 position = PositionAt(Distance);
        Vector3 direction = PositionAt(Mathf.Min(Length, Distance + 1)) - PositionAt(Mathf.Max(0, Distance - 1));
        Quaternion rotation = Quaternion.FromToRotation(Vector3.right, direction.normalized);
        truck.FollowRoute(position, Quaternion.Slerp(truck.transform.rotation, rotation, Mathf.Min(1, dt * 5)), speed);
        bool inside = truck.InsideTruck;
        if (inside && CarriedCash > 0) BankCash();
        if (inside && !wasInside && stock.Packed > 0) stock.Unpack();
        wasInside = inside;
        queueTimer -= dt;
        if (queueTimer <= 0) { FillWindowQueue(); queueTimer = .75f; }
        if (Distance >= Length) FinishRoute();
    }
    private void FillWindowQueue()
    {
        WindowQueue.RemoveAll(c => !c.Available);
        if (!Stopped) return;
        var candidates = new List<RouteCustomer>();
        foreach (var h in hotspots) if (h.gameObject.activeSelf && h.Available && Vector3.Distance(h.transform.position, truck.transform.position) < 30)
            foreach (var customer in h.Customers) if (customer.Available && !WindowQueue.Contains(customer)) candidates.Add(customer);
        candidates.Sort((a, b) => Vector3.Distance(a.transform.position, truck.transform.position).CompareTo(Vector3.Distance(b.transform.position, truck.transform.position)));
        foreach (var customer in candidates) { if (WindowQueue.Count >= queuePoints.Length) break; WindowQueue.Add(customer); }
    }
    public void CompleteSale(RouteCustomer customer, int price)
    {
        Served++; WindowQueue.Remove(customer);
        if (truck.InsideTruck) { Bank += price; BankedToday += price; hud.Flash("$" + price + " banked at the truck."); }
        else { CarriedCash += price; cashPouch.SetActive(true); hud.Flash("Carrying $" + CarriedCash + ". Return to the truck to bank it."); }
        FillWindowQueue();
    }
    private void BankCash()
    {
        Bank += CarriedCash; BankedToday += CarriedCash;
        hud.Flash("$" + CarriedCash + " safely banked."); CarriedCash = 0; cashPouch.SetActive(false);
    }
    public bool Pay(int amount)
    {
        if (Bank < amount) { hud.Flash("Not enough banked cash."); return false; }
        Bank -= amount; return true;
    }
    public int DeliveryStop(float readyAt)
    {
        for (int i = 0; i < points.Length; i++)
            if (points[i].control == RouteControl.Stop && !points[i].used && points[i].distance > Distance && Clock + RemainingTimeTo(points[i].distance) >= readyAt) return i;
        return -1;
    }
    public float RemainingTimeTo(float targetDistance)
    {
        float time = StopRemaining + Mathf.Max(0, targetDistance - Distance) / cruiseSpeed;
        foreach (var point in points)
        {
            if (point.control == RouteControl.Stop && !point.used && point.distance >= Distance && point.distance < targetDistance) time += stopDuration;
            if (point.control == RouteControl.Slow)
            {
                float overlap = Mathf.Max(0, Mathf.Min(targetDistance, point.distance + slowRadius) - Mathf.Max(Distance, point.distance - slowRadius));
                time += overlap * (1 / slowSpeed - 1 / cruiseSpeed);
            }
        }
        return time;
    }
    public void OrderDelivery(int ingredient)
    {
        int stop = DeliveryStop(Clock + deliverySeconds);
        if (stop < 0) { hud.Flash("No planned stop after the 45-second delivery time. Bulk order unavailable."); return; }
        int price = stock.prices[ingredient] * 6 + 3;
        if (!Pay(price)) return;
        Deliveries.Add(new Delivery { ingredient = ingredient, quantity = 6, stop = stop, readyAt = Clock + deliverySeconds });
        hud.Flash("Six " + ((RouteStock.Ingredient)ingredient) + " ordered for stop " + points[stop].label + ". Overflow is lost.");
    }
    private void ReceiveDeliveries(int stop)
    {
        foreach (var delivery in Deliveries)
        {
            if (delivery.delivered || Clock < delivery.readyAt) continue;
            int added = stock.Add(delivery.ingredient, delivery.quantity);
            delivery.delivered = true;
            hud.Flash("Delivery received: " + added + "/6 stored, " + (6 - added) + " overflow lost.");
        }
    }
    public void EmergencyStop()
    {
        if (Phase != RoutePhase.Running || EmergencyStops == 0 || Stopped) return;
        EmergencyStops--; StopRemaining = 25; CurrentStop = -1;
        truck.FollowRoute(truck.transform.position, truck.transform.rotation, 0);
        hud.Flash("Emergency stop: 25 seconds. Bring the runner home.");
        FillWindowQueue();
    }
    public void FinishRoute()
    {
        if (Phase == RoutePhase.Results) return;
        LeftBehind = !truck.InsideTruck;
        if (LeftBehind)
        {
            LostCash = CarriedCash; CarriedCash = 0;
            LostIngredients = stock.Packed; Array.Clear(stock.packed, 0, stock.packed.Length);
            if (interaction.Held is IceCreamCone) { LostCones++; Destroy(interaction.Release().gameObject); }
            else if (interaction.Held == tray) { LostCones += tray.Cones.Count; tray.Empty(); }
            else if (interaction.Held != null && interaction.Held.LoadedFlavor != null) { LostIngredients++; interaction.Held.EmptyScoop(); }
        }
        else { BankCash(); stock.Unpack(); }
        savedCones.Clear();
        foreach (var holder in holders) if (holder.Occupant != null) SaveCone(holder.Occupant);
        if (truck.InsideTruck || interaction.Held != tray) foreach (var cone in tray.Cones) SaveCone(cone);
        if (!LeftBehind && interaction.Held is IceCreamCone carried) SaveCone(carried);
        savedStock = (int[])stock.amounts.Clone(); savedBank = Mathf.Max(40, Bank);
        reserve = BankedToday >= Goal && !LeftBehind ? 1 : 0;
        Phase = RoutePhase.Results; MapOpen = false; WindowQueue.Clear(); cashPouch.SetActive(false);
        truck.FollowRoute(truck.transform.position, truck.transform.rotation, 0);
        Cursor.lockState = CursorLockMode.None; Cursor.visible = true;
        hud.RefreshPlan();
    }
    private static void SaveCone(IceCreamCone cone)
    {
        savedCones.Add(new SavedCone { flavors = cone.Flavors.ToArray(), sprinkles = cone.HasSprinkles });
    }
    public void NextDay()
    {
        if (Phase != RoutePhase.Results) return;
        DayNumber++; SceneManager.LoadScene("ParkRoute");
    }
}
