using UnityEngine;

public class TycoonTubVisual : MonoBehaviour
{
    public Renderer[] fill;
    private Vector3[] scales, positions;
    private void Awake()
    {
        scales = new Vector3[fill.Length]; positions = new Vector3[fill.Length];
        for (int i = 0; i < fill.Length; i++) { scales[i] = fill[i].transform.localScale; positions[i] = fill[i].transform.localPosition; }
    }
    public void SetFill(float remaining)
    {
        for (int i = 0; i < fill.Length; i++)
        {
            fill[i].enabled = remaining > 0;
            fill[i].transform.localScale = new Vector3(scales[i].x, scales[i].y * Mathf.Max(.03f, remaining), scales[i].z);
            fill[i].transform.localPosition = positions[i] - Vector3.up * (1 - remaining) * .075f;
        }
    }
}
