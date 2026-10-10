namespace Quantum
{
    using System;
    using Photon.Deterministic;

    // The day clock (it starts when the van leaves Big Dairy's lot; dusk sends the kids home, night brings the sugar
    // curfew), the collection and end cards, cooling heat, and fixture timers: the churn finishing a batch, patches and
    // tables restocking, and the vault door following its pressure plate.
    public unsafe class DayCycleSystem : SystemMainThread
    {
        public override void Update(Frame f)
        {
            var settings = f.FindAsset(f.RuntimeConfig.DadsSettings);
            var run = f.Unsafe.GetPointerSingleton<DadsRun>();
            var dt = f.DeltaTime;
            var van = f.Get<Transform3D>(f.GetSingletonEntityRef<Van>());
            switch (run->Phase)
            {
                case DayPhase.Morning:
                    if ((van.Position - settings.LotPark).SqrMagnitude > settings.LotRadius * settings.LotRadius) SetPhase(f, run, DayPhase.Day);
                    break;
                case DayPhase.Day:
                case DayPhase.Dusk:
                case DayPhase.Night:
                    run->Clock = FPMath.Min(1, run->Clock + dt / settings.DayLength);
                    run->Heat = FPMath.Max(0, run->Heat - settings.HeatDecay * dt);
                    if (run->Phase == DayPhase.Day && run->Clock >= settings.DuskAt) SetPhase(f, run, DayPhase.Dusk);
                    if (run->Phase == DayPhase.Dusk && run->Clock >= settings.NightAt) SetPhase(f, run, DayPhase.Night);
                    break;
                case DayPhase.Collection:
                    run->PhaseTimer -= dt;
                    if (run->PhaseTimer <= 0) DadsGame.FinishCollection(f);
                    return;
                case DayPhase.Won:
                case DayPhase.Repo:
                    run->PhaseTimer -= dt;
                    if (run->PhaseTimer <= 0) DadsGame.StartRun(f);
                    return;
            }
            Fixtures(f, settings, dt);
        }

        static void SetPhase(Frame f, DadsRun* run, DayPhase phase)
        {
            run->Phase = phase;
            f.Events.DayPhaseChanged(phase, run->Day);
        }

        static void Fixtures(Frame f, DadsSettings settings, FP dt)
        {
            var pressed = false;
            foreach (var pair in f.Unsafe.GetComponentBlockIterator<Fixture>())
            {
                if (pair.Component->Kind == FixtureKind.Plate) pressed |= Pressed(f, pair.Entity, pair.Component);
            }
            foreach (var pair in f.Unsafe.GetComponentBlockIterator<Fixture>())
            {
                var fixture = pair.Component;
                var wasCounting = fixture->Timer > 0;
                fixture->Timer = FPMath.Max(0, fixture->Timer - dt);
                if (fixture->Kind == FixtureKind.Churn && wasCounting && fixture->Timer <= 0 && fixture->Input != DadItem.None)
                {
                    var treat = DadSystem.TreatOf(fixture->Input);
                    var tub = DadSystem.FreeTub(f, treat, settings);
                    fixture->Input = DadItem.None;
                    if (tub == null) continue;
                    tub->Treat = treat;
                    tub->Count = Math.Min(settings.TubCapacity, tub->Count + settings.ScoopsPerBatch);
                    f.Events.Churned(pair.Entity, treat);
                }
                if (fixture->Kind == FixtureKind.Vault && fixture->Open != pressed)
                {
                    fixture->Open = pressed;
                    f.Events.VaultChanged(pair.Entity, pressed);
                }
            }
        }

        // A dad standing on the plate, or anything heavy dropped on it, holds the vault open.
        static bool Pressed(Frame f, EntityRef entity, Fixture* plate)
        {
            var center = f.Unsafe.GetPointer<Transform3D>(entity)->Position;
            var held = false;
            foreach (var pair in f.Unsafe.GetComponentBlockIterator<Dad>())
            {
                var offset = f.Unsafe.GetPointer<Transform3D>(pair.Entity)->Position - center;
                if (pair.Component->Knocked <= 0 && FPMath.Abs(offset.Y) < FP._0_50 && offset.X * offset.X + offset.Z * offset.Z < FP._0_75 * FP._0_75) held = true;
            }
            foreach (var pair in f.Unsafe.GetComponentBlockIterator<Loot>())
            {
                var offset = f.Unsafe.GetPointer<Transform3D>(pair.Entity)->Position - center;
                if (pair.Component->Resting && pair.Component->Item.Kind >= DadItem.MudBucket && offset.X * offset.X + offset.Z * offset.Z < FP._1_10 * FP._1_10) held = true;
            }
            plate->Open = held;
            return held;
        }
    }
}
