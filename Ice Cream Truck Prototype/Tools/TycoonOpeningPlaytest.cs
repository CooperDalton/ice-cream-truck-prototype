var g=TycoonGameManager.Instance;
var p=g.player; p.manualInput=true;
System.IO.Directory.CreateDirectory("Library/CodexPlaytests");
g.Save();
System.IO.File.Copy(TycoonGameManager.SavePath,"Library/CodexPlaytests/TycoonBeforeTests.json",true);
var evidence=new System.Collections.Generic.List<string>();
var inv=new TycoonInventory(1); var source=new TycoonItem(TycoonItem.Kind.Tub,24,2); var target=new TycoonItem(TycoonItem.Kind.Tub,7,2);
if(TycoonInventory.Refill(source,target)!=17||source.amount!=7||target.amount!=24) throw new System.Exception("Partial tub transfer failed");
evidence.Add("Partial refill: source 24 -> 7, target 7 -> 24; total preserved.");
var bowls=new TycoonInventory(1); bowls.Add(new TycoonItem(TycoonItem.Kind.Bowls,10)); var extra=new TycoonItem(TycoonItem.Kind.Bowls,5);
if(bowls.Add(extra)||bowls.slots[0].amount!=12||extra.amount!=3) throw new System.Exception("Stack overflow was lost");
evidence.Add("Full inventory: bowl stack 10 -> 12, source retained overflow 3.");
g.OpenDay(); foreach(var s in g.sites)s.open=false;
var prep=g.Parts(0,TycoonPart.Kind.Prep).First(); var counter=g.Parts(0,TycoonPart.Kind.ServingCounter).First();
for(int flavor=0;flavor<2;flavor++)
{
    var customer=UnityEngine.Object.Instantiate(g.catalog.customerPrefab,g.sites[0].queuePoint.position,UnityEngine.Quaternion.identity);
    customer.game=g;customer.site=0;customer.order=g.GenerateOrder(0); g.sites[0].queue.Add(customer);g.actors.Add(customer);
    customer.TakeOrder();customer.agent.Warp(customer.QueuePosition);
    var tub=g.Parts(0,TycoonPart.Kind.Tub).Single(t=>t.variant==flavor); int stock=tub.contents.amount;
    p.Select(1);p.target=prep;p.Use(false);
    p.Select(0);p.target=tub;p.Use(false);
    for(int frame=0;frame<240&&p.Held.loadedFlavor<0;frame++)p.Gesture(new UnityEngine.Vector2(0,frame/12%2==0?15:-15),1f/60);
    if(p.Held.loadedFlavor!=flavor||tub.contents.amount!=stock-1)throw new System.Exception("Basic scoop did not debit once");
    p.target=prep;p.Use(false);p.Use(true);
    int serving=p.inventory.Locate(TycoonItem.Kind.Serving);p.Select(serving);p.target=counter;p.Use(false);
    if(!UnityEngine.Mathf.Approximately(g.cash,(flavor+1)*8.4f))throw new System.Exception("Opening sale payment failed");
    evidence.Add("Sale "+(flavor+1)+": bowl placed, up/down scooping, scoop deposited, serving collected, cash $"+g.cash+"; tub "+stock+" -> "+tub.contents.amount);
}
if(!g.BuyUpgrade(0,0)||!UnityEngine.Mathf.Approximately(g.cash,4.8f))throw new System.Exception("First tool purchase failed");
evidence.Add("Two $6 sales with $2.40 tips funded the $12 improved scooper. Physical tool delivered at home.");
System.IO.File.WriteAllLines("Library/CodexPlaytests/TycoonOpening.txt",evidence);
return evidence;
