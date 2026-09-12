using System.Linq;
using UnityEngine;
using UnityEngine.AI;

public class TycoonWorker : MonoBehaviour
{
    public enum Step { Idle, Supplies, GetBowl, GoIron, Pour, Close, Cook, Open, TakeCone, Place, GoTub, Scoop, Deposit, Topping, Take, Serve, Refill, ReturnRefill, TakeOrder }
    public TycoonGameManager game;
    public TycoonActor actor;
    public TycoonPart locker, prep, iron, target;
    public TycoonInventory inventory = new TycoonInventory(8);
    public int employeeId, tier, site, startDay, ticketId = -1, scoopIndex, toppingIndex;
    public bool onDuty, driver;
    public Step step;
    public float progress;
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
        if (!onDuty || game.phase != TycoonGameManager.Phase.Trading) { status = "Off duty"; actor.RestHands(); return; }
        if (driver && game.truck.DriveRoute(this)) return;
        if (!locker.installed) { status = "Waiting for assigned locker to be placed"; actor.agent.ResetPath(); return; }
        if (step != Step.Idle && Customer == null) { ResetTicket(); return; }
        Tick(Time.deltaTime);
    }
    public void Tick(float dt)
    {
        if (step == Step.Idle)
        {
            actor.RestHands();
            var customer = game.sites[site].queue.FirstOrDefault(c => c.order.owner == "" && c.order.stage == TycoonOrder.Stage.Pickup) ?? game.sites[site].queue.FirstOrDefault(c => c.order.owner == "" && c.ReadyToOrder);
            if (customer == null) { status = "Waiting for an order"; return; }
            prep = customer.order.cone ? game.Parts(site, TycoonPart.Kind.Prep).FirstOrDefault(p => p.claimedBy == "" && p.contents == null) : game.builder.ReserveBowl(site);
            if (prep == null) { status = "Waiting for a preparation spot"; return; }
            prep.Claim(Owner); customer.order.owner = Owner; ticketId = customer.order.id;
            scoopIndex = 0; toppingIndex = 0; Go(customer.order.stage == TycoonOrder.Stage.Ordering ? Step.TakeOrder : Step.Supplies); return;
        }
        var order = Customer.order;
        if (step == Step.TakeOrder)
        {
            status = "Taking customer order";
            if (!actor.Walk(game.sites[site].registerOperatingPoint.position)) return;
            progress += dt;
            if (progress >= .6f && Customer.TakeOrder()) Go(Step.Supplies);
            return;
        }
        if (step == Step.Supplies)
        {
            status = "Collecting tools and supplies from locker";
            if (!actor.Walk(locker.operatingPoint.position)) return;
            if (!Animate(locker, .6f / HandleSpeed, dt)) return;
            if (!Supply(order)) { progress = 0; return; }
            Go(order.cone ? Step.GoIron : Step.GetBowl); return;
        }
        if (step == Step.GetBowl)
        {
            int bowl = inventory.Locate(TycoonItem.Kind.Bowls);
            if (bowl < 0) { Go(Step.Supplies); return; }
            inventory.Consume(bowl); carrying = new TycoonItem(TycoonItem.Kind.Serving); actor.Hold(carrying); Go(Step.Place); return;
        }
        if (step == Step.GoIron)
        {
            iron = game.Parts(site, TycoonPart.Kind.Iron).FirstOrDefault(p => p.Available(Owner) && p.ironStage == 0);
            if (iron == null) { status = "Waiting for waffle iron"; return; }
            if (!iron.Claim(Owner) || !actor.Walk(iron.operatingPoint.position)) return;
            actor.Hold(inventory.slots[inventory.Locate(TycoonItem.Kind.Batter)]); Go(Step.Pour); return;
        }
        if (step == Step.Pour)
        {
            status = "Pouring waffle batter";
            if (iron.ironStage == 0) iron.BeginPour(inventory.slots[inventory.Locate(TycoonItem.Kind.Batter)], Owner);
            iron.pourProgress = Mathf.Clamp01(progress * PourSpeed);
            if (!Animate(iron, 1 / PourSpeed, dt)) return;
            if (!iron.Pour(inventory.slots[inventory.Locate(TycoonItem.Kind.Batter)], Owner)) { status = "Batter missing"; return; }
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
            if (cone == null) { status = "Cone unavailable"; return; }
            carrying = new TycoonItem(TycoonItem.Kind.Serving) { cone = true }; actor.Hold(carrying); Go(Step.Place); return;
        }
        if (step == Step.Place)
        {
            status = order.cone ? "Placing cone in holder" : "Placing bowl on table";
            if (!actor.Walk(prep.operatingPoint.position) || !Animate(prep, .6f / HandleSpeed, dt)) return;
            prep.contents = carrying; carrying = null; actor.Hold(null); Go(Step.GoTub); return;
        }
        if (step == Step.GoTub)
        {
            if (prep.contents == null) { status = "Serving missing from preparation spot"; return; }
            target = game.Parts(site, TycoonPart.Kind.Tub).FirstOrDefault(p => p.variant == order.flavors[scoopIndex] && p.Available(Owner));
            if (target == null) { status = "Waiting for ice cream tub"; return; }
            bool refill = inventory.Locate(TycoonItem.Kind.Tub,target.variant)>=0 || game.Parts(site,TycoonPart.Kind.ColdStorage).Any(r=>r.storage.Locate(TycoonItem.Kind.Tub,target.variant)>=0);
            if (target.contents.amount == 0 || (target.contents.amount<=6 && refill)) { Go(Step.Refill); return; }
            if (!target.Claim(Owner) || !actor.Walk(target.operatingPoint.position)) return;
            actor.Hold(Tool()); Go(Step.Scoop); return;
        }
        if (step == Step.Scoop)
        {
            status = "Scooping " + TycoonCatalogSO.FlavorNames[target.variant];
            var tool = Tool(); float strokes = tool.kind == TycoonItem.Kind.ImprovedScooper ? 1 : 3;
            if (!Animate(target, strokes / ScoopSpeed, dt, true)) return;
            if (!target.Scoop(tool, Owner)) { Go(Step.GoTub); return; }
            actor.Hold(tool); Go(Step.Deposit); return;
        }
        if (step == Step.Deposit)
        {
            status = "Placing scoop into serving";
            if (!actor.Walk(prep.operatingPoint.position) || !Animate(prep, .6f / HandleSpeed, dt)) return;
            if (!prep.Deposit(Tool(), Owner)) { status = "Serving missing or changed"; return; }
            actor.Hold(Tool()); scoopIndex++;
            Go(scoopIndex < order.flavors.Length ? Step.GoTub : Step.Topping); return;
        }
        if (step == Step.Topping)
        {
            while (toppingIndex < 6 && (order.toppings & (1 << toppingIndex)) == 0) toppingIndex++;
            if (toppingIndex == 6) { actor.Hold(null); Go(Step.Take); return; }
            int slot = inventory.Locate(TycoonItem.Kind.Topping, toppingIndex);
            if (slot < 0) { status = "Missing topping container"; return; }
            var topping = inventory.slots[slot]; actor.Hold(topping); status = "Applying " + TycoonCatalogSO.ToppingNames[toppingIndex];
            if (!prep.BeginTopping(topping, Owner)) { status = "Topping or serving missing"; return; }
            prep.contents.toppingProgress = Mathf.Clamp01(progress * FinishSpeed / (toppingIndex % 2 == 0 ? 1 : 1.5f));
            if (!Animate(prep, (toppingIndex % 2 == 0 ? 1 : 1.5f) / FinishSpeed, dt)) return;
            if (!prep.Finish(topping, Owner)) { status = "Topping or serving missing"; return; }
            toppingIndex++; progress = 0; return;
        }
        if (step == Step.Take)
        {
            status = "Picking up completed order";
            if (!Animate(prep, .6f / HandleSpeed, dt)) return;
            if (prep.contents == null || !prep.contents.Matches(order)) { status = "Serving does not match ticket"; return; }
            carrying = prep.contents; prep.contents = null;
            if (prep.kind == TycoonPart.Kind.Bowl) { prep.RemoveBowl(); prep = null; }
            actor.Hold(carrying); Go(Step.Serve); return;
        }
        if (step == Step.Serve)
        {
            status = "Serving customer";
            var counter = game.Parts(site, TycoonPart.Kind.ServingCounter).FirstOrDefault();
            if (counter == null) { status = "Waiting for pickup counter to be placed"; return; }
            if (!actor.Walk(counter.operatingPoint.position) || !Customer.ReadyForPickup || !Animate(counter, .6f / HandleSpeed, dt)) return;
            game.Pay(Customer, carrying); carrying = null; actor.Hold(null); ResetTicket(); return;
        }
        if (step == Step.Refill)
        {
            status = "Refilling ice cream tub";
            int slot = inventory.Locate(TycoonItem.Kind.Tub, target.variant);
            if (slot < 0)
            {
                var rack = game.Parts(site, TycoonPart.Kind.ColdStorage).FirstOrDefault(p => p.storage.Locate(TycoonItem.Kind.Tub, target.variant) >= 0);
                if (rack == null) { status = "Cold storage needs " + TycoonCatalogSO.FlavorNames[target.variant]; return; }
                if (!actor.Walk(rack.operatingPoint.position)) return;
                rack.storage.Transfer(rack.storage.Locate(TycoonItem.Kind.Tub, target.variant), inventory);
                return;
            }
            actor.Hold(inventory.slots[slot]);
            if (!target.Claim(Owner) || !actor.Walk(target.operatingPoint.position) || !Animate(target, .8f, dt)) return;
            TycoonInventory.Refill(inventory.slots[slot], target.contents);
            target.claimedBy = "";
            if (inventory.slots[slot].amount > 0) { Go(Step.ReturnRefill); return; }
            if (inventory.slots[slot].amount == 0) inventory.slots[slot] = null;
            actor.Hold(null); Go(Step.GoTub);
        }
        if (step == Step.ReturnRefill)
        {
            int slot=inventory.Locate(TycoonItem.Kind.Tub,target.variant);
            var rack=game.Parts(site,TycoonPart.Kind.ColdStorage).FirstOrDefault(r=>r.storage.FreeSlot>=0);
            if(rack==null){status="Make room in cold storage for the remaining refill";return;}
            status="Returning remaining ice cream to cold storage";actor.Hold(inventory.slots[slot]);
            if(!actor.Walk(rack.operatingPoint.position)||!Animate(rack,.6f/HandleSpeed,dt))return;
            inventory.Transfer(slot,rack.storage);actor.Hold(null);Go(Step.GoTub);
        }
    }
    private bool Supply(TycoonOrder order)
    {
        int tool = inventory.Locate(TycoonItem.Kind.ImprovedScooper);
        if (tool < 0) tool = inventory.Locate(TycoonItem.Kind.BasicScooper);
        int upgrade = locker.storage.Locate(TycoonItem.Kind.ImprovedScooper);
        if (tool >= 0 && inventory.slots[tool].kind == TycoonItem.Kind.BasicScooper && upgrade >= 0)
        {
            var basic = inventory.slots[tool]; inventory.slots[tool] = locker.storage.slots[upgrade]; locker.storage.slots[upgrade] = basic;
        }
        if (tool < 0)
        {
            int source = upgrade >= 0 ? upgrade : locker.storage.Locate(TycoonItem.Kind.BasicScooper);
            if (source < 0 || !locker.storage.Transfer(source, inventory)) { status = "Put a scooper in the assigned locker"; return false; }
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
        if (slot < 0) { status = "Locker needs " + kind + (kind == TycoonItem.Kind.Topping ? " / " + TycoonCatalogSO.ToppingNames[variant] : ""); return false; }
        var item = inventory.slots[slot];
        foreach (var source in locker.storage.slots) if (source != null) TycoonInventory.Refill(source, item);
        for (int i = 0; i < locker.storage.slots.Length; i++) if (locker.storage.slots[i] != null && locker.storage.slots[i].amount == 0 && locker.storage.slots[i].Disposable) locker.storage.slots[i] = null;
        if (item.amount == 0) { status = "Locker needs a matching refill"; return false; }
        return true;
    }
    private TycoonItem Tool()
    {
        return inventory.slots.First(i => i != null && i.Tool);
    }
    private bool Animate(TycoonPart part, float duration, float dt, bool scoop = false)
    {
        progress += dt; actor.Reach(part.handTarget.position, progress * (scoop ? ScoopSpeed : 1), scoop);
        return progress >= duration;
    }
    private void Go(Step next)
    {
        step = next; progress = 0;
    }
    public void ResetTicket()
    {
        if (prep != null && prep.kind == TycoonPart.Kind.Bowl && prep.contents == null) { prep.RemoveBowl(); prep = null; }
        foreach (var part in game.parts) if (part.claimedBy == Owner) part.claimedBy = "";
        ticketId = -1; step = Step.Idle; progress = 0;
    }
}
