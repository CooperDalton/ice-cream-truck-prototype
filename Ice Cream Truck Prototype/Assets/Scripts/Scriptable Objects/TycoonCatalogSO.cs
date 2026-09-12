using System;
using UnityEngine;

[CreateAssetMenu(menuName = "Ice cream/Tycoon catalog")]
public class TycoonCatalogSO : ScriptableObject
{
    public static readonly string[] FlavorNames = { "Vanilla", "Chocolate", "Strawberry", "Mint", "Cookie cream", "Cherry", "Coffee", "Mango", "Blueberry", "Peach", "Pistachio", "Blue moon" };
    public static readonly string[] ToppingNames = { "Sprinkles", "Chocolate sauce", "Cookie crumbs", "Caramel sauce", "Chopped nuts", "Whipped cream" };
    public static readonly float[] Premiums = { 0, 0, 1, 2, 2.5f, 3, 3.5f, 4, 4.5f, 5, 5.5f, 6 };
    public static readonly float[] TubPrices = { 12, 12, 18, 24, 30, 36, 42, 48, 54, 60, 66, 72 };
    public static readonly float[] ToppingPremiums = { 1.5f, 2, 2, 2.5f, 2.5f, 3 };
    public static readonly float[] RefillPrices = { 6, 9, 9, 12, 12, 15 };
    public static readonly float[] Thresholds = { 0, 60, 150, 300, 500, 750, 1100 };
    public GameObject bowl, cone, basicScooper, improvedScooper, batter, bowlPack, batterPack, flatWaffle;
    public GameObject[] tubs, scoops, toppings, toppingPacks, toppingLayers;
    public TycoonActor workerPrefab, customerPrefab;
    public TycoonPart[] partPrefabs;
    public GameObject[] placementPreviews;
    public TycoonLooseItem loosePrefab;
    public Material[] flavorMaterials;
    public Sprite bowlIcon, coneIcon, basicIcon, improvedIcon, batterIcon, bowlPackIcon, batterPackIcon;
    public Sprite[] flavorIcons, tubIcons, toppingIcons, equipmentIcons;
    public Sprite Icon(TycoonItem item)
    {
        if(item==null||item.kind==TycoonItem.Kind.None)return null;
        return item.kind switch {
            TycoonItem.Kind.Equipment=>equipmentIcons[item.variant],TycoonItem.Kind.Tub=>tubIcons[item.variant],TycoonItem.Kind.Topping=>toppingIcons[item.variant],
            TycoonItem.Kind.BasicScooper=>basicIcon,TycoonItem.Kind.ImprovedScooper=>improvedIcon,TycoonItem.Kind.Batter=>batterIcon,
            TycoonItem.Kind.Cone=>coneIcon,TycoonItem.Kind.Serving=>item.cone?coneIcon:bowlIcon,_=>bowlIcon};
    }
    public string Label(TycoonItem item)
    {
        if (item == null || item.kind == TycoonItem.Kind.None) return "Empty";
        return item.kind switch {
            TycoonItem.Kind.Equipment => partPrefabs[item.variant].kind switch { TycoonPart.Kind.ColdStorage => "Cold storage", TycoonPart.Kind.Prep => "Prep station", TycoonPart.Kind.Tub => "Ice cream tub", TycoonPart.Kind.BusinessBoard => "Business board", TycoonPart.Kind.Register => "Order counter", TycoonPart.Kind.ServingCounter => "Pickup counter", _ => partPrefabs[item.variant].kind.ToString() },
            TycoonItem.Kind.Tub => FlavorNames[item.variant], TycoonItem.Kind.Topping => ToppingNames[item.variant],
            TycoonItem.Kind.Bowls => "Bowls",
            TycoonItem.Kind.BasicScooper => "Basic scooper", TycoonItem.Kind.ImprovedScooper => "One-swipe scooper",
            TycoonItem.Kind.Serving => (item.cone ? "Cone" : "Bowl") + (item.scoops.Length > 0 ? " / " + FlavorNames[item.scoops[0]] : ""), _ => item.kind.ToString() };
    }
    public GameObject Model(TycoonItem item)
    {
        return item.kind switch {
            TycoonItem.Kind.Equipment => bowlPack,
            TycoonItem.Kind.Tub => tubs[item.variant], TycoonItem.Kind.Topping => toppings[item.variant],
            TycoonItem.Kind.BasicScooper => basicScooper, TycoonItem.Kind.ImprovedScooper => improvedScooper, TycoonItem.Kind.Batter => batter,
            TycoonItem.Kind.Cone => cone, TycoonItem.Kind.Serving => item.cone ? cone : bowl, _ => bowl };
    }
    public GameObject Display(TycoonItem item, Transform parent)
    {
        var result = Instantiate(Model(item), parent);
        result.transform.localPosition = Vector3.zero; result.transform.localRotation = Quaternion.identity;
        if (item.kind == TycoonItem.Kind.Tub) result.GetComponent<TycoonTubVisual>().SetFill(item.Fill);
        if (item.Tool && item.loadedFlavor >= 0)
        {
            var scoop = Instantiate(scoops[item.loadedFlavor], result.transform);
            scoop.transform.localPosition = new Vector3(0, .035f, -.111f);
        }
        if (item.kind == TycoonItem.Kind.Serving)
        {
            for (int i = 0; i < item.scoops.Length; i++)
            {
                var scoop = Instantiate(scoops[item.scoops[i]], result.transform);
                scoop.transform.localPosition = new Vector3((i == 0 ? -.025f : .03f), (item.cone ? .18f : .065f) + i * .06f, 0);
            }
            for (int i = 0; i < 6; i++) if ((item.toppings & (1 << i)) != 0)
            {
                var layer = Instantiate(toppingLayers[i], result.transform);
                layer.transform.localPosition = new Vector3(0, (item.cone ? .22f : .10f) + Mathf.Max(0, item.scoops.Length - 1) * .06f, 0);
            }
        }
        return result;
    }
}
