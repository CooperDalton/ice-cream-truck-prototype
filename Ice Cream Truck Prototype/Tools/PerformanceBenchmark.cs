using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using Unity.Profiling;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

public static class PerformanceBenchmark
{
    const string Folder = "Library/CodexPlaytests/Performance";
    const string SettingsPath = "Assets/Settings/PrototypeSettings.asset";
    public static string Prepare()
    {
        if (EditorApplication.isPlaying) throw new Exception("Stop Play Mode before preparing the benchmark.");
        var scene = UnityEngine.SceneManagement.SceneManager.GetActiveScene();
        if (scene.isDirty) EditorSceneManager.SaveScene(scene);
        Directory.CreateDirectory(Folder);
        SessionState.SetInt("TruckBenchmark.VSync", QualitySettings.vSyncCount);
        SessionState.SetInt("TruckBenchmark.FrameRate", Application.targetFrameRate);
        File.WriteAllText(Folder + "/restore-scene.txt", scene.path);
        var settings = AssetDatabase.LoadAssetAtPath<PrototypeSettingsSO>(SettingsPath);
        File.WriteAllText(Folder + "/restore-settings.json", EditorJsonUtility.ToJson(settings));
        settings.randomizeWorldSeed = false;
        settings.worldSeed = 4312;
        EditorSceneManager.OpenScene("Assets/Scenes/IceCreamPrototype.unity");
        return "Prepared seed 4312. Enter Play Mode, then run PerformanceBenchmark.Run.";
    }
    public static string Restore()
    {
        if (EditorApplication.isPlaying) throw new Exception("Stop Play Mode before restoring benchmark settings.");
        EditorJsonUtility.FromJsonOverwrite(File.ReadAllText(Folder + "/restore-settings.json"), AssetDatabase.LoadAssetAtPath<PrototypeSettingsSO>(SettingsPath));
        QualitySettings.vSyncCount = SessionState.GetInt("TruckBenchmark.VSync", 0);
        Application.targetFrameRate = SessionState.GetInt("TruckBenchmark.FrameRate", -1);
        EditorSceneManager.OpenScene(File.ReadAllText(Folder + "/restore-scene.txt"));
        return "Restored the original settings and scene.";
    }
    public static async Task<string> Run()
    {
        var r = PrototypeSceneReferences.Instance;
        if (r.world.Seed != 4312) throw new Exception("Run Prepare before entering Play Mode so results use the same world.");
        r.player.ManualInput = r.interaction.ManualInput = r.truck.ManualInput = true;
        r.day.enabled = false;
        Application.targetFrameRate = -1;
        QualitySettings.vSyncCount = 0;
        Time.captureDeltaTime = 1f / 60;
        var recorders = new Dictionary<string, ProfilerRecorder>();
        var counters = new[] { "Main Thread", "PlayerLoop", "GPU Frame Time", "RenderLoop.Draw", "GC Allocated In Frame", "Draw Calls Count", "Batches Count", "Triangles Count", "Truck.Navigation", "Truck.Placement", "Physics.Simulate", "Physics.SyncTransforms" };
        foreach (string name in counters)
        {
            var category = name == "PlayerLoop" ? new ProfilerCategory("PlayerLoop") : name.StartsWith("Truck.") ? ProfilerCategory.Scripts : name.StartsWith("Physics.") ? ProfilerCategory.Physics : name == "GC Allocated In Frame" ? ProfilerCategory.Memory : name.Contains("Count") || name == "GPU Frame Time" || name == "RenderLoop.Draw" ? ProfilerCategory.Render : ProfilerCategory.Internal;
            recorders.Add(name, ProfilerRecorder.StartNew(category, name, 1));
        }
        var frames = Enumerable.Range(0, 720).Select(_ => new double[counters.Length + 1]).ToArray();
        var phases = new string[720];
        var csv = new StringBuilder("phase,wall_ms," + string.Join(",", counters) + "\n");
        var renderers = r.world.generatedRoot.GetComponentsInChildren<MeshRenderer>();
        var report = new StringBuilder($"Unity Editor {Application.unityVersion}; seed {r.world.Seed}; game view {r.player.view.pixelWidth}x{r.player.view.pixelHeight}; GPU {SystemInfo.graphicsDeviceName}\nWorld renderers: {renderers.Length}; residents: {r.customers.Residents.Count}\nTimes include Editor overhead. Zero GPU timings indicate an unavailable counter.\n");
        try
        {
            for (int i = 0; i < 90; i++) await Awaitable.NextFrameAsync();
            var route = RoadRoute(r.world);
            r.player.Teleport(r.truck.transform, r.truck.driver.position, r.truck.driver.rotation);
            double previous = Time.realtimeSinceStartupAsDouble;
            int segment = 1;
            Vector3 position = route[0];
            for (int frame = 0; frame < 720; frame++)
            {
                string phase = frame < 300 ? "drive" : frame < 540 ? "crowd" : "placement";
                if (frame < 300)
                {
                    var direction = route[segment] - position;
                    position = Vector3.MoveTowards(position, route[segment], .8f);
                    r.truck.FollowRoute(position, Quaternion.Euler(0, -Mathf.Atan2(direction.z, direction.x) * Mathf.Rad2Deg, 0), 12);
                    if ((position - route[segment]).sqrMagnitude < .01f && segment < route.Count - 1) segment++;
                }
                if (frame == 300)
                {
                    var target = r.world.Hotspots[0].position;
                    var road = AllRoads(r.world).OrderBy(p => (p - target).sqrMagnitude).First();
                    r.truck.FollowRoute(road, Quaternion.identity, 0);
                    if (!r.boombox.Playing) r.boombox.ToggleMusic();
                }
                if (frame == 540)
                {
                    r.player.Teleport(r.truck.transform, r.truck.transform.TransformPoint(new Vector3(-2.15f, .64f, .2f)), r.truck.transform.rotation);
                    r.interaction.PickUp(r.scooper);
                }
                if (frame >= 540)
                {
                    float x = -1.75f + Mathf.Sin(frame * .03f) * .12f;
                    r.player.view.transform.LookAt(r.truck.transform.TransformPoint(new Vector3(x, 1.534f, -.72f)));
                    r.interaction.ProcessInput(false, false, false, false, Vector2.zero, 1f / 60);
                }
                await Awaitable.NextFrameAsync();
                double now = Time.realtimeSinceStartupAsDouble;
                var values = frames[frame];
                values[0] = (now - previous) * 1000;
                previous = now;
                for (int i = 0; i < counters.Length; i++) values[i + 1] = recorders[counters[i]].Valid ? recorders[counters[i]].LastValue : -1;
                phases[frame] = phase;
            }
            for (int frame = 0; frame < frames.Length; frame++)
                csv.Append(phases[frame]).Append(',').AppendLine(string.Join(",", frames[frame].Select(v => v.ToString("F3", CultureInfo.InvariantCulture))));
            foreach (string phase in new[] { "drive", "crowd", "placement" })
            {
                var rows = frames.Where((row, index) => phases[index] == phase).Skip(10).ToArray();
                report.AppendLine(phase + ":");
                report.AppendLine($"  Frames over 33.3 ms: {rows.Count(row => row[0] > 33.3)}/{rows.Length}");
                for (int i = 0; i <= counters.Length; i++)
                {
                    var values = rows.Select(row => row[i]).OrderBy(v => v).ToArray();
                    double divisor = i > 0 && counters[i - 1] != "GC Allocated In Frame" && !counters[i - 1].Contains("Count") ? 1000000 : 1;
                    report.AppendLine($"  {(i == 0 ? "wall_ms" : counters[i - 1])}: mean {values.Average() / divisor:F3}; p95 {values[(int)(values.Length * .95)] / divisor:F3}; max {values.Last() / divisor:F3}");
                }
            }
            string prefix = Folder + "/" + DateTime.UtcNow.ToString("yyyyMMdd-HHmmss");
            File.WriteAllText(prefix + ".csv", csv.ToString());
            File.WriteAllText(prefix + ".txt", report.ToString());
            File.WriteAllText(Folder + "/latest.txt", report.ToString());
            if (r.player.view.targetTexture == null) ScreenCapture.CaptureScreenshot(prefix + ".png");
            await Awaitable.NextFrameAsync();
            await Awaitable.NextFrameAsync();
            return prefix + "\n" + report;
        }
        finally
        {
            foreach (var recorder in recorders.Values) recorder.Dispose();
            Time.captureDeltaTime = 0;
        }
    }
    public static async Task<string> RunGraphics()
    {
        var camera = PrototypeSceneReferences.Instance.player.view;
        var original = camera.targetTexture;
        var target = new RenderTexture(1920, 1080, 24, RenderTextureFormat.DefaultHDR);
        target.Create();
        camera.targetTexture = target;
        try { return await Run(); }
        finally
        {
            camera.targetTexture = original;
            target.Release();
            UnityEngine.Object.Destroy(target);
        }
    }
    static List<Vector3> AllRoads(WorldGenerator world)
    {
        var roads = new List<Vector3>();
        var ports = world.RoadPorts;
        int center = ports.GetLength(0) / 2;
        for (int x = 0; x < ports.GetLength(0); x++) for (int z = 0; z < ports.GetLength(1); z++)
            if (ports[x,z] != 0) roads.Add(new Vector3((x-center)*world.settings.tileSize, 0, (z-center)*world.settings.tileSize));
        return roads;
    }
    static List<Vector3> RoadRoute(WorldGenerator world)
    {
        var ports = world.RoadPorts;
        int center = ports.GetLength(0) / 2;
        var start = new Vector2Int(center, center);
        var queue = new Queue<Vector2Int>(); queue.Enqueue(start);
        var previous = new Dictionary<Vector2Int, Vector2Int> { [start] = start };
        var directions = new[] { Vector2Int.up, Vector2Int.right, Vector2Int.down, Vector2Int.left };
        var last = start;
        while (queue.Count > 0)
        {
            last = queue.Dequeue();
            for (int d = 0; d < 4; d++)
            {
                if ((ports[last.x,last.y] & (1 << d)) == 0) continue;
                var next = last + directions[d];
                if (previous.ContainsKey(next)) continue;
                previous[next] = last; queue.Enqueue(next);
            }
        }
        var route = new List<Vector3>();
        while (last != start)
        {
            route.Add(new Vector3((last.x-center)*world.settings.tileSize, 0, (last.y-center)*world.settings.tileSize));
            last = previous[last];
        }
        route.Add(Vector3.zero); route.Reverse(); return route;
    }
}
