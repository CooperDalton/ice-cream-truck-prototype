using Quantum;
using UnityEngine;

// Kevin, a zombie that ice cream half cured, who runs every depot shop and always somehow gets there first. He greets
// the crew, answers when talked to, and has an opinion on every purchase, empty wallet and slot machine spin. Lines are
// picked from the event data so every player sees the same one. He bobs, turns his head toward the camera and waves
// while talking; the speech bubble is a world-space text that wraps and fades.
public class ShopkeeperView : QuantumEntityViewComponent
{
    [SerializeField] private Transform body;
    [SerializeField] private Transform head;
    [SerializeField] private Transform waveArm;
    [SerializeField] private Vector3 waveEuler = new Vector3(0, 0, 140);
    [SerializeField] private TextMesh bubble;
    [SerializeField] private TextMesh bubbleShadow;
    [SerializeField] private float lineTime = 5f;
    [SerializeField] private int wrapColumns = 26;
    [SerializeField] private float hearingRange = 30f;
    [SerializeField, TextArea] private string[] greetings =
    {
        "Welcome to Kevin's! I was a zombie for three weeks. Ice cream fixed me. Mostly.",
        "Oh hey, you again! No, I didn't pass you on the road. I don't know how I got here either.",
        "Welcome back! Please don't shoot me. I'm like 10% zombie now, tops.",
        "Making great time! I'm making great brai-- BARGAINS. Great bargains.",
        "Kevin's: open 24/7, mostly because I don't sleep anymore.",
        "You look tired. Have you tried being undead? Kidding. Don't. It's a whole thing.",
    };
    [SerializeField, TextArea] private string[] talk =
    {
        "Chocolate makes them tip. Zombies are weirdly generous.",
        "Mint freezes 'em solid. Then you just drive into them. Very satisfying.",
        "Coffee goes right through 'em. Like coffee does.",
        "Rocky Road hits like a truck. Speaking of which, yours runs on ice cream. I checked. That's not normal.",
        "Cocoa plus strawberries in the churn makes Neapolitan. Both bonuses. You're welcome.",
        "Hot spots are packed with loot. And zombies. Mostly zombies. Bring a cone.",
        "Cones are for bonking. They eat the scoop, you press R and add another.",
        "The slot machine is totally fair. I only rigged it a little. For you. In a good way.",
        "Don't run out of ice cream out there. Walking is how I got like this.",
        "I'm not hungry. For brains. I'm hungry for... commerce. Haha. Ha.",
        "Three brains on the slots? That's my cousin. He lives in there.",
        "My left ear? Lost it gambling. Don't worry about it.",
    };
    [SerializeField, TextArea] private string[] purchased =
    {
        "Pleasure doing business!",
        "No refunds. Also no receipts. I ate the register.",
        "Great choice. That one only bit me twice.",
        "Ooh, good eye. Bad smell, but good eye. That's me. I smell.",
        "Sold! Don't tell the other Kevins.",
    };
    [SerializeField, TextArea] private string[] broke =
    {
        "That's more money than you have. I can count. Barely, but I can.",
        "No cash, no cone. Kevin's rule.",
        "Go splat a few more, then come back.",
    };
    [SerializeField, TextArea] private string jackpot = "JACKPOT! Ohhh, I hate that sound.";
    [SerializeField, TextArea] private string pair = "Two outta three! Have a tub. Participation sundae.";
    [SerializeField, TextArea] private string brains = "Three brains! Uh. RUN. That one's not cured.";
    [SerializeField, TextArea] private string nothing = "House wins! I'm the house. This is my house.";
    [SerializeField, TextArea] private string farewell = "Drive safe! Or don't. I'll see you at the next one anyway. Somehow.";
    private Quaternion headRest;
    private Quaternion armRest;
    private Vector3 bodyRest;
    private float saidAt = -100f;

    public override void OnInitialize()
    {
        headRest = head.localRotation;
        armRest = waveArm.localRotation;
        bodyRest = body.localPosition;
    }

    public override void OnActivate(Frame frame)
    {
        bubble.text = bubbleShadow.text = "";
        QuantumEvent.Subscribe(this, (EventPhaseChanged e) => OnPhase(e));
        QuantumEvent.Subscribe(this, (EventShopkeeperTalked e) => { if (e.Keeper == EntityRef) Say(talk[(e.Line - 1) % talk.Length]); });
        QuantumEvent.Subscribe(this, (EventPurchased e) => { if ((e.Position.ToUnityVector3() - transform.position).sqrMagnitude < hearingRange * hearingRange) Say(purchased[e.Tick % purchased.Length]); });
        QuantumEvent.Subscribe(this, (EventShopDenied e) => { if ((e.Position.ToUnityVector3() - transform.position).sqrMagnitude < hearingRange * hearingRange) Say(broke[e.Tick % broke.Length]); });
        QuantumEvent.Subscribe(this, (EventSlotsResult e) => Say(e.Tier == ShopSystem.Jackpot ? jackpot : e.Tier == ShopSystem.Pair ? pair : e.Tier == ShopSystem.Brains ? brains : nothing));
    }

    private void OnPhase(EventPhaseChanged e)
    {
        if (e.Phase == GamePhase.Depot) Say(greetings[(e.Area - 1) % greetings.Length]);
        if (e.Phase == GamePhase.Driving) Say(farewell);
    }

    private void Say(string line)
    {
        var wrapped = "";
        var column = 0;
        foreach (var word in line.Split(' '))
        {
            if (column > 0 && column + word.Length > wrapColumns)
            {
                wrapped += "\n";
                column = 0;
            }
            else if (column > 0)
            {
                wrapped += " ";
                column++;
            }
            wrapped += word;
            column += word.Length;
        }
        bubble.text = bubbleShadow.text = wrapped;
        saidAt = Time.time;
    }

    public override void OnUpdateView()
    {
        var age = Time.time - saidAt;
        var talking = age < lineTime;
        var fade = Mathf.Clamp01((lineTime - age) / 0.5f);
        bubble.color = new Color(1f, 0.93f, 0.6f, fade);
        bubbleShadow.color = new Color(0.1f, 0.06f, 0.2f, fade);
        var camera = Camera.main.transform;
        bubble.transform.parent.rotation = camera.rotation;

        body.localPosition = bodyRest + Vector3.up * (Mathf.Abs(Mathf.Sin(Time.time * (talking ? 9f : 2f))) * (talking ? 0.04f : 0.015f));
        var toCamera = transform.InverseTransformDirection(camera.position - head.position);
        var yaw = Mathf.Clamp(Mathf.Atan2(toCamera.x, toCamera.z) * Mathf.Rad2Deg, -60f, 60f);
        head.localRotation = Quaternion.Slerp(head.localRotation, Quaternion.Euler(0, yaw, talking ? Mathf.Sin(Time.time * 7f) * 6f : 0) * headRest, 1 - Mathf.Exp(-6 * Time.deltaTime));
        var wave = talking ? 0.6f + 0.4f * Mathf.Sin(Time.time * 10f) : 0f;
        waveArm.localRotation = Quaternion.Slerp(waveArm.localRotation, armRest * Quaternion.Euler(waveEuler * wave), 1 - Mathf.Exp(-8 * Time.deltaTime));
    }
}
