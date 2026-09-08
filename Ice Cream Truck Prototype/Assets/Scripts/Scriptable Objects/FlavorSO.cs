using UnityEngine;

[CreateAssetMenu(menuName = "Ice Cream/Flavor")]
public class FlavorSO : ScriptableObject
{
    public string displayName;
    public Color color = Color.white;
    public Material material;
    public Sprite orderPicture;
    public Mesh scoopMesh;
    public Material chunkMaterial;

    public void ApplyToScoop(MeshFilter filter, Renderer renderer)
    {
        filter.sharedMesh = scoopMesh;
        renderer.sharedMaterials = chunkMaterial == null ? new[] { material } : new[] { material, chunkMaterial };
    }
}
