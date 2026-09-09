using System.Collections.Generic;
using UnityEngine;

public class Customer : Interactable
{
    public Transform appearance;
    public Renderer shirt;
    public Collider interactionCollider;
    public GameObject servingStep;
    [SerializeField] private float childServingLift = .4f;
    public List<FlavorSO> Order { get; private set; } = new List<FlavorSO>();
    public bool WantsSprinkles { get; private set; }
    public float Patience { get; private set; }
    public bool Leaving { get; private set; }
    public bool Arrived { get; private set; }
    public CustomerManager Manager { get; private set; }
    public bool Idle { get; private set; } = true;
    public bool IsChild { get; private set; }
    public bool ParkResident { get; private set; }
    public bool ServedToday { get; private set; }
    public int HomeArea { get; private set; }
    public float Cooldown { get; private set; }
    public Vector3 Home { get; private set; }
    private List<Vector3> path;
    private int pathIndex;
    private float repathTimer;
    private Vector3 destination;
    private Color shirtColor;
    private float walkTime;
    private MaterialPropertyBlock block;
    public void Initialize(CustomerManager manager, List<FlavorSO> order, bool sprinkles)
    {
        block = new MaterialPropertyBlock();
        Manager = manager;
        Order = order;
        WantsSprinkles = sprinkles;
        Patience = manager.settings.customerPatience;
        Leaving = false; interactionCollider.enabled = true;
        shirtColor = Random.ColorHSV(0,1,.35f,.65f,.65f,.95f);
        block.SetColor("_BaseColor",shirtColor);
        shirt.SetPropertyBlock(block, 0);
    }
    public void SetHome(Vector3 point, bool child, bool park, int area)
    {
        Home = point; IsChild = child; ParkResident = park; Idle = true;
        HomeArea = area;
    }
    public void Follow(List<Vector3> route)
    {
        path = route; pathIndex = 0; destination = route[route.Count - 1];
        Arrived = false; Idle = false;
    }
    public void SetDestination(Vector3 point)
    {
        destination = point;
        var route = Manager.world.Path(transform.position, point);
        if (route != null) Follow(route);
        else { path = null; Arrived = false; }
    }
    private void Update()
    {
        if (Manager.day.CanPlay) Advance(Time.deltaTime);
    }
    public void Advance(float dt)
    {
        if (!Manager.day.CanPlay) return;
        Cooldown = Mathf.Max(0, Cooldown - dt);
        if (Idle) return;
        repathTimer -= dt;
        if (path == null)
        {
            if (repathTimer <= 0) { SetDestination(destination); repathTimer = 1; }
            return;
        }
        float remaining = (Leaving ? Manager.settings.customerWalkSpeed : Manager.settings.customerRunSpeed) * dt;
        while (pathIndex < path.Count && remaining > 0)
        {
            var next = path[pathIndex];
            Vector3 offset = next - transform.position;
            float distance = offset.magnitude;
            if (distance < .04f) { pathIndex++; continue; }
            if (!Manager.world.ClearSegment(transform.position, next))
            {
                if (repathTimer <= 0) { SetDestination(destination); repathTimer = 1; }
                break;
            }
            transform.position = Vector3.MoveTowards(transform.position, next, remaining);
            transform.rotation = Quaternion.Slerp(transform.rotation, Quaternion.LookRotation(offset), Mathf.Min(1, dt * 6));
            remaining -= distance;
            if (remaining >= 0) pathIndex++;
        }
        if (pathIndex >= path.Count)
        {
            appearance.localPosition = Vector3.up * (IsChild && !Leaving ? childServingLift : 0);
            servingStep.SetActive(IsChild && !Leaving && Manager.Front == this); Arrived = true;
            if (Leaving) { Leaving = false; Idle = true; Cooldown = Manager.settings.repeatCustomerDelay; interactionCollider.enabled = true; return; }
            Vector3 look = Manager.serviceLookPoint.position - transform.position; look.y = 0;
            if (look.sqrMagnitude > .001f) transform.rotation = Quaternion.Slerp(transform.rotation, Quaternion.LookRotation(look), Mathf.Min(1, dt * 6));
        }
        else
        {
            servingStep.SetActive(false);
            walkTime += dt * 8;
            appearance.localPosition = Vector3.up * (Mathf.Abs(Mathf.Sin(walkTime)) * .035f);
        }
        if (!Leaving)
        {
            Patience -= dt;
            if (Patience <= 0) Manager.Lose(this);
        }
    }
    public string OrderDescription()
    {
        var names = new List<string>();
        foreach (var flavor in Order) names.Add(flavor.displayName);
        return string.Join(" + ", names) + (WantsSprinkles ? "\nWith sprinkles" : "\nNo sprinkles");
    }
    public bool Matches(IceCreamCone cone)
    {
        if (cone.Flavors.Count != Order.Count || cone.HasSprinkles != WantsSprinkles) return false;
        for (int i=0; i<Order.Count; i++) if (cone.Flavors[i] != Order[i]) return false;
        return true;
    }
    public override string Prompt(PlayerInteraction player)
    {
        if (ServedToday) return "Thanks for the ice cream! See you tomorrow.";
        if (Idle) return "Park nearby or play the boombox to attract customers";
        if (Leaving) return "Thanks!";
        if (Manager.Front != this || !Arrived) return "Waiting in line";
        return "Click to serve • " + OrderDescription().Replace("\n", " • ");
    }
    public override void Use(PlayerInteraction player)
    {
        if (!Manager.truck.ServiceOpen || Leaving || Manager.Front != this || !Arrived) return;
        if (!(player.Held is IceCreamCone cone)) { player.Notify("Hand over a finished cone", true); return; }
        if (!Matches(cone)) { player.Notify("That doesn't match. Check flavors, scoop order, and sprinkles.", true); return; }
        int price = Manager.settings.conePrice + Order.Count * Manager.settings.scoopPrice + (WantsSprinkles ? Manager.settings.sprinklePrice : 0);
        if (!Manager.day.RecordSale(price)) return;
        Destroy(player.Release().gameObject);
        player.Play(player.saleSound);
        player.hud.ShowMessage("Thank you! +$" + price);
        Manager.Served(this);
    }
    public void Leave(bool served = false)
    {
        ServedToday |= served;
        Leaving = true;
        servingStep.SetActive(false);
        interactionCollider.enabled = false;
        SetDestination(Home);
        Highlight(false);
    }
}
