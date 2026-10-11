using System;
using Quantum;
using UnityEngine;

// A freezer tub in the van: the tub model of its flavor, with the ice cream surface sinking into the tub as it is
// scooped out (full at the tub's capacity) and narrowing with the tub's taper.
public class TubView : QuantumEntityViewComponent
{
    [Serializable]
    public struct Fill
    {
        [Tooltip("The ice cream surface, swirl and toppings of one flavor's tub model.")]
        public Transform[] Parts;
    }

    [Tooltip("Indexed by Treat; element 0 (None) is empty.")]
    [SerializeField] private GameObject[] tubs;
    [Tooltip("Indexed by Treat; element 0 (None) is empty.")]
    [SerializeField] private Fill[] fills;
    [Tooltip("How far the surface sinks (tub model space) from full to the last scoop.")]
    [SerializeField] private float depth = 0.17f;
    [Tooltip("Width of the surface at the bottom of the tub, relative to the top.")]
    [SerializeField] private float bottomWidth = 0.9f;
    private Vector3[][] restPositions;
    private Vector3[][] restScales;

    public override void OnInitialize()
    {
        restPositions = new Vector3[fills.Length][];
        restScales = new Vector3[fills.Length][];
        for (int t = 1; t < fills.Length; t++)
        {
            var parts = fills[t].Parts;
            restPositions[t] = new Vector3[parts.Length];
            restScales[t] = new Vector3[parts.Length];
            for (int p = 0; p < parts.Length; p++)
            {
                restPositions[t][p] = parts[p].localPosition;
                restScales[t][p] = parts[p].localScale;
            }
        }
    }

    public override void OnUpdateView()
    {
        var tub = GetPredictedQuantumComponent<Fixture>();
        var settings = PredictedFrame.FindAsset(PredictedFrame.RuntimeConfig.DadsSettings);
        for (int i = 1; i < tubs.Length; i++) tubs[i].SetActive(tub.Count > 0 && i == (int)tub.Treat);
        if (tub.Count <= 0) return;
        var level = Mathf.Clamp01((float)tub.Count / settings.TubCapacity);
        var width = Mathf.Lerp(bottomWidth, 1f, level);
        var t = (int)tub.Treat;
        var parts = fills[t].Parts;
        for (int p = 0; p < parts.Length; p++)
        {
            var rest = restPositions[t][p];
            parts[p].localPosition = new Vector3(rest.x * width, rest.y - (1 - level) * depth, rest.z * width);
            parts[p].localScale = Vector3.Scale(restScales[t][p], new Vector3(width, 1, width));
        }
    }
}
