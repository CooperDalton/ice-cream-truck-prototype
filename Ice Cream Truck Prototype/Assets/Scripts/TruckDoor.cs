using UnityEngine;

public class TruckDoor : Interactable
{
    public TruckController truck;
    public Transform hinge;
    public float openAngle = 105;
    public float degreesPerSecond = 180;
    public bool IsOpen { get; private set; }
    private float angle;
    private Quaternion closedRotation;

    private void Awake()
    {
        closedRotation = hinge.localRotation;
        angle = 0;
    }
    private void Update()
    {
        if (!truck.day.CanPlay) return;
        angle = Mathf.MoveTowards(angle, IsOpen ? openAngle : 0, degreesPerSecond * Time.deltaTime);
        hinge.localRotation = closedRotation * Quaternion.Euler(0, angle, 0);
    }
    public override string Prompt(PlayerInteraction player) => IsOpen ? "E to close door" : "E to open door";
    public override void Use(PlayerInteraction player)
    {
        if (!truck.automaticRoute && Mathf.Abs(truck.Speed) > .05f) return;
        IsOpen = !IsOpen;
        player.Play(player.actionSound);
    }
}
