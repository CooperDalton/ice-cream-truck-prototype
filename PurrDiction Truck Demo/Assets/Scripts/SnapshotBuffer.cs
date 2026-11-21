using System.Collections.Generic;

// Time-stamped samples on the shared server timeline. Every remote thing a client shows is
// sampled from one of these at NetClock.RenderTime, so all of it stays coherent.
public class SnapshotBuffer<T>
{
    readonly List<double> times = new List<double>();
    readonly List<T> values = new List<T>();
    readonly int capacity;

    public SnapshotBuffer(int capacity = 64)
    {
        this.capacity = capacity;
    }

    public int Count => times.Count;
    public double NewestTime => times[times.Count - 1];
    public T Newest => values[values.Count - 1];
    public double OldestTime => times[0];
    public T Oldest => values[0];

    public void Clear()
    {
        times.Clear();
        values.Clear();
    }

    // Samples may arrive out of order (redundant copies, jitter): insert in time order, drop
    // duplicates and anything older than the history kept.
    public void Add(double time, T value)
    {
        int i = times.Count;
        while (i > 0 && times[i - 1] > time)
        {
            i--;
        }
        if (i > 0 && times[i - 1] == time || i == 0 && times.Count >= capacity)
        {
            return;
        }
        times.Insert(i, time);
        values.Insert(i, value);
        if (times.Count > capacity)
        {
            times.RemoveAt(0);
            values.RemoveAt(0);
        }
    }

    // Like Add, but a sample at an existing time replaces it (a replayed prediction for a tick).
    public void Put(double time, T value)
    {
        int i = times.Count;
        while (i > 0 && times[i - 1] > time)
        {
            i--;
        }
        if (i > 0 && times[i - 1] == time)
        {
            values[i - 1] = value;
            return;
        }
        Add(time, value);
    }

    // Returns the pair bracketing time and the blend factor. t > 1 means time is past the
    // newest sample (the caller decides whether to extrapolate or hold).
    public void Sample(double time, out T a, out T b, out float t)
    {
        int n = times.Count;
        if (time <= times[0] || n == 1)
        {
            a = values[0];
            b = values[0];
            t = 0f;
            return;
        }
        if (time >= times[n - 1])
        {
            a = values[n - 2];
            b = values[n - 1];
            t = (float)((time - times[n - 2]) / (times[n - 1] - times[n - 2]));
            return;
        }
        int i = n - 1;
        while (times[i - 1] > time)
        {
            i--;
        }
        a = values[i - 1];
        b = values[i];
        t = (float)((time - times[i - 1]) / (times[i] - times[i - 1]));
    }

    public void RemoveBefore(double time)
    {
        while (times.Count > 0 && times[0] < time)
        {
            times.RemoveAt(0);
            values.RemoveAt(0);
        }
    }
}
