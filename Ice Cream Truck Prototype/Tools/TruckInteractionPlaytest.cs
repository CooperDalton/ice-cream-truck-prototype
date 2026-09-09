using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Threading.Tasks;
using UnityEditor;
using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.InputSystem.LowLevel;

public static class TruckInteractionPlaytest
{
    static PrototypeSceneReferences r;
    static List<string> checks;
    static void Check(bool value, string message)
    {
        if (!value) throw new Exception("TRUCK TEST FAILED: " + message);
        checks.Add(message);
    }
    static void Aim(Interactable target)
    {
        r.player.view.transform.LookAt(target.GetComponent<Collider>().bounds.center);
        Physics.SyncTransforms();
        r.interaction.ProcessInput(false, false, false, false, Vector2.zero, .02f);
        Check(r.interaction.Target == target, "Ray reaches " + target.name + "; actual=" + r.interaction.Target);
    }
    static void Use()
    {
        r.interaction.ProcessInput(!(r.interaction.Target is TruckDoor || r.interaction.Target is TruckSeat || r.truck.IsDriving), false, false, false, Vector2.zero, .02f, r.interaction.Target is TruckDoor || r.interaction.Target is TruckSeat || r.truck.IsDriving);
        Physics.SyncTransforms();
    }
    static void Walk(float yaw, int frames)
    {
        r.player.transform.rotation = r.truck.transform.rotation * Quaternion.Euler(0, yaw, 0);
        for (int i = 0; i < frames; i++) r.player.Move(Vector2.up, Vector2.zero, .02f);
        Physics.SyncTransforms();
    }
    public static async Task<string> GestureAndIndicator()
    {
        r = PrototypeSceneReferences.Instance; checks = new List<string>();
        r.player.ManualInput = r.interaction.ManualInput = r.truck.ManualInput = true;
        EditorApplication.isPaused = false;
        try
        {
            if (r.interaction.Held != null) r.holders[2].Use(r.interaction);
            r.player.Teleport(r.truck.transform, r.truck.transform.TransformPoint(new Vector3(.35f, .64f, .1f)), r.truck.transform.rotation);
            Aim(r.waffle);
            await Task.Delay(100);
            var indicator = r.waffle.GetComponentInChildren<WaffleIndicator>(true);
            Check(!indicator.useKey.activeSelf && indicator.clickIcon.gameObject.activeInHierarchy, "Waffle use shows mouse icon");
            ScreenCapture.CaptureScreenshot("Library/CodexPlaytests/waffle-click-interaction.png");
            await Task.Delay(100);
            if (!r.waffle.IsOpen) Use();
            r.interaction.PickUp(r.batter);
            await Task.Delay(100);
            Check(!indicator.useKey.activeSelf && indicator.clickIcon.gameObject.activeInHierarchy, "Pouring shows mouse hold icon");
            r.batter.Drop(r.interaction);
            r.interaction.PickUp(r.scooper); r.scooper.EmptyScoop();
            Aim(r.tubs[0]);
            for (int i = 0; i < 10; i++) r.interaction.ProcessInput(false, true, false, false, new Vector2(0, i % 2 == 0 ? 20 : -20), .02f);
            Check(r.interaction.Scooping && r.tubs[0].Progress > .1f, "Mouse hold starts and grows scoop without pressing E");
            r.interaction.ProcessInput(false, false, true, true, Vector2.zero, .02f);
            string report = "PASS " + checks.Count + " checks\n" + string.Join("\n", checks);
            File.WriteAllText("Library/CodexPlaytests/truck-gesture-indicator.txt", report);
            return report;
        }
        finally { EditorApplication.isPaused = true; }
    }
    public static async Task<string> KeyboardControls()
    {
        r = PrototypeSceneReferences.Instance; checks = new List<string>();
        r.player.ManualInput = r.truck.ManualInput = r.customers.ManualInput = true;
        r.interaction.ManualInput = false;
        var previous = Keyboard.current;
        var previousMouse = Mouse.current;
        var mouse = InputSystem.AddDevice<Mouse>();
        var keyboard = InputSystem.AddDevice<Keyboard>();
        EditorApplication.isPaused = false;
        try
        {
            r.player.Teleport(r.truck.transform, r.truck.kitchen.position, r.truck.kitchen.rotation);
            r.player.view.transform.LookAt(r.scooper.GetComponent<Collider>().bounds.center);
            await Task.Delay(100);
            Check(r.interaction.Target == r.scooper, "Live Update ray targets scooper");
            Vector3 before = r.player.transform.position;
            InputSystem.QueueStateEvent(keyboard, new KeyboardState(Key.F));
            await Task.Delay(100);
            Check(r.player.transform.position == before && !r.truck.IsDriving, "F no longer teleports player or enters seat");
            InputSystem.QueueStateEvent(keyboard, new KeyboardState());
            await Task.Delay(50);
            InputSystem.QueueStateEvent(keyboard, new KeyboardState(Key.E));
            await Task.Delay(100);
            Check(r.interaction.Held == null, "E does not pick up the targeted scooper");
            InputSystem.QueueStateEvent(mouse, new MouseState { buttons = 1 });
            await Task.Delay(100);
            Check(r.interaction.Held == r.scooper, "Left click through Input System and Update picks up the scooper");
            InputSystem.QueueStateEvent(mouse, new MouseState());
            InputSystem.QueueStateEvent(keyboard, new KeyboardState());
            await Task.Delay(50);
            r.interaction.ManualInput = true;
            r.scooper.Drop(r.interaction);
            r.player.Teleport(r.truck.transform, r.truck.transform.TransformPoint(new Vector3(-2.6f,.64f,0)), r.truck.transform.rotation);
            Aim(r.truck.rearDoor);r.interaction.ManualInput=false;
            InputSystem.QueueStateEvent(mouse,new MouseState { buttons=1 });await Task.Delay(100);
            Check(!r.truck.rearDoor.IsOpen,"Left click does not open the rear door");
            InputSystem.QueueStateEvent(mouse,new MouseState());InputSystem.QueueStateEvent(keyboard,new KeyboardState(Key.E));await Task.Delay(100);
            Check(r.truck.rearDoor.IsOpen,"E through live Update opens the rear door");
            InputSystem.QueueStateEvent(keyboard,new KeyboardState());await Task.Delay(50);
            InputSystem.QueueStateEvent(keyboard,new KeyboardState(Key.E));await Task.Delay(100);
            Check(!r.truck.rearDoor.IsOpen,"E through live Update closes the rear door");
            InputSystem.QueueStateEvent(keyboard,new KeyboardState());await Task.Delay(50);
            r.player.Teleport(r.truck.transform,r.truck.standPoint.position,r.truck.standPoint.rotation);Aim(r.truck.seat);
            InputSystem.QueueStateEvent(mouse,new MouseState { buttons=1 });await Task.Delay(100);
            Check(!r.truck.IsDriving,"Left click does not enter the driver seat");
            InputSystem.QueueStateEvent(mouse,new MouseState());InputSystem.QueueStateEvent(keyboard,new KeyboardState(Key.E));await Task.Delay(100);
            Check(r.truck.IsDriving,"E through live Update enters the driver seat");
            InputSystem.QueueStateEvent(keyboard,new KeyboardState());await Task.Delay(50);
            InputSystem.QueueStateEvent(mouse,new MouseState { buttons=1 });await Task.Delay(100);
            Check(r.truck.IsDriving,"Left click does not leave the driver seat");
            InputSystem.QueueStateEvent(mouse,new MouseState());InputSystem.QueueStateEvent(keyboard,new KeyboardState(Key.E));await Task.Delay(100);
            Check(!r.truck.IsDriving,"E through live Update leaves the stopped driver seat");
            string report = "PASS " + checks.Count + " checks\n" + string.Join("\n", checks);
            File.WriteAllText("Library/CodexPlaytests/truck-keyboard.txt", report);
            return report;
        }
        finally
        {
            r.interaction.ManualInput = true;
            InputSystem.RemoveDevice(keyboard);
            InputSystem.RemoveDevice(mouse);
            previousMouse.MakeCurrent();
            previous.MakeCurrent();
            EditorApplication.isPaused = true;
        }
    }
    public static async Task<string> Main()
    {
        r = PrototypeSceneReferences.Instance; checks = new List<string>();
        r.player.ManualInput = r.interaction.ManualInput = r.truck.ManualInput = r.customers.ManualInput = true;
        EditorApplication.isPaused = false;
        try
        {
            var front = r.customers.Front ?? r.customers.SpawnCustomer();
            Check(front != null, "Customer waits for truck interaction test");
            int queue = r.customers.Queue.Count;
            r.player.Teleport(r.truck.transform, r.truck.transform.TransformPoint(new Vector3(-2.6f, .64f, 0)), r.truck.transform.rotation);
            Walk(270, 30);
            Check(r.truck.transform.InverseTransformPoint(r.player.transform.position).x > -3.6f, "Closed rear door blocks walking: " + r.player.transform.position);
            Aim(r.truck.rearDoor);
            Vector3 before = r.player.transform.position;
            Use();
            Check(r.truck.rearDoor.IsOpen && r.player.transform.position == before, "E opens rear door without moving player");
            await Task.Delay(850);
            Check(Quaternion.Angle(r.truck.rearDoor.hinge.localRotation, Quaternion.identity) > 100, "Rear door visibly swings open");
            Walk(270, 50);
            Check(!r.truck.InsideTruck && r.player.transform.parent == null, "Walked through open rear door to outside: " + r.player.transform.position);
            Check(r.customers.Queue.Count == queue && !front.Leaving, "Walking outside preserves waiting customers");
            r.player.view.transform.LookAt(r.truck.rearDoor.GetComponent<Collider>().bounds.center);
            ScreenCapture.CaptureScreenshot("Library/CodexPlaytests/rear-door-open.png");
            await Task.Delay(100);
            Walk(90, 65);
            Check(r.truck.InsideTruck && r.player.transform.parent == r.truck.transform, "Walked back up rear step into truck: " + r.player.transform.position);
            r.player.Teleport(r.truck.transform, r.truck.transform.TransformPoint(new Vector3(-2.7f, .64f, 0)), r.truck.transform.rotation);
            Aim(r.truck.rearDoor); Use();
            Check(!r.truck.rearDoor.IsOpen, "E closes rear door");
            await Task.Delay(850);
            r.player.Teleport(r.truck.transform, r.truck.standPoint.position, r.truck.standPoint.rotation);
            r.player.view.transform.rotation = r.truck.transform.rotation * Quaternion.LookRotation(Vector3.up);
            r.interaction.ProcessInput(false, false, false, false, Vector2.zero, .02f); Use();
            Check(!r.truck.IsDriving, "E looking away from seat does not start driving");
            r.player.Teleport(r.truck.transform, r.truck.transform.TransformPoint(new Vector3(-2.7f, .64f, .2f)), r.truck.transform.rotation);
            r.player.view.transform.LookAt(r.truck.seat.GetComponent<Collider>().bounds.center); Use();
            Check(!r.truck.IsDriving, "Distant E cannot enter driver seat");
            r.player.Teleport(r.truck.transform, r.truck.standPoint.position, r.truck.standPoint.rotation);
            Aim(r.truck.seat); Use();
            Check(r.truck.IsDriving && !r.player.controller.enabled, "Nearby E on seat starts driving");
            Check(r.customers.Queue.Count == queue && !front.Leaving && r.truck.ServiceOpen, "Sitting in parked truck preserves customers and service");
            Use();
            Check(!r.truck.IsDriving && r.player.controller.enabled && Vector3.Distance(r.player.transform.position, r.truck.standPoint.position) < .01f, "E while stopped stands beside driver seat");
            Aim(r.truck.seat); Use();
            for (int i = 0; i < 40; i++) r.truck.Drive(1, 0, false, .02f);
            Check(r.truck.Speed > 1 && r.customers.Queue.Count == 0, "Actual driving dismisses queue; speed=" + r.truck.Speed);
            Use();
            Check(r.truck.IsDriving, "E cannot stand up while truck is moving");
            for (int i = 0; i < 80; i++) r.truck.Drive(0, 0, true, .02f);
            Use();
            Check(!r.truck.IsDriving && r.truck.Speed == 0, "Braking then E returns to walking");
            string report = "PASS " + checks.Count + " checks\n" + string.Join("\n", checks);
            File.WriteAllText("Library/CodexPlaytests/truck-interactions.txt", report);
            return report;
        }
        finally { EditorApplication.isPaused = true; }
    }
}
