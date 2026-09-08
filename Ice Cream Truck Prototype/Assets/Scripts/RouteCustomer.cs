using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;

public class RouteCustomer : Interactable
{
    public Transform appearance;
    public Renderer shirt;
    public Collider interactionCollider;
    public GameObject servingStep;
    public Transform bubble;
    public GameObject orderPanel, sprinkles;
    public Image[] scoopPictures;
    public Image patience;
    public RouteHotspot Hotspot { get; private set; }
    public RouteHotspot.Order Order { get; private set; }
    public bool Served { get; private set; }
    public bool Arrived { get; private set; }
    public bool Child { get; private set; }
    public bool Available => !Served && Hotspot.Available;
    private int index;
    private Vector3 home, destination;
    private float repath;
    private List<Vector3> path;
    private int pathIndex;
    private RouteGameManager route;

    public void Initialize(RouteHotspot hotspot, RouteHotspot.Order order, int customerIndex, bool child)
    {
        Hotspot = hotspot; Order = order; route = hotspot.route; index = customerIndex; Child = child;
        home = transform.position; destination = home;
        var colors = new[] { new Color(.94f,.48f,.58f), new Color(.42f,.76f,.64f), new Color(.43f,.62f,.9f), new Color(.95f,.75f,.4f) };
        var block = new MaterialPropertyBlock(); block.SetColor("_BaseColor", colors[(int)hotspot.kind]); shirt.SetPropertyBlock(block, 0);
        for (int i = 0; i < scoopPictures.Length; i++)
        {
            scoopPictures[i].gameObject.SetActive(i < order.recipe.Length);
            if (i < order.recipe.Length) { scoopPictures[i].sprite = order.recipe[i].orderPicture; scoopPictures[i].color = Color.white; }
        }
        sprinkles.SetActive(order.sprinkles);
        servingStep.SetActive(false);
        orderPanel.SetActive(false);
    }
    private void Update()
    {
        if (route.day.Paused) return;
        appearance.gameObject.SetActive(Available);
        interactionCollider.enabled = Available;
        if (!Available) { orderPanel.SetActive(false); servingStep.SetActive(false); return; }
        Advance(Time.deltaTime);
    }
    public void Advance(float dt)
    {
        int queueIndex = route.WindowQueue.IndexOf(this);
        Vector3 target = home;
        if (queueIndex >= 0) target = route.queuePoints[queueIndex].position;
        else if (Hotspot.kind == RouteHotspot.CrowdKind.Playground)
        {
            Vector3 center = !route.truck.InsideTruck && Vector3.Distance(route.player.transform.position, home) < 9 ? route.player.transform.position : home;
            target = center + new Vector3(Mathf.Cos(route.Clock * .35f + index * 2), 0, Mathf.Sin(route.Clock * .35f + index * 2)) * 2.2f;
        }
        target.y = 0;
        repath -= dt;
        if (repath <= 0)
        {
            destination = target; path = route.navigation.Path(transform.position, target); pathIndex = 0; repath = .7f;
        }
        if (path != null && pathIndex < path.Count)
        {
            Vector3 next = path[pathIndex];
            Vector3 direction = next - transform.position; direction.y = 0;
            if (direction.magnitude < .08f) pathIndex++;
            else if (route.navigation.ClearSegment(transform.position, next))
            {
                transform.position = Vector3.MoveTowards(transform.position, next, dt * (Child ? 2 : 1.7f));
                transform.rotation = Quaternion.Slerp(transform.rotation, Quaternion.LookRotation(direction), dt * 7);
            }
        }
        Arrived = Vector3.Distance(transform.position, destination) < .4f;
        bool atWindow = queueIndex == 0 && Arrived;
        appearance.localPosition = Vector3.up * (Child && atWindow ? .4f : 0);
        servingStep.SetActive(Child && atWindow);
        bool show = route.truck.InsideTruck ? atWindow : Vector3.Distance(route.player.transform.position, transform.position) < 13;
        orderPanel.SetActive(show);
        bubble.localPosition = Vector3.up * (Child ? 2.35f : 2.65f);
        bubble.rotation = route.player.view.transform.rotation;
        if (show && Order.sprinkles) sprinkles.transform.position = scoopPictures[Order.recipe.Length - 1].transform.TransformPoint(new Vector3(0, 20, 0));
        patience.fillAmount = Mathf.InverseLerp(Hotspot.closesAt, Hotspot.opensAt, route.Clock);
    }
    public bool Matches(IceCreamCone cone)
    {
        if (cone.Flavors.Count != Order.recipe.Length || cone.HasSprinkles != Order.sprinkles) return false;
        for (int i = 0; i < Order.recipe.Length; i++) if (cone.Flavors[i] != Order.recipe[i]) return false;
        return true;
    }
    public override string Prompt(PlayerInteraction player) => "Click to serve " + Order.Label;
    public override void Use(PlayerInteraction player)
    {
        if (!Available || (route.truck.InsideTruck && (route.WindowQueue.Count == 0 || route.WindowQueue[0] != this || !Arrived))) return;
        IceCreamCone cone = player.Held as IceCreamCone;
        var tray = player.Held as ServingTray;
        if (tray != null) cone = tray.Match(this);
        if (cone == null || !Matches(cone)) { player.Notify("This customer wants " + Order.Label, true); return; }
        if (tray != null) tray.Serve(cone); else Destroy(player.Release().gameObject);
        Served = true;
        route.CompleteSale(this, Order.price);
        player.Play(player.saleSound);
        orderPanel.SetActive(false); appearance.gameObject.SetActive(false); interactionCollider.enabled = false;
    }
}
