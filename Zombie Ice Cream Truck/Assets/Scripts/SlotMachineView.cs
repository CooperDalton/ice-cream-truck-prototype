using System;
using Quantum;
using UnityEngine;

// The Scoop Slots machine at the depot. While a spin runs the reels flick through their symbols and stop one after
// another on the result the simulation already picked; the lever yanks down on every pull and the bulbs chase faster.
public class SlotMachineView : QuantumEntityViewComponent
{
    [Serializable]
    public struct Reel
    {
        [Tooltip("One model per symbol, indexed by Flavor: the brain (None), then Vanilla through Coffee.")]
        public GameObject[] Symbols;
    }

    [SerializeField] private Reel[] reels;
    [SerializeField] private Transform lever;
    [SerializeField] private Vector3 leverPullEuler = new Vector3(70, 0, 0);
    [SerializeField] private TextMesh priceLabel;
    [Tooltip("Remaining fraction of the spin at which each reel stops.")]
    [SerializeField] private float[] reelStops = { 0.5f, 0.28f, 0.06f };
    [SerializeField] private float flickRate = 14f;
    [Tooltip("Symbols shown before the first pull.")]
    [SerializeField] private Flavor[] idleSymbols = { Flavor.Vanilla, Flavor.Chocolate, Flavor.Strawberry };
    private Quaternion leverRest;
    private float pull;

    public override void OnInitialize()
    {
        leverRest = lever.localRotation;
    }

    public override void OnActivate(Frame frame)
    {
        QuantumEvent.Subscribe(this, (EventSlotsPulled e) => OnPulled(e));
    }

    private void OnPulled(EventSlotsPulled e)
    {
        if (e.Machine == EntityRef) pull = 1;
    }

    public override void OnUpdateView()
    {
        var station = GetPredictedQuantumComponent<Station>();
        var settings = PredictedFrame.FindAsset(PredictedFrame.RuntimeConfig.Settings);
        var remaining = (station.Timer / settings.SlotSpinTime).AsFloat;
        for (int i = 0; i < reels.Length; i++)
        {
            var symbols = reels[i].Symbols;
            var shown = station.Slots[i].Kind == ItemKind.None ? (int)idleSymbols[i] : (int)station.Slots[i].Flavor;
            if (remaining > reelStops[i]) shown = (int)(Time.time * flickRate + i * 2) % symbols.Length;
            for (int s = 0; s < symbols.Length; s++) symbols[s].SetActive(s == shown);
        }
        pull = Mathf.MoveTowards(pull, 0, Time.deltaTime * 2.5f);
        lever.localRotation = leverRest * Quaternion.Euler(leverPullEuler * Mathf.Sin(pull * Mathf.PI * 0.5f));
        priceLabel.text = station.Timer > 0 ? "SPINNING..." : "SCOOP SLOTS\n$" + station.Price;
        priceLabel.transform.rotation = Camera.main.transform.rotation;
    }
}
