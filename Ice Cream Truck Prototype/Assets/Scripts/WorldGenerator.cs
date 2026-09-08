using System.Collections.Generic;
using UnityEngine;

[DefaultExecutionOrder(-200)]
public class WorldGenerator : MonoBehaviour
{
    [System.Serializable] public struct RoadPrefab { public GameObject prefab; public int ports; }
    [System.Serializable] public struct Hotspot { public Vector3 position; public bool park; }
    public PrototypeSettingsSO settings;
    public bool generateOnAwake = true;
    public RoadPrefab[] roads;
    public GameObject grass, park;
    public GameObject boundary;
    public GameObject[] houses, trees;
    public Transform generatedRoot;
    public List<Hotspot> Hotspots { get; private set; } = new List<Hotspot>();
    public int[,] RoadPorts { get; private set; }
    public int Seed { get; private set; }
    public float HalfExtent => (Mathf.Clamp(settings.junctionsPerSide | 1, 3, 5) * 2 - 1) * settings.tileSize * .5f;
    static readonly Vector2Int[] directions = { Vector2Int.up, Vector2Int.right, Vector2Int.down, Vector2Int.left };
    void Awake() { if (generateOnAwake) Generate(settings.randomizeWorldSeed ? Random.Range(1, int.MaxValue) : settings.worldSeed); }

