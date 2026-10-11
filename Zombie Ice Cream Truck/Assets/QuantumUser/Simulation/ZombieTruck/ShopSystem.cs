namespace Quantum
{
    using Photon.Deterministic;

    // The depot's slot machine. A pull decides the prize up front and lays out reels that show it; when the spin ends the
    // machine pays out: a jackpot coughs up a Jackpot Blaster and cash, a pair a tub of that flavor, three brains a
    // zombie.
    public unsafe class ShopSystem : SystemMainThread
    {
        public const int Nothing = 0;
        public const int Pair = 1;
        public const int Jackpot = 2;
        public const int Brains = 3;

        public static void Spin(Frame f, Station* station, ZombieTruckSettings settings)
        {
            station->Timer = settings.SlotSpinTime;
            var roll = f.RNG->Next();
            var tier = roll < settings.SlotJackpotChance ? Jackpot
                : roll < settings.SlotJackpotChance + settings.SlotPairChance ? Pair
                : roll < settings.SlotJackpotChance + settings.SlotPairChance + settings.SlotBrainsChance ? Brains
                : Nothing;
            // Reel symbols: Flavor.None is the brain, then Vanilla through Coffee.
            var reels = stackalloc Flavor[3];
            var main = (Flavor)f.RNG->Next(1, 6);
            reels[0] = reels[1] = reels[2] = tier == Brains ? Flavor.None : main;
            if (tier == Pair)
            {
                var odd = (Flavor)f.RNG->Next(0, 6);
                while (odd == main) odd = (Flavor)f.RNG->Next(0, 6);
                reels[f.RNG->Next(0, 3)] = odd;
            }
            if (tier == Nothing)
            {
                reels[0] = (Flavor)f.RNG->Next(0, 6);
                reels[1] = (Flavor)f.RNG->Next(0, 6);
                while (reels[1] == reels[0]) reels[1] = (Flavor)f.RNG->Next(0, 6);
                reels[2] = (Flavor)f.RNG->Next(0, 6);
                while (reels[2] == reels[0] || reels[2] == reels[1]) reels[2] = (Flavor)f.RNG->Next(0, 6);
            }
            for (int i = 0; i < 3; i++) *station->Slots.GetPointer(i) = new Item { Kind = ItemKind.Scoop, Flavor = reels[i] };
            station->Slots.GetPointer(3)->Count = tier;
        }

        public override void Update(Frame f)
        {
            var settings = f.FindAsset(f.RuntimeConfig.Settings);
            foreach (var pair in f.Unsafe.GetComponentBlockIterator<Station>())
            {
                var station = pair.Component;
                if (station->Kind != StationKind.SlotMachine || station->Timer <= 0) continue;
                station->Timer -= f.DeltaTime;
                if (station->Timer > 0) continue;
                var machine = f.Get<Transform3D>(pair.Entity);
                var tray = machine.TransformPoint(new FPVector3(0, FP._0_75, FP._0_75));
                var toss = machine.Forward * 3 + FPVector3.Up * 3;
                var tier = station->Slots.GetPointer(3)->Count;
                var first = station->Slots.GetPointer(0)->Flavor;
                var flavor = first == station->Slots.GetPointer(1)->Flavor || first == station->Slots.GetPointer(2)->Flavor ? first : station->Slots.GetPointer(1)->Flavor;
                if (tier == Jackpot)
                {
                    var blaster = Inventory.Gun(ItemKind.JackpotBlaster);
                    Inventory.SpawnPickup(f, new Item { Kind = ItemKind.JackpotBlaster, Flavor = flavor, Count = blaster.RoundsPerPint }, tray, toss, false);
                    f.Global->Money += settings.SlotJackpotCash;
                }
                if (tier == Pair)
                {
                    Inventory.SpawnPickup(f, new Item { Kind = ItemKind.Tub, Flavor = flavor, Count = Inventory.ScoopsPerTub }, tray, toss, false);
                }
                if (tier == Brains)
                {
                    var exit = machine.TransformPoint(new FPVector3(0, 0, FP._1_25));
                    ZombieSystem.Create(f, settings, ZombieKind.Sprinter, exit, exit + machine.Forward, ZombieState.Chasing);
                }
                f.Events.SlotsResult(pair.Entity, tier, flavor);
            }
        }
    }
}
