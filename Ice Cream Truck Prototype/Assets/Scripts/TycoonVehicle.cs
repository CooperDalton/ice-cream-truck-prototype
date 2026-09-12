using UnityEngine;

public class TycoonVehicle : MonoBehaviour
{
    public TycoonGameManager game;
    public TycoonPart interaction;
    public Transform seat, exit, kitchenEntry;
    public Transform[] wheels;
    public GameObject smallCargoModel, largeCargoModel;
    public TycoonInventory cargo = new TycoonInventory(4);
    public bool truck, operatingToday, routeComplete;
    public int routeStop, travelStage;
    public int[] demand = { 7, 7 };
    public float speed;
    private bool transportingDriver;
    public bool AtStop => truck && Vector3.Distance(transform.position, game.truckStops[routeStop].position) < 2.5f && Mathf.Abs(speed) < .1f;
    private void Start()
    {
        interaction.storage = cargo;
    }
    public void BeginDay()
    {
        operatingToday = false; routeComplete = false; demand = new[] { 7, 7 }; routeStop = 0; travelStage = 0;
    }
    public void Enter()
    {
        if (truck && (!game.sites[2].owned || game.workers.Exists(w => w.driver && w.onDuty))) { game.notice = "The truck is unavailable while its driver is on duty."; return; }
        if (truck && game.sites[2].queue.Count > 0) { game.notice = "Finish the waiting orders before moving the truck."; return; }
        game.player.CancelGesture();
        game.player.vehicle = this; game.player.controller.enabled = false;
        game.player.transform.SetParent(seat, false); game.player.transform.localPosition = Vector3.zero; game.player.transform.localRotation = Quaternion.identity;
        if (truck) game.sites[2].open = false;
        game.notice = "WASD to drive / E to get out";
    }
    public void Exit()
    {
        game.player.transform.SetParent(null, true); game.player.Teleport(exit.position);
        game.player.vehicle = null; speed = 0;
        if (!truck) return;
        for (int i = 0; i < game.truckStops.Length; i++) if (Vector3.Distance(transform.position, game.truckStops[i].position) < 2.5f) routeStop = i;
        game.navigation.BuildNavMesh();
        game.sites[2].open = AtStop && operatingToday && game.phase == TycoonGameManager.Phase.Trading;
        game.notice = AtStop ? "Selling stop reached. Enter the rear kitchen to prepare orders." : "Park in the center of a marked selling stop to trade.";
    }
    public void Drive(Vector2 input, float dt)
    {
        speed = Mathf.MoveTowards(speed, input.y * (truck ? 12 : 8), dt * 7);
        transform.Rotate(0, input.x * speed * dt * 7, 0);
        Vector3 delta = (truck ? transform.right : transform.forward) * speed * dt;
        bool blocked = false;
        foreach (var hit in Physics.SphereCastAll(transform.position + Vector3.up * (truck ? 1.8f : .65f), truck ? 1.3f : .3f, delta.normalized, delta.magnitude + (truck ? 3 : .3f), ~0, QueryTriggerInteraction.Ignore))
            if (!hit.collider.transform.IsChildOf(transform) && hit.collider.gameObject != game.player.gameObject) blocked = true;
        if (blocked) speed = 0; else transform.position += delta;
        RollWheels(dt);
    }
    private void RollWheels(float dt)
    {
        foreach (var wheel in wheels) wheel.Rotate(truck ? Vector3.forward : Vector3.right, speed * dt * 160, Space.Self);
    }
    public bool DriveRoute(TycoonWorker worker)
    {
        if (!operatingToday || routeComplete) { game.sites[2].open = false; worker.status = "Truck route closed for today"; return true; }
        if (AtStop && !transportingDriver)
        {
            game.sites[2].open = true;
            if (demand[routeStop] > 0 || game.sites[2].queue.Count > 0 || worker.ticketId >= 0) return false;
            if (routeStop == 1) { routeComplete = true; game.sites[2].open = false; worker.status = "Both selling stops complete"; return true; }
            routeStop = 1; travelStage = 0;
        }
        game.sites[2].open = false;
        if (!transportingDriver)
        {
            worker.actor.agent.enabled = false; worker.transform.SetParent(seat, false); worker.transform.localPosition = Vector3.zero; worker.transform.localRotation = Quaternion.identity;
            worker.actor.Hold(null); transportingDriver = true;
        }
        worker.status = "Driving to " + game.truckStops[routeStop].name;
        var destination = game.truckStops[routeStop].position;
        float cornerX = routeStop == 0 ? 5 : 64;
        var next = travelStage == 0 ? new Vector3(cornerX, 0, transform.position.z) : travelStage == 1 ? new Vector3(cornerX, 0, destination.z) : destination;
        if (Mathf.Abs(transform.position.z - destination.z) < .1f) { travelStage = 2; next = destination; }
        Vector3 direction = next - transform.position;
        if (direction.sqrMagnitude > .01f) transform.rotation = Quaternion.LookRotation(direction) * Quaternion.Euler(0, -90, 0);
        speed = 8; transform.position = Vector3.MoveTowards(transform.position, next, Time.deltaTime * speed); RollWheels(Time.deltaTime);
        if (Vector3.Distance(transform.position, next) < .05f) travelStage++;
        if (travelStage <= 2) return true;
        speed = 0; transportingDriver = false;
        worker.transform.SetParent(null, true); worker.transform.position = kitchenEntry.position;
        game.navigation.BuildNavMesh(); worker.actor.agent.enabled = true; worker.actor.agent.Warp(kitchenEntry.position);
        game.sites[2].open = true; game.sites[2].spawnTimer = 1;
        return false;
    }
    public void ReleaseDriver(TycoonWorker worker)
    {
        if (!transportingDriver) return;
        speed = 0; transportingDriver = false; worker.transform.SetParent(null, true); worker.transform.position = kitchenEntry.position;
        game.navigation.BuildNavMesh(); worker.actor.agent.enabled = true; worker.actor.agent.Warp(kitchenEntry.position);
    }
}
