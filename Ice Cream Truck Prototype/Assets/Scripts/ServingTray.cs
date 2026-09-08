using System.Collections.Generic;
using UnityEngine;

public class ServingTray : PickupItem
{
    public Transform[] slots;
    public List<IceCreamCone> Cones { get; private set; } = new List<IceCreamCone>();
    public override string Prompt(PlayerInteraction player) => "Click to carry tray or load a finished cone";
    public override void Use(PlayerInteraction player)
    {
        if (player.Held is IceCreamCone cone)
        {
            if (Cones.Count >= slots.Length) { player.Notify("The tray is full", true); return; }
            player.Release();
            cone.Holder = null;
            Cones.Add(cone);
            Arrange();
            player.Play(player.pickupSound);
        }
        else base.Use(player);
    }
    public IceCreamCone Match(RouteCustomer customer)
    {
        foreach (var cone in Cones) if (customer.Matches(cone)) return cone;
        return null;
    }
    public void Serve(IceCreamCone cone)
    {
        Cones.Remove(cone);
        Destroy(cone.gameObject);
        Arrange();
    }
    public void Store(IceCreamCone cone)
    {
        Cones.Add(cone);
        Arrange();
    }
    private void Arrange()
    {
        for (int i = 0; i < Cones.Count; i++)
        {
            var cone = Cones[i];
            cone.transform.SetParent(slots[i], false);
            cone.transform.localPosition = Vector3.zero;
            cone.transform.localRotation = Quaternion.identity;
            cone.pickupCollider.enabled = false;
        }
    }
    public void Empty()
    {
        foreach (var cone in Cones) Destroy(cone.gameObject);
        Cones.Clear();
    }
}
