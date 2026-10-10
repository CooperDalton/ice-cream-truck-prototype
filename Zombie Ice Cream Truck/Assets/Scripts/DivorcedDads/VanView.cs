using Quantum;
using UnityEngine;

// The van: spinning and steering wheels, the steering wheel, the churn crank while a batch is churning, the bell
// mallet, the minigun hopper gauge, the bought loudspeaker and roof minigun, the fat kid rocking it, engine sound,
// the music-box jingle (only while it is switched on), exhaust, road dust and headlights after dusk.
public class VanView : QuantumEntityViewComponent
{
    [SerializeField] private Transform body;
    [SerializeField] private Transform[] wheels;
    [SerializeField] private Transform[] steeringPivots;
    [SerializeField] private float wheelRadius = 0.45f;
    [SerializeField] private Transform steeringWheel;
    [SerializeField] private Transform churnCrank;
    [SerializeField] private Transform gaugeNeedle;
    [SerializeField] private Transform bellMallet;
    [SerializeField] private GameObject loudspeaker;
    [SerializeField] private GameObject minigun;
    [SerializeField] private GameObject[] headlights;
    [SerializeField] private AudioSource engineSound;
    [SerializeField] private AudioSource music;
    [SerializeField] private ParticleSystem exhaust;
    [SerializeField] private ParticleSystem[] wheelDust;
    private float spin;
    private float crankAngle;
    private float malletSwing;
    private Quaternion steeringRest;
    private Quaternion crankRest;
    private Quaternion needleRest;
    private Quaternion malletRest;

    public override void OnInitialize()
    {
        steeringRest = steeringWheel.localRotation;
        crankRest = churnCrank.localRotation;
        needleRest = gaugeNeedle.localRotation;
        malletRest = bellMallet.localRotation;
        QuantumEvent.Subscribe(this, (EventBellRung e) => malletSwing = 1);
    }

    public override void OnUpdateView()
    {
        var frame = PredictedFrame;
        var van = GetPredictedQuantumComponent<Van>();
        var run = frame.GetSingleton<DadsRun>();
        var settings = frame.FindAsset(frame.RuntimeConfig.DadsSettings);
        var speed = van.Speed.AsFloat;
        var dt = Time.deltaTime;
        spin += speed / wheelRadius * Mathf.Rad2Deg * dt;
        foreach (var wheel in wheels) wheel.localRotation = Quaternion.Euler(spin, 0, 0);
        foreach (var pivot in steeringPivots) pivot.localRotation = Quaternion.Euler(0, van.Steer.AsFloat, 0);
        steeringWheel.localRotation = steeringRest * Quaternion.Euler(0, van.Steer.AsFloat * 3f, 0);
        gaugeNeedle.localRotation = Quaternion.Slerp(gaugeNeedle.localRotation, needleRest * Quaternion.Euler(0, 0, Mathf.Lerp(60, -60, (float)van.HopperRounds / settings.HopperCapacity)), 1 - Mathf.Exp(-6 * dt));

        foreach (var pair in frame.GetComponentIterator<Fixture>())
        {
            if (pair.Component.Kind == FixtureKind.Churn && pair.Component.Timer > 0) crankAngle += 720 * dt;
        }
        churnCrank.localRotation = crankRest * Quaternion.Euler(crankAngle, 0, 0);
        malletSwing = Mathf.MoveTowards(malletSwing, 0, dt * 3);
        bellMallet.localRotation = malletRest * Quaternion.Euler(0, 0, Mathf.Sin(malletSwing * Mathf.PI * 3) * 70f * malletSwing);
        loudspeaker.SetActive(run.Loudspeaker);
        minigun.SetActive(run.Minigun);
        var dark = run.Clock.AsFloat > settings.DuskAt.AsFloat - 0.05f;
        foreach (var light in headlights) light.SetActive(dark);

        // The fat kid's body slam rocks the van on its springs.
        var shake = van.Shake.AsFloat;
        body.localRotation = Quaternion.Euler(Mathf.Sin(Time.time * 40) * shake * 4, 0, Mathf.Sin(Time.time * 33) * shake * 6);

        var throttle = van.Driver.IsValid ? 1f : 0.3f;
        var pace = Mathf.Abs(speed) / 16f;
        engineSound.pitch = Mathf.Lerp(engineSound.pitch, 0.7f + pace * 1.1f, 1 - Mathf.Exp(-4 * dt));
        engineSound.volume = 0.3f + 0.4f * throttle;
        if (van.Jingle && !music.isPlaying) music.Play();
        if (!van.Jingle && music.isPlaying) music.Pause();
        music.volume = run.Loudspeaker ? 0.8f : 0.5f;
        music.maxDistance = run.Loudspeaker ? 110 : 70;
        SetRate(exhaust, 6 + 30 * pace * throttle);
        foreach (var dust in wheelDust) SetRate(dust, Mathf.Abs(speed) > 4 ? 25 * pace : 0);
    }

    private static void SetRate(ParticleSystem particles, float rate)
    {
        var emission = particles.emission;
        emission.rateOverTime = rate;
    }
}
