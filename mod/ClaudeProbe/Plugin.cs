// Thin geometry proxy for Blue Prince. Generic Unity APIs only (camera pose, physics raycasts).
// Deliberately reports no object names, tags or game-specific data, to avoid spoilers.
// All logic (scans, navigation, obstacle avoidance) lives in tools/nav.py so it can change mid-day.
//
// Protocol on 127.0.0.1:7777, one connection per request, newline-separated commands,
// one reply line per command:
//   pose                          -> "x y z yaw pitch"       (camera; yaw 0 = +Z, 90 = +X; pitch + = down)
//   cast ox oy oz dx dy dz [max]  -> "dist px py pz nx ny nz" or "none"   (triggers ignored, max default 100)
//   ray                           -> cast from the camera along its forward vector
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

[BepInPlugin("claude.probe", "ClaudeProbe", "0.2.0")]
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
                var ms = new System.IO.MemoryStream();
                var buf = new byte[65536];
                int n;
                while ((n = stream.Read(buf, 0, buf.Length)) > 0) ms.Write(buf, 0, n);
                var req = new Req { Cmd = Encoding.UTF8.GetString(ms.ToArray()) };
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
            var sb = new StringBuilder();
            foreach (var line in req.Cmd.Split('\n', StringSplitOptions.RemoveEmptyEntries))
            {
                string r;
                try { r = Handle(line.Trim()); }
                catch (Exception e) { r = "error " + e.Message; }
                if (sb.Length > 0) sb.Append('\n');
                sb.Append(r);
            }
            req.Reply = sb.ToString();
            req.Done.Set();
        }
    }

    static string F(float v) => v.ToString("0.###", Inv);
    static float P(string s) => float.Parse(s, Inv);

    static string Cast(Vector3 o, Vector3 d, float max)
    {
        if (!Physics.Raycast(o, d.normalized, out var hit, max, ~0, QueryTriggerInteraction.Ignore)) return "none";
        return $"{F(hit.distance)} {F(hit.point.x)} {F(hit.point.y)} {F(hit.point.z)} {F(hit.normal.x)} {F(hit.normal.y)} {F(hit.normal.z)}";
    }

    static string Handle(string cmd)
    {
        var p = cmd.Split(' ', StringSplitOptions.RemoveEmptyEntries);
        if (p.Length == 0) return "";
        var cam = Camera.main;
        switch (p[0])
        {
            case "pose":
            {
                if (cam == null) return "nocam";
                var t = cam.transform; var e = t.eulerAngles;
                float pitch = e.x > 180 ? e.x - 360 : e.x;
                return $"{F(t.position.x)} {F(t.position.y)} {F(t.position.z)} {F(e.y)} {F(pitch)}";
            }
            case "ray":
                if (cam == null) return "nocam";
                return Cast(cam.transform.position, cam.transform.forward, 100f);
            case "cast":
                return Cast(new Vector3(P(p[1]), P(p[2]), P(p[3])), new Vector3(P(p[4]), P(p[5]), P(p[6])),
                            p.Length > 7 ? P(p[7]) : 100f);
            default:
                return "unknown";
        }
    }
}
