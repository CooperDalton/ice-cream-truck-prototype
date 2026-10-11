using Quantum;
using UnityEngine;

// Truck presentation: swings the rear door and the roof hatch lid open and shut, spins and steers the wheels, turns the steering wheel, cranks the churn while someone works it,
// moves the hopper and fuel gauges, swings the bell mallet, shows the parts for every bought upgrade, and runs the engine sound,
// the music-box jingle, exhaust, road dust and the bloody tire tracks left after running zombies over.
public class TruckView : QuantumEntityViewComponent
{
    [SerializeField] private Transform[] wheels;
    [SerializeField] private Transform[] steeringPivots;
    [SerializeField] private float wheelRadius = 0.45f;
    [SerializeField] private Transform steeringWheel;
    [SerializeField] private Transform churnCrank;
    [SerializeField] private Transform gaugeNeedle;
    [SerializeField] private Transform fuelNeedle;
    [SerializeField] private Transform rearDoor;
    [SerializeField] private Transform hatchLid;
    [Tooltip("Swing of the rear door about the truck's up axis when open (the model is closed).")]
    [SerializeField] private float doorOpenAngle = -95f;
    [Tooltip("Turn of the hatch lid about the truck's X axis to shut it (the model is open).")]
    [SerializeField] private float lidCloseAngle = 112f;
    [SerializeField] private GameObject bigTank;
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
    private float needleAngle;
    private Quaternion steeringRest;
    private Quaternion crankRest;
    private Quaternion needleRest;
    private Quaternion fuelNeedleRest;
    private Quaternion doorRest;
    private Quaternion lidRest;
    private Quaternion malletRest;

    public override void OnInitialize()
    {
        steeringRest = steeringWheel.localRotation;
        crankRest = churnCrank.localRotation;
        needleRest = gaugeNeedle.localRotation;
        fuelNeedleRest = fuelNeedle.localRotation;
        doorRest = rearDoor.localRotation;
        lidRest = hatchLid.localRotation;
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
        // The ammo dial's scale runs 120 degrees either side of straight up and the needle model rests 52 degrees right of
        // it. The angle is eased as a number so a big swing (an empty hopper filled up) goes round the scale, not under it.
        needleAngle = Mathf.Lerp(needleAngle, Mathf.Lerp(-172, 68, (float)truck.HopperRounds / capacity), 1 - Mathf.Exp(-6 * dt));
        gaugeNeedle.localRotation = needleRest * Quaternion.Euler(0, 0, needleAngle);
        var tank = settings.FuelCapacity + (truck.BigTank ? settings.BigTankBonus : 0);
        fuelNeedle.localRotation = Quaternion.Slerp(fuelNeedle.localRotation, fuelNeedleRest * Quaternion.Euler(0, 0, Mathf.Lerp(-70, 70, (truck.Fuel / tank).AsFloat)), 1 - Mathf.Exp(-6 * dt));

        foreach (var pair in frame.GetComponentIterator<Station>())
        {
            if (pair.Component.Kind == StationKind.RearDoor)
            {
                var door = pair.Component.Open ? Quaternion.AngleAxis(doorOpenAngle, Vector3.up) * doorRest : doorRest;
                rearDoor.localRotation = Quaternion.Slerp(rearDoor.localRotation, door, 1 - Mathf.Exp(-10 * dt));
            }
            if (pair.Component.Kind == StationKind.Hatch)
            {
                var lid = pair.Component.Open ? lidRest : Quaternion.AngleAxis(lidCloseAngle, Vector3.right) * lidRest;
                hatchLid.localRotation = Quaternion.Slerp(hatchLid.localRotation, lid, 1 - Mathf.Exp(-10 * dt));
            }
        }

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
        bigTank.SetActive(truck.BigTank);
        turretMounts[0].SetActive(truck.Turret);
        turretMounts[1].SetActive(truck.SecondTurret);

        var throttle = truck.Driver.IsValid ? 1f : 0.3f;
        var pace = Mathf.Abs(speed) / 20f;
        engineSound.pitch = Mathf.Lerp(engineSound.pitch, 0.7f + pace * 1.1f + (truck.Engine ? 0.15f : 0), 1 - Mathf.Exp(-4 * dt));
        // An empty tank leaves the engine barely turning over.
        engineSound.volume = truck.Fuel > 0 ? 0.35f + 0.4f * throttle : 0.12f;
        if (!music.isPlaying) music.Play();
        music.mute = truck.MusicOff;
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
