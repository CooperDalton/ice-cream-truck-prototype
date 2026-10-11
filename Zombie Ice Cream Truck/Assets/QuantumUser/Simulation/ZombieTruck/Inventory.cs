namespace Quantum
{
    using System;
    using Photon.Deterministic;

    // Melee cones reuse the fields: RoundsPerPint is bites per scoop, Range is reach and Cleave is how many zombies one
    // swing can hit. Price is what the depot pedestals ask.
    public struct GunSpec
    {
        public FP Interval;
        public Int32 RoundsPerPint;
        public Int32 Damage;
        public Int32 Pellets;
        public FP Spread;
        public FP Range;
        public bool Pierce;
        public bool Launcher;
        public bool UsesJar;
        public bool Harpoon;
        public bool Hose;
        public bool Rocket;
        public bool Jackpot;
        public bool Melee;
        public Int32 Cleave;
        public Int32 Price;
    }

    // Hotbar rules, gun stats and pickup spawning. Everything goes in the hotbar; scoops and ingredient packs (MilkCrate
    // through NutBag in ItemKind) stack.
    public static unsafe class Inventory
    {
        public const Int32 MaxScoopStack = 8;
        public const Int32 MaxIngredientStack = 4;
        public const Int32 ScoopsPerPint = 4;
        public const Int32 ScoopsPerTub = 8;
        public const Int32 RoundsPerJar = 40;

        public static GunSpec Gun(ItemKind kind)
        {
            switch (kind)
            {
                case ItemKind.ScoopPistol:
                    return new GunSpec { Interval = FP._0_20, RoundsPerPint = 16, Damage = 1, Pellets = 1, Spread = FP._0_50, Range = 60, Price = 20 };
                case ItemKind.SundaeShotgun:
                    return new GunSpec { Interval = FP._0_75, RoundsPerPint = 8, Damage = 1, Pellets = 8, Spread = 7, Range = 25, Price = 45 };
                case ItemKind.SprinkleSMG:
                    return new GunSpec { Interval = FP._0_10 - FP._0_02, RoundsPerPint = RoundsPerJar, Damage = 1, Pellets = 1, Spread = FP._2 + FP._0_50, Range = 45, UsesJar = true, Price = 40 };
                case ItemKind.LongSpoon:
                    return new GunSpec { Interval = FP._1, RoundsPerPint = 4, Damage = 3, Pellets = 1, Spread = 0, Range = 120, Pierce = true, Price = 50 };
                case ItemKind.ConeLauncher:
                    return new GunSpec { Interval = FP._0_75 + FP._0_20, RoundsPerPint = 4, Pellets = 1, Range = 0, Launcher = true, Price = 60 };
                case ItemKind.BananaHarpoon:
                    return new GunSpec { Interval = FP._1_25, Damage = 2, Pellets = 1, Range = 30, Harpoon = true, Price = 35 };
                // A short piercing stream of soft serve; too messy to aim for heads.
                case ItemKind.SoftServeHose:
                    return new GunSpec { Interval = FP._0_10, RoundsPerPint = 40, Damage = 1, Pellets = 1, Spread = 4, Range = 11, Pierce = true, Hose = true, Price = 55 };
                // A straight-flying sundae rocket with a huge blast.
                case ItemKind.SundaeBazooka:
                    return new GunSpec { Interval = FP._1_50, RoundsPerPint = 2, Damage = 6, Pellets = 1, Range = 0, Rocket = true, Price = 80 };
                // Every shot spins: a dud, a shotgun spread or a jackpot blast. Only the slot machine pays it out.
                case ItemKind.JackpotBlaster:
                    return new GunSpec { Interval = FP._0_50, RoundsPerPint = 12, Damage = 1, Pellets = 1, Spread = 2, Range = 50, Jackpot = true, Price = 0 };
                case ItemKind.PlainCone:
                    return new GunSpec { Interval = FP._0_50, RoundsPerPint = 4, Damage = 2, Pellets = 1, Range = 2, Melee = true, Cleave = 1, Price = 10 };
                case ItemKind.WaffleCone:
                    return new GunSpec { Interval = FP._0_50, RoundsPerPint = 6, Damage = 3, Pellets = 1, Range = FP._2 + FP._0_25, Melee = true, Cleave = 2, Price = 30 };
                case ItemKind.DoubleDip:
                    return new GunSpec { Interval = FP._0_50 + FP._0_10, RoundsPerPint = 8, Damage = 5, Pellets = 1, Range = FP._2 + FP._0_50, Melee = true, Cleave = 3, Price = 50 };
                default:
                    return default;
            }
        }

        // Adds an item to the hotbar, merging scoop and ingredient stacks. Returns false when there is no room.
        public static bool TryAdd(Survivor* survivor, Item item)
        {
            var stack = item.Kind == ItemKind.Scoop ? MaxScoopStack : item.Kind >= ItemKind.MilkCrate && item.Kind <= ItemKind.NutBag ? MaxIngredientStack : 0;
            for (int i = 0; i < survivor->Hotbar.Length; i++)
            {
                var slot = survivor->Hotbar.GetPointer(i);
                if (slot->Kind != item.Kind || slot->Flavor != item.Flavor || slot->Count + item.Count > stack) continue;
                slot->Count += item.Count;
                return true;
            }
            for (int i = 0; i < survivor->Hotbar.Length; i++)
            {
                var slot = survivor->Hotbar.GetPointer(i);
                if (slot->Kind != ItemKind.None) continue;
                *slot = item;
                return true;
            }
            return false;
        }

        // Removes one throwable unit from the selected hotbar slot (one scoop or pack from a stack).
        public static Item TakeOne(Survivor* survivor)
        {
            var slot = survivor->Hotbar.GetPointer(survivor->Selected);
            var item = *slot;
            var stacks = item.Kind == ItemKind.Scoop || (item.Kind >= ItemKind.MilkCrate && item.Kind <= ItemKind.NutBag);
            if (stacks && item.Count > 1)
            {
                slot->Count--;
                item.Count = 1;
                return item;
            }
            *slot = default;
            return item;
        }

        // The selected hotbar item if its kind is between first and last in ItemKind, otherwise the first such item in the
        // hotbar; null when there is none. Stations take what fits from the hotbar without the player switching to it.
        public static Item* Find(Survivor* survivor, ItemKind first, ItemKind last)
        {
            var selected = survivor->Hotbar.GetPointer(survivor->Selected);
            if (selected->Kind >= first && selected->Kind <= last) return selected;
            for (int i = 0; i < survivor->Hotbar.Length; i++)
            {
                var slot = survivor->Hotbar.GetPointer(i);
                if (slot->Kind >= first && slot->Kind <= last) return slot;
            }
            return null;
        }

        public static EntityRef SpawnPickup(Frame f, Item item, FPVector3 position, FPVector3 velocity, bool resting)
        {
            var settings = f.FindAsset(f.RuntimeConfig.Settings);
            var entity = f.Create(settings.ItemPrototypes[(int)item.Kind]);
            f.Unsafe.GetPointer<Transform3D>(entity)->Teleport(f, position);
            f.Add(entity, new Pickup { Item = item, Velocity = velocity, Resting = resting });
            var shape = Shape3D.CreateBox(new FPVector3(FP._0_25, FP._0_25, FP._0_25), new FPVector3(0, FP._0_25, 0));
            f.Add(entity, PhysicsCollider3D.Create(f, shape, null, true));
            return entity;
        }

        public static void GiveLoadout(Survivor* survivor, ZombieTruckSettings settings)
        {
            for (int i = 0; i < survivor->Hotbar.Length; i++) *survivor->Hotbar.GetPointer(i) = default;
            *survivor->Hotbar.GetPointer(0) = new Item { Kind = ItemKind.ScoopPistol, Flavor = Flavor.Vanilla, Count = settings.StartingRounds };
            *survivor->Hotbar.GetPointer(1) = new Item { Kind = ItemKind.Pint, Flavor = Flavor.Vanilla, Count = ScoopsPerPint };
            *survivor->Hotbar.GetPointer(2) = new Item { Kind = ItemKind.PlainCone, Flavor = Flavor.Vanilla, Count = Gun(ItemKind.PlainCone).RoundsPerPint };
            survivor->Selected = 0;
            survivor->Health = settings.MaxHealth;
            survivor->Dead = false;
            survivor->Driving = false;
            survivor->Climbing = false;
            survivor->TurretSeat = 0;
        }
    }
}
