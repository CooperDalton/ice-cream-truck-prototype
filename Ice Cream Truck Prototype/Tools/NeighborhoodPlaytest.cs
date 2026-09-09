using System;
using System.Collections.Generic;
using System.Linq;
using System.IO;
using UnityEngine;
using Object=UnityEngine.Object;
public static class NeighborhoodPlaytest
{
    static PrototypeSceneReferences r;
    static List<string> checks;
    public static string Run()
    {
        r=PrototypeSceneReferences.Instance;checks=new List<string>();
        r.player.ManualInput=r.interaction.ManualInput=r.truck.ManualInput=r.customers.ManualInput=true;
        r.day.enabled=false;
        Check(r.world.HalfExtent==204,"Town is 408 metres across");
        var ports=r.world.RoadPorts;int width=ports.GetLength(0);int center=width/2;
        var dirs=new[]{Vector2Int.up,Vector2Int.right,Vector2Int.down,Vector2Int.left};
        var queue=new Queue<Vector2Int>();var distance=new Dictionary<Vector2Int,int>();
        var start=new Vector2Int(center,center);queue.Enqueue(start);distance[start]=0;
        while(queue.Count>0)
        {
            var cell=queue.Dequeue();
            for(int d=0;d<4;d++)
            {
                if((ports[cell.x,cell.y]&(1<<d))==0)continue;
                var next=cell+dirs[d];
                if(next.x<0||next.y<0||next.x>=width||next.y>=width||(ports[next.x,next.y]&(1<<((d+2)%4)))==0)throw new Exception("Disconnected road port");
                if(distance.ContainsKey(next))continue;
                distance[next]=distance[cell]+1;queue.Enqueue(next);
            }
        }
        Check(distance.Count==ports.Cast<int>().Count(p=>p!=0),"Every road connects to the starting junction");
        Check(distance.Values.Max()*r.world.settings.tileSize>=300,"Farthest road trip is "+distance.Values.Max()*r.world.settings.tileSize+" metres");
        float nearest=float.MaxValue;
        for(int a=0;a<r.world.Hotspots.Count;a++)for(int b=a+1;b<r.world.Hotspots.Count;b++)nearest=Mathf.Min(nearest,Vector3.Distance(r.world.Hotspots[a].position,r.world.Hotspots[b].position));
        Check(nearest>=96,"Customer areas are at least "+nearest.ToString("F1")+" metres apart");
        Check(r.customers.Residents.GroupBy(c=>c.HomeArea).All(g=>g.Count()==6),"Every area has six residents");
        Check(r.world.trees.Length==6 && r.world.houses.Length==6,"Six tree and six house models are wired");
        r.customers.ReleaseQueue();
        foreach(var resident in r.customers.Residents) if(resident.Leaving) {resident.transform.position=resident.Home;resident.Follow(new List<Vector3>{resident.Home});resident.Advance(.1f);resident.Advance(61);}
        ParkAt(0);
        if(!r.boombox.Playing)r.boombox.ToggleMusic();
        var crowd=r.customers.Residents.Where(c=>c.HomeArea==0).ToArray();
        int count=r.customers.Residents.Count;int revenue=r.day.Earnings;
        for(int served=0;served<crowd.Length;served++)
        {
            r.customers.AttractNearby();
            var customer=r.customers.Front;
            Check(customer!=null && customer.HomeArea==0,"Next customer belongs to this stop");
            for(int tick=0;tick<1600 && !customer.Arrived;tick++)foreach(var waiting in r.customers.Queue.ToArray())waiting.Advance(.05f);
            Check(customer.Arrived,"Customer reaches serving window around scenery");
            var cone=Object.Instantiate(r.waffle.conePrefab);cone.Restore(customer.Order.ToArray(),customer.WantsSprinkles);
            r.interaction.PickUp(cone,true);customer.Use(r.interaction);
            Check(customer.ServedToday && r.interaction.Held==null,"Sale marks customer served for the day");
        }
        Check(crowd.All(c=>c.ServedToday),"All six residents served; area cleared");
        foreach(var customer in crowd)
        {
            for(int i=0;i<1600&&!customer.Idle;i++)customer.Advance(.05f);
            Check(customer.Idle,"Served resident walks home");
            customer.Advance(601);
        }
        r.customers.AttractNearby();
        Check(r.customers.Queue.Count==0,"Cleared area stays empty after ten minutes with music playing");
        Check(r.customers.Residents.Count==count,"No replacement residents spawn");
        int nextArea=Enumerable.Range(1,r.world.Hotspots.Count-1).OrderBy(i=>Vector3.Distance(r.world.Hotspots[0].position,r.world.Hotspots[i].position)).First();
        ParkAt(nextArea);r.customers.AttractNearby();
        Check(r.customers.Queue.Count>0 && r.customers.Queue.All(c=>c.HomeArea==nextArea && !c.ServedToday),"Arriving at another neighborhood attracts a fresh crowd");
        checks.Add("Revenue from first stop: $"+(r.day.Earnings-revenue));
        string report=string.Join("\n",checks);Directory.CreateDirectory("Library/CodexPlaytests");File.WriteAllText("Library/CodexPlaytests/neighborhood-checks.txt",report);return report;
    }
    static void ParkAt(int area)
    {
        var target=r.world.Hotspots[area].position;
        var ports=r.world.RoadPorts;int center=ports.GetLength(0)/2;
        Vector3 best=Vector3.zero;float distance=float.MaxValue;int mask=0;
        for(int x=0;x<ports.GetLength(0);x++)for(int z=0;z<ports.GetLength(1);z++)
        {
            if(ports[x,z]==0)continue;
            var point=new Vector3((x-center)*24,0,(z-center)*24);
            if((point-target).sqrMagnitude>=distance)continue;
            best=point;distance=(point-target).sqrMagnitude;mask=ports[x,z];
        }
        r.truck.transform.SetPositionAndRotation(best,Quaternion.Euler(0,(mask&10)!=0?0:90,0));
        r.player.Teleport(r.truck.transform,r.truck.kitchen.position,r.truck.kitchen.rotation);
        Physics.SyncTransforms();
    }
    static void Check(bool passed,string message)
    {
        if(!passed)throw new Exception(message);
        checks.Add("PASS: "+message);
    }
}
