# Tools
- Start daemon: `nix-shell -p python3Packages.evdev --run "python3 tools/inputd.py"` (background)
- `tools/inp "key w 500; move 300 0; click"` — sends input only if the game window has focus
- `tools/shot NAME` — capture the active window → `shots/NAME.png` + `shots/NAME.small.jpg`
- `tools/shot crop NAME WxH+X+Y` — full-res crop for reading text
- `tools/focus` — title of the focused window
Game window: fullscreen 3440x1440 on DP-2; game renders 2560x1440 pillarboxed, `shot` crops to that (small.jpg = half scale, so multiply coords by 2).
