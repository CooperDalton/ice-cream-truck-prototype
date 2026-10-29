using Quantum;
using UnityEngine;

// The red and blue light on a cop's hat, flashing while he chases someone.
public class CopLight : QuantumEntityViewComponent
{
    [SerializeField] private GameObject red;
    [SerializeField] private GameObject blue;

    public override void OnUpdateView()
    {
        var chasing = GetPredictedQuantumComponent<Npc>().State == NpcState.Chase;
        var phase = Mathf.Repeat(Time.time * 4, 1) < 0.5f;
        red.SetActive(chasing && phase);
        blue.SetActive(chasing && !phase);
    }
}
