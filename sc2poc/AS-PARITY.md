# Alien Swarm parity: deltas and plan, 2026-10-24

The goal is a port that plays like Alien Swarm in every way, starting with its first two levels, Landing Bay (`asi-jac1-landingbay_01`) and Cargo Elevator (`asi-jac1-landingbay_02`). Deima Surface Bridge and Rydberg Reactor followed on 2026-10-24 (Phase 8). This note lists where the port differs from AS today and lays out a phased plan to close the gaps.

**Sources:**
- The SDK in `../AlienSwarm/src/game/{server,client,shared}/swarm/`.
- The Steam install in `C:\Program Files (x86)\Steam\steamapps\common\Alien Swarm\swarm\`: weapon scripts, `cfg/difficulty.cfg`, `resource/swarm_english.txt`, `scripts/mod_lessons.txt`, and the two maps' BSPs (entity lump, faces, lights, static props).
- The port as of the working tree on `cargo-elevator`, including the uncommitted laser and fire-rate work.

**Detailed evidence** is in `dist/asref/`:
- `parity-weapons.md`: every gun and item against the scripts and SDK.
- `parity-entities.md`: every spawner, trigger, door, PDA and set piece in both BSPs, in port cells.
- `parity-geometry.md`: floor heights, drops, walls, lights, fog and props from the BSPs.
- `lb01-overlay.png`: the real Landing Bay floor with the port's areas drawn over it.
- `lb01-heights.png`, `lb02-heights.png`: floor height maps. `parity-grid-lb0X.txt`: the real footprints on the port's grid.

**Confidence.** Items marked *checked* were read in the SDK by hand during this review. The rest come from source-reading passes that cite file and line; recheck the cited lines when implementing each one.

**Units.** A port cell is 80 Hammer units when tracing maps (the fit gives 79.8) and about 97 units for speeds (290 u/s is 3 cells/s). This note gives AS values in Hammer units and converts where it matters.

## Where the port stands

| System | Match today | Biggest gaps |
|---|---|---|
| Weapon numbers | Close | Sentry gun does twice AS's damage; sentries can't be hurt, dismantled or rotated |
| Combat feel | Partial | No hurt-slow on aliens; instant turning; sideways aim assist on every gun; no clip-ring reticle |
| Alien stats | Close | Uber too fast; several per-type rules missing |
| Alien behaviour | Weak | Aliens sense the squad at any range through walls; sleepers are visible and wake on noise; boomer, jumper, buzzer, ranger, mortar, harvester, egg and shieldbug all act differently |
| Spawning and director | Partial | Onslaught director matches; spawner orders, burrowed starts and timers are missing |
| Landing Bay layout | Close in the south, loose in the north | One flat floor; 26% of real floor missing; north halls too narrow; dock and yard too big |
| Landing Bay script | Close | PDAs rotated by one; invented 40 s control-door force; missing catwalks, jump links and banging door |
| Cargo Elevator | Invented | Layout, flow, set pieces, ride, alien types and exit are not AS's |
| Elevations | None | Every floor is flat at one height |
| Deaths and failure | Weak | No death camera or banner; tech death always restarts; no infested death |
| Prompts and hints | Partial | Missing lessons, hint priority and the lift's "access denied" pop-up |
| Squad AI | Partial | Breadcrumb follow with hidden teleports instead of AS's formation |
| Marine chatter | Partial (Phase 4) | Barks over the marine on AS's triggers, voiced in each marine's own voice (38 lines a marine, Gemini TTS, `tools/barks.py`), not AS's 124 recorded lines |
| Lighting and fog | Partial | Orange light in the wrong room; outdoor zones missing in the north block and all of Cargo Elevator |
| Deima Surface Bridge | Close (traced) | Built 2026-10-24, not yet run in the client; the dropship is a stand-in, its guns scripted |
| Rydberg Reactor | Close (traced) | Built 2026-10-24, not yet run in the client; the exit doors open after a fixed 32 s, not AS's animation |
| SynTek Residential | Close (traced) | Built 2026-10-24; the autopilot finishes it cleanly (2026-10-25); no grub sacs, the fire extinguishers are scenery |
| Sewer Junction B5 | Close (traced) | Built 2026-10-25; the autopilot finishes it cleanly (2026-10-25); the sumps are drops, the turbine is a button |

## The deltas

### 1. Maps and elevation

**How the port builds maps.** `build.py` puts every level in one map at the same coordinates and swaps them at runtime. The terrain is one flat heightmap at `FLOOR` 8.0, and `build.py:481` asserts that all levels share it. SC2 can't change terrain height at runtime, so with this layout no level can have real height.

**Landing Bay's real heights** (playable floor only):

| Real level | Height | Next to |
|---|---|---|
| Dock, walkway, yard, security gate | 944 | – |
| Gate west balcony | 1024 | 80 above the gate, up a stair |
| Inner storage, annex, maintenance hall, pump room | 872 | 72 below the gate |
| Raised west pump deck | 952 | 80 above the pump room |
| Crew office | 792 | 80 below the pump room |
| Supply strip | 848 | ramp up to the tank room |
| Tank room | 904 | 18.6° ramp from the supply strip |
| North block (stair hall to escape lift) | 832 | 72 below the tank room |
| Flight control island | 872 | 40 up on three bridge ramps over a 616 u pit |

Every stair is a prop (16 in all); there are four walkable brush ramps. Off the route are real drops: the orange-lit pit beside storage (264 u down), six tank pits (744), the hangar pit by the escape lift (800 to 900), and the dock's catwalk edges (2,900 to 3,850, fogged over a black floor).

**Landing Bay's footprint.** The port's rooms are in the right order and the south half sits on the real rooms. The differences:
- 518 cells of real floor (26%) lie outside every port area:
  - The north stair is a wide hall about 24×6 cells.
  - The concourse is 6 to 7 cells deep, not 3.
  - A big west room, about 9×15 cells, stands beside the service way.
  - An east hall runs out from the pump room.
  - A corridor runs west from the security gate.
- The dock and freight yard are drawn about twice their real size. The real ones are catwalk-sized: an L-shaped dock about 11×5 cells and a yard about 8×7.
- The exit passage is 2 to 4 cells further south and wider.

**Cargo Elevator.** `tools/cargo.py` says it was invented, and almost none of it matches:

| | Real | Port |
|---|---|---|
| Walkable floor | 1,806 cells, 76×135, one north-running spine | 3,910 cells on 128×112, running north, east, then south |
| Rooms | About 9 | 17 areas |
| Lift platform | 7.0×6.6 cells | 12×12 cells inside a 16×16 void |
| Exit | An outdoor, snowy bay right beside the shaft, about 21 cells from the platform | A 60-cell hive "lower level" (Freight Junction, Service Shaft, Colony Concourse, Transit Station) that doesn't exist |
| Heights | 832 for the start and gallery, 800 for the pipe hall, lobby and exit, 792 for the platform, 870 for the window alcoves | Flat |

The real route:
1. The start pad, which is Landing Bay's escape lift.
2. A double door into the orange-lit catwalk hall over a 416 u lower bay.
3. An east hallway to a security door (`LandingBayDoor11`, a plain button, auto-open).
4. The north corridor.
5. The fire shaft: a barrel blows, explosions follow at 0, 1 and 1.4 s with a shake and breaking glass.
6. The glass observation gallery. Seven window alcoves have a 40% chance each to spawn strips of drones, and eight drones wait inside at the start.
7. The burrow rooms, then a ramp room.
8. The pipe and gap puzzle: a barrel blast rolls `HugePipe`, which drops a metal platform across a 5,000-damage pit.
9. A second ramp room, then `LandingBayDoor10`.
10. An outdoor yard with a supply cache (two medkits, autogun ammo, an ammo drop), then the lift.

**Cargo Elevator's lift ride:**
- **There are only two objectives:** press the lift button, then reach the exit zone.
- **The lift needs all four marines** (`trigger_lift_marine_check` with playersrequired 4). Pressing early shows an "access denied" info pop-up (`#asw_landingbay_lift1`, image `LandingBayLift`).
- **The ride timeline:**
  - 0 s: the entrance ramp closes.
  - 1 s: start sound.
  - 2 s: shake and a dust burst.
  - 3 s: the walls start at 25 u/s, the top light goes off and the red spinners come on.
  - 4 s: music.
  - 15 s: spawn timers start.
  - 16 s: a 16 s slow-motion beat.
  - 17 s: Insane parasites.
  - 13.8, 37.3, 60.4 and 79.8 s: path events.
  - 106.2 s: the end. A big shake, the exit lights chase, the exit spawners fire, the ramp opens at +1 s and the escape objective arrives at +4 s.
