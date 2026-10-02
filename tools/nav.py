#!/usr/bin/env python3
"""Closed-loop navigation using the ClaudeProbe plugin (pose/raycast) + inputd (virtual mouse/pad).

  tools/nav pose                      print x y z yaw pitch
  tools/nav face YAW [PITCH]          turn to absolute yaw (deg, 0=+Z, 90=+X) and optional pitch (+ = down)
  tools/nav turn DEG                  turn relative (+ = right)
  tools/nav lookat X Y Z              aim the crosshair at a world point
  tools/nav goto X Z [TOL]            walk to a point on the floor (stops within TOL m, default 0.5)
  tools/nav fwd METERS                walk forward a distance along current heading
  tools/nav ray                       distance/point under crosshair
  tools/nav scan [N]                  horizontal distance ring (N rays, default 72), printed as compass + polar sketch
  tools/nav aim YAW PITCH PX PY       aim at pixel (PX,PY) of a 1280x720 shot taken while facing YAW/PITCH
  tools/nav approach YAW PITCH PX PY [STANDOFF]  aim at pixel, raycast, walk to STANDOFF m (default 1.2) from it, look at it
  tools/nav near PX PY [STANDOFF]     approach a pixel of a shot taken from the current pose
  tools/nav here PX PY                aim at a pixel of a shot taken from the current pose
  tools/nav calib                     measure mouse units/degree and save to tools/nav_calib.json
"""
import json, math, os, socket, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
CALIB = os.path.join(HERE, "nav_calib.json")
SOCK = os.path.join(HERE, ".inputd.sock")


def probe(cmd):
    s = socket.create_connection(("127.0.0.1", 7777), timeout=6)
    s.sendall(cmd.encode()); s.shutdown(socket.SHUT_WR)
    out = b""
    while True:
        c = s.recv(65536)
        if not c: break
        out += c
    return out.decode().strip()


def focused():
    r = subprocess.run([os.path.join(HERE, "focus")], capture_output=True, text=True)
    return r.stdout.strip() == "BLUE PRINCE"


def inp(cmds):
    if not focused():
        sys.exit("REFUSED: game window not focused (run tools/activate)")
    s = socket.socket(socket.AF_UNIX); s.connect(SOCK)
    s.sendall((cmds + "\n\n").encode())
    s.settimeout(120)
    out = s.recv(4096).decode()
    s.close()
    if out != "ok": raise RuntimeError(out)


def pose():
    r = probe("pose")
    if r in ("nocam", "timeout") or r.startswith("error"):
        raise RuntimeError("probe: " + r)
    x, y, z, yaw, pitch = map(float, r.split())
    return x, y, z, yaw, pitch


def wrap(a):
    return (a + 180) % 360 - 180


def calib():
    try: return json.load(open(CALIB))
    except Exception: return {"units_per_deg": 15.2, "pitch_units_per_deg": 15.2, "speed": 3.0}


def do_calib():
    c = calib()
    _, _, _, y0, p0 = pose()
    inp("move 1500 0 50"); time.sleep(0.3)
    _, _, _, y1, _ = pose()
    inp("move -1500 0 50"); time.sleep(0.3)
    c["units_per_deg"] = 1500 / wrap(y1 - y0)
    inp("move 0 300 20"); time.sleep(0.3)
    _, _, _, _, p1 = pose()
    inp("move 0 -300 20"); time.sleep(0.3)
    c["pitch_units_per_deg"] = 300 / (p1 - p0) if abs(p1 - p0) > 0.1 else c["pitch_units_per_deg"]
    x0, _, z0, _, _ = pose()
    inp("stick L 0 -1 1000"); time.sleep(0.3)
    x1, _, z1, _, _ = pose()
    inp("stick L 0 1 1000"); time.sleep(0.3)
    c["speed"] = max(0.3, math.hypot(x1 - x0, z1 - z0))
    json.dump(c, open(CALIB, "w"), indent=1)
    print(c)


def face_stick(yaw, pitch=None, tol=0.8):
    """Turn with the right stick (safe when the game has released the mouse pointer)."""
    for _ in range(14):
        _, _, _, y, p = pose()
        dy = wrap(yaw - y)
        dp = 0 if pitch is None else pitch - p
        if abs(dy) < tol and abs(dp) < tol: return
        # ~70 deg/s at 0.5 deflection; use gentler deflection for small corrections
        def cmd(d):
            if abs(d) < tol: return 0.0, 0
            mag = 0.5 if abs(d) > 15 else 0.3
            rate = 70.0 if mag == 0.5 else 35.0
            return (mag if d > 0 else -mag), int(min(2500, max(40, abs(d) / rate * 1000 * 0.85)))
        sx, tx = cmd(dy); sy, ty = cmd(dp)
        if tx: inp(f"stick R {sx} 0 {tx}")
        if ty: inp(f"stick R 0 {sy} {ty}")
        time.sleep(0.12)


def face(yaw, pitch=None, tol=0.7):
    c = calib()
    if os.environ.get("NAV_TURN") != "stick":
        _, _, _, y0, p0 = pose()
        dy = wrap(yaw - y0)
        dp = 0 if pitch is None else pitch - p0
        if abs(dy) < tol and abs(dp) < tol: return
        ux, uy = int(round(dy * c["units_per_deg"])), int(round(dp * c["pitch_units_per_deg"]))
        inp(f"move {ux} {uy} {max(4, int(max(abs(ux), abs(uy)) / 25))}")
        time.sleep(0.15)
        _, _, _, y1, p1 = pose()
        if abs(wrap(y1 - y0)) + abs(p1 - p0) < 0.2 * (abs(dy) + abs(dp)):
            print("mouse not captured; using right stick", file=sys.stderr)
            return face_stick(yaw, pitch, max(tol, 0.8))
        for _ in range(5):
            _, _, _, y, p = pose()
            dy = wrap(yaw - y)
            dp = 0 if pitch is None else pitch - p
            if abs(dy) < tol and abs(dp) < tol: return
            ux, uy = int(round(dy * c["units_per_deg"])), int(round(dp * c["pitch_units_per_deg"]))
            inp(f"move {ux} {uy} {max(4, int(max(abs(ux), abs(uy)) / 25))}")
            time.sleep(0.15)
    else:
        face_stick(yaw, pitch, max(tol, 0.8))


