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
        var memory = new GameObject("Tutorial Memory").AddComponent<TutorialMemory>();
        memory.transform.SetParent(gameplay, false);
        Set(memory, ("runner", runner));
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

        var hud = BuildHud(input, display, camera);
        foreach (var child in screen.GetComponentsInChildren<Transform>(true).Concat(hud.GetComponentsInChildren<Transform>(true))) child.gameObject.layer = UiLayer;
        BuildEffectsObject(gameplay, fx, viewUpdater, cameraRig, hud);
        BuildAudio(gameplay, camera.transform, viewUpdater, input);
        BuildDayNight(gameplay, sun, camera);

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

    static void BuildDayNight(Transform gameplay, Light sun, Camera sky)
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
        Set(dayNight, ("sun", sun), ("sky", sky),
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
        var popupText = WorldText(popup.transform, "Text", Vector3.zero, 0.1f, "+$5");
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
            ("sadTrombone", Clip("Dads/sad_trombone")), ("lessonDing", Clip("Dads/lesson_ding")));
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
        // Guns angle in toward the crosshair; bulky ingredients stay upright in the hand.
        var aim = Quaternion.Inverse(hand.rotation) * recoil.rotation * Quaternion.LookRotation(new Vector3(0, 0, 6) - handPosition);
        var held = HeldRig(hand, hand, aim, 0.55f, Quaternion.Inverse(hand.rotation) * recoil.rotation);
        var viewModel = root.gameObject.AddComponent<DadsViewModel>();
        Set(viewModel, ("input", input), ("cameraRig", cameraRig), ("arms", recoil.gameObject), ("held", held), ("sway", sway), ("recoilPivot", recoil));
    }

    const string Sprites = "Assets/Art/Sprites";
    const string Fonts = "Assets/Art/Fonts";
    // HUD frames are pixel sprites drawn twice their size on the 1280 x 720 canvas, like the zombie HUD.
    const float HudFrameScale = 2f;
    static readonly Color HudYellow = new Color(1f, 0.88f, 0.29f);
    static readonly Color HudMint = new Color(0.22f, 0.95f, 0.76f);
    static readonly Color HudLavender = new Color(0.71f, 0.55f, 1f);

    // Nine-slice borders (left, bottom, right, top, in sprite pixels) of the frames drawn by hud_sprites_dads.py.
    static readonly Dictionary<string, Vector4> SpriteBorders = new Dictionary<string, Vector4>
    {
        { "DadsHUD/panel", new Vector4(8, 8, 8, 8) }, { "DadsHUD/panel_mint", new Vector4(8, 8, 8, 8) }, { "DadsHUD/panel_gold", new Vector4(8, 8, 8, 8) },
        { "DadsHUD/card", new Vector4(8, 8, 8, 8) }, { "DadsHUD/slot", new Vector4(8, 8, 8, 8) }, { "DadsHUD/slot_selected", new Vector4(8, 8, 8, 8) },
        { "DadsHUD/bar_back", new Vector4(4, 4, 4, 4) }, { "DadsHUD/banner", new Vector4(4, 8, 4, 2) },
    };

    // Point-filtered UI sprites for the HUD frames, glyphs and item icons (hud_sprites_dads.py, hud_icons_dads.py).
    static void ConfigureSprites()
    {
        foreach (var folder in new[] { "DadsHUD", "DadsIcons" })
        {
            foreach (var path in Directory.GetFiles($"{Sprites}/{folder}", "*.png"))
            {
                var assetPath = path.Replace('\\', '/');
                var importer = (TextureImporter)AssetImporter.GetAtPath(assetPath);
                importer.textureType = TextureImporterType.Sprite;
                importer.spriteImportMode = SpriteImportMode.Single;
                var key = assetPath.Substring(Sprites.Length + 1).Replace(".png", "");
                importer.spriteBorder = SpriteBorders.TryGetValue(key, out var border) ? border : Vector4.zero;
                importer.filterMode = FilterMode.Point;
                importer.mipmapEnabled = false;
                importer.textureCompression = TextureImporterCompression.Uncompressed;
                importer.alphaIsTransparency = true;
                importer.wrapMode = TextureWrapMode.Clamp;
                importer.SaveAndReimport();
            }
        }
    }

    // Candy PS1 HUD on a 1280 x 720 reference canvas, laid out like the zombie HUD: nine-slice frames with an icon and
    // pixel-font text, the hotbar along the bottom, the prompt panel under the crosshair, and the story card.
    static DadsHud BuildHud(DadsInput input, Camera display, Camera eye)
    {
        var canvas = Canvas("HUD", 10, display, 0.5f);
        var root = canvas.transform;
        var title = PixelFont("PressStart2P-Regular");
        var body = PixelFont("PixelifySans-SemiBold");
        var splats = new Object[6];
        for (int i = 0; i < splats.Length; i++)
        {
            var splat = HudImage(root, $"Screen Splat {i + 1}", $"screen_splat_{i % 3 + 1}", new Vector2(0.5f, 0.5f), new Vector2(300, 300));
            splat.color = Color.clear;
            splats[i] = splat;
        }
        var cough = Overlay(root, "Cough Tint");
        var frozen = Overlay(root, "Brain Freeze Tint");
        HudImage(root, "Crosshair", "DadsHUD/crosshair", new Vector2(0.5f, 0.5f), new Vector2(32, 32));

        // Top left: cash, the day, heat.
        var moneyPanel = Panel(root, "Money", "panel", new Vector2(0, 1), new Vector2(16, -16), new Vector2(212, 60));
        Icon(moneyPanel, "Money Icon", "DadsIcons/LunchMoney", new Vector2(34, 0), 48);
        var money = PanelText(moneyPanel, "Money Text", title, 22, HudYellow, 66, TextAnchor.MiddleLeft);
        var dayPanel = Panel(root, "Day", "panel", new Vector2(0, 1), new Vector2(16, -84), new Vector2(212, 60));
        var dayIcon = Icon(dayPanel, "Sun Icon", "DadsHUD/sun", new Vector2(30, 0), 36);
        var day = PanelText(dayPanel, "Day Text", body, 18, Color.white, 58, TextAnchor.MiddleLeft);
        var heatPanel = Panel(root, "Heat", "panel", new Vector2(0, 1), new Vector2(16, -152), new Vector2(212, 46));
        var badges = new Object[5];
        for (int i = 0; i < badges.Length; i++) badges[i] = Icon(heatPanel, $"Badge {i + 1}", "DadsHUD/badge", new Vector2(30 + i * 38, 0), 30);

        // Top right: Big Dairy's debt and tonight's installment with strikes, then the jingle and the speed.
        var debtPanel = Panel(root, "Debt", "panel_gold", new Vector2(1, 1), new Vector2(-16, -16), new Vector2(300, 76));
        Icon(debtPanel, "Carton Icon", "DadsHUD/carton", new Vector2(32, 0), 44);
        var debt = PanelText(debtPanel, "Debt Text", title, 14, HudYellow, 62, TextAnchor.UpperLeft);
        debt.rectTransform.offsetMax = new Vector2(-10, -14);
        var trough = Panel(debtPanel, "Bar", "bar_back", new Vector2(0, 0), new Vector2(60, 12), new Vector2(222, 24));
        trough.pivot = new Vector2(0, 0);
        var debtFill = HudImage(trough, "Paid", "DadsHUD/bar_fill_mint", new Vector2(0.5f, 0.5f), Vector2.zero);
        Stretch(debtFill.rectTransform);
        debtFill.rectTransform.offsetMin = new Vector2(4, 4);
        debtFill.rectTransform.offsetMax = new Vector2(-4, -4);
        debtFill.type = Image.Type.Filled;
        debtFill.fillMethod = Image.FillMethod.Horizontal;
        var duePanel = Panel(root, "Tonight", "panel_gold", new Vector2(1, 1), new Vector2(-16, -100), new Vector2(300, 50));
        var due = PanelText(duePanel, "Tonight Text", title, 13, Color.white, 18, TextAnchor.MiddleLeft);
        var strikes = new Object[3];
        for (int i = 0; i < strikes.Length; i++) strikes[i] = Icon(duePanel, $"Strike {i + 1}", "DadsHUD/strike", new Vector2(214 + i * 30, 0), 26);
        var jinglePanel = Panel(root, "Jingle", "panel_mint", new Vector2(1, 1), new Vector2(-16, -158), new Vector2(180, 46));
        Icon(jinglePanel, "Note Icon", "DadsHUD/note", new Vector2(26, 0), 30);
        PanelText(jinglePanel, "Jingle Text", title, 11, HudMint, 48, TextAnchor.MiddleLeft).text = "JINGLE ON";
        var speedPanel = Panel(root, "Speed", "panel_mint", new Vector2(1, 1), new Vector2(-16, -212), new Vector2(180, 46));
        var speed = PanelText(speedPanel, "Speed Text", title, 13, Color.white, 18, TextAnchor.MiddleLeft);
        // The van's condition once lamp posts have dented it.
        var truckPanel = Panel(root, "Truck", "panel", new Vector2(1, 1), new Vector2(-16, -266), new Vector2(180, 46));
        PanelText(truckPanel, "Truck Text", title, 11, Color.white, 14, TextAnchor.MiddleLeft).text = "TRUCK";
        var truckBar = Panel(truckPanel, "Bar", "bar_back", new Vector2(1, 0.5f), new Vector2(-10, 0), new Vector2(96, 22));
        var truckFill = HudImage(truckBar, "Condition", "DadsHUD/bar_fill", new Vector2(0.5f, 0.5f), Vector2.zero);
        Stretch(truckFill.rectTransform);
        truckFill.rectTransform.offsetMin = new Vector2(4, 4);
        truckFill.rectTransform.offsetMax = new Vector2(-4, -4);
        truckFill.type = Image.Type.Filled;
        truckFill.fillMethod = Image.FillMethod.Horizontal;

        // Moving day: the lesson checklist (where the jingle and speed go once the truck is moving), and the arrow that
        // bobs over the next thing to use, its pivot on the arrow's tip.
        var lessonPanel = Panel(root, "Lessons", "panel_mint", new Vector2(1, 1), new Vector2(-16, -158), new Vector2(300, 290));
        var lessons = PanelText(lessonPanel, "Lesson Text", body, 18, Color.white, 18, TextAnchor.UpperLeft);
        lessons.rectTransform.offsetMax = new Vector2(-10, -14);
        lessons.lineSpacing = 1.1f;
        lessons.verticalOverflow = VerticalWrapMode.Overflow;
        var marker = HudImage(root, "Lesson Marker", "DadsHUD/marker", Vector2.zero, new Vector2(48, 48));
        marker.rectTransform.pivot = new Vector2(0.5f, 0);

        // Phase banner across the top, the next-step tip under it.
        var banner = HudImage(root, "Phase Banner", "DadsHUD/banner", new Vector2(0.5f, 1), new Vector2(720, 24 * HudFrameScale));
        banner.rectTransform.anchoredPosition = new Vector2(0, -14);
        banner.type = Image.Type.Tiled;
        banner.pixelsPerUnitMultiplier = 1 / HudFrameScale;
        var phase = HudText(banner.transform, "Phase Text", body, new Vector2(0.5f, 1), new Vector2(0, -6), TextAnchor.UpperCenter, 22, Color.white);
        phase.rectTransform.sizeDelta = new Vector2(700, 40);
        var tip = HudText(root, "Tip", body, new Vector2(0.5f, 1), new Vector2(0, -70), TextAnchor.UpperCenter, 20, HudMint);
        tip.rectTransform.sizeDelta = new Vector2(720, 60);

        // Interaction prompt under the crosshair; the panel grows to fit the text.
        var promptPanel = Panel(root, "Prompt", "panel", new Vector2(0.5f, 0.5f), new Vector2(0, -44), Vector2.zero);
        promptPanel.pivot = new Vector2(0.5f, 1);
        var layout = promptPanel.gameObject.AddComponent<VerticalLayoutGroup>();
        layout.padding = new RectOffset(20, 20, 12, 12);
        layout.childControlWidth = layout.childControlHeight = true;
        var fitter = promptPanel.gameObject.AddComponent<ContentSizeFitter>();
        fitter.horizontalFit = fitter.verticalFit = ContentSizeFitter.FitMode.PreferredSize;
        var prompt = HudText(promptPanel, "Prompt Text", body, new Vector2(0.5f, 0.5f), Vector2.zero, TextAnchor.MiddleCenter, 20, Color.white);
        prompt.horizontalOverflow = HorizontalWrapMode.Overflow;
        prompt.lineSpacing = 1.15f;

        // Hotbar: item icon, slot number, scoop count and the loaded flavor per slot, a candy frame around the selected one.
        var slotIcons = new Object[4];
        var slotBadges = new Object[4];
        var slotCounts = new Object[4];
        var slotSelected = new Object[4];
        for (int i = 0; i < 4; i++)
        {
            var slot = Panel(root, $"Slot {i + 1}", "slot", new Vector2(0.5f, 0), new Vector2((i - 1.5f) * 82, 16), new Vector2(74, 74));
            var selected = Panel(slot, "Selected", "slot_selected", new Vector2(0.5f, 0.5f), Vector2.zero, Vector2.zero);
            selected.anchorMin = Vector2.zero;
            selected.anchorMax = Vector2.one;
            selected.offsetMin = new Vector2(-6, -6);
            selected.offsetMax = new Vector2(6, 6);
            var icon = Icon(slot, "Icon", "DadsIcons/Cone", Vector2.zero, 62);
            icon.rectTransform.anchorMin = icon.rectTransform.anchorMax = icon.rectTransform.pivot = new Vector2(0.5f, 0.5f);
            icon.rectTransform.anchoredPosition = new Vector2(0, 2);
            // The loaded flavor's scoop sits on the cone's rim (or on top of a gun).
            var badge = Icon(slot, "Flavor", "DadsIcons/ScoopMud", Vector2.zero, 36);
            badge.rectTransform.anchorMin = badge.rectTransform.anchorMax = new Vector2(0.5f, 1);
            badge.rectTransform.pivot = new Vector2(0.5f, 0.5f);
            badge.rectTransform.anchoredPosition = new Vector2(0, -16);
            var key = HudText(slot, "Key", title, new Vector2(0, 1), new Vector2(7, -7), TextAnchor.UpperLeft, 10, Color.white);
            key.rectTransform.sizeDelta = new Vector2(30, 20);
            key.text = (i + 1).ToString();
            var count = HudText(slot, "Count", title, new Vector2(1, 0), new Vector2(-6, 6), TextAnchor.LowerRight, 11, Color.white);
            count.rectTransform.sizeDelta = new Vector2(70, 20);
            slotIcons[i] = icon;
            slotBadges[i] = badge;
            slotCounts[i] = count;
            slotSelected[i] = selected.gameObject;
        }
        var selectedName = HudText(root, "Selected Name", body, new Vector2(0.5f, 0), new Vector2(0, 100), TextAnchor.LowerCenter, 22, Color.white);


        // Bottom left: the controls panel. Bottom right: ammo.
        var help = HudText(root, "Help Hint", body, new Vector2(0, 0), new Vector2(20, 16), TextAnchor.LowerLeft, 16, HudLavender);
        help.text = "<color=#ffe14a>F1</color> controls";
        var controls = Panel(root, "Controls", "panel", new Vector2(0, 0), new Vector2(16, 40), new Vector2(312, 250));
        var controlsText = PanelText(controls, "Text", body, 17, Color.white, 20, TextAnchor.UpperLeft);
        controlsText.rectTransform.offsetMax = new Vector2(-12, -12);
        controlsText.lineSpacing = 1.1f;
        controlsText.text = "CONTROLS\n" + string.Join("\n", new[]
        {
            ("WASD", "move"), ("SHIFT", "run"), ("SPACE", "jump"), ("CLICK", "shove / shoot / plop scoops"), ("E", "use"),
            ("Q", "drop  (hold to throw)"), ("1-4 / WHEEL", "hotbar"), ("RIGHT CLICK", "jingle (driving)"), ("F1", "hide this"),
        }.Select(c => $"<color=#ffe14a>{c.Item1}</color>  {c.Item2}"));

        var ammoPanel = Panel(root, "Ammo", "panel_mint", new Vector2(1, 0), new Vector2(-16, 16), new Vector2(232, 76));
        var ammoIcon = Icon(ammoPanel, "Icon", "DadsIcons/ScoopMud", new Vector2(40, 0), 58);
        var ammo = PanelText(ammoPanel, "Count", title, 26, Color.white, 82, TextAnchor.UpperLeft);
        ammo.rectTransform.offsetMax = new Vector2(-8, -12);
        var ammoLabel = PanelText(ammoPanel, "Label", body, 17, HudMint, 82, TextAnchor.LowerLeft);
        ammoLabel.rectTransform.offsetMin = new Vector2(82, 10);

        // Black flash when taking the wheel on moving day drives the truck to Big Dairy's lot (under the card).
        var fade = Overlay(root, "Fade");

        // The story card: moving day, each morning's intro, Big Dairy's collection, the win and the repo.
        var card = Panel(root, "Card", "card", new Vector2(0.5f, 0.5f), Vector2.zero, new Vector2(760, 420));
        var cardGroup = card.gameObject.AddComponent<CanvasGroup>();
        var cardTitle = HudText(card, "Title", title, new Vector2(0.5f, 1), new Vector2(0, -34), TextAnchor.UpperCenter, 28, HudYellow);
        cardTitle.rectTransform.sizeDelta = new Vector2(720, 50);
        var cardBody = HudText(card, "Body", body, new Vector2(0.5f, 0.5f), new Vector2(0, -16), TextAnchor.MiddleCenter, 24, Color.white);
        cardBody.rectTransform.sizeDelta = new Vector2(700, 270);
        cardBody.lineSpacing = 1.1f;
        var cardStamp = HudText(card, "Stamp", title, new Vector2(1, 0), new Vector2(-34, 28), TextAnchor.LowerRight, 30, Color.clear);
        cardStamp.rectTransform.sizeDelta = new Vector2(420, 60);
        cardStamp.rectTransform.localRotation = Quaternion.Euler(0, 0, 12);

        var hud = canvas.gameObject.AddComponent<DadsHud>();
        Set(hud,
            ("input", input), ("eye", eye), ("lessonPanel", lessonPanel), ("lessonText", lessons), ("lessonMarker", marker.rectTransform), ("fade", fade),
            ("minigunIcon", HudSprite("DadsIcons/Minigun")), ("sunIcon", HudSprite("DadsHUD/sun")), ("moonIcon", HudSprite("DadsHUD/moon")),
            ("coneIcons", new Object[] { HudSprite("DadsIcons/Cone"), HudSprite("DadsIcons/WaffleCone"), HudSprite("DadsIcons/DoubleWaffleCone") }),
            ("scoopIcons", Treats.Select(t => t == null ? null : (Object)HudSprite($"DadsIcons/Scoop{t.Replace(" ", "")}")).ToArray()),
            ("moneyText", money), ("dayIcon", dayIcon), ("dayText", day), ("heatPanel", heatPanel.gameObject), ("heatBadges", badges),
            ("debtText", debt), ("debtFill", debtFill), ("dueText", due), ("strikeIcons", strikes), ("jinglePanel", jinglePanel.gameObject),
            ("speedPanel", speedPanel.gameObject), ("speedText", speed), ("truckPanel", truckPanel.gameObject), ("truckFill", truckFill),
            ("phaseBanner", banner.gameObject), ("phaseText", phase), ("tipText", tip), ("promptPanel", promptPanel.gameObject), ("promptText", prompt),
            ("slotIcons", slotIcons), ("slotBadges", slotBadges), ("slotCounts", slotCounts), ("slotSelected", slotSelected), ("selectedName", selectedName),
            ("ammoPanel", ammoPanel.gameObject), ("ammoIcon", ammoIcon), ("ammoText", ammo), ("ammoLabel", ammoLabel),
            ("controlsPanel", controls.gameObject), ("screenSplats", splats), ("coughTint", cough), ("frozenTint", frozen),
            ("card", cardGroup), ("cardTitle", cardTitle), ("cardBody", cardBody), ("cardStamp", cardStamp));
        var icons = new[]
        {
            (DadItem.ScoopPistol, "ScoopPistol"), (DadItem.SundaeShotgun, "SundaeShotgun"), (DadItem.MudBucket, "MudBucket"),
            (DadItem.StrawberryBasket, "StrawberryBasket"), (DadItem.IcedCoffee, "IcedCoffee"), (DadItem.NutSack, "NutSack"), (DadItem.GoldLeaf, "GoldLeaf"),
        };
        var serialized = new SerializedObject(hud);
        var list = serialized.FindProperty("icons");
        list.arraySize = icons.Length;
        for (int i = 0; i < icons.Length; i++)
        {
            list.GetArrayElementAtIndex(i).FindPropertyRelative("Kind").enumValueIndex = (int)icons[i].Item1;
            list.GetArrayElementAtIndex(i).FindPropertyRelative("Sprite").objectReferenceValue = HudSprite($"DadsIcons/{icons[i].Item2}");
        }
        serialized.ApplyModifiedPropertiesWithoutUndo();
        return hud;
    }

    // Nine-slice HUD frame from Sprites/DadsHUD, drawn at HudFrameScale.
    static RectTransform Panel(Transform parent, string name, string sprite, Vector2 anchor, Vector2 position, Vector2 size)
    {
        var image = HudImage(parent, name, $"DadsHUD/{sprite}", anchor, size);
        image.rectTransform.anchoredPosition = position;
        image.type = Image.Type.Sliced;
        image.pixelsPerUnitMultiplier = 1 / HudFrameScale;
        return image.rectTransform;
    }

    // Square icon centered vertically at x from the parent's left edge.
    static Image Icon(Transform parent, string name, string sprite, Vector2 position, float size)
    {
        var image = HudImage(parent, name, sprite, new Vector2(0, 0.5f), new Vector2(size, size));
        image.rectTransform.pivot = new Vector2(0.5f, 0.5f);
        image.rectTransform.anchoredPosition = position;
        image.preserveAspect = true;
        return image;
    }

    // Text filling the parent panel from left (px) to the right edge.
    static Text PanelText(Transform parent, string name, Font font, int size, Color color, float left, TextAnchor alignment)
    {
        var text = HudText(parent, name, font, new Vector2(0.5f, 0.5f), Vector2.zero, alignment, size, color);
        Stretch(text.rectTransform);
        text.rectTransform.offsetMin = new Vector2(left, 6);
        text.rectTransform.offsetMax = new Vector2(-10, -6);
        return text;
    }

    static Sprite HudSprite(string name)
    {
        var sprite = AssetDatabase.LoadAssetAtPath<Sprite>($"{Sprites}/{name}.png");
        if (sprite == null) throw new FileNotFoundException($"Missing HUD sprite {Sprites}/{name}.png; run hud_sprites_dads.py / hud_icons_dads.py");
        return sprite;
    }

    // Pixel fonts render hinted at their exact pixel size so they stay crisp at any HUD scale.
    static Font PixelFont(string name)
    {
        var path = $"{Fonts}/{name}.ttf";
        var importer = (TrueTypeFontImporter)AssetImporter.GetAtPath(path);
        if (importer.fontRenderingMode != FontRenderingMode.HintedRaster)
        {
            importer.fontRenderingMode = FontRenderingMode.HintedRaster;
            importer.SaveAndReimport();
        }
        return AssetDatabase.LoadAssetAtPath<Font>(path);
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
        image.sprite = HudSprite(sprite);
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
        // Press Start 2P runs twice as wide as a proportional font, so its glyphs are drawn at half size.
        mesh.characterSize = size * 0.5f;
        mesh.fontSize = 48;
        mesh.anchor = TextAnchor.MiddleCenter;
        mesh.alignment = TextAlignment.Center;
        mesh.font = PixelFont("PressStart2P-Regular");
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
