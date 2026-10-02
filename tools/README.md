# Tools

## Startup (every session)
1. Start daemon in background: `nix-shell -p python3Packages.evdev --run "python3 tools/inputd.py"`
2. Once it prints "inputd ready": `tools/flatmouse` (otherwise mouse turns are not repeatable)
3. If the game isn't focused: `nix run nixpkgs#xdotool -- search --name "BLUE PRINCE" windowactivate`

## Commands
- `tools/inp "key w 500; move 300 0; click"` — input, only sent if game window has focus. See inputd.py docstring for all ops
  (keyboard, mouse, and an emulated Xbox 360 pad: `pad a`, `stick L 0 -1 800`, `stick R 1 0 500`, `dpad up`, `trig R`).
- `tools/shot NAME` → `shots/NAME.png` (2560x1440) + `shots/NAME.small.jpg` (1280x720; multiply coords by 2)
- `tools/shot crop NAME WxH+X+Y` — full-res crop for reading text
- `tools/record start NAME` / `stop NAME` — record audio + frames, then whisper transcript (for cutscenes/voice)
- `tools/peek NAME` — latest frame of an in-progress recording
- `tools/focus` — title of focused window

## Calibration (flat mouse)
- Mouse: 360° ≈ 5480 units, 90° ≈ 1370, 1° ≈ 15. Repeatable to the pixel.
- Right stick at 1.0 ≈ ~100°/s but noisy; don't use it for precise turns.
- Game renders 2560x1440 pillarboxed inside a 3440x1440 fullscreen window; `shot` crops to that.
- Whisper: `-mc 0` prevents repetition loops; a lone "Thank you." over music is a hallucination.
