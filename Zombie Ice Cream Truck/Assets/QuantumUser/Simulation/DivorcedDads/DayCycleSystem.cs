namespace Quantum
{
    using System;
    using Photon.Deterministic;

    // Moving day's lessons, the day clock (it starts when the van leaves Big Dairy's lot; dusk sends the kids home, night
    // brings the sugar curfew), the collection and end cards, cooling heat, and fixture timers: the churn finishing a
    // batch, patches and tables restocking, and the vault door following its pressure plate.
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
                case DayPhase.Tutorial:
                    Lessons(f, settings, run);
                    break;
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
                    if (run->PhaseTimer <= 0) DadsGame.StartRun(f, false);
                    return;
            }
            Fixtures(f, settings, dt);
        }

        // Moving day. A lesson is ticked off as soon as the world shows it was done, so doing things early counts. The
        // dads' kid walks over once there is ice cream to scoop, and taking the wheel at any point ends the tutorial.
        static void Lessons(Frame f, DadsSettings settings, DadsRun* run)
        {
            foreach (var pair in f.Unsafe.GetComponentBlockIterator<Dad>())
            {
                if (!pair.Component->Driving) continue;
                DadsGame.FinishTutorial(f, pair.Entity);
                return;
            }
            while (run->Lesson < Lesson.Drive && Learned(f, settings, run, run->Lesson))
            {
                var learned = run->Lesson;
                run->Lesson++;
                f.Events.LessonLearned(learned);
            }
            if (run->Lesson >= Lesson.Scoop && run->KidsFed == 0 && f.ComponentCount<Npc>() == 0) NpcSystem.SpawnOwnKid(f, settings);
        }

        static bool Learned(Frame f, DadsSettings settings, DadsRun* run, Lesson lesson)
        {
            var mud = Stocked(f, Treat.Mud);
            var vanEntity = f.GetSingletonEntityRef<Van>();
            var van = f.Get<Transform3D>(vanEntity);
            var carrying = false;
            var inside = false;
            var scooped = false;
            foreach (var pair in f.Unsafe.GetComponentBlockIterator<Dad>())
            {
                var dad = pair.Component;
                for (int i = 0; i < dad->Hotbar.Length; i++) carrying |= dad->Hotbar[i].Kind == DadItem.MudBucket;
                var local = van.InverseTransformPoint(f.Unsafe.GetPointer<Transform3D>(pair.Entity)->Position);
                inside |= dad->Standing == vanEntity && local.Y < settings.RoofHeight - 1;
                for (int i = 0; i < dad->Hotbar.Length; i++) scooped |= dad->Hotbar[i].Kind == DadItem.Cone && dad->Hotbar[i].Count > 0;
            }
            switch (lesson)
            {
                case Lesson.Mud: return mud || carrying;
                case Lesson.Board: return mud || inside;
                case Lesson.Churn: return mud;
                case Lesson.Scoop: return scooped || run->KidsFed > 0;
                case Lesson.Serve: return run->KidsFed > 0;
                case Lesson.Strawberries: return Stocked(f, Treat.Strawberry);
                case Lesson.Nuts: return Stocked(f, Treat.RockyRoad);
                default: return false;
            }
        }

        static bool Stocked(Frame f, Treat treat)
        {
            foreach (var pair in f.Unsafe.GetComponentBlockIterator<Fixture>())
            {
                if (pair.Component->Kind == FixtureKind.Tub && pair.Component->Treat == treat && pair.Component->Count > 0) return true;
            }
            return false;
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
