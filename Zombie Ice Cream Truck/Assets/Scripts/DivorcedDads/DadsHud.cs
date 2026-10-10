using Quantum;
using UnityEngine;
using UnityEngine.UI;

// The Divorced Dads HUD: cash on hand, Big Dairy's debt meter and tonight's installment, the day and time of day in
// words (no clock), heat badges, the jingle, the freezer stock, the hotbar, what pressing E would do, plus screen
// splats, the cough and brain freeze tints, and the story cards (each morning's intro, Big Dairy's collection, the
// win and the repo). Every text and image is authored in the scene; this only fills in values.
public class DadsHud : MonoBehaviour
{
    [SerializeField] private DadsInput input;
    [SerializeField] private Text moneyText;
    [SerializeField] private Text dayText;
    [SerializeField] private Text debtText;
    [SerializeField] private Image debtFill;
    [SerializeField] private Text dueText;
    [SerializeField] private Text heatText;
    [SerializeField] private Text jingleText;
    [SerializeField] private Text phaseText;
    [SerializeField] private Text promptText;
    [SerializeField] private Text carriedText;
    [SerializeField] private Text speedText;
    [SerializeField] private Text tipText;
    [SerializeField] private Image[] tubChips;
    [SerializeField] private Text[] tubTexts;
    [SerializeField] private Text[] slotTexts;
    [SerializeField] private Image[] slotFrames;
    [SerializeField] private Color selectedColor = new Color(1f, 0.31f, 0.64f, 0.85f);
    [SerializeField] private Color slotColor = new Color(0.1f, 0.06f, 0.2f, 0.7f);
    [SerializeField] private Image[] screenSplats;
    [SerializeField] private Image coughTint;
    [SerializeField] private Image frozenTint;
    [SerializeField] private CanvasGroup card;
    [SerializeField] private Text cardTitle;
    [SerializeField] private Text cardBody;
    [SerializeField] private Text cardStamp;
    [SerializeField] private float splatTime = 2.5f;
    [SerializeField] private float introTime = 7f;
    [TextArea]
    [SerializeField] private string[] dayIntros =
    {
        "Three years ago you went out for milk.\nYou never came back.\n\nNow you're divorced, deep in debt to BIG DAIRY,\nand all you've got left is this ice cream truck.\n\nFeed the kids. Pay the man. Win them back.",
        "Meanwhile, at your ex's house...\nYour kid asked who the guy in the truck is.\nYour ex said \"nobody, sweetie.\"",
        "Meanwhile, at your ex's house...\nThe kids made a video about you.\nIt has four views. All yours.",
        "Big Dairy sent a fruit basket.\nIt's all milk.",
        "Final installment.\nYour ex says she's \"cautiously curious.\"\nDon't blow this.",
        "Overtime.\nBig Dairy charges interest in milk.",
    };
    private float[] splatAge;
    private int nextSplat;
    private int lastMoney;
    private float moneyPunch;
    private float cardTimer;
    private float cardShownAt;
    private Color stampColor;
    private float promptShownAt;

    private void OnEnable()
    {
        QuantumEvent.Subscribe(this, (EventDayPhaseChanged e) => OnPhase(e));
        QuantumEvent.Subscribe(this, (EventCollected e) => OnCollected(e));
        splatAge = new float[screenSplats.Length];
        for (int i = 0; i < splatAge.Length; i++) splatAge[i] = splatTime;
        card.alpha = 0;
    }

    // Splats a blob of ice cream across the screen; it slides down and fades.
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

