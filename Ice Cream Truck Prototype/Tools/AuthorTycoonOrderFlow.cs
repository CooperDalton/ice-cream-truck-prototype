using System;
using System.Collections.Generic;
using System.Linq;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.UI;
using Object = UnityEngine.Object;

public static class AuthorTycoonOrderFlow
{
    public static string Build()
    {
        if (EditorApplication.isPlaying) throw new Exception("Stop Play Mode before authoring order flow");
        var scene = UnityEngine.SceneManagement.SceneManager.GetActiveScene();
        var game = scene.GetRootGameObjects()[0].GetComponent<TycoonGameManager>();
        var hud = game.hud;
        var paper = hud.moneyDisplay.parent.GetComponent<Image>().sprite;
        var font = hud.money.font;
        var customerPath = AssetDatabase.GetAssetPath(game.catalog.customerPrefab);
        var customer = PrefabUtility.LoadPrefabContents(customerPath);
        try
        {
            var actor = customer.GetComponent<TycoonActor>();
            if (actor.patienceDisplay != null) Object.DestroyImmediate(actor.patienceDisplay.gameObject);
            var collider = customer.GetComponent<CapsuleCollider>();
            if (collider == null) collider = customer.AddComponent<CapsuleCollider>();
            collider.center = new Vector3(0,1.05f,0); collider.height = 1.8f; collider.radius = .3f;
            var canvas = new GameObject("Customer patience", typeof(RectTransform), typeof(Canvas)).GetComponent<Canvas>();
            canvas.renderMode = RenderMode.WorldSpace; canvas.transform.SetParent(customer.transform, false);
            canvas.transform.localPosition = new Vector3(0,2.02f,0); canvas.transform.localScale = Vector3.one * .01f;
            actor.patienceDisplay = (RectTransform)canvas.transform; actor.patienceDisplay.sizeDelta = new Vector2(64,8);
            var track = Image("Track", canvas.transform, new Vector2(64,8), new Color(.24f,.20f,.28f,.9f), null);
            actor.patienceBar = Image("Patience", track.transform, new Vector2(60,4), new Color(.43f,.76f,.61f), hud.xpBar.sprite);
            actor.patienceBar.type = UnityEngine.UI.Image.Type.Filled; actor.patienceBar.fillMethod = UnityEngine.UI.Image.FillMethod.Horizontal;
            actor.patienceBar.fillOrigin = 0; actor.patienceBar.fillAmount = 1;
            PrefabUtility.SaveAsPrefabAsset(customer, customerPath);
        }
        finally { PrefabUtility.UnloadPrefabContents(customer); }
        for (int i = 0; i < game.sites.Length; i++)
        {
            var site = game.sites[i];
            var counter = game.Parts(i,TycoonPart.Kind.ServingCounter).First();
            if (site.registerCounter != null) Object.DestroyImmediate(site.registerCounter);
            site.registerCounter = new GameObject("Order counter " + site.name);
            site.registerCounter.transform.SetParent(site.origin, false);
            if (site.pickupQueuePoint == null) site.pickupQueuePoint = new GameObject("Pickup queue").transform;
            site.pickupQueuePoint.SetParent(site.queuePoint.parent, true);
            site.pickupQueuePoint.SetPositionAndRotation(counter.transform.position + counter.transform.forward * 1.2f, counter.transform.rotation);
            site.pickupQueuePoint.position = new Vector3(site.pickupQueuePoint.position.x, site.queuePoint.position.y, site.pickupQueuePoint.position.z);
            var registerPosition = counter.transform.position + counter.transform.right * (i == 2 ? -.65f : -2f) + counter.transform.forward * (i == 2 ? 0 : 1f);
            site.registerCounter.transform.SetPositionAndRotation(registerPosition, counter.transform.rotation);
            if (i != 2)
            {
                var visual = Object.Instantiate(game.catalog.partPrefabs[7].transform.GetChild(0).gameObject, site.registerCounter.transform);
                visual.name = "Register counter"; visual.transform.localPosition = Vector3.zero;
                visual.transform.localRotation = Quaternion.identity; visual.transform.localScale = new Vector3(.65f,1,.8f);
                var box = site.registerCounter.AddComponent<BoxCollider>(); box.center = new Vector3(0,.5f,0); box.size = new Vector3(1.3f,1,.8f);
            }
            else site.pickupQueuePoint.position += counter.transform.right * .65f;
            site.queuePoint.SetPositionAndRotation(registerPosition + counter.transform.forward * 1.2f, counter.transform.rotation);
            site.queuePoint.position = new Vector3(site.queuePoint.position.x, site.pickupQueuePoint.position.y, site.queuePoint.position.z);
            site.registerOperatingPoint = new GameObject("Register operating point").transform;
            site.registerOperatingPoint.SetParent(site.registerCounter.transform, false); site.registerOperatingPoint.localPosition = new Vector3(0,0,-.9f);
            Sign(site.registerCounter.transform, new Vector3(0,1.13f,0), "ORDER", font, paper);
        }
        var counterPath = AssetDatabase.GetAssetPath(game.catalog.partPrefabs[7]);
        var counterPrefab = PrefabUtility.LoadPrefabContents(counterPath);
        try
        {
            // Keep this sign on the counter prefab so saved and moved counters retain it.
            if (counterPrefab.transform.childCount == 6) Object.DestroyImmediate(counterPrefab.transform.GetChild(5).gameObject);
            Sign(counterPrefab.transform, new Vector3(.35f,1.13f,0), "PICKUP", font, paper);
            PrefabUtility.SaveAsPrefabAsset(counterPrefab,counterPath);
        }
        finally { PrefabUtility.UnloadPrefabContents(counterPrefab); }
        var cards = hud.tickets.ToList();
        while (cards.Count < 6)
        {
            var source = cards[0]; var root = Object.Instantiate(source.root,source.root.transform.parent);
            root.name = "Order card " + (cards.Count + 1);
            cards.Add(new TycoonHUD.OrderView { root = root, title = Map(source.title,source.root,root), description = Map(source.description,source.root,root), container = Map(source.container,source.root,root), coin = Map(source.coin,source.root,root), ingredients = Map(source.ingredients,source.root,root), flavors = source.flavors.Select(f=>Map(f,source.root,root)).ToArray(), toppings = source.toppings.Select(t=>Map(t,source.root,root)).ToArray() });
        }
        hud.tickets = cards.ToArray();
        for (int i = 0; i < hud.tickets.Length; i++)
        {
            var card = hud.tickets[i]; var rect = (RectTransform)card.root.transform;
            rect.anchoredPosition = new Vector2(-24,-120-i*112); rect.sizeDelta = new Vector2(330,104);
            var price = (RectTransform)card.title.transform.parent; price.anchoredPosition = new Vector2(144,29); price.sizeDelta = new Vector2(80,34);
            card.reward = price.GetComponent<Image>(); if (card.reward == null) card.reward = price.gameObject.AddComponent<Image>();
            card.reward.sprite = paper; card.reward.type = UnityEngine.UI.Image.Type.Sliced; card.reward.color = new Color(.43f,.76f,.61f); card.reward.raycastTarget = false;
            var layout = price.GetComponent<HorizontalLayoutGroup>(); layout.padding = new RectOffset(9,9,0,0);
            card.title.fontSize = 22;
            if (price.childCount == 3) Object.DestroyImmediate(price.GetChild(2).gameObject);
            card.ingredients.anchoredPosition = new Vector2(0,-17); card.root.SetActive(false);
        }
        hud.salePopupBackground = hud.salePopup.GetComponent<Image>();
        hud.salePopup.sizeDelta = new Vector2(224,80);
        ((RectTransform)hud.salePopup.GetChild(0)).anchoredPosition = new Vector2(-77,0);
        hud.salePopupAmount.rectTransform.anchoredPosition = new Vector2(23,15);
        hud.salePopupAmount.rectTransform.sizeDelta = new Vector2(146,34);
        if (hud.salePopupTip == null) hud.salePopupTip = Object.Instantiate(hud.salePopupAmount,hud.salePopup);
        hud.salePopupTip.name = "Tip reward"; hud.salePopupTip.text = "+$2.40 tip"; hud.salePopupTip.fontSize = 19;
        hud.salePopupTip.rectTransform.anchoredPosition = new Vector2(23,-17);
        EditorUtility.SetDirty(game); EditorUtility.SetDirty(hud);
        game.navigation.BuildNavMesh();
        EditorSceneManager.MarkSceneDirty(scene); EditorSceneManager.SaveScene(scene); AssetDatabase.SaveAssets();
        return "Authored register and pickup queues at all three sites, customer interaction colliders and patience bars, six tickets and colored payouts.";
    }
    private static T Map<T>(T component, GameObject source, GameObject target) where T : Component
    {
        var path = new Stack<int>(); var t = component.transform;
        while (t != source.transform) { path.Push(t.GetSiblingIndex()); t = t.parent; }
        t = target.transform; foreach (int i in path) t = t.GetChild(i);
        return t.GetComponent<T>();
    }
    private static Image Image(string name, Transform parent, Vector2 size, Color color, Sprite sprite)
    {
        var image = new GameObject(name,typeof(RectTransform),typeof(Image)).GetComponent<Image>();
        image.transform.SetParent(parent,false); image.rectTransform.sizeDelta = size; image.color = color; image.sprite = sprite;
        image.type = sprite == null ? UnityEngine.UI.Image.Type.Simple : UnityEngine.UI.Image.Type.Sliced; image.raycastTarget = false;
        return image;
    }
    private static void Sign(Transform parent, Vector3 position, string title, Font font, Sprite paper)
    {
        var root = new GameObject(title + " sign",typeof(RectTransform),typeof(Canvas),typeof(TycoonStationSign)); root.transform.SetParent(parent,false);
        root.transform.localPosition = position; root.transform.localScale = Vector3.one * .006f;
        var canvas = root.GetComponent<Canvas>(); canvas.renderMode = RenderMode.WorldSpace;
        ((RectTransform)root.transform).sizeDelta = new Vector2(150,38);
        var panel = Image("Sign face",root.transform,new Vector2(150,38),new Color(1,.97f,.90f),paper);
        var label = new GameObject("Label",typeof(RectTransform),typeof(Text)).GetComponent<Text>(); label.transform.SetParent(panel.transform,false);
        label.rectTransform.sizeDelta = new Vector2(146,34); label.text = title; label.font = font; label.fontSize = 25;
        label.alignment = TextAnchor.MiddleCenter; label.color = new Color(.24f,.20f,.29f); label.raycastTarget = false;
    }
}
