using System.Collections.Generic;
using PurrNet;
using PurrNet.Transports;
using UnityEngine;

// Shots and the shooter's hit points, relayed by the host. Player avatars are PurrDiction
// identities and can't carry PurrNet RPCs, so one scene object carries everyone's shots.
// Shots go out unreliable and are sent twice, a tick apart, by the shooter and again by the
// host: a lost reliable packet would arrive a resend later and the shot would be late.
public class ShotRelay : NetworkBehaviour, ITick
{
    const double ResendDelay = 0.034;

    readonly List<ShotMessage> resend = new List<ShotMessage>();
    readonly List<(ShotMessage shot, double at)> relayResend = new List<(ShotMessage, double)>();
    readonly HashSet<int> serverSeenShots = new HashSet<int>();
    readonly HashSet<int> clientSeenShots = new HashSet<int>();
    readonly List<ShotHitMessage> hitResend = new List<ShotHitMessage>();
    readonly List<(ShotHitMessage hit, double at)> relayHitResend = new List<(ShotHitMessage, double)>();
    readonly HashSet<int> serverSeenHits = new HashSet<int>();

    public void Fire(ShotMessage shot)
    {
        SendShot(shot);
        resend.Add(shot);
    }

    [ServerRpc(Channel.Unreliable, requireOwnership: false)]
    void SendShot(ShotMessage shot, RPCInfo info = default)
    {
        if (!serverSeenShots.Add(shot.shotId))
        {
            return;
        }
        shot.shooter = info.sender;
        shot.time = GameManager.Instance.ServerStamp(info.sender, shot.time);
        RelayShot(shot);
        relayResend.Add((shot, GameManager.Instance.Now));
    }

    [ObserversRpc(Channel.Unreliable)]
    void RelayShot(ShotMessage shot)
    {
        if (shot.shooter == GameManager.Instance.LocalPlayer || !clientSeenShots.Add(shot.shotId))
        {
            return;
        }
        // A shot can arrive before the shooter's avatar exists here (it just joined).
        if (GameManager.Instance.Avatars.TryGetValue(shot.shooter, out PlayerAvatar avatar))
        {
            avatar.PendingShots.Add(shot);
        }
    }

    // The shooter's hit point, so every cosmetic copy splats where the real shot landed. Sent
    // like shots (unreliable, twice): it has to arrive before the timeline reaches it.
    public void ReportShotHit(int shotId, Vector3 point)
    {
        var hit = new ShotHitMessage { time = GameManager.Instance.Now, shotId = shotId, point = point };
        SendShotHit(hit);
        hitResend.Add(hit);
    }

    [ServerRpc(Channel.Unreliable, requireOwnership: false)]
    void SendShotHit(ShotHitMessage hit, RPCInfo info = default)
    {
        if (!serverSeenHits.Add(hit.shotId))
        {
            return;
        }
        hit.shooter = info.sender;
        hit.time = GameManager.Instance.ServerStamp(info.sender, hit.time);
        RelayShotHit(hit);
        relayHitResend.Add((hit, GameManager.Instance.Now));
    }

    [ObserversRpc(Channel.Unreliable)]
    void RelayShotHit(ShotHitMessage hit)
    {
        if (hit.shooter != GameManager.Instance.LocalPlayer && Projectile.Cosmetic.TryGetValue(hit.shotId, out Projectile p))
        {
            p.ScheduleSplat(hit.point, hit.time);
        }
    }

    public void OnTick(float delta)
    {
        double now = GameManager.Instance.Now;
        for (int i = relayHitResend.Count - 1; i >= 0; i--)
        {
            if (now - relayHitResend[i].at >= ResendDelay)
            {
                RelayShotHit(relayHitResend[i].hit);
                relayHitResend.RemoveAt(i);
            }
        }
        for (int i = relayResend.Count - 1; i >= 0; i--)
        {
            if (now - relayResend[i].at >= ResendDelay)
            {
                RelayShot(relayResend[i].shot);
                relayResend.RemoveAt(i);
            }
        }
        for (int i = resend.Count - 1; i >= 0; i--)
        {
            if (now - resend[i].time >= ResendDelay)
            {
                SendShot(resend[i]);
                resend.RemoveAt(i);
            }
        }
        for (int i = hitResend.Count - 1; i >= 0; i--)
        {
            if (now - hitResend[i].time >= ResendDelay)
            {
                SendShotHit(hitResend[i]);
                hitResend.RemoveAt(i);
            }
        }
    }
}
