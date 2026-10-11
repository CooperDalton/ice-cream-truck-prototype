using Quantum;
using UnityEngine;

// A shop pedestal at Big Dairy's lot: the item it sells turning above it, and a floating price tag that greys out once
// bought or while not available yet.
public class ShopTag : QuantumEntityViewComponent
{
    [SerializeField] private TextMesh text;
    [SerializeField] private Transform display;
    [Tooltip("Indexed by Upgrade; element 0 (None) is empty.")]
    [SerializeField] private GameObject[] items;
    [SerializeField] private float spinSpeed = 45f;

    public override unsafe void OnUpdateView()
    {
        var shop = GetPredictedQuantumComponent<Fixture>();
        var run = PredictedFrame.GetSingleton<DadsRun>();
        var soldOut = DadsGame.SoldOut(&run, shop.Upgrade);
        text.text = Name(shop.Upgrade) + (soldOut ? "\n---" : "\n$" + shop.Price);
        text.color = soldOut ? Color.gray : run.Money >= shop.Price ? new Color(0.22f, 0.95f, 0.76f) : new Color(1f, 0.6f, 0.2f);
        text.transform.rotation = DadsCamera.Instance.transform.rotation;
        for (int i = 1; i < items.Length; i++) items[i].SetActive(i == (int)shop.Upgrade);
        display.localRotation = Quaternion.Euler(0, Time.time * spinSpeed, 0);
    }

    public static string Name(Upgrade upgrade)
    {
        switch (upgrade)
        {
            case Upgrade.ScoopPistol: return "SCOOP PISTOL";
            case Upgrade.WaffleCone: return "WAFFLE CONES";
            case Upgrade.DoubleWaffle: return "DOUBLE WAFFLES";
            case Upgrade.SundaeShotgun: return "SUNDAE SHOTGUN";
            case Upgrade.Loudspeaker: return "LOUDSPEAKER";
            case Upgrade.Minigun: return "SOFT SERVE MINIGUN";
            case Upgrade.MapleGrovePermit: return "MAPLE GROVE PERMIT";
            case Upgrade.HillsidePermit: return "HILLSIDE PERMIT";
            default: return upgrade.ToString().ToUpper();
        }
    }
}
