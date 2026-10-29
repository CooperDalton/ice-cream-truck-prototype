using Quantum;
using UnityEngine;

// Hides what has been taken from a fixture until it restocks: strawberries on a patch, iced coffees on a patio
// table, gold in the vault, nuts on the tree.
public class RestockView : QuantumEntityViewComponent
{
    [SerializeField] private GameObject stock;

    public override void OnUpdateView()
    {
        stock.SetActive(GetPredictedQuantumComponent<Fixture>().Timer <= 0);
    }
}
