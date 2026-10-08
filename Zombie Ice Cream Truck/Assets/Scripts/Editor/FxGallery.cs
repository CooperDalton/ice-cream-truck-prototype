using System.IO;
using System.Linq;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

// Renders every effect prefab in Assets/Prefabs/FX that has an FxBurst at three moments of its life into one contact
// sheet (Library/CodexPlaytests/fx_gallery.png), tinted strawberry pink, so effects can be reviewed without playing.
// Run: Unity -batchmode -quit -projectPath <project> -executeMethod FxGallery.Capture
public static class FxGallery
{
    const int CellWidth = 360;
    const int CellHeight = 240;
    static readonly float[] Times = { 0.08f, 0.3f, 0.9f };

    [MenuItem("Tools/Zombie Truck/Capture FX Gallery")]
    public static void Capture()
    {
        EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
        var ground = GameObject.CreatePrimitive(PrimitiveType.Plane);
        ground.transform.localScale = Vector3.one * 4;
        var groundMaterial = new Material(Shader.Find("Universal Render Pipeline/Unlit"));
        groundMaterial.SetColor("_BaseColor", new Color(0.25f, 0.22f, 0.32f));
        ground.GetComponent<Renderer>().sharedMaterial = groundMaterial;
        var light = new GameObject("Sun").AddComponent<Light>();
        light.type = LightType.Directional;
        light.transform.rotation = Quaternion.Euler(50, -30, 0);
        var camera = new GameObject("Camera").AddComponent<Camera>();
        camera.clearFlags = CameraClearFlags.SolidColor;
        camera.backgroundColor = new Color(0.106f, 0.063f, 0.2f);
        camera.fieldOfView = 60;
        var target = new RenderTexture(CellWidth, CellHeight, 24);
        camera.targetTexture = target;

        var bursts = AssetDatabase.FindAssets("t:Prefab", new[] { "Assets/Prefabs/FX" })
            .Select(guid => AssetDatabase.LoadAssetAtPath<FxBurst>(AssetDatabase.GUIDToAssetPath(guid)))
            .Where(burst => burst != null).OrderBy(burst => burst.name).ToArray();
        var sheet = new Texture2D(CellWidth * Times.Length, CellHeight * bursts.Length, TextureFormat.RGB24, false);
        for (int row = 0; row < bursts.Length; row++)
        {
            var instance = (FxBurst)PrefabUtility.InstantiatePrefab(bursts[row]);
            instance.transform.position = Vector3.up;
            var tinted = new SerializedObject(instance).FindProperty("tinted");
            for (int i = 0; i < tinted.arraySize; i++)
            {
                var main = ((ParticleSystem)tinted.GetArrayElementAtIndex(i).objectReferenceValue).main;
                main.startColor = new Color(1f, 0.31f, 0.64f);
            }
            // Big effects (explosions, the bloater) get a wider shot.
            var big = instance.name.StartsWith("Explosion") || instance.name.StartsWith("Bloater");
            camera.transform.position = big ? new Vector3(0, 4, -11) : new Vector3(0, 2, -4.5f);
            camera.transform.LookAt(Vector3.up * (big ? 1.5f : 1.2f));
            var systems = instance.GetComponentsInChildren<ParticleSystem>();
            for (int column = 0; column < Times.Length; column++)
            {
                foreach (var system in systems) system.Simulate(Times[column], false, true, true);
                camera.Render();
                RenderTexture.active = target;
                sheet.ReadPixels(new Rect(0, 0, CellWidth, CellHeight), column * CellWidth, (bursts.Length - 1 - row) * CellHeight);
                RenderTexture.active = null;
            }
            Object.DestroyImmediate(instance.gameObject);
            Debug.Log($"FxGallery: row {row} = {bursts[row].name}");
        }
        sheet.Apply();
        Directory.CreateDirectory("Library/CodexPlaytests");
        File.WriteAllBytes("Library/CodexPlaytests/fx_gallery.png", sheet.EncodeToPNG());
        Debug.Log($"FxGallery: wrote {bursts.Length} effects");
    }
}
