namespace Quantum
{
    using Photon.Deterministic;

    // Creates the van with its kitchen, the town's fixtures (puddles, patches, the lot shop, gates...) and a dad per
    // player, then starts the run.
    public unsafe class DadsSetupSystem : SystemSignalsOnly, ISignalOnPlayerAdded
    {
        public override void OnInit(Frame f)
        {
            var settings = f.FindAsset(f.RuntimeConfig.DadsSettings);
            var vanEntity = f.Create(settings.VanPrototype);
            var shape = Shape3D.CreatePersistentCompound();
            foreach (var box in settings.VanColliders)
            {
                var part = Shape3D.CreateBox(box.Extents, box.Center);
                shape.Compound.AddShape(f, ref part, true);
            }
            f.Add(vanEntity, PhysicsCollider3D.Create(f, shape));
            shape.Compound.FreePersistent(f);
            f.Add(vanEntity, new Van());
            f.Add(vanEntity, new DadsRun());
            var vanTransform = f.Unsafe.GetPointer<Transform3D>(vanEntity);
            vanTransform->Teleport(f, settings.LotPark, FPQuaternion.Euler(0, settings.LotYaw, 0));
            foreach (var placement in settings.VanFixtures)
            {
                if (placement.Kind == FixtureKind.Turret) continue;
                DadsGame.AttachFixture(f, placement, *vanTransform);
            }
            foreach (var placement in settings.TownFixtures)
            {
                DadsGame.CreateFixture(f, placement, placement.Position, FPQuaternion.Euler(0, placement.Yaw, 0));
            }
            DadsGame.StartRun(f, settings.Tutorial && !f.RuntimeConfig.SkipTutorial);
        }

        public void OnPlayerAdded(Frame f, PlayerRef player, bool firstTime)
        {
            var settings = f.FindAsset(f.RuntimeConfig.DadsSettings);
            int index = player;
            var entity = f.Create(settings.DadPrototypes[index % settings.DadPrototypes.Length]);
            var controller = new CharacterController3D();
            controller.Init(f, f.FindAsset(settings.DadController));
            f.Add(entity, controller);
            var dad = new Dad { Player = player };
            DadsGame.GiveLoadout(&dad);
            f.Add(entity, dad);
            if (f.GetSingleton<DadsRun>().Phase == DayPhase.Tutorial)
            {
                // Moving day: everyone starts out in the trailer yard, side by side.
                f.Unsafe.GetPointer<Transform3D>(entity)->Teleport(f, settings.TutorialStart + new FPVector3(index * FP._1_50, 0, 0));
                return;
            }
            var van = f.Get<Transform3D>(f.GetSingletonEntityRef<Van>());
            DadsGame.BoardVan(f, entity, f.Unsafe.GetPointer<Dad>(entity), van, index);
        }
    }
}
