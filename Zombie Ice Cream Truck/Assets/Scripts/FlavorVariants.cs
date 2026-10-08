using System;
using Quantum;
using UnityEngine;

// Shows the child model matching an item's flavor (pints, scoops, tubs, projectiles). Items without flavor variants
// keep their single model.
public class FlavorVariants : QuantumEntityViewComponent
{
    [Serializable]
    public struct Variant
    {
        public Flavor Flavor;
        public GameObject Model;
    }

    [SerializeField] private Variant[] variants;
    private Flavor shown = (Flavor)255;

    public override void OnUpdateView()
    {
        var flavor = HasPredictedQuantumComponent<Pickup>() ? GetPredictedQuantumComponent<Pickup>().Item.Flavor
            : GetPredictedQuantumComponent<Projectile>().Flavor;
        if (flavor == shown) return;
        shown = flavor;
        foreach (var variant in variants) variant.Model.SetActive(variant.Flavor == flavor);
    }
}
