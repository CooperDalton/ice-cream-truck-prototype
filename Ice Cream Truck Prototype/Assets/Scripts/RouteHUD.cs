using System;
using UnityEngine;
using UnityEngine.UI;

public class RouteHUD : MonoBehaviour
{
    public RouteGameManager route;
    public GameObject planPanel, pausePanel, resultsPanel, noticePanel;
    public Text planningFunds, emergencyLabel;
    public Text heading, budget, bank, carry, clock, nextStop, supplies, notice, detailTitle, detailStats, detailNeeds, detailBehavior, resultsTitle, resultsText, launchText, deliveryText;
    public Button launch, inspect, resume, emergency, nextDay, unpack;
    public Button[] pointButtons, hotspotButtons, buyButtons, packButtons;
    public Text[] pointLabels, buyLabels, stockLabels;
    [Serializable]
    public class OrderRow
    {
        public GameObject root, sprinkles;
        public Text quantityPrice;
        public Image[] flavors;
    }
    [Serializable]
    public class CrowdCard
    {
        public Text title;
        public OrderRow[] orders;
    }
    public CrowdCard[] crowdCards;
    public RectTransform detailPopup;
    public Button closeDetail, mapBackground;
    public RectTransform map, truckMarker;
    public Vector2 mapMin = new Vector2(-40, -25), mapMax = new Vector2(200, 95);
    public int SelectedHotspot { get; private set; }
    private float noticeTime, refreshTime;

