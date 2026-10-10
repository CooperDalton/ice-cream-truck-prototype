using Quantum;
using UnityEngine;

// Kids and cops: the thought bubble with the scoop they want, ice cream smeared on their face once fed, a cone to lick
// on the way home (or on a cop's break), coffee jitters, the pre-fart wobble of a lactose kid, and cartwheeling when
// the van clips them. Purely cosmetic.
public class NpcView : QuantumEntityViewComponent
{
    [SerializeField] private Transform model;
    [SerializeField] private GameObject bubble;
    [Tooltip("Scoop shown in the thought bubble, indexed by Treat; element 0 (None) is empty.")]
    [SerializeField] private GameObject[] bubbleScoops;
    [SerializeField] private Renderer faceCream;
    [Tooltip("Cone licked on the way home, indexed by Treat; element 0 (None) is empty.")]
    [SerializeField] private GameObject[] treatCones;
    [SerializeField] private float spinSpeed = 600f;
    private MaterialPropertyBlock block;
    private Treat lastTreat;
    private Vector3 spinAxis;
    private float hop;
    private float bubbleBob;

    public override void OnInitialize()
    {
        block = new MaterialPropertyBlock();
        QuantumEvent.Subscribe(this, (EventKidFed e) => OnFed(e));
    }

    public override void OnActivate(Frame frame)
    {
        lastTreat = Treat.None;
        faceCream.gameObject.SetActive(false);
        model.localRotation = Quaternion.identity;
        model.localPosition = Vector3.zero;
        spinAxis = Random.onUnitSphere;
    }

    private void OnFed(EventKidFed e)
    {
        if (e.Kid != EntityRef) return;
        lastTreat = e.Treat;
        hop = 1;
        faceCream.gameObject.SetActive(true);
        block.SetColor("_BaseColor", TreatPalette.Of(e.Treat));
        faceCream.SetPropertyBlock(block);
    }

    public override void OnUpdateView()
    {
        var npc = GetPredictedQuantumComponent<Npc>();
        var dt = Time.deltaTime;
        var hungry = npc.State == NpcState.Approach || npc.State == NpcState.Queue;
        bubble.SetActive(hungry && npc.Wants != Treat.None);
        if (bubble.activeSelf)
        {
            for (int i = 1; i < bubbleScoops.Length; i++) bubbleScoops[i].SetActive(i == (int)npc.Wants);
            bubbleBob += dt;
            bubble.transform.localPosition = new Vector3(0, Mathf.Sin(bubbleBob * 3) * 0.05f, 0);
            bubble.transform.rotation = DadsCamera.Instance.transform.rotation;
        }
        var licking = npc.State == NpcState.Happy || npc.State == NpcState.Hyper || npc.State == NpcState.Break;
        for (int i = 1; i < treatCones.Length; i++) treatCones[i].SetActive(licking && i == (int)lastTreat);

        if (npc.State == NpcState.Tumble)
        {
            if (transform.position.y > 0.05f) model.Rotate(spinAxis, spinSpeed * dt, Space.World);
            else model.localRotation = Quaternion.Slerp(model.localRotation, Quaternion.Euler(-90, 0, 0), 1 - Mathf.Exp(-10 * dt));
            return;
        }
        hop = Mathf.MoveTowards(hop, 0, dt * 3);
        var jitter = npc.State == NpcState.Hyper || npc.Gassy > 0 ? Random.insideUnitSphere * 0.04f : Vector3.zero;
        model.localPosition = Vector3.up * Mathf.Sin(hop * Mathf.PI) * 0.35f + jitter;
        var lean = npc.Gassy > 0 ? Quaternion.Euler(Mathf.Sin(Time.time * 30) * 6f, 0, 0) : Quaternion.identity;
        model.localRotation = Quaternion.Slerp(model.localRotation, lean, 1 - Mathf.Exp(-12 * dt));
    }
}