- **The walls travel up and south** (dz +1,992, dy −1,756), an inclined shaft running toward the camera. The port's do the same (Phase 6).
- **Ride spawns are only drones:**
  - A timer every 2 to 3.5 s picks one of 8 groups of infinite jumper spawners.
  - Nine crawler templates spawn every 1.5 to 2 s; each climbs at 80 u/s and then drops a drone.
  - There are no buzzers, ubers, rippers or power surges on the ride.
- **The exit:** exit spawners are ordered to `ElevatorExitTarget`, and the squad crosses about 19 cells of outdoor yard to the exit zone.

**Port inventions in Cargo Elevator:** the security-door override hack, the upper and lower levels, the transit station, the 45 s transit hold, the vent blow, the east-only gallery and the checkpoints.

**What the trigger model can't express today.** Both levels need these, and the Cargo Elevator rebuild needs most of them:
- Random timers (`logic_timer` with a random interval).
- Spawner outputs (`OnAllSpawnedDead`, `SpawnOneAlien`).
- Physics and prop activators, NPC-only triggers and `playersrequired`.
- "All marines past" counters.
- Spawners that start off (SpawnerState 0).
- Alien orders with a target.
- Per-spawner near distance and spawn-time jitter. Today they are fixed at 9.3 cells and ±25% in `src/Objects.galaxy`.
- Movers, path-track pass events and info-message pop-ups.

### 2. Aliens: types and numbers per level

**Landing Bay** (matches the port, 47 reachable spawners):
- **All skills:** 108 finite drones, 5 infinite holdout spawners and 3 jumpers.
- **Normal and up:** adds 5 drones.
- **Hard and up:** adds 2 jumpers.
- **Insane:** adds 12 buzzers, 2 parasites, 5 harvesters, 2 rangers, 3 infinite ranger spawners and 1 boomer.

