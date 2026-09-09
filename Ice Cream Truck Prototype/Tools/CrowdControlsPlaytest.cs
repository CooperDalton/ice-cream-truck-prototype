using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Threading.Tasks;
using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.InputSystem.LowLevel;

public static class CrowdControlsPlaytest
{
    static List<string> checks = new List<string>();
    public static async Task<string> Run()
    {
        var r = PrototypeSceneReferences.Instance;
        r.player.ManualInput = r.truck.ManualInput = r.customers.ManualInput = true;
        r.day.enabled = false;
        foreach (var resident in r.customers.Residents) resident.enabled = false;
        Check(r.customers.Residents.GroupBy(c => c.HomeArea).All(g => g.Count() == 6), "Six residents per area");
        Check(r.customers.Residents.All(a => r.customers.Residents.All(b => a == b || a.HomeArea != b.HomeArea || Vector3.Distance(a.Home, b.Home) >= 3)), "Residents start at least three metres apart");
        var c = r.customers.Residents[0];
        Vector3 start = Vector3.zero;
        bool found = false;
        for (int x = -18; x <= 18 && !found; x += 2)
        for (int z = -18; z <= 18 && !found; z += 2)
        {
            var p = new Vector3(x, 0, z);
            float distance = Vector3.Distance(p, r.customers.serviceLookPoint.position);
            if (distance < 14 || distance > 20 || !r.world.Walkable(p) || r.world.Path(p, r.customers.queuePoints[0].position) == null) continue;
            start = p; found = true;
        }
        Check(found, "Found a walkable approach to the van");
        c.transform.position = start;
        r.truck.FollowRoute(r.truck.transform.position, r.truck.transform.rotation, 3);
        r.customers.AttractNearby();
        Check(c.Chasing && c.FollowingVan && c.Order.Count == 0 && r.customers.Queue.Count == 0, "Moving van attracts customers without orders");
        float before = Vector3.Distance(c.transform.position, r.customers.queuePoints[0].position);
        for (int i = 0; i < 60; i++) c.Advance(.05f);
        Check(Vector3.Distance(c.transform.position, r.customers.queuePoints[0].position) < before - 1, "Customer runs toward the van");
        r.truck.FollowRoute(r.truck.transform.position, r.truck.transform.rotation, 0);
        for (int i = 0; i < 600 && !r.customers.Queue.Contains(c); i++) { c.Advance(.05f); r.customers.AttractNearby(); }
        Check(r.customers.Queue.Contains(c) && c.Order.Count > 0, "Customer places an order near the parked van");
        r.truck.FollowRoute(r.truck.transform.position, r.truck.transform.rotation, 3);
        r.customers.AttractNearby();
        Check(c.Chasing && c.Order.Count == 0 && r.customers.Queue.Count == 0, "Driving off turns the queue back into followers");
        r.truck.FollowRoute(new Vector3(150, 0, 150), Quaternion.identity, 0);
        c.transform.position = start;
        r.boombox.transform.SetParent(null);
        r.boombox.transform.position = start + Vector3.right * 5;
        if (!r.boombox.Playing) r.boombox.ToggleMusic();
        r.customers.AttractNearby();
        Check(c.Chasing && !c.FollowingVan && c.Order.Count == 0, "Remote boombox attracts listeners without ordering at a distant van");
        r.interaction.ManualInput = false;
        r.interaction.PickUp(r.boombox, true);
        bool music = r.boombox.Playing;
        var keyboard = Keyboard.current;
        var mouse = Mouse.current;
        try
        {
            InputSystem.QueueStateEvent(mouse, new MouseState { buttons = 2 });
            await Frames(3);
            Check(r.interaction.Held == r.boombox, "Right click keeps the held item");
            InputSystem.QueueStateEvent(mouse, new MouseState());
            InputSystem.QueueStateEvent(keyboard, new KeyboardState(Key.Q));
            await Frames(3);
            Check(r.interaction.Held == null && !r.boombox.body.isKinematic, "Q drops the item with physics");
            Check(r.boombox.Playing == music, "Q does not toggle music");
            InputSystem.QueueStateEvent(keyboard, new KeyboardState());
            await Frames(2);
            r.interaction.PickUp(r.boombox, true);
            InputSystem.QueueStateEvent(keyboard, new KeyboardState(Key.B));
            await Frames(3);
            Check(r.boombox.Playing == music && r.interaction.Held == r.boombox, "B leaves boombox playback unchanged");
        }
        finally
        {
            InputSystem.QueueStateEvent(keyboard, new KeyboardState());
            InputSystem.QueueStateEvent(mouse, new MouseState());
            r.interaction.ManualInput = true;
        }
        string report = string.Join("\n", checks);
        Directory.CreateDirectory("Library/CodexPlaytests");
        File.WriteAllText("Library/CodexPlaytests/crowd-controls.txt", report);
        return report;
    }
    static async Task Frames(int count)
    {
        for (int i = 0; i < count; i++) await Awaitable.NextFrameAsync();
    }
    static void Check(bool passed, string message)
    {
        if (!passed) throw new Exception(message);
        checks.Add("PASS: " + message);
    }
}
