#!/usr/bin/env python3
"""Virtual keyboard + mouse + Xbox 360 pad daemon for playing via uinput.

Run:   nix-shell -p python3Packages.evdev --run "python3 tools/inputd.py"
Talk:  tools/inp <command> [; <command> ...]

Commands (one per line or ';'-separated):
  key NAME [ms]        tap key (default 60ms hold). NAME like w, space, esc, enter, KEY_LEFTSHIFT
  hold NAME ms         hold key for ms
  combo A+B [ms]       hold several keys together
  type TEXT            type literal text (a-z0-9 space and basic punctuation)
  move DX DY [steps]   relative mouse move, split into steps (default auto)
  click [left|right|middle] [ms]
  mdown / mup [btn]    press / release mouse button
  scroll N             wheel clicks (+up / -down)
  pad BTN [ms]         tap gamepad button: a b x y lb rb back start guide ls rs
  padhold BTN ms       hold gamepad button
  dpad DIR [ms]        tap d-pad: up down left right
  stick L|R X Y ms     hold a stick at X,Y in [-1,1] (Y: -1 = up/forward) for ms, then recenter
  sticks LX LY RX RY ms  both sticks at once (e.g. walk while turning)
  trig L|R [ms]        pull a trigger fully for ms
  wait ms
  release              release everything
Every command batch ends with a release-all. The daemon also releases on exit.
"""
import os, socket, sys, time, signal
from evdev import UInput, AbsInfo, ecodes as e

SOCK = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".inputd.sock")

# Pad only: virtual keyboard/mouse devices would deliver input to the user's KDE desktop.
# For typing into the game, use tools/type (wtype into the headless sway session).
class _NoDev:
    def write(self, *a): raise RuntimeError("keyboard/mouse disabled (pad-only daemon); use tools/type for text")
    def syn(self): pass
kbd = mouse = _NoDev()
PAD_BTNS = {"a": e.BTN_SOUTH, "b": e.BTN_EAST, "x": e.BTN_NORTH, "y": e.BTN_WEST, "lb": e.BTN_TL,
            "rb": e.BTN_TR, "back": e.BTN_SELECT, "start": e.BTN_START, "guide": e.BTN_MODE,
            "ls": e.BTN_THUMBL, "rs": e.BTN_THUMBR}
_st = AbsInfo(value=0, min=-32768, max=32767, fuzz=16, flat=128, resolution=0)
_tr = AbsInfo(value=0, min=0, max=255, fuzz=0, flat=0, resolution=0)
_hat = AbsInfo(value=0, min=-1, max=1, fuzz=0, flat=0, resolution=0)
pad = UInput({e.EV_KEY: list(PAD_BTNS.values()),
              e.EV_ABS: [(e.ABS_X, _st), (e.ABS_Y, _st), (e.ABS_RX, _st), (e.ABS_RY, _st),
                         (e.ABS_Z, _tr), (e.ABS_RZ, _tr), (e.ABS_HAT0X, _hat), (e.ABS_HAT0Y, _hat)]},
             name="Microsoft X-Box 360 pad", vendor=0x045e, product=0x028e, version=0x110, bustype=e.BUS_USB)
time.sleep(1.0)

held_keys, held_btns = set(), set()

ALIASES = {"esc": "ESC", "escape": "ESC", "enter": "ENTER", "return": "ENTER", "space": "SPACE",
           "shift": "LEFTSHIFT", "ctrl": "LEFTCTRL", "alt": "LEFTALT", "tab": "TAB",
           "up": "UP", "down": "DOWN", "left": "LEFT", "right": "RIGHT", "bksp": "BACKSPACE",
           "backspace": "BACKSPACE", "del": "DELETE"}
PUNCT = {" ": ("SPACE", False), "-": ("MINUS", False), ".": ("DOT", False), ",": ("COMMA", False),
         "/": ("SLASH", False), "'": ("APOSTROPHE", False), "?": ("SLASH", True), "!": ("1", True)}
BTNS = {"left": e.BTN_LEFT, "right": e.BTN_RIGHT, "middle": e.BTN_MIDDLE}


def code(name):
    n = name.strip()
    if n.upper().startswith("KEY_"):
        return e.ecodes[n.upper()]
    n = ALIASES.get(n.lower(), n.upper())
    return e.ecodes["KEY_" + n]


def kdown(c):
    kbd.write(e.EV_KEY, c, 1); kbd.syn(); held_keys.add(c)


def kup(c):
    kbd.write(e.EV_KEY, c, 0); kbd.syn(); held_keys.discard(c)


def pad_center():
    for a in (e.ABS_X, e.ABS_Y, e.ABS_RX, e.ABS_RY, e.ABS_Z, e.ABS_RZ, e.ABS_HAT0X, e.ABS_HAT0Y):
        pad.write(e.EV_ABS, a, 0)
    for b in PAD_BTNS.values():
        pad.write(e.EV_KEY, b, 0)
    pad.syn()


def axis(v):
    return int(max(-1.0, min(1.0, float(v))) * 32767)


def release_all():
    pad_center()
    held_keys.clear(); held_btns.clear()


def sleep_ms(ms):
    time.sleep(max(0, float(ms)) / 1000.0)


