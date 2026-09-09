using UnityEngine;
using UnityEngine.UI;

public class PauseSettings : MonoBehaviour
{
    public PlayerController player;
    public Slider sensitivity;
    public Text sensitivityValue;
    public Slider musicVolume, effectsVolume;
    public Text musicValue, effectsValue;

    private void OnEnable()
    {
        sensitivity.SetValueWithoutNotify(player.MouseSensitivity);
        sensitivityValue.text = (player.MouseSensitivity / .1f).ToString("0.0") + "x";
        sensitivity.onValueChanged.AddListener(ChangeSensitivity);
        musicVolume.SetValueWithoutNotify(PlayerPrefs.GetFloat("MusicVolume", 1));
        effectsVolume.SetValueWithoutNotify(PlayerPrefs.GetFloat("EffectsVolume", 1));
        musicValue.text = Mathf.RoundToInt(musicVolume.value * 100) + "%";
        effectsValue.text = Mathf.RoundToInt(effectsVolume.value * 100) + "%";
        musicVolume.onValueChanged.AddListener(ChangeMusicVolume);
        effectsVolume.onValueChanged.AddListener(ChangeEffectsVolume);
    }

    private void OnDisable()
    {
        sensitivity.onValueChanged.RemoveListener(ChangeSensitivity);
        musicVolume.onValueChanged.RemoveListener(ChangeMusicVolume);
        effectsVolume.onValueChanged.RemoveListener(ChangeEffectsVolume);
        PlayerPrefs.Save();
    }

    private void ChangeSensitivity(float value)
    {
        player.SetMouseSensitivity(value);
        sensitivityValue.text = (player.MouseSensitivity / .1f).ToString("0.0") + "x";
    }

    private void ChangeMusicVolume(float value)
    {
        PlayerPrefs.SetFloat("MusicVolume", value);
        musicValue.text = Mathf.RoundToInt(value * 100) + "%";
    }

    private void ChangeEffectsVolume(float value)
    {
        PlayerPrefs.SetFloat("EffectsVolume", value);
        effectsValue.text = Mathf.RoundToInt(value * 100) + "%";
    }
}
