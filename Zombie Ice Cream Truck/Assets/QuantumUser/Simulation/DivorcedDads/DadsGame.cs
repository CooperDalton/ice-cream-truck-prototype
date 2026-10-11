namespace Quantum
{
    using System;
    using Photon.Deterministic;

    // Run and day lifecycle (Big Dairy's collections, strikes, winning), the lot shop, fixtures, dropped items and
    // lunch money, knockdowns, and the feeding rules every way of serving ice cream goes through.
    public static unsafe class DadsGame
    {
        public static void StartRun(Frame f, bool tutorial)
        {
            var settings = f.FindAsset(f.RuntimeConfig.DadsSettings);
            var run = f.Unsafe.GetPointerSingleton<DadsRun>();
            *run = default;
            run->Day = settings.StartingDay;
            run->Money = settings.StartingMoney;
            run->ConeSize = settings.StartingConeSize;
            for (int i = settings.StartingDay - 1; i < settings.Dues.Length; i++) run->Debt += settings.Dues[i];
            var van = f.Unsafe.GetPointerSingleton<Van>();
            *van = default;
            foreach (var pair in f.Unsafe.GetComponentBlockIterator<Fixture>())
            {
                var fixture = pair.Component;
                if (fixture->Kind == FixtureKind.Turret)
                {
                    f.Destroy(pair.Entity);
                    continue;
                }
                for (int i = 0; i < fixture->Slots.Length; i++) *fixture->Slots.GetPointer(i) = default;
                if (fixture->Kind != FixtureKind.Tub) continue;
                // Day one starts with a tub of the only ice cream the dads can afford; on moving day they make it themselves.
                var stocked = fixture->Index == 0 && !tutorial;
                fixture->Treat = stocked ? Treat.Mud : Treat.None;
                fixture->Count = stocked ? settings.ScoopsPerBatch : 0;
            }
            foreach (var pair in f.Unsafe.GetComponentBlockIterator<Dad>()) GiveLoadout(pair.Component);
            if (!tutorial)
            {
                StartDay(f);
                return;
            }
            // Moving day: the truck waits outside the trailer and the dads learn the ropes on foot (they are placed in
            // the yard as they join).
            run->Phase = DayPhase.Tutorial;
            run->Due = Math.Min(run->Debt, settings.Dues[run->Day - 1]);
            ParkVan(f, settings.TutorialPark, settings.TutorialYaw);
            f.Events.DayPhaseChanged(DayPhase.Tutorial, run->Day);
        }

        // Taking the wheel on moving day drives the truck to Big Dairy's lot: the first morning starts with that dad still
        // at the wheel. Skipping the lessons still leaves a tub of mud to sell.
        public static void FinishTutorial(Frame f, EntityRef driver)
        {
            var settings = f.FindAsset(f.RuntimeConfig.DadsSettings);
            var stocked = false;
            foreach (var pair in f.Unsafe.GetComponentBlockIterator<Fixture>())
            {
                if (pair.Component->Kind == FixtureKind.Tub && pair.Component->Count > 0) stocked = true;
            }
            foreach (var pair in f.Unsafe.GetComponentBlockIterator<Fixture>())
            {
                if (stocked || pair.Component->Kind != FixtureKind.Tub || pair.Component->Index != 0) continue;
                pair.Component->Treat = Treat.Mud;
                pair.Component->Count = settings.ScoopsPerBatch;
            }
            f.Events.LessonLearned(Lesson.Drive);
            StartDay(f);
            var dad = f.Unsafe.GetPointer<Dad>(driver);
            dad->Driving = true;
            // The truck turned on the way over; so does the driver's view.
            dad->YawOffset += settings.LotYaw - settings.TutorialYaw;
            f.Unsafe.GetPointerSingleton<Van>()->Driver = dad->Player;
        }

        // Morning at Big Dairy's lot: the van parks, everyone climbs in the back, the town resets.
        public static void StartDay(Frame f)
        {
            var settings = f.FindAsset(f.RuntimeConfig.DadsSettings);
            var run = f.Unsafe.GetPointerSingleton<DadsRun>();
            foreach (var pair in f.Unsafe.GetComponentBlockIterator<Npc>()) f.Destroy(pair.Entity);
            foreach (var pair in f.Unsafe.GetComponentBlockIterator<Glob>()) f.Destroy(pair.Entity);
            foreach (var pair in f.Unsafe.GetComponentBlockIterator<Cash>()) f.Destroy(pair.Entity);
            foreach (var pair in f.Unsafe.GetComponentBlockIterator<Gas>()) f.Destroy(pair.Entity);
            foreach (var pair in f.Unsafe.GetComponentBlockIterator<Loot>())
            {
                if (!f.Has<Riding>(pair.Entity)) f.Destroy(pair.Entity);
            }

            run->Phase = DayPhase.Morning;
            run->Clock = 0;
            run->PhaseTimer = 0;
            run->Heat = 0;
            run->KidsFed = 0;
            run->Earned = 0;
            run->SpawnTimer = 2;
            run->CopTimer = 0;
            run->FatKidSpawned = false;
            var scheduled = run->Day <= settings.Dues.Length ? settings.Dues[run->Day - 1] : 0;
            run->Due = Math.Min(run->Debt, scheduled + run->Carry);

            ParkVan(f, settings.LotPark, settings.LotYaw);
            var vanTransform = f.Unsafe.GetPointer<Transform3D>(f.GetSingletonEntityRef<Van>());
            foreach (var pair in f.Unsafe.GetComponentBlockIterator<Fixture>())
            {
                var fixture = pair.Component;
                if (f.Has<Riding>(pair.Entity)) continue;
                fixture->Timer = 0;
                fixture->Count = 0;
                fixture->Open = fixture->Kind == FixtureKind.Gate && run->Permits >= fixture->Index;
                if (fixture->Kind == FixtureKind.Gate) f.Unsafe.GetPointer<PhysicsCollider3D>(pair.Entity)->Enabled = !fixture->Open;
            }

            int index = 0;
            foreach (var pair in f.Unsafe.GetComponentBlockIterator<Dad>())
            {
                BoardVan(f, pair.Entity, pair.Component, *vanTransform, index);
                index++;
            }
            f.Events.DayPhaseChanged(DayPhase.Morning, run->Day);
        }

        // Stops the van with nobody at the wheel and moves it, with everything riding on it, to a parking spot.
        static void ParkVan(Frame f, FPVector3 position, FP yaw)
        {
            var vanEntity = f.GetSingletonEntityRef<Van>();
            var van = f.Unsafe.GetPointer<Van>(vanEntity);
            van->Speed = 0;
            van->Steer = 0;
            van->Driver = PlayerRef.None;
            van->Jingle = false;
            for (int i = 0; i < van->Queue.Length; i++) *van->Queue.GetPointer(i) = EntityRef.None;
            var vanTransform = f.Unsafe.GetPointer<Transform3D>(vanEntity);
            vanTransform->Teleport(f, position, FPQuaternion.Euler(0, yaw, 0));
            foreach (var pair in f.Unsafe.GetComponentBlockIterator<Riding>())
            {
                var transform = f.Unsafe.GetPointer<Transform3D>(pair.Entity);
                transform->Teleport(f, vanTransform->TransformPoint(pair.Component->LocalPosition), vanTransform->Rotation * pair.Component->LocalRotation);
            }
        }

        // Puts a dad back in the kitchen at the back of the van, clearing seats, tumbles and arrests.
        public static void BoardVan(Frame f, EntityRef entity, Dad* dad, Transform3D van, int index)
        {
            var settings = f.FindAsset(f.RuntimeConfig.DadsSettings);
            dad->Driving = false;
            dad->Turret = false;
            dad->Knocked = 0;
            dad->Busted = 0;
            dad->Fling = FPVector3.Zero;
            dad->Standing = f.GetSingletonEntityRef<Van>();
            // Clear of the freezer tubs along the -X wall.
            var offset = new FPVector3(index % 2 == 0 ? FP._0_10 : FP._0_50 + FP._0_10, 0, (index / 2) * FP._0_75);
            f.Unsafe.GetPointer<Transform3D>(entity)->Teleport(f, van.TransformPoint(settings.RearInside + offset));
            f.Unsafe.GetPointer<CharacterController3D>(entity)->Velocity = FPVector3.Zero;
        }

        public static void GiveLoadout(Dad* dad)
        {
            for (int i = 0; i < dad->Hotbar.Length; i++) *dad->Hotbar.GetPointer(i) = default;
            dad->Hotbar.GetPointer(0)->Kind = DadItem.Cone;
            dad->Carried = default;
            dad->Selected = 0;
        }

        // Big Dairy takes today's installment. A short payment is a strike and the rest rolls into tomorrow.
        public static void Collect(Frame f)
        {
            var settings = f.FindAsset(f.RuntimeConfig.DadsSettings);
            var run = f.Unsafe.GetPointerSingleton<DadsRun>();
            var paid = Math.Min(run->Money, run->Due);
            run->Money -= paid;
            run->Debt -= paid;
            run->Paid = paid;
            run->Carry = run->Due - paid;
            if (paid < run->Due) run->Strikes++;
            run->Phase = DayPhase.Collection;
            run->PhaseTimer = settings.CollectionTime;
            var van = f.Unsafe.GetPointerSingleton<Van>();
            van->Jingle = false;
            f.Events.Collected(run->Day, run->Due, paid, run->Strikes, run->Debt);
            f.Events.DayPhaseChanged(DayPhase.Collection, run->Day);
        }

        // After the collection card: the debt is gone (win), the third strike repossesses the van, or the next day starts.
        public static void FinishCollection(Frame f)
        {
            var settings = f.FindAsset(f.RuntimeConfig.DadsSettings);
            var run = f.Unsafe.GetPointerSingleton<DadsRun>();
            if (run->Debt <= 0 || run->Strikes >= 3)
            {
                run->Phase = run->Debt <= 0 ? DayPhase.Won : DayPhase.Repo;
                run->PhaseTimer = settings.EndTime;
                f.Events.DayPhaseChanged(run->Phase, run->Day);
                return;
            }
            run->Day++;
            StartDay(f);
        }

        // Upgrades that are already owned, or not available yet (double waffle before waffle, Hillside before Maple Grove).
        public static bool SoldOut(DadsRun* run, Upgrade upgrade)
        {
            switch (upgrade)
            {
                case Upgrade.ScoopPistol: return run->Pistol;
                case Upgrade.WaffleCone: return run->ConeSize >= 2;
                case Upgrade.DoubleWaffle: return run->ConeSize >= 3 || run->ConeSize < 2;
                case Upgrade.SundaeShotgun: return run->Shotgun;
                case Upgrade.Loudspeaker: return run->Loudspeaker;
                case Upgrade.Minigun: return run->Minigun;
                case Upgrade.MapleGrovePermit: return run->Permits >= 1;
                case Upgrade.HillsidePermit: return run->Permits >= 2 || run->Permits < 1;
                default: return true;
            }
        }

        public static void Buy(Frame f, Fixture* shop, FPVector3 position)
        {
            var settings = f.FindAsset(f.RuntimeConfig.DadsSettings);
            var run = f.Unsafe.GetPointerSingleton<DadsRun>();
            if (SoldOut(run, shop->Upgrade) || run->Money < shop->Price) return;
            run->Money -= shop->Price;
            switch (shop->Upgrade)
            {
                case Upgrade.ScoopPistol:
                    run->Pistol = true;
                    StoreGun(f, Loaded(DadItem.ScoopPistol, settings.PistolClip, Treat.Mud), position);
                    break;
                case Upgrade.SundaeShotgun:
                    run->Shotgun = true;
                    StoreGun(f, Loaded(DadItem.SundaeShotgun, settings.ShotgunClip, Treat.Mud), position);
                    break;
                case Upgrade.WaffleCone: run->ConeSize = 2; break;
                case Upgrade.DoubleWaffle: run->ConeSize = 3; break;
                case Upgrade.Loudspeaker: run->Loudspeaker = true; break;
                case Upgrade.Minigun:
                    run->Minigun = true;
                    var van = f.Get<Transform3D>(f.GetSingletonEntityRef<Van>());
                    foreach (var placement in settings.VanFixtures)
                    {
                        if (placement.Kind == FixtureKind.Turret) AttachFixture(f, placement, van);
                    }
                    break;
                case Upgrade.MapleGrovePermit:
                case Upgrade.HillsidePermit:
                    run->Permits = shop->Upgrade == Upgrade.MapleGrovePermit ? 1 : 2;
                    foreach (var pair in f.Unsafe.GetComponentBlockIterator<Fixture>())
                    {
                        var gate = pair.Component;
                        if (gate->Kind != FixtureKind.Gate || gate->Open || gate->Index > run->Permits) continue;
                        gate->Open = true;
                        f.Unsafe.GetPointer<PhysicsCollider3D>(pair.Entity)->Enabled = false;
                        f.Events.GateOpened(pair.Entity);
                    }
                    break;
            }
            f.Events.Bought(shop->Upgrade, shop->Price, position);
        }

        static DadSlot Loaded(DadItem gun, Int32 rounds, Treat treat)
        {
            var slot = new DadSlot { Kind = gun, Count = rounds };
            *slot.Scoops.GetPointer(0) = treat;
            return slot;
        }

        // New guns go in the van's gun rack, or land at the shop if the rack is full.
        static void StoreGun(Frame f, DadSlot gun, FPVector3 shopPosition)
        {
            foreach (var pair in f.Unsafe.GetComponentBlockIterator<Fixture>())
            {
                if (pair.Component->Kind != FixtureKind.GunRack) continue;
                for (int i = 0; i < pair.Component->Slots.Length; i++)
                {
                    var slot = pair.Component->Slots.GetPointer(i);
                    if (slot->Kind != DadItem.None) continue;
                    *slot = gun;
                    return;
                }
            }
            SpawnLoot(f, gun, shopPosition + FPVector3.Up, FPVector3.Up * 2, false);
        }

        public static EntityRef CreateFixture(Frame f, FixturePlacement placement, FPVector3 position, FPQuaternion rotation)
        {
            var settings = f.FindAsset(f.RuntimeConfig.DadsSettings);
            var entity = f.Create(settings.FixturePrototypes[(int)placement.Kind]);
            f.Unsafe.GetPointer<Transform3D>(entity)->Teleport(f, position, rotation);
            f.Add(entity, new Fixture { Kind = placement.Kind, Index = placement.Index, Upgrade = placement.Upgrade, Price = placement.Price });
            var shape = Shape3D.CreateBox(placement.HalfSize, placement.Center);
            f.Add(entity, PhysicsCollider3D.Create(f, shape, null, placement.Trigger));
            return entity;
        }

        public static EntityRef AttachFixture(Frame f, FixturePlacement placement, Transform3D van)
        {
            var local = FPQuaternion.Euler(0, placement.Yaw, 0);
            var entity = CreateFixture(f, placement, van.TransformPoint(placement.Position), van.Rotation * local);
            f.Add(entity, new Riding { LocalPosition = placement.Position, LocalRotation = local });
            return entity;
        }

        public static EntityRef SpawnLoot(Frame f, DadSlot item, FPVector3 position, FPVector3 velocity, bool resting)
        {
            var settings = f.FindAsset(f.RuntimeConfig.DadsSettings);
            var entity = f.Create(settings.LootPrototypes[(int)item.Kind]);
            f.Unsafe.GetPointer<Transform3D>(entity)->Teleport(f, position);
            f.Add(entity, new Loot { Item = item, Velocity = velocity, Resting = resting });
            var shape = Shape3D.CreateBox(new FPVector3(FP._0_25, FP._0_25, FP._0_25), new FPVector3(0, FP._0_25, 0));
            f.Add(entity, PhysicsCollider3D.Create(f, shape, null, true));
            return entity;
        }

        // Lunch money bursts out as a handful of bills and coins that fly to the nearest dad.
        public static void SpawnCash(Frame f, Int32 amount, FPVector3 position)
        {
            var settings = f.FindAsset(f.RuntimeConfig.DadsSettings);
            var pieces = Math.Min(amount, 5);
            for (int i = 0; i < pieces; i++)
            {
                var entity = f.Create(settings.CashPrototype);
                var angle = f.RNG->Next(0, 360);
                var outward = FPQuaternion.Euler(0, angle, 0) * FPVector3.Forward * f.RNG->Next(FP._1, FP._3);
                f.Unsafe.GetPointer<Transform3D>(entity)->Teleport(f, position);
                var share = amount / pieces + (i == 0 ? amount % pieces : 0);
                f.Add(entity, new Cash { Amount = share, Velocity = outward + FPVector3.Up * f.RNG->Next(4, 7) });
            }
        }

        // Shaking by hand counts one hit, a glob one, ramming it with the van five. Every fifth hit drops two sacks of
        // nuts from the canopy; then the tree is bare for a while.
        public static void ShakeTree(Frame f, EntityRef entity, Fixture* tree, Int32 hits)
        {
            if (tree->Timer > 0)
            {
                f.Events.TreeShaken(entity, 0);
                return;
            }
            tree->Count += hits;
            if (tree->Count < 5)
            {
                f.Events.TreeShaken(entity, 0);
                return;
            }
            tree->Count = 0;
            tree->Timer = 40;
            var transform = f.Get<Transform3D>(entity);
            for (int i = 0; i < 2; i++)
            {
                var drop = transform.TransformPoint(new FPVector3(i == 0 ? -2 : 2, 4, f.RNG->Next(-FP._1, FP._1)));
                SpawnLoot(f, new DadSlot { Kind = DadItem.NutSack }, drop, new FPVector3(f.RNG->Next(-FP._1, FP._1), 0, f.RNG->Next(-FP._1, FP._1)), false);
            }
            f.Events.TreeShaken(entity, 2);
        }

        public static void LeaveQueue(Frame f, EntityRef npc)
        {
            var van = f.Unsafe.GetPointerSingleton<Van>();
            for (int i = 0; i < van->Queue.Length; i++)
            {
                if (*van->Queue.GetPointer(i) == npc) *van->Queue.GetPointer(i) = EntityRef.None;
            }
            f.Unsafe.GetPointer<Npc>(npc)->QueueSlot = -1;
        }

        public static void KnockNpc(Frame f, EntityRef entity, Npc* npc, FPVector3 velocity)
        {
            if (npc->Kind == NpcKind.FatKid) return;
            LeaveQueue(f, entity);
            npc->State = NpcState.Tumble;
            npc->Velocity = velocity;
            npc->Timer = 2;
            var position = f.Unsafe.GetPointer<Transform3D>(entity)->Position;
            f.Events.NpcKnocked(entity, npc->Kind, position, velocity.Magnitude, npc->Fed >= npc->Hunger);
        }

        // Sends a dad tumbling: he lets go of the wheel or turret and drops whatever he was carrying.
        public static void KnockDad(Frame f, EntityRef entity, Dad* dad, FPVector3 fling)
        {
            var settings = f.FindAsset(f.RuntimeConfig.DadsSettings);
            if (dad->Knocked > 0) return;
            LeaveSeat(f, dad);
            dad->Knocked = settings.KnockTime;
            dad->Fling = fling;
            dad->Standing = EntityRef.None;
            var position = f.Unsafe.GetPointer<Transform3D>(entity)->Position;
            if (dad->Carried.Kind != DadItem.None)
            {
                SpawnLoot(f, dad->Carried, position + FPVector3.Up, fling * FP._0_50, false);
                dad->Carried = default;
            }
            f.Events.DadKnocked(dad->Player, position);
        }

        public static void LeaveSeat(Frame f, Dad* dad)
        {
            if (dad->Driving) f.Unsafe.GetPointerSingleton<Van>()->Driver = PlayerRef.None;
            dad->Driving = false;
            dad->Turret = false;
        }

        // The single feeding rule for shoves, scoops, splashes and turret fire. Cops take a bribe and go on break; rich
        // kids spit out mud; diabetic kids get the cops called; lactose kids eat the dairy and then let rip. Strawberry
        // splashes onto neighbours, rocky road counts double and its last bite bowls kids over, coffee makes them hyper.
        public static void Feed(Frame f, EntityRef entity, Npc* npc, Treat treat, Int32 bites, FPVector3 point, bool splash)
        {
            var settings = f.FindAsset(f.RuntimeConfig.DadsSettings);
            var run = f.Unsafe.GetPointerSingleton<DadsRun>();
            var position = f.Unsafe.GetPointer<Transform3D>(entity)->Position;
            if (npc->Fed >= npc->Hunger) return;
            if (npc->Kind == NpcKind.Cop)
            {
                if (npc->State == NpcState.Break) return;
                npc->State = NpcState.Break;
                npc->Timer = settings.CopBreak;
                run->Heat = FPMath.Max(0, run->Heat - FP._0_25);
                SpawnCash(f, settings.Bribe, position + FPVector3.Up * FP._1_50);
                f.Events.CopBribed(entity, settings.Bribe, position);
                return;
            }
            if (npc->Kind == NpcKind.RichKid && treat == Treat.Mud)
            {
                LeaveQueue(f, entity);
                npc->State = NpcState.Flee;
                npc->Goal = point;
                npc->Timer = 3;
                f.Events.KidRefused(entity, position);
                return;
            }
            if (npc->Kind == NpcKind.DiabeticKid && !npc->Alerted)
            {
                npc->Alerted = true;
                run->Heat += FP._1_50;
                f.Events.SugarAlert(entity, position);
            }
            if (npc->Kind == NpcKind.LactoseKid && treat != Treat.Mud && npc->Gassy <= 0)
            {
                npc->Gassy = FP._1_50;
                f.Events.UhOh(entity, position);
            }

            var multiplier = npc->Kind == NpcKind.RichKid ? settings.RichMultiplier : npc->Kind == NpcKind.LactoseKid && treat == Treat.Mud ? 2 : 1;
            npc->Fed += treat == Treat.RockyRoad ? bites * 2 : bites;
            npc->Tab += settings.TreatValues[(int)treat] * bites * multiplier;
            var wanted = treat == npc->Wants;
            npc->GotWanted |= wanted;
            f.Events.KidFed(entity, npc->Kind, treat, wanted, position);

            if (treat == Treat.Strawberry && !splash)
            {
                foreach (var other in f.Unsafe.GetComponentBlockIterator<Npc>())
                {
                    if (other.Entity == entity || other.Component->Kind == NpcKind.Cop) continue;
                    var otherPosition = f.Unsafe.GetPointer<Transform3D>(other.Entity)->Position;
                    if ((otherPosition - position).SqrMagnitude > settings.SplashRadius * settings.SplashRadius) continue;
                    Feed(f, other.Entity, other.Component, Treat.Strawberry, 1, otherPosition + FPVector3.Up, true);
                }
            }
            if (npc->Fed < npc->Hunger) return;
            Pay(f, entity, npc, treat, position);
            // The last bite of rocky road is so heavy it bowls the kid over (they get up happy).
            if (treat != Treat.RockyRoad || npc->Kind == NpcKind.FatKid) return;
            var push = position - point;
            push.Y = 0;
            KnockNpc(f, entity, npc, push.Normalized * 3 + FPVector3.Up * 4);
        }

        static void Pay(Frame f, EntityRef entity, Npc* npc, Treat last, FPVector3 position)
        {
            var settings = f.FindAsset(f.RuntimeConfig.DadsSettings);
            var run = f.Unsafe.GetPointerSingleton<DadsRun>();
            var tip = npc->GotWanted ? settings.WantedTip * (npc->Kind == NpcKind.RichKid ? settings.RichMultiplier : 1) : 0;
            var amount = npc->Tab + tip + (npc->Kind == NpcKind.FatKid ? settings.FatKidBonus : 0);
            if (last == Treat.Coffee) amount += amount / 2;
            LeaveQueue(f, entity);
            npc->State = last == Treat.Coffee ? NpcState.Hyper : NpcState.Happy;
            npc->Timer = last == Treat.Coffee ? settings.HyperTime : 6;
            SpawnCash(f, amount, position + FPVector3.Up * (npc->Kind == NpcKind.FatKid ? 2 : 1));
            run->KidsFed++;
            run->Earned += amount;
            f.Events.KidPaid(entity, npc->Kind, amount, tip > 0, position);
            if (npc->Kind != NpcKind.FatKid) return;
            // The fat kid's burp bowls over everyone around him.
            foreach (var other in f.Unsafe.GetComponentBlockIterator<Npc>())
            {
                if (other.Entity == entity) continue;
                var offset = f.Unsafe.GetPointer<Transform3D>(other.Entity)->Position - position;
                if (offset.SqrMagnitude > 36) continue;
                offset.Y = 0;
                KnockNpc(f, other.Entity, other.Component, offset.Normalized * 6 + FPVector3.Up * 4);
            }
        }
    }
}
