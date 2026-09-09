using System;
using UnityEngine;
using UnityEngine.UI;

public class PrototypeHUD : MonoBehaviour
{
    public DayManager day;
    public CustomerManager customers;
    public RouteHUD routeHUD;
    public Text clockText, moneyText, orderText, promptText, heldText, messageText, resultText, queueText, waffleText;
    public Image progressRing, patienceFill, quotaFill;
    public GameObject pausePanel, resultPanel;
    public Button resumeButton, restartButton, retryButton;
    public WaffleMaker waffle;
    public TruckController truck;
    public Text drivingText, resultsButtonText;
    public Text dayText, quotaText, resultTitleText;
    private float messageTime;
    private void Start()
    {
        resumeButton.onClick.AddListener(day.TogglePause);
        restartButton.onClick.AddListener(day.RestartDay);
        retryButton.onClick.AddListener(day.ContinueAfterResults);
        day.Changed += OnDayChanged;
        RefreshPanels();
    }
    private void OnDestroy()
    {
        day.Changed -= OnDayChanged;
    }
    private void OnDayChanged(object sender, EventArgs e)
    {
        RefreshPanels();
    }
    private void RefreshPanels()
    {
        pausePanel.SetActive(day.Paused);
        resultPanel.SetActive(day.Phase == DayManager.DayPhase.Closed);
        bool success = day.QuotaMet;
        resultTitleText.text = success ? "A sweet day's work!" : "Let's try that day again";
        resultText.text = "$" + day.Earnings + " earned  /  $" + day.Quota + " goal\n\n" + day.OrdersServed + (day.OrdersServed == 1 ? " order served\n" : " orders served\n") + day.CustomersLost + (day.CustomersLost == 1 ? " customer left" : " customers left") + (success ? "\n\nThe next day starts in a moment." : "\n\nReach the goal before closing time.");
    }
    private void Update()
    {
        dayText.text = "DAY " + DayManager.DayNumber;
        clockText.text = day.ClockLabel;
        moneyText.text = "$" + day.Earnings + "/" + day.Quota;
        quotaFill.fillAmount = day.Quota == 0 ? 1 : Mathf.Clamp01((float)day.Earnings / day.Quota);
        resultsButtonText.text = day.QuotaMet ? "Next day" : "Try again";
        if (day.CanPlay) messageTime -= Time.deltaTime;
        if (messageTime <= 0) messageText.text = "";
    }
    public void ShowMessage(string message)
    {
        if (routeHUD != null) routeHUD.Flash(message);
        messageText.text = message;
        messageTime = day.settings.messageSeconds;
    }
}
