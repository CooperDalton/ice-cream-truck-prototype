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
            if (!TryHomePosition(hotspot.position, area, random, out Vector3 point)) continue;
            bool child = random.NextDouble() < (hotspot.park ? settings.parkChildChance : settings.residentialChildChance);
            int variant = (child ? 1 : 0) + (random.Next(2) * 2);
            var resident = Instantiate(customerPrefabs[variant], point, Quaternion.Euler(0, random.Next(360), 0));
            resident.Initialize(this, new List<FlavorSO>(), false);
            resident.SetHome(point, child, hotspot.park, area);
            Residents.Add(resident);
        }
        attractionTimer = settings.firstCustomerDelay;
    }
    private bool TryHomePosition(Vector3 center, int area, System.Random random, out Vector3 point)
    {
        for (int attempt = 0; attempt < 80; attempt++)
        {
            float angle = (float)random.NextDouble() * Mathf.PI * 2;
            float radius = Mathf.Sqrt((float)random.NextDouble()) * settings.residentSpreadRadius;
            Vector3 candidate = center + new Vector3(Mathf.Cos(angle), 0, Mathf.Sin(angle)) * radius;
            if (!world.Walkable(candidate) || Residents.Exists(c => c.HomeArea == area && (c.Home - candidate).sqrMagnitude < 9)) continue;
            if (world.Path(candidate, center) == null) continue;
            point = candidate;
            return true;
        }
        point = center;
        return false;
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
        return Vector3.Distance(point, serviceLookPoint.position) <= settings.truckAttractionRadius ||
            (boombox.Playing && Vector3.Distance(point, boombox.transform.position) <= settings.boomboxAttractionRadius);
    }
    public void AttractNearby()
    {
        if (!day.CanPlay) return;
        if (!truck.ServiceOpen && Queue.Count > 0) ReleaseQueue(followVan: true);
        for (int i = 0; i < Residents.Count; i++)
        {
            var resident = Residents[i];
            if (resident.ServedToday || resident.Leaving || resident.Cooldown > 0 || !resident.Idle && !resident.Chasing) continue;
            float vanDistance = Vector3.Distance(resident.transform.position, serviceLookPoint.position);
            if (truck.ServiceOpen && vanDistance <= settings.customerQueueRadius && JoinQueue(resident)) continue;
            bool vanNearby = vanDistance <= settings.truckAttractionRadius * (resident.Chasing && resident.FollowingVan ? 2 : 1);
            bool musicNearby = boombox.Playing && Vector3.Distance(resident.transform.position, boombox.transform.position) <= settings.boomboxAttractionRadius;
            if (vanNearby) resident.Chase(queuePoints[i % queuePoints.Length].position, van: true);
            else if (musicNearby)
            {
                float angle = i * 2.4f;
                Vector3 target = boombox.transform.position + new Vector3(Mathf.Cos(angle), 0, Mathf.Sin(angle)) * 3;
                target.y = 0;
                resident.Chase(target, van: false);
            }
            else if (resident.Chasing) resident.Leave();
        }
    }
    public Customer SpawnCustomer()
    {
        foreach (var resident in Residents) if (resident.Idle && JoinQueue(resident)) return resident;
        return null;
    }
    bool JoinQueue(Customer customer)
    {
        if (!day.CanPlay || !truck.ServiceOpen || Queue.Count >= queuePoints.Length || customer.ServedToday || !customer.Idle && !customer.Chasing || customer.Cooldown > 0) return false;
        if (!world.Walkable(queuePoints[Queue.Count].position)) return false;
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
    public void ReleaseQueue(bool followVan = false)
    {
        for (int i = 0; i < Queue.Count; i++)
        {
            if (followVan) Queue[i].Chase(queuePoints[i].position, van: true);
            else Queue[i].Leave();
        }
        Queue.Clear();
    }
    void RepositionQueue()
    {
        for (int i = 0; i < Queue.Count; i++) Queue[i].SetDestination(queuePoints[i].position);
    }
}
