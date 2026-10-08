using Photon.Deterministic;
using Quantum;
using UnityEngine;
using UnityEngine.InputSystem;

// Polls the local keyboard and mouse into Quantum input. Look angles and the selected hotbar slot are kept here and
// sent as absolute values so the camera never waits on the simulation. While the survivor is working a station
// (cranking the churn, scooping), mouse movement turns into gesture progress instead of looking around.
public class SurvivorInput : MonoBehaviour
{
    [SerializeField] private float mouseSensitivity = 0.12f;
    [SerializeField] private int hotbarSize = 6;
    [Tooltip("Off only for the headless play-test bot, which cannot lock the cursor.")]
    [SerializeField] private bool requireCursorLock = true;
    public float Yaw { get; private set; }
    public float Pitch { get; private set; }
    public int SelectedSlot { get; private set; }
    public EntityRef LocalEntity { get; private set; }
    public bool Working { get; private set; }
    public bool Aiming { get; private set; }
    // Mouse movement spent on station work this frame, for the view model's crank and scoop motion.
    public float GestureMotion { get; private set; }
    private float gesture;

    private void OnEnable()
    {
        QuantumCallback.Subscribe(this, (CallbackPollInput callback) => PollInput(callback));
        Cursor.lockState = CursorLockMode.Locked;
    }

    private void Update()
    {
        var game = QuantumRunner.Default?.Game;
        if (game?.Frames.Predicted != null)
        {
            var frame = game.Frames.Predicted;
            LocalEntity = EntityRef.None;
            // Only local slot 0 gets keyboard and mouse input (see PollInput), so that is the survivor this client views.
            game.Session.TryGetLocalPlayer(0, out var player);
            foreach (var pair in frame.GetComponentIterator<PlayerLink>())
            {
                if (pair.Component.Player != player) continue;
                LocalEntity = pair.Entity;
                Working = frame.Get<Survivor>(pair.Entity).WorkTarget.IsValid;
            }
        }

        var keyboard = Keyboard.current;
        var mouse = Mouse.current;
        if (keyboard.escapeKey.wasPressedThisFrame) Cursor.lockState = CursorLockMode.None;
        if (mouse.leftButton.wasPressedThisFrame) Cursor.lockState = CursorLockMode.Locked;
        for (int i = 0; i < hotbarSize; i++)
        {
            if (keyboard[Key.Digit1 + i].wasPressedThisFrame) SelectedSlot = i;
        }
        var scroll = mouse.scroll.ReadValue().y;
        if (scroll != 0) SelectedSlot = (SelectedSlot + (scroll < 0 ? 1 : hotbarSize - 1)) % hotbarSize;
        GestureMotion = 0;
        Aiming = false;
        if (requireCursorLock && Cursor.lockState != CursorLockMode.Locked) return;

        Aiming = mouse.rightButton.isPressed;
        var delta = mouse.delta.ReadValue() * mouseSensitivity;
        if (Working && mouse.leftButton.isPressed)
        {
            GestureMotion = Mathf.Abs(delta.x) + Mathf.Abs(delta.y);
            gesture += GestureMotion;
            return;
        }
        if (Aiming) delta *= 0.6f;
        Yaw += delta.x;
        Pitch = Mathf.Clamp(Pitch - delta.y, -85, 85);
    }

    private void PollInput(CallbackPollInput callback)
    {
        if (callback.PlayerSlot != 0)
        {
            callback.SetInput(new Quantum.Input(), DeterministicInputFlags.Repeatable);
            return;
        }
        var keyboard = Keyboard.current;
        var mouse = Mouse.current;
        var locked = !requireCursorLock || Cursor.lockState == CursorLockMode.Locked;
        var move = new Vector2((keyboard.dKey.isPressed ? 1 : 0) - (keyboard.aKey.isPressed ? 1 : 0),
            (keyboard.wKey.isPressed ? 1 : 0) - (keyboard.sKey.isPressed ? 1 : 0));
        var input = new Quantum.Input
        {
            Move = move.ToFPVector2(),
            Yaw = FP.FromFloat_UNSAFE(Yaw),
            Pitch = FP.FromFloat_UNSAFE(Pitch),
            Gesture = FP.FromFloat_UNSAFE(gesture),
            Slot = (byte)(SelectedSlot + 1),
            Jump = keyboard.spaceKey.isPressed,
            Fire = locked && mouse.leftButton.isPressed,
            Aim = locked && mouse.rightButton.isPressed,
            Interact = keyboard.eKey.isPressed,
            Drop = keyboard.qKey.isPressed,
            Reload = keyboard.rKey.isPressed,
            Sprint = keyboard.leftShiftKey.isPressed,
        };
        gesture = 0;
        callback.SetInput(input, DeterministicInputFlags.Repeatable);
    }
}
