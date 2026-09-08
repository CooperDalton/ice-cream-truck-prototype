using UnityEngine;

public class PickupItem : Interactable
{
    public enum ItemKind { Batter, Scooper, Sprinkles, Cone, Boombox, Tray }
    public ItemKind kind;
    public string displayName;
    public Collider pickupCollider;
    public Transform home;
    public Vector3 heldOffset;
    public Vector3 heldRotation;
    public Transform grip;
    public bool openHandGrip;
    public Mesh handMesh;
    public GameObject loadedScoop;
    public Renderer loadedScoopRenderer;
    public MeshFilter loadedScoopFilter;
    public FlavorSO LoadedFlavor { get; private set; }
    public override string Prompt(PlayerInteraction player)
    {
        return player.Held == null ? "Click to pick up " + displayName : "Put down your item first";
    }
    public override void Use(PlayerInteraction player)
    {
        if (!player.PickUp(this)) player.Notify("Put down your item first", true);
    }
    public virtual void OnPickedUp() { }
    public virtual void ReturnHome(PlayerInteraction player)
    {
        if (home == null)
        {
            player.Notify("Place the cone in a holder or on the counter", true);
            return;
        }
        player.Release();
        transform.SetParent(home.parent, true);
        transform.SetPositionAndRotation(home.position, home.rotation);
        player.Play(player.pickupSound);
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
