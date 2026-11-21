using System.Collections.Generic;
using PurrNet;
using UnityEngine;

// One kid or cop. Holds the server AI state (server only), the walk and ragdoll timelines
// every machine samples at RenderTime, and the local ragdoll simulation on the machine that
// owns the current ragdoll.
public class Npc : MonoBehaviour
{
    public enum Show { Walk, LocalRagdoll, Stream, GetUp, LocalGetUp, Hold, PreHit }

    [SerializeField] Humanoid body;
    [SerializeField] bool isCop;

    public const float GetUpDuration = 1.1f;
    const float PoseBlendTime = 0.15f;
    const float MergeTime = 0.4f;
    const float MinRagdollTime = 1.2f;
    const float MaxRagdollTime = 6f;

    NpcManager manager;
    public int Index { get; private set; }
    public bool IsCop => isCop;

    // ---- Server AI ----
    System.Random rng;
    enum ServerMode { Walk, Ragdoll, GetUp }
    ServerMode serverMode;
    Vector2 serverPos;
    float serverYaw;
    float serverPhase;
    float serverStride;
    Vector2 wanderTarget;
    int serverEpoch;
    PlayerID serverOwner;
    double resumeAt;
    Vector3 resumeRoot;
    float resumeYaw;
    float laneOffset;
    Vector2 serverVelocity;

    // Last finished episode, so a late unreliable frame from its owner cannot reclaim the NPC.
    PlayerID lastEndOwner;
    double lastEndOwnerTime = double.MinValue;

    public bool ServerWalking => serverMode == ServerMode.Walk;
    public bool ServerRagdolling => serverMode == ServerMode.Ragdoll;
    public bool ServerCanRagdoll => serverMode != ServerMode.Ragdoll;
    public PlayerID ServerOwner => serverOwner;
    public int ServerEpoch => serverEpoch;

    // ---- Timelines on every machine ----
    readonly SnapshotBuffer<NpcWalkSample> walk = new SnapshotBuffer<NpcWalkSample>(64);
    SnapshotBuffer<RagFrame> stream = new SnapshotBuffer<RagFrame>(64);
    // The episode before the current one, kept until the timeline has played it out: a new
    // episode's first frame can arrive before the old one has been drawn to its end.
    SnapshotBuffer<RagFrame> prevStream = new SnapshotBuffer<RagFrame>(64);
    bool prevActive;
    int epoch;
    PlayerID ragOwner;
    bool ragActive;
    bool hasEnd;
    double endStamp;
    RagFrame endFrame;
    Vector3 endRoot;
    float endYaw;
    bool prevEndActive;
    double prevEndStamp;
    RagFrame prevEndFrame;
    Vector3 prevEndRoot;
    float prevEndYaw;

    // ---- Local simulation (ragdoll owner) ----
    bool localSim;
    double simStart;
    Vector3 lastPelvisVelocity;
    float stillTime;
    bool localGetUp;
    double localGetUpStart;
    readonly Vector3[] finalPos = new Vector3[Humanoid.BoneCount];
    readonly Quaternion[] finalRot = new Quaternion[Humanoid.BoneCount];
    Vector3 localRoot;
    float localYaw;

    // ---- Display ----
    readonly Vector3[] pos = new Vector3[Humanoid.BoneCount];
    readonly Quaternion[] rot = new Quaternion[Humanoid.BoneCount];
    readonly Vector3[] tmpPos = new Vector3[Humanoid.BoneCount];
    readonly Quaternion[] tmpRot = new Quaternion[Humanoid.BoneCount];
    readonly Vector3[] blendPos = new Vector3[Humanoid.BoneCount];
    readonly Quaternion[] blendRot = new Quaternion[Humanoid.BoneCount];
    double blendStart = -10;
    Vector3 blendPos0Stream;
    bool blendPending;
    double streamKnownAt;
    Show lastShow;
    Vector3 lastRoot;

