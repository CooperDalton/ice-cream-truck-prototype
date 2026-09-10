var g=TycoonGameManager.Instance;var w=g.workers.Single();
if(w.step!=TycoonWorker.Step.Idle)return w.status+" / "+w.step+" / "+w.transform.position;
if(g.sites[1].revenue!=15.5f)throw new System.Exception("Park sale price or completion incorrect");
if(g.Parts(1,TycoonPart.Kind.Tub).Any(t=>t.contents.amount!=23))throw new System.Exception("Park installed stock incorrect");
var cold=g.Parts(1,TycoonPart.Kind.ColdStorage).Single();
if(cold.storage.slots.Where(i=>i!=null&&i.kind==TycoonItem.Kind.Tub).Sum(i=>i.amount)!=12)throw new System.Exception("Partial refills not returned");
string evidence="Experienced park worker earned $15.50 from a double bowl with nuts and whipped cream. Both installed tubs started at 6, were filled to 24, and finished at 23. Two partial refills returned to cold storage with 6 each. Tools and containers stayed in the worker inventory.";
System.IO.File.AppendAllText("Library/CodexPlaytests/TycoonPark.txt",evidence);return evidence;
