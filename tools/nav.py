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
    """Measure right-stick turn rates and walking speed. Run somewhere with room to walk forward ~3 m."""
    c = calib()
    rates = {}
    for mag in ("0.5", "0.3"):
        _, _, _, y0, p0 = pose()
        inp(f"stick R {mag} 0 1000"); time.sleep(0.25)
        _, _, _, y1, _ = pose()
        inp(f"stick R -{mag} 0 1000"); time.sleep(0.25)
        inp(f"stick R 0 {mag} 400"); time.sleep(0.25)
        _, _, _, _, p1 = pose()
        inp(f"stick R 0 -{mag} 400"); time.sleep(0.25)
        rates[mag] = [abs(wrap(y1 - y0)) / 1.0, max(5.0, abs(p1 - p0) / 0.4)]
    c["stick_rates"] = rates
    x0, _, z0, _, _ = pose()
    inp("stick L 0 -1 1000"); time.sleep(0.3)
    x1, _, z1, _, _ = pose()
    inp("stick L 0 1 1000"); time.sleep(0.3)
    c["speed"] = max(0.3, math.hypot(x1 - x0, z1 - z0))
    json.dump(c, open(CALIB, "w"), indent=1)
    print(c)


def face_stick(yaw, pitch=None, tol=0.8):
    """Turn with the right stick. Rates (deg/s at each deflection) come from nav_calib.json (tools/nav calib)."""
    c = calib()
    rates = c.get("stick_rates", {"0.5": [71.5, 48.0], "0.3": [14.5, 9.7]})
    for _ in range(10):
        _, _, _, y, p = pose()
        dy = wrap(yaw - y)
        dp = 0 if pitch is None else pitch - p
        if abs(dy) < tol and abs(dp) < tol: return
        def cmd(d, axis):
            if abs(d) < tol: return 0.0, 0
            mag = "0.5" if abs(d) > 4 else "0.3"
            rate = rates[mag][axis]
            return (float(mag) if d > 0 else -float(mag)), int(min(4000, max(30, abs(d) / rate * 1000)))
        sx, tx = cmd(dy, 0); sy, ty = cmd(dp, 1)
        if tx: inp(f"stick R {sx} 0 {tx}")
        if ty: inp(f"stick R 0 {sy} {ty}")
        time.sleep(0.1)


def face(yaw, pitch=None, tol=0.7):
    c = calib()
    if os.environ.get("NAV_TURN") == "mouse":
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


def clearance(x, y, z, heading, reach=6.0):
    """Free distance along heading for a body ~0.6 m wide, checked at knee and waist height."""
    h = math.radians(heading)
    fx, fz = math.sin(h), math.cos(h)
    rx, rz = fz, -fx
    rays = []
    for dy in (-1.3, -0.8):          # camera is ~1.68 above the floor
        for off in (-0.22, 0.0, 0.22):
            rays.append((x + rx * off, y + dy, z + rz * off, fx, 0, fz, reach))
    res = casts(rays)
    return min((r[0] if r else reach) for r in res)


def goto(tx, tz, tol=0.5, max_iter=60, timeout=40.0):
    """Walk to (tx, tz). Steers around obstacles using knee/waist raycasts; reports if it can't get there."""
    c = calib()
    stuck = 0
    t_end = time.time() + timeout
    for _ in range(max_iter):
        if time.time() > t_end:
            x, _, z, _, _ = pose()
            print(f"timeout at {x:.2f} {z:.2f}, {math.hypot(tx - x, tz - z):.2f} m from target"); return False
        x, y, z, yaw, _ = pose()
        dx, dz = tx - x, tz - z
        d = math.hypot(dx, dz)
        if d < tol:
            print(f"arrived {x:.2f} {z:.2f} (d={d:.2f})"); return True
        want = math.degrees(math.atan2(dx, dz)) % 360
        need = min(d, 2.0)
        heading, free = want, clearance(x, y, z, want)
        if free < need:
            # try deviations, nearest to the desired heading first
            best = None
            for dev in (20, -20, 40, -40, 60, -60, 90, -90, 120, -120):
                f = clearance(x, y, z, want + dev)
                if f >= min(need, 1.2):
                    best = (want + dev, f); break
            if best is None:
                print(f"blocked at {x:.2f} {z:.2f}, {d:.2f} m from target"); return False
            heading, free = best[0] % 360, best[1]
        face(heading)
        walk = min(need, free - 0.35) if heading != want else min(d, free - 0.35)
        walk = max(walk, 0.25)
        ms = int(min(1500, max(100, walk / c["speed"] * 1000)))
        inp(f"stick L 0 -1 {ms}"); time.sleep(0.1)
        x2, _, z2, _, _ = pose()
        if math.hypot(x2 - x, z2 - z) < 0.05:
            stuck += 1
            if stuck > 3:
                print(f"stuck at {x2:.2f} {z2:.2f}, {d:.2f} m from target"); return False
            inp(f"stick L {1 if stuck % 2 else -1} 0 350"); time.sleep(0.1)
        else:
            stuck = 0
    print("gave up"); return False


F_PX = 586.0  # focal length in 1280-wide pixels (hFOV ~95 deg)


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


