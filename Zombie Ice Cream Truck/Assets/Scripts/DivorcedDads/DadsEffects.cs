using Quantum;
using UnityEngine;

// Turns Divorced Dads events into one-shot effects: cream bursts and ground splats where ice cream lands, lunch money
// popups, fart clouds, dust when the van bowls someone over, confetti for purchases, crash sparks, leaves off the nut
// tree, and floating words for everything that deserves one (HONK!, BUSTED!, SUGAR ALERT!...). Every effect is an
// authored prefab; this only places, tints and times them.
public class DadsEffects : MonoBehaviour
{
    [SerializeField] private QuantumEntityViewUpdater viewUpdater;
    [SerializeField] private DadsCamera cameraRig;
    [SerializeField] private DadsHud hud;
    [SerializeField] private FxBurst creamBurst;
    [SerializeField] private FxBurst bigCreamBurst;
    [SerializeField] private FxBurst gasBurst;
    [SerializeField] private FxBurst dustBurst;
    [SerializeField] private FxBurst leafBurst;
    [SerializeField] private FxBurst crashBurst;
    [SerializeField] private FxBurst confettiBurst;
    [SerializeField] private FxBurst sparkleBurst;
    [SerializeField] private GameObject muzzlePuff;
    [Tooltip("Persistent world-space system the ground splats are emitted into.")]
    [SerializeField] private ParticleSystem groundSplats;
    [SerializeField] private DadsPopup popupPrefab;

    private static readonly Color Gold = new Color(1f, 0.85f, 0.2f);
    private static readonly Color Pink = new Color(1f, 0.31f, 0.64f);
    private static readonly Color Mint = new Color(0.22f, 0.95f, 0.76f);
    private static readonly Color Siren = new Color(0.35f, 0.55f, 1f);
    private static readonly Color Green = new Color(0.6f, 0.9f, 0.3f);

    private void OnEnable()
    {
        QuantumEvent.Subscribe(this, (EventShoved e) => OnShoved(e));
        QuantumEvent.Subscribe(this, (EventGlobFired e) => OnFired(e));
        QuantumEvent.Subscribe(this, (EventGlobSplat e) => OnSplat(e));
        QuantumEvent.Subscribe(this, (EventKidPaid e) => OnPaid(e));
        QuantumEvent.Subscribe(this, (EventKidRefused e) => Say(e.Position.ToUnityVector3(), 2f, "EWW! POOR PEOPLE\nICE CREAM!", Pink, 1.1f));
        QuantumEvent.Subscribe(this, (EventSugarAlert e) => Say(e.Position.ToUnityVector3(), 2.2f, "SUGAR ALERT!\nMOM IS CALLING THE COPS", Siren, 1.2f));
        QuantumEvent.Subscribe(this, (EventUhOh e) => Say(e.Position.ToUnityVector3(), 2f, "uh oh...", Green, 1.2f));
        QuantumEvent.Subscribe(this, (EventGasReleased e) => OnGas(e));
        QuantumEvent.Subscribe(this, (EventNpcKnocked e) => OnKnocked(e.Position, e.Kind == NpcKind.Cop ? "ASSAULTING AN\nOFFICER!" : e.Happy ? "WHEEE!" : "BONK!"));
        QuantumEvent.Subscribe(this, (EventDadKnocked e) => OnKnocked(e.Position, "OOF!"));
        QuantumEvent.Subscribe(this, (EventDadBusted e) => Say(e.Position.ToUnityVector3(), 2.2f, "BUSTED! -$" + e.Fine, Siren, 1.5f));
        QuantumEvent.Subscribe(this, (EventTicketed e) => Say(e.Position.ToUnityVector3(), 2.4f, "PARKING TICKET! -$" + e.Fine, Siren, 1.4f));
        QuantumEvent.Subscribe(this, (EventCopBribed e) => Say(e.Position.ToUnityVector3(), 2.4f, "HUSH MONEY +$" + e.Amount, Gold, 1.1f));
        QuantumEvent.Subscribe(this, (EventCopSpotted e) => Say(e.Position.ToUnityVector3(), 2.4f, "HEY! YOU!", Siren, 1.3f));
        QuantumEvent.Subscribe(this, (EventChurned e) => OnChurned(e));
        QuantumEvent.Subscribe(this, (EventTheft e) => Say(e.Position.ToUnityVector3(), 2f, "HEY! THAT'S\nNOT YOURS!", Pink, 1.1f));
        QuantumEvent.Subscribe(this, (EventTreeShaken e) => OnTree(e));
        QuantumEvent.Subscribe(this, (EventGateOpened e) => OnGate(e));
        QuantumEvent.Subscribe(this, (EventBought e) => OnBought(e));
        QuantumEvent.Subscribe(this, (EventHonked e) => Say(e.Position.ToUnityVector3(), 3.6f, "HONK!", Gold, 1.6f));
        QuantumEvent.Subscribe(this, (EventBellRung e) => Say(e.Position.ToUnityVector3(), 1.8f, "DING DING DING!\nICE CREAM!", Gold, 1.4f));
        QuantumEvent.Subscribe(this, (EventFatKidArrived e) => OnFatKid(e));
        QuantumEvent.Subscribe(this, (EventVanSlammed e) => OnSlammed(e));
        QuantumEvent.Subscribe(this, (EventVanCrashed e) => OnCrash(e));
        QuantumEvent.Subscribe(this, (EventBrainFreeze e) => OnBrainFreeze(e));
        QuantumEvent.Subscribe(this, (EventGathered e) => OnGathered(e));
        QuantumEvent.Subscribe(this, (EventVaultChanged e) => OnVault(e));
    }

