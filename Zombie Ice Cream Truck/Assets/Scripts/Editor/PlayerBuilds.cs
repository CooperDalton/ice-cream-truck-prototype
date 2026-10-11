using System;
using System.Linq;
using UnityEditor;
using UnityEditor.Build.Reporting;
using UnityEngine;

// Player builds of every scene in the build settings (the main menu first). Batch mode:
// Unity -batchmode -quit -projectPath <project> -executeMethod PlayerBuilds.Windows -buildOutput <folder>
public static class PlayerBuilds
{
    [MenuItem("Tools/Build Players/Windows")]
    public static void Windows()
    {
        Build(BuildTarget.StandaloneWindows64, "Windows", "IceCreamTruck.exe");
    }

    [MenuItem("Tools/Build Players/macOS")]
    public static void Mac()
    {
        Build(BuildTarget.StandaloneOSX, "Mac", "IceCreamTruck.app");
    }

    static void Build(BuildTarget target, string folder, string file)
    {
        var args = Environment.GetCommandLineArgs();
        var index = Array.IndexOf(args, "-buildOutput");
        var root = index >= 0 ? args[index + 1] : "Builds";
        var report = BuildPipeline.BuildPlayer(new BuildPlayerOptions
        {
            scenes = EditorBuildSettings.scenes.Where(s => s.enabled).Select(s => s.path).ToArray(),
            locationPathName = $"{root}/{folder}/{file}",
            target = target,
            options = BuildOptions.None,
        });
        Debug.Log($"PlayerBuilds: {target} {report.summary.result}, {report.summary.totalSize / (1024 * 1024)} MB, {report.summary.totalErrors} errors -> {report.summary.outputPath}");
        if (Application.isBatchMode && report.summary.result != BuildResult.Succeeded) EditorApplication.Exit(1);
    }
}
