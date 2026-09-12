var g=TycoonGameManager.Instance;var p=g.player;p.manualInput=true;p.inventory=new TycoonInventory(8);g.cash=100;
var bike=g.bike;var start=bike.transform.position;
bike.Enter();var destination=g.supplier.position+new UnityEngine.Vector3(0,0,3);
for(int i=0;i<250&&UnityEngine.Vector3.Distance(bike.transform.position,destination)>1.5f;i++)
{
    bike.transform.rotation=UnityEngine.Quaternion.LookRotation(destination-bike.transform.position);UnityEngine.Physics.SyncTransforms();bike.Drive(UnityEngine.Vector2.up,.05f);
}
bike.Exit();
if(UnityEngine.Vector3.Distance(p.transform.position,g.supplier.position)>8)throw new System.Exception("Bicycle did not reach supplier");
if(!g.PurchaseSupply(18)||g.cash!=94)throw new System.Exception("Supplier purchase failed");
g.hud.OpenStorage(bike.cargo,"Bicycle cargo");
for(int i=0;i<3;i++)g.hud.playerSlots[i].button.onClick.Invoke();g.hud.ClosePanels();
if(bike.cargo.slots.Where(i=>i!=null&&i.kind==TycoonItem.Kind.Bowls).Sum(i=>i.amount)!=30)throw new System.Exception("Bicycle bowl loading failed");
if(!g.PurchaseSupply(0)||g.cash!=82)throw new System.Exception("Tub purchase failed");
int slot=p.inventory.Locate(TycoonItem.Kind.Tub);
p.inventory.Transfer(slot,bike.cargo);
bike.Enter();
for(int i=0;i<250&&UnityEngine.Vector3.Distance(bike.transform.position,start)>1.5f;i++)
{
    bike.transform.rotation=UnityEngine.Quaternion.LookRotation(start-bike.transform.position);UnityEngine.Physics.SyncTransforms();bike.Drive(UnityEngine.Vector2.up,.05f);
}
bike.Exit();
if(UnityEngine.Vector3.Distance(bike.transform.position,start)>2)throw new System.Exception("Bicycle return trip blocked");
bike.cargo.Transfer(bike.cargo.Locate(TycoonItem.Kind.Tub),p.inventory);p.Select(p.inventory.Locate(TycoonItem.Kind.Tub));
var tub=g.Parts(0,TycoonPart.Kind.Tub).Single(t=>t.variant==0);int before=tub.contents.amount;p.target=tub;p.Use(false);
if(tub.contents.amount!=24||p.Held.amount!=before)throw new System.Exception("Returned refill did not conserve stock");
var shelf=g.Parts(0,TycoonPart.Kind.Shelf).First();foreach(int i in Enumerable.Range(0,bike.cargo.slots.Length).Where(i=>bike.cargo.slots[i]!=null).ToArray())bike.cargo.Transfer(i,shelf.storage);
g.Save();
string result="Rode bicycle from home to supplier and back through Drive/Enter/Exit. Bought 30 bowls for $6 and a $12 vanilla tub directly into the hotbar, loaded cargo, unloaded at home. Cash $100 -> $82. Installed vanilla "+before+" -> 24, refill 24 -> "+before+". Bowls retained in home supply shelf.";
System.IO.File.WriteAllText("Library/CodexPlaytests/TycoonLogistics.txt",result);return result;
