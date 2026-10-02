# Mechanics (as observed)

## The estate grid
- Blueprint map (RT opens it) shows the estate as a **5 columns × 9 rows = 45 cells** grid → "45-room estate".
- **Entrance Hall** = bottom row, middle column (col 3, row 9). Doors: W, N, E (S = front door, outside).
- **Antechamber** = top row, middle column (col 3, row 1), shown pre-placed from day 1. Doors on all 4 sides incl. **N edge (off-grid!)**.
- Blueprint also has an INVENTORY panel, a dashed empty square (selected item / slot?), and a "CALL IT A DAY" button.
- Letter: rooms behind a given door change from day to day.

## Steps
- Bequest mode: 50 steps at start of each day. Walking inside a room does NOT cost steps.
- (Hypothesis: entering a room costs a step. Verify.)

## Controls (gamepad)
- A = interact (eye icon = read/inspect, hand icon = pick up). B = back/close. D-pad L/R = turn pages. RT = Blueprint menu.
- Crosshair is a tiny triangle at screen center; changes to an icon on interactables.

## Drafting
- Opening an unexplored door → "SELECT A ROOM TO DRAFT": choose 1 of 3 rooms. The room is placed in the grid cell behind the door.
- Draft tiles are drawn with the **entry door at the bottom**; when placed they rotate so the bottom faces the door you came through.
  (Entering eastward: tile-up = east, tile-left = north, tile-right = south.)
- Each entry into a room costs 1 step (49 after entering first room). Bedroom: "Whenever you enter this room, gain 2 steps".
- Room colours: purple = bedroom, blue = regular rooms (Closet, Nook, Den), orange = hallways (Hallway, Corridor).
- Rooms can list contents: Closet "2 items", Nook "+1 key", Den "+1 gem". Corridor: "always left unlocked" → other doors can be locked.
- Room name + "Rank N" shown bottom-right in the room. Rank = row counted from the bottom (Entrance Hall = rank 1, Antechamber = rank 9).

## Rooms seen in drafts (Day 1)
- Bedroom (W,S rel.) +2 steps on entry · Closet (S only) 2 items · Hallway (T: L,R,S) · Nook (S,R) +1 key · Den (U,S,R; fireplace on L) +1 gem · Corridor (U,S) always unlocked

## Days
- Quitting to menu mid-day ENDS the day: on return it was Day 2 with a fresh map. Finish/"call it a day" before restarting the game.
- Each day starts at 8:00 on the clock tower (outside by the fountain, walking up to the door). Map resets to Entrance Hall + Antechamber only.
- Walking out the front door and back in costs steps (lost 2 on Day 2 doing that). Calibrate/test indoors.
- User says there is no real-time limit.

## Parlor game (see puzzles/parlor-three-boxes.md)
- Parlor: 3 boxes (black/white/blue) with statements + a wind-up key on the desk + rules letter. One guess. Prize = gems (2 on Day 2).
- Locked doors exist: prompt 'THE DOOR IS LOCKED' with USE (key) / EXIT. (Spare Room N door, rank 4→5, Day 2)
- **Some rooms cost gems to draft**: drafting Commissary took 1 gem (4→3). Check the draft card for a gem cost before picking.
- Commissary shop (Day 2): Gem(1)=3 coins, Sledge Hammer=8, Set of Gems(4)=10, Running Shoes=8. Opened via basket icon on the register. Exit = B.
- Tutorial card (Drawing Room): "Each time you click on a door, you will DRAW three floorplans, from which you must select one to draft. However, there are some items and rooms that will allow you to 'redraw' if you do not like your initial three options." Drawing Room = can redraw while drafting from it.
- Drafting Drawing Room cost 1 gem (3→2).
- Locked door with 0 keys: no prompt, just a brief 'locked.' text flash (easy to miss — use tools/record to catch it). Drawing Room E door (col2 r5) was locked, Day 2.
- **Fruit restores steps**: orange = +5 steps (Pantry, Day 2). Note implies apples/bananas too. Eat with A (hand icon).
- Blueprint map: LT opens a **day history** (per-day map + stats). Day One was titled 'MT. HOLLY — ABANDONED PROJECT' (4 rooms, rank 1, 2 steps, 0 items) — because I quit to menu mid-day.
- Day end summary gives the house a title by size (Day 1 abandoned → "Abandoned Project"; 20 rooms → "Charming Cottage"). "Items Found" excludes keys/gems/coins → real *items* (tools?) exist.
- Quitting the game mid-day abandons the day. End days with Call it a Day.
- **Coat Check** room exists: 'Check one item and retrieve it on another day' → cross-day item storage!
- **Banana = +3 steps** (orange +5).
- Door positions: the BLUEPRINT tile preview (RT, top-left of map) shows exact door gaps. Doors so far always at/near edge midpoints. Bedroom (this variant) = S+E only.
- Green rooms (e.g. Terrace) don't cost gems to draft.
- Chapel charges the coin EVERY time you pass through (lost 3 coins on Day 3 going back and forth). Avoid routing through it twice.
- **Items** exist (counted in 'Items Found'): first one = **Small Coin Purse** (Parlor side table, Day 3): every 3 coins collected → +1 coin interest. Items appear in INVENTORY on the blueprint.
- Doors are NOT always at wall midpoints (Billiard Room W door at z≈45, room centre z≈43.5). Find them by scanning the wall for a recess (nav casts) or by eye.
- **Ivory Die** (Closet): consumable '+1 die' — while drafting, use to roll new floorplans. Closet 'items' can include keys (gold key = normal key).
- Rooms come from a **Draft Pool**; some rooms (The Pool) ADD rooms to today's pool (Locker Room, Sauna, Pump Room).
- **Security doors**: striped metal door with red keycard reader (Darkroom E wall, Day 3). Need keycard (or keycard system off + offline unlocked?).
