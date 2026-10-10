using Quantum;
using UnityEngine;

// A lactose kid's fart cloud: green puffs that fill the cloud's radius and thin out as it clears.
public class GasView : QuantumEntityViewComponent
{
    [SerializeField] private ParticleSystem puffs;
    [SerializeField] private AudioSource hiss;

    public override void OnActivate(Frame frame)
    {
        var gas = GetPredictedQuantumComponent<Gas>();
        var shape = puffs.shape;
        shape.radius = gas.Radius.AsFloat * 0.8f;
        puffs.Play();
        hiss.Play();
    }

    public override void OnUpdateView()
    {
        var timer = GetPredictedQuantumComponent<Gas>().Timer.AsFloat;
        var emission = puffs.emission;
        emission.rateOverTime = timer > 1.5f ? 40 : 0;
        hiss.volume = Mathf.Clamp01(timer / 2f) * 0.5f;
    }
}
