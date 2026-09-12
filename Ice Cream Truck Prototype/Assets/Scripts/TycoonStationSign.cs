using UnityEngine;

public class TycoonStationSign : MonoBehaviour
{
    private void LateUpdate()
    {
        var view = TycoonGameManager.Instance.player.view.transform;
        transform.rotation = view.rotation;
    }
}
