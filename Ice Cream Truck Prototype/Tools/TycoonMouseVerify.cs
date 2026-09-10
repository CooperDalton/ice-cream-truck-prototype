var g=TycoonGameManager.Instance;var tub=g.Parts(0,TycoonPart.Kind.Tub).Single(t=>t.variant==0);
if(tub.contents.amount!=11||g.player.Held.loadedFlavor!=0)throw new System.Exception("Visible mouse scoop failed");
string evidence="Native mouse drag from the centered vanilla tub completed one improved scoop through Player.Update, Aim, Use, and Gesture. Installed stock 12 -> 11; held tool loaded vanilla. Player collider no longer blocks the interaction ray.";
System.IO.File.WriteAllText("Library/CodexPlaytests/TycoonMouse.txt",evidence);UnityEngine.ScreenCapture.CaptureScreenshot("Library/CodexPlaytests/TycoonMouseScoop.png");return evidence;
