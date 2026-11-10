using Quantum;
using UnityEngine;

// A dad as everyone else sees him: carrying his cone, gun or ingredient, cartwheeling through the air after the van
// hits him and lying flat until he gets up, coughing in a gas cloud, frosted over with brain freeze, and slumped in
// handcuffs while busted.
public class DadView : QuantumEntityViewComponent
{
    [SerializeField] private Transform model;
    [SerializeField] private HeldItems held;
    [SerializeField] private ParticleSystem cough;
    [SerializeField] private GameObject frost;
    [SerializeField] private GameObject cuffs;
    [SerializeField] private float spinSpeed = 720f;
    private Vector3 spinAxis = Vector3.right;
    private bool down;

    public override void OnUpdateView()
    {
        var dad = GetPredictedQuantumComponent<Dad>();
        held.Show(dad.Hotbar[dad.Selected], PredictedFrame.GetSingleton<DadsRun>().ConeSize);
        var knocked = dad.Knocked > 0 || dad.Busted > 0;
        if (knocked && !down) spinAxis = Quaternion.Euler(0, Random.Range(-40f, 40f), 0) * Vector3.right;
        down = knocked;
        var dt = Time.deltaTime;
        if (knocked && dad.Fling != Photon.Deterministic.FPVector3.Zero)
        {
            model.Rotate(spinAxis, spinSpeed * dt, Space.Self);
        }
        else if (knocked)
        {
            // Landed: flat on his back, nose to the sky.
            model.localRotation = Quaternion.Slerp(model.localRotation, Quaternion.Euler(-90, 0, 0), 1 - Mathf.Exp(-12 * dt));
            model.localPosition = Vector3.Lerp(model.localPosition, new Vector3(0, 0.25f, 0), 1 - Mathf.Exp(-12 * dt));
        }
        else
        {
            model.localRotation = Quaternion.Slerp(model.localRotation, Quaternion.identity, 1 - Mathf.Exp(-10 * dt));
            model.localPosition = Vector3.Lerp(model.localPosition, Vector3.zero, 1 - Mathf.Exp(-10 * dt));
        }
        var emission = cough.emission;
        emission.rateOverTime = dad.Coughing > 0 ? 12 : 0;
        frost.SetActive(dad.Frozen > 0);
        cuffs.SetActive(dad.Busted > 0);
    }
}
