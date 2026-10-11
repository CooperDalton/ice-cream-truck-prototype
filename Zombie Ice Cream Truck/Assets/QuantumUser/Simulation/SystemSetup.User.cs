namespace Quantum
{
    using System.Collections.Generic;

    public static partial class DeterministicSystemSetup
    {
        // The runtime config picks the game mode: the Divorced Dads scene sets DadsSettings, the zombie scene Settings.
        static partial void AddSystemsUser(ICollection<SystemBase> systems, RuntimeConfig gameConfig, SimulationConfig simulationConfig, SystemsConfig systemsConfig)
        {
            if (gameConfig.DadsSettings.IsValid)
            {
                systems.Add(new DadsSetupSystem());
                systems.Add(new DayCycleSystem());
                systems.Add(new DadSystem());
                systems.Add(new VanSystem());
                systems.Add(new NpcSystem());
                systems.Add(new GlobSystem());
                systems.Add(new DadsCheatSystem());
                return;
            }
            systems.Add(new GameSetupSystem());
            systems.Add(new RoadSystem());
            systems.Add(new SurvivorSystem());
            systems.Add(new TruckSystem());
            systems.Add(new ZombieSystem());
            systems.Add(new WeaponSystem());
            systems.Add(new ProjectileSystem());
        }
    }
}
