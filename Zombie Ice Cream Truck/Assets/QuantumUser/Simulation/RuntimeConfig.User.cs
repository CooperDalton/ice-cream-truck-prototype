namespace Quantum
{
    public partial class RuntimeConfig
    {
        public AssetRef<ZombieTruckSettings> Settings;
        // Starts the first run on the road instead of in the tutorial (play-tests that aren't about the tutorial).
        public bool SkipTutorial;
    }
}
