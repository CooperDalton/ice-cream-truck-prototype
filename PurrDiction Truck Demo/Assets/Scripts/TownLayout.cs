using System.Collections.Generic;
using UnityEngine;

// Grid town shared by the scene builder (to place geometry) and TruckSim (to collide).
public static class TownLayout
{
    public const int Blocks = 5;
    public const float BlockSize = 36f;
    public const float RoadWidth = 18f;
    public const float Sidewalk = 4f;
    public const float Pitch = BlockSize + RoadWidth;
    public const float Extent = Blocks * Pitch + RoadWidth;

    public static readonly List<Rect> Buildings = BuildBuildings();

    // Centre of the road between block rows/columns i (0..Blocks).
    public static float RoadCenter(int i)
    {
        return -Extent * 0.5f + RoadWidth * 0.5f + i * Pitch;
    }

    static List<Rect> BuildBuildings()
    {
        var list = new List<Rect>();
        for (int x = 0; x < Blocks; x++)
        {
            for (int z = 0; z < Blocks; z++)
            {
                float minX = RoadCenter(x) + RoadWidth * 0.5f + Sidewalk;
                float minZ = RoadCenter(z) + RoadWidth * 0.5f + Sidewalk;
                float size = BlockSize - Sidewalk * 2f;
                list.Add(new Rect(minX, minZ, size, size));
            }
        }
        // Outer walls keep the truck in town.
        float e = Extent * 0.5f;
        list.Add(new Rect(-e - 10f, -e - 10f, Extent + 20f, 10f));
        list.Add(new Rect(-e - 10f, e, Extent + 20f, 10f));
        list.Add(new Rect(-e - 10f, -e, 10f, Extent));
        list.Add(new Rect(e, -e, 10f, Extent));
        return list;
    }
}
