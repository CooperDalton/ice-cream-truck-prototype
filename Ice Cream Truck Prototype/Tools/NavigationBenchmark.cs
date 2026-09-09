using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using UnityEngine;

public static class NavigationBenchmark
{
    public static string Run()
    {
        var r = PrototypeSceneReferences.Instance;
        var settings = r.world.settings;
        var points = new List<Vector3>();
        var ports = r.world.RoadPorts;
        int center = ports.GetLength(0) / 2;
        for (int x = 0; x < ports.GetLength(0); x++) for (int z = 0; z < ports.GetLength(1); z++)
            if (ports[x,z] != 0) points.Add(new Vector3((x-center)*settings.tileSize,0,(z-center)*settings.tileSize));
        var times = new List<double>();
        int reached = 0;
        var timer = new Stopwatch();
        foreach (var resident in r.customers.Residents)
        {
            var target = points.OrderBy(p => (p-resident.Home).sqrMagnitude).First() + new Vector3(-1,0,3);
            timer.Restart();
            var path = r.world.Path(resident.Home, target);
            timer.Stop();
            if (path != null) reached++;
            times.Add(timer.Elapsed.TotalMilliseconds);
        }
        var blocked = r.world.generatedRoot.GetComponentsInChildren<Collider>().First(c => c.gameObject.layer == 10 && !r.world.Walkable(new Vector3(c.bounds.center.x,0,c.bounds.center.z)));
        var end = new Vector3(blocked.bounds.center.x,0,blocked.bounds.center.z);
        var start = points.OrderBy(p => (p-end).sqrMagnitude).First();
        timer.Restart();
        var invalid = r.world.Path(start, end);
        timer.Stop();
        if (invalid != null) throw new Exception("Navigation accepted an obstructed endpoint.");
        string report = $"Resident approaches: {times.Count}; reached: {reached}; mean {times.Average():F3} ms; max {times.Max():F3} ms.\nBlocked destination ({end}): {timer.Elapsed.TotalMilliseconds:F3} ms.";
        File.WriteAllText("Library/CodexPlaytests/Performance/navigation-"+DateTime.UtcNow.ToString("HHmmss")+".txt",report);
        return report;
    }
}
