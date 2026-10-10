using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using Quantum;
using Quantum.Editor;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.UI;
using Object = UnityEngine.Object;

// Scene assembly for the Divorced Dads builder: the Quantum runner and its own map, the PS1 low-res camera, the
// first-person rig, day/night and ambience, effects, audio and the HUD; plus the effect prefabs and shared helpers.
public static partial class DivorcedDadsSceneBuilder
{
    // The scene starts as a copy of the zombie scene for its Quantum runner, view updater and stats objects; everything
    // else in it is rebuilt here.
    static Scene OpenScene()
    {
        if (!File.Exists(ScenePath)) AssetDatabase.CopyAsset(ZombieScenePath, ScenePath);
        var scene = EditorSceneManager.OpenScene(ScenePath);
        var keep = new[] { "Main Camera", "Directional Light", "QuantumEntityViewUpdater", "QuantumDebugRunner", "QuantumMap", "QuantumStats" };
        foreach (var root in scene.GetRootGameObjects())
        {
            if (!keep.Contains(root.name)) Object.DestroyImmediate(root);
        }
        return scene;
    }

    static void BuildScene(Scene scene, DadsSettings settings, Fx fx, TownBuild town)
    {
        QuantumEntityViewUpdater viewUpdater = null;
        QuantumRunnerLocalDebug runner = null;
        QuantumMapData mapData = null;
        Camera camera = null;
        Light sun = null;
        foreach (var root in scene.GetRootGameObjects())
        {
            if (root.TryGetComponent(out QuantumEntityViewUpdater foundUpdater)) viewUpdater = foundUpdater;
            if (root.TryGetComponent(out QuantumRunnerLocalDebug foundRunner)) runner = foundRunner;
            if (root.TryGetComponent(out QuantumMapData foundMap)) mapData = foundMap;
            if (root.TryGetComponent(out Camera foundCamera)) camera = foundCamera;
            if (root.TryGetComponent(out Light foundLight)) sun = foundLight;
        }

        var environment = new GameObject("Environment").transform;
        var ground = Primitive(PrimitiveType.Cube, environment, "Ground Collider", new Vector3(0, -0.5f, 0), new Vector3(1200, 1, 600), Material("Dads Grass", new Color(0.3f, 0.62f, 0.32f)), true);
        ground.GetComponent<Renderer>().enabled = false;
        ground.AddComponent<QuantumStaticBoxCollider3D>().SourceCollider = ground.GetComponent<BoxCollider>();
        Primitive(PrimitiveType.Cube, environment, "Ground", new Vector3(0, -0.12f, 0), new Vector3(1200, 0.1f, 600), Material("Dads Grass", new Color(0.3f, 0.62f, 0.32f)), false);
        town.Root.SetParent(environment, true);
        sun.color = new Color(1f, 0.9f, 0.82f);
        sun.intensity = 1.3f;
        sun.shadows = LightShadows.Soft;
        RenderSettings.ambientMode = UnityEngine.Rendering.AmbientMode.Flat;
        RenderSettings.fog = true;
        RenderSettings.fogMode = FogMode.Linear;
        RenderSettings.fogStartDistance = 45;
        RenderSettings.fogEndDistance = 170;

        var gameplay = new GameObject("Gameplay").transform;
        var input = new GameObject("Dads Input").AddComponent<DadsInput>();
        input.transform.SetParent(gameplay, false);
        // The game renders into a small point-filtered texture shown full screen through the dither shader.
        var lowRes = new RenderTexture(480, 270, 24) { filterMode = FilterMode.Point, name = "Dads PS1 Screen" };
        lowRes = ReplaceAsset(lowRes, "Assets/Art/Dads PS1 Screen.renderTexture");
        camera.targetTexture = lowRes;
        camera.nearClipPlane = 0.05f;
        camera.farClipPlane = 400;
        camera.fieldOfView = 75;
        camera.clearFlags = CameraClearFlags.SolidColor;
        foreach (var component in camera.GetComponents<MonoBehaviour>()) Object.DestroyImmediate(component);
        foreach (Transform child in camera.transform) Object.DestroyImmediate(child.gameObject);
        var cameraRig = camera.gameObject.AddComponent<DadsCamera>();
        Set(cameraRig, ("viewUpdater", viewUpdater), ("input", input), ("eye", camera));
        BuildViewModel(camera, input, cameraRig);
        var display = new GameObject("Display Camera").AddComponent<Camera>();
        display.cullingMask = 1 << UiLayer;
        display.nearClipPlane = 0.1f;
        camera.cullingMask = ~(1 << UiLayer);
        display.clearFlags = CameraClearFlags.SolidColor;
        display.backgroundColor = Color.black;
        display.depth = -10;
        var screen = Canvas("Screen", 0, display, 1f);
        var image = new GameObject("PS1 Image", typeof(RectTransform), typeof(RawImage)).GetComponent<RawImage>();
        image.transform.SetParent(screen.transform, false);
        Stretch(image.rectTransform);
        image.texture = lowRes;
        image.material = AssetDatabase.LoadAssetAtPath<Material>($"{MaterialFolder}/PS1 Dither.mat");
        image.raycastTarget = false;

        var hud = BuildHud(input, display);
        foreach (var child in screen.GetComponentsInChildren<Transform>(true).Concat(hud.GetComponentsInChildren<Transform>(true))) child.gameObject.layer = UiLayer;
        BuildEffectsObject(gameplay, fx, viewUpdater, cameraRig, hud);
        BuildAudio(gameplay, camera.transform, viewUpdater, input);
        BuildDayNight(gameplay, sun, camera, town);

        var map = AssetDatabase.LoadAssetAtPath<Map>($"{ConfigFolder}/DivorcedDadsMap.asset");
        if (map == null)
        {
            AssetDatabase.CreateAsset(ScriptableObject.CreateInstance<Map>(), $"{ConfigFolder}/DivorcedDadsMap.asset");
            AssetDatabase.ImportAsset($"{ConfigFolder}/DivorcedDadsMap.asset", ImportAssetOptions.ForceSynchronousImport);
            map = AssetDatabase.LoadAssetAtPath<Map>($"{ConfigFolder}/DivorcedDadsMap.asset");
            // The baker resolves the map through the asset DB, which only knows about the new asset after a refresh.
            QuantumUnityDBUtilities.RefreshGlobalDB(true);
        }
        // The town spans about 560 x 140 m; the physics broadphase has to cover all of it.
        map.WorldSize = 1024;
        map.BucketsCount = 64;
        mapData.AssetRef = map;
        runner.RuntimeConfig.Map = map;
        runner.RuntimeConfig.Settings = default;
        runner.RuntimeConfig.DadsSettings = settings;
        runner.MaxPlayerCount = 4;
        runner.LocalPlayers = new[] { new RuntimePlayer { PlayerNickname = "Dad 1" } };
        EditorUtility.SetDirty(runner);
        QuantumMapDataBaker.BakeMapData(mapData, true);
        EditorUtility.SetDirty(mapData);
        EditorUtility.SetDirty(map);
        EditorSceneManager.MarkSceneDirty(scene);
        EditorSceneManager.SaveScene(scene);
        // The Quantum sample menu (quick play, regions, party codes) lists every scene info in Resources, so this one adds
        // Divorced Dads next to the zombie mode for online games.
        var sceneInfo = ScriptableObject.CreateInstance<QuantumMenuSceneInfo>();
        sceneInfo.Name = "Divorced Dads";
        sceneInfo.ScenePath = ScenePath;
        sceneInfo.RuntimeConfig = runner.RuntimeConfig;
        ReplaceAsset(sceneInfo, $"{ConfigFolder}/DivorcedDadsSceneInfo.asset");
        var scenes = EditorBuildSettings.scenes.Where(s => s.path != ScenePath).ToList();
        scenes.Add(new EditorBuildSettingsScene(ScenePath, true));
        EditorBuildSettings.scenes = scenes.ToArray();
    }

