using UnityEngine;

// World-space floating text (lunch money, HONK!, BUSTED!, tips) that pops in, rises, faces the camera and fades.
public class DadsPopup : MonoBehaviour
{
    [SerializeField] private TextMesh text;
    [SerializeField] private float riseSpeed = 1.5f;
    [SerializeField] private float lifetime = 1.3f;
    private float age;
    private float size;

    public void Show(string message, Color color, float scale)
    {
        text.text = message;
        text.color = color;
        size = scale;
        transform.position += Random.insideUnitSphere * 0.25f;
        Destroy(gameObject, lifetime);
    }

    private void Update()
    {
        age += Time.deltaTime;
        var eye = DadsCamera.Instance.transform;
        transform.position += Vector3.up * riseSpeed * Time.deltaTime;
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
