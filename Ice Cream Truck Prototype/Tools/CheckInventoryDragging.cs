// Run after campaign loading finishes, on a backed-up tutorial save at Scoop or Deposit.
var g = TycoonGameManager.Instance;
var h = g.hud; var p = g.player; var tutorial = g.tutorial;
p.manualInput = true; g.restartRequested = true;
var checks = new System.Collections.Generic.List<string>();
void Check(bool condition, string message) { if (!condition) throw new System.Exception(message); checks.Add(message); }
Check(!g.loadingCampaign, "Campaign finished loading before input checks");
void Drag(int from, int to)
{
    var source = h.inventorySlots[from].button.GetComponent<TycoonInventorySlot>();
    var destination = h.inventorySlots[to].button.GetComponent<TycoonInventorySlot>();
    var data = new UnityEngine.EventSystems.PointerEventData(UnityEngine.EventSystems.EventSystem.current) {
        button = UnityEngine.EventSystems.PointerEventData.InputButton.Left, pointerDrag = source.gameObject,
        position = UnityEngine.RectTransformUtility.WorldToScreenPoint(null, source.transform.position), eligibleForClick = true };
    source.OnBeginDrag(data);
    Check(h.inventoryDragIcon.gameObject.activeSelf && !data.eligibleForClick, "Drag displays the item and suppresses click-to-transfer");
    data.position = UnityEngine.RectTransformUtility.WorldToScreenPoint(null, destination.transform.position);
    source.OnDrag(data); destination.OnDrop(data); source.OnEndDrag(data);
}
Check(tutorial.progress.step == TycoonTutorial.Step.Scoop || tutorial.progress.step == TycoonTutorial.Step.Deposit, "Fixture resumes during scooping tutorial");
tutorial.progress.step = TycoonTutorial.Step.Scoop;
p.inventory.slots[6].loadedFlavor = -1;
h.ToggleInventory();
var tool = p.inventory.slots[6]; var bowls = p.inventory.slots[7];
Drag(6, 7);
Check(p.inventory.slots[7] == tool && p.inventory.slots[6] == bowls && p.selected == 7, "Occupied drop swaps items and follows the equipped tool");
Drag(7, 0);
Check(p.inventory.slots[0] == tool && (p.inventory.slots[7] == null || p.inventory.slots[7].kind == TycoonItem.Kind.None) && p.selected == 0, "Empty drop moves the whole item");
var slot = h.inventorySlots[0].button.GetComponent<TycoonInventorySlot>();
var cancel = new UnityEngine.EventSystems.PointerEventData(UnityEngine.EventSystems.EventSystem.current) { pointerDrag = slot.gameObject };
slot.OnBeginDrag(cancel); slot.OnEndDrag(cancel);
Check(p.inventory.slots[0] == tool && !h.inventoryDragIcon.gameObject.activeSelf, "Dropping outside the slots leaves inventory unchanged");
slot.OnBeginDrag(cancel); h.ClosePanels(); h.DropInventoryItem(1); slot.OnEndDrag(cancel);
Check(p.inventory.slots[0] == tool && p.inventory.FreeSlot == 1, "Closing inventory cancels an active drag");
Check(h.hotbar.Concat(h.playerSlots).All(s => s.button.GetComponent<TycoonInventorySlot>().hud == h), "All player inventory views have authored drag handlers");
Check(!h.inventoryDragIcon.raycastTarget, "Dragged icon cannot block drop targets");
tutorial.progress.step = TycoonTutorial.Step.TakeOrder; tutorial.SendMessage("LateUpdate");
Check(!tutorial.itemIcon.gameObject.activeSelf, "Take order has no unrelated bowl icon (step=" + tutorial.progress.step + ", loading=" + g.loadingCampaign + ", cue=" + tutorial.uiRoot.activeSelf + ")");
tutorial.progress.step = TycoonTutorial.Step.SelectScooper; p.Select(1); tutorial.SendMessage("LateUpdate");
Check(tutorial.itemIcon.sprite == g.catalog.Icon(tool) && tutorial.input.text == "1", "Selection prompt shows the scooper and its rearranged slot");
h.ToggleInventory(); tutorial.SendMessage("LateUpdate");
var ring = tutorial.slotHighlight; var target = h.inventorySlots[0].frame.rectTransform;
Check(Vector3.Distance(ring.position, target.position) < .1f, "Tutorial highlight follows the moved item in inventory");
h.ClosePanels(); p.Select(0); tutorial.progress.step = TycoonTutorial.Step.Scoop;
var tub = tutorial.Equipment[3 + tutorial.Customer.order.flavors[0]];
p.Teleport(tub.transform.position + Vector3.right * 1.3f);
p.view.transform.rotation = Quaternion.LookRotation(tub.handTarget.position - p.view.transform.position);
Physics.SyncTransforms(); p.Aim(); p.Use(false); p.Gesture(new Vector2(0, 90), .25f);
h.SendMessage("Update"); tutorial.SendMessage("LateUpdate");
Check(p.Scooping && p.gestureProgress > 0 && h.useBar.transform.parent.gameObject.activeSelf, "Swiping displays scoop progress");
Check(!h.targetStockBar.transform.parent.gameObject.activeSelf, "Tub stock bar is hidden while scooping");
var progressCorners = new Vector3[4]; var promptCorners = new Vector3[4];
((RectTransform)h.useBar.transform.parent).GetWorldCorners(progressCorners); tutorial.instructionPanel.GetWorldCorners(promptCorners);
Check(progressCorners[0].y > promptCorners[1].y + 5, "Scoop progress sits above the tutorial prompt with a clear gap");
System.IO.Directory.CreateDirectory("Library/CodexPlaytests");
System.IO.File.WriteAllText("Library/CodexPlaytests/InventoryDragChecks.txt", "PASS\n" + string.Join("\n", checks));
ScreenCapture.CaptureScreenshot("Library/CodexPlaytests/ScoopProgressClear.png");
return string.Join("\n", checks);