    private void Start()
    {
        launch.onClick.AddListener(route.StartRoute);
        inspect.onClick.AddListener(route.ToggleMap);
        resume.onClick.AddListener(route.day.TogglePause);
        emergency.onClick.AddListener(route.EmergencyStop);
        nextDay.onClick.AddListener(route.NextDay);
        unpack.onClick.AddListener(route.stock.Unpack);
        closeDetail.onClick.AddListener(() => detailPopup.gameObject.SetActive(false));
        mapBackground.onClick.AddListener(() => detailPopup.gameObject.SetActive(false));
        for (int i = 0; i < pointButtons.Length; i++) { int index = i; pointButtons[i].onClick.AddListener(() => { detailPopup.gameObject.SetActive(false); route.CyclePoint(index); }); }
        for (int i = 0; i < hotspotButtons.Length; i++) { int index = i; hotspotButtons[i].onClick.AddListener(() => SelectHotspot(index)); }
        for (int i = 0; i < buyButtons.Length; i++)
        {
            int index = i; buyButtons[i].onClick.AddListener(() => route.stock.Purchase(index));
            packButtons[i].onClick.AddListener(() => route.stock.Pack(index));
        }
        route.stock.Changed += OnStockChanged;
        RefreshPlan();
    }
    private void OnDestroy()
    {
        route.stock.Changed -= OnStockChanged;
    }
    private void OnStockChanged(object sender, EventArgs e)
    {
        RefreshStock();
        RefreshDetail();
    }
    private void Update()
    {
        bool results = route.Phase == RouteGameManager.RoutePhase.Results;
        planPanel.SetActive(route.MapOpen && !results);
        pausePanel.SetActive(route.day.Paused && !results);
        resultsPanel.SetActive(results);
        bool pointer = route.MapOpen || route.day.Paused || results;
        Cursor.lockState = pointer ? CursorLockMode.None : CursorLockMode.Locked;
        Cursor.visible = pointer;
        noticeTime -= Time.unscaledDeltaTime; noticePanel.SetActive(noticeTime > 0 && !results);
        bank.text = "$" + route.Bank + " BANKED";
        carry.text = "$" + route.CarriedCash + " carried  ·  $" + route.BankedToday + "/" + route.Goal + " day";
        clock.text = "DAY " + RouteGameManager.DayNumber + "  •  " + TimeLabel(route.Clock);
        nextStop.text = route.Phase == RouteGameManager.RoutePhase.Planning ? "M  Plan route" : route.Stopped ? "DEPARTING IN " + Mathf.CeilToInt(route.StopRemaining) + "s" : "TRUCK " + Mathf.CeilToInt(Vector3.Distance(route.player.transform.position, route.truck.transform.position)) + "m  •  EXIT IN " + TimeLabel(route.RemainingTimeTo(route.Length));
        emergencyLabel.text = "R  Rescue stop  ·  " + route.EmergencyStops;
        emergency.interactable = route.Phase == RouteGameManager.RoutePhase.Running && !route.Stopped && route.EmergencyStops > 0;
        truckMarker.anchoredPosition = MapPosition(route.truck.transform.position);
        refreshTime -= Time.unscaledDeltaTime;
        if (refreshTime <= 0) { refreshTime = .5f; RefreshPlan(); }
    }
    public static string TimeLabel(float seconds)
    {
        int total = Mathf.Max(0, Mathf.FloorToInt(seconds));
        return (total / 60).ToString("00") + ":" + (total % 60).ToString("00");
    }
    public Vector2 MapPosition(Vector3 world)
    {
        return new Vector2((Mathf.InverseLerp(mapMin.x, mapMax.x, world.x) - .5f) * map.rect.width,
            (Mathf.InverseLerp(mapMin.y, mapMax.y, world.z) - .5f) * map.rect.height);
    }
    public void SelectHotspot(int index)
    {
        bool open = !detailPopup.gameObject.activeSelf || SelectedHotspot != index;
        SelectedHotspot = index;
        detailPopup.gameObject.SetActive(open);
        var point = ((RectTransform)hotspotButtons[index].transform).anchoredPosition;
        float x = point.x + (point.x > 0 ? -325 : 325);
        detailPopup.anchoredPosition = new Vector2(
            Mathf.Clamp(x, -map.rect.width / 2 + 180, map.rect.width / 2 - 180),
            Mathf.Clamp(point.y, -map.rect.height / 2 + 155, map.rect.height / 2 - 155));
        RefreshDetail();
    }
    public void RefreshPlan()
    {
        bool planning = route.Phase == RouteGameManager.RoutePhase.Planning;
        heading.text = "PARK ROUTE  /  DAY " + RouteGameManager.DayNumber;
        planningFunds.text = "$" + route.Bank + "  ·  STOCK " + route.stock.Used + "/" + route.stock.capacity;
        budget.text = "STOPS " + route.Count(RouteGameManager.RouteControl.Stop) + "/" + route.stopBudget + "     SLOW ZONES " + route.Count(RouteGameManager.RouteControl.Slow) + "/" + route.slowBudget + "     EXIT " + TimeLabel(route.ArrivalAt(route.Length));
        launch.gameObject.SetActive(planning);
        for (int i = 0; i < route.points.Length; i++)
        {
            var point = route.points[i];
            pointButtons[i].interactable = planning;
            pointButtons[i].GetComponent<Image>().color = point.control == RouteGameManager.RouteControl.Stop ? new Color(.96f,.56f,.58f) : point.control == RouteGameManager.RouteControl.Slow ? new Color(1,.82f,.38f) : new Color(.95f,.96f,.9f);
            pointLabels[i].text = point.label + "  " + (point.control == RouteGameManager.RouteControl.None ? "PASS" : point.control.ToString().ToUpper()) + "\n" + (!planning && point.distance <= route.Distance ? "DONE" : TimeLabel(planning ? route.ArrivalAt(point.distance) : route.Clock + route.RemainingTimeTo(point.distance)));
        }
        for (int i = 0; i < hotspotButtons.Length; i++)
        {
            var crowd = route.hotspots[i];
            hotspotButtons[i].gameObject.SetActive(crowd.gameObject.activeSelf);
            var card = crowdCards[i];
            card.title.text = crowd.displayName;
            for (int orderIndex = 0; orderIndex < card.orders.Length; orderIndex++)
            {
                var row = card.orders[orderIndex];
                row.root.SetActive(orderIndex < crowd.orders.Length);
                if (orderIndex >= crowd.orders.Length) continue;
                var order = crowd.orders[orderIndex];
                row.quantityPrice.text = "×" + (planning ? order.quantity : crowd.RemainingFor(order)) + "  $" + order.price + " ea";
                for (int scoop = 0; scoop < row.flavors.Length; scoop++)
                {
                    row.flavors[scoop].gameObject.SetActive(scoop < order.recipe.Length);
                    if (scoop < order.recipe.Length) row.flavors[scoop].sprite = order.recipe[scoop].orderPicture;
                }
                row.sprinkles.SetActive(order.sprinkles);
            }
        }
        RefreshStock(); RefreshDetail();
        var pending = new System.Collections.Generic.List<string>();
        foreach (var d in route.Deliveries) if (!d.delivered) pending.Add("6 " + ((RouteStock.Ingredient)d.ingredient) + " · ready " + TimeLabel(d.readyAt) + " · stop " + route.points[d.stop].label);
        deliveryText.text = string.Join("\n", pending);
        if (route.Phase == RouteGameManager.RoutePhase.Results)
        {
            resultsTitle.text = route.LeftBehind ? "The truck left without you" : "Back with the takings";
            resultsText.text = "$" + route.BankedToday + " banked today  •  " + route.Served + " customers served\n$" + route.Bank + " in the register\n\nLost outside: $" + route.LostCash + ", " + route.LostCones + " cones, " + route.LostIngredients + " ingredients\nStorage overflow: " + route.WastedStock + " units\n\nNext day: 2 stops + 2 slow zones, leftover stock and cones.\n" + (route.BankedToday >= route.Goal && !route.LeftBehind ? "Earned one reserve rescue stop. Reserve is capped at one." : "One rescue stop is included every day.") + (route.Bank < 40 ? "\nRecovery fund tops your register up to $40." : "");
        }
    }
    public void RefreshStock()
    {
        bool planning = route.Phase == RouteGameManager.RoutePhase.Planning;
        supplies.text = "STOCK " + route.stock.Used + "/" + route.stock.capacity + "   ·   SUPPLY BAG " + route.stock.Packed + "/6   ·   TRAY " + route.tray.Cones.Count + "/" + route.tray.slots.Length;
        for (int i = 0; i < stockLabels.Length; i++)
        {
            stockLabels[i].text = ((RouteStock.Ingredient)i) + "  " + route.stock.amounts[i];
            buyLabels[i].text = planning ? "+1  $" + route.stock.prices[i] : "+6  $" + (route.stock.prices[i] * 6 + 3);
            buyButtons[i].interactable = route.Phase != RouteGameManager.RoutePhase.Results;
            packButtons[i].interactable = route.truck.InsideTruck && route.stock.amounts[i] > 0 && route.stock.Packed < 6;
        }
        unpack.interactable = route.truck.InsideTruck && route.stock.Packed > 0;
    }
    private void RefreshDetail()
    {
        var h = route.hotspots[SelectedHotspot];
        detailTitle.text = h.displayName;
        detailStats.text = "Open " + TimeLabel(h.opensAt) + "–" + TimeLabel(h.closesAt) + "\nArrive " + TimeLabel(route.ArrivalAt(h.routeDistance));
        int[] needed = h.RequiredStock(route.Phase != RouteGameManager.RoutePhase.Planning); var lines = new System.Collections.Generic.List<string>();
        for (int i = 0; i < needed.Length; i++) if (needed[i] > route.stock.amounts[i]) lines.Add(((RouteStock.Ingredient)i) + "  " + (needed[i] - route.stock.amounts[i]));
        detailNeeds.text = lines.Count == 0 ? "Stock ready" : "Missing\n" + string.Join("\n", lines);
        detailBehavior.text = route.Phase == RouteGameManager.RoutePhase.Planning ? "" : h.Available ? h.Remaining + " remaining" : route.Clock < h.opensAt ? "Not yet open" : "Closed";
    }
    public void Flash(string message)
    {
        notice.text = message;
        noticeTime = 5;
    }
}
