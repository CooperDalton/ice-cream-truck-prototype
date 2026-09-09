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
    public bool LocksMouseLook => gesture != null && !(gesture is WaffleMaker);
    public bool Scooping => gesture is IceCreamTub;
    public bool ManualInput { get; set; }
    public Vector3 HitPoint { get; private set; }
    public bool CanPlace { get; private set; }
    public Vector3 PlacementPosition { get; private set; }
    private Quaternion placementRotation;
    private GameObject placementPreview;
    private Interactable gesture;
    private WaffleMaker pressedWaffle;
    private float waffleHoldTime;
    private bool pouredBatter;
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
            mouse.leftButton.wasReleasedThisFrame, Keyboard.current.qKey.wasPressedThisFrame, mouse.delta.ReadValue(), Time.deltaTime, Keyboard.current.eKey.wasPressedThisFrame);
    }
    public void ProcessInput(bool usePressed, bool held, bool released, bool putDown, Vector2 motion, float dt, bool ePressed = false)
    {
        soundCooldown -= dt;
        if (!day.CanPlay || truck.IsDriving)
        {
            CanPlace = false;
            if (placementPreview != null) placementPreview.SetActive(false);
            EndGesture();
            pressedWaffle = null;
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
        if (usePressed && Target is WaffleMaker waffle)
        {
            pressedWaffle = waffle;
            waffleHoldTime = 0;
            pouredBatter = false;
        }
        UpdatePlacement(hit);
        if (pressedWaffle != null)
        {
            if (Target != pressedWaffle)
            {
                EndGesture();
                pressedWaffle = null;
            }
            else
            {
                waffleHoldTime += dt;
                if (held && waffleHoldTime >= .18f && gesture == null && pressedWaffle.CanGesture(this))
                {
                    gesture = pressedWaffle;
                    pouredBatter = true;
                }
                if (released)
                {
                    if (!pouredBatter) pressedWaffle.Use(this);
                    pressedWaffle = null;
                }
            }
        }
        if (Target != null && !(Target is WaffleMaker) && (usesKeyboard ? ePressed : usePressed))
        {
            Target.Use(this);
        }
        if (held && gesture == null && Target != null && !(Target is WaffleMaker) && Target.CanGesture(this))
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
            pressedWaffle = null;
            if (!TryPlaceHeld()) Held.Drop(this);
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
    private void UpdatePlacement(RaycastHit hit)
    {
        using var sample = PlacementMarker.Auto();
        CanPlace = false;
        if (Held == null) return;
        placementPreview.SetActive(false);
        if (hit.collider == null || hit.collider.GetComponent<PlacementSurface>() == null || hit.normal.y < .95f) return;
        float surfaceYaw = hit.transform.IsChildOf(truck.transform) ? truck.transform.eulerAngles.y : hit.transform.eulerAngles.y;
        placementRotation = Quaternion.Euler(0, surfaceYaw, 0) * Quaternion.Euler(Held.placementRotation);
        CanPlace = FitsOnSurface(hit);
        for (int step = 1; step <= 8 && !CanPlace; step++)
        for (int direction = 0; direction < 8 && !CanPlace; direction++)
        {
            float angle = direction * Mathf.PI / 4;
            Vector3 offset = new Vector3(Mathf.Cos(angle), 0, Mathf.Sin(angle)) * (step * .02f);
            if (Physics.Raycast(hit.point + offset + Vector3.up * .06f, Vector3.down, out var nearby, .12f,
                ~((1 << 2) | (1 << 8)), QueryTriggerInteraction.Ignore) && nearby.collider == hit.collider
                && Vector3.Distance(view.transform.position, nearby.point) <= settings.reach)
                CanPlace = FitsOnSurface(nearby);
        }
        if (!CanPlace) return;
        placementPreview.transform.SetPositionAndRotation(PlacementPosition, placementRotation);
        placementPreview.SetActive(true);
    }
    static readonly Unity.Profiling.ProfilerMarker PlacementMarker = new Unity.Profiling.ProfilerMarker("Truck.Placement");
    private bool FitsOnSurface(RaycastHit hit)
    {
        Vector3 half = Held.placementSize * .5f;
        Vector3 center = hit.point + Vector3.up * (half.y + .012f);
        PlacementPosition = center - placementRotation * Held.placementCenter;
        foreach (var overlap in Physics.OverlapBox(center, half * .96f, placementRotation, ~((1 << 2) | (1 << 8)), QueryTriggerInteraction.Ignore))
            if (overlap != hit.collider && overlap != Held.pickupCollider) return false;
        for (int x = -1; x <= 1; x += 2)
        for (int z = -1; z <= 1; z += 2)
        {
            Vector3 corner = hit.point + placementRotation * new Vector3(x * half.x * .9f, 0, z * half.z * .9f);
            if (!Physics.Raycast(corner + Vector3.up * .05f, Vector3.down, out var support, .1f, ~((1 << 2) | (1 << 8)), QueryTriggerInteraction.Ignore)
                || support.collider.GetComponent<PlacementSurface>() == null) return false;
        }
        return true;
    }
    public bool TryPlaceHeld()
    {
        if (Held == null || !CanPlace) return false;
        Held.transform.SetPositionAndRotation(PlacementPosition, placementRotation);
        Held.Drop(this);
        return true;
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
        item.StopPhysics();
        item.OnPickedUp();
        item.transform.SetParent(handAnchor, false);
        item.transform.localPosition = item.heldOffset;
        item.transform.localRotation = Quaternion.Euler(item.heldRotation);
        item.pickupCollider.enabled = false;
        placementPreview = Instantiate(item.placementPreviewPrefab);
        placementPreview.SetActive(false);
        Play(pickupSound);
        return true;
    }
    public PickupItem Release()
    {
        PickupItem item = Held;
        Held = null;
        CanPlace = false;
        Destroy(placementPreview);
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
        audioSource.PlayOneShot(clip, settings.soundVolume * PlayerPrefs.GetFloat("EffectsVolume", 1));
    }
    public void GestureSound(AudioClip clip)
    {
        if (soundCooldown > 0) return;
        Play(clip);
        soundCooldown = .22f;
    }
}
