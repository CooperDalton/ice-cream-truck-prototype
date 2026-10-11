using System;
using Photon.Deterministic;
using Quantum;
using UnityEngine;
using Random = UnityEngine.Random;

// Plays Divorced Dads events as sound: the plop of a scoop on a cone, shoves and splats, happy and disgusted kids,
// farts, sirens and whistles, coins, the churn, the horn, Big Dairy's register, and the day's rooster and chimes. One-
// shots are spawned from an authored audio source prefab at the event position; the local player's own feedback
// plays flat so it always sits on top of the mix. Also keeps the fat kid stomping and a gassed dad coughing.
public class DadsAudio : MonoBehaviour
{
    [Serializable]
    public struct GatherSound
    {
        public DadItem Kind;
        public AudioClip Clip;
    }

    [SerializeField] private AudioSource oneShotPrefab;
    [SerializeField] private Transform listener;
    [SerializeField] private QuantumEntityViewUpdater viewUpdater;
    [SerializeField] private DadsInput input;
    [SerializeField] private AudioClip shove;
    [SerializeField] private AudioClip whiff;
    [SerializeField] private AudioClip scoopShot;
    [SerializeField] private AudioClip minigun;
    [SerializeField] private AudioClip splatFace;
    [SerializeField] private AudioClip splatGround;
    [SerializeField] private AudioClip[] kidYay;
    [SerializeField] private AudioClip kidGiggle;
    [SerializeField] private AudioClip kidEww;
    [SerializeField] private AudioClip kidCry;
    [SerializeField] private AudioClip coinBurst;
    [SerializeField] private AudioClip coinPickup;
    [SerializeField] private AudioClip fatKidBurp;
    [SerializeField] private AudioClip fatKidRoar;
    [SerializeField] private AudioClip fatKidStomp;
    [SerializeField] private AudioClip[] farts;
    [SerializeField] private AudioClip cough;
    [SerializeField] private AudioClip plop;
    [SerializeField] private AudioClip refill;
    [SerializeField] private AudioClip coneGrab;
    [SerializeField] private AudioClip pickup;
    [SerializeField] private AudioClip thrown;
    [SerializeField] private GatherSound[] gatherSounds;
    [SerializeField] private AudioClip baristaHey;
    [SerializeField] private AudioClip churn;
    [SerializeField] private AudioClip treeShake;
    [SerializeField] private AudioClip nutDrop;
    [SerializeField] private AudioClip vaultOpen;
    [SerializeField] private AudioClip plateClick;
    [SerializeField] private AudioClip gateOpen;
    [SerializeField] private AudioClip cashRegister;
    [SerializeField] private AudioClip stamp;
    [SerializeField] private AudioClip honk;
    [SerializeField] private AudioClip bell;
    [SerializeField] private AudioClip crash;
    [SerializeField] private AudioClip oof;
    [SerializeField] private AudioClip tumble;
    [SerializeField] private AudioClip busted;
    [SerializeField] private AudioClip ticket;
    [SerializeField] private AudioClip whistle;
    [SerializeField] private AudioClip siren;
    [SerializeField] private AudioClip brainFreeze;
    [SerializeField] private AudioClip rooster;
    [SerializeField] private AudioClip duskChime;
    [SerializeField] private AudioClip fanfare;
    [SerializeField] private AudioClip sadTrombone;
    [SerializeField] private AudioClip lessonDing;
    private float stompTimer;
    private float coughTimer;
    private float coinTimer;

