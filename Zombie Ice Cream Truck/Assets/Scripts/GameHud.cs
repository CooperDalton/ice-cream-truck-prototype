using System;
using Quantum;
using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.UI;

// Shows the shared run state (money, kills, area, speed and the ice cream in the fuel tank) and the local survivor's
// hotbar (item icons and counts), health, ammo and what pressing E would do, plus the hit feedback: hit/kill markers, ice cream and gore splatted across the screen, and the low-health
// vignette. Every text, image and panel is authored in the scene; this only fills in values, swaps icons and shows or
// hides panels. The controls panel shows for the first 30 s; F1 toggles it.
public class GameHud : MonoBehaviour
{
    [Serializable]
    public struct ItemIcon
    {
        public ItemKind Kind;
        public Flavor Flavor;
        public Sprite Sprite;
    }

    private const string Key = "<color=#ffe14a>";
    private const string End = "</color>";
    // Display names indexed by Flavor.
    public static readonly string[] FlavorNames = { "", "Vanilla", "Chocolate", "Strawberry", "Mint", "Coffee", "Rocky Road", "Neapolitan" };

    [SerializeField] private SurvivorInput input;
    [SerializeField] private ItemIcon[] icons;
    [SerializeField] private Sprite minigunIcon;
    [SerializeField] private Text moneyText;
    [SerializeField] private Text killsText;
    [SerializeField] private Text speedText;
    [SerializeField] private Text areaText;
    [SerializeField] private Image fuelIcon;
    [SerializeField] private Image fuelFill;
    [SerializeField] private Text fuelText;
    [SerializeField] private float hordeAlertTime = 3.5f;
    [Tooltip("Banner text for each TutorialStep, in order; the banner fits about 46 characters after the step count.")]
    [SerializeField] private string[] tutorialSteps =
    {
        "Open the back door (E), grab the milk crate",
        "Carry it inside and put it in the churn (E)",
        "Fetch the sugar sack from behind the truck",
        "Put the sugar in the churn too (E)",
        "Hold CLICK on the churn and stir the mouse",
        "Grab the new tub (E), put it in the freezer",
        "CLICK the freezer to grab a stack of scoops",
        "Fuel the truck: scoops into the cab intake (E)",
        "Zombie! Get out, bonk it with the cone (3)",
        "Take the driver's seat to start the run!",
    };
    [SerializeField] private GameObject ammoPanel;
    [SerializeField] private Image ammoIcon;
    [SerializeField] private Text ammoText;
    [SerializeField] private Text ammoLabel;
    [SerializeField] private GameObject promptPanel;
    [SerializeField] private Text promptText;
    [SerializeField] private GameObject phaseBanner;
    [SerializeField] private Text phaseText;
    [SerializeField] private GameObject controlsPanel;
    [SerializeField] private float controlsShowTime = 30f;
    [SerializeField] private Image healthFill;
    [SerializeField] private Text healthText;
    [SerializeField] private Image hurtFlash;
    [SerializeField] private Image[] slotIcons;
    [SerializeField] private Text[] slotCounts;
    [SerializeField] private GameObject[] slotSelected;
    [SerializeField] private Text selectedName;
    [SerializeField] private float nameShowTime = 1.6f;
    [SerializeField] private Image hitMarker;
    [SerializeField] private Image[] screenSplats;
    [SerializeField] private Image vignette;
    [SerializeField] private float splatTime = 2.5f;
    [SerializeField] private Color emptyAmmoColor = new Color(1f, 0.31f, 0.64f);
    private float hitAge = 10f;
    private float hitScale = 1f;
    private float[] splatAge;
    private int nextSplat;
    private int lastMoney;
    private float moneyPunch;
    private float promptShownAt;
    private int lastSelected = -1;
    private ItemKind lastSelectedKind;
    private float selectedShownAt;
    private bool controlsToggled;
    private string hordeAlert = "";
    private float hordeAlertAt = -100f;

