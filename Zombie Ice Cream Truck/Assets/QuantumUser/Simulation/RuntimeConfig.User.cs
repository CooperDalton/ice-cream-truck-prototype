namespace Quantum
{
    public partial class RuntimeConfig
    {
        public AssetRef<DadsSettings> DadsSettings;
        // Starts at Big Dairy's lot instead of moving day (set from the player's saved progress).
        public bool SkipTutorial;
    }
}
