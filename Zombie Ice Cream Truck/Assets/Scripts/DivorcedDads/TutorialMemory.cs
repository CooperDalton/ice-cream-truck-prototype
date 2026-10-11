using Quantum;
using UnityEngine;

// Remembers in PlayerPrefs that this player has been through moving day (finished it or skipped it by taking the wheel),
// and from then on starts local games straight at Big Dairy's lot. Runs before the local runner starts its game.
public class TutorialMemory : MonoBehaviour
{
    public const string PlayedKey = "DivorcedDads.TutorialPlayed";

    [SerializeField] private QuantumRunnerLocalDebug runner;

    private void Awake()
    {
        runner.RuntimeConfig.SkipTutorial = PlayerPrefs.GetInt(PlayedKey, 0) == 1;
    }

    private void OnEnable()
    {
        QuantumEvent.Subscribe(this, (EventLessonLearned e) => OnLesson(e));
    }

    private void OnLesson(EventLessonLearned e)
    {
        if (e.Lesson != Lesson.Drive) return;
        PlayerPrefs.SetInt(PlayedKey, 1);
        PlayerPrefs.Save();
    }
}
