using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using UnityEngine;
using UnityEditor;
using Object = UnityEngine.Object;

public static class ExpansionPlaytest
{
    static List<string> checks;
    static void Check(bool value, string message)
    {
        if (!value) throw new Exception("EXPANSION FAILED: " + message);
        checks.Add(message);
    }
    static string Report(string name)
    {
        string report = "PASS\n" + string.Join("\n", checks);
        Directory.CreateDirectory("Library/CodexPlaytests");
        File.WriteAllText("Library/CodexPlaytests/" + name + ".txt", report); return report;
    }
    public static string DrivingAndWorld()
    {
        var r = PrototypeSceneReferences.Instance; checks = new List<string>();
        r.player.ManualInput = r.interaction.ManualInput = r.truck.ManualInput = r.customers.ManualInput = true;
        Check(r.day.settings.dayDurationSeconds == 7200, "12 real seconds per game minute yields a 7200-second day");
        int[,] ports = r.world.RoadPorts; int width = ports.GetLength(0), total = 0;
        Vector2Int[] dirs = { Vector2Int.up, Vector2Int.right, Vector2Int.down, Vector2Int.left };
        var seen = new HashSet<Vector2Int>(); var queue = new Queue<Vector2Int>(); queue.Enqueue(new Vector2Int(2, 2));
        for (int x = 0; x < width; x++) for (int z = 0; z < width; z++)
        {
            if (ports[x, z] == 0) continue; total++;
            for (int d = 0; d < 4; d++) if ((ports[x, z] & (1 << d)) != 0)
            {
                var p = new Vector2Int(x, z) + dirs[d];
                Check(p.x >= 0 && p.y >= 0 && p.x < width && p.y < width && (ports[p.x, p.y] & (1 << ((d + 2) % 4))) != 0, "Reciprocal road port " + x + "," + z + " direction " + d);
            }
        }
        while (queue.Count > 0)
        {
            var p = queue.Dequeue(); if (!seen.Add(p)) continue;
            for (int d = 0; d < 4; d++) if ((ports[p.x, p.y] & (1 << d)) != 0) queue.Enqueue(p + dirs[d]);
        }
        Check(seen.Count == total, "All " + total + " road cells form one connected network");
        Check(r.world.Hotspots.Any(h => h.park) && r.world.Hotspots.Any(h => !h.park), "Parks and residential hotspots both exist");
        Check(r.customers.Residents.Any(c => c.IsChild) && r.customers.Residents.Any(c => !c.IsChild), "Child and adult residents spawned");
        Check(r.customers.Residents.All(c => c.Idle || r.customers.Queue.Contains(c)), "Residents start idle until attracted");
        var stationary = r.customers.Residents.First(c => c.Idle); Vector3 home = stationary.transform.position; stationary.Advance(10);
        Check(stationary.transform.position == home, "Idle resident remains stationary");
        var cone = Object.Instantiate(r.waffle.conePrefab, r.holders[0].socket.position, Quaternion.identity, r.truck.transform);
        Vector3 coneLocal = cone.transform.localPosition, waffleLocal = r.waffle.transform.localPosition;
        r.player.Teleport(r.truck.transform, r.truck.standPoint.position, r.truck.standPoint.rotation);
        r.player.view.transform.LookAt(r.truck.seat.GetComponent<Collider>().bounds.center);
        r.interaction.ProcessInput(false, false, false, false, Vector2.zero, .02f);
        Check(r.truck.ToggleDriving(), "Entered driver's seat");
        Check(!r.player.controller.enabled && r.truck.ServiceOpen, "Sitting disables walking while parked service remains open");
        for (int i = 0; i < 100; i++) r.truck.Drive(1, 0, false, .02f);
        Check(r.truck.transform.position.x > 5 && r.truck.Speed > 5, "Accelerated forward: " + r.truck.transform.position + " speed=" + r.truck.Speed);
        Check(!r.truck.ToggleDriving(), "Cannot leave seat while moving");
        Check(cone.transform.localPosition == coneLocal && r.waffle.transform.localPosition == waffleLocal, "Cone and prep equipment move with truck");
        for (int i = 0; i < 100; i++) r.truck.Drive(0, 0, true, .02f);
        Check(r.truck.Speed == 0, "Space brake stops truck");
        Vector3 stopped = r.truck.transform.position;
        for (int i = 0; i < 60; i++) r.truck.Drive(-1, 0, false, .02f);
        Check(r.truck.transform.position.x < stopped.x - 1, "Reverse moves backward");
        for (int i = 0; i < 100; i++) r.truck.Drive(0, 0, true, .02f);
        var barrier = GameObject.CreatePrimitive(PrimitiveType.Cube); barrier.layer = 10;
        barrier.transform.position = r.truck.transform.position + Vector3.right * 12 + Vector3.up * 2;
        barrier.transform.localScale = new Vector3(1, 4, 10); Physics.SyncTransforms();
        for (int i = 0; i < 250; i++) r.truck.Drive(1, 0, false, .02f);
        Check(r.truck.Speed == 0 && r.truck.transform.position.x < barrier.transform.position.x - 4, "Truck stops before solid obstacle");
        Object.DestroyImmediate(barrier);
        for (int i = 0; i < 45; i++) r.truck.Drive(1, 1, false, .02f);
        Check(Quaternion.Angle(r.truck.transform.rotation, Quaternion.identity) > 2, "Steering turns the truck");
        for (int i = 0; i < 100; i++) r.truck.Drive(0, 0, true, .02f);
        Check(r.truck.ToggleDriving() && r.truck.ServiceOpen && r.player.controller.enabled, "Stopped and returned to kitchen");
        r.truck.transform.SetPositionAndRotation(Vector3.zero, Quaternion.identity); Physics.SyncTransforms();
        r.player.Teleport(null, r.truck.transform.TransformPoint(new Vector3(-5, 0, 0)), Quaternion.identity);
        for (int i = 0; i < 30; i++) r.player.Move(Vector2.zero, Vector2.zero, .02f);
        float baseHeight = r.player.transform.position.y;
        Check(r.player.Jump(), "Grounded player can jump");
        float peak = baseHeight;
        for (int i = 0; i < 80; i++) { r.player.Move(Vector2.zero, Vector2.zero, .02f); peak = Mathf.Max(peak, r.player.transform.position.y); }
        Check(peak > baseHeight + .3f && r.player.controller.isGrounded, "Jump rises and lands; height=" + (peak - baseHeight));
        r.player.Teleport(r.truck.transform, r.truck.kitchen.position, r.truck.kitchen.rotation);
        Object.DestroyImmediate(cone.gameObject);
        return Report("expansion-driving-world");
    }
    public static string AttractionAndService()
    {
        var r = PrototypeSceneReferences.Instance; checks = new List<string>();
        Check(!r.boombox.Playing, "Boombox starts off");
        r.boombox.ToggleMusic();
        Check(r.boombox.Playing, "Boombox music enabled");
        r.customers.AttractNearby();
        Check(r.customers.Queue.Count > 0, "Nearby residents join queue when music plays");
        var front = r.customers.Front;
        for (int i = 0; i < 600 && !front.Arrived; i++) foreach (var customer in r.customers.Queue.ToArray()) customer.Advance(.1f);
        Check(front.Arrived && Vector3.Distance(front.transform.position, r.customers.queuePoints[0].position) < .1f, "Front customer follows route to serving window");
        Check(front.Order.Count >= 1 && front.Order.Count <= 3, "Customer has a one-to-three-scoop recipe");
        var cone = Object.Instantiate(r.waffle.conePrefab);
        r.interaction.PickUp(r.scooper);
        foreach (var flavor in front.Order) { r.scooper.LoadScoop(flavor); cone.Use(r.interaction); }
        r.scooper.ReturnHome(r.interaction);
        if (front.WantsSprinkles)
        {
            r.interaction.PickUp(r.shaker);
            for (int i = 0; i < 100; i++) cone.Gesture(r.interaction, new Vector2(0, 20), .02f);
            r.shaker.ReturnHome(r.interaction);
        }
        r.interaction.PickUp(cone);
        r.player.Teleport(r.truck.transform, new Vector3(-1.1f, .68f, .6f), Quaternion.identity);
        r.player.view.transform.LookAt(front.transform.position + Vector3.up * 1.85f); Physics.SyncTransforms();
        r.interaction.ProcessInput(false, false, false, false, Vector2.zero, .02f);
        Check(r.interaction.Target == front, "Serving ray reaches customer at window");
        int earnings = r.day.Earnings;
        int price = r.day.settings.conePrice + front.Order.Count * r.day.settings.scoopPrice + (front.WantsSprinkles ? r.day.settings.sprinklePrice : 0);
        r.interaction.ProcessInput(true, false, false, false, Vector2.zero, .02f);
        Check(r.day.Earnings == earnings + price && r.interaction.Held == null && front.Leaving, "Click hands cone over and pays $" + price);
        Check(r.customers.Front != front, "Queue advances after payment");
        r.customers.ReleaseQueue();
        Check(r.customers.Queue.Count == 0, "Leaving the stop releases waiting customers");
        return Report("expansion-service");
    }
    public static string ClosingFailure()
    {
        var r = PrototypeSceneReferences.Instance; checks = new List<string>();
        float before = r.day.Elapsed; r.day.Advance(12);
        Check(Mathf.Abs(r.day.Elapsed - before - 12) < .001f, "Clock advances 12 real seconds");
        r.day.TogglePause(); before = r.day.Elapsed; r.day.Advance(30);
        Check(r.day.Elapsed == before, "Pause stops day clock"); r.day.TogglePause();
        r.day.Advance(r.day.settings.dayDurationSeconds - r.day.Elapsed - .01f);
        Check(r.day.CanPlay, "Day open immediately before 6 PM");
        r.day.Advance(.02f);
        Check(r.day.Hour == 18 && !r.day.CanPlay && !r.day.QuotaMet, "6 PM closes service and fails unmet quota");
        Check(!r.day.RecordSale(1000), "Cannot earn money after closing");
        r.day.NextDay();
        Check(DayManager.DayNumber == 1, "Failed quota cannot advance to next day");
        return Report("expansion-closing-failure");
    }
}
