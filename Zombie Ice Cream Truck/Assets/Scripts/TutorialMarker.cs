using Quantum;
using UnityEngine;

// A bobbing "!" over whatever the current tutorial step is about: the milk crate or sugar sack, the churn, the new tub
// or the freezer, the fuel intake, the practice zombie, then the driver's seat. Hidden outside the tutorial.
public class TutorialMarker : MonoBehaviour
{
    [SerializeField] private TextMesh marker;
    [Tooltip("Height of the marker over a pickup on the ground, a station or the driver's seat, and a zombie's feet.")]
    [SerializeField] private float pickupHeight = 0.8f;
    [SerializeField] private float stationHeight = 1.5f;
    [SerializeField] private float zombieHeight = 2.4f;
    [SerializeField] private float bobHeight = 0.12f;

    private unsafe void Update()
    {
        var frame = QuantumRunner.Default?.Game?.Frames.Predicted;
        var tutorial = frame != null && frame.Global->Phase == GamePhase.Tutorial;
        marker.gameObject.SetActive(tutorial);
        if (!tutorial) return;
        marker.transform.position = Target(frame) + Vector3.up * bobHeight * Mathf.Sin(Time.time * 4f);
        marker.transform.rotation = Camera.main.transform.rotation;
    }

    // Where the marker floats for the current step.
    private unsafe Vector3 Target(Frame frame)
    {
        var step = frame.Global->Tutorial;
        var truck = frame.Get<Transform3D>(frame.GetSingletonEntityRef<Truck>());
        var wanted = step == TutorialStep.GrabMilk ? ItemKind.MilkCrate : step == TutorialStep.GrabSugar ? ItemKind.SugarSack
            : step == TutorialStep.Freezer ? ItemKind.Tub : ItemKind.None;
        // Stops and hot spots up the road hold the same items; the tutorial's are the ones by the truck.
        var nearest = float.MaxValue;
        Vector3? item = null;
        foreach (var pair in frame.GetComponentIterator<Pickup>())
        {
            if (wanted == ItemKind.None || pair.Component.Item.Kind != wanted) continue;
            var position = frame.Get<Transform3D>(pair.Entity).Position.ToUnityVector3();
            var distance = (position - truck.Position.ToUnityVector3()).sqrMagnitude;
            if (distance >= nearest) continue;
            nearest = distance;
            item = position;
        }
        if (item.HasValue) return item.Value + Vector3.up * pickupHeight;
        if (step == TutorialStep.Fight)
        {
            foreach (var pair in frame.GetComponentIterator<Zombie>())
            {
                if (pair.Component.State != ZombieState.Dead) return frame.Get<Transform3D>(pair.Entity).Position.ToUnityVector3() + Vector3.up * zombieHeight;
            }
        }
        if (step == TutorialStep.Drive || step == TutorialStep.Fight)
        {
            var settings = frame.FindAsset(frame.RuntimeConfig.Settings);
            return truck.TransformPoint(settings.DriverSeat).ToUnityVector3() + Vector3.up * pickupHeight;
        }
        var station = step == TutorialStep.Freezer || step == TutorialStep.Scoop ? StationKind.Freezer
            : step == TutorialStep.Fuel ? StationKind.FuelIntake : StationKind.Churn;
        foreach (var pair in frame.GetComponentIterator<Station>())
        {
            if (pair.Component.Kind == station) return frame.Get<Transform3D>(pair.Entity).Position.ToUnityVector3() + Vector3.up * stationHeight;
        }
        throw new System.InvalidOperationException($"No {station} station for tutorial step {step}");
    }
}
