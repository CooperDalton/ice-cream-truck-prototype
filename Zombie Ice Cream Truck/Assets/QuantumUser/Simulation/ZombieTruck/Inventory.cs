namespace Quantum
{
    using System;
    using Photon.Deterministic;

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
    }

    // Hotbar rules, gun stats and pickup spawning. Items from MilkCrate onward in ItemKind are bulky: carried in both
    // hands instead of the hotbar.
    public static unsafe class Inventory
    {
        public const Int32 MaxScoopStack = 8;
        public const Int32 ScoopsPerPint = 4;
        public const Int32 ScoopsPerTub = 8;
        public const Int32 RoundsPerJar = 40;

        public static GunSpec Gun(ItemKind kind)
        {
            switch (kind)
            {
                case ItemKind.ScoopPistol:
                    return new GunSpec { Interval = FP._0_20, RoundsPerPint = 16, Damage = 1, Pellets = 1, Spread = FP._0_50, Range = 60 };
                case ItemKind.SundaeShotgun:
                    return new GunSpec { Interval = FP._0_75, RoundsPerPint = 8, Damage = 1, Pellets = 8, Spread = 7, Range = 25 };
                case ItemKind.SprinkleSMG:
                    return new GunSpec { Interval = FP._0_10 - FP._0_02, RoundsPerPint = RoundsPerJar, Damage = 1, Pellets = 1, Spread = FP._2 + FP._0_50, Range = 45, UsesJar = true };
                case ItemKind.LongSpoon:
                    return new GunSpec { Interval = FP._1, RoundsPerPint = 4, Damage = 3, Pellets = 1, Spread = 0, Range = 120, Pierce = true };
                case ItemKind.ConeLauncher:
                    return new GunSpec { Interval = FP._0_75 + FP._0_20, RoundsPerPint = 4, Pellets = 1, Range = 0, Launcher = true };
                case ItemKind.BananaHarpoon:
                    return new GunSpec { Interval = FP._1_25, Damage = 2, Pellets = 1, Range = 30, Harpoon = true };
                default:
                    return default;
            }
        }

        // Adds an item to the carried slot (bulky) or the hotbar, merging scoop stacks. Returns false when there is no room.
        public static bool TryAdd(Survivor* survivor, Item item)
        {
            if (item.Kind >= ItemKind.MilkCrate)
            {
                if (survivor->Carried.Kind != ItemKind.None) return false;
                survivor->Carried = item;
                return true;
            }
            if (item.Kind == ItemKind.Scoop)
            {
                for (int i = 0; i < survivor->Hotbar.Length; i++)
                {
                    var slot = survivor->Hotbar.GetPointer(i);
                    if (slot->Kind != ItemKind.Scoop || slot->Flavor != item.Flavor || slot->Count >= MaxScoopStack) continue;
                    slot->Count += item.Count;
                    return true;
                }
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

        // Removes one throwable unit from the carried slot or the selected hotbar slot (one scoop from a stack).
        public static Item TakeOne(Survivor* survivor)
        {
            if (survivor->Carried.Kind != ItemKind.None)
            {
                var carried = survivor->Carried;
                survivor->Carried = default;
                return carried;
            }
            var slot = survivor->Hotbar.GetPointer(survivor->Selected);
            var item = *slot;
            if (item.Kind == ItemKind.Scoop && item.Count > 1)
            {
                slot->Count--;
                item.Count = 1;
                return item;
            }
            *slot = default;
            return item;
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
            *survivor->Hotbar.GetPointer(1) = new Item { Kind = ItemKind.Scooper };
            *survivor->Hotbar.GetPointer(2) = new Item { Kind = ItemKind.Pint, Flavor = Flavor.Vanilla, Count = ScoopsPerPint };
            survivor->Carried = default;
            survivor->Selected = 0;
            survivor->Health = settings.MaxHealth;
            survivor->Dead = false;
            survivor->Driving = false;
            survivor->TurretSeat = 0;
        }
    }
}
