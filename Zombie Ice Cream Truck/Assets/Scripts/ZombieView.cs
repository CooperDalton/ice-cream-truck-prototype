using System;
using Quantum;
using UnityEngine;
using Random = UnityEngine.Random;

// Zombie presentation: picks one of the outfit variants, groans, flinches when hit, tumbles the corpse while it flies,
// throws its arms off on death (and pops the head off on headshots and run-overs, with a geyser from the neck), and
// encases it in ice while frozen by mint. The variant choice is cosmetic and local to each client.
public class ZombieView : QuantumEntityViewComponent
{
    [Serializable]
    public struct Variant
    {
        public GameObject Root;
        public Transform[] Limbs;
        public Transform Head;
    }

    [SerializeField] private Transform model;
    [SerializeField] private Variant[] variants;
    [SerializeField] private GameObject iceBlock;
    [SerializeField] private FxBurst neckGeyserPrefab;
    [SerializeField] private FxBurst iceShatterPrefab;
    [SerializeField] private AudioSource voice;
    [SerializeField] private AudioClip[] groans;
    [SerializeField] private Vector2 groanInterval = new Vector2(2.5f, 8f);
    [SerializeField] private float tumbleSpeed = 540f;
    [SerializeField] private float limbSpeed = 7f;
    private Vector3 tumbleAxis;
    private int variant;
    private bool frozen;
    private bool dead;
    private float groanTimer;
    private Vector3 flinch;

    public override void OnActivate(Frame frame)
    {
        model.localRotation = Quaternion.identity;
        tumbleAxis = Random.onUnitSphere;
        dead = false;
        frozen = false;
        variant = Random.Range(0, variants.Length);
        for (int i = 0; i < variants.Length; i++) variants[i].Root.SetActive(i == variant);
        groanTimer = Random.Range(0f, groanInterval.y);
    }

    public void Flinch(Vector3 direction)
    {
        direction.y = 0;
        flinch = direction.normalized * 0.25f;
    }

    public void Kill(bool popHead, Vector3 impulse)
    {
        if (dead) return;
        dead = true;
        voice.Stop();
        foreach (var limb in variants[variant].Limbs)
        {
            if (Random.value < 0.3f) continue;
            Throw(limb, impulse * 0.6f + Random.insideUnitSphere * limbSpeed + Vector3.up * limbSpeed * 0.5f);
        }
        if (!popHead) return;
        var head = variants[variant].Head;
        var neck = Instantiate(neckGeyserPrefab, head.parent);
        neck.transform.localPosition = head.localPosition;
        neck.transform.localRotation = Quaternion.identity;
        neck.Play(FlavorPalette.Gore, 1f);
        Throw(head, impulse * 0.3f + Vector3.up * Random.Range(9f, 13f) + Random.insideUnitSphere * 2f);
    }

    private static void Throw(Transform limb, Vector3 velocity)
    {
        limb.SetParent(null, true);
        var body = limb.gameObject.AddComponent<Rigidbody>();
        body.linearVelocity = velocity;
        body.angularVelocity = Random.insideUnitSphere * 20f;
        Destroy(limb.gameObject, 4f);
    }

    public override void OnUpdateView()
    {
        var zombie = GetPredictedQuantumComponent<Zombie>();
        var isFrozen = zombie.FrozenTimer > 0 && zombie.State != ZombieState.Dead;
        if (frozen && !isFrozen) Instantiate(iceShatterPrefab, transform.position + Vector3.up, Quaternion.identity).Play(FlavorPalette.Of(Flavor.Mint), 1f);
        frozen = isFrozen;
        iceBlock.SetActive(frozen);

        flinch = Vector3.Lerp(flinch, Vector3.zero, 1 - Mathf.Exp(-12 * Time.deltaTime));
        model.localPosition = transform.InverseTransformDirection(flinch);
        if (zombie.State == ZombieState.Dead)
        {
            if (transform.position.y > 0.05f) model.Rotate(tumbleAxis, tumbleSpeed * Time.deltaTime, Space.World);
            return;
        }
        groanTimer -= Time.deltaTime;
        if (groanTimer > 0 || frozen) return;
        groanTimer = Random.Range(groanInterval.x, groanInterval.y);
        voice.pitch = Random.Range(0.8f, 1.15f);
        voice.PlayOneShot(groans[Random.Range(0, groans.Length)]);
    }
}
