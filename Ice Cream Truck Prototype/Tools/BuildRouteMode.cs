using System;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEditor.Events;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.InputSystem.UI;
using UnityEngine.SceneManagement;
using UnityEngine.UI;
using Object = UnityEngine.Object;

public static class BuildRouteMode
{
    static readonly Color cream = new Color(1,.98f,.92f), ink = new Color(.14f,.27f,.26f), mint = new Color(.25f,.65f,.5f), coral = new Color(.93f,.42f,.48f), gold = new Color(1,.79f,.32f), pale = new Color(.87f,.93f,.84f);
    static Sprite panel, circle;
    static Font font;
    static void Assets()
    {
        panel = AssetDatabase.LoadAssetAtPath<Sprite>("Assets/Art/UI/Soft panel.png");
        circle = AssetDatabase.LoadAssetAtPath<Sprite>("Assets/Art/UI/Circle.png");
        font = Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");
    }
    static RectTransform Rect(Transform parent, string name, Vector2 position, Vector2 size)
    {
        var rt = new GameObject(name, typeof(RectTransform)).GetComponent<RectTransform>(); rt.SetParent(parent,false);
        rt.anchoredPosition = position; rt.sizeDelta = size; return rt;
    }
    static Image Image(Transform parent, string name, Vector2 pos, Vector2 size, Color color, Sprite sprite = null)
    {
        var im = Rect(parent,name,pos,size).gameObject.AddComponent<Image>();
        im.sprite = sprite == null ? panel : sprite; im.type = sprite == null ? UnityEngine.UI.Image.Type.Sliced : UnityEngine.UI.Image.Type.Simple;
        im.color = color; im.raycastTarget = false; return im;
    }
    static Text Text(Transform parent, string name, string caption, Vector2 pos, Vector2 size, int sizeText = 22, TextAnchor align = TextAnchor.MiddleLeft)
    {
        var t = Rect(parent,name,pos,size).gameObject.AddComponent<Text>(); t.font = font; t.fontSize = sizeText;
        t.text = caption; t.color = ink; t.alignment = align; t.raycastTarget = false;
        t.horizontalOverflow = HorizontalWrapMode.Wrap; t.verticalOverflow = VerticalWrapMode.Truncate;
        return t;
    }
    static Button Button(Transform parent, string name, string caption, Vector2 pos, Vector2 size, Color color, int sizeText = 22)
    {
        var im = Image(parent,name,pos,size,color); im.raycastTarget = true;
        var b = im.gameObject.AddComponent<Button>(); b.targetGraphic = im;
        var label = Text(b.transform,"Label",caption,Vector2.zero,size-Vector2.one*8,sizeText,TextAnchor.MiddleCenter);
        label.fontStyle = FontStyle.Bold;
        return b;
    }
    static Canvas Canvas(string name)
    {
        var c = new GameObject(name,typeof(RectTransform),typeof(Canvas),typeof(CanvasScaler),typeof(GraphicRaycaster)).GetComponent<Canvas>();
        c.renderMode = RenderMode.ScreenSpaceOverlay;
        var scaler = c.GetComponent<CanvasScaler>(); scaler.uiScaleMode = CanvasScaler.ScaleMode.ScaleWithScreenSize;
        scaler.referenceResolution = new Vector2(1600,900); scaler.matchWidthOrHeight = .5f;
        return c;
    }
    static GameObject Primitive(Transform parent, string name, PrimitiveType type, Vector3 pos, Vector3 scale, Material mat, int layer = 11)
    {
        var go = GameObject.CreatePrimitive(type); go.name=name; go.transform.SetParent(parent,false);
        go.transform.localPosition=pos; go.transform.localScale=scale; go.layer=layer;
        go.GetComponent<Renderer>().sharedMaterial=mat; return go;
    }
    static Material Mat(string name, Color color)
    {
        var mat = new Material(Shader.Find("Universal Render Pipeline/Lit")); mat.name=name; mat.color=color;
        AssetDatabase.CreateAsset(mat,"Assets/Art/Materials/"+name+".mat"); return mat;
    }
    public static string CreateRoute()
    {
        Assets();
        if (File.Exists("Assets/Scenes/ParkRoute.unity")) throw new InvalidOperationException("ParkRoute already exists.");
        if (SceneManager.GetActiveScene().isDirty) EditorSceneManager.SaveScene(SceneManager.GetActiveScene());
        var scene = EditorSceneManager.OpenScene("Assets/Scenes/IceCreamPrototype.unity");
        EditorSceneManager.SaveScene(scene,"Assets/Scenes/ParkRoute.unity");
        var r = PrototypeSceneReferences.Instance;
        var oldSettings = r.day.settings;
        var settings = Object.Instantiate(oldSettings); settings.name="ParkRouteSettings"; settings.tileSize=120; settings.randomizeWorldSeed=false;
        settings.cookSeconds=4; settings.pourSeconds=1.1f;
        AssetDatabase.CreateAsset(settings,"Assets/Settings/ParkRouteSettings.asset");
        foreach (var root in scene.GetRootGameObjects()) foreach (var behaviour in root.GetComponentsInChildren<MonoBehaviour>(true))
        {
            if (behaviour == null) continue;
            var serialized = new SerializedObject(behaviour); var property = serialized.FindProperty("settings");
            if (property != null && property.propertyType==SerializedPropertyType.ObjectReference && property.objectReferenceValue==oldSettings)
            { property.objectReferenceValue=settings; serialized.ApplyModifiedPropertiesWithoutUndo(); }
        }
        r.world.generateOnAwake=false; r.world.enabled=false; r.customers.enabled=false;
        r.hud.enabled=false; foreach(Transform child in r.hud.transform) child.gameObject.SetActive(false);
        r.boombox.gameObject.SetActive(false);
        var route = r.gameObject.AddComponent<RouteGameManager>(); r.route=route;
        route.day=r.day; r.day.route=route; route.truck=r.truck; r.truck.automaticRoute=true;
        route.player=r.player; route.interaction=r.interaction; route.navigation=r.world;
        route.waffle=r.waffle; route.holders=r.holders; route.queuePoints=r.customers.queuePoints;
        var stock=r.gameObject.AddComponent<RouteStock>(); route.stock=stock; stock.route=route; r.interaction.stock=stock;
        stock.flavors=new[]{"Vanilla","Chocolate","Strawberry"}.Select(n=>AssetDatabase.LoadAssetAtPath<FlavorSO>("Assets/Settings/"+n+".asset")).ToArray();
        foreach(var tub in r.tubs) if(!stock.flavors.Contains(tub.flavor)) tub.gameObject.SetActive(false);
        var world = new GameObject("Park route world").transform;
        var grass=Mat("Route grass",new Color(.44f,.64f,.43f)); var asphalt=Mat("Route path",new Color(.39f,.47f,.5f));
        var paint=Mat("Route markings",new Color(.99f,.9f,.66f));
        Primitive(world,"Park ground",PrimitiveType.Cube,new Vector3(80,-.2f,30),new Vector3(340,.3f,190),grass);
        Vector3[] path={new Vector3(0,0,0),new Vector3(180,0,0),new Vector3(180,0,60),new Vector3(-30,0,60)};
        route.path=new Transform[path.Length];
        for(int i=0;i<path.Length;i++)
        {
            var t=new GameObject("Route waypoint "+i).transform; t.SetParent(world,false); t.localPosition=path[i]; route.path[i]=t;
            if(i==0)continue;
            Vector3 offset=path[i]-path[i-1]; var mid=(path[i]+path[i-1])*.5f;
            Primitive(world,"Park road "+i,PrimitiveType.Cube,mid+Vector3.down*.035f,new Vector3(Mathf.Abs(offset.x)+12,.07f,Mathf.Abs(offset.z)+12),asphalt);
            for(float distance=4;distance<offset.magnitude;distance+=8)
                Primitive(world,"Route dash",PrimitiveType.Cube,path[i-1]+offset.normalized*distance+Vector3.up*.006f,Mathf.Abs(offset.x)>1?new Vector3(3,.01f,.12f):new Vector3(.12f,.01f,3),paint);
        }
        route.points=new[]{new RouteGameManager.RoutePoint{label="A",distance=42},new RouteGameManager.RoutePoint{label="B",distance=105},new RouteGameManager.RoutePoint{label="C",distance=165},new RouteGameManager.RoutePoint{label="D",distance=225},new RouteGameManager.RoutePoint{label="E",distance=300},new RouteGameManager.RoutePoint{label="F",distance=365}};
        var prefabs=CreateCustomers(r);
        Vector3[] locations={new Vector3(45,0,15),new Vector3(102,0,-16),new Vector3(165,0,18),new Vector3(164,0,80),new Vector3(104,0,83),new Vector3(35,0,77)};
        float[] near={45,102,165,256,316,385};
        route.hotspots=new RouteHotspot[6];
        for(int i=0;i<6;i++)
        {
            var go=new GameObject("Hotspot "+(i+1));go.transform.SetParent(world,false);go.transform.localPosition=locations[i];
            var h=go.AddComponent<RouteHotspot>(); h.route=route;h.customerPrefabs=prefabs;h.routeDistance=near[i];route.hotspots[i]=h;
            var marker=Primitive(go.transform,"Crowd clearing",PrimitiveType.Cylinder,new Vector3(0,-.015f,0),new Vector3(12,.02f,12),paint);
            Object.DestroyImmediate(marker.GetComponent<Collider>());
            var bench=PrototypeSceneBuilder.ExtractModel("Picnic_Table_ROOT",locations[i]+new Vector3(5,0,3));bench.transform.SetParent(world,true);
            foreach(var filter in bench.GetComponentsInChildren<MeshFilter>()) { filter.gameObject.layer=10;var col=filter.gameObject.AddComponent<MeshCollider>();col.sharedMesh=filter.sharedMesh; }
            for(int t=0;t<3;t++) Object.Instantiate(r.world.trees[t%r.world.trees.Length],locations[i]+new Vector3(-8+t*8,0,10),Quaternion.identity,world);
        }
        CreateTray(r,route);
        route.cashPouch=Primitive(r.player.transform,"Carried cash pouch",PrimitiveType.Cube,new Vector3(-.3f,.8f,-.1f),new Vector3(.22f,.2f,.1f),paint,2);
        Object.DestroyImmediate(route.cashPouch.GetComponent<Collider>());
        var nav=r.gameObject.AddComponent<GameModeMenu>();
        CreateHUD(route,nav); r.hud.routeHUD=route.hud;
        EditorSceneManager.MarkSceneDirty(scene); EditorSceneManager.SaveScene(scene);AssetDatabase.SaveAssets();
        return "Saved ParkRoute scene, finite stock, park, customer prefabs, tray, and planning UI.";
    }
    static RouteCustomer[] CreateCustomers(PrototypeSceneReferences r)
    {
        var result=new RouteCustomer[2];
        for(int i=0;i<2;i++)
        {
            var go=PrefabUtility.LoadPrefabContents(AssetDatabase.GetAssetPath(r.customers.customerPrefabs[i]));
            try
            {
                var old=go.GetComponent<Customer>();var bubble=go.GetComponentInChildren<OrderBubble>(true);
                var customer=go.AddComponent<RouteCustomer>();
                customer.appearance=old.appearance;customer.shirt=old.shirt;customer.interactionCollider=old.interactionCollider;customer.servingStep=old.servingStep;
                customer.highlightRenderers=old.highlightRenderers;customer.bubble=bubble.transform;customer.orderPanel=bubble.panel;
                customer.scoopPictures=bubble.scoops;customer.sprinkles=bubble.sprinkles;customer.patience=bubble.patience;
                Object.DestroyImmediate(bubble);Object.DestroyImmediate(old);
                var prefab=PrefabUtility.SaveAsPrefabAsset(go,"Assets/Prefabs/Route"+(i==0?"Adult":"Child")+".prefab");result[i]=prefab.GetComponent<RouteCustomer>();
            }
            finally{PrefabUtility.UnloadPrefabContents(go);}
        }
        return result;
    }
    static void CreateTray(PrototypeSceneReferences r,RouteGameManager route)
    {
        var go=new GameObject("Serving tray");go.transform.SetParent(r.truck.transform,false);go.transform.localPosition=new Vector3(-.85f,1.5f,.95f);
        var mat=AssetDatabase.LoadAssetAtPath<Material>("Assets/Art/Materials/Enamel • mint.003.mat");
        var platter=Primitive(go.transform,"Mint tray",PrimitiveType.Cylinder,Vector3.zero,new Vector3(.63f,.025f,.34f),mat,9);Object.DestroyImmediate(platter.GetComponent<Collider>());
        var tray=go.AddComponent<ServingTray>();route.tray=tray;tray.kind=PickupItem.ItemKind.Tray;tray.displayName="serving tray";
        var collider=go.AddComponent<BoxCollider>();collider.size=new Vector3(.63f,.16f,.34f);tray.pickupCollider=collider;go.layer=9;
        tray.highlightRenderers=new[]{platter.GetComponent<Renderer>()};tray.heldOffset=new Vector3(-.12f,-.14f,.18f);
        var home=new GameObject("Tray home").transform;home.SetParent(r.truck.transform,false);home.localPosition=go.transform.localPosition;tray.home=home;
        tray.slots=new Transform[3];
        for(int i=0;i<3;i++){var slot=new GameObject("Cone slot "+i).transform;slot.SetParent(go.transform,false);slot.localPosition=new Vector3((i-1)*.19f,.035f,0);tray.slots[i]=slot;}
    }
    static void CreateHUD(RouteGameManager route,GameModeMenu nav)
    {
        var canvas=Canvas("Route HUD");var h=canvas.gameObject.AddComponent<RouteHUD>();h.route=route;route.hud=h;
        Image(canvas.transform,"Bank card",new Vector2(-625,398),new Vector2(310,76),cream);
        h.bank=Text(canvas.transform,"Banked","",new Vector2(-610,411),new Vector2(265,30),25);
        h.carry=Text(canvas.transform,"Carried","",new Vector2(-610,382),new Vector2(265,28),20);
        Image(canvas.transform,"Route clock card",new Vector2(-190,398),new Vector2(530,76),cream);
        h.clock=Text(canvas.transform,"Route clock","",new Vector2(-180,411),new Vector2(490,30),22);
        h.nextStop=Text(canvas.transform,"Return window","",new Vector2(-180,382),new Vector2(490,30),20);
        h.emergency=Button(canvas.transform,"Rescue stop","",new Vector2(600,404),new Vector2(325,56),gold,20);
        Image(canvas.transform,"Supply card",new Vector2(-435,-408),new Vector2(690,48),cream);
        h.supplies=Text(canvas.transform,"Supply totals","",new Vector2(-423,-408),new Vector2(650,42),19);
        Text(canvas.transform,"Route controls","M  Map / shop     E  Use     R  Rescue stop",new Vector2(474,-408),new Vector2(590,40),20,TextAnchor.MiddleRight);
        var plan=Image(canvas.transform,"Planning map",Vector2.zero,new Vector2(1600,900),cream);plan.raycastTarget=true;h.planPanel=plan.gameObject;
        h.heading=Text(plan.transform,"Heading","",new Vector2(-480,408),new Vector2(570,40),24);h.heading.fontStyle=FontStyle.Bold;
        h.launch=Button(plan.transform,"Start route","Start route",new Vector2(646,394),new Vector2(250,62),coral,26);h.launchText=h.launch.GetComponentInChildren<Text>();
        h.inspect=Button(plan.transform,"Inspect truck","M  Inspect truck",new Vector2(359,394),new Vector2(266,62),pale,23);
        h.budget=Text(plan.transform,"Route budget","",new Vector2(-294,365),new Vector2(942,32),20);
        h.map=Image(plan.transform,"Park map",new Vector2(-300,90),new Vector2(930,474),pale).rectTransform;
        Text(h.map,"North","N ↑",new Vector2(-422,209),new Vector2(65,30),22);
        Vector2 World(Vector3 p)=>new Vector2((Mathf.InverseLerp(-40,200,p.x)-.5f)*930,(Mathf.InverseLerp(-25,95,p.z)-.5f)*474);
        for(int i=1;i<route.path.Length;i++)
        {
            Vector2 a=World(route.path[i-1].position),b=World(route.path[i].position),delta=b-a;
            var line=Image(h.map,"Route line",(a+b)*.5f,new Vector2(delta.magnitude,16),new Color(.51f,.62f,.53f));line.transform.localRotation=Quaternion.Euler(0,0,Mathf.Atan2(delta.y,delta.x)*Mathf.Rad2Deg);
        }
        Text(h.map,"Start","START",World(route.path[0].position)+Vector2.down*26,new Vector2(80,25),16,TextAnchor.MiddleCenter);
        Text(h.map,"Exit","EXIT →",World(route.path[3].position)+Vector2.up*31,new Vector2(100,25),16,TextAnchor.MiddleCenter);
        h.pointButtons=new Button[6];h.pointLabels=new Text[6];
        for(int i=0;i<6;i++)
        {
            float d=route.points[i].distance;Vector3 position=Position(route.path,d);
            var b=Button(h.map,"Route point "+route.points[i].label,"",World(position),new Vector2(108,54),cream,16);h.pointButtons[i]=b;h.pointLabels[i]=b.GetComponentInChildren<Text>();
        }
        h.hotspotButtons=new Button[6];
        for(int i=0;i<6;i++) h.hotspotButtons[i]=Button(h.map,"Hotspot "+(i+1),(i+1)+"  CROWD",World(route.hotspots[i].transform.position),new Vector2(106,39),gold,15);
        h.truckMarker=Image(h.map,"Truck position",World(Vector3.zero),new Vector2(20,20),coral,circle).rectTransform;
        var detail=Image(plan.transform,"Hotspot details",new Vector2(482,93),new Vector2(548,460),new Color(.96f,.93f,.85f));
        h.detailTitle=Text(detail.transform,"Hotspot title","",new Vector2(0,187),new Vector2(488,42),31);h.detailTitle.fontStyle=FontStyle.Bold;
        h.detailStats=Text(detail.transform,"Hotspot stats","",new Vector2(0,120),new Vector2(488,72),21);
        h.detailNeeds=Text(detail.transform,"Ingredients needed","",new Vector2(0,-112),new Vector2(488,116),19);
        h.detailBehavior=Text(detail.transform,"Crowd behavior","",new Vector2(0,-204),new Vector2(488,30),18);
        var shop=Image(plan.transform,"Stock shop",new Vector2(-300,-250),new Vector2(930,157),new Color(.93f,.92f,.85f));
        Text(shop.transform,"Shop title","STOCK",new Vector2(-292,55),new Vector2(280,26),18);
        h.unpack=Button(shop.transform,"Unload supplies","Unload bag",new Vector2(358,54),new Vector2(170,33),pale,16);
        h.buyButtons=new Button[5];h.buyLabels=new Text[5];h.stockLabels=new Text[5];h.packButtons=new Button[5];
        for(int i=0;i<5;i++)
        {
            float x=-365+i*183;h.stockLabels[i]=Text(shop.transform,"Stock "+i,"",new Vector2(x,16),new Vector2(174,32),18,TextAnchor.MiddleCenter);
            h.buyButtons[i]=Button(shop.transform,"Buy "+i,"",new Vector2(x-27,-30),new Vector2(109,42),mint,18);h.buyLabels[i]=h.buyButtons[i].GetComponentInChildren<Text>();
            h.packButtons[i]=Button(shop.transform,"Pack "+i,"Pack",new Vector2(x+64,-30),new Vector2(66,42),cream,16);
        }
        h.deliveryText=Text(plan.transform,"Deliveries","",new Vector2(482,-235),new Vector2(528,138),18);
        var pause=Image(canvas.transform,"Pause veil",Vector2.zero,new Vector2(1600,900),new Color(.12f,.25f,.23f,.6f));pause.raycastTarget=true;h.pausePanel=pause.gameObject;
        var pauseCard=Image(pause.transform,"Pause card",Vector2.zero,new Vector2(760,560),cream);
        Text(pauseCard.transform,"Pause title","Taking a break",new Vector2(0,201),new Vector2(660,60),40,TextAnchor.MiddleCenter);
        Text(pauseCard.transform,"Controls","E to use tools, load the tray, serve, or open the door.\nHold mouse to pour; move up/down to scoop or shake.\nM opens the map and stock shop. R calls a rescue stop.\nCarry several cones on the tray. Board to bank outside cash.\nThe map stays live. This pause menu stops the clocks.",new Vector2(0,36),new Vector2(670,220),23,TextAnchor.MiddleCenter);
        h.resume=Button(pauseCard.transform,"Resume","Back to the route",new Vector2(-175,-174),new Vector2(310,58),mint);
        var back=Button(pauseCard.transform,"Main menu","Main menu",new Vector2(175,-174),new Vector2(310,58),coral);UnityEventTools.AddPersistentListener(back.onClick,nav.ReturnToMenu);pause.gameObject.SetActive(false);
        var results=Image(canvas.transform,"Route results",Vector2.zero,new Vector2(1600,900),new Color(.12f,.25f,.23f,.65f));results.raycastTarget=true;h.resultsPanel=results.gameObject;
        var resultsCard=Image(results.transform,"Results card",Vector2.zero,new Vector2(1050,690),cream);
        h.resultsTitle=Text(resultsCard.transform,"Results title","",new Vector2(0,257),new Vector2(960,80),43,TextAnchor.MiddleCenter);
        h.resultsText=Text(resultsCard.transform,"Result totals","",new Vector2(0,14),new Vector2(944,360),24,TextAnchor.MiddleCenter);
        h.nextDay=Button(resultsCard.transform,"Next day","Plan next day",new Vector2(-193,-249),new Vector2(340,62),mint,26);
        var main=Button(resultsCard.transform,"Main menu","Main menu",new Vector2(193,-249),new Vector2(340,62),coral,26);UnityEventTools.AddPersistentListener(main.onClick,nav.ReturnToMenu);results.gameObject.SetActive(false);
        var notice=Image(canvas.transform,"Route notice",new Vector2(0,-350),new Vector2(1070,62),cream);h.noticePanel=notice.gameObject;
        h.notice=Text(notice.transform,"Message","",Vector2.zero,new Vector2(1030,54),22,TextAnchor.MiddleCenter);notice.gameObject.SetActive(false);
    }
    static Vector3 Position(Transform[] path,float distance)
    {
        for(int i=1;i<path.Length;i++){float length=Vector3.Distance(path[i-1].position,path[i].position);if(distance<=length)return Vector3.Lerp(path[i-1].position,path[i].position,distance/length);distance-=length;}
        return path[path.Length-1].position;
    }
    public static string CreateMenu()
    {
        Assets();
        if(File.Exists("Assets/Scenes/MainMenu.unity"))throw new InvalidOperationException("MainMenu already exists.");
        if(SceneManager.GetActiveScene().isDirty)EditorSceneManager.SaveScene(SceneManager.GetActiveScene());
        var scene=EditorSceneManager.NewScene(NewSceneSetup.EmptyScene,NewSceneMode.Single);
        var camera=new GameObject("Menu camera",typeof(Camera)).GetComponent<Camera>();camera.clearFlags=CameraClearFlags.SolidColor;camera.backgroundColor=cream;
        var events=new GameObject("UI input",typeof(EventSystem),typeof(InputSystemUIInputModule));
        var input=events.GetComponent<InputSystemUIInputModule>();input.AssignDefaultActions();
        var canvas=Canvas("Main menu");var menu=canvas.gameObject.AddComponent<GameModeMenu>();menu.mainMenu=true;
        Image(canvas.transform,"Background",Vector2.zero,new Vector2(1600,900),cream);
        Image(canvas.transform,"Mint circle",new Vector2(-720,360),new Vector2(540,540),pale,circle);
        Image(canvas.transform,"Peach circle",new Vector2(746,-340),new Vector2(610,610),new Color(.99f,.85f,.74f),circle);
        Text(canvas.transform,"Eyebrow","ICE CREAM TRUCK",new Vector2(0,331),new Vector2(1320,50),27,TextAnchor.MiddleCenter);
        var title=Text(canvas.transform,"Title","Two ways to make a sweet living",new Vector2(0,252),new Vector2(1420,100),58,TextAnchor.MiddleCenter);title.fontStyle=FontStyle.Bold;
        Text(canvas.transform,"Subtitle","Choose a game system to play",new Vector2(0,180),new Vector2(1100,50),25,TextAnchor.MiddleCenter);
        var left=Image(canvas.transform,"Free drive card",new Vector2(-361,-70),new Vector2(645,410),new Color(.83f,.92f,.83f));
        var right=Image(canvas.transform,"Park route card",new Vector2(361,-70),new Vector2(645,410),new Color(.98f,.86f,.79f));
        var flavor=AssetDatabase.LoadAssetAtPath<Sprite>("Assets/Art/OrderPictures/Vanilla.png");
        Image(left.transform,"Ice cream",new Vector2(-246,136),new Vector2(75,75),Color.white,flavor);
        Image(right.transform,"Ice cream",new Vector2(-246,136),new Vector2(75,75),Color.white,AssetDatabase.LoadAssetAtPath<Sprite>("Assets/Art/OrderPictures/Strawberry.png"));
        Text(left.transform,"Mode title","Free drive",new Vector2(31,136),new Vector2(460,69),42).fontStyle=FontStyle.Bold;
        Text(right.transform,"Mode title","Park route",new Vector2(31,136),new Vector2(460,69),42).fontStyle=FontStyle.Bold;
        Text(left.transform,"Description","Your original game\n\nDrive where you want. Park near customers.\nMake their orders and meet the daily quota.\nUnlimited ingredients, at your own pace.",new Vector2(0,7),new Vector2(559,167),24);
        Text(right.transform,"Description","The planning & runner alternative\n\nPlan stops, slow zones, and limited stock.\nServe crowds beside an automatic truck.\nBring your cash back before it leaves.",new Vector2(0,7),new Vector2(559,167),24);
        var free=Button(left.transform,"Play Free drive","Play Free drive",new Vector2(0,-139),new Vector2(553,64),mint,27);UnityEventTools.AddPersistentListener(free.onClick,menu.FreeDrive);
        var route=Button(right.transform,"Play Park route","Plan a park route",new Vector2(0,-139),new Vector2(553,64),coral,27);UnityEventTools.AddPersistentListener(route.onClick,menu.ParkRoute);
        Text(canvas.transform,"Prototype note","Single-player prototypes  •  Shared hands-on ice cream preparation",new Vector2(0,-356),new Vector2(1370,45),21,TextAnchor.MiddleCenter);
        EditorSceneManager.SaveScene(scene,"Assets/Scenes/MainMenu.unity");
        return "Saved main menu with both game modes.";
    }
    public static string Polish()
    {
        Assets();
        var scene=EditorSceneManager.OpenScene("Assets/Scenes/ParkRoute.unity");
        var h=PrototypeSceneReferences.Instance.route.hud;
        h.carry.fontSize=18;
        h.noticePanel.GetComponent<RectTransform>().anchoredPosition=new Vector2(0,291);
        var controls=h.GetComponentsInChildren<Text>(true).Single(t=>t.name=="Route controls");
        var card=Image(h.transform,"Controls card",new Vector2(474,-408),new Vector2(610,48),cream);
        card.transform.SetSiblingIndex(controls.transform.GetSiblingIndex());
        EditorSceneManager.MarkSceneDirty(scene);EditorSceneManager.SaveScene(scene);
        EditorSceneManager.OpenScene("Assets/Scenes/MainMenu.unity");
        return "Saved route HUD polish.";
    }
    public static string Refine()
    {
        Assets();
        var scene=EditorSceneManager.OpenScene("Assets/Scenes/ParkRoute.unity");
        var r=PrototypeSceneReferences.Instance;
        r.route.hud.planningFunds=Text(r.route.hud.planPanel.transform,"Planning funds","",new Vector2(-5,408),new Vector2(432,38),20,TextAnchor.MiddleCenter);
        r.route.tray.transform.localPosition=new Vector3(-.85f,1.47f,2.15f);
        r.route.tray.home.localPosition=r.route.tray.transform.localPosition;
        EditorSceneManager.MarkSceneDirty(scene);EditorSceneManager.SaveScene(scene);
        scene=EditorSceneManager.OpenScene("Assets/Scenes/MainMenu.unity");
        var root=scene.GetRootGameObjects().Single(o=>o.name=="Main menu");
        var menu=root.GetComponent<GameModeMenu>();
        menu.freeDriveButton=root.GetComponentsInChildren<Button>().Single(b=>b.name=="Play Free drive");
        menu.parkRouteButton=root.GetComponentsInChildren<Button>().Single(b=>b.name=="Play Park route");
        EditorSceneManager.MarkSceneDirty(scene);EditorSceneManager.SaveScene(scene);
        return "Saved planning funds, tray on serving ledge, and main menu button references.";
    }
    public static string Finish()
    {
        Assets();
        var scene=EditorSceneManager.OpenScene("Assets/Scenes/IceCreamPrototype.unity");var r=PrototypeSceneReferences.Instance;
        var nav=r.gameObject.AddComponent<GameModeMenu>();
        var pause=Button(r.hud.pausePanel.transform,"Main menu","Main menu",new Vector2(0,-363),new Vector2(310,56),cream,23);
        UnityEventTools.AddPersistentListener(pause.onClick,nav.ReturnToMenu);
        var result=Button(r.hud.resultPanel.transform,"Main menu","Main menu",new Vector2(0,-358),new Vector2(310,56),cream,23);
        UnityEventTools.AddPersistentListener(result.onClick,nav.ReturnToMenu);
        EditorSceneManager.MarkSceneDirty(scene);EditorSceneManager.SaveScene(scene);
        EditorBuildSettings.scenes=new[]{new EditorBuildSettingsScene("Assets/Scenes/MainMenu.unity",true),new EditorBuildSettingsScene("Assets/Scenes/IceCreamPrototype.unity",true),new EditorBuildSettingsScene("Assets/Scenes/ParkRoute.unity",true)};
        EditorSceneManager.playModeStartScene=AssetDatabase.LoadAssetAtPath<SceneAsset>("Assets/Scenes/MainMenu.unity");
        EditorSceneManager.OpenScene("Assets/Scenes/MainMenu.unity");AssetDatabase.SaveAssets();
        return "Main menu is the build and Editor entry point. Both modes can return to it.";
    }
    public static string WireRescueLabel()
    {
        var scene=EditorSceneManager.OpenScene("Assets/Scenes/ParkRoute.unity");
        var h=PrototypeSceneReferences.Instance.route.hud;
        h.emergencyLabel=h.emergency.transform.GetChild(0).GetComponent<Text>();
        EditorSceneManager.MarkSceneDirty(scene);EditorSceneManager.SaveScene(scene);
        EditorSceneManager.OpenScene("Assets/Scenes/MainMenu.unity");
        return "Saved explicit rescue-label reference.";
    }

