using System;
using Quantum;
using UnityEngine;
using Random = UnityEngine.Random;

// Turns simulation events into one-shot effects: tracers, muzzle flashes and smoke, sprinkle casings, flavor splats,
// kill bursts with gibs and flying limbs, head pops, flavor explosions, ground splats, truck crashes, popups, screen
// shake and screen gore. Every effect is an authored prefab; this only places, tints and times them.
public class CombatEffects : MonoBehaviour
{
    [Serializable]
    public struct MuzzleFlash
    {
        public ItemKind Gun;
        public GameObject Prefab;
        public float Kick;
    }

    [SerializeField] private QuantumEntityViewUpdater viewUpdater;
    [SerializeField] private FirstPersonCamera cameraRig;
    [SerializeField] private GameHud hud;
    [SerializeField] private LineRenderer tracerPrefab;
    [SerializeField] private MuzzleFlash[] muzzleFlashes;
    [SerializeField] private FxBurst hitBurst;
    [SerializeField] private FxBurst killBurst;
    [SerializeField] private FxBurst headshotBurst;
    [SerializeField] private FxBurst shatterBurst;
    [Tooltip("Indexed by Flavor (None = plain scoop grenade).")]
    [SerializeField] private FxBurst[] explosionBursts;
    [SerializeField] private FxBurst bloaterBurst;
    [SerializeField] private FxBurst crashBurst;
    [SerializeField] private FxBurst confettiBurst;
    [SerializeField] private GameObject[] gibPrefabs;
    [Tooltip("Persistent world-space system the ground splats are emitted into.")]
    [SerializeField] private ParticleSystem groundSplats;
    [Tooltip("Persistent world-space system for casings and muzzle smoke.")]
    [SerializeField] private ParticleSystem casings;
    [SerializeField] private ParticleSystem smoke;
    [SerializeField] private Popup popupPrefab;
    [SerializeField] private float tracerLifetime = 0.06f;
    [SerializeField] private float screenGoreRange = 3f;

    private static readonly Color Gold = new Color(1f, 0.85f, 0.2f);
    private static readonly Color Pink = new Color(1f, 0.31f, 0.64f);
    private static readonly Color Mint = new Color(0.22f, 0.95f, 0.76f);

    private void OnEnable()
    {
        QuantumEvent.Subscribe(this, (EventShotFired e) => OnShot(e));
        QuantumEvent.Subscribe(this, (EventZombieHit e) => OnHit(e));
        QuantumEvent.Subscribe(this, (EventZombieKilled e) => OnKilled(e));
        QuantumEvent.Subscribe(this, (EventExplosion e) => OnExplosion(e));
        QuantumEvent.Subscribe(this, (EventTruckCrashed e) => OnCrash(e));
        QuantumEvent.Subscribe(this, (EventSurvivorHurt e) => OnHurt(e));
        QuantumEvent.Subscribe(this, (EventTipEarned e) => ShowPopup(e.Position.ToUnityVector3() + Vector3.up * 2.4f, "+$" + e.Amount + " TIP", Gold, 1.2f));
        QuantumEvent.Subscribe(this, (EventPurchased e) => OnPurchased(e));
        QuantumEvent.Subscribe(this, (EventSurvivorRevived e) => OnRevived(e));
        QuantumEvent.Subscribe(this, (EventStationUsed e) => OnStationUsed(e));
    }

    private static bool IsLocal(PlayerRef player)
    {
        return QuantumRunner.Default.Game.PlayerIsLocal(player);
    }

    private void OnShot(EventShotFired e)
    {
        var from = e.From.ToUnityVector3();
        var to = e.To.ToUnityVector3();
        var direction = (to - from).normalized;
        var local = IsLocal(e.Player);
        // The local player sees shots leave the view-model muzzle instead of their eyes.
        var start = local ? cameraRig.transform.position + cameraRig.transform.rotation * new Vector3(0.2f, -0.1f, 0.75f) : from + Vector3.down * 0.2f;
        var tracer = Instantiate(tracerPrefab);
        tracer.SetPosition(0, start);
        tracer.SetPosition(1, to);
        tracer.startColor = tracer.endColor = FlavorPalette.Of(e.Flavor);
        tracer.widthMultiplier = e.Gun == ItemKind.LongSpoon ? 0.09f : 0.04f;
        Destroy(tracer.gameObject, e.Gun == ItemKind.LongSpoon ? tracerLifetime * 4 : tracerLifetime);
        foreach (var flash in muzzleFlashes)
        {
            if (flash.Gun != e.Gun) continue;
            Destroy(Instantiate(flash.Prefab, start + direction * 0.15f, Quaternion.LookRotation(direction)), 0.06f);
            if (local) cameraRig.Kick(flash.Kick);
        }
        Emit(smoke, start + direction * 0.3f, direction * 0.6f + Vector3.up * 0.4f, 0.25f, new Color(0.95f, 0.93f, 1f), 0.6f, 2);
        var side = Vector3.Cross(Vector3.up, direction).normalized;
        for (int i = 0; i < 2; i++)
        {
            var color = Color.HSVToRGB(Random.value, 0.65f, 1f);
            Emit(casings, start - direction * 0.2f, side * Random.Range(1.5f, 3f) + Vector3.up * Random.Range(1.5f, 3f), 0.12f, color, 1.5f, 1);
        }
        // Shots that hit the ground leave a little flavor splat there.
        if (to.y < 0.25f && e.Gun != ItemKind.ConeLauncher && e.Gun != ItemKind.BananaHarpoon) GroundSplat(to, FlavorPalette.Of(e.Flavor), 0.25f, 0.5f);
    }

