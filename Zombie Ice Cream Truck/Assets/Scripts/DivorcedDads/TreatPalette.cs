using Quantum;
using UnityEngine;

// Display colors for each ice cream flavor, shared by splats, bursts, the HUD and tinted models.
public static class TreatPalette
{
    public static Color Of(Treat treat)
    {
        switch (treat)
        {
            case Treat.Mud: return new Color(0.48f, 0.35f, 0.24f);
            case Treat.Strawberry: return new Color(1f, 0.31f, 0.64f);
            case Treat.Coffee: return new Color(0.78f, 0.57f, 0.38f);
            case Treat.RockyRoad: return new Color(0.43f, 0.23f, 0.12f);
            case Treat.GoldLeaf: return new Color(1f, 0.85f, 0.25f);
            default: return new Color(1f, 0.95f, 0.85f);
        }
    }

    public static string Name(Treat treat)
    {
        switch (treat)
        {
            case Treat.RockyRoad: return "Rocky Road";
            case Treat.GoldLeaf: return "Gold Leaf";
            default: return treat.ToString();
        }
    }
}