    private void OnPhase(EventDayPhaseChanged e)
    {
        if (e.Phase == DayPhase.Morning)
        {
            ShowCard("DAY " + e.Day, dayIntros[Mathf.Min(e.Day, dayIntros.Length) - 1], "", Color.clear, introTime);
        }
        if (e.Phase == DayPhase.Won)
        {
            ShowCard("DEBT PAID OFF!", "Your exes are... mildly impressed.\nThe kids want to know if the truck\ndoes birthday parties.\n\nYou did it, dads.", "FREE", new Color(0.22f, 0.95f, 0.76f), 15);
        }
        if (e.Phase == DayPhase.Repo)
        {
            ShowCard("REPOSSESSED", "Big Dairy took the truck.\nYou are now divorced dads with nothing.\n\nAgain.", "STRIKE 3", new Color(1f, 0.2f, 0.3f), 15);
        }
    }

    private void OnCollected(EventCollected e)
    {
        var short_ = e.Paid < e.Due;
        var body = "Big Dairy takes $" + e.Paid + " of the $" + e.Due + " you owe tonight.\n\n" + (e.Debt > 0 ? "Still owed: $" + e.Debt : "That's the last of it.");
        ShowCard("COLLECTION, DAY " + e.Day, body, short_ ? "STRIKE " + e.Strikes + "/3" : "PAID", short_ ? new Color(1f, 0.2f, 0.3f) : new Color(0.22f, 0.95f, 0.76f), 7);
    }

    private void ShowCard(string title, string body, string stamp, Color stampColor, float seconds)
    {
        cardTitle.text = title;
        cardBody.text = body;
        cardStamp.text = stamp;
        this.stampColor = stampColor;
        cardStamp.color = Color.clear;
        cardStamp.rectTransform.localScale = Vector3.one * 3;
        cardTimer = seconds;
        cardShownAt = Time.time;
    }

    private void Update()
    {
        var dt = Time.deltaTime;
        UpdateOverlays(dt);
        var game = QuantumRunner.Default?.Game;
        if (game?.Frames.Predicted == null) return;
        var frame = game.Frames.Predicted;
        var settings = frame.FindAsset(frame.RuntimeConfig.DadsSettings);
        var run = frame.GetSingleton<DadsRun>();
        var van = frame.GetSingleton<Van>();

        moneyText.text = "$" + run.Money;
        if (run.Money > lastMoney) moneyPunch = 1;
        if (run.Money < lastMoney) moneyPunch = -1;
        lastMoney = run.Money;
        moneyPunch = Mathf.MoveTowards(moneyPunch, 0, dt * 4);
        moneyText.rectTransform.localScale = Vector3.one * (1 + 0.35f * Mathf.Abs(moneyPunch));
        moneyText.color = moneyPunch < 0 ? new Color(1f, 0.3f, 0.3f) : new Color(1f, 0.88f, 0.29f);
        var total = 0;
        foreach (var due in settings.Dues) total += due;
        debtText.text = "OWED TO BIG DAIRY  $" + run.Debt;
        debtFill.fillAmount = 1 - (float)run.Debt / total;
        dueText.text = "TONIGHT  $" + run.Due + (run.Strikes > 0 ? "   STRIKES " + run.Strikes + "/3" : "");
        dayText.text = "DAY " + run.Day + "  " + TimeOfDay(run, settings);
        var heat = Mathf.Clamp(Mathf.FloorToInt(run.Heat.AsFloat), 0, 5);
        heatText.text = heat > 0 ? "HEAT " + new string('*', heat) + new string('-', 5 - heat) : "";
        jingleText.text = van.Jingle ? "JINGLE ON" : "";
        speedText.text = Mathf.Abs(van.Speed.AsFloat) > 0.5f ? Mathf.RoundToInt(Mathf.Abs(van.Speed.AsFloat) * 2.237f) + " MPH" : "";
        phaseText.text = PhaseBanner(run);

        foreach (var pair in frame.GetComponentIterator<Fixture>())
        {
            var fixture = pair.Component;
            if (fixture.Kind != FixtureKind.Tub) continue;
            tubTexts[fixture.Index].text = fixture.Count > 0 ? TreatPalette.Name(fixture.Treat).ToUpper() + " " + fixture.Count : "EMPTY";
            tubChips[fixture.Index].color = fixture.Count > 0 ? TreatPalette.Of(fixture.Treat) : new Color(0.3f, 0.3f, 0.35f, 0.7f);
        }

        if (!input.LocalEntity.IsValid) return;
        var dad = frame.Get<Dad>(input.LocalEntity);
        coughTint.color = Color.Lerp(coughTint.color, new Color(0.45f, 0.8f, 0.2f, dad.Coughing > 0 ? 0.35f : 0), 1 - Mathf.Exp(-6 * dt));
        frozenTint.color = Color.Lerp(frozenTint.color, new Color(0.7f, 0.9f, 1f, dad.Frozen > 0 ? 0.45f : 0), 1 - Mathf.Exp(-8 * dt));
        for (int i = 0; i < slotTexts.Length; i++)
        {
            slotTexts[i].text = (i + 1) + "\n" + Label(dad.Hotbar[i], run.ConeSize);
            slotFrames[i].color = i == dad.Selected ? selectedColor : slotColor;
        }
        carriedText.text = dad.Carried.Kind == DadItem.None ? "" : "CARRYING " + Label(dad.Carried, 0) + "   take it to the churn  /  Q drop";
        var prompt = dad.Busted > 0 ? "BUSTED. Thinking about your choices..." : dad.Knocked > 0 ? "OOF" : Prompt(frame, dad, input.LocalEntity, settings, run);
        if (prompt != promptText.text) promptShownAt = Time.time;
        promptText.text = prompt;
        tipText.text = Tip(frame, dad, run);
        // Seat controls get out of the way of the windshield once they have been read.
        promptText.enabled = !(dad.Driving || dad.Turret) || Time.time - promptShownAt < 4f;
    }

