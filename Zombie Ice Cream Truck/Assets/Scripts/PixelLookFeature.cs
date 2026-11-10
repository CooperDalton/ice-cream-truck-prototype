using UnityEngine.Rendering.Universal;

// Full-screen pass that runs the distance-aware Pixel Look shader on the game camera only (tagged MainCamera), so the
// display camera that draws the HUD stays crisp. ZombieTruckSceneBuilder adds it to the PC renderer.
public class PixelLookFeature : FullScreenPassRendererFeature
{
    public override void AddRenderPasses(ScriptableRenderer renderer, ref RenderingData renderingData)
    {
        if (!renderingData.cameraData.camera.CompareTag("MainCamera")) return;
        base.AddRenderPasses(renderer, ref renderingData);
    }
}
