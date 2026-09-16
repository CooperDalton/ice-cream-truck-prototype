using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.UI;

public class GameModeMenu : MonoBehaviour
{
    public bool mainMenu;
    public Button freeDriveButton, parkRouteButton, tycoonButton;
    public static GameModeMenu Instance { get; private set; }
    private void Awake()
    {
        if (mainMenu) Instance = this;
    }
    private void Start()
    {
        if (!mainMenu) return;
        Time.timeScale = 1;
        Cursor.lockState = CursorLockMode.None;
        Cursor.visible = true;
    }
    public void FreeDrive()
    {
        DayManager.BeginRun();
        SceneManager.LoadScene("IceCreamPrototype");
    }
    public void ParkRoute()
    {
        RouteGameManager.BeginRun();
        SceneManager.LoadScene("ParkRoute");
    }
    public void Tycoon()
    {
        Time.timeScale = 1;
        SceneManager.LoadScene("IceCreamTycoon");
    }
    public void ReturnToMenu()
    {
        Cursor.lockState = CursorLockMode.None;
        Cursor.visible = true;
        SceneManager.LoadScene("MainMenu");
    }
}
