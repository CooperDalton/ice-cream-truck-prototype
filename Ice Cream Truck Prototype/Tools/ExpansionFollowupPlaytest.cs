using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using UnityEngine;
using UnityEditor;

public static class ExpansionFollowupPlaytest
{
    static void Check(bool value, string message, List<string> checks)
    {
        if (!value) throw new Exception("FOLLOWUP FAILED: " + message);
        checks.Add(message);
    }
    static string Report(string name, List<string> checks)
    {
        var report = "PASS\n" + string.Join("\n", checks); File.WriteAllText("Library/CodexPlaytests/" + name + ".txt", report); return report;
    }
    public static string TruckAttraction()
    {
        var r = PrototypeSceneReferences.Instance; var checks = new List<string>();
        if (r.interaction.Held != null) r.holders[2].Use(r.interaction);
        if (r.boombox.Playing) r.boombox.ToggleMusic();
        r.customers.ReleaseQueue();
        r.truck.transform.position = new Vector3(-24, 0, 0); Physics.SyncTransforms();
        r.customers.AttractNearby();
        Check(r.customers.Queue.Count > 0, "Parked truck attracts nearby residents with music off", checks);
        var front = r.customers.Front;
        for (int i = 0; i < 1000 && !front.Arrived; i++) foreach (var c in r.customers.Queue.ToArray()) c.Advance(.05f);
        Check(front.Arrived, "Customer routes to window after truck changes location", checks);
        front.Initialize(r.customers, new List<FlavorSO> { r.tubs[2].flavor, r.tubs[0].flavor, r.tubs[1].flavor }, true);
        r.player.Teleport(r.truck.transform, r.truck.transform.TransformPoint(new Vector3(-1.1f, .68f, .6f)), r.truck.transform.rotation);
        r.player.view.transform.LookAt(front.transform.position + Vector3.up * 1.85f);
        Physics.SyncTransforms();
        r.interaction.ProcessInput(false, false, false, false, Vector2.zero, .02f);
        Check(r.interaction.Target == front, "Customer remains clickable after driving to another stop", checks);
        ScreenCapture.CaptureScreenshot("Library/CodexPlaytests/picture-order-final.png"); EditorApplication.Step();
        return Report("expansion-truck-attraction", checks);
    }
    public static string BubbleAndBoombox()
    {
        var r = PrototypeSceneReferences.Instance; var checks = new List<string>();
        var c = r.customers.Front;
        // Test reads the authored customer's own hierarchy, not a global scene search.
        var bubble = c.GetComponentInChildren<OrderBubble>(true);
        Check(bubble.panel.activeInHierarchy, "Front customer's picture card is visible", checks);
        Check(bubble.scoops.Count(s => s.gameObject.activeSelf) == 3 && bubble.sprinkles.activeSelf, "Picture shows three scoops and requested sprinkles", checks);
        for (int i = 0; i < 3; i++) Check(bubble.scoops[i].sprite == c.Order[i].orderPicture, "Generated flavor picture matches scoop " + (i + 1), checks);
        r.customers.ReleaseQueue();
        r.truck.transform.position = Vector3.zero; Physics.SyncTransforms();
        r.player.Teleport(r.truck.transform, r.truck.kitchen.position, r.truck.kitchen.rotation);
        Check(r.interaction.PickUp(r.boombox), "Boombox can be carried", checks);
        r.player.Teleport(null, r.truck.transform.TransformPoint(new Vector3(-5, 0, 0)), Quaternion.identity);
        r.boombox.ReturnHome(r.interaction);
        Check(r.interaction.Held == null && r.boombox.transform.parent == null && r.boombox.pickupCollider.enabled, "Boombox can be placed on outside ground", checks);
        r.boombox.ToggleMusic();
        Check(r.boombox.Playing && r.customers.InAttractionRange(r.boombox.transform.position + Vector3.forward * 30), "Placed boombox broadcasts its larger attraction radius", checks);
        r.interaction.PickUp(r.boombox); r.player.Teleport(r.truck.transform, r.truck.kitchen.position, r.truck.kitchen.rotation); r.boombox.ReturnHome(r.interaction);
        Check(r.boombox.transform.parent == r.truck.transform, "Boombox returns to truck and follows it", checks);
        return Report("expansion-bubble-boombox", checks);
    }
    public static string BeginNextDay()
    {
        var r = PrototypeSceneReferences.Instance; var checks = new List<string>();
        r.day.RecordSale(Mathf.Max(0, r.day.Quota - r.day.Earnings));
        r.day.Advance(r.day.settings.dayDurationSeconds - r.day.Elapsed);
        Check(r.day.Hour == 18 && r.day.QuotaMet && r.hud.resultPanel.activeSelf, "Quota success shows results at 6 PM", checks);
        r.day.Advance(r.day.settings.nextDayDelay - .1f);
        Check(DayManager.DayNumber == 1, "Results remain visible before next-day delay ends", checks);
        r.day.Advance(.11f);
        return Report("expansion-next-day-trigger", checks);
    }
    public static string VerifyNextDay()
    {
        var r = PrototypeSceneReferences.Instance; var checks = new List<string>();
        Check(DayManager.DayNumber == 2 && r.day.ClockLabel == "8:00 AM", "Automatic transition starts day two at 8 AM", checks);
        Check(r.day.Earnings == 0 && r.day.CanPlay && !r.hud.resultPanel.activeSelf, "New day resets earnings and resumes play", checks);
        Check(r.day.Quota == r.day.settings.quota + r.day.settings.quotaIncreasePerDay, "Next day applies editable quota increase", checks);
        return Report("expansion-next-day", checks);
    }
    public static string WorldSeeds()
    {
        var r = PrototypeSceneReferences.Instance; var checks = new List<string>();
        r.customers.ManualInput = r.player.ManualInput = r.interaction.ManualInput = r.truck.ManualInput = true;
        var fingerprints = new List<string>();
        foreach (int seed in new[] { 4312, 8123, 4312 })
        {
            r.world.Generate(seed);
            fingerprints.Add(string.Join(",", r.world.RoadPorts.Cast<int>()));
            int width = r.world.RoadPorts.GetLength(0), center = width / 2;
            foreach (Transform tile in r.world.generatedRoot)
            {
                if (!tile.gameObject.activeSelf) continue;
                var ports = tile.GetComponentsInChildren<Transform>().Where(t => t.name.Contains("RoadPort_")).ToArray();
                if (ports.Length == 0) continue;
                int mask = 0;
                foreach (var port in ports)
                {
                    var delta = port.position - tile.position;
                    int d = Mathf.Abs(delta.x) > Mathf.Abs(delta.z) ? (delta.x > 0 ? 1 : 3) : (delta.z > 0 ? 0 : 2);
                    mask |= 1 << d;
                    Check(Mathf.Abs(Mathf.Max(Mathf.Abs(delta.x), Mathf.Abs(delta.z)) - r.day.settings.tileSize / 2) < .01f, "Road port lies on tile edge", checks);
                }
                int x = Mathf.RoundToInt(tile.position.x / r.day.settings.tileSize) + center;
                int z = Mathf.RoundToInt(tile.position.z / r.day.settings.tileSize) + center;
                Check(mask == r.world.RoadPorts[x, z], "Actual model ports match generated road mask at " + x + "," + z, checks);
            }
        }
        Check(fingerprints[0] != fingerprints[1], "Different seeds produce different roads", checks);
        Check(fingerprints[0] == fingerprints[2], "Same seed reproduces the same roads", checks);
        return Report("expansion-world-seeds", checks);
    }
}
