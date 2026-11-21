using UnityEngine;

// Primitive 11-bone body shared by kids, cops and players. Bones are rigidbodies with
// character joints; they are kinematic and posed procedurally while walking, and either
// simulated (on the machine that owns the ragdoll) or posed from a network stream.
public class Humanoid : MonoBehaviour
{
    public const int BoneCount = 11;
    public static readonly int[] Parent = { -1, 0, 1, 1, 3, 1, 5, 0, 7, 0, 9 };

    [SerializeField] Rigidbody[] bones;
    [SerializeField] float height = 1f;

    Vector3[] restLocal;
    public Rigidbody[] Bones => bones;
    public float Height => height;
    public bool Simulating { get; private set; }

    void Awake()
    {
        restLocal = new Vector3[BoneCount];
        for (int i = 0; i < BoneCount; i++)
        {
            restLocal[i] = bones[i].transform.localPosition;
        }
    }

    public void SetSimulating(bool simulate)
    {
        Simulating = simulate;
        foreach (Rigidbody bone in bones)
        {
            bone.isKinematic = !simulate;
        }
    }

    public void Capture(Vector3[] pos, Quaternion[] rot)
    {
        for (int i = 0; i < BoneCount; i++)
        {
            pos[i] = bones[i].transform.position;
            rot[i] = bones[i].transform.rotation;
        }
    }

    public void Apply(Vector3[] pos, Quaternion[] rot)
    {
        for (int i = 0; i < BoneCount; i++)
        {
            bones[i].transform.SetPositionAndRotation(pos[i], rot[i]);
        }
    }

    // Forward kinematics of the procedural walk cycle for a body standing at rootPos facing yaw.
    // phase in radians; stride 0 = standing still.
    public void StandPose(Vector3 rootPos, float yaw, float phase, float stride, Vector3[] pos, Quaternion[] rot)
    {
        float swing = Mathf.Sin(phase) * 32f * stride;
        float knee = Mathf.Max(0f, -Mathf.Cos(phase)) * 35f * stride;
        float kneeR = Mathf.Max(0f, Mathf.Cos(phase)) * 35f * stride;
        Quaternion[] local =
        {
            Quaternion.identity,
            Quaternion.Euler(4f * stride, 0f, 0f),
            Quaternion.identity,
            Quaternion.Euler(-swing, 0f, -6f),
            Quaternion.Euler(-12f * stride - 8f, 0f, 0f),
            Quaternion.Euler(swing, 0f, 6f),
            Quaternion.Euler(-12f * stride - 8f, 0f, 0f),
            Quaternion.Euler(swing, 0f, 0f),
            Quaternion.Euler(knee, 0f, 0f),
            Quaternion.Euler(-swing, 0f, 0f),
            Quaternion.Euler(kneeR, 0f, 0f),
        };
        Quaternion rootRot = Quaternion.Euler(0f, yaw, 0f);
        float bob = Mathf.Abs(Mathf.Cos(phase)) * 0.03f * stride * height;
        for (int i = 0; i < BoneCount; i++)
        {
            int p = Parent[i];
            Vector3 parentPos = p < 0 ? rootPos + Vector3.up * bob : pos[p];
            Quaternion parentRot = p < 0 ? rootRot : rot[p];
            pos[i] = parentPos + parentRot * restLocal[i];
            rot[i] = parentRot * local[i];
        }
    }

    public static void Lerp(Vector3[] aPos, Quaternion[] aRot, Vector3[] bPos, Quaternion[] bRot, float t, Vector3[] pos, Quaternion[] rot)
    {
        for (int i = 0; i < BoneCount; i++)
        {
            pos[i] = Vector3.LerpUnclamped(aPos[i], bPos[i], t);
            rot[i] = Quaternion.SlerpUnclamped(aRot[i], bRot[i], t);
        }
    }

    public float MaxBoneSpeed()
    {
        float max = 0f;
        foreach (Rigidbody bone in bones)
        {
            max = Mathf.Max(max, bone.linearVelocity.magnitude);
        }
        return max;
    }

    // Where the body stands up after a ragdoll: under the pelvis, facing from the feet toward the head.
    public void GetUpRoot(out Vector3 rootPos, out float yaw)
    {
        Vector3 pelvis = bones[0].transform.position;
        Vector3 head = bones[2].transform.position;
        Vector3 along = head - pelvis;
        along.y = 0f;
        yaw = along.sqrMagnitude > 0.0001f ? Mathf.Atan2(along.x, along.z) * Mathf.Rad2Deg : bones[0].transform.eulerAngles.y;
        rootPos = new Vector3(pelvis.x, 0f, pelvis.z);
    }
}
