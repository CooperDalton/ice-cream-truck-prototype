using System.Collections.Generic;
using UnityEngine;

// A scoop of ice cream on a ballistic arc. Never networked as an object: the shooter's copy
// is authoritative for hits; every other machine draws a cosmetic copy that leaves the gun as
// drawn on that screen and converges onto the shooter's trajectory within ConvergeTime.
public class Projectile : MonoBehaviour
{
    // Cosmetic copies by shot id, so the shooter's confirmed hit can splat them in place.
    public static readonly Dictionary<int, Projectile> Cosmetic = new Dictionary<int, Projectile>();

    const float ConvergeTime = 0.3f;
    const float Lifetime = 4f;
    const float Gravity = 9.81f;
    const float Radius = 0.12f;

    ShotMessage shot;
    bool authoritative;
    Vector3 start;
    Vector3 velocity;
    float age;
    bool splatted;
    float splatAge;
    bool splatScheduled;
    Vector3 scheduledPoint;
    double scheduledTime;

    public void Launch(ShotMessage message, bool isAuthoritative, Vector3 visualStart, Vector3 visualVelocity, float startAge)
    {
        shot = message;
        authoritative = isAuthoritative;
        start = visualStart;
        velocity = visualVelocity;
        age = startAge;
        transform.position = Vector3.Lerp(Ballistic(start, velocity, age), Ballistic(shot.worldOrigin, shot.worldVelocity, age), Mathf.Clamp01(age / ConvergeTime));
        if (!authoritative)
        {
            Cosmetic[shot.shotId] = this;
        }
        GameManager.Instance.Log.Event("proj_spawn", "{\"id\":" + shot.shotId + ",\"auth\":" + (authoritative ? 1 : 0) + ",\"pos\":" + FrameLogger.V(visualStart) + "}");
    }

    static Vector3 Ballistic(Vector3 origin, Vector3 v, float t)
    {
        return origin + v * t + Vector3.down * (0.5f * Gravity * t * t);
    }

    void Update()
    {
        if (splatted)
        {
            splatAge += Time.deltaTime;
            if (splatAge > 2f)
            {
                Destroy(gameObject);
            }
            return;
        }
        if (splatScheduled && GameManager.Instance.RenderTime >= scheduledTime)
        {
            Splat(scheduledPoint);
            return;
        }
        float prevAge = age;
        age += Time.deltaTime;
        // Every copy traces the shooter's true path against the same static world, so wall
        // and ground splats match on every machine. Only the shooter's copy hits NPCs; other
        // copies splat where the shooter reports its hit landed.
        Vector3 from = Ballistic(shot.worldOrigin, shot.worldVelocity, prevAge);
        Vector3 to = Ballistic(shot.worldOrigin, shot.worldVelocity, age);
        Vector3 delta = to - from;
        int mask = authoritative ? LayerMask.GetMask("World", "Ragdoll") : LayerMask.GetMask("World");
        if (Physics.SphereCast(from, Radius, delta.normalized, out RaycastHit hit, delta.magnitude, mask, QueryTriggerInteraction.Ignore))
        {
            Npc npc = hit.collider.GetComponentInParent<Npc>();
            if (npc != null)
            {
                int bone = System.Array.IndexOf(npc.GetComponent<Humanoid>().Bones, hit.rigidbody);
                npc.LocalHit(Mathf.Max(bone, 0), delta.normalized * 7f + Vector3.up * 2.5f, false);
                GameManager.Instance.Shots.ReportShotHit(shot.shotId, hit.point);
            }
            Splat(hit.point);
            return;
        }
        // Drawn path: leaves the gun as drawn here, converges onto the true path.
        float w = Mathf.Clamp01(age / ConvergeTime);
        w = w * w * (3f - 2f * w);
        transform.position = Vector3.Lerp(Ballistic(start, velocity, age), to, w);
        if (age > Lifetime || to.y < -1f)
        {
            Destroy(gameObject);
        }
    }

    public void ScheduleSplat(Vector3 point, double renderTime)
    {
        splatScheduled = true;
        scheduledPoint = point;
        scheduledTime = renderTime;
    }

    void OnDestroy()
    {
        if (!authoritative && Cosmetic.TryGetValue(shot.shotId, out Projectile p) && p == this)
        {
            Cosmetic.Remove(shot.shotId);
        }
    }

    void Splat(Vector3 point)
    {
        splatScheduled = false;
        splatted = true;
        transform.position = point;
        transform.localScale = new Vector3(0.45f, 0.12f, 0.45f);
        GameManager.Instance.Log.Event("splat", "{\"id\":" + shot.shotId + ",\"auth\":" + (authoritative ? 1 : 0) + ",\"pos\":" + FrameLogger.V(point) + "}");
    }
}
