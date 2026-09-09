using UnityEngine;

public class PlacementSurface : Interactable
{
    public override string Prompt(PlayerInteraction player)
    {
        return player.Held == null ? "Preparation counter" : "Q to place " + player.Held.displayName;
    }
    public override void Use(PlayerInteraction player)
    {
        if (player.Held != null) player.TryPlaceHeld();
    }
}
