using System.Collections.Generic;
using System.IO;
using System.Linq;
using Photon.Deterministic;
using Quantum;
using Quantum.Editor;
using UnityEditor;
using UnityEngine;
using Object = UnityEngine.Object;

// The town: three districts of 40 m blocks between 20 m road cells, joined by single gated roads over a creek.
// The Flats (trailers, mud and Big Dairy's lot) -> Maple Grove (houses, park, school, coffee strip) -> Hillside Estates
// (mansions and the vault). Roads are the zombie mode's road chunks picked by how many neighbours each road cell has.
// Every building, fence and prop between 0.4 m and 1.9 m is rasterized into static box colliders baked into the
// Quantum map; sockets in the block art become kid hangouts, cop patrol points and fixture placements.
public static partial class DivorcedDadsSceneBuilder
{
    const float Cell = 20f;
    const int Rows = 7;
    // District column spans in cells (inclusive); the columns between them are the connectors.
    static readonly (int from, int to)[] Districts = { (0, 6), (9, 18), (21, 27) };
    const int Columns = 28;
    const int ConnectorRow = 3;
    static readonly int[] GateColumns = { 7, 19 };

    // Blocks per district, in block order (x then z).
    static readonly string[][] DistrictBlocks =
    {
        new[] { "Big Dairy Lot", "Trailer Lot A", "Trailer Lot B", "Trailer Lot A" },
        new[] { "Suburb Block A", "Park Block", "Suburb Block B", "School Block", "Coffee Strip", "Suburb Block C" },
        new[] { "Mansion Block A", "Vault Mansion", "Mansion Block B", "Mansion Block A" },
    };

    const float ColliderCell = 0.25f;
    const float SolidFrom = 0.4f;
    const float SolidTo = 1.9f;
    const float ColliderHeight = 3f;

    class TownBuild
    {
        public Transform Root;
        public List<GameObject> Lamps = new List<GameObject>();
        public Vector3 Min;
        public Vector3 Max;
    }

    static Vector3 CellCenter(int x, int z)
    {
        return new Vector3((x - (Columns - 1) / 2f) * Cell, 0, (z - (Rows - 1) / 2f) * Cell);
    }

    static int DistrictOf(int x)
    {
        for (int d = 0; d < Districts.Length; d++)
        {
            if (x >= Districts[d].from && x <= Districts[d].to) return d;
        }
        return -1;
    }

    static bool IsRoad(int x, int z)
    {
        if (x < 0 || z < 0 || x >= Columns || z >= Rows) return false;
        var district = DistrictOf(x);
        if (district < 0) return z == ConnectorRow;
        var local = x - Districts[district].from;
        return local % 3 == 0 || z % 3 == 0;
    }

