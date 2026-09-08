using UnityEngine;
using UnityEngine.UI;

public class WaffleIndicator : MonoBehaviour
{
    public WaffleMaker waffle;
    public PlayerInteraction player;
    public Canvas canvas;
    public GameObject panel;
    public Image ring;
    public Image clickIcon;
    public GameObject useKey;
    [SerializeField] private Color idle = new Color(.78f, .8f, .83f);
    [SerializeField] private Color ready = new Color(.3f, .8f, .52f);
    [SerializeField] private Color cooking = new Color(1, .68f, .25f);
    [SerializeField] private Color burned = new Color(.93f, .25f, .23f);

    private void LateUpdate()
    {
        bool active = waffle.State != WaffleMaker.CookState.Empty || waffle.BatterProgress > 0;
        panel.SetActive(player.day.CanPlay && !player.truck.IsDriving && (active || player.Target == waffle));
        transform.rotation = player.view.transform.rotation;
        bool finished = waffle.State == WaffleMaker.CookState.Ready || waffle.State == WaffleMaker.CookState.BatterReady;
        ring.fillAmount = finished || waffle.State == WaffleMaker.CookState.Burned ? 1 : Mathf.Max(.04f, waffle.Progress);
        ring.color = waffle.State == WaffleMaker.CookState.Burned ? burned : finished ? ready : active ? cooking : idle;
        clickIcon.gameObject.SetActive(true);
        useKey.SetActive(false);
        clickIcon.color = finished ? ready : Color.white;
    }
}
