# Blue Prince — Claude's notebook

Read this first every session. Keep it short; details live in the linked files.

## Rules I've set myself
- No looking anything up. Everything here comes from playing.
- Don't read the save files, Player.log, or the `drafting-investigation/` folder in the game dir.
- Transcribe every piece of in-game text verbatim into `documents/` the moment I see it, with a crop in `images/`.
- Write down anything odd, even if it doesn't look like a puzzle yet → `open-questions.md`.

## Layout
- `journal/` — one file per in-game day/run, chronological (`day-001.md`, …)
- `documents/` — verbatim text: notes, letters, signs, books, inscriptions
- `puzzles/` — one file per suspected puzzle: what I know, attempts, status
- `grounds.md` — outside map (coords)
- `rooms.md` — catalogue of rooms seen: name, cost, doors, effects, contents
- `mechanics.md` — rules of the game as I understand them
- `open-questions.md` — unexplained things
- `images/` — cropped screenshots worth keeping (maps, diagrams, text)

## Current state
- Day: 3 finished (Call it a Day; summary screen showing). Next session starts Day 4.
- Goals: find the 46th room. Learn the basic mechanics first.
- Leads:

## Controls / tooling
See `../tools/README.md`.

## Pending user request (2026-10-02)
After Day 2 ends, move the game to a headless session (sway headless + wayvnc or similar) so the user gets their desktop back. Then use only the virtual gamepad (no uinput keyboard/mouse into KDE).
- TODO with the migration: add probe `cast` (ray from arbitrary origin/dir) to ClaudeProbe and give `nav goto` local obstacle avoidance at knee height (it gets stuck on tables/edges; round table in Entrance Hall centre!).
- Mod design (user advice): keep ClaudeProbe a **thin proxy** (pose, raw raycast from arbitrary origin/dir, maybe more primitives); put all logic in tools/*.py, editable mid-day. Restarting the game ends the day!
- User hint (Day 2): "there's one area you haven't looked at yet — a lot of new players miss it for days." Don't ask for more. Guess: the **grounds outside the house** (letter: "abandon the path"). Explore outside.

## Day 3 leads (from Day 2)
- Locked doors are common at rank 6–7; Billiard dartboard gives 2 keys — worth drafting Billiard Room early if offered.
- Security terminal: estate inventory, keycard security level, password unknown. Utility Closet breaker: keycard system switch, V.A.C. indicators.
- Grounds: west gate won't open; east drive unexplored beyond x≈145; fountain wish costs a coin.
- Not yet reached the Antechamber (rank 9). Unknown what's needed beyond reaching it.
- Unread: pause menu Room Directory / House History.

## Day 4 leads (from Day 3)
- **Pump Room puzzle** (puzzles/pump-room.md): panel + schematic + pump levers. Unsolved; in-room actions cost no steps, so it's cheap to experiment if drafted early.
- Keys are the bottleneck going north (ranks 5–7 full of locked doors). Billiard Room dartboard = reliable 2 keys (rule known). Closets/Nooks/Storerooms give keys.
- Security door (Darkroom E wall) stayed shut even with keycard system OFF; terminal settings likely reset daily — set offline mode UNLOCKED *and* cut keycard power the same day.
- Darkroom breaker was OFF on the breaker box Day 3 (lights?).
- Grounds: Campsite found E of the Private Drive. User hint about a missed area still open — maybe not outdoors.
- Tools: nav floor (ASCII top-down), nav map (PNG), tools/route, tools/dart N. Rays pass through some walls (no colliders) — trust eyes for doors.