    private void OnHit(EventZombieHit e)
    {
        var point = e.Point.ToUnityVector3();
        Instantiate(hitBurst, point, Quaternion.identity).Play(FlavorPalette.Of(e.Flavor), e.Headshot ? 1.6f : 1f);
        var view = viewUpdater.GetView(e.Zombie);
        if (view != null)
        {
            view.GetComponent<ZombieView>().Flinch(point - cameraRig.transform.position);
            GroundSplat(view.transform.position + Random.insideUnitSphere * 0.5f, FlavorPalette.Gore, 0.4f, 0.8f);
        }
        if (IsLocal(e.Player)) hud.HitMarker(e.Headshot, false);
    }

    private void OnKilled(EventZombieKilled e)
    {
        var position = e.Position.ToUnityVector3();
        var impulse = e.Impulse.ToUnityVector3();
        var view = viewUpdater.GetView(e.Zombie);
        var headPop = e.Headshot || e.RunOver;
        if (view != null) view.GetComponent<ZombieView>().Kill(headPop, impulse);

        var center = position + Vector3.up;
        var flavor = FlavorPalette.Of(e.Flavor);
        var scale = e.Kind == ZombieKind.Bloater ? 2f : e.RunOver ? 1.7f : 1.2f;
        Instantiate(killBurst, center, Quaternion.identity).Play(flavor, scale);
        if (e.Headshot)
        {
            var head = position + Vector3.up * 1.6f;
            Instantiate(headshotBurst, head, Quaternion.identity).Play(flavor, 1f);
            ShowPopup(head + Vector3.up * 0.6f, "HEADSHOT!", Pink, 1.5f);
        }
        if (e.RunOver && e.Flavor == Flavor.Mint) Instantiate(shatterBurst, center, Quaternion.identity).Play(Mint, 1.5f);
        if (e.RunOver) ShowPopup(position + Vector3.up * 2.4f, Random.value < 0.5f ? "SPLAT!" : "ROADKILL!", Mint, 1.3f);
        if (e.Reward > 0) ShowPopup(position + Vector3.up * (e.Headshot ? 1.9f : 2f), "+$" + e.Reward, Gold, 1f);

        foreach (var prefab in gibPrefabs)
        {
            var gib = Instantiate(prefab, center + Random.insideUnitSphere * 0.4f, Random.rotation);
            var body = gib.GetComponent<Rigidbody>();
            body.linearVelocity = impulse * 0.5f + Random.insideUnitSphere * 6f + Vector3.up * 4f;
            body.angularVelocity = Random.insideUnitSphere * 15f;
            Destroy(gib, 4f);
        }
        // A spray of splats on the road, thrown the way the body went.
        var spray = new Vector3(impulse.x, 0, impulse.z) * 0.15f;
        for (int i = 0; i < 6; i++)
        {
            var offset = Random.insideUnitSphere * 1.2f + spray * Random.value;
            GroundSplat(position + offset, i % 2 == 0 ? FlavorPalette.Gore : flavor, 0.6f, 1.5f);
        }

        var distance = Vector3.Distance(cameraRig.transform.position, center);
        cameraRig.AddTrauma(Mathf.Clamp01(1 - distance / 10f) * (e.RunOver ? 0.35f : 0.15f));
        if (distance < screenGoreRange) hud.Splat(Random.value < 0.6f ? FlavorPalette.Gore : flavor);
        if (IsLocal(e.Player)) hud.HitMarker(e.Headshot, true);
    }

