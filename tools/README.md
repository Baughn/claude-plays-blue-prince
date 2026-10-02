# Tools

## Setup: headless session (since end of Day 2)
The game runs inside a headless sway session, not on the user's KDE desktop.
- `headless/start` — starts systemd user units `bp-sway` (sway + wayvnc on 127.0.0.1:5900) and `bp-inputd`
  (virtual Xbox 360 pad), plus a silent PipeWire sink `bp-sink` for game audio.
- `headless/stop` — stops all of it and removes the sink.
- Steam launch options for Blue Prince: `/home/svein/dev/blueprince/tools/launch %command%`
  (enables BepInEx; puts the game in the headless session if it's running, else on the normal desktop).
- Watch / take over: `nix run nixpkgs#tigervnc -- vncviewer localhost:5900` (or krdc vnc://localhost:5900).
- Launch the game: `steam steam://rungameid/1569580`.

## Input
- `tools/inp "pad a; stick L 0 -1 800; stick R 0.5 0 300; dpad up; trig R"` — gamepad only.
  Keyboard/mouse commands are disabled on purpose (they'd reach the KDE desktop).
- `tools/type "text"` / `tools/type -k Return` — keyboard into the game via sway (wtype). Use for terminals.
- Pad: A interact, B back, Y alt action (e.g. fountain wish), Start pause, RT blueprint, LT day history (in blueprint).
  Left stick in a "selection" close-up (dartboard) points at things; d-pad moves toward a direction.

## Seeing
- `tools/shot NAME` → `shots/NAME.png` (2560x1440) + `shots/NAME.small.jpg` (1280x720; ×2 for full-res coords)
- `tools/shot crop NAME WxH+X+Y` — full-res crop for reading text
- `tools/pano NAME` — 8 shots 45° apart, montaged
- `tools/record start NAME [interval]` / `stop NAME` — frames + audio (from bp-sink) + whisper transcript
- `tools/peek NAME` — latest frame of an in-progress recording
- `tools/focus` / `tools/activate` — focused window in the headless session

## Navigation (`tools/nav`, logic in tools/nav.py — edit freely mid-day)
Backed by the ClaudeProbe BepInEx plugin (mod/ClaudeProbe), a thin proxy on 127.0.0.1:7777:
`pose`, `ray`, `cast ox oy oz dx dy dz [max]` (multiple lines per request). Geometry only, no object names.
Rebuilding the plugin needs a game restart, and **restarting mid-day abandons the day**.
- `nav pose | face YAW [PITCH] | turn DEG | lookat X Y Z | goto X Z [TOL] | fwd M | ray | scan [N]`
- `nav aim/approach YAW PITCH PX PY [STANDOFF]`, `nav here PX PY`, `nav near PX PY [STANDOFF]` — pixel-targeting
- `nav calib` — measures stick turn rates and walk speed → tools/nav_calib.json. Run once in an open room.
- World: x = east, z = north, yaw 0 = north, 90 = east. Room grid pitch ≈ 9.7 m; Entrance Hall centre ≈ (34.9, 15.2).

## Lessons
- Never send mouse clicks to the desktop (happened once with the old setup).
- Whisper: `-mc 0` prevents repetition loops; "Thank you." / "*music*" over music = no speech.
- jj refuses files >1 MiB: keep notes images as JPG.