    public Show Showing { get; private set; }
    public Vector3 DisplayRoot { get; private set; }
    public Vector3 DisplayVelocity { get; private set; }
    public double DisplaySourceTime { get; private set; }
    public bool LocalSimulating => localSim;
    public RagWire? LastSentFrame { get; set; }
    public Vector3 Pelvis => body.Bones[0].position;
    public bool CanBeHitLocally => Showing == Show.Walk || Showing == Show.GetUp || Showing == Show.Hold || Showing == Show.LocalGetUp;
    public bool HasEnd => hasEnd;
    public Vector3 EndRoot => endRoot;
    public float EndYaw => endYaw;
    public int Epoch => epoch;

    public void Init(NpcManager owner, int index)
    {
        manager = owner;
        Index = index;
        body.SetSimulating(false);
        foreach (Rigidbody bone in body.Bones)
        {
            bone.GetComponent<Collider>().gameObject.layer = LayerMask.NameToLayer("Ragdoll");
        }
    }

    // ================= Server AI =================

    public void ServerInit(int seed)
    {
        rng = new System.Random(seed);
        serverPos = RandomSidewalkPoint();
        wanderTarget = RandomSidewalkPoint();
        serverYaw = (float)(rng.NextDouble() * 360.0);
        laneOffset = (float)(rng.NextDouble() * 2.0 - 1.0);
    }

    Vector2 RandomSidewalkPoint()
    {
        int bx = rng.Next(TownLayout.Blocks);
        int bz = rng.Next(TownLayout.Blocks);
        Rect b = TownLayout.Buildings[bx * TownLayout.Blocks + bz];
        float side = (float)rng.NextDouble();
        float along = (float)rng.NextDouble();
        float m = TownLayout.Sidewalk * 0.5f;
        switch (rng.Next(4))
        {
            case 0: return new Vector2(b.xMin - m, Mathf.Lerp(b.yMin, b.yMax, along));
            case 1: return new Vector2(b.xMax + m, Mathf.Lerp(b.yMin, b.yMax, along));
            case 2: return new Vector2(Mathf.Lerp(b.xMin, b.xMax, side), b.yMin - m);
            default: return new Vector2(Mathf.Lerp(b.xMin, b.xMax, side), b.yMax + m);
        }
    }

