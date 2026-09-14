using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Threading.Tasks;
using UnityEngine;

// Run only in a disposable fresh campaign, with the user's save backed up first.
public static class TycoonTutorialPlaytest
{
    public static string Result { get; private set; } = "Not started";
    private static TycoonGameManager game;
    private static TycoonTutorial tutorial;
    private static TycoonPlayer player;
    private static readonly List<string> evidence = new List<string>();
    public static async void Start()
    {
        Result = "Running"; evidence.Clear();
        try
        {
            game = TycoonGameManager.Instance; tutorial = game.tutorial; player = game.player;
            player.manualInput = true; game.restartRequested = true;
            Check(tutorial.progress.step == TycoonTutorial.Step.PlaceEquipment, "Fresh tutorial starts with placement");
            Check(player.inventory.slots.Count(i => i != null && i.kind == TycoonItem.Kind.Equipment) == 6 && game.cash == 100, "Six packed furnishings and $100");
            Check(player.inventory.Locate(TycoonItem.Kind.BasicScooper) == 0 && player.inventory.Locate(TycoonItem.Kind.Bowls) == 1, "Scooper in slot 1 and bowls in slot 2");
            game.OpenDay(); Check(game.phase == TycoonGameManager.Phase.Preparation, "Opening is gated until layout is placed");
            await Shot("Tutorial01Setup");
            for (int i = 0; i < 6; i++)
            {
                var part = tutorial.Equipment[i]; var spot = tutorial.placementSpots[i];
                Check(!game.builder.CanPlace(part, spot.position + Vector3.right * .5f, spot.rotation, null, out _), "Wrong cell is rejected");
                player.Select(i + 2);
                var from = spot.position + (i == 3 || i == 4 ? Vector3.right * 1.3f : Vector3.back * 1.4f);
                Aim(spot.position, from);
                Check(game.builder.preview.activeSelf, "Placement preview visible for item " + i);
                player.Use(false); tutorial.Tick();
                Check(part.installed && !part.packed && Vector3.Distance(part.transform.position, spot.position) < .06f, "Placed item " + i + ": " + player.prompt);
                await Task.Delay(100);
                if (i == 2)
                {
                    game.Save(); TycoonSave.Load(game);
                    await WaitForLoad();
                    Check(tutorial.progress.placement == 3 && tutorial.Equipment.Take(3).All(p => p.installed), "Resume preserves placement progress and installed items");
                }
            }
            Check(tutorial.progress.step == TycoonTutorial.Step.OpenDay, "Layout completes before first opening");
            var hangingSign = game.Parts(0, TycoonPart.Kind.Sign).Single();
            Aim(hangingSign.transform.position, hangingSign.transform.position + new Vector3(0,-1.88f,-1.2f));
            Check(player.target == hangingSign, "Player can aim at the hanging canopy sign");
            player.Use(true); hangingSign.RefreshVisual();
            Check(hangingSign.signLabels.Length == 2 && hangingSign.signLabels.All(l => l.text == "OPEN"), "E opens the shop and both sign faces read OPEN");
            Check(game.sites[0].queue.Count == 1 && tutorial.Customer.ReadyToOrder, "First customer appears immediately at the register");
            for (int order = 0; order < 3; order++)
            {
                var customer = tutorial.Customer;
                if (order > 0)
                {
                    Check(tutorial.Practicing && !tutorial.uiRoot.activeSelf && !tutorial.bowlGhost.activeSelf && !tutorial.focusMesh.gameObject.activeSelf, "Later customers have no tutorial prompts, arrows or highlights");
                    if (order == 1)
                    {
                        game.Save(); TycoonSave.Load(game); await WaitForLoad(); customer = tutorial.Customer;
                        Check(tutorial.Practicing, "Practice resumes without repeating the walkthrough");
                    }
                }
                customer.TickPatience(500); Check(!customer.leaving && customer.order.patience > 0, "Tutorial customer waits for the player");
                Aim(customer.transform.position + Vector3.up * 1.4f, customer.transform.position + Vector3.back * 2);
                Check(player.customerTarget == customer, "Raycast targets the customer");
                player.Use(true); tutorial.Tick();
                Check(customer.order.stage == TycoonOrder.Stage.Pickup && (order == 0 ? tutorial.progress.step == TycoonTutorial.Step.SelectBowls : tutorial.Practicing), "E takes the order");
                if (order == 0) await Shot("Tutorial02BowlSlot");
                player.Select(player.inventory.Locate(TycoonItem.Kind.Bowls)); tutorial.Tick();
                var bowlPosition = tutorial.bowlSpot.position + (order == 0 ? Vector3.zero : Vector3.left * .25f);
                Aim(bowlPosition, bowlPosition + new Vector3(0, -.94f, -1.3f));
                player.Use(false); tutorial.Tick();
                Check(game.parts.Any(p => p.kind == TycoonPart.Kind.Bowl && Vector3.Distance(p.transform.position, bowlPosition) < .06f), order == 0 ? "Bowl placed on its ghost" : "Practice bowl can be placed away from the tutorial spot");
                if (order == 0)
                {
                    game.Save(); TycoonSave.Load(game); await WaitForLoad(); customer = tutorial.Customer;
                    Check(tutorial.progress.step == TycoonTutorial.Step.SelectScooper && customer.order.stage == TycoonOrder.Stage.Pickup && game.parts.Any(p => p.id == tutorial.progress.bowlId), "Resume reconnects the active customer and bowl");
                }
                player.Select(player.inventory.Locate(TycoonItem.Kind.BasicScooper)); tutorial.Tick();
                var tub = tutorial.Equipment[3 + customer.order.flavors[0]];
                Aim(tub.handTarget.position, tub.transform.position + Vector3.right * 1.3f);
                Check(player.target == tub, "Raycast targets highlighted flavor");
                if (order == 0) await Shot("Tutorial03Scoop");
                player.Use(false);
                for (int stroke = 0; stroke < 12 && player.Held.loadedFlavor < 0; stroke++) player.Gesture(new Vector2(0, stroke % 2 == 0 ? 90 : -90), .25f);
                player.CancelGesture(); tutorial.Tick();
                Check(player.Held.loadedFlavor == customer.order.flavors[0], "Mouse swipes load the correct flavor");
                var bowl = game.parts.Single(p => p.kind == TycoonPart.Kind.Bowl && Vector3.Distance(p.transform.position, bowlPosition) < .06f);
                Aim(bowl.transform.position + Vector3.up * .05f, bowl.transform.position + new Vector3(0, -.94f, -1.3f));
                player.Use(false); tutorial.Tick();
                Check(bowl.contents.Matches(customer.order), "Click deposits the scoop");
                player.Use(true); tutorial.Tick();
                Check(player.Held.Matches(customer.order), "E picks up the matching bowl");
                for (int frame = 0; frame < 100 && !customer.ReadyForPickup; frame++) await Task.Delay(100);
                Check(customer.ReadyForPickup, "Customer can reach the pickup counter");
                Aim(customer.transform.position + Vector3.up * 1.4f, customer.transform.position + Vector3.back * 2);
                Check(player.customerTarget == customer, "Pickup customer is reachable with E");
                player.Use(true); tutorial.Tick();
                Check(game.sales == order + 1 && player.Held == null, "Sale pays and consumes the completed serving");
                await Task.Delay(100);
            }
            Check(tutorial.progress.served == 3 && game.sites[0].queue.Count == 0, "Exactly three customers served");
            for (int frame = 0; frame < 140 && (!game.hud.daySummary.gameObject.activeSelf || !game.hud.daySummary.Finished); frame++) await Task.Delay(100);
            Check(game.phase == TycoonGameManager.Phase.Results && game.level == 2 && game.FlavorCount == 4, "Day ends early and unlocks exactly two flavors");
            Check(game.hud.daySummary.DisplayedLevel == 2 && game.hud.daySummary.unlocks.Count(u => u.root.activeSelf) == 2, "Level-up and both flavor cards are visible");
            await Shot("Tutorial04LevelUp");
            Check(!tutorial.buttonHighlight.gameObject.activeSelf && !tutorial.instructionPanel.gameObject.activeSelf, "Results have no Next day highlight or Continue prompt");
            game.hud.daySummary.continueButton.onClick.Invoke();
            Check(game.day == 2 && tutorial.progress.step == TycoonTutorial.Step.Supplier, "Continue starts day-two shopping");
            Check(game.cash >= 36, "Day-two budget covers vanilla, chocolate and improved scooper");
            var reward = game.parts.First(p => p.rewardDelivery);
            Check(game.parts.Count(p => p.rewardDelivery) == 2 && game.looseItems.Count(l => l.levelReward) == 2, "First level-up includes both new holders and full tubs at base");
            Aim(reward.transform.position + Vector3.up * .8f, reward.transform.position + Vector3.forward * 1.6f);
            player.Use(true);
            Check(reward.packed && tutorial.progress.rewardDeliverySeen, "Collecting the first reward dismisses its delivery highlight");
            player.Teleport(tutorial.playerSpawn.position); await Task.Delay(500);
            Check(tutorial.destinationPanel.gameObject.activeSelf && tutorial.destinationCaption.text == "Buy Supplies" && !tutorial.instructionPanel.gameObject.activeSelf, "Buy Supplies is centered without a key or icon gap");
            Check(tutorial.supplyRoute.activeSelf && tutorial.supplyRouteArrows.Length >= 2, "Fixed street arrows lead from the shop to the supplier");
            Check(Vector3.Distance(tutorial.supplyRouteArrows.Last().position, tutorial.supplyDestination.position) < 3, "Street arrows end at the supplier terminal");
            Check(tutorial.worldCue.gameObject.activeSelf, "Supplier keeps its yellow destination arrow");
            player.view.transform.rotation = Quaternion.LookRotation(tutorial.supplyRouteArrows[0].position - player.view.transform.position);
            await Shot("Tutorial06SupplyRoute");
            player.Teleport(game.supplier.position + Vector3.back * 2); game.hud.OpenShop(); tutorial.Tick();
            await Shot("Tutorial05Shopping");
            foreach (int product in new[] { 0, 1, 20 })
            {
                Check(game.PurchaseSupply(product), "Purchase product " + product); tutorial.Tick();
            }
            Check(tutorial.progress.step == TycoonTutorial.Step.CollectSupplies && game.looseItems.Count(l => l.supplySlot >= 0) == 3, "All three purchases wait on the indoor counter");
            game.Save(); TycoonSave.Load(game); await WaitForLoad();
            Check(tutorial.progress.boughtVanilla && tutorial.progress.boughtChocolate && tutorial.progress.boughtScooper, "Purchases and tutorial phase survive resume");
            Check(game.looseItems.Where(l => l.supplySlot >= 0).All(l => l.body.isKinematic), "Uncollected purchases stay on the counter after resume");
            game.hud.ClosePanels();
            var aisle = game.supplier.position + new Vector3(0,.2f,.8f);
            foreach (var delivery in game.looseItems.Where(l => l.supplySlot >= 0).OrderBy(l => Vector3.Distance(l.transform.position, aisle)).ToArray())
            {
                Aim(delivery.transform.position + Vector3.up * .1f, aisle);
                Check(player.looseTarget == delivery, "Purchased item is reachable from the indoor aisle");
                player.Use(true); tutorial.Tick();
            }
            Check(tutorial.progress.step == TycoonTutorial.Step.ReturnHome && !game.looseItems.Any(l => l.supplySlot >= 0), "Collecting purchases starts the trip home");
            game.hud.ClosePanels(); player.Teleport(tutorial.Equipment[3].transform.position + Vector3.right * 1.3f); tutorial.Tick();
            for (int flavor = 0; flavor < 2; flavor++)
            {
                player.Select(player.inventory.Locate(TycoonItem.Kind.Tub, flavor)); var tub = tutorial.Equipment[3 + flavor];
                Aim(tub.handTarget.position, tub.transform.position + Vector3.right * 1.3f); player.Use(false); tutorial.Tick();
                Check(tub.contents.amount == 24, "Refill flavor " + flavor);
            }
            player.Select(player.inventory.Locate(TycoonItem.Kind.ImprovedScooper)); tutorial.Tick();
            Check(!tutorial.Active && tutorial.progress.step == TycoonTutorial.Step.Complete, "Selecting the better scooper completes onboarding");
            game.Save(); TycoonSave.Load(game); await WaitForLoad();
            Check(!tutorial.Active, "Completed tutorial stays completed on resume");
            Result = "PASS\n" + string.Join("\n", evidence);
        }
        catch (Exception exception) { Result = "FAIL\n" + exception + "\n" + string.Join("\n", evidence); }
    }
    private static void Aim(Vector3 point, Vector3 from)
    {
        player.CancelGesture(); player.Teleport(from); player.view.transform.rotation = Quaternion.LookRotation(point - player.view.transform.position);
        Physics.SyncTransforms(); player.Aim(); game.builder.AimPlacement(false);
    }
    private static void Check(bool passed, string message)
    {
        if (!passed) throw new Exception(message);
        evidence.Add(message);
    }
    private static async Task WaitForLoad()
    {
        for (int i = 0; i < 100 && game.loadingCampaign; i++) await Task.Delay(100);
        Check(!game.loadingCampaign, "Campaign finishes loading"); player.manualInput = true;
    }
    private static async Task Shot(string name)
    {
        Directory.CreateDirectory("Library/CodexPlaytests"); await Task.Delay(150);
        ScreenCapture.CaptureScreenshot("Library/CodexPlaytests/" + name + ".png"); await Task.Delay(150);
    }
}
