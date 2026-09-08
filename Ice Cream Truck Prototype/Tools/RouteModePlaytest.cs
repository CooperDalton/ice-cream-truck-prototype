using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Threading.Tasks;
using UnityEditor;
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.SceneManagement;
using UnityEngine.UI;
using Object = UnityEngine.Object;

public static class RouteModePlaytest
{
    static PrototypeSceneReferences r;
    static RouteGameManager route;
    static List<string> checks;
    static void Check(bool value,string message)
    {
        if(!value)throw new Exception("ROUTE TEST FAILED: "+message);
        checks.Add(message);
    }
    static async Task Frames(int count=5)
    {
        for(int i=0;i<count;i++)await Awaitable.NextFrameAsync();
        Canvas.ForceUpdateCanvases();
    }
    static void Manual()
    {
        r=PrototypeSceneReferences.Instance;route=r.route;
        r.player.ManualInput=r.interaction.ManualInput=r.truck.ManualInput=true;
        if(route!=null)route.ManualInput=true;
    }
    static void Click(Button button)
    {
        var pointer=new PointerEventData(EventSystem.current);
        pointer.position=RectTransformUtility.WorldToScreenPoint(null,button.transform.position);
        var hits=new List<RaycastResult>();EventSystem.current.RaycastAll(pointer,hits);
        Check(hits.Count>0&&hits[0].gameObject==button.gameObject,"Pointer reaches "+button.name);
        ExecuteEvents.Execute(button.gameObject,pointer,ExecuteEvents.pointerClickHandler);
    }
    static string Report(string name)
    {
        string report="PASS "+checks.Count+" checks\n"+string.Join("\n",checks);
        File.WriteAllText("Library/CodexPlaytests/"+name+".txt",report);
        EditorApplication.isPaused=true;
        return report;
    }
    static void PrepareOrder(RouteHotspot.Order order)
    {
        if(!r.waffle.IsOpen)Use(r.waffle);
        Use(r.batter);Hold(r.waffle,90,false);PutDown();Use(r.waffle);
        r.waffle.Advance(r.day.settings.cookSeconds+.1f);Use(r.waffle);Use(r.waffle);
        var cone=(IceCreamCone)r.interaction.Held;Use(r.holders[2]);Use(r.scooper);
        foreach(var flavor in order.recipe){Hold(r.tubs.Single(t=>t.flavor==flavor),70,true);Use(cone);}
        PutDown();
        if(order.sprinkles){Use(r.shaker);Hold(cone,60,true);PutDown();}
        Use(cone);Use(route.tray);
    }
    public static async Task<string> MixedOrders()
    {
        checks=new List<string>();EditorApplication.isPaused=false;await Frames();
        Click(GameModeMenu.Instance.parkRouteButton);await Frames(12);Manual();var h=route.hud;
        Check(route.hotspots.Where(c=>c.gameObject.activeSelf).All(c=>c.orders.Length==2&&c.orders[0].Label!=c.orders[1].Label),"Every day-one location offers two different recipes");
        for(int i=0;i<route.hotspots.Length;i++)
        {
            var crowd=route.hotspots[i];if(!crowd.gameObject.activeSelf)continue;
            Check(crowd.Customers.Count==crowd.CustomerCount,"Customer total matches order quantities at "+i);
            for(int j=0;j<crowd.orders.Length;j++)
            {
                var order=crowd.orders[j];var row=h.crowdCards[i].orders[j];
                Check(crowd.Customers.Count(c=>c.Order==order)==order.quantity,"Recipe "+i+"/"+j+" reaches the stated number of customers");
                Check(row.quantityPrice.text=="×"+order.quantity+"  $"+order.price+" ea","Recipe row "+i+"/"+j+" shows its own count and price");
                Check(row.flavors.Count(f=>f.gameObject.activeSelf)==order.recipe.Length&&row.flavors[0].sprite==order.recipe[0].orderPicture&&row.sprinkles.activeSelf==order.sprinkles,"Recipe row "+i+"/"+j+" has matching icons");
                var customer=crowd.Customers.First(c=>c.Order==order);
                Check(customer.scoopPictures[0].sprite==order.recipe[0].orderPicture&&customer.sprinkles.activeSelf==order.sprinkles,"Customer bubble agrees with recipe "+i+"/"+j);
            }
            Check(!h.crowdCards[i].orders[2].root.activeSelf,"Unused third row is hidden at "+i);
        }
        foreach(var button in h.pointButtons){Click(button);Click(button);Click(button);}
        var party=route.hotspots[0];
        Check(party.orders[0].quantity==3&&party.orders[0].price==9&&party.orders[1].quantity==2&&party.orders[1].price==7,"Birthday party wants three strawberry with sprinkles at $9 and two vanilla at $7");
        Check(party.RequiredStock().SequenceEqual(new[]{5,2,0,3,3})&&party.Revenue==41,"Mixed party needs five batter, two vanilla, three strawberry, three sprinkles and yields $41");
        await Frames();ScreenCapture.CaptureScreenshot("Library/CodexPlaytests/mixed-orders-map.png");await Frames();
        Click(h.hotspotButtons[0]);await Frames();Check(h.detailNeeds.text=="Missing\nBatter  1\nStrawberry  1\nSprinkles  1","Popup totals shortages across both recipes");Click(h.closeDetail);Click(h.inspect);
        int[] stock=(int[])route.stock.amounts.Clone();PrepareOrder(party.orders[0]);PrepareOrder(party.orders[1]);
        Check(route.tray.Cones.Count==2&&route.stock.amounts.SequenceEqual(new[]{stock[0]-2,stock[1]-1,stock[2],stock[3]-1,stock[4]-1}),"Cooking two different orders consumes their exact ingredients");
        Use(route.tray);route.StartRoute();await Frames();
        var target=party.Customers.First(c=>c.Order==party.orders[1]);
        var wrong=Object.Instantiate(r.waffle.conePrefab);wrong.Restore(party.orders[0].recipe,party.orders[0].sprinkles);
        r.interaction.Release();r.interaction.PickUp(wrong);AimCustomer(target,false);
        r.interaction.ProcessInput(true,false,false,false,Vector2.zero,.02f);
        Check(!target.Served&&route.CarriedCash==0&&r.interaction.Held==wrong,"A customer rejects the other recipe from the same location");
        Object.Destroy(r.interaction.Release().gameObject);r.interaction.PickUp(route.tray);AimCustomer(target,false);
        var expected=route.tray.Cones.Single(c=>target.Matches(c));r.interaction.ProcessInput(true,false,false,false,Vector2.zero,.02f);
        Check(target.Served&&route.CarriedCash==7&&route.tray.Cones.Count==1&&!route.tray.Cones.Contains(expected),"Tray selects the vanilla cone and pays that customer's $7 price");
        Check(party.RemainingFor(party.orders[0])==3&&party.RemainingFor(party.orders[1])==1,"Only vanilla's remaining count decreases");
        target=party.Customers.First(c=>c.Order==party.orders[0]);AimCustomer(target,false);r.interaction.ProcessInput(true,false,false,false,Vector2.zero,.02f);
        Check(target.Served&&route.CarriedCash==16&&route.tray.Cones.Count==0,"The strawberry order pays $9 and consumes the other cone");
        Check(party.RequiredStock(true).SequenceEqual(new[]{3,1,0,2,2}),"Remaining ingredient demand excludes both served orders");
        h.RefreshPlan();route.ToggleMap();await Frames();
        Check(h.crowdCards[0].orders[0].quantityPrice.text=="×2  $9 ea"&&h.crowdCards[0].orders[1].quantityPrice.text=="×1  $7 ea","Map updates each recipe count after service");
        ScreenCapture.CaptureScreenshot("Library/CodexPlaytests/mixed-orders-after-service.png");await Frames();
        for(int day=2;day<=3;day++)
        {
            r.player.Teleport(r.truck.transform,r.truck.kitchen.position,r.truck.kitchen.rotation);route.FinishRoute();route.NextDay();await Frames(12);Manual();h=route.hud;
            Check(route.hotspots.All(c=>c.orders.Length==3&&c.orders.Select(o=>o.Label).Distinct().Count()==3),"Day "+day+" locations have three distinct recipes");
            Check(route.hotspots.All(c=>c.Customers.Count==c.CustomerCount),"Day "+day+" spawns every mixed order customer");
            foreach(var button in h.pointButtons){Click(button);Click(button);Click(button);}
        }
        Check(route.hotspots.Any(c=>c.orders.Any(o=>o.recipe.Length==3&&o.sprinkles))&&route.hotspots.Any(c=>c.orders.Any(o=>o.recipe.Length==2)),"Later days mix single, double, and triple scoop orders with optional sprinkles");
        for(int i=0;i<h.crowdCards.Length;i++)foreach(var row in h.crowdCards[i].orders)Check(row.quantityPrice.preferredWidth<=row.quantityPrice.rectTransform.rect.width,"Recipe count and price fit their row");
        await Frames();ScreenCapture.CaptureScreenshot("Library/CodexPlaytests/mixed-orders-day-three.png");await Frames();
        return Report("mixed-orders");
    }
    public static async Task<string> Menu()
    {
        checks=new List<string>();EditorApplication.isPaused=false;await Frames();
        Check(SceneManager.GetActiveScene().name=="MainMenu","Play starts at the mode menu");
        var menu=GameModeMenu.Instance;
        ScreenCapture.CaptureScreenshot("Library/CodexPlaytests/mode-main-menu.png");await Frames();
        Click(menu.freeDriveButton);await Frames(12);Manual();
        Check(route==null&&r.interaction.stock==null&&!r.truck.automaticRoute&&r.tubs.Count(t=>t.gameObject.activeSelf)==12,"Free drive retains twelve tubs, unlimited stock, and manual driving");
        r.GetComponent<GameModeMenu>().ReturnToMenu();await Frames(12);
        Check(SceneManager.GetActiveScene().name=="MainMenu","Free drive can return to menu");
        Click(GameModeMenu.Instance.parkRouteButton);await Frames(12);Manual();
        Check(route!=null&&route.Phase==RouteGameManager.RoutePhase.Planning&&route.MapOpen,"Park route opens pre-day planning");
        Check(route.Bank==75&&route.stock.Used==14&&route.stock.capacity==36,"Planning starts with $75 and fourteen leftover units in 36-unit storage");
        Check(!r.customers.enabled&&!r.world.generateOnAwake&&r.truck.automaticRoute,"Route scene uses its own crowds and automatic truck");
        return Report("route-menu");
    }
    public static async Task<string> Planning()
    {
        checks=new List<string>();EditorApplication.isPaused=false;Manual();await Frames();
        int before=route.Bank;Click(route.hud.buyButtons[3]);Click(route.hud.buyButtons[4]);
        Check(route.Bank==before-3&&route.stock.amounts[3]==3&&route.stock.amounts[4]==3,"Buying one strawberry and one sprinkles charges exactly $3");
        Click(route.hud.pointButtons[0]);Click(route.hud.pointButtons[0]);
        Click(route.hud.pointButtons[4]);Click(route.hud.pointButtons[4]);
        Click(route.hud.pointButtons[1]);Click(route.hud.pointButtons[5]);
        Check(route.Count(RouteGameManager.RouteControl.Stop)==2&&route.Count(RouteGameManager.RouteControl.Slow)==2,"Plan contains two stops and two slow zones");
        Click(route.hud.pointButtons[2]);
        Check(route.points[2].control==RouteGameManager.RouteControl.None,"A full control budget refuses additional placements");
        Check(Mathf.Abs(route.ArrivalAt(route.Length)-436)<.1f,"Exit projection includes 80 seconds stopped and 56 seconds of slowing");
        Click(route.hud.hotspotButtons[1]);
        Check(route.hud.SelectedHotspot==1&&route.hud.detailTitle.text.Contains("Playground")&&route.hud.crowdCards[1].orders[0].flavors[0].sprite==route.stock.flavors[0].orderPicture,"Hotspot selection reveals the crowd's recipe");
        int predicted=route.hotspots.Where(h=>h.gameObject.activeSelf).Sum(h=>h.Revenue);
        Check(predicted>route.Goal*2&&route.hotspots.Count(h=>h.gameObject.activeSelf)==4,"First day provides four hotspots worth more than twice the banking goal");
        Check(route.hotspots.Where(h=>h.gameObject.activeSelf).All(h=>h.Difficulty>=1&&h.closesAt>h.opensAt&&h.LaborSeconds>0),"Every hotspot exposes a valid labor estimate and time window");
        route.hud.SelectHotspot(0);await Frames();
        ScreenCapture.CaptureScreenshot("Library/CodexPlaytests/route-planning.png");await Frames();
        return Report("route-planning");
    }
    static void Aim(Interactable target)
    {
        Vector3 local=r.truck.transform.InverseTransformPoint(target.transform.position);
        r.player.Teleport(r.truck.transform,r.truck.transform.TransformPoint(new Vector3(Mathf.Clamp(local.x+(target is IceCreamTub ? .65f : 0),-2.8f,.8f),.64f,target is ServingTray ? .65f : .10f)),r.truck.transform.rotation);
        r.player.view.transform.LookAt(target.GetComponent<Collider>().bounds.center);Physics.SyncTransforms();
        r.interaction.ProcessInput(false,false,false,false,Vector2.zero,.02f);
        Check(r.interaction.Target==target,"Kitchen ray reaches "+target.name+"; actual="+r.interaction.Target);
    }
    static void Use(Interactable target)
    {
        Aim(target);r.interaction.ProcessInput(!(target is TruckDoor || target is TruckSeat),false,false,false,Vector2.zero,.02f,target is TruckDoor || target is TruckSeat);
    }
    static void Hold(Interactable target,int frames,bool motion)
    {
        Aim(target);
        for(int i=0;i<frames;i++)r.interaction.ProcessInput(false,true,false,false,motion?new Vector2(0,i%2==0?20:-20):Vector2.zero,.02f);
        r.interaction.ProcessInput(false,false,true,false,Vector2.zero,.02f);
    }
    static void PutDown()
    {
        r.interaction.ProcessInput(false,false,false,true,Vector2.zero,.02f);
        Check(r.interaction.Held==null,"Tool returned home");
    }
    public static async Task<string> Preparation()
    {
        checks=new List<string>();EditorApplication.isPaused=false;Manual();
        if(route.MapOpen)route.ToggleMap();await Frames();
        int[] before=(int[])route.stock.amounts.Clone();
        for(int count=0;count<3;count++)
        {
            if(!r.waffle.IsOpen)Use(r.waffle);
            Use(r.batter);Hold(r.waffle,70,false);PutDown();Use(r.waffle);
            r.waffle.Advance(r.day.settings.cookSeconds+.1f);Use(r.waffle);Use(r.waffle);
            Check(r.interaction.Held is IceCreamCone,"Finite batter cooks into a held cone");
            var cone=(IceCreamCone)r.interaction.Held;Use(r.holders[2]);
            Use(r.scooper);Hold(r.tubs.Single(t=>t.flavor==route.stock.flavors[2]),70,true);Use(cone);PutDown();
            Use(r.shaker);Hold(cone,60,true);PutDown();Use(cone);Use(route.tray);
        }
        Check(route.stock.amounts[0]==before[0]-3&&route.stock.amounts[3]==before[3]-3&&route.stock.amounts[4]==before[4]-3,"Three completed cones consume exactly three batter, strawberry, and sprinkles");
        Check(route.tray.Cones.Count==3&&route.tray.Cones.All(c=>c.Flavors.Count==1&&c.HasSprinkles),"Tray stores three visibly prepared matching cones");
        Use(r.scooper);
        Check(!r.tubs.Single(t=>t.flavor==route.stock.flavors[2]).CanGesture(r.interaction),"Exhausted strawberry cannot produce another scoop");PutDown();Use(route.tray);
        r.player.view.transform.LookAt(route.tray.transform.position);await Frames();
        ScreenCapture.CaptureScreenshot("Library/CodexPlaytests/route-loaded-tray.png");await Frames();
        return Report("route-preparation");
    }
    static void Tick(float seconds)
    {
        int frames=Mathf.CeilToInt(seconds/.1f);
        for(int i=0;i<frames;i++)route.Advance(Mathf.Min(.1f,seconds-i*.1f));
    }
    static void Walk(float yaw,int frames)
    {
        r.player.transform.rotation=r.truck.transform.rotation*Quaternion.Euler(0,yaw,0);
        for(int i=0;i<frames;i++)r.player.Move(Vector2.up,Vector2.zero,.02f);
        Physics.SyncTransforms();
    }
    static void AimCustomer(RouteCustomer customer,bool inside)
    {
        if(inside)
        {
            Vector3 local=r.truck.transform.InverseTransformPoint(customer.transform.position);
            r.player.Teleport(r.truck.transform,r.truck.transform.TransformPoint(new Vector3(Mathf.Clamp(local.x,-2.4f,.4f),.64f,.75f)),r.truck.transform.rotation);
        }
        else r.player.Teleport(null,customer.transform.position+Vector3.forward*2,Quaternion.identity);
        r.player.view.transform.LookAt(customer.transform.position+Vector3.up*(inside?1.85f:1.1f));Physics.SyncTransforms();
        r.interaction.ProcessInput(false,false,false,false,Vector2.zero,.02f);
        Check(r.interaction.Target==customer,"Serving ray reaches "+customer.name+"; actual="+r.interaction.Target);
    }
    public static async Task<string> ServiceAndDelivery()
    {
        checks=new List<string>();EditorApplication.isPaused=false;Manual();
        if(!route.MapOpen)route.ToggleMap();await Frames();Click(route.hud.launch);await Frames();
        Check(route.Phase==RouteGameManager.RoutePhase.Running&&!route.MapOpen,"Launch button starts automatic route");
        Vector3 local=r.player.transform.localPosition;Tick(2);
        Check(route.Distance>2&&Vector3.Distance(local,r.player.transform.localPosition)<.01f,"Standing player rides with moving truck");
        route.ToggleMap();float before=route.Clock;Tick(1);
        Check(route.Clock>before&&!r.day.CanPlay,"Map remains live while camera interaction is suspended");
        r.day.TogglePause();before=route.Clock;Tick(1);Check(route.Clock==before,"Pause freezes the truck clock");r.day.TogglePause();route.ToggleMap();
        var control=route.points[2].control;route.CyclePoint(2);Check(route.points[2].control==control,"Placements lock after departure");
        for(int i=0;i<1000&&!route.Stopped;i++)route.Advance(.1f);
        Check(route.CurrentStop==0&&Mathf.Abs(route.Distance-42)<.01f,"Truck reaches planned stop A without overshooting");
        Tick(1);
        foreach(var h in route.hotspots)foreach(var c in h.Customers)for(int i=0;i<300;i++)if(c.Available)c.Advance(.05f);
        Check(route.WindowQueue.Count>0&&route.WindowQueue[0].Arrived,"Nearby crowd lines up at the stopped truck window");
        var customer=route.WindowQueue[0];route.tray.Cones[0].Restore(customer.Order.recipe,customer.Order.sprinkles);AimCustomer(customer,true);int bank=route.Bank;
        r.interaction.ProcessInput(true,false,false,false,Vector2.zero,.02f);
        Check(customer.Served&&route.Bank==bank+customer.Order.price&&route.CarriedCash==0&&route.tray.Cones.Count==2,"Window sale removes the matching tray cone and banks its order price");
        r.player.Teleport(r.truck.transform,r.truck.transform.TransformPoint(new Vector3(-2.6f,.64f,0)),r.truck.transform.rotation);
        r.player.view.transform.LookAt(r.truck.rearDoor.GetComponent<Collider>().bounds.center);r.interaction.ProcessInput(false,false,false,false,Vector2.zero,.02f,true);await Task.Delay(800);
        Walk(270,65);Check(!r.truck.InsideTruck,"Runner walks out while carrying the serving tray");
        customer=route.WindowQueue[0];route.tray.Cones[0].Restore(customer.Order.recipe,customer.Order.sprinkles);AimCustomer(customer,false);bank=route.Bank;
        r.interaction.ProcessInput(true,false,false,false,Vector2.zero,.02f);
        Check(customer.Served&&route.CarriedCash==customer.Order.price&&route.Bank==bank,"Outside sale is carried cash and does not credit the register");
        r.player.view.transform.LookAt(r.truck.transform.position+Vector3.up);await Frames();ScreenCapture.CaptureScreenshot("Library/CodexPlaytests/route-runner-cash.png");await Frames();
        r.player.Teleport(null,r.truck.transform.TransformPoint(new Vector3(-5,-.025f,0)),r.truck.transform.rotation);Walk(90,65);Tick(.1f);
        Check(r.truck.InsideTruck&&route.CarriedCash==0&&route.Bank==bank+customer.Order.price,"Walking back aboard banks the runner's sale");
        int funds=route.Bank,units=route.stock.amounts[1];route.stock.Purchase(1);
        Check(route.Deliveries.Count==1&&route.Deliveries[0].quantity==6&&route.Bank==funds-9&&route.stock.amounts[1]==units,"During-route purchase charges $9 for a six-pack without instant stock");
        Check(route.Deliveries[0].stop==4&&route.Deliveries[0].readyAt>route.Clock,"Delivery targets the next planned stop after deterministic readiness");
        Tick(route.StopRemaining+.1f);route.EmergencyStop();
        Check(route.Stopped&&route.EmergencyStops==0&&route.StopRemaining==25,"Baseline rescue stop holds truck for 25 seconds");
        route.EmergencyStop();Check(route.EmergencyStops==0,"Rescue reserve cannot be spent twice");Tick(25.1f);
        route.stock.Add(0,route.stock.capacity-route.stock.Used-2);
        int waste=route.WastedStock;
        for(int i=0;i<5000&&!route.Deliveries[0].delivered;i++)route.Advance(.1f);
        Check(route.CurrentStop==4&&route.Deliveries[0].delivered,"Bulk supplies arrive at planned stop E");
        Check(route.stock.Used==route.stock.capacity&&route.WastedStock==waste+4,"Two delivered units fit; four overflow units are lost");
        funds=route.Bank;route.OrderDelivery(1);Check(route.Deliveries.Count==1&&route.Bank==funds,"No later delivery stop means no charge and no order");
        return Report("route-service-delivery");
    }
    public static async Task<string> ExitAndNextDay()
    {
        checks=new List<string>();EditorApplication.isPaused=false;Manual();
        if(route.MapOpen)route.ToggleMap();
        r.player.Teleport(r.truck.transform,r.truck.kitchen.position,r.truck.kitchen.rotation);
        if(route.stock.Packed>0)route.stock.Unpack();
        await Frames();
        route.stock.Pack(0);route.stock.Pack(0);route.stock.Pack(0);Check(route.stock.Packed==3,"Supply bag packs three units from truck stock");
        var customer=route.hotspots[3].Customers.First(c=>c.Available);
        route.tray.Cones[0].Restore(customer.Order.recipe,customer.Order.sprinkles);
        AimCustomer(customer,false);int bank=route.Bank;r.interaction.ProcessInput(true,false,false,false,Vector2.zero,.02f);
        Check(route.CarriedCash==customer.Order.price,"Runner earns cash from a second hotspot");
        for(int i=0;i<2;i++){var c=Object.Instantiate(r.waffle.conePrefab);c.Restore(route.hotspots[0].orders[0].recipe,true);route.tray.Store(c);}
        var saved=Object.Instantiate(r.waffle.conePrefab,r.holders[0].socket.position,r.holders[0].socket.rotation,r.holders[0].socket.parent);saved.Restore(new[]{route.stock.flavors[0]},false);r.holders[0].Occupant=saved;saved.Holder=r.holders[0];
        int carried=route.CarriedCash;int[] stock=(int[])route.stock.amounts.Clone();
        for(int i=0;i<8000&&route.Phase!=RouteGameManager.RoutePhase.Results;i++)route.Advance(.1f);
        Check(route.Phase==RouteGameManager.RoutePhase.Results&&route.LeftBehind,"Park exit closes route with runner left outside");
        Check(route.LostCash==carried&&route.LostCones==2&&route.LostIngredients==3&&route.CarriedCash==0&&route.tray.Cones.Count==0,"Exit removes carried cash, two tray cones, and three packed ingredients");
        Check(route.Bank==bank,"Lost outside earnings never enter banked funds");await Frames();
        ScreenCapture.CaptureScreenshot("Library/CodexPlaytests/route-left-behind.png");await Frames();Click(route.hud.nextDay);await Frames(12);Manual();
        Check(RouteGameManager.DayNumber==2&&route.Phase==RouteGameManager.RoutePhase.Planning,"Next day returns to planning");
        Check(route.stock.amounts.SequenceEqual(stock)&&r.holders[0].Occupant!=null,"Leftover truck stock and prepared cone survive into the next day");
        Check(route.stopBudget==2&&route.slowBudget==2&&route.EmergencyStops==1,"A poor result retains the baseline route-control budget");
        Check(route.hotspots.Count(h=>h.gameObject.activeSelf)==6&&route.hotspots.Any(h=>h.kind==RouteHotspot.CrowdKind.Sports),"Day two expands to six opportunities and short sports surges");
        route.StartRoute();route.FinishRoute();route.NextDay();await Frames(12);Manual();
        Check(route.hotspots.Any(h=>h.kind==RouteHotspot.CrowdKind.Picnic&&h.orders.Any(o=>o.recipe.Length==3&&o.sprinkles)),"Day three introduces premium three-flavor picnics");
        return Report("route-exit-next-day");
    }
    public static async Task<string> MovingKitchenAndSuccess()
    {
        checks=new List<string>();EditorApplication.isPaused=false;Manual();
        if(route.MapOpen)route.ToggleMap();
        route.StartRoute();
        int batter=route.stock.amounts[0],vanilla=route.stock.amounts[1];
        Use(r.waffle);Use(r.batter);Aim(r.waffle);
        float start=route.Distance;
        for(int i=0;i<70;i++)
        {
            r.interaction.ProcessInput(false,true,false,false,Vector2.zero,.02f);
            route.Advance(.02f);r.player.Move(Vector2.zero,Vector2.zero,.02f);
        }
        r.interaction.ProcessInput(false,false,true,false,Vector2.zero,.02f);PutDown();Use(r.waffle);
        for(int i=0;i<300;i++){route.Advance(.02f);r.waffle.Advance(.02f);r.player.Move(Vector2.zero,Vector2.zero,.02f);}
        Use(r.waffle);Use(r.waffle);
        Check(r.interaction.Held is IceCreamCone&&route.stock.amounts[0]==batter-1,"Pouring and cooking aboard the moving truck produces a cone and spends one batter");
        var cone=(IceCreamCone)r.interaction.Held;Use(r.holders[2]);Use(r.scooper);Aim(r.tubs.Single(t=>t.flavor==route.stock.flavors[0]));
        for(int i=0;i<70;i++)
        {
            r.interaction.ProcessInput(false,true,false,false,new Vector2(0,i%2==0?20:-20),.02f);
            route.Advance(.02f);r.player.Move(Vector2.zero,Vector2.zero,.02f);
        }
        r.interaction.ProcessInput(false,false,true,false,Vector2.zero,.02f);Use(cone);PutDown();
        Check(cone.Flavors.Count==1&&cone.Flavors[0]==route.stock.flavors[0]&&route.stock.amounts[1]==vanilla-1,"Moving-truck scooping completes and spends one vanilla");
        Check(route.Distance>start+10&&r.truck.InsideTruck&&r.player.transform.parent==r.truck.transform&&r.player.controller.isGrounded,"CharacterController stays grounded aboard through ten meters of kitchen work");
        route.CompleteSale(route.hotspots[0].Customers[0],route.Goal);route.FinishRoute();
        Check(!route.LeftBehind&&route.LostCash==0,"Finishing aboard banks earnings without outside loss");
        route.NextDay();await Frames(12);Manual();
        Check(route.EmergencyStops==2&&route.stopBudget==2&&route.slowBudget==2,"A successful day adds one rescue reserve and preserves the baseline plan budget");
        route.StartRoute();route.CompleteSale(route.hotspots[0].Customers[0],route.Goal);route.FinishRoute();route.NextDay();await Frames(12);Manual();
        Check(route.EmergencyStops==2,"Consecutive success cannot accumulate more than one rescue reserve");
        return Report("route-moving-kitchen-success");
    }

