var g=TycoonGameManager.Instance;g.player.manualInput=true;
if(g.level!=7||g.looseItems.Count!=16||g.parts.Count(p=>p.kind==TycoonPart.Kind.Tub&&p.site==0)!=12)throw new System.Exception("Level rewards were lost or duplicated on reload");
if(g.Parts(0,TycoonPart.Kind.Tub).Single(t=>t.variant==0).contents.amount!=24)throw new System.Exception("Installed stock not restored");
if(g.player.inventory.slots[g.player.inventory.Locate(TycoonItem.Kind.Tub)].amount!=10)throw new System.Exception("Partial refill inventory not restored");
if(g.Parts(0,TycoonPart.Kind.Shelf).First().storage.Locate(TycoonItem.Kind.BowlPack)<0)throw new System.Exception("Supplier package not restored");
g.NextDay();g.hud.ToggleMap();UnityEngine.ScreenCapture.CaptureScreenshot("Library/CodexPlaytests/TycoonMap.png");
string evidence="Reloaded campaign: level 7, all 16 physical starter rewards retained exactly once, twelve home cooled modules with ten pending placement, installed vanilla full, partial refill retained, purchased package on shelf, bicycle position restored.";
System.IO.File.WriteAllText("Library/CodexPlaytests/TycoonReload.txt",evidence);return evidence;
