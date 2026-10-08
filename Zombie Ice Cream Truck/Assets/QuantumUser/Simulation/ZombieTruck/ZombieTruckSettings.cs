namespace Quantum
{
    using System;
    using Photon.Deterministic;

    [Serializable]
    public struct TruckBox
    {
        public FPVector3 Center;
        public FPVector3 Extents;
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

    [Serializable]
    public struct ZombieStats
    {
        public Int32 Health;
        public FP Speed;
        public FP Damage;
        public FP AttackInterval;
        public Int32 Reward;
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
        public AssetRef<EntityPrototype> ProjectilePrototype;
        public AssetRef<CharacterController3DConfig> SurvivorController;

        public FP WalkSpeed = 4;
        public FP SprintSpeed = 7;
        public FP EyeHeight = FP._1_50;
        public FP InteractRange = FP._1_50;
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
        public FPVector3[] TurretStands;
        public FPVector3[] TurretMuzzles;
        public Placement[] TruckStations;
        public Int32 HopperCapacity = 120;
        public Int32 RoundsPerScoop = 15;

        public ZombieStats[] Zombies;
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

        public FP ChunkLength = 20;
        public Int32 AreaChunks = 30;
        public Int32 ChunksAhead = 10;
        public FP ChunkDespawnBehind = 60;
        public FP CurveChance = FP._0_20;
        public FP WreckChance = FP._0_10;
        public Int32[] StopChunks;
        public Placement[] ChunkContents;
        public ChunkBox[] ChunkColliders;
        public FPVector3 DepotParking;
        public FP DepotParkRadius = 8;
        public FP WipeResetTime = 4;
        public Int32 StartingRounds = 16;
    }
}
