namespace Quantum
{
    using System;
    using Photon.Deterministic;

    // Run lifecycle: starting and wiping a run, generating road chunks ahead of the truck, depots, areas and upgrades.
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

            var global = f.Global;
            global->Phase = GamePhase.Driving;
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

            *f.Unsafe.GetPointer<Truck>(truckEntity) = default;
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
            f.Events.PhaseChanged(GamePhase.Driving, 1);
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
            if (local == settings.AreaChunks - 1)
            {
                kind = ChunkKind.Depot;
            }
            else if (stopIndex >= 0)
            {
                kind = (ChunkKind)((int)ChunkKind.Dairy + (stopIndex + global->Area) % 3);
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

            foreach (var placement in settings.ChunkContents)
            {
                if (placement.Chunk != kind) continue;
                var position = center + rotation * placement.Position;
                var owned = placement.IsStation
                    ? CreateStation(f, placement, position, rotation * FPQuaternion.Euler(0, placement.Yaw, 0))
                    : Inventory.SpawnPickup(f, new Item { Kind = placement.Item, Flavor = placement.Flavor, Count = placement.Count }, position, FPVector3.Zero, true);
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
                case UpgradeKind.Plow: return truck->PlowLevel >= 2;
                default: return false;
            }
        }
    }
}
