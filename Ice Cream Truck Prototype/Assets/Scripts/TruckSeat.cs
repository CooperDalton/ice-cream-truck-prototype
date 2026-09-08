using UnityEngine;

public class TruckSeat : Interactable
{
    public TruckController truck;
    public float reach = 2;
    public override string Prompt(PlayerInteraction player) => "E to sit in the driver's seat";
    public override void Use(PlayerInteraction player)
    {
        truck.ToggleDriving();
    }
}
