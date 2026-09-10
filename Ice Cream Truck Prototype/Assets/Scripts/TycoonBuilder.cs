using System.Linq;
using UnityEngine;
using UnityEngine.InputSystem;

public class TycoonBuilder : MonoBehaviour
{
    public TycoonGameManager game;
    public bool active;
    public TycoonPart selected;
    public GameObject preview;
    public GameObject grid;
    public Renderer[] buildOccluders;
    public Renderer previewRenderer;
    public Material validMaterial, invalidMaterial;
    public bool valid;
    public string reason;
    private Vector3 proposed;
    private Quaternion rotation;
    private TycoonPart support;
    private Vector3 cameraPosition;
    private Quaternion cameraRotation;
    public void Toggle()
    {
        active = !active; selected = null; preview.SetActive(false);
        if (active)
        {
            cameraPosition = game.player.view.transform.localPosition; cameraRotation = game.player.view.transform.localRotation;
            var site = game.sites.Where(s => s.owned).OrderBy(s => Vector3.Distance(s.origin.position, game.player.transform.position)).First();
            game.player.view.transform.position = site.origin.position + new Vector3(0,8.5f,-4);
            game.player.view.transform.rotation = Quaternion.Euler(68,0,0);
            grid.transform.SetPositionAndRotation(site.origin.position+Vector3.up*.04f,site.origin.rotation);
        }
        else { game.player.view.transform.localPosition = cameraPosition; game.player.view.transform.localRotation = cameraRotation; }
        grid.SetActive(active); foreach(var renderer in buildOccluders)renderer.enabled=!active;
        game.player.grip.gameObject.SetActive(!active);game.player.leftHand.gameObject.SetActive(!active);game.player.rightHand.gameObject.SetActive(!active);
        game.hud.ClosePanels(); game.notice = active ? "Build: click furniture to move, R to rotate, click a valid grid cell to place. B to finish." : "Layout saved.";
        if (!active) { game.navigation.BuildNavMesh(); game.Save(); }
    }
    private void Update()
    {
        if (!active || game.hud.AnyPanel) return;
        var keyboard = Keyboard.current;
        Vector3 pan = new Vector3((keyboard.dKey.isPressed ? 1 : 0) - (keyboard.aKey.isPressed ? 1 : 0), 0, (keyboard.wKey.isPressed ? 1 : 0) - (keyboard.sKey.isPressed ? 1 : 0));
        game.player.view.transform.position += pan * Time.unscaledDeltaTime * 8;
        var mouse = Mouse.current;
        var ray = game.player.view.ScreenPointToRay(mouse.position.ReadValue());
        if (!Physics.Raycast(ray, out var hit, 100)) return;
        if (selected == null)
        {
            if (mouse.leftButton.wasPressedThisFrame)
            {
                var part = hit.collider.GetComponentInParent<TycoonPart>();
                if (part != null && part.kind != TycoonPart.Kind.Sign && part.kind != TycoonPart.Kind.ServingCounter && part.kind != TycoonPart.Kind.Supplier && part.kind != TycoonPart.Kind.Plot && part.kind != TycoonPart.Kind.Bike && part.kind != TycoonPart.Kind.Truck)
                { selected = part; rotation = part.transform.rotation; preview.SetActive(true); }
            }
            return;
        }
        if (Keyboard.current.rKey.wasPressedThisFrame) rotation *= Quaternion.Euler(0, 90, 0);
        support = selected.tabletop ? hit.collider.GetComponentInParent<TycoonPart>() : null;
        var grid = support != null && (support.kind == TycoonPart.Kind.Table || support.kind == TycoonPart.Kind.ServingCounter) ? support.transform : game.sites[selected.site].origin;
        float cell = selected.tabletop ? .25f : .5f;
        var local = grid.InverseTransformPoint(hit.point);
        proposed = grid.TransformPoint(new Vector3(Mathf.Round(local.x / cell) * cell, selected.tabletop ? .94f : 0, Mathf.Round(local.z / cell) * cell));
        valid = CanPlace(selected, proposed, rotation, support, out reason);
        preview.transform.SetPositionAndRotation(proposed + Vector3.up * .02f, rotation);
        preview.transform.localScale = new Vector3(selected.footprint.x, .025f, selected.footprint.y);
        previewRenderer.sharedMaterial = valid ? validMaterial : invalidMaterial;
        game.notice = valid ? "Click to place / R to rotate" : reason;
        if (mouse.leftButton.wasPressedThisFrame && valid) Place(selected, proposed, rotation, support);
        if (mouse.rightButton.wasPressedThisFrame) { selected = null; preview.SetActive(false); }
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
    public void Place(TycoonPart part, Vector3 position, Quaternion rotation, TycoonPart support)
    {
        part.transform.SetParent(support != null ? support.transform : part.site == 2 ? game.truck.transform : null, true);
        part.transform.SetPositionAndRotation(position, rotation); part.support = support; part.installed = true;
        selected = null; preview.SetActive(false); game.navigation.BuildNavMesh();
        foreach (var worker in game.workers) if (!worker.ValidateLayout()) game.notice = worker.status;
    }
}