    public void Generate(int seed)
    {
        foreach (Transform child in generatedRoot)
        {
            child.gameObject.SetActive(false);
            Destroy(child.gameObject);
        }
        Seed = seed;
        var random = new System.Random(seed);
        int n = Mathf.Clamp(settings.junctionsPerSide | 1, 3, 5), width = n * 2 - 1;
        RoadPorts = new int[width, width];
        var visited = new bool[n, n];
        var stack = new Stack<Vector2Int>();
        stack.Push(Vector2Int.zero); visited[0, 0] = true;
        while (stack.Count > 0)
        {
            var p = stack.Peek();
            var options = new List<int>();
            for (int d = 0; d < 4; d++)
            {
                var next = p + directions[d];
                if (next.x >= 0 && next.y >= 0 && next.x < n && next.y < n && !visited[next.x, next.y]) options.Add(d);
            }
            if (options.Count == 0) { stack.Pop(); continue; }
            int chosen = options[random.Next(options.Count)];
            var q = p + directions[chosen];
            Connect(p * 2, chosen); visited[q.x, q.y] = true; stack.Push(q);
        }
        for (int x = 0; x < n; x++) for (int z = 0; z < n; z++)
        {
            if (x < n - 1 && random.NextDouble() < settings.extraRoadChance) Connect(new Vector2Int(x * 2, z * 2), 1);
            if (z < n - 1 && random.NextDouble() < settings.extraRoadChance) Connect(new Vector2Int(x * 2, z * 2), 0);
        }
        // The starting truck sits at the central junction, facing along the east road.
        int center = (n / 2) * 2;
        if (center < width - 1) Connect(new Vector2Int(center, center), 1);
        if (center > 0) Connect(new Vector2Int(center, center), 3);
        Hotspots.Clear();
        for (int x = 0; x < width; x++) for (int z = 0; z < width; z++)
        {
            Vector3 pos = new Vector3((x - center) * settings.tileSize, -.05f, (z - center) * settings.tileSize);
            int ports = RoadPorts[x, z];
            if (ports != 0)
            {
                foreach (var road in roads)
                {
                    bool placed = false;
                    for (int rotation = 0; rotation < 4; rotation++)
                        if (RotatePorts(road.ports, rotation) == ports)
                        {
                            PlaceTile(road.prefab, pos, Quaternion.Euler(0, rotation * 90, 0));
                            placed = true; break;
                        }
                    if (placed) break;
                }
            }
            else
            {
                bool isPark = random.NextDouble() < settings.parkChance || (x == center + 1 && z == center + 1);
                PlaceTile(isPark ? park : grass, pos, Quaternion.identity);
                if (!isPark)
                {
                    Instantiate(houses[random.Next(houses.Length)], pos + new Vector3(0, .05f, -2), Quaternion.Euler(0, random.Next(4) * 90, 0), generatedRoot);
                    for (int t = 0; t < 3; t++) Instantiate(trees[random.Next(trees.Length)], pos + new Vector3(t == 0 ? -8 : 8, .05f, -7 + t * 7), Quaternion.identity, generatedRoot);
                }
                Hotspots.Add(new Hotspot { position = pos + new Vector3(0, .05f, 8), park = isPark });
            }
        }
        Physics.SyncTransforms();
        for (int side = 0; side < 4; side++)
        {
            var wall = Instantiate(boundary, generatedRoot);
            wall.transform.position = Quaternion.Euler(0, side * 90, 0) * new Vector3(0, 1.5f, HalfExtent + .5f);
            wall.transform.rotation = Quaternion.Euler(0, side * 90, 0);
            wall.transform.localScale = new Vector3(HalfExtent * 2 + 2, 3, 1);
        }
    }
    void PlaceTile(GameObject prefab, Vector3 position, Quaternion rotation)
    {
        var tile = Instantiate(prefab, position, rotation, generatedRoot);
        var scale = tile.transform.localScale; float ratio = settings.tileSize / 24;
        tile.transform.localScale = new Vector3(scale.x * ratio, scale.y, scale.z * ratio);
    }
    void Connect(Vector2Int p, int direction)
    {
        var middle = p + directions[direction]; var end = middle + directions[direction];
        RoadPorts[p.x, p.y] |= 1 << direction;
        RoadPorts[middle.x, middle.y] |= (1 << direction) | (1 << ((direction + 2) % 4));
        RoadPorts[end.x, end.y] |= 1 << ((direction + 2) % 4);
    }
    public static int RotatePorts(int ports, int turns)
    {
        for (int i = 0; i < turns; i++) ports = ((ports << 1) & 15) | (ports >> 3);
        return ports;
    }
    public bool ClearSegment(Vector3 a, Vector3 b)
    {
        var delta = b - a; delta.y = 0;
        return !Physics.CapsuleCast(a + Vector3.up * .65f, a + Vector3.up * 1.4f, .25f,
            delta.normalized, delta.magnitude, (1 << 9) | (1 << 10) | (1 << 11), QueryTriggerInteraction.Ignore);
    }
    public bool Walkable(Vector3 point)
    {
        return !Physics.CheckCapsule(point + Vector3.up * .65f, point + Vector3.up * 1.4f, .25f,
            (1 << 9) | (1 << 10) | (1 << 11), QueryTriggerInteraction.Ignore);
    }
    public List<Vector3> Path(Vector3 start, Vector3 end)
    {
        start.y = end.y = 0;
        if (ClearSegment(start, end)) return new List<Vector3> { end };
        float cell = settings.navigationCellSize;
        Vector2Int origin = Vector2Int.RoundToInt(new Vector2(start.x, start.z) / cell);
        Vector2Int goal = Vector2Int.RoundToInt(new Vector2(end.x, end.z) / cell);
        var open = new List<Vector2Int> { origin };
        var cost = new Dictionary<Vector2Int, float> { [origin] = 0 };
        var previous = new Dictionary<Vector2Int, Vector2Int>();
        var closed = new HashSet<Vector2Int>();
        for (int iteration = 0; open.Count > 0 && iteration < 2500; iteration++)
        {
            int best = 0;
            for (int i = 1; i < open.Count; i++)
                if (cost[open[i]] + Vector2Int.Distance(open[i], goal) < cost[open[best]] + Vector2Int.Distance(open[best], goal)) best = i;
            var current = open[best]; open.RemoveAt(best); closed.Add(current);
            Vector3 point = current == origin ? start : new Vector3(current.x * cell, 0, current.y * cell);
            if (Vector2Int.Distance(current, goal) < 2 && ClearSegment(point, end))
            {
                var path = new List<Vector3> { end };
                while (current != origin)
                {
                    path.Add(new Vector3(current.x * cell, 0, current.y * cell));
                    current = previous[current];
                }
                path.Reverse(); return path;
            }
            for (int dx = -1; dx <= 1; dx++) for (int dz = -1; dz <= 1; dz++)
            {
                if (dx == 0 && dz == 0) continue;
                var next = current + new Vector2Int(dx, dz);
                if (closed.Contains(next)) continue;
                var nextPoint = new Vector3(next.x * cell, 0, next.y * cell);
                if (Mathf.Abs(nextPoint.x) > HalfExtent || Mathf.Abs(nextPoint.z) > HalfExtent || !Walkable(nextPoint) || !ClearSegment(point, nextPoint)) continue;
                float score = cost[current] + Mathf.Sqrt(dx * dx + dz * dz);
                if (cost.TryGetValue(next, out float old) && old <= score) continue;
                cost[next] = score; previous[next] = current;
                if (!open.Contains(next)) open.Add(next);
            }
        }
        return null;
    }
}
