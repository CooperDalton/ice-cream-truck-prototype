using UnityEngine;

public class IceCreamTub : Interactable
{
    public PrototypeSettingsSO settings;
    public FlavorSO flavor;
    public Transform scoopTop, scoopBottom;
    [SerializeField] private float strokeMouseDistance = 180;
    private float progress;
    private float stroke = .5f;
    private PickupItem scooper;
    public Vector3 ScoopPosition => Vector3.Lerp(scoopBottom.position, scoopTop.position, stroke);
    public Quaternion ScoopRotation => scoopTop.rotation;
    public override float Progress => progress;
    public override string Prompt(PlayerInteraction player)
    {
        if (player.stock != null && !player.stock.HasFlavor(flavor)) return flavor.displayName + " is out of stock. Buy supplies on the map.";
        if (player.Held == null || player.Held.kind != PickupItem.ItemKind.Scooper) return flavor.displayName + " • Pick up the scooper";
        return player.Held.LoadedFlavor != null ? "Place your scoop on a cone first" : flavor.displayName + " • Hold click and move mouse up/down";
    }
    public override void Use(PlayerInteraction player)
    {
        if (!CanGesture(player)) { player.Notify(Prompt(player), true); return; }
        scooper = player.Held;
        stroke = .5f;
        progress = 0;
    }
    public override bool CanGesture(PlayerInteraction player)
    {
        return player.Held != null && player.Held.kind == PickupItem.ItemKind.Scooper && player.Held.LoadedFlavor == null && (player.stock == null || player.stock.HasFlavor(flavor));
    }
    public override void Gesture(PlayerInteraction player, Vector2 delta, float dt)
    {
        if (!CanGesture(player)) return;
        float previous = stroke;
        stroke = Mathf.Clamp01(stroke + delta.y / strokeMouseDistance);
        float travel = Mathf.Abs(stroke - previous) * strokeMouseDistance;
        progress += Mathf.Min(travel / settings.scoopMouseDistance, dt / settings.minimumScoopSeconds);
        scooper.PreviewScoop(flavor, progress);
        if (delta.sqrMagnitude > 1) player.GestureSound(player.scoopSound);
        if (progress >= 1)
        {
            if (player.stock != null) player.stock.ConsumeFlavor(flavor);
            player.Held.LoadScoop(flavor);
            player.Notify(flavor.displayName + " scoop ready");
            progress = 0;
        }
    }
    public override void StopGesture()
    {
        progress = 0;
        if (scooper != null && scooper.LoadedFlavor == null) scooper.EmptyScoop();
        scooper = null;
    }
}
