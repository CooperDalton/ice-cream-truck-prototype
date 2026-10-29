using System;
using Quantum;
using UnityEngine;

// Guns hanging in the van's gun rack, one prepared model per gun at every slot.
public class RackView : QuantumEntityViewComponent
{
    [Serializable]
    public struct Slot
    {
        public GameObject Pistol;
        public GameObject Shotgun;
    }

    [SerializeField] private Slot[] slots;

    public override void OnUpdateView()
    {
        var rack = GetPredictedQuantumComponent<Fixture>();
        for (int i = 0; i < slots.Length; i++)
        {
            slots[i].Pistol.SetActive(rack.Slots[i].Kind == DadItem.ScoopPistol);
            slots[i].Shotgun.SetActive(rack.Slots[i].Kind == DadItem.SundaeShotgun);
        }
    }
}
