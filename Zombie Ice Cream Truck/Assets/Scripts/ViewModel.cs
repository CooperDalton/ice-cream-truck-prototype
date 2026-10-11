using System;
using Quantum;
using UnityEngine;

// First-person arms and whatever the local survivor is holding: the selected hotbar item (crates, sacks and tubs in both
// hands). Moves the whole rig for feel: aim-down-sights, walk bob, look sway, the crank/scoop circles while working a
// station, a lowered pose while reloading, the recoil kick and the cone jab. Melee cones show their scoop tinted to its
// flavor, and no scoop once it has been eaten.
public class ViewModel : MonoBehaviour
{
    [Serializable]
    public struct HeldModel
    {
        public ItemKind Kind;
        public Flavor Flavor;
        public GameObject Model;
        public Renderer[] Scoops;
    }

    [SerializeField] private SurvivorInput input;
    [SerializeField] private GameObject arms;
    [SerializeField] private HeldModel[] models;
    [SerializeField] private Transform sway;
    [SerializeField] private Transform recoilPivot;
    [SerializeField] private float recoilDistance = 0.06f;
    [SerializeField] private float recoilAngle = 7f;
    [Tooltip("Rig offset that brings the gun's sights to the middle of the screen.")]
    [SerializeField] private Vector3 aimOffset = new Vector3(-0.15f, 0.07f, -0.05f);
    [SerializeField] private float workRadius = 0.06f;
    [SerializeField] private float bobAmount = 0.018f;
    [SerializeField] private Vector3 jabOffset = new Vector3(-0.12f, 0.06f, 0.22f);
    [SerializeField] private Vector3 jabEuler = new Vector3(-55f, -30f, 25f);
    [Tooltip("Emission strength of the PS1 materials, kept when a scoop is tinted.")]
    [SerializeField] private float scoopEmission = 0.32f;
    private Item shown = new Item { Kind = (ItemKind)255 };
    private MaterialPropertyBlock tint;
    private float workPhase;
    private float bobPhase;
    private float reloadDip;
    private Vector3 lastPosition;
    private Quaternion lastRotation;
    private Vector3 lookSway;

    private void OnEnable()
    {
        QuantumEvent.Subscribe(this, (EventShotFired e) => OnShot(e));
        QuantumEvent.Subscribe(this, (EventReloaded e) => OnReloaded(e));
        QuantumEvent.Subscribe(this, (EventMeleeSwung e) => OnSwung(e));
        tint = new MaterialPropertyBlock();
    }

    private void OnSwung(EventMeleeSwung e)
    {
        if (!QuantumRunner.Default.Game.PlayerIsLocal(e.Player)) return;
        recoilPivot.localPosition = jabOffset;
        recoilPivot.localRotation = Quaternion.Euler(jabEuler);
    }

    private void OnShot(EventShotFired e)
    {
        if (!QuantumRunner.Default.Game.PlayerIsLocal(e.Player)) return;
        var heavy = e.Gun == ItemKind.SundaeBazooka ? 3.2f
            : e.Gun == ItemKind.SundaeShotgun || e.Gun == ItemKind.LongSpoon || e.Gun == ItemKind.ConeLauncher ? 2.2f
            : e.Gun == ItemKind.SoftServeHose ? 0.4f : 1f;
        recoilPivot.localPosition = Vector3.back * recoilDistance * heavy;
        recoilPivot.localRotation = Quaternion.Euler(-recoilAngle * heavy, UnityEngine.Random.Range(-2f, 2f), 0);
    }

    private void OnReloaded(EventReloaded e)
    {
        if (QuantumRunner.Default.Game.PlayerIsLocal(e.Player)) reloadDip = 1;
    }

