using UnityEngine;
using UnityEngine.UI;

public class TycoonWaffleFeedback : MonoBehaviour
{
    public TycoonPart part;
    public Transform rawBatter;
    public GameObject cookedWaffle;
    public Renderer[] waffleRenderers;
    public Material[] cookedMaterials;
    public Material burnedMaterial;
    public Canvas canvas;
    public GameObject panel, clickIcon, useKey;
    public Image ring, burnRing;
    public LineRenderer pourStream;
    public AudioClip pourSound, actionSound, readySound;
    public float lidAnimationSpeed = 8;
    public static readonly Vector3 BottleNozzle = new Vector3(0, .26f, 0);
    private Transform pouringHand;
    private int pourFrame = -1, previousStage;
    private float nextPourSound;
    private bool wasReady;

    private void Start()
    {
        canvas.worldCamera = part.game.player.view;
        previousStage = part.ironStage;
        wasReady = part.cookTime >= 6;
    }

    public void PourFrom(Transform hand)
    {
        pouringHand = hand;
        pourFrame = Time.frameCount;
    }

    public void StopPour()
    {
        pourFrame = -1;
        pourStream.enabled = false;
    }

    private void LateUpdate()
    {
        var game = part.game;
        int stage = part.ironStage;
        bool ready = (stage == 2 && part.cookTime >= 6) || stage == 3;
        bool burned = stage == 4;
        if (!game.Paused)
        {
            part.lid.localRotation = Quaternion.Slerp(part.lid.localRotation,
                Quaternion.Euler(stage == 2 ? 0 : -105, 0, 0), 1 - Mathf.Exp(-lidAnimationSpeed * Time.deltaTime));
            if (ready && !wasReady) game.PreparationSound(readySound, part.transform.position);
            if (stage != previousStage && (stage == 2 || stage == 3)) game.PreparationSound(actionSound, part.transform.position);
        }
        wasReady = ready;
        previousStage = stage;
        rawBatter.gameObject.SetActive(stage == 5 || stage == 1 || stage == 2 && !ready);
        rawBatter.localScale = Vector3.one * Mathf.Lerp(.15f, 1, part.pourProgress);
        cookedWaffle.SetActive(ready || burned);
        for (int i = 0; i < waffleRenderers.Length; i++)
            waffleRenderers[i].sharedMaterial = burned ? burnedMaterial : cookedMaterials[i];

        var player = game.player;
        bool active = stage != 0;
        panel.SetActive(!game.Paused && player.vehicle == null &&
            Vector3.Distance(player.view.transform.position, part.transform.position) < 3.5f && (active || player.target == part));
        canvas.transform.rotation = player.view.transform.rotation;
        bool finished = ready || stage == 1;
        ring.fillAmount = finished || burned ? 1 : Mathf.Max(.04f, stage == 2 ? part.cookTime / 6 : stage == 5 ? part.pourProgress : 0);
        ring.color = burned ? new Color(.93f, .25f, .23f) : finished ? new Color(.3f, .8f, .52f) : active ? new Color(1, .68f, .25f) : new Color(.78f, .8f, .83f);
        burnRing.gameObject.SetActive(stage == 2 && ready || burned);
        burnRing.fillAmount = Mathf.Clamp01((part.cookTime - 6) / 12);
        clickIcon.SetActive(stage == 0 || stage == 5 || burned);
        useKey.SetActive(stage == 1 || ready);

        pourStream.enabled = !game.Paused && stage == 5 && pourFrame == Time.frameCount;
        if (pourStream.enabled)
        {
            pourStream.SetPosition(0, pouringHand.TransformPoint(BottleNozzle));
            pourStream.SetPosition(1, part.contentPoint.position + part.transform.up * .02f);
            if (Time.time >= nextPourSound)
            {
                game.PreparationSound(pourSound, part.transform.position);
                nextPourSound = Time.time + .22f;
            }
        }
    }
}
