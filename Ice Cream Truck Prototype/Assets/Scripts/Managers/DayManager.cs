using System;
using UnityEngine;
using UnityEngine.SceneManagement;

public class DayManager : MonoBehaviour
{
    public enum DayPhase { Open, Closed }
    public PrototypeSettingsSO settings;
    public Light sun;
    public RouteGameManager route;
    public static int DayNumber { get; private set; } = 1;
    public int Quota => settings.quota + (DayNumber - 1) * settings.quotaIncreasePerDay;
    public bool QuotaMet => Earnings >= Quota;
    private float closedTime;
    [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.SubsystemRegistration)]
    static void ResetSession() { DayNumber = 1; }
    public DayPhase Phase { get; private set; }
    public float Elapsed { get; private set; }
    public int Earnings { get; private set; }
    public int OrdersServed { get; private set; }
    public int CustomersLost { get; private set; }
    public bool Paused { get; private set; }
    public float Hour => Mathf.Lerp(settings.openingHour, settings.closingHour, Elapsed / settings.dayDurationSeconds);
    public string ClockLabel
    {
        get
        {
            int totalMinutes = Mathf.FloorToInt(Hour * 60) % 1440;
            int hour = totalMinutes / 60;
            return (hour % 12 == 0 ? 12 : hour % 12) + ":" + (totalMinutes % 60).ToString("00") + (hour < 12 ? " AM" : " PM");
        }
    }
    public bool CanPlay => Phase == DayPhase.Open && !Paused && (route == null || route.CanPlay);
    public event EventHandler Changed;

    private void Update()
    {
        if (route != null) return;
        Advance(Time.deltaTime);
        if (sun != null)
        {
            float progress = Mathf.InverseLerp(settings.openingHour, settings.closingHour, Hour);
            sun.transform.rotation = Quaternion.Euler(Mathf.Lerp(20, 160, progress), -35, 0);
            sun.intensity = Mathf.Lerp(.6f, 1.5f, Mathf.Sin(progress * Mathf.PI));
            sun.color = Color.Lerp(new Color(1, .7f, .45f), Color.white, Mathf.Sin(progress * Mathf.PI));
        }
    }
    public void Advance(float seconds)
    {
        if (Phase == DayPhase.Closed)
        {
            if (QuotaMet)
            {
                closedTime += seconds;
                if (closedTime >= settings.nextDayDelay) NextDay();
            }
            return;
        }
        if (!CanPlay) return;
        Elapsed = Mathf.Min(Elapsed + seconds, settings.dayDurationSeconds);
        if (Elapsed >= settings.dayDurationSeconds)
        {
            Phase = DayPhase.Closed;
            Cursor.lockState = CursorLockMode.None;
            Cursor.visible = true;
            Changed?.Invoke(this, EventArgs.Empty);
        }
    }
    public bool RecordSale(int amount)
    {
        if (!CanPlay) return false;
        Earnings += amount;
        OrdersServed++;
        Changed?.Invoke(this, EventArgs.Empty);
        return true;
    }
    public void RecordLostCustomer()
    {
        CustomersLost++;
        Changed?.Invoke(this, EventArgs.Empty);
    }
    public void TogglePause()
    {
        if (Phase != DayPhase.Open) return;
        Paused = !Paused;
        Cursor.lockState = Paused ? CursorLockMode.None : CursorLockMode.Locked;
        Cursor.visible = Paused;
        Changed?.Invoke(this, EventArgs.Empty);
    }
    public void NextDay()
    {
        if (Phase != DayPhase.Closed || !QuotaMet) return;
        DayNumber++;
        SceneManager.LoadScene(SceneManager.GetActiveScene().buildIndex);
    }
    public void ContinueAfterResults()
    {
        if (QuotaMet) NextDay(); else RestartDay();
    }
    public static void BeginRun()
    {
        DayNumber = 1;
    }
    public void RestartDay()
    {
        SceneManager.LoadScene(SceneManager.GetActiveScene().buildIndex);
    }
}
