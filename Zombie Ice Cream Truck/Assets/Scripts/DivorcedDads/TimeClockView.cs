using Quantum;
using UnityEngine;

// The punch clock at the lot: tells the dads whether they can clock out yet.
public class TimeClockView : QuantumEntityViewComponent
{
    [SerializeField] private TextMesh label;

    public override void OnUpdateView()
    {
        var run = PredictedFrame.GetSingleton<DadsRun>();
        var working = run.Phase == DayPhase.Day || run.Phase == DayPhase.Dusk || run.Phase == DayPhase.Night;
        label.text = working ? "CLOCK OUT\npay Big Dairy" : "GO SELL\nSOME ICE CREAM";
        label.color = working ? new Color(1f, 0.88f, 0.29f) : Color.gray;
        label.transform.rotation = DadsCamera.Instance.transform.rotation;
    }
}