    static void BuildDayNight(Transform gameplay, Light sun, Camera sky, TownBuild town)
    {
        var dayNight = new GameObject("Day Night").AddComponent<DayNight>();
        dayNight.transform.SetParent(gameplay, false);
        // Clock: 0 morning, ~0.35 noon, 0.7 dusk, 0.82 night, 1 midnight.
        var sunColor = Gradient((0, new Color(1f, 0.85f, 0.7f)), (0.3f, new Color(1f, 0.97f, 0.9f)), (0.62f, new Color(1f, 0.8f, 0.55f)), (0.74f, new Color(1f, 0.45f, 0.35f)), (0.85f, new Color(0.45f, 0.5f, 0.9f)), (1, new Color(0.35f, 0.4f, 0.8f)));
        var ambient = Gradient((0, new Color(0.55f, 0.5f, 0.65f)), (0.3f, new Color(0.62f, 0.6f, 0.72f)), (0.68f, new Color(0.6f, 0.45f, 0.55f)), (0.78f, new Color(0.35f, 0.28f, 0.5f)), (0.86f, new Color(0.18f, 0.16f, 0.36f)), (1, new Color(0.14f, 0.12f, 0.3f)));
        var skyColor = Gradient((0, new Color(0.78f, 0.82f, 1f)), (0.2f, new Color(0.55f, 0.8f, 1f)), (0.6f, new Color(0.6f, 0.75f, 1f)), (0.72f, new Color(1f, 0.55f, 0.45f)), (0.8f, new Color(0.45f, 0.25f, 0.55f)), (0.88f, new Color(0.1f, 0.06f, 0.22f)), (1, new Color(0.06f, 0.04f, 0.15f)));
        var intensity = new AnimationCurve(new Keyframe(0, 0.9f), new Keyframe(0.3f, 1.35f), new Keyframe(0.7f, 1f), new Keyframe(0.8f, 0.35f), new Keyframe(1, 0.25f));
        var serialized = new SerializedObject(dayNight);
        serialized.FindProperty("sunColor").gradientValue = sunColor;
        serialized.FindProperty("ambientColor").gradientValue = ambient;
        serialized.FindProperty("skyColor").gradientValue = skyColor;
        serialized.FindProperty("sunIntensity").animationCurveValue = intensity;
        serialized.ApplyModifiedPropertiesWithoutUndo();
        Set(dayNight, ("sun", sun), ("sky", sky), ("streetLamps", town.Lamps.Cast<Object>().ToArray()),
            ("lotMusic", Ambience(dayNight.transform, "Lot Music", "Dads/music_greensleeves")),
            ("birds", Ambience(dayNight.transform, "Birds", "Dads/birds_loop")),
            ("crickets", Ambience(dayNight.transform, "Crickets", "Dads/crickets_loop")),
            ("curfewMusic", Ambience(dayNight.transform, "Curfew Music", "Dads/music_curfew_loop")));
    }

    static AudioSource Ambience(Transform parent, string name, string clip)
    {
        var source = new GameObject(name).AddComponent<AudioSource>();
        source.transform.SetParent(parent, false);
        source.clip = Clip(clip);
        source.loop = true;
        source.playOnAwake = false;
        source.spatialBlend = 0;
        source.volume = 0;
        return source;
    }

    static Gradient Gradient(params (float time, Color color)[] keys)
    {
        var gradient = new Gradient();
        gradient.SetKeys(keys.Select(k => new GradientColorKey(k.color, k.time)).ToArray(), new[] { new GradientAlphaKey(1, 0), new GradientAlphaKey(1, 1) });
        return gradient;
    }

    static void BuildEffectsObject(Transform gameplay, Fx fx, QuantumEntityViewUpdater viewUpdater, DadsCamera cameraRig, DadsHud hud)
    {
        var effects = new GameObject("Dads Effects").AddComponent<DadsEffects>();
        effects.transform.SetParent(gameplay, false);
        var popup = new GameObject("Dads Popup");
        var popupText = WorldText(popup.transform, "Text", Vector3.zero, 0.07f, "+$5");
        Set(popup.AddComponent<DadsPopup>(), ("text", popupText));
        var popupPrefab = SavePrefab(popup, FxFolder).GetComponent<DadsPopup>();
        var splats = AddLayer(gameplay, "Ground Splats", new Layer { Count = 0, Loop = true, Duration = 1, Speed = Vector2.zero, Size = new Vector2(0.5f, 1f), Life = new Vector2(30, 30), Gravity = 0, Flat = true, Max = 800 });
        var puff = new GameObject("Muzzle Puff");
        Place(Model("FX", "Pistol Muzzle Flash"), puff.transform, Vector3.zero, Quaternion.identity);
        var puffPrefab = SavePrefab(puff, FxFolder);
        Set(effects, ("viewUpdater", viewUpdater), ("cameraRig", cameraRig), ("hud", hud),
            ("creamBurst", fx.Cream), ("bigCreamBurst", fx.BigCream), ("gasBurst", fx.Gas), ("dustBurst", fx.Dust), ("leafBurst", fx.Leaves),
            ("crashBurst", fx.Crash), ("confettiBurst", fx.Confetti), ("sparkleBurst", fx.Sparkle), ("muzzlePuff", puffPrefab),
            ("groundSplats", splats), ("popupPrefab", popupPrefab));
    }