    private void OnEnable()
    {
        QuantumEvent.Subscribe(this, (EventSurvivorHurt e) => OnHurt(e));
        QuantumEvent.Subscribe(this, (EventHordeReleased e) => OnHorde(e));
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
        rect.anchoredPosition = new Vector2(UnityEngine.Random.Range(-480f, 480f), UnityEngine.Random.Range(-220f, 240f));
        rect.localRotation = Quaternion.Euler(0, 0, UnityEngine.Random.Range(0f, 360f));
        rect.localScale = Vector3.one * UnityEngine.Random.Range(0.8f, 1.6f);
        color.a = 0.92f;
        splat.color = color;
    }

    private void OnHorde(EventHordeReleased e)
    {
        hordeAlertAt = Time.time;
        hordeAlert = e.Chunk == ChunkKind.School ? "HORDE!  Sprinkle Hills Elementary is letting out"
            : e.Chunk == ChunkKind.Park ? "HORDE!  Cherry Swirl Park is crawling with them"
            : "HORDE!  Sundae Funday Fair is open for business";
    }

    private void OnHurt(EventSurvivorHurt e)
    {
        if (!QuantumRunner.Default.Game.PlayerIsLocal(e.Player)) return;
        hurtFlash.color = new Color(1, 0, 0.2f, 0.45f);
    }

    private unsafe void Update()
    {
        var dt = Time.deltaTime;
        if (Keyboard.current.f1Key.wasPressedThisFrame)
        {
            controlsPanel.SetActive(!controlsPanel.activeSelf);
            controlsToggled = true;
        }
        // The controls panel shows for the first stretch of the session unless F1 was used.
        if (!controlsToggled && Time.timeSinceLevelLoad > controlsShowTime) controlsPanel.SetActive(false);
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
        killsText.text = frame.Global->Kills.ToString();
        speedText.text = Mathf.RoundToInt(Mathf.Abs(truck.Speed.AsFloat) * 2.237f) + " MPH";
        areaText.text = "AREA " + frame.Global->Area;
        var tank = settings.FuelCapacity + (truck.BigTank ? settings.BigTankBonus : 0);
        fuelFill.fillAmount = (truck.Fuel / tank).AsFloat;
        fuelFill.color = FlavorPalette.Of(truck.FuelFlavor);
        fuelIcon.sprite = Icon(new Item { Kind = ItemKind.Tub, Flavor = truck.FuelFlavor });
        var empty = truck.Fuel <= 0;
        fuelText.text = empty ? "EMPTY" : Mathf.CeilToInt(truck.Fuel.AsFloat).ToString();
        fuelText.color = empty && Time.time % 0.6f < 0.3f ? emptyAmmoColor : Color.white;
        phaseText.text = frame.Global->Phase == GamePhase.Tutorial ? $"TUTORIAL {(int)frame.Global->Tutorial + 1}/{tutorialSteps.Length}:  {tutorialSteps[(int)frame.Global->Tutorial]}"
            : frame.Global->Phase == GamePhase.Depot ? "KEVIN'S DEPOT!  Shop, gamble, then hit the exit sign to roll out"
            : frame.Global->Phase == GamePhase.Wiped ? "EVERYONE'S DEAD  -  back to area 1"
            : Time.time - hordeAlertAt < hordeAlertTime ? hordeAlert
            : empty ? "OUT OF ICE CREAM!  Feed a tub, pint or scoops into the fuel intake in the cab" : "";
        phaseBanner.SetActive(phaseText.text != "");
        if (!input.LocalEntity.IsValid) return;

        var survivor = frame.Get<Survivor>(input.LocalEntity);
        var health = (survivor.Health / settings.MaxHealth).AsFloat;
        healthFill.fillAmount = health;
        healthText.text = Mathf.CeilToInt(survivor.Health.AsFloat).ToString();
        // Below a third of health the screen edges throb red.
        var danger = survivor.Dead ? 0 : Mathf.Clamp01((0.35f - health) / 0.35f);
        vignette.color = new Color(0.7f, 0f, 0.1f, danger * (0.55f + 0.25f * Mathf.Sin(Time.time * 6f)));

        for (int i = 0; i < slotIcons.Length; i++)
        {
            var item = survivor.Hotbar[i];
            slotIcons[i].enabled = item.Kind != ItemKind.None;
            if (slotIcons[i].enabled) slotIcons[i].sprite = Icon(item);
            slotCounts[i].text = Count(item);
            slotSelected[i].SetActive(i == survivor.Selected);
        }
        var held = survivor.Hotbar[survivor.Selected];
        if (survivor.Selected != lastSelected || held.Kind != lastSelectedKind) selectedShownAt = Time.time;
        lastSelected = survivor.Selected;
        lastSelectedKind = held.Kind;
        selectedName.text = Name(held);
        var nameColor = selectedName.color;
        nameColor.a = Mathf.Clamp01(1 - (Time.time - selectedShownAt - nameShowTime) / 0.4f);
        selectedName.color = nameColor;

        var gun = Inventory.Gun(held.Kind);
        var turret = survivor.TurretSeat > 0;
        ammoPanel.SetActive(turret || (gun.Pellets > 0 && !gun.Harpoon));
        var refill = gun.Melee ? $"{Key}R{End} ADD A SCOOP" : $"{Key}R{End} RELOAD";
        if (turret)
        {
            ammoIcon.sprite = minigunIcon;
            ammoText.text = truck.HopperRounds.ToString();
            ammoText.color = truck.HopperRounds == 0 ? emptyAmmoColor : Color.white;
            ammoLabel.text = "HOPPER  " + truck.HopperFlavor.ToString().ToUpper();
        }
        else if (ammoPanel.activeSelf)
        {
            ammoIcon.sprite = Icon(new Item { Kind = ItemKind.Scoop, Flavor = held.Flavor });
            ammoText.text = held.Count.ToString();
            ammoText.color = held.Count == 0 ? emptyAmmoColor : Color.white;
            ammoLabel.text = held.Count == 0 ? refill : FlavorNames[(int)held.Flavor].ToUpper() + (gun.Melee ? " BITES" : "");
        }

        var prompt = survivor.Dead ? "YOU DIED\nA teammate can revive you with a Second Scoop" : Prompt(frame, survivor, input.LocalEntity, settings);
        if (prompt != promptText.text) promptShownAt = Time.time;
        promptText.text = prompt;
        // Seat and turret controls get out of the way of the windshield once they have been read.
        promptPanel.SetActive(prompt != "" && (!(survivor.Driving || turret) || Time.time - promptShownAt < 4f));
    }

