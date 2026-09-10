using UnityEngine;
using UnityEngine.AI;

public class TycoonTownWalker : MonoBehaviour
{
    public TycoonGameManager game;
    public NavMeshAgent agent;
    public Transform body;
    public Vector3[] stops;
    public int next;
    private Vector3 rest;
    private System.Collections.IEnumerator Start()
    {
        rest=body.localPosition;
        yield return null;
        while(game.loadingCampaign)yield return null;
        agent.enabled=true;agent.SetDestination(stops[next]);
    }
    private void Update()
    {
        if(!agent.enabled)return;
        agent.isStopped=game.Paused;
        if(game.Paused)return;
        body.localPosition=rest+Vector3.up*Mathf.Sin(Time.time*4+next)*.035f;
        if(!agent.pathPending&&agent.remainingDistance<.3f)
        {
            next=(next+1)%stops.Length;agent.SetDestination(stops[next]);
        }
    }
}