    static void BuildAudio(Transform gameplay, Transform listener, QuantumEntityViewUpdater viewUpdater, DadsInput input)
    {
        var oneShot = new GameObject("Dads One Shot").AddComponent<AudioSource>();
        oneShot.playOnAwake = false;
        oneShot.spatialBlend = 1;
        oneShot.minDistance = 3;
        oneShot.maxDistance = 70;
        oneShot.rolloffMode = AudioRolloffMode.Linear;
        oneShot.dopplerLevel = 0;
        var oneShotPrefab = SavePrefab(oneShot.gameObject, FxFolder).GetComponent<AudioSource>();
        var audio = new GameObject("Dads Audio").AddComponent<DadsAudio>();
        audio.transform.SetParent(gameplay, false);
        var serialized = new SerializedObject(audio);
        var gather = serialized.FindProperty("gatherSounds");
        var gathers = new[] { (DadItem.MudBucket, "Dads/mud_squelch"), (DadItem.StrawberryBasket, "Dads/berry_pick"), (DadItem.IcedCoffee, "Dads/coffee_grab"), (DadItem.GoldLeaf, "kaching") };
        gather.arraySize = gathers.Length;
        for (int i = 0; i < gathers.Length; i++)
        {
            gather.GetArrayElementAtIndex(i).FindPropertyRelative("Kind").enumValueIndex = (int)gathers[i].Item1;
            gather.GetArrayElementAtIndex(i).FindPropertyRelative("Clip").objectReferenceValue = Clip(gathers[i].Item2);
        }
        serialized.ApplyModifiedPropertiesWithoutUndo();
        Set(audio, ("oneShotPrefab", oneShotPrefab), ("listener", listener), ("viewUpdater", viewUpdater), ("input", input),
            ("shove", Clip("Dads/shove")), ("whiff", Clip("throw")), ("scoopShot", Clip("Dads/scoop_shot")), ("minigun", Clip("gun_minigun")),
            ("splatFace", Clip("Dads/splat_face")), ("splatGround", Clip("splat_land")),
            ("kidYay", new Object[] { Clip("Dads/kid_yay_1"), Clip("Dads/kid_yay_2"), Clip("Dads/kid_yay_3") }),
            ("kidGiggle", Clip("Dads/kid_giggle")), ("kidEww", Clip("Dads/kid_eww")), ("kidCry", Clip("Dads/kid_cry")),
            ("coinBurst", Clip("Dads/coin_burst")), ("coinPickup", Clip("Dads/coin_pickup")),
            ("fatKidBurp", Clip("Dads/fat_kid_burp")), ("fatKidRoar", Clip("Dads/fat_kid_roar")), ("fatKidStomp", Clip("Dads/fat_kid_stomp")),
            ("farts", new Object[] { Clip("Dads/fart_1"), Clip("Dads/fart_2") }), ("cough", Clip("Dads/cough")),
            ("plop", Clip("Dads/plop")), ("refill", Clip("Dads/refill")), ("coneGrab", Clip("Dads/cone_grab")), ("pickup", Clip("pickup")),
            ("thrown", Clip("throw")), ("baristaHey", Clip("Dads/barista_hey")), ("churn", Clip("Dads/churn_whir")),
            ("treeShake", Clip("Dads/tree_shake")), ("nutDrop", Clip("Dads/nut_drop")), ("vaultOpen", Clip("Dads/vault_open")),
            ("plateClick", Clip("Dads/plate_click")), ("gateOpen", Clip("Dads/gate_open")), ("cashRegister", Clip("Dads/cash_register")),
            ("stamp", Clip("Dads/stamp")), ("honk", Clip("Dads/honk")), ("bell", Clip("bell")), ("crash", Clip("crash")),
            ("oof", Clip("Dads/oof")), ("tumble", Clip("Dads/tumble")), ("busted", Clip("Dads/busted")), ("ticket", Clip("Dads/ticket")),
            ("whistle", Clip("Dads/whistle")), ("siren", Clip("Dads/siren_loop")), ("brainFreeze", Clip("Dads/brain_freeze")),
            ("rooster", Clip("Dads/rooster")), ("duskChime", Clip("Dads/dusk_chime")), ("fanfare", Clip("Dads/fanfare")),
            ("sadTrombone", Clip("Dads/sad_trombone")));
    }

    static AudioClip Clip(string name)
    {
        var path = $"{Audio}/{name}.wav";
        var clip = AssetDatabase.LoadAssetAtPath<AudioClip>(path);
        if (clip == null) throw new FileNotFoundException($"Missing sound {path}");
        return clip;
    }

    static void BuildViewModel(Camera camera, DadsInput input, DadsCamera cameraRig)
    {
        var root = new GameObject("View Model").transform;
        root.SetParent(camera.transform, false);
        var sway = new GameObject("Sway").transform;
        sway.SetParent(root, false);
        var recoil = new GameObject("Recoil").transform;
        recoil.SetParent(sway, false);
        var arms = Place(Model(Characters, "Dad First-Person Arms"), recoil, Vector3.zero, Quaternion.identity);
        arms.transform.localPosition = -Child(arms, "Dad First-Person Arms socket camera").localPosition + new Vector3(0.09f, -0.13f, 0.04f);
        foreach (var renderer in arms.GetComponentsInChildren<Renderer>()) renderer.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
        var hand = Child(arms, "Dad First-Person Arms socket hand R");
        var handPosition = recoil.InverseTransformPoint(hand.position);
        // Guns angle in toward the crosshair; bulky ingredients are held out in front in both hands.
        var aim = Quaternion.Inverse(hand.rotation) * recoil.rotation * Quaternion.LookRotation(new Vector3(0, 0, 6) - handPosition);
        var chest = new GameObject("Both Hands").transform;
        chest.SetParent(recoil, false);
        chest.localPosition = new Vector3(0, -0.45f, 0.75f);
        var held = HeldRig(hand, chest, aim, 0.85f);
        var viewModel = root.gameObject.AddComponent<DadsViewModel>();
        Set(viewModel, ("input", input), ("cameraRig", cameraRig), ("arms", recoil.gameObject), ("held", held), ("sway", sway), ("recoilPivot", recoil));
    }

