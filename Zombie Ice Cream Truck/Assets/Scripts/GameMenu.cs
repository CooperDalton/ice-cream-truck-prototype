using System;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.UI;

// The first scene of a build: pick a game, then single player (its scene starts a local game by itself) or multiplayer
// (the Quantum online menu, with that game already picked in its scene list).
public class GameMenu : MonoBehaviour
{
    [Serializable]
    public struct Game
    {
        [Tooltip("The game's QuantumMenuSceneInfo name, which the online menu matches its scene choice against.")]
        public string Name;
        public string ScenePath;
    }

    // Where the Quantum online menu keeps its scene choice (QuantumMenuConnectArgs.LoadFromPlayerPrefs).
    private const string OnlineSceneKey = "Photon.Menu.SceneName";

    [SerializeField] private Game[] games;
    [SerializeField] private string onlineMenuScene = "Assets/Photon/QuantumMenu/QuantumSampleMenu.unity";
    [SerializeField] private GameObject gameScreen;
    [SerializeField] private GameObject modeScreen;
    [SerializeField] private Text modeTitle;
    private int chosen;

    private void Awake()
    {
        Cursor.lockState = CursorLockMode.None;
        Cursor.visible = true;
    }

    public void Pick(int game)
    {
        chosen = game;
        modeTitle.text = games[game].Name.ToUpper();
        gameScreen.SetActive(false);
        modeScreen.SetActive(true);
    }

    public void Back()
    {
        modeScreen.SetActive(false);
        gameScreen.SetActive(true);
    }

    public void Play(bool online)
    {
        var game = games[chosen];
        if (!online)
        {
            SceneManager.LoadScene(game.ScenePath);
            return;
        }
        PlayerPrefs.SetString(OnlineSceneKey, game.Name);
        SceneManager.LoadScene(onlineMenuScene);
    }
}
