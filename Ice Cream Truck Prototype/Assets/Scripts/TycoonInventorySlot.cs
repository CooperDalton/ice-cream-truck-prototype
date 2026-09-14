using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.UI;

public class TycoonInventorySlot : MonoBehaviour, IBeginDragHandler, IDragHandler, IEndDragHandler, IDropHandler
{
    public TycoonHUD hud;
    public Button button;
    public int index;
    private bool dragging;

    public void OnBeginDrag(PointerEventData eventData)
    {
        if (eventData.button != PointerEventData.InputButton.Left || !button.IsInteractable()) return;
        dragging = hud.BeginInventoryDrag(index);
        if (!dragging) return;
        eventData.eligibleForClick = false;
        OnDrag(eventData);
    }
    public void OnDrag(PointerEventData eventData)
    {
        if (!dragging) return;
        var icon = hud.inventoryDragIcon.rectTransform;
        RectTransformUtility.ScreenPointToLocalPointInRectangle((RectTransform)icon.parent, eventData.position, eventData.pressEventCamera, out var position);
        icon.anchoredPosition = position;
    }
    public void OnDrop(PointerEventData eventData)
    {
        if (eventData.button != PointerEventData.InputButton.Left || !button.IsInteractable() || eventData.pointerDrag == null) return;
        var source = eventData.pointerDrag.GetComponent<TycoonInventorySlot>();
        if (source != null && source.hud == hud && source.dragging) hud.DropInventoryItem(index);
    }
    public void OnEndDrag(PointerEventData eventData)
    {
        dragging = false;
        hud.EndInventoryDrag();
    }
}
