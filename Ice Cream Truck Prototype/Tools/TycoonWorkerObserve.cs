var g=TycoonGameManager.Instance;var w=g.workers.Single();
string result="clock="+g.clock+"; step="+w.step+"; status="+w.status+"; position="+w.transform.position+"; destination="+w.actor.agent.destination+"; path="+w.actor.agent.pathStatus+"; remaining="+w.actor.agent.remainingDistance+"; cash="+g.cash+"; stock="+string.Join(",",g.Parts(0,TycoonPart.Kind.Tub).Select(t=>t.contents.amount))+"; inventory="+string.Join(",",w.inventory.slots.Select(i=>i==null?"empty":i.kind+":"+i.amount));
System.IO.File.AppendAllText("Library/CodexPlaytests/TycoonWorker.txt",result+"\n");
return result;
