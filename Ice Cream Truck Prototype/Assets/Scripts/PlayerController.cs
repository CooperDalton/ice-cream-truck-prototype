using UnityEngine;
using UnityEngine.InputSystem;

public class PlayerController : MonoBehaviour
{
    public PrototypeSettingsSO settings;
    public DayManager day;
    public CharacterController controller;
    public Camera view;
    public PlayerInteraction interaction;
    public TruckController truck;
    [SerializeField] private float eyeHeight = 1.55f;
    [SerializeField] private float gravity = -20;
    [SerializeField] private float pitch = 24;
    private float fallSpeed;
    private float bobTime;
    public bool ManualInput { get; set; }
    public const string MouseSensitivityKey = "MouseSensitivity";
    public float MouseSensitivity { get; private set; }

    private void Awake()
    {
        MouseSensitivity = Mathf.Clamp(PlayerPrefs.GetFloat(MouseSensitivityKey, settings.mouseSensitivity), .01f, .5f);
    }

    public void SetMouseSensitivity(float value)
    {
        MouseSensitivity = Mathf.Clamp(value, .01f, .5f);
        PlayerPrefs.SetFloat(MouseSensitivityKey, MouseSensitivity);
    }

    private void Start()
    {
        Application.runInBackground = true;
        Cursor.lockState = day.CanPlay ? CursorLockMode.Locked : CursorLockMode.None;
        Cursor.visible = !day.CanPlay;
        view.fieldOfView = settings.fieldOfView;
    }
    private void Update()
    {
        if (ManualInput) return;
        var keyboard = Keyboard.current;
        if (keyboard.escapeKey.wasPressedThisFrame) day.TogglePause();
        Vector2 movement = new Vector2((keyboard.dKey.isPressed ? 1 : 0) - (keyboard.aKey.isPressed ? 1 : 0),
            (keyboard.wKey.isPressed ? 1 : 0) - (keyboard.sKey.isPressed ? 1 : 0));
        if (keyboard.spaceKey.wasPressedThisFrame && !truck.IsDriving) Jump();
        Move(movement, Mouse.current.delta.ReadValue(), Time.deltaTime, keyboard.leftShiftKey.isPressed || keyboard.rightShiftKey.isPressed);
    }
    public void Move(Vector2 movement, Vector2 mouse, float dt, bool sprint = false)
    {
        bool sprinting = sprint && movement.sqrMagnitude > .01f && day.CanPlay && !truck.IsDriving;
        float targetFov = settings.fieldOfView + (sprinting ? settings.sprintFovIncrease : 0);
        view.fieldOfView = Mathf.Lerp(view.fieldOfView, targetFov, 1 - Mathf.Exp(-settings.cameraSmoothing * dt));
        if (!day.CanPlay) return;
        if (!interaction.Gesturing)
        {
            transform.Rotate(0, mouse.x * MouseSensitivity, 0);
            pitch = Mathf.Clamp(pitch - mouse.y * MouseSensitivity, -80, 80);
            view.transform.localRotation = Quaternion.Euler(pitch, 0, 0);
        }
        if (truck.IsDriving) return;
        movement = Vector2.ClampMagnitude(movement, 1);
        bool walking = movement.sqrMagnitude > .01f && controller.isGrounded;
        if (controller.isGrounded && fallSpeed < 0) fallSpeed = -2;
        fallSpeed += gravity * dt;
        float speed = settings.walkSpeed * (sprinting ? settings.sprintMultiplier : 1);
        controller.Move((transform.TransformDirection(new Vector3(movement.x, 0, movement.y)) * speed + Vector3.up * fallSpeed) * dt);
        transform.SetParent(truck.InsideTruck ? truck.transform : null, true);
        if (walking) bobTime += dt * settings.bobFrequency * Mathf.PI * 2;
        float bob = settings.headBob && walking ? Mathf.Sin(bobTime) * settings.bobAmplitude : 0;
        view.transform.localPosition = Vector3.Lerp(view.transform.localPosition, new Vector3(0, eyeHeight + bob, 0), 1 - Mathf.Exp(-settings.cameraSmoothing * dt));
    }
    public bool Jump()
    {
        if (!day.CanPlay || !controller.isGrounded || truck.IsDriving) return false;
        fallSpeed = Mathf.Sqrt(-2 * gravity * settings.jumpHeight);
        return true;
    }
    public void Teleport(Transform parent, Vector3 position, Quaternion rotation)
    {
        controller.enabled = false;
        transform.SetParent(parent, true);
        transform.SetPositionAndRotation(position, rotation);
        fallSpeed = 0;
        pitch = 10;
        view.transform.localPosition = new Vector3(0, eyeHeight, 0);
        view.transform.localRotation = Quaternion.Euler(pitch, 0, 0);
        controller.enabled = true;
        Physics.SyncTransforms();
    }
}