    private Sprite Icon(Item item)
    {
        var flavor = item.Flavor == Flavor.None ? Flavor.Vanilla : item.Flavor;
        foreach (var icon in icons)
        {
            if (icon.Kind == item.Kind && (icon.Flavor == Flavor.None || icon.Flavor == flavor)) return icon.Sprite;
        }
        throw new InvalidOperationException($"GameHud has no icon for {item.Kind} {item.Flavor}");
    }

    private static string Count(Item item)
    {
        switch (item.Kind)
        {
            case ItemKind.Pint: return item.Count + "/4";
            case ItemKind.Scoop: return "x" + item.Count;
            case ItemKind.MilkCrate:
            case ItemKind.SugarSack:
            case ItemKind.CocoaBag:
            case ItemKind.StrawberryBasket:
            case ItemKind.MintBundle:
            case ItemKind.CoffeeSack:
            case ItemKind.NutBag:
                return item.Count > 1 ? "x" + item.Count : "";
            case ItemKind.ScoopPistol:
            case ItemKind.SundaeShotgun:
            case ItemKind.SprinkleSMG:
            case ItemKind.LongSpoon:
            case ItemKind.ConeLauncher:
            case ItemKind.SoftServeHose:
            case ItemKind.SundaeBazooka:
            case ItemKind.JackpotBlaster:
            case ItemKind.PlainCone:
            case ItemKind.WaffleCone:
            case ItemKind.DoubleDip:
                return item.Count.ToString();
            default: return "";
        }
    }

