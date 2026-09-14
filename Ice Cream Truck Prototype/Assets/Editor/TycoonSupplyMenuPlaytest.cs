using System;
using System.Linq;
using UnityEngine;

public static class TycoonSupplyMenuPlaytest
{
    public static string Result { get; private set; } = "Not started";
    public static async void Start()
    {
        Result = "Running";
        try
        {
            // Play Mode check. Back up the campaign first: this buys three products.
            var game=TycoonGameManager.Instance;var hud=game.hud;var tutorial=game.tutorial;
            await System.Threading.Tasks.Task.Delay(150);
            while(game.loadingCampaign) await System.Threading.Tasks.Task.Delay(100);
            game.player.manualInput=true;game.restartRequested=true;game.player.Teleport(game.supplier.position+Vector3.forward);
            hud.OpenShop();
            var checks=new System.Collections.Generic.List<string>();
            void Check(bool passed,string message){if(!passed)throw new Exception(message);checks.Add(message);}
            async System.Threading.Tasks.Task Click(UnityEngine.UI.Button button)
            {
                await System.Threading.Tasks.Task.Delay(120); Canvas.ForceUpdateCanvases();
                var point=RectTransformUtility.WorldToScreenPoint(null,button.transform.TransformPoint(((RectTransform)button.transform).rect.center));
                var pointer=new UnityEngine.EventSystems.PointerEventData(UnityEngine.EventSystems.EventSystem.current){position=point,button=UnityEngine.EventSystems.PointerEventData.InputButton.Left};
                var hits=new System.Collections.Generic.List<UnityEngine.EventSystems.RaycastResult>();
                UnityEngine.EventSystems.EventSystem.current.RaycastAll(pointer,hits);
                Check(hits.Count>0 && hits[0].gameObject.GetComponentInParent<UnityEngine.UI.Button>()==button,"UI ray reaches "+button.name);
                UnityEngine.EventSystems.ExecuteEvents.Execute(button.gameObject,pointer,UnityEngine.EventSystems.ExecuteEvents.pointerClickHandler);
            }
            for(int category=0;category<4;category++)
            {
                await Click(hud.supplyCategoryButtons[category]);
                Check(hud.SupplyCategory==category && hud.supplyCategoryPanels.Count(p=>p.activeSelf)==1,"Category "+category+" shows only its own products");
                int expected=category==0?12:category==1?6:2;
                var cards=hud.supplyButtons.Where(b=>b.gameObject.activeInHierarchy).ToArray();
                Check(cards.Length==expected,"Category product count "+expected);
                foreach(var card in cards)
                {
                    var icon=card.GetComponentsInChildren<UnityEngine.UI.Image>().Single(i=>i.name=="Icon");
                    Check(icon.sprite!=null && icon.preserveAspect,"Product has its own icon: "+card.name);
                }
            }
            await Click(hud.supplyCategoryButtons[0]);
            float before=game.cash;
            await Click(hud.supplyButtons[4]);
            Check(game.cash==before && !hud.supplyButtons[4].interactable && hud.supplyLocks[4].activeSelf,"Locked flavor shows its level and cannot be purchased");
            tutorial.progress.boughtVanilla=false;tutorial.progress.boughtChocolate=false;tutorial.progress.boughtScooper=false;tutorial.progress.step=TycoonTutorial.Step.BuyVanilla;
            int delivered=game.looseItems.Count(l=>l.supplySlot>=0);
            await Click(hud.supplyButtons[0]);tutorial.Tick();
            await Click(hud.supplyButtons[1]);tutorial.Tick();tutorial.SendMessage("LateUpdate");
            Check(tutorial.progress.step==TycoonTutorial.Step.BuyScooper && tutorial.caption.text=="Tools","Tutorial points to Tools when the next product is in another category");
            await Click(hud.supplyCategoryButtons[3]);tutorial.SendMessage("LateUpdate");
            Check(tutorial.caption.text=="Buy" && hud.supplyButtons[20].gameObject.activeInHierarchy,"Opening Tools reveals the highlighted better scooper");
            await Click(hud.supplyButtons[20]);tutorial.Tick();
            Check(Mathf.Abs(game.cash-(before-36))<.001f && game.looseItems.Count(l=>l.supplySlot>=0)==delivered+3,"Correct products and prices deliver three physical purchases");
            Check(tutorial.progress.step==TycoonTutorial.Step.CollectSupplies,"Buying the scooper advances to collection");
            ScreenCapture.CaptureScreenshot("Library/CodexPlaytests/SupplyToolsCards.png");
            System.IO.File.WriteAllText("Library/CodexPlaytests/SupplyCardsChecks.txt","PASS\n"+string.Join("\n",checks));
            Result = "PASS: category clicks, 22 icons, locked products, tutorial tab guidance and three purchases.";

        }
        catch(Exception exception) { Result = "FAIL: " + exception; }
    }
}
