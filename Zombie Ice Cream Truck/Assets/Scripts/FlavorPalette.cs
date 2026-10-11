using Quantum;
using UnityEngine;

// Display colors for each flavor, shared by tracers, splats, explosions and flavor-tinted models.
public static class FlavorPalette
{
    // Zombie blood: a bright cartoon crimson so the gore reads as candy-colored rather than grim.
    public static readonly Color Gore = new Color(0.78f, 0.04f, 0.2f);

    public static Color Of(Flavor flavor)
    {
        switch (flavor)
        {
            case Flavor.Vanilla: return new Color(1f, 0.95f, 0.78f);
            case Flavor.Chocolate: return new Color(0.43f, 0.23f, 0.12f);
            case Flavor.Strawberry: return new Color(1f, 0.31f, 0.64f);
            case Flavor.Mint: return new Color(0.22f, 0.95f, 0.76f);
            case Flavor.Coffee: return new Color(0.69f, 0.48f, 0.31f);
            case Flavor.RockyRoad: return new Color(0.3f, 0.17f, 0.12f);
            case Flavor.Neapolitan: return new Color(1f, 0.62f, 0.7f);
            default: return new Color(1f, 0.88f, 0.29f);
        }
    }
}