    public void ServerStep(float dt, TruckState truck, Npc[] all)
    {
        if (serverMode == ServerMode.GetUp && GameManager.Instance.Now >= resumeAt)
        {
            serverMode = ServerMode.Walk;
            serverPos = new Vector2(resumeRoot.x, resumeRoot.z);
            serverYaw = resumeYaw;
            serverPhase = 0f;
            serverStride = 0f;
            serverVelocity = Vector2.zero;
        }
        if (serverMode != ServerMode.Walk)
        {
            return;
        }
        Vector2 toTruck = truck.pos - serverPos;
        float truckDistance = toTruck.magnitude;
        Vector2 target;
        float speed;
        Vector2 f = TruckSim.Forward(truck.yaw);
        Vector2 right = new Vector2(f.y, -f.x);
        if (isCop)
        {
            bool chase = truckDistance < 30f;
            target = chase ? truck.pos - f * (TruckSim.Length * 0.5f + 1.5f) - right * 1.5f : wanderTarget;
            speed = chase ? 4.6f : 1.8f;
        }
        else
        {
            bool crowd = truckDistance < 18f;
            // Kids crowd the serving window on the truck's right side.
            target = crowd ? truck.pos + right * (TruckSim.Width * 0.5f + 1.1f) + f * (laneOffset * 2f) : wanderTarget;
            speed = crowd ? 3.4f : 1.5f;
        }
        if (!isCop && truckDistance >= 18f || isCop && truckDistance >= 30f)
        {
            if ((wanderTarget - serverPos).magnitude < 1f)
            {
                wanderTarget = RandomSidewalkPoint();
            }
        }
        Vector2 to = target - serverPos;
        Vector2 desired = to.magnitude > 0.3f ? to.normalized * speed : Vector2.zero;
        serverVelocity = Vector2.MoveTowards(serverVelocity, desired, 9f * dt);
        Vector2 velocity = serverVelocity;

        // Separation from other NPCs.
        foreach (Npc other in all)
        {
            if (other == this || other.serverMode != ServerMode.Walk)
            {
                continue;
            }
            Vector2 d = serverPos - other.serverPos;
            float m = d.magnitude;
            if (m < 0.7f && m > 0.0001f)
            {
                velocity += d / m * (0.7f - m) * 6f;
            }
        }
        // Step out of the truck footprint with velocity, never by teleporting: a hard clamp
        // moved kids that stood up against the truck 15 cm in one frame on every screen.
        Vector2 rel = serverPos - truck.pos;
        float lx = Vector2.Dot(rel, right);
        float lz = Vector2.Dot(rel, f);
        float hx = TruckSim.Width * 0.5f + 0.35f;
        float hz = TruckSim.Length * 0.5f + 0.35f;
        if (Mathf.Abs(lx) < hx && Mathf.Abs(lz) < hz)
        {
            velocity += hx - Mathf.Abs(lx) < hz - Mathf.Abs(lz) ? right * (Mathf.Sign(lx) * 5f) : f * (Mathf.Sign(lz) * 5f);
        }
        velocity = Vector2.ClampMagnitude(velocity, speed + 1.5f);
        serverPos += velocity * dt;

        float moving = velocity.magnitude;
        if (moving > 0.2f)
        {
            float targetYaw = Mathf.Atan2(velocity.x, velocity.y) * Mathf.Rad2Deg;
            serverYaw = Mathf.MoveTowardsAngle(serverYaw, targetYaw, 400f * dt);
        }
        serverStride = Mathf.MoveTowards(serverStride, Mathf.Clamp01(moving / 2.5f), 3f * dt);
        serverPhase += moving * dt * 4.2f / body.Height;
    }

    public NpcWalkSample ServerSample()
    {
        return new NpcWalkSample { index = (short)Index, pos = serverPos, yaw = serverYaw, phase = serverPhase, stride = serverStride };
    }

    public int ServerBeginRagdoll(PlayerID owner)
    {
        serverMode = ServerMode.Ragdoll;
        serverOwner = owner;
        serverEpoch++;
        return serverEpoch;
    }

    public bool ServerIsStaleFrame(PlayerID sender, double ownerTime)
    {
        return sender == lastEndOwner && ownerTime <= lastEndOwnerTime;
    }

    public void ServerEndRagdoll(double stamp, double ownerTime, Vector3 root, float yaw)
    {
        lastEndOwner = serverOwner;
        lastEndOwnerTime = ownerTime;
        serverMode = ServerMode.GetUp;
        resumeAt = stamp + GetUpDuration;
        resumeRoot = root;
        resumeYaw = yaw;
    }

    // ================= Network timeline input =================

    public void AddWalk(double time, NpcWalkSample sample)
    {
        walk.Add(time, sample);
    }

    public void OnOwnerChanged(PlayerID owner, int newEpoch)
    {
        if (newEpoch < epoch)
        {
            return;
        }
        if (newEpoch > epoch)
        {
            BeginEpoch(newEpoch);
        }
        ragOwner = owner;
        if (localSim && owner != GameManager.Instance.LocalPlayer)
        {
            OnClaimRejected();
        }
    }