    static TownBuild BuildTown(DadsSettings settings)
    {
        var town = new TownBuild { Root = new GameObject("Town").transform };
        var kidSpots = new List<TownSpot>();
        var roadSpots = new List<TownSpot>();
        var fixtures = new List<FixturePlacement>();
        var collided = new List<GameObject>();
        var spotBlocks = new List<Rect>();

        // Directions N, E, S, W; turning a chunk by k * 90 degrees moves direction i to (i + k) % 4.
        var steps = new[] { new Vector2Int(0, 1), new Vector2Int(1, 0), new Vector2Int(0, -1), new Vector2Int(-1, 0) };
        for (int x = 0; x < Columns; x++)
        {
            for (int z = 0; z < Rows; z++)
            {
                var center = CellCenter(x, z);
                if (!IsRoad(x, z))
                {
                    if (DistrictOf(x) < 0) collided.Add(Place(Model(Town, "Creek Fill"), town.Root, center, Quaternion.Euler(0, z < ConnectorRow ? 0 : 180, 0)));
                    continue;
                }
                var open = Enumerable.Range(0, 4).Where(i => IsRoad(x + steps[i].x, z + steps[i].y)).ToArray();
                string piece;
                int turn;
                if (open.Length == 4)
                {
                    piece = "Crossroads";
                    turn = 0;
                }
                else if (open.Length == 3)
                {
                    // T Junction is open north, south and west: turn its closed east side onto the missing one.
                    piece = "T Junction";
                    var missing = Enumerable.Range(0, 4).First(i => !open.Contains(i));
                    turn = (missing - 1 + 4) % 4;
                }
                else if (open.Length == 2 && (open[1] - open[0]) % 2 == 1)
                {
                    // Curve Left joins south and west.
                    piece = "Curve Left";
                    turn = Enumerable.Range(0, 4).First(k => open.Contains((2 + k) % 4) && open.Contains((3 + k) % 4));
                }
                else
                {
                    piece = "Town Straight";
                    turn = open.Contains(1) || open.Contains(3) ? 1 : 0;
                }
                // Road dressing (bins, bushes, hydrants) is decoration: the van crosses sidewalks into lots and driveways.
                var road = Place(Model(piece == "Crossroads" ? Town : "Road", piece), town.Root, center, Quaternion.Euler(0, turn * 90, 0));
                foreach (var socket in road.GetComponentsInChildren<Transform>().Where(t => t.name.EndsWith("socket light")).ToList())
                {
                    if ((x + z) % 2 == 0) town.Lamps.Add(StreetLight(socket));
                }
                var district = DistrictOf(x);
                // Connector roads count as the district past their gate.
                roadSpots.Add(new TownSpot { Position = center.ToFPVector3(), District = district >= 0 ? district : x < Districts[1].from ? 1 : 2 });
            }
        }

        // Blocks: 2x2 cells between the roads of each district.
        for (int d = 0; d < Districts.Length; d++)
        {
            var blocksX = (Districts[d].to - Districts[d].from) / 3;
            for (int bx = 0; bx < blocksX; bx++)
            {
                for (int bz = 0; bz < 2; bz++)
                {
                    var name = DistrictBlocks[d][bx * 2 + bz];
                    var x0 = Districts[d].from + bx * 3 + 1;
                    var z0 = bz * 3 + 1;
                    var center = (CellCenter(x0, z0) + CellCenter(x0 + 1, z0 + 1)) / 2;
                    // The lot opens onto the middle road; other blocks alternate their facing for variety.
                    var yaw = name == "Big Dairy Lot" ? 0 : (bx + bz) % 2 == 0 ? 0 : 180;
                    var block = Place(Model(Town, name), town.Root, center, Quaternion.Euler(0, yaw, 0));
                    block.name = $"{name} {d}-{bx}-{bz}";
                    collided.Add(block);
                    ReadSockets(block, name, d, kidSpots, fixtures, settings);
                    while (spotBlocks.Count < kidSpots.Count) spotBlocks.Add(new Rect(center.x - Cell, center.z - Cell, Cell * 2, Cell * 2));
                }
            }
        }

        // Gates on the connector roads, across the road (which runs along X).
        for (int g = 0; g < GateColumns.Length; g++)
        {
            fixtures.Add(new FixturePlacement
            {
                Kind = FixtureKind.Gate, Index = g + 1, Position = CellCenter(GateColumns[g], ConnectorRow).ToFPVector3(), Yaw = 90,
                Center = new Vector3(-1.5f, 1.5f, 0).ToFPVector3(), HalfSize = new Vector3(6.5f, 1.5f, 0.3f).ToFPVector3(),
            });
        }

        town.Min = CellCenter(0, 0) - new Vector3(Cell / 2, 0, Cell / 2);
        town.Max = CellCenter(Columns - 1, Rows - 1) + new Vector3(Cell / 2, 0, Cell / 2);
        var solid = BuildColliders(town, collided, fixtures);
        // The vault puzzle has to be reachable on foot: plan the plate and the vault like kid spots and report them.
        var puzzle = fixtures.Where(p => p.Kind == FixtureKind.Plate || p.Kind == FixtureKind.Vault)
            .Select(p => new TownSpot { Position = p.Position + (p.Kind == FixtureKind.Vault ? (Quaternion.Euler(0, p.Yaw.AsFloat, 0) * Vector3.forward * 1.5f).ToFPVector3() : default) }).ToList();
        var puzzleBlocks = puzzle.Select(p => spotBlocks[kidSpots.FindIndex(k => (k.Position.ToUnityVector3() - p.Position.ToUnityVector3()).sqrMagnitude < 40 * 40)]).ToList();
        PlanPaths(solid, town.Min, puzzle, puzzleBlocks);
        settings.PuzzleRoutes = puzzle.ToArray();
        PlanPaths(solid, town.Min, kidSpots, spotBlocks);
        settings.KidSpots = kidSpots.ToArray();
        settings.RoadSpots = roadSpots.ToArray();
        settings.TownFixtures = fixtures.ToArray();
        Debug.Log($"DivorcedDadsSceneBuilder: {kidSpots.Count} kid spots, {roadSpots.Count} road spots, {fixtures.Count} town fixtures");
        return town;
    }

