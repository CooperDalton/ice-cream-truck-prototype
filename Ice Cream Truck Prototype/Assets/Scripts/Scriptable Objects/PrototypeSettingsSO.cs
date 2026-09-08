using UnityEngine;

[CreateAssetMenu(menuName = "Ice Cream/Prototype settings")]
public class PrototypeSettingsSO : ScriptableObject
{
    [Header("Day")]
    [Range(0, 23)] public int openingHour = 8;
    [Range(1, 24)] public int closingHour = 18;
    [Min(.1f)] public float secondsPerGameMinute = 12;
    public float dayDurationSeconds => (closingHour - openingHour) * 60 * secondsPerGameMinute;
    [Min(0)] public int quota = 100;
    [Min(0)] public int quotaIncreasePerDay = 25;
    [Min(1)] public float nextDayDelay = 8;
    [Header("Walking and camera")]
    [Min(.1f)] public float walkSpeed = 3;
    [Min(1)] public float sprintMultiplier = 1.65f;
    [Range(0, 15)] public float sprintFovIncrease = 5;
    [Min(0)] public float jumpHeight = .65f;
    [Header("Driving")]
    [Min(1)] public float truckSpeed = 10;
    [Min(1)] public float reverseSpeed = 4;
    [Min(.1f)] public float acceleration = 4;
    [Min(.1f)] public float braking = 12;
    [Range(5, 70)] public float steeringAngle = 32;
    [Min(1)] public float wheelbase = 4;
    [Min(1)] public float truckAttractionRadius = 22;
    [Min(1)] public float boomboxAttractionRadius = 38;
    [Min(.01f)] public float mouseSensitivity = .10f;
    public bool headBob = true;
    [Range(0, .12f)] public float bobAmplitude = .025f;
    [Min(.1f)] public float bobFrequency = 1.8f;
    [Min(1)] public float cameraSmoothing = 12;
    [Range(50, 100)] public float fieldOfView = 75;
    [Header("Interaction")]
    [Min(.5f)] public float reach = 3.8f;
    [Min(.1f)] public float pourSeconds = 1.5f;
    [Min(.1f)] public float cookSeconds = 6;
    [Min(.1f)] public float burnGraceSeconds = 12;
    [Min(10)] public float scoopMouseDistance = 400;
    [Min(10)] public float sprinkleMouseDistance = 280;
    [Min(.1f)] public float minimumScoopSeconds = 1;
    [Min(.1f)] public float minimumSprinkleSeconds = .7f;
    [Min(.1f)] public float lidAnimationSpeed = 8;
    [Range(1, 3)] public int maximumScoops = 3;
    [Header("Customers")]
    [Min(1)] public float firstCustomerDelay = 3;
    [Min(5)] public float customerPatience = 150;
    [Min(.1f)] public float customerWalkSpeed = 1.4f;
    [Min(.1f)] public float customerRunSpeed = 3.5f;
    [Min(.1f)] public float attractionCheckInterval = .5f;
    [Min(0)] public float repeatCustomerDelay = 60;
    [Range(0, 1)] public float sprinkleOrderChance = .4f;
    [Min(0)] public int conePrice = 2;
    [Min(0)] public int scoopPrice = 3;
    [Min(0)] public int sprinklePrice = 1;
    [Header("Neighborhood")]
    public bool randomizeWorldSeed = true;
    public int worldSeed = 4312;
    [Range(3, 5)] public int junctionsPerSide = 3;
    [Min(16)] public float tileSize = 24;
    [Range(0, 1)] public float extraRoadChance = .3f;
    [Range(0, 1)] public float parkChance = .35f;
    [Range(1, 12)] public int residentsPerHotspot = 5;
    [Range(0, 1)] public float parkChildChance = .85f;
    [Range(0, 1)] public float residentialChildChance = .25f;
    [Min(.2f)] public float navigationCellSize = 2;
    [Header("Feedback")]
    [Range(0, 1)] public float soundVolume = .35f;
    [Min(.1f)] public float messageSeconds = 3;
    private void OnValidate()
    {
        closingHour = Mathf.Max(openingHour + 1, closingHour);
        secondsPerGameMinute = Mathf.Max(.1f, secondsPerGameMinute);
        junctionsPerSide = Mathf.Clamp(junctionsPerSide | 1, 3, 5);
    }
}