    private void OnEnable()
    {
        QuantumEvent.Subscribe(this, (EventShoved e) => Play(e.Whiff ? whiff : shove, e.Point, 1f, e.Player));
        QuantumEvent.Subscribe(this, (EventGlobFired e) => Play(e.Turret ? minigun : scoopShot, e.From, e.Turret ? 0.5f : 0.8f, e.Player));
        QuantumEvent.Subscribe(this, (EventGlobSplat e) => Play(e.Target.IsValid ? splatFace : splatGround, e.Point, 0.7f));
        QuantumEvent.Subscribe(this, (EventKidFed e) => OnFed(e));
        QuantumEvent.Subscribe(this, (EventKidPaid e) => OnPaid(e));
        QuantumEvent.Subscribe(this, (EventKidRefused e) => Play(kidEww, e.Position, 1f));
        QuantumEvent.Subscribe(this, (EventSugarAlert e) => Play(whistle, e.Position, 1f));
        QuantumEvent.Subscribe(this, (EventUhOh e) => Play(kidEww, e.Position, 0.8f, default, false, 0.75f));
        QuantumEvent.Subscribe(this, (EventGasReleased e) => Play(farts[Random.Range(0, farts.Length)], e.Position, 1f));
        QuantumEvent.Subscribe(this, (EventNpcKnocked e) => OnNpcKnocked(e));
        QuantumEvent.Subscribe(this, (EventDadKnocked e) => Play(oof, e.Position, 1f, e.Player));
        QuantumEvent.Subscribe(this, (EventDadBusted e) => Play(busted, e.Position, 1f, e.Player));
        QuantumEvent.Subscribe(this, (EventTicketed e) => Play(ticket, e.Position, 1f, default, true));
        QuantumEvent.Subscribe(this, (EventCopBribed e) => Play(coinPickup, e.Position, 0.8f));
        QuantumEvent.Subscribe(this, (EventCopSpotted e) => Play(whistle, e.Position, 1f));
        QuantumEvent.Subscribe(this, (EventCashCollected e) => OnCash(e));
        QuantumEvent.Subscribe(this, (EventChurnStarted e) => Play(churn, ViewPosition(e.Fixture), 0.8f));
        QuantumEvent.Subscribe(this, (EventScoopAdded e) => Play(plop, ViewPosition(e.Tub), 1f, e.Player, false, 0.9f + e.Count * 0.12f));
        QuantumEvent.Subscribe(this, (EventRefilled e) => { if (QuantumRunner.Default.Game.PlayerIsLocal(e.Player)) Play(refill, default(FPVector3), 0.9f, default, true); });
        QuantumEvent.Subscribe(this, (EventConeTaken e) => { if (QuantumRunner.Default.Game.PlayerIsLocal(e.Player)) Play(coneGrab, default(FPVector3), 1f, default, true); });
        QuantumEvent.Subscribe(this, (EventPickedUp e) => Play(pickup, e.Position, 0.7f, e.Player));
        QuantumEvent.Subscribe(this, (EventItemThrown e) => Play(thrown, e.Position, 0.7f, e.Player));
        QuantumEvent.Subscribe(this, (EventGathered e) => OnGathered(e));
        QuantumEvent.Subscribe(this, (EventTheft e) => Play(baristaHey, e.Position, 1f));
        QuantumEvent.Subscribe(this, (EventTreeShaken e) => OnTree(e));
        QuantumEvent.Subscribe(this, (EventVaultChanged e) => Play(e.Open ? vaultOpen : plateClick, ViewPosition(e.Vault), 1f));
        QuantumEvent.Subscribe(this, (EventSwung e) => Play(e.Open ? gateOpen : plateClick, ViewPosition(e.Fixture), 0.7f));
        QuantumEvent.Subscribe(this, (EventGateOpened e) => Play(gateOpen, ViewPosition(e.Gate), 1f));
        QuantumEvent.Subscribe(this, (EventBought e) => Play(cashRegister, e.Position, 1f, default, true));
        QuantumEvent.Subscribe(this, (EventHonked e) => Play(honk, e.Position, 1f));
        QuantumEvent.Subscribe(this, (EventBellRung e) => Play(bell, e.Position, 1f));
        QuantumEvent.Subscribe(this, (EventFatKidArrived e) => OnFatKid(e));
        QuantumEvent.Subscribe(this, (EventVanSlammed e) => OnSlammed(e));
        QuantumEvent.Subscribe(this, (EventVanCrashed e) => Play(crash, e.Position, 1f));
        QuantumEvent.Subscribe(this, (EventBrainFreeze e) => { if (QuantumRunner.Default.Game.PlayerIsLocal(e.Player)) Play(brainFreeze, default(FPVector3), 1f, default, true); });
        QuantumEvent.Subscribe(this, (EventDayPhaseChanged e) => OnPhase(e));
        QuantumEvent.Subscribe(this, (EventCollected e) => OnCollected(e));
        QuantumEvent.Subscribe(this, (EventLessonLearned e) => Play(lessonDing, default(FPVector3), 0.8f, default, true));
    }

    private FPVector3 ViewPosition(EntityRef entity)
    {
        var position = viewUpdater.GetView(entity).transform.position;
        return position.ToFPVector3();
    }

    private void OnFed(EventKidFed e)
    {
        if (e.Wanted) Play(kidGiggle, e.Position, 0.8f, default, false, Random.Range(0.95f, 1.2f));
    }