    static GameObject StreetLight(Transform socket)
    {
        var light = new GameObject("Street Light").AddComponent<Light>();
        light.transform.SetParent(socket, false);
        light.type = LightType.Point;
        light.range = 11;
        light.intensity = 2.2f;
        light.color = new Color(1f, 0.82f, 0.55f);
        light.gameObject.SetActive(false);
        return light.gameObject;
    }

    // Turns a block's sockets into kid spots and fixtures (world positions; the block is already placed).
    static void ReadSockets(GameObject block, string name, int district, List<TownSpot> kidSpots, List<FixturePlacement> fixtures, DadsSettings settings)
    {
        foreach (var socket in block.GetComponentsInChildren<Transform>().Where(t => t.name.StartsWith($"{name} socket ")))
        {
            var purpose = socket.name.Substring($"{name} socket ".Length);
            var position = new Vector3(socket.position.x, 0, socket.position.z);
            var yaw = FP.FromFloat_UNSAFE(Quaternion.LookRotation(Flat(socket.forward)).eulerAngles.y);
            if (purpose.StartsWith("kid ")) kidSpots.Add(new TownSpot { Position = position.ToFPVector3(), District = district });
            else if (purpose.StartsWith("mud ")) fixtures.Add(Fixture(FixtureKind.MudPuddle, position, yaw, new Vector3(0, 0.25f, 0), new Vector3(0.9f, 0.25f, 0.75f), true));
            else if (purpose.StartsWith("patch ")) fixtures.Add(Fixture(FixtureKind.StrawberryPatch, position, yaw, new Vector3(0, 0.3f, 0), new Vector3(0.85f, 0.3f, 0.45f), true));
            else if (purpose.StartsWith("cup ")) fixtures.Add(Fixture(FixtureKind.CoffeeTable, socket.position, yaw, new Vector3(0, 0.15f, 0), new Vector3(0.3f, 0.2f, 0.3f), true));
            else if (purpose == "nut tree") fixtures.Add(Fixture(FixtureKind.NutTree, position, yaw, new Vector3(0, 2f, 0), new Vector3(0.5f, 2f, 0.5f), false));
            else if (purpose == "vault") fixtures.Add(Fixture(FixtureKind.Vault, position, yaw, new Vector3(0, 1.2f, 0.1f), new Vector3(1f, 1.2f, 0.4f), false));
            else if (purpose == "plate") fixtures.Add(Fixture(FixtureKind.Plate, position, yaw, new Vector3(0, 0.1f, 0), new Vector3(0.5f, 0.1f, 0.5f), true));
            else if (purpose == "collector") fixtures.Add(Fixture(FixtureKind.Collector, position, yaw, new Vector3(0, 1f, 0), new Vector3(0.55f, 1f, 0.45f), false));
            else if (purpose == "end day") fixtures.Add(Fixture(FixtureKind.TimeClock, position, yaw, new Vector3(0, 0.9f, 0), new Vector3(0.3f, 0.9f, 0.3f), false));
            else if (purpose.StartsWith("shop "))
            {
                var index = int.Parse(purpose.Substring(5));
                if (index >= ShopStock.Length) continue;
                var shop = Fixture(FixtureKind.Shop, position, yaw, new Vector3(0, 0.6f, 0), new Vector3(0.35f, 0.6f, 0.35f), false);
                shop.Index = index;
                shop.Upgrade = ShopStock[index].upgrade;
                shop.Price = ShopStock[index].price;
                fixtures.Add(shop);
            }
            else if (purpose == "truck park")
            {
                settings.LotPark = position.ToFPVector3();
                settings.LotYaw = yaw;
                // A free puddle beside the van at the lot, so day one's mud is never far away.
                var side = position + Quaternion.LookRotation(Flat(socket.forward)) * new Vector3(6, 0, -2);
                fixtures.Add(Fixture(FixtureKind.MudPuddle, side, yaw, new Vector3(0, 0.25f, 0), new Vector3(0.9f, 0.25f, 0.75f), true));
            }
        }
    }

    static Vector3 Flat(Vector3 direction)
    {
        direction.y = 0;
        return direction.sqrMagnitude > 0.0001f ? direction.normalized : Vector3.forward;
    }