    private void OnShoved(EventShoved e)
    {
        if (e.Whiff) return;
        var point = e.Point.ToUnityVector3();
        var color = TreatPalette.Of(e.Treat);
        Instantiate(bigCreamBurst, point, Quaternion.identity).Play(color, 1.2f);
        for (int i = 0; i < 4; i++) GroundSplat(point + Random.insideUnitSphere * 0.6f, color, 0.3f, 0.7f);
        var words = new[] { "SPLORCH!", "OM NOM!", "FACE FULL!", "ENJOY!", "SHHLUP!" };
        Say(e.Point.ToUnityVector3(), 0.8f, words[Random.Range(0, words.Length)], color, 1.2f);
        if (Vector3.Distance(cameraRig.transform.position, point) < 2.6f) hud.Splat(color);
    }

    private void OnFired(EventGlobFired e)
    {
        var from = e.From.ToUnityVector3();
        Destroy(Instantiate(muzzlePuff, from, Quaternion.LookRotation(e.Direction.ToUnityVector3())), 0.08f);
    }

    private void OnSplat(EventGlobSplat e)
    {
        var point = e.Point.ToUnityVector3();
        var color = TreatPalette.Of(e.Treat);
        Instantiate(creamBurst, point, Quaternion.identity).Play(color, e.Target.IsValid ? 1f : 0.6f);
        GroundSplat(point, color, 0.3f, 0.6f);
    }

    private void OnPaid(EventKidPaid e)
    {
        var position = e.Position.ToUnityVector3();
        Instantiate(sparkleBurst, position + Vector3.up * 1.2f, Quaternion.identity).Play(Gold, e.Kind == NpcKind.FatKid ? 2.5f : 1f);
        Say(e.Position.ToUnityVector3(), e.Kind == NpcKind.FatKid ? 3.2f : 2f, "+$" + e.Amount + (e.Tip ? "  TIP!" : ""), Gold, e.Kind == NpcKind.FatKid ? 2f : 1.3f);
        if (e.Kind == NpcKind.FatKid)
        {
            Say(e.Position.ToUnityVector3(), 4.2f, "*BUUUURP*", Green, 2.2f);
            Instantiate(gasBurst, position + Vector3.up * 1.5f, Quaternion.identity).Play(Green, 1.5f);
            cameraRig.Jolt(0.5f, 0, false);
        }
    }

    private void OnGas(EventGasReleased e)
    {
        var position = e.Position.ToUnityVector3();
        Instantiate(gasBurst, position + Vector3.up * 0.6f, Quaternion.identity).Play(Green, e.Radius.AsFloat / 3f);
        Say(e.Position.ToUnityVector3(), 2.2f, "*PFFFRRRT*", Green, 1.8f);
        if (Vector3.Distance(cameraRig.transform.position, position) < e.Radius.AsFloat * 2) cameraRig.Jolt(0.25f, 0, false);
    }

    private void OnKnocked(Photon.Deterministic.FPVector3 at, string word)
    {
        var position = at.ToUnityVector3();
        Instantiate(dustBurst, position + Vector3.up * 0.5f, Quaternion.identity).Play(new Color(0.85f, 0.78f, 0.7f), 1f);
        Say(position, 2.2f, word, Color.white, 1.4f);
        cameraRig.Jolt(Mathf.Clamp01(1 - Vector3.Distance(cameraRig.transform.position, position) / 12f) * 0.3f, 0, false);
    }

    private void OnChurned(EventChurned e)
    {
        var position = viewUpdater.GetView(e.Fixture).transform.position;
        Instantiate(sparkleBurst, position + Vector3.up * 1.3f, Quaternion.identity).Play(TreatPalette.Of(e.Treat), 0.6f);
        Say(position, 1.6f, "+TUB OF " + TreatPalette.Name(e.Treat).ToUpper(), TreatPalette.Of(e.Treat), 0.7f);
    }