    private void UpdateOverlays(float dt)
    {
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
        cardTimer -= dt;
        card.alpha = Mathf.MoveTowards(card.alpha, cardTimer > 0 ? 1 : 0, dt * 3);
        // The stamp slams down a second after the card, with Big Dairy's stamp sound.
        if (Time.time - cardShownAt < 1) return;
        cardStamp.color = stampColor;
        cardStamp.rectTransform.localScale = Vector3.Lerp(cardStamp.rectTransform.localScale, Vector3.one, 1 - Mathf.Exp(-14 * dt));
    }

    // No clock on screen: the time of day in words, from the sun's progress.
    private static string TimeOfDay(DadsRun run, DadsSettings settings)
    {
        if (run.Phase == DayPhase.Morning) return "MORNING AT THE LOT";
        if (run.Phase == DayPhase.Collection || run.Phase == DayPhase.Won || run.Phase == DayPhase.Repo) return "PAYDAY";
        if (run.Phase == DayPhase.Night) return run.Clock.AsFloat >= 1 ? "MIDNIGHT" : "NIGHT";
        if (run.Phase == DayPhase.Dusk) return "DUSK";
        var day = run.Clock.AsFloat / settings.DuskAt.AsFloat;
        return day < 0.25f ? "MORNING" : day < 0.45f ? "NOON" : day < 0.75f ? "AFTERNOON" : "EVENING";
    }

