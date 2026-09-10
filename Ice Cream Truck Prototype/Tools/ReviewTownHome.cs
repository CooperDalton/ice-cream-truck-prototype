var g=TycoonGameManager.Instance;g.restartRequested=true;g.player.manualInput=true;g.phase=TycoonGameManager.Phase.Preparation;g.hud.ClosePanels();
g.player.Teleport(new UnityEngine.Vector3(-1,0,-2.3f));g.player.transform.rotation=UnityEngine.Quaternion.identity;g.player.pitch=12;g.player.view.transform.localRotation=UnityEngine.Quaternion.Euler(12,0,0);
UnityEngine.ScreenCapture.CaptureScreenshot("Library/CodexPlaytests/TownHome.png");
return "Captured the starting stand with the new town and HUD.";
