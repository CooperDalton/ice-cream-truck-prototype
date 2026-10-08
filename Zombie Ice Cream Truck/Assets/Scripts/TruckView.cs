using Quantum;
using UnityEngine;

// Truck presentation: spins and steers the wheels, turns the steering wheel, cranks the churn while someone works it,
// moves the hopper gauge, swings the bell mallet, shows the parts for every bought upgrade, and runs the engine sound,
// the music-box jingle, exhaust, road dust and the bloody tire tracks left after running zombies over.
public class TruckView : QuantumEntityViewComponent
{
    [SerializeField] private Transform[] wheels;
    [SerializeField] private Transform[] steeringPivots;
    [SerializeField] private float wheelRadius = 0.45f;
    [SerializeField] private Transform steeringWheel;
    [SerializeField] private Transform churnCrank;
    [SerializeField] private Transform gaugeNeedle;
    [SerializeField] private Transform bellMallet;
    [SerializeField] private GameObject basePlow;
    [SerializeField] private GameObject[] plowLevels;
    [SerializeField] private GameObject spikes;
    [SerializeField] private GameObject armor;
    [SerializeField] private GameObject engine;
    [SerializeField] private GameObject bigHopper;
    [SerializeField] private GameObject[] turretMounts;
    [SerializeField] private AudioSource engineSound;
    [SerializeField] private AudioSource music;
    [SerializeField] private ParticleSystem exhaust;
    [SerializeField] private ParticleSystem[] engineStacks;
    [SerializeField] private ParticleSystem[] wheelDust;
    [SerializeField] private ParticleSystem[] bloodTrails;
    [SerializeField] private float bloodyTime = 3f;
    private float spin;
    private float crankAngle;
    private float malletSwing;
    private float bloody;
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
    }

    public override void OnActivate(Frame frame)
    {
        QuantumEvent.Subscribe(this, (EventZombieKilled e) => OnKilled(e));
        QuantumEvent.Subscribe(this, (EventStationUsed e) => OnStationUsed(e));
    }

    private void OnKilled(EventZombieKilled e)
    {
        if (e.RunOver) bloody = bloodyTime;
    }

    private void OnStationUsed(EventStationUsed e)
    {
        if (e.Kind == StationKind.Bell) malletSwing = 1;
    }

    public override void OnUpdateView()
    {
        var frame = PredictedFrame;
        var truck = GetPredictedQuantumComponent<Truck>();
        var speed = truck.Speed.AsFloat;
        var dt = Time.deltaTime;
        spin += speed / wheelRadius * Mathf.Rad2Deg * dt;
        foreach (var wheel in wheels) wheel.localRotation = Quaternion.Euler(spin, 0, 0);
        foreach (var pivot in steeringPivots) pivot.localRotation = Quaternion.Euler(0, truck.Steer.AsFloat, 0);
        steeringWheel.localRotation = steeringRest * Quaternion.Euler(0, truck.Steer.AsFloat * 3f, 0);
        var settings = frame.FindAsset(frame.RuntimeConfig.Settings);
        var capacity = settings.HopperCapacity * (truck.BigHopper ? 2 : 1);
        gaugeNeedle.localRotation = Quaternion.Slerp(gaugeNeedle.localRotation, needleRest * Quaternion.Euler(0, 0, Mathf.Lerp(60, -60, (float)truck.HopperRounds / capacity)), 1 - Mathf.Exp(-6 * dt));

        // The crank turns while anyone is working the churn.
        foreach (var pair in frame.GetComponentIterator<Survivor>())
        {
            var target = pair.Component.WorkTarget;
            if (target.IsValid && frame.TryGet(target, out Station station) && station.Kind == StationKind.Churn) crankAngle += 540 * dt;
        }
        churnCrank.localRotation = crankRest * Quaternion.Euler(crankAngle, 0, 0);
        malletSwing = Mathf.MoveTowards(malletSwing, 0, dt * 3);
        bellMallet.localRotation = malletRest * Quaternion.Euler(0, 0, Mathf.Sin(malletSwing * Mathf.PI) * 70f);

        basePlow.SetActive(truck.PlowLevel == 0);
        for (int i = 0; i < plowLevels.Length; i++) plowLevels[i].SetActive(truck.PlowLevel == i + 1);
        spikes.SetActive(truck.Spikes);
        armor.SetActive(truck.Armor);
        engine.SetActive(truck.Engine);
        bigHopper.SetActive(truck.BigHopper);
        turretMounts[0].SetActive(truck.Turret);
        turretMounts[1].SetActive(truck.SecondTurret);

        var throttle = truck.Driver.IsValid ? 1f : 0.3f;
        var pace = Mathf.Abs(speed) / 20f;
        engineSound.pitch = Mathf.Lerp(engineSound.pitch, 0.7f + pace * 1.1f + (truck.Engine ? 0.15f : 0), 1 - Mathf.Exp(-4 * dt));
        engineSound.volume = 0.35f + 0.4f * throttle;
        if (!music.isPlaying) music.Play();
        SetRate(exhaust, 6 + 30 * pace * throttle);
        foreach (var stack in engineStacks) SetRate(stack, truck.Engine ? 10 + 40 * pace : 0);
        foreach (var dust in wheelDust) SetRate(dust, Mathf.Abs(speed) > 4 ? 25 * pace : 0);
        bloody = Mathf.Max(0, bloody - dt);
        foreach (var trail in bloodTrails) SetRate(trail, bloody > 0 && Mathf.Abs(speed) > 1 ? 30 : 0);
    }

    private static void SetRate(ParticleSystem particles, float rate)
    {
        var emission = particles.emission;
        emission.rateOverTime = rate;
    }
}
