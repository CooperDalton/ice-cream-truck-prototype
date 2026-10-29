using Photon.Deterministic;
using Quantum;
using UnityEngine;
using UnityEngine.InputSystem;

// Polls the local keyboard and mouse into Quantum input for the Divorced Dads mode. Look angles and the selected
// hotbar slot are kept here and sent as absolute values so the camera never waits on the simulation.
public class DadsInput : MonoBehaviour
{
    [SerializeField] private float mouseSensitivity = 0.12f;
    [SerializeField] private int hotbarSize = 4;
    [Tooltip("Off only for the headless play-test bot, which cannot lock the cursor.")]
    [SerializeField] private bool requireCursorLock = true;
    public float Yaw { get; private set; }
    public float Pitch { get; private set; }
    public int SelectedSlot { get; private set; }
    public EntityRef LocalEntity { get; private set; }
    public bool Aiming { get; private set; }
    // The debug menu takes the number keys while it is open.
    public bool MenuOpen { get; set; }

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
            LocalEntity = EntityRef.None;
            // Only local slot 0 gets keyboard and mouse input (see PollInput), so that is the dad this client views.
            game.Session.TryGetLocalPlayer(0, out var player);
            foreach (var pair in game.Frames.Predicted.GetComponentIterator<Dad>())
            {
                if (pair.Component.Player == player) LocalEntity = pair.Entity;
            }
        }

        var keyboard = Keyboard.current;
        var mouse = Mouse.current;
        if (keyboard.escapeKey.wasPressedThisFrame) Cursor.lockState = CursorLockMode.None;
        if (mouse.leftButton.wasPressedThisFrame) Cursor.lockState = CursorLockMode.Locked;
        for (int i = 0; i < hotbarSize && !MenuOpen; i++)
        {
            if (keyboard[Key.Digit1 + i].wasPressedThisFrame) SelectedSlot = i;
        }
        var scroll = mouse.scroll.ReadValue().y;
        if (scroll != 0) SelectedSlot = (SelectedSlot + (scroll < 0 ? 1 : hotbarSize - 1)) % hotbarSize;
        Aiming = false;
        if (requireCursorLock && Cursor.lockState != CursorLockMode.Locked) return;
        Aiming = mouse.rightButton.isPressed;
        var delta = mouse.delta.ReadValue() * mouseSensitivity;
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
            Slot = (byte)(SelectedSlot + 1),
            Jump = keyboard.spaceKey.isPressed,
            Fire = locked && mouse.leftButton.isPressed,
            Aim = locked && mouse.rightButton.isPressed,
            Interact = keyboard.eKey.isPressed,
            Drop = keyboard.qKey.isPressed,
            Reload = keyboard.rKey.isPressed,
            Sprint = keyboard.leftShiftKey.isPressed,
        };
        callback.SetInput(input, DeterministicInputFlags.Repeatable);
    }
}
