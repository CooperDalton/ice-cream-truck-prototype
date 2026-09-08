using UnityEngine;

public class ConeHolder : Interactable
{
    public Transform socket;
    public IceCreamCone Occupant { get; set; }
    public override string Prompt(PlayerInteraction player)
    {
        return Occupant != null ? Occupant.Prompt(player) : "Click to place a cone in the holder";
    }
    public override void Use(PlayerInteraction player)
    {
        if (Occupant != null) { Occupant.Use(player); return; }
        if (player.Held is IceCreamCone cone)
        {
            player.Release();
            cone.transform.SetParent(socket.parent, true);
            cone.transform.SetPositionAndRotation(socket.position, socket.rotation);
            Occupant = cone;
            cone.Holder = this;
            player.Play(player.pickupSound);
        }
        else player.Notify("Hold a cone to place it here", true);
    }
    public override bool CanGesture(PlayerInteraction player) => Occupant != null && Occupant.CanGesture(player);
    public override float Progress => Occupant == null ? 0 : Occupant.Progress;
    public override void Gesture(PlayerInteraction player, Vector2 delta, float dt)
    {
        Occupant.Gesture(player, delta, dt);
    }
    public override void StopGesture()
    {
        if (Occupant != null) Occupant.StopGesture();
    }
}
