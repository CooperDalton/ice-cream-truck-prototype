namespace Quantum
{
    using Photon.Deterministic;

    // Sent by a client whose player has finished the tutorial before (saved on that machine): skips it for the session.
    public class CommandSkipTutorial : DeterministicCommand
    {
        public override void Serialize(BitStream stream)
        {
        }
    }

    // Walks the crew through the basics on the first run: fetch milk and sugar, churn a tub, freeze it, scoop it, fuel
    // the truck, and deal with one zombie. Each step completes as soon as the game state shows it done, by whoever does
    // it; the last step, taking the driver's seat, ends the tutorial (SurvivorSystem calls Run.EndTutorial). A player
    // who has done it before skips it with CommandSkipTutorial.
    public unsafe class TutorialSystem : SystemMainThread
    {
        public override void Update(Frame f)
        {
            var global = f.Global;
            if (global->Phase != GamePhase.Tutorial) return;
            foreach (var pair in f.Unsafe.GetComponentBlockIterator<PlayerLink>())
            {
                if (f.GetPlayerCommand(pair.Component->Player) is not CommandSkipTutorial) continue;
                Run.EndTutorial(f);
                return;
            }
            var settings = f.FindAsset(f.RuntimeConfig.Settings);
            Station churn = default;
            var freezerTubs = 0;
            foreach (var pair in f.Unsafe.GetComponentBlockIterator<Station>())
            {
                if (pair.Component->Kind == StationKind.Churn) churn = *pair.Component;
                if (pair.Component->Kind != StationKind.Freezer) continue;
                for (int i = 0; i < pair.Component->Slots.Length; i++) freezerTubs += pair.Component->Slots.GetPointer(i)->Count > 0 ? 1 : 0;
            }
            var carryingMilk = false;
            var carryingSugar = false;
            var holdingScoops = false;
            foreach (var pair in f.Unsafe.GetComponentBlockIterator<Survivor>())
            {
                for (int i = 0; i < pair.Component->Hotbar.Length; i++)
                {
                    var kind = pair.Component->Hotbar.GetPointer(i)->Kind;
                    carryingMilk |= kind == ItemKind.MilkCrate;
                    carryingSugar |= kind == ItemKind.SugarSack;
                    holdingScoops |= kind == ItemKind.Scoop;
                }
            }

            bool done;
            switch (global->Tutorial)
            {
                case TutorialStep.GrabMilk: done = carryingMilk || churn.Milk > 0; break;
                case TutorialStep.MilkIn: done = churn.Milk > 0; break;
                case TutorialStep.GrabSugar: done = carryingSugar || churn.Sugar > 0; break;
                case TutorialStep.SugarIn: done = churn.Sugar > 0; break;
                // The crate and sack each add two; one turn of the churn uses one of each.
                case TutorialStep.Crank: done = churn.Milk < 2; break;
                // The freezer starts with three tubs; the new one fills the fourth slot.
                case TutorialStep.Freezer: done = freezerTubs == 4; break;
                case TutorialStep.Scoop: done = holdingScoops; break;
                case TutorialStep.Fuel: done = f.GetSingleton<Truck>().Fuel > settings.StartingFuel; break;
                case TutorialStep.Fight: done = global->Kills > 0; break;
                default: done = false; break;
            }
            if (!done) return;
            global->Tutorial++;
            f.Events.TutorialAdvanced(global->Tutorial);
            if (global->Tutorial == TutorialStep.Fight)
            {
                ZombieSystem.Create(f, settings, ZombieKind.Walker, settings.TutorialZombieSpot, FPVector3.Zero, ZombieState.Chasing);
            }
        }
    }
}
