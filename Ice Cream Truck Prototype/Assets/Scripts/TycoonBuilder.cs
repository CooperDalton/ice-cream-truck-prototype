using System.Linq;
using UnityEngine;

public class TycoonBuilder : MonoBehaviour
{
    public TycoonGameManager game;
    public GameObject preview;
    public Renderer previewRenderer, gridRenderer;
    public TycoonPart bowlPrefab;
    private TycoonItem previewItem;
    private Renderer[] ghostRenderers;
    private MaterialPropertyBlock gridProperties;
    public Material validMaterial, invalidMaterial;
    public float pickupProgress;
    private TycoonPart pickupTarget;
    private bool pickupConsumed;
    private TycoonPart selected, support;
    private Vector3 proposed;
    private Quaternion rotation;
    private bool valid;

    private void Awake()
    {
        gridProperties = new MaterialPropertyBlock();
        preview.SetActive(false); gridRenderer.gameObject.SetActive(false);
    }

    public bool CanPack(TycoonPart part, out string reason)
    {
        reason = "";
        if (part == null || part.packed || !game.sites[part.site].owned || part.kind == TycoonPart.Kind.Bowl || part.kind == TycoonPart.Kind.Supplier || part.kind == TycoonPart.Kind.Plot || part.kind == TycoonPart.Kind.Bike || part.kind == TycoonPart.Kind.Truck)
            return false;
        if (game.player.inventory.FreeSlot < 0) { reason = "Make room in your inventory."; return false; }
        if (game.parts.Any(p => (p == part || p.transform.IsChildOf(part.transform)) && !string.IsNullOrEmpty(p.claimedBy))) { reason = "Finish using this equipment first."; return false; }
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
        game.player.PickUp(item);
        foreach (var member in game.parts.Where(p => p == part || p.transform.IsChildOf(part.transform))) member.installed = false;
        part.transform.SetParent(null, true); part.support = null; part.installed = false; part.packed = true; part.gameObject.SetActive(false);
        pickupTarget = null; pickupProgress = 0; pickupConsumed = true;
        game.navigation.BuildNavMesh(); game.Save(); game.notice = game.catalog.Label(item) + " packed.";
    }
    public void AimPlacement(bool rotate)
    {
        var item = game.player.Held;
        bool bowl = item != null && (item.kind == TycoonItem.Kind.Bowls || item.kind == TycoonItem.Kind.Serving && !item.cone);
        var target = game.player.target;
        bool serving = bowl && (game.player.customerTarget != null || target != null && target.kind == TycoonPart.Kind.ServingCounter && game.sites[target.site].queue.Any(c => c.ReadyForPickup && item.Matches(c.order)));
        gridRenderer.gameObject.SetActive(false);
        if (item == null || (!bowl && item.kind != TycoonItem.Kind.Equipment) || serving || game.hud.AnyPanel || game.Paused)
        { selected = null; previewItem = null; valid = false; preview.SetActive(false); return; }
        var part = bowl ? bowlPrefab : game.parts.Single(p => p.id == item.equipmentId);
        if (selected != part || previewItem != item)
        {
            selected = part; previewItem = item; rotation = bowl ? Quaternion.identity : part.transform.rotation;
            foreach (Transform child in preview.transform) { child.gameObject.SetActive(false); Destroy(child.gameObject); }
            Instantiate(game.catalog.placementPreviews[part.catalogIndex], preview.transform);
            if (!bowl)
                foreach (var child in game.parts.Where(p => p != part && p.transform.IsChildOf(part.transform)))
                {
                    var ghost = Instantiate(game.catalog.placementPreviews[child.catalogIndex], preview.transform).transform;
                    ghost.localPosition = part.transform.InverseTransformPoint(child.transform.position);
                    ghost.localRotation = Quaternion.Inverse(part.transform.rotation) * child.transform.rotation;
                }
            ghostRenderers = preview.GetComponentsInChildren<Renderer>(true).Where(r => r.gameObject.activeSelf).ToArray();
        }
        if (rotate) rotation *= Quaternion.Euler(0, 90, 0);
        valid = false; preview.SetActive(false); support = null;
        var view = game.player.view.transform;
        if (!Physics.Raycast(view.position, view.forward, out var hit, 4, Physics.DefaultRaycastLayers, QueryTriggerInteraction.Ignore))
        { game.player.prompt = bowl ? "Aim at a table to place a bowl" : "Aim at a surface to place / R rotate"; return; }
        var hitPart = hit.collider.GetComponentInParent<TycoonPart>();
        if (part.tabletop && hitPart != null)
        {
            var surface = hitPart.TableSurface ? hitPart : hitPart.support;
            if (surface != null && surface.TableSurface && surface.installed) support = surface;
        }
        int siteIndex = bowl && support != null ? support.site : part.site;
        var site = game.sites[siteIndex];
        var grid = support != null ? support.transform : site.origin;
        float cell = part.tabletop ? .25f : .5f;
        var local = grid.InverseTransformPoint(hit.point);
        float height = support != null ? support.surfaceHeight : local.y;
        proposed = grid.TransformPoint(new Vector3(Mathf.Round(local.x / cell) * cell, height, Mathf.Round(local.z / cell) * cell));
        bool surfaceValid = hit.normal.y > .65f && (part.tabletop ? support != null : Mathf.Abs(local.y) < .2f);
        string reason = part.tabletop ? "Choose a table to place this." : "Aim at the ground within your plot.";
        if (surfaceValid)
        {
            if (!part.tabletop) proposed.y = site.origin.position.y;
            valid = CanPlace(part, proposed, rotation, support, out reason);
            ShowGrid(grid, support != null ? support.footprint : site.plotSize, support != null ? support.surfaceHeight + .008f : .035f, cell);
        }
        preview.SetActive(true); preview.transform.SetPositionAndRotation(proposed, rotation); preview.transform.localScale = Vector3.one;
        foreach (var renderer in ghostRenderers) renderer.sharedMaterial = valid ? validMaterial : invalidMaterial;
        game.player.prompt = valid ? bowl ? "Click to place one bowl" : "Click to place / R rotate" : reason;
    }
    private void ShowGrid(Transform surface, Vector2 size, float height, float cell)
    {
        gridRenderer.gameObject.SetActive(true);
        gridRenderer.transform.SetPositionAndRotation(surface.TransformPoint(Vector3.up * height), surface.rotation);
        gridRenderer.transform.localScale = new Vector3(size.x, 1, size.y);
        gridProperties.SetVector("_GridSize", new Vector4(size.x, size.y, 0, 0));
        gridProperties.SetFloat("_CellSize", cell); gridRenderer.SetPropertyBlock(gridProperties);
    }
    public void PlaceHeld()
    {
        if (!valid || selected == null) return;
        var item = game.player.Held;
        if (selected.kind == TycoonPart.Kind.Bowl)
        {
            var contents = item.kind == TycoonItem.Kind.Serving ? item : new TycoonItem(TycoonItem.Kind.Serving);
            CreateBowl(support, proposed, contents);
            if (item.kind == TycoonItem.Kind.Serving) game.player.inventory.slots[game.player.selected] = null;
            else game.player.inventory.Consume(game.player.selected);
        }
        else
        {
            var part = selected;
            part.transform.SetParent(support != null ? support.transform : part.site == 2 ? game.truck.transform : null, true);
            part.transform.SetPositionAndRotation(proposed, rotation); part.support = support; part.installed = true; part.packed = false; part.gameObject.SetActive(true);
            foreach (var member in game.parts.Where(p => p == part || p.transform.IsChildOf(part.transform))) member.installed = true;
            game.player.inventory.slots[game.player.selected] = null;
            game.navigation.BuildNavMesh();
        }
        selected = null; previewItem = null; valid = false; preview.SetActive(false); gridRenderer.gameObject.SetActive(false);
        game.Save(); game.player.RefreshHeld(); game.notice = "Placed.";
    }
    public TycoonPart CreateBowl(TycoonPart table, Vector3 position, TycoonItem contents)
    {
        var bowl = game.AddPart(bowlPrefab.catalogIndex, table.site, position);
        bowl.support = table; bowl.transform.SetParent(table.transform, true); bowl.transform.rotation = table.transform.rotation;
        bowl.operatingPoint.position = table.operatingPoint.position;
        bowl.contents = contents; bowl.RefreshVisual(); return bowl;
    }
    public TycoonPart ReserveBowl(int site)
    {
        foreach (var table in game.parts.Where(p => p.site == site && p.installed && p.TableSurface))
            for (float x = -table.footprint.x / 2 + .25f; x < table.footprint.x / 2; x += .25f)
                for (float z = -table.footprint.y / 2 + .25f; z < table.footprint.y / 2; z += .25f)
                {
                    var position = table.transform.TransformPoint(new Vector3(x, table.surfaceHeight, z));
                    if (CanPlace(bowlPrefab, position, table.transform.rotation, table, out _)) return CreateBowl(table, position, null);
                }
        return null;
    }
    public bool CanPlace(TycoonPart part, Vector3 position, Quaternion rotation, TycoonPart support, out string reason)
    {
        reason = "";
        Vector3 size = rotation * new Vector3(part.footprint.x, 0, part.footprint.y);
        size = new Vector3(Mathf.Abs(size.x), .5f, Mathf.Abs(size.z));
        int siteIndex = part.kind == TycoonPart.Kind.Bowl && support != null ? support.site : part.site;
        var site = game.sites[siteIndex]; var offset = site.origin.InverseTransformPoint(position);
        var plotSize = Quaternion.Inverse(site.origin.rotation) * rotation * new Vector3(part.footprint.x,0,part.footprint.y);
        if (!site.owned || Mathf.Abs(offset.x) + Mathf.Abs(plotSize.x) / 2 > site.plotSize.x / 2 || Mathf.Abs(offset.z) + Mathf.Abs(plotSize.z) / 2 > site.plotSize.y / 2)
        { reason = "Place within the owned plot."; return false; }
        if (part.tabletop)
        {
            if (support == null || !support.TableSurface || !support.installed || support.site != siteIndex) { reason = "Choose a table at this business."; return false; }
            var relative = support.transform.InverseTransformPoint(position);
            var topSize = Quaternion.Inverse(support.transform.rotation) * rotation * new Vector3(part.footprint.x,0,part.footprint.y);
            if (Mathf.Abs(relative.x) + Mathf.Abs(topSize.x) / 2 > support.footprint.x / 2 || Mathf.Abs(relative.z) + Mathf.Abs(topSize.z) / 2 > support.footprint.y / 2) { reason = "Equipment must fit on the tabletop."; return false; }
        }
        foreach (var other in game.parts.Where(p => p != part && p != support && p.site == siteIndex && p.installed && p.kind != TycoonPart.Kind.Truck && p.kind != TycoonPart.Kind.Bike && p.kind != TycoonPart.Kind.Plot && p.tabletop == part.tabletop && (!part.tabletop || p.support == support) && !p.transform.IsChildOf(part.transform)))
        {
            var delta = position - other.transform.position;
            var otherSize = other.transform.rotation * new Vector3(other.footprint.x, 0, other.footprint.y);
            if (Mathf.Abs(delta.x) < (size.x + Mathf.Abs(otherSize.x)) / 2 - .01f && Mathf.Abs(delta.z) < (size.z + Mathf.Abs(otherSize.z)) / 2 - .01f)
            { reason = "These grid cells are occupied."; return false; }
        }
        return true;
    }
}