Port fixes:
- Seven spawners sit more than 1.5 cells off.
- The boomer and a ranger are swapped at the exit.
- `insane_ranger` also starts when the hack starts (+0 s).

**Cargo Elevator** (does not match):

| Skill | AS | Port |
|---|---|---|
| All | 128 drones, 1 infinite drone spawner, 17 infinite jumper spawners | Drones, buzzers, parasites, ubers, a ripper, a mortar, a shieldbug (with 3+ players), scaled by player count |
| Normal+ | +11 drones | – |
| Hard+ | +16 drones | – |
| Insane | +10 drones, 9 parasites, 2 harvesters, 2 rangers, 3 infinite ranger spawners, 2 mortars, 1 boomer | – |

Below Insane, AS's Cargo Elevator is drones only.

**Difficulty scaling** (the `md` table: health, damage, speed, director) already matches `difficulty.cfg`.

### 3. Alien behaviour

**Senses and sleep** (high):
- **AS** *(checked, `asw_alien.cpp:538-548`, `asw_drone_advanced.cpp:1482`)*:
  - An alien sees 768 u and senses the swarm at 576 u through walls.
  - Long-range spawners double that (1,536 and 1,152).
  - A drone with a new enemy widens to 1,768 and 1,200 so it doesn't lose the target, and it gives up past 2,000.
  - Sleeping aliens are hidden and can't be shot. They wake only when a marine's camera views them, plus a 384 u margin, and they don't hear gunfire.
- **Port:**
  - `AS_Nearest(q,1000)` tracks a marine at any range through walls.
  - Sleepers are visible.
  - They wake within 9 cells, or within 16 after gunfire.

**Hits** (high):
- **AS** *(checked, `asw_alien.cpp:946-949`)*:
  - Every hit slows the alien to 0.5× for 0.5 s, refreshed by each hit.
  - The stagger chance is the gun's flinch chance times the health fraction, and a stagger lasts 0.4 to 0.8 s.
  - Bullets don't push.
- **Port:**
  - No hurt-slow.
  - Flinch is `min(0.7, 0.1+0.012×damage)` for 0.22 s, plus a 0.18 push.
  - Bullets push.

**Per type:**

| Alien | AS | Port |
|---|---|---|
| Boomer | Inflates when a marine is within 200 u (a 40% roll each second), then bursts into 1 to 8 blobs: 55 damage, radius 240, fuse 2.5 to 3.4 s. Killed before inflating, it bursts with nothing | Instant 30-damage burst plus 5 blobs on every death |
| Jumper | Jumps only when the predicted landing point is 512 to 1,024 u away; the jump does no damage; 2 to 6 s cooldown | 1.8 to 4 cell pounces that do damage |
| Uber | Half a drone's speed (about 169 u/s), 15 damage; shotguns ×0.6 and lasers ×0.5 armour | Speed 2.9 cells/s, 18 damage, no armour |
| Xenomite | 15-damage kamikaze; dies after 60 s | 5-damage biter |
| Shieldbug | Front shield takes 0% except blasts; shield up and down states; knockdown 500/300; can't be hurt until engaged; never gibs; reach 100 u | ±70° front ×0.1 |
| Buzzer | Bite 15×dt at most once per 1.5 s, with a screen blur 0.6×(1+md/10); charges and bounces; dies when frozen; burns 30 s at 5 with no ×3 | 8 damage per 0.8 s |
| Ranger | 3-shot volley, 12 damage each (not difficulty-scaled), 425 u/s, every 4 s; steps back when hit; no keep-distance | Keeps distance, single shots |
| Mortar | 3 shells, 50 damage, radius 220, fuse 3 s after landing, range 1,500, no line of sight needed, no ground ring | Shows a ground ring, other numbers differ |
| Harvester | Lays a xenomite every 1 s up to 5, range 1,500, no line of sight; flees; 4 to 6 xenomites on death; touch 5 | Different cadence, doesn't flee |
| Egg | 50 HP; opens at 120 u, or a 10% chance per check within 450; hatches in 3 to 6 s; burnable | 30 HP, hatches in 0.7 s |
| Alien goo | 100 HP, hurt only by fire, dissolves under 10, spreads fire, 10 acid per second on touch | Biomass 600 HP |
| Explosive barrel | 4 HP (3+0.45(md−1)), 200 damage radius 160, radius 80 against marines | 30 HP |

**Orders and spawners** (medium):
- AS spawners give orders: MoveTo a target, IgnoringMarines, and SpreadThenHibernate.
- Spawners can start burrowed, with an unburrow window.
- Onslaught opens with a shieldbug and parasite packs.
- Doors take dents. Reinforced doors have 2,400 HP, and a falling door crushes what is under it.
- An infested marine's death releases 3 to 5 parasites.

**Port-only alien behaviour:**
- The ripper.
- Waking on gunfire.
- Keep-distance for ranged aliens.
- The mortar ring.
- The story director when Onslaught is off.
- Damage numbers on by default (AS has them off).

### 4. Weapons and combat feel

All 38 items' clips, reserves, reloads, damage, skill steps, unlock levels, class locks and the XP table match. Fire rates now match in the working tree. The grenade launcher's script `fire_rate` of 1.8 is dead data: its code returns 0.4 *(checked)*, and the port's 0.4 is right. That corrects `dist/asref/combat-sdk-notes.md`.

