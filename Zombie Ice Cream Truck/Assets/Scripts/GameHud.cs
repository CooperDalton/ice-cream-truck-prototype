using Quantum;
using UnityEngine;
using UnityEngine.UI;

// Shows the shared run state and the local survivor's hotbar, health, ammo and what pressing E would do, plus the
// hit feedback: hit/kill markers, ice cream and gore splatted across the screen, and the low-health vignette.
// Every text and image is authored in the scene; this only fills in values.
public class GameHud : MonoBehaviour
{
    [SerializeField] private SurvivorInput input;
    [SerializeField] private Text moneyText;
    [SerializeField] private Text killsText;
    [SerializeField] private Text speedText;
    [SerializeField] private Text areaText;
    [SerializeField] private Text ammoText;
    [SerializeField] private Text carriedText;
    [SerializeField] private Text promptText;
    [SerializeField] private Text phaseText;
    [SerializeField] private Image healthFill;
    [SerializeField] private Image hurtFlash;
    [SerializeField] private Text[] slotTexts;
    [SerializeField] private Image[] slotFrames;
    [SerializeField] private Color selectedColor = new Color(1f, 0.31f, 0.64f, 0.85f);
    [SerializeField] private Color slotColor = new Color(0.1f, 0.06f, 0.2f, 0.7f);
    [SerializeField] private Image hitMarker;
    [SerializeField] private Image[] screenSplats;
    [SerializeField] private Image vignette;
    [SerializeField] private float splatTime = 2.5f;
    private float hitAge = 10f;
    private float hitScale = 1f;
    private float[] splatAge;
    private int nextSplat;
    private int lastMoney;
    private float moneyPunch;
    private float promptShownAt;

    private void OnEnable()
    {
        QuantumEvent.Subscribe(this, (EventSurvivorHurt e) => OnHurt(e));
        splatAge = new float[screenSplats.Length];
        for (int i = 0; i < splatAge.Length; i++) splatAge[i] = splatTime;
    }

    public void HitMarker(bool headshot, bool kill)
    {
        hitAge = 0;
        hitScale = kill ? 1.8f : headshot ? 1.4f : 1f;
        hitMarker.color = kill ? new Color(1f, 0.2f, 0.35f) : headshot ? new Color(1f, 0.88f, 0.29f) : Color.white;
    }

    // Splats a blob of ice cream or zombie across the screen; it slides down and fades.
    public void Splat(Color color)
    {
        var splat = screenSplats[nextSplat];
        splatAge[nextSplat] = 0;
        nextSplat = (nextSplat + 1) % screenSplats.Length;
        var rect = splat.rectTransform;
        rect.anchoredPosition = new Vector2(Random.Range(-480f, 480f), Random.Range(-220f, 240f));
        rect.localRotation = Quaternion.Euler(0, 0, Random.Range(0f, 360f));
        rect.localScale = Vector3.one * Random.Range(0.8f, 1.6f);
        color.a = 0.92f;
        splat.color = color;
    }

    private void OnHurt(EventSurvivorHurt e)
    {
        if (!QuantumRunner.Default.Game.PlayerIsLocal(e.Player)) return;
        hurtFlash.color = new Color(1, 0, 0.2f, 0.45f);
    }

    private unsafe void Update()
    {
        var dt = Time.deltaTime;
        hurtFlash.color = Color.Lerp(hurtFlash.color, Color.clear, 1 - Mathf.Exp(-4 * dt));
        hitAge += dt;
        var hit = Mathf.Clamp01(1 - hitAge / 0.25f);
        hitMarker.rectTransform.localScale = Vector3.one * hitScale * (1 + 0.6f * hit);
        var markerColor = hitMarker.color;
        markerColor.a = hit;
        hitMarker.color = markerColor;
        for (int i = 0; i < screenSplats.Length; i++)
        {
            splatAge[i] += dt;
            var splat = screenSplats[i];
            var fade = Mathf.Clamp01(1 - splatAge[i] / splatTime);
            var color = splat.color;
            color.a = 0.92f * Mathf.Clamp01(fade * 2);
            splat.color = color;
            splat.rectTransform.anchoredPosition += Vector2.down * 25f * dt * (1 - fade + 0.2f);
        }
        var game = QuantumRunner.Default?.Game;
        if (game?.Frames.Predicted == null) return;
        var frame = game.Frames.Predicted;
        var settings = frame.FindAsset(frame.RuntimeConfig.Settings);
        var truck = frame.GetSingleton<Truck>();
        moneyText.text = "$" + frame.Global->Money;
        if (frame.Global->Money > lastMoney) moneyPunch = 1;
        lastMoney = frame.Global->Money;
        moneyPunch = Mathf.MoveTowards(moneyPunch, 0, dt * 4);
        moneyText.rectTransform.localScale = Vector3.one * (1 + 0.35f * moneyPunch);
        killsText.text = frame.Global->Kills + " KILLS";
        speedText.text = Mathf.RoundToInt(Mathf.Abs(truck.Speed.AsFloat) * 2.237f) + " MPH";
        areaText.text = "AREA " + frame.Global->Area;
        phaseText.text = frame.Global->Phase == GamePhase.Depot ? "DEPOT - buy upgrades, then hit the exit sign to roll out"
            : frame.Global->Phase == GamePhase.Wiped ? "EVERYONE'S DEAD - back to area 1" : "";
        if (!input.LocalEntity.IsValid) return;

        var survivor = frame.Get<Survivor>(input.LocalEntity);
        var health = (survivor.Health / settings.MaxHealth).AsFloat;
        healthFill.fillAmount = health;
        // Below a third of health the screen edges throb red.
        var danger = survivor.Dead ? 0 : Mathf.Clamp01((0.35f - health) / 0.35f);
        vignette.color = new Color(0.7f, 0f, 0.1f, danger * (0.55f + 0.25f * Mathf.Sin(Time.time * 6f)));
        for (int i = 0; i < slotTexts.Length; i++)
        {
            var item = survivor.Hotbar[i];
            slotTexts[i].text = (i + 1) + "\n" + Label(item);
            slotFrames[i].color = i == survivor.Selected ? selectedColor : slotColor;
        }
        carriedText.text = survivor.Carried.Kind == ItemKind.None ? "" : "CARRYING " + Label(survivor.Carried) + "   Q drop / hold Q throw";
        var held = survivor.Hotbar[survivor.Selected];
        var gun = Inventory.Gun(held.Kind);
        ammoText.text = survivor.TurretSeat > 0 ? "HOPPER " + truck.HopperRounds + " " + truck.HopperFlavor.ToString().ToUpper()
            : gun.Pellets > 0 && !gun.Harpoon ? held.Count + " " + held.Flavor.ToString().ToUpper() + (held.Count == 0 ? "   R reload" : "")
            : "";
        var prompt = survivor.Dead ? "YOU DIED - a teammate can revive you with a Second Scoop" : Prompt(frame, survivor, input.LocalEntity, settings);
        if (prompt != promptText.text) promptShownAt = Time.time;
        promptText.text = prompt;
        // Seat and turret controls get out of the way of the windshield once they have been read.
        promptText.enabled = !(survivor.Driving || survivor.TurretSeat > 0) || Time.time - promptShownAt < 4f;
    }

