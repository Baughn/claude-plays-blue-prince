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
- `rooms.md` — catalogue of rooms seen: name, cost, doors, effects, contents
- `mechanics.md` — rules of the game as I understand them
- `open-questions.md` — unexplained things
- `images/` — cropped screenshots worth keeping (maps, diagrams, text)

## Current state
- Day: 1 (just started, in entrance hall)
- Goals: find the 46th room. Learn the basic mechanics first.
- Leads:

## Controls / tooling
See `../tools/README.md`.

## Pending user request (2026-10-02)
After Day 2 ends, move the game to a headless session (sway headless + wayvnc or similar) so the user gets their desktop back. Then use only the virtual gamepad (no uinput keyboard/mouse into KDE).
- TODO with the migration: add probe `cast` (ray from arbitrary origin/dir) to ClaudeProbe and give `nav goto` local obstacle avoidance at knee height (it gets stuck on tables/edges; round table in Entrance Hall centre!).
