// Layout captured from the user's campaign on 2026-09-13.
if (EditorApplication.isPlaying) throw new Exception("Stop Play Mode before authoring tutorial targets.");
var scene=UnityEngine.SceneManagement.SceneManager.GetActiveScene();
var game=scene.GetRootGameObjects().SelectMany(g=>g.GetComponents<TycoonGameManager>()).Single();
var positions=new[]{new Vector3(-13,0,-25),new Vector3(-9.25f,0,-22.5f),new Vector3(-13.5f,0,-22.5f),new Vector3(-11.75f,0,-24.75f),new Vector3(-11.25f,0,-24.75f),new Vector3(-15.5f,0,-24.75f)};
for(int i=0;i<positions.Length;i++)game.tutorial.placementSpots[i].SetPositionAndRotation(positions[i],Quaternion.identity);
game.tutorial.bowlSpot.SetPositionAndRotation(positions[0]+new Vector3(.375f,.94f,.125f),Quaternion.identity);
UnityEditor.SceneManagement.EditorSceneManager.MarkSceneDirty(scene);
UnityEditor.SceneManagement.EditorSceneManager.SaveScene(scene);
return "All six tutorial targets match saved positions and rotations.";
