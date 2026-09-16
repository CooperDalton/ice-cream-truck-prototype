using System;
using System.Collections;
using System.Linq;
using System.Threading.Tasks;
using UnityEngine;

// Disposable Play Mode fixture: back up the campaign before running, then restore it.
public static class TycoonWaffleChecks
{
    public static Task<string> Run()
    {
        var result = new TaskCompletionSource<string>();
        TycoonGameManager.Instance.StartCoroutine(Observe(CheckCycle(), result));
        return result.Task;
    }

    private static IEnumerator Observe(IEnumerator checks, TaskCompletionSource<string> result)
    {
        while (true)
        {
            try
            {
                if (!checks.MoveNext()) break;
            }
            catch (Exception exception) { result.SetException(exception); yield break; }
            yield return checks.Current;
        }
        result.SetResult("PASS: visible batter stream and fill ring; interrupted pour resumes for one portion; smooth close/open; six-second cook and ready ring; one cone collected; second cycle burns visibly and discards cleanly.");
    }

    private static IEnumerator CheckCycle()
    {
        var game = TycoonGameManager.Instance; var player = game.player;
        game.restartRequested = true; game.enabled = false; game.tutorial.enabled = false;
        game.tutorial.progress.step = TycoonTutorial.Step.Complete;
        foreach (var worker in game.workers) worker.enabled = false;
        game.hud.ClosePanels(); player.manualInput = true; player.CancelGesture();
        var iron = game.parts.First(p => p.site == 0 && p.kind == TycoonPart.Kind.Iron);
        var feedback = iron.waffleFeedback;
        iron.ironStage = 0; iron.contents = null; iron.claimedBy = ""; iron.pourProgress = 0;
        player.inventory = new TycoonInventory(8);
        player.inventory.slots[0] = new TycoonItem(TycoonItem.Kind.Batter, 10); player.Select(0);
        player.target = iron; player.customerTarget = null; player.workerTarget = null; player.looseTarget = null;
        player.prompt = iron.Prompt();
        player.view.transform.LookAt(iron.transform.position + Vector3.up * .32f);
        yield return new WaitForSeconds(.7f);

        player.Use(false);
        while (iron.pourProgress < .4f)
        {
            player.Gesture(Vector2.zero, Time.deltaTime);
            yield return new WaitForEndOfFrame();
            Check(feedback.pourStream.enabled, "Batter stream is visible during the pour");
            Check(Vector3.Distance(feedback.pourStream.GetPosition(0), player.grip.TransformPoint(TycoonWaffleFeedback.BottleNozzle)) < .001f, "Stream starts at the current bottle nozzle");
            yield return null;
        }
        Check(feedback.rawBatter.gameObject.activeSelf && !feedback.cookedWaffle.activeSelf, "Pouring shows raw batter, not a baked waffle");
        Check(feedback.panel.activeInHierarchy && feedback.ring.fillAmount > .3f && feedback.ring.fillAmount < .6f, "World ring displays partial pour progress");
        Capture("WafflePour");
        yield return new WaitForEndOfFrame();
        player.CancelGesture();
        yield return new WaitForSeconds(.1f);
        Check(!feedback.pourStream.enabled && iron.ironStage == 5 && player.Held.amount == 9, "Stopping hides the stream and retains the charged partial pour");
        player.Use(false);
        while (iron.ironStage == 5)
        {
            player.Gesture(Vector2.zero, Time.deltaTime);
            yield return null;
        }
        yield return new WaitForEndOfFrame();
        Check(iron.ironStage == 1 && player.Held.amount == 9 && feedback.ring.fillAmount == 1 && !feedback.pourStream.enabled, "Resuming finishes one portion and fills the ring");
        player.Use(true);
        Check(iron.ironStage == 2 && !iron.OpenIron("Player"), "E starts cooking and rejects early opening");
        yield return new WaitForSeconds(.1f);
        float closingAngle = Quaternion.Angle(iron.lid.localRotation, Quaternion.identity);
        Check(closingAngle > 1 && closingAngle < 100, "Closing passes through an intermediate angle");
        player.Select(7);
        player.prompt = iron.Prompt();
        yield return new WaitForSeconds(.7f);
        var closed = LidBounds(iron);
        Check(Mathf.Abs(closed.center.z) < .1f && closed.max.y < .3f, "Closed lid covers the plate");
        Check(feedback.ring.fillAmount > 0 && feedback.ring.fillAmount < 1, "Ring advances while cooking");
        Capture("WaffleClosed");
        yield return new WaitForSeconds(5.5f);
        Check(iron.ironStage == 2 && iron.cookTime >= 6 && feedback.ring.fillAmount == 1 && feedback.burnRing.gameObject.activeSelf, "Ready waffle has a full ring and an outer burn timer");
        Check(feedback.cookedWaffle.activeSelf && !feedback.rawBatter.gameObject.activeSelf, "Ready state switches to our baked waffle model");
        player.Use(true);
        player.prompt = iron.Prompt();
        yield return new WaitForSeconds(.1f);
        float openingAngle = Quaternion.Angle(iron.lid.localRotation, Quaternion.identity);
        Check(openingAngle > 1 && openingAngle < 100, "Opening passes through an intermediate angle");
        yield return new WaitForSeconds(.7f);
        Check(iron.ironStage == 3 && LidBounds(iron).max.y > closed.max.y + .25f, "Open lid raises above the waffle");
        Capture("WaffleOpen");
        yield return new WaitForEndOfFrame();
        player.Use(true);
        Check(iron.ironStage == 0 && iron.contents == null && player.inventory.slots.Count(i => i != null && i.kind == TycoonItem.Kind.Cone) == 1, "E collects one cone and resets the iron");
        player.Select(0); player.Use(false); player.Gesture(Vector2.zero, 1); player.Use(true);
        Check(iron.ironStage == 2 && player.Held.amount == 8, "Second cycle consumes exactly one more portion");
        iron.cookTime = 17.8f;
        yield return new WaitForSeconds(.5f);
        Check(iron.ironStage == 4 && feedback.burnRing.fillAmount == 1 && feedback.waffleRenderers.All(r => r.sharedMaterial == feedback.burnedMaterial), "Overcooking fills the burn ring and darkens our waffle model");
        player.Use(false);
        yield return new WaitForEndOfFrame();
        Check(iron.ironStage == 0 && !feedback.cookedWaffle.activeSelf && !feedback.rawBatter.gameObject.activeSelf && !feedback.pourStream.enabled, "Discard clears the waffle and effects");
    }

    private static void Capture(string name)
    {
        var texture = ScreenCapture.CaptureScreenshotAsTexture();
        System.IO.File.WriteAllBytes("Library/CodexPlaytests/" + name + ".png", texture.EncodeToPNG());
        UnityEngine.Object.Destroy(texture);
    }

    private static Bounds LidBounds(TycoonPart iron)
    {
        var points = iron.lid.GetComponentsInChildren<MeshFilter>().SelectMany(f => f.sharedMesh.vertices.Select(v => iron.transform.InverseTransformPoint(f.transform.TransformPoint(v)))).ToArray();
        var bounds = new Bounds(points[0], Vector3.zero);
        foreach (var point in points) bounds.Encapsulate(point);
        return bounds;
    }

    private static void Check(bool value, string message)
    {
        if (!value) throw new InvalidOperationException(message);
    }
}
