var g=TycoonGameManager.Instance;var w=g.workers.Single(w=>w.driver);
w.locker.transform.localPosition=new UnityEngine.Vector3(0,.58f,-1.2f);w.locker.transform.localRotation=UnityEngine.Quaternion.Euler(0,180,0);g.navigation.BuildNavMesh();
if(!w.ValidateLayout())throw new System.Exception(w.status);
g.OpenDay();foreach(var s in g.sites)s.open=false;foreach(var employee in g.workers)if(!employee.driver)employee.onDuty=false;
g.truck.demand=new[]{0,0};
var customer=UnityEngine.Object.Instantiate(g.catalog.customerPrefab,g.truckStops[0].position+new UnityEngine.Vector3(-1.5f,0,3),UnityEngine.Quaternion.identity);
customer.game=g;customer.site=2;customer.order=new TycoonOrder{id=g.nextId++,cone=true,flavors=new[]{0,1},toppings=3,patience=300};g.sites[2].queue.Add(customer);g.actors.Add(customer);
System.IO.File.WriteAllText("Library/CodexPlaytests/TycoonTruck.txt","Start $"+g.cash+"; target truck order $19.50; two stops with finite demand.\n");
return "Driver layout valid; paid daily wage and vehicle charge; driving to first stop with a two-scoop cone and toppings ticket.";
