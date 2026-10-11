namespace Quantum
{
    using System;
    using Photon.Deterministic;

    // Everything a dad does with his hands and feet: walking (stepping up into the van), the van's seats, doors and
    // ladder, gathering ingredients, loading cones and guns at the freezer tubs, shoving cones into faces, shooting,
    // throwing, tumbling after being run over, and sitting out an arrest.
    public unsafe class DadSystem : SystemMainThreadFilter<DadSystem.Filter>
    {
        public struct Filter
        {
            public EntityRef Entity;
            public Transform3D* Transform;
            public Dad* Dad;
            public CharacterController3D* Controller;
        }

        public override void Update(Frame f, ref Filter filter)
        {
            var settings = f.FindAsset(f.RuntimeConfig.DadsSettings);
            var dad = filter.Dad;
            var dt = f.DeltaTime;
            var input = f.GetPlayerInput(dad->Player);
            var run = f.Unsafe.GetPointerSingleton<DadsRun>();
            var vanEntity = f.GetSingletonEntityRef<Van>();
            var van = f.Get<Transform3D>(vanEntity);
            dad->Coughing = FPMath.Max(0, dad->Coughing - dt);
            dad->Frozen = FPMath.Max(0, dad->Frozen - dt);
            dad->FireCooldown -= dt;
            dad->Pitch = FPMath.Clamp(input->Pitch, -85, 85);

            if (run->Phase == DayPhase.Collection || run->Phase == DayPhase.Won || run->Phase == DayPhase.Repo)
            {
                filter.Controller->Velocity = FPVector3.Zero;
                return;
            }
            if (dad->Busted > 0)
            {
                dad->Busted -= dt;
                if (dad->Busted <= 0) DadsGame.BoardVan(f, filter.Entity, dad, van, 0);
                return;
            }
            if (dad->Knocked > 0)
            {
                Tumble(f, ref filter, dt);
                return;
            }

            filter.Transform->Rotation = FPQuaternion.Euler(0, input->Yaw + dad->YawOffset, 0);
            if (input->Slot > 0 && input->Slot <= dad->Hotbar.Length) dad->Selected = input->Slot - 1;

            if (dad->Driving || dad->Turret)
            {
                Seated(f, ref filter, input, van, settings);
                return;
            }

            var eye = filter.Transform->Position + FPVector3.Up * settings.EyeHeight;
            var look = filter.Transform->Rotation * FPQuaternion.Euler(dad->Pitch, 0, 0) * FPVector3.Forward;
            var hit = f.Physics3D.Raycast(eye, look, settings.ReachDistance, -1, QueryOptions.HitAll);
            var target = hit.HasValue ? hit.Value.Entity : EntityRef.None;
            dad->LookTarget = target;
            if (input->Interact.WasPressed) Interact(f, ref filter, target, van, settings);
            Drop(f, ref filter, input, eye, look, settings);
            if (input->Fire.WasPressed && target.IsValid && f.Unsafe.TryGetPointer(target, out Fixture* tub) && tub->Kind == FixtureKind.Tub)
            {
                UseTub(f, dad, target, tub, settings);
            }
            else if (input->Fire.IsDown && dad->FireCooldown <= 0 && dad->Coughing <= 0)
            {
                Use(f, ref filter, input, eye, look, settings);
            }

            if (Climb(f, ref filter, input, van, settings)) return;
            var move = new FPVector3(input->Move.X, 0, input->Move.Y);
            if (move.SqrMagnitude > 1) move = move.Normalized;
            var speed = input->Sprint.IsDown ? settings.SprintSpeed : settings.WalkSpeed;
            if (dad->Coughing > 0 || dad->Frozen > 0) speed *= FP._0_50;
            filter.Controller->MaxSpeed = speed;
            if (input->Jump.WasPressed) filter.Controller->Jump(f);
            var direction = filter.Transform->Rotation * move;
            StepUp(f, ref filter, direction, settings);
            filter.Controller->Move(f, filter.Entity, direction);
            // The controller is a ball at the feet: keep the head (and the camera) under ceilings like the van's roof.
            var up = f.Physics3D.Raycast(filter.Transform->Position + FPVector3.Up * FP._0_25, FPVector3.Up, settings.EyeHeight + FP._0_50, -1, QueryOptions.HitSolids);
            if (up.HasValue && filter.Transform->Position.Y > up.Value.Point.Y - settings.EyeHeight - FP._0_20)
            {
                filter.Transform->Position.Y = up.Value.Point.Y - settings.EyeHeight - FP._0_20;
                if (filter.Controller->Velocity.Y > 0) filter.Controller->Velocity.Y = 0;
            }
            var ground = f.Physics3D.Raycast(filter.Transform->Position + FPVector3.Up * FP._0_25, FPVector3.Down, FP._0_75, -1, QueryOptions.HitSolids);
            dad->Standing = ground.HasValue ? ground.Value.Entity : EntityRef.None;
            // Standing on top of anything riding the van is standing on the van.
            if (dad->Standing.IsValid && f.Has<Riding>(dad->Standing)) dad->Standing = f.GetSingletonEntityRef<Van>();
        }

        // Steps straight up onto a ledge right in front (its edge within the controller's reach, so he lands on it rather
        // than beside it) that is no higher than StepHeight and has room above it: how a dad gets up the truck's rear step
        // and in through the open back door, from behind or from the side.
        static void StepUp(Frame f, ref Filter filter, FPVector3 direction, DadsSettings settings)
        {
            if (direction.SqrMagnitude < FP._0_01 || !filter.Controller->Grounded) return;
            var position = filter.Transform->Position;
            var forward = direction.Normalized;
            // Only ledges at least 10 cm above the feet: the ground he stands on is never a step.
            var above = position + forward * FP._0_33 + FPVector3.Up * (settings.StepHeight + FP._0_05);
            var ledge = f.Physics3D.Raycast(above, FPVector3.Down, settings.StepHeight - FP._0_05, -1, QueryOptions.HitSolids | QueryOptions.ComputeDetailedInfo);
            if (!ledge.HasValue || ledge.Value.Normal.Y < FP._0_75) return;
            var rise = ledge.Value.Point.Y - position.Y;
            if (f.Physics3D.Raycast(position + FPVector3.Up * (rise + 1), forward, FP._0_33, -1, QueryOptions.HitSolids).HasValue) return;
            filter.Transform->Position = position + FPVector3.Up * rise;
        }

        // The ladder from the kitchen up through the open roof hatch. Walking into it facing the wall gets a dad on, as does
        // stepping into the hatch from the roof. W climbs toward where he looks (up, or down when looking down), S the other
        // way, jump lets go. Out of the top he steps onto the roof.
        static bool Climb(Frame f, ref Filter filter, Input* input, Transform3D van, DadsSettings settings)
        {
            var dad = filter.Dad;
            var local = van.InverseTransformPoint(filter.Transform->Position);
            var dx = local.X - settings.Ladder.X;
            var dz = local.Z - settings.Ladder.Z;
            if (!dad->Climbing)
            {
                var facing = FPVector3.Dot(filter.Transform->Forward, van.Right) > FP._0_50;
                var below = FPMath.Abs(local.Y - settings.Ladder.Y) < FP._0_50 && dx * dx + dz * dz < FP._0_25 && input->Move.Y > 0 && facing;
                var above = local.Y > settings.RoofHeight - FP._0_25 && FPMath.Abs(dx) < FP._0_33 && FPMath.Abs(dz) < FP._0_33;
                if (!below && !above) return false;
                dad->Climbing = true;
                if (above) local.Y = settings.RoofHeight - FP._0_50;
            }
            var climb = input->Move.Y * (dad->Pitch > 40 ? -1 : 1);
            var y = local.Y + climb * settings.ClimbSpeed * f.DeltaTime;
            filter.Controller->Velocity = FPVector3.Zero;
            dad->Standing = f.GetSingletonEntityRef<Van>();
            if (y >= settings.RoofHeight)
            {
                dad->Climbing = false;
                filter.Transform->Position = van.TransformPoint(settings.HatchTop);
                return true;
            }
            if (input->Jump.WasPressed || y <= settings.Ladder.Y) dad->Climbing = false;
            filter.Transform->Position = van.TransformPoint(new FPVector3(settings.Ladder.X, FPMath.Max(y, settings.Ladder.Y), settings.Ladder.Z));
            return true;
        }

        // Driver: W/S/A/D drive, click honks, right click toggles the jingle. Turret: click fires the soft serve minigun.
        // E leaves either seat.
        static void Seated(Frame f, ref Filter filter, Input* input, Transform3D van, DadsSettings settings)
        {
            var dad = filter.Dad;
            var vanState = f.Unsafe.GetPointerSingleton<Van>();
            if (input->Interact.WasPressed)
            {
                var exit = dad->Driving ? settings.CabStand : settings.HatchTop;
                DadsGame.LeaveSeat(f, dad);
                filter.Transform->Teleport(f, van.TransformPoint(exit));
                return;
            }
            filter.Transform->Position = van.TransformPoint(dad->Driving ? settings.DriverSeat : settings.TurretStand);
            filter.Controller->Velocity = FPVector3.Zero;
            dad->Standing = f.GetSingletonEntityRef<Van>();
            if (dad->Driving)
            {
                if (input->Fire.WasPressed)
                {
                    vanState->Honk = 1;
                    f.Events.Honked(van.Position);
                }
                if (input->Aim.WasPressed)
                {
                    vanState->Jingle = !vanState->Jingle;
                    f.Events.JingleToggled(vanState->Jingle);
                }
                return;
            }
            if (!input->Fire.IsDown || dad->FireCooldown > 0 || vanState->HopperRounds <= 0) return;
            vanState->HopperRounds--;
            dad->FireCooldown = FP._0_10 - FP._0_02;
            var aim = filter.Transform->Rotation * FPQuaternion.Euler(dad->Pitch, 0, 0);
            var spread = FPQuaternion.Euler(f.RNG->Next(-FP._1_50, FP._1_50), f.RNG->Next(-FP._1_50, FP._1_50), 0);
            var direction = aim * spread * FPVector3.Forward;
            var muzzle = van.TransformPoint(settings.TurretMuzzle);
            FireGlob(f, dad->Player, vanState->HopperTreat, muzzle, direction * settings.GlobSpeed * FP._1_25 + van.Forward * vanState->Speed, 1);
            f.Events.GlobFired(dad->Player, DadItem.None, vanState->HopperTreat, muzzle, direction, true);
        }

        static void Interact(Frame f, ref Filter filter, EntityRef target, Transform3D van, DadsSettings settings)
        {
            var dad = filter.Dad;
            if (target.IsValid && f.Unsafe.TryGetPointer(target, out Loot* loot))
            {
                if (!TryAdd(dad, loot->Item)) return;
                f.Events.PickedUp(dad->Player, loot->Item.Kind, f.Unsafe.GetPointer<Transform3D>(target)->Position);
                f.Destroy(target);
                return;
            }
            if (target.IsValid && f.Unsafe.TryGetPointer(target, out Fixture* fixture))
            {
                UseFixture(f, ref filter, target, fixture, settings);
                return;
            }

            // The driver's seat is the one spot on the van used with E alone; doors, the hatch and the ladder are walked through.
            var vanState = f.Unsafe.GetPointerSingleton<Van>();
            var local = van.InverseTransformPoint(filter.Transform->Position);
            if ((local - settings.DriverSeat).SqrMagnitude >= settings.InteractRange * settings.InteractRange) return;
            if (vanState->Driver.IsValid) return;
            dad->Driving = true;
            vanState->Driver = dad->Player;
        }

        static void UseFixture(Frame f, ref Filter filter, EntityRef entity, Fixture* fixture, DadsSettings settings)
        {
            var dad = filter.Dad;
            var run = f.Unsafe.GetPointerSingleton<DadsRun>();
            var vanState = f.Unsafe.GetPointerSingleton<Van>();
            var position = f.Unsafe.GetPointer<Transform3D>(entity)->Position;
            switch (fixture->Kind)
            {
                case FixtureKind.Churn:
                    var slot = IngredientSlot(dad);
                    if (slot < 0 || fixture->Timer > 0) return;
                    var ingredient = dad->Hotbar.GetPointer(slot);
                    if (FreeTub(f, TreatOf(ingredient->Kind), settings) == null) return;
                    fixture->Input = ingredient->Kind;
                    fixture->Timer = settings.ChurnTime;
                    *ingredient = default;
                    f.Events.ChurnStarted(entity, fixture->Input);
                    return;
                case FixtureKind.Tub:
                    UseTub(f, dad, entity, fixture, settings);
                    return;
                case FixtureKind.ConeCounter:
                    var selected = dad->Hotbar.GetPointer(dad->Selected);
                    if (selected->Kind != DadItem.None && !TryAdd(dad, new DadSlot { Kind = DadItem.Cone })) return;
                    if (selected->Kind == DadItem.None) *selected = new DadSlot { Kind = DadItem.Cone };
                    f.Events.ConeTaken(dad->Player);
                    return;
                case FixtureKind.GunRack:
                    var held = dad->Hotbar.GetPointer(dad->Selected);
                    if (IsGun(held->Kind))
                    {
                        for (int i = 0; i < fixture->Slots.Length; i++)
                        {
                            if (fixture->Slots.GetPointer(i)->Kind != DadItem.None) continue;
                            *fixture->Slots.GetPointer(i) = *held;
                            *held = default;
                            return;
                        }
                        return;
                    }
                    for (int i = 0; i < fixture->Slots.Length; i++)
                    {
                        var rackSlot = fixture->Slots.GetPointer(i);
                        if (rackSlot->Kind == DadItem.None || !TryAdd(dad, *rackSlot)) continue;
                        *rackSlot = default;
                        f.Events.PickedUp(dad->Player, dad->Hotbar.GetPointer(dad->Selected)->Kind, position);
                        return;
                    }
                    return;
                case FixtureKind.Hopper:
                    // Pours the fullest tub into the roof minigun.
                    Fixture* fullest = null;
                    foreach (var pair in f.Unsafe.GetComponentBlockIterator<Fixture>())
                    {
                        if (pair.Component->Kind == FixtureKind.Tub && pair.Component->Count > 0 && (fullest == null || pair.Component->Count > fullest->Count)) fullest = pair.Component;
                    }
                    if (fullest == null || !run->Minigun) return;
                    var room = (settings.HopperCapacity - vanState->HopperRounds) / settings.RoundsPerScoop;
                    var poured = Math.Min(room, fullest->Count);
                    if (poured <= 0) return;
                    vanState->HopperRounds += poured * settings.RoundsPerScoop;
                    vanState->HopperTreat = fullest->Treat;
                    fullest->Count -= poured;
                    if (fullest->Count == 0) fullest->Treat = Treat.None;
                    f.Events.Refilled(dad->Player, vanState->HopperTreat);
                    return;
                case FixtureKind.RearDoor:
                    // Shut it is solid; open it still answers to E.
                    fixture->Open = !fixture->Open;
                    f.Unsafe.GetPointer<PhysicsCollider3D>(entity)->IsTrigger = fixture->Open;
                    f.Events.Swung(entity, fixture->Open);
                    return;
                case FixtureKind.Bell:
                    if (vanState->BellCooldown > 0) return;
                    vanState->Bell = 4;
                    vanState->BellCooldown = 15;
                    f.Events.BellRung(position);
                    return;
                case FixtureKind.Turret:
                    foreach (var other in f.Unsafe.GetComponentBlockIterator<Dad>())
                    {
                        if (other.Component->Turret) return;
                    }
                    dad->Turret = true;
                    return;
                case FixtureKind.Shop:
                    DadsGame.Buy(f, fixture, position);
                    return;
                case FixtureKind.TimeClock:
                    var vanPosition = f.Get<Transform3D>(f.GetSingletonEntityRef<Van>()).Position;
                    var parked = (vanPosition - settings.LotPark).SqrMagnitude < settings.LotRadius * settings.LotRadius;
                    var working = run->Phase == DayPhase.Day || run->Phase == DayPhase.Dusk || run->Phase == DayPhase.Night;
                    if (parked && working) DadsGame.Collect(f);
                    return;
                case FixtureKind.MudPuddle:
                    if (!TryAdd(dad, new DadSlot { Kind = DadItem.MudBucket })) return;
                    f.Events.Gathered(dad->Player, DadItem.MudBucket, position, entity);
                    return;
                case FixtureKind.StrawberryPatch:
                    if (fixture->Timer > 0 || !TryAdd(dad, new DadSlot { Kind = DadItem.StrawberryBasket })) return;
                    fixture->Timer = 50;
                    f.Events.Gathered(dad->Player, DadItem.StrawberryBasket, position, entity);
                    return;
                case FixtureKind.CoffeeTable:
                    if (fixture->Timer > 0 || !TryAdd(dad, new DadSlot { Kind = DadItem.IcedCoffee })) return;
                    fixture->Timer = 40;
                    run->Heat += FP._0_50;
                    f.Events.Gathered(dad->Player, DadItem.IcedCoffee, position, entity);
                    f.Events.Theft(position);
                    return;
                case FixtureKind.NutTree:
                    DadsGame.ShakeTree(f, entity, fixture, 1);
                    return;
                case FixtureKind.Vault:
                    if (!fixture->Open || fixture->Timer > 0 || !TryAdd(dad, new DadSlot { Kind = DadItem.GoldLeaf })) return;
                    fixture->Timer = 60;
                    f.Events.Gathered(dad->Player, DadItem.GoldLeaf, position, entity);
                    return;
            }
        }

        // Loads the selected cone with a scoop of this tub, or refills the selected gun from it.
        static void UseTub(Frame f, Dad* dad, EntityRef entity, Fixture* tub, DadsSettings settings)
        {
            var run = f.Unsafe.GetPointerSingleton<DadsRun>();
            var selected = dad->Hotbar.GetPointer(dad->Selected);
            if (tub->Count <= 0) return;
            int cost;
            if (selected->Kind == DadItem.Cone)
            {
                if (selected->Count >= run->ConeSize) return;
                *selected->Scoops.GetPointer(selected->Count) = tub->Treat;
                selected->Count++;
                cost = 1;
                f.Events.ScoopAdded(dad->Player, tub->Treat, selected->Count, entity);
            }
            else if (IsGun(selected->Kind))
            {
                var pistol = selected->Kind == DadItem.ScoopPistol;
                var clip = pistol ? settings.PistolClip : settings.ShotgunClip;
                if (selected->Count >= clip && *selected->Scoops.GetPointer(0) == tub->Treat) return;
                cost = Math.Min(tub->Count, pistol ? settings.PistolRefill : settings.ShotgunRefill);
                selected->Count = clip;
                *selected->Scoops.GetPointer(0) = tub->Treat;
                f.Events.Refilled(dad->Player, tub->Treat);
            }
            else
            {
                return;
            }
            tub->Count -= cost;
            if (tub->Count == 0) tub->Treat = Treat.None;
        }

        // Clicking with a loaded cone shoves its top scoop into the face of whoever is in front: a kid gets a whole
        // scoop (three bites), a fellow dad gets brain freeze. Guns fire scoop globs.
        static void Use(Frame f, ref Filter filter, Input* input, FPVector3 eye, FPVector3 look, DadsSettings settings)
        {
            var dad = filter.Dad;
            var selected = dad->Hotbar.GetPointer(dad->Selected);
            if (selected->Kind == DadItem.Cone)
            {
                if (!input->Fire.WasPressed) return;
                dad->FireCooldown = settings.ShoveCooldown;
                if (selected->Count == 0)
                {
                    f.Events.Shoved(dad->Player, EntityRef.None, eye + look, Treat.None, true);
                    return;
                }
                var treat = *selected->Scoops.GetPointer(selected->Count - 1);
                var minDot = FPMath.Cos(settings.ShoveAngle * FP.Deg2Rad);
                var best = EntityRef.None;
                var bestDistance = settings.ShoveRange;
                var bestPoint = FPVector3.Zero;
                foreach (var pair in f.Unsafe.GetComponentBlockIterator<Npc>())
                {
                    var stats = settings.Npcs[(int)pair.Component->Kind];
                    var face = f.Unsafe.GetPointer<Transform3D>(pair.Entity)->Position + FPVector3.Up * stats.Height * FP._0_75;
                    if (Better(eye, look, face, minDot, ref bestDistance))
                    {
                        best = pair.Entity;
                        bestPoint = face;
                    }
                }
                foreach (var pair in f.Unsafe.GetComponentBlockIterator<Dad>())
                {
                    if (pair.Entity == filter.Entity) continue;
                    var face = f.Unsafe.GetPointer<Transform3D>(pair.Entity)->Position + FPVector3.Up * settings.EyeHeight;
                    if (Better(eye, look, face, minDot, ref bestDistance))
                    {
                        best = pair.Entity;
                        bestPoint = face;
                    }
                }
                if (!best.IsValid)
                {
                    f.Events.Shoved(dad->Player, EntityRef.None, eye + look, treat, true);
                    return;
                }
                selected->Count--;
                *selected->Scoops.GetPointer(selected->Count) = Treat.None;
                f.Events.Shoved(dad->Player, best, bestPoint, treat, false);
                if (f.Unsafe.TryGetPointer(best, out Npc* npc))
                {
                    DadsGame.Feed(f, best, npc, treat, 3, bestPoint, false);
                }
                else
                {
                    var other = f.Unsafe.GetPointer<Dad>(best);
                    other->Frozen = settings.FrozenTime;
                    f.Events.BrainFreeze(other->Player, treat);
                }
                return;
            }
            if (!IsGun(selected->Kind)) return;
            if (selected->Count <= 0) return;
            var pistol = selected->Kind == DadItem.ScoopPistol;
            dad->FireCooldown = pistol ? FP._0_20 + FP._0_02 : FP._0_75 + FP._0_05;
            selected->Count--;
            var loaded = *selected->Scoops.GetPointer(0);
            var carry = dad->Standing == f.GetSingletonEntityRef<Van>() ? f.Get<Transform3D>(dad->Standing).Forward * f.GetSingleton<Van>().Speed : FPVector3.Zero;
            var aim = filter.Transform->Rotation * FPQuaternion.Euler(dad->Pitch, 0, 0);
            var from = eye + look * FP._0_50;
            var pellets = pistol ? 1 : settings.ShotgunPellets;
            for (int i = 0; i < pellets; i++)
            {
                var spread = pistol ? FP._0_50 : 6;
                var direction = aim * FPQuaternion.Euler(f.RNG->Next(-spread, spread), f.RNG->Next(-spread, spread), 0) * FPVector3.Forward;
                FireGlob(f, dad->Player, loaded, from, direction * settings.GlobSpeed + carry, 1);
            }
            f.Events.GlobFired(dad->Player, selected->Kind, loaded, from, look, false);
            if (selected->Count == 0) *selected->Scoops.GetPointer(0) = Treat.None;
        }

        static bool Better(FPVector3 eye, FPVector3 look, FPVector3 face, FP minDot, ref FP bestDistance)
        {
            var offset = face - eye;
            var distance = offset.Magnitude;
            if (distance >= bestDistance || distance < FP._0_10) return false;
            if (FPVector3.Dot(offset / distance, look) < minDot) return false;
            bestDistance = distance;
            return true;
        }

        public static void FireGlob(Frame f, PlayerRef owner, Treat treat, FPVector3 from, FPVector3 velocity, Int32 bites)
        {
            var settings = f.FindAsset(f.RuntimeConfig.DadsSettings);
            var glob = f.Create(settings.GlobPrototype);
            f.Unsafe.GetPointer<Transform3D>(glob)->Teleport(f, from, FPQuaternion.LookRotation(velocity.Normalized));
            f.Add(glob, new Glob { Treat = treat, Velocity = velocity, Owner = owner, Bites = bites });
        }

        // Tap Q to drop, hold to throw harder. A thrown loaded cone flies as one big glob worth all its scoops.
        static void Drop(Frame f, ref Filter filter, Input* input, FPVector3 eye, FPVector3 look, DadsSettings settings)
        {
            var dad = filter.Dad;
            if (input->Drop.IsDown)
            {
                dad->DropHeld += f.DeltaTime;
                return;
            }
            if (!input->Drop.WasReleased) return;
            var held = dad->DropHeld;
            dad->DropHeld = 0;
            var selected = dad->Hotbar.GetPointer(dad->Selected);
            if (selected->Kind == DadItem.None) return;
            var item = *selected;
            *selected = default;
            var thrown = held >= settings.ThrowHoldTime;
            var power = thrown ? FPMath.Lerp(settings.ThrowSpeedMin, settings.ThrowSpeedMax, held - settings.ThrowHoldTime) : FP._1_50;
            var velocity = look * power + FPVector3.Up * (thrown ? 2 : 1);
            if (dad->Standing == f.GetSingletonEntityRef<Van>())
            {
                velocity += f.Get<Transform3D>(dad->Standing).Forward * f.GetSingleton<Van>().Speed;
            }
            var from = eye + look * FP._0_50;
            if (thrown) f.Events.ItemThrown(dad->Player, from);
            if (thrown && item.Kind == DadItem.Cone && item.Count > 0)
            {
                FireGlob(f, dad->Player, *item.Scoops.GetPointer(item.Count - 1), from, velocity, item.Count * 3);
                return;
            }
            DadsGame.SpawnLoot(f, item, from, velocity, false);
        }

        // Ballistic flight after being hit by the van or slammed by the fat kid, then lying there until the timer runs out.
        static void Tumble(Frame f, ref Filter filter, FP dt)
        {
            var dad = filter.Dad;
            var transform = filter.Transform;
            filter.Controller->Velocity = FPVector3.Zero;
            dad->Knocked -= dt;
            if (dad->Fling != FPVector3.Zero)
            {
                dad->Fling += FPVector3.Down * 20 * dt;
                var step = dad->Fling * dt;
                var side = new FPVector3(step.X, 0, step.Z);
                if (side != FPVector3.Zero && f.Physics3D.Raycast(transform->Position + FPVector3.Up * FP._0_50, side.Normalized, side.Magnitude + FP._0_25, -1, QueryOptions.HitStatics).HasValue)
                {
                    dad->Fling = new FPVector3(-dad->Fling.X * FP._0_25, dad->Fling.Y, -dad->Fling.Z * FP._0_25);
                    step = new FPVector3(0, step.Y, 0);
                }
                var ground = f.Physics3D.Raycast(transform->Position + FPVector3.Up * FP._0_25, FPVector3.Down, FP._0_25 - step.Y, -1, QueryOptions.HitStatics);
                if (dad->Fling.Y < 0 && ground.HasValue)
                {
                    transform->Position = ground.Value.Point;
                    dad->Fling = FPVector3.Zero;
                }
                else
                {
                    transform->Position += step;
                }
            }
            if (dad->Knocked > 0) return;
            dad->Knocked = 0;
            dad->Fling = FPVector3.Zero;
            if (transform->Position.Y < 0) transform->Position.Y = 0;
        }

        public static Treat TreatOf(DadItem ingredient)
        {
            switch (ingredient)
            {
                case DadItem.MudBucket: return Treat.Mud;
                case DadItem.StrawberryBasket: return Treat.Strawberry;
                case DadItem.IcedCoffee: return Treat.Coffee;
                case DadItem.NutSack: return Treat.RockyRoad;
                case DadItem.GoldLeaf: return Treat.GoldLeaf;
                default: return Treat.None;
            }
        }

        // The tub a fresh batch of this flavor goes into: one of the same flavor with room, else an empty one.
        public static Fixture* FreeTub(Frame f, Treat treat, DadsSettings settings)
        {
            Fixture* empty = null;
            foreach (var pair in f.Unsafe.GetComponentBlockIterator<Fixture>())
            {
                var tub = pair.Component;
                if (tub->Kind != FixtureKind.Tub) continue;
                if (tub->Treat == treat && tub->Count + settings.ScoopsPerBatch <= settings.TubCapacity) return tub;
                if (tub->Count == 0 && (empty == null || tub->Index < empty->Index)) empty = tub;
            }
            return empty;
        }

        public static bool IsGun(DadItem kind)
        {
            return kind == DadItem.ScoopPistol || kind == DadItem.SundaeShotgun;
        }

        // The selected hotbar slot if it holds an ingredient, else the first one that does, else -1.
        public static int IngredientSlot(Dad* dad)
        {
            if (TreatOf(dad->Hotbar.GetPointer(dad->Selected)->Kind) != Treat.None) return dad->Selected;
            for (int i = 0; i < dad->Hotbar.Length; i++)
            {
                if (TreatOf(dad->Hotbar.GetPointer(i)->Kind) != Treat.None) return i;
            }
            return -1;
        }

        // Into the selected hotbar slot if it is empty, else the first free one.
        public static bool TryAdd(Dad* dad, DadSlot item)
        {
            if (dad->Hotbar.GetPointer(dad->Selected)->Kind == DadItem.None)
            {
                *dad->Hotbar.GetPointer(dad->Selected) = item;
                return true;
            }
            for (int i = 0; i < dad->Hotbar.Length; i++)
            {
                var slot = dad->Hotbar.GetPointer(i);
                if (slot->Kind != DadItem.None) continue;
                *slot = item;
                return true;
            }
            return false;
        }
    }
}