    static DadsHud BuildHud(DadsInput input, Camera display)
    {
        var canvas = Canvas("HUD", 10, display, 0.5f);
        var font = Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");
        var splats = new Object[6];
        for (int i = 0; i < splats.Length; i++)
        {
            var splat = HudImage(canvas.transform, $"Screen Splat {i + 1}", $"screen_splat_{i % 3 + 1}", new Vector2(0.5f, 0.5f), new Vector2(300, 300));
            splat.color = Color.clear;
            splats[i] = splat;
        }
        var cough = Overlay(canvas.transform, "Cough Tint");
        var frozen = Overlay(canvas.transform, "Brain Freeze Tint");
        var money = HudText(canvas.transform, "Money", font, new Vector2(0, 1), new Vector2(24, -14), TextAnchor.UpperLeft, 36, new Color(1f, 0.88f, 0.29f));
        var day = HudText(canvas.transform, "Day", font, new Vector2(0, 1), new Vector2(24, -58), TextAnchor.UpperLeft, 20, Color.white);
        var heat = HudText(canvas.transform, "Heat", font, new Vector2(0, 1), new Vector2(24, -84), TextAnchor.UpperLeft, 20, new Color(0.45f, 0.6f, 1f));
        var debt = HudText(canvas.transform, "Debt", font, new Vector2(1, 1), new Vector2(-24, -14), TextAnchor.UpperRight, 20, new Color(1f, 0.31f, 0.64f));
        var debtBack = new GameObject("Debt Meter", typeof(RectTransform), typeof(Image)).GetComponent<Image>();
        debtBack.transform.SetParent(canvas.transform, false);
        debtBack.rectTransform.anchorMin = debtBack.rectTransform.anchorMax = debtBack.rectTransform.pivot = new Vector2(1, 1);
        debtBack.rectTransform.anchoredPosition = new Vector2(-24, -44);
        debtBack.rectTransform.sizeDelta = new Vector2(300, 14);
        debtBack.color = new Color(0.1f, 0.06f, 0.2f, 0.85f);
        var debtFill = new GameObject("Paid", typeof(RectTransform), typeof(Image)).GetComponent<Image>();
        debtFill.transform.SetParent(debtBack.transform, false);
        Stretch(debtFill.rectTransform);
        debtFill.sprite = AssetDatabase.GetBuiltinExtraResource<Sprite>("UI/Skin/UISprite.psd");
        debtFill.type = Image.Type.Filled;
        debtFill.fillMethod = Image.FillMethod.Horizontal;
        debtFill.color = new Color(0.22f, 0.95f, 0.76f);
        var due = HudText(canvas.transform, "Due", font, new Vector2(1, 1), new Vector2(-24, -64), TextAnchor.UpperRight, 20, new Color(1f, 0.88f, 0.29f));
        var jingle = HudText(canvas.transform, "Jingle", font, new Vector2(1, 1), new Vector2(-24, -92), TextAnchor.UpperRight, 20, new Color(0.22f, 0.95f, 0.76f));
        var speed = HudText(canvas.transform, "Speed", font, new Vector2(1, 0), new Vector2(-24, 96), TextAnchor.LowerRight, 26, new Color(0.22f, 0.95f, 0.76f));
        var phase = HudText(canvas.transform, "Phase", font, new Vector2(0.5f, 1), new Vector2(0, -16), TextAnchor.UpperCenter, 22, new Color(1f, 0.31f, 0.64f));
        var prompt = HudText(canvas.transform, "Prompt", font, new Vector2(0.5f, 0.5f), new Vector2(0, -60), TextAnchor.UpperCenter, 20, Color.white);
        var carried = HudText(canvas.transform, "Carried", font, new Vector2(0.5f, 0), new Vector2(0, 112), TextAnchor.LowerCenter, 18, new Color(1f, 0.88f, 0.29f));
        var tip = HudText(canvas.transform, "Tip", font, new Vector2(0.5f, 1), new Vector2(0, -44), TextAnchor.UpperCenter, 18, new Color(0.22f, 0.95f, 0.76f));
        HudText(canvas.transform, "Crosshair", font, new Vector2(0.5f, 0.5f), Vector2.zero, TextAnchor.MiddleCenter, 26, Color.white).text = "+";
        HudText(canvas.transform, "Controls", font, new Vector2(0, 0), new Vector2(24, 10), TextAnchor.LowerLeft, 13, new Color(1, 1, 1, 0.6f)).text =
            "WASD move  SHIFT run  SPACE jump  CLICK shove / shoot / plop scoops  E use  Q drop (hold to throw)  1-4 hotbar";

        var tubChips = new Object[4];
        var tubTexts = new Object[4];
        for (int i = 0; i < 4; i++)
        {
            var chip = new GameObject($"Tub {i + 1}", typeof(RectTransform), typeof(Image)).GetComponent<Image>();
            chip.transform.SetParent(canvas.transform, false);
            chip.rectTransform.anchorMin = chip.rectTransform.anchorMax = chip.rectTransform.pivot = new Vector2(0, 0);
            chip.rectTransform.anchoredPosition = new Vector2(24, 40 + (3 - i) * 26);
            chip.rectTransform.sizeDelta = new Vector2(18, 18);
            chip.raycastTarget = false;
            var label = HudText(canvas.transform, $"Tub {i + 1} Label", font, new Vector2(0, 0), new Vector2(50, 38 + (3 - i) * 26), TextAnchor.LowerLeft, 16, Color.white);
            label.rectTransform.sizeDelta = new Vector2(300, 22);
            tubChips[i] = chip;
            tubTexts[i] = label;
        }
        HudText(canvas.transform, "Freezer Title", font, new Vector2(0, 0), new Vector2(24, 146), TextAnchor.LowerLeft, 14, new Color(1, 1, 1, 0.7f)).text = "FREEZER";

        var slotTexts = new Object[4];
        var slotFrames = new Object[4];
        for (int i = 0; i < 4; i++)
        {
            var frame = new GameObject($"Slot {i + 1}", typeof(RectTransform), typeof(Image)).GetComponent<Image>();
            frame.transform.SetParent(canvas.transform, false);
            frame.rectTransform.anchorMin = frame.rectTransform.anchorMax = frame.rectTransform.pivot = new Vector2(0.5f, 0);
            frame.rectTransform.anchoredPosition = new Vector2((i - 1.5f) * 132, 28);
            frame.rectTransform.sizeDelta = new Vector2(124, 74);
            frame.raycastTarget = false;
            var text = HudText(frame.transform, "Label", font, new Vector2(0.5f, 0.5f), Vector2.zero, TextAnchor.MiddleCenter, 13, Color.white);
            text.rectTransform.sizeDelta = new Vector2(120, 70);
            slotTexts[i] = text;
            slotFrames[i] = frame;
        }

        var cardRoot = new GameObject("Card", typeof(RectTransform), typeof(CanvasGroup), typeof(Image));
        cardRoot.transform.SetParent(canvas.transform, false);
        var cardRect = cardRoot.GetComponent<RectTransform>();
        cardRect.anchorMin = cardRect.anchorMax = cardRect.pivot = new Vector2(0.5f, 0.5f);
        cardRect.sizeDelta = new Vector2(760, 420);
        cardRoot.GetComponent<Image>().color = new Color(0.1f, 0.06f, 0.2f, 0.92f);
        cardRoot.GetComponent<Image>().raycastTarget = false;
        var cardTitle = HudText(cardRoot.transform, "Title", font, new Vector2(0.5f, 1), new Vector2(0, -24), TextAnchor.UpperCenter, 40, new Color(1f, 0.88f, 0.29f));
        cardTitle.rectTransform.sizeDelta = new Vector2(720, 60);
        var cardBody = HudText(cardRoot.transform, "Body", font, new Vector2(0.5f, 0.5f), new Vector2(0, -10), TextAnchor.MiddleCenter, 22, Color.white);
        cardBody.rectTransform.sizeDelta = new Vector2(720, 280);
        var cardStamp = HudText(cardRoot.transform, "Stamp", font, new Vector2(1, 0), new Vector2(-30, 24), TextAnchor.LowerRight, 46, Color.clear);
        cardStamp.rectTransform.sizeDelta = new Vector2(400, 70);
        cardStamp.rectTransform.localRotation = Quaternion.Euler(0, 0, 12);

        var hud = canvas.gameObject.AddComponent<DadsHud>();
        Set(hud,
            ("input", input), ("moneyText", money), ("dayText", day), ("debtText", debt), ("debtFill", debtFill), ("dueText", due), ("heatText", heat),
            ("jingleText", jingle), ("phaseText", phase), ("promptText", prompt), ("carriedText", carried), ("speedText", speed), ("tipText", tip),
            ("tubChips", tubChips), ("tubTexts", tubTexts), ("slotTexts", slotTexts), ("slotFrames", slotFrames), ("screenSplats", splats),
            ("coughTint", cough), ("frozenTint", frozen), ("card", cardRoot.GetComponent<CanvasGroup>()), ("cardTitle", cardTitle), ("cardBody", cardBody),
            ("cardStamp", cardStamp));
        return hud;
    }

