using System;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using Object = UnityEngine.Object;

public static class AuthorHandGrips
{
    static void Grip(PickupItem item,Vector3 point,Vector3 rotation,bool open=false)
    {
        var grip=new GameObject("Hand grip").transform;grip.SetParent(item.transform,false);
        grip.localPosition=point;grip.localRotation=Quaternion.Euler(rotation);
        item.grip=grip;item.openHandGrip=open;
        item.heldOffset=-(Quaternion.Euler(item.heldRotation)*point);
    }
    public static string Build()
    {
        if(EditorApplication.isPlaying)throw new Exception("Stop Play Mode first");
        foreach(var path in new[]{"Assets/Scenes/IceCreamPrototype.unity","Assets/Scenes/ParkRoute.unity"})
        {
            var scene=EditorSceneManager.OpenScene(path);var r=PrototypeSceneReferences.Instance;var p=r.interaction;var pose=r.player.GetComponent<FloatingHands>();
            pose.handsRenderer=p.rightHand.GetComponentInChildren<SkinnedMeshRenderer>();
            pose.rightHandBone=pose.handsRenderer.bones.Single(b=>b.name=="Hand_R");
            pose.handsRenderer.updateWhenOffscreen=true;
            var socket=new GameObject("Hand grip").transform;socket.SetParent(pose.rightHandBone,false);
            socket.localPosition=new Vector3(0,.0015f,-.0009f);
            pose.handGrip=socket;p.handAnchor.localPosition=new Vector3(.28f,-.25f,.60f);
            r.scooper.heldRotation=new Vector3(-15,35,-20);
            Grip(r.scooper,new Vector3(.075f,0,0),new Vector3(0,180,0));
            Grip(r.batter,new Vector3(0,.12f,0),new Vector3(0,180,90));
            Grip(r.shaker,new Vector3(0,.085f,0),new Vector3(0,180,90));
            r.boombox.heldRotation=Vector3.zero;
            Grip(r.boombox,new Vector3(0,.65f,0),new Vector3(0,180,0));
            r.boombox.heldOffset+=new Vector3(0,.15f,.12f);
            if(r.route!=null)
            {
                r.route.tray.heldRotation=Vector3.zero;
                Grip(r.route.tray,new Vector3(.2f,-.045f,0),new Vector3(-90,180,0),true);
            }
            EditorSceneManager.MarkSceneDirty(scene);EditorSceneManager.SaveScene(scene);
        }
        var prefab=PrefabUtility.LoadPrefabContents("Assets/Prefabs/IceCreamCone.prefab");
        Grip(prefab.GetComponent<IceCreamCone>(),new Vector3(0,.11f,0),new Vector3(0,180,90));
        PrefabUtility.SaveAsPrefabAsset(prefab,"Assets/Prefabs/IceCreamCone.prefab");PrefabUtility.UnloadPrefabContents(prefab);
        AssetDatabase.SaveAssets();EditorSceneManager.OpenScene("Assets/Scenes/MainMenu.unity");
        return "Authored a closing right-hand pose and grips for scooper, batter, shaker, cone, boombox, and tray in both modes.";
    }
    public static string WirePoseOwner()
    {
        foreach(var path in new[]{"Assets/Scenes/IceCreamPrototype.unity","Assets/Scenes/ParkRoute.unity"})
        {
            var scene=EditorSceneManager.OpenScene(path);var r=PrototypeSceneReferences.Instance;
            var pose=r.player.GetComponent<FloatingHands>();
            pose.handsRenderer=r.interaction.rightHand.GetComponentInChildren<SkinnedMeshRenderer>();
            pose.handGrip=pose.rightHandBone.GetComponentsInChildren<Transform>().Single(t=>t.name=="Hand grip");
            EditorSceneManager.MarkSceneDirty(scene);EditorSceneManager.SaveScene(scene);
        }
        EditorSceneManager.OpenScene("Assets/Scenes/MainMenu.unity");
        return "Saved grip references on FloatingHands.";
    }

}
