namespace Quantum
{
    using System.Collections.Generic;

    public static partial class DeterministicSystemSetup
    {
        static partial void AddSystemsUser(ICollection<SystemBase> systems, RuntimeConfig gameConfig, SimulationConfig simulationConfig, SystemsConfig systemsConfig)
        {
            systems.Add(new DadsSetupSystem());
            systems.Add(new DayCycleSystem());
            systems.Add(new DadSystem());
            systems.Add(new VanSystem());
            systems.Add(new NpcSystem());
            systems.Add(new GlobSystem());
            systems.Add(new DadsCheatSystem());
        }
    }
}
