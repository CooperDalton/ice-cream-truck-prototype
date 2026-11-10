using UnityEngine;

// World-space floating text (lunch money, HONK!, BUSTED!, tips) that pops in, rises, faces the camera and fades. It
// can ride along above someone (a paid kid walking off) for as long as they are around.
public class DadsPopup : MonoBehaviour
{
    [SerializeField] private TextMesh text;
    [SerializeField] private float riseSpeed = 1.5f;
    [SerializeField] private float lifetime = 1.3f;
    [Tooltip("Rise speed while following someone.")]
    [SerializeField] private float followRiseSpeed = 0.35f;
    private float age;
    private float size;
    private Transform follow;
    private Vector3 offset;

    // seconds 0 keeps the authored lifetime; without a follow target the popup jitters a little and rises on its own.
    public void Show(string message, Color color, float scale, Transform target = null, float seconds = 0)
    {
        text.text = message;
        text.color = color;
        size = scale;
        if (seconds > 0) lifetime = seconds;
        follow = target;
        if (target == null) transform.position += Random.insideUnitSphere * 0.25f;
        else offset = transform.position - target.position;
        Destroy(gameObject, lifetime);
    }

    private void Update()
    {
        age += Time.deltaTime;
        var eye = DadsCamera.Instance.transform;
        // The kid may go home (and their view with them) before the popup is done; it then rises on its own.
        if (follow != null)
        {
            offset += Vector3.up * followRiseSpeed * Time.deltaTime;
            transform.position = follow.position + offset;
        }
        else transform.position += Vector3.up * riseSpeed * Time.deltaTime;
        transform.rotation = eye.rotation;
        var pop = age < 0.12f ? Mathf.Lerp(0.2f, 1.5f, age / 0.12f) : Mathf.Lerp(1.5f, 1f, (age - 0.12f) / 0.15f);
        // Far popups grow so they stay readable at the low PS1 resolution.
        var distance = (transform.position - eye.position).magnitude;
        transform.localScale = Vector3.one * size * pop * Mathf.Max(1, distance / 6);
        var color = text.color;
        color.a = Mathf.Clamp01(2 * (1 - age / lifetime));
        text.color = color;
    }
}
