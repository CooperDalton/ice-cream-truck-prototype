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
        if (!player.PickUp(item)) return false;
        game.looseItems.Remove(this); Destroy(gameObject); player.RefreshHeld(); return true;
    }
}
