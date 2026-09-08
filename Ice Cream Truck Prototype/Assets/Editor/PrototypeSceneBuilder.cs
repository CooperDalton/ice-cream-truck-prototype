using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.UI;
using UnityEngine.EventSystems;
using UnityEngine.InputSystem.UI;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;
using Object = UnityEngine.Object;

public static class PrototypeSceneBuilder
{
    private const string ScenePath = "Assets/Scenes/IceCreamPrototype.unity";
    private static Dictionary<string, Transform> source;
    private static Dictionary<string, Material> materials;
    private static PrototypeSettingsSO settings;
    private static Font font;
    [Serializable] private class MaterialList { public MaterialData[] materials; }
    [Serializable] private class MaterialData { public string name; public float[] color; public float metallic; public float roughness; }

    // Names resolve the authored FBX once during assembly. Runtime references are serialized.
    private static Dictionary<string, Transform> Index(Transform root)
    {
        var map = new Dictionary<string,Transform>();
        foreach (var t in root.GetComponentsInChildren<Transform>(true)) if (!map.ContainsKey(t.name)) map.Add(t.name,t);
        return map;
    }
    public static GameObject ExtractModel(string name, Vector3 position)
    {
        source = Index(AssetDatabase.LoadAssetAtPath<GameObject>("Assets/Art/Workshop.fbx").transform);
        materials = AssetDatabase.FindAssets("t:Material", new[] { "Assets/Art/Materials" })
            .Select(id => AssetDatabase.LoadAssetAtPath<Material>(AssetDatabase.GUIDToAssetPath(id))).ToDictionary(m => m.name, m => m);
        return Model(name, position);
    }
    private static GameObject Model(string name, Vector3 position, Transform parent = null)
    {
        var wrapper = new GameObject(name.Replace("_ROOT", ""));
        wrapper.transform.SetParent(parent,false);
        wrapper.transform.position = position;
        var src=source[name];
        var visual=Object.Instantiate(src.gameObject,wrapper.transform);
        visual.name="Visual";
        visual.transform.localPosition=Vector3.zero;
        visual.transform.localRotation=src.rotation;
        visual.transform.localScale=src.lossyScale;
        var bones=Index(visual.transform);
        foreach(var skin in source.Values.Select(t=>t.GetComponent<SkinnedMeshRenderer>()).Where(r=>r!=null && r.bones.Any(b=>b!=null && b.IsChildOf(src))))
        {
            var mesh=Object.Instantiate(skin.gameObject,wrapper.transform);
            mesh.transform.localPosition=skin.transform.position-src.position;
            mesh.transform.localRotation=skin.transform.rotation;
            mesh.transform.localScale=skin.transform.lossyScale;
            var copy=mesh.GetComponent<SkinnedMeshRenderer>();
            copy.bones=skin.bones.Select(b=>bones[b.name]).ToArray();
            copy.rootBone=bones[skin.rootBone.name];
            copy.updateWhenOffscreen=true;
        }
        foreach(var r in wrapper.GetComponentsInChildren<Renderer>(true))
        {
            r.sharedMaterials=r.sharedMaterials.Select(m=>materials[m.name]).ToArray();
            r.shadowCastingMode=ShadowCastingMode.On;
        }
        foreach(var a in visual.GetComponentsInChildren<Animator>()) Object.DestroyImmediate(a);
        return wrapper;
    }
    private static Transform Point(string name, Vector3 position, Transform parent=null)
    {
        var point=new GameObject(name).transform;
        point.SetParent(parent,false); point.position=position;
        return point;
    }
    private static Bounds BoundsOf(GameObject o)
    {
        var rs=o.GetComponentsInChildren<Renderer>(true);
        Bounds bounds=rs[0].bounds;
        foreach(var r in rs) bounds.Encapsulate(r.bounds);
        return bounds;
    }
    private static BoxCollider Box(GameObject o, Vector3 center, Vector3 size)
    {
        var collider=o.AddComponent<BoxCollider>();
        collider.center=o.transform.InverseTransformPoint(center);
        collider.size=new Vector3(size.x/o.transform.lossyScale.x,size.y/o.transform.lossyScale.y,size.z/o.transform.lossyScale.z);
        return collider;
    }
    private static void StaticColliders(GameObject o)
    {
        foreach(var f in o.GetComponentsInChildren<MeshFilter>(true))
        {
            if(f.GetComponent<Collider>()!=null) continue;
            var c=f.gameObject.AddComponent<MeshCollider>(); c.sharedMesh=f.sharedMesh;
        }
    }
    private static GameObject Detach(Transform visual, string name)
    {
        var wrapper=new GameObject(name); wrapper.transform.position=visual.position;
        visual.SetParent(wrapper.transform,true);
        return wrapper;
    }
    private static T SetupTarget<T>(GameObject o, Vector3 center, Vector3 size) where T:Interactable
    {
        var target=o.AddComponent<T>();
        Box(o,center,size);
        target.highlightRenderers=o.GetComponentsInChildren<Renderer>(true);
        return target;
    }
    private static Material Material(string name, Color color)
    {
        var material=new Material(Shader.Find("Universal Render Pipeline/Lit"));
        material.name=name; material.SetColor("_BaseColor",color); material.SetFloat("_Smoothness",.25f); material.EnableKeyword("_EMISSION");
        AssetDatabase.CreateAsset(material,"Assets/Art/Materials/"+name+".mat");
        return material;
    }
    [MenuItem("Ice Cream/Build prototype scene")]
    public static void Build()
    {
        if (File.Exists(ScenePath)) throw new InvalidOperationException("Prototype exists. Edit the scene directly; rebuild only after preserving it.");
        var active=UnityEngine.SceneManagement.SceneManager.GetActiveScene();
        if(active.isDirty && !string.IsNullOrEmpty(active.path)) EditorSceneManager.SaveScene(active);
        Directory.CreateDirectory("Assets/Art/Materials");
        AssetDatabase.Refresh();
        var asset=AssetDatabase.LoadAssetAtPath<GameObject>("Assets/Art/Workshop.fbx");
        source=Index(asset.transform); materials=new Dictionary<string,Material>();
        var info=JsonUtility.FromJson<MaterialList>(File.ReadAllText("Assets/Art/WorkshopMaterials.json"));
        foreach(var d in info.materials)
        {
            var m=Material(d.name.Replace('/','_'),new Color(d.color[0],d.color[1],d.color[2],d.color[3]).gamma);
            m.SetFloat("_Metallic",d.metallic); m.SetFloat("_Smoothness",1-d.roughness);
            if(d.name.Contains("flat color texture")) { m.SetTexture("_BaseMap",AssetDatabase.LoadAssetAtPath<Texture2D>("Assets/Art/Textures/WaffleCone_BaseColor.png")); m.SetColor("_BaseColor",Color.white); }
            materials[d.name]=m;
            materials[d.name.Replace('/','_')]=m;
        }
        settings=ScriptableObject.CreateInstance<PrototypeSettingsSO>();
        AssetDatabase.CreateAsset(settings,"Assets/Settings/PrototypeSettings.asset");
        font=Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");
        var scene=EditorSceneManager.NewScene(NewSceneSetup.EmptyScene,NewSceneMode.Single);
        var systems=new GameObject("Prototype systems");
        var refs=systems.AddComponent<PrototypeSceneReferences>();
        var day=systems.AddComponent<DayManager>(); day.settings=settings; refs.day=day;
        var customers=systems.AddComponent<CustomerManager>(); customers.settings=settings; customers.day=day; refs.customers=customers;
        var player=MakePlayer(day); refs.player=player; refs.interaction=player.interaction;
        MakeEnvironment();
        var truck=Model("IceCreamTruck_ROOT",Vector3.zero);
        var parts=Index(truck.transform);
        // Remove display cones and route all usable equipment to independent roots.
        foreach(var name in new[]{"EmptyCone_ROOT.001","FinishedCone_ROOT.001","Cone_2Scoops_ROOT.001","Cone_3Scoops_ROOT.001"}) Object.DestroyImmediate(parts[name].gameObject);
        var burnt=Material("Burned waffle",new Color(.16f,.075f,.045f));
        var cone=MakeConePrefab();
        var waffleGO=Detach(parts["WaffleMaker_ROOT.001"],"Waffle maker");
        var waffle=SetupTarget<WaffleMaker>(waffleGO,waffleGO.transform.position+new Vector3(0,.18f,0),new Vector3(.61f,.42f,.60f));
        waffle.settings=settings; waffle.day=day; waffle.player=player.interaction; waffle.conePrefab=cone;
        waffle.lid=parts["Lid_HINGE • rotate local X.001"]; waffle.lid.localRotation=Quaternion.identity;
        waffle.rawBatter=Detach(parts["RawBatter_ROOT.001"],"Raw batter");
        waffle.cookedWaffle=Detach(parts["CookedWaffle_ROOT.001"],"Cooked waffle");
        waffle.waffleRenderers=waffle.cookedWaffle.GetComponentsInChildren<Renderer>();
        waffle.cookedMaterial=waffle.waffleRenderers[0].sharedMaterial; waffle.burnedMaterial=burnt;
        waffle.rawBatter.SetActive(false); waffle.cookedWaffle.SetActive(false);
        refs.waffle=waffle;
        refs.batter=MakeTool(parts["BatterBottle_ROOT.001"],PickupItem.ItemKind.Batter,"batter bottle");
        refs.scooper=MakeTool(parts["Scooper_ROOT.001"],PickupItem.ItemKind.Scooper,"scooper");
        refs.shaker=MakeTool(parts["SprinkleShaker_ROOT.001"],PickupItem.ItemKind.Sprinkles,"sprinkle shaker");
        var scoop=Model("Cone3_Scoop01_ROOT",refs.scooper.transform.position,refs.scooper.transform);
        scoop.transform.position=parts["HeldScoop_SOCKET.001"].position;
        refs.scooper.loadedScoop=scoop; refs.scooper.loadedScoopRenderer=scoop.GetComponentInChildren<Renderer>(); scoop.SetActive(false);
        var flavors=new List<FlavorSO>(); var tubs=new List<IceCreamTub>();
        string[] names={"Strawberry","Vanilla","Chocolate","Mint","Blueberry","Mango","Cherry","Cookie cream","Coffee","Pistachio","Blue moon","Peach"};
        for(int i=0;i<12;i++)
        {
            var tub=parts["Tub_"+(i/6+1)+"_"+(i%6+1)+"_"+names[i]+".001"];
            var fill=parts["IceCream_Fill • "+(i+1)+".001"].GetComponentInChildren<Renderer>();
            var flavor=ScriptableObject.CreateInstance<FlavorSO>(); flavor.displayName=names[i]; flavor.material=fill.sharedMaterial; flavor.color=fill.sharedMaterial.GetColor("_BaseColor");
            AssetDatabase.CreateAsset(flavor,"Assets/Settings/"+names[i]+".asset"); flavors.Add(flavor);
            var go=Detach(tub,names[i]+" tub");
            var target=SetupTarget<IceCreamTub>(go,go.transform.position+Vector3.up*.035f,new Vector3(.36f,.12f,.30f));target.settings=settings; target.flavor=flavor; tubs.Add(target);
            WorldLabel(names[i],go.transform.position+new Vector3(0,.10f,-.03f),new Vector3(70,0,0),.013f);
        }
        customers.flavors=flavors.ToArray(); refs.tubs=tubs.ToArray();
        var holders=new List<ConeHolder>();
        for(int i=0;i<6;i++)
        {
            var holder=parts["ConeHolder_"+(i+1)+".001"];
            var go=Detach(holder,"Cone holder "+(i+1)); var b=BoundsOf(go);
            var target=SetupTarget<ConeHolder>(go,new Vector3(b.center.x,b.min.y+.07f,b.center.z),new Vector3(.13f,.14f,.13f));
            target.socket=Point("Cone placement",new Vector3(b.center.x,1.556f,b.center.z));
            holders.Add(target);
        }
        refs.holders=holders.ToArray();
        StaticColliders(truck);
        var counter=new GameObject("Counter placement surface");
        var surface=SetupTarget<PlacementSurface>(counter,new Vector3(-1.35f,1.521f,-.75f),new Vector3(2.65f,.025f,.22f));
        surface.highlightRenderers=Array.Empty<Renderer>();
        var floor=new GameObject("Interior walkable floor");Box(floor,new Vector3(-.6f,.565f,0),new Vector3(5.8f,.10f,3.65f));
        var bin=Model("Park_TrashBin_ROOT",new Vector3(-3.1f,.62f,.9f));
        var bb=BoundsOf(bin);refs.bin=SetupTarget<DiscardBin>(bin,bb.center,bb.size);
        MakeCustomers(customers);
        var hud=MakeHUD(day,customers,waffle);refs.hud=hud;player.interaction.hud=hud;
        EditorSceneManager.MarkSceneDirty(scene);
        EditorSceneManager.SaveScene(scene,ScenePath);
        EditorBuildSettings.scenes=new[]{new EditorBuildSettingsScene(ScenePath,true)};
        AssetDatabase.SaveAssets();
        PrototypeSceneRefinement.Apply();
        PrototypeVisualPolish.Apply();
        PrototypeFinalLayout.Apply();
        Selection.activeObject=settings;
        Debug.Log("Prototype scene built with twelve infinite tubs, six holders, customers, and editable day settings.");
    }
    private static PlayerController MakePlayer(DayManager day)
    {
        var go=new GameObject("Player");go.layer=8;go.transform.position=new Vector3(-1.1f,.68f,.05f);go.transform.rotation=Quaternion.Euler(0,180,0);
        var p=go.AddComponent<PlayerController>();p.settings=settings;p.day=day;
        p.controller=go.AddComponent<CharacterController>();p.controller.height=1.65f;p.controller.radius=.23f;p.controller.center=new Vector3(0,.825f,0);p.controller.stepOffset=.2f;p.controller.skinWidth=.025f;
        var camera=new GameObject("First person camera");camera.transform.SetParent(go.transform,false);camera.transform.localPosition=new Vector3(0,1.55f,0);p.view=camera.AddComponent<Camera>();p.view.nearClipPlane=.035f;p.view.farClipPlane=150;p.view.fieldOfView=settings.fieldOfView;p.view.tag="MainCamera";camera.AddComponent<AudioListener>();
        var data=p.view.GetUniversalAdditionalCameraData();data.renderPostProcessing=true;
        var interaction=go.AddComponent<PlayerInteraction>();p.interaction=interaction;interaction.settings=settings;interaction.day=day;interaction.view=p.view;
        interaction.handAnchor=Point("Carried item",Vector3.zero,camera.transform);interaction.handAnchor.localPosition=new Vector3(.26f,-.36f,.57f);
        var hands=Model("FirstPersonHands_ROOT",Vector3.zero,camera.transform);hands.transform.localPosition=new Vector3(0,-.45f,.55f);hands.transform.localRotation=Quaternion.Euler(0,180,0);hands.transform.localScale=Vector3.one*.5f;
        interaction.rightHand=hands.transform;
        foreach(var t in hands.GetComponentsInChildren<Transform>()) t.gameObject.layer=2;
        interaction.audioSource=go.AddComponent<AudioSource>();interaction.audioSource.playOnAwake=false;
        interaction.pickupSound=AssetDatabase.LoadAssetAtPath<AudioClip>("Assets/Audio/Pickup.wav");interaction.actionSound=AssetDatabase.LoadAssetAtPath<AudioClip>("Assets/Audio/Action.wav");interaction.readySound=AssetDatabase.LoadAssetAtPath<AudioClip>("Assets/Audio/Ready.wav");interaction.saleSound=AssetDatabase.LoadAssetAtPath<AudioClip>("Assets/Audio/Sale.wav");interaction.errorSound=AssetDatabase.LoadAssetAtPath<AudioClip>("Assets/Audio/Error.wav");interaction.pourSound=AssetDatabase.LoadAssetAtPath<AudioClip>("Assets/Audio/Pour.wav");interaction.scoopSound=AssetDatabase.LoadAssetAtPath<AudioClip>("Assets/Audio/Scoop.wav");interaction.sprinkleSound=AssetDatabase.LoadAssetAtPath<AudioClip>("Assets/Audio/Sprinkle.wav");
        return p;
    }
    private static PickupItem MakeTool(Transform visual, PickupItem.ItemKind kind, string name)
    {
        var go=Detach(visual,name);var b=BoundsOf(go);
        var item=SetupTarget<PickupItem>(go,b.center,Vector3.Max(b.size,new Vector3(.12f,.12f,.12f)));
        item.kind=kind;item.displayName=name;item.pickupCollider=go.GetComponent<Collider>();item.home=Point(name+" home",go.transform.position);item.heldOffset=Vector3.zero;
        return item;
    }
    private static IceCreamCone MakeConePrefab()
    {
        var go=Model("EmptyCone_ROOT",Vector3.zero);go.name="Ice cream cone";
        var cone=SetupTarget<IceCreamCone>(go,new Vector3(0,.24f,0),new Vector3(.23f,.50f,.23f));cone.kind=PickupItem.ItemKind.Cone;cone.displayName="ice cream cone";cone.settings=settings;cone.pickupCollider=go.GetComponent<Collider>();
        cone.scoopVisuals=new GameObject[3];cone.scoopRenderers=new Renderer[3];cone.toppingVisuals=new GameObject[3];
        var sprinkleMaterials=new[]{Material("Sprinkle pink",new Color(1,.3f,.55f)),Material("Sprinkle yellow",new Color(1,.85f,.2f)),Material("Sprinkle blue",new Color(.25f,.8f,1))};
        for(int i=0;i<3;i++)
        {
            var scoop=Model("Cone3_Scoop01_ROOT",new Vector3(0,.201f+i*.12f,0),go.transform);
            cone.scoopVisuals[i]=scoop;cone.scoopRenderers[i]=scoop.GetComponentInChildren<Renderer>();
            var topping=new GameObject("Sprinkles "+(i+1));topping.transform.SetParent(go.transform,false);
            for(int j=0;j<18;j++)
            {
                float angle=j*2.39996f;float radius=.067f*Mathf.Sqrt((j+.5f)/18f);
                var sprinkle=GameObject.CreatePrimitive(PrimitiveType.Cube);sprinkle.name="Sprinkle";Object.DestroyImmediate(sprinkle.GetComponent<Collider>());sprinkle.transform.SetParent(topping.transform,false);sprinkle.transform.localPosition=new Vector3(Mathf.Cos(angle)*radius,.219f+i*.12f+Mathf.Sqrt(.075f*.075f-radius*radius),Mathf.Sin(angle)*radius);sprinkle.transform.localScale=new Vector3(.016f,.005f,.005f);sprinkle.transform.localRotation=Quaternion.Euler(j*17,j*39,j*21);sprinkle.GetComponent<Renderer>().sharedMaterial=sprinkleMaterials[j%3];
            }
            cone.toppingVisuals[i]=topping;topping.SetActive(false);scoop.SetActive(false);
        }
        var prefab=PrefabUtility.SaveAsPrefabAsset(go,"Assets/Prefabs/IceCreamCone.prefab").GetComponent<IceCreamCone>();Object.DestroyImmediate(go);return prefab;
    }
    private static void MakeEnvironment()
    {
        var road=Model("Road_Straight_ROOT",new Vector3(0,-.05f,0));StaticColliders(road);
        var park=Model("Park_Cell_ROOT",new Vector3(0,-.05f,24));StaticColliders(park);
        for(int i=0;i<4;i++)
        {
            string[] houses={"House_Cottage_ROOT","House_Townhouse_ROOT","House_Bungalow_ROOT","House_Family_ROOT"};
            var house=Model(houses[i],new Vector3(-15+i*10,0,-17));house.transform.rotation=Quaternion.Euler(0,180,0);StaticColliders(house);
            Model(i%2==0?"Tree_Broadoak_ROOT":"Tree_Roundmaple_ROOT",new Vector3(-10+i*7,0,-10));
        }
        var ground=GameObject.CreatePrimitive(PrimitiveType.Cube);ground.name="Neighborhood ground";ground.transform.position=new Vector3(0,-.24f,0);ground.transform.localScale=new Vector3(100,.2f,100);ground.GetComponent<Renderer>().sharedMaterial=materials["Town kit • Grass"];
        var sun=new GameObject("Afternoon sunlight").AddComponent<Light>();sun.type=LightType.Directional;sun.transform.rotation=Quaternion.Euler(45,-35,0);sun.intensity=1.5f;sun.shadows=LightShadows.Soft;
        var fill=new GameObject("Truck interior fill").AddComponent<Light>();fill.type=LightType.Point;fill.transform.position=new Vector3(-1.2f,2.8f,0);fill.range=6;fill.intensity=2;fill.color=new Color(1,.91f,.78f);
        RenderSettings.ambientMode=AmbientMode.Flat;RenderSettings.ambientLight=new Color(.6f,.65f,.73f);RenderSettings.fog=true;RenderSettings.fogColor=new Color(.68f,.82f,.87f);RenderSettings.fogMode=FogMode.Linear;RenderSettings.fogStartDistance=40;RenderSettings.fogEndDistance=100;
        var sky=new Material(Shader.Find("Skybox/Procedural"));sky.SetColor("_SkyTint",new Color(.65f,.8f,.94f));sky.SetFloat("_AtmosphereThickness",.6f);AssetDatabase.CreateAsset(sky,"Assets/Art/Materials/Prototype sky.mat");RenderSettings.skybox=sky;
    }
    private static void MakeCustomers(CustomerManager manager)
    {
        var list=new List<Customer>();
        foreach(var name in new[]{"Adult_ROOT","Child_ROOT","AdultVariant_ROOT","ChildVariant_ROOT"})
        {
            var go=Model(name,Vector3.zero);go.name=name.Replace("_ROOT", " customer");
            var b=BoundsOf(go);var customer=SetupTarget<Customer>(go,new Vector3(0,1.2f,0),new Vector3(.8f,2.4f,.7f));
            customer.appearance=go.transform.GetChild(0);customer.interactionCollider=go.GetComponent<Collider>();
            var renderers=go.GetComponentsInChildren<Renderer>();
            customer.shirt=renderers.First(r=>r.sharedMaterials.Any(m=>m.name.Contains("Clothes")));
            list.Add(PrefabUtility.SaveAsPrefabAsset(go,"Assets/Prefabs/"+name+".prefab").GetComponent<Customer>());Object.DestroyImmediate(go);
        }
        manager.customerPrefabs=list.ToArray();
        manager.spawnPoint=Point("Customer arrival",new Vector3(-8,0,3.6f));
        manager.exitPoint=Point("Customer departure",new Vector3(10,0,4.8f));
        manager.serviceLookPoint=Point("Service window",new Vector3(-1.1f,1.8f,1.3f));
        manager.queuePoints=new Transform[4];
        for(int i=0;i<4;i++) manager.queuePoints[i]=Point("Queue "+(i+1),new Vector3(-1.1f-i*1.2f,0,2.85f));
    }
    private static Text WorldLabel(string value,Vector3 position,Vector3 rotation,float scale)
    {
        var canvas=new GameObject(value+" label",typeof(RectTransform),typeof(Canvas));canvas.GetComponent<Canvas>().renderMode=RenderMode.WorldSpace;canvas.transform.position=position;canvas.transform.rotation=Quaternion.Euler(rotation);canvas.transform.localScale=Vector3.one*scale;
        var rt=(RectTransform)canvas.transform;rt.sizeDelta=new Vector2(28,9);
        var text=TextElement(canvas.transform,"Flavor",value,12,new Vector2(0,0),new Vector2(28,9),TextAnchor.MiddleCenter);text.color=new Color(.16f,.12f,.19f);text.resizeTextForBestFit=true;text.resizeTextMinSize=7;
        return text;
    }
    private static RectTransform Rect(Transform parent,string name,Vector2 position,Vector2 size)
    {
        var rt=new GameObject(name,typeof(RectTransform)).GetComponent<RectTransform>();rt.SetParent(parent,false);rt.anchorMin=rt.anchorMax=new Vector2(.5f,.5f);rt.anchoredPosition=position;rt.sizeDelta=size;return rt;
    }
    private static Image Panel(Transform parent,string name,Vector2 pos,Vector2 size,Color color)
    {
        var rt=Rect(parent,name,pos,size);var image=rt.gameObject.AddComponent<Image>();image.color=color;image.raycastTarget=false;return image;
    }
    private static Text TextElement(Transform parent,string name,string value,int fontSize,Vector2 pos,Vector2 size,TextAnchor align=TextAnchor.MiddleLeft)
    {
        var rt=Rect(parent,name,pos,size);var text=rt.gameObject.AddComponent<Text>();text.font=font;text.text=value;text.fontSize=fontSize;text.color=new Color(.98f,.96f,.91f);text.alignment=align;text.raycastTarget=false;return text;
    }
    private static Button ButtonElement(Transform parent,string name,string label,Vector2 pos)
    {
        var background=Panel(parent,name,pos,new Vector2(270,54),new Color(.78f,.29f,.44f));background.raycastTarget=true;
        var button=background.gameObject.AddComponent<Button>();button.targetGraphic=background;
        TextElement(background.transform,"Label",label,21,Vector2.zero,new Vector2(260,48),TextAnchor.MiddleCenter);return button;
    }
    private static PrototypeHUD MakeHUD(DayManager day,CustomerManager customers,WaffleMaker waffle)
    {
        var canvas=new GameObject("Prototype HUD",typeof(RectTransform),typeof(Canvas),typeof(CanvasScaler),typeof(GraphicRaycaster));canvas.GetComponent<Canvas>().renderMode=RenderMode.ScreenSpaceOverlay;
        var scaler=canvas.GetComponent<CanvasScaler>();scaler.uiScaleMode=CanvasScaler.ScaleMode.ScaleWithScreenSize;scaler.referenceResolution=new Vector2(1600,900);scaler.matchWidthOrHeight=0;
        var hud=canvas.AddComponent<PrototypeHUD>();hud.day=day;hud.customers=customers;hud.waffle=waffle;
        Color dark=new Color(.12f,.10f,.17f,.93f),mint=new Color(.44f,.84f,.68f);
        var top=Panel(canvas.transform,"Day status",new Vector2(-535,376),new Vector2(470,96),dark);
        TextElement(top.transform,"Title","ICE CREAM TRUCK",16,new Vector2(-20,26),new Vector2(380,25));
        hud.clockText=TextElement(top.transform,"Clock","8:00 AM",28,new Vector2(-95,-10),new Vector2(230,42));
        hud.moneyText=TextElement(top.transform,"Money","$0 / $100",25,new Vector2(118,-10),new Vector2(200,42));
        hud.quotaFill=Panel(top.transform,"Quota progress",new Vector2(0,-40),new Vector2(438,5),mint);hud.quotaFill.type=Image.Type.Filled;hud.quotaFill.fillMethod=Image.FillMethod.Horizontal;
        var order=Panel(canvas.transform,"Customer order",new Vector2(555,309),new Vector2(430,230),dark);
        TextElement(order.transform,"Title","NEXT ORDER",17,new Vector2(-55,87),new Vector2(275,30));
        hud.queueText=TextElement(order.transform,"Queue","0 in line",16,new Vector2(125,87),new Vector2(120,30),TextAnchor.MiddleRight);
        hud.orderText=TextElement(order.transform,"Recipe","A customer will be here soon",23,new Vector2(0,8),new Vector2(386,130));
        hud.patienceFill=Panel(order.transform,"Patience",new Vector2(0,-88),new Vector2(386,7),mint);hud.patienceFill.type=Image.Type.Filled;hud.patienceFill.fillMethod=Image.FillMethod.Horizontal;
        hud.waffleText=TextElement(canvas.transform,"Waffle status","WAFFLE EMPTY",17,new Vector2(-555,292),new Vector2(430,36));
        var bottom=Panel(canvas.transform,"Interaction prompt",new Vector2(0,-329),new Vector2(860,66),dark);
        hud.promptText=TextElement(bottom.transform,"Prompt","Look at the waffle maker",22,Vector2.zero,new Vector2(828,60),TextAnchor.MiddleCenter);
        hud.heldText=TextElement(canvas.transform,"Held item","Hands free",17,new Vector2(0,-387),new Vector2(800,34),TextAnchor.MiddleCenter);
        hud.messageText=TextElement(canvas.transform,"Feedback","",23,new Vector2(0,-228),new Vector2(1100,66),TextAnchor.MiddleCenter);
        TextElement(canvas.transform,"Controls","WASD  Walk     Mouse  Look\nClick  Grab / use     Right click  Put down\nHold + move mouse  Scoop / shake     Esc  Pause",16,new Vector2(-505,-407),new Vector2(530,75));
        var dot=Panel(canvas.transform,"Crosshair",Vector2.zero,new Vector2(5,5),Color.white);
        // A ring sprite is authored once and saved with the scene.
        var tex=new Texture2D(64,64,TextureFormat.RGBA32,false);for(int y=0;y<64;y++)for(int x=0;x<64;x++){float d=Vector2.Distance(new Vector2(x+.5f,y+.5f),new Vector2(32,32));tex.SetPixel(x,y,d>25 && d<30?Color.white:Color.clear);}tex.Apply();File.WriteAllBytes("Assets/Art/ProgressRing.png",tex.EncodeToPNG());Object.DestroyImmediate(tex);AssetDatabase.ImportAsset("Assets/Art/ProgressRing.png");var importer=(TextureImporter)AssetImporter.GetAtPath("Assets/Art/ProgressRing.png");importer.textureType=TextureImporterType.Sprite;importer.spriteImportMode=SpriteImportMode.Single;importer.alphaIsTransparency=true;importer.SaveAndReimport();
        hud.progressRing=Panel(canvas.transform,"Gesture progress",Vector2.zero,new Vector2(54,54),mint);hud.progressRing.sprite=AssetDatabase.LoadAllAssetsAtPath("Assets/Art/ProgressRing.png").OfType<Sprite>().Single();hud.progressRing.type=Image.Type.Filled;hud.progressRing.fillMethod=Image.FillMethod.Radial360;hud.progressRing.fillOrigin=2;hud.progressRing.fillAmount=0;
        hud.pausePanel=Panel(canvas.transform,"Pause",Vector2.zero,new Vector2(1600,900),new Color(.09f,.07f,.13f,.95f)).gameObject;
        TextElement(hud.pausePanel.transform,"Title","TAKE A BREATHER",38,new Vector2(0,185),new Vector2(850,70),TextAnchor.MiddleCenter);
        TextElement(hud.pausePanel.transform,"Instructions","Open the iron. Pour batter. Close and cook.\nTake the cone and place it in a holder.\nScoop flavors, add sprinkles, and serve the next customer.\n\nIngredients are unlimited. Close at 6 PM.",23,new Vector2(0,25),new Vector2(900,230),TextAnchor.MiddleCenter);
        hud.resumeButton=ButtonElement(hud.pausePanel.transform,"Resume","RESUME",new Vector2(0,-154));hud.restartButton=ButtonElement(hud.pausePanel.transform,"Restart","RESTART DAY",new Vector2(0,-225));hud.pausePanel.SetActive(false);
        hud.resultPanel=Panel(canvas.transform,"Day results",Vector2.zero,new Vector2(1600,900),new Color(.09f,.07f,.13f,.97f)).gameObject;
        hud.resultText=TextElement(hud.resultPanel.transform,"Result","",32,new Vector2(0,65),new Vector2(950,320),TextAnchor.MiddleCenter);hud.retryButton=ButtonElement(hud.resultPanel.transform,"Play again","PLAY AGAIN",new Vector2(0,-180));hud.resultPanel.SetActive(false);
        var events=new GameObject("UI input",typeof(EventSystem),typeof(InputSystemUIInputModule));
        return hud;
    }
}
