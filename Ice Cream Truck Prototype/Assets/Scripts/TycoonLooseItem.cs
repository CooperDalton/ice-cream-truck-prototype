using UnityEngine;

public class TycoonLooseItem : MonoBehaviour
{
    public TycoonItem item;
    public TycoonGameManager game;
    public Rigidbody body;
    public Transform visualRoot;
    public int supplySlot = -1;
    public bool levelReward;
    private void Start()
    {
        game.catalog.Display(item, visualRoot);
    }
    private void OnDestroy()
    {
        if (game != null) game.looseItems.Remove(this);
    }
    public bool Collect(TycoonPlayer player)
    {
        if (!player.PickUp(item)) return false;
        if (levelReward) game.tutorial.progress.rewardDeliverySeen = true;
        game.looseItems.Remove(this); Destroy(gameObject); player.RefreshHeld(); game.Save(); return true;
    }
}