def casts(rays):
    """Batch raycasts: rays = [(ox,oy,oz,dx,dy,dz,max), ...] -> list of (dist, (px,py,pz)) or None."""
    out = []
    lines = probe("\n".join("cast " + " ".join(f"{v:.4f}" for v in r) for r in rays)).split("\n")
    for ln in lines:
        v = ln.split()
        out.append(None if not v or v[0] in ("none", "error", "unknown") else (float(v[0]), tuple(map(float, v[1:4]))))
    return out


def scan(n=72, height=None):
    """Horizontal distance ring around the player (height = absolute y; default eye level)."""
    x, y, z, yaw, _ = pose()
    h = y if height is None else height
    rays = [(x, h, z, math.sin(math.radians(yaw + 360 * i / n)), 0, math.cos(math.radians(yaw + 360 * i / n)), 100)
            for i in range(n)]
    res = casts(rays)
    print(f"scan from yaw {yaw:.0f} at y={h:.2f} (relative angle: distance m)")
    for i, r in enumerate(res):
        d = r[0] if r else 100.0
        a = 360 * i / n
        print(f"{a:5.0f}°→{(yaw + a) % 360:5.0f}: {d:5.2f} " + "#" * int(min(d, 30) * 2))


def heightmap(cx, cz, half=6.0, step=0.2, top=2.3, out=None):
    """Top-down map: cast down from y=top over a grid. Writes a PNG (white=floor, darker=taller, red=no hit/solid)."""
    import struct, zlib
    n = int(2 * half / step) + 1
    pts = [(cx - half + i * step, cz + half - j * step) for j in range(n) for i in range(n)]
    hs = []
    for k in range(0, len(pts), 400):
        res = casts([(x, top, z, 0, -1, 0, top + 3) for x, z in pts[k:k + 400]])
        hs += [None if r is None else r[1][1] for r in res]
    fl = sorted(h for h in hs if h is not None)
    floor = fl[len(fl) // 10] if fl else 0.0
    x0, _, z0, yaw, _ = pose()
    scale = 8
    W = n * scale
    rows = []
    for j in range(n):
        row = bytearray()
        for i in range(n):
            h = hs[j * n + i]
            if h is None: c = (200, 40, 40)
            else:
                d = max(0.0, min(2.3, h - floor))
                g = int(255 - d / 2.3 * 220)
                c = (g, g, g) if d > 0.05 else (250, 250, 235)
            row += bytes(c) * scale
        for _ in range(scale): rows.append(bytearray(row))
    # lidar overlay: horizontal rays from the player at knee and chest height
    def put(wx, wz, col):
        ii, jj = int((wx - (cx - half)) / step * scale), int(((cz + half) - wz) / step * scale)
        for a in range(-1, 2):
            for b in range(-1, 2):
                if 0 <= jj + a < W and 0 <= ii + b < W: rows[jj + a][(ii + b) * 3:(ii + b) * 3 + 3] = bytes(col)
    xl, yl, zl, _, _ = pose()
    for hgt, col in ((0.5, (230, 120, 0)), (1.3, (150, 0, 150))):
        rays = [(xl, hgt, zl, math.sin(math.radians(k * 0.5)), 0, math.cos(math.radians(k * 0.5)), 2 * half) for k in range(720)]
        for k in range(0, 720, 360):
            for r in casts(rays[k:k + 360]):
                if r: put(r[1][0], r[1][2], col)
    # player marker + heading
    pi, pj = int((x0 - (cx - half)) / step), int(((cz + half) - z0) / step)
    for t in range(0, 12):
        qi = pi + int(round(math.sin(math.radians(yaw)) * t * 0.5)); qj = pj - int(round(math.cos(math.radians(yaw)) * t * 0.5))
        for a in range(-1, 2):
            for b in range(-1, 2):
                yy, xx = qj * scale + 1 + a, qi * scale + 1 + b
                if 0 <= yy < W and 0 <= xx < W: rows[yy][xx*3:xx*3+3] = bytes((30, 90, 255))
    # grid lines every metre
    raw = b''
    for y, r in enumerate(rows):
        wz = (cz + half) - (y / scale) * step
        for i in range(n):
            wx = cx - half + i * step
            if abs(wx - round(wx)) < step / 2 and abs(wx - round(wx)) <= abs(wx + step - round(wx + step)):
                pass
        raw += b'\x00' + bytes(r)
    def chunk(t, d): return struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)
    png = b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', W, W, 8, 2, 0, 0, 0)) + chunk(b'IDAT', zlib.compress(raw)) + chunk(b'IEND', b'')
    out = out or os.path.join(HERE, '..', 'shots', 'map.png')
    open(out, 'wb').write(png)
    print(f"map {out}: centre ({cx:.1f},{cz:.1f}) ±{half} m, {step} m/px*{scale}; up = north; floor y={floor:.2f}; player blue, lidar orange=0.5 m purple=1.3 m")


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
    elif cmd == "map":
        if len(a) >= 3: heightmap(float(a[1]), float(a[2]), float(a[3]) if len(a) > 3 else 6.0)
        else:
            x, _, z, _, _ = pose(); heightmap(x, z)
    elif cmd == "calib": do_calib()
    else: print(__doc__)


if __name__ == "__main__":
    main()