    void BeginEpoch(int newEpoch)
    {
        // Hit again while the last episode is still being drawn (tumbling or getting up): keep
        // drawing it until the new stream starts. The walk buffer only holds samples from
        // before the first hit.
        // Someone else hit it while we, its last owner, were still standing it up locally: our
        // stand-up is superseded (it held the kid still for a whole episode on our screen).
        if (localGetUp)
        {
            localGetUp = false;
            blendPending = true;
        }
        prevActive = ragActive && (stream.Count > 0 || hasEnd);
        prevEndActive = hasEnd;
        if (hasEnd)
        {
            prevEndStamp = endStamp;
            prevEndFrame = endFrame;
            prevEndRoot = endRoot;
            prevEndYaw = endYaw;
        }
        (prevStream, stream) = (stream, prevStream);
        stream.Clear();
        epoch = newEpoch;
        ragActive = true;
        hasEnd = false;
    }

    public void OnFrame(int frameEpoch, RagFrame frame)
    {
        if (frameEpoch < epoch)
        {
            return;
        }
        if (frameEpoch > epoch)
        {
            BeginEpoch(frameEpoch);
        }
        if (localSim || localGetUp)
        {
            return;
        }
        if (stream.Count == 0)
        {
            streamKnownAt = GameManager.Instance.RenderTime;
            GameManager.Instance.Log.Event("rag_stream_begin", "{\"npc\":" + Index + ",\"epoch\":" + frameEpoch + "}");
        }
        stream.Add(frame.time, frame);
    }

    public void OnEnd(int endEpoch, RagFrame final, Vector3 root, float yaw)
    {
        if (endEpoch == epoch - 1 && prevActive && !prevEndActive)
        {
            // The previous episode's end, overtaken by the new episode's first frame.
            prevEndActive = true;
            prevEndStamp = final.time;
            prevEndFrame = final;
            prevEndRoot = root;
            prevEndYaw = yaw;
            prevStream.Add(final.time, final);
            return;
        }
        if (endEpoch < epoch)
        {
            return;
        }
        if (endEpoch > epoch)
        {
            BeginEpoch(endEpoch);
        }
        hasEnd = true;
        endStamp = final.time;
        endFrame = final;
        // The final pose is the last stream sample, so the stream runs into it without a hold.
        stream.Add(final.time, final);
        endRoot = root;
        endYaw = yaw;
        GameManager.Instance.Log.Event("rag_end_recv", "{\"npc\":" + Index + ",\"epoch\":" + endEpoch + ",\"root\":" + FrameLogger.V(root) + ",\"yaw\":" + FrameLogger.F(yaw) + "}");
    }

    public void OnClaimRejected()
    {
        if (!localSim)
        {
            return;
        }
        // Someone else's claim won. Keep our pose as the blend start and follow their stream.
        localSim = false;
        body.SetSimulating(false);
        blendPending = true;
        GameManager.Instance.Log.Event("claim_rejected", "{\"npc\":" + Index + "}");
    }

    // ================= Local ragdoll =================

    public void LocalHit(int bone, Vector3 dv, bool fromTruck)
    {
        if (localSim)
        {
            ApplyImpulse(bone, dv);
            return;
        }
        if (!CanBeHitLocally)
        {
            manager.ForwardImpulse(Index, bone, dv);
            return;
        }
        // Optimistic claim: start simulating now from exactly what is drawn, tell the server.
        localSim = true;
        localGetUp = false;
        LastSentFrame = null;
        lastPelvisVelocity = DisplayVelocity;
        simStart = GameManager.Instance.Now;
        stillTime = 0f;
        body.SetSimulating(true);
        foreach (Rigidbody b in body.Bones)
        {
            b.linearVelocity = DisplayVelocity;
            b.angularVelocity = Vector3.zero;
        }
        ApplyImpulse(bone, dv);
        manager.ClaimRagdoll(Index, bone, dv);
        Showing = Show.LocalRagdoll;
        GameManager.Instance.Log.Event("hit", "{\"npc\":" + Index + ",\"truck\":" + (fromTruck ? 1 : 0) + ",\"pelvis\":" + FrameLogger.V(Pelvis) + "}");
    }

