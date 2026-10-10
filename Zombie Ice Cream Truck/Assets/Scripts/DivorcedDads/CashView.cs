using Quantum;
using UnityEngine;

// Lunch money spins and bobs while it flies to a dad.
public class CashView : QuantumEntityViewComponent
{
    [SerializeField] private Transform model;
    [SerializeField] private float spin = 540f;

    public override void OnUpdateView()
    {
        model.Rotate(Vector3.up, spin * Time.deltaTime, Space.World);
        model.localPosition = Vector3.up * (0.15f + Mathf.Sin(Time.time * 8 + transform.position.x) * 0.05f);
    }
}
