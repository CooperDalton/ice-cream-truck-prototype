using UnityEngine;
using UnityEngine.SceneManagement;

// The first scene of a build: single player (the game scene starts a local game by itself) or multiplayer (the Quantum
// online menu, with the game already picked in its scene list).
public class GameMenu : MonoBehaviour
{
    // Where the Quantum online menu keeps its scene choice (QuantumMenuConnectArgs.LoadFromPlayerPrefs).
    private const string OnlineSceneKey = "Photon.Menu.SceneName";

    [Tooltip("The game's QuantumMenuSceneInfo name, which the online menu matches its scene choice against.")]
    [SerializeField] private string gameName;
    [SerializeField] private string gameScene;
    [SerializeField] private string onlineMenuScene = "Assets/Photon/QuantumMenu/QuantumSampleMenu.unity";

    private void Awake()
    {
        Cursor.lockState = CursorLockMode.None;
        Cursor.visible = true;
    }

    public void Play(bool online)
    {
        if (!online)
        {
            SceneManager.LoadScene(gameScene);
            return;
        }
        PlayerPrefs.SetString(OnlineSceneKey, gameName);
        SceneManager.LoadScene(onlineMenuScene);
    }
}
