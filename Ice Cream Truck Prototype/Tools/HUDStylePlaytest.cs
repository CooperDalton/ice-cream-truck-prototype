using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Threading.Tasks;
using UnityEditor;
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.UI;

public static class HUDStylePlaytest
{
    static PrototypeSceneReferences r;
    static List<string> checks;
    static void Setup()
    {
        r = PrototypeSceneReferences.Instance;
        r.player.ManualInput = r.interaction.ManualInput = r.truck.ManualInput = r.customers.ManualInput = true;
        checks = new List<string>();
        EditorApplication.isPaused = false;
    }
    static void Check(bool value, string message)
    {
        if (!value) throw new Exception("HUD TEST FAILED: " + message);
        checks.Add(message);
    }
    static async Task Frames()
    {
        for (int i = 0; i < 5; i++) await Awaitable.NextFrameAsync();
        Canvas.ForceUpdateCanvases();
    }
    static string Report(string filename)
    {
        EditorApplication.isPaused = true;
        string report = "PASS " + checks.Count + " checks\n" + string.Join("\n", checks);
        File.WriteAllText("Library/CodexPlaytests/" + filename + ".txt", report);
        return report;
    }
    static void ButtonHit(Button button)
    {
        var pointer = new PointerEventData(EventSystem.current);
        pointer.position = RectTransformUtility.WorldToScreenPoint(null, button.transform.position);
        var hits = new List<RaycastResult>();
        EventSystem.current.RaycastAll(pointer, hits);
        Check(hits.Count > 0 && hits[0].gameObject == button.gameObject, "Pointer ray reaches " + button.GetComponentInChildren<Text>().text);
    }
    public static async Task<string> Orders()
    {
        Setup();
        var front = r.customers.Front ?? r.customers.SpawnCustomer();
        for (int i = 0; i < 2000 && !front.Arrived; i++) foreach (var customer in r.customers.Queue.ToArray()) customer.Advance(.05f);
        Check(front.Arrived, "Order test customer reaches serving window");
        r.player.Teleport(r.truck.transform, r.truck.transform.TransformPoint(new Vector3(-1.1f, .68f, .6f)), r.truck.transform.rotation);
        r.player.view.transform.LookAt(front.transform.position + Vector3.up * 2.3f);
        var bubble = front.GetComponentInChildren<OrderBubble>(true);
        float previousHeight = 0;
        for (int count = 1; count <= 3; count++)
        {
            front.Initialize(r.customers, new List<FlavorSO>(r.customers.flavors.Take(count)), count == 3);
            await Frames();
            Check(bubble.panel.activeInHierarchy && bubble.scoops.Count(s => s.gameObject.activeSelf) == count, count + "-scoop order displays correct picture count");
            float height = ((RectTransform)bubble.panel.transform).rect.height;
            Check(height > previousHeight + 50, "Authored layout fits " + count + " scoops without empty slots");
            previousHeight = height;
            for (int i = 0; i < count; i++)
            {
                Check(bubble.scoops[i].sprite == front.Order[i].orderPicture, "Generated picture matches order index " + i);
                if (i > 0) Check(bubble.scoops[i].transform.localPosition.y > bubble.scoops[i - 1].transform.localPosition.y, "Pictures keep bottom-to-top flavor order");
            }
            Check(bubble.sprinkles.activeSelf == (count == 3), "Sprinkles appear only when requested");
            Check(Quaternion.Angle(bubble.transform.rotation, r.player.view.transform.rotation) < .1f, "Picture bubble faces camera");
            ScreenCapture.CaptureScreenshot("Library/CodexPlaytests/illustrated-order-" + count + ".png");
            await Frames();
        }
        r.player.view.transform.Rotate(0, 12, 0, Space.World);
        await Frames();
        Check(Quaternion.Angle(bubble.transform.rotation, r.player.view.transform.rotation) < .1f, "Order bubble follows changed viewing angle");
        return Report("illustrated-orders");
    }
    public static async Task<string> WaffleStates()
    {
        Setup();
        r.player.controller.enabled = false;
        r.player.transform.position = new Vector3(r.waffle.transform.position.x, .64f, .10f);
        r.player.controller.enabled = true;
        r.player.view.transform.LookAt(r.waffle.GetComponent<Collider>().bounds.center);
        Physics.SyncTransforms();
        r.interaction.ProcessInput(false, false, false, false, Vector2.zero, .02f);
        var indicator = r.waffle.GetComponentInChildren<WaffleIndicator>(true);
        await Frames();
        Check(indicator.panel.activeInHierarchy, "Hovering empty waffle maker shows world click icon");
        r.waffle.Use(r.interaction);
        r.interaction.PickUp(r.batter);
        r.waffle.Gesture(r.interaction, Vector2.zero, r.day.settings.pourSeconds);
        r.waffle.StopGesture(); r.batter.Drop(r.interaction);
        await Frames();
        Check(indicator.ring.fillAmount == 1 && indicator.ring.color.g > indicator.ring.color.r, "Filled batter displays green ring");
        r.waffle.Use(r.interaction); r.waffle.Advance(r.day.settings.cookSeconds * .5f);
        await Frames();
        Check(indicator.ring.fillAmount > .45f && indicator.ring.fillAmount < .7f, "Cooking advances the ring above the machine");
        r.waffle.Advance(r.day.settings.cookSeconds * .5f);
        await Frames();
        Check(r.waffle.State == WaffleMaker.CookState.Ready && indicator.ring.fillAmount == 1 && indicator.ring.color.g > indicator.ring.color.r, "Ready waffle shows full green ring");
        ScreenCapture.CaptureScreenshot("Library/CodexPlaytests/illustrated-waffle-ready.png");
        await Frames();
        r.waffle.Advance(r.day.settings.burnGraceSeconds + 1);
        await Frames();
        Check(indicator.ring.fillAmount == 1 && indicator.ring.color.r > indicator.ring.color.g, "Burned waffle shows full red ring");
        Check(Quaternion.Angle(indicator.transform.rotation, r.player.view.transform.rotation) < .1f, "Waffle indicator follows camera after moving from serving window");
        r.waffle.Use(r.interaction); r.waffle.Use(r.interaction);
        await Frames();
        Check(r.waffle.State == WaffleMaker.CookState.Empty && indicator.ring.fillAmount < .1f, "Clearing burned waffle resets ring");
        return Report("illustrated-waffle-states");
    }
    public static async Task<string> HUDAndPause()
    {
        Setup();
        int before = r.day.Earnings;
        r.day.RecordSale(25);
        await Frames();
        Check(r.hud.moneyText.text == "$" + (before + 25), "Sale updates earnings next to coin icon");
        Check(Mathf.Abs(r.hud.quotaFill.fillAmount - (float)r.day.Earnings / r.day.Quota) < .001f, "Sale updates daily goal meter");
        Check(r.hud.clockText.text == r.day.ClockLabel && r.hud.dayText.text == "DAY " + DayManager.DayNumber, "Clock card displays current day and time");
        Check(!r.hud.promptText.gameObject.activeInHierarchy && !r.hud.orderText.gameObject.activeInHierarchy, "Instruction and duplicate order overlays remain hidden");
        r.day.TogglePause();
        await Frames();
        Check(r.hud.pausePanel.activeSelf && !r.day.CanPlay, "Pause opens styled menu and pauses game");
        ButtonHit(r.hud.resumeButton); ButtonHit(r.hud.restartButton);
        ScreenCapture.CaptureScreenshot("Library/CodexPlaytests/illustrated-pause.png");
        await Frames();
        r.hud.resumeButton.onClick.Invoke();
        Check(!r.hud.pausePanel.activeSelf && r.day.CanPlay, "Resume button closes menu and resumes game");
        return Report("illustrated-hud-pause");
    }
    public static async Task<string> FailedDay()
    {
        Setup();
        r.day.Advance(r.day.settings.dayDurationSeconds - r.day.Elapsed);
        await Frames();
        Check(r.hud.resultPanel.activeSelf && !r.day.QuotaMet, "Missed quota opens styled results");
        Check(r.hud.resultsButtonText.text == "Try again" && r.hud.resultTitleText.text.Contains("try"), "Failure displays retry copy");
        ButtonHit(r.hud.retryButton);
        ScreenCapture.CaptureScreenshot("Library/CodexPlaytests/illustrated-results-failure.png");
        await Frames();
        return Report("illustrated-results-failure");
    }
    public static async Task<string> SuccessfulDay()
    {
        Setup();
        r.day.RecordSale(r.day.Quota);
        r.day.Advance(r.day.settings.dayDurationSeconds - r.day.Elapsed);
        await Frames();
        Check(r.hud.resultPanel.activeSelf && r.day.QuotaMet, "Met quota opens styled success results");
        Check(r.hud.resultsButtonText.text == "Next day" && r.hud.resultTitleText.text.Contains("sweet"), "Success displays next-day copy");
        ButtonHit(r.hud.retryButton);
        ScreenCapture.CaptureScreenshot("Library/CodexPlaytests/illustrated-results-success.png");
        await Frames();
        return Report("illustrated-results-success");
    }
}
