using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using UnityEngine;

public static class TycoonDaySummaryPlaytest
{
    public static async Task<string[]> Run()
    {
        var g=TycoonGameManager.Instance;
        var summary=g.hud.daySummary;
        var checks=new List<string>();
        g.restartRequested=true;g.player.manualInput=true;
        foreach(var site in g.sites)site.open=false;
        foreach(var worker in g.workers)worker.onDuty=false;
        g.hud.ClosePanels();g.phase=TycoonGameManager.Phase.Trading;
        Check(!g.hud.xpBar.transform.parent.gameObject.activeSelf&&!summary.gameObject.activeSelf,"Daytime XP hidden");
        checks.Add("Daytime HUD has no XP bar or XP summary.");
        Setup(g,1,40,30);g.CloseDay();summary.Begin();
        Check(summary.DisplayedLevel==1&&summary.earnedXP.text=="+0 XP"&&!summary.unlockGroup.gameObject.activeSelf&&!summary.continueButton.interactable,"Starts at previous progress without unlocks");
        g.hud.ToggleMenu();g.hud.ToggleInventory();g.hud.ToggleMap();
        Check(summary.gameObject.activeSelf&&!g.hud.menuPanel.activeSelf&&!g.hud.personalInventoryPanel.activeSelf,"Menu keys cannot interrupt results");
        int day=g.day;summary.continueButton.onClick.Invoke();Check(g.day==day,"Continue cannot skip unfinished animation");
        await Task.Delay(850);
        Check(Time.timeScale==0&&summary.xpFill.fillAmount>40f/60&&summary.earnedXP.text!="+0 XP"&&!summary.unlockGroup.gameObject.activeSelf,"XP animates while game paused; unlocks hidden");
        ScreenCapture.CaptureScreenshot("Library/CodexPlaytests/DaySummaryAnimating.png");
        await Finished(summary);
        Check(summary.DisplayedLevel==2&&summary.earnedXP.text=="+30 XP"&&Mathf.Abs(summary.xpFill.fillAmount-10f/90)<.001f,"Final XP and rollover");
        Check(summary.unlockGroup.gameObject.activeSelf&&summary.unlocks.Count(x=>x.root.activeSelf)==2&&summary.unlocks[0].label.text=="Strawberry"&&summary.unlocks[1].label.text=="Mint","Exact level-two unlocks");
        checks.Add("40 + 30 XP fills level 1, rolls into level 2, then reveals Strawberry and Mint; animation runs with timeScale zero.");
        summary.continueButton.onClick.Invoke();Check(g.day==day+1&&g.phase==TycoonGameManager.Phase.Preparation&&!g.hud.AnyPanel,"Continue advances once");
        Check(!g.hud.xpBar.transform.parent.gameObject.activeSelf,"XP remains hidden next day");
        checks.Add("Next day is unavailable until the reveal finishes; clicking it returns to preparation with XP hidden.");
        Setup(g,2,70,20);g.CloseDay();summary.Begin();await Finished(summary);
        Check(summary.DisplayedLevel==2&&!summary.unlockGroup.gameObject.activeSelf&&summary.window.sizeDelta.y==390&&summary.earnedXP.text=="+20 XP","No level up stays compact");
        ScreenCapture.CaptureScreenshot("Library/CodexPlaytests/DaySummaryNoLevel.png");await Task.Delay(100);
        checks.Add("A day with no level-up stays compact and shows no unlock section.");
        Setup(g,2,70,0);g.CloseDay();summary.Begin();await Finished(summary);
        Check(summary.earnedXP.text=="+0 XP"&&!summary.unlockGroup.gameObject.activeSelf,"Zero sales");
        checks.Add("Zero-XP days finish without false level-ups or unlocks.");
        Setup(g,1,0,1100);g.CloseDay();summary.Begin();await Finished(summary);
        Check(summary.DisplayedLevel==7&&summary.progress.text=="Max level"&&summary.unlocks.Count(x=>x.root.activeSelf)==16,"All levels unlock");
        Check(summary.unlockContent.rect.height>summary.unlockScroll.viewport.rect.height,"Many unlocks scroll");
        checks.Add("A six-level jump animates every threshold and reveals all 16 ingredients in a scrollable grid.");
        Setup(g,7,1100,100);g.CloseDay();summary.Begin();await Finished(summary);
        Check(summary.progress.text=="Max level"&&summary.earnedXP.text=="+100 XP"&&!summary.unlockGroup.gameObject.activeSelf,"Already max level");
        checks.Add("At max level, daily XP still counts up without repeating unlocks.");
        Setup(g,1,42,152.4f);g.CloseDay();summary.Begin();await Finished(summary);
        ScreenCapture.CaptureScreenshot("Library/CodexPlaytests/DaySummaryUnlocked.png");
        g.Save();
        return checks.ToArray();
    }
    private static void Setup(TycoonGameManager g,int level,float start,float earned)
    {
        g.hud.ClosePanels();g.phase=TycoonGameManager.Phase.Trading;g.level=level;g.xp=start+earned;g.salesToday=earned;g.clock=480;
    }
    private static async Task Finished(TycoonDaySummary summary)
    {
        float deadline=Time.realtimeSinceStartup+20;
        while(!summary.Finished&&Time.realtimeSinceStartup<deadline)await Task.Delay(100);
        Check(summary.Finished&&summary.continueButton.interactable,"Animation completed");
    }
    private static void Check(bool value,string message)
    {
        if(!value)throw new Exception(message);
    }
}