    public static async Task<string> FullConeCarryover()
    {
        checks=new List<string>();EditorApplication.isPaused=false;await Frames();
        GameModeMenu.Instance.ParkRoute();await Frames(12);Manual();route.ToggleMap();
        foreach(var holder in r.holders)
        {
            var cone=Object.Instantiate(r.waffle.conePrefab,holder.socket.position,holder.socket.rotation,holder.socket.parent);
            cone.Restore(route.hotspots[0].orders[0].recipe,true);holder.Occupant=cone;cone.Holder=holder;
        }
        for(int i=0;i<3;i++){var cone=Object.Instantiate(r.waffle.conePrefab);cone.Restore(route.hotspots[0].orders[0].recipe,true);route.tray.Store(cone);}
        var held=Object.Instantiate(r.waffle.conePrefab);held.Restore(route.hotspots[0].orders[0].recipe,true);r.interaction.PickUp(held);
        route.StartRoute();route.FinishRoute();route.NextDay();await Frames(12);Manual();
        Check(r.holders.All(h=>h.Occupant!=null),"All six stored cones survive the next day");
        Check(route.tray.Cones.Count==3&&r.interaction.Held is IceCreamCone,"Full tray and handheld cone also survive the next day");
        Check(route.tray.Cones.All(c=>c.HasSprinkles&&c.Flavors[0]==route.stock.flavors[2])&&((IceCreamCone)r.interaction.Held).HasSprinkles,"Restored cones retain flavors and sprinkles");
        route.StartRoute();Tick(100);route.hud.RefreshPlan();
        Check(route.hud.pointLabels[0].text.Contains("DONE"),"Passed route points are marked done");
        Check(route.hud.emergencyLabel.text.Contains("Rescue stop"),"Authored rescue label updates through its serialized reference");
        return Report("route-full-cone-carryover");
    }

}