**Feel (high):**
- Alien hurt-slow and staggers, as above.
- **Turning:** AS turns the marine at 600°/s, or 300°/s while firing, and bullets leave along the turned facing. The port faces the cursor instantly.
- **Sideways aim assist:** AS has it only for the prototype rifle, the autogun and near flares. The plain rifle's assist only fixes the shot's height. The port snaps every gun but the flamer, launcher and tesla, with a default autoaim of 4 (`State.galaxy:290`).
- **The reticle:** AS's cursor is a ring that shows the clip. It drains as you fire, and during a reload it fills and flashes yellow and red with the fast-reload window marked. The port has none.

**Items (high):**
- AS sentries have 300 HP, aliens target them, and they blow up for 150 damage over 400 u.
- Hold E dismantles a sentry back into a weapon with its ammo, and a quick E rotates it.
- The sentry gun fires every 0.1 s at 10×difficulty. The port's every 0.0625 s at 12.8 is twice AS's damage.
- The freeze sentry also does 25 damage; the port's does none.

**Medium:**
- **Friendly fire:** AS uses full damage × difficulty with an armour-absorption ramp. The port uses a flat 50%.
- **The rifle grenade:** AS's flies straight at 1,000 u/s. The port's lobs to the cursor.
- **Electric armour:** fully absorbs claws in AS; the port cuts them ×0.25.
- **Heal beacon:** the low-health boost is 1+3(1−hp) in AS and 1+(1−hp) in the port. The heal gun's cure is spread over the clip in AS.
- **Reloading and switching:** a roll cancels a reload in AS. Switching guns takes 0.5 s, not 0.3. Slow-downs after firing are per gun.
- **Rounding:** the medical gun and launcher rates are rounded to 1/16 s without rescaling heal or damage.
- **Hacking skill:** AS has one; the port doesn't.

**Low:** triangular spread, no camera shake on the shotgun and railgun, a low-ammo click, chainsaw reach 30 u, hornet ±35° radius 50, mine spacing, and the rest in `parity-weapons.md`.

### 5. Marine, deaths and failure

**Tech death** (high, *checked*, `asw_gamerules.cpp:1853-1857`, `6200-6211`):
- In AS a restart only restarts within the first 30 s of a mission. After that the mission fails: a 5.9 s countdown, then MISSION FAILED.
- The port always restarts on the tech's death (`AS_MissionMarineDied`, `AS_WipePulse`). `STATUS.md` states the SDK rule wrongly.

**Death scene** (high). When a marine dies, AS:
- Slows time to 0.035× for 0.4 s.
- Swings the camera from 412 to 200 u at pitch 50, orbiting at 35°/s.
- Holds it 1.75 s, or 5 s for your own marine.
- Makes the squad invulnerable for about 2 s.
- Shows a "KILLED IN ACTION" skull banner and plays a death beep.

The port has none of this.

**Infestation** (medium):
- **AS:**
  - Infestation ticks once a second after about 0.9 s of grace.
  - It tints the screen green and shows "- INFESTED -".
  - An infested death gibs and releases 3 to 5 parasites.
- **Port bug** *(checked)*: the drain calls `AS_HurtMarineBy` every 1/16 s step from point (0,0) (`Marine.galaxy:662-667`). That spawns the blood effect and the red spray 16 times a second, thrown away from the map's corner.

**Other marine rules** (medium):
- Three-hit melee combo (2a, 2b, 2c; 2c has a 70 u hull).
- Stumbles at most every 2 s, and the shieldbug knocks marines down.
- A heartbeat under 60% health, suit sparks under 65% and 35%, and a directional damage indicator.
- A 0.2× slow-motion for 1.8 s on each objective update.
- Stims slow the whole game to 0.35×, not just aliens.
- Rolling gives no parasite immunity, and the roll is an animated dive.
- The mouse wheel cycles weapons in AS; the port zooms.
- AS has a walk key.

### 6. Squad AI

- **Formation** (high): AS keeps three formation slots, including a rear guard at (−120, 0) facing back. It aims at the leader's position 0.3 s ahead and catches up at ×1.1 to ×1.75 speed, with no teleport. The port follows breadcrumbs and teleports hidden bots.
- **Items** (medium):
  - Bots pick up ammo and use ammo bags.
  - Medics heal with the heal gun from 65% up to 85%.
  - Bots don't use their own medkits.
  - The 2, 3 and 4 hotbar keys and a single-marine order arrow are missing.
- **Chatter** (high for feel): AS has 124 chatter types on about 40 triggers: reloading, spotting aliens, low ammo, taking damage, friendly fire, kills and more. The port has none.

### 7. Prompts, pop-ups and hints

- **Lessons:**
  - AS's hints have a priority bump during combat and are pinned to the world.
  - These lessons are missing: Heal Other, Destroy Door, Watch Scanner, Extinguish, Get and Give Ammo, Rotate Sentry, Activate Panel, and Killed By Infestation.
- **Fail advice:** AS scores 16 categories with a three-round cooldown. The port picks one of 9 lines at random.
- **Info messages:** Cargo Elevator's lift "access denied" message is in (`msg_lift_deny`), as a titled message rather than AS's picture pop-up.
- **Sounds:** the scanner's warning and idle pings are missing.
- **Other UI:** AS has a radial emote menu and a vote UI.
- **Progression:** AS gives no XP offline.

