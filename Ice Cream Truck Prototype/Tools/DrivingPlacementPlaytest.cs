using System;
using System.Collections.Generic;
using System.IO;
using System.Threading.Tasks;
using UnityEngine;

public static class DrivingPlacementPlaytest
{
    static PrototypeSceneReferences r;
    static List<string> checks = new List<string>();
    public static async Task<string> Run()
    {
        r = PrototypeSceneReferences.Instance;
        r.player.ManualInput = r.interaction.ManualInput = r.truck.ManualInput = r.customers.ManualInput = true;
        r.day.enabled = false;
        Check(!r.batter.body.isKinematic && !r.shaker.body.isKinematic, "Tools begin as loose physical objects");
        r.player.Teleport(null, new Vector3(-1.1f, 0, 3.4f), Quaternion.identity);
        r.interaction.PickUp(r.scooper);
        r.player.view.transform.LookAt(new Vector3(-1.1f, 1.46f, 2.2f));
        Physics.SyncTransforms();
        r.interaction.ProcessInput(false, false, false, false, Vector2.zero, .02f);
        Check(r.interaction.CanPlace, "Aiming at the service counter shows a valid placement preview; target=" + r.interaction.Target);
        var expected = r.interaction.PlacementPosition;
        ScreenCapture.CaptureScreenshot("Library/CodexPlaytests/placement-preview.png");
        await Frames(3);
        r.interaction.ProcessInput(false, false, false, true, Vector2.zero, .02f);
        Check(r.interaction.Held == null && Vector3.Distance(r.scooper.transform.position, expected) < .01f && !r.scooper.body.isKinematic, "Q places the scooper at its preview with physics enabled");
        await Steps(60);
        Check(r.scooper.pickupCollider.bounds.min.y > 1.35f, "Placed scooper rests on the counter");
        r.interaction.PickUp(r.scooper);
        r.player.view.transform.rotation = Quaternion.LookRotation(Vector3.up);
        var hand = r.scooper.transform.position;
        r.interaction.ProcessInput(false, false, false, true, Vector2.zero, .02f);
        Check(!r.interaction.CanPlace && r.interaction.Held == null && Vector3.Distance(hand, r.scooper.transform.position) < .01f, "Q drops from the hand when no table is in range");
        r.player.Teleport(r.truck.transform, r.truck.driver.position, r.truck.driver.rotation);
        r.player.view.transform.LookAt(r.truck.seat.GetComponent<Collider>().bounds.center);
        Physics.SyncTransforms();
        r.interaction.ProcessInput(false, false, false, false, Vector2.zero, .02f, true);
        Check(r.truck.IsDriving, "Entered the driver seat through the interaction path");
        r.truck.obstacles = 0;
        for (int i = 0; i < 100; i++) r.truck.Drive(1, 0, false, .02f);
        float accelerating = r.truck.Speed;
        Check(accelerating > 2 && accelerating < 6, "Throttle builds speed gradually: " + accelerating.ToString("F2") + " m/s after two seconds");
        for (int i = 0; i < 50; i++) r.truck.Drive(0, 0, false, .02f);
        float coasting = r.truck.Speed;
        Check(coasting > 1 && coasting > accelerating - 2, "Releasing throttle coasts instead of stopping");
        for (int i = 0; i < 50; i++) r.truck.Drive(0, 0, true, .02f);
        Check(r.truck.Speed < coasting - 2, "Braking slows the van more strongly than coasting");
        for (int i = 0; i < 500; i++) r.truck.Drive(1, 0, false, .02f);
        r.truck.Drive(-1, 0, false, .02f);
        Check(r.truck.Speed > 0, "Reverse input first brakes forward motion");
        for (int i = 0; i < 40; i++) r.truck.Drive(1, 1, false, .02f);
        Check(r.truck.WheelAngle < 20 && r.truck.Acceleration.magnitude > 1, "High speed limits steering angle and produces cornering acceleration");
        for (int i = 0; i < 200; i++) r.truck.Drive(0, 0, true, .02f);
        r.interaction.PickUp(r.shaker, true);
        r.shaker.transform.position = r.truck.transform.TransformPoint(new Vector3(-.5f, 1.1f, .2f));
        r.shaker.Drop(r.interaction);
        await Steps(100);
        Vector3 cargoStart = r.truck.transform.InverseTransformPoint(r.shaker.transform.position);
        for (int i = 0; i < 180; i++) { r.truck.Drive(1, 1, false, .02f); await Steps(1); }
        Vector3 cargoEnd = r.truck.transform.InverseTransformPoint(r.shaker.transform.position);
        Check(Vector3.Distance(cargoStart, cargoEnd) > .2f, "Acceleration and turning move loose cargo inside the van: " + Vector3.Distance(cargoStart, cargoEnd).ToString("F2") + " m");
        string report = string.Join("\n", checks);
        File.WriteAllText("Library/CodexPlaytests/driving-placement.txt", report);
        return report;
    }
    static async Task Steps(int count)
    {
        for (int i = 0; i < count; i++) await Awaitable.FixedUpdateAsync();
    }
    static async Task Frames(int count)
    {
        for (int i = 0; i < count; i++) await Awaitable.NextFrameAsync();
    }
    static void Check(bool condition, string message)
    {
        if (!condition) throw new Exception(message);
        checks.Add("PASS: " + message);
    }
}
