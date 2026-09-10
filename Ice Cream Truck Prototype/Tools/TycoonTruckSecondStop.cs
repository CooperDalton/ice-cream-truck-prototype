var g=TycoonGameManager.Instance;var w=g.workers.Single(w=>w.driver);
if(g.truck.routeStop!=1||!g.truck.AtStop||g.sites[2].revenue!=19.5f)throw new System.Exception("First truck sale or route failed");
g.truck.routeComplete=false;
var customer=UnityEngine.Object.Instantiate(g.catalog.customerPrefab,g.sites[2].queuePoint.position,UnityEngine.Quaternion.identity);
customer.game=g;customer.site=2;customer.order=new TycoonOrder{id=g.nextId++,cone=false,flavors=new[]{2,3},toppings=3,patience=180};g.sites[2].queue.Add(customer);g.actors.Add(customer);
g.player.Teleport(g.truck.kitchenEntry.position);g.player.transform.rotation=g.truck.transform.rotation*UnityEngine.Quaternion.Euler(0,90,0);g.player.view.transform.localRotation=UnityEngine.Quaternion.Euler(20,0,0);
UnityEngine.ScreenCapture.CaptureScreenshot("Library/CodexPlaytests/TycoonTruckKitchen.png");
return "Second stop: strawberry and mint bowl with both toppings. Expected additional $18.50.";
