namespace Quantum
{
    public partial class RuntimeConfig
    {
        public AssetRef<ZombieTruckSettings> Settings;
        public AssetRef<DadsSettings> DadsSettings;
        // Zombie mode: starts the first run on the road instead of in the tutorial (play-tests that aren't about the
        // tutorial). Divorced Dads: starts at Big Dairy's lot instead of moving day (set from the player's saved progress).
        public bool SkipTutorial;
    }
}
