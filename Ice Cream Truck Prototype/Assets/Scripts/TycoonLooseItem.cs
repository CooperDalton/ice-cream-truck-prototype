using UnityEngine;

public class TycoonLooseItem : MonoBehaviour
{
    public TycoonItem item;
    public TycoonGameManager game;
    public Rigidbody body;
    public Transform visualRoot;
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
        if (item.Bulk)
        {
            if (player.cargo != null) return false;
            player.cargo = item;
        }
        else if (!player.inventory.Add(item)) return false;
        game.looseItems.Remove(this); Destroy(gameObject); player.RefreshHeld(); return true;
    }
}
