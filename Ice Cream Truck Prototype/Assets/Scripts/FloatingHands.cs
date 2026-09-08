using UnityEngine;

public class FloatingHands : MonoBehaviour
{
    public PlayerInteraction interaction;
    public Transform view, leftHandBone, rightHandBone, handGrip;
    public SkinnedMeshRenderer handsRenderer;
    public Mesh openHandsMesh, leftHandMesh;
    public MeshFilter closedHand;
    [SerializeField] private Vector3 leftRest = new Vector3(-.27f,-.27f,.55f);
    [SerializeField] private Vector3 rightRest = new Vector3(.27f,-.27f,.55f);
    [SerializeField] private float followSpeed = 18;
    private Quaternion rightRestRotation, boneToGripRotation;
    private void Awake()
    {
        rightRestRotation = rightHandBone.localRotation;
        boneToGripRotation = Quaternion.Inverse(rightHandBone.rotation) * handGrip.rotation;
        rightHandBone.position = view.TransformPoint(rightRest);
    }
    private void LateUpdate()
    {
        float blend=1-Mathf.Exp(-followSpeed*Time.deltaTime);
        leftHandBone.position=Vector3.Lerp(leftHandBone.position,view.TransformPoint(leftRest),blend);
        var item=interaction.Held;
        bool gripping=item!=null && !item.openHandGrip;
        handsRenderer.sharedMesh=gripping?leftHandMesh:openHandsMesh;
        closedHand.gameObject.SetActive(gripping);
        if(gripping)closedHand.sharedMesh=item.handMesh;
        if(item==null)
        {
            rightHandBone.position=Vector3.Lerp(rightHandBone.position,view.TransformPoint(rightRest),blend);
            rightHandBone.localRotation=Quaternion.Slerp(rightHandBone.localRotation,rightRestRotation,blend);
            return;
        }
        rightHandBone.rotation=item.grip.rotation*Quaternion.Inverse(boneToGripRotation);
        rightHandBone.position+=item.grip.position-handGrip.position;
    }
}
