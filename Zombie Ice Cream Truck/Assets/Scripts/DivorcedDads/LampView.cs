using Quantum;
using UnityEngine;

// A street lamp along the roads: lit after dusk (on every other road cell, its fixture Index 1), mowed down when the van
// hits it fast enough. It tips over away from the van, goes dark, and stands again the next morning.
public class LampView : QuantumEntityViewComponent
{
    [Tooltip("Pivot at the foot of the pole; the lamp model hangs under it.")]
    [SerializeField] private Transform pole;
    [SerializeField] private GameObject lamp;
    [SerializeField] private float fallSpeed = 5f;
    private bool down;
    private Quaternion fallen;

    public override void OnUpdateView()
    {
        var fixture = GetPredictedQuantumComponent<Fixture>();
        var frame = PredictedFrame;
        var settings = frame.FindAsset(frame.RuntimeConfig.DadsSettings);
        if (fixture.Open && !down)
        {
            // Away from where the van came from, in the pole's own space.
            var away = transform.position - frame.Get<Transform3D>(frame.GetSingletonEntityRef<Van>()).Position.ToUnityVector3();
            away.y = 0;
            var axis = Vector3.Cross(Vector3.up, away.sqrMagnitude > 0.01f ? away.normalized : transform.forward);
            fallen = Quaternion.Inverse(transform.rotation) * Quaternion.AngleAxis(85f, axis) * transform.rotation;
        }
        down = fixture.Open;
        pole.localRotation = down ? Quaternion.Slerp(pole.localRotation, fallen, 1 - Mathf.Exp(-fallSpeed * Time.deltaTime)) : Quaternion.identity;
        var dark = frame.GetSingleton<DadsRun>().Clock.AsFloat >= settings.DuskAt.AsFloat - 0.03f;
        lamp.SetActive(!down && fixture.Index == 1 && dark);
    }
}
