var game=TycoonGameManager.Instance;var player=game.player;
var shelf=game.Parts(0,TycoonPart.Kind.Shelf).Single();
var camera=player.view.transform;var position=camera.position;var rotation=camera.rotation;
int checks=0;
try
{
    foreach(float x in new[]{-.45f,0,.45f})
    foreach(float height in new[]{1.35f,1.72f})
    {
        var point=shelf.transform.TransformPoint(new Vector3(x,height,0));
        camera.position=shelf.transform.TransformPoint(new Vector3(x,1.66f,2));camera.LookAt(point);
        Physics.SyncTransforms();player.Aim();
        if(player.target!=shelf)throw new Exception("Player missed shelf near top at "+point);
        checks++;
    }
    player.Use(true);
    if(!game.hud.AnyPanel)throw new Exception("E did not open shelf storage from the top");
    game.hud.ClosePanels();
    System.IO.File.WriteAllText("Library/CodexPlaytests/HitboxTutorialPlaytest.txt",TycoonTutorialPlaytest.Result);
    return "PASS: player aims at six upper-shelf points, including both top corners; E opens shelf storage.";
}
finally{camera.SetPositionAndRotation(position,rotation);player.Aim();}
