using UnityEngine;
using UnityEngine.InputSystem;

public class PlayerInteraction : MonoBehaviour
{
    public PrototypeSettingsSO settings;
    public DayManager day;
    public TruckController truck;
    public Camera view;
    public Transform handAnchor;
    public Transform rightHand;
    public PrototypeHUD hud;
    public RouteStock stock;
    public AudioSource audioSource;
    public AudioClip pickupSound, actionSound, readySound, saleSound, errorSound, pourSound, scoopSound, sprinkleSound;
    public PickupItem Held { get; private set; }
    public Interactable Target { get; private set; }
    public bool Gesturing => gesture != null;
    public bool Scooping => gesture is IceCreamTub;
    public bool ManualInput { get; set; }
    public Vector3 HitPoint { get; private set; }
    private Interactable gesture;
    private float soundCooldown;
    private Vector3 anchorRest;
    private Quaternion anchorRotation;

    private void Awake()
    {
        anchorRest = handAnchor.localPosition;
        anchorRotation = handAnchor.localRotation;
    }
    private void Update()
    {
        if (ManualInput) return;
        var mouse = Mouse.current;
        ProcessInput(mouse.leftButton.wasPressedThisFrame, mouse.leftButton.isPressed,
            mouse.leftButton.wasReleasedThisFrame, mouse.rightButton.wasPressedThisFrame, mouse.delta.ReadValue(), Time.deltaTime, Keyboard.current.eKey.wasPressedThisFrame);
    }
    public void ProcessInput(bool usePressed, bool held, bool released, bool putDown, Vector2 motion, float dt, bool ePressed = false)
    {
        soundCooldown -= dt;
        if (!day.CanPlay || truck.IsDriving)
        {
            EndGesture();
            if (day.CanPlay && ePressed) truck.ToggleDriving();
            return;
        }
        RaycastHit hit;
        Interactable next = null;
        if (Physics.Raycast(view.transform.position, view.transform.forward, out hit, settings.reach, ~((1 << 2) | (1 << 8)), QueryTriggerInteraction.Collide))
        {
            next = hit.collider.GetComponent<Interactable>();
            HitPoint = hit.point;
        }
        if (Target != next)
        {
            if (Target != null) Target.Highlight(false);
            Target = next;
            if (Target != null) Target.Highlight(true);
        }
        bool usesKeyboard = Target is TruckDoor || Target is TruckSeat;
        if (Target != null && (usesKeyboard ? ePressed : usePressed))
        {
            Target.Use(this);
        }
        if (held && gesture == null && Target != null && Target.CanGesture(this))
        {
            Target.Use(this);
            gesture = Target;
        }
        if (held && gesture != null)
        {
            if (Vector3.Distance(view.transform.position, gesture.transform.position) > settings.reach + .5f) EndGesture();
            else
            {
                gesture.Gesture(this, motion, dt);
                if (!gesture.CanGesture(this)) EndGesture();
            }
        }
        if (released || !held) EndGesture();
        if (putDown && Held != null)
        {
            EndGesture();
            Held.ReturnHome(this);
        }
        float wiggle = Gesturing ? Mathf.Sin(Time.time * 18) * .015f : 0;
        if (gesture is IceCreamTub tub)
        {
            handAnchor.rotation = tub.ScoopRotation * Quaternion.Inverse(Quaternion.Euler(Held.heldRotation));
            handAnchor.position += tub.ScoopPosition - Held.loadedScoop.transform.position;
        }
        else
        {
            handAnchor.localPosition = anchorRest;
            handAnchor.localRotation = Quaternion.Slerp(handAnchor.localRotation,
                Gesturing ? Quaternion.Euler(Held != null && Held.kind == PickupItem.ItemKind.Batter ? 105 : 0, 0, wiggle * 500) : anchorRotation, dt * 10);
        }
    }
    private void EndGesture()
    {
        if (gesture != null) gesture.StopGesture();
        gesture = null;
        handAnchor.localPosition = anchorRest;
        handAnchor.localRotation = anchorRotation;
    }
    public bool PickUp(PickupItem item, bool restoring = false)
    {
        if (Held != null || !restoring && !day.CanPlay) return false;
        Held = item;
        item.OnPickedUp();
        item.transform.SetParent(handAnchor, false);
        item.transform.localPosition = item.heldOffset;
        item.transform.localRotation = Quaternion.Euler(item.heldRotation);
        item.pickupCollider.enabled = false;
        Play(pickupSound);
        return true;
    }
    public PickupItem Release()
    {
        PickupItem item = Held;
        Held = null;
        item.transform.SetParent(null, true);
        item.pickupCollider.enabled = true;
        return item;
    }
    public void Notify(string message, bool error = false)
    {
        hud.ShowMessage(message);
        Play(error ? errorSound : actionSound);
    }
    public void Play(AudioClip clip)
    {
        audioSource.PlayOneShot(clip, settings.soundVolume);
    }
    public void GestureSound(AudioClip clip)
    {
        if (soundCooldown > 0) return;
        Play(clip);
        soundCooldown = .22f;
    }
}