    public static string Name(Item item)
    {
        switch (item.Kind)
        {
            case ItemKind.None: return "";
            case ItemKind.ScoopPistol: return "Scoop Pistol";
            case ItemKind.SundaeShotgun: return "Sundae Shotgun";
            case ItemKind.SprinkleSMG: return "Sprinkle SMG";
            case ItemKind.LongSpoon: return "Long Spoon";
            case ItemKind.ConeLauncher: return "Cone Launcher";
            case ItemKind.BananaHarpoon: return "Banana Harpoon";
            case ItemKind.SoftServeHose: return "Soft Serve Hose";
            case ItemKind.SundaeBazooka: return "Sundae Bazooka";
            case ItemKind.JackpotBlaster: return "Jackpot Blaster";
            case ItemKind.PlainCone: return item.Count > 0 ? $"{FlavorNames[(int)item.Flavor]} Cone" : "Empty Cone";
            case ItemKind.WaffleCone: return item.Count > 0 ? $"{FlavorNames[(int)item.Flavor]} Waffle Cone" : "Empty Waffle Cone";
            case ItemKind.DoubleDip: return item.Count > 0 ? $"{FlavorNames[(int)item.Flavor]} Double Dip" : "Empty Double Dip";
            case ItemKind.SprinkleJar: return "Sprinkle Jar";
            case ItemKind.SecondScoop: return "Second Scoop";
            case ItemKind.MilkCrate: return "Milk Crate";
            case ItemKind.SugarSack: return "Sugar Sack";
            case ItemKind.CocoaBag: return "Cocoa Bag";
            case ItemKind.StrawberryBasket: return "Strawberry Basket";
            case ItemKind.MintBundle: return "Mint Bundle";
            case ItemKind.CoffeeSack: return "Coffee Sack";
            case ItemKind.NutBag: return "Rocky Road Mix";
            case ItemKind.Pint: return $"{FlavorNames[(int)item.Flavor]} Pint  {item.Count}/4";
            case ItemKind.Scoop: return $"{FlavorNames[(int)item.Flavor]} Scoop  x{item.Count}";
            case ItemKind.Tub: return $"{FlavorNames[(int)item.Flavor]} Tub";
            default: return item.Kind.ToString();
        }
    }

    private static unsafe string Prompt(Frame frame, Survivor survivor, EntityRef entity, ZombieTruckSettings settings)
    {
        if (survivor.Driving)
        {
            var musicOff = frame.GetSingleton<Truck>().MusicOff;
            return $"{Key}W/S{End} drive   {Key}A/D{End} steer   {Key}RIGHT CLICK{End} music {(musicOff ? "on" : "off")}   {Key}E{End} leave the seat";
        }
        if (survivor.TurretSeat > 0) return $"{Key}CLICK{End} fire the minigun   {Key}E{End} leave the turret";
        var target = survivor.LookTarget;
        if (target.IsValid && frame.TryGet(target, out Pickup pickup)) return $"{Key}E{End}  pick up {Name(pickup.Item)}";
        // Same rule as SurvivorSystem.Interact: truck stations only work from inside or on top of the truck, except the
        // rear door.
        var outside = survivor.Standing != frame.GetSingletonEntityRef<Truck>();
        if (target.IsValid && frame.TryGet(target, out Station station) && !(outside && frame.Has<Attached>(target) && station.Kind != StationKind.RearDoor))
        {
            return StationPrompt(frame, station);
        }
        if (survivor.Climbing) return $"{Key}W/S{End} climb   {Key}SPACE{End} let go";

        var truck = frame.Get<Transform3D>(frame.GetSingletonEntityRef<Truck>());
        var local = truck.InverseTransformPoint(frame.Get<Transform3D>(entity).Position);
        // Same nearest-spot rule as SurvivorSystem.Interact.
        var nearest = float.MaxValue;
        var prompt = "";
        var canDrive = !frame.GetSingleton<Truck>().Driver.IsValid;
        var hatchOpen = false;
        foreach (var pair in frame.GetComponentIterator<Station>()) hatchOpen |= pair.Component.Kind == StationKind.Hatch && pair.Component.Open;
        var spots = new[] { (settings.LadderBottom, settings.LadderRange, "grab the ladder"),
            (settings.HatchTop, settings.InteractRange, hatchOpen ? "climb down the ladder" : ""),
            (settings.DriverSeat, settings.InteractRange, !canDrive ? "" : frame.Global->Phase == GamePhase.Tutorial ? "drive (starts the run)" : "drive") };
        foreach (var (spot, range, text) in spots)
        {
            var distance = (local - spot).SqrMagnitude.AsFloat;
            if (distance >= nearest || distance >= (range * range).AsFloat || text == "") continue;
            nearest = distance;
            prompt = $"{Key}E{End}  {text}";
        }
        return prompt;
    }

