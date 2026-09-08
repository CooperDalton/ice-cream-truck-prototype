using UnityEngine;

[ExecuteAlways]
public class PrototypeSceneReferences : MonoBehaviour
{
    public static PrototypeSceneReferences Instance { get; private set; }
    public DayManager day;
    public PlayerController player;
    public PlayerInteraction interaction;
    public WaffleMaker waffle;
    public PickupItem batter, scooper, shaker;
    public IceCreamTub[] tubs;
    public ConeHolder[] holders;
    public CustomerManager customers;
    public PrototypeHUD hud;
    public DiscardBin bin;
    public TruckController truck;
    public WorldGenerator world;
    public Boombox boombox;
    public RouteGameManager route;
    private void OnEnable()
    {
        Instance = this;
    }
}