### 8. Look and atmosphere

- **Outdoor zones:**
  - Landing Bay has three exterior zones with fog and snow: the dock to the yard, a pocket south of the crew office, and the whole north block (concourse, freight office, flight control). The port has only the first.
  - In Cargo Elevator the lift lobby and the exit bay are outdoors and snowy. The port lights its exit as a hive.
- **Light colour:**
  - About 60% of interior lights are one pale cyan-white (174,198,194), dim, punctuated by bright spots.
  - Warm white floods (223,206,149) light the outdoors.
  - Sodium orange (247,134,60) lights the pit beside storage and the lower bays. The pump room is lit cold.
  - Red comes from 105 red glow sprites and the dock's rotating alarm.
  - The port puts the orange in the pump room and lights the dock cold.
- **Fog:** exterior (39,53,86), interior (120,90,60) and the lift shaft (43,37,32 at 0.9). Exterior film grain is heavy (100).
- **Floors:**
  - The tank room is metal and grating, not concrete.
  - The dock and yard are a third snow-blended.
- **Walls:** 192 u, which the port's 2.5 cells match. There are no ceilings, and overhead pipes and beams hang just under the wall tops.
- **Props:** about 300 railings along the catwalks, truss columns rising out of the drops, oil pipelines and snow cliffs.
- **Particles:** steam vents, drips, leaky roofs and snow through doors. There are no dust-mote entities.

## The plan

The phases are ordered so that the shared systems come first: they change both levels and are what a player feels most. Map rebuilds come after the build can carry real heights.

### Phase 0: decisions and foundations

1. **Settle the open decisions** at the end of this note.
2. **Give each level its own region of the map.** This is the only way to get real elevations, since SC2 can't change terrain height at runtime.
   - Lay the levels side by side. Landing Bay is 64×144 and a traced Cargo Elevator about 76×135, so 140×144 fits SC2's 256 limit.
   - Add a per-level origin to every cell coordinate the Galaxy code uses. Drop the shared-floor assert in `build.py`.
   - Write a per-cell height from the traced plateaus: (z − 832)/80 cells above a base height raised enough to allow the shallow pits.
3. **Build an extractor for the BSPs.** Port the review's reader into `tools/` and dump numbers only: spawners, triggers, doors, lights, plateaus, ramps and props. Commit the generated tables; nothing of Valve's is shipped. This replaces hand-copied coordinates and makes later checks repeatable.
4. **Extend the trigger model** with the items listed under "What the trigger model can't express" in section 1. Both levels need them, and Cargo Elevator can't be rebuilt without them.

**Status (2026-10-24): done, not yet run in the client.** Map layout went to overlap packing (`tools/pack.py`): levels share map space where their floors agree, so the whole campaign fits one 256x256 map, with three levels giving up 2.6 to 15% of their floor vertices where floors clash (see `STATUS.md`). Landing Bay has its real heights; Cargo Elevator stays flat until Phase 6. The extractor is `tools/asextract.py` (tables in `tools/asdata/`), heights `tools/heights.py`, the trigger model `src/Objects.galaxy` (everything in the list above except physics and prop activators, which have nothing to act on in SC2). The other open decisions stand at their recommendations until settled: port-only additions off by default, chatter as text barks, bots count toward the four-marine lift.

### Phase 1: combat feel (both levels)

1. Alien hurt-slow (0.5× for 0.5 s), AS stagger chance and length, and no bullet push.
2. Turn rate 600°/s, 300°/s while firing, with rounds and the laser leaving along the turned facing.
3. Sideways aim assist only for the prototype rifle, the autogun and flares (flare radius ×2). Height-only assist for the others.
4. The clip-ring reticle (a new ring mesh in `tools/fx.py`).
5. Sentries: 300 HP, targeted by aliens, death blast, dismantle and rotate on E, AS's gun rate and damage, and the freeze sentry's damage.
6. Friendly fire with AS's ramp, the straight rifle grenade, full electric armour, beacon and heal-gun numbers, roll cancels reload, 0.5 s switch, per-gun slows, rescaled medical gun and launcher, and the Hacking skill.
7. Fix the infestation drain: one tick a second with no blood effects, from the marine's own position.

These are the open items in `AS-COMBAT.md`'s "Still proposed", plus the weapons audit.

### Phase 2: alien behaviour (both levels)

1. **Senses:** sight 768 and swarm sense 576 through walls, doubled for long-range spawners, widened on a new enemy, and lost past 2,000. Replace the any-range nearest-marine search with a line-of-sight check.
2. **Sleep:** sleepers are hidden and can't be shot. They wake on camera view plus 384 u, not on noise.
3. **Per-type rewrites** to the table in section 3: boomer, jumper, uber, xenomite, shieldbug, buzzer, ranger, mortar, harvester, egg, goo and barrel.
4. **Spawner orders** (MoveTo, IgnoringMarines, SpreadThenHibernate), burrowed starts, Onslaught's opening packs, door dents and crush, and the infested death.
5. **Port-only behaviour** off by default: the ripper, waking on gunfire, keep-distance, the mortar ring, the story director and damage numbers.

### Phase 3: deaths, failure and prompts