def run(cmd):
    p = cmd.split()
    if not p:
        return
    op, a = p[0].lower(), p[1:]
    if op == "key":
        c = code(a[0]); kdown(c); sleep_ms(a[1] if len(a) > 1 else 60); kup(c)
    elif op == "hold":
        c = code(a[0]); kdown(c); sleep_ms(min(float(a[1]), 15000)); kup(c)
    elif op == "combo":
        cs = [code(x) for x in a[0].split("+")]
        for c in cs: kdown(c)
        sleep_ms(min(float(a[1]) if len(a) > 1 else 80, 15000))
        for c in reversed(cs): kup(c)
    elif op == "type":
        text = cmd.split(None, 1)[1] if len(p) > 1 else ""
        for ch in text:
            if ch.isalpha():
                n, sh = ch.upper(), ch.isupper()
            elif ch.isdigit():
                n, sh = ch, False
            else:
                n, sh = PUNCT[ch]
            c = e.ecodes["KEY_" + n]
            if sh: kdown(e.KEY_LEFTSHIFT)
            kdown(c); sleep_ms(30); kup(c)
            if sh: kup(e.KEY_LEFTSHIFT)
            sleep_ms(30)
    elif op == "move":
        dx, dy = int(float(a[0])), int(float(a[1]))
        steps = int(a[2]) if len(a) > 2 else max(1, max(abs(dx), abs(dy)) // 20)
        sx = sy = 0
        for i in range(1, steps + 1):
            tx, ty = dx * i // steps, dy * i // steps
            mouse.write(e.EV_REL, e.REL_X, tx - sx); mouse.write(e.EV_REL, e.REL_Y, ty - sy); mouse.syn()
            sx, sy = tx, ty
            time.sleep(0.005)
    elif op == "click":
        b = BTNS[a[0]] if a else e.BTN_LEFT
        mouse.write(e.EV_KEY, b, 1); mouse.syn(); sleep_ms(a[1] if len(a) > 1 else 60)
        mouse.write(e.EV_KEY, b, 0); mouse.syn()
    elif op == "mdown":
        b = BTNS[a[0]] if a else e.BTN_LEFT
        mouse.write(e.EV_KEY, b, 1); mouse.syn(); held_btns.add(b)
    elif op == "mup":
        b = BTNS[a[0]] if a else e.BTN_LEFT
        mouse.write(e.EV_KEY, b, 0); mouse.syn(); held_btns.discard(b)
    elif op == "scroll":
        n = int(a[0]); s = 1 if n > 0 else -1
        for _ in range(abs(n)):
            mouse.write(e.EV_REL, e.REL_WHEEL, s); mouse.syn(); time.sleep(0.03)
    elif op in ("pad", "padhold"):
        b = PAD_BTNS[a[0].lower()]
        ms = a[1] if len(a) > 1 else 80
        pad.write(e.EV_KEY, b, 1); pad.syn(); sleep_ms(min(float(ms), 15000))
        pad.write(e.EV_KEY, b, 0); pad.syn()
    elif op == "dpad":
        ax, v = {"up": (e.ABS_HAT0Y, -1), "down": (e.ABS_HAT0Y, 1),
                 "left": (e.ABS_HAT0X, -1), "right": (e.ABS_HAT0X, 1)}[a[0].lower()]
        pad.write(e.EV_ABS, ax, v); pad.syn(); sleep_ms(a[1] if len(a) > 1 else 80)
        pad.write(e.EV_ABS, ax, 0); pad.syn()
    elif op == "stick":
        ax, ay = (e.ABS_X, e.ABS_Y) if a[0].upper() == "L" else (e.ABS_RX, e.ABS_RY)
        pad.write(e.EV_ABS, ax, axis(a[1])); pad.write(e.EV_ABS, ay, axis(a[2])); pad.syn()
        sleep_ms(min(float(a[3]), 15000))
        pad.write(e.EV_ABS, ax, 0); pad.write(e.EV_ABS, ay, 0); pad.syn()
    elif op == "sticks":
        vals = list(zip((e.ABS_X, e.ABS_Y, e.ABS_RX, e.ABS_RY), a[:4]))
        for ax, v in vals: pad.write(e.EV_ABS, ax, axis(v))
        pad.syn(); sleep_ms(min(float(a[4]), 15000))
        for ax, _ in vals: pad.write(e.EV_ABS, ax, 0)
        pad.syn()
    elif op == "trig":
        ax = e.ABS_Z if a[0].upper() == "L" else e.ABS_RZ
        pad.write(e.EV_ABS, ax, 255); pad.syn(); sleep_ms(a[1] if len(a) > 1 else 80)
        pad.write(e.EV_ABS, ax, 0); pad.syn()
    elif op == "wait":
        sleep_ms(min(float(a[0]), 30000))
    elif op == "release":
        release_all()
    else:
        raise ValueError("unknown op " + op)


def shutdown(*_):
    release_all()
    try: os.unlink(SOCK)
    except FileNotFoundError: pass
    sys.exit(0)


signal.signal(signal.SIGTERM, shutdown)
signal.signal(signal.SIGINT, shutdown)
try: os.unlink(SOCK)
except FileNotFoundError: pass
srv = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
srv.bind(SOCK); srv.listen(1)
print("inputd ready", flush=True)
try:
    while True:
        conn, _ = srv.accept()
        with conn:
            data = b""
            while not data.endswith(b"\n\n"):
                chunk = conn.recv(65536)
                if not chunk: break
                data += chunk
            out = "ok"
            try:
                for line in data.decode().replace(";", "\n").splitlines():
                    run(line)
            except Exception as ex:
                out = "error: %r" % ex
            finally:
                release_all()
            try:
                conn.sendall(out.encode())
            except OSError as ex:
                print("client gone:", ex, flush=True)
finally:
    shutdown()
