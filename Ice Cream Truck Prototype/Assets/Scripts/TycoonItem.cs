using System;
using UnityEngine;

[Serializable]
public class TycoonItem
{
    public enum Kind { None, Bowls, Cone, BasicScooper, ImprovedScooper, Tub, Batter, Topping, Serving = 11, Equipment }
    public Kind kind;
    public int variant, amount;
    public int equipmentId;
    public int loadedFlavor = -1;
    public bool cone;
    public int[] scoops = Array.Empty<int>();
    public int toppings;
    public int pendingTopping = -1;
    public float toppingProgress;
    public TycoonItem() { }
    public TycoonItem(Kind kind, int amount = 1, int variant = 0)
    {
        this.kind = kind; this.amount = amount; this.variant = variant;
    }
    public int Capacity => kind switch { Kind.Bowls => 12, Kind.Cone => 4, Kind.Tub => 24, Kind.Batter => 10, Kind.Topping => 15, _ => 1 };
    public bool Consumable => kind == Kind.Bowls || kind == Kind.Cone || kind == Kind.Tub || kind == Kind.Batter || kind == Kind.Topping;
    public bool Tool => kind == Kind.BasicScooper || kind == Kind.ImprovedScooper;
    public bool Disposable => kind != Kind.Batter && kind != Kind.Topping;
    public float Fill => Mathf.Clamp01((float)amount / Capacity);
    public TycoonItem Copy()
    {
        return JsonUtility.FromJson<TycoonItem>(JsonUtility.ToJson(this));
    }
    public bool Matches(TycoonOrder order)
    {
        if (kind != Kind.Serving || cone != order.cone || toppings != order.toppings || scoops.Length != order.flavors.Length) return false;
        var a = (int[])scoops.Clone(); var b = (int[])order.flavors.Clone();
        Array.Sort(a); Array.Sort(b); return string.Join(",", a) == string.Join(",", b);
    }
}

[Serializable]
public class TycoonInventory : ISerializationCallbackReceiver
{
    public TycoonItem[] slots;
    public TycoonInventory(int capacity) { slots = new TycoonItem[capacity]; }
    public void OnBeforeSerialize() { }
    public void OnAfterDeserialize()
    {
        for (int i = 0; i < slots.Length; i++) if (slots[i] != null && slots[i].kind == TycoonItem.Kind.None) slots[i] = null;
    }
    public int FreeSlot => Array.FindIndex(slots, x => x == null || x.kind == TycoonItem.Kind.None);
    public int Locate(TycoonItem.Kind kind, int variant = -1)
    {
        return Array.FindIndex(slots, x => x != null && x.kind == kind && (variant < 0 || x.variant == variant));
    }
    public bool Add(TycoonItem item)
    {
        if (item.kind == TycoonItem.Kind.Bowls || item.kind == TycoonItem.Kind.Cone)
        {
            foreach (var slot in slots)
            {
                if (slot == null || slot.kind != item.kind) continue;
                int moved = Mathf.Min(item.amount, slot.Capacity - slot.amount);
                slot.amount += moved; item.amount -= moved;
                if (item.amount == 0) return true;
            }
        }
        int index = FreeSlot;
        if (index < 0) return false;
        slots[index] = item; return true;
    }
    public bool Transfer(int index, TycoonInventory destination)
    {
        var item = slots[index];
        if (item == null || item.kind == TycoonItem.Kind.None) return false;
        if (!destination.Add(item)) return false;
        slots[index] = null; return true;
    }
    public static int Refill(TycoonItem source, TycoonItem target)
    {
        bool compatible = source.kind == target.kind && source.variant == target.variant && source.Consumable;
        if (!compatible || ReferenceEquals(source, target)) return 0;
        int moved = Mathf.Min(source.amount, target.Capacity - target.amount);
        source.amount -= moved; target.amount += moved; return moved;
    }
    public void Consume(int slot, int amount = 1)
    {
        var item = slots[slot];
        if (item.amount < amount) throw new InvalidOperationException("Insufficient stock");
        item.amount -= amount;
        if (item.amount == 0 && item.Disposable) slots[slot] = null;
    }
}

[Serializable]
public class TycoonOrder
{
    public enum Stage { Ordering, Pickup }
    public Stage stage;
    public bool startedWaiting;
    public int id;
    public bool cone;
    public int[] flavors;
    public int toppings;
    public float patience = 90, patienceLimit = 90;
    public float PatienceFraction => Mathf.Clamp01(patience / patienceLimit);
    public Color RewardColor => patience <= 0 ? new Color(.76f,.77f,.72f) : PatienceFraction <= .25f ? new Color(1,.68f,.38f) : PatienceFraction <= .5f ? new Color(.98f,.85f,.40f) : new Color(.43f,.76f,.61f);
    public float Tip(int site)
    {
        float maximum = Price(site) * .4f;
        return Mathf.Round(maximum * Mathf.Clamp01(PatienceFraction * 2) * 100) / 100;
    }
    public string owner = "";
    public float Price(int site)
    {
        float price = flavors.Length == 1 ? 6 : 9;
        foreach (int flavor in flavors) price += TycoonCatalogSO.Premiums[flavor];
        for (int i = 0; i < 6; i++) if ((toppings & (1 << i)) != 0) price += TycoonCatalogSO.ToppingPremiums[i];
        return price + (cone ? 4 : 0) + (site == 1 ? 1 : site == 2 ? 3 : 0);
    }
    public string Description => string.Join(" + ", Array.ConvertAll(flavors, x => TycoonCatalogSO.FlavorNames[x])) + (cone ? " cone" : " bowl") + ToppingDescription();
    private string ToppingDescription()
    {
        string text = "";
        for (int i = 0; i < 6; i++) if ((toppings & (1 << i)) != 0) text += " / " + TycoonCatalogSO.ToppingNames[i];
        return text;
    }
}