    private void OnPaid(EventKidPaid e)
    {
        if (e.Kind == NpcKind.FatKid) Play(fatKidBurp, e.Position, 1f);
        else Play(kidYay[Random.Range(0, kidYay.Length)], e.Position, 0.9f, default, false, Random.Range(0.9f, 1.25f));
        Play(coinBurst, e.Position, 0.8f);
        if (e.Bonus > 0) Play(cashRegister, e.Position, 1f);
    }

    private void OnNpcKnocked(EventNpcKnocked e)
    {
        Play(tumble, e.Position, 0.9f);
        Play(e.Kind == NpcKind.Cop ? oof : e.Happy ? kidGiggle : kidCry, e.Position, 0.9f, default, false, Random.Range(0.95f, 1.15f));
    }

    private void OnCash(EventCashCollected e)
    {
        if (!QuantumRunner.Default.Game.PlayerIsLocal(e.Player) || coinTimer > 0) return;
        coinTimer = 0.06f;
        Play(coinPickup, e.Position, 0.5f, default, true, Random.Range(0.95f, 1.15f));
    }

    private void OnGathered(EventGathered e)
    {
        foreach (var sound in gatherSounds)
        {
            if (sound.Kind == e.Kind) Play(sound.Clip, e.Position, 1f, e.Player);
        }
    }

    private void OnTree(EventTreeShaken e)
    {
        var position = ViewPosition(e.Tree);
        Play(treeShake, position, 1f);
        if (e.Nuts > 0) Play(nutDrop, position, 1f);
    }

    private void OnFatKid(EventFatKidArrived e)
    {
        Play(fatKidRoar, e.Position, 1f, default, true);
        Play(fatKidStomp, e.Position, 1f);
    }

    private void OnSlammed(EventVanSlammed e)
    {
        Play(fatKidStomp, e.Position, 1f);
        Play(crash, e.Position, 0.7f, default, false, 0.7f);
    }

    private void OnPhase(EventDayPhaseChanged e)
    {
        if (e.Phase == DayPhase.Morning) Play(rooster, default(FPVector3), 0.8f, default, true);
        if (e.Phase == DayPhase.Dusk) Play(duskChime, default(FPVector3), 0.9f, default, true);
        if (e.Phase == DayPhase.Night) Play(siren, default(FPVector3), 0.5f, default, true);
        if (e.Phase == DayPhase.Won) Play(fanfare, default(FPVector3), 1f, default, true);
        if (e.Phase == DayPhase.Repo) Play(sadTrombone, default(FPVector3), 1f, default, true);
    }

    private void OnCollected(EventCollected e)
    {
        Play(cashRegister, default(FPVector3), 1f, default, true);
        Play(stamp, default(FPVector3), 1f, default, true, 1f, 1f);
        Play(e.Paid < e.Due ? sadTrombone : fanfare, default(FPVector3), 0.9f, default, true, 1f, 1.6f);
    }

    private void Update()
    {
        var dt = Time.deltaTime;
        coinTimer -= dt;
        stompTimer -= dt;
        coughTimer -= dt;
        var game = QuantumRunner.Default?.Game;
        if (game?.Frames.Predicted == null) return;
        var frame = game.Frames.Predicted;
        if (stompTimer <= 0)
        {
            foreach (var pair in frame.GetComponentIterator<Npc>())
            {
                if (pair.Component.Kind != NpcKind.FatKid || pair.Component.State != NpcState.Chase) continue;
                stompTimer = 0.55f;
                Play(fatKidStomp, frame.Get<Transform3D>(pair.Entity).Position, 0.8f, default, false, Random.Range(0.9f, 1.1f));
            }
        }
        if (input.LocalEntity.IsValid && coughTimer <= 0 && frame.Get<Dad>(input.LocalEntity).Coughing > 0)
        {
            coughTimer = 1.6f;
            Play(cough, default(FPVector3), 0.8f, default, true, Random.Range(0.9f, 1.1f));
        }
    }

    // Spatial at the event position, or flat at the listener for the local player's own feedback (and for global cues).
    private void Play(AudioClip clip, FPVector3 position, float volume, PlayerRef player = default, bool flat = false, float pitch = 1f, float delay = 0f)
    {
        flat |= player.IsValid && QuantumRunner.Default.Game.PlayerIsLocal(player);
        var source = Instantiate(oneShotPrefab, flat ? listener.position : position.ToUnityVector3(), Quaternion.identity);
        if (flat) source.spatialBlend = 0;
        source.clip = clip;
        source.volume = volume;
        source.pitch = pitch * (1 + Random.Range(-0.05f, 0.05f));
        source.PlayDelayed(delay);
        Destroy(source.gameObject, delay + clip.length / source.pitch + 0.1f);
    }
}
