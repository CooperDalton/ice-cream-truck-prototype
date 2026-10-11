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

        static readonly ItemKind[] CrateGuns = { ItemKind.SundaeShotgun, ItemKind.SprinkleSMG, ItemKind.LongSpoon, ItemKind.ConeLauncher, ItemKind.BananaHarpoon,
            ItemKind.SoftServeHose, ItemKind.WaffleCone };

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

            survivor->Crouching = input->Crouch.IsDown && !survivor->Driving && survivor->TurretSeat == 0 && !survivor->Climbing;
            survivor->Pitch = FPMath.Clamp(input->Pitch, -85, 85);
            filter.Transform->Rotation = FPQuaternion.Euler(0, input->Yaw + survivor->YawOffset, 0);
            if (input->Slot > 0 && input->Slot <= survivor->Hotbar.Length && survivor->Selected != input->Slot - 1)
            {
                survivor->Selected = input->Slot - 1;
                survivor->WorkProgress = 0;
            }

            if (survivor->Driving || survivor->TurretSeat > 0)
            {
                if (survivor->Driving && input->Aim.WasPressed)
                {
                    var music = f.Unsafe.GetPointerSingleton<Truck>();
                    music->MusicOff = !music->MusicOff;
                }
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

            var eye = filter.Transform->Position + FPVector3.Up * (survivor->Crouching ? settings.CrouchEyeHeight : settings.EyeHeight);
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

            if (survivor->Climbing)
            {
                Climb(f, ref filter, input, truck, settings);
                return;
            }

            var move = new FPVector3(input->Move.X, 0, input->Move.Y);
            if (move.SqrMagnitude > 1)
            {
                move = move.Normalized;
            }
            filter.Controller->MaxSpeed = survivor->Crouching ? settings.CrouchSpeed : input->Sprint.IsDown ? settings.SprintSpeed : settings.WalkSpeed;
            if (input->Jump.WasPressed)
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
            // Truck stations work from inside or on top of the truck; from outside only the rear door does, so E doesn't
            // reach a station in view through the doorway.
            var outside = survivor->Standing != f.GetSingletonEntityRef<Truck>();
            if (target.IsValid && f.Unsafe.TryGetPointer(target, out Station* station)
                && !(outside && f.Has<Attached>(target) && station->Kind != StationKind.RearDoor))
            {
                UseStation(f, ref filter, target, station, settings);
                return;
            }

            // Fixed spots on the truck: the ladder (grab it), the open hatch from the roof (climb down) and the driver seat.
            // The nearest one in range is used.
            var truckState = f.Unsafe.GetPointerSingleton<Truck>();
            var local = truck.InverseTransformPoint(filter.Transform->Position);
            var nearest = FP.MaxValue;
            var spots = stackalloc FPVector3[] { settings.LadderBottom, settings.HatchTop, settings.DriverSeat };
            var ranges = stackalloc FP[] { settings.LadderRange, settings.InteractRange, settings.InteractRange };
            var usable = stackalloc bool[] { true, HatchOpen(f), !truckState->Driver.IsValid };
            var best = -1;
            for (int i = 0; i < 3; i++)
            {
                var distance = (local - spots[i]).SqrMagnitude;
                if (distance >= nearest || distance >= ranges[i] * ranges[i] || !usable[i]) continue;
                nearest = distance;
                best = i;
            }
            if (best < 0) return;
            if (best == 2)
            {
                survivor->Driving = true;
                truckState->Driver = filter.Link->Player;
                if (f.Global->Phase == GamePhase.Tutorial) Run.EndTutorial(f);
                return;
            }
            survivor->Climbing = true;
            var feet = best == 0 ? settings.LadderClimb.Y : settings.RoofHeight - FP._0_10;
            filter.Transform->Teleport(f, truck.TransformPoint(new FPVector3(settings.LadderClimb.X, feet, settings.LadderClimb.Z)));
            filter.Controller->Velocity = FPVector3.Zero;
        }

        // On the ladder W/S climb and jump lets go. Climbing past the roof through the open hatch steps off beside it; a
        // shut hatch stops the climber just under it (they can push it open with E from there).
        static void Climb(Frame f, ref Filter filter, Input* input, Transform3D truck, ZombieTruckSettings settings)
        {
            var survivor = filter.Survivor;
            filter.Controller->Velocity = FPVector3.Zero;
            survivor->Standing = f.GetSingletonEntityRef<Truck>();
            var local = truck.InverseTransformPoint(filter.Transform->Position);
            var open = HatchOpen(f);
            var feet = FPMath.Clamp(local.Y + input->Move.Y * settings.ClimbSpeed * f.DeltaTime, settings.LadderClimb.Y, open ? settings.RoofHeight : settings.LadderClosedTop);
            if (input->Jump.WasPressed || (input->Move.Y < 0 && feet <= settings.LadderClimb.Y))
            {
                survivor->Climbing = false;
                return;
            }
            if (open && feet >= settings.RoofHeight)
            {
                survivor->Climbing = false;
                filter.Transform->Teleport(f, truck.TransformPoint(settings.HatchExit));
                return;
            }
            filter.Transform->Position = truck.TransformPoint(new FPVector3(settings.LadderClimb.X, feet, settings.LadderClimb.Z));
        }

        static bool HatchOpen(Frame f)
        {
            foreach (var pair in f.Unsafe.GetComponentBlockIterator<Station>())
            {
                if (pair.Component->Kind == StationKind.Hatch) return pair.Component->Open;
            }
            throw new InvalidOperationException("The truck has no hatch station");
        }

        static void UseStation(Frame f, ref Filter filter, EntityRef entity, Station* station, ZombieTruckSettings settings)
        {
            var survivor = filter.Survivor;
            var selected = survivor->Hotbar.GetPointer(survivor->Selected);
            var truck = f.Unsafe.GetPointerSingleton<Truck>();
            var position = f.Unsafe.GetPointer<Transform3D>(entity)->Position;
            switch (station->Kind)
            {
                // One pack of the selected ingredient, or the first one in the hotbar.
                case StationKind.Churn:
                    var ingredient = Inventory.Find(survivor, ItemKind.MilkCrate, ItemKind.NutBag);
                    if (ingredient == null) return;
                    switch (ingredient->Kind)
                    {
                        case ItemKind.MilkCrate: station->Milk += 2; break;
                        case ItemKind.SugarSack: station->Sugar += 2; break;
                        // Cocoa and strawberries together churn Neapolitan.
                        case ItemKind.CocoaBag: station->Flavoring = station->Flavoring == Flavor.Strawberry ? Flavor.Neapolitan : Flavor.Chocolate; break;
                        case ItemKind.StrawberryBasket: station->Flavoring = station->Flavoring == Flavor.Chocolate ? Flavor.Neapolitan : Flavor.Strawberry; break;
                        case ItemKind.MintBundle: station->Flavoring = Flavor.Mint; break;
                        case ItemKind.CoffeeSack: station->Flavoring = Flavor.Coffee; break;
                        case ItemKind.NutBag: station->Flavoring = Flavor.RockyRoad; break;
                    }
                    ingredient->Count--;
                    if (ingredient->Count <= 0) *ingredient = default;
                    break;
                // Selected scoops go back in as a tub holding that many, else a tub from the hotbar goes in; with neither
                // E grabs a stack of scoops like a click.
                case StationKind.Freezer:
                    var tub = selected->Kind == ItemKind.Scoop ? selected : Inventory.Find(survivor, ItemKind.Tub, ItemKind.Tub);
                    if (tub == null)
                    {
                        TakeScoops(f, survivor, entity, station);
                        return;
                    }
                    for (int i = 0; i < station->Slots.Length; i++)
                    {
                        if (station->Slots.GetPointer(i)->Kind != ItemKind.None) continue;
                        *station->Slots.GetPointer(i) = new Item { Kind = ItemKind.Tub, Flavor = tub->Flavor, Count = tub->Count };
                        *tub = default;
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
                    survivor->TurretSeat = station->Index + 1;
                    break;
                case StationKind.GunCrate:
                    if (station->Open) return;
                    station->Open = true;
                    var gun = CrateGuns[f.RNG->Next(0, CrateGuns.Length)];
                    var spec = Inventory.Gun(gun);
                    Inventory.SpawnPickup(f, new Item { Kind = gun, Flavor = Flavor.Vanilla, Count = spec.RoundsPerPint }, position + FPVector3.Up, FPVector3.Up * 3, false);
                    var ammo = spec.UsesJar ? new Item { Kind = ItemKind.SprinkleJar }
                        : spec.Melee ? new Item { Kind = ItemKind.Scoop, Flavor = (Flavor)f.RNG->Next(1, 6), Count = Inventory.ScoopsPerPint }
                        : new Item { Kind = ItemKind.Pint, Flavor = (Flavor)f.RNG->Next(1, 6), Count = Inventory.ScoopsPerPint };
                    Inventory.SpawnPickup(f, ammo, position + FPVector3.Up, FPVector3.Up * 2 + FPVector3.Right, false);
                    break;
                // Upgrade pedestals sell their upgrade, the others Slots[0]: weapons once, supplies as often as you like.
                case StationKind.Shop:
                    var stock = station->Slots.GetPointer(0);
                    if (f.Global->Phase != GamePhase.Depot || Run.SoldOut(truck, station->Upgrade) || (station->Upgrade == UpgradeKind.None && stock->Kind == ItemKind.None)) return;
                    if (f.Global->Money < station->Price)
                    {
                        f.Events.ShopDenied(position);
                        return;
                    }
                    f.Global->Money -= station->Price;
                    f.Events.Purchased(station->Upgrade, *stock, station->Price, position);
                    if (station->Upgrade != UpgradeKind.None)
                    {
                        Run.ApplyUpgrade(f, station->Upgrade, position);
                        break;
                    }
                    // The goods hop off the stand toward the buyer.
                    var front = f.Unsafe.GetPointer<Transform3D>(entity)->Forward;
                    Inventory.SpawnPickup(f, *stock, position + front * FP._0_75 + FPVector3.Up * FP._0_50, front * 2 + FPVector3.Up * 2, false);
                    if (Inventory.Gun(stock->Kind).Pellets > 0) *stock = default;
                    break;
                case StationKind.FuelIntake:
                    var tank = settings.FuelCapacity + (truck->BigTank ? settings.BigTankBonus : 0);
                    // The held tub, pint or scoops, otherwise the first tub in the hotbar (pints and scoops are ammo too, so
                    // they only go in when held).
                    var fuel = selected->Kind == ItemKind.Tub || selected->Kind == ItemKind.Pint || selected->Kind == ItemKind.Scoop ? selected
                        : Inventory.Find(survivor, ItemKind.Tub, ItemKind.Tub);
                    if (fuel == null || fuel->Count == 0 || truck->Fuel >= tank) return;
                    truck->Fuel = FPMath.Min(tank, truck->Fuel + fuel->Count);
                    truck->FuelFlavor = fuel->Flavor;
                    f.Events.Refueled(position, fuel->Count, fuel->Flavor);
                    *fuel = default;
                    break;
                case StationKind.SlotMachine:
                    if (f.Global->Phase != GamePhase.Depot || station->Timer > 0) return;
                    if (f.Global->Money < station->Price)
                    {
                        f.Events.ShopDenied(position);
                        return;
                    }
                    f.Global->Money -= station->Price;
                    ShopSystem.Spin(f, station, settings);
                    f.Events.SlotsPulled(entity);
                    break;
                // The rear door swings out about its hinge and the hatch lid flips up, taking their colliders with them.
                case StationKind.RearDoor:
                case StationKind.Hatch:
                    station->Open = !station->Open;
                    var hinge = f.Unsafe.GetPointer<Attached>(entity);
                    foreach (var placement in settings.TruckStations)
                    {
                        if (placement.Station != station->Kind) continue;
                        var closed = FPQuaternion.Euler(0, placement.Yaw, 0);
                        var swing = station->Kind == StationKind.RearDoor ? FPQuaternion.Euler(0, settings.DoorOpenYaw, 0) : FPQuaternion.Euler(settings.HatchOpenPitch, 0, 0);
                        hinge->LocalRotation = station->Open ? closed * swing : closed;
                    }
                    break;
                case StationKind.Shopkeeper:
                    station->Index++;
                    f.Events.ShopkeeperTalked(entity, station->Index);
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
            if (survivor->Hotbar.GetPointer(survivor->Selected)->Kind == ItemKind.None) return;
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
                f.Add(projectile, new Projectile { Flavor = item.Flavor, Velocity = velocity, Owner = filter.Link->Player, Radius = settings.GrenadeRadius, Damage = 3 });
                return;
            }
            Inventory.SpawnPickup(f, item, from, velocity, false);
        }

        // Guns load a pint (or a sprinkle jar); melee cones take one scoop off a stack.
        static void Reload(Frame f, PlayerRef player, Survivor* survivor)
        {
            var gun = survivor->Hotbar.GetPointer(survivor->Selected);
            var spec = Inventory.Gun(gun->Kind);
            if (spec.Pellets == 0 || spec.Harpoon) return;
            var best = -1;
            for (int i = 0; i < survivor->Hotbar.Length; i++)
            {
                var slot = survivor->Hotbar.GetPointer(i);
                var fits = spec.UsesJar ? slot->Kind == ItemKind.SprinkleJar
                    : spec.Melee ? slot->Kind == ItemKind.Scoop
                    : slot->Kind == ItemKind.Pint && slot->Count > 0;
                if (!fits) continue;
                if (best < 0 || (slot->Flavor == gun->Flavor && survivor->Hotbar.GetPointer(best)->Flavor != gun->Flavor)) best = i;
            }
            if (best < 0) return;
            var ammo = survivor->Hotbar.GetPointer(best);
            gun->Count = spec.UsesJar || spec.Melee ? spec.RoundsPerPint : spec.RoundsPerPint * ammo->Count / Inventory.ScoopsPerPint;
            gun->Flavor = spec.UsesJar ? Flavor.None : ammo->Flavor;
            if (spec.Melee && ammo->Count > 1) ammo->Count--;
            else *ammo = default;
            f.Events.Reloaded(player, gun->Flavor);
        }

        // Takes a stack of scoops out of the first freezer tub with any left.
        static void TakeScoops(Frame f, Survivor* survivor, EntityRef freezer, Station* station)
        {
            for (int i = 0; i < station->Slots.Length; i++)
            {
                var tub = station->Slots.GetPointer(i);
                if (tub->Count <= 0) continue;
                var taken = Math.Min(tub->Count, Inventory.MaxScoopStack);
                if (!Inventory.TryAdd(survivor, new Item { Kind = ItemKind.Scoop, Flavor = tub->Flavor, Count = taken })) return;
                tub->Count -= taken;
                if (tub->Count == 0) *tub = default;
                f.Events.StationUsed(freezer, station->Kind);
                return;
            }
        }

        // Holding fire on the churn turns mouse movement into cranking. Clicking the freezer grabs a stack of scoops, and
        // clicking the scoop counter with scoops selected packs one into a pint.
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

            if (station->Kind == StationKind.Freezer)
            {
                if (input->Fire.WasPressed) TakeScoops(f, survivor, target, station);
                return;
            }

            if (station->Kind != StationKind.Churn || station->Milk <= 0 || station->Sugar <= 0) return;
            survivor->WorkProgress += input->Gesture * settings.GestureRate;
            if (survivor->WorkProgress < 1) return;
            survivor->WorkProgress = 0;
            var stationPosition = f.Unsafe.GetPointer<Transform3D>(target)->Position;
            station->Milk--;
            station->Sugar--;
            var flavor = station->Flavoring == Flavor.None ? Flavor.Vanilla : station->Flavoring;
            station->Flavoring = Flavor.None;
            var made = new Item { Kind = ItemKind.Tub, Flavor = flavor, Count = Inventory.ScoopsPerTub };
            Inventory.SpawnPickup(f, made, stationPosition + FPVector3.Up * FP._1_50, FPVector3.Up * 2, false);
            f.Events.StationUsed(target, station->Kind);
        }
    }
}
