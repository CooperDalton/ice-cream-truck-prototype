using System.Collections.Generic;

// Maps a remote machine's clock onto the local clock using the fastest packet seen in a
// sliding window, so stamps keep the sender's even spacing (no jitter) and only shift
// slowly. Used by clients to estimate server time, and by the server to stamp owner-sent
// player states, shots and ragdoll frames onto the server timeline.
public class ClockMapper
{
    const double Window = 2.0;
    const double SlewPerSecond = 0.01; // timeline may warp by at most 1%

    readonly Queue<(double localTime, double offset)> samples = new Queue<(double, double)>();
    double offset;
    double lastUpdate;
    bool initialized;

    public bool Initialized => initialized;

    // offset = localReceive - remoteSend; the smallest one is the least-delayed packet.
    public void Observe(double remoteTime, double localReceive)
    {
        double sample = localReceive - remoteTime;
        samples.Enqueue((localReceive, sample));
        while (samples.Peek().localTime < localReceive - Window)
        {
            samples.Dequeue();
        }
        double min = double.MaxValue;
        foreach (var s in samples)
        {
            if (s.offset < min)
            {
                min = s.offset;
            }
        }
        if (!initialized)
        {
            offset = min;
            lastUpdate = localReceive;
            initialized = true;
            return;
        }
        double maxStep = (localReceive - lastUpdate) * SlewPerSecond;
        lastUpdate = localReceive;
        double delta = min - offset;
        if (delta > 0.25 || delta < -0.25)
        {
            offset = min;
        }
        else if (delta > maxStep)
        {
            offset += maxStep;
        }
        else if (delta < -maxStep)
        {
            offset -= maxStep;
        }
        else
        {
            offset = min;
        }
    }

    public double ToLocal(double remoteTime)
    {
        return remoteTime + offset;
    }

    public double ToRemote(double localTime)
    {
        return localTime - offset;
    }
}
