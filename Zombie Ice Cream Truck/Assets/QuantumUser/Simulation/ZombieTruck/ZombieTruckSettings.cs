namespace Quantum
{
    using System;
    using Photon.Deterministic;

    // Pitch tilts the box about the truck's X axis (the ramp up to the rear door).
    [Serializable]
    public struct TruckBox
    {
        public FPVector3 Center;
        public FPVector3 Extents;
        public FP Pitch;
    }

    // A station or pickup placed in the local space of the truck or of a road chunk.
    [Serializable]
    public struct Placement
    {
        public ChunkKind Chunk;
        public bool IsStation;
        public StationKind Station;
        public ItemKind Item;
        public Flavor Flavor;
        public Int32 Count;
        public UpgradeKind Upgrade;
        public Int32 Price;
        public FPVector3 Position;
        public FP Yaw;
        public FPVector3 Center;
        public FPVector3 HalfSize;
    }

    // Solid footprint of a road chunk's buildings and props, in chunk-local space (generated from the art).
    [Serializable]
    public struct ChunkBox
    {
        public ChunkKind Chunk;
        public FPVector3 Center;
        public FPVector3 Extents;
    }

    // Solid footprint of a scenery block's buildings and props, in block-local space (generated from the art).
    [Serializable]
    public struct SceneryBox
    {
        public Int32 Block;
        public FPVector3 Center;
        public FPVector3 Extents;
    }

    // A spot in a road chunk's local space, such as a hot spot's horde exits.
    [Serializable]
    public struct ChunkPoint
    {
        public ChunkKind Chunk;
        public FPVector3 Position;
    }

    // How a hot spot's horde is made up: its size and the share of sprinters and bloaters in it and in the stream that
    // follows while the truck is near.
    [Serializable]
    public struct HotSpotStats
    {
        public ChunkKind Chunk;
        public Int32 Horde;
        public FP SprinterChance;
        public FP BloaterChance;
    }

    // One entry of the hot spot loot table (Item itself isn't serializable in an asset).
    [Serializable]
    public struct Loot
    {
        public ItemKind Kind;
        public Flavor Flavor;
        public Int32 Count;
    }

    [Serializable]
    public struct ZombieStats
    {
        public Int32 Health;
        public FP Speed;
        public FP Damage;
        public FP AttackInterval;
        public Int32 Reward;
        // How close a survivor on foot gets before an idle zombie of this kind notices.
        public FP NoticeRange;
        public FP HeadHeight;
        public FPVector3 HalfSize;
    }

    public class ZombieTruckSettings : AssetObject
    {
        // Prototypes are indexed by the matching enum (ZombieKind, ItemKind, StationKind, ChunkKind) and by player for survivors.
        public AssetRef<EntityPrototype> TruckPrototype;
        public AssetRef<EntityPrototype>[] SurvivorPrototypes;
        public AssetRef<EntityPrototype>[] ZombiePrototypes;
        public AssetRef<EntityPrototype>[] ItemPrototypes;
        public AssetRef<EntityPrototype>[] StationPrototypes;
        public AssetRef<EntityPrototype>[] ChunkPrototypes;
        public AssetRef<EntityPrototype>[] SceneryPrototypes;
        public AssetRef<EntityPrototype> ProjectilePrototype;
        public AssetRef<CharacterController3DConfig> SurvivorController;

        public FP WalkSpeed = 4;
        public FP SprintSpeed = 7;
        public FP CrouchSpeed = 2;
        public FP EyeHeight = FP._1_50;
        public FP CrouchEyeHeight = FP._0_75 + FP._0_20;
        public FP InteractRange = FP._1_50;
        // The ladder is grabbed only from right in front of it, so E by the rear door works the door.
        public FP LadderRange = FP._0_75;
        public FP ReachDistance = 3;
        public FP MaxHealth = 100;
        public FP ThrowHoldTime = FP._0_25;
        public FP ThrowSpeedMin = 6;
        public FP ThrowSpeedMax = 15;
        public FP GestureRate = FP._0_01;

        public FP TruckMaxSpeed = 20;
        public FP EngineBonusSpeed = 6;
        public FP TruckReverseSpeed = 6;
        public FP TruckAcceleration = 6;
        public FP TruckBraking = 14;
        public FP TruckDrag = FP._0_20;
        public FP TruckMaxSteer = 30;
        public FP TruckWheelbase = FP._3 + FP._0_50;
        public FP RunOverSpeed = 6;
        public FP RunOverSlowdown = FP._0_50;
        public FP CrowdSlowdown = 3;
        public FP BloaterSlowdown = FP._0_75;
        public FP ClimbMaxSpeed = 12;
        // How long a sprinter takes to climb from the road onto the truck roof.
        public FP ZombieClimbTime = FP._1_25;
        public FP CrashBounce = FP._0_25;
        public FP CrashMinSpeed = 3;
        public TruckBox[] TruckColliders;
        public FPVector3 TruckHalfSize;
        public FP RoofHeight = 3;
        public FPVector3 DriverSeat;
        public FPVector3 CabStand;
        public FPVector3 LadderBottom;
        public FPVector3 HatchTop;
        public FPVector3 RearInside;
        public FPVector3 RearOutside;
        // The ladder: the column the climber's feet travel up (from the floor), the highest the feet get while the hatch
        // is shut, and where a climber steps off onto the roof.
        public FPVector3 LadderClimb;
        public FP LadderClosedTop;
        public FPVector3 HatchExit;
        public FP ClimbSpeed = 2;
        // How far the rear door swings out about its hinge, and the hatch lid up about its own.
        public FP DoorOpenYaw = -95;
        public FP HatchOpenPitch = -112;
        public FPVector3[] TurretStands;
        public FPVector3[] TurretMuzzles;
        public Placement[] TruckStations;
        public Int32 HopperCapacity = 120;
        public Int32 RoundsPerScoop = 15;

        // Fuel is counted in scoops of ice cream.
        public FP FuelCapacity = 24;
        public FP BigTankBonus = 16;
        public FP StartingFuel = 12;
        public FP MetersPerScoop = 40;
        public FP CoffeeFuelBonusSpeed = 5;

        public ZombieStats[] Zombies;
        // Idle zombies shuffle at this share of their speed. The truck's music box carries TruckNoticeRange; noises wake
        // idle zombies within their range.
        public FP IdleSpeed = FP._0_33;
        public FP TruckNoticeRange = 22;
        public FP EngineNoticeRange = 10;
        public FP GunshotNoise = 28;
        public FP ExplosionNoise = 40;
        public FP CrashNoise = 30;
        public FP SpawnInterval = FP._0_75;
        public FP SpawnIntervalPerArea = FP._0_10;
        public FP SprinterChance = FP._0_20;
        public FP BloaterChance = FP._0_05;
        public FP ChancePerArea = FP._0_10;
        public Int32 MaxZombies = 45;
        public FP SpawnHalfWidth = 9;
        public FP DespawnBehind = 50;
        public FP CorpseTime = 4;
        public FP FreezeTime = 3;
        public FP SplashRadius = FP._1_50;
        public FP GrenadeRadius = FP._2 + FP._0_50;
        public FP BloaterRadius = FP._3 + FP._0_50;
        public FP BloaterPlayerDamage = 30;
        public Int32 ChocolateTip = 2;
        public Int32 RockyRoadBonus = 2;
        public FP BazookaRadius = FP._4 + FP._0_50;
        public FP JackpotRadius = 5;
        public FP JackpotChance = FP._0_10 + FP._0_05;
        public FP JackpotSpreadChance = FP._0_33;

        public FP ChunkLength = 20;
        public Int32 AreaChunks = 30;
        public Int32 ChunksAhead = 10;
        public FP ChunkDespawnBehind = 60;
        public FP CurveChance = FP._0_20;
        public FP WreckChance = FP._0_10;
        public Int32[] StopChunks;
        public Int32[] HotSpotChunks;
        public HotSpotStats[] HotSpots;
        public ChunkPoint[] HordeExits;
        public FP HotSpotRange = 45;
        public FP HotSpotSpawnInterval = FP._0_25;
        public Int32 HotSpotMaxZombies = 70;
        // Random loot for pickups placed without an item (hot spot loot spots); repeats weight the odds.
        public Loot[] HotSpotLoot;
        // Weapons the depot pedestals roll their stock from.
        public ItemKind[] ShopWeapons;
        public FP SlotSpinTime = 2;
        public FP SlotJackpotChance = FP._0_10 - FP._0_02;
        public FP SlotPairChance = FP._0_25 + FP._0_10 + FP._0_05;
        public FP SlotBrainsChance = FP._0_05 + FP._0_02;
        public Int32 SlotJackpotCash = 50;
        public Placement[] ChunkContents;
        public ChunkBox[] ChunkColliders;

        // Scenery blocks fill the empty grid cells within SceneryRings of the road. Town and rural lists index
        // SceneryPrototypes (repeats weight the pick); the side street faces a T junction.
        public FP CellSize = 20;
        public Int32 SceneryRings = 2;
        public Int32[] TownBlocks;
        public Int32[] RuralBlocks;
        public Int32 SideStreetBlock;
        public SceneryBox[] SceneryColliders;
        public FPVector3 DepotParking;
        public FP DepotParkRadius = 8;
        public FP WipeResetTime = 4;

        // Tutorial props behind the parked truck (world space; the truck starts at the origin facing +Z).
        public FPVector3 TutorialMilkSpot = new FPVector3(-2, 0, -7);
        public FPVector3 TutorialSugarSpot = new FPVector3(2, 0, -8);
        public FPVector3 TutorialZombieSpot = new FPVector3(0, 0, -16);
        public Int32 StartingRounds = 16;
    }
}
