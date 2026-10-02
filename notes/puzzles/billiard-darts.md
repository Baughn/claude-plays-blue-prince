# Billiard Room dartboard (Day 2) — SOLVED → 2 keys

Dartboard in a cabinet; cabinet doors are chalkboards with + − × ÷ chalked on them. Darts on the ledges (L: 1 green; R: green, red, green).
A on board → board close-up. **Left stick held toward an angle (~1s) moves selection to that sector** (d-pad moves toward a direction too, not free stepping). A = throw.
Stick angle: x = sin(a), y = -cos(a), a = clockwise from 20 at top. Sectors clockwise: 20,1,18,4,13,6,10,15,2,17,3,19,7,16,8,11,14,9,12,5 (18° apart).

Each round shades segments; answer = a sector number. No visible "correct" feedback; the board just changes.
- R1: blue inner-single on 17 → threw 17 → new round.
- R2: blue 5, blue 7 → threw 12 (blue = add) → new round.
- R3: blue 18 (inner single), **yellow 4 (treble ring)** → threw 14 (yellow = subtract?) → new round.
- R4: blue 3, yellow 1 (treble) → threw 2 ✓
- R5: blue 4, **pink 2 (outer single)** → threw 8 (pink = ×) ✓
- R6: blue 12, yellow 7 (treble), pink 4 (outer single) → threw 20 = (12−7)×4 ✓ → board swung open, **2 keys** inside.

## RULE (confirmed)
Rings from centre outward = chalkboard ops top to bottom: inner single (blue) = +, treble (yellow) = −, outer single (pink) = ×, double ring (colour?) = ÷ (not yet seen).
Apply in ring order (inside → out). Blue values are the starting/added numbers. 6 rounds; no penalty observed.

## Day 3 instance (dartboard on N wall)
R1 blue 16 → 16 ✓. R2 blue 1,9,3 → 13 ✓. R3 blue 9,4, yellow 6 → 7 ✓. R4 blue 15, yellow 11, pink 3 → 12 ✓. R5 blue 9, yellow 1, pink 2 → 16 ✓ → opened, **2 keys**. (5 rounds this time.)
Helper: `tools/dart N [throw]` selects sector N.
Order of operations so far: all blues summed, then −yellow, then ×pink. Not yet seen ÷ (double ring).
