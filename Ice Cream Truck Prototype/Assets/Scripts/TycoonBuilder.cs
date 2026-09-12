using System.Linq;
using UnityEngine;

public class TycoonBuilder : MonoBehaviour
{
    public TycoonGameManager game;
    public GameObject preview;
    public Renderer previewRenderer;
    public Material validMaterial, invalidMaterial;
    public float pickupProgress;
    private TycoonPart pickupTarget;
    private bool pickupConsumed;
    private TycoonPart selected, support;
    private Vector3 proposed;
    private Quaternion rotation;
    private bool valid;

    public bool CanPack(TycoonPart part, out string reason)
    {
        reason = "";
        if (part == null || part.packed || !game.sites[part.site].owned || part.kind == TycoonPart.Kind.Supplier || part.kind == TycoonPart.Kind.Plot || part.kind == TycoonPart.Kind.Bike || part.kind == TycoonPart.Kind.Truck || part.kind == TycoonPart.Kind.Sign || part.kind == TycoonPart.Kind.ServingCounter)
            return false;
        if (game.player.inventory.FreeSlot < 0) { reason = "Make room in your inventory."; return false; }
        if (!string.IsNullOrEmpty(part.claimedBy)) { reason = "Finish using this equipment first."; return false; }
        if (game.parts.Any(p => p.support == part)) { reason = "Pack the equipment on top first."; return false; }
        if (game.workers.Any(w => w.locker == part)) { reason = "Assign the employee to another locker first."; return false; }
        if (game.phase == TycoonGameManager.Phase.Trading && game.workers.Any(w => w.site == part.site && w.onDuty))
        { reason = "Wait until the employees finish their shift."; return false; }
        return true;
    }
    public void HoldPickup(TycoonPart part, bool held, float dt)
    {
        if (!held || game.Paused || game.hud.AnyPanel || game.player.vehicle != null)
        {
            pickupTarget = null; pickupProgress = 0; pickupConsumed = held; return;
        }
        if (pickupConsumed) return;
        if (pickupTarget != part) { pickupTarget = part; pickupProgress = 0; }
        if (!CanPack(part, out var reason)) { pickupProgress = 0; if (reason != "") game.notice = reason; return; }
        pickupProgress = Mathf.Clamp01(pickupProgress + dt / 1.0f);
        if (pickupProgress < 1) return;
        var item = new TycoonItem(TycoonItem.Kind.Equipment, 1, part.catalogIndex) { equipmentId = part.id };
        game.player.inventory.Add(item);
        part.transform.SetParent(null, true); part.support = null; part.installed = false; part.packed = true; part.gameObject.SetActive(false);
        pickupTarget = null; pickupProgress = 0; pickupConsumed = true;
        game.navigation.BuildNavMesh(); game.Save(); game.notice = game.catalog.Label(item) + " packed.";
    }
    public void AimPlacement(bool rotate)
    {
        var item = game.player.Held;
        if (item == null || item.kind != TycoonItem.Kind.Equipment || game.hud.AnyPanel || game.Paused)
        { selected = null; valid = false; preview.SetActive(false); return; }
        var part = game.parts.Single(p => p.id == item.equipmentId);
        if (selected != part) { selected = part; rotation = part.transform.rotation; }
        if (rotate) rotation *= Quaternion.Euler(0, 90, 0);
        valid = false; preview.SetActive(false);
        var view = game.player.view.transform;
        if (!Physics.Raycast(view.position, view.forward, out var hit, 4, Physics.DefaultRaycastLayers, QueryTriggerInteraction.Ignore))
        { game.player.prompt = "Aim at your plot to place / R rotate"; return; }
        support = part.tabletop ? hit.collider.GetComponentInParent<TycoonPart>() : null;
        var grid = support != null && (support.kind == TycoonPart.Kind.Table || support.kind == TycoonPart.Kind.ServingCounter) ? support.transform : game.sites[part.site].origin;
        float cell = part.tabletop ? .25f : .5f;
        var local = grid.InverseTransformPoint(hit.point);
        proposed = grid.TransformPoint(new Vector3(Mathf.Round(local.x / cell) * cell, part.tabletop ? .94f : 0, Mathf.Round(local.z / cell) * cell));
        valid = CanPlace(part, proposed, rotation, support, out var reason);
        preview.SetActive(true); preview.transform.SetPositionAndRotation(proposed + Vector3.up * .025f, rotation);
        preview.transform.localScale = new Vector3(part.footprint.x, .025f, part.footprint.y);
        previewRenderer.sharedMaterial = valid ? validMaterial : invalidMaterial;
        game.player.prompt = valid ? "Click to place / R rotate" : reason;
    }
    public void PlaceHeld()
    {
        if (!valid || selected == null) return;
        var part = selected;
        part.transform.SetParent(support != null ? support.transform : part.site == 2 ? game.truck.transform : null, true);
        part.transform.SetPositionAndRotation(proposed, rotation); part.support = support; part.installed = true; part.packed = false; part.gameObject.SetActive(true);
        game.player.inventory.slots[game.player.selected] = null;
        selected = null; valid = false; preview.SetActive(false);
        game.navigation.BuildNavMesh(); game.Save(); game.player.RefreshHeld(); game.notice = "Equipment placed.";
    }
    public bool CanPlace(TycoonPart part, Vector3 position, Quaternion rotation, TycoonPart support, out string reason)
    {
        reason = "";
        Vector3 size = rotation * new Vector3(part.footprint.x, 0, part.footprint.y);
        size = new Vector3(Mathf.Abs(size.x), .5f, Mathf.Abs(size.z));
        var site = game.sites[part.site]; var offset = site.origin.InverseTransformPoint(position);
        var plotSize = Quaternion.Inverse(site.origin.rotation) * rotation * new Vector3(part.footprint.x,0,part.footprint.y);
        if (!site.owned || Mathf.Abs(offset.x) + Mathf.Abs(plotSize.x) / 2 > site.plotSize.x / 2 || Mathf.Abs(offset.z) + Mathf.Abs(plotSize.z) / 2 > site.plotSize.y / 2)
        { reason = "Place within the owned plot."; return false; }
        if (part.tabletop)
        {
            if (support == null || (support.kind != TycoonPart.Kind.Table && support.kind != TycoonPart.Kind.ServingCounter) || support.site != part.site) { reason = "Choose a table at this business."; return false; }
            var relative = support.transform.InverseTransformPoint(position);
            var topSize = Quaternion.Inverse(support.transform.rotation) * rotation * new Vector3(part.footprint.x,0,part.footprint.y);
            if (Mathf.Abs(relative.x) + Mathf.Abs(topSize.x) / 2 > support.footprint.x / 2 || Mathf.Abs(relative.z) + Mathf.Abs(topSize.z) / 2 > support.footprint.y / 2) { reason = "Equipment must fit on the tabletop."; return false; }
        }
        foreach (var other in game.parts.Where(p => p != part && p != support && p.site == part.site && p.installed && p.kind != TycoonPart.Kind.Truck && p.kind != TycoonPart.Kind.Bike && p.kind != TycoonPart.Kind.Plot && p.tabletop == part.tabletop && !p.transform.IsChildOf(part.transform)))
        {
            var delta = position - other.transform.position;
            var otherSize = other.transform.rotation * new Vector3(other.footprint.x, 0, other.footprint.y);
            if (Mathf.Abs(delta.x) < (size.x + Mathf.Abs(otherSize.x)) / 2 - .01f && Mathf.Abs(delta.z) < (size.z + Mathf.Abs(otherSize.z)) / 2 - .01f)
            { reason = "These grid cells are occupied."; return false; }
        }
        return true;
    }
}