    // One hint at a time for whatever the dads should be doing next.
    private static string Tip(Frame frame, Dad dad, DadsRun run)
    {
        var van = frame.GetSingleton<Van>();
        var stock = 0;
        foreach (var pair in frame.GetComponentIterator<Fixture>())
        {
            if (pair.Component.Kind == FixtureKind.Tub) stock += pair.Component.Count;
        }
        var held = dad.Hotbar[dad.Selected];
        var queued = 0;
        for (int i = 0; i < van.Queue.Length; i++)
        {
            if (van.Queue[i].IsValid && frame.Exists(van.Queue[i])) queued++;
        }
        if (run.Phase == DayPhase.Night || run.Phase == DayPhase.Dusk) return "Drive back to Big Dairy's lot and punch the clock to pay up.";
        if (run.Phase != DayPhase.Morning && run.Phase != DayPhase.Day) return "";
        if (dad.Carried.Kind != DadItem.None) return "Take it to the flavor churn in the van and press E.";
        if (stock == 0) return "Out of ice cream! Scoop mud from a puddle (or find better stuff) and dump it in the churn.";
        if (held.Kind == DadItem.Cone && held.Count == 0) return "Click a freezer tub at the back of the van to plop a scoop on your cone.";
        if (DadSystem.IsGun(held.Kind) && held.Count == 0) return "Press E at a freezer tub to refill your gun.";
        if (run.Phase == DayPhase.Morning) return dad.Driving ? "Drive out of the lot to start the day." : "Take the wheel up front (E at the seat) and drive out of the lot.";
        if (dad.Driving && !van.Jingle) return "RIGHT CLICK to play the jingle. Kids come running. CLICK to honk.";
        if (dad.Driving && queued > 0 && Mathf.Abs(van.Speed.AsFloat) < 1) return queued + " kids at the serving window! Leave the seat and shove cones in their faces.";
        if (dad.Driving) return "Park somewhere with kids around: they line up at the serving window.";
        return queued > 0 ? "Kids at the window: stand at the counter and CLICK to shove a cone in a face." : "";
    }

    private static string PhaseBanner(DadsRun run)
    {
        switch (run.Phase)
        {
            case DayPhase.Morning: return "Buy stuff at the lot, then drive out and sell!";
            case DayPhase.Dusk: return "The kids are heading home. Back to the lot soon!";
            case DayPhase.Night: return "SUGAR CURFEW! Cops are out (and the jingle draws them). Get back to the lot: they won't follow you in.";
            default: return "";
        }
    }

    public static string Label(DadSlot item, int coneSize)
    {
        switch (item.Kind)
        {
            case DadItem.None: return "";
            case DadItem.Cone:
                if (item.Count == 0) return "Empty cone";
                var scoops = "";
                for (int i = item.Count - 1; i >= 0; i--) scoops += TreatPalette.Name(item.Scoops[i]) + (i > 0 ? "\n" : "");
                return scoops;
            case DadItem.ScoopPistol:
            case DadItem.SundaeShotgun:
                var name = item.Kind == DadItem.ScoopPistol ? "Pistol" : "Shotgun";
                return item.Count > 0 ? name + " " + item.Count + "\n" + TreatPalette.Name(item.Scoops[0]) : name + "\nEMPTY";
            case DadItem.MudBucket: return "BUCKET OF MUD";
            case DadItem.StrawberryBasket: return "STRAWBERRIES";
            case DadItem.IcedCoffee: return "ICED COFFEES";
            case DadItem.NutSack: return "SACK OF NUTS";
            case DadItem.GoldLeaf: return "GOLD LEAF";
            default: return item.Kind.ToString();
        }
    }

