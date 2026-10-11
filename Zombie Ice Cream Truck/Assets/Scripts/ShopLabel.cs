using Quantum;
using UnityEngine;

// Floating price tag over a depot shop pedestal; greys out once the upgrade is maxed or not yet available. Upgrade
// pedestals show a coin; item pedestals show the item itself (through their StationView) and read SOLD once a weapon
// has been bought.
public class ShopLabel : QuantumEntityViewComponent
{
    [SerializeField] private TextMesh text;
    [SerializeField] private GameObject coin;
    [SerializeField] private float upgradeLabelHeight = 2.1f;
    [Tooltip("Item pedestals sit on top of their stand, so their tag hangs lower over the item.")]
    [SerializeField] private float itemLabelHeight = 1.1f;

    public override unsafe void OnUpdateView()
    {
        var station = GetPredictedQuantumComponent<Station>();
        var truck = PredictedFrame.GetSingleton<Truck>();
        var stock = station.Slots[0];
        var upgrade = station.Upgrade != UpgradeKind.None;
        var soldOut = upgrade ? Run.SoldOut(&truck, station.Upgrade) : stock.Kind == ItemKind.None;
        var locked = station.Upgrade == UpgradeKind.SecondTurret && !truck.Turret;
        var title = upgrade ? station.Upgrade.ToString() : soldOut ? "" : GameHud.Name(stock);
        text.text = title + (locked ? "\nNEEDS TURRET" : soldOut ? "\nSOLD" : "\n$" + station.Price);
        text.color = soldOut ? Color.gray : PredictedFrame.Global->Money >= station.Price ? new Color(0.22f, 0.95f, 0.76f) : new Color(1f, 0.31f, 0.64f);
        text.transform.rotation = Camera.main.transform.rotation;
        coin.SetActive(upgrade);
        text.transform.localPosition = Vector3.up * (upgrade ? upgradeLabelHeight : itemLabelHeight);
    }
}
