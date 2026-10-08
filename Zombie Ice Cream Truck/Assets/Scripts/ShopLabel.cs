using Quantum;
using UnityEngine;

// Floating price tag over a depot shop pedestal; greys out once the upgrade is maxed or not yet available.
public class ShopLabel : QuantumEntityViewComponent
{
    [SerializeField] private TextMesh text;

    public override unsafe void OnUpdateView()
    {
        var station = GetPredictedQuantumComponent<Station>();
        var truck = PredictedFrame.GetSingleton<Truck>();
        var soldOut = Run.SoldOut(&truck, station.Upgrade);
        var locked = station.Upgrade == UpgradeKind.SecondTurret && !truck.Turret;
        text.text = station.Upgrade + (locked ? "\nNEEDS TURRET" : soldOut ? "\nSOLD OUT" : "\n$" + station.Price);
        text.color = soldOut ? Color.gray : PredictedFrame.Global->Money >= station.Price ? new Color(0.22f, 0.95f, 0.76f) : new Color(1f, 0.31f, 0.64f);
        text.transform.rotation = Camera.main.transform.rotation;
    }
}
