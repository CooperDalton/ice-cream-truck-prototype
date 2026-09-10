var scene=UnityEngine.SceneManagement.SceneManager.GetActiveScene();
var g=scene.GetRootGameObjects().SelectMany(o=>o.GetComponents<TycoonGameManager>()).Single();
var settings=UnityEngine.AI.NavMesh.CreateSettings();
var project=new UnityEditor.SerializedObject(UnityEditor.Unsupported.GetSerializedAssetInterfaceSingleton("NavMeshProjectSettings"));
var list=project.FindProperty("m_Settings");var entry=list.GetArrayElementAtIndex(list.arraySize-1);
entry.FindPropertyRelative("agentRadius").floatValue=.25f;entry.FindPropertyRelative("agentHeight").floatValue=1.8f;entry.FindPropertyRelative("agentClimb").floatValue=.3f;
project.FindProperty("m_SettingNames").GetArrayElementAtIndex(list.arraySize-1).stringValue="Floating crew";project.ApplyModifiedPropertiesWithoutUndo();
g.navigation.agentTypeID=settings.agentTypeID;g.navigation.overrideVoxelSize=true;g.navigation.voxelSize=.06f;g.navigation.minRegionArea=.2f;
foreach(var actor in new[]{g.catalog.workerPrefab,g.catalog.customerPrefab})
{
    var path=UnityEditor.AssetDatabase.GetAssetPath(actor);var root=UnityEditor.PrefabUtility.LoadPrefabContents(path);
    root.GetComponent<TycoonActor>().agent.agentTypeID=settings.agentTypeID;
    UnityEditor.PrefabUtility.SaveAsPrefabAsset(root,path);UnityEditor.PrefabUtility.UnloadPrefabContents(root);
}
g.navigation.BuildNavMesh();UnityEditor.AssetDatabase.SaveAssets();UnityEditor.SceneManagement.EditorSceneManager.SaveScene(scene);
return "Floating crew navigation uses radius 0.25 m, height 1.8 m and 0.06 m voxels. Agent type "+settings.agentTypeID;
