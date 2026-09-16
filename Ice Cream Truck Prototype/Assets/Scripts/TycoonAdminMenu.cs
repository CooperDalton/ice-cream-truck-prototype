using System.Globalization;
using UnityEngine;
using UnityEngine.UI;

public class TycoonAdminMenu : MonoBehaviour
{
    public TycoonGameManager game;
    public GameObject panel;
    public InputField levelInput, cashInput;
    public Text summary, status;
    public Button setLevelButton, addCashButton, setCashButton, skipTutorialButton, finishDayButton, closeButton;

    private void Start()
    {
        setLevelButton.onClick.AddListener(SetLevel);
        addCashButton.onClick.AddListener(() => ChangeCash(true));
        setCashButton.onClick.AddListener(() => ChangeCash(false));
        skipTutorialButton.onClick.AddListener(SkipTutorial);
        finishDayButton.onClick.AddListener(FinishDay);
        closeButton.onClick.AddListener(Toggle);
    }

    public void Toggle()
    {
        if (game.loadingCampaign) return;
        bool open = !panel.activeSelf;
        if (open)
        {
            if (game.phase != TycoonGameManager.Phase.Results) game.hud.ClosePanels();
            levelInput.text = game.level.ToString(); cashInput.text = "1000";
            status.text = "Changes are saved to this campaign.";
            RefreshSummary();
        }
        panel.SetActive(open);
        Time.timeScale = game.Paused ? 0 : 1;
        bool unlocked = game.hud.AnyPanel || game.phase == TycoonGameManager.Phase.Results;
        Cursor.lockState = unlocked ? CursorLockMode.None : CursorLockMode.Locked;
        Cursor.visible = unlocked;
    }

    public void SetLevel()
    {
        if (!int.TryParse(levelInput.text, out int level) || level < 1 || level > 7)
        { status.text = "Enter a level from 1 to 7."; return; }
        game.level = level;
        game.xp = TycoonCatalogSO.Thresholds[level - 1];
        game.Save(); RefreshSummary();
        status.text = "Level set. Ingredients unlocked; supplies stay as they are.";
    }

    public void ChangeCash(bool add)
    {
        if (!float.TryParse(cashInput.text, NumberStyles.AllowDecimalPoint, CultureInfo.InvariantCulture, out float amount)
            || float.IsNaN(amount) || float.IsInfinity(amount) || amount < 0 || amount > 1000000)
        { status.text = "Enter a cash amount from 0 to 1,000,000."; return; }
        game.cash = add ? game.cash + amount : amount;
        game.Save(); RefreshSummary();
        status.text = add ? "Cash added and saved." : "Cash set and saved.";
    }

    public void SkipTutorial()
    {
        game.tutorial.progress.step = TycoonTutorial.Step.Complete;
        game.Save(); RefreshSummary();
        status.text = "Tutorial skipped. Place and stock equipment as needed.";
    }

    public void FinishDay()
    {
        if (game.phase != TycoonGameManager.Phase.Trading) return;
        panel.SetActive(false);
        game.CloseDay();
    }

    private void RefreshSummary()
    {
        summary.text = "Level " + game.level + "   |   $" + game.cash.ToString("0.##") + "   |   Day " + game.day;
        skipTutorialButton.interactable = game.tutorial.Active;
        finishDayButton.interactable = game.phase == TycoonGameManager.Phase.Trading;
    }
}
