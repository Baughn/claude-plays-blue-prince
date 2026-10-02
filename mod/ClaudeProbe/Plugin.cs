// Minimal navigation probe for Blue Prince. Uses only generic Unity APIs (camera, physics raycasts).
// Deliberately reports no object names, tags or game-specific data: geometry only, to avoid spoilers.
//
// Line protocol on 127.0.0.1:7777, one request per connection:
//   pose            -> "x y z yaw pitch"            (camera world position; yaw 0 = +Z, 90 = +X)
//   ray             -> "dist px py pz nx ny nz"     (crosshair ray, triggers ignored; "none" if no hit within 100m)
//   scan N [pitch]  -> N distances, evenly spaced over 360° of yaw starting at the current yaw,
//                      at the given pitch (default 0 = horizontal), from the camera position.
using System;
using System.Collections.Concurrent;
using System.Globalization;
using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Threading;
using BepInEx;
using BepInEx.Unity.IL2CPP;
using UnityEngine;

namespace ClaudeProbe;

[BepInPlugin("claude.probe", "ClaudeProbe", "0.1.0")]
public class Plugin : BasePlugin
{
    public override void Load()
    {
        AddComponent<Probe>();
        Log.LogInfo("ClaudeProbe loaded");
    }
}

public class Probe : MonoBehaviour
{
    public Probe(IntPtr ptr) : base(ptr) { }

    class Req { public string Cmd; public string Reply; public ManualResetEventSlim Done = new(false); }

    static readonly ConcurrentQueue<Req> Queue = new();
    static Thread _listener;
    static readonly CultureInfo Inv = CultureInfo.InvariantCulture;

    void Awake()
    {
        if (_listener != null) return;
        _listener = new Thread(Listen) { IsBackground = true };
        _listener.Start();
    }

    static void Listen()
    {
        var srv = new TcpListener(IPAddress.Loopback, 7777);
        srv.Start();
        while (true)
        {
            try
            {
                using var client = srv.AcceptTcpClient();
                using var stream = client.GetStream();
                var buf = new byte[4096];
                int n = stream.Read(buf, 0, buf.Length);
                var req = new Req { Cmd = Encoding.UTF8.GetString(buf, 0, n).Trim() };
                Queue.Enqueue(req);
                string reply = req.Done.Wait(5000) ? req.Reply : "timeout";
                var outb = Encoding.UTF8.GetBytes(reply + "\n");
                stream.Write(outb, 0, outb.Length);
            }
            catch (Exception) { /* keep serving */ }
        }
    }

    void Update()
    {
        while (Queue.TryDequeue(out var req))
        {
            try { req.Reply = Handle(req.Cmd); }
            catch (Exception e) { req.Reply = "error " + e.Message; }
            req.Done.Set();
        }
    }

    static string F(float v) => v.ToString("0.###", Inv);

    static string Handle(string cmd)
    {
        var p = cmd.Split(' ', StringSplitOptions.RemoveEmptyEntries);
        var cam = Camera.main;
        if (cam == null) return "nocam";
        var t = cam.transform;
        var e = t.eulerAngles;
        float pitch = e.x > 180 ? e.x - 360 : e.x;
        switch (p.Length > 0 ? p[0] : "")
        {
            case "pose":
                return $"{F(t.position.x)} {F(t.position.y)} {F(t.position.z)} {F(e.y)} {F(pitch)}";
            case "ray":
            {
                if (!Physics.Raycast(t.position, t.forward, out var hit, 100f, ~0, QueryTriggerInteraction.Ignore))
                    return "none";
                return $"{F(hit.distance)} {F(hit.point.x)} {F(hit.point.y)} {F(hit.point.z)} {F(hit.normal.x)} {F(hit.normal.y)} {F(hit.normal.z)}";
            }
            case "scan":
            {
                int n = p.Length > 1 ? int.Parse(p[1], Inv) : 36;
                float sp = p.Length > 2 ? float.Parse(p[2], Inv) : 0f;
                var sb = new StringBuilder();
                for (int i = 0; i < n; i++)
                {
                    var dir = Quaternion.Euler(sp, e.y + 360f * i / n, 0) * Vector3.forward;
                    float d = Physics.Raycast(t.position, dir, out var hit, 100f, ~0, QueryTriggerInteraction.Ignore) ? hit.distance : 100f;
                    sb.Append(F(d)).Append(' ');
                }
                return sb.ToString().TrimEnd();
            }
            default:
                return "unknown";
        }
    }
}
