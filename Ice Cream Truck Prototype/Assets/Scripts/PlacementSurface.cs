using UnityEngine;

public class PlacementSurface : Interactable
{
    public override string Prompt(PlayerInteraction player)
    {
        return player.Held == null ? "Preparation counter" : "Click to put down " + player.Held.displayName;
    }
    public override void Use(PlayerInteraction player)
    {
        if (player.Held == null) return;
        var item = player.Release();
        item.transform.SetParent(transform, true);
        item.transform.SetPositionAndRotation(player.HitPoint + Vector3.up * .015f, Quaternion.identity);
        player.Play(player.pickupSound);
    }
}
