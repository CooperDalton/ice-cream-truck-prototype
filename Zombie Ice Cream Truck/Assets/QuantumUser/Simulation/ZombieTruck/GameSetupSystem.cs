namespace Quantum
{
    using Photon.Deterministic;

    public unsafe class GameSetupSystem : SystemSignalsOnly, ISignalOnPlayerAdded
    {
        public override void OnInit(Frame f)
        {
            var settings = f.FindAsset(f.RuntimeConfig.Settings);
            var truck = f.Create(settings.TruckPrototype);
            var shape = Shape3D.CreatePersistentCompound();
            foreach (var box in settings.TruckColliders)
            {
                var part = Shape3D.CreateBox(box.Extents, box.Center);
                shape.Compound.AddShape(f, ref part, true);
            }
            f.Add(truck, PhysicsCollider3D.Create(f, shape));
            shape.Compound.FreePersistent(f);
            f.Add(truck, new Truck());
            Run.Start(f, truck);
        }

        public void OnPlayerAdded(Frame f, PlayerRef player, bool firstTime)
        {
            var settings = f.FindAsset(f.RuntimeConfig.Settings);
            int index = player;
            var survivor = f.Create(settings.SurvivorPrototypes[index % settings.SurvivorPrototypes.Length]);
            var truckEntity = f.GetSingletonEntityRef<Truck>();
            var truck = f.Get<Transform3D>(truckEntity);
            var offset = new FPVector3(index % 2 == 0 ? -FP._0_50 : FP._0_50, 0, (index / 2) * FP._0_75);
            f.Unsafe.GetPointer<Transform3D>(survivor)->Teleport(f, truck.TransformPoint(settings.RearInside + offset));
            var controller = new CharacterController3D();
            controller.Init(f, f.FindAsset(settings.SurvivorController));
            f.Add(survivor, controller);
            f.Add(survivor, new PlayerLink { Player = player });
            var state = new Survivor { Standing = truckEntity };
            Inventory.GiveLoadout(&state, settings);
            f.Add(survivor, state);
        }
    }
}