    static FixturePlacement Fixture(FixtureKind kind, Vector3 position, FP yaw, Vector3 center, Vector3 halfSize, bool trigger)
    {
        return new FixturePlacement
        {
            Kind = kind, Position = position.ToFPVector3(), Yaw = yaw, Center = center.ToFPVector3(), HalfSize = halfSize.ToFPVector3(), Trigger = trigger,
        };
    }

    // Rasterizes everything solid between knee and head height onto one 0.25 m grid over the whole town, keeps fixture
    // footprints and walkways clear, drops specks thinner than a lamp post, merges the rest into boxes and adds them as
    // static Quantum colliders, plus walls around the town. Writes Library/CodexPlaytests/dads_colliders.png to check.
    static bool[,] BuildColliders(TownBuild town, List<GameObject> pieces, List<FixturePlacement> fixtures)
    {
        var width = Mathf.CeilToInt((town.Max.x - town.Min.x) / ColliderCell);
        var depth = Mathf.CeilToInt((town.Max.z - town.Min.z) / ColliderCell);
        var solid = new bool[width, depth];
        foreach (var piece in pieces)
        {
            foreach (var filter in piece.GetComponentsInChildren<MeshFilter>())
            {
                var mesh = filter.sharedMesh;
                if (!mesh.isReadable) throw new System.InvalidOperationException($"{mesh.name} is not readable; run Tools > Zombie Truck > Reimport PS1 Art");
                var matrix = filter.transform.localToWorldMatrix;
                var vertices = mesh.vertices.Select(v => matrix.MultiplyPoint3x4(v)).ToArray();
                var triangles = mesh.triangles;
                for (int t = 0; t < triangles.Length; t += 3)
                {
                    var a = vertices[triangles[t]];
                    var b = vertices[triangles[t + 1]];
                    var c = vertices[triangles[t + 2]];
                    if (Mathf.Max(a.y, b.y, c.y) < SolidFrom || Mathf.Min(a.y, b.y, c.y) > SolidTo) continue;
                    var steps = Mathf.Max(1, Mathf.CeilToInt(Mathf.Max((b - a).magnitude, (c - a).magnitude, (c - b).magnitude) / (ColliderCell * 0.4f)));
                    for (int i = 0; i <= steps; i++)
                    {
                        for (int j = 0; j <= steps - i; j++)
                        {
                            var p = a + (b - a) * (i / (float)steps) + (c - a) * (j / (float)steps);
                            if (p.y < SolidFrom || p.y > SolidTo) continue;
                            var x = Mathf.FloorToInt((p.x - town.Min.x) / ColliderCell);
                            var z = Mathf.FloorToInt((p.z - town.Min.z) / ColliderCell);
                            if (x >= 0 && z >= 0 && x < width && z < depth) solid[x, z] = true;
                        }
                    }
                }
            }
        }
        // Fixtures bring their own colliders; the art around them stays walkable so they can be reached.
        foreach (var fixture in fixtures)
        {
            var position = fixture.Position.ToUnityVector3();
            var radius = fixture.Kind == FixtureKind.Gate ? 0 : fixture.Kind == FixtureKind.CoffeeTable ? 0.5f : 1.1f;
            Clear(solid, town.Min, position, radius);
        }
        DropSpecks(solid, 3);

        var colliders = new GameObject("Town Colliders").transform;
        colliders.SetParent(town.Root, false);
        var owner = new int[width, depth];
        var count = 0;
        for (int z = 0; z < depth; z++)
        {
            for (int x = 0; x < width; x++)
            {
                if (!solid[x, z] || owner[x, z] != 0) continue;
                var x1 = x;
                while (x1 + 1 < width && solid[x1 + 1, z] && owner[x1 + 1, z] == 0) x1++;
                var z1 = z;
                while (z1 + 1 < depth && Enumerable.Range(x, x1 - x + 1).All(cx => solid[cx, z1 + 1] && owner[cx, z1 + 1] == 0)) z1++;
                count++;
                for (int cz = z; cz <= z1; cz++)
                {
                    for (int cx = x; cx <= x1; cx++) owner[cx, cz] = count;
                }
                var size = new Vector3((x1 - x + 1) * ColliderCell, ColliderHeight, (z1 - z + 1) * ColliderCell);
                var center = new Vector3(town.Min.x + x * ColliderCell + size.x / 2, ColliderHeight / 2, town.Min.z + z * ColliderCell + size.z / 2);
                StaticBox(colliders, $"Box {count}", center, size);
            }
        }
        var span = town.Max - town.Min;
        var middle = (town.Max + town.Min) / 2;
        StaticBox(colliders, "Wall North", new Vector3(middle.x, 2, town.Max.z + 0.5f), new Vector3(span.x + 2, 4, 1));
        StaticBox(colliders, "Wall South", new Vector3(middle.x, 2, town.Min.z - 0.5f), new Vector3(span.x + 2, 4, 1));
        StaticBox(colliders, "Wall East", new Vector3(town.Max.x + 0.5f, 2, middle.z), new Vector3(1, 4, span.z + 2));
        StaticBox(colliders, "Wall West", new Vector3(town.Min.x - 0.5f, 2, middle.z), new Vector3(1, 4, span.z + 2));
        WriteColliderImage(owner, town.Min, fixtures);
        Debug.Log($"DivorcedDadsSceneBuilder: {count} town collider boxes");
        return solid;
    }

