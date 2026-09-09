using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEngine;
using UnityEngine.UI;

public static class ScoopWorldUIPlaytest
{
    static PrototypeSceneReferences r;
    static List<string> checks;
    static void Begin()
    {
        r = PrototypeSceneReferences.Instance;
        r.player.ManualInput = r.interaction.ManualInput = r.truck.ManualInput = r.customers.ManualInput = true;
        checks = new List<string>();
    }
    static void Check(bool value, string message)
    {
        if (!value) throw new Exception("SCOOP/UI TEST FAILED: " + message);
        checks.Add(message);
    }
    static string Report(string name)
    {
        string report = "PASS " + checks.Count + " checks\n" + string.Join("\n", checks);
        File.WriteAllText("Library/CodexPlaytests/" + name + ".txt", report);
        return report;
    }
    static void Aim(Interactable target)
    {
        Vector3 position = target.transform.position;
        r.player.controller.enabled = false;
        r.player.transform.position = new Vector3(Mathf.Clamp(position.x + (target is IceCreamTub ? .65f : 0), -2.8f, .8f), .64f, .10f);
        r.player.controller.enabled = true;
        r.player.view.transform.LookAt(target.GetComponent<Collider>().bounds.center);
        Physics.SyncTransforms();
        r.interaction.ProcessInput(false, false, false, false, Vector2.zero, .02f);
        Check(r.interaction.Target == target, "Scene ray reaches " + target.name);
    }
    static void Input(bool pressed, bool held, float delta)
    {
        Physics.SyncTransforms();
        r.interaction.ProcessInput(pressed, held, !held, false, new Vector2(0, delta), .02f);
    }
    public static async System.Threading.Tasks.Task<string> PartialScoop()
    {
        Begin();
        r.interaction.PickUp(r.scooper);
        Aim(r.tubs[0]);
        Input(true, true, 0);
        for (int i = 0; i < 60; i++) Input(false, true, 0);
        Check(r.tubs[0].Progress == 0 && !r.scooper.loadedScoop.activeSelf, "Holding still produces no ice cream");
        for (int i = 0; i < 10; i++) Input(false, true, i % 2 == 0 ? 20 : -20);
        Check(r.tubs[0].Progress > .15f && r.tubs[0].Progress < .25f, "Ten short strokes advance scoop to 20 percent");
        Check(r.scooper.loadedScoop.activeSelf && r.scooper.LoadedFlavor == null, "Partial scoop is visible but cannot be served");
        Check(r.scooper.loadedScoop.transform.localScale.x > .5f && r.scooper.loadedScoop.transform.localScale.x < .7f, "Visible ball grows with collected volume");
        Check(Vector3.Distance(r.scooper.loadedScoop.transform.position, r.tubs[0].ScoopPosition) < .001f, "Scoop bowl is positioned on the selected tub path");
        EditorApplication.isPaused = false;
        for (int i = 0; i < 20; i++) await Awaitable.NextFrameAsync();
        EditorApplication.isPaused = true;
        ScreenCapture.CaptureScreenshot("Library/CodexPlaytests/scoop-partial.png");
        EditorApplication.Step();
        return Report("scoop-partial");
    }
    public static string ScoopingAndCancellation()
    {
        Begin();
        var hands = r.player.GetComponent<FloatingHands>();
        Check(Vector3.Distance(hands.rightHandBone.position, r.interaction.handAnchor.position) < .2f, "Floating right hand follows the scoop at the tub");
        var initial = r.scooper.loadedScoop.transform.position;
        Input(false, true, 180);
        var top = r.scooper.loadedScoop.transform.position;
        Check(Vector3.Distance(top, r.tubs[0].scoopTop.position) < .001f && Vector3.Distance(initial, top) > .05f, "Upward mouse motion reaches top endpoint");
        float progress = r.tubs[0].Progress;
        for (int i = 0; i < 20; i++) Input(false, true, 180);
        Check(Mathf.Abs(r.tubs[0].Progress - progress) < .0001f, "Dragging past endpoint cannot farm progress");
        Input(false, true, -180);
        Check(Vector3.Distance(r.scooper.loadedScoop.transform.position, r.tubs[0].scoopBottom.position) < .001f, "Downward mouse motion reaches bottom endpoint");
        Input(false, false, 0);
        Check(!r.interaction.Gesturing && !r.scooper.loadedScoop.activeSelf && r.tubs[0].Progress == 0, "Releasing early clears partial ice cream and exits tub pose");
        Vector3 rest = r.interaction.handAnchor.localPosition;
        for (int tubIndex = 0; tubIndex < r.tubs.Length; tubIndex++)
        {
            var tub = r.tubs[tubIndex];
            Aim(tub); Input(true, true, 0);
            Input(false, true, 180);
            Check(Vector3.Distance(r.scooper.loadedScoop.transform.position, tub.scoopTop.position) < .001f, tub.flavor.displayName + " has its own scoop endpoint");
            for (int i = 0; i < 60; i++) Input(false, true, i % 2 == 0 ? -20 : 20);
            Check(r.scooper.LoadedFlavor == tub.flavor && r.scooper.loadedScoop.transform.localScale == Vector3.one, tub.flavor.displayName + " completes a full-size scoop");
            Check(!r.interaction.Gesturing && r.interaction.handAnchor.localPosition == rest, tub.flavor.displayName + " returns loaded scoop to hand");
            Input(false, false, 0); r.scooper.EmptyScoop();
        }
        Aim(r.tubs[1]); Input(true, true, 20);
        r.day.TogglePause(); Input(false, true, 20);
        Check(!r.interaction.Gesturing && !r.scooper.loadedScoop.activeSelf, "Pause cancels incomplete scoop");
        r.day.TogglePause();
        Aim(r.tubs[2]); Input(true, true, 20);
        r.interaction.ProcessInput(false, true, false, true, Vector2.zero, .02f);
        Check(r.interaction.Held == null && !r.scooper.loadedScoop.activeSelf, "Returning scooper cancels partial ice cream");
        Check(!r.hud.promptText.gameObject.activeInHierarchy && !r.hud.heldText.gameObject.activeInHierarchy && !r.hud.messageText.gameObject.activeInHierarchy && !r.hud.orderText.gameObject.activeInHierarchy && !r.hud.progressRing.gameObject.activeInHierarchy, "Instruction box, held label, feedback text, HUD order and cursor ring are hidden");
        Check(r.hud.clockText.gameObject.activeInHierarchy && r.hud.moneyText.gameObject.activeInHierarchy, "Clock and earnings remain visible");
        return Report("scoop-all-tubs");
    }
    public static string WaffleReady()
    {
        Begin();
        Aim(r.waffle); r.waffle.Use(r.interaction);
        r.interaction.PickUp(r.batter);
        Input(true, true, 0);
        for (int i = 0; i < 90; i++) Input(false, true, 0);
        Input(false, false, 0);
        Check(r.waffle.State == WaffleMaker.CookState.BatterReady, "Pouring still fills the waffle maker");
        r.batter.Drop(r.interaction);
        r.waffle.Use(r.interaction);
        r.waffle.Advance(r.day.settings.cookSeconds + .1f);
        Check(r.waffle.State == WaffleMaker.CookState.Ready, "Waffle reaches ready state");
        var indicator = r.waffle.GetComponentInChildren<WaffleIndicator>(true);
        Check(indicator.canvas.renderMode == RenderMode.WorldSpace && indicator.transform.IsChildOf(r.waffle.transform), "Waffle indicator is authored in world space above the machine");
        ScreenCapture.CaptureScreenshot("Library/CodexPlaytests/waffle-world-ready.png");
        EditorApplication.Step();
        return Report("waffle-world-ready");
    }
    public static string VerifyWaffleAndShowOrder()
    {
        Begin();
        var indicator = r.waffle.GetComponentInChildren<WaffleIndicator>(true);
        Check(indicator.panel.activeInHierarchy && indicator.ring.fillAmount == 1 && indicator.ring.color.g > indicator.ring.color.r, "Ready waffle displays full green ring");
        Check(Quaternion.Angle(indicator.transform.rotation, r.player.view.transform.rotation) < .1f, "Waffle canvas faces player camera");
        r.customers.AttractNearby();
        var front = r.customers.Front ?? r.customers.SpawnCustomer();
        Check(front != null, "A resident joins the order test queue");
        for (int i = 0; i < 1000 && !front.Arrived; i++) foreach (var c in r.customers.Queue.ToArray()) c.Advance(.05f);
        Check(front.Arrived, "Customer reaches window");
        front.Initialize(r.customers, new List<FlavorSO> {r.tubs[2].flavor, r.tubs[0].flavor, r.tubs[1].flavor}, true);
        r.player.Teleport(r.truck.transform, r.truck.transform.TransformPoint(new Vector3(-1.1f, .68f, .6f)), r.truck.transform.rotation);
        r.player.view.transform.LookAt(front.transform.position + Vector3.up * 2.3f);
        Physics.SyncTransforms();
        r.interaction.ProcessInput(false, false, false, false, Vector2.zero, .02f);
        ScreenCapture.CaptureScreenshot("Library/CodexPlaytests/generated-order-bubble.png");
        EditorApplication.Step();
        return Report("waffle-and-order");
    }
    public static string VerifyOrder()
    {
        Begin();
        var front = r.customers.Front;
        var bubble = front.GetComponentInChildren<OrderBubble>(true);
        Check(bubble.panel.activeInHierarchy, "Front customer has visible picture bubble");
        Check(bubble.scoops.Count(s => s.gameObject.activeSelf) == 3 && bubble.sprinkles.activeSelf, "Three-scoop order shows three pictures and sprinkles");
        for (int i = 0; i < 3; i++) Check(bubble.scoops[i].sprite == front.Order[i].orderPicture, "Order picture matches flavor at stack index " + i);
        Check(!bubble.flavors.gameObject.activeInHierarchy, "Order uses pictures without flavor instruction text");
        Check(Quaternion.Angle(bubble.transform.rotation, r.player.view.transform.rotation) < .1f, "Order bubble faces player camera");
        foreach (var flavor in r.customers.flavors) Check(flavor.orderPicture != null, flavor.displayName + " has imported generated picture");
        return Report("generated-order-bubble");
    }
}