    void ApplyImpulse(int bone, Vector3 dv)
    {
        Rigidbody[] bones = body.Bones;
        foreach (Rigidbody b in bones)
        {
            b.AddForce(dv * 0.55f, ForceMode.VelocityChange);
        }
        bones[bone].AddForce(dv * 0.6f, ForceMode.VelocityChange);
    }

    public void ApplyRemoteImpulse(int bone, Vector3 dv)
    {
        if (localSim)
        {
            ApplyImpulse(bone, dv);
            GameManager.Instance.Log.Event("impulse_applied", "{\"npc\":" + Index + ",\"t\":" + FrameLogger.D(GameManager.Instance.Now) + ",\"dv\":" + FrameLogger.F(dv.magnitude) + "}");
        }
    }

    public RagFrame CaptureFrame()
    {
        var frame = new RagFrame { time = GameManager.Instance.Now, pos = new Vector3[Humanoid.BoneCount], rot = new Quaternion[Humanoid.BoneCount] };
        body.Capture(frame.pos, frame.rot);
        GameManager.Instance.Log.RagOwnerFrame(Index, epoch, frame);
        return frame;
    }

    public void LocalSimStep(float dt)
    {
        if (!localSim)
        {
            return;
        }
        double age = GameManager.Instance.Now - simStart;
        Vector3 v = body.Bones[0].linearVelocity;
        if ((v - lastPelvisVelocity).magnitude > 5f)
        {
            // A hard physical impact (truck, wall): logged so the analyzer can tell real
            // physics apart from network snaps.
            GameManager.Instance.Log.Event("impulse_applied", "{\"npc\":" + Index + ",\"t\":" + FrameLogger.D(GameManager.Instance.Now) + ",\"dv\":" + FrameLogger.F((v - lastPelvisVelocity).magnitude) + ",\"impact\":1}");
        }
        lastPelvisVelocity = v;
        stillTime = body.MaxBoneSpeed() < 0.3f ? stillTime + dt : 0f;
        if (age > MaxRagdollTime || age > MinRagdollTime && stillTime > 0.4f)
        {
            EndLocal();
        }
    }

    void EndLocal()
    {
        localSim = false;
        body.SetSimulating(false);
        body.GetUpRoot(out Vector3 root, out float yaw);
        localRoot = root;
        localYaw = yaw;
        RagFrame final = CaptureFrame();
        System.Array.Copy(final.pos, finalPos, Humanoid.BoneCount);
        System.Array.Copy(final.rot, finalRot, Humanoid.BoneCount);
        localGetUp = true;
        localGetUpStart = GameManager.Instance.Now;
        manager.EndRagdoll(Index, final, root, yaw);
        GameManager.Instance.Log.Event("rag_end_sent", "{\"npc\":" + Index + ",\"epoch\":" + epoch + ",\"root\":" + FrameLogger.V(root) + ",\"yaw\":" + FrameLogger.F(yaw) + "}");
    }

    // ================= Display =================

