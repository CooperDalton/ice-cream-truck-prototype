using System;
using System.Linq;
using UnityEngine;
using UnityEngine.AI;
using UnityEngine.UI;

public class TycoonTutorial : MonoBehaviour
{
    public enum Step { Inactive, PlaceEquipment, OpenDay, TakeOrder, SelectBowls, PlaceBowl, SelectScooper, Scoop, Deposit, TakeBowl, Serve, FinishDay, DaySummary, Supplier, BuyVanilla, BuyChocolate, BuyScooper, ReturnHome, RefillVanilla, RefillChocolate, EquipScooper, Complete, Practice, CollectSupplies, InstallRewards, FillRewards, ReopenDay }
    [Serializable] public class Progress
    {
        public Step step;
        public int placement, customerOrderId, bowlId, served;
        public int[] equipmentIds = new int[6];
        public bool boughtVanilla, boughtChocolate, boughtScooper;
        public bool rewardDeliverySeen;
    }
    public TycoonGameManager game;
    public Transform playerSpawn, bowlSpot;
    public Transform[] placementSpots;
    public GameObject[] placementGhosts;
    public GameObject bowlGhost, uiRoot;
    public RectTransform instructionPanel, slotHighlight, buttonHighlight, worldCue, worldArrow, swipeHint;
    public Image itemIcon;
    public Text input, caption;
    public RectTransform destinationPanel;
    public Text destinationCaption;
    public GameObject supplyRoute;
    public Transform[] supplyRouteArrows;
    public Transform supplyDestination;
    public MeshFilter focusMesh;
    public Progress progress = new Progress();
    public bool Active => progress.step != Step.Inactive && progress.step != Step.Complete;
    public bool FirstDay => Active && game.day == 1 && (progress.step <= Step.FinishDay || Practicing);
    public bool Practicing => progress.step == Step.Practice;
    public bool CanOpen => !Active || progress.step == Step.OpenDay || progress.step == Step.ReopenDay;
    public TycoonPart[] Equipment { get; private set; } = Array.Empty<TycoonPart>();
    public TycoonActor Customer { get; private set; }
    private float age;
    private readonly Vector3[] corners = new Vector3[4];
    private TycoonPart Bowl => game.parts.FirstOrDefault(p => p.id == progress.bowlId);

