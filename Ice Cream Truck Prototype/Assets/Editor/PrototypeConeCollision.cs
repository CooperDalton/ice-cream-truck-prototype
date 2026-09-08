using System.Collections.Generic;
using System.Linq;
using UnityEditor;
using UnityEngine;

public static class PrototypeConeCollision
{
    [MenuItem("Ice Cream/Update cone collision")]
    public static void Apply()
    {
        const string path = "Assets/Prefabs/IceCreamCone.prefab";
        var root = PrefabUtility.LoadPrefabContents(path);
        try
        {
            Configure(root.GetComponent<IceCreamCone>());
            PrefabUtility.SaveAsPrefabAsset(root, path);
            AssetDatabase.SaveAssets();
        }
        finally { PrefabUtility.UnloadPrefabContents(root); }
    }

    public static void Configure(IceCreamCone cone)
    {
        var pieces = new List<CombineInstance>();
        var filters = cone.GetComponentsInChildren<MeshFilter>(true);
        foreach (var filter in filters)
        {
            if (cone.scoopVisuals.Any(s => filter.transform.IsChildOf(s.transform)) ||
                cone.toppingVisuals.Any(t => filter.transform.IsChildOf(t.transform))) continue;
            AddMesh(pieces, cone, filter);
        }
        cone.collisionShapes = new Mesh[cone.scoopVisuals.Length + 1];
        for (int count = 0; count < cone.collisionShapes.Length; count++)
        {
            if (count > 0)
                foreach (var filter in cone.scoopVisuals[count - 1].GetComponentsInChildren<MeshFilter>(true))
                    AddMesh(pieces, cone, filter);
            var mesh = new Mesh { name = "Cone collision " + count + " scoops" };
            mesh.CombineMeshes(pieces.ToArray(), true, true);
            string path = "Assets/Art/ConeCollision" + count + ".asset";
            var existing = AssetDatabase.LoadAssetAtPath<Mesh>(path);
            if (existing == null) AssetDatabase.CreateAsset(mesh, path);
            else
            {
                EditorUtility.CopySerialized(mesh, existing);
                Object.DestroyImmediate(mesh);
                mesh = existing;
            }
            cone.collisionShapes[count] = mesh;
        }
        if (cone.pickupCollider != null) Object.DestroyImmediate(cone.pickupCollider);
        cone.shapeCollider = cone.gameObject.AddComponent<MeshCollider>();
        // Placed cones have no Rigidbody. A surface mesh preserves gaps beside the scoops.
        cone.shapeCollider.sharedMesh = cone.collisionShapes[0];
        cone.pickupCollider = cone.shapeCollider;
    }

    private static void AddMesh(List<CombineInstance> pieces, IceCreamCone cone, MeshFilter filter)
    {
        for (int submesh = 0; submesh < filter.sharedMesh.subMeshCount; submesh++)
            pieces.Add(new CombineInstance {
                mesh = filter.sharedMesh, subMeshIndex = submesh,
                transform = cone.transform.worldToLocalMatrix * filter.transform.localToWorldMatrix
            });
    }
}
