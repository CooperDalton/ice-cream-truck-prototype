using System;
using System.Collections.Generic;
using UnityEngine;

public class RouteHotspot : MonoBehaviour
{
    public enum CrowdKind { Birthday, Playground, Sports, Picnic }
    [Serializable]
    public class Order
    {
        public FlavorSO[] recipe;
        public bool sprinkles;
        public int quantity, price;
        public string Label
        {
            get
            {
                var names = new List<string>();
                foreach (var flavor in recipe) names.Add(flavor.displayName);
                return string.Join(" + ", names) + (sprinkles ? " + sprinkles" : "");
            }
        }
    }
    public RouteGameManager route;
    public CrowdKind kind;
    public string displayName;
    public float routeDistance;
    public float opensAt, closesAt;
    public Order[] orders;
    public RouteCustomer[] customerPrefabs;
    public List<RouteCustomer> Customers { get; private set; } = new List<RouteCustomer>();
    public bool Available => route.Phase == RouteGameManager.RoutePhase.Running && route.Clock >= opensAt && route.Clock < closesAt;
    public int CustomerCount { get { int count = 0; foreach (var order in orders) count += order.quantity; return count; } }
    public int Revenue { get { int revenue = 0; foreach (var order in orders) revenue += order.quantity * order.price; return revenue; } }
    public int Remaining { get { int count = 0; foreach (var customer in Customers) if (!customer.Served) count++; return count; } }
    public float LaborSeconds
    {
        get
        {
            float seconds = Vector3.Distance(transform.position, route.PositionAt(routeDistance)) * 2 / route.player.settings.walkSpeed;
            foreach (var order in orders) seconds += order.quantity * (10 + order.recipe.Length * 5 + (order.sprinkles ? 3 : 0) + (kind == CrowdKind.Playground ? 3 : 0));
            return seconds;
        }
    }
    public int Difficulty => Mathf.Clamp(Mathf.CeilToInt(LaborSeconds / 40), 1, 5);
    public int RemainingFor(Order order)
    {
        int count = 0;
        foreach (var customer in Customers) if (customer.Order == order && !customer.Served) count++;
        return count;
    }
    public int[] RequiredStock(bool remainingOnly = false)
    {
        var needed = new int[5];
        foreach (var order in orders)
        {
            int quantity = remainingOnly ? RemainingFor(order) : order.quantity;
            needed[0] += quantity;
            foreach (var flavor in order.recipe) needed[Array.IndexOf(route.stock.flavors, flavor) + 1] += quantity;
            if (order.sprinkles) needed[4] += quantity;
        }
        return needed;
    }
    public void Spawn()
    {
        int index = 0;
        foreach (var order in orders)
        {
            for (int i = 0; i < order.quantity; i++)
            {
                bool child = kind == CrowdKind.Birthday || kind == CrowdKind.Playground;
                float angle = index * Mathf.PI * 2 / CustomerCount;
                Vector3 point = transform.position + new Vector3(Mathf.Cos(angle), 0, Mathf.Sin(angle)) * 2;
                var customer = Instantiate(customerPrefabs[child ? 1 : 0], point, Quaternion.identity, transform);
                customer.Initialize(this, order, index++, child);
                Customers.Add(customer);
            }
        }
    }
}
