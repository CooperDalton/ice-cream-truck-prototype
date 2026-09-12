using System;
using System.Collections;
using System.Linq;
using UnityEngine;
using UnityEngine.UI;

public class TycoonDaySummary : MonoBehaviour
{
    [Serializable] public class UnlockView { public GameObject root; public Image icon; public Text label; }
    public TycoonGameManager game;
    public RectTransform window;
    public Text title, sales, costs, cash, missed, earnedXP, level, progress, unlockTitle;
    public Image xpFill;
    public CanvasGroup unlockGroup;
    public RectTransform unlockContent;
    public ScrollRect unlockScroll;
    public UnlockView[] unlocks;
    public Button continueButton;
    public int DisplayedLevel { get; private set; }
    public bool Finished { get; private set; }
    private int startLevel;
    private float startXP, shownXP;

    private void Awake()
    {
        continueButton.onClick.AddListener(() => {
            if (!Finished) return;
            game.NextDay(); game.hud.ClosePanels();
        });
    }
    public void Begin()
    {
        gameObject.SetActive(true);
        Finished = false; continueButton.interactable = false;
        title.text = "Day " + game.day + " complete";
        sales.text = "$" + game.salesToday.ToString("0.00");
        costs.text = "$" + game.wagesToday.ToString("0.00");
        cash.text = "$" + game.cash.ToString("0.00");
        missed.text = game.sites.Sum(s => s.lostSales).ToString();
        startXP = Mathf.Max(0, game.xp - game.salesToday);
        shownXP = startXP; startLevel = 1;
        while (startLevel < game.level && startXP >= TycoonCatalogSO.Thresholds[startLevel]) startLevel++;
        DisplayedLevel = startLevel;
        unlockGroup.gameObject.SetActive(false); unlockGroup.alpha = 0;
        window.sizeDelta = new Vector2(640, 390);
        foreach (var card in unlocks) card.root.SetActive(false);
        RefreshProgress();
        StartCoroutine(AnimateXP());
    }
    private IEnumerator AnimateXP()
    {
        yield return new WaitForSecondsRealtime(.35f);
        while (shownXP < game.xp)
        {
            float from = shownXP;
            float target = DisplayedLevel < 7 ? Mathf.Min(game.xp, TycoonCatalogSO.Thresholds[DisplayedLevel]) : game.xp;
            float elapsed = 0;
            while (elapsed < 1.1f)
            {
                elapsed += Time.unscaledDeltaTime;
                shownXP = Mathf.Lerp(from, target, Mathf.SmoothStep(0, 1, elapsed / 1.1f));
                RefreshProgress(); yield return null;
            }
            shownXP = target; RefreshProgress();
            if (DisplayedLevel < game.level && shownXP >= TycoonCatalogSO.Thresholds[DisplayedLevel])
            {
                yield return new WaitForSecondsRealtime(.2f);
                DisplayedLevel++; RefreshProgress();
                game.feedback.PlayOneShot(game.upgradeSound, .3f);
                for (float pulse = 0; pulse < .3f; pulse += Time.unscaledDeltaTime)
                {
                    level.transform.localScale = Vector3.one * (1 + .16f * Mathf.Sin(pulse / .3f * Mathf.PI));
                    yield return null;
                }
                level.transform.localScale = Vector3.one;
            }
        }
        yield return new WaitForSecondsRealtime(.25f);
        if (DisplayedLevel > startLevel)
        {
            float height = PopulateUnlocks();
            unlockGroup.gameObject.SetActive(true);
            for (float elapsed = 0; elapsed < .3f; elapsed += Time.unscaledDeltaTime)
            {
                float t = Mathf.SmoothStep(0, 1, elapsed / .3f);
                window.sizeDelta = new Vector2(640, Mathf.Lerp(390, height, t));
                unlockGroup.alpha = t; yield return null;
            }
            window.sizeDelta = new Vector2(640, height); unlockGroup.alpha = 1;
        }
        Finished = true; continueButton.interactable = true;
    }
    private void RefreshProgress()
    {
        earnedXP.text = "+" + (shownXP - startXP).ToString("0.#") + " XP";
        level.text = "Level " + DisplayedLevel;
        if (DisplayedLevel == 7) { xpFill.fillAmount = 1; progress.text = "Max level"; }
        else
        {
            float floor = TycoonCatalogSO.Thresholds[DisplayedLevel - 1];
            float needed = TycoonCatalogSO.Thresholds[DisplayedLevel] - floor;
            xpFill.fillAmount = (shownXP - floor) / needed;
            progress.text = (shownXP - floor).ToString("0.#") + " / " + needed.ToString("0") + " XP";
        }
    }
    private float PopulateUnlocks()
    {
        unlockTitle.text = "Unlocked";
        int count = 0;
        for (int unlocked = startLevel + 1; unlocked <= DisplayedLevel; unlocked++)
        {
            bool flavor = unlocked % 2 == 0;
            int first = flavor ? unlocked == 2 ? 2 : unlocked == 4 ? 4 : 8 : unlocked == 3 ? 0 : unlocked == 5 ? 2 : 4;
            int amount = flavor && unlocked > 2 ? 4 : 2;
            for (int i = first; i < first + amount; i++)
            {
                var card = unlocks[count++]; card.root.SetActive(true);
                card.icon.sprite = flavor ? game.catalog.tubIcons[i] : game.catalog.toppingIcons[i];
                card.label.text = flavor ? TycoonCatalogSO.FlavorNames[i] : TycoonCatalogSO.ToppingNames[i];
            }
        }
        unlockContent.sizeDelta = new Vector2(568, Mathf.Ceil(count / 4f) * 92);
        float visibleHeight = Mathf.Min(2, Mathf.Ceil(count / 4f)) * 92 - 8;
        unlockScroll.viewport.sizeDelta = new Vector2(568, visibleHeight);
        unlockScroll.verticalNormalizedPosition = 1;
        return 420 + visibleHeight;
    }
}