    static Image Overlay(Transform parent, string name)
    {
        var image = new GameObject(name, typeof(RectTransform), typeof(Image)).GetComponent<Image>();
        image.transform.SetParent(parent, false);
        Stretch(image.rectTransform);
        image.color = Color.clear;
        image.raycastTarget = false;
        return image;
    }

    static Image HudImage(Transform parent, string name, string sprite, Vector2 anchor, Vector2 size)
    {
        var image = new GameObject(name, typeof(RectTransform), typeof(Image)).GetComponent<Image>();
        image.transform.SetParent(parent, false);
        image.rectTransform.anchorMin = image.rectTransform.anchorMax = image.rectTransform.pivot = anchor;
        image.rectTransform.sizeDelta = size;
        image.sprite = AssetDatabase.LoadAssetAtPath<Sprite>($"Assets/Art/Sprites/{sprite}.png");
        image.raycastTarget = false;
        return image;
    }

    // ------------------------------------------------------------------------------------------------ effects

    // Rows of Assets/Art/Sprites/fx_atlas.png, top to bottom (drawn by Art/Tools/zombie-styles/fx_sprites.py).
    enum FxRow { Blob, Star, Smoke, Sprinkle, Spark, Drop, Ring, Shard }

    static readonly Color SparkYellow = new Color(1f, 0.85f, 0.3f);
    static readonly Color SparkOrange = new Color(1f, 0.5f, 0.15f);

    class Fx
    {
        public FxBurst Cream, BigCream, Gas, Dust, Leaves, Crash, Confetti, Sparkle;
    }

    // One particle layer of an effect. The defaults describe a short burst of blobs falling under gravity.
    class Layer
    {
        public FxRow Row = FxRow.Blob;
        public int Count = 10;
        public Vector2 Speed = new Vector2(2, 5);
        public Vector2 Size = new Vector2(0.1f, 0.2f);
        public Vector2 Life = new Vector2(0.5f, 1f);
        public float Gravity = 1.5f;
        public Color Color = Color.white;
        public bool Glow, Stretch, Flat, Collide, Rainbow, Loop;
        public float Radius = 0.15f;
        public float Cone = -1;
        public float Grow;
        public float Rate;
        public float Duration = 0.1f;
        public int Max = 1000;
    }