    private static string Prompt(Frame frame, Dad dad, EntityRef entity, DadsSettings settings, DadsRun run)
    {
        if (dad.Driving) return "W/S drive  A/D steer  CLICK honk  RIGHT CLICK jingle on/off  E get out";
        if (dad.Turret) return "CLICK fire the soft serve minigun  E leave the turret";
        var target = dad.LookTarget;
        if (target.IsValid && frame.TryGet(target, out Loot loot)) return "E  pick up " + Label(loot.Item, run.ConeSize).Replace("\n", " ");
        if (target.IsValid && frame.TryGet(target, out Fixture fixture)) return FixturePrompt(frame, fixture, dad, settings, run);

        var van = frame.Get<Transform3D>(frame.GetSingletonEntityRef<Van>());
        var local = van.InverseTransformPoint(frame.Get<Transform3D>(entity).Position);
        // Same nearest-spot rule as DadSystem.Interact.
        var nearest = settings.InteractRange * settings.InteractRange;
        var prompt = "";
        var canDrive = !frame.GetSingleton<Van>().Driver.IsValid && dad.Carried.Kind == DadItem.None;
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

    private static unsafe string FixturePrompt(Frame frame, Fixture fixture, Dad dad, DadsSettings settings, DadsRun run)
    {
        var held = dad.Hotbar[dad.Selected];
        switch (fixture.Kind)
        {
            case FixtureKind.Churn:
                if (fixture.Timer > 0) return "CHURNING...";
                return DadSystem.TreatOf(dad.Carried.Kind) != Treat.None ? "E  dump it in the churn" : "FLAVOR CHURN\nbring mud, strawberries, iced coffee, nuts or gold";
            case FixtureKind.Tub:
                if (fixture.Count == 0) return "EMPTY TUB";
                var flavor = TreatPalette.Name(fixture.Treat).ToUpper() + " (" + fixture.Count + ")";
                if (held.Kind == DadItem.Cone) return held.Count < run.ConeSize ? flavor + "\nCLICK  plop a scoop on your cone" : flavor + "\ncone's full! go feed a kid";
                if (DadSystem.IsGun(held.Kind)) return flavor + "\nE  refill your " + (held.Kind == DadItem.ScoopPistol ? "pistol" : "shotgun");
                return flavor + "\nhold a cone or a gun";
            case FixtureKind.ConeCounter: return "E  grab a cone";
            case FixtureKind.GunRack: return DadSystem.IsGun(held.Kind) ? "E  hang up your gun" : "E  take a gun";
            case FixtureKind.Hopper: return run.Minigun ? "E  pour the fullest tub into the minigun (" + frame.GetSingleton<Van>().HopperRounds + ")" : "MINIGUN HOPPER (buy the Soft Serve Minigun)";
            case FixtureKind.Bell: return frame.GetSingleton<Van>().BellCooldown > 0 ? "the bell is still ringing" : "E  ring the dinner bell (kids come running)";
            case FixtureKind.Turret: return "E  man the soft serve minigun";
            case FixtureKind.Shop:
                if (DadsGame.SoldOut(&run, fixture.Upgrade)) return ShopTag.Name(fixture.Upgrade) + "  (not available)";
                return run.Money >= fixture.Price ? "E  buy " + ShopTag.Name(fixture.Upgrade) + " for $" + fixture.Price : ShopTag.Name(fixture.Upgrade) + "  $" + fixture.Price + "  (you're broke)";
            case FixtureKind.Collector: return "BIG DAIRY: \"You got my $" + run.Due + "?\"";
            case FixtureKind.TimeClock:
                if (run.Phase == DayPhase.Morning) return "go sell some ice cream first";
                return "E  clock out and pay Big Dairy $" + run.Due + "\n(the truck has to be parked in the lot)";
            case FixtureKind.MudPuddle: return dad.Carried.Kind == DadItem.None ? "E  scoop up some mud" : "hands full";
            case FixtureKind.StrawberryPatch: return fixture.Timer > 0 ? "picked clean (growing back)" : "E  pick strawberries";
            case FixtureKind.CoffeeTable: return fixture.Timer > 0 ? "no coffees left (restocking)" : "E  \"borrow\" some iced coffees";
            case FixtureKind.NutTree: return fixture.Timer > 0 ? "no nuts left (for now)" : "E  shake the tree (or ram it with the truck)";
            case FixtureKind.Vault:
                if (!fixture.Open) return "VAULT: somebody has to stand on the pressure plate";
                return fixture.Timer > 0 ? "the vault is empty (for now)" : "E  grab the gold leaf";
            case FixtureKind.Plate: return "PRESSURE PLATE: stand here or drop something heavy on it";
            case FixtureKind.Gate: return fixture.Open ? "" : "PERMIT REQUIRED: buy one at Big Dairy's lot";
            default: return "";
        }
    }
}
