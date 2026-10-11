using Quantum;
using UnityEngine;

// Swaps a dead survivor's body for the floating spectator ghost, and squashes the body down while crouching.
public class SurvivorView : QuantumEntityViewComponent
{
    [SerializeField] private GameObject body;
    [SerializeField] private GameObject ghost;
    [SerializeField] private float crouchHeight = 0.65f;

    public override void OnUpdateView()
    {
        var survivor = GetPredictedQuantumComponent<Survivor>();
        body.SetActive(!survivor.Dead);
        ghost.SetActive(survivor.Dead);
        var height = survivor.Crouching ? crouchHeight : 1f;
        body.transform.localScale = Vector3.Lerp(body.transform.localScale, new Vector3(1, height, 1), 1 - Mathf.Exp(-14 * Time.deltaTime));
    }
}
