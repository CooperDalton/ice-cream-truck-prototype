using Quantum;
using UnityEngine;

// Swaps a dead survivor's body for the floating spectator ghost.
public class SurvivorView : QuantumEntityViewComponent
{
    [SerializeField] private GameObject body;
    [SerializeField] private GameObject ghost;

    public override void OnUpdateView()
    {
        var dead = GetPredictedQuantumComponent<Survivor>().Dead;
        body.SetActive(!dead);
        ghost.SetActive(dead);
    }
}
