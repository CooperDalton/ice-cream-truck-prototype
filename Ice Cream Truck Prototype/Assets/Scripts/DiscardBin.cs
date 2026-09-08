using UnityEngine;

public class DiscardBin : Interactable
{
    public override string Prompt(PlayerInteraction player)
    {
        return "Click to discard a cone or empty the scooper";
    }
    public override void Use(PlayerInteraction player)
    {
        if (player.Held is IceCreamCone)
        {
            Destroy(player.Release().gameObject);
            player.Notify("Cone discarded");
        }
        else if (player.Held != null && player.Held.kind == PickupItem.ItemKind.Scooper)
        {
            player.Held.EmptyScoop();
            player.Notify("Scooper emptied");
        }
        else player.Notify("Tools stay in the truck", true);
    }
}
