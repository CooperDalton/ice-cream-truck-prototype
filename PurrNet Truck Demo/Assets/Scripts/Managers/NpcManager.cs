using PurrNet;
using PurrNet.Packing;
using PurrNet.Transports;
using UnityEngine;

public struct NpcWalkSample
{
    public short index;
    public Vector2 pos;
    public float yaw;
    public float phase;
    public float stride;
}

// Wire form of a ragdoll frame: pelvis in world space, other bones relative to it in half
// precision (~1 mm), rotations as half quaternions. 168 bytes instead of 324, so each packet
// can also carry the previous frame and a single lost packet leaves no hole.
public struct RagWire
{
    public double time;
    public double ownerTime;
    public Vector3 pelvis;
    public HalfVector3[] rel;
    public HalfQuaternion[] rot;

    public static RagWire From(RagFrame f)
    {
        var w = new RagWire { time = f.time, ownerTime = f.ownerTime, pelvis = f.pos[0], rel = new HalfVector3[Humanoid.BoneCount], rot = new HalfQuaternion[Humanoid.BoneCount] };
        for (int i = 0; i < Humanoid.BoneCount; i++)
        {
            w.rel[i] = f.pos[i] - f.pos[0];
            w.rot[i] = f.rot[i];
        }
        return w;
    }

    public RagFrame ToFrame()
    {
        var f = new RagFrame { time = time, ownerTime = ownerTime, pos = new Vector3[Humanoid.BoneCount], rot = new Quaternion[Humanoid.BoneCount] };
        for (int i = 0; i < Humanoid.BoneCount; i++)
        {
            f.pos[i] = pelvis + (Vector3)rel[i];
            f.rot[i] = ((Quaternion)rot[i]).normalized;
        }
        return f;
    }
}

public struct RagFrame
{
    public double time; // owner clock when sent; server time after stamping
    public double ownerTime; // kept for log comparison against the owner's own frames
    public Vector3[] pos;
    public Quaternion[] rot;
}

// Server runs the kid and cop AI and streams walking state. A ragdoll is simulated by the
// machine that caused it (shooter or driver): it claims the NPC, simulates locally with no
// delay, streams bone poses through the server, and ends with one reliable final pose and
// stand-up spot that every machine then animates identically. No cross-machine physics
// determinism is needed because only one machine ever simulates a given ragdoll.
[DefaultExecutionOrder(-300)]
public class NpcManager : NetworkBehaviour, ITick
{
    [SerializeField] Npc[] npcs;

    public Npc[] All => npcs;

    protected override void OnSpawned(bool asServer)
    {
        for (int i = 0; i < npcs.Length; i++)
        {
            npcs[i].Init(this, i);
            if (asServer)
            {
                npcs[i].ServerInit(GameManager.Instance.Seed * 977 + i * 31);
            }
        }
    }

    void FixedUpdate()
    {
        if (!isSpawned)
        {
            return;
        }
        if (isServer)
        {
            TruckState truck = GameManager.Instance.Truck.ServerState;
            foreach (Npc npc in npcs)
            {
                npc.ServerStep(Time.fixedDeltaTime, truck, npcs);
            }
        }
        foreach (Npc npc in npcs)
        {
            npc.LocalSimStep(Time.fixedDeltaTime);
        }
    }

    void Update()
    {
        if (!isSpawned || !GameManager.Instance.ClockReady)
        {
            return;
        }
        foreach (Npc npc in npcs)
        {
            npc.Display();
        }
        // Bone colliders were moved by transform; make raycasts this frame see what is drawn.
        Physics.SyncTransforms();
    }

    public void OnTick(float delta)
    {
        if (isServer)
        {
            int count = 0;
            foreach (Npc npc in npcs)
            {
                if (npc.ServerWalking)
                {
                    count++;
                }
            }
            var samples = new NpcWalkSample[count];
            int k = 0;
            foreach (Npc npc in npcs)
            {
                if (npc.ServerWalking)
                {
                    samples[k++] = npc.ServerSample();
                }
            }
            double now = GameManager.Instance.Now;
            foreach (NpcWalkSample s in samples)
            {
                npcs[s.index].AddWalk(now, s);
            }
            WalkSnapshot(now, samples);
        }
        foreach (Npc npc in npcs)
        {
            if (npc.LocalSimulating)
            {
                RagWire frame = RagWire.From(npc.CaptureFrame());
                SendFrame(npc.Index, frame, npc.LastSentFrame ?? frame);
                npc.LastSentFrame = frame;
            }
        }
    }

    [ObserversRpc(Channel.Unreliable)]
    void WalkSnapshot(double time, NpcWalkSample[] samples)
    {
        if (isServer)
        {
            return;
        }
        GameManager.Instance.ObserveServerTime(time);
        GameManager.Instance.NoteArrival(time);
        foreach (NpcWalkSample s in samples)
        {
            npcs[s.index].AddWalk(time, s);
        }
    }

    // ---- Ragdoll ownership ----

