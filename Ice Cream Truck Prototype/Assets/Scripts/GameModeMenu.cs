using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.UI;

public class GameModeMenu : MonoBehaviour
{
    public bool mainMenu;
    public Button freeDriveButton, parkRouteButton;
    public static GameModeMenu Instance { get; private set; }
    private void Awake()
    {
        if (mainMenu) Instance = this;
    }
    private void Start()
    {
        if (!mainMenu) return;
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
    public void ReturnToMenu()
    {
        Cursor.lockState = CursorLockMode.None;
        Cursor.visible = true;
        SceneManager.LoadScene("MainMenu");
    }
}
