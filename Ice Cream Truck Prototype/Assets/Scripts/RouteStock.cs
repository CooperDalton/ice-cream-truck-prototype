using System;
using UnityEngine;

public class RouteStock : MonoBehaviour
{
    public enum Ingredient { Batter, Vanilla, Chocolate, Strawberry, Sprinkles }
    public RouteGameManager route;
    public FlavorSO[] flavors;
    public int capacity = 36;
    public int[] amounts = new int[5];
    public int[] packed = new int[5];
    public int[] prices = { 2, 1, 2, 2, 1 };
    public int Used { get { int total = 0; foreach (int n in amounts) total += n; return total; } }
    public int Packed { get { int total = 0; foreach (int n in packed) total += n; return total; } }
    public event EventHandler Changed;

    public bool Has(Ingredient ingredient) => amounts[(int)ingredient] > 0;
    public bool HasFlavor(FlavorSO flavor) => amounts[Array.IndexOf(flavors, flavor) + 1] > 0;
    public void Consume(Ingredient ingredient)
    {
        if (!Has(ingredient)) throw new InvalidOperationException("Ingredient already exhausted: " + ingredient);
        amounts[(int)ingredient]--;
        Changed?.Invoke(this, EventArgs.Empty);
    }
    public void ConsumeFlavor(FlavorSO flavor)
    {
        Consume((Ingredient)(Array.IndexOf(flavors, flavor) + 1));
        route.hud.RefreshStock();
    }
    public int Add(int ingredient, int quantity)
    {
        int accepted = Mathf.Min(quantity, capacity - Used);
        amounts[ingredient] += accepted;
        route.WastedStock += quantity - accepted;
        Changed?.Invoke(this, EventArgs.Empty);
        return accepted;
    }
    public void Purchase(int ingredient)
    {
        if (route.Phase == RouteGameManager.RoutePhase.Planning)
        {
            if (Used >= capacity) { route.hud.Flash("Storage is full. Use or pack some stock first."); return; }
            if (!route.Pay(prices[ingredient])) return;
            Add(ingredient, 1);
        }
        else if (route.Phase == RouteGameManager.RoutePhase.Running) route.OrderDelivery(ingredient);
    }
    public void Pack(int ingredient)
    {
        if (!route.truck.InsideTruck || route.Phase == RouteGameManager.RoutePhase.Results) return;
        if (Packed >= 6 || amounts[ingredient] == 0) { route.hud.Flash("Supply bag holds six units. Stock must be available."); return; }
        amounts[ingredient]--; packed[ingredient]++;
        Changed?.Invoke(this, EventArgs.Empty);
    }
    public void Unpack()
    {
        if (!route.truck.InsideTruck) { route.hud.Flash("Return to the truck to unload supplies."); return; }
        for (int i = 0; i < packed.Length; i++) { Add(i, packed[i]); packed[i] = 0; }
        Changed?.Invoke(this, EventArgs.Empty);
    }
}
