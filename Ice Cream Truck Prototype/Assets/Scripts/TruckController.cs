using UnityEngine;
using UnityEngine.InputSystem;

[DefaultExecutionOrder(-100)]
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
    public Vector3 Velocity { get; private set; }
    public Vector3 Acceleration { get; private set; }
    public Vector3 AngularVelocity { get; private set; }
    public Vector3 AngularAcceleration { get; private set; }
    public float WheelAngle { get; private set; }
    float throttle, steering;
    float engineInput;
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
        if (!day.CanPlay) return;
        if (!IsDriving) { Speed = 0; UpdateMotion(Vector3.zero, Vector3.zero, dt); return; }
        gas = Mathf.Clamp(gas, -1, 1);
        bool changingDirection = gas * Speed < -.05f;
        engineInput = Mathf.MoveTowards(engineInput, braking || changingDirection ? 0 : gas, settings.throttleResponse * dt);
        if (braking || changingDirection) Speed = Mathf.MoveTowards(Speed, 0, settings.braking * dt);
        else
        {
            float limit = engineInput >= 0 ? settings.truckSpeed : settings.reverseSpeed;
            float driveForce = engineInput * settings.acceleration * (1 - Mathf.Clamp01(Mathf.Abs(Speed) / limit));
            Speed += driveForce * dt;
            Speed = Mathf.MoveTowards(Speed, 0, (settings.rollingResistance + settings.aerodynamicDrag * Speed * Speed) * dt);
        }
        float maxAngle = Mathf.Min(settings.steeringAngle,
            Mathf.Atan(settings.corneringAcceleration * settings.wheelbase / Mathf.Max(1, Speed * Speed)) * Mathf.Rad2Deg);
        WheelAngle = Mathf.MoveTowards(WheelAngle, Mathf.Clamp(turn, -1, 1) * maxAngle, settings.steeringResponse * dt);
        float angle = Mathf.Tan(WheelAngle * Mathf.Deg2Rad) * Speed / settings.wheelbase * Mathf.Rad2Deg * dt;
        Quaternion rotation = transform.rotation * Quaternion.Euler(0, angle, 0);
        Vector3 movement = rotation * Vector3.right * (Speed * dt);
        Vector3 start = transform.TransformPoint(collisionCenter);
        Vector3 position = transform.position + movement;
        bool blocked = movement.sqrMagnitude > 0 && Physics.BoxCast(start, collisionHalfSize, movement.normalized,
            out _, transform.rotation, movement.magnitude + .03f, obstacles, QueryTriggerInteraction.Ignore);
        blocked |= Physics.OverlapBoxNonAlloc(position + rotation * collisionCenter, collisionHalfSize, overlaps,
            rotation, obstacles, QueryTriggerInteraction.Ignore) > 0;
        if (blocked) { Speed = 0; angle = 0; }
        else
        {
            if (movement.sqrMagnitude > .000001f && customers.Queue.Count > 0) customers.ReleaseQueue(followVan: true);
            transform.SetPositionAndRotation(position, rotation);
        }
        foreach (var wheel in wheels) wheel.Rotate(Vector3.forward, -Speed * dt * 100, Space.Self);
        steeringWheel.localRotation = wheelRest * Quaternion.Euler(0, 0, -WheelAngle / settings.steeringAngle * 75);
        UpdateMotion(transform.right * Speed, Vector3.up * (angle * Mathf.Deg2Rad / dt), dt);
        Physics.SyncTransforms();
    }
    void UpdateMotion(Vector3 velocity, Vector3 angularVelocity, float dt)
    {
        Acceleration = (velocity - Velocity) / dt;
        AngularAcceleration = (angularVelocity - AngularVelocity) / dt;
        Velocity = velocity;
        AngularVelocity = angularVelocity;
    }
    public Vector3 CargoAcceleration(Vector3 point, Vector3 relativeVelocity)
    {
        Vector3 offset = point - transform.position;
        return -Acceleration - Vector3.Cross(AngularAcceleration, offset)
            - Vector3.Cross(AngularVelocity, Vector3.Cross(AngularVelocity, offset))
            - 2 * Vector3.Cross(AngularVelocity, relativeVelocity);
    }
    public void FollowRoute(Vector3 position, Quaternion rotation, float speed)
    {
        float angle = Mathf.DeltaAngle(transform.eulerAngles.y, rotation.eulerAngles.y) * Mathf.Deg2Rad;
        UpdateMotion(rotation * Vector3.right * speed, Vector3.up * (angle / Time.deltaTime), Time.deltaTime);
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
