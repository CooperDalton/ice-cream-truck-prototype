using UnityEngine;
using UnityEngine.InputSystem;

public class TruckController : MonoBehaviour
{
    public PrototypeSettingsSO settings;
    public DayManager day;
    public PlayerController player;
    public CustomerManager customers;
    public Transform driver, kitchen, standPoint;
    public TruckSeat seat;
    public TruckDoor rearDoor;
    public Bounds cabinBounds = new Bounds(new Vector3(-.35f, 1.9f, 0), new Vector3(6.5f, 2.8f, 3.6f));
    public Transform[] wheels;
    public Transform steeringWheel;
    public Vector3 collisionCenter = new Vector3(.1f, 1.5f, .35f);
    public Vector3 collisionHalfSize = new Vector3(3.8f, 1.2f, 2.3f);
    public LayerMask obstacles = 1 << 10;
    public bool IsDriving { get; private set; }
    public bool InsideTruck => cabinBounds.Contains(transform.InverseTransformPoint(player.transform.position));
    public bool ServiceOpen => Mathf.Abs(Speed) < .05f;
    public float Speed { get; private set; }
    public bool ManualInput { get; set; }
    public bool automaticRoute;
    float throttle, steering;
    bool brake;
    Quaternion wheelRest;
    readonly Collider[] overlaps = new Collider[16];

    void Awake() { wheelRest = steeringWheel.localRotation; }
    void Update()
    {
        if (automaticRoute || ManualInput || !day.CanPlay) return;
        var k = Keyboard.current;
        throttle = (k.wKey.isPressed ? 1 : 0) - (k.sKey.isPressed ? 1 : 0);
        steering = (k.dKey.isPressed ? 1 : 0) - (k.aKey.isPressed ? 1 : 0);
        brake = k.spaceKey.isPressed;
    }
    void FixedUpdate()
    {
        if (!automaticRoute && !ManualInput) Drive(throttle, steering, brake, Time.fixedDeltaTime);
    }
    public void Drive(float gas, float turn, bool braking, float dt)
    {
        if (!day.CanPlay || !IsDriving) { Speed = 0; return; }
        float target = braking ? 0 : gas * (gas >= 0 ? settings.truckSpeed : settings.reverseSpeed);
        Speed = Mathf.MoveTowards(Speed, target, (braking || gas == 0 ? settings.braking : settings.acceleration) * dt);
        float angle = Mathf.Tan(turn * settings.steeringAngle * Mathf.Deg2Rad) * Speed / settings.wheelbase * Mathf.Rad2Deg * dt;
        Quaternion rotation = transform.rotation * Quaternion.Euler(0, angle, 0);
        Vector3 movement = rotation * Vector3.right * (Speed * dt);
        Vector3 start = transform.TransformPoint(collisionCenter);
        Vector3 position = transform.position + movement;
        bool blocked = movement.sqrMagnitude > 0 && Physics.BoxCast(start, collisionHalfSize, movement.normalized,
            out _, transform.rotation, movement.magnitude + .03f, obstacles, QueryTriggerInteraction.Ignore);
        blocked |= Physics.OverlapBoxNonAlloc(position + rotation * collisionCenter, collisionHalfSize, overlaps,
            rotation, obstacles, QueryTriggerInteraction.Ignore) > 0;
        if (blocked) Speed = 0;
        else
        {
            if (movement.sqrMagnitude > .000001f && customers.Queue.Count > 0) customers.ReleaseQueue();
            transform.SetPositionAndRotation(position, rotation);
        }
        foreach (var wheel in wheels) wheel.Rotate(Vector3.forward, -Speed * dt * 100, Space.Self);
        steeringWheel.localRotation = wheelRest * Quaternion.Euler(0, 0, -turn * 75);
        Physics.SyncTransforms();
    }
    public void FollowRoute(Vector3 position, Quaternion rotation, float speed)
    {
        Speed = speed;
        transform.SetPositionAndRotation(position, rotation);
        foreach (var wheel in wheels) wheel.Rotate(Vector3.forward, -speed * Time.deltaTime * 100, Space.Self);
        Physics.SyncTransforms();
    }
    public bool ToggleDriving()
    {
        if (!day.CanPlay) return false;
        if (automaticRoute) { player.interaction.Notify("The truck follows your route plan"); return false; }
        if (IsDriving)
        {
            if (Mathf.Abs(Speed) > .15f) { player.interaction.Notify("Brake to a stop before leaving the seat", true); return false; }
            IsDriving = false;
            player.Teleport(transform, standPoint.position, standPoint.rotation);
            player.interaction.rightHand.gameObject.SetActive(true);
            player.interaction.Notify("Parked");
            return true;
        }
        if (!InsideTruck || player.interaction.Target != seat || Vector3.Distance(player.transform.position, driver.position) > seat.reach)
        { player.interaction.Notify("Enter the truck and approach the driver's seat", true); return false; }
        if (player.interaction.Held != null) { player.interaction.Notify("Put down your item before driving", true); return false; }
        IsDriving = true;
        player.Teleport(transform, driver.position, driver.rotation);
        player.controller.enabled = false;
        player.interaction.rightHand.gameObject.SetActive(false);
        return true;
    }
}
