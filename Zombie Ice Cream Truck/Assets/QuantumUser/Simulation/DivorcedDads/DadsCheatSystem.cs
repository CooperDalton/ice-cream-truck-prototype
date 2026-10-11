namespace Quantum
{
    using Photon.Deterministic;

    // The debug menu's cheats (P in game, keys 1-9).
    public enum Cheat : byte
    {
        Money, Sales, FillFreezer, AllUpgrades, FillHopper, Repair, SkipAhead, ClearStrikes, ToLot,
    }

    // Sent as a command so a cheat reaches every client on the same tick.
    public class DadsCheat : DeterministicCommand
    {
        public Cheat Cheat;

        public override void Serialize(BitStream stream)
        {
            var value = (byte)Cheat;
            stream.Serialize(ref value);
            Cheat = (Cheat)value;
        }
    }

    // Applies the debug-menu cheats any player sends: cash and sales, a full freezer of the fancy flavors, every
    // upgrade, a full minigun hopper, a repaired truck, skipping to the next part of the day, a clean slate with Big
    // Dairy and the cops, and the truck (with whoever is aboard) back at Big Dairy's lot.
    public unsafe class DadsCheatSystem : SystemMainThread
    {
        public override void Update(Frame f)
        {
            for (int p = 0; p < f.PlayerCount; p++)
            {
                if (f.GetPlayerCommand(p) is DadsCheat command) Apply(f, p, command.Cheat);
            }
        }

        static void Apply(Frame f, PlayerRef player, Cheat cheat)
        {
            var settings = f.FindAsset(f.RuntimeConfig.DadsSettings);
            var run = f.Unsafe.GetPointerSingleton<DadsRun>();
            var vanEntity = f.GetSingletonEntityRef<Van>();
            var van = f.Unsafe.GetPointer<Van>(vanEntity);
            switch (cheat)
            {
                case Cheat.Money:
                    run->Money += 500;
                    return;
                case Cheat.Sales:
                    run->Earned += 100;
                    return;
                case Cheat.FillFreezer:
                    var flavors = stackalloc Treat[] { Treat.Strawberry, Treat.Coffee, Treat.RockyRoad, Treat.GoldLeaf };
                    foreach (var pair in f.Unsafe.GetComponentBlockIterator<Fixture>())
                    {
                        if (pair.Component->Kind != FixtureKind.Tub) continue;
                        pair.Component->Treat = flavors[pair.Component->Index % 4];
                        pair.Component->Count = settings.TubCapacity;
                    }
                    return;
                case Cheat.AllUpgrades:
                    // In shop order, so waffle cones come before double waffles and Maple Grove before Hillside.
                    var position = f.Get<Transform3D>(vanEntity).Position;
                    for (var upgrade = Upgrade.ScoopPistol; upgrade <= Upgrade.HillsidePermit; upgrade++)
                    {
                        if (!DadsGame.SoldOut(run, upgrade)) DadsGame.Grant(f, upgrade, position);
                    }
                    return;
                case Cheat.FillHopper:
                    van->HopperRounds = settings.HopperCapacity;
                    van->HopperTreat = Treat.Strawberry;
                    return;
                case Cheat.Repair:
                    van->Damage = 0;
                    return;
                case Cheat.SkipAhead:
                    SkipAhead(f, settings, run, player);
                    return;
                case Cheat.ClearStrikes:
                    run->Strikes = 0;
                    run->Heat = 0;
                    return;
                case Cheat.ToLot:
                    ToLot(f, settings, vanEntity);
                    return;
            }
        }

        // The tutorial ends (this player at the wheel), the morning ends, the afternoon turns to dusk, dusk to night, and
        // the night goes straight to Big Dairy's collection.
        static void SkipAhead(Frame f, DadsSettings settings, DadsRun* run, PlayerRef player)
        {
            switch (run->Phase)
            {
                case DayPhase.Tutorial:
                    foreach (var pair in f.Unsafe.GetComponentBlockIterator<Dad>())
                    {
                        if (pair.Component->Player == player) DadsGame.FinishTutorial(f, pair.Entity);
                    }
                    return;
                case DayPhase.Morning:
                    run->Phase = DayPhase.Day;
                    f.Events.DayPhaseChanged(DayPhase.Day, run->Day);
                    return;
                case DayPhase.Day:
                    run->Clock = FPMath.Max(run->Clock, settings.DuskAt);
                    return;
                case DayPhase.Dusk:
                    run->Clock = FPMath.Max(run->Clock, settings.NightAt);
                    return;
                case DayPhase.Night:
                    DadsGame.Collect(f);
                    return;
            }
        }

        // Moves the van to its spot at Big Dairy's lot; dads standing on or in it come along where they were.
        static void ToLot(Frame f, DadsSettings settings, EntityRef vanEntity)
        {
            var before = f.Get<Transform3D>(vanEntity);
            DadsGame.ParkVan(f, settings.LotPark, settings.LotYaw);
            var after = f.Get<Transform3D>(vanEntity);
            var turn = after.Rotation * FPQuaternion.Inverse(before.Rotation);
            foreach (var pair in f.Unsafe.GetComponentBlockIterator<Dad>())
            {
                if (pair.Component->Standing != vanEntity) continue;
                var transform = f.Unsafe.GetPointer<Transform3D>(pair.Entity);
                transform->Teleport(f, after.TransformPoint(before.InverseTransformPoint(transform->Position)));
                pair.Component->YawOffset += turn.AsEuler.Y;
            }
        }
    }
}
