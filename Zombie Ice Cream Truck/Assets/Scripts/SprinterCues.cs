using Quantum;
using UnityEngine;

// Makes sprinters easy to hear coming: a shriek the first time one charges within earshot of the local player, and a
// patter of running footsteps that gets louder the faster it moves. View only.
public class SprinterCues : QuantumEntityViewComponent
{
    [SerializeField] private AudioSource shriekSource;
    [SerializeField] private AudioClip[] shrieks;
    [SerializeField] private AudioSource footsteps;
    [SerializeField] private float alertRange = 35f;
    [SerializeField] private float fullSpeed = 5f;
    private bool alerted;
    private Vector3 lastPosition;

    public override void OnActivate(Frame frame)
    {
        alerted = false;
        lastPosition = transform.position;
        footsteps.volume = 0;
        footsteps.Play();
    }

    public override void OnUpdateView()
    {
        var zombie = GetPredictedQuantumComponent<Zombie>();
        var moved = transform.position - lastPosition;
        lastPosition = transform.position;
        moved.y = 0;
        var speed = moved.magnitude / Mathf.Max(Time.deltaTime, 0.0001f);
        var running = zombie.State == ZombieState.Chasing && zombie.FrozenTimer <= 0;
        footsteps.volume = Mathf.MoveTowards(footsteps.volume, running ? Mathf.Clamp01(speed / fullSpeed) : 0, Time.deltaTime * 4f);
        if (alerted || !running || (Camera.main.transform.position - transform.position).sqrMagnitude > alertRange * alertRange) return;
        alerted = true;
        shriekSource.pitch = Random.Range(0.9f, 1.15f);
        shriekSource.PlayOneShot(shrieks[Random.Range(0, shrieks.Length)]);
    }
}
