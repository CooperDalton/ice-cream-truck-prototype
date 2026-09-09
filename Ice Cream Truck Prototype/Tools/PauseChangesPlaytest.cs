using System;
using System.Collections.Generic;
using System.Linq;
using UnityEngine;
public static class PauseChangesPlaytest
{
    public static string Run()
    {
        var r = PrototypeSceneReferences.Instance;
        var checks = new List<string>();
        r.player.ManualInput = true;
        r.interaction.ManualInput = true;
        float hour = r.day.Hour;
        r.day.Advance(2);
        Check(Mathf.Abs((r.day.Hour - hour) * 60 - 1) < .002f, "2 seconds advances clock by 1 minute", checks);
        r.interaction.PickUp(r.batter, true);
        var position = r.waffle.transform.position;
        r.player.controller.enabled = false;
        r.player.transform.position = new Vector3(Mathf.Clamp(position.x, -2.8f, .8f), .64f, .10f);
        r.player.controller.enabled = true;
        r.player.view.transform.LookAt(r.waffle.GetComponent<Collider>().bounds.center);
        Physics.SyncTransforms();
        r.interaction.ProcessInput(false, false, false, false, Vector2.zero, .02f);
        Check(r.interaction.Target == r.waffle, "Scene ray reaches waffle iron", checks);
        Click(r.interaction);
        Check(r.waffle.IsOpen, "Click opens iron while holding batter", checks);
        Click(r.interaction);
        Check(!r.waffle.IsOpen && r.interaction.Held == r.batter, "Lid closes before pouring without dropping batter", checks);
        Click(r.interaction);
        r.interaction.ProcessInput(true, true, false, false, Vector2.zero, .02f);
        for (int i = 0; i < 100; i++) r.interaction.ProcessInput(false, true, false, false, Vector2.zero, .02f);
        r.interaction.ProcessInput(false, false, true, false, Vector2.zero, .02f);
        Check(r.waffle.State == WaffleMaker.CookState.BatterReady, "Holding pour fills iron", checks);
        Click(r.interaction);
        Check(!r.waffle.IsOpen && r.waffle.State == WaffleMaker.CookState.Cooking && r.interaction.Held == r.batter, "Click closes filled iron and starts cooking while holding batter", checks);
        r.waffle.Advance(r.waffle.settings.cookSeconds);
        Click(r.interaction);
        Check(r.waffle.IsOpen && r.waffle.State == WaffleMaker.CookState.Ready, "Ready iron opens with batter held", checks);
        r.batter.Drop(r.interaction);
        Click(r.interaction);
        Check(r.interaction.Held is IceCreamCone, "Cone can still be collected after putting batter down", checks);
        r.day.TogglePause();
        var ui = r.hud.pausePanel.GetComponentInChildren<PauseSettings>(true);
        float sensitivity = ui.sensitivity.value;
        float music = ui.musicVolume.value;
        float effects = ui.effectsVolume.value;
        ui.sensitivity.value = .2f;
        ui.musicVolume.value = .25f;
        ui.effectsVolume.value = 0;
        Check(Mathf.Approximately(r.player.MouseSensitivity, .2f) && ui.sensitivityValue.text == "2.0x", "Sensitivity slider changes camera setting and label", checks);
        Check(PlayerPrefs.GetFloat("MusicVolume") == .25f && PlayerPrefs.GetFloat("EffectsVolume") == 0, "Volume sliders independently store 25% music and muted effects", checks);
        r.day.TogglePause();
        float yaw = r.player.transform.eulerAngles.y;
        r.player.Move(Vector2.zero, new Vector2(10, 0), 0);
        Check(Mathf.Abs(Mathf.DeltaAngle(yaw, r.player.transform.eulerAngles.y) - 2) < .001f, "10 pixels turns camera 2 degrees at 2x sensitivity", checks);
        r.day.TogglePause();
        Check(Mathf.Approximately(ui.sensitivity.value, .2f), "Sensitivity survives closing and reopening menu", checks);
        ui.sensitivity.value = sensitivity;
        ui.musicVolume.value = music;
        ui.effectsVolume.value = effects;
        PlayerPrefs.Save();
        return string.Join("\n", checks);
    }
    private static void Check(bool passed, string text, List<string> checks)
    {
        if (!passed) throw new Exception(text);
        checks.Add("PASS: " + text);
    }
    private static void Click(PlayerInteraction interaction)
    {
        interaction.ProcessInput(true, true, false, false, Vector2.zero, .02f);
        interaction.ProcessInput(false, false, true, false, Vector2.zero, .02f);
    }
}