    public void Display()
    {
        double r = GameManager.Instance.RenderTime;
        double now = GameManager.Instance.Now;
        DisplaySourceTime = -1;
        if (localSim)
        {
            Showing = Show.LocalRagdoll;
            DisplayRoot = new Vector3(Pelvis.x, 0f, Pelvis.z);
        }
        else if (localGetUp)
        {
            // Owner: stand up now, then hold until the shared timeline reaches the same moment.
            float t = Mathf.Clamp01((float)((now - localGetUpStart) / GetUpDuration));
            ShowGetUp(finalPos, finalRot, localRoot, localYaw, t);
            Showing = t < 1f ? Show.LocalGetUp : Show.Hold;
            if (t >= 1f && hasEnd && r >= endStamp + GetUpDuration && TryResumeWalk(r))
            {
                localGetUp = false;
            }
        }
        else if (ragActive && hasEnd && r >= endStamp)
        {
            float t = (float)((r - endStamp) / GetUpDuration);
            if (t < 1f)
            {
                ShowGetUp(endFrame.pos, endFrame.rot, endRoot, endYaw, t);
                Showing = Show.GetUp;
            }
            else if (!TryResumeWalk(r))
            {
                ShowGetUp(endFrame.pos, endFrame.rot, endRoot, endYaw, 1f);
                Showing = Show.Hold;
            }
        }
        else if (ragActive && stream.Count > 0 && r >= stream.OldestTime)
        {
            stream.Sample(r, out RagFrame a, out RagFrame b, out float t);
            if (t > 1f)
            {
                // Newest frame lost or late: keep the tumble going briefly instead of freezing
                // and then jumping when the next frame lands. Not past the final pose.
                GameManager.Instance.Log.Underrun("ragdoll", t);
                t = hasEnd ? 1f : Mathf.Min(t, 2f);
            }
            Humanoid.Lerp(a.pos, a.rot, b.pos, b.rot, t, pos, rot);
            DisplaySourceTime = a.ownerTime + (b.ownerTime - a.ownerTime) * t;
            if (lastShow != Show.Stream || blendPending)
            {
                // Entering the stream from a different pose: decay the difference instead of snapping.
                BeginBlend(now);
            }
            ApplyBlended(now);
            Showing = Show.Stream;
            Vector3 drawn = body.Bones[0].position;
            DisplayRoot = new Vector3(drawn.x, 0f, drawn.z);
            prevEndActive = false;
            prevActive = false;
        }
        else if (prevActive && prevStream.Count > 0 && (prevEndActive ? r < prevEndStamp : r <= prevStream.NewestTime))
        {
            prevStream.Sample(r, out RagFrame a, out RagFrame b, out float t);
            Humanoid.Lerp(a.pos, a.rot, b.pos, b.rot, Mathf.Clamp01(t), pos, rot);
            ApplyBlended(now);
            Showing = Show.Stream;
            Vector3 drawn = body.Bones[0].position;
            DisplayRoot = new Vector3(drawn.x, 0f, drawn.z);
        }
        else if (prevActive && prevEndActive)
        {
            float t = Mathf.Clamp01((float)((r - prevEndStamp) / GetUpDuration));
            ShowGetUp(prevEndFrame.pos, prevEndFrame.rot, prevEndRoot, prevEndYaw, t);
            Showing = t < 1f ? Show.GetUp : Show.Hold;
        }
        else
        {
            ShowWalk(r);
        }
        if (Showing != lastShow)
        {
            GameManager.Instance.Log.Event("npc_show", "{\"npc\":" + Index + ",\"from\":" + (int)lastShow + ",\"to\":" + (int)Showing + "}");
        }
        lastShow = Showing;
        float dt = Mathf.Max(Time.deltaTime, 0.0001f);
        DisplayVelocity = Showing == Show.Walk ? (DisplayRoot - lastRoot) / dt : Vector3.zero;
        lastRoot = DisplayRoot;
    }

    bool TryResumeWalk(double r)
    {
        double resume = endStamp + GetUpDuration;
        walk.RemoveBefore(resume - 0.0001);
        if (walk.Count == 0 || walk.OldestTime < resume - 0.0001)
        {
            return false;
        }
        ragActive = false;
        hasEnd = false;
        prevEndActive = false;
        prevActive = false;
        ShowWalk(r);
        return true;
    }

