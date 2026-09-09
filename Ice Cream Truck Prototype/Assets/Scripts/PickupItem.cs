using UnityEngine;

public class PickupItem : Interactable
{
    public enum ItemKind { Batter, Scooper, Sprinkles, Cone, Boombox, Tray }
    public ItemKind kind;
    public string displayName;
    public Collider pickupCollider;
    public Rigidbody body;
    public Transform home;
    public Vector3 heldOffset;
    public Vector3 heldRotation;
    public Transform grip;
    public bool openHandGrip;
    public Mesh handMesh;
    public GameObject placementPreviewPrefab;
    public Vector3 placementCenter, placementSize;
    public Vector3 placementRotation;
    public bool startLoose;
    public PlayerInteraction physicsOwner;
    public GameObject loadedScoop;
    public Renderer loadedScoopRenderer;
    public MeshFilter loadedScoopFilter;
    public FlavorSO LoadedFlavor { get; private set; }
    private PlayerInteraction droppedBy;
    private bool dropped;
    private Vector3 pausedVelocity, pausedAngularVelocity;

    private void Start()
    {
        if (startLoose) BeginPhysics(physicsOwner);
    }

    private void FixedUpdate()
    {
        if (!dropped) return;
        bool paused = droppedBy.day.Paused || droppedBy.day.Phase == DayManager.DayPhase.Closed;
        if (paused != body.isKinematic)
        {
            if (paused)
            {
                pausedVelocity = body.linearVelocity;
                pausedAngularVelocity = body.angularVelocity;
            }
            body.isKinematic = paused;
            if (!paused)
            {
                body.linearVelocity = pausedVelocity;
                body.angularVelocity = pausedAngularVelocity;
            }
        }
        var truck = droppedBy.truck;
        if (!paused && transform.parent == truck.transform)
            body.AddForce(truck.CargoAcceleration(body.worldCenterOfMass, body.linearVelocity), ForceMode.Acceleration);
        if (transform.parent == truck.transform && !truck.cabinBounds.Contains(truck.transform.InverseTransformPoint(body.worldCenterOfMass)))
        {
            transform.SetParent(null, true);
            if (!paused) body.linearVelocity += truck.Velocity + Vector3.Cross(truck.AngularVelocity, body.worldCenterOfMass - truck.transform.position);
        }
    }
    public override string Prompt(PlayerInteraction player)
    {
        return player.Held == null ? "Click to pick up " + displayName : "Put down your item first";
    }
    public override void Use(PlayerInteraction player)
    {
        if (!player.PickUp(this)) player.Notify("Put down your item first", true);
    }
    public virtual void OnPickedUp() { }
    public void StopPhysics()
    {
        dropped = false;
        body.isKinematic = true;
        body.interpolation = RigidbodyInterpolation.None;
    }
    public void Drop(PlayerInteraction player)
    {
        player.Release();
        BeginPhysics(player);
        player.Play(player.pickupSound);
    }
    private void BeginPhysics(PlayerInteraction player)
    {
        droppedBy = player;
        dropped = true;
        var truck = player.truck;
        if (truck.cabinBounds.Contains(truck.transform.InverseTransformPoint(pickupCollider.bounds.center)))
            transform.SetParent(truck.transform, true);
        body.position = transform.position;
        body.rotation = transform.rotation;
        body.isKinematic = false;
        body.interpolation = RigidbodyInterpolation.Interpolate;
        body.linearVelocity = Vector3.zero;
        body.angularVelocity = Vector3.zero;
        Physics.IgnoreCollision(pickupCollider, player.truck.player.controller, true);
    }
    public void PreviewScoop(FlavorSO flavor, float progress)
    {
        flavor.ApplyToScoop(loadedScoopFilter, loadedScoopRenderer);
        loadedScoop.transform.localScale = Vector3.one * Mathf.Pow(Mathf.Clamp01(progress), 1f / 3f);
        loadedScoop.SetActive(progress > 0);
    }
    public void LoadScoop(FlavorSO flavor)
    {
        LoadedFlavor = flavor;
        loadedScoop.transform.localScale = Vector3.one;
        flavor.ApplyToScoop(loadedScoopFilter, loadedScoopRenderer);
        loadedScoop.SetActive(true);
    }
    public void EmptyScoop()
    {
        LoadedFlavor = null;
        loadedScoop.SetActive(false);
    }
}
