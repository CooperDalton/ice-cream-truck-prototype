var g=TycoonGameManager.Instance;
if(!g.truck.routeComplete)return "Driver still traveling: "+g.truck.transform.position;
g.clock=480;g.CloseDay();
if(!g.completed||g.phase!=TycoonGameManager.Phase.Results)throw new System.Exception("Expansion milestone failed");
UnityEngine.ScreenCapture.CaptureScreenshot("Library/CodexPlaytests/TycoonResultsFinal.png");System.IO.File.AppendAllText("Library/CodexPlaytests/TycoonFinalCampaign.txt","Driver finished restored route. Closing awarded the three-site expansion milestone. No fixed income was added while no orders were served.\n");return g.results;