    private void OnTree(EventTreeShaken e)
    {
        var position = viewUpdater.GetView(e.Tree).transform.position;
        Instantiate(leafBurst, position + Vector3.up * 4.5f, Quaternion.identity).Play(new Color(0.35f, 0.75f, 0.3f), e.Nuts > 0 ? 2f : 1f);
        if (e.Nuts > 0) Say(position, 6f, "NUTS!", Gold, 1.6f);
    }

    private void OnGate(EventGateOpened e)
    {
        var position = viewUpdater.GetView(e.Gate).transform.position;
        Instantiate(confettiBurst, position + Vector3.up * 2f, Quaternion.identity).Play(Gold, 1.5f);
    }

    private void OnBought(EventBought e)
    {
        var position = e.Position.ToUnityVector3();
        Instantiate(confettiBurst, position + Vector3.up * 1.5f, Quaternion.identity).Play(Gold, 1f);
        Say(position, 2.8f, ShopTag.Name(e.Upgrade) + "!", Mint, 1.4f);
    }

    private void OnFatKid(EventFatKidArrived e)
    {
        Say(e.Position.ToUnityVector3(), 3.5f, "HUNGRYYYY!!", Pink, 2.5f);
        cameraRig.Jolt(0.35f, 0, false);
    }

    private void OnSlammed(EventVanSlammed e)
    {
        var position = e.Position.ToUnityVector3();
        Instantiate(dustBurst, position + Vector3.up, Quaternion.identity).Play(new Color(0.85f, 0.78f, 0.7f), 2f);
        Say(e.Position.ToUnityVector3(), 3.4f, e.Stolen > 0 ? "NOM NOM NOM  -" + e.Stolen + " SCOOPS" : "SLAM!", Pink, 1.8f);
    }

    private void OnCrash(EventVanCrashed e)
    {
        var position = e.Position.ToUnityVector3();
        var speed = Mathf.Abs(e.Speed.AsFloat);
        Instantiate(crashBurst, position, Quaternion.identity).Play(Color.white, Mathf.Clamp(speed / 10f, 0.6f, 2f));
        cameraRig.Jolt(Mathf.Clamp01(1 - Vector3.Distance(cameraRig.transform.position, position) / 15f) * Mathf.Clamp01(speed / 12f), 0, false);
        Say(position, 2.5f, "CRASH!", Color.white, 1.4f);
    }

    private void OnBrainFreeze(EventBrainFreeze e)
    {
        if (!QuantumRunner.Default.Game.PlayerIsLocal(e.Player)) return;
        hud.Splat(TreatPalette.Of(e.Treat));
        hud.Splat(TreatPalette.Of(e.Treat));
        cameraRig.Jolt(0.3f, 0, false);
    }

    private void OnGathered(EventGathered e)
    {
        var position = e.Position.ToUnityVector3();
        var color = e.Kind == DadItem.MudBucket ? TreatPalette.Of(Treat.Mud) : e.Kind == DadItem.StrawberryBasket ? Pink : e.Kind == DadItem.GoldLeaf ? Gold : TreatPalette.Of(Treat.Coffee);
        Instantiate(creamBurst, position + Vector3.up * 0.5f, Quaternion.identity).Play(color, 0.8f);
    }

    private void OnVault(EventVaultChanged e)
    {
        if (!e.Open) return;
        var position = viewUpdater.GetView(e.Vault).transform.position;
        Instantiate(sparkleBurst, position + Vector3.up * 1.5f, Quaternion.identity).Play(Gold, 1.5f);
        Say(position, 2.8f, "VAULT OPEN!", Gold, 1.4f);
    }

    private void GroundSplat(Vector3 position, Color color, float minSize, float maxSize)
    {
        if (position.y > 0.5f) return;
        var emit = new ParticleSystem.EmitParams
        {
            position = new Vector3(position.x, 0.03f + Random.value * 0.01f, position.z),
            startColor = color,
            startSize = Random.Range(minSize, maxSize),
            rotation = Random.Range(0f, 360f),
            velocity = Vector3.zero,
            applyShapeToPosition = false,
        };
        groundSplats.Emit(emit, 1);
    }

    // Floating words; skipped when too far away to read.
    private void Say(Vector3 position, float height, string message, Color color, float size)
    {
        var point = position + Vector3.up * height;
        if (Vector3.Distance(point, cameraRig.transform.position) > 60) return;
        Instantiate(popupPrefab, point, Quaternion.identity).Show(message, color, size);
    }
}
