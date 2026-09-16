using System.Linq;
using UnityEngine;
using UnityEngine.AI;

public class TycoonWorker : MonoBehaviour
{
    public enum Step { Idle, Supplies, GetBowl, GoIron, Pour, Close, Cook, Open, TakeCone, Place, GoTub, Scoop, Deposit, Topping, Take, Serve, Refill, ReturnRefill, TakeOrder, Restock }
    public TycoonGameManager game;
    public TycoonActor actor;
    public TycoonPart locker, prep, iron, target;
    public TycoonInventory inventory = new TycoonInventory(8);
    public int employeeId, tier, site, startDay, ticketId = -1, scoopIndex, toppingIndex;
    public bool onDuty, driver;
    public Step step;
    public float progress;
    public Step resumeStep;
    public TycoonItem.Kind neededSupply;
    public int neededVariant;
    public bool allowEmptySupply;
    public bool Blocked { get; private set; }
    private float tickDelta, stalledTime;
    private Vector3 walkPosition, walkDestination;
    public string status = "Off duty";
    public TycoonItem carrying;
    public float Wage => driver ? 60 : new[] { 24, 42, 66 }[tier];
    public float ScoopSpeed => new[] { .8f, 1, 1.3f }[tier];
    public float PourSpeed => new[] { .8f, 1, 1.2f }[tier];
    public float FinishSpeed => new[] { .8f, 1, 1.25f }[tier];
    public float HandleSpeed => new[] { .9f, 1, 1.15f }[tier];
    public string Owner => "Employee " + employeeId;
    public TycoonActor Customer => game.sites[site].queue.FirstOrDefault(c => c.order.id == ticketId);
    public bool ValidateLayout()
    {
        if (!game.parts.Any(p => p.site == site && p.installed && p.TableSurface)) { status = "A table for preparing bowls is missing."; return false; }
        var path = new NavMeshPath();
        var filter = new NavMeshQueryFilter { agentTypeID = actor.agent.agentTypeID, areaMask = NavMesh.AllAreas };
        foreach (var part in game.parts.Where(p => p.site == site && p.installed && (p.kind == TycoonPart.Kind.Tub || p.kind == TycoonPart.Kind.Prep || p == locker || p.kind == TycoonPart.Kind.Iron || p.TableSurface)))
        {
            if (!NavMesh.SamplePosition(part.operatingPoint.position, out var standing, .3f, filter) || !NavMesh.CalculatePath(transform.position, standing.position, filter, path) || path.status != NavMeshPathStatus.PathComplete)
            { status = "Blocked access: move " + part.kind + " or clear the aisle."; return false; }
        }
        return true;
    }
    private void Update()
    {
        if (game == null || game.Paused) return;
        actor.agent.speed = new[] { 1.3f, 1.5f, 1.7f }[tier];
        if (!onDuty || game.phase != TycoonGameManager.Phase.Trading)
        {
            Blocked = true;
            status = startDay > game.day ? "Starts on day " + startDay : game.phase != TycoonGameManager.Phase.Trading ? "" : "Off duty: the daily wage was not paid.";
            actor.RestHands(); return;
        }
        if (driver && game.truck.DriveRoute(this)) return;
        if (!locker.installed) { Wait("Place the assigned locker to start work."); return; }
        Tick(Time.deltaTime);
    }
    public void Tick(float dt)
    {
        tickDelta = dt; Blocked = false;
        if (step != Step.Idle && Customer == null) { ResetTicket(); status = "Order cancelled; waiting for another customer."; return; }
        if ((step == Step.GoTub || step == Step.Scoop || step == Step.Deposit || step == Step.Topping || step == Step.Take) && prep.contents == null)
        { ResetTicket(); status = "Serving was removed; restarting the order."; return; }
        if (step == Step.Restock) { Restock(); return; }
        if (step == Step.Idle)
        {
            actor.RestHands();
            var customer = game.sites[site].queue.FirstOrDefault(c => c.order.owner == "" && c.order.stage == TycoonOrder.Stage.Pickup) ?? game.sites[site].queue.FirstOrDefault(c => c.order.owner == "" && c.ReadyToOrder);
            if (customer == null)
            {
                status = game.sites[site].queue.Any(c => c.order.owner != "") ? "Other staff are handling the waiting orders." : game.sites[site].queue.Count > 0 ? "Waiting for a customer to reach the order counter." : "Waiting for a customer.";
                return;
            }
            prep = customer.order.cone ? game.Parts(site, TycoonPart.Kind.Prep).FirstOrDefault(p => p.claimedBy == "" && p.contents == null) : game.builder.ReserveBowl(site);
            if (prep == null) { Wait(customer.order.cone ? "Place an empty cone holder for this order." : "Clear space on a table for a bowl."); return; }
            prep.Claim(Owner); customer.order.owner = Owner; ticketId = customer.order.id;
            scoopIndex = 0; toppingIndex = 0; Go(customer.order.stage == TycoonOrder.Stage.Ordering ? Step.TakeOrder : Step.Supplies); return;
        }
        var order = Customer.order;
        if (step == Step.TakeOrder)
        {
            status = "Taking customer order";
            if (!Walk(game.sites[site].registerOperatingPoint.position, "order counter")) return;
            progress += dt;
            if (progress >= .6f && Customer.TakeOrder()) Go(Step.Supplies);
            return;
        }
        if (step == Step.Supplies)
        {
            if (HasOrderSupplies(order)) { Go(order.cone ? Step.GoIron : Step.GetBowl); return; }
            status = "Collecting tools and supplies from locker";
            if (!Walk(locker.operatingPoint.position, "locker")) return;
            if (!Supply(order)) { Wait(status); return; }
            Go(order.cone ? Step.GoIron : Step.GetBowl); return;
        }
        if (step == Step.GetBowl)
        {
            if (!RequireSupply(TycoonItem.Kind.Bowls, 0, Step.GetBowl, out var bowls)) return;
            int bowl = System.Array.IndexOf(inventory.slots, bowls);
            inventory.Consume(bowl); carrying = new TycoonItem(TycoonItem.Kind.Serving); actor.Hold(carrying); Go(Step.Place); return;
        }
        if (step == Step.GoIron)
        {
            if (!RequireSupply(TycoonItem.Kind.Batter, 0, Step.GoIron, out var batter)) return;
            iron = game.Parts(site, TycoonPart.Kind.Iron).FirstOrDefault(p => p.Available(Owner) && p.ironStage == 0);
            if (iron == null) { Wait(game.Parts(site, TycoonPart.Kind.Iron).Any() ? "Waffle iron is busy. Finish or clear its waffle." : "Place a waffle iron on a table."); return; }
            if (!iron.Claim(Owner) || !Walk(iron.operatingPoint.position, "waffle iron")) return;
            actor.Hold(batter); Go(Step.Pour); return;
        }
        if (step == Step.Pour)
        {
            if (!RequireSupply(TycoonItem.Kind.Batter, 0, Step.Pour, out var batter, iron.ironStage == 5)) return;
            if (!Walk(iron.operatingPoint.position, "waffle iron")) return;
            status = "Pouring waffle batter"; actor.Hold(batter);
            if (iron.ironStage == 0) iron.BeginPour(batter, Owner);
            progress += dt; iron.pourProgress = Mathf.Clamp01(progress * PourSpeed);
            actor.grip.localRotation = Quaternion.Slerp(actor.grip.localRotation, Quaternion.Euler(105, 0, Mathf.Sin(Time.time * 18) * 7.5f), 1 - Mathf.Exp(-10 * dt));
            actor.Reach(iron.handTarget.position + Vector3.up * .18f - actor.grip.TransformVector(TycoonWaffleFeedback.BottleNozzle), progress, false);
            iron.waffleFeedback.PourFrom(actor.grip);
            if (progress < 1 / PourSpeed) return;
            if (!iron.Pour(batter, Owner)) { Wait("Waffle iron changed. Clear it before preparing another cone."); return; }
            actor.Hold(null); Go(Step.Close); return;
        }
        if (step == Step.Close)
        {
            status = "Closing waffle iron";
            if (Animate(iron, .5f / HandleSpeed, dt)) { iron.CloseIron(Owner); Go(Step.Cook); } return;
        }
        if (step == Step.Cook)
        {
            status = "Cooking waffle"; actor.RestHands();
            if (iron.cookTime >= 6) Go(Step.Open); return;
        }
        if (step == Step.Open)
        {
            status = "Opening waffle iron";
            if (Animate(iron, .5f / HandleSpeed, dt)) { iron.OpenIron(Owner); Go(Step.TakeCone); } return;
        }
        if (step == Step.TakeCone)
        {
            status = "Taking fresh cone";
            if (!Animate(iron, .6f / HandleSpeed, dt)) return;
            var cone = iron.TakeCone(Owner);
            if (cone == null) { Wait("Cone was removed from the waffle iron. Finish or clear the iron."); return; }
            carrying = new TycoonItem(TycoonItem.Kind.Serving) { cone = true }; actor.Hold(carrying); Go(Step.Place); return;
        }
        if (step == Step.Place)
        {
            status = order.cone ? "Placing cone in holder" : "Placing bowl on table";
            if (!Walk(prep.operatingPoint.position, "preparation table") || !Animate(prep, .6f / HandleSpeed, dt)) return;
            prep.contents = carrying; carrying = null; actor.Hold(null); Go(Step.GoTub); return;
        }
        if (step == Step.GoTub)
        {
            if (prep.contents == null) { ResetTicket(); status = "Serving was removed; restarting the order."; return; }
            if (!RequireSupply(TycoonItem.Kind.BasicScooper, 0, Step.GoTub, out var tool)) return;
            if (tool.loadedFlavor == order.flavors[scoopIndex]) { actor.Hold(tool); Go(Step.Deposit); return; }
            if (tool.loadedFlavor >= 0) { Wait("Scooper holds " + TycoonCatalogSO.FlavorNames[tool.loadedFlavor] + ". Give an empty scooper for " + TycoonCatalogSO.FlavorNames[order.flavors[scoopIndex]] + "."); return; }
            target = game.Parts(site, TycoonPart.Kind.Tub).FirstOrDefault(p => p.variant == order.flavors[scoopIndex] && p.Available(Owner));
            if (target == null)
            {
                string flavor = TycoonCatalogSO.FlavorNames[order.flavors[scoopIndex]];
                Wait(game.Parts(site, TycoonPart.Kind.Tub).Any(p => p.variant == order.flavors[scoopIndex]) ? flavor + " holder is in use by someone else." : "Place and fill the " + flavor + " holder for this order."); return;
            }
            status = "Walking to " + TycoonCatalogSO.FlavorNames[target.variant];
            bool refill = inventory.Locate(TycoonItem.Kind.Tub,target.variant)>=0 || game.Parts(site,TycoonPart.Kind.Shelf).Any(r=>r.storage.Locate(TycoonItem.Kind.Tub,target.variant)>=0);
            if (target.contents.amount == 0 || (target.contents.amount<=6 && refill)) { Go(Step.Refill); return; }
            if (!target.Claim(Owner) || !Walk(target.operatingPoint.position, "ice cream holder")) return;
            actor.Hold(Tool()); Go(Step.Scoop); return;
        }
        if (step == Step.Scoop)
        {
            if (!RequireSupply(TycoonItem.Kind.BasicScooper, 0, Step.GoTub, out var tool)) return;
            status = "Scooping " + TycoonCatalogSO.FlavorNames[target.variant];
            float strokes = tool.ScoopDuration * 3;
            if (!Animate(target, strokes / ScoopSpeed, dt, true)) return;
            if (!target.Scoop(tool, Owner)) { Go(Step.GoTub); return; }
            actor.Hold(tool); Go(Step.Deposit); return;
        }
        if (step == Step.Deposit)
        {
            if (!RequireSupply(TycoonItem.Kind.BasicScooper, 0, Step.GoTub, out var tool)) return;
            if (tool.loadedFlavor != order.flavors[scoopIndex]) { Go(Step.GoTub); return; }
            status = "Placing scoop into serving";
            if (!Walk(prep.operatingPoint.position, "preparation table") || !Animate(prep, .6f / HandleSpeed, dt)) return;
            if (!prep.Deposit(Tool(), Owner)) { Wait("Serving changed. Remove it from the table to restart this order."); return; }
            actor.Hold(Tool()); scoopIndex++;
            Go(scoopIndex < order.flavors.Length ? Step.GoTub : Step.Topping); return;
        }
        if (step == Step.Topping)
        {
            while (toppingIndex < 6 && (order.toppings & (1 << toppingIndex)) == 0) toppingIndex++;
            if (toppingIndex == 6) { actor.Hold(null); Go(Step.Take); return; }
            if (!RequireSupply(TycoonItem.Kind.Topping, toppingIndex, Step.Topping, out var topping, prep.contents.pendingTopping == toppingIndex)) return;
            if (!Walk(prep.operatingPoint.position, "preparation table")) return;
            actor.Hold(topping); status = "Applying " + TycoonCatalogSO.ToppingNames[toppingIndex];
            if (!prep.BeginTopping(topping, Owner)) { Wait("Serving changed. Remove it from the table to restart this order."); return; }
            prep.contents.toppingProgress = Mathf.Clamp01(progress * FinishSpeed / (toppingIndex % 2 == 0 ? 1 : 1.5f));
            if (!Animate(prep, (toppingIndex % 2 == 0 ? 1 : 1.5f) / FinishSpeed, dt)) return;
            if (!prep.Finish(topping, Owner)) { Wait("Serving changed. Remove it from the table to restart this order."); return; }
            toppingIndex++; progress = 0; return;
        }
        if (step == Step.Take)
        {
            status = "Picking up completed order";
            if (!Animate(prep, .6f / HandleSpeed, dt)) return;
            if (prep.contents == null || !prep.contents.Matches(order)) { Wait("Serving does not match the order. Remove it from the table to restart."); return; }
            carrying = prep.contents; prep.contents = null;
            if (prep.kind == TycoonPart.Kind.Bowl) { prep.RemoveBowl(); prep = null; }
            actor.Hold(carrying); Go(Step.Serve); return;
        }
        if (step == Step.Serve)
        {
            status = "Serving customer";
            var counter = game.Parts(site, TycoonPart.Kind.ServingCounter).FirstOrDefault();
            if (counter == null) { Wait("Place a pickup counter to serve this order."); return; }
            if (!Walk(counter.operatingPoint.position, "pickup counter")) return;
            if (!Customer.ReadyForPickup) { Wait("Waiting for the customer to reach the pickup counter."); return; }
            if (!Animate(counter, .6f / HandleSpeed, dt)) return;
            game.Pay(Customer, carrying); carrying = null; actor.Hold(null); ResetTicket(); return;
        }
        if (step == Step.Refill)
        {
            status = "Refilling ice cream tub";
            if (!RequireSupply(TycoonItem.Kind.Tub, target.variant, Step.Refill, out var refillTub)) return;
            int slot = System.Array.IndexOf(inventory.slots, refillTub);
            actor.Hold(inventory.slots[slot]);
            if (!target.Claim(Owner)) { Wait("Ice cream holder is in use by someone else."); return; }
            if (!Walk(target.operatingPoint.position, "ice cream holder") || !Animate(target, .8f, dt)) return;
            TycoonInventory.Refill(inventory.slots[slot], target.contents);
            target.claimedBy = "";
            if (inventory.slots[slot].amount > 0) { Go(Step.ReturnRefill); return; }
            if (inventory.slots[slot].amount == 0) inventory.slots[slot] = null;
            actor.Hold(null); Go(Step.GoTub);
        }
        if (step == Step.ReturnRefill)
        {
            int slot=inventory.Locate(TycoonItem.Kind.Tub,target.variant);
            if (slot < 0) { actor.Hold(null); Go(Step.GoTub); return; }
            var rack=game.Parts(site,TycoonPart.Kind.Shelf).FirstOrDefault(r=>r.storage.FreeSlot>=0);
            if(rack==null){Wait("Make room in shelf storage for the remaining refill.");return;}
            status="Returning remaining ice cream to shelf storage";actor.Hold(inventory.slots[slot]);
            if(!Walk(rack.operatingPoint.position, "shelf storage")||!Animate(rack,.6f/HandleSpeed,dt))return;
            inventory.Transfer(slot,rack.storage);actor.Hold(null);Go(Step.GoTub);
        }
    }
    public void InventoryChanged()
    {
        if (step == Step.Scoop || step == Step.Deposit && (Tool() == null || Tool().loadedFlavor < 0))
        {
            if (target != null && target.claimedBy == Owner) target.claimedBy = "";
            Go(Step.GoTub);
        }
        actor.Hold(carrying != null && carrying.kind == TycoonItem.Kind.Serving ? carrying : null);
        if (onDuty && game.phase == TycoonGameManager.Phase.Trading && !game.Paused) Tick(0);
    }
    private bool HasOrderSupplies(TycoonOrder order)
    {
        bool Has(TycoonItem.Kind kind, int variant) => inventory.slots.Any(i => i != null && i.kind == kind && i.variant == variant && i.amount > 0);
        return Tool() != null && Has(order.cone ? TycoonItem.Kind.Batter : TycoonItem.Kind.Bowls, 0)
            && Enumerable.Range(0, 6).All(i => (order.toppings & (1 << i)) == 0 || Has(TycoonItem.Kind.Topping, i));
    }
    private bool RequireSupply(TycoonItem.Kind kind, int variant, Step resume, out TycoonItem item, bool allowEmpty = false)
    {
        item = kind == TycoonItem.Kind.BasicScooper ? Tool() : inventory.slots.FirstOrDefault(i => i != null && i.kind == kind && i.variant == variant && (i.amount > 0 || allowEmpty));
        if (item != null) return true;
        neededSupply = kind; neededVariant = variant; resumeStep = resume; allowEmptySupply = allowEmpty;
        if (target != null && target.claimedBy == Owner) target.claimedBy = "";
        Go(Step.Restock); Restock(); return false;
    }
    private void Restock()
    {
        bool Matches(TycoonItem i) => i != null && (neededSupply == TycoonItem.Kind.BasicScooper ? i.Tool : i.kind == neededSupply && i.variant == neededVariant) && (i.amount > 0 || allowEmptySupply);
        if (inventory.slots.Any(Matches)) { Go(resumeStep); return; }
        string label = neededSupply == TycoonItem.Kind.BasicScooper ? "a scooper" : game.catalog.Label(new TycoonItem(neededSupply, 1, neededVariant));
        var source = locker.storage.slots.Any(Matches) ? locker : neededSupply == TycoonItem.Kind.Tub ? game.Parts(site, TycoonPart.Kind.Shelf).FirstOrDefault(p => p.storage.slots.Any(Matches)) : null;
        if (source == null) { Wait("Need " + label + ". Add it to this inventory or " + (neededSupply == TycoonItem.Kind.Tub ? "shelf storage." : "the assigned locker.")); return; }
        var refillTarget = inventory.slots.FirstOrDefault(i => i != null && i.kind == neededSupply && i.variant == neededVariant && i.Consumable && i.amount < i.Capacity);
        if (refillTarget == null && inventory.FreeSlot < 0) { Wait("Inventory full. Free a slot for " + label + "."); return; }
        if (!Walk(source.operatingPoint.position, source == locker ? "assigned locker" : "shelf storage")) return;
        int slot = System.Array.FindIndex(source.storage.slots, i => Matches(i));
        if (refillTarget != null)
        {
            TycoonInventory.Refill(source.storage.slots[slot], refillTarget);
            if (source.storage.slots[slot].amount == 0 && source.storage.slots[slot].Disposable) source.storage.slots[slot] = null;
        }
        else source.storage.Transfer(slot, inventory);
        Go(resumeStep);
    }
    private bool Walk(Vector3 point, string destination)
    {
        if (actor.Walk(point)) { stalledTime = 0; return true; }
        if (Vector3.Distance(walkDestination, point) > .1f || Vector3.Distance(walkPosition, transform.position) > .03f) stalledTime = 0;
        else stalledTime += tickDelta;
        walkDestination = point; walkPosition = transform.position;
        bool unreachable = !actor.agent.pathPending && actor.agent.pathStatus != NavMeshPathStatus.PathComplete;
        Blocked = unreachable || stalledTime > 2;
        status = Blocked ? "Path to " + destination + " is blocked. Clear the aisle or move the equipment." : "Walking to " + destination;
        actor.RestHands(); return false;
    }
    private void Wait(string reason)
    {
        status = reason; Blocked = true;
        if (actor.agent.hasPath) actor.agent.ResetPath();
        actor.RestHands();
    }
    private bool Supply(TycoonOrder order)
    {
        int tool = System.Array.FindIndex(inventory.slots, i => i != null && i.Tool);
        int upgrade = Enumerable.Range(0, locker.storage.slots.Length).Where(i => locker.storage.slots[i] != null && locker.storage.slots[i].Tool).OrderByDescending(i => locker.storage.slots[i].ToolTier).DefaultIfEmpty(-1).First();
        if (tool >= 0 && upgrade >= 0 && inventory.slots[tool].ToolTier < locker.storage.slots[upgrade].ToolTier)
        {
            var basic = inventory.slots[tool]; inventory.slots[tool] = locker.storage.slots[upgrade]; locker.storage.slots[upgrade] = basic;
        }
        if (tool < 0)
        {
            int source = upgrade;
            if (source < 0) { status = "Need a scooper. Add one here or to the assigned locker."; return false; }
            if (!locker.storage.Transfer(source, inventory)) { status = "Inventory full. Free a slot for a scooper."; return false; }
        }
        for (int i = 0; i < inventory.slots.Length; i++)
        {
            var item = inventory.slots[i];
            if (item != null && item.kind == TycoonItem.Kind.Topping && (order.toppings & (1 << item.variant)) == 0) inventory.Transfer(i, locker.storage);
        }
        if (!Ensure(order.cone ? TycoonItem.Kind.Batter : TycoonItem.Kind.Bowls, 0)) return false;
        for (int i = 0; i < 6; i++) if ((order.toppings & (1 << i)) != 0 && !Ensure(TycoonItem.Kind.Topping, i)) return false;
        return true;
    }
    private bool Ensure(TycoonItem.Kind kind, int variant)
    {
        int slot = inventory.Locate(kind, variant);
        if (slot < 0)
        {
            int source = locker.storage.Locate(kind, variant);
            if (source >= 0) locker.storage.Transfer(source, inventory);
            else if (kind == TycoonItem.Kind.Bowls && inventory.FreeSlot >= 0) inventory.slots[inventory.FreeSlot] = new TycoonItem(kind, 0);
            slot = inventory.Locate(kind, variant);
        }
        if (slot < 0) { status = inventory.FreeSlot < 0 ? "Inventory full. Free a slot for supplies." : "Need " + game.catalog.Label(new TycoonItem(kind, 1, variant)) + ". Add it here or to the assigned locker."; return false; }
        var item = inventory.slots[slot];
        foreach (var source in locker.storage.slots) if (source != null) TycoonInventory.Refill(source, item);
        for (int i = 0; i < locker.storage.slots.Length; i++) if (locker.storage.slots[i] != null && locker.storage.slots[i].amount == 0 && locker.storage.slots[i].Disposable) locker.storage.slots[i] = null;
        if (item.amount == 0) { status = "Need " + game.catalog.Label(item) + ". Refill this inventory or the assigned locker."; return false; }
        return true;
    }
    private TycoonItem Tool()
    {
        int flavor = Customer == null ? -1 : Customer.order.flavors[Mathf.Min(scoopIndex, Customer.order.flavors.Length - 1)];
        return inventory.slots.Where(i => i != null && i.Tool).OrderByDescending(i => i.loadedFlavor == flavor && flavor >= 0).ThenByDescending(i => i.loadedFlavor < 0).ThenByDescending(i => i.ToolTier).FirstOrDefault();
    }
    private bool Animate(TycoonPart part, float duration, float dt, bool scoop = false)
    {
        progress += dt; actor.Reach(part.handTarget.position, progress * (scoop ? ScoopSpeed : 1), scoop);
        return progress >= duration;
    }
    private void Go(Step next)
    {
        step = next; progress = 0; actor.RestHands();
    }
    public void ResetTicket()
    {
        if (Customer != null && Customer.order.owner == Owner) Customer.order.owner = "";
        if (carrying != null && carrying.kind != TycoonItem.Kind.None) { game.Deliver(carrying, transform.position + Vector3.up); carrying = null; }
        if (prep != null && prep.kind == TycoonPart.Kind.Bowl && prep.contents == null) { prep.RemoveBowl(); prep = null; }
        foreach (var part in game.parts) if (part.claimedBy == Owner) part.claimedBy = "";
        ticketId = -1; step = Step.Idle; progress = 0; actor.Hold(null); actor.RestHands();
    }
}
