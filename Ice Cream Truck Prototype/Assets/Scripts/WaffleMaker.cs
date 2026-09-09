using UnityEngine;

public class WaffleMaker : Interactable
{
    public enum CookState { Empty, BatterReady, Cooking, Ready, Burned }
    public PrototypeSettingsSO settings;
    public DayManager day;
    public PlayerInteraction player;
    public Transform lid;
    public GameObject rawBatter, cookedWaffle;
    public Renderer[] waffleRenderers;
    public Material cookedMaterial, burnedMaterial;
    public IceCreamCone conePrefab;
    public LineRenderer pourStream;
    [SerializeField] private Vector3 openRotation = new Vector3(-108, 0, 0);
    public CookState State { get; private set; }
    public bool IsOpen { get; private set; }
    public float BatterProgress { get; private set; }
    private float cookTime;
    public override float Progress => State == CookState.Cooking ? cookTime / settings.cookSeconds : BatterProgress;

    private void Awake()
    {
        rawBatter.SetActive(false);
        cookedWaffle.SetActive(false);
        pourStream.enabled = false;
    }
    private void Update()
    {
        if (!day.CanPlay) return;
        Advance(Time.deltaTime);
        lid.localRotation = Quaternion.Slerp(lid.localRotation, Quaternion.Euler(IsOpen ? openRotation : Vector3.zero), Time.deltaTime * settings.lidAnimationSpeed);
    }
    public void Advance(float dt)
    {
        if (!day.CanPlay || IsOpen || (State != CookState.Cooking && State != CookState.Ready)) return;
        cookTime += dt;
        if (State == CookState.Cooking && cookTime >= settings.cookSeconds)
        {
            State = CookState.Ready;
            rawBatter.SetActive(false);
            cookedWaffle.SetActive(true);
            foreach (var renderer in waffleRenderers) renderer.sharedMaterial = cookedMaterial;
            player.Play(player.readySound);
            player.hud.ShowMessage("Waffle ready! Open the lid before it burns.");
        }
        if (cookTime >= settings.cookSeconds + settings.burnGraceSeconds)
        {
            State = CookState.Burned;
            foreach (var renderer in waffleRenderers) renderer.sharedMaterial = burnedMaterial;
            player.Notify("Waffle burned. Open and click to clear it.", true);
        }
    }
    public override string Prompt(PlayerInteraction p)
    {
        if (p.Held != null && p.Held.kind == PickupItem.ItemKind.Batter)
            return !IsOpen ? "Click to open the lid" : State == CookState.Empty ? "Hold left click to pour • Click to close lid" : "Click to close lid • Put down bottle to take waffle";
        if (p.Held != null) return "Put down your item to use the waffle maker";
        if (State == CookState.Cooking) return "Cooking waffle...";
        if (State == CookState.Ready) return IsOpen ? "Click to take the cone" : "Waffle ready • Click to open";
        if (State == CookState.Burned) return IsOpen ? "Click to discard burned waffle" : "Burned waffle • Click to open";
        if (State == CookState.BatterReady) return "Click to close and cook";
        return IsOpen ? "Add batter • Click to close lid" : "Click to open waffle maker";
    }
    public override void Use(PlayerInteraction p)
    {
        if (p.Held != null)
        {
            if (p.Held.kind == PickupItem.ItemKind.Batter)
            {
                ToggleLid(p);
            }
            else p.Notify(Prompt(p), true);
            return;
        }
        if (State == CookState.Cooking) return;
        if (!IsOpen) { IsOpen = true; p.Play(p.actionSound); return; }
        if (State == CookState.Ready)
        {
            var cone = Instantiate(conePrefab);
            p.PickUp(cone);
            ResetWaffle();
        }
        else if (State == CookState.Burned) { ResetWaffle(); p.Notify("Waffle maker cleared"); }
        else if (State == CookState.BatterReady)
        {
            IsOpen = false;
            State = CookState.Cooking;
            cookTime = 0;
            p.Play(p.actionSound);
        }
        else IsOpen = false;
    }
    public override bool CanGesture(PlayerInteraction p)
    {
        return IsOpen && State == CookState.Empty && p.Held != null && p.Held.kind == PickupItem.ItemKind.Batter && (p.stock == null || BatterProgress > 0 || p.stock.Has(RouteStock.Ingredient.Batter));
    }
    public void ToggleLid(PlayerInteraction p)
    {
        IsOpen = !IsOpen;
        StopGesture();
        if (!IsOpen && State == CookState.BatterReady)
        {
            State = CookState.Cooking;
            cookTime = 0;
        }
        p.Play(p.actionSound);
    }
    public override void Gesture(PlayerInteraction p, Vector2 delta, float dt)
    {
        if (!CanGesture(p)) return;
        if (BatterProgress == 0 && p.stock != null) p.stock.Consume(RouteStock.Ingredient.Batter);
        pourStream.enabled = true;
        pourStream.SetPosition(0, p.Held.transform.TransformPoint(new Vector3(0,.24f,0)));
        pourStream.SetPosition(1, rawBatter.transform.position + Vector3.up * .02f);
        BatterProgress = Mathf.Min(1, BatterProgress + dt / settings.pourSeconds);
        rawBatter.SetActive(true);
        rawBatter.transform.localScale = Vector3.one * Mathf.Lerp(.15f, 1, BatterProgress);
        p.GestureSound(p.pourSound);
        if (BatterProgress >= 1)
        {
            State = CookState.BatterReady;
            pourStream.enabled = false;
        }
    }
    public override void StopGesture()
    {
        pourStream.enabled = false;
    }
    private void ResetWaffle()
    {
        State = CookState.Empty;
        BatterProgress = 0;
        cookTime = 0;
        rawBatter.SetActive(false);
        cookedWaffle.SetActive(false);
        pourStream.enabled = false;
    }
}