    private void OnExplosion(EventExplosion e)
    {
        var position = e.Position.ToUnityVector3();
        var radius = e.Radius.AsFloat;
        var burst = e.Bloater ? bloaterBurst : explosionBursts[(int)e.Flavor];
        var color = e.Bloater ? FlavorPalette.Gore : FlavorPalette.Of(e.Flavor);
        Instantiate(burst, position, Quaternion.identity).Play(color, radius / 2.5f);
        for (int i = 0; i < 10; i++)
        {
            var offset = Random.insideUnitCircle * radius;
            GroundSplat(new Vector3(position.x + offset.x, 0, position.z + offset.y), color, 0.6f, 1.8f);
        }
        var distance = Vector3.Distance(cameraRig.transform.position, position);
        cameraRig.AddTrauma(Mathf.Clamp01(1 - distance / (radius * 6)) * (e.Bloater ? 0.9f : 0.6f));
        if (distance < radius * 1.3f)
        {
            hud.Splat(color);
            hud.Splat(e.Bloater ? FlavorPalette.Gore : color);
        }
    }

    private void OnCrash(EventTruckCrashed e)
    {
        var position = e.Position.ToUnityVector3();
        var speed = Mathf.Abs(e.Speed.AsFloat);
        Instantiate(crashBurst, position, Quaternion.identity).Play(Color.white, Mathf.Clamp(speed / 10f, 0.6f, 2f));
        var distance = Vector3.Distance(cameraRig.transform.position, position);
        cameraRig.AddTrauma(Mathf.Clamp01(1 - distance / 15f) * Mathf.Clamp01(speed / 15f));
        ShowPopup(position + Vector3.up * 2.5f, "CRASH!", Color.white, 1.4f);
    }

    private void OnHurt(EventSurvivorHurt e)
    {
        if (!IsLocal(e.Player)) return;
        cameraRig.AddTrauma(0.4f);
        hud.Splat(FlavorPalette.Gore);
    }

    private void OnPurchased(EventPurchased e)
    {
        var position = e.Position.ToUnityVector3();
        Instantiate(confettiBurst, position + Vector3.up * 1.5f, Quaternion.identity).Play(Gold, 1f);
        ShowPopup(position + Vector3.up * 2.8f, UpgradeName(e.Upgrade) + "!", Mint, 1.4f);
    }

    private void OnRevived(EventSurvivorRevived e)
    {
        foreach (var pair in QuantumRunner.Default.Game.Frames.Predicted.GetComponentIterator<PlayerLink>())
        {
            if (pair.Component.Player != e.Player) continue;
            var view = viewUpdater.GetView(pair.Entity);
            Instantiate(confettiBurst, view.transform.position + Vector3.up, Quaternion.identity).Play(Mint, 1f);
            ShowPopup(view.transform.position + Vector3.up * 2.4f, "SECOND SCOOP!", Mint, 1.4f);
        }
    }

    private void OnStationUsed(EventStationUsed e)
    {
        if (e.Kind != StationKind.Bell) return;
        var position = viewUpdater.GetView(e.Station).transform.position;
        ShowPopup(position + Vector3.up * 1.8f, "YO! MORE AMMO!", Gold, 1.6f);
    }

    private static string UpgradeName(UpgradeKind upgrade)
    {
        switch (upgrade)
        {
            case UpgradeKind.Plow: return "PLOW";
            case UpgradeKind.Spikes: return "SIDE SPIKES";
            case UpgradeKind.Armor: return "WINDOW ARMOR";
            case UpgradeKind.Turret: return "SOFT SERVE MINIGUN";
            case UpgradeKind.SecondTurret: return "SECOND MINIGUN";
            case UpgradeKind.BigHopper: return "BIG HOPPER";
            case UpgradeKind.Engine: return "BIG ENGINE";
            case UpgradeKind.SecondScoop: return "SECOND SCOOP";
            default: return upgrade.ToString().ToUpper();
        }
    }

    private void GroundSplat(Vector3 position, Color color, float minSize, float maxSize)
    {
        // Splats only stick to the road; ones on the moving truck's roof would be left floating in the air.
        if (position.y > 0.5f) return;
        var emit = new ParticleSystem.EmitParams
        {
            position = new Vector3(position.x, Mathf.Max(position.y, 0f) + 0.03f + Random.value * 0.01f, position.z),
            startColor = color,
            startSize = Random.Range(minSize, maxSize),
            rotation = Random.Range(0f, 360f),
            velocity = Vector3.zero,
            applyShapeToPosition = false,
        };
        groundSplats.Emit(emit, 1);
    }

    private static void Emit(ParticleSystem system, Vector3 position, Vector3 velocity, float size, Color color, float lifetime, int count)
    {
        var emit = new ParticleSystem.EmitParams
        {
            position = position,
            velocity = velocity,
            startSize = size,
            startColor = color,
            startLifetime = lifetime,
            applyShapeToPosition = false,
        };
        system.Emit(emit, count);
    }

    private void ShowPopup(Vector3 position, string message, Color color, float size)
    {
        Instantiate(popupPrefab, position, Quaternion.identity).Show(message, color, size);
    }
}
