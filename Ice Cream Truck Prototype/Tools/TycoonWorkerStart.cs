var g=TycoonGameManager.Instance;var w=g.workers.Single();
if(!w.ValidateLayout())throw new System.Exception(w.status);
float before=g.cash;g.OpenDay();foreach(var s in g.sites)s.open=false;
if(!w.onDuty||g.cash!=before-24)throw new System.Exception("Daily wage not paid correctly");
var customer=UnityEngine.Object.Instantiate(g.catalog.customerPrefab,g.sites[0].queuePoint.position,UnityEngine.Quaternion.identity);
customer.game=g;customer.site=0;customer.order=new TycoonOrder{id=g.nextId++,cone=true,flavors=new[]{0,1},toppings=3};g.sites[0].queue.Add(customer);g.actors.Add(customer);
g.player.Teleport(new UnityEngine.Vector3(-3.7f,0,-2));g.player.transform.rotation=UnityEngine.Quaternion.Euler(0,50,0);
System.IO.File.WriteAllText("Library/CodexPlaytests/TycoonWorker.txt","Starting cash "+before+"; after $24 wage "+g.cash+". Expected sale $16.50.\n");
return new {w.onDuty,g.cash,w.status,position=w.transform.position,locker=w.locker.operatingPoint.position};
