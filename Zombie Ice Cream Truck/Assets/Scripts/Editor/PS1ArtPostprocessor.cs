using UnityEditor;
using UnityEditor.AssetImporters;
using UnityEditor.Rendering.Universal.ShaderGUI;
using UnityEngine;
using UnityEngine.Rendering.Universal;

// Import rules for the PS1 art written by Art/Tools/zombie-styles/export_unity.py into Assets/Art/PS1/.
// Textures are point-sampled pixel art; models are meshes plus pivot/socket empties at 1 unit = 1 m; materials are
// URP Lit with the texture as base map and emission. Name tags written by the exporter:
// "__repeat" textures wrap, "__clip" materials alpha clip on both faces, "__blend" materials are transparent.
public class PS1ArtPostprocessor : AssetPostprocessor
{
    const string ArtFolder = "Assets/Art/PS1/";
    const float Smoothness = 0.15f;
    const float AlphaCutoff = 0.5f;

    void OnPreprocessTexture()
    {
        if (!assetPath.StartsWith(ArtFolder))
            return;

        var importer = (TextureImporter)assetImporter;
        importer.textureType = TextureImporterType.Default;
        importer.sRGBTexture = true;
        importer.filterMode = FilterMode.Point;
        importer.mipmapEnabled = false;
        importer.npotScale = TextureImporterNPOTScale.None;
        importer.textureCompression = TextureImporterCompression.Uncompressed;
        importer.wrapMode = assetPath.EndsWith("__repeat.png") ? TextureWrapMode.Repeat : TextureWrapMode.Clamp;
        importer.alphaIsTransparency = importer.DoesSourceTextureHaveAlpha();
    }

    void OnPreprocessModel()
    {
        if (!assetPath.StartsWith(ArtFolder))
            return;

        var importer = (ModelImporter)assetImporter;
        importer.globalScale = 1f;
        importer.useFileScale = true;
        importer.importCameras = false;
        importer.importLights = false;
        importer.importAnimation = false;
        importer.animationType = ModelImporterAnimationType.None;
        // ZombieTruckSceneBuilder reads road and stop triangles to generate the chunk colliders.
        importer.isReadable = assetPath.StartsWith(ArtFolder + "Road/") || assetPath.StartsWith(ArtFolder + "Stops/");
        importer.materialImportMode = ModelImporterMaterialImportMode.ImportViaMaterialDescription;
        importer.materialLocation = ModelImporterMaterialLocation.InPrefab;
    }

    // Runs after URP's FBXMaterialDescriptionPreprocessor (order -980) and replaces its setup.
    void OnPreprocessMaterialDescription(MaterialDescription description, Material material, AnimationClip[] clips)
    {
        if (!assetPath.StartsWith(ArtFolder))
            return;

        description.TryGetProperty("DiffuseColor", out TexturePropertyDescription baseMap);
        // Blender writes each material's emission strength here: 0.32 for the style baseline, higher for glowing FX.
        description.TryGetProperty("EmissiveFactor", out float emission);
        bool clip = description.materialName.EndsWith("__clip");
        bool blend = description.materialName.EndsWith("__blend");

        material.shader = AssetDatabase.LoadAssetAtPath<Shader>(AssetDatabase.GUIDToAssetPath(ShaderUtils.GetShaderGUID(ShaderPathID.Lit)));
        material.SetTexture("_BaseMap", baseMap.texture);
        // Glass and ice would read as solid with full emission, so transparent materials glow less and fade further.
        material.SetColor("_BaseColor", blend ? new Color(1f, 1f, 1f, 0.55f) : Color.white);
        if (blend) emission *= 0.25f;
        material.SetFloat("_Metallic", 0f);
        material.SetFloat("_Smoothness", Smoothness);
        material.SetTexture("_EmissionMap", baseMap.texture);
        // Material colors are stored in gamma space; .gamma makes the shader's linear multiplier equal the Blender strength.
        material.SetColor("_EmissionColor", new Color(emission, emission, emission).gamma);
        material.globalIlluminationFlags = MaterialGlobalIlluminationFlags.RealtimeEmissive;
        material.SetFloat("_Surface", blend ? (float)BaseShaderGUI.SurfaceType.Transparent : (float)BaseShaderGUI.SurfaceType.Opaque);
        material.SetFloat("_Blend", (float)BaseShaderGUI.BlendMode.Alpha);
        material.SetFloat("_AlphaClip", clip ? 1f : 0f);
        material.SetFloat("_Cutoff", AlphaCutoff);
        material.SetFloat("_Cull", clip ? (float)BaseShaderGUI.RenderFace.Both : (float)BaseShaderGUI.RenderFace.Front);
        BaseShaderGUI.SetMaterialKeywords(material, LitGUI.SetMaterialKeywords);
    }
}
