using System;
using System.Linq;
using UnityEngine;
using UnityEngine.UI;
using UnityEngine.InputSystem;

public class TycoonHUD : MonoBehaviour
{
    [Serializable] public class SlotView { public Button button; public Text label; public Image bar, frame, icon; }
    [Serializable] public class OrderView { public GameObject root; public Text title, description; public Image container; public Image[] flavors, toppings; }
    public OrderView[] tickets;
    public TycoonGameManager game;
    public Text money, clock, notice, prompt, orders, heldLabel, panelTitle, panelText, waypointText;
    public Text resultsText;
    public Text dayValue, levelValue;
    public GameObject reticle;
    public Image xpBar, useBar, pickupRing;
    public RectTransform moneyDisplay, salePopup;
    public CanvasGroup salePopupGroup;
    public Text salePopupAmount;
    private Vector2 salePopupOrigin;
    private float saleAge = 2, saleTotal;
    public Image targetStockBar;
    public GameObject panel, inventoryPanel, shopPanel, businessPanel, mapPanel, menuPanel;
    public SlotView[] hotbar, playerSlots, storageSlots;
    public Button[] supplyButtons, upgradeButtons, hireButtons;
    public Button closeButton, openButton, saveButton, nextButton, cargoButton, recoveryButton;
    public Button assignLockerButton, newGameButton, quitButton;
    public RectTransform miniMarker, fullMarker, waypointMarker;
    public RectTransform[] miniLocations, mapLocations;
    public Button[] destinationButtons;
    public Button[] mapButtons;
    public RectTransform mapContent;
    public RectTransform[] miniRoads;
    public Vector3[] roadCenters;
    public bool menuOpen;
    public bool AnyPanel => panel.activeSelf;
    private TycoonInventory storage;
    private bool bulkAllowed;
    private int businessSite, transferSelection = -1;
    private Vector3 waypoint;
    private bool hasWaypoint;
    private TycoonWorker inspectedWorker;
    private bool confirmingNewGame;
    private float mapZoom=1;
    private void Start()
    {
        salePopupOrigin = salePopup.anchoredPosition;
        salePopup.gameObject.SetActive(false);
        game.SaleCompleted += ShowSale;
        closeButton.onClick.AddListener(ClosePanels);
        openButton.onClick.AddListener(() => { ClosePanels(); game.OpenDay(); });
        saveButton.onClick.AddListener(() => { game.Save(); game.notice = "Game saved."; });
        nextButton.onClick.AddListener(() => { ClosePanels(); game.NextDay(); });
        cargoButton.onClick.AddListener(TransferCargo);
        recoveryButton.onClick.AddListener(() => { ClosePanels(); game.notice = "Carry the marked supplier crates to the loading pad for emergency stock."; game.player.StartRecovery(); });
        assignLockerButton.onClick.AddListener(() => {
            var lockers = game.Parts(inspectedWorker.site, TycoonPart.Kind.Locker).ToArray();
            inspectedWorker.locker = lockers[(Array.IndexOf(lockers, inspectedWorker.locker) + 1) % lockers.Length];
            game.notice = "Assigned locker changed. Its position is marked on the minimap."; waypoint = inspectedWorker.locker.transform.position; hasWaypoint = true;
        });
        newGameButton.onClick.AddListener(() => {
            if (!confirmingNewGame) { confirmingNewGame = true; panelText.text = "Start a new game? Click New game again to replace your saved game."; return; }
            game.restartRequested = true; System.IO.File.Delete(TycoonGameManager.SavePath); Time.timeScale = 1; UnityEngine.SceneManagement.SceneManager.LoadScene("IceCreamTycoon");
        });
        quitButton.onClick.AddListener(() => { game.Save(); Application.Quit(); });
        for (int i = 0; i < supplyButtons.Length; i++) { int index = i; supplyButtons[i].onClick.AddListener(() => { game.PurchaseSupply(index); panelText.text = game.notice; }); }
        for (int i = 0; i < upgradeButtons.Length; i++) { int index = i; upgradeButtons[i].onClick.AddListener(() => { game.BuyUpgrade(index, businessSite); panelText.text = game.notice; }); }
        for (int i = 0; i < hireButtons.Length; i++) { int index = i; hireButtons[i].onClick.AddListener(() => game.Hire(Mathf.Min(index, 2), index == 3 ? 2 : businessSite, index == 3)); }
        for (int i = 0; i < hotbar.Length; i++) { int index = i; hotbar[i].button.onClick.AddListener(() => game.player.Select(index)); playerSlots[i].button.onClick.AddListener(() => ClickPlayer(index)); }
        for (int i = 0; i < storageSlots.Length; i++) { int index = i; storageSlots[i].button.onClick.AddListener(() => ClickStorage(index)); }
        for (int i = 0; i < destinationButtons.Length; i++) { int index = i; destinationButtons[i].onClick.AddListener(() => { waypoint = Location(index); hasWaypoint = true; game.notice = "Destination marked."; }); mapButtons[i].onClick.AddListener(()=>{waypoint=Location(index);hasWaypoint=true;game.notice="Destination marked.";}); }
        ClosePanels();
    }
    private void OnDestroy()
    {
        game.SaleCompleted -= ShowSale;
    }
    private void ShowSale(object sender, TycoonGameManager.SaleEventArgs sale)
    {
        if (saleAge >= 1.4f) saleTotal = 0;
        saleTotal += sale.amount; saleAge = 0;
        salePopupAmount.text = "+$" + saleTotal.ToString("0.##");
        salePopup.anchoredPosition = salePopupOrigin;
        salePopupGroup.alpha = 1; salePopup.gameObject.SetActive(true);
    }
    private void Update()
    {
        saleAge += Time.unscaledDeltaTime;
        moneyDisplay.localScale = Vector3.one * (1 + .09f * Mathf.Sin(Mathf.Clamp01(saleAge / .3f) * Mathf.PI));
        if (salePopup.gameObject.activeSelf)
        {
            salePopup.anchoredPosition = salePopupOrigin + Vector2.up * (42 * Mathf.Clamp01(saleAge / 1.4f));
            salePopup.localScale = Vector3.one * (1 + .16f * Mathf.Sin(Mathf.Clamp01(saleAge / .25f) * Mathf.PI));
            salePopupGroup.alpha = 1 - Mathf.Clamp01((saleAge - .85f) / .55f);
            if (saleAge >= 1.4f) salePopup.gameObject.SetActive(false);
        }
        money.text = "$" + game.cash.ToString("0.##");dayValue.text=game.day.ToString();levelValue.text=game.level.ToString();
        int minute = 600 + Mathf.FloorToInt(game.clock);
        clock.text = (minute / 60).ToString("00") + ":" + (minute % 60).ToString("00");
        float threshold = TycoonCatalogSO.Thresholds[Mathf.Min(game.level, 6)];
        xpBar.fillAmount = game.level >= 7 ? 1 : (game.xp - TycoonCatalogSO.Thresholds[game.level - 1]) / (threshold - TycoonCatalogSO.Thresholds[game.level - 1]);
        pickupRing.fillAmount = game.builder.pickupProgress;
        pickupRing.transform.parent.gameObject.SetActive(game.builder.pickupProgress > 0 && !AnyPanel);
        prompt.text = AnyPanel ? "" : game.player.prompt;
        useBar.fillAmount = game.player.gestureProgress;
        useBar.transform.parent.gameObject.SetActive(game.player.gestureProgress>0&&!AnyPanel);
        bool stockTarget = !AnyPanel && game.player.target != null && game.player.target.contents != null && game.player.target.contents.Consumable;
        targetStockBar.transform.parent.gameObject.SetActive(stockTarget);
        if (stockTarget) targetStockBar.fillAmount = game.player.target.contents.Fill;
        for (int i = 0; i < supplyButtons.Length; i++) supplyButtons[i].interactable = i < 12 ? i < game.FlavorCount : i < 18 ? i - 12 < game.ToppingCount : i < 21 || i >= 27 || i - 21 < game.ToppingCount;
        for (int i = 0; i < 8; i++) { Show(hotbar[i], game.player.inventory.slots[i], i == game.player.selected); Show(playerSlots[i], game.player.inventory.slots[i], i == transferSelection); }
        for (int i = 0; i < storageSlots.Length; i++)
        {
            storageSlots[i].button.gameObject.SetActive(storage != null && i < storage.slots.Length);
            if (storage != null && i < storage.slots.Length) Show(storageSlots[i], storage.slots[i], false);
        }
        bool workerLocked = inspectedWorker != null && inspectedWorker.onDuty && game.phase == TycoonGameManager.Phase.Trading;
        foreach (var slot in playerSlots) slot.button.interactable = !workerLocked;
        foreach (var slot in storageSlots) slot.button.interactable = !workerLocked;
        assignLockerButton.interactable = !workerLocked;
        orders.text = string.Join("\n\n", game.sites.SelectMany((s, i) => s.queue.Take(2).Select(c => s.name + " / $" + c.order.Price(i).ToString("0.##") + "\n" + c.order.Description + (c.order.owner == "" ? "" : "\n" + c.order.owner))));
        var visibleOrders=game.sites.SelectMany(s=>s.queue).OrderBy(c=>Vector3.Distance(game.sites[c.site].origin.position,game.player.transform.position)).Take(tickets.Length).ToArray();
        for(int i=0;i<tickets.Length;i++)
        {
            var customer=i<visibleOrders.Length?visibleOrders[i]:null;var card=tickets[i];card.root.SetActive(customer!=null&&!AnyPanel);
            if(customer==null)continue;
            var order=customer.order;card.title.text="$"+order.Price(customer.site).ToString("0.##");
            card.container.sprite=order.cone?game.catalog.coneIcon:game.catalog.bowlIcon;
            for(int j=0;j<2;j++){card.flavors[j].gameObject.SetActive(j<order.flavors.Length);if(j<order.flavors.Length)card.flavors[j].sprite=game.catalog.flavorIcons[order.flavors[j]];}
            var toppings=Enumerable.Range(0,6).Where(t=>(order.toppings&(1<<t))!=0).ToArray();
            for(int j=0;j<2;j++){card.toppings[j].gameObject.SetActive(j<toppings.Length);if(j<toppings.Length)card.toppings[j].sprite=game.catalog.toppingIcons[toppings[j]];}
        }
        if (businessPanel.activeSelf)
        {
            var site = game.sites[businessSite];
            panelText.text = site.name + " / $" + site.revenue.ToString("0.##") + " today / " + (site.open ? "Open" : "Closed") + "\n" + string.Join("\n", game.workers.Where(w => w.site == businessSite).Take(2).Select(w => w.Owner + " / $" + w.Wage + " daily / " + w.status));
        }
        if (game.phase == TycoonGameManager.Phase.Results)
        {
            if (!resultsText.gameObject.activeSelf) ClosePanels();
            panel.SetActive(true); menuPanel.SetActive(false); menuOpen = true;
            panelTitle.text = "Day complete"; panelText.gameObject.SetActive(false);
            resultsText.gameObject.SetActive(true); resultsText.text = game.results;
            closeButton.gameObject.SetActive(false); nextButton.gameObject.SetActive(true);
        }
        openButton.interactable=game.phase==TycoonGameManager.Phase.Preparation;
        miniMarker.parent.gameObject.SetActive(!AnyPanel);
        waypointText.gameObject.SetActive(false);
        reticle.SetActive(!AnyPanel);
        miniMarker.anchoredPosition = Vector2.zero;
        fullMarker.anchoredPosition = MapPoint(game.player.transform.position, 470);
        miniMarker.localRotation = Quaternion.Euler(0, 0, -game.player.transform.eulerAngles.y);
        fullMarker.localRotation = miniMarker.localRotation;
        for (int i = 0; i < miniLocations.Length; i++) { miniLocations[i].anchoredPosition = MiniPoint(Location(i),true); mapLocations[i].anchoredPosition = MapPoint(Location(i), 470); }
        for(int i=0;i<miniRoads.Length;i++)miniRoads[i].anchoredPosition=MiniPoint(roadCenters[i],false);
        if(mapPanel.activeSelf)
        {
            var mouse=Mouse.current;mapZoom=Mathf.Clamp(mapZoom+mouse.scroll.ReadValue().y*.002f,.75f,3);mapContent.localScale=Vector3.one*mapZoom;
            if(mouse.rightButton.isPressed)mapContent.anchoredPosition+=mouse.delta.ReadValue()/GetComponent<Canvas>().scaleFactor;
        }
        waypointMarker.gameObject.SetActive(hasWaypoint);
        if (hasWaypoint)
        {
            var direction = waypoint - game.player.transform.position;
            waypointText.text = "Destination / " + Mathf.RoundToInt(direction.magnitude) + " m";
            waypointMarker.anchoredPosition = MiniPoint(waypoint,true);
        }
        else waypointText.text = "M / town map";
    }
    private Vector3 Location(int i)
    {
        return i switch { 0 => game.sites[0].origin.position, 1 => game.supplier.position, 2 => game.sites[1].origin.position, 3 => game.truckStops[0].position, 4 => game.truckStops[1].position, _ => game.bike.transform.position };
    }
    private Vector2 MapPoint(Vector3 point, float size)
    {
        return new Vector2(Mathf.Clamp((point.x - 30) / 130, -.5f, .5f), Mathf.Clamp((point.z - 20) / 110, -.5f, .5f)) * size;
    }
    private Vector2 MiniPoint(Vector3 point,bool edge)
    {
        var delta=point-game.player.transform.position;var result=new Vector2(delta.x,delta.z)/120*185;
        return edge?new Vector2(Mathf.Clamp(result.x,-87,87),Mathf.Clamp(result.y,-87,87)):result;
    }
    private void Show(SlotView slot, TycoonItem item, bool selected)
    {
        slot.label.gameObject.SetActive(item != null && item.kind == TycoonItem.Kind.Equipment);
        slot.label.text = item != null && item.kind == TycoonItem.Kind.Equipment ? game.catalog.Label(item) : "";
        slot.icon.sprite=game.catalog.Icon(item);slot.icon.gameObject.SetActive(slot.icon.sprite!=null);
        slot.bar.transform.parent.gameObject.SetActive(item != null && item.Consumable);
        slot.bar.fillAmount = item == null ? 0 : item.Fill;
        slot.frame.color = selected ? new Color(1,.79f,.88f,1) : new Color(1,1,1,item==null?.34f:.86f);
        slot.frame.rectTransform.localScale=Vector3.one*(selected?1.1f:1);
    }
    public void ClosePanels()
    {
        panel.SetActive(false); inventoryPanel.SetActive(false); shopPanel.SetActive(false); businessPanel.SetActive(false); mapPanel.SetActive(false); menuPanel.SetActive(false);
        closeButton.gameObject.SetActive(true);
        menuOpen = false; transferSelection = -1; nextButton.gameObject.SetActive(false); inspectedWorker = null; assignLockerButton.gameObject.SetActive(false); confirmingNewGame = false;panelText.gameObject.SetActive(true);resultsText.gameObject.SetActive(false);
    }
    public void ToggleMenu()
    {
        if (AnyPanel) { ClosePanels(); return; }
        panel.SetActive(true); menuPanel.SetActive(true); menuOpen = true; panelTitle.text = "Pause";
        panelText.text = "";
    }
    public void ToggleMap()
    {
        if (mapPanel.activeSelf) { ClosePanels(); return; }
        ClosePanels(); panel.SetActive(true); mapPanel.SetActive(true); menuOpen = true; panelTitle.text = "Town map"; panelText.text = "";
    }
    public void ToggleInventory()
    {
        if (inventoryPanel.activeSelf) { ClosePanels(); return; }
        OpenStorage(null, "Inventory / select a source, then a destination", false);
    }
    public void OpenStorage(TycoonInventory inventory, string name, bool allowBulk)
    {
        ClosePanels(); storage = inventory; bulkAllowed = allowBulk; panel.SetActive(true); inventoryPanel.SetActive(true); panelTitle.text = name;
        panelText.text = "";
    }
    public void OpenShop()
    {
        ClosePanels(); panel.SetActive(true); shopPanel.SetActive(true); panelTitle.text = "Wholesale supplies"; panelText.text = "Scoopers go into your hotbar. Collect other supplies from the pickup shelf beside the shop.";
    }
    public void OpenEmployee(TycoonWorker worker)
    {
        OpenStorage(worker.inventory, worker.Owner + " / " + new[] { "Rookie", "Experienced", "Expert" }[worker.tier], false);
        inspectedWorker = worker; assignLockerButton.gameObject.SetActive(true);
        panelText.text = "$" + worker.Wage + " daily / scoop " + worker.ScoopSpeed.ToString("0.##") + "x / pour " + worker.PourSpeed.ToString("0.##") + "x / topping " + worker.FinishSpeed.ToString("0.##") + "x\n" + worker.status + ". Equipment can be changed while off duty.";
    }
    public void OpenBusiness(int site)
    {
        ClosePanels(); businessSite = site; panel.SetActive(true); businessPanel.SetActive(true); panelTitle.text = game.sites[site].name + " / business";
    }
    private void ClickPlayer(int index)
    {
        if (storage != null) { game.player.inventory.Transfer(index, storage, bulkAllowed); return; }
        if (transferSelection < 0) { transferSelection = index; return; }
        var source = game.player.inventory.slots[transferSelection]; var target = game.player.inventory.slots[index];
        if (source != null && target != null && TycoonInventory.Refill(source, target) > 0)
        { if (source.amount == 0 && source.Disposable) game.player.inventory.slots[transferSelection] = null; }
        else { game.player.inventory.slots[index] = source; game.player.inventory.slots[transferSelection] = target; }
        transferSelection = -1;
    }
    private void ClickStorage(int index)
    {
        var item = storage.slots[index];
        if (item == null) return;
        if (item.Bulk)
        {
            var held = game.player.inventory.slots[game.player.selected];
            if (held != null && TycoonInventory.Refill(item, held) > 0)
            { if (item.amount == 0) storage.slots[index] = null; return; }
            if (item.kind == TycoonItem.Kind.BowlPack && game.player.inventory.FreeSlot >= 0)
            {
                var bowls = new TycoonItem(TycoonItem.Kind.Bowls, 0); TycoonInventory.Refill(item, bowls); game.player.inventory.Add(bowls);
                if (item.amount == 0) storage.slots[index] = null; return;
            }
            if (game.player.cargo == null) { game.player.cargo = item; storage.slots[index] = null; }
        }
        else storage.Transfer(index, game.player.inventory);
    }
    private void TransferCargo()
    {
        if (storage == null || game.player.cargo == null) return;
        if (storage.Add(game.player.cargo, true)) game.player.cargo = null;
        else game.notice = "Storage is full.";
    }
}