    static Fx BuildEffects()
    {
        var fx = new Fx();
        fx.Cream = FxPrefab("Cream Burst", 2.5f, root =>
        {
            AddLayer(root, "Sparkles", new Layer { Row = FxRow.Star, Count = 5, Speed = new Vector2(1, 3), Size = new Vector2(0.1f, 0.18f), Life = new Vector2(0.2f, 0.4f), Gravity = 0, Glow = true, Color = Color.white });
            return new[]
            {
                AddLayer(root, "Blobs", new Layer { Count = 16, Speed = new Vector2(2, 5), Size = new Vector2(0.08f, 0.2f), Collide = true }),
                AddLayer(root, "Drops", new Layer { Row = FxRow.Drop, Count = 8, Speed = new Vector2(3, 6), Size = new Vector2(0.05f, 0.1f), Gravity = 2, Stretch = true }),
            };
        });
        fx.BigCream = FxPrefab("Big Cream Burst", 3f, root =>
        {
            AddLayer(root, "Confetti", new Layer { Row = FxRow.Sprinkle, Count = 30, Speed = new Vector2(3, 7), Size = new Vector2(0.1f, 0.18f), Life = new Vector2(1f, 1.6f), Gravity = 1, Rainbow = true, Collide = true });
            AddLayer(root, "Stars", new Layer { Row = FxRow.Star, Count = 8, Speed = new Vector2(2, 4), Size = new Vector2(0.15f, 0.28f), Life = new Vector2(0.3f, 0.5f), Gravity = 0, Glow = true, Color = SparkYellow });
            AddModel(root, "Hit Star", 0.25f, 1.3f, false, true, new Vector3(0, 0, 500), 0.9f);
            return new[]
            {
                AddLayer(root, "Blobs", new Layer { Count = 40, Speed = new Vector2(3, 8), Size = new Vector2(0.12f, 0.3f), Life = new Vector2(0.8f, 1.3f), Collide = true, Radius = 0.25f }),
                AddLayer(root, "Drops", new Layer { Row = FxRow.Drop, Count = 20, Speed = new Vector2(4, 9), Size = new Vector2(0.07f, 0.13f), Gravity = 2, Stretch = true }),
            };
        });
        fx.Gas = FxPrefab("Gas Burst", 4f, root => new[]
        {
            AddLayer(root, "Cloud", new Layer { Row = FxRow.Smoke, Count = 30, Speed = new Vector2(1, 4), Size = new Vector2(1f, 2f), Life = new Vector2(1.5f, 2.5f), Gravity = -0.05f, Grow = 2.5f, Radius = 1f }),
            AddLayer(root, "Bubbles", new Layer { Row = FxRow.Ring, Count = 12, Speed = new Vector2(1, 3), Size = new Vector2(0.2f, 0.4f), Life = new Vector2(0.8f, 1.4f), Gravity = -0.2f, Radius = 0.8f }),
        });
        fx.Dust = FxPrefab("Dust Burst", 2.5f, root =>
        {
            AddLayer(root, "Stars", new Layer { Row = FxRow.Star, Count = 6, Speed = new Vector2(2, 4), Size = new Vector2(0.15f, 0.3f), Life = new Vector2(0.4f, 0.7f), Gravity = 0.3f, Glow = true, Color = SparkYellow });
            return new[] { AddLayer(root, "Dust", new Layer { Row = FxRow.Smoke, Count = 14, Speed = new Vector2(1, 3), Size = new Vector2(0.4f, 0.8f), Life = new Vector2(0.6f, 1f), Gravity = -0.05f, Grow = 2, Radius = 0.4f }) };
        });
        fx.Leaves = FxPrefab("Leaf Burst", 3.5f, root => new[]
        {
            AddLayer(root, "Leaves", new Layer { Row = FxRow.Shard, Count = 40, Speed = new Vector2(1, 4), Size = new Vector2(0.15f, 0.3f), Life = new Vector2(1.5f, 2.5f), Gravity = 0.4f, Radius = 2.5f, Collide = true }),
        });
        fx.Crash = FxPrefab("Crash Burst", 3f, root =>
        {
            AddLayer(root, "Sparks", new Layer { Row = FxRow.Spark, Count = 40, Speed = new Vector2(5, 12), Size = new Vector2(0.15f, 0.3f), Life = new Vector2(0.2f, 0.5f), Gravity = 1, Glow = true, Stretch = true, Color = SparkOrange, Radius = 0.5f });
            AddLayer(root, "Glass", new Layer { Row = FxRow.Shard, Count = 25, Speed = new Vector2(3, 8), Size = new Vector2(0.1f, 0.25f), Gravity = 2, Color = new Color(0.7f, 0.9f, 1f), Collide = true, Radius = 0.5f });
            AddLayer(root, "Smoke", new Layer { Row = FxRow.Smoke, Count = 10, Speed = new Vector2(0.5f, 2f), Size = new Vector2(0.8f, 1.4f), Life = new Vector2(1f, 1.8f), Gravity = -0.06f, Grow = 2.5f, Color = new Color(0.3f, 0.27f, 0.35f), Radius = 0.8f });
            return new ParticleSystem[0];
        });
        fx.Confetti = FxPrefab("Confetti Burst", 3f, root =>
        {
            AddLayer(root, "Sprinkles", new Layer { Row = FxRow.Sprinkle, Count = 80, Speed = new Vector2(5, 10), Size = new Vector2(0.12f, 0.2f), Life = new Vector2(1.5f, 2.5f), Gravity = 0.8f, Rainbow = true, Cone = 35, Collide = true });
            return new[] { AddLayer(root, "Stars", new Layer { Row = FxRow.Star, Count = 15, Speed = new Vector2(2, 5), Size = new Vector2(0.2f, 0.35f), Life = new Vector2(0.4f, 0.8f), Gravity = 0, Glow = true }) };
        });
        fx.Sparkle = FxPrefab("Sparkle Burst", 2.5f, root =>
        {
            AddLayer(root, "Sprinkles", new Layer { Row = FxRow.Sprinkle, Count = 25, Speed = new Vector2(2, 5), Size = new Vector2(0.1f, 0.16f), Life = new Vector2(0.8f, 1.4f), Gravity = 0.8f, Rainbow = true, Cone = 40 });
            return new[] { AddLayer(root, "Stars", new Layer { Row = FxRow.Star, Count = 18, Speed = new Vector2(1.5f, 4), Size = new Vector2(0.15f, 0.3f), Life = new Vector2(0.4f, 0.9f), Gravity = -0.2f, Glow = true }) };
        });
        return fx;
    }

    static FxBurst FxPrefab(string name, float lifetime, Func<Transform, ParticleSystem[]> build)
    {
        var root = new GameObject(name);
        var tinted = build(root.transform);
        Set(root.AddComponent<FxBurst>(), ("tinted", tinted.Cast<Object>().ToArray()), ("lifetime", lifetime));
        return SavePrefab(root, FxFolder).GetComponent<FxBurst>();
    }

