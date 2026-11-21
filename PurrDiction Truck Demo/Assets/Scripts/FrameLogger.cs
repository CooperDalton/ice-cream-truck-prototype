using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Text;
using UnityEngine;

// One JSON line per frame with everything this machine draws, for Loop/analyze.py.
[DefaultExecutionOrder(1000)]
public class FrameLogger : MonoBehaviour
{
    [SerializeField] Camera captureCamera;

    StreamWriter writer;
    readonly StringBuilder line = new StringBuilder(4096);
    readonly List<string> events = new List<string>();
    readonly Dictionary<string, float> underruns = new Dictionary<string, float>();
    string captureDir;
    float nextCapture;
    RenderTexture captureTarget;
    Texture2D captureTexture;
    int captureIndex;

    public void Open(string path)
    {
        writer = new StreamWriter(path, false, Encoding.UTF8, 1 << 16);
        captureDir = GameManager.Arg("-capture", "");
        if (captureDir != "")
        {
            Directory.CreateDirectory(captureDir);
            captureTarget = new RenderTexture(640, 360, 24);
            captureTexture = new Texture2D(640, 360, TextureFormat.RGB24, false);
        }
    }

    public void Close()
    {
        if (writer != null)
        {
            writer.Flush();
            writer.Close();
            writer = null;
        }
    }

    void OnApplicationQuit()
    {
        Close();
    }

    public static string F(float v)
    {
        return v.ToString("0.####", CultureInfo.InvariantCulture);
    }

    public static string D(double v)
    {
        return v.ToString("0.#####", CultureInfo.InvariantCulture);
    }

    public static string V(Vector3 v)
    {
        return "[" + F(v.x) + "," + F(v.y) + "," + F(v.z) + "]";
    }

    public void Event(string kind, string json)
    {
        if (writer == null)
        {
            return;
        }
        events.Add("{\"k\":\"" + kind + "\",\"d\":" + json + "}");
    }

    public void Underrun(string what, float t)
    {
        underruns.TryGetValue(what, out float worst);
        underruns[what] = Mathf.Max(worst, t);
    }

    public void RagOwnerFrame(int npc, int epoch, RagFrame frame)
    {
        Event("rag_frame", "{\"npc\":" + npc + ",\"epoch\":" + epoch + ",\"t\":" + D(frame.time) + ",\"pelvis\":" + V(frame.pos[0]) + ",\"head\":" + V(frame.pos[2]) + "}");
    }

    void LateUpdate()
    {
        if (writer == null)
        {
            return;
        }
        GameManager gm = GameManager.Instance;
        line.Clear();
        line.Append("{\"f\":").Append(Time.frameCount);
        line.Append(",\"t\":").Append(D(gm.Now));
        line.Append(",\"w\":").Append(D(System.DateTime.UtcNow.Subtract(new System.DateTime(2026, 1, 1)).TotalSeconds));
        line.Append(",\"dt\":").Append(F(Time.deltaTime));
        line.Append(",\"ready\":").Append(gm.ClockReady && gm.Truck.Ready && gm.LocalAvatar != null ? 1 : 0);
        if (gm.Network.isServer || gm.Network.isClient)
        {
            line.Append(",\"R\":").Append(D(gm.RenderTime));
            line.Append(",\"L\":").Append(D(gm.LatestServerTime));
            line.Append(",\"rtt\":").Append(F((float)gm.Network.tickModule.rtt));
            line.Append(",\"D\":").Append(F((float)gm.InterpDelay));
        }
        Truck truck = gm.Truck;
        if (truck.Ready)
        {
            line.Append(",\"tr\":[").Append(F(truck.DisplayPosition.x)).Append(',').Append(F(truck.DisplayPosition.z)).Append(',')
                .Append(F(truck.DisplayYaw)).Append(',').Append((int)truck.Mode).Append(',').Append(truck.DisplayCrashing ? 1 : 0).Append(',')
                .Append(F(truck.DisplayVelocity.magnitude)).Append(',').Append(F(truck.DisplaySteer)).Append(']');
            if (gm.IsServer)
            {
                TruckState s = truck.ServerState;
                line.Append(",\"ts\":[").Append(F(s.pos.x)).Append(',').Append(F(s.pos.y)).Append(',').Append(F(s.yaw)).Append(',')
                    .Append(F(s.speed)).Append(']');
            }
            line.Append(",\"inp\":[").Append(gm.Input.steer).Append(',').Append(gm.Input.throttle).Append(']');
        }
        line.Append(",\"pl\":[");
        bool first = true;
        foreach (PlayerAvatar a in gm.Avatars.Values)
        {
            if (!first)
            {
                line.Append(',');
            }
            first = false;
            line.Append('[').Append(a.OwnerId.id.value).Append(',').Append(a.isOwner ? 1 : 0).Append(',').Append((int)a.DisplayedMode).Append(',')
                .Append(F(a.DisplayWorld.x)).Append(',').Append(F(a.DisplayWorld.y)).Append(',').Append(F(a.DisplayWorld.z)).Append(',')
                .Append(F(a.DisplayLocal.x)).Append(',').Append(F(a.DisplayLocal.y)).Append(',').Append(F(a.DisplayLocal.z)).Append(',')
                .Append(F(a.DisplayYawWorld)).Append(',').Append(a.MovingInput ? 1 : 0).Append(']');
        }
        line.Append("],\"np\":[");
        first = true;
        foreach (Npc n in gm.Npcs.All)
        {
            if (!first)
            {
                line.Append(',');
            }
            first = false;
            Vector3 p = n.Pelvis;
            line.Append('[').Append(n.Index).Append(',').Append((int)n.Showing).Append(',').Append(F(n.DisplayRoot.x)).Append(',').Append(F(n.DisplayRoot.z)).Append(',')
                .Append(F(p.x)).Append(',').Append(F(p.y)).Append(',').Append(F(p.z)).Append(',').Append(D(n.DisplaySourceTime)).Append(',').Append(n.Epoch).Append(']');
        }
        line.Append(']');
        if (underruns.Count > 0)
        {
            line.Append(",\"under\":{");
            first = true;
            foreach (var kv in underruns)
            {
                if (!first)
                {
                    line.Append(',');
                }
                first = false;
                line.Append('"').Append(kv.Key).Append("\":").Append(F(kv.Value));
            }
            line.Append('}');
            underruns.Clear();
        }
        if (events.Count > 0)
        {
            line.Append(",\"ev\":[").Append(string.Join(",", events)).Append(']');
            events.Clear();
        }
        line.Append('}');
        writer.WriteLine(line.ToString());

        if (captureDir != "" && Time.time >= nextCapture && gm.LocalAvatar != null)
        {
            nextCapture = Time.time + 0.1f;
            Capture();
        }
    }

    void Capture()
    {
        captureCamera.targetTexture = captureTarget;
        captureCamera.Render();
        captureCamera.targetTexture = null;
        RenderTexture.active = captureTarget;
        captureTexture.ReadPixels(new Rect(0, 0, 640, 360), 0, 0);
        RenderTexture.active = null;
        File.WriteAllBytes(Path.Combine(captureDir, captureIndex.ToString("00000") + ".jpg"), captureTexture.EncodeToJPG(80));
        captureIndex++;
    }
}