    // For every kid spot: a breadth-first search on the collider grid (walls grown by a kid's radius) from the spot to
    // the first open cell 1 m outside its block, simplified to the few waypoints that can see each other.
    static void PlanPaths(bool[,] solid, Vector3 min, List<TownSpot> spots, List<Rect> blocks)
    {
        var width = solid.GetLength(0);
        var depth = solid.GetLength(1);
        var blocked = new bool[width, depth];
        for (int x = 0; x < width; x++)
        {
            for (int z = 0; z < depth; z++)
            {
                for (int dx = -1; dx <= 1 && !blocked[x, z]; dx++)
                {
                    for (int dz = -1; dz <= 1; dz++)
                    {
                        var nx = x + dx;
                        var nz = z + dz;
                        if (nx >= 0 && nz >= 0 && nx < width && nz < depth && solid[nx, nz]) blocked[x, z] = true;
                    }
                }
            }
        }
        var stranded = 0;
        for (int i = 0; i < spots.Count; i++)
        {
            var spot = spots[i];
            var start = GridCell(min, spot.Position.ToUnityVector3());
            var outside = blocks[i];
            outside.min -= Vector2.one;
            outside.max += Vector2.one;
            var previous = new Dictionary<Vector2Int, Vector2Int> { [start] = start };
            var open = new Queue<Vector2Int>();
            open.Enqueue(start);
            var exit = start;
            var found = false;
            while (open.Count > 0 && !found)
            {
                var cell = open.Dequeue();
                for (int d = 0; d < 4; d++)
                {
                    var next = cell + (d == 0 ? Vector2Int.left : d == 1 ? Vector2Int.right : d == 2 ? Vector2Int.up : Vector2Int.down);
                    if (next.x < 0 || next.y < 0 || next.x >= width || next.y >= depth || blocked[next.x, next.y] || previous.ContainsKey(next)) continue;
                    previous[next] = cell;
                    var world = World(min, next);
                    if (!outside.Contains(new Vector2(world.x, world.z)))
                    {
                        exit = next;
                        found = true;
                        break;
                    }
                    open.Enqueue(next);
                }
            }
            if (!found)
            {
                stranded++;
                spot.Path = new FPVector3[0];
                spots[i] = spot;
                continue;
            }
            var cells = new List<Vector2Int>();
            for (var cell = exit; cell != start; cell = previous[cell]) cells.Add(cell);
            cells.Add(start);
            cells.Reverse();
            var waypoints = new List<Vector3>();
            var from = 0;
            while (from < cells.Count - 1)
            {
                var to = cells.Count - 1;
                while (to > from + 1 && !Clear(blocked, cells[from], cells[to])) to--;
                waypoints.Add(World(min, cells[to]));
                from = to;
            }
            spot.Path = waypoints.Select(w => w.ToFPVector3()).ToArray();
            spots[i] = spot;
        }
        Debug.Log($"DivorcedDadsSceneBuilder: planned {spots.Count - stranded} kid paths, {stranded} spots with no way out");
    }

    static Vector2Int GridCell(Vector3 min, Vector3 position)
    {
        return new Vector2Int(Mathf.FloorToInt((position.x - min.x) / ColliderCell), Mathf.FloorToInt((position.z - min.z) / ColliderCell));
    }

    static Vector3 World(Vector3 min, Vector2Int cell)
    {
        return new Vector3(min.x + (cell.x + 0.5f) * ColliderCell, 0, min.z + (cell.y + 0.5f) * ColliderCell);
    }

