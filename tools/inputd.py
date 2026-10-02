#!/usr/bin/env python3
"""Virtual keyboard + mouse daemon for playing via uinput.

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
  wait ms
  release              release everything
Every command batch ends with a release-all. The daemon also releases on exit.
"""
import os, socket, sys, time, signal
from evdev import UInput, ecodes as e

SOCK = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".inputd.sock")

KEYS = [v for k, v in e.ecodes.items() if k.startswith("KEY_") and isinstance(v, int) and v < 0x100]
kbd = UInput({e.EV_KEY: KEYS}, name="claude-virtual-keyboard")
mouse = UInput({e.EV_KEY: [e.BTN_LEFT, e.BTN_RIGHT, e.BTN_MIDDLE],
                e.EV_REL: [e.REL_X, e.REL_Y, e.REL_WHEEL]}, name="claude-virtual-mouse")
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


def release_all():
    for c in list(held_keys):
        kup(c)
    for b in list(held_btns):
        mouse.write(e.EV_KEY, b, 0); mouse.syn(); held_btns.discard(b)


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
            conn.sendall(out.encode())
finally:
    shutdown()
