using UnityEngine;
using UnityEngine.UI;

public class OrderBubble : MonoBehaviour
{
    public Customer customer;
    public GameObject panel;
    public Image[] scoops;
    public GameObject sprinkles, tail;
    public Text flavors;
    public Image patience;
    [SerializeField] private float childHeight = 2.15f, adultHeight = 2.35f;
    void LateUpdate()
    {
        bool show = customer.Manager.Front == customer && customer.Arrived && !customer.Leaving && customer.Manager.truck.ServiceOpen;
        panel.SetActive(show);
        if (!show) return;
        transform.localPosition = new Vector3(0, customer.IsChild ? childHeight : adultHeight, 0);
        transform.rotation = customer.Manager.view.transform.rotation;
        for (int i = 0; i < scoops.Length; i++)
        {
            scoops[i].gameObject.SetActive(i < customer.Order.Count);
            if (i < customer.Order.Count)
            {
                scoops[i].sprite = customer.Order[i].orderPicture;
                scoops[i].color = Color.white;
            }
        }
        sprinkles.SetActive(customer.WantsSprinkles);
        sprinkles.transform.position = scoops[customer.Order.Count - 1].transform.TransformPoint(new Vector3(0, 20, 0));

        patience.fillAmount = customer.Patience / customer.Manager.settings.customerPatience;
    }
}
