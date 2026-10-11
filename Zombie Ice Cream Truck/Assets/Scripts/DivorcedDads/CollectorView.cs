using Quantum;
using UnityEngine;

// Big Dairy at his payment window: turns to watch the nearest dad and says something menacing about money.
public class CollectorView : QuantumEntityViewComponent
{
    [SerializeField] private Transform model;
    [SerializeField] private TextMesh speech;
    [SerializeField] private string[] lines =
    {
        "You got my money?", "Milk ain't free, pal.", "Tick tock, dads.", "Big Dairy always collects.",
        "Nice truck. Be a shame if\nsomething happened to it.", "Your ex says hi.", "Moo-ve along.",
    };
    private float lineTimer;
    private int line;

    public override void OnUpdateView()
    {
        var frame = PredictedFrame;
        var run = frame.GetSingleton<DadsRun>();
        var nearest = 12f;
        var target = transform.position + transform.forward;
        foreach (var pair in frame.GetComponentIterator<Dad>())
        {
            var position = frame.Get<Transform3D>(pair.Entity).Position.ToUnityVector3();
            var distance = Vector3.Distance(position, transform.position);
            if (distance >= nearest) continue;
            nearest = distance;
            target = position;
        }
        var look = target - model.position;
        look.y = 0;
        if (look.sqrMagnitude > 0.01f) model.rotation = Quaternion.Slerp(model.rotation, Quaternion.LookRotation(look), 1 - Mathf.Exp(-4 * Time.deltaTime));
        lineTimer -= Time.deltaTime;
        if (lineTimer <= 0)
        {
            lineTimer = 5;
            line = (line + 1) % lines.Length;
        }
        speech.text = run.Phase == DayPhase.Morning ? lines[line] + "\n\nSELL $" + run.Due + " TODAY" : lines[line];
        speech.transform.rotation = DadsCamera.Instance.transform.rotation;
    }
}