    private static unsafe string Prompt(Frame frame, Survivor survivor, EntityRef entity, ZombieTruckSettings settings)
    {
        if (survivor.Driving) return "W/S drive  A/D steer  E leave the seat";
        if (survivor.TurretSeat > 0) return "CLICK fire the minigun  E leave the turret";
        var target = survivor.LookTarget;
        if (target.IsValid && frame.TryGet(target, out Pickup pickup)) return "E  pick up " + Label(pickup.Item);
        if (target.IsValid && frame.TryGet(target, out Station station)) return StationPrompt(frame, station);

        var truck = frame.Get<Transform3D>(frame.GetSingletonEntityRef<Truck>());
        var local = truck.InverseTransformPoint(frame.Get<Transform3D>(entity).Position);
        // Same nearest-spot rule as SurvivorSystem.Interact.
        var nearest = settings.InteractRange * settings.InteractRange;
        var prompt = "";
        var canDrive = !frame.GetSingleton<Truck>().Driver.IsValid && survivor.Carried.Kind == ItemKind.None;
        var spots = new[] { (settings.LadderBottom, "E  climb to the roof"), (settings.HatchTop, "E  climb down into the kitchen"),
            (settings.RearOutside, "E  get in the truck"), (settings.RearInside, "E  get out the back"), (settings.DriverSeat, canDrive ? "E  drive" : "") };
        foreach (var (spot, text) in spots)
        {
            var distance = (local - spot).SqrMagnitude;
            if (distance >= nearest || text == "") continue;
            nearest = distance;
            prompt = text;
        }
        return prompt;
    }

    private static unsafe string StationPrompt(Frame frame, Station station)
    {
        switch (station.Kind)
        {
            case StationKind.Churn:
                var flavor = station.Flavoring == Flavor.None ? "vanilla" : station.Flavoring.ToString().ToLower();
                return $"CHURN  milk {station.Milk}  sugar {station.Sugar}  ({flavor})\nE add ingredient   HOLD CLICK + move mouse to crank";
            case StationKind.Freezer:
                var tubs = "";
                for (int i = 0; i < station.Slots.Length; i++)
                {
                    var tub = station.Slots[i];
                    tubs += tub.Kind == ItemKind.None ? "[empty] " : $"[{tub.Flavor} {tub.Count}] ";
                }
                return "FREEZER " + tubs + "\nE put a tub in   HOLD CLICK with the scooper to scoop";
            case StationKind.Counter:
                var pints = "";
                for (int i = 0; i < station.Slots.Length; i++)
                {
                    var pint = station.Slots[i];
                    pints += pint.Kind == ItemKind.None ? "[empty] " : $"[{pint.Flavor} {pint.Count}/4] ";
                }
                return "PINTS " + pints + "\nCLICK with scoops to fill   E take the fullest pint";
            case StationKind.GunRack: return "GUN RACK  E store the held gun / take a gun";
            case StationKind.Hopper: return "MINIGUN HOPPER  E load the held pint";
            case StationKind.Bell: return "E  ring the bell (MORE AMMO!)";
            case StationKind.Turret: return "E  man the minigun";
            case StationKind.GunCrate: return station.Open ? "empty crate" : "E  crack open the gun crate";
            case StationKind.Shop: return $"E  buy {station.Upgrade} for ${station.Price}";
            case StationKind.DepotExit: return frame.Global->Phase == GamePhase.Depot ? "E  roll out to the next area" : "";
            default: return "";
        }
    }

    public static string Label(Item item)
    {
        switch (item.Kind)
        {
            case ItemKind.None: return "";
            case ItemKind.Pint: return $"{item.Flavor} pint {item.Count}/4";
            case ItemKind.Scoop: return $"{item.Flavor} scoop x{item.Count}";
            case ItemKind.Tub: return $"{item.Flavor} tub";
            case ItemKind.ScoopPistol:
            case ItemKind.SundaeShotgun:
            case ItemKind.LongSpoon:
            case ItemKind.ConeLauncher:
            case ItemKind.SprinkleSMG:
                return $"{item.Kind} {item.Count}";
            default: return item.Kind.ToString();
        }
    }
}
