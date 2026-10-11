using Quantum;
using UnityEngine;

// Puts the camera at the local survivor's eyes, using the locally accumulated look angles plus the truck rotation the
// simulation carried the survivor through. When the local survivor is dead it follows a living teammate from behind.
// On top of that it adds the purely cosmetic feel: trauma-based screen shake, recoil kick, and the aim zoom.
public class FirstPersonCamera : MonoBehaviour
{
    [SerializeField] private QuantumEntityViewUpdater viewUpdater;
    [SerializeField] private SurvivorInput input;
    [SerializeField] private Camera eye;
    [SerializeField] private Vector3 spectateOffset = new Vector3(0, 2.6f, -3.5f);
    [SerializeField] private float fieldOfView = 75f;
    [SerializeField] private float aimFieldOfView = 55f;
    [SerializeField] private float scopeFieldOfView = 22f;
    [SerializeField] private float maxShakeAngle = 6f;
    [SerializeField] private float maxShakeOffset = 0.12f;
    [SerializeField] private float traumaDecay = 1.4f;
    private QuantumEntityView hiddenView;
    private float trauma;
    private float kick;
    private float eyeHeight;

    public void AddTrauma(float amount)
    {
        trauma = Mathf.Clamp01(trauma + amount);
    }

    public void Kick(float degrees)
    {
        kick += degrees;
    }

    private void LateUpdate()
    {
        var game = QuantumRunner.Default?.Game;
        if (game?.Frames.Predicted == null || !input.LocalEntity.IsValid) return;
        var frame = game.Frames.Predicted;
        var survivor = frame.Get<Survivor>(input.LocalEntity);
        var view = viewUpdater.GetView(input.LocalEntity);
        if (view == null) return;
        if (hiddenView != view)
        {
            foreach (var renderer in view.GetComponentsInChildren<Renderer>(true)) renderer.enabled = false;
            hiddenView = view;
        }
        if (!survivor.Dead)
        {
            // Crouching lowers the eyes smoothly; the simulation uses the same two heights for aiming and reach.
            var settings = frame.FindAsset(frame.RuntimeConfig.Settings);
            var wantedEye = (survivor.Crouching ? settings.CrouchEyeHeight : settings.EyeHeight).AsFloat;
            eyeHeight = eyeHeight == 0 ? wantedEye : Mathf.Lerp(eyeHeight, wantedEye, 1 - Mathf.Exp(-14 * Time.deltaTime));
            transform.SetPositionAndRotation(view.transform.position + Vector3.up * eyeHeight,
                Quaternion.Euler(input.Pitch - kick, input.Yaw + survivor.YawOffset.AsFloat, 0));
            var held = survivor.Hotbar[survivor.Selected].Kind;
            var aiming = input.Aiming && Inventory.Gun(held).Pellets > 0 && !survivor.Driving;
            var targetFov = !aiming ? fieldOfView : held == ItemKind.LongSpoon ? scopeFieldOfView : aimFieldOfView;
            eye.fieldOfView = Mathf.Lerp(eye.fieldOfView, targetFov, 1 - Mathf.Exp(-14 * Time.deltaTime));
        }
        else
        {
            var followed = viewUpdater.GetView(frame.GetSingletonEntityRef<Truck>()).transform;
            foreach (var pair in frame.GetComponentIterator<Survivor>())
            {
                if (pair.Component.Dead) continue;
                followed = viewUpdater.GetView(pair.Entity).transform;
                break;
            }
            var target = followed.position + followed.rotation * spectateOffset;
            transform.position = Vector3.Lerp(transform.position, target, 1 - Mathf.Exp(-6 * Time.deltaTime));
            transform.rotation = Quaternion.LookRotation(followed.position + Vector3.up * 1.4f - transform.position);
            eye.fieldOfView = fieldOfView;
        }

        kick = Mathf.Lerp(kick, 0, 1 - Mathf.Exp(-12 * Time.deltaTime));
        trauma = Mathf.Max(0, trauma - traumaDecay * Time.deltaTime);
        // Shake grows with the square of trauma so small hits stay subtle and explosions really rattle.
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