    public static string SimplifyMenu()
    {
        var scene=EditorSceneManager.OpenScene("Assets/Scenes/MainMenu.unity");
        var root=scene.GetRootGameObjects().Single(o=>o.name=="Main menu");
        var menu=root.GetComponent<GameModeMenu>();
        foreach(var text in root.GetComponentsInChildren<Text>(true))
        {
            if(text.name=="Title") text.text="Ice Cream Truck Simulator";
            else if(text.name!="Mode title") Object.DestroyImmediate(text.gameObject);
        }
        foreach(var button in new[]{menu.freeDriveButton,menu.parkRouteButton})
        {
            var card=(RectTransform)button.transform.parent;
            card.sizeDelta=new Vector2(645,330);
            card.anchoredPosition=new Vector2(card.anchoredPosition.x,-50);
            var rect=(RectTransform)button.transform;
            rect.anchorMin=Vector2.zero;rect.anchorMax=Vector2.one;
            rect.offsetMin=rect.offsetMax=Vector2.zero;
            button.GetComponent<Image>().color=Color.clear;
            button.targetGraphic=card.GetComponent<Image>();
            var label=card.GetComponentsInChildren<Text>().Single();
            label.rectTransform.anchoredPosition=new Vector2(0,-75);
            label.alignment=TextAnchor.MiddleCenter;
            var icon=card.GetComponentsInChildren<Image>().Single(image=>image.name=="Ice cream");
            icon.rectTransform.anchoredPosition=new Vector2(0,50);
            icon.rectTransform.sizeDelta=new Vector2(110,110);
        }
        EditorSceneManager.MarkSceneDirty(scene);EditorSceneManager.SaveScene(scene);
        return string.Join(" | ",root.GetComponentsInChildren<Text>().Select(t=>t.text))+"; both buttons retain their scene-selection listeners.";
    }

