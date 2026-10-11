namespace Quantum
{
    using System.Collections.Generic;

    public static partial class DeterministicSystemSetup
    {
        static partial void AddSystemsUser(ICollection<SystemBase> systems, RuntimeConfig gameConfig, SimulationConfig simulationConfig, SystemsConfig systemsConfig)
        {
            systems.Add(new GameSetupSystem());
            systems.Add(new RoadSystem());
            systems.Add(new SurvivorSystem());
            systems.Add(new TruckSystem());
            systems.Add(new ZombieSystem());
            systems.Add(new WeaponSystem());
            systems.Add(new ProjectileSystem());
            systems.Add(new ShopSystem());
            systems.Add(new TutorialSystem());
        }
    }
}
