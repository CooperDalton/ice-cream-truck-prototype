using System;
using Photon.Deterministic;
using Quantum;
using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.UI;

// The Divorced Dads HUD, in the same candy PS1 style as the zombie mode: cash on hand, the day with a sun or moon,
// heat badges, Big Dairy's debt meter with tonight's installment and strikes, the jingle and speed, the freezer tubs,
// the hotbar with item icons, the carried ingredient, ammo, what pressing E would do, a hint for what to do next, the
// controls panel (F1), screen splats, cough and brain freeze tints, the story cards (moving day, each morning, Big
// Dairy's collection, the win, the repo), and on moving day the lesson checklist with a bobbing arrow over whatever
// to use next. Every panel, text and image is authored in the scene; this only fills in values,
// swaps icons and shows or hides panels.
public class DadsHud : MonoBehaviour
{
    [Serializable]
    public struct ItemIcon
    {
        public DadItem Kind;
        public Sprite Sprite;
    }

    private const string Key = "<color=#ffe14a>";
    private const string End = "</color>";

    [SerializeField] private DadsInput input;
    [SerializeField] private Camera eye;
    [SerializeField] private ItemIcon[] icons;
    [Tooltip("Indexed by Treat; element 0 (None) is empty.")]
    [SerializeField] private Sprite[] scoopIcons;
    [Tooltip("Indexed by Treat; element 0 (None) is empty.")]
    [SerializeField] private Sprite[] tubIcons;
    [Tooltip("Sugar, waffle and double waffle cone, by the van's cone size.")]
    [SerializeField] private Sprite[] coneIcons;
    [SerializeField] private Sprite minigunIcon;
    [SerializeField] private Sprite sunIcon;
    [SerializeField] private Sprite moonIcon;
    [SerializeField] private Text moneyText;
    [SerializeField] private Image dayIcon;
    [SerializeField] private Text dayText;
    [SerializeField] private GameObject heatPanel;
    [SerializeField] private Image[] heatBadges;
    [SerializeField] private Text debtText;
    [SerializeField] private Image debtFill;
    [SerializeField] private Text dueText;
    [SerializeField] private Image[] strikeIcons;
    [SerializeField] private GameObject jinglePanel;
    [SerializeField] private GameObject speedPanel;
    [SerializeField] private Text speedText;
    [SerializeField] private Image[] tubImages;
    [SerializeField] private Text[] tubTexts;
    [SerializeField] private GameObject phaseBanner;
    [SerializeField] private Text phaseText;
    [SerializeField] private Text tipText;
    [SerializeField] private GameObject promptPanel;
    [SerializeField] private Text promptText;
    [SerializeField] private Image[] slotIcons;
    [SerializeField] private Image[] slotBadges;
    [SerializeField] private Text[] slotCounts;
    [SerializeField] private GameObject[] slotSelected;
    [SerializeField] private Text selectedName;
    [SerializeField] private float nameShowTime = 1.6f;
    [SerializeField] private GameObject carriedPanel;
    [SerializeField] private Image carriedIcon;
    [SerializeField] private Text carriedText;
    [SerializeField] private GameObject ammoPanel;
    [SerializeField] private Image ammoIcon;
    [SerializeField] private Text ammoText;
    [SerializeField] private Text ammoLabel;
    [SerializeField] private GameObject controlsPanel;
    [SerializeField] private float controlsShowTime = 30f;
    [SerializeField] private Image[] screenSplats;
    [SerializeField] private Image coughTint;
    [SerializeField] private Image frozenTint;
    [SerializeField] private CanvasGroup card;
    [SerializeField] private Text cardTitle;
    [SerializeField] private Text cardBody;
    [SerializeField] private Text cardStamp;
    [SerializeField] private RectTransform lessonPanel;
    [SerializeField] private Text lessonText;
    [Tooltip("Bobbing arrow over the next thing to use, anchored to the bottom left corner of the canvas.")]
    [SerializeField] private RectTransform lessonMarker;
    [SerializeField] private Image fade;
    [SerializeField] private float splatTime = 2.5f;
    [SerializeField] private float introTime = 7f;
    [SerializeField] private Color emptyColor = new Color(1f, 0.31f, 0.64f);
    [TextArea]
    [SerializeField] private string tutorialIntro = "Three years ago you went out for milk.\nYou never came back.\n\nShe kept the house. You got the trailer next door\nand an ice cream truck that BIG DAIRY owns.\n\nYour kid is coming over. Make some ice cream.";
    [Tooltip("Checklist line per Lesson.")]
    [SerializeField] private string[] lessonNames =
    {
        "Scoop up some mud", "Climb in the truck", "Churn the mud", "Scoop a cone", "Serve your kid", "Churn strawberries",
        "Churn some nuts", "Take the wheel",
    };
    [TextArea]
    [SerializeField] private string[] dayIntros =
    {
        "Welcome to BIG DAIRY's lot.\nHe owns the truck, the loan,\nand every sweet tooth in town.\n\nFeed the kids. Pay the man. Win them back.",
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
    private int lastSelected = -1;
    private DadItem lastSelectedKind;
    private float selectedShownAt;
    private bool controlsToggled;
    private float lessonPunch;

    private void OnEnable()
    {
        QuantumEvent.Subscribe(this, (EventDayPhaseChanged e) => OnPhase(e));
        QuantumEvent.Subscribe(this, (EventCollected e) => OnCollected(e));
        QuantumEvent.Subscribe(this, (EventLessonLearned e) => OnLesson(e));
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
        rect.anchoredPosition = new Vector2(UnityEngine.Random.Range(-480f, 480f), UnityEngine.Random.Range(-220f, 240f));
        rect.localRotation = Quaternion.Euler(0, 0, UnityEngine.Random.Range(0f, 360f));
        rect.localScale = Vector3.one * UnityEngine.Random.Range(0.8f, 1.6f);
        color.a = 0.92f;
        splat.color = color;
    }

    private void OnPhase(EventDayPhaseChanged e)
    {
        if (e.Phase == DayPhase.Tutorial) ShowCard("MOVING DAY", tutorialIntro, "", Color.clear, introTime + 2);
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

    // Each lesson punches the checklist; taking the wheel fades through black to Big Dairy's lot.
    private void OnLesson(EventLessonLearned e)
    {
        lessonPunch = 1;
        if (e.Lesson == Lesson.Drive) fade.color = Color.black;
    }

    private void OnCollected(EventCollected e)
    {
        var shortPaid = e.Paid < e.Due;
        var body = $"Big Dairy takes {Key}${e.Paid}{End} of the ${e.Due} you owe tonight.\n\n" + (e.Debt > 0 ? $"Still owed: ${e.Debt}" : "That's the last of it.");
        ShowCard("PAYDAY, DAY " + e.Day, body, shortPaid ? "STRIKE " + e.Strikes + "/3" : "PAID", shortPaid ? new Color(1f, 0.2f, 0.3f) : new Color(0.22f, 0.95f, 0.76f), 7);
    }

    private void ShowCard(string title, string body, string stamp, Color color, float seconds)
    {
        cardTitle.text = title;
        cardBody.text = body;
        cardStamp.text = stamp;
        stampColor = color;
        cardStamp.color = Color.clear;
        cardStamp.rectTransform.localScale = Vector3.one * 3;
        cardTimer = seconds;
        cardShownAt = Time.time;
    }

    private void Update()
    {
        var dt = Time.deltaTime;
        if (Keyboard.current.f1Key.wasPressedThisFrame)
        {
            controlsPanel.SetActive(!controlsPanel.activeSelf);
            controlsToggled = true;
        }
        // The controls panel shows for the first stretch of the session unless F1 was used.
        if (!controlsToggled && Time.timeSinceLevelLoad > controlsShowTime) controlsPanel.SetActive(false);
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
        moneyText.color = moneyPunch < 0 ? emptyColor : new Color(1f, 0.88f, 0.29f);
        var night = run.Clock.AsFloat >= settings.DuskAt.AsFloat;
        dayIcon.sprite = night ? moonIcon : sunIcon;
        dayText.text = $"DAY {run.Day}\n{Key}{TimeOfDay(run, settings)}{End}";
        var heat = Mathf.Clamp(Mathf.FloorToInt(run.Heat.AsFloat), 0, heatBadges.Length);
        heatPanel.SetActive(heat > 0);
        for (int i = 0; i < heatBadges.Length; i++) heatBadges[i].color = i < heat ? Color.white : new Color(1, 1, 1, 0.2f);

        var total = 0;
        foreach (var due in settings.Dues) total += due;
        debtText.text = "OWED $" + run.Debt;
        debtFill.fillAmount = 1 - (float)run.Debt / total;
        dueText.text = "TONIGHT $" + run.Due;
        for (int i = 0; i < strikeIcons.Length; i++) strikeIcons[i].color = i < run.Strikes ? Color.white : new Color(1, 1, 1, 0.15f);
        jinglePanel.SetActive(van.Jingle);
        var speed = Mathf.Abs(van.Speed.AsFloat);
        speedPanel.SetActive(speed > 0.5f);
        speedText.text = Mathf.RoundToInt(speed * 2.237f) + " MPH";
        phaseText.text = PhaseBanner(run);
        phaseBanner.SetActive(phaseText.text != "");

        foreach (var pair in frame.GetComponentIterator<Fixture>())
        {
            var tub = pair.Component;
            if (tub.Kind != FixtureKind.Tub) continue;
            var stocked = tub.Count > 0;
            tubImages[tub.Index].enabled = stocked;
            if (stocked) tubImages[tub.Index].sprite = tubIcons[(int)tub.Treat];
            tubTexts[tub.Index].text = stocked ? $"{TreatPalette.Name(tub.Treat).ToUpper()}  {Key}{tub.Count}{End}" : "empty";
            tubTexts[tub.Index].color = stocked ? Color.white : new Color(1, 1, 1, 0.45f);
        }

        if (!input.LocalEntity.IsValid) return;
        var dad = frame.Get<Dad>(input.LocalEntity);
        coughTint.color = Color.Lerp(coughTint.color, new Color(0.45f, 0.8f, 0.2f, dad.Coughing > 0 ? 0.35f : 0), 1 - Mathf.Exp(-6 * dt));
        frozenTint.color = Color.Lerp(frozenTint.color, new Color(0.7f, 0.9f, 1f, dad.Frozen > 0 ? 0.45f : 0), 1 - Mathf.Exp(-8 * dt));
        for (int i = 0; i < slotIcons.Length; i++)
        {
            var item = dad.Hotbar[i];
            slotIcons[i].enabled = item.Kind != DadItem.None;
            if (slotIcons[i].enabled) slotIcons[i].sprite = Icon(item, run.ConeSize);
            var loaded = item.Kind == DadItem.Cone ? (item.Count > 0 ? item.Scoops[item.Count - 1] : Treat.None) : DadSystem.IsGun(item.Kind) && item.Count > 0 ? item.Scoops[0] : Treat.None;
            slotBadges[i].enabled = loaded != Treat.None;
            if (slotBadges[i].enabled) slotBadges[i].sprite = scoopIcons[(int)loaded];
            slotCounts[i].text = item.Kind == DadItem.Cone ? item.Count + "/" + run.ConeSize : DadSystem.IsGun(item.Kind) ? item.Count.ToString() : "";
            slotSelected[i].SetActive(i == dad.Selected);
        }
        var held = dad.Hotbar[dad.Selected];
        if (dad.Selected != lastSelected || held.Kind != lastSelectedKind) selectedShownAt = Time.time;
        lastSelected = dad.Selected;
        lastSelectedKind = held.Kind;
        selectedName.text = Label(held, run.ConeSize);
        var nameColor = selectedName.color;
        nameColor.a = Mathf.Clamp01(1 - (Time.time - selectedShownAt - nameShowTime) / 0.4f);
        selectedName.color = nameColor;

        carriedPanel.SetActive(dad.Carried.Kind != DadItem.None);
        if (carriedPanel.activeSelf)
        {
            carriedIcon.sprite = Icon(dad.Carried, run.ConeSize);
            carriedText.text = $"{Label(dad.Carried, run.ConeSize)}\n{Key}E{End} at the churn   {Key}Q{End} drop";
        }

        ammoPanel.SetActive(dad.Turret || DadSystem.IsGun(held.Kind));
        if (dad.Turret)
        {
            ammoIcon.sprite = minigunIcon;
            ammoText.text = van.HopperRounds.ToString();
            ammoText.color = van.HopperRounds == 0 ? emptyColor : Color.white;
            ammoLabel.text = van.HopperRounds == 0 ? "LOAD THE HOPPER" : "HOPPER  " + TreatPalette.Name(van.HopperTreat).ToUpper();
        }
        else if (ammoPanel.activeSelf)
        {
            var flavor = held.Count > 0 ? held.Scoops[0] : Treat.Mud;
            ammoIcon.sprite = scoopIcons[(int)flavor];
            ammoText.text = held.Count.ToString();
            ammoText.color = held.Count == 0 ? emptyColor : Color.white;
            ammoLabel.text = held.Count == 0 ? $"{Key}E{End} AT A TUB" : TreatPalette.Name(flavor).ToUpper();
        }

        var prompt = dad.Busted > 0 ? "BUSTED\nThinking about your choices..." : dad.Knocked > 0 ? "OOF" : Prompt(frame, dad, input.LocalEntity, settings, run);
        if (prompt != promptText.text) promptShownAt = Time.time;
        promptText.text = prompt;
        // Seat controls get out of the way of the windshield once they have been read.
        promptPanel.SetActive(prompt != "" && (!(dad.Driving || dad.Turret) || Time.time - promptShownAt < 4f));
        var tutorial = run.Phase == DayPhase.Tutorial;
        lessonPanel.gameObject.SetActive(tutorial);
        lessonMarker.gameObject.SetActive(tutorial);
        if (!tutorial)
        {
            tipText.text = Tip(frame, dad, run);
            return;
        }
        tipText.text = Coach(frame, dad, settings, run, out var target);
        Mark(target);
        var list = "MOVING DAY";
        for (int i = 0; i < lessonNames.Length; i++)
        {
            var done = i < (int)run.Lesson;
            var line = (done ? "<color=#38f2c3>+ " : i == (int)run.Lesson ? "<color=#ffe14a>> " : "<color=#b8a8e8>  ") + lessonNames[i] + End;
            list += "\n" + line;
        }
        lessonText.text = list + "\n\n<color=#b8a8e8>Skip: take the wheel</color>";
    }

    // Puts the arrow over a world point, or on the screen edge pointing toward it when it is off screen or behind.
    private void Mark(Vector3 target)
    {
        var point = eye.WorldToViewportPoint(target + Vector3.up * (0.7f + 0.2f * Mathf.Sin(Time.time * 5f)));
        var offset = new Vector2(point.x - 0.5f, point.y - 0.5f);
        if (point.z < 0) offset = -offset;
        if (offset.sqrMagnitude < 0.000001f) offset = Vector2.down;
        var limit = new Vector2(0.45f, 0.38f);
        var edge = point.z < 0 || Mathf.Abs(offset.x) > limit.x || Mathf.Abs(offset.y) > limit.y;
        if (edge) offset /= Mathf.Max(Mathf.Abs(offset.x) / limit.x, Mathf.Abs(offset.y) / limit.y);
        var canvas = ((RectTransform)lessonMarker.parent).rect.size;
        lessonMarker.anchoredPosition = (offset + new Vector2(0.5f, 0.5f)) * canvas;
        // The arrow sprite points down: turn it toward the target along the edge.
        lessonMarker.localRotation = edge ? Quaternion.Euler(0, 0, Mathf.Atan2(offset.y, offset.x) * Mathf.Rad2Deg + 90) : Quaternion.identity;
    }

    // Moving day's coaching line for the current lesson, and where its arrow goes.
    private static string Coach(Frame frame, Dad dad, DadsSettings settings, DadsRun run, out Vector3 target)
    {
        var vanTransform = frame.Get<Transform3D>(frame.GetSingletonEntityRef<Van>());
        var churn = Nearest(frame, FixtureKind.Churn, vanTransform.Position) + Vector3.up;
        var held = dad.Hotbar[dad.Selected];
        switch (run.Lesson)
        {
            case Lesson.Mud:
                target = Nearest(frame, FixtureKind.MudPuddle, vanTransform.Position);
                return $"Look at the mud puddle by your trailer and press {Key}E{End} to fill a bucket.";
            case Lesson.Board:
                target = vanTransform.TransformPoint(settings.RearOutside).ToUnityVector3() + Vector3.up;
                return $"Carry it to the back of the truck and press {Key}E{End} at the rear door to climb in.";
            case Lesson.Churn:
                target = churn;
                return $"Press {Key}E{End} on the flavor churn to dump the mud in.  Out comes a tub of ice cream!";
            case Lesson.Scoop:
                foreach (var pair in frame.GetComponentIterator<Fixture>())
                {
                    if (pair.Component.Kind != FixtureKind.Tub || pair.Component.Treat != Treat.Mud) continue;
                    target = frame.Get<Transform3D>(pair.Entity).Position.ToUnityVector3();
                    return held.Kind == DadItem.Cone ? $"{Key}CLICK{End} the freezer tub to plop a scoop of mud on your cone." : $"Press {Key}1{End} to hold your cone, then {Key}CLICK{End} the tub.";
                }
                target = churn;
                return "The mud's all gone!  Churn another bucket.";
            case Lesson.Serve:
                foreach (var pair in frame.GetComponentIterator<Npc>())
                {
                    target = frame.Get<Transform3D>(pair.Entity).Position.ToUnityVector3() + Vector3.up * 1.4f;
                    if (pair.Component.State == NpcState.Queue) return $"Your kid's at the window.  Face them and {Key}CLICK{End} to shove the cone in.  Yes, they pay.";
                    return "Your kid's coming over from your ex's house.  Meet them at the serving window.";
                }
                target = vanTransform.TransformPoint(settings.WindowOutside).ToUnityVector3();
                return held.Kind == DadItem.Cone && held.Count == 0 ? "Scoop another cone first." : "Wait for your kid at the serving window.";
            case Lesson.Strawberries:
                if (dad.Carried.Kind == DadItem.StrawberryBasket)
                {
                    target = churn;
                    return "Into the churn with them.  Every flavor gets its own tub.";
                }
                target = Nearest(frame, FixtureKind.StrawberryPatch, vanTransform.Position);
                return $"Kids pay more for fancier flavors.  Pick strawberries from the patch ({Key}E{End}).";
            case Lesson.Nuts:
                if (dad.Carried.Kind == DadItem.NutSack)
                {
                    target = churn;
                    return "Churn the nuts into Rocky Road.  Its last bite knocks kids flat.";
                }
                foreach (var pair in frame.GetComponentIterator<Loot>())
                {
                    if (pair.Component.Item.Kind != DadItem.NutSack) continue;
                    target = frame.Get<Transform3D>(pair.Entity).Position.ToUnityVector3();
                    return $"Grab a sack of nuts ({Key}E{End}).";
                }
                target = Nearest(frame, FixtureKind.NutTree, vanTransform.Position) + Vector3.up * 3;
                return $"Shake the nut tree: keep pressing {Key}E{End} on it until the nuts drop.";
            default:
                target = vanTransform.TransformPoint(settings.DriverSeat).ToUnityVector3() + Vector3.up;
                return $"Stocked up!  Press {Key}E{End} by the driver's door and take the wheel.  Big Dairy is waiting.";
        }
    }

    // The tutorial's fixtures are the ones closest to the truck parked outside the trailer.
    private static Vector3 Nearest(Frame frame, FixtureKind kind, FPVector3 from)
    {
        var best = Vector3.zero;
        var bestDistance = float.MaxValue;
        foreach (var pair in frame.GetComponentIterator<Fixture>())
        {
            if (pair.Component.Kind != kind) continue;
            var position = frame.Get<Transform3D>(pair.Entity).Position;
            var distance = (position - from).SqrMagnitude.AsFloat;
            if (distance >= bestDistance) continue;
            bestDistance = distance;
            best = position.ToUnityVector3();
        }
        return best;
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
        fade.color = Color.Lerp(fade.color, Color.clear, dt * 1.5f);
        lessonPunch = Mathf.MoveTowards(lessonPunch, 0, dt * 3);
        lessonPanel.localScale = Vector3.one * (1 + 0.06f * lessonPunch);
        cardTimer -= dt;
        card.alpha = Mathf.MoveTowards(card.alpha, cardTimer > 0 ? 1 : 0, dt * 3);
        // The stamp slams down a second after the card, with Big Dairy's stamp sound.
        if (Time.time - cardShownAt < 1) return;
        cardStamp.color = stampColor;
        cardStamp.rectTransform.localScale = Vector3.Lerp(cardStamp.rectTransform.localScale, Vector3.one, 1 - Mathf.Exp(-14 * dt));
    }

    private Sprite Icon(DadSlot item, int coneSize)
    {
        if (item.Kind == DadItem.Cone) return coneIcons[Mathf.Clamp(coneSize, 1, coneIcons.Length) - 1];
        foreach (var icon in icons)
        {
            if (icon.Kind == item.Kind) return icon.Sprite;
        }
        throw new InvalidOperationException($"DadsHud has no icon for {item.Kind}");
    }

    // No clock on screen: the time of day in words, from the sun's progress.
    private static string TimeOfDay(DadsRun run, DadsSettings settings)
    {
        if (run.Phase == DayPhase.Tutorial) return "MOVING DAY";
        if (run.Phase == DayPhase.Morning) return "AT THE LOT";
        if (run.Phase == DayPhase.Collection || run.Phase == DayPhase.Won || run.Phase == DayPhase.Repo) return "PAYDAY";
        if (run.Phase == DayPhase.Night) return run.Clock.AsFloat >= 1 ? "MIDNIGHT" : "NIGHT";
        if (run.Phase == DayPhase.Dusk) return "DUSK";
        var day = run.Clock.AsFloat / settings.DuskAt.AsFloat;
        return day < 0.25f ? "MORNING" : day < 0.45f ? "NOON" : day < 0.75f ? "AFTERNOON" : "EVENING";
    }

    private static string PhaseBanner(DadsRun run)
    {
        switch (run.Phase)
        {
            case DayPhase.Tutorial: return "MOVING DAY!  Stock the truck, then take the wheel";
            case DayPhase.Morning: return "BIG DAIRY'S LOT!  Shop, load up, then drive out and sell";
            case DayPhase.Dusk: return "The kids are heading home.  Back to the lot soon!";
            case DayPhase.Night: return "SUGAR CURFEW!  Cops are out and the jingle draws them";
            default: return "";
        }
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
        if (run.Phase == DayPhase.Night || run.Phase == DayPhase.Dusk) return "Drive back to Big Dairy's lot (cops won't follow you in) and punch the clock.";
        if (run.Phase != DayPhase.Morning && run.Phase != DayPhase.Day) return "";
        if (dad.Carried.Kind != DadItem.None) return "Take it to the flavor churn in the van.";
        if (stock == 0) return "Out of ice cream!  Scoop mud from a puddle and dump it in the churn.";
        if (held.Kind == DadItem.Cone && held.Count == 0) return "Click a freezer tub at the back of the van to plop a scoop on your cone.";
        if (DadSystem.IsGun(held.Kind) && held.Count == 0) return "Press E at a freezer tub to refill your gun.";
        if (run.Phase == DayPhase.Morning) return dad.Driving ? "Drive out of the lot to start the day." : "Take the wheel up front and drive out of the lot.";
        if (dad.Driving && !van.Jingle) return "RIGHT CLICK plays the jingle and kids come running.  CLICK honks.";
        if (dad.Driving && queued > 0 && Mathf.Abs(van.Speed.AsFloat) < 1) return queued + " kids at the serving window!  Leave the seat and go serve them.";
        if (dad.Driving) return "Park near kids: they line up at the serving window.";
        return queued > 0 ? "Kids at the window: stand at the counter and CLICK to shove a cone in a face." : "";
    }

    public static string Label(DadSlot item, int coneSize)
    {
        switch (item.Kind)
        {
            case DadItem.None: return "";
            case DadItem.Cone:
                var cone = coneSize >= 3 ? "Double Waffle Cone" : coneSize == 2 ? "Waffle Cone" : "Cone";
                if (item.Count == 0) return "Empty " + cone;
                var scoops = "";
                for (int i = item.Count - 1; i >= 0; i--) scoops += TreatPalette.Name(item.Scoops[i]) + (i > 0 ? " + " : "");
                return scoops + " " + cone;
            case DadItem.ScoopPistol: return "Scoop Pistol";
            case DadItem.SundaeShotgun: return "Sundae Shotgun";
            case DadItem.MudBucket: return "Bucket of Mud";
            case DadItem.StrawberryBasket: return "Strawberries";
            case DadItem.IcedCoffee: return "Iced Coffees";
            case DadItem.NutSack: return "Sack of Nuts";
            case DadItem.GoldLeaf: return "Gold Leaf";
            default: return item.Kind.ToString();
        }
    }

    private static string Prompt(Frame frame, Dad dad, EntityRef entity, DadsSettings settings, DadsRun run)
    {
        if (dad.Driving) return $"{Key}W/S{End} drive   {Key}A/D{End} steer   {Key}CLICK{End} honk   {Key}RIGHT CLICK{End} jingle   {Key}E{End} get out";
        if (dad.Turret) return $"{Key}CLICK{End} fire the soft serve minigun   {Key}E{End} leave the turret";
        var target = dad.LookTarget;
        if (target.IsValid && frame.TryGet(target, out Loot loot)) return $"{Key}E{End}  pick up {Label(loot.Item, run.ConeSize)}";
        if (target.IsValid && frame.TryGet(target, out Fixture fixture)) return FixturePrompt(frame, fixture, dad, run);

        var van = frame.Get<Transform3D>(frame.GetSingletonEntityRef<Van>());
        var local = van.InverseTransformPoint(frame.Get<Transform3D>(entity).Position);
        // Same nearest-spot rule as DadSystem.Interact.
        var nearest = settings.InteractRange * settings.InteractRange;
        var prompt = "";
        var canDrive = !frame.GetSingleton<Van>().Driver.IsValid && dad.Carried.Kind == DadItem.None;
        var spots = new[] { (settings.LadderBottom, "climb to the roof"), (settings.HatchTop, "climb down into the kitchen"),
            (settings.RearOutside, "get in the truck"), (settings.RearInside, "get out the back"), (settings.DriverSeat, canDrive ? "drive" : "") };
        foreach (var (spot, text) in spots)
        {
            var distance = (local - spot).SqrMagnitude;
            if (distance >= nearest || text == "") continue;
            nearest = distance;
            prompt = $"{Key}E{End}  {text}";
        }
        return prompt;
    }

    private static unsafe string FixturePrompt(Frame frame, Fixture fixture, Dad dad, DadsRun run)
    {
        var held = dad.Hotbar[dad.Selected];
        switch (fixture.Kind)
        {
            case FixtureKind.Churn:
                if (fixture.Timer > 0) return "CHURNING...";
                return DadSystem.TreatOf(dad.Carried.Kind) != Treat.None ? $"{Key}E{End}  dump it in the churn" : "FLAVOR CHURN\nbring mud, strawberries, iced coffee, nuts or gold";
            case FixtureKind.Tub:
                if (fixture.Count == 0) return "EMPTY TUB";
                var flavor = $"{TreatPalette.Name(fixture.Treat).ToUpper()} TUB  ({fixture.Count})";
                if (held.Kind == DadItem.Cone) return held.Count < run.ConeSize ? $"{flavor}\n{Key}CLICK{End} plop a scoop on your cone" : $"{flavor}\nyour cone's full: go feed a kid";
                if (DadSystem.IsGun(held.Kind)) return $"{flavor}\n{Key}E{End} refill your {(held.Kind == DadItem.ScoopPistol ? "pistol" : "shotgun")}";
                return $"{flavor}\nhold a cone or a gun";
            case FixtureKind.ConeCounter: return $"{Key}E{End}  grab a cone";
            case FixtureKind.GunRack: return DadSystem.IsGun(held.Kind) ? $"{Key}E{End}  hang up your gun" : $"{Key}E{End}  take a gun";
            case FixtureKind.Hopper: return run.Minigun ? $"MINIGUN HOPPER  ({frame.GetSingleton<Van>().HopperRounds})\n{Key}E{End} pour in the fullest tub" : "MINIGUN HOPPER\nbuy the Soft Serve Minigun at the lot";
            case FixtureKind.Bell: return frame.GetSingleton<Van>().BellCooldown > 0 ? "the bell is still ringing" : $"{Key}E{End}  ring the dinner bell (kids come running)";
            case FixtureKind.Turret: return $"{Key}E{End}  man the soft serve minigun";
            case FixtureKind.Shop:
                if (DadsGame.SoldOut(&run, fixture.Upgrade)) return ShopTag.Name(fixture.Upgrade) + "\nnot available";
                return run.Money >= fixture.Price ? $"{Key}E{End}  buy {ShopTag.Name(fixture.Upgrade)} for ${fixture.Price}" : $"{ShopTag.Name(fixture.Upgrade)}  ${fixture.Price}\nyou're broke";
            case FixtureKind.Collector: return $"BIG DAIRY\n\"You got my ${run.Due}?\"";
            case FixtureKind.TimeClock:
                if (run.Phase == DayPhase.Morning) return "TIME CLOCK\ngo sell some ice cream first";
                return $"{Key}E{End}  clock out and pay Big Dairy ${run.Due}\n(park the truck in the lot first)";
            case FixtureKind.MudPuddle: return dad.Carried.Kind == DadItem.None ? $"{Key}E{End}  scoop up some mud" : "hands full";
            case FixtureKind.StrawberryPatch: return fixture.Timer > 0 ? "picked clean (growing back)" : $"{Key}E{End}  pick strawberries";
            case FixtureKind.CoffeeTable: return fixture.Timer > 0 ? "no coffees left (restocking)" : $"{Key}E{End}  \"borrow\" some iced coffees";
            case FixtureKind.NutTree: return fixture.Timer > 0 ? "no nuts left (for now)" : $"{Key}E{End}  shake the tree (or ram it with the truck)";
            case FixtureKind.Vault:
                if (!fixture.Open) return "VAULT\nsomebody has to stand on the pressure plate";
                return fixture.Timer > 0 ? "the vault is empty (for now)" : $"{Key}E{End}  grab the gold leaf";
            case FixtureKind.Plate: return "PRESSURE PLATE\nstand here or drop something heavy on it";
            case FixtureKind.Gate: return fixture.Open ? "" : "PERMIT REQUIRED\nbuy one at Big Dairy's lot";
            default: return "";
        }
    }
}
