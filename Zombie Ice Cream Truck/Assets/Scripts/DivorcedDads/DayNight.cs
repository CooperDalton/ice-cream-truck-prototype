using Quantum;
using UnityEngine;

// The only clock the dads get: the sun crosses the sky with the day clock, the light warms through the afternoon,
// the street lamps come on at dusk and the town goes dark blue at night. Also swaps the ambience and the music:
// Greensleeves at Big Dairy's lot in the morning, birds by day, crickets and the sneaky curfew tune at night.
public class DayNight : MonoBehaviour
{
    [SerializeField] private Light sun;
    [SerializeField] private Camera sky;
    [SerializeField] private Gradient sunColor;
    [SerializeField] private Gradient ambientColor;
    [SerializeField] private Gradient skyColor;
    [SerializeField] private AnimationCurve sunIntensity;
    [SerializeField] private GameObject[] streetLamps;
    [SerializeField] private AudioSource lotMusic;
    [SerializeField] private AudioSource birds;
    [SerializeField] private AudioSource crickets;
    [SerializeField] private AudioSource curfewMusic;
    private bool lampsOn;

    private void Update()
    {
        var game = QuantumRunner.Default?.Game;
        if (game?.Frames.Predicted == null) return;
        var frame = game.Frames.Predicted;
        var run = frame.GetSingleton<DadsRun>();
        var settings = frame.FindAsset(frame.RuntimeConfig.DadsSettings);
        var clock = run.Clock.AsFloat;
        var dt = Time.deltaTime;
        // Morning sun low in the east, noon overhead around a third of the day, set at dusk, moon light at night.
        var sunAngle = Mathf.Lerp(20f, 185f, clock / settings.NightAt.AsFloat);
        sun.transform.rotation = Quaternion.Slerp(sun.transform.rotation, Quaternion.Euler(clock < settings.NightAt.AsFloat ? sunAngle : 50f, -35f, 0), 1 - Mathf.Exp(-2 * dt));
        sun.color = sunColor.Evaluate(clock);
        sun.intensity = sunIntensity.Evaluate(clock);
        RenderSettings.ambientLight = ambientColor.Evaluate(clock);
        RenderSettings.fogColor = skyColor.Evaluate(clock);
        sky.backgroundColor = RenderSettings.fogColor;

        var dark = clock >= settings.DuskAt.AsFloat - 0.03f;
        if (dark != lampsOn)
        {
            lampsOn = dark;
            foreach (var lamp in streetLamps) lamp.SetActive(dark);
        }
        var atLot = run.Phase == DayPhase.Morning || run.Phase == DayPhase.Collection;
        var night = run.Phase == DayPhase.Night;
        Fade(lotMusic, atLot ? 0.45f : 0, dt);
        Fade(birds, run.Phase == DayPhase.Day ? 0.5f : 0, dt);
        Fade(crickets, run.Phase == DayPhase.Dusk || night ? 0.5f : 0, dt);
        Fade(curfewMusic, night ? 0.35f : 0, dt);
    }

    private static void Fade(AudioSource source, float volume, float dt)
    {
        source.volume = Mathf.MoveTowards(source.volume, volume, dt * 0.4f);
        if (source.volume > 0 && !source.isPlaying) source.Play();
        if (source.volume <= 0 && source.isPlaying) source.Stop();
    }
}