    private void Update()
    {
        var dt = Time.deltaTime;
        recoilPivot.localPosition = Vector3.Lerp(recoilPivot.localPosition, Vector3.zero, 1 - Mathf.Exp(-18 * dt));
        recoilPivot.localRotation = Quaternion.Slerp(recoilPivot.localRotation, Quaternion.identity, 1 - Mathf.Exp(-14 * dt));
        var game = QuantumRunner.Default?.Game;
        var held = default(Item);
        var visible = false;
        var aiming = false;
        if (game?.Frames.Predicted != null && input.LocalEntity.IsValid)
        {
            var survivor = game.Frames.Predicted.Get<Survivor>(input.LocalEntity);
            visible = !survivor.Dead && !survivor.Driving && survivor.TurretSeat == 0;
            held = survivor.Hotbar[survivor.Selected];
            var gun = Inventory.Gun(held.Kind);
            aiming = input.Aiming && gun.Pellets > 0 && !gun.Melee;
        }
        arms.SetActive(visible);
        UpdateSway(aiming, dt);
        if (held.Kind == shown.Kind && held.Flavor == shown.Flavor && (held.Count > 0) == (shown.Count > 0)) return;
        if (held.Kind != shown.Kind) reloadDip = Mathf.Max(reloadDip, 0.6f);  // swapping items dips the rig like a quick holster
        shown = held;
        var color = FlavorPalette.Of(held.Flavor);
        tint.SetColor("_BaseColor", color);
        tint.SetColor("_EmissionColor", color * scoopEmission);
        foreach (var model in models)
        {
            model.Model.SetActive(model.Kind == held.Kind && (model.Flavor == Flavor.None || model.Flavor == held.Flavor));
            foreach (var scoop in model.Scoops)
            {
                scoop.enabled = held.Count > 0;
                scoop.SetPropertyBlock(tint);
            }
        }
    }

    private void UpdateSway(bool aiming, float dt)
    {
        var camera = transform.parent;
        var moved = camera.position - lastPosition;
        moved.y = 0;
        var speed = Mathf.Min(moved.magnitude / Mathf.Max(dt, 0.0001f), 8f);
        lastPosition = camera.position;
        // Truck rides move the camera too, so only walking-pace motion bobs the arms.
        var walking = speed > 0.5f && speed < 7.5f ? 1f : 0f;
        bobPhase += speed * dt * 2.2f;
        var bob = new Vector3(Mathf.Cos(bobPhase) * bobAmount, -Mathf.Abs(Mathf.Sin(bobPhase)) * bobAmount, 0) * walking * (aiming ? 0.2f : 1f);

        // The rig lags a little behind fast mouse turns.
        var turn = Quaternion.Inverse(lastRotation) * camera.rotation;
        lastRotation = camera.rotation;
        var euler = turn.eulerAngles;
        var lag = new Vector3(-Mathf.DeltaAngle(0, euler.y), Mathf.DeltaAngle(0, euler.x), 0) * 0.004f;
        lookSway = Vector3.Lerp(lookSway + Vector3.ClampMagnitude(lag, 0.05f), Vector3.zero, 1 - Mathf.Exp(-10 * dt));

        // Working the churn or scooping turns mouse motion into circles of the hands.
        workPhase += input.GestureMotion * 0.25f;
        var working = input.Working ? new Vector3(Mathf.Cos(workPhase), Mathf.Sin(workPhase), 0) * workRadius + new Vector3(-0.05f, -0.06f, 0.08f) : Vector3.zero;

        reloadDip = Mathf.MoveTowards(reloadDip, 0, dt * 2.2f);
        var dip = Mathf.Sin(reloadDip * Mathf.PI);
        var target = (aiming ? aimOffset : Vector3.zero) + bob + lookSway + working + new Vector3(0, -0.12f, 0) * dip;
        sway.localPosition = Vector3.Lerp(sway.localPosition, target, 1 - Mathf.Exp(-16 * dt));
        sway.localRotation = Quaternion.Slerp(sway.localRotation, Quaternion.Euler(dip * 35f, 0, dip * -20f), 1 - Mathf.Exp(-16 * dt));
    }
}
