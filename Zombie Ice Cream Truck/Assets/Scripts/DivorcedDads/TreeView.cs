using Quantum;
using UnityEngine;

// The nut tree's canopy wobbles every time it is shaken, punched, shot or rammed.
public class TreeView : QuantumEntityViewComponent
{
    [SerializeField] private Transform canopy;
    private float wobble;
    private Quaternion rest;

    public override void OnInitialize()
    {
        rest = canopy.localRotation;
        QuantumEvent.Subscribe(this, (EventTreeShaken e) => OnShaken(e));
    }

    private void OnShaken(EventTreeShaken e)
    {
        if (e.Tree == EntityRef) wobble = e.Nuts > 0 ? 1.6f : 1f;
    }

    public override void OnUpdateView()
    {
        wobble = Mathf.MoveTowards(wobble, 0, Time.deltaTime * 1.5f);
        canopy.localRotation = rest * Quaternion.Euler(Mathf.Sin(Time.time * 25) * 6 * wobble, 0, Mathf.Sin(Time.time * 19) * 5 * wobble);
    }
}
