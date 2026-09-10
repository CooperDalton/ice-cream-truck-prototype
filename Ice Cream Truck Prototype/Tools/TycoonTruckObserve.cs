var g=TycoonGameManager.Instance;var w=g.workers.Single(w=>w.driver);
string line="Clock "+g.clock+" truck="+g.truck.transform.position+" stop="+g.truck.routeStop+" atStop="+g.truck.AtStop+" worker="+w.transform.position+" step="+w.step+" status="+w.status+" cash="+g.cash+" queue="+g.sites[2].queue.Count;
System.IO.File.AppendAllText("Library/CodexPlaytests/TycoonTruck.txt",line+"\n");return line;
