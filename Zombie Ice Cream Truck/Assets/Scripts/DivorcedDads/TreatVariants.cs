using Quantum;
using UnityEngine;

// Shows the child model matching a glob's flavor (the flying scoop).
public class TreatVariants : QuantumEntityViewComponent
{
    [Tooltip("Indexed by Treat; element 0 (None) is empty.")]
    [SerializeField] private GameObject[] variants;
    private Treat shown = (Treat)255;

    public override void OnUpdateView()
    {
        var treat = GetPredictedQuantumComponent<Glob>().Treat;
        if (treat == shown) return;
        shown = treat;
        for (int i = 1; i < variants.Length; i++) variants[i].SetActive(i == (int)treat);
    }
}
