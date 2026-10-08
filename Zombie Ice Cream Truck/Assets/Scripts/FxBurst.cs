using UnityEngine;

// An authored one-shot effect: particle systems plus optional popping models. Tints the flavor-colored particles,
// scales the whole effect, and removes it once everything has finished.
public class FxBurst : MonoBehaviour
{
    [SerializeField] private ParticleSystem[] tinted;
    [SerializeField] private float lifetime = 2.5f;

    public void Play(Color color, float scale)
    {
        transform.localScale = Vector3.one * scale;
        foreach (var particles in tinted)
        {
            var main = particles.main;
            main.startColor = color;
        }
        Destroy(gameObject, lifetime);
    }
}
