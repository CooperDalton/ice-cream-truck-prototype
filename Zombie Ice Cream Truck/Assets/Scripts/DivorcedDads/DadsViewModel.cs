using Quantum;
using UnityEngine;

// First-person hairy dad arms and whatever the local dad is holding. Moves the rig for feel: walk bob, look sway,
// aim-down-sights, the big forward jab of a cone shove, gun recoil, and a quick dip when switching items.
public class DadsViewModel : MonoBehaviour
{
    [SerializeField] private DadsInput input;
    [SerializeField] private DadsCamera cameraRig;
    [SerializeField] private GameObject arms;
    [SerializeField] private HeldItems held;
    [SerializeField] private Transform sway;
    [SerializeField] private Transform recoilPivot;
    [SerializeField] private float recoilDistance = 0.06f;
    [SerializeField] private float recoilAngle = 7f;
    [Tooltip("Rig offset that brings the gun's sights to the middle of the screen.")]
    [SerializeField] private Vector3 aimOffset = new Vector3(-0.22f, -0.045f, -0.06f);
    [SerializeField] private Vector3 shoveReach = new Vector3(-0.12f, 0.12f, 0.45f);
    [SerializeField] private float bobAmount = 0.018f;
    private float bobPhase;
    private float dip;
    private float jab;
    private Vector3 lastPosition;
    private Quaternion lastRotation;
    private Vector3 lookSway;

    private void OnEnable()
    {
        QuantumEvent.Subscribe(this, (EventGlobFired e) => OnFired(e));
        QuantumEvent.Subscribe(this, (EventShoved e) => OnShoved(e));
        QuantumEvent.Subscribe(this, (EventRefilled e) => OnRefilled(e));
    }

    private void OnFired(EventGlobFired e)
    {
        if (!QuantumRunner.Default.Game.PlayerIsLocal(e.Player) || e.Turret) return;
        var heavy = e.Gun == DadItem.SundaeShotgun ? 2.2f : 1f;
        recoilPivot.localPosition = Vector3.back * recoilDistance * heavy;
        recoilPivot.localRotation = Quaternion.Euler(-recoilAngle * heavy, Random.Range(-2f, 2f), 0);
        cameraRig.Jolt(0.05f * heavy, 1.5f * heavy, false);
    }

    private void OnShoved(EventShoved e)
    {
        if (!QuantumRunner.Default.Game.PlayerIsLocal(e.Player)) return;
        jab = 1;
        cameraRig.Jolt(e.Whiff ? 0.05f : 0.25f, e.Whiff ? 0 : -3f, !e.Whiff);
    }

    private void OnRefilled(EventRefilled e)
    {
        if (QuantumRunner.Default.Game.PlayerIsLocal(e.Player)) dip = 1;
    }

    private void Update()
    {
        var dt = Time.deltaTime;
        recoilPivot.localPosition = Vector3.Lerp(recoilPivot.localPosition, Vector3.zero, 1 - Mathf.Exp(-18 * dt));
        recoilPivot.localRotation = Quaternion.Slerp(recoilPivot.localRotation, Quaternion.identity, 1 - Mathf.Exp(-14 * dt));
        var game = QuantumRunner.Default?.Game;
        var visible = false;
        var aiming = false;
        if (game?.Frames.Predicted != null && input.LocalEntity.IsValid)
        {
            var frame = game.Frames.Predicted;
            var dad = frame.Get<Dad>(input.LocalEntity);
            visible = dad.Knocked <= 0 && dad.Busted <= 0 && !dad.Driving && !dad.Turret;
            var item = dad.Hotbar[dad.Selected];
            aiming = input.Aiming && DadSystem.IsGun(item.Kind);
            if (held.Show(item, frame.GetSingleton<DadsRun>().ConeSize)) dip = Mathf.Max(dip, 0.6f);
        }
        arms.SetActive(visible);
        UpdateSway(aiming, dt);
    }

    private void UpdateSway(bool aiming, float dt)
    {
        var camera = transform.parent;
        var moved = camera.position - lastPosition;
        moved.y = 0;
        var speed = Mathf.Min(moved.magnitude / Mathf.Max(dt, 0.0001f), 8f);
        lastPosition = camera.position;
        // Van rides move the camera too, so only walking-pace motion bobs the arms.
        var walking = speed > 0.5f && speed < 7.5f ? 1f : 0f;
        bobPhase += speed * dt * 2.2f;
        var bob = new Vector3(Mathf.Cos(bobPhase) * bobAmount, -Mathf.Abs(Mathf.Sin(bobPhase)) * bobAmount, 0) * walking * (aiming ? 0.2f : 1f);

        // The rig lags a little behind fast mouse turns.
        var turn = Quaternion.Inverse(lastRotation) * camera.rotation;
        lastRotation = camera.rotation;
        var euler = turn.eulerAngles;
        var lag = new Vector3(-Mathf.DeltaAngle(0, euler.y), Mathf.DeltaAngle(0, euler.x), 0) * 0.004f;
        lookSway = Vector3.Lerp(lookSway + Vector3.ClampMagnitude(lag, 0.05f), Vector3.zero, 1 - Mathf.Exp(-10 * dt));

        // The shove: a fast jab out to the face in front, then back.
        jab = Mathf.MoveTowards(jab, 0, dt * 4.5f);
        var thrust = Mathf.Sin(jab * Mathf.PI);
        dip = Mathf.MoveTowards(dip, 0, dt * 2.2f);
        var lowered = Mathf.Sin(dip * Mathf.PI);
        var target = (aiming ? aimOffset : Vector3.zero) + bob + lookSway + shoveReach * thrust + new Vector3(0, -0.12f, 0) * lowered;
        sway.localPosition = Vector3.Lerp(sway.localPosition, target, 1 - Mathf.Exp(-(jab > 0 ? 40 : 16) * dt));
        sway.localRotation = Quaternion.Slerp(sway.localRotation, Quaternion.Euler(lowered * 35f - thrust * 25f, 0, lowered * -20f), 1 - Mathf.Exp(-16 * dt));
    }
}
