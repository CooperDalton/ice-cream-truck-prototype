using System;
using Quantum;
using UnityEngine;

// Shows a station's contents: tubs in the freezer, pints on the counter, guns on the rack, and the gun crate's lid.
// Each slot has one prepared model per item kind and flavor; the matching one is switched on.
public class StationView : QuantumEntityViewComponent
{
    [Serializable]
    public struct SlotModel
    {
        public ItemKind Kind;
        public Flavor Flavor;
        public GameObject Model;
    }

    [Serializable]
    public struct Slot
    {
        public SlotModel[] Models;
    }

    [SerializeField] private Slot[] slots;
    [SerializeField] private Transform lid;
    [SerializeField] private Vector3 lidOpenEuler = new Vector3(-110, 0, 0);

    public override void OnUpdateView()
    {
        var station = GetPredictedQuantumComponent<Station>();
        for (int i = 0; i < slots.Length; i++)
        {
            var item = station.Slots[i];
            foreach (var model in slots[i].Models)
            {
                var flavorMatches = model.Flavor == Flavor.None || model.Flavor == item.Flavor;
                model.Model.SetActive(item.Count > 0 || Inventory.Gun(item.Kind).Pellets > 0 ? model.Kind == item.Kind && flavorMatches : false);
            }
        }
        if (lid == null) return;
        var target = station.Open ? Quaternion.Euler(lidOpenEuler) : Quaternion.identity;
        lid.localRotation = Quaternion.Slerp(lid.localRotation, target, 1 - Mathf.Exp(-10 * Time.deltaTime));
    }
}
