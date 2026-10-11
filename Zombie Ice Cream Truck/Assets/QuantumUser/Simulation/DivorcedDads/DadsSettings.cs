namespace Quantum
{
    using System;
    using Photon.Deterministic;

    [Serializable]
    public struct DadsBox
    {
        public FPVector3 Center;
        public FPVector3 Extents;
    }

    // A fixture placed in van-local space (kitchen) or world space (the town). Trigger fixtures can be walked and driven
    // through (puddles, patches, plates); solid ones stop the van.
    [Serializable]
    public struct FixturePlacement
    {
        public FixtureKind Kind;
        public Int32 Index;
        public Upgrade Upgrade;
        public Int32 Price;
        public FPVector3 Position;
        public FP Yaw;
        public FPVector3 Center;
        public FPVector3 HalfSize;
        public bool Trigger;
    }

    // Where kids hang out (yards, porches, playgrounds) and points along the roads cops patrol, by district
    // (0 The Flats, 1 Maple Grove, 2 Hillside Estates).
    [Serializable]
    public struct TownSpot
    {
        public FPVector3 Position;
        public Int32 District;
        // Kid spots: waypoints from the spot out of its fenced block to the sidewalk (planned by the scene builder).
        public FPVector3[] Path;
    }

    [Serializable]
    public struct NpcStats
    {
        public Int32 Hunger;
        public FP WalkSpeed;
        public FP RunSpeed;
        public FP Height;
        public FP Radius;
    }

    public class DadsSettings : AssetObject
    {
        // Prototypes are indexed by the matching enum (NpcKind, FixtureKind, DadItem) and by player for dads.
        // Kids additionally have outfit variants: NpcPrototypes covers NpcKind, KidLooks the plain Kid outfits.
        public AssetRef<EntityPrototype> VanPrototype;
        public AssetRef<EntityPrototype>[] DadPrototypes;
        public AssetRef<EntityPrototype>[] NpcPrototypes;
        public AssetRef<EntityPrototype>[] KidLooks;
        public AssetRef<EntityPrototype>[] FixturePrototypes;
        public AssetRef<EntityPrototype>[] LootPrototypes;
        public AssetRef<EntityPrototype> CashPrototype;
        public AssetRef<EntityPrototype> GlobPrototype;
        public AssetRef<EntityPrototype> GasPrototype;
        public AssetRef<CharacterController3DConfig> DadController;

        public FP WalkSpeed = 4;
        public FP SprintSpeed = FP._6 + FP._0_50;
        public FP EyeHeight = FP._1_50;
        public FP InteractRange = FP._1_50;
        public FP ReachDistance = 3;
        public FP ThrowHoldTime = FP._0_25;
        public FP ThrowSpeedMin = 6;
        public FP ThrowSpeedMax = 15;
        public FP KnockTime = FP._2 + FP._0_25;
        public FP BustedTime = 3;
        public FP FrozenTime = FP._1_25;
        // Ledges a dad steps straight up onto: the truck's rear step, then its floor.
        public FP StepHeight = FP._0_50;
        public FP ClimbSpeed = FP._2 + FP._0_50;

        public FP VanMaxSpeed = 16;
        public FP VanReverseSpeed = 6;
        public FP VanAcceleration = 7;
        public FP VanBraking = 14;
        public FP VanDrag = FP._0_20;
        public FP VanMaxSteer = 32;
        public FP VanWheelbase = FP._3 + FP._0_50;
        public FP CrashBounce = FP._0_25;
        public FP CrashMinSpeed = 3;
        public FP KnockSpeed = FP._3 + FP._0_50;
        public DadsBox[] VanColliders;
        public FPVector3 VanHalfSize;
        public FP RoofHeight = 3;
        public FPVector3 DriverSeat;
        public FPVector3 CabStand;
        // Van-local line the ladder is climbed on (x, z) from the kitchen floor (y) up through the roof hatch.
        public FPVector3 Ladder;
        public FPVector3 HatchTop;
        public FPVector3 RearInside;
        public FPVector3 RearOutside;
        public FPVector3 TurretStand;
        public FPVector3 TurretMuzzle;
        // Van-local ground point outside the serving window where the queue starts; the line grows outward along -X.
        public FPVector3 WindowOutside;
        public FixturePlacement[] VanFixtures;
        public Int32 HopperCapacity = 120;
        public Int32 RoundsPerScoop = 4;

        // Reaches a kid standing anywhere around their queue spot outside the serving window from the kitchen aisle.
        public FP ShoveRange = 4;
        public FP ShoveAngle = 40;
        public FP ShoveCooldown = FP._0_50;
        public Int32 PistolClip = 10;
        public Int32 PistolRefill = 3;
        public Int32 ShotgunClip = 6;
        public Int32 ShotgunRefill = 5;
        public Int32 ShotgunPellets = 6;
        public FP GlobSpeed = 24;
        public FP GlobGravity = 7;
        public FP GlobRadius = FP._0_50;
        public FP SplashRadius = FP._1_50;
        public Int32 TubCapacity = 16;
        public FP ChurnTime = FP._1_50;
        public Int32 ScoopsPerBatch = 8;
        // Dollars per bite, indexed by Treat.
        public Int32[] TreatValues = { 0, 1, 2, 3, 4, 8 };
        public Int32 WantedTip = 3;
        public Int32 RichMultiplier = 3;
        public FP HyperTime = 5;
        public FP CashMagnetRange = 8;
        public FP CashLifetime = 40;

        public NpcStats[] Npcs;
        public Int32 KidCap = 22;
        public FP SpawnInterval = FP._1;
        public FP SpawnMin = 18;
        public FP SpawnMax = 70;
        public FP DespawnRange = 100;
        public FP JingleRadius = 28;
        public FP LoudspeakerRadius = 45;
        public FP HonkRadius = 30;
        public FP BellRadius = 70;
        public FP FatKidHearing = 90;
        public FP QueueSpacing = FP._0_75 + FP._0_10;
        public FP GasRadius = 5;
        public FP GasTime = 8;
        public FP FatKidSlamInterval = 3;
        public Int32 FatKidBite = 6;
        public Int32 FatKidBonus = 40;
        public TownSpot[] KidSpots;
        public TownSpot[] RoadSpots;
        // Walking routes from the sidewalk to the vault's pressure plate and to the vault (for the play-test bot).
        public TownSpot[] PuzzleRoutes;

        public FP CopNotice = 22;
        public FP CopCatch = FP._1_25;
        public Int32 BustFine = 15;
        public Int32 TicketFine = 25;
        public Int32 Bribe = 2;
        public FP CopBreak = 12;
        public FP HeatDecay = FP._0_01;
        public Int32 MaxCops = 6;

        public FixturePlacement[] TownFixtures;
        public FPVector3 LotPark;
        public FP LotYaw;
        public FP LotRadius = 22;
        // Moving day, the tutorial yard south of town: where the truck waits, where the dads start and where their kid
        // walks over from.
        public FPVector3 TutorialPark;
        public FP TutorialYaw;
        public FPVector3 TutorialStart;
        public FPVector3 TutorialKid;

        public FP DayLength = 300;
        public FP DuskAt = FP._0_75 - FP._0_05;
        public FP NightAt = FP._0_75 + FP._0_05 + FP._0_02;
        public Int32[] Dues = { 40, 90, 160, 260, 400 };
        public FP CollectionTime = 7;
        public FP EndTime = 15;
        public Int32 StartingConeSize = 1;
        // Play-test shortcuts: skip the tutorial, start the run on a later day and with cash in hand.
        public bool Tutorial = true;
        public Int32 StartingDay = 1;
        public Int32 StartingMoney;
    }
}