1. AS's tech-death rule: restart only within 30 s, else a 5.9 s countdown to MISSION FAILED. Correct `STATUS.md` to match.
2. The death scene: slow motion, the camera swing and orbit, the squad's invulnerability, the "KILLED IN ACTION" banner and the beep.
3. The infestation overlay, the infested death and the other marine rules in section 5.
4. Hints: combat priority, world-pinned hints, the missing lessons, scored fail advice and info-message pop-ups.
5. The scanner sounds, the objective slow-motion beat, game-wide stim slow, and weapon cycling on the wheel.

### Phase 4: squad AI

1. AS's formation: three slots with a rear guard, leader prediction, catch-up speeds and no teleporting.
2. Bots pick up and share ammo, medics heal, and bots don't use their own medkits.
3. The hotbar keys and the single-marine order.
4. Chatter: barks on AS's triggers, in the form decided in Phase 0.

### Phase 5: Landing Bay

1. Re-trace the footprint from the extractor: add the 518 missing cells (north hall, deep concourse, west room, east hall, west gate corridor), shrink the dock and yard to their catwalk shapes, and move the exit passage.
2. Real heights from Phase 0: the balcony, raised decks, crew office, tank room ramp and flight-control bridges, with stairs where AS has stair props.
3. Real pits where the height range allows (the orange pit, tank pits, hangar pit). Paint the deep catwalk drops as today.
4. Script fixes:
   - Rotate the PDAs back to their owners: Howe's mail at (38.2, 48.5), Callen's at (13.6, 71.4) and Cain's at (9.4, 111.8).
   - Fix the seven displaced spawners and the boomer and ranger swap. Start `insane_ranger` with the hack.
   - Remove the invented 40 s control-door force.
   - Add the tank-room catwalks with the hurt pit and the three jump links, the banging first door, and the decor door.
5. Lighting: the orange pit, cold interiors, warm outdoor floods, the red glow sprites and the two missing outdoor zones.

### Phase 6: Cargo Elevator rebuild

Status, 2026-10-24: steps 1 to 7 are built and pass the build's checks, not yet played in the client. `tools/cargo.py` is traced from `asi-jac1-landingbay_02` and runs as a data-driven level (`AS_LV_SCRIPT`). Still to do:
- the falling pipe;
- the exit drawn outdoors.

**The lift, redone after AS's own (2026-10-24, the `cargo-elevator` session):**
- **The platform** is AS's: 8 by 6 cells with the console's notch in its north edge, the floor's trim and hazard plates where AS's are, the orange-red railing along the north edge round the notch, and crates at the south edge.
- **The start** is AS's: "Activate Panel" on the console (`trigger_lift_button`) starts the lift only if everyone alive, up to four, is aboard. Otherwise it shows `msg_lift_deny` ("All unregistered personnel must be on the lift before it can be activated") and can be pressed again. The press completes the first objective. The console's screen is red until the squad is aboard, then green. The autopilot presses it once everyone is on.
- **The shaft** (`tools/elevator.py`) is AS's inclined tube. The walls travel up and south at 25 u/s for 2,655 units (106 s), starting and stopping dead. A train of seven wall segments rides that incline, each carrying what AS's walls show:
  - a flanged pipe along each top edge, and yellow conduits;
  - the east wall's slung cables and X-braced trusses;
  - a caged lamp with its orange-red glow on each wall, each with a light that rides with it.

  The entrance doorway rides up and away in the west wall. The exit doorway comes round in the east wall and stops where the entrance stood.
- **The drop** round the platform lies 6 units below the deck (`VOID_DEPTH`), so the walls and the shaft's ceiling are seen running down into the brown haze north of the platform, as in AS.
- **The beats** follow `relay_lift_but_succeed`:

  | Time | What happens |
  |---|---|
  | 0 s | The ramp and doors shut. |
  | 1 s | The motor starts. |
  | 2 s | Shake, the dust coming down, motor sparks. |
  | 3 s | The walls move. The amber light over the entrance goes out and the red takes over. Rail sparks start, thinning out until 16.5 s. |
  | 4 s | Music. |
  | At the end | The red goes out, with a big shake. The amber beacon turns by the exit, the exit lamps chase green, and the exit ramp can be walked 2 s later. |

  The red beacon is handed down the west wall at the 13, 35, 57 and 75% path events. The ride is lit by the `ASLiftRide` preset.
