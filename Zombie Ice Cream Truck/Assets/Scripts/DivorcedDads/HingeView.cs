using Quantum;
using UnityEngine;

// A part that swings or slides while its fixture is open: the vault door, the gate arm, the pressure plate.
public class HingeView : QuantumEntityViewComponent
{
    [SerializeField] private Transform part;
    [SerializeField] private Vector3 openEuler;
    [SerializeField] private Vector3 openOffset;
    [SerializeField] private float speed = 4f;
    private Quaternion closedRotation;
    private Vector3 closedPosition;

    public override void OnInitialize()
    {
        closedRotation = part.localRotation;
        closedPosition = part.localPosition;
    }

    public override void OnUpdateView()
    {
        var open = GetPredictedQuantumComponent<Fixture>().Open;
        var blend = 1 - Mathf.Exp(-speed * Time.deltaTime);
        part.localRotation = Quaternion.Slerp(part.localRotation, open ? closedRotation * Quaternion.Euler(openEuler) : closedRotation, blend);
        part.localPosition = Vector3.Lerp(part.localPosition, open ? closedPosition + openOffset : closedPosition, blend);
    }
}
