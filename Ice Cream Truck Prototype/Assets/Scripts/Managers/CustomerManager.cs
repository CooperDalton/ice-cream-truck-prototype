using System.Collections.Generic;
using UnityEngine;

public class CustomerManager : MonoBehaviour
{
    public PrototypeSettingsSO settings;
    public DayManager day;
    public Customer[] customerPrefabs;
    public FlavorSO[] flavors;
    public Transform spawnPoint, exitPoint, serviceLookPoint;
    public Transform[] queuePoints;
    public TruckController truck;
    public WorldGenerator world;
    public Boombox boombox;
    public Camera view;
    public List<Customer> Queue { get; private set; } = new List<Customer>();
    public List<Customer> Residents { get; private set; } = new List<Customer>();
    public Customer Front => Queue.Count == 0 ? null : Queue[0];
    public bool ManualInput { get; set; }
    float attractionTimer;
    int totalSpawned;
    void Start()
    {
        var random = new System.Random(world.Seed ^ 7521);
        for (int area = 0; area < world.Hotspots.Count; area++)
        for (int i = 0; i < settings.residentsPerHotspot; i++)
        {
            var hotspot = world.Hotspots[area];
            Vector3 point = hotspot.position + new Vector3((i % 3 - 1) * 2.5f, 0, i / 3 * 1.5f);
            if (!world.Walkable(point)) continue;
            bool child = random.NextDouble() < (hotspot.park ? settings.parkChildChance : settings.residentialChildChance);
            int variant = (child ? 1 : 0) + (random.Next(2) * 2);
            var resident = Instantiate(customerPrefabs[variant], point, Quaternion.Euler(0, random.Next(360), 0));
            resident.Initialize(this, new List<FlavorSO>(), false);
            resident.SetHome(point, child, hotspot.park, area);
            Residents.Add(resident);
        }
        attractionTimer = settings.firstCustomerDelay;
    }
    void Update()
    {
        if (ManualInput || !day.CanPlay) return;
        attractionTimer -= Time.deltaTime;
        if (attractionTimer > 0) return;
        attractionTimer = settings.attractionCheckInterval;
        AttractNearby();
    }
    public bool InAttractionRange(Vector3 point)
    {
        if (!truck.ServiceOpen) return false;
        return Vector3.Distance(point, serviceLookPoint.position) <= settings.truckAttractionRadius ||
            (boombox.Playing && Vector3.Distance(point, boombox.transform.position) <= settings.boomboxAttractionRadius);
    }
    public void AttractNearby()
    {
        if (!day.CanPlay || !truck.ServiceOpen) return;
        foreach (var resident in Residents)
        {
            if (Queue.Count >= queuePoints.Length || !world.Walkable(queuePoints[Queue.Count].position)) break;
            if (resident.Idle && !resident.ServedToday && resident.Cooldown <= 0 && InAttractionRange(resident.transform.position)) JoinQueue(resident);
        }
    }
    public Customer SpawnCustomer()
    {
        foreach (var resident in Residents) if (resident.Idle && JoinQueue(resident)) return resident;
        return null;
    }
    bool JoinQueue(Customer customer)
    {
        if (!day.CanPlay || !truck.ServiceOpen || Queue.Count >= queuePoints.Length || customer.ServedToday || !customer.Idle || customer.Cooldown > 0) return false;
        var path = world.Path(customer.transform.position, queuePoints[Queue.Count].position);
        if (path == null) return false;
        var order = new List<FlavorSO>();
        int count = totalSpawned == 0 ? 1 : Random.Range(1, settings.maximumScoops + 1);
        for (int i = 0; i < count; i++) order.Add(totalSpawned == 0 ? flavors[0] : flavors[Random.Range(0, flavors.Length)]);
        customer.Initialize(this, order, totalSpawned > 0 && Random.value < settings.sprinkleOrderChance);
        Queue.Add(customer);
        customer.Follow(path);
        totalSpawned++;
        return true;
    }
    public void Served(Customer customer)
    {
        Queue.Remove(customer); customer.Leave(served: true); RepositionQueue();
        if (Residents.TrueForAll(resident => resident.HomeArea != customer.HomeArea || resident.ServedToday))
            truck.player.interaction.hud.ShowMessage("Everyone here has been served. Drive to another neighborhood!");
    }
    public void Lose(Customer customer)
    {
        day.RecordLostCustomer(); Queue.Remove(customer); customer.Leave(); RepositionQueue();
    }
    public void ReleaseQueue()
    {
        foreach (var customer in Queue) customer.Leave();
        Queue.Clear();
    }
    void RepositionQueue()
    {
        for (int i = 0; i < Queue.Count; i++) Queue[i].SetDestination(queuePoints[i].position);
    }
}
