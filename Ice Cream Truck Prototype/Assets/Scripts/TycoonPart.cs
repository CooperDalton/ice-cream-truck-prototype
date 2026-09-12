using System;
using UnityEngine;

public class TycoonPart : MonoBehaviour
{
    public enum Kind { Table, Tub, Prep, Iron, Locker, ColdStorage, Sign, ServingCounter, Supplier, Bike, Truck, Plot, Trash, Shelf }
    public Kind kind;
    public int catalogIndex, site, id, variant;
    public Vector2 footprint = new Vector2(.5f, .5f);
    public bool tabletop;
    public bool installed = true;
    public bool packed;
    public Transform operatingPoint, handTarget, contentPoint, lid;
    public Renderer[] fillRenderers;
    public GameObject[] lockerModels;
    public GameObject tubModel;
    public Transform signModel;
    private TycoonTubVisual tubVisual;
    private int shownFlavor = -1;
    public TycoonInventory storage = new TycoonInventory(4);
    public TycoonItem contents;
    public string claimedBy = "";
    public float cookTime;
    public float pourProgress;
    public int ironStage;
    public TycoonPart support;
    public TycoonGameManager game;
    private GameObject contentVisual;
    private string visualState;
    public bool Available(string actor) => claimedBy == "" || claimedBy == actor;
    public bool Claim(string actor)
    {
        if (!Available(actor)) return false;
        claimedBy = actor; return true;
    }
    private void Awake()
    {
        if (contents != null && contents.kind == TycoonItem.Kind.None) contents = null;
    }
    private void Update()
    {
        if (game == null) return;
        if (!game.Paused && kind == Kind.Iron && ironStage == 2)
        {
            cookTime += Time.deltaTime;
            if (cookTime >= 18) ironStage = 4;
        }
        RefreshVisual();
    }
    public void RefreshVisual()
    {
        if (kind == Kind.Sign) signModel.localRotation = Quaternion.Euler(0,game.sites[site].open ? 0 : 180,0);
        if (kind == Kind.Locker) RefreshLocker();
        if (kind == Kind.Tub && contents != null)
        {
            if (shownFlavor != variant)
            {
                Destroy(tubModel); tubModel = Instantiate(game.catalog.tubs[variant], transform); tubModel.transform.localPosition = Vector3.up * .722f; tubModel.transform.localRotation = Quaternion.Euler(0,180,0); tubVisual = tubModel.GetComponent<TycoonTubVisual>(); shownFlavor = variant;
            }
            tubVisual.SetFill(contents.Fill);
            handTarget.localPosition = new Vector3(0, .9f - (1 - contents.Fill) * .075f, 0);
        }
        if (kind == Kind.Iron) lid.localRotation = Quaternion.Euler(ironStage == 2 ? 0 : -105, 0, 0);
        string state = contents == null ? "" : JsonUtility.ToJson(contents);
        if (state == visualState || kind == Kind.Tub) return;
        visualState = state;
        if (contentVisual != null) Destroy(contentVisual);
        if (contents != null) contentVisual = kind == Kind.Iron ? Instantiate(game.catalog.flatWaffle, contentPoint) : game.catalog.Display(contents, contentPoint);
    }
    public void RefreshLocker()
    {
        if (lockerModels == null) return;
        for (int i = 0; i < lockerModels.Length; i++) lockerModels[i].SetActive(i == storage.slots.Length / 4 - 1);
    }
    public bool Scoop(TycoonItem tool, string actor)
    {
        if (kind != Kind.Tub || !Available(actor) || !tool.Tool || tool.loadedFlavor >= 0 || contents.amount == 0) return false;
        contents.amount--; tool.loadedFlavor = variant; claimedBy = ""; game.PreparationSound(game.scoopSound,transform.position); return true;
    }
    public bool Deposit(TycoonItem tool, string actor)
    {
        if (kind != Kind.Prep || !Available(actor) || contents == null || tool.loadedFlavor < 0 || contents.scoops.Length >= 2) return false;
        int n = contents.scoops.Length; Array.Resize(ref contents.scoops, n + 1);
        contents.scoops[n] = tool.loadedFlavor; tool.loadedFlavor = -1; game.PreparationSound(game.depositSound,transform.position); return true;
    }
    public bool BeginTopping(TycoonItem topping, string actor)
    {
        if (kind != Kind.Prep || !Available(actor) || contents == null || contents.scoops.Length == 0 || topping.kind != TycoonItem.Kind.Topping) return false;
        if (contents.pendingTopping == topping.variant) return true;
        if (contents.pendingTopping >= 0 || topping.amount < 1) return false;
        int bit = 1 << topping.variant;
        if ((contents.toppings & bit) != 0) return false;
        topping.amount--; contents.pendingTopping = topping.variant; contents.toppingProgress = 0; return true;
    }
    public bool Finish(TycoonItem topping, string actor)
    {
        if (!Available(actor) || contents == null || contents.pendingTopping != topping.variant) return false;
        contents.toppings |= 1 << topping.variant; contents.pendingTopping = -1; contents.toppingProgress = 0; return true;
    }
    public bool BeginPour(TycoonItem batter, string actor)
    {
        if (kind != Kind.Iron || !Available(actor) || ironStage != 0 || batter.kind != TycoonItem.Kind.Batter || batter.amount < 1) return false;
        batter.amount--; ironStage = 5; cookTime = 0; pourProgress = 0;
        contents = new TycoonItem(TycoonItem.Kind.Cone); return true;
    }
    public bool Pour(TycoonItem batter, string actor)
    {
        if (!Available(actor) || ironStage != 5) return false;
        ironStage = 1; pourProgress = 1; return true;
    }
    public bool CloseIron(string actor)
    {
        if (!Available(actor) || ironStage != 1) return false;
        ironStage = 2; return true;
    }
    public bool OpenIron(string actor)
    {
        if (!Available(actor) || ironStage != 2 || cookTime < 6) return false;
        ironStage = 3; return true;
    }
    public TycoonItem TakeCone(string actor)
    {
        if (!Available(actor) || ironStage != 3) return null;
        var cone = contents; contents = null; ironStage = 0; claimedBy = ""; return cone;
    }
    public string Prompt()
    {
        return kind switch {
            Kind.Tub => TycoonCatalogSO.FlavorNames[variant] + (contents.amount > 0 ? " / hold click and swipe to scoop, click with a refill tub to top up" : " / empty, needs a refill tub"),
            Kind.Prep => contents == null ? "Place a bowl or cone here" : "Add a scoop or topping / E to take serving",
            Kind.Iron => ironStage switch { 0 => "Hold click with batter to pour", 1 => "Click to close waffle iron", 2 => cookTime < 6 ? "Waffle cooking" : "Click to open waffle iron", 3 => "E to take fresh cone", 5 => "Hold click to finish pouring", _ => "Burned waffle / click to discard" },
            Kind.Locker => "E / staff locker", Kind.ColdStorage => "E / cold storage", Kind.Supplier => "E / buy supplies and equipment",
            Kind.Sign => "E / open or close this stand", Kind.ServingCounter => "Click with completed order to serve", Kind.Bike => "E / ride bicycle, F / cargo", Kind.Truck => "E / drive truck, F / cargo",
            Kind.Plot => "E / business upgrades", Kind.Trash => "Click / discard held item", _ => "E / storage" };
    }
}
