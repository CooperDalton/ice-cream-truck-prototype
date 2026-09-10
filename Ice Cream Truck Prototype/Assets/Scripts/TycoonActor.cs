using UnityEngine;
using UnityEngine.AI;

public class TycoonActor : MonoBehaviour
{
    public NavMeshAgent agent;
    public Transform body, leftHand, rightHand, grip;
    public TycoonGameManager game;
    public bool worker;
    public int site;
    public TycoonOrder order;
    public bool leaving;
    public bool ReadyToOrder => Vector3.Distance(transform.position, game.sites[site].queuePoint.position) < 3.5f;
    private Vector3 leftRest, rightRest, bodyRest;
    private GameObject heldVisual;
    private string heldState;
    private void Awake()
    {
        leftRest = leftHand.localPosition; rightRest = rightHand.localPosition; bodyRest = body.localPosition;
    }
    private void Update()
    {
        if (game == null || game.Paused) return;
        body.localPosition = bodyRest + Vector3.up * Mathf.Sin(Time.time * 4) * .012f;
        if (worker) return;
        if (leaving)
        {
            if (!agent.pathPending && agent.remainingDistance < .6f) { game.actors.Remove(this); Destroy(gameObject); }
            return;
        }
        int index = game.sites[site].queue.IndexOf(this);
        if (index < 0) return;
        agent.SetDestination(game.sites[site].queuePoint.position + game.sites[site].queuePoint.forward * index * .8f);
        if(!agent.pathPending&&agent.remainingDistance<.2f){var facing=game.sites[site].origin.position-transform.position;facing.y=0;transform.rotation=Quaternion.Slerp(transform.rotation,Quaternion.LookRotation(facing),Time.deltaTime*6);}
        if (order.owner == "" && ReadyToOrder) order.patience -= Time.deltaTime;
        if (order.patience <= 0) { game.sites[site].lostSales++; Leave(); }
    }
    public void Leave()
    {
        game.sites[site].queue.Remove(this); leaving = true;
        agent.SetDestination(game.spawnPoints[(order.id + 3) % game.spawnPoints.Length].position);
    }
    public bool Walk(Vector3 point)
    {
        if (Vector3.Distance(agent.destination, point) > .1f) agent.SetDestination(point);
        var offset = transform.position - point; offset.y = 0;
        return !agent.pathPending && agent.pathStatus == NavMeshPathStatus.PathComplete && agent.remainingDistance < .18f && offset.magnitude < .35f;
    }
    public void Hold(TycoonItem item)
    {
        string state = item == null ? "" : JsonUtility.ToJson(item);
        if (state == heldState) return;
        heldState = state;
        if (heldVisual != null) Destroy(heldVisual);
        if (item != null) heldVisual = game.catalog.Display(item, grip);
    }
    public void Reach(Vector3 target, float cycle, bool scoop)
    {
        var facing = target - transform.position; facing.y = 0;
        transform.rotation = Quaternion.Slerp(transform.rotation, Quaternion.LookRotation(facing), .25f);
        rightHand.position = Vector3.Lerp(rightHand.position, target + Vector3.up * Mathf.Sin(cycle * Mathf.PI * 2) * (scoop ? .10f : .025f), .3f);
        leftHand.localPosition = Vector3.Lerp(leftHand.localPosition, leftRest, .2f);
    }
    public void RestHands()
    {
        rightHand.localPosition = Vector3.Lerp(rightHand.localPosition, rightRest, .2f);
        leftHand.localPosition = Vector3.Lerp(leftHand.localPosition, leftRest, .2f);
    }
}
