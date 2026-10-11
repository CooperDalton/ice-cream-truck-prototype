namespace Quantum
{
    using System;
    using System.Collections.Generic;
    using Photon.Deterministic;

    // Run lifecycle: starting and wiping a run, generating road chunks ahead of the truck and the scenery blocks around
    // them, depots, areas and upgrades.
    public static unsafe class Run
    {
        public static void Start(Frame f, EntityRef truckEntity)
        {
            var settings = f.FindAsset(f.RuntimeConfig.Settings);
            foreach (var pair in f.Unsafe.GetComponentBlockIterator<Zombie>()) f.Destroy(pair.Entity);
            foreach (var pair in f.Unsafe.GetComponentBlockIterator<Pickup>()) f.Destroy(pair.Entity);
            foreach (var pair in f.Unsafe.GetComponentBlockIterator<Projectile>()) f.Destroy(pair.Entity);
            foreach (var pair in f.Unsafe.GetComponentBlockIterator<RoadChunk>()) f.Destroy(pair.Entity);
            foreach (var pair in f.Unsafe.GetComponentBlockIterator<Station>()) f.Destroy(pair.Entity);
            foreach (var pair in f.Unsafe.GetComponentBlockIterator<Scenery>()) f.Destroy(pair.Entity);

            var global = f.Global;
            // The first run opens with the tutorial: the truck stays parked and nothing spawns until someone drives.
            global->Phase = global->TutorialDone ? GamePhase.Driving : GamePhase.Tutorial;
            global->Tutorial = TutorialStep.GrabMilk;
            global->PhaseTimer = 0;
            global->Area = 1;
            global->Money = 0;
            global->Kills = 0;
            global->SpawnTimer = settings.SpawnInterval * 4;
            global->NextChunk = 0;
            global->TruckChunk = 0;
            global->AreaStartChunk = 0;
            global->RoadEnd = FPVector3.Back * (settings.ChunkLength / 2);
            global->RoadHeading = 0;
            global->DepotChunk = EntityRef.None;

            *f.Unsafe.GetPointer<Truck>(truckEntity) = new Truck { Fuel = settings.StartingFuel, FuelFlavor = Flavor.Vanilla };
            var truckTransform = f.Unsafe.GetPointer<Transform3D>(truckEntity);
            truckTransform->Teleport(f, FPVector3.Zero, FPQuaternion.Identity);
            foreach (var placement in settings.TruckStations)
            {
                if (placement.Station == StationKind.Turret) continue;
                AttachStation(f, placement, *truckTransform);
            }

            int index = 0;
            foreach (var pair in f.Unsafe.GetComponentBlockIterator<Survivor>())
            {
                Inventory.GiveLoadout(pair.Component, settings);
                pair.Component->Standing = truckEntity;
                var offset = new FPVector3(index % 2 == 0 ? -FP._0_50 : FP._0_50, 0, (index / 2) * FP._0_75);
                f.Unsafe.GetPointer<Transform3D>(pair.Entity)->Teleport(f, truckTransform->TransformPoint(settings.RearInside + offset));
                index++;
            }
            while (global->NextChunk <= settings.ChunksAhead) AddChunk(f, settings);
            UpdateScenery(f, settings);
            if (global->Phase == GamePhase.Tutorial)
            {
                Inventory.SpawnPickup(f, new Item { Kind = ItemKind.MilkCrate, Count = 1 }, settings.TutorialMilkSpot, FPVector3.Zero, true);
                Inventory.SpawnPickup(f, new Item { Kind = ItemKind.SugarSack, Count = 1 }, settings.TutorialSugarSpot, FPVector3.Zero, true);
            }
            f.Events.PhaseChanged(global->Phase, 1);
        }

        public static EntityRef CreateStation(Frame f, Placement placement, FPVector3 position, FPQuaternion rotation)
        {
            var settings = f.FindAsset(f.RuntimeConfig.Settings);
            var entity = f.Create(settings.StationPrototypes[(int)placement.Station]);
            f.Unsafe.GetPointer<Transform3D>(entity)->Teleport(f, position, rotation);
            f.Add(entity, new Station { Kind = placement.Station, Upgrade = placement.Upgrade, Price = placement.Price, Index = placement.Count });
            var shape = Shape3D.CreateBox(placement.HalfSize, placement.Center);
            f.Add(entity, PhysicsCollider3D.Create(f, shape));
            return entity;
        }

        static EntityRef AttachStation(Frame f, Placement placement, Transform3D truck)
        {
            var local = FPQuaternion.Euler(0, placement.Yaw, 0);
            var entity = CreateStation(f, placement, truck.TransformPoint(placement.Position), truck.Rotation * local);
            f.Add(entity, new Attached { LocalPosition = placement.Position, LocalRotation = local });
            if (placement.Station == StationKind.Freezer)
            {
                var station = f.Unsafe.GetPointer<Station>(entity);
                *station->Slots.GetPointer(0) = new Item { Kind = ItemKind.Tub, Flavor = Flavor.Vanilla, Count = Inventory.ScoopsPerTub };
                *station->Slots.GetPointer(1) = new Item { Kind = ItemKind.Tub, Flavor = Flavor.Vanilla, Count = Inventory.ScoopsPerTub };
                *station->Slots.GetPointer(2) = new Item { Kind = ItemKind.Tub, Flavor = Flavor.Chocolate, Count = Inventory.ScoopsPerTub };
            }
            return entity;
        }

        // Chunks are 20 m squares whose entry sits at local -Z; straights exit at +Z, curves exit at -X (left) or +X (right).
        // Curves alternate so the road keeps heading forward overall and never loops back on itself.
        public static void AddChunk(Frame f, ZombieTruckSettings settings)
        {
            var global = f.Global;
            var index = global->NextChunk;
            var local = index - global->AreaStartChunk;
            ChunkKind kind;
            var stopIndex = System.Array.IndexOf(settings.StopChunks, local);
            var hotSpotIndex = System.Array.IndexOf(settings.HotSpotChunks, local);
            if (local == settings.AreaChunks - 1)
            {
                kind = ChunkKind.Depot;
            }
            else if (stopIndex >= 0)
            {
                kind = (ChunkKind)((int)ChunkKind.Dairy + (stopIndex + global->Area) % 3);
            }
            else if (hotSpotIndex >= 0)
            {
                kind = (ChunkKind)((int)ChunkKind.School + (hotSpotIndex + global->Area) % 3);
            }
            else if (local < 2 || local >= settings.AreaChunks - 3)
            {
                kind = global->Area % 2 == 1 ? ChunkKind.Straight : ChunkKind.Rural;
            }
            else
            {
                var roll = f.RNG->Next();
                if (roll < settings.CurveChance)
                {
                    kind = global->RoadHeading < 0 ? ChunkKind.CurveRight
                        : global->RoadHeading > 0 ? ChunkKind.CurveLeft
                        : f.RNG->Next() < FP._0_50 ? ChunkKind.CurveLeft : ChunkKind.CurveRight;
                }
                else if (roll < settings.CurveChance + settings.WreckChance)
                {
                    kind = ChunkKind.Wreck;
                }
                else if (global->Area % 2 == 1)
                {
                    var town = f.RNG->Next();
                    kind = town < FP._0_10 + FP._0_05 ? ChunkKind.Junction : town < FP._0_25 ? ChunkKind.Broken : ChunkKind.Straight;
                }
                else
                {
                    kind = ChunkKind.Rural;
                }
            }

            var rotation = FPQuaternion.Euler(0, global->RoadHeading, 0);
            var half = settings.ChunkLength / 2;
            var center = global->RoadEnd + rotation * FPVector3.Forward * half;
            var entity = f.Create(settings.ChunkPrototypes[(int)kind]);
            f.Unsafe.GetPointer<Transform3D>(entity)->Teleport(f, center, rotation);
            f.Add(entity, new RoadChunk { Index = index, Kind = kind });
            var solid = Shape3D.CreatePersistentCompound();
            var boxes = 0;
            foreach (var box in settings.ChunkColliders)
            {
                if (box.Chunk != kind) continue;
                var part = Shape3D.CreateBox(box.Extents, box.Center);
                solid.Compound.AddShape(f, ref part, true);
                boxes++;
            }
            if (boxes > 0) f.Add(entity, PhysicsCollider3D.Create(f, solid));
            solid.Compound.FreePersistent(f);
            if (kind == ChunkKind.CurveLeft)
            {
                global->RoadEnd = center + rotation * FPVector3.Left * half;
                global->RoadHeading -= 90;
            }
            else if (kind == ChunkKind.CurveRight)
            {
                global->RoadEnd = center + rotation * FPVector3.Right * half;
                global->RoadHeading += 90;
            }
            else
            {
                global->RoadEnd = center + rotation * FPVector3.Forward * half;
            }

            // Pickups without an item roll hot spot loot; shop pedestals without an upgrade or item roll a weapon, never the
            // same one twice in a depot.
            ulong rolledWeapons = 0;
            foreach (var placement in settings.ChunkContents)
            {
                if (placement.Chunk != kind) continue;
                var position = center + rotation * placement.Position;
                EntityRef owned;
                if (placement.IsStation)
                {
                    owned = CreateStation(f, placement, position, rotation * FPQuaternion.Euler(0, placement.Yaw, 0));
                    var station = f.Unsafe.GetPointer<Station>(owned);
                    if (placement.Station == StationKind.Shop && placement.Upgrade == UpgradeKind.None)
                    {
                        var stock = new Item { Kind = placement.Item, Flavor = placement.Flavor, Count = placement.Item == ItemKind.Tub ? Inventory.ScoopsPerTub : 1 };
                        if (placement.Item == ItemKind.None)
                        {
                            var weapon = settings.ShopWeapons[f.RNG->Next(0, settings.ShopWeapons.Length)];
                            while ((rolledWeapons & (1UL << (int)weapon)) != 0) weapon = settings.ShopWeapons[f.RNG->Next(0, settings.ShopWeapons.Length)];
                            rolledWeapons |= 1UL << (int)weapon;
                            var spec = Inventory.Gun(weapon);
                            stock = new Item { Kind = weapon, Flavor = Flavor.Vanilla, Count = spec.RoundsPerPint };
                            station->Price = spec.Price;
                        }
                        *station->Slots.GetPointer(0) = stock;
                    }
                }
                else
                {
                    var item = new Item { Kind = placement.Item, Flavor = placement.Flavor, Count = placement.Count };
                    if (item.Kind == ItemKind.None)
                    {
                        var loot = settings.HotSpotLoot[f.RNG->Next(0, settings.HotSpotLoot.Length)];
                        item = new Item { Kind = loot.Kind, Flavor = loot.Flavor, Count = loot.Count };
                    }
                    owned = Inventory.SpawnPickup(f, item, position, FPVector3.Zero, true);
                }
                f.Add(owned, new ChunkOwned { Chunk = index });
            }
            if (kind == ChunkKind.Depot) global->DepotChunk = entity;
            global->NextChunk++;
        }

        public static void RemoveChunk(Frame f, EntityRef chunk, Int32 index)
        {
            foreach (var pair in f.Unsafe.GetComponentBlockIterator<ChunkOwned>())
            {
                if (pair.Component->Chunk == index) f.Destroy(pair.Entity);
            }
            f.Destroy(chunk);
        }

        // Fills the empty grid cells within SceneryRings of the road with scenery blocks facing it and clears the ones the
        // road has left behind. A cell is only filled once the road has moved past its row (the road never heads
        // backward), so the road can't later be built over it. Road cells and the cells a stop, hot spot or depot set
        // piece spills into stay empty; the cell a T junction's side road leads into gets the side street. Called
        // whenever road chunks are added or removed.
        public static void UpdateScenery(Frame f, ZombieTruckSettings settings)
        {
            var road = new List<(int x, int y, ChunkKind kind)>();
            var setPieces = new List<(int x, int y)>();
            var sideStreets = new List<(int x, int y, int roadX, int roadY)>();
            var frontRow = int.MinValue;
            foreach (var pair in f.Unsafe.GetComponentBlockIterator<RoadChunk>())
            {
                var chunk = f.Get<Transform3D>(pair.Entity);
                var x = FPMath.RoundToInt(chunk.Position.X / settings.CellSize);
                var y = FPMath.RoundToInt(chunk.Position.Z / settings.CellSize);
                var kind = pair.Component->Kind;
                road.Add((x, y, kind));
                frontRow = Math.Max(frontRow, y);
                // Set pieces and the junction's side road sit on the chunk's local -X side; Kevin's stall stands on the
                // depot's +X sidewalk, so that side stays open too.
                var left = chunk.Rotation * FPVector3.Left;
                var leftX = FPMath.RoundToInt(left.X);
                var leftY = FPMath.RoundToInt(left.Z);
                if (kind >= ChunkKind.Dairy && kind != ChunkKind.Wreck) setPieces.Add((x + leftX, y + leftY));
                if (kind == ChunkKind.Depot) setPieces.Add((x - leftX, y - leftY));
                if (kind == ChunkKind.Junction) sideStreets.Add((x + leftX, y + leftY, x, y));
            }

            var wanted = new List<(int x, int y)>();
            foreach (var cell in road)
            {
                for (int dx = -settings.SceneryRings; dx <= settings.SceneryRings; dx++)
                {
                    for (int dy = -settings.SceneryRings; dy <= settings.SceneryRings; dy++)
                    {
                        var target = (cell.x + dx, cell.y + dy);
                        if (target.Item2 >= frontRow || setPieces.Contains(target) || wanted.Contains(target)) continue;
                        if (road.Exists(r => r.x == target.Item1 && r.y == target.Item2)) continue;
                        wanted.Add(target);
                    }
                }
            }

            var built = new List<(int x, int y)>();
            foreach (var pair in f.Unsafe.GetComponentBlockIterator<Scenery>())
            {
                var cell = (pair.Component->CellX, pair.Component->CellY);
                if (wanted.Contains(cell)) built.Add(cell);
                else f.Destroy(pair.Entity);
            }
            var townCurves = f.Global->Area % 2 == 1;
            foreach (var cell in wanted)
            {
                if (built.Contains(cell)) continue;
                int block;
                (int x, int y) faces;
                var street = sideStreets.FindIndex(s => s.x == cell.x && s.y == cell.y);
                if (street >= 0)
                {
                    block = settings.SideStreetBlock;
                    faces = (sideStreets[street].roadX, sideStreets[street].roadY);
                }
                else
                {
                    // Face the closest road cell: fewest steps, then straightest line.
                    var nearest = road[0];
                    var bestSteps = int.MaxValue;
                    var bestManhattan = int.MaxValue;
                    foreach (var other in road)
                    {
                        var steps = Math.Max(Math.Abs(other.x - cell.x), Math.Abs(other.y - cell.y));
                        var manhattan = Math.Abs(other.x - cell.x) + Math.Abs(other.y - cell.y);
                        if (steps > bestSteps || (steps == bestSteps && manhattan >= bestManhattan)) continue;
                        nearest = other;
                        bestSteps = steps;
                        bestManhattan = manhattan;
                    }
                    faces = (nearest.x, nearest.y);
                    var town = nearest.kind == ChunkKind.CurveLeft || nearest.kind == ChunkKind.CurveRight ? townCurves
                        : nearest.kind != ChunkKind.Rural && nearest.kind != ChunkKind.Dairy && nearest.kind != ChunkKind.Garden;
                    var choices = town ? settings.TownBlocks : settings.RuralBlocks;
                    var hash = cell.x * 73856093 ^ cell.y * 19349663;
                    block = choices[(hash % choices.Length + choices.Length) % choices.Length];
                }
                // Blocks are modeled with their front (+Z) toward the road.
                var toRoadX = faces.x - cell.x;
                var toRoadY = faces.y - cell.y;
                var direction = Math.Abs(toRoadX) > Math.Abs(toRoadY) ? new FPVector3(Math.Sign(toRoadX), 0, 0) : new FPVector3(0, 0, Math.Sign(toRoadY));
                var entity = f.Create(settings.SceneryPrototypes[block]);
                f.Unsafe.GetPointer<Transform3D>(entity)->Teleport(f, new FPVector3(cell.x * settings.CellSize, 0, cell.y * settings.CellSize), FPQuaternion.LookRotation(direction));
                f.Add(entity, new Scenery { CellX = cell.x, CellY = cell.y, Block = block });
                var solid = Shape3D.CreatePersistentCompound();
                var boxes = 0;
                foreach (var box in settings.SceneryColliders)
                {
                    if (box.Block != block) continue;
                    var part = Shape3D.CreateBox(box.Extents, box.Center);
                    solid.Compound.AddShape(f, ref part, true);
                    boxes++;
                }
                if (boxes > 0) f.Add(entity, PhysicsCollider3D.Create(f, solid));
                solid.Compound.FreePersistent(f);
            }
        }

        // Taking the driver's seat finishes (or skips) the tutorial and starts the run proper.
        public static void EndTutorial(Frame f)
        {
            var settings = f.FindAsset(f.RuntimeConfig.Settings);
            f.Global->TutorialDone = true;
            f.Global->Phase = GamePhase.Driving;
            f.Global->SpawnTimer = settings.SpawnInterval * 4;
            f.Events.PhaseChanged(GamePhase.Driving, f.Global->Area);
        }

        public static void EnterDepot(Frame f)
        {
            var settings = f.FindAsset(f.RuntimeConfig.Settings);
            f.Global->Phase = GamePhase.Depot;
            foreach (var pair in f.Unsafe.GetComponentBlockIterator<Zombie>()) f.Destroy(pair.Entity);
            var truck = f.Get<Transform3D>(f.GetSingletonEntityRef<Truck>());
            foreach (var pair in f.Unsafe.GetComponentBlockIterator<Survivor>())
            {
                if (pair.Component->Dead) Combat.Revive(f, pair.Entity, pair.Component, truck.TransformPoint(settings.RearOutside));
            }
            f.Unsafe.GetPointerSingleton<Truck>()->Speed = 0;
            f.Events.PhaseChanged(GamePhase.Depot, f.Global->Area);
        }

        public static void StartNextArea(Frame f)
        {
            f.Global->Phase = GamePhase.Driving;
            f.Global->Area++;
            f.Global->AreaStartChunk = f.Global->NextChunk;
            f.Global->DepotChunk = EntityRef.None;
            f.Events.PhaseChanged(GamePhase.Driving, f.Global->Area);
        }

        // Applies a depot purchase. Turrets add their roof seat station.
        public static void ApplyUpgrade(Frame f, UpgradeKind upgrade, FPVector3 shopPosition)
        {
            var settings = f.FindAsset(f.RuntimeConfig.Settings);
            var truckEntity = f.GetSingletonEntityRef<Truck>();
            var truck = f.Unsafe.GetPointer<Truck>(truckEntity);
            var truckTransform = f.Get<Transform3D>(truckEntity);
            switch (upgrade)
            {
                case UpgradeKind.Plow: truck->PlowLevel++; break;
                case UpgradeKind.Spikes: truck->Spikes = true; break;
                case UpgradeKind.Armor: truck->Armor = true; break;
                case UpgradeKind.BigHopper: truck->BigHopper = true; break;
                case UpgradeKind.Engine: truck->Engine = true; break;
                case UpgradeKind.BigTank: truck->BigTank = true; break;
                case UpgradeKind.SecondScoop:
                    Inventory.SpawnPickup(f, new Item { Kind = ItemKind.SecondScoop }, shopPosition + FPVector3.Up, FPVector3.Up * 2, false);
                    break;
                case UpgradeKind.Turret:
                case UpgradeKind.SecondTurret:
                    var seat = upgrade == UpgradeKind.Turret ? 0 : 1;
                    if (upgrade == UpgradeKind.Turret) truck->Turret = true;
                    else truck->SecondTurret = true;
                    foreach (var placement in settings.TruckStations)
                    {
                        if (placement.Station == StationKind.Turret && placement.Count == seat) AttachStation(f, placement, truckTransform);
                    }
                    break;
            }
        }

        // Upgrades that are already maxed out, or not available yet (second turret before the first).
        public static bool SoldOut(Truck* truck, UpgradeKind upgrade)
        {
            switch (upgrade)
            {
                case UpgradeKind.Spikes: return truck->Spikes;
                case UpgradeKind.Armor: return truck->Armor;
                case UpgradeKind.Turret: return truck->Turret;
                case UpgradeKind.SecondTurret: return truck->SecondTurret || !truck->Turret;
                case UpgradeKind.BigHopper: return truck->BigHopper;
                case UpgradeKind.Engine: return truck->Engine;
                case UpgradeKind.BigTank: return truck->BigTank;
                case UpgradeKind.Plow: return truck->PlowLevel >= 2;
                default: return false;
            }
        }
    }
}