    static ParticleSystem AddLayer(Transform parent, string name, Layer layer)
    {
        var go = new GameObject(name);
        go.transform.SetParent(parent, false);
        // Cone shapes emit along local +Z; turn them to spray upward.
        if (layer.Cone >= 0) go.transform.localRotation = Quaternion.Euler(-90, 0, 0);
        var particles = go.AddComponent<ParticleSystem>();
        particles.Stop(true, ParticleSystemStopBehavior.StopEmittingAndClear);
        var main = particles.main;
        main.duration = layer.Duration;
        main.loop = layer.Loop;
        main.startLifetime = new ParticleSystem.MinMaxCurve(layer.Life.x, layer.Life.y);
        main.startSpeed = new ParticleSystem.MinMaxCurve(layer.Speed.x, layer.Speed.y);
        main.startSize = new ParticleSystem.MinMaxCurve(layer.Size.x, layer.Size.y);
        main.startRotation = new ParticleSystem.MinMaxCurve(0, Mathf.PI * 2);
        main.startColor = layer.Rainbow ? new ParticleSystem.MinMaxGradient(Rainbow()) { mode = ParticleSystemGradientMode.RandomColor } : new ParticleSystem.MinMaxGradient(layer.Color);
        main.gravityModifier = layer.Gravity;
        main.simulationSpace = ParticleSystemSimulationSpace.World;
        main.scalingMode = ParticleSystemScalingMode.Hierarchy;
        main.maxParticles = layer.Max;
        var emission = particles.emission;
        emission.rateOverTime = layer.Rate;
        emission.SetBursts(layer.Count > 0 ? new[] { new ParticleSystem.Burst(0, (short)layer.Count) } : new ParticleSystem.Burst[0]);
        var shape = particles.shape;
        shape.shapeType = layer.Cone >= 0 ? ParticleSystemShapeType.Cone : ParticleSystemShapeType.Sphere;
        shape.angle = Mathf.Max(layer.Cone, 0);
        shape.radius = Mathf.Max(layer.Radius, 0.0001f);
        var size = particles.sizeOverLifetime;
        size.enabled = true;
        size.size = layer.Grow > 0
            ? new ParticleSystem.MinMaxCurve(1, new AnimationCurve(new Keyframe(0, 1 / layer.Grow), new Keyframe(1, 1)))
            : new ParticleSystem.MinMaxCurve(1, new AnimationCurve(new Keyframe(0, 1), new Keyframe(0.75f, 1), new Keyframe(1, 0)));
        if (layer.Grow > 0) main.startSize = new ParticleSystem.MinMaxCurve(layer.Size.x * layer.Grow, layer.Size.y * layer.Grow);
        var sheet = particles.textureSheetAnimation;
        sheet.enabled = true;
        sheet.mode = ParticleSystemAnimationMode.Grid;
        sheet.numTilesX = 8;
        sheet.numTilesY = 8;
        sheet.animation = ParticleSystemAnimationType.SingleRow;
        sheet.rowMode = ParticleSystemAnimationRowMode.Custom;
        sheet.rowIndex = (int)layer.Row;
        sheet.frameOverTime = new ParticleSystem.MinMaxCurve(0f, 0.999f);
        if (layer.Collide)
        {
            var collision = particles.collision;
            collision.enabled = true;
            collision.type = ParticleSystemCollisionType.World;
            collision.mode = ParticleSystemCollisionMode.Collision3D;
            collision.dampen = 0.7f;
            collision.bounce = 0.15f;
            collision.radiusScale = 0.5f;
            collision.quality = ParticleSystemCollisionQuality.Medium;
        }
        var renderer = go.GetComponent<ParticleSystemRenderer>();
        renderer.sharedMaterial = AssetDatabase.LoadAssetAtPath<Material>($"{MaterialFolder}/{(layer.Glow ? "FX Atlas Glow" : "FX Atlas")}.mat");
        renderer.renderMode = layer.Flat ? ParticleSystemRenderMode.HorizontalBillboard : layer.Stretch ? ParticleSystemRenderMode.Stretch : ParticleSystemRenderMode.Billboard;
        renderer.velocityScale = 0.06f;
        renderer.lengthScale = 1.5f;
        renderer.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
        renderer.receiveShadows = false;
        return particles;
    }

    static Gradient Rainbow()
    {
        var gradient = new Gradient();
        gradient.SetKeys(
            new[] { new GradientColorKey(new Color(1f, 0.31f, 0.64f), 0), new GradientColorKey(new Color(1f, 0.88f, 0.29f), 0.25f),
                new GradientColorKey(new Color(0.22f, 0.95f, 0.76f), 0.5f), new GradientColorKey(new Color(0.18f, 0.53f, 1f), 0.75f), new GradientColorKey(Color.white, 1) },
            new[] { new GradientAlphaKey(1, 0), new GradientAlphaKey(1, 1) });
        gradient.mode = GradientMode.Fixed;
        return gradient;
    }

    // An FX model that pops in and out.
    static void AddModel(Transform parent, string model, float duration, float overshoot, bool ring, bool faceCamera, Vector3 spin, float scale)
    {
        var instance = Place(Model("FX", model), parent, Vector3.zero, Quaternion.identity);
        instance.transform.localScale = Vector3.one * scale;
        foreach (var renderer in instance.GetComponentsInChildren<Renderer>()) renderer.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
        Set(instance.AddComponent<FxExpand>(), ("duration", duration), ("overshoot", overshoot), ("ring", ring), ("faceCamera", faceCamera), ("spin", spin));
    }

    // ------------------------------------------------------------------------------------------------ helpers

    static GameObject Model(string category, string name)
    {
        var path = $"{Art}/{category}/{name}.fbx";
        var model = AssetDatabase.LoadAssetAtPath<GameObject>(path);
        if (model == null) throw new FileNotFoundException($"Missing PS1 model {path}");
        return model;
    }

    static GameObject Place(GameObject model, Transform parent, Vector3 position, Quaternion rotation)
    {
        var instance = (GameObject)PrefabUtility.InstantiatePrefab(model, parent);
        instance.transform.localPosition = position;
        instance.transform.localRotation = rotation;
        return instance;
    }

    static Transform Child(GameObject root, string name)
    {
        var child = root.GetComponentsInChildren<Transform>(true).FirstOrDefault(t => t.name == name);
        if (child == null) throw new InvalidOperationException($"{root.name} has no child named '{name}'");
        return child;
    }

    // Combined renderer bounds in the space of the given root (optionally destroying the root afterwards).
    static Bounds LocalBounds(Transform root, bool destroy = false)
    {
        var bounds = new Bounds();
        var first = true;
        foreach (var filter in root.GetComponentsInChildren<MeshFilter>(true))
        {
            var mesh = filter.sharedMesh.bounds;
            for (int corner = 0; corner < 8; corner++)
            {
                var local = mesh.center + Vector3.Scale(mesh.extents, new Vector3((corner & 1) != 0 ? 1 : -1, (corner & 2) != 0 ? 1 : -1, (corner & 4) != 0 ? 1 : -1));
                var point = root.InverseTransformPoint(filter.transform.TransformPoint(local));
                if (first) bounds = new Bounds(point, Vector3.zero);
                else bounds.Encapsulate(point);
                first = false;
            }
        }
        if (destroy) Object.DestroyImmediate(root.gameObject);
        return bounds;
    }

    static GameObject EntityRoot(string name)
    {
        var root = new GameObject(name);
        root.AddComponent<QuantumEntityPrototype>().TransformMode = QuantumEntityPrototypeTransformMode.Transform3D;
        root.AddComponent<QuantumEntityView>();
        return root;
    }

