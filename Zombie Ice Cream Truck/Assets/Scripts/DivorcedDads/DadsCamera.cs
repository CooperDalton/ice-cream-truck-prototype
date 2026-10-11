using Quantum;
using UnityEngine;

// Puts the camera at the local dad's eyes, using the locally accumulated look angles plus the van rotation the
// simulation carried him through. While he tumbles after being run over (or sits in the back of a cruiser) the camera
// pulls out behind his body so the player gets to watch, and on the roof minigun it looks down the gun's back through
// its sight. On top of that: trauma screen shake, a punch-in lunge for cone shoves, recoil kick and the aim zoom.
public class DadsCamera : MonoBehaviour
{
    [SerializeField] private QuantumEntityViewUpdater viewUpdater;
    [SerializeField] private DadsInput input;
    [SerializeField] private Camera eye;
    [SerializeField] private float eyeHeight = 1.5f;
    [SerializeField] private Vector3 tumbleOffset = new Vector3(0, 2.8f, -4.2f);
    [SerializeField] private float fieldOfView = 75f;
    [SerializeField] private float aimFieldOfView = 55f;
    [SerializeField] private float turretFieldOfView = 60f;
    [SerializeField] private float maxShakeAngle = 6f;
    [SerializeField] private float maxShakeOffset = 0.12f;
    [SerializeField] private float traumaDecay = 1.4f;
    public static DadsCamera Instance { get; private set; }
    private QuantumEntityView hiddenView;
    private float trauma;
    private float kick;
    private float lunge;
    private bool tumbling;

    private void Awake()
    {
        Instance = this;
    }

    // Shake (trauma 0-1), recoil kick in degrees, and the forward punch-in of a cone shove.
    public void Jolt(float traumaAmount, float kickDegrees, bool lungeForward)
    {
        trauma = Mathf.Clamp01(trauma + traumaAmount);
        kick += kickDegrees;
        if (lungeForward) lunge = 1;
    }

    private void LateUpdate()
    {
        var game = QuantumRunner.Default?.Game;
        if (game?.Frames.Predicted == null || !input.LocalEntity.IsValid) return;
        var frame = game.Frames.Predicted;
        var dad = frame.Get<Dad>(input.LocalEntity);
        var view = viewUpdater.GetView(input.LocalEntity);
        if (view == null) return;
        var down = dad.Knocked > 0 || dad.Busted > 0;
        if (hiddenView != view || tumbling != down)
        {
            // Our own body is hidden in first person and shown while we watch it tumble.
            foreach (var renderer in view.GetComponentsInChildren<Renderer>(true)) renderer.enabled = down;
            hiddenView = view;
            tumbling = down;
        }
        var dt = Time.deltaTime;
        if (down)
        {
            var body = view.transform.position;
            var behind = Quaternion.Euler(0, input.Yaw + dad.YawOffset.AsFloat, 0) * tumbleOffset;
            transform.position = Vector3.Lerp(transform.position, body + behind, 1 - Mathf.Exp(-5 * dt));
            transform.rotation = Quaternion.LookRotation(body + Vector3.up * 0.6f - transform.position);
            eye.fieldOfView = fieldOfView;
        }
        else if (dad.Turret)
        {
            var settings = frame.FindAsset(frame.RuntimeConfig.DadsSettings);
            var truck = viewUpdater.GetView(frame.GetSingletonEntityRef<Van>()).transform;
            var aim = Quaternion.Euler(input.Pitch - kick, input.Yaw + dad.YawOffset.AsFloat, 0);
            var pivot = truck.TransformPoint(settings.TurretPivot.ToUnityVector3());
            transform.SetPositionAndRotation(pivot + aim * settings.TurretEye.ToUnityVector3(), aim);
            eye.fieldOfView = Mathf.Lerp(eye.fieldOfView, turretFieldOfView, 1 - Mathf.Exp(-14 * dt));
        }
        else
        {
            lunge = Mathf.MoveTowards(lunge, 0, dt * 5);
            var punch = Mathf.Sin(lunge * Mathf.PI) * 0.25f;
            var rotation = Quaternion.Euler(input.Pitch - kick, input.Yaw + dad.YawOffset.AsFloat, 0);
            transform.SetPositionAndRotation(view.transform.position + Vector3.up * eyeHeight + rotation * Vector3.forward * punch, rotation);
            var held = dad.Hotbar[dad.Selected].Kind;
            var aiming = input.Aiming && DadSystem.IsGun(held) && !dad.Driving;
            eye.fieldOfView = Mathf.Lerp(eye.fieldOfView, aiming ? aimFieldOfView : fieldOfView, 1 - Mathf.Exp(-14 * dt));
        }

        kick = Mathf.Lerp(kick, 0, 1 - Mathf.Exp(-12 * dt));
        var van = frame.GetSingleton<Van>();
        if (van.Shake > 0) trauma = Mathf.Max(trauma, 0.5f);
        trauma = Mathf.Max(0, trauma - traumaDecay * dt);
        // Shake grows with the square of trauma so small bumps stay subtle and slams really rattle.
        var shake = trauma * trauma;
        var time = Time.time * 25f;
        transform.rotation *= Quaternion.Euler(
            maxShakeAngle * shake * (Mathf.PerlinNoise(time, 1.1f) * 2 - 1),
            maxShakeAngle * shake * (Mathf.PerlinNoise(time, 2.3f) * 2 - 1),
            maxShakeAngle * shake * (Mathf.PerlinNoise(time, 3.7f) * 2 - 1));
        transform.position += transform.rotation * new Vector3(
            maxShakeOffset * shake * (Mathf.PerlinNoise(time, 4.1f) * 2 - 1),
            maxShakeOffset * shake * (Mathf.PerlinNoise(time, 5.3f) * 2 - 1), 0);
    }
}
