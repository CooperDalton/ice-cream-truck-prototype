namespace Quantum
{
    using System;
    using Photon.Deterministic;

    public unsafe class SurvivorSystem : SystemMainThreadFilter<SurvivorSystem.Filter>
    {
        public struct Filter
        {
            public EntityRef Entity;
            public Transform3D* Transform;
            public Survivor* Survivor;
            public PlayerLink* Link;
            public CharacterController3D* Controller;
        }

        static readonly ItemKind[] CrateGuns = { ItemKind.SundaeShotgun, ItemKind.SprinkleSMG, ItemKind.LongSpoon, ItemKind.ConeLauncher, ItemKind.BananaHarpoon };

        public override void Update(Frame f, ref Filter filter)
        {
            var settings = f.FindAsset(f.RuntimeConfig.Settings);
            var input = f.GetPlayerInput(filter.Link->Player);
            var survivor = filter.Survivor;
            var truckEntity = f.GetSingletonEntityRef<Truck>();
            var truck = f.Get<Transform3D>(truckEntity);
            if (survivor->Dead || f.Global->Phase == GamePhase.Wiped)
            {
                filter.Controller->Velocity = FPVector3.Zero;
                return;
            }

            survivor->Pitch = FPMath.Clamp(input->Pitch, -85, 85);
            filter.Transform->Rotation = FPQuaternion.Euler(0, input->Yaw + survivor->YawOffset, 0);
            if (input->Slot > 0 && input->Slot <= survivor->Hotbar.Length && survivor->Selected != input->Slot - 1)
            {
                survivor->Selected = input->Slot - 1;
                survivor->WorkProgress = 0;
            }

            if (survivor->Driving || survivor->TurretSeat > 0)
            {
                if (!input->Interact.WasPressed)
                {
                    var seat = survivor->Driving ? settings.DriverSeat : settings.TurretStands[survivor->TurretSeat - 1];
                    filter.Transform->Position = truck.TransformPoint(seat);
                    filter.Controller->Velocity = FPVector3.Zero;
                    survivor->Standing = truckEntity;
                    return;
                }
                var exit = survivor->Driving ? settings.CabStand : settings.HatchTop;
                if (survivor->Driving) f.Unsafe.GetPointerSingleton<Truck>()->Driver = PlayerRef.None;
                survivor->Driving = false;
                survivor->TurretSeat = 0;
                filter.Transform->Teleport(f, truck.TransformPoint(exit));
                return;
            }

            var eye = filter.Transform->Position + FPVector3.Up * settings.EyeHeight;
            var look = filter.Transform->Rotation * FPQuaternion.Euler(survivor->Pitch, 0, 0) * FPVector3.Forward;
            var hit = f.Physics3D.Raycast(eye, look, settings.ReachDistance, -1, QueryOptions.HitAll);
            var target = hit.HasValue ? hit.Value.Entity : EntityRef.None;
            survivor->LookTarget = target;
            if (input->Interact.WasPressed)
            {
                Interact(f, ref filter, target, truck, settings);
            }
            Drop(f, ref filter, input, eye, look, settings);
            if (input->Reload.WasPressed)
            {
                Reload(f, filter.Link->Player, survivor);
            }
            Work(f, ref filter, input, target, settings);
            var selected = survivor->Hotbar.GetPointer(survivor->Selected);
            if (input->Fire.WasPressed && selected->Kind == ItemKind.SecondScoop)
            {
                foreach (var other in f.Unsafe.GetComponentBlockIterator<Survivor>())
                {
                    if (!other.Component->Dead) continue;
                    Combat.Revive(f, other.Entity, other.Component, filter.Transform->Position + look * FP._0_75);
                    *selected = default;
                    break;
                }
            }

            var move = new FPVector3(input->Move.X, 0, input->Move.Y);
            if (move.SqrMagnitude > 1)
            {
                move = move.Normalized;
            }
            var bulky = survivor->Carried.Kind != ItemKind.None;
            filter.Controller->MaxSpeed = bulky ? settings.WalkSpeed * FP._0_75 : input->Sprint.IsDown ? settings.SprintSpeed : settings.WalkSpeed;
            if (input->Jump.WasPressed && !bulky)
            {
                filter.Controller->Jump(f);
            }
            filter.Controller->Move(f, filter.Entity, filter.Transform->Rotation * move);
            var ground = f.Physics3D.Raycast(filter.Transform->Position + FPVector3.Up * FP._0_25, FPVector3.Down, FP._0_75, -1, QueryOptions.HitSolids);
            survivor->Standing = ground.HasValue ? ground.Value.Entity : EntityRef.None;
        }

        static void Interact(Frame f, ref Filter filter, EntityRef target, Transform3D truck, ZombieTruckSettings settings)
        {
            var survivor = filter.Survivor;
            if (target.IsValid && f.Unsafe.TryGetPointer(target, out Pickup* pickup))
            {
                if (!Inventory.TryAdd(survivor, pickup->Item)) return;
                f.Events.ItemPickedUp(filter.Link->Player, pickup->Item.Kind, f.Unsafe.GetPointer<Transform3D>(target)->Position);
                f.Destroy(target);
                return;
            }
            if (target.IsValid && f.Unsafe.TryGetPointer(target, out Station* station))
            {
                UseStation(f, ref filter, target, station, settings);
                return;
            }

            // Fixed spots on the truck: driver seat, ladder, hatch and rear door. The nearest one in range is used; the seat
            // takes the wheel, the others move the survivor to their partner spot.
            var truckState = f.Unsafe.GetPointerSingleton<Truck>();
            var local = truck.InverseTransformPoint(filter.Transform->Position);
            var nearest = settings.InteractRange * settings.InteractRange;
            var spots = stackalloc FPVector3[] { settings.LadderBottom, settings.HatchTop, settings.RearOutside, settings.RearInside, settings.DriverSeat };
            var partners = stackalloc FPVector3[] { settings.HatchTop, settings.LadderBottom, settings.RearInside, settings.RearOutside };
            var canDrive = !truckState->Driver.IsValid && survivor->Carried.Kind == ItemKind.None;
            var best = -1;
            for (int i = 0; i < 5; i++)
            {
                var distance = (local - spots[i]).SqrMagnitude;
                if (distance >= nearest || (i == 4 && !canDrive)) continue;
                nearest = distance;
                best = i;
            }
            if (best < 0) return;
            if (best == 4)
            {
                survivor->Driving = true;
                truckState->Driver = filter.Link->Player;
                return;
            }
            filter.Transform->Teleport(f, truck.TransformPoint(partners[best]));
            filter.Controller->Velocity = FPVector3.Zero;
        }

        static void UseStation(Frame f, ref Filter filter, EntityRef entity, Station* station, ZombieTruckSettings settings)
        {
            var survivor = filter.Survivor;
            var carried = &survivor->Carried;
            var selected = survivor->Hotbar.GetPointer(survivor->Selected);
            var truck = f.Unsafe.GetPointerSingleton<Truck>();
            var position = f.Unsafe.GetPointer<Transform3D>(entity)->Position;
            switch (station->Kind)
            {
                case StationKind.Churn:
                    switch (carried->Kind)
                    {
                        case ItemKind.MilkCrate: station->Milk += 2; break;
                        case ItemKind.SugarSack: station->Sugar += 2; break;
                        case ItemKind.CocoaBag: station->Flavoring = Flavor.Chocolate; break;
                        case ItemKind.StrawberryBasket: station->Flavoring = Flavor.Strawberry; break;
                        case ItemKind.MintBundle: station->Flavoring = Flavor.Mint; break;
                        default: return;
                    }
                    *carried = default;
                    break;
                case StationKind.Freezer:
                    if (carried->Kind != ItemKind.Tub) return;
                    for (int i = 0; i < station->Slots.Length; i++)
                    {
                        if (station->Slots.GetPointer(i)->Kind != ItemKind.None) continue;
                        *station->Slots.GetPointer(i) = *carried;
                        *carried = default;
                        break;
                    }
                    break;
                case StationKind.Counter:
                    var best = -1;
                    for (int i = 0; i < station->Slots.Length; i++)
                    {
                        var slot = station->Slots.GetPointer(i);
                        if (slot->Count > 0 && (best < 0 || slot->Count > station->Slots.GetPointer(best)->Count)) best = i;
                    }
                    if (best < 0 || !Inventory.TryAdd(survivor, *station->Slots.GetPointer(best))) return;
                    *station->Slots.GetPointer(best) = default;
                    break;
                case StationKind.GunRack:
                    if (Inventory.Gun(selected->Kind).Pellets > 0)
                    {
                        for (int i = 0; i < station->Slots.Length; i++)
                        {
                            if (station->Slots.GetPointer(i)->Kind != ItemKind.None) continue;
                            *station->Slots.GetPointer(i) = *selected;
                            *selected = default;
                            break;
                        }
                        break;
                    }
                    for (int i = 0; i < station->Slots.Length; i++)
                    {
                        var rackSlot = station->Slots.GetPointer(i);
                        if (rackSlot->Kind == ItemKind.None || !Inventory.TryAdd(survivor, *rackSlot)) continue;
                        *rackSlot = default;
                        break;
                    }
                    break;
                case StationKind.Hopper:
                    if (selected->Kind != ItemKind.Pint || selected->Count == 0) return;
                    var capacity = settings.HopperCapacity * (truck->BigHopper ? 2 : 1);
                    truck->HopperRounds = System.Math.Min(capacity, truck->HopperRounds + selected->Count * settings.RoundsPerScoop);
                    truck->HopperFlavor = selected->Flavor;
                    *selected = default;
                    break;
                case StationKind.Turret:
                    foreach (var other in f.Unsafe.GetComponentBlockIterator<Survivor>())
                    {
                        if (other.Component->TurretSeat == station->Index + 1) return;
                    }
                    if (carried->Kind != ItemKind.None) return;
                    survivor->TurretSeat = station->Index + 1;
                    break;
                case StationKind.GunCrate:
                    if (station->Open) return;
                    station->Open = true;
                    var gun = CrateGuns[f.RNG->Next(0, CrateGuns.Length)];
                    var spec = Inventory.Gun(gun);
                    Inventory.SpawnPickup(f, new Item { Kind = gun, Flavor = Flavor.Vanilla, Count = spec.RoundsPerPint }, position + FPVector3.Up, FPVector3.Up * 3, false);
                    var ammo = spec.UsesJar
                        ? new Item { Kind = ItemKind.SprinkleJar }
                        : new Item { Kind = ItemKind.Pint, Flavor = (Flavor)f.RNG->Next(1, 5), Count = Inventory.ScoopsPerPint };
                    Inventory.SpawnPickup(f, ammo, position + FPVector3.Up, FPVector3.Up * 2 + FPVector3.Right, false);
                    break;
                case StationKind.Shop:
                    if (f.Global->Phase != GamePhase.Depot || Run.SoldOut(truck, station->Upgrade) || f.Global->Money < station->Price) return;
                    f.Global->Money -= station->Price;
                    Run.ApplyUpgrade(f, station->Upgrade, position);
                    f.Events.Purchased(station->Upgrade, station->Price, position);
                    break;
                case StationKind.DepotExit:
                    if (f.Global->Phase != GamePhase.Depot) return;
                    Run.StartNextArea(f);
                    break;
            }
            f.Events.StationUsed(entity, station->Kind);
        }

        // Tap Q to drop, hold to throw harder. A thrown scoop becomes a grenade.
        static void Drop(Frame f, ref Filter filter, Input* input, FPVector3 eye, FPVector3 look, ZombieTruckSettings settings)
        {
            var survivor = filter.Survivor;
            if (input->Drop.IsDown)
            {
                survivor->DropHeld += f.DeltaTime;
                return;
            }
            if (!input->Drop.WasReleased) return;
            var held = survivor->DropHeld;
            survivor->DropHeld = 0;
            if (survivor->Carried.Kind == ItemKind.None && survivor->Hotbar.GetPointer(survivor->Selected)->Kind == ItemKind.None) return;
            var item = Inventory.TakeOne(survivor);
            var thrown = held >= settings.ThrowHoldTime;
            var power = thrown ? FPMath.Lerp(settings.ThrowSpeedMin, settings.ThrowSpeedMax, held - settings.ThrowHoldTime) : FP._1_50;
            var velocity = look * power + FPVector3.Up * (thrown ? 2 : 1);
            if (survivor->Standing == f.GetSingletonEntityRef<Truck>())
            {
                var truck = f.Get<Transform3D>(survivor->Standing);
                velocity += truck.Forward * f.GetSingleton<Truck>().Speed;
            }
            var from = eye + look * FP._0_50;
            if (thrown) f.Events.Thrown(filter.Link->Player, from);
            if (thrown && item.Kind == ItemKind.Scoop)
            {
                var projectile = f.Create(settings.ProjectilePrototype);
                f.Unsafe.GetPointer<Transform3D>(projectile)->Teleport(f, from);
                f.Add(projectile, new Projectile { Flavor = item.Flavor, Velocity = velocity, Owner = filter.Link->Player, Radius = settings.GrenadeRadius });
                return;
            }
            Inventory.SpawnPickup(f, item, from, velocity, false);
        }

        static void Reload(Frame f, PlayerRef player, Survivor* survivor)
        {
            var gun = survivor->Hotbar.GetPointer(survivor->Selected);
            var spec = Inventory.Gun(gun->Kind);
            if (spec.Pellets == 0 || spec.Harpoon) return;
            var best = -1;
            for (int i = 0; i < survivor->Hotbar.Length; i++)
            {
                var slot = survivor->Hotbar.GetPointer(i);
                var fits = spec.UsesJar ? slot->Kind == ItemKind.SprinkleJar : slot->Kind == ItemKind.Pint && slot->Count > 0;
                if (!fits) continue;
                if (best < 0 || (slot->Flavor == gun->Flavor && survivor->Hotbar.GetPointer(best)->Flavor != gun->Flavor)) best = i;
            }
            if (best < 0) return;
            var ammo = survivor->Hotbar.GetPointer(best);
            gun->Count = spec.UsesJar ? Inventory.RoundsPerJar : spec.RoundsPerPint * ammo->Count / Inventory.ScoopsPerPint;
            gun->Flavor = spec.UsesJar ? Flavor.None : ammo->Flavor;
            *ammo = default;
            f.Events.Reloaded(player, gun->Flavor);
        }

        // Holding fire on the churn (crank) or on the freezer with the scooper turns mouse movement into progress.
        // Clicking the scoop counter with scoops selected packs one into a pint.
        static void Work(Frame f, ref Filter filter, Input* input, EntityRef target, ZombieTruckSettings settings)
        {
            var survivor = filter.Survivor;
            if (!input->Fire.IsDown || !target.IsValid || !f.Unsafe.TryGetPointer(target, out Station* station))
            {
                survivor->WorkProgress = 0;
                survivor->WorkTarget = EntityRef.None;
                return;
            }
            if (survivor->WorkTarget != target)
            {
                survivor->WorkProgress = 0;
                survivor->WorkTarget = target;
            }
            var selected = survivor->Hotbar.GetPointer(survivor->Selected);
            if (station->Kind == StationKind.Counter && input->Fire.WasPressed && selected->Kind == ItemKind.Scoop)
            {
                for (int i = 0; i < station->Slots.Length; i++)
                {
                    var pint = station->Slots.GetPointer(i);
                    var fits = pint->Kind == ItemKind.None || (pint->Flavor == selected->Flavor && pint->Count < Inventory.ScoopsPerPint);
                    if (!fits) continue;
                    *pint = new Item { Kind = ItemKind.Pint, Flavor = selected->Flavor, Count = pint->Count + 1 };
                    selected->Count--;
                    if (selected->Count == 0) *selected = default;
                    f.Events.StationUsed(target, station->Kind);
                    return;
                }
                return;
            }

            var tub = -1;
            for (int i = 0; i < station->Slots.Length && station->Kind == StationKind.Freezer; i++)
            {
                if (station->Slots.GetPointer(i)->Count > 0)
                {
                    tub = i;
                    break;
                }
            }
            var churning = station->Kind == StationKind.Churn && station->Milk > 0 && station->Sugar > 0;
            var scooping = tub >= 0 && selected->Kind == ItemKind.Scooper;
            if (!churning && !scooping) return;
            survivor->WorkProgress += input->Gesture * settings.GestureRate;
            if (survivor->WorkProgress < 1) return;
            survivor->WorkProgress = 0;
            var stationPosition = f.Unsafe.GetPointer<Transform3D>(target)->Position;
            if (churning)
            {
                station->Milk--;
                station->Sugar--;
                var flavor = station->Flavoring == Flavor.None ? Flavor.Vanilla : station->Flavoring;
                station->Flavoring = Flavor.None;
                var made = new Item { Kind = ItemKind.Tub, Flavor = flavor, Count = Inventory.ScoopsPerTub };
                Inventory.SpawnPickup(f, made, stationPosition + FPVector3.Up * FP._1_50, FPVector3.Up * 2, false);
            }
            else
            {
                var slot = station->Slots.GetPointer(tub);
                var scoop = new Item { Kind = ItemKind.Scoop, Flavor = slot->Flavor, Count = 1 };
                slot->Count--;
                if (slot->Count == 0) *slot = default;
                if (!Inventory.TryAdd(survivor, scoop))
                {
                    Inventory.SpawnPickup(f, scoop, stationPosition + FPVector3.Up * FP._1_50, FPVector3.Up, false);
                }
            }
            f.Events.StationUsed(target, station->Kind);
        }
    }
}
