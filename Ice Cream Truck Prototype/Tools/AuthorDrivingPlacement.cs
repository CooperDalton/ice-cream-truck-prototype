using System.Linq;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.UI;

public static class AuthorDrivingPlacement
{
    public static string Run()
    {
        const string folder = "Assets/Prefabs/Placement";
        if (!AssetDatabase.IsValidFolder(folder)) AssetDatabase.CreateFolder("Assets/Prefabs", "Placement");
        string materialPath = folder + "/GreenPreview.mat";
        var material = AssetDatabase.LoadAssetAtPath<Material>(materialPath);
        if (material == null)
        {
            material = new Material(Shader.Find("Universal Render Pipeline/Unlit"));
            AssetDatabase.CreateAsset(material, materialPath);
        }
        material.SetColor("_BaseColor", new Color(.2f, 1, .02f, .55f));
        material.SetFloat("_Surface", 1);
        material.SetFloat("_SrcBlend", (float)BlendMode.SrcAlpha);
        material.SetFloat("_DstBlend", (float)BlendMode.OneMinusSrcAlpha);
        material.SetFloat("_ZWrite", 0);
        material.EnableKeyword("_SURFACE_TYPE_TRANSPARENT");
        material.renderQueue = 3000;
        EditorUtility.SetDirty(material);
        string frictionPath = folder + "/LooseItems.physicMaterial";
        var friction = AssetDatabase.LoadAssetAtPath<PhysicsMaterial>(frictionPath);
        if (friction == null)
        {
            friction = new PhysicsMaterial("Loose items");
            AssetDatabase.CreateAsset(friction, frictionPath);
        }
        friction.staticFriction = .25f;
        friction.dynamicFriction = .18f;
        friction.frictionCombine = PhysicsMaterialCombine.Minimum;
        friction.bounciness = .08f;
        EditorUtility.SetDirty(friction);
        foreach (string name in new[] { "IceCreamPrototype", "ParkRoute" })
        {
            var scene = EditorSceneManager.OpenScene("Assets/Scenes/" + name + ".unity");
            var r = PrototypeSceneReferences.Instance;
            var settings = r.truck.settings;
            settings.acceleration = 3;
            settings.braking = 5;
            settings.truckSpeed = 14;
            settings.rollingResistance = .3f;
            settings.aerodynamicDrag = .006f;
            settings.throttleResponse = 1.5f;
            settings.steeringResponse = 65;
            settings.corneringAcceleration = 5;
            EditorUtility.SetDirty(settings);
            var items = new[] { r.batter, r.scooper, r.shaker, (PickupItem)r.boombox }.ToList();
            if (name == "ParkRoute") items.Add(r.route.tray);
            foreach (var item in items)
            {
                AuthorItem(item, material, folder);
                item.startLoose = true;
                item.physicsOwner = r.interaction;
                item.pickupCollider.sharedMaterial = friction;
            }
            string conePath = AssetDatabase.GetAssetPath(r.waffle.conePrefab);
            var cone = PrefabUtility.LoadPrefabContents(conePath);
            try
            {
                AuthorItem(cone.GetComponent<PickupItem>(), material, folder);
                cone.GetComponent<PickupItem>().pickupCollider.sharedMaterial = friction;
                PrefabUtility.SaveAsPrefabAsset(cone, conePath);
            }
            finally { PrefabUtility.UnloadPrefabContents(cone); }
            foreach (var collider in r.truck.GetComponentsInChildren<MeshCollider>(true))
            {
                if (!collider.name.StartsWith("PrepCounter_") && !collider.name.StartsWith("ServiceLedge_")) continue;
                var surface = collider.GetComponent<PlacementSurface>();
                if (surface == null) surface = collider.gameObject.AddComponent<PlacementSurface>();
                surface.highlightRenderers = new Renderer[0];
            }
            foreach (var root in scene.GetRootGameObjects())
            foreach (var label in root.GetComponentsInChildren<Text>(true))
                label.text = label.text.Replace("Q drops the item from your hand.", "Q places on a green preview, or drops from your hand.");
            EditorSceneManager.MarkSceneDirty(scene);
            EditorSceneManager.SaveScene(scene);
        }
        AssetDatabase.SaveAssets();
        EditorSceneManager.OpenScene("Assets/Scenes/IceCreamPrototype.unity");
        return "Authored green item previews, counters, loose cargo, and driving settings in both scenes.";
    }
    static void AuthorItem(PickupItem item, Material material, string folder)
    {
        Bounds bounds;
        if (item.pickupCollider is BoxCollider box) bounds = new Bounds(box.center, box.size);
        else if (item.pickupCollider is CapsuleCollider capsule)
            bounds = new Bounds(capsule.center, new Vector3(capsule.radius * 2, capsule.height, capsule.radius * 2));
        else bounds = ((MeshCollider)item.pickupCollider).sharedMesh.bounds;
        item.placementCenter = bounds.center;
        item.placementSize = bounds.size;
        item.placementRotation = Vector3.zero;
        var preview = new GameObject(item.kind + " placement preview");
        preview.layer = 2;
        foreach (var filter in item.GetComponentsInChildren<MeshFilter>(true))
        {
            bool visible = true;
            for (var ancestor = filter.transform; ancestor != item.transform; ancestor = ancestor.parent)
                visible &= ancestor.gameObject.activeSelf;
            if (!visible) continue;
            var mesh = new GameObject(filter.name);
            mesh.layer = 2;
            mesh.transform.SetParent(preview.transform, false);
            mesh.transform.localPosition = item.transform.InverseTransformPoint(filter.transform.position);
            mesh.transform.localRotation = Quaternion.Inverse(item.transform.rotation) * filter.transform.rotation;
            mesh.transform.localScale = filter.transform.lossyScale;
            mesh.AddComponent<MeshFilter>().sharedMesh = filter.sharedMesh;
            var renderer = mesh.AddComponent<MeshRenderer>();
            renderer.sharedMaterials = Enumerable.Repeat(material, filter.sharedMesh.subMeshCount).ToArray();
            renderer.shadowCastingMode = ShadowCastingMode.Off;
            renderer.receiveShadows = false;
        }
        item.placementPreviewPrefab = PrefabUtility.SaveAsPrefabAsset(preview, folder + "/" + item.kind + ".prefab");
        Object.DestroyImmediate(preview);
        EditorUtility.SetDirty(item);
    }
}
