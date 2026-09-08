using System;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.UI;

public static class PrototypeUIPlaytest
{
    private static void Click(PrototypeHUD hud,Button button)
    {
        Canvas.ForceUpdateCanvases();
        var pointer=new PointerEventData(EventSystem.current){position=RectTransformUtility.WorldToScreenPoint(null,button.transform.position),button=PointerEventData.InputButton.Left};
        var hits=new List<RaycastResult>();hud.GetComponent<GraphicRaycaster>().Raycast(pointer,hits);
        if(hits.Count==0 || hits[0].gameObject!=button.gameObject)throw new Exception("Button not reachable through HUD raycaster");
        ExecuteEvents.Execute(button.gameObject,pointer,ExecuteEvents.pointerClickHandler);
    }
    public static object RestartFromResults()
    {
        var r=PrototypeSceneReferences.Instance;
        if(!r.hud.resultPanel.activeSelf)throw new Exception("Day-end results did not open");
        string result=r.hud.resultText.text;
        Click(r.hud,r.hud.retryButton);
        return new{result,button="Play again received a pointer click through the HUD raycaster"};
    }
    public static object OpenPause()
    {
        var r=PrototypeSceneReferences.Instance;
        if(r.day.Earnings!=0 || r.day.Phase!=DayManager.DayPhase.Open || r.interaction.Held!=null)throw new Exception("Restart did not reset play state");
        r.day.TogglePause();
        if(!r.hud.pausePanel.activeSelf)throw new Exception("Pause panel failed to open");
        return new {resetEarnings=r.day.Earnings,clock=r.day.ClockLabel,pauseOpened=r.hud.pausePanel.activeSelf};
    }
    public static object Resume()
    {
        var r=PrototypeSceneReferences.Instance;
        Click(r.hud,r.hud.resumeButton);
        if(r.day.Paused || r.hud.pausePanel.activeSelf)throw new Exception("Resume failed");
        return new{resetEarnings=r.day.Earnings,clock=r.day.ClockLabel,resume="Pointer click resumed play"};
    }
    public static string ScheduleResume()
    {
        PrototypeSceneReferences.Instance.hud.StartCoroutine(ResumeDuringPlayerLoop());
        return "Resume check scheduled in player loop";
    }
    private static System.Collections.IEnumerator ResumeDuringPlayerLoop()
    {
        yield return null;
        object result;
        try { result=Resume(); System.IO.File.WriteAllText("Library/CodexPlaytests/resume-player-loop.txt", "PASS " + result); }
        catch(Exception e) { System.IO.File.WriteAllText("Library/CodexPlaytests/resume-player-loop.txt", "FAIL " + e.Message + " screen " + Screen.width+"x"+Screen.height); }
    }

}
