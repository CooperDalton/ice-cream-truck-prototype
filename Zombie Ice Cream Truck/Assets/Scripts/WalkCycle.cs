using UnityEngine;

// Procedural walk for the pivot-rigged PS1 characters: swings the leg pivots (and optionally the arms) in step with how
// fast the model actually moves over the ground. Purely cosmetic.
public class WalkCycle : MonoBehaviour
{
    [SerializeField] private Transform[] legs;
    [SerializeField] private Transform[] arms;
    [SerializeField] private float legSwing = 28f;
    [SerializeField] private float armSwing = 14f;
    [SerializeField] private float strideLength = 1.1f;
    private Quaternion[] legRest;
    private Quaternion[] armRest;
    private Vector3 lastPosition;
    private float phase;
    private float blend;

    private void Awake()
    {
        legRest = new Quaternion[legs.Length];
        for (int i = 0; i < legs.Length; i++) legRest[i] = legs[i].localRotation;
        armRest = new Quaternion[arms.Length];
        for (int i = 0; i < arms.Length; i++) armRest[i] = arms[i].localRotation;
        lastPosition = transform.position;
    }

    private void LateUpdate()
    {
        var delta = transform.position - lastPosition;
        lastPosition = transform.position;
        delta.y = 0;
        // Teleports and truck rides should not read as sprinting, so cap the measured speed.
        var speed = Mathf.Min(delta.magnitude / Mathf.Max(Time.deltaTime, 0.0001f), 8f);
        blend = Mathf.MoveTowards(blend, speed > 0.2f ? 1 : 0, Time.deltaTime * 4);
        phase += speed / strideLength * Mathf.PI * Time.deltaTime;
        var swing = Mathf.Sin(phase) * blend;
        for (int i = 0; i < legs.Length; i++) legs[i].localRotation = legRest[i] * Quaternion.Euler((i % 2 == 0 ? 1 : -1) * swing * legSwing, 0, 0);
        for (int i = 0; i < arms.Length; i++) arms[i].localRotation = armRest[i] * Quaternion.Euler((i % 2 == 0 ? -1 : 1) * swing * armSwing, 0, 0);
    }
}
