using System;
using System.Linq;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.UI;

public static class AuthorTruckInteractions
{
    public static string Finish()
    {
        var r = PrototypeSceneReferences.Instance;
        r.player.controller.stepOffset = .45f;
        var indicator = r.waffle.GetComponentInChildren<WaffleIndicator>(true);
        var key = new GameObject("E key", typeof(RectTransform), typeof(Image));
        key.transform.SetParent(indicator.clickIcon.transform.parent, false);
        var rect = key.GetComponent<RectTransform>();
        rect.sizeDelta = new Vector2(25, 27);
        var background = key.GetComponent<Image>();
        background.sprite = AssetDatabase.LoadAssetAtPath<Sprite>("Assets/Art/UI/Soft panel.png");
        background.type = Image.Type.Sliced;
        background.color = new Color(1, .98f, .91f); background.raycastTarget = false;
        var letter = new GameObject("Letter", typeof(RectTransform), typeof(Text));
        letter.transform.SetParent(key.transform, false);
        var text = letter.GetComponent<Text>();
        text.rectTransform.sizeDelta = new Vector2(25, 27);
        text.font = Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");
        text.fontSize = 20; text.fontStyle = FontStyle.Bold;
        text.alignment = TextAnchor.MiddleCenter; text.color = new Color(.15f, .3f, .3f);
        text.text = "E"; text.raycastTarget = false;
        indicator.useKey = key;
        EditorSceneManager.MarkSceneDirty(r.gameObject.scene);
        EditorSceneManager.SaveScene(r.gameObject.scene);
        return "Saved step height and E key indicator.";
    }
    public static string Main()
    {
        var r = PrototypeSceneReferences.Instance;
        var truck = r.truck;
        if (truck.rearDoor != null) throw new InvalidOperationException("Truck interactions already authored.");
        var parts = truck.GetComponentsInChildren<Transform>(true);
        var modelHinge = parts.Single(t => t.name == "RearEntryDoor_HINGE");
        var mesh = parts.Single(t => t.name == "RearEntryDoor_HINGE_Mesh");
        var pivot = new GameObject("Rear door pivot").transform;
        pivot.SetParent(truck.transform, false);
        pivot.position = modelHinge.position;
        modelHinge.SetParent(pivot, true);
        var door = mesh.gameObject.AddComponent<TruckDoor>();
        door.truck = truck; door.hinge = pivot;
        door.highlightRenderers = modelHinge.GetComponentsInChildren<Renderer>();
        truck.rearDoor = door;
        truck.seat = truck.GetComponentsInChildren<TruckSeat>(true).Single();
        truck.seat.transform.position = truck.driver.position + Vector3.up * .65f;
        truck.seat.gameObject.layer = 9;
        var seatCollider = truck.seat.GetComponent<BoxCollider>();
        seatCollider.size = new Vector3(.85f, .8f, .85f);
        seatCollider.isTrigger = true;
        var stand = new GameObject("Stand beside driver").transform;
        stand.SetParent(truck.transform, false);
        stand.localPosition = new Vector3(.55f, .64f, .35f);
        stand.localRotation = Quaternion.Euler(0, 270, 0);
        truck.standPoint = stand;
        var outside = parts.Single(t => t.name == "Outside entry");
        UnityEngine.Object.DestroyImmediate(outside.gameObject);
        var instructions = r.hud.pausePanel.GetComponentsInChildren<Text>(true).Single(t => t.name == "Instructions");
        instructions.text = "Open the iron. Pour batter. Close and cook.\nPlace your cone, scoop flavors, add sprinkles, then serve.\n\nWASD to move  •  Mouse to look  •  Space to jump / brake\nE to use, open doors, or sit in the driver's seat\nE while parked to stand up  •  Walk through the rear door\nHold mouse + move up/down to scoop or shake\nRight click to put down  •  Q for music";
        EditorSceneManager.MarkSceneDirty(r.gameObject.scene);
        EditorSceneManager.SaveScene(r.gameObject.scene);
        return "Saved rear door hinge, seat interaction collider, standing point, and controls.";
    }
}
