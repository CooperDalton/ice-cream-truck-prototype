// Run on the disposable campaign after the tutorial playtest.
var game = TycoonGameManager.Instance; var player = game.player;
player.manualInput = true; game.restartRequested = true;
var checks = new System.Collections.Generic.List<string>();
void Check(bool condition, string message) { if (!condition) throw new System.Exception(message); checks.Add(message); }
void Aim(Vector3 point, Vector3 from)
{
    player.Teleport(from); player.view.transform.rotation = Quaternion.LookRotation(point-player.view.transform.position);
    Physics.SyncTransforms(); player.Aim();
}
game.hud.ClosePanels();
player.Teleport(game.supplier.position + new Vector3(0,0,3.6f));
for (int i=0; i<55; i++) player.controller.Move(new Vector3(0,-.04f,-.05f));
Check(player.transform.position.z < game.supplier.position.z + 1.1f && player.transform.position.y > .1f, "Player walks through the open doorway onto the indoor floor");
var tablet = game.parts.Single(p=>p.kind==TycoonPart.Kind.Supplier);
Aim(tablet.transform.position+Vector3.up*1.1f, game.supplier.position+new Vector3(0,.2f,.8f));
player.Select(player.inventory.Locate(TycoonItem.Kind.Bowls));
Check(player.target==tablet, "Tablet is reachable from inside the shop");
player.Use(false); Check(game.hud.shopPanel.activeSelf, "Clicking the tablet opens supplies while holding an item");
game.hud.ClosePanels();
game.tutorial.progress.step=TycoonTutorial.Step.CollectSupplies;
player.Select(player.inventory.Locate(TycoonItem.Kind.BasicScooper));
var oldScooper=player.Held; player.Drop();
var dropped=game.looseItems.Single(l=>ReferenceEquals(l.item,oldScooper));
Check(player.inventory.Locate(TycoonItem.Kind.BasicScooper)<0 && !dropped.body.isKinematic && dropped.supplySlot<0, "Q drop action releases the old scooper during day-two tutorial");
Check(dropped.Collect(player) && player.Held.kind==TycoonItem.Kind.BasicScooper, "Dropped scooper can be picked up again");
game.tutorial.progress.step=TycoonTutorial.Step.Complete;
for (int i=0; i<player.inventory.slots.Length; i++) player.inventory.slots[i]=new TycoonItem(TycoonItem.Kind.BasicScooper);
float cash=game.cash;
Check(game.PurchaseSupply(20), "Purchases succeed with a full inventory");
var delivery=game.looseItems.Single(l=>l.supplySlot>=0);
Check(game.cash==cash-12 && player.inventory.slots.All(i=>i.kind==TycoonItem.Kind.BasicScooper), "Purchase charges once and does not replace inventory items");
Check(!delivery.Collect(player) && game.looseItems.Contains(delivery) && delivery.body.isKinematic, "Full inventory leaves the purchase waiting on the counter");
player.Select(0); player.Drop();
Check(delivery.Collect(player) && player.Held.kind==TycoonItem.Kind.ImprovedScooper, "Dropping the old tool makes room to collect the upgrade");
game.PurchaseSupply(0); game.PurchaseSupply(1); game.PurchaseSupply(20);
Aim(game.supplier.position+new Vector3(0,1.15f,-.2f), game.supplier.position+new Vector3(0,0,4.6f));
System.IO.Directory.CreateDirectory("Library/CodexPlaytests");
ScreenCapture.CaptureScreenshot("Library/CodexPlaytests/WalkInSupplyShop.png");
System.IO.File.WriteAllText("Library/CodexPlaytests/SupplyShopChecks.txt","PASS\n"+string.Join("\n",checks));
return string.Join("\n",checks);
