using UnityEngine;

// Pops a model in and out: blast shells and stars grow past full size and shrink away; shockwave rings keep growing
// while they flatten out. Flat models like the stars can face the camera.
public class FxExpand : MonoBehaviour
{
    [SerializeField] private float duration = 0.45f;
    [SerializeField] private float overshoot = 1.2f;
    [SerializeField] private bool ring;
    [SerializeField] private bool faceCamera;
    [SerializeField] private Vector3 spin;
    private Vector3 fullScale;
    private float age;
    private Quaternion rest;
    private Vector3 spun;

    private void Awake()
    {
        fullScale = transform.localScale;
        rest = transform.localRotation;
        transform.localScale = Vector3.zero;
    }

    private void Update()
    {
        age += Time.deltaTime;
        var t = Mathf.Clamp01(age / duration);
        var grow = 1 - (1 - t) * (1 - t);
        if (ring)
        {
            var flat = Mathf.Clamp01((1 - t) / 0.5f);
            transform.localScale = Vector3.Scale(fullScale, new Vector3(grow * overshoot, grow * overshoot * flat, grow * overshoot));
        }
        else
        {
            var pop = t < 0.3f ? 1 - Mathf.Pow(1 - t / 0.3f, 2) : 1 - Mathf.Pow((t - 0.3f) / 0.7f, 2);
            transform.localScale = fullScale * pop * overshoot;
        }
        spun += spin * Time.deltaTime;
        transform.localRotation = (faceCamera ? Quaternion.Inverse(transform.parent.rotation) * Camera.main.transform.rotation * Quaternion.Euler(0, 180, 0) : rest) * Quaternion.Euler(spun);
    }
}