    // Line of sight between two grid cells (sampled every half cell).
    static bool Clear(bool[,] blocked, Vector2Int a, Vector2Int b)
    {
        var steps = Mathf.CeilToInt(Vector2Int.Distance(a, b) * 2) + 1;
        for (int i = 0; i <= steps; i++)
        {
            var p = Vector2.Lerp(a, b, i / (float)steps);
            if (blocked[Mathf.RoundToInt(p.x), Mathf.RoundToInt(p.y)]) return false;
        }
        return true;
    }

    static void Clear(bool[,] solid, Vector3 min, Vector3 position, float radius)
    {
        var cells = Mathf.CeilToInt(radius / ColliderCell);
        var cx = Mathf.FloorToInt((position.x - min.x) / ColliderCell);
        var cz = Mathf.FloorToInt((position.z - min.z) / ColliderCell);
        for (int x = cx - cells; x <= cx + cells; x++)
        {
            for (int z = cz - cells; z <= cz + cells; z++)
            {
                if (x < 0 || z < 0 || x >= solid.GetLength(0) || z >= solid.GetLength(1)) continue;
                var cell = new Vector2(min.x + (x + 0.5f) * ColliderCell, min.z + (z + 0.5f) * ColliderCell);
                if ((cell - new Vector2(position.x, position.z)).sqrMagnitude < radius * radius) solid[x, z] = false;
            }
        }
    }

    static void StaticBox(Transform parent, string name, Vector3 center, Vector3 size)
    {
        var go = new GameObject(name);
        go.transform.SetParent(parent, false);
        go.transform.position = center;
        var box = go.AddComponent<BoxCollider>();
        box.size = size;
        go.AddComponent<QuantumStaticBoxCollider3D>().SourceCollider = box;
    }

    static void DropSpecks(bool[,] solid, int minCells)
    {
        var width = solid.GetLength(0);
        var depth = solid.GetLength(1);
        var seen = new bool[width, depth];
        var open = new Stack<Vector2Int>();
        var island = new List<Vector2Int>();
        for (int x = 0; x < width; x++)
        {
            for (int z = 0; z < depth; z++)
            {
                if (!solid[x, z] || seen[x, z]) continue;
                island.Clear();
                open.Push(new Vector2Int(x, z));
                seen[x, z] = true;
                while (open.Count > 0)
                {
                    var cell = open.Pop();
                    island.Add(cell);
                    for (int i = 0; i < 4; i++)
                    {
                        var next = cell + (i == 0 ? Vector2Int.left : i == 1 ? Vector2Int.right : i == 2 ? Vector2Int.up : Vector2Int.down);
                        if (next.x < 0 || next.y < 0 || next.x >= width || next.y >= depth || !solid[next.x, next.y] || seen[next.x, next.y]) continue;
                        seen[next.x, next.y] = true;
                        open.Push(next);
                    }
                }
                if (island.Count >= minCells) continue;
                foreach (var cell in island) solid[cell.x, cell.y] = false;
            }
        }
    }

    // Top-down view, +Z up the image: each collider box its own color, fixtures as white squares.
    static void WriteColliderImage(int[,] owner, Vector3 min, List<FixturePlacement> fixtures)
    {
        const int scale = 1;
        var width = owner.GetLength(0);
        var depth = owner.GetLength(1);
        var image = new Texture2D(width * scale, depth * scale);
        var pixels = new Color32[width * depth];
        for (int x = 0; x < width; x++)
        {
            for (int z = 0; z < depth; z++)
            {
                var id = owner[x, z];
                pixels[z * width + x] = id != 0 ? (Color32)Color.HSVToRGB(id * 0.618f % 1f, 0.7f, 0.95f) : new Color32(30, 60, 30, 255);
            }
        }
        foreach (var fixture in fixtures)
        {
            var p = fixture.Position.ToUnityVector3();
            var cx = Mathf.FloorToInt((p.x - min.x) / ColliderCell);
            var cz = Mathf.FloorToInt((p.z - min.z) / ColliderCell);
            for (int dx = -3; dx <= 3; dx++)
            {
                for (int dz = -3; dz <= 3; dz++)
                {
                    var ix = cx + dx;
                    var iz = cz + dz;
                    if (ix >= 0 && iz >= 0 && ix < width && iz < depth) pixels[iz * width + ix] = new Color32(255, 255, 255, 255);
                }
            }
        }
        image.SetPixels32(pixels);
        Directory.CreateDirectory("Library/CodexPlaytests");
        File.WriteAllBytes("Library/CodexPlaytests/dads_colliders.png", image.EncodeToPNG());
        Object.DestroyImmediate(image);
    }
}
