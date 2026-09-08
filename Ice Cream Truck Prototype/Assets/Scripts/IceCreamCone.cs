using System.Collections.Generic;
using UnityEngine;

public class IceCreamCone : PickupItem
{
    public PrototypeSettingsSO settings;
    public GameObject[] scoopVisuals;
    public Renderer[] scoopRenderers;
    public MeshFilter[] scoopFilters;
    public GameObject[] toppingVisuals;
    public MeshCollider shapeCollider;
    [Tooltip("Collision meshes for an empty cone, then one, two and three scoops.")]
    public Mesh[] collisionShapes;
    public List<FlavorSO> Flavors { get; private set; } = new List<FlavorSO>();
    public bool HasSprinkles { get; private set; }
    public ConeHolder Holder { get; set; }
    private float sprinkles;
    public override float Progress => sprinkles;
    public override string Prompt(PlayerInteraction player)
    {
        if (player.Held == null) return "Click to pick up cone • " + Flavors.Count + "/" + settings.maximumScoops + " scoops";
        if (player.Held.kind == ItemKind.Scooper) return Flavors.Count >= settings.maximumScoops ? "Cone is full" : "Click to add " + (player.Held.LoadedFlavor == null ? "a scoop • Scoop a flavor first" : player.Held.LoadedFlavor.displayName);
        if (player.Held.kind == ItemKind.Sprinkles) return HasSprinkles ? "Sprinkles added" : "Hold click and shake mouse up/down";
        return "Put down your item first";
    }
    public override void Use(PlayerInteraction player)
    {
        if (player.Held == null) { player.PickUp(this); return; }
        if (player.Held.kind == ItemKind.Scooper && player.Held.LoadedFlavor != null && Flavors.Count < settings.maximumScoops)
        {
            int index = Flavors.Count;
            Flavors.Add(player.Held.LoadedFlavor);
            player.Held.LoadedFlavor.ApplyToScoop(scoopFilters[index], scoopRenderers[index]);
            scoopVisuals[index].SetActive(true);
            shapeCollider.sharedMesh = collisionShapes[Flavors.Count];
            HasSprinkles = false;
            foreach (var topping in toppingVisuals) topping.SetActive(false);
            player.Held.EmptyScoop();
            player.Play(player.actionSound);
        }
        else if (!CanGesture(player)) player.Notify(Prompt(player), true);
    }
    public override bool CanGesture(PlayerInteraction player)
    {
        return player.Held != null && player.Held.kind == ItemKind.Sprinkles && Flavors.Count > 0 && !HasSprinkles && (player.stock == null || player.stock.Has(RouteStock.Ingredient.Sprinkles));
    }
    public override void Gesture(PlayerInteraction player, Vector2 delta, float dt)
    {
        if (!CanGesture(player)) return;
        sprinkles += Mathf.Min(Mathf.Abs(delta.y) / settings.sprinkleMouseDistance, dt / settings.minimumSprinkleSeconds);
        if (delta.sqrMagnitude > 1) player.GestureSound(player.sprinkleSound);
        if (sprinkles >= 1)
        {
            if (player.stock != null) player.stock.Consume(RouteStock.Ingredient.Sprinkles);
            HasSprinkles = true;
            toppingVisuals[Flavors.Count - 1].SetActive(true);
            player.Notify("Sprinkles added");
            sprinkles = 0;
        }
    }
    public override void StopGesture()
    {
        sprinkles = 0;
    }
    public void Restore(FlavorSO[] flavors, bool toppings)
    {
        Flavors.Clear(); Flavors.AddRange(flavors); HasSprinkles = toppings;
        for (int i = 0; i < scoopVisuals.Length; i++)
        {
            scoopVisuals[i].SetActive(i < flavors.Length);
            if (i < flavors.Length) flavors[i].ApplyToScoop(scoopFilters[i], scoopRenderers[i]);
            toppingVisuals[i].SetActive(toppings && i == flavors.Length - 1);
        }
        shapeCollider.sharedMesh = collisionShapes[flavors.Length];
    }
    public override void OnPickedUp()
    {
        if (Holder != null) Holder.Occupant = null;
        Holder = null;
    }
    public override void ReturnHome(PlayerInteraction player)
    {
        player.Notify("Click an empty holder or counter to place the cone");
    }
}
