var g=TycoonGameManager.Instance;g.player.manualInput=true;
if(g.loadingCampaign||g.workers.Count!=3||!g.sites.All(s=>s.owned)||!g.sites[0].kiosk.activeSelf)throw new System.Exception("Campaign restore failed");
if(g.parts.Where(p=>p.site==2&&p.kind!=TycoonPart.Kind.Truck).Any(p=>!p.transform.IsChildOf(g.truck.transform)))throw new System.Exception("Truck equipment detached on restore");
var driver=g.workers.Single(w=>w.driver);string result="Reload: three staff, all owned sites, expanded kiosk, truck equipment still attached. Driver "+driver.status+"; truck "+g.truck.transform.position+"; route "+g.truck.routeStop;
System.IO.File.AppendAllText("Library/CodexPlaytests/TycoonFinalCampaign.txt",result+"\n");return result;