    public void BeginNewGame()
    {
        foreach (var part in game.parts.Where(p => p.site == 0 && p.kind != TycoonPart.Kind.Sign && p.kind != TycoonPart.Kind.BusinessBoard && p.kind != TycoonPart.Kind.Plot && p.kind != TycoonPart.Kind.Supplier && p.kind != TycoonPart.Kind.Bike && p.kind != TycoonPart.Kind.Truck && p.kind != TycoonPart.Kind.Trash).ToArray())
        {
            game.parts.Remove(part); part.gameObject.SetActive(false); Destroy(part.gameObject);
        }
        progress = new Progress { step = Step.PlaceEquipment };
        game.cash = 100;
        game.player.inventory = new TycoonInventory(8);
        Equipment = new TycoonPart[6];
        int[] prefabs = { 0, 10, 7, 1, 1, 8 };
        for (int i = 0; i < Equipment.Length; i++)
        {
            var part = game.AddPart(prefabs[i], 0, placementSpots[i].position);
            part.transform.rotation = placementSpots[i].rotation;
            part.installed = false; part.packed = true; part.gameObject.SetActive(false);
            if (part.kind == TycoonPart.Kind.Tub) { part.variant = i - 3; part.contents = new TycoonItem(TycoonItem.Kind.Tub, 12, part.variant); }
            Equipment[i] = part; progress.equipmentIds[i] = part.id;
            game.player.inventory.slots[i + 2] = new TycoonItem(TycoonItem.Kind.Equipment, 1, prefabs[i]) { equipmentId = part.id };
        }
        game.player.inventory.slots[0] = new TycoonItem(TycoonItem.Kind.BasicScooper);
        game.player.inventory.slots[1] = new TycoonItem(TycoonItem.Kind.Bowls, 12);
        game.player.Teleport(playerSpawn.position); game.player.transform.rotation = playerSpawn.rotation;
        game.player.pitch = 22; game.player.view.transform.localRotation = Quaternion.Euler(22, 0, 0);
        game.player.Select(2); game.navigation.BuildNavMesh(); game.notice = "";
    }
    public void Restore(Progress saved)
    {
        progress = saved ?? new Progress();
        if (!Active) return;
        if (FirstDay && progress.served > 0 && progress.served < 3) progress.step = Step.Practice;
        Equipment = progress.equipmentIds.Select(id => game.parts.Single(p => p.id == id)).ToArray();
        Customer = game.actors.FirstOrDefault(a => !a.worker && a.order.id == progress.customerOrderId);
        age = 0;
    }
    public bool AllowsPlacement(TycoonPart part, Vector3 position, Quaternion rotation, TycoonPart support, out string reason)
    {
        reason = "";
        if (!FirstDay || Practicing) return true;
        Transform spot;
        if (progress.step == Step.PlaceEquipment && part == Equipment[progress.placement]) spot = placementSpots[progress.placement];
        else if (progress.step == Step.PlaceBowl && part.kind == TycoonPart.Kind.Bowl && support == Equipment[0]) spot = bowlSpot;
        else { reason = "Follow the highlight"; return false; }
        bool fits = Vector3.Distance(position, spot.position) < .06f && (part.kind == TycoonPart.Kind.Bowl || Quaternion.Angle(rotation, spot.rotation) < 5);
        if (!fits) reason = "Match the ghost";
        return fits;
    }
    public void SpawnCustomer()
    {
        var site = game.sites[0];
        if (!NavMesh.SamplePosition(site.queuePoint.position, out var hit, 2, NavMesh.AllAreas))
            throw new InvalidOperationException("Tutorial order counter needs a reachable queue point.");
        Customer = Instantiate(game.catalog.customerPrefab, hit.position, Quaternion.identity);
        Customer.game = game; Customer.site = 0;
        Customer.order = new TycoonOrder { id = game.nextId++, flavors = new[] { progress.served % 2 }, patience = game.orderPatience, patienceLimit = game.orderPatience, joinedQueue = true };
        Customer.agent.Warp(hit.position);
        site.queue.Add(Customer); game.actors.Add(Customer); progress.customerOrderId = Customer.order.id;
        Advance(progress.served == 0 ? Step.TakeOrder : Step.Practice);
    }
    public bool GuidesCustomer(TycoonActor actor)
    {
        return FirstDay && actor == Customer;
    }
    public bool AllowsUse(TycoonPart target, TycoonActor customer, bool take)
    {
        if (!FirstDay || Practicing) return true;
        var held = game.player.Held;
        return progress.step switch {
            Step.PlaceEquipment or Step.PlaceBowl => !take,
            Step.OpenDay => target != null && target.kind == TycoonPart.Kind.Sign,
            Step.TakeOrder or Step.Serve => take && customer == Customer,
            Step.Scoop => !take && target == Equipment[3 + Customer.order.flavors[0]] && held != null && held.Tool,
            Step.Deposit => !take && target == Bowl && held != null && held.Tool,
            Step.TakeBowl => take && target == Bowl,
            _ => false
        };
    }
    public void PrepareDayEnd()
    {
        if (!FirstDay) return;
        game.xp = Mathf.Max(game.xp, TycoonCatalogSO.Thresholds[1]);
        progress.step = Step.DaySummary;
    }
    public void BeginShopping()
    {
        if (progress.step != Step.DaySummary) return;
        progress.step = Step.InstallRewards; age = 0;
    }
    public void Purchased(int product)
    {
        if (!Active || game.day < 2) return;
        if (product == 0) progress.boughtVanilla = true;
        if (product == 1) progress.boughtChocolate = true;
        if (product == 20) progress.boughtScooper = true;
        game.Save();
    }
    private void Update()
    {
        if (!Active || game.loadingCampaign) return;
        if (!game.Paused) age += Time.deltaTime;
    }
    public void Tick()
    {
        var held = game.player.Held;
        switch (progress.step)
        {
            case Step.PlaceEquipment:
                if (!Equipment[progress.placement].installed) break;
                progress.placement++;
                if (progress.placement == Equipment.Length) Advance(Step.OpenDay); else game.Save();
                break;
            case Step.TakeOrder:
                if (Customer.order.stage == TycoonOrder.Stage.Pickup) Advance(Step.SelectBowls);
                break;
            case Step.SelectBowls:
                if (held != null && held.kind == TycoonItem.Kind.Bowls) Advance(Step.PlaceBowl);
                break;
            case Step.PlaceBowl:
                var bowl = game.parts.FirstOrDefault(p => p.kind == TycoonPart.Kind.Bowl && p.support == Equipment[0] && Vector3.Distance(p.transform.position, bowlSpot.position) < .06f);
                if (bowl != null) { progress.bowlId = bowl.id; Advance(Step.SelectScooper); }
                break;
            case Step.SelectScooper:
                if (held != null && held.Tool) Advance(Step.Scoop);
                break;
            case Step.Scoop:
                if (held != null && held.Tool && held.loadedFlavor == Customer.order.flavors[0]) Advance(Step.Deposit);
                break;
            case Step.Deposit:
                if (Bowl.contents.Matches(Customer.order)) Advance(Step.TakeBowl);
                break;
            case Step.TakeBowl:
                if (held != null && held.Matches(Customer.order)) Advance(Step.Serve);
                break;
            case Step.Serve:
            case Step.Practice:
                if (!Customer.leaving) break;
                progress.served++; game.clock = progress.served * 160;
                if (progress.served == 3) Advance(Step.FinishDay); else SpawnCustomer();
                break;
            case Step.FinishDay:
                if (age >= 2.5f) game.CloseDay();
                break;
            case Step.InstallRewards:
                if (Enumerable.Range(2, 2).All(flavor => game.Parts(0, TycoonPart.Kind.Tub).Any(p => p.variant == flavor))) Advance(Step.FillRewards);
                break;
            case Step.FillRewards:
                if (Enumerable.Range(2, 2).All(flavor => game.Parts(0, TycoonPart.Kind.Tub).Any(p => p.variant == flavor && p.contents.amount == p.contents.Capacity))) Advance(Step.Supplier);
                break;
            case Step.ReopenDay:
                if (game.phase == TycoonGameManager.Phase.Trading) Advance(Step.Complete);
                break;
            case Step.Supplier:
                if (game.hud.shopPanel.activeInHierarchy) Advance(Step.BuyVanilla);
                break;
            case Step.BuyVanilla:
                if (progress.boughtVanilla) Advance(Step.BuyChocolate);
                break;
            case Step.BuyChocolate:
                if (progress.boughtChocolate) Advance(Step.BuyScooper);
                break;
            case Step.BuyScooper:
                if (progress.boughtScooper) Advance(Step.CollectSupplies);
                break;
            case Step.CollectSupplies:
                if (game.player.inventory.Locate(TycoonItem.Kind.Tub, 0) >= 0 && game.player.inventory.Locate(TycoonItem.Kind.Tub, 1) >= 0 && game.player.inventory.Locate(TycoonItem.Kind.ImprovedScooper) >= 0) Advance(Step.ReturnHome);
                break;
            case Step.ReturnHome:
                if (!game.hud.AnyPanel && Vector3.Distance(game.player.transform.position, Equipment[3].transform.position) < 3) Advance(Step.RefillVanilla);
                break;
            case Step.RefillVanilla:
                if (Equipment[3].contents.amount == Equipment[3].contents.Capacity) Advance(Step.RefillChocolate);
                break;
            case Step.RefillChocolate:
                if (Equipment[4].contents.amount == Equipment[4].contents.Capacity) Advance(Step.EquipScooper);
                break;
            case Step.EquipScooper:
                if (held != null && held.kind == TycoonItem.Kind.ImprovedScooper) Advance(Step.ReopenDay);
                break;
        }
    }
    private void Advance(Step step)
    {
        progress.step = step; age = 0; game.notice = ""; game.Save();
    }
    private void LateUpdate()
    {
        if (Active && !game.loadingCampaign && !game.Paused) Tick();
        var reward = !progress.rewardDeliverySeen && game.level > 1 ? game.parts.FirstOrDefault(p => p.rewardDelivery) : null;
        bool showReward = reward != null && progress.step != Step.InstallRewards && progress.step != Step.FillRewards && game.phase != TycoonGameManager.Phase.Results;
        uiRoot.SetActive((Active && !Practicing || showReward) && !game.hud.menuOpen && !game.loadingCampaign);
        foreach (var ghost in placementGhosts) ghost.SetActive(false);
        bowlGhost.SetActive(false); focusMesh.gameObject.SetActive(false);
        slotHighlight.gameObject.SetActive(false); buttonHighlight.gameObject.SetActive(false); worldCue.gameObject.SetActive(false);
        instructionPanel.gameObject.SetActive(false); swipeHint.gameObject.SetActive(false);
        destinationPanel.gameObject.SetActive(false); supplyRoute.SetActive(false);
        if (!uiRoot.activeSelf) return;
        if (showReward && !game.hud.AnyPanel)
        {
            focusMesh.sharedMesh = game.catalog.placementPreviews[reward.catalogIndex].GetComponent<MeshFilter>().sharedMesh;
            focusMesh.transform.SetPositionAndRotation(reward.transform.position + Vector3.up * .004f, reward.transform.rotation);
            focusMesh.transform.localScale = Vector3.one * 1.035f; focusMesh.gameObject.SetActive(true);
            PointAt(reward.transform.position + Vector3.up * 1.3f);
            instructionPanel.gameObject.SetActive(true); input.text = "E"; caption.text = "New flavors";
            itemIcon.sprite = game.catalog.tubIcons[reward.variant]; itemIcon.gameObject.SetActive(true);
            return;
        }
        var inventory = game.player.inventory;
        int slot = -1;
        Vector3 point = Vector3.zero;
        bool world = false;
        TycoonPart focus = null;
        RectTransform button = null;
        string key = "", action = "";
        Sprite icon = null;
        switch (progress.step)
        {
            case Step.PlaceEquipment:
                var part = Equipment[progress.placement];
                slot = Array.FindIndex(inventory.slots, i => i != null && i.kind == TycoonItem.Kind.Equipment && i.equipmentId == part.id);
                placementGhosts[progress.placement].SetActive(!game.hud.AnyPanel);
                point = placementSpots[progress.placement].position + Vector3.up * 1.3f; world = true;
                key = "Click"; action = "Place"; icon = game.catalog.equipmentIcons[part.catalogIndex];
                break;
            case Step.OpenDay:
            case Step.ReopenDay:
                point = game.sites[0].signMount.position + Vector3.up * .4f; world = true;
                key = "E"; action = "Open shop"; break;
            case Step.TakeOrder:
            case Step.Serve:
                point = Customer.transform.position + Vector3.up * 1.7f; world = true;
                key = "E"; action = progress.step == Step.TakeOrder ? "Take order" : "Serve";
                if (progress.step == Step.Serve) icon = game.catalog.bowlIcon;
                break;
            case Step.SelectBowls:
            case Step.PlaceBowl:
                slot = inventory.Locate(TycoonItem.Kind.Bowls); key = "Click"; action = "Place bowl"; icon = game.catalog.bowlIcon;
                bowlGhost.SetActive(!game.hud.AnyPanel); point = bowlSpot.position + Vector3.up * .4f; world = true;
                if (progress.step == Step.SelectBowls) focus = Equipment[3 + Customer.order.flavors[0]];
                break;
            case Step.SelectScooper:
            case Step.Scoop:
                slot = Array.FindIndex(inventory.slots, i => i != null && i.Tool);
                focus = Equipment[3 + Customer.order.flavors[0]]; icon = game.catalog.tubIcons[focus.variant];
                key = "Hold"; action = "Swipe"; swipeHint.gameObject.SetActive(game.player.selected == slot); break;
            case Step.Deposit:
            case Step.TakeBowl:
                focus = Bowl; key = progress.step == Step.Deposit ? "Click" : "E";
                action = progress.step == Step.Deposit ? "Add scoop" : "Take bowl"; icon = game.catalog.bowlIcon;
                if (progress.step == Step.Deposit) slot = Array.FindIndex(inventory.slots, i => i != null && i.Tool && i.loadedFlavor >= 0);
                break;
            case Step.FinishDay: action = "Day complete"; break;
            case Step.InstallRewards:
                var holder = game.parts.First(p => p.site == 0 && p.kind == TycoonPart.Kind.Tub && (p.variant == 2 || p.variant == 3) && !p.installed);
                if (holder.packed)
                {
                    slot = Array.FindIndex(inventory.slots, i => i != null && i.equipmentId == holder.id);
                    key = "Click"; action = "Place " + TycoonCatalogSO.FlavorNames[holder.variant] + " holder";
                }
                else { focus = holder; key = "E"; action = "Collect holder"; }
                icon = game.catalog.tubIcons[holder.variant];
                break;
            case Step.FillRewards:
                var emptyHolder = game.Parts(0, TycoonPart.Kind.Tub).First(p => (p.variant == 2 || p.variant == 3) && p.contents.amount < p.contents.Capacity);
                slot = inventory.Locate(TycoonItem.Kind.Tub, emptyHolder.variant);
                if (slot >= 0) { focus = emptyHolder; key = "Click"; action = "Fill " + TycoonCatalogSO.FlavorNames[emptyHolder.variant]; }
                else
                {
                    var refill = game.looseItems.First(l => l.levelReward && l.item.kind == TycoonItem.Kind.Tub && l.item.variant == emptyHolder.variant);
                    point = refill.transform.position + Vector3.up * .35f; world = true; key = "E"; action = "Collect ice cream";
                }
                icon = game.catalog.tubIcons[emptyHolder.variant];
                break;
            case Step.Supplier:
            case Step.BuyVanilla:
            case Step.BuyChocolate:
            case Step.BuyScooper:
                if (!game.hud.shopPanel.activeInHierarchy)
                {
                    action = "Buy Supplies";
                    point = supplyDestination.position + Vector3.up * 2.2f; world = true;
                    supplyRoute.SetActive(!game.hud.AnyPanel);
                }
                else
                {
                    int product = progress.step == Step.BuyScooper ? 20 : progress.step == Step.BuyChocolate ? 1 : 0;
                    int category = product == 20 ? 3 : 0;
                    bool categoryVisible = game.hud.SupplyCategory == category;
                    button = (RectTransform)(categoryVisible ? game.hud.supplyButtons[product] : game.hud.supplyCategoryButtons[category]).transform;
                    icon = product == 20 ? game.catalog.improvedIcon : game.catalog.tubIcons[product]; key = "Click";
                    action = categoryVisible ? "Buy" : category == 3 ? "Tools" : "Ice Cream";
                }
                break;
            case Step.ReturnHome:
                if (game.hud.AnyPanel) { button = (RectTransform)game.hud.closeButton.transform; key = "Click"; action = "Back to shop"; }
                else { point = Equipment[3].transform.position + Vector3.up; world = true; action = "Back to shop"; }
                break;
            case Step.CollectSupplies:
                if (game.hud.AnyPanel) { button = (RectTransform)game.hud.closeButton.transform; key = "Click"; action = "Collect supplies"; }
                else
                {
                    var delivery = game.looseItems.FirstOrDefault(l => l.supplySlot >= 0 && inventory.Locate(l.item.kind, l.item.variant) < 0);
                    point = delivery == null ? game.pickupPoint.position : delivery.transform.position;
                    point += Vector3.up * .35f; world = true; key = "E"; action = "Collect";
                    if (delivery != null) icon = game.catalog.Icon(delivery.item);
                }
                break;
            case Step.RefillVanilla:
            case Step.RefillChocolate:
                int flavor = progress.step == Step.RefillVanilla ? 0 : 1;
                slot = inventory.Locate(TycoonItem.Kind.Tub, flavor); focus = Equipment[3 + flavor];
                icon = game.catalog.tubIcons[flavor]; key = "Click"; action = "Refill"; break;
            case Step.EquipScooper:
                slot = inventory.Locate(TycoonItem.Kind.ImprovedScooper); icon = game.catalog.improvedIcon; action = "Ready!"; break;
        }
        if (slot >= 0)
        {
            var target = game.hud.personalInventoryPanel.activeSelf ? game.hud.inventorySlots[slot].frame.rectTransform : game.hud.hotbar[slot].frame.rectTransform;
            Highlight(slotHighlight, target);
            if (game.player.selected != slot) { key = (slot + 1).ToString(); action = "Select"; icon = game.catalog.Icon(inventory.slots[slot]); }
        }
        if (button != null) Highlight(buttonHighlight, button);
        if (focus != null && !game.hud.AnyPanel)
        {
            focusMesh.sharedMesh = game.catalog.placementPreviews[focus.catalogIndex].GetComponent<MeshFilter>().sharedMesh;
            focusMesh.transform.SetPositionAndRotation(focus.transform.position + Vector3.up * .004f, focus.transform.rotation);
            focusMesh.transform.localScale = Vector3.one * 1.035f; focusMesh.gameObject.SetActive(true);
            point = focus.transform.position + Vector3.up * (focus.kind == TycoonPart.Kind.Tub ? 1.1f : .4f); world = true;
        }
        if (world && !game.hud.AnyPanel) PointAt(point);
        bool destination = action != "" && key == "" && icon == null;
        instructionPanel.gameObject.SetActive(action != "" && !destination);
        destinationPanel.gameObject.SetActive(destination); destinationCaption.text = action;
        input.text = key; caption.text = action; itemIcon.sprite = icon; itemIcon.gameObject.SetActive(icon != null);
        swipeHint.anchoredPosition = new Vector2(145, Mathf.Sin(Time.unscaledTime * 5) * 12);
    }
    private void Highlight(RectTransform highlight, RectTransform target)
    {
        target.GetWorldCorners(corners);
        var parent = (RectTransform)highlight.parent;
        var min = parent.InverseTransformPoint(corners[0]); var max = parent.InverseTransformPoint(corners[2]);
        highlight.anchoredPosition = (min + max) * .5f;
        highlight.sizeDelta = new Vector2(max.x - min.x + 14, max.y - min.y + 14);
        highlight.localScale = Vector3.one * (1 + .035f * Mathf.Sin(Time.unscaledTime * 5));
        highlight.gameObject.SetActive(true);
    }
    private void PointAt(Vector3 point)
    {
        var screen = game.player.view.WorldToScreenPoint(point);
        var center = new Vector2(Screen.width, Screen.height) * .5f;
        var direction = (Vector2)screen - center;
        bool behind = screen.z <= 0;
        if (behind) direction = -direction;
        bool offscreen = behind || screen.x < 64 || screen.x > Screen.width - 64 || screen.y < 110 || screen.y > Screen.height - 64;
        Vector2 pixel;
        if (offscreen)
        {
            if (direction.sqrMagnitude < 1) direction = Vector2.down;
            direction.Normalize();
            float distance = Mathf.Min((center.x - 64) / Mathf.Max(.001f, Mathf.Abs(direction.x)), (center.y - 110) / Mathf.Max(.001f, Mathf.Abs(direction.y)));
            pixel = center + direction * distance;
            worldArrow.localRotation = Quaternion.Euler(0, 0, Mathf.Atan2(direction.y, direction.x) * Mathf.Rad2Deg + 90);
        }
        else { pixel = (Vector2)screen + Vector2.up * (25 + 7 * Mathf.Sin(Time.unscaledTime * 4)); worldArrow.localRotation = Quaternion.identity; }
        RectTransformUtility.ScreenPointToLocalPointInRectangle((RectTransform)worldCue.parent, pixel, null, out var local);
        worldCue.anchoredPosition = local; worldCue.gameObject.SetActive(true);
    }
}
