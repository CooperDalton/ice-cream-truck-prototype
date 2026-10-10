using System;
using Quantum;
using UnityEngine;

// The models a dad can hold, prepared once and switched on and off: the cone (sugar, waffle or double waffle by the
// van's cone upgrade) with up to three scoops stacked on it, the guns, and the bulky ingredients carried in both
// hands. Used by both the first-person view model and the third-person body.
public class HeldItems : MonoBehaviour
{
    [Serializable]
    public struct ItemModel
    {
        public DadItem Kind;
        public GameObject Model;
    }

    [Serializable]
    public struct ScoopSlot
    {
        [Tooltip("Indexed by Treat; element 0 (None) is empty.")]
        public GameObject[] Scoops;
    }

    [Serializable]
    public struct ConeModel
    {
        public GameObject Root;
        public ScoopSlot[] Slots;
    }

    [SerializeField] private ItemModel[] items;
    [Tooltip("Sugar, waffle and double waffle cone, by the van's cone size.")]
    [SerializeField] private ConeModel[] cones;
    private DadItem shownKind = (DadItem)255;
    private int shownSize = -1;
    private int shownScoops = -1;

    // Returns true when what is shown changed (the view model dips like a quick holster).
    public bool Show(DadSlot held, DadSlot carried, int coneSize)
    {
        var item = carried.Kind != DadItem.None ? carried : held;
        // One number for the whole stack: count and the three flavors in base 6.
        var scoops = item.Kind == DadItem.Cone ? item.Count * 216 + (int)item.Scoops[0] + (int)item.Scoops[1] * 6 + (int)item.Scoops[2] * 36 : 0;
        if (item.Kind == shownKind && coneSize == shownSize && scoops == shownScoops) return false;
        var swapped = item.Kind != shownKind;
        shownKind = item.Kind;
        shownSize = coneSize;
        shownScoops = scoops;
        foreach (var model in items) model.Model.SetActive(model.Kind == item.Kind);
        for (int c = 0; c < cones.Length; c++)
        {
            var visible = item.Kind == DadItem.Cone && c == Mathf.Clamp(coneSize, 1, cones.Length) - 1;
            cones[c].Root.SetActive(visible);
            for (int s = 0; s < cones[c].Slots.Length; s++)
            {
                var scoopModels = cones[c].Slots[s].Scoops;
                for (int t = 1; t < scoopModels.Length; t++) scoopModels[t].SetActive(visible && s < item.Count && (int)item.Scoops[s] == t);
            }
        }
        return swapped;
    }
}