    static GameObject SavePrefab(GameObject root, string folder = PrefabFolder)
    {
        Directory.CreateDirectory(folder);
        var path = $"{folder}/{root.name}.prefab";
        var prefab = PrefabUtility.SaveAsPrefabAsset(root, path);
        Object.DestroyImmediate(root);
        if (prefab.GetComponent<QuantumEntityPrototype>() != null)
        {
            QuantumAssetObjectPostprocessor.TryCreateOrUpdatePrototypeAssetForPrefab(path, out var prototypePath);
            AssetDatabase.ImportAsset(prototypePath, ImportAssetOptions.ForceSynchronousImport);
        }
        return prefab;
    }

    static AssetRef<EntityPrototype> PrototypeFor(GameObject prefab)
    {
        var path = QuantumEntityPrototypeAssetObjectImporter.GetPathForPrefab(AssetDatabase.GetAssetPath(prefab));
        return AssetDatabase.LoadAssetAtPath<EntityPrototype>(path);
    }

    static T ReplaceAsset<T>(T asset, string path) where T : Object
    {
        var existing = AssetDatabase.LoadAssetAtPath<T>(path);
        if (existing == null)
        {
            AssetDatabase.CreateAsset(asset, path);
            AssetDatabase.ImportAsset(path, ImportAssetOptions.ForceSynchronousImport);
            return AssetDatabase.LoadAssetAtPath<T>(path);
        }
        // Keep the existing asset and copy the new values into it, restoring its Quantum identifier so references hold.
        var identifier = existing is AssetObject quantumAsset ? quantumAsset.Identifier : default;
        EditorUtility.CopySerialized(asset, existing);
        if (existing is AssetObject restored) restored.Identifier = identifier;
        EditorUtility.SetDirty(existing);
        return existing;
    }

    static Material Material(string name, Color color, string shader = "Universal Render Pipeline/Lit", bool transparent = false)
    {
        var path = $"{MaterialFolder}/{name}.mat";
        var material = AssetDatabase.LoadAssetAtPath<Material>(path);
        if (material == null)
        {
            material = new Material(Shader.Find(shader));
            AssetDatabase.CreateAsset(material, path);
        }
        material.SetColor("_BaseColor", color);
        if (transparent)
        {
            material.SetFloat("_Surface", 1);
            material.SetFloat("_Blend", 0);
            material.SetOverrideTag("RenderType", "Transparent");
            material.renderQueue = (int)UnityEngine.Rendering.RenderQueue.Transparent;
            material.SetInt("_SrcBlend", (int)UnityEngine.Rendering.BlendMode.SrcAlpha);
            material.SetInt("_DstBlend", (int)UnityEngine.Rendering.BlendMode.OneMinusSrcAlpha);
            material.SetInt("_ZWrite", 0);
            material.EnableKeyword("_SURFACE_TYPE_TRANSPARENT");
        }
        EditorUtility.SetDirty(material);
        return material;
    }

    static GameObject Primitive(PrimitiveType type, Transform parent, string name, Vector3 position, Vector3 size, Material material, bool keepCollider)
    {
        var go = GameObject.CreatePrimitive(type);
        go.name = name;
        if (!keepCollider) Object.DestroyImmediate(go.GetComponent<Collider>());
        go.transform.SetParent(parent, false);
        go.transform.localPosition = position;
        go.transform.localScale = size;
        go.GetComponent<Renderer>().sharedMaterial = material;
        return go;
    }

    static TextMesh WorldText(Transform parent, string name, Vector3 position, float size, string text)
    {
        var go = new GameObject(name);
        go.transform.SetParent(parent, false);
        go.transform.localPosition = position;
        var mesh = go.AddComponent<TextMesh>();
        mesh.text = text;
        mesh.characterSize = size;
        mesh.fontSize = 48;
        mesh.anchor = TextAnchor.MiddleCenter;
        mesh.alignment = TextAlignment.Center;
        mesh.fontStyle = FontStyle.Bold;
        mesh.font = Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");
        go.GetComponent<MeshRenderer>().sharedMaterial = mesh.font.material;
        return mesh;
    }

    // Screen-space canvases drawn by the display camera on the UI layer, so a camera render captures the whole frame.
    static Canvas Canvas(string name, int order, Camera display, float distance)
    {
        var go = new GameObject(name, typeof(Canvas), typeof(CanvasScaler));
        var canvas = go.GetComponent<Canvas>();
        canvas.renderMode = RenderMode.ScreenSpaceCamera;
        canvas.worldCamera = display;
        canvas.planeDistance = distance;
        canvas.sortingOrder = order;
        var scaler = go.GetComponent<CanvasScaler>();
        scaler.uiScaleMode = CanvasScaler.ScaleMode.ScaleWithScreenSize;
        scaler.referenceResolution = new Vector2(1280, 720);
        return canvas;
    }

    static void Stretch(RectTransform rect)
    {
        rect.anchorMin = Vector2.zero;
        rect.anchorMax = Vector2.one;
        rect.offsetMin = rect.offsetMax = Vector2.zero;
    }

    static Text HudText(Transform parent, string name, Font font, Vector2 anchor, Vector2 position, TextAnchor alignment, int size, Color color)
    {
        var rect = new GameObject(name, typeof(RectTransform), typeof(Text), typeof(Outline)).GetComponent<RectTransform>();
        rect.SetParent(parent, false);
        rect.anchorMin = rect.anchorMax = rect.pivot = anchor;
        rect.anchoredPosition = position;
        rect.sizeDelta = new Vector2(900, 80);
        var text = rect.GetComponent<Text>();
        text.font = font;
        text.fontSize = size;
        text.fontStyle = FontStyle.Bold;
        text.alignment = alignment;
        text.color = color;
        text.raycastTarget = false;
        rect.GetComponent<Outline>().effectColor = new Color(0.1f, 0.06f, 0.2f);
        return text;
    }

    static void Set(Object target, params (string field, object value)[] values)
    {
        var serialized = new SerializedObject(target);
        foreach (var (field, value) in values)
        {
            var property = serialized.FindProperty(field);
            if (property == null) throw new InvalidOperationException($"{target.GetType().Name} has no serialized field '{field}'");
            switch (value)
            {
                case Object[] array:
                    property.arraySize = array.Length;
                    for (int i = 0; i < array.Length; i++) property.GetArrayElementAtIndex(i).objectReferenceValue = array[i];
                    break;
                case float number: property.floatValue = number; break;
                case bool flag: property.boolValue = flag; break;
                case Vector3 vector: property.vector3Value = vector; break;
                default: property.objectReferenceValue = (Object)value; break;
            }
        }
        serialized.ApplyModifiedPropertiesWithoutUndo();
    }
}
