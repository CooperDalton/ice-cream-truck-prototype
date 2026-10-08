namespace Quantum
{
    using System;
    using Photon.Deterministic;

    // Keeps road chunks generated ahead of the truck, drops the ones far behind, and drives the run phases:
    // reaching the depot, and resetting the run after every survivor is dead.
    public unsafe class RoadSystem : SystemMainThread
    {
        public override void Update(Frame f)
        {
            var settings = f.FindAsset(f.RuntimeConfig.Settings);
            var global = f.Global;
            var truckEntity = f.GetSingletonEntityRef<Truck>();
            var truckPosition = f.Get<Transform3D>(truckEntity).Position;

            if (global->Phase == GamePhase.Wiped)
            {
                global->PhaseTimer -= f.DeltaTime;
                if (global->PhaseTimer <= 0) Run.Start(f, truckEntity);
                return;
            }

            int survivors = 0;
            int alive = 0;
            foreach (var pair in f.Unsafe.GetComponentBlockIterator<Survivor>())
            {
                survivors++;
                if (!pair.Component->Dead) alive++;
            }
            if (survivors > 0 && alive == 0)
            {
                global->Phase = GamePhase.Wiped;
                global->PhaseTimer = settings.WipeResetTime;
                f.Events.PhaseChanged(GamePhase.Wiped, global->Area);
                return;
            }

            var nearest = FP.MaxValue;
            foreach (var pair in f.Unsafe.GetComponentBlockIterator<RoadChunk>())
            {
                var chunkPosition = f.Unsafe.GetPointer<Transform3D>(pair.Entity)->Position;
                var distance = (chunkPosition - truckPosition).SqrMagnitude;
                if (distance < nearest)
                {
                    nearest = distance;
                    global->TruckChunk = pair.Component->Index;
                }
            }
            foreach (var pair in f.Unsafe.GetComponentBlockIterator<RoadChunk>())
            {
                var chunkPosition = f.Unsafe.GetPointer<Transform3D>(pair.Entity)->Position;
                if (pair.Component->Index < global->TruckChunk && (chunkPosition - truckPosition).SqrMagnitude > settings.ChunkDespawnBehind * settings.ChunkDespawnBehind)
                {
                    Run.RemoveChunk(f, pair.Entity, pair.Component->Index);
                }
            }
            var depotDone = global->DepotChunk.IsValid;
            while (global->NextChunk <= global->TruckChunk + settings.ChunksAhead && !depotDone)
            {
                Run.AddChunk(f, settings);
                depotDone = global->DepotChunk.IsValid;
            }

            if (global->Phase == GamePhase.Driving && f.Exists(global->DepotChunk))
            {
                var depot = f.Get<Transform3D>(global->DepotChunk);
                var parking = depot.TransformPoint(settings.DepotParking);
                var speed = FPMath.Abs(f.GetSingleton<Truck>().Speed);
                if ((parking - truckPosition).SqrMagnitude < settings.DepotParkRadius * settings.DepotParkRadius && speed < 1)
                {
                    Run.EnterDepot(f);
                }
            }
        }
    }
}
