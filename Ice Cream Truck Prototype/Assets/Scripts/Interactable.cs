using UnityEngine;

public abstract class Interactable : MonoBehaviour
{
    public Renderer[] highlightRenderers;
    public abstract string Prompt(PlayerInteraction player);
    public abstract void Use(PlayerInteraction player);
    public virtual bool CanGesture(PlayerInteraction player) => false;
    public virtual float Progress => 0;
    public virtual void Gesture(PlayerInteraction player, Vector2 delta, float dt) { }
    public virtual void StopGesture() { }
    public void Highlight(bool enabled)
    {
        var block = new MaterialPropertyBlock();
        foreach (var renderer in highlightRenderers)
        {
            renderer.GetPropertyBlock(block);
            block.SetColor("_EmissionColor", enabled ? new Color(.10f, .14f, .08f) : Color.black);
            renderer.SetPropertyBlock(block);
        }
    }
}
