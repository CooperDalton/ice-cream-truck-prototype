using UnityEngine;

public class Boombox : PickupItem
{
    public PrototypeSettingsSO settings;
    public PlayerInteraction player;
    public TruckController truck;
    public AudioSource music;
    public bool Playing { get; private set; }
    public override string Prompt(PlayerInteraction p) => "Click to pick up and play • Q to drop boombox";
    public override void OnPickedUp()
    {
        if (!Playing) ToggleMusic();
    }
    void Update()
    {
        music.volume = player.day.CanPlay ? settings.soundVolume * .6f * PlayerPrefs.GetFloat("MusicVolume", 1) : 0;
    }
    public void ToggleMusic()
    {
        Playing = !Playing;
        if (Playing) music.Play(); else music.Stop();
        player.Notify(Playing ? "Music on. Nearby people can hear you" : "Music off");
    }
}
