using System;
using Photon.Deterministic;
using Quantum;
using UnityEngine;
using Random = UnityEngine.Random;

// Plays simulation events as sound: guns, splats, head pops, explosions, crashes, the bell, the shop till and the
// run jingles. One-shots are spawned from an authored audio source prefab at the event position; the local player's
// own feedback (their gun, pickups, reloads, getting hurt) plays flat so it always sits on top of the mix.
public class GameAudio : MonoBehaviour
{
    [Serializable]
    public struct GunSound
    {
        public ItemKind Gun;
        public AudioClip Clip;
    }

    [SerializeField] private AudioSource oneShotPrefab;
    [SerializeField] private Transform listener;
    [SerializeField] private QuantumEntityViewUpdater viewUpdater;
    [SerializeField] private GunSound[] gunSounds;
    [SerializeField] private AudioClip[] hits;
    [SerializeField] private AudioClip headshot;
    [SerializeField] private AudioClip kill;
    [SerializeField] private AudioClip explosion;
    [SerializeField] private AudioClip bloaterPop;
    [SerializeField] private AudioClip freeze;
    [SerializeField] private AudioClip iceShatter;
    [SerializeField] private AudioClip crash;
    [SerializeField] private AudioClip hurt;
    [SerializeField] private AudioClip snarl;
    [SerializeField] private AudioClip death;
    [SerializeField] private AudioClip revive;
    [SerializeField] private AudioClip wipe;
    [SerializeField] private AudioClip depot;
    [SerializeField] private AudioClip bell;
    [SerializeField] private AudioClip pickup;
    [SerializeField] private AudioClip kaching;
    [SerializeField] private AudioClip tip;
    [SerializeField] private AudioClip crank;
    [SerializeField] private AudioClip scoop;
    [SerializeField] private AudioClip reload;
    [SerializeField] private AudioClip empty;
    [SerializeField] private AudioClip thrown;

    private void OnEnable()
    {
        QuantumEvent.Subscribe(this, (EventShotFired e) => OnShot(e));
        QuantumEvent.Subscribe(this, (EventZombieHit e) => Play(e.Headshot ? headshot : hits[Random.Range(0, hits.Length)], e.Point, 0.8f));
        QuantumEvent.Subscribe(this, (EventZombieKilled e) => OnKilled(e));
        QuantumEvent.Subscribe(this, (EventExplosion e) => OnExplosion(e));
        QuantumEvent.Subscribe(this, (EventTruckCrashed e) => Play(crash, e.Position, 1f));
        QuantumEvent.Subscribe(this, (EventSurvivorHurt e) => OnHurt(e));
        QuantumEvent.Subscribe(this, (EventSurvivorDied e) => PlayLocal(death, 0.8f, IsLocal(e.Player)));
        QuantumEvent.Subscribe(this, (EventSurvivorRevived e) => PlayFlat(revive, 0.8f));
        QuantumEvent.Subscribe(this, (EventPhaseChanged e) => OnPhase(e));
        QuantumEvent.Subscribe(this, (EventStationUsed e) => OnStationUsed(e));
        QuantumEvent.Subscribe(this, (EventItemPickedUp e) => PlayLocal(pickup, 0.6f, IsLocal(e.Player), e.Position));
        QuantumEvent.Subscribe(this, (EventPurchased e) => PlayFlat(kaching, 0.9f));
        QuantumEvent.Subscribe(this, (EventTipEarned e) => Play(tip, e.Position, 0.7f));
        QuantumEvent.Subscribe(this, (EventReloaded e) => PlayLocal(reload, 0.8f, IsLocal(e.Player)));
        QuantumEvent.Subscribe(this, (EventGunEmpty e) => PlayLocal(empty, 0.8f, IsLocal(e.Player)));
        QuantumEvent.Subscribe(this, (EventThrown e) => PlayLocal(thrown, 0.7f, IsLocal(e.Player), e.Position));
    }

    private static bool IsLocal(PlayerRef player)
    {
        return QuantumRunner.Default.Game.PlayerIsLocal(player);
    }

    private void OnShot(EventShotFired e)
    {
        foreach (var sound in gunSounds)
        {
            if (sound.Gun != e.Gun) continue;
            if (IsLocal(e.Player)) PlayFlat(sound.Clip, 0.7f);
            else Play(sound.Clip, e.From, 0.9f);
        }
    }

    private void OnKilled(EventZombieKilled e)
    {
        Play(kill, e.Position, 1f);
        if (e.RunOver && e.Flavor == Flavor.Mint) Play(iceShatter, e.Position, 1f);
    }

    private void OnExplosion(EventExplosion e)
    {
        Play(e.Bloater ? bloaterPop : explosion, e.Position, 1f);
        if (e.Flavor == Flavor.Mint) Play(freeze, e.Position, 0.9f);
    }

    private void OnHurt(EventSurvivorHurt e)
    {
        if (!IsLocal(e.Player)) return;
        PlayFlat(hurt, 0.8f);
        PlayFlat(snarl, 0.5f);
    }

    private void OnPhase(EventPhaseChanged e)
    {
        if (e.Phase == GamePhase.Depot) PlayFlat(depot, 0.8f);
        if (e.Phase == GamePhase.Wiped) PlayFlat(wipe, 0.9f);
    }

    private void OnStationUsed(EventStationUsed e)
    {
        var position = viewUpdater.GetView(e.Station).transform.position;
        switch (e.Kind)
        {
            case StationKind.Bell: Play(bell, position, 1f, 0.02f); break;
            case StationKind.Churn: Play(crank, position, 0.8f); break;
            case StationKind.Freezer:
            case StationKind.Counter: Play(scoop, position, 0.8f); break;
            case StationKind.Hopper: Play(reload, position, 0.8f); break;
            case StationKind.GunCrate: Play(crash, position, 0.5f, 0.3f); break;
        }
    }

    private void PlayLocal(AudioClip clip, float volume, bool local, FPVector3 position = default)
    {
        if (local) PlayFlat(clip, volume);
        else if (position != default) Play(clip, position, volume);
    }

    private void Play(AudioClip clip, FPVector3 position, float volume, float pitchJitter = 0.1f)
    {
        Play(clip, position.ToUnityVector3(), volume, pitchJitter);
    }

    private void Play(AudioClip clip, Vector3 position, float volume, float pitchJitter = 0.1f)
    {
        var source = Instantiate(oneShotPrefab, position, Quaternion.identity);
        source.clip = clip;
        source.volume = volume;
        source.pitch = 1 + Random.Range(-pitchJitter, pitchJitter);
        source.Play();
        Destroy(source.gameObject, clip.length / source.pitch + 0.1f);
    }

    private void PlayFlat(AudioClip clip, float volume)
    {
        var source = Instantiate(oneShotPrefab, listener.position, Quaternion.identity);
        source.spatialBlend = 0;
        source.clip = clip;
        source.volume = volume;
        source.pitch = 1 + Random.Range(-0.05f, 0.05f);
        source.Play();
        Destroy(source.gameObject, clip.length / source.pitch + 0.1f);
    }
}
