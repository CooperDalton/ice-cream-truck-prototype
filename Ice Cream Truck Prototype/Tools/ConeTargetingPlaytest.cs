using System;
using System.Collections.Generic;
using System.IO;
using UnityEditor;
using UnityEngine;
using Object = UnityEngine.Object;

public static class ConeTargetingPlaytest
{
    static List<string> checks;
    static void Check(bool value, string message)
    {
        if (!value) throw new Exception("Cone targeting: " + message);
        checks.Add(message);
    }

    public static string Run()
    {
        if (!EditorApplication.isPlaying) throw new Exception("Enter Play Mode first.");
        var r = PrototypeSceneReferences.Instance;
        var p = r.interaction;
        checks = new List<string>();
        p.ManualInput = r.player.ManualInput = true;
        var holder = r.holders[2];
        var cone = Object.Instantiate(r.waffle.conePrefab, holder.socket.position, holder.socket.rotation);
        holder.Occupant = cone;
        cone.Holder = holder;
        var oldRoot = new GameObject("Old cone hitbox comparison") { layer = 2 };
        oldRoot.transform.SetPositionAndRotation(cone.transform.position, cone.transform.rotation);
        var oldBox = oldRoot.AddComponent<BoxCollider>();
        oldBox.center = new Vector3(0, .24f, 0);
        oldBox.size = new Vector3(.23f, .5f, .23f);
        r.player.controller.enabled = false;
        r.player.transform.position = new Vector3(cone.transform.position.x, .64f, .1f);
        r.player.controller.enabled = true;
        Check(p.PickUp(r.scooper), "Picked up empty scooper");
        try
        {
            for (int count = 0; count <= 3; count++)
            {
                Physics.SyncTransforms();
                Ray exposedRay = default;
                IceCreamTub exposedTub = null;
                // Search the actual tub surfaces for a ray the old box blocked.
                foreach (var tub in r.tubs)
                {
                    var bounds = tub.GetComponent<Collider>().bounds;
                    for (int x = 1; x < 20 && exposedTub == null; x++)
                    for (int z = 1; z < 20 && exposedTub == null; z++)
                    {
                        var point = new Vector3(Mathf.Lerp(bounds.min.x, bounds.max.x, x / 20f),
                            bounds.max.y - .005f, Mathf.Lerp(bounds.min.z, bounds.max.z, z / 20f));
                        var ray = new Ray(p.view.transform.position, point - p.view.transform.position);
                        if (!oldBox.Raycast(ray, out var before, p.settings.reach)) continue;
                        if (!Physics.Raycast(ray, out var after, p.settings.reach, ~((1 << 2) | (1 << 8)), QueryTriggerInteraction.Collide)) continue;
                        if (after.collider.GetComponent<IceCreamTub>() != tub || before.distance >= after.distance) continue;
                        exposedRay = ray;
                        exposedTub = tub;
                    }
                    if (exposedTub != null) break;
                }
                Check(exposedTub != null, count + " scoops: a tub ray blocked by the old box now reaches the exposed ice cream");
                p.view.transform.rotation = Quaternion.LookRotation(exposedRay.direction);
                p.ProcessInput(true, true, false, false, Vector2.zero, .02f);
                Check(p.Target == exposedTub && p.Gesturing, count + " scoops: clicking exposed tub starts scooping");
                for (int i = 0; i < 100; i++) p.ProcessInput(false, true, false, false, new Vector2(0, i % 2 == 0 ? 20 : -20), .02f);
                p.ProcessInput(false, false, true, false, Vector2.zero, .02f);
                Check(r.scooper.LoadedFlavor == exposedTub.flavor, count + " scoops: gesture loads the tub's flavor");
                checks.Add("Ray origin=" + exposedRay.origin.ToString("F4") + " direction=" + exposedRay.direction.ToString("F4"));
                AimCone(p, cone, count);
                p.ProcessInput(true, false, false, false, Vector2.zero, .02f);
                if (count < 3)
                {
                    Check(cone.Flavors.Count == count + 1 && r.scooper.LoadedFlavor == null, "Click adds scoop " + (count + 1));
                    Check(cone.shapeCollider.sharedMesh == cone.collisionShapes[count + 1], "Collision grows with scoop " + (count + 1));
                }
                else Check(cone.Flavors.Count == 3 && r.scooper.LoadedFlavor != null, "Full cone rejects fourth scoop without losing it");
            }
            r.scooper.ReturnHome(p);
            Check(p.PickUp(r.shaker), "Picked up shaker");
            AimCone(p, cone, 3);
            p.ProcessInput(true, true, false, false, Vector2.zero, .02f);
            for (int i = 0; i < 100; i++) p.ProcessInput(false, true, false, false, new Vector2(0, 20), .02f);
            p.ProcessInput(false, false, true, false, Vector2.zero, .02f);
            Check(cone.HasSprinkles, "Sprinkles gesture still works on the visible scoop");
            r.shaker.ReturnHome(p);
            AimCone(p, cone, 3);
            p.ProcessInput(true, false, false, false, Vector2.zero, .02f);
            Check(p.Held == cone && !cone.pickupCollider.enabled && holder.Occupant == null, "Picking up cone disables collision and clears holder");
            holder.Use(p);
            Check(p.Held == null && cone.pickupCollider.enabled && holder.Occupant == cone, "Placing cone restores its fitted collision");
            foreach (var mesh in cone.collisionShapes)
                checks.Add(mesh.name + ": " + mesh.triangles.Length / 3 + " collision triangles, shared across instances");
            string report = "PASS\n" + string.Join("\n", checks);
            Directory.CreateDirectory("Library/CodexPlaytests");
            File.WriteAllText("Library/CodexPlaytests/cone-targeting.txt", report);
            return report;
        }
        finally
        {
            Object.DestroyImmediate(oldRoot);
        }
    }

    static void AimCone(PlayerInteraction player, IceCreamCone cone, int count)
    {
        Physics.SyncTransforms();
        Vector3 point = count == 0 ? cone.transform.TransformPoint(new Vector3(0, .15f, 0)) : cone.scoopRenderers[count - 1].bounds.center;
        player.view.transform.LookAt(point);
        player.ProcessInput(false, false, false, false, Vector2.zero, .02f);
        Check(player.Target == cone, "Visible cone remains targetable with " + count + " scoops (hit " + player.Target?.name + ")");
    }
}