    // Reliable but unordered: an ordered channel would hold a claim behind any earlier lost
    // packet for a round trip (head-of-line blocking).
    [ServerRpc(Channel.ReliableUnordered, requireOwnership: false)]
    public void ClaimRagdoll(int index, int bone, Vector3 dv, RPCInfo info = default)
    {
        Npc npc = npcs[index];
        if (npc.ServerRagdolling && npc.ServerOwner == info.sender)
        {
            return; // already granted by its first streamed frame
        }
        if (npc.ServerCanRagdoll)
        {
            int epoch = npc.ServerBeginRagdoll(info.sender);
            RagdollOwnerChanged(index, info.sender, epoch);
            return;
        }
        ClaimRejected(info.sender, index);
        ForwardToOwner(npc, bone, dv);
    }

    [ServerRpc(Channel.ReliableUnordered, requireOwnership: false)]
    public void ForwardImpulse(int index, int bone, Vector3 dv)
    {
        Npc npc = npcs[index];
        if (npc.ServerRagdolling)
        {
            ForwardToOwner(npc, bone, dv);
        }
    }

    void ForwardToOwner(Npc npc, int bone, Vector3 dv)
    {
        if (npc.ServerRagdolling)
        {
            ApplyImpulse(npc.ServerOwner, npc.Index, bone, dv);
        }
    }

    [TargetRpc]
    void ApplyImpulse(PlayerID target, int index, int bone, Vector3 dv)
    {
        npcs[index].ApplyRemoteImpulse(bone, dv);
    }

    [TargetRpc]
    void ClaimRejected(PlayerID target, int index)
    {
        npcs[index].OnClaimRejected();
    }

    [ObserversRpc]
    void RagdollOwnerChanged(int index, PlayerID owner, int epoch)
    {
        npcs[index].OnOwnerChanged(owner, epoch);
    }

    [ServerRpc(Channel.Unreliable, requireOwnership: false)]
    void SendFrame(int index, RagWire frame, RagWire previous, RPCInfo info = default)
    {
        Npc npc = npcs[index];
        if (npc.ServerIsStaleFrame(info.sender, frame.time))
        {
            return; // overtook its own episode's reliable end; not a new claim
        }
        if (npc.ServerCanRagdoll)
        {
            // A frame is an implicit claim, so the ragdoll starts as soon as the first frame
            // lands even if the reliable claim is still being resent.
            int epoch = npc.ServerBeginRagdoll(info.sender);
            RagdollOwnerChanged(index, info.sender, epoch);
        }
        if (npc.ServerOwner != info.sender)
        {
            return;
        }
        frame.ownerTime = frame.time;
        frame.time = GameManager.Instance.ServerStamp(info.sender, frame.time);
        previous.ownerTime = previous.time;
        previous.time = GameManager.Instance.ServerStampNoObserve(info.sender, previous.time);
        RelayFrame(index, npc.ServerEpoch, frame, previous);
    }

    [ObserversRpc(Channel.Unreliable)]
    void RelayFrame(int index, int epoch, RagWire frame, RagWire previous)
    {
        GameManager.Instance.NoteArrival(frame.time);
        npcs[index].OnFrame(epoch, previous.ToFrame());
        npcs[index].OnFrame(epoch, frame.ToFrame());
    }

    [ServerRpc(requireOwnership: false)]
    public void EndRagdoll(int index, RagFrame final, Vector3 root, float yaw, RPCInfo info = default)
    {
        Npc npc = npcs[index];
        if (!npc.ServerRagdolling || npc.ServerOwner != info.sender)
        {
            return;
        }
        final.ownerTime = final.time;
        final.time = GameManager.Instance.ServerStamp(info.sender, final.time);
        npc.ServerEndRagdoll(final.time, final.ownerTime, root, yaw);
        RelayEnd(index, npc.ServerEpoch, final, root, yaw);
    }

    [ObserversRpc]
    void RelayEnd(int index, int epoch, RagFrame final, Vector3 root, float yaw)
    {
        npcs[index].OnEnd(epoch, final, root, yaw);
    }

    // Truck footprint check on the machine that sees the truck in the present.
    public void CheckRunOvers(Vector3 truckPos, float truckYaw, Vector3 truckVelocity)
    {
        Quaternion inv = Quaternion.Inverse(Quaternion.Euler(0f, truckYaw, 0f));
        foreach (Npc npc in npcs)
        {
            if (!npc.CanBeHitLocally)
            {
                continue;
            }
            Vector3 rel = inv * (npc.DisplayRoot - truckPos);
            if (Mathf.Abs(rel.x) < TruckSim.Width * 0.5f + 0.3f && Mathf.Abs(rel.z) < TruckSim.Length * 0.5f + 0.3f)
            {
                Vector3 away = (npc.DisplayRoot - truckPos);
                away.y = 0f;
                Vector3 dv = truckVelocity * 1.3f + away.normalized * 2f + Vector3.up * 3.5f;
                npc.LocalHit(0, dv, true);
            }
        }
    }
}
