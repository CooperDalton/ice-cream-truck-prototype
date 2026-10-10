using Quantum;
using UnityEngine;

// Floating price tag over a shop pedestal at Big Dairy's lot; greys out once bought or while not available yet.
public class ShopTag : QuantumEntityViewComponent
{
    [SerializeField] private TextMesh text;

    public override unsafe void OnUpdateView()
    {
        var shop = GetPredictedQuantumComponent<Fixture>();
        var run = PredictedFrame.GetSingleton<DadsRun>();
        var soldOut = DadsGame.SoldOut(&run, shop.Upgrade);
        text.text = Name(shop.Upgrade) + (soldOut ? "\n---" : "\n$" + shop.Price);
        text.color = soldOut ? Color.gray : run.Money >= shop.Price ? new Color(0.22f, 0.95f, 0.76f) : new Color(1f, 0.6f, 0.2f);
        text.transform.rotation = DadsCamera.Instance.transform.rotation;
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
