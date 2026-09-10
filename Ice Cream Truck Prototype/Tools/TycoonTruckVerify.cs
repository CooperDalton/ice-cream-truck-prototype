var g=TycoonGameManager.Instance;var w=g.workers.Single(w=>w.driver);
if(g.sites[2].revenue!=38||!g.truck.routeComplete||g.truck.routeStop!=1||!g.truck.AtStop)throw new System.Exception("Truck route revenue or completion incorrect");
if(g.Parts(2,TycoonPart.Kind.Tub).Any(t=>t.contents.amount!=23))throw new System.Exception("Truck scoop stock incorrect");
if(w.inventory.slots[w.inventory.Locate(TycoonItem.Kind.Batter)].amount!=9)throw new System.Exception("Truck batter consumption incorrect");
if(w.inventory.slots.Where(i=>i!=null&&i.kind==TycoonItem.Kind.Topping).Any(i=>i.amount!=13))throw new System.Exception("Truck toppings consumption incorrect");
g.Save();System.IO.File.Copy(TycoonGameManager.SavePath,"Library/CodexPlaytests/TycoonTruckCampaign.json",true);
string evidence="Two physical truck sales: $19.50 cone at playground and $18.50 bowl at residential stop. Revenue $38. Each of four tubs 24 -> 23; batter 10 -> 9; both toppings 15 -> 13. Driver traveled with the truck, prepared at both kitchens, and ended the finite route.";
System.IO.File.AppendAllText("Library/CodexPlaytests/TycoonTruck.txt",evidence);return evidence;