    private static unsafe string StationPrompt(Frame frame, Station station)
    {
        switch (station.Kind)
        {
            case StationKind.Churn:
                var flavor = station.Flavoring == Flavor.None ? "vanilla" : FlavorNames[(int)station.Flavoring].ToLower();
                return $"CHURN   milk {station.Milk}   sugar {station.Sugar}   ({flavor})\n{Key}E{End} add ingredient   {Key}HOLD CLICK{End} + move mouse to crank";
            case StationKind.Freezer:
                var tubs = "";
                for (int i = 0; i < station.Slots.Length; i++)
                {
                    var tub = station.Slots[i];
                    tubs += tub.Kind == ItemKind.None ? "[empty]  " : $"[{FlavorNames[(int)tub.Flavor]} {tub.Count}]  ";
                }
                return $"FREEZER   {tubs}\n{Key}CLICK{End}/{Key}E{End} grab scoops   {Key}E{End} on scoops or a tub: put back";
            case StationKind.Counter:
                var pints = "";
                for (int i = 0; i < station.Slots.Length; i++)
                {
                    var pint = station.Slots[i];
                    pints += pint.Kind == ItemKind.None ? "[empty]  " : $"[{FlavorNames[(int)pint.Flavor]} {pint.Count}/4]  ";
                }
                return $"PINTS   {pints}\n{Key}CLICK{End} with scoops to fill   {Key}E{End} take the fullest pint";
            case StationKind.GunRack: return $"GUN RACK\n{Key}E{End} store the held gun / take a gun";
            case StationKind.Hopper: return $"MINIGUN HOPPER\n{Key}E{End} load the held pint";
            case StationKind.Bell: return $"{Key}E{End}  ring the bell (MORE AMMO!)";
            case StationKind.Turret: return $"{Key}E{End}  man the minigun";
            case StationKind.GunCrate: return station.Open ? "empty crate" : $"{Key}E{End}  crack open the gun crate";
            case StationKind.Shop:
                if (station.Upgrade != UpgradeKind.None) return $"{Key}E{End}  buy {station.Upgrade} for ${station.Price}";
                return station.Slots[0].Kind == ItemKind.None ? "SOLD OUT" : $"{Key}E{End}  buy {Name(station.Slots[0])} for ${station.Price}";
            case StationKind.FuelIntake:
                return $"FUEL INTAKE  (any flavor; coffee runs hot)\n{Key}E{End} pour in a tub, or the held pint or scoops";
            case StationKind.SlotMachine:
                return station.Timer > 0 ? "spinning..." : $"SCOOP SLOTS\n{Key}E{End}  pull for ${station.Price}   (3 of a kind: JACKPOT)";
            case StationKind.Shopkeeper: return $"{Key}E{End}  talk to Kevin";
            case StationKind.RearDoor: return $"{Key}E{End}  {(station.Open ? "close" : "open")} the back door";
            case StationKind.Hatch: return $"{Key}E{End}  {(station.Open ? "close" : "open")} the hatch";
            case StationKind.DepotExit: return frame.Global->Phase == GamePhase.Depot ? $"{Key}E{End}  roll out to the next area" : "";
            default: return "";
        }
    }
}
