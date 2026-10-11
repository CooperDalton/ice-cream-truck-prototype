using Quantum;
using UnityEngine;

// Remembers on this machine that the player has been through the tutorial (finished it or skipped it by driving off),
// and on later games asks the simulation to skip it.
public class TutorialProgress : MonoBehaviour
{
    public const string DoneKey = "ZombieTruck.TutorialDone";
    private bool skipSent;
    private bool sawTutorial;

    private void OnEnable()
    {
        QuantumEvent.Subscribe(this, (EventPhaseChanged e) => OnPhase(e));
    }

    private void OnPhase(EventPhaseChanged e)
    {
        if (!sawTutorial || e.Phase != GamePhase.Driving) return;
        PlayerPrefs.SetInt(DoneKey, 1);
        PlayerPrefs.Save();
    }

    private unsafe void Update()
    {
        var game = QuantumRunner.Default?.Game;
        var frame = game?.Frames.Predicted;
        if (frame == null || frame.Global->Phase != GamePhase.Tutorial) return;
        sawTutorial = true;
        if (skipSent || PlayerPrefs.GetInt(DoneKey, 0) == 0 || !game.Session.TryGetLocalPlayer(0, out _)) return;
        skipSent = game.SendCommand(new CommandSkipTutorial()) == Photon.Deterministic.DeterministicCommandSendResult.Success;
    }
}
