using UnityEngine;
using UnityEngine.InputSystem;

public class Boombox : PickupItem
{
    public PrototypeSettingsSO settings;
    public PlayerInteraction player;
    public TruckController truck;
    public AudioSource music;
    public bool Playing { get; private set; }
    public override string Prompt(PlayerInteraction p) => "Click to carry boombox • Q toggles music";
    void Update()
    {
        if (player.day.CanPlay && Keyboard.current.qKey.wasPressedThisFrame &&
            (player.Held == this || Vector3.Distance(player.transform.position, transform.position) < settings.reach)) ToggleMusic();
        music.volume = player.day.CanPlay ? settings.soundVolume * .6f : 0;
    }
    public void ToggleMusic()
    {
        Playing = !Playing;
        if (Playing) music.Play(); else music.Stop();
        player.Notify(Playing ? "Music on. Nearby people can hear you" : "Music off");
    }
    public override void ReturnHome(PlayerInteraction p)
    {
        if (truck.InsideTruck) { base.ReturnHome(p); transform.SetParent(truck.transform, true); return; }
        Vector3 point = p.transform.position + p.transform.forward * .9f + Vector3.up;
        if (!Physics.Raycast(point, Vector3.down, out var hit, 3, 1 << 11)) { p.Notify("Find clear ground for the boombox", true); return; }
        p.Release();
        transform.SetPositionAndRotation(hit.point + Vector3.up * .02f, Quaternion.Euler(0, p.transform.eulerAngles.y, 0));
    }
}
