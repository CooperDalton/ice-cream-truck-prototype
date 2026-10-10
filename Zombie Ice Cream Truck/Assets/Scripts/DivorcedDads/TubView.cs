using Quantum;
using UnityEngine;

// A freezer tub in the van: the tub model of its flavor and a little label with the scoops left.
public class TubView : QuantumEntityViewComponent
{
    [Tooltip("Indexed by Treat; element 0 (None) is empty.")]
    [SerializeField] private GameObject[] tubs;
    [SerializeField] private TextMesh label;

    public override void OnUpdateView()
    {
        var tub = GetPredictedQuantumComponent<Fixture>();
        for (int i = 1; i < tubs.Length; i++) tubs[i].SetActive(tub.Count > 0 && i == (int)tub.Treat);
        label.text = tub.Count > 0 ? TreatPalette.Name(tub.Treat).ToUpper() + "\n" + tub.Count : "EMPTY";
        label.color = tub.Count > 0 ? TreatPalette.Of(tub.Treat) : Color.gray;
    }
}