- **The crawlers** go along the ceiling with the walls, as AS's `path_drone_climb` does, and drop at `ElevatorSpawn_crawl_1` and `_2`.
- **There is no wide framing** on the ride: AS keeps its normal camera.
- `tools/preview_lift.py` renders the ride from the game camera.
- **Seen in the client** (2026-10-25, `-Auto` run d7ef552de590, Normal): p1 pressed the console with all four aboard, and the red beacon was handed over at 0.02, 4.32, 11.66, 18.89 and 24.94 cells. The ride:13, ride:57 and ride:75 events fired at those handovers. The lift arrived after 106.3 s with the exit segment at 2.60 (the entrance's place), and the exit opened. The squad lost no one on the ride, and Cargo Elevator was complete in 181.6 s with no script errors from the lift. In run a8346278852d, with the crawlers logged, six drones climbed along the ceiling and dropped onto the deck, three from each `ElevatorSpawn_crawl` spawner. Each spawner keeps one alive at a time (AS's MaxLiveAliens 1), so most of the timer's calls find it busy, as in AS.
- **Seen in the client** (2026-10-25, the user's report, then a filmed ride at the 10.5 camera): the shaft walls had gone see-through and aliens showed through them. Two fixes were made (7bdd5f5). The lift's models never fade (`OccludingOpacity 1`), and aliens are no longer drawn as silhouettes through walls (`Occlusion Hide`). The walkways' floor showed as grey slabs running out to the walls, so the drop over them is now plain black, and the haze lies only deep down. Frames at 10, 68 and 132 m show both walls solid and red-lit, with black drops either side of the platform.

**Checked against the map, entity by entity (2026-10-25).** Every output of `relay_lift_but_succeed`, the walls' five `path_track`s, `elevator_walls_end` and `relay_block_elevator_exit` was read from `asi-jac1-landingbay_02.bsp`. The SDK (`asw_env_slomo.cpp`, `asw_gamerules.cpp`) was read for the slow motion.

| AS | When | Port |
|---|---|---|
| `relay_block_elevator_entrance`: the ramp closes, the big doors shut, the clip goes on | 0 s | Same |
| `ElevatorButtonSound` (bigelevatoractivate) | 0 s | The console's click |
| `ElevatorStartSound` (elevator_large_start1) | 1 s | A stock lift sound |
| `shake_elevator_start` (amplitude 4, 1 s), `part_lift_start_dust`, a motor spark | 2 s | Same: shake 0.2 for 1 s, the dust |
| `lift_motor_sparks` | 2.5 to 5 s | Same |
| `FreightElevatorWalls` start at 25 u/s over 2,655 u; `light_spin_ele_top` (amber 249,192,0) off; `light_spin_ele_0` (red 249,0,0) on; the move loop | 3 s | Same; the loop is a stock rumble |
| `lift_rail_sparks`, thinning at 4, 6 and 9 s | 3 to 16.5 s | Same |
| `ElevatorMusic` (asw_song.elevatorMusic) | 4 s | A stock battle loop |
| `timer_elevator_spawn` (2 to 3.5 s), `timer_elevator_crawlers_1` (1.5 to 2 s) | 15 s | Same |
| `ElevatorSlomo`: env_slomo, duration 16, which is `StartStim(16)`: the whole game at 0.35 for 16 game seconds | 16 s | **Fixed today.** It was a 0.9 s dip to Slower; now it is a 16 s adrenaline stim (`as_slowMo`) |
| `ins_para_spawn` (Insane only) | 17 s | Same |
| `ElevatorCamera` (point_camera) on | 15 s | Nothing: it feeds a monitor texture, and the player's view is unchanged |
| path 13/35/57/75%: the red beacon handed down `light_spin_ele_1`..`4`; Insane parasites at 13% and 57% (+5 s); the crawler timer off at 75% | path events | Same (logged in run d7ef552de590) |
| `elevator_walls_end`: red off, `light_spin_ele_bottom` (amber) on, loop off, stop sound, `shake_elevator_stop` (amplitude 12, 2 s), exit lamps chasing 0.3 s apart for good, `ExitSpawner` on, `ins_para_spawn4` at 0.5 s, the groups and spawn timer off at 5 s | arrival | Same. **Fixed today:** the stop shake is three times the start's (0.6) |
| `relay_block_elevator_exit`: the ramp opens; its clip goes 2 s later | arrival +1 s, walkable +3 s | **Fixed today:** it was walkable at +2 s; now the doors part from +1.3 s and it opens at +3 s |
| `commander_choreo_m1_ob3` (scene `co_m1_ob6`) | arrival +5 s | Same: "We better get to the colony to see what we can find." AS has no caption for it; the user transcribed it from `sound/vo/command/co_m1_ob6.wav` |
| `fog_elevator` (43,37,32, density 0.9) in the shaft | the ride | The haze mesh in the drop and the drifting haze over the deck, with the `ASLiftRide` light preset. SC2's own fog was tried in this colour during the ride (densities 0.3 and 0.6, 2026-10-25) and dropped. It is height fog, so it greyed the whole picture, deck and marines included, and the red light went with it; blood and acid decals drew as black shapes. AS's fog is by distance (256 to 4,000 units), so at the camera's 412 the deck is barely touched and only the far shaft browns, which is what the haze in the drop gives |

**Seen in the client, after those fixes** (2026-10-25, an `-Auto --start 1` build of the working tree):
- Pressed at t=69.1 with four aboard.
- The slow motion came at t=85.1, exactly 16 s later. The blue adrenaline tint came on as the first drones landed. From the log's clock against the wall clock, script time ran 1:1 until then. The next 22.8 s of it took 54 real seconds, so the 16 s stim ran at about 0.34, AS's 0.35.
- Six crawlers dropped.
- The lift arrived after 106.3 s of travel at t=178.3, and the exit opened at t=181.3 (3.0 s).
- Cargo Elevator was complete in 187.3 s, with no script error log.

Still not AS's: the sounds and music are stock SC2 stand-ins, since Valve's files can't be shipped. The commander's lines in Cargo Elevator (`co_m1_ob6`, `ob7`, `ob8`) have no captions in AS, so the user transcribed them from the voice files. They now use AS's own words.

1. Replace `tools/cargo.py` with the traced map: the nine real rooms, real heights and a 7×6.6-cell lift.
2. Rebuild the route and set pieces in AS's order: the double door, the orange catwalk hall, the security door, the fire shaft, the glass gallery with its window spawners, the burrow rooms, the pipe puzzle, the yard cache and the lift.
3. Two objectives only. The lift needs all four marines and shows the access-denied pop-up otherwise.
4. AS's ride timeline, with the walls moving up and south at 25 u/s for 106 s. Spawns are jumper groups on a 2 to 3.5 s timer plus crawlers every 1.5 to 2 s.
5. The exit: a short outdoor yard with exit spawners ordered to the exit target.
6. Remove the inventions: the hack, the lower level, the transit station and hold, the vent blow and the checkpoints.
7. AS's roster per skill from section 2.

### Phase 7: verification

1. Extend `tools/lbcheck_spawners.py` into a checker that compares every built spawner, trigger, door and objective with the extractor's tables for both levels.
2. Overlay checks like `lb01-overlay.png` for both levels after each layout change.
3. Autopilot runs on each skill level, logging alien counts by type and time to finish, compared with AS's totals.
4. Side-by-side play against the recorded demos (`lb_run1.dem`, `ce_run1.dem`, `combat1.dem`).

### Phase 8: the rest of Jacob's Rest

The next missions after Cargo Elevator are traced from their maps from the start, so they need no rebuild: their layout, heights, spawners, triggers, doors and objectives are the extractor's.

1. **Deima Surface Bridge** (`tools/deima.py`): done 2026-10-24.
2. **Rydberg Reactor** (`tools/rydberg.py`): done 2026-10-24.
3. **SynTek Residential** (`tools/residential.py`): done 2026-10-24.
4. **Sewer Junction B5** (`tools/sewer.py`): done 2026-10-25.
5. **Timor Station:** to do. It will be a module like the ones above. Six levels already need the packer's backtracking search (`tools/pack.py` `search`). In `tools/pack.py --campaign`, Timor Station gives up 2.6% of its floor vertices.

Both done missions run on the scripted-mission data (`STATUS.md`). What they do differently from AS:
- **Deima:** the dropship is a stand-in model on path nodes, and its turrets are scripted.
- **Rydberg:**
  - The north doors open on a fixed delay rather than AS's mover animation.
  - The reactor core is a prop rising out of a well opened for it; AS's fall volumes there lie under the floor.
- **Residential:**
  - AS's grub sacs, which burst into grubs as a marine passes, are left out. The grubs themselves sleep where AS places them.
  - The office windows are a door kind that gives way when a marine comes up or a drone swipes. AS's break to any damage.
  - The elevator's second mortarbug template is left out.
- **Sewer Junction:**
  - The sumps under the north walkways are a drop. AS's sludge floor down there is walkable, and its route dips into the sump by the turbine, which is decked over here.
  - The turbine's control is a button rather than a prop to shoot, and the turbine itself is not modelled.
  - The tunnel is rock beyond its mouth from the start. One charge going up brings it down; AS counts four breakables.
  - The tunnel's growth stands on the mouth's flanks rather than over it.
  - The PDW, shotgun and rifle pickups have no item in the port.
  - The catwalk bridge, the channel walks and the turbine catwalk are one cell wide, as in AS, and aliens spawn in them or sleep at their ends. An alien standing in one of them can hold the autopilot marine in place. `AS_AutoUnstick` (`src/Bots.galaxy`, fcbe94f) steps it free after 4 s pinned. Before that commit, a build of the commits alone sat at the bridge (run 5ba7b412cc34).

**Status:** both are built and checked offline, and both play to the end in the client. The full-campaign autopilot run (a8346278852d) and a Sewer-only run (29ace728390a) of the working tree, and runs of the commits alone (Sewer f2d4f2b5d4eb in 265.1 s, SynTek Residential c6fd5b44417c in 399.6 s), finished with 0 kit leaks. The commits-alone runs raised one script error, an unknown button sound, which 7f55f00 replaced; no run has been made since that fix.

## What SC2 can't match exactly

- **Lighting per room.** SC2 lighting is one preset for the whole map, so room-by-room colour has to come from lights placed as doodads and painted floors.
- **Fog per zone.** Fog is global; zones have to be faked with haze effects.
- **Slow motion is global** in multiplayer, as AS's is.
- **Alien and marine art.** The port uses SC2 stand-in models; no Valve models or textures can ship.
- **Voice.** AS's chatter audio can't ship either. The options are text barks, SC2 voice lines or newly recorded lines.
- **Deep drops.** Terrain height is limited, so drops deeper than a few cells stay painted.
- **Physics.** The rolling pipe, breaking glass and falling doors have to be scripted.

## Decisions needed

1. **Map layout.** Separate regions with real heights (recommended), or keep one flat map and fake steps with ramps and props.
2. **Port-only additions.** Turn them off by default with an option to keep them (recommended), or delete them outright. The list: the story director, the ripper, waking on gunfire, keep-distance, the mortar ring, damage numbers, the Cargo Elevator inventions and the Landing Bay control-door force.
3. **Chatter.** Text barks, SC2 voice lines or new recordings.
4. **A short squad.** AS's lift needs four marines. With fewer players, bots fill the squad, so the check counts bots.