    public static string CorrectClickHelp()
    {
        foreach(var path in new[]{"Assets/Scenes/IceCreamPrototype.unity","Assets/Scenes/ParkRoute.unity"})
        {
            var scene=EditorSceneManager.OpenScene(path);
            foreach(var text in scene.GetRootGameObjects().SelectMany(o=>o.GetComponentsInChildren<Text>(true)))
            {
                text.text=text.text.Replace("E to use, open doors, or sit in the driver's seat", "Click to use tools or serve. E for doors and the driver seat");
                if(text.name=="Route controls") text.text="M  Map / shop     Click  Use     R  Rescue stop";
                else if(text.text.Contains("E to use tools")) text.text=text.text.Replace("E to use tools, load the tray, serve, or open the door.","Click to use tools, load the tray, or serve. E opens the door.");
                else if(text.text.Contains("E") && text.text.Contains("pick")) text.text="WASD move · Mouse look · Space jump\nClick to pick up, place, serve, or use kitchen equipment.\nE opens/closes the rear door or enters/exits the driver seat.\nHold mouse to pour; move up/down to scoop or shake.\nRight click returns tools. Escape pauses.";
            }
            EditorSceneManager.MarkSceneDirty(scene);EditorSceneManager.SaveScene(scene);
        }
        EditorSceneManager.OpenScene("Assets/Scenes/MainMenu.unity");
        return "Saved click controls in both modes' help.";
    }

}
