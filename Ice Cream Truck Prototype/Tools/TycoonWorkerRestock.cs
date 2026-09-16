var g=TycoonGameManager.Instance;var rack=g.Parts(0,TycoonPart.Kind.Shelf).First();
rack.storage.slots[0]=new TycoonItem(TycoonItem.Kind.Tub,24,0);rack.storage.slots[1]=new TycoonItem(TycoonItem.Kind.Tub,24,1);
System.IO.File.AppendAllText("Library/CodexPlaytests/TycoonWorker.txt","Observed worker stopped with empty installed tubs and no payment. Added two finite refill tubs to assigned-site shelf storage.\n");
return "Shelf stocked with two full refill tubs; the worker must walk to collect and transfer them.";
