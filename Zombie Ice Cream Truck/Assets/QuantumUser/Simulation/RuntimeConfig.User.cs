namespace Quantum
{
    public partial class RuntimeConfig
    {
        public AssetRef<ZombieTruckSettings> Settings;
        public AssetRef<DadsSettings> DadsSettings;
        // Divorced Dads: start at Big Dairy's lot instead of moving day (set from the player's saved progress).
        public bool SkipTutorial;
    }
}