def goto(tx, tz, tol=0.5, max_iter=40):
    c = calib()
    stuck = 0
    for _ in range(max_iter):
        x, _, z, y, _ = pose()
        dx, dz = tx - x, tz - z
        d = math.hypot(dx, dz)
        if d < tol:
            print(f"arrived {x:.2f} {z:.2f} (d={d:.2f})"); return True
        face(math.degrees(math.atan2(dx, dz)))
        ms = int(min(1500, max(120, d / c["speed"] * 1000 * 0.8)))
        inp(f"stick L 0 -1 {ms}"); time.sleep(0.15)
        x2, _, z2, _, _ = pose()
        if math.hypot(x2 - x, z2 - z) < 0.05:
            stuck += 1
            side = 1 if stuck % 2 else -1
            inp(f"stick L {side} 0 400"); time.sleep(0.1)
            if stuck > 4:
                print(f"stuck at {x2:.2f} {z2:.2f}, {d:.2f} m from target"); return False
    print("gave up"); return False


F_PX = 586.0  # focal length in 1280-wide pixels (hFOV ~95 deg); refine via calib_fov


def pixel_dir(yaw, pitch, px, py):
    """World yaw/pitch of the ray through pixel (px,py) of a 1280x720 frame taken at yaw/pitch (pitch + = down)."""
    cx, cy, cz = (px - 640) / F_PX, -(py - 360) / F_PX, 1.0
    p = math.radians(pitch)  # rotate about X (camera pitch down)
    cy, cz = cy * math.cos(p) - cz * math.sin(p), cy * math.sin(p) + cz * math.cos(p)
    y = math.radians(yaw)
    wx, wz = cx * math.cos(y) + cz * math.sin(y), -cx * math.sin(y) + cz * math.cos(y)
    return (math.degrees(math.atan2(wx, wz)) % 360, -math.degrees(math.atan2(cy, math.hypot(wx, wz))))


def approach(yaw, pitch, px, py, standoff=1.2):
    ty, tp = pixel_dir(yaw, pitch, px, py)
    face(ty, tp)
    r = probe("ray").split()
    if r[0] == "none": print("no hit"); return
    hx, hy, hz = map(float, r[1:4])
    x, _, z, _, _ = pose()
    d = math.hypot(hx - x, hz - z)
    if d > standoff:
        k = (d - standoff) / d
        goto(x + (hx - x) * k, z + (hz - z) * k, 0.3)
    x, y, z, _, _ = pose()
    face(math.degrees(math.atan2(hx - x, hz - z)) % 360, -math.degrees(math.atan2(hy - y, math.hypot(hx - x, hz - z))))
    print(f"target {hx:.2f} {hy:.2f} {hz:.2f}; now at", " ".join(f"{v:.2f}" for v in pose()))


def scan(n=72):
    r = probe(f"scan {n} 0")
    ds = [float(v) for v in r.split()]
    _, _, _, yaw, _ = pose()
    print(f"scan from yaw {yaw:.0f} (relative angle: distance m)")
    rows = []
    for i, d in enumerate(ds):
        a = 360 * i / n
        rows.append(f"{a:5.0f}°→{(yaw + a) % 360:5.0f}: {d:5.2f} " + "#" * int(min(d, 30) * 2))
    print("\n".join(rows))


def main():
    a = sys.argv[1:]
    if not a: print(__doc__); return
    cmd = a[0]
    if cmd == "pose": print(" ".join(f"{v:.2f}" for v in pose()))
    elif cmd == "face": face(float(a[1]), float(a[2]) if len(a) > 2 else None); print(" ".join(f"{v:.2f}" for v in pose()))
    elif cmd == "turn":
        _, _, _, y, _ = pose(); face((y + float(a[1])) % 360); print(" ".join(f"{v:.2f}" for v in pose()))
    elif cmd == "lookat":
        x, y, z, _, _ = pose(); tx, ty, tz = map(float, a[1:4])
        h = math.hypot(tx - x, tz - z)
        face(math.degrees(math.atan2(tx - x, tz - z)), -math.degrees(math.atan2(ty - y, h)))
    elif cmd == "goto": goto(float(a[1]), float(a[2]), float(a[3]) if len(a) > 3 else 0.5)
    elif cmd == "fwd":
        x, _, z, y, _ = pose(); m = float(a[1])
        goto(x + m * math.sin(math.radians(y)), z + m * math.cos(math.radians(y)), 0.3)
    elif cmd == "ray": print(probe("ray"))
    elif cmd == "scan": scan(int(a[1]) if len(a) > 1 else 72)
    elif cmd == "aim": face(*pixel_dir(*map(float, a[1:5])))
    elif cmd == "here":
        _, _, _, y, p = pose(); face(*pixel_dir(y, p, float(a[1]), float(a[2])))
    elif cmd == "near":
        _, _, _, y, p = pose(); approach(y, p, float(a[1]), float(a[2]), float(a[3]) if len(a) > 3 else 1.0)
    elif cmd == "approach": approach(*map(float, a[1:6]))
    elif cmd == "calib": do_calib()
    else: print(__doc__)


if __name__ == "__main__":
    main()
