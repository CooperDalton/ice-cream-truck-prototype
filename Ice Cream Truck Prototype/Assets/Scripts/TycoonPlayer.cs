using System;
using System.Linq;
using UnityEngine;
using UnityEngine.InputSystem;

public class TycoonPlayer : MonoBehaviour
{
    public TycoonGameManager game;
    public Camera view;
    public CharacterController controller;
    public Transform grip, leftHand, rightHand;
    public TycoonInventory inventory = new TycoonInventory(8);
    public int selected;
    public TycoonPart target;
    public TycoonLooseItem looseTarget;
    public TycoonWorker workerTarget;
    public TycoonActor customerTarget;
    public TycoonVehicle vehicle;
    public float pitch = 18;
    public bool manualInput;
    public string prompt;
    public float gestureProgress;
    public const string MouseSensitivityKey = "MouseSensitivity";
    public float MouseSensitivity { get; private set; }
    private float fallSpeed, scoopStroke, gestureTime;
    private TycoonPart gestureTarget;
    private bool gestureLookLocked;
    private GameObject heldVisual;
    private string heldState;
    public TycoonItem Held
    {
        get
        {
            var item = inventory.slots[selected];
            return item != null && item.kind == TycoonItem.Kind.None ? null : item;
        }
    }
    private void Awake()
    {
        MouseSensitivity = Mathf.Clamp(PlayerPrefs.GetFloat(MouseSensitivityKey, .11f), .01f, .5f);
    }
    private void Update()
    {
        RefreshHeld();
        if (manualInput) return;
        var k = Keyboard.current; var m = Mouse.current;
        if (k.escapeKey.wasPressedThisFrame) game.hud.ToggleMenu();
        if (k.mKey.wasPressedThisFrame) game.hud.ToggleMap();
        if (k.tabKey.wasPressedThisFrame) game.hud.ToggleInventory();
        bool unlocked = game.hud.AnyPanel || game.phase == TycoonGameManager.Phase.Results;
        Cursor.lockState = unlocked ? CursorLockMode.None : CursorLockMode.Locked; Cursor.visible = unlocked;
        if (unlocked || game.loadingCampaign) { CancelGesture(); game.builder.HoldPickup(null, false, 0); game.builder.AimPlacement(false); return; }
        if (k.nKey.wasPressedThisFrame && game.phase == TycoonGameManager.Phase.Preparation) game.OpenDay();
        if (k.f5Key.wasPressedThisFrame) { game.Save(); game.notice = "Game saved."; }
        if (k.qKey.wasPressedThisFrame) Drop();
        for (int i = 0; i < 8; i++) if (k[(Key)((int)Key.Digit1 + i)].wasPressedThisFrame) Select(i);
        float scroll = m.scroll.ReadValue().y;
        if (scroll != 0) Select((selected + (scroll > 0 ? 7 : 1)) % 8);
        Vector2 move = new Vector2((k.dKey.isPressed ? 1 : 0) - (k.aKey.isPressed ? 1 : 0), (k.wKey.isPressed ? 1 : 0) - (k.sKey.isPressed ? 1 : 0));
        if (gestureTarget == null && !gestureLookLocked)
        {
            var delta = m.delta.ReadValue(); transform.Rotate(0, delta.x * MouseSensitivity, 0);
            pitch = Mathf.Clamp(pitch - delta.y * MouseSensitivity, -80, 80); view.transform.localRotation = Quaternion.Euler(pitch, 0, 0);
        }
        if (vehicle != null)
        {
            game.builder.HoldPickup(null, false, 0);
            vehicle.Drive(move, Time.deltaTime);
            if (k.eKey.wasPressedThisFrame) vehicle.Exit();
            return;
        }
        if (controller.isGrounded && fallSpeed < 0) fallSpeed = -2;
        if (controller.isGrounded && k.spaceKey.wasPressedThisFrame) fallSpeed = 5;
        fallSpeed -= 20 * Time.deltaTime;
        controller.Move((transform.TransformDirection(new Vector3(move.x, 0, move.y).normalized) * (k.leftShiftKey.isPressed ? 6 : 3.5f) + Vector3.up * fallSpeed) * Time.deltaTime);
        Aim();
        game.builder.AimPlacement(k.rKey.wasPressedThisFrame);
        game.builder.HoldPickup(target, m.rightButton.isPressed, Time.deltaTime);
        if (m.rightButton.isPressed) { CancelGesture(); return; }
        if (k.eKey.wasPressedThisFrame) Use(true);
        if (k.fKey.wasPressedThisFrame && target != null && (target.kind == TycoonPart.Kind.Bike || target.kind == TycoonPart.Kind.Truck)) game.hud.OpenStorage(target.storage, "Vehicle cargo");
        if (m.leftButton.wasPressedThisFrame) Use(false);
        if (m.leftButton.isPressed && gestureTarget != null) Gesture(m.delta.ReadValue(), Time.deltaTime);
        if (m.leftButton.wasReleasedThisFrame) CancelGesture();
    }
    public void Aim()
    {
        target = null; looseTarget = null; workerTarget = null; customerTarget = null; prompt = "";
        if (!Physics.Raycast(view.transform.position, view.transform.forward, out var hit, 2.8f, Physics.DefaultRaycastLayers, QueryTriggerInteraction.Ignore)) return;
        target = hit.collider.GetComponentInParent<TycoonPart>();
        looseTarget = hit.collider.GetComponentInParent<TycoonLooseItem>();
        workerTarget = hit.collider.GetComponentInParent<TycoonWorker>();
        var actor = hit.collider.GetComponentInParent<TycoonActor>();
        if (actor != null && !actor.worker && !actor.leaving) customerTarget = actor;
        if (target != null) prompt = target.Prompt();
        if (game.builder.CanPack(target, out var packReason)) prompt += " / Hold right-click to pack";
        else if (packReason != "") prompt += " / " + packReason;
        if (looseTarget != null) prompt = "E / pick up " + game.catalog.Label(looseTarget.item);
        if (workerTarget != null) prompt = "E / inspect employee and equipment";
        if (customerTarget != null) prompt = customerTarget.order.owner != "" ? "Employee is handling this order" : customerTarget.ReadyToOrder ? "E / take order" : customerTarget.ReadyForPickup ? "E / deliver order" : "Customer is joining the queue";
    }
    public void Select(int slot)
    {
        CancelGesture(); selected = slot; RefreshHeld();
    }
    public bool PickUp(TycoonItem item)
    {
        int slot = inventory.FreeSlot;
        if (item.kind == TycoonItem.Kind.Bowls || item.kind == TycoonItem.Kind.Cone)
        {
            int stack = Array.FindIndex(inventory.slots, s => s != null && s.kind == item.kind && s.amount < s.Capacity);
            if (stack >= 0) slot = stack;
        }
        int before = item.amount;
        bool added = inventory.Add(item);
        if (added || item.amount < before) Select(slot);
        return added;
    }
    public void Use(bool take)
    {
        if (customerTarget != null)
        {
            if (!take || customerTarget.order.owner != "") return;
            if (customerTarget.ReadyToOrder) customerTarget.TakeOrder();
            else if (customerTarget.ReadyForPickup)
            {
                if (Held == null || !Held.Matches(customerTarget.order)) { game.notice = "Hold the matching completed order to deliver it."; return; }
                game.Pay(customerTarget, Held); inventory.slots[selected] = null; RefreshHeld();
            }
            return;
        }
        if (Held != null && Held.kind == TycoonItem.Kind.Equipment)
        {
            if (!take) game.builder.PlaceHeld();
            return;
        }
        if (!take && Held != null && (Held.kind == TycoonItem.Kind.Bowls || Held.kind == TycoonItem.Kind.Serving && !Held.cone))
        {
            bool deliver = target != null && target.kind == TycoonPart.Kind.ServingCounter && game.sites[target.site].queue.Any(c => c.ReadyForPickup && Held.Matches(c.order));
            if (!deliver) { game.builder.PlaceHeld(); return; }
        }
        if (workerTarget != null && take) { game.hud.OpenEmployee(workerTarget); return; }
        if (looseTarget != null) { if (!looseTarget.Collect(this)) game.notice = "Make room before picking that up."; return; }
        if (target == null) return;
        var item = Held;
        if (!target.Available("Player")) { game.notice = "This equipment is being used by " + target.claimedBy; return; }
        if (target.kind == TycoonPart.Kind.Supplier) { game.hud.OpenShop(); return; }
        if (target.kind == TycoonPart.Kind.Plot || target.kind == TycoonPart.Kind.BusinessBoard) { game.hud.OpenBusiness(target.site); return; }
        if (target.kind == TycoonPart.Kind.Sign)
        {
            if (!game.sites[target.site].owned) { game.hud.OpenBusiness(target.site); return; }
            if (game.phase == TycoonGameManager.Phase.Preparation) game.OpenDay();
            else { game.sites[target.site].open = !game.sites[target.site].open; game.notice = game.sites[target.site].open ? "Stand open" : "Stand closed for a supply run"; }
            return;
        }
        if (target.kind == TycoonPart.Kind.Bike || target.kind == TycoonPart.Kind.Truck)
        {
            if (take) (target.kind == TycoonPart.Kind.Bike ? game.bike : game.truck).Enter();
            else game.hud.OpenStorage(target.storage, "Vehicle cargo");
            return;
        }
        if (target.kind == TycoonPart.Kind.Locker || target.kind == TycoonPart.Kind.ColdStorage || target.kind == TycoonPart.Kind.Shelf)
        { game.hud.OpenStorage(target.storage, target.kind == TycoonPart.Kind.ColdStorage ? "Cold storage" : target.kind == TycoonPart.Kind.Locker ? "Staff locker" : "Shelf"); return; }
        if (target.kind == TycoonPart.Kind.Trash)
        {
            inventory.slots[selected] = null;
            CancelGesture(); return;
        }
        if (target.kind == TycoonPart.Kind.Tub && item != null)
        {
            if (item.kind == TycoonItem.Kind.Tub)
            {
                if (target.contents.amount == 0 && game.phase == TycoonGameManager.Phase.Preparation) { target.variant = item.variant; target.contents.variant = item.variant; }
                int moved = TycoonInventory.Refill(item, target.contents);
                game.notice = moved > 0 ? "Tub topped up." : "Use a matching tub with room to refill.";
                if (item.amount == 0) inventory.slots[selected] = null;
                return;
            }
            if (item.Tool && item.loadedFlavor < 0 && target.contents.amount > 0) BeginGesture(target);
            return;
        }
        if (target.kind == TycoonPart.Kind.Prep || target.kind == TycoonPart.Kind.Bowl)
        {
            if (take && target.contents != null)
            {
                if (PickUp(target.contents))
                {
                    target.contents = null; target.claimedBy = "";
                    if (target.kind == TycoonPart.Kind.Bowl) { target.RemoveBowl(); target = null; }
                }
                else game.notice = "Your inventory is full.";
                return;
            }
            if (item == null) return;
            if (target.kind == TycoonPart.Kind.Prep && target.contents == null && (item.kind == TycoonItem.Kind.Cone || item.kind == TycoonItem.Kind.Serving && item.cone))
            {
                target.contents = item.kind == TycoonItem.Kind.Serving ? item : new TycoonItem(TycoonItem.Kind.Serving) { cone = item.kind == TycoonItem.Kind.Cone };
                if (item.kind == TycoonItem.Kind.Serving) inventory.slots[selected] = null; else inventory.Consume(selected);
            }
            else if (item.Tool) target.Deposit(item, "Player");
            else if (item.kind == TycoonItem.Kind.Topping && target.BeginTopping(item, "Player"))
            {
                BeginGesture(target); gestureTime = target.contents.toppingProgress * (item.variant % 2 == 0 ? 1 : 1.5f);
            }
            return;
        }
        if (target.kind == TycoonPart.Kind.Iron)
        {
            if ((target.ironStage == 0 || target.ironStage == 5) && item != null && item.kind == TycoonItem.Kind.Batter && (item.amount > 0 || target.ironStage == 5))
            {
                if (target.ironStage == 0) target.BeginPour(item, "Player");
                BeginGesture(target); gestureTime = target.pourProgress;
            }
            else if (target.ironStage == 1) target.CloseIron("Player");
            else if (target.ironStage == 2) target.OpenIron("Player");
            else if (target.ironStage == 3 && inventory.FreeSlot >= 0) PickUp(target.TakeCone("Player"));
            else if (target.ironStage == 4) { target.ironStage = 0; target.contents = null; target.claimedBy = ""; }
            return;
        }
        if (target.kind == TycoonPart.Kind.ServingCounter && item != null && item.kind == TycoonItem.Kind.Serving)
        {
            var customer = game.sites[target.site].queue.FirstOrDefault(c => c.order.owner == "" && c.ReadyForPickup && item.Matches(c.order));
            if (customer == null) { game.notice = "The serving does not match a waiting order."; return; }
            game.Pay(customer, item); inventory.slots[selected] = null;
        }
    }
    private void BeginGesture(TycoonPart part)
    {
        if (!part.Claim("Player")) return;
        gestureTarget = part; gestureLookLocked = true; gestureProgress = 0; scoopStroke = .5f; gestureTime = 0;
    }
    public void Gesture(Vector2 delta, float dt)
    {
        var item = Held;
        if (gestureTarget.kind == TycoonPart.Kind.Tub)
        {
            float previous = scoopStroke;
            scoopStroke = Mathf.Clamp01(scoopStroke + delta.y / 180);
            float travel = Mathf.Abs(scoopStroke - previous) * 180;
            bool improved = item.kind == TycoonItem.Kind.ImprovedScooper;
            gestureProgress += Mathf.Min(travel / (improved ? 140 : 400), dt / (improved ? .35f : 1));
            if (gestureProgress >= 1 && gestureTarget.Scoop(item, "Player")) { game.notice = "Scoop ready. Place it in your bowl or cone."; CancelGesture(false); }
        }
        else
        {
            bool moving = delta.sqrMagnitude > 1 || item.kind == TycoonItem.Kind.Batter || item.variant == 5;
            if (moving) gestureTime += dt;
            if (gestureTarget.kind == TycoonPart.Kind.Iron) gestureTarget.pourProgress = Mathf.Clamp01(gestureTime);
            gestureProgress = gestureTime / (item.kind == TycoonItem.Kind.Batter ? 1 : item.variant % 2 == 0 ? 1 : 1.5f);
            if (gestureTarget.kind == TycoonPart.Kind.Prep || gestureTarget.kind == TycoonPart.Kind.Bowl) gestureTarget.contents.toppingProgress = Mathf.Clamp01(gestureProgress);
            if (gestureProgress >= 1)
            {
                if (gestureTarget.kind == TycoonPart.Kind.Iron) gestureTarget.Pour(item, "Player");
                else gestureTarget.Finish(item, "Player");
                CancelGesture(false);
            }
        }
        if (gestureTarget != null)
        {
            var handPosition = gestureTarget.handTarget.position;
            if (gestureTarget.kind == TycoonPart.Kind.Tub)
            {
                handPosition += gestureTarget.handTarget.forward * ((.5f - scoopStroke) * .20f);
                handPosition -= grip.TransformVector(new Vector3(0, .035f, -.111f));
            }
            grip.position = Vector3.Lerp(grip.position, handPosition, .4f);
            rightHand.position = grip.position;
        }
    }
    public void CancelGesture(bool releaseLook = true)
    {
        if (gestureTarget != null && gestureTarget.claimedBy == "Player") gestureTarget.claimedBy = "";
        gestureTarget = null; gestureProgress = 0;
        if(releaseLook)gestureLookLocked=false;
        ApplyHeldPose();
    }
    public void Drop()
    {
        if (Held == null) return;
        game.Deliver(Held, view.transform.position + view.transform.forward * .8f);
        inventory.slots[selected] = null;
        CancelGesture();
    }
    public void RefreshHeld()
    {
        string state = Held == null ? "" : JsonUtility.ToJson(Held);
        if (state == heldState) return;
        heldState = state;
        if (heldVisual != null) Destroy(heldVisual);
        if (Held != null && Held.kind != TycoonItem.Kind.Equipment)
        {
            heldVisual = game.catalog.Display(Held, grip);
            if (Held.kind == TycoonItem.Kind.Tub || Held.kind == TycoonItem.Kind.Equipment) heldVisual.transform.localScale = Vector3.one * .65f;

        }
        ApplyHeldPose();
    }
    private void ApplyHeldPose()
    {
        grip.localPosition = new Vector3(.24f, -.28f, .55f); grip.localRotation = Quaternion.identity;
        rightHand.localPosition = new Vector3(.24f, -.32f, .54f); leftHand.localPosition = new Vector3(-.24f, -.35f, .50f);
        if (Held == null) return;
        if (Held.Tool)
        {
            grip.localRotation = Quaternion.Euler(25, 180, 0);
            rightHand.localPosition = grip.localPosition + new Vector3(0, 0, -.04f);
        }
        else if (Held.kind == TycoonItem.Kind.Equipment)
        {
            rightHand.localPosition = new Vector3(.3f, -.65f, .45f); leftHand.localPosition = new Vector3(-.3f, -.65f, .45f);
        }
        else if (Held.kind == TycoonItem.Kind.Tub)
        {
            grip.localPosition = new Vector3(0, -.32f, .60f);

            rightHand.localPosition = new Vector3(.17f, -.25f, .60f); leftHand.localPosition = new Vector3(-.17f, -.25f, .60f);
        }
        else if (Held.kind == TycoonItem.Kind.Cone || Held.kind == TycoonItem.Kind.Serving && Held.cone)
            rightHand.localPosition = grip.localPosition + new Vector3(0, .045f, 0);
        else if (Held.kind == TycoonItem.Kind.Batter || Held.kind == TycoonItem.Kind.Topping)
        {
            grip.localPosition = new Vector3(.24f, -.36f, .55f);
            rightHand.localPosition = grip.localPosition + new Vector3(0, .09f, 0);
        }
    }
    public void Teleport(Vector3 position)
    {
        controller.enabled = false; transform.position = position; controller.enabled = true; fallSpeed = 0;
    }
    public void SetMouseSensitivity(float value)
    {
        MouseSensitivity = Mathf.Clamp(value, .01f, .5f);
        PlayerPrefs.SetFloat(MouseSensitivityKey, MouseSensitivity);
    }
}