    void ShowWalk(double r)
    {
        // Walk samples stop while an NPC ragdolls, so after one episode the buffer still holds
        // its walk from before the first hit. Never draw those: hold the current pose until
        // fresh samples arrive. (Drawing them put kids 21 m away for a few frames, and a
        // shooter who hit the stale copy won the claim for everyone.)
        if (walk.Count == 0 || walk.NewestTime < r - 0.25)
        {
            Showing = Show.Hold;
            return;
        }
        walk.Sample(r, out NpcWalkSample a, out NpcWalkSample b, out float t);
        if (t > 1f)
        {
            if (!ragActive)
            {
                GameManager.Instance.Log.Underrun("npc", t);
            }
            t = ragActive ? 1f : Mathf.Min(t, 2.5f);
        }
        Vector2 p = Vector2.LerpUnclamped(a.pos, b.pos, t);
        float yaw = a.yaw + Mathf.DeltaAngle(a.yaw, b.yaw) * t;
        float phase = Mathf.LerpUnclamped(a.phase, b.phase, t);
        float stride = Mathf.Lerp(a.stride, b.stride, t);
        DisplayRoot = new Vector3(p.x, 0f, p.y);
        bool preHit = false;
        if (ragActive && !localSim && stream.Count > 0 && r < stream.OldestTime)
        {
            // We already know where the ragdoll will start (the interp delay is our lookahead):
            // the shooter saw this kid a moment earlier than we draw it. Ease the walking kid
            // onto the start spot before the hit instead of yanking it afterwards.
            double s = stream.OldestTime;
            walk.Sample(s, out NpcWalkSample sa, out NpcWalkSample sb, out float st);
            Vector2 atStart = Vector2.Lerp(sa.pos, sb.pos, Mathf.Clamp01(st));
            Vector3 startPelvis = stream.Oldest.pos[0];
            Vector2 gap = new Vector2(startPelvis.x, startPelvis.z) - atStart;
            // At most 1/0.15 s of the gap per second; whatever is left at the hit goes to the
            // start blend.
            float w = Mathf.Clamp01((float)((r - streamKnownAt) / System.Math.Max(s - streamKnownAt, 0.15)));
            DisplayRoot += new Vector3(gap.x, 0f, gap.y) * (w * w * (3f - 2f * w));
            preHit = true;
        }
        body.StandPose(DisplayRoot, yaw, phase, stride, pos, rot);
        if (lastShow == Show.LocalRagdoll || blendPending)
        {
            BeginBlend(GameManager.Instance.Now);
        }
        ApplyBlended(GameManager.Instance.Now);
        Showing = preHit ? Show.PreHit : Show.Walk;
    }

    void ShowGetUp(Vector3[] fromPos, Quaternion[] fromRot, Vector3 root, float yaw, float t)
    {
        body.StandPose(root, yaw, 0f, 0f, tmpPos, tmpRot);
        float s = t * t * (3f - 2f * t);
        Humanoid.Lerp(fromPos, fromRot, tmpPos, tmpRot, s, pos, rot);
        body.Apply(pos, rot);
        DisplayRoot = Vector3.Lerp(new Vector3(fromPos[0].x, 0f, fromPos[0].z), root, s);
    }

    // Starts easing from what is drawn now to the target pose in pos/rot.
    void BeginBlend(double now)
    {
        body.Capture(blendPos, blendRot);
        blendStart = now;
        blendPos0Stream = pos[0];
        blendPending = false;
    }

    // Applies pos/rot, easing out the difference from the pose captured at blendStart: the
    // body's place merges over MergeTime (invisible inside a tumbling ragdoll), the limb layout
    // over PoseBlendTime.
    void ApplyBlended(double now)
    {
        float u = Mathf.Clamp01((float)((now - blendStart) / MergeTime));
        float v = Mathf.Clamp01((float)((now - blendStart) / PoseBlendTime));
        if (u >= 1f)
        {
            body.Apply(pos, rot);
            return;
        }
        float kPlace = 1f - u * u * (3f - 2f * u);
        float kPose = 1f - v * v * (3f - 2f * v);
        Vector3 place = (blendPos[0] - blendPos0Stream) * kPlace;
        for (int i = 0; i < Humanoid.BoneCount; i++)
        {
            Vector3 layout = (blendPos[i] - blendPos[0]) - (pos[i] - pos[0]);
            tmpPos[i] = pos[i] + place + layout * kPose;
            tmpRot[i] = Quaternion.Slerp(rot[i], blendRot[i], kPose);
        }
        body.Apply(tmpPos, tmpRot);
    }
}
