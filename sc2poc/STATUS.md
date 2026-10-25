# Halcyon Drift: Alien Swarm combat proof of concept (work in progress)

**Status (2026-10-25): six missions in the campaign: Landing Bay (after Alien Swarm's first mission, with its briefing, hacking, death rules, difficulty, hints and progression), Cargo Elevator, and Jacob's Rest's next four, Deima Surface Bridge, Rydberg Reactor, SynTek Residential and Sewer Junction B5, traced from the real maps. The newest work is in the last section; the early sections below are kept as history.**

## Done

- `tools/basemap.py`: writes a blank map from scratch. Covers MapInfo v39, DocumentHeader with Swarm mod and Swarm campaign dependencies, the t3 terrain layers and the painted pathing layer. Adapted from GameNight/Saboteur.
- `tools/shipkit.py`: procedural hull textures and an M3 writer with emissive layers and no-shadow ceilings. A smoke test passed (`dist/texsheet.png`).
- `tools/level.py`: the derelict deck on a 96x80 map, with 18 rooms and corridors, pillars, props, 47 flickering lamps, vents, eggs, biomass and ammo crates. Wall, cap and ceiling meshes are chunked 24x24. Terrain masks are included. The connectivity check passed (`dist/layout.png`).
- `tools/alien.py`: the **ripper**, an original animated alien mesh (15-bone rig; Stand, Walk, Attack and Death tracks; emissive bioluminescent spots), written as a native M3 after Saboteur's Tunnel Run miners. `py tools/alien.py` also writes a CPU preview sheet to `dist/ripper-preview.png`. In game it stalks in and lunges with its scythes; it spawns in labs, hives and hordes, and Ctrl + J spawns one at the cursor.
- `tools/fx.py`: additive effect meshes (tracer, laser, tesla arc, flash, burst, flame, ring).
- `tools/catalog.py`: Unit, Actor, Model and Light catalogs plus font styles. Covers the marine, 9 aliens, eggs, biomass, sentry, pickups, projectiles, light units and death or impact one-shots. Four lighting presets.
- `src/*.galaxy`:
  - State: weapon table from the `asw_weapon_*.txt` scripts.
  - Fx
  - Marine: WASD movement, top-down and third-person cameras, laser sight, flashlight.
  - Weapons: 10 guns, rifle grenade, sentry, medkit, flares.
  - Aliens: AI for all 9 alien types, plus eggs and biomass.
  - Director
  - HUD
  - Main: input and the 16 Hz loop.

## Still to do

1. Write **`build.py`**, after GameNight's `build.py`. It needs to:
   - Call `basemap` with tileset `Korhal`, cliffset `KorhalCliff0`, `level.TEXTURES`, players 1-4 as users and 15 as hostile.
   - Write the terrain and pathing from `level.carve`/`blocked`.
   - Pack the hull meshes as `Base.SC2Assets/Derelict/<chunk>.m3` and the textures through `shipkit.pack_textures`.
   - Place the hull doodads (`AS<chunk>` at z=8) and the props (`ASP_<model>`) in `Objects`, with HeightAbsolute and ForcePlacement flags.
   - Write the fx files and `catalog.build`.
   - Add UI textures `Derelict/UI/white.dds` and `vignette.dds` (`shipkit.dds_rgba`).
   - Generate `src/Level`, containing `AS_LevelInit()`: wall rows into `as_wall`, `AS_Lamp(...)` per light, vents, ammo crates, rooms, eggs and biomass via `AS_SpawnAlien`, and creep in the nest via `CreepModify`.
   - Substitute `@spawnX@`, `@spawnY@` and `@spawnFacing@`.
   - Concatenate the modules in the order State, Level, Fx, Marine, Weapons, Aliens, Director, HUD, Main, with forward declarations for `AS_*`.
   - Emit `MapScript.galaxy` as `include "TriggerLibs/NativeLib"` + code + `void InitMap () { libNtve_InitLib(); AS_Init(); }`.
   - Pack with `pack()`.
2. Check the generated script with `py tools/galaxy_check.py <MapScript> --no-selftest`. Some natives are still unverified: `EventKeyControl`, `ASin`, `RegionEntireMap`, `c_gameSpeedNormal`, `c_keyK`.
3. Write `launch.ps1`: stage the map to `Maps\Test\AlienPOC.SC2Map` and run it through `SC2Switcher_x64.exe`, or in a background client per doodad-royale `tools/playtest/bgclient.ps1`. The SC2 client is shared, so check before launching.
4. Look at it in the client and tune:
   - Lamp radius, which `LightOmni*` scale works.
   - Flashlight orientation.
   - Prop scales.
   - Camera distance, field of view and pitch.
   - Terrain textures.
   - Wall height.

## Hull kit test (2026-10-22)

`py build.py --kit` builds `AlienPOC-Kit`: no hull meshes, prop doodads or painted pathing in the map. `src/Kit.galaxy` builds the deck when the level loads, from 80 deck strings and a kit of 69 pieces (`level.kit_pieces`). `--kit-painted` (`AlienPOC-KitP`) is the same build but keeps the baked painted pathing instead of blocker units. Launch either with `launch.ps1 -Kit` / `-KitPainted`.

Seen in the client:

- **Visuals match the baked deck** (`dist/screens/kit-compare-baked.jpg` against `kit-compare-kit.jpg`). Walls, lamps, caps and props all line up once rotations account for `SetRotation` pointing the model's **-Y** along the forward vector.
- **Load:** 1,921 actors (444 walls, 452 ceiling, 963 caps, 62 props), placed in 1.5 s real time over a few ticks, with no script errors.
- **Size:** the kit packs to 738 KB, against 287 KB for this deck's baked hull. It is a fixed cost, so it only wins from about the third level. Most of it is the 42 ceiling variants.
- **Painted pathing fixed (both builds).** `basemap.painted_pathing` wrote open half-cells as bytes (1, 0). `PathingType` reads only the first byte, so it read the layer back perfectly, but the pathfinder needs both bytes: native movers stalled in open floor. Working layers (doodad-royale, doodad-heist) use (1, 1) open, (0, 0) shut and (128, 128) unpainted. With (1, 1), the baked probe crosses the bay (12.3 units in 3.6 s) and reaches the crew mess by the South Passage (29.4 units in 8.7 s, never inside a wall).
- **`PathingModify` does nothing on this map.** Adding unpathable, removing ground and adding building all left both `PathingType` and the probe unchanged: the probe walked through the hull. The kit therefore shuts the hull with stock `PathingBlocker2x2`/`1x1` units over every collision cell that touches the deck: 487 units, invisible in game, with 0 edge leaks and 0 deck cells shut on readback. The kit probe crosses the bay (12.3 units in 3.6 s) and reaches the mess (28.1 units in 8.3 s, never inside a wall), matching the baked build.

QA keys (both builds): Ctrl+N room tour, Ctrl+P probe, Ctrl+U reset trigger pathing, dump `PathingType` to the `ASPathDump` bank and rerun the probe, Ctrl+B turn props 90°, Ctrl+Y mirror the wall turns. The top-right readout shows the KIT and PROBE lines.

## Mission 2: Cargo Elevator (2026-10-22)

`py build.py` now builds the **Cargo Elevator** mission (`--level deck` keeps the old combat deck). The pieces:

- `tools/cargo.py`: the level, a 128x112 map in 17 areas. Upper level: landing bay, bay corridor, observation gallery (4 windows), security office, security door, crew quarters, north passage, upper concourse, cargo office, elevator lobby. Lower level: freight junction, service shaft, colony concourse, transit station. Between them, the lift: a 12x12 platform in a black void ring, with an entrance bridge (west) and an exit bridge (east). It also holds the mission tables: zones, checkpoints, the door, the panels, the extraction rectangle and the autopilot route. Its layout and connectivity check is `dist/cargo-layout.png`.
- `tools/elevator.py`: textures and meshes for the shaft panels (4 and 2 wide, plain and lamp-lit), the "CARGO LIFT 01" lintel, gate leaves, bridges, the platform with rails, the void, the security door, and the gallery's window wall. Preview: `dist/elevator-textures.png`.
- `src/Mission.galaxy`: objectives, the door override (stand at the console; a swarm comes while you do), window bursts, the vent explosion, boarding (the whole living squad on the platform for 5 s), the ride, the escape, extraction, the debrief, respawns beside teammates, and squad wipes back to checkpoints. **The ride:** the platform never moves. Fifteen shaft columns of four panels each (units whose meshes hang below their origin) scroll upward, about 75 s for 108 units with a ramp at each end. The entrance lintel and gates ride up and out. On the last lap the exit lintel is swapped into slot 3, which stops exactly at the floor. The ride also has shaft lamps sweeping past, red lights circling, alarm beacons, aliens crawling down the walls (model actors) that leap onto the deck as real aliens, buzzers rising from the drop, and a power surge at 38-40 s. The waves scale with squad size.
- `src/Bots.galaxy`: AI marines for empty slots. Each follows the leader's trail, holds a spot on the platform and the transit pad, shoots the nearest visible alien, and medkits itself. Also the `--auto` autopilot and the `AS_Log` QA log (ASAuto bank).
- HUD: an objectives list with a compass bearing to the objective, a centre bar (override %, lift countdown, ride depth), squad health, and the debrief.
- build.py now catches three compile errors galaxy_check misses: duplicate globals, globals used above their declaration, and locals declared after a statement.

**Autopilot run passes (2026-10-22).** `.\launch.ps1 -Auto` plays the mission end to end: **MISSION COMPLETE in 228.3 s** (game time), every stage logged in order, the ride 74.6 s with the exit lintel set and the entrance gone, 2 marine deaths in the whole run, no script errors. Two fixes came out of the first autopilot run, which never finished:

- After its last waypoint the autopilot marine stopped steering, and the swarm shoved it off the transit platform to the south wall (y ≈ 12), so the extraction check never passed. `AS_RouteGoal` now holds the last waypoint.
- Victory killed the leftover aliens before it turned on god mode, so a boomer bursting in that cleanup could still down a marine. God mode now comes first.

Balance from the runs: the first full run (no finale) was over in 187 s, with the AI marines losing about 20 HP in the whole ride. So the ride's climber waves are 40% bigger, and the escape ends in a **45 s transit-car hold**: the first marine on the platform calls the car, a squad-sized swarm comes every 12 s (boomers after 25 s), swarms stop once the car arrives, then everyone boards. The first hold run used the director's growing horde size (30+ a wave) and kept swarming after the car came, and the squad was overrun. Sized to the squad, the third run held (17 to 27 aliens alive, no deaths in the hold) and finished in 232 s. A bot left behind on the lower level caught up once (`AS_BotCatchUp`).

Also added since the first client run: a third shaft panel (cables and a CAUTION MOVING PLATFORM chevron sign), five panels per column so the north wall's top never shows on screen (checked with `tools/preview_lift.py`, a CPU render from the game camera: `dist/lift-preview.png`), rail sparks and a train-rumble loop during the ride, the hive ambience below, and bot goals refreshed every fourth step to keep the 16 Hz loop light.

The status line now logs deaths per marine (`/d`). Next: look at the ride in person (`.\launch.ps1 -QA`, Ctrl+L to skip ahead), then the online test in `TESTING-ONLINE.md`. Not covered by the autopilot: how anything looks, input feel, and frame rate.

## Every level in one map (2026-10-22, in progress)

`py build.py` now builds one map holding every level in `build.py` LEVELS: mission 1 **Distress Beacon** (the deck, now with an objective: hold the reactor console until the power is back, then return to the dropship) and mission 2 **Cargo Elevator**. The terrain is a blank 128x112 deck. The script builds whichever level is being played from its strings with the hull kit, which now also handles the lift void, the lift (no ceiling) and the gallery windows. `src/Campaign.galaxy` reads each marine's `HalcyonDrift` bank (`HalcyonDriftQA` in QA builds) and shows the host a mission menu of the levels any marine has unlocked; it starts the furthest one by itself after 60 s. A won mission is saved to every bank, the level is torn down (kit actors, blockers, mission units, aliens, effects, lamps, crates, creep) and the next one is built. `--start N` skips the menu; `--auto` plays the whole campaign. The baked builds and `--kit`/`--kit-painted` are gone. Map: 2.9 MB.

Known regression: one terrain for every level, so the per-room floor textures and the organic growth of the baked builds are gone (plates with rust everywhere).

First autopilot run (cut short, the client was needed): banks read, Distress Beacon began, its kit built (1,921 actors, 487 blockers, 0 leaks, 2.1 s), the squad reached the reactor console at 13.5 s. Not yet seen: the power restore, the extraction, the teardown, Cargo Elevator built by the kit, the bank write, the menu.

## HUD after Alien Swarm's (2026-10-22)

The HUD is rebuilt to match the original game's. The numbers come from the SDK's HUD code (`asw_hud_master`, `asw_hud_objective`, `asw_hud_minimap`, `asw_hud_use_icon`, `asw_hud_3dmarinenames`) and from the installed game's `scripts/HudLayout.res` and scheme, times 2.5 for SC2's 1200-high UI. The art is drawn from scratch after its sprite sheets; nothing of Valve's is shipped in the map.

- `tools/hudlayout.py`: every position, size, font height and tint. `build.py` writes it into the script as `AS_HUD_*` (tints as colour functions), along with each level's minimap square (`AS_HudMaps`).
- `tools/hudart.py`: 93 power-of-two RGBA textures in `Derelict/UI/`, 752 KB compressed. They cover:
  - the portrait backplate, the 270° health ring (track plus 37 fill frames), four helmet portraits and six class medallions;
  - the bullet, grenade and clip stencils;
  - line-art icons for the ten guns and the sentry, medkit and flare;
  - the squad panel and its bar, the objectives' black bar and tick boxes;
  - the use panel with its key cap and progress bar, the menu and debrief frames, header and buttons;
  - blips, the crosshair, and a minimap per level.
  
  `py tools/hudart.py` writes `dist/hud-sheet.png` and `dist/hud-mockup.png`, a 1920×1200 layout check.
- `src/HUD.galaxy`, by screen area:
  - **Marine, bottom left:** the weapon in hand (white) with the last one (blue) above; the portrait in its ring, the class medallion, and the ring's track pulsing red under 60% health; the weapon name, `%03d` bullets, rifle grenades, five clip pips (or one plus `xN`), and a blinking `- LOW AMMO -` / `- NO AMMO -`; Q/E/X items with counts; the reload bar.
  - **Squad, along the bottom:** a panel per marine with name, class, health bar, ammo ticks, clips and medkits.
  - **Objectives, top left:** shown for 8 s when they change (TAB pins them), with "Objective complete!" typed out under the list.
  - **Use panel, bottom centre:** overrides and countdowns, plus "Infested - use a medkit".
  - **Minimap, bottom right:** a static top-down image of each level, with marine, self, alien (24) and objective blips.
  - **Names under the marines:** dialogs that follow each unit; yellow for you, blue for other players, white for AI, with a teal bar that turns orange under half health and flashes red while infested. They hide while the debrief is up.
  - **Centre:** announcements on a dark band (white with a cyan glow), notices in a black box, and the third-person crosshair.
  - **Debrief:** AS's stats screen, with a header strip and per-column table. Accuracy is capped at 100%, since pellets and piercing shots hit more than once per shot.
- The mission menu (Campaign) uses the same frame, header and buttons.
- Dropped as not in AS: the 1..0 weapon bar, the mission/kills/wave/hints lines, the compass bearing (the minimap marks the objective) and the weapon-name notice on switching.

Seen in the client: two `-Auto` runs, plus QA runs played by hand. Screenshots are in `dist/screens/hud-*.jpg`. Every element renders:
- the unit-anchored name dialogs, glow styles, image swaps and the infestation states;
- the low-ammo blink with empty clip outlines;
- the health ring's white lost-health segment catching up after a moment;
- the second weapon icon after switching;
- "Lift starting" and "Descending - depth N m" in the use panel;
- the mission menu's AS buttons.

Fixes from the client:
- **Ammo digits:** they overlapped the grenade icon, so they're now style height 30.
- **Name dialogs:** they drew over the debrief and now hide under it.
- **Use panel:** with no key cap it now uses the cap's space.
- **HUD in the menu:** it showed behind the mission menu and now appears with the first level.
- **QA status line:** it covered the second gun icon and was moved.
- **Menu buttons:** SC2 slices a button's own image as a border, dropping the edge lines, so the box is now an image under a clear button with a pale hover tint.

QA keys added: Ctrl+H hurts your own marine by 25, Ctrl+R empties the gun's reserve.

**Autopilot stall fixed (both runs had it):** the squad stopped at the Cargo Elevator security door, and then at the lift's exit bridge. The cause is in the all-levels build: the mission marks the door and the shut exit bridge as wall while the hull kit is still laying its blockers over a few ticks. The kit therefore shut those cells with its own 1x1 and 2x2 blockers, and opening the door or the bridge removed only the mission's. `AS_KitUnblock` (`src/Mission.galaxy`) now removes every kit blocker lying wholly inside the rectangle when it opens: 4 at the door, 2 at the bridge. The kit teardown skips the units already removed.

The full `-Auto` campaign now completes:
- Distress Beacon in 44.8 s;
- Cargo Elevator in 226.1 s (ride 74.6 s, transit-car hold, car arrived at 284.5 s);
- CAMPAIGN COMPLETE at 316.4 s, with no script errors.

A side-by-side of the bottom-left HUD against an Alien Swarm capture lines up on ring size and thickness, backplate and ammo bar, weapon name, ammo digits, clip pips, the weapon icon stack and the squad panels. Deliberate differences:
- three item slots instead of AS's one, so the squad starts further right;
- helmet portraits instead of AS's face renders;
- no squad item hotkey numbers (AS shows those only offline).
**Debrief, after AS's stats screen (2026-10-23).** It is now full screen in steel blue, with:
- a top strip: the mission time, DEBRIEF, and the mission and place;
- AS's kills graph: every marine's kills sampled every 2 s (`AS_KillLogPulse`), drawn as step lines in player colours (blue, red, green, yellow), with time along the bottom, the most kills on the right, and the names beside it in the same colours;
- the level's map, framed bottom left;
- the result panel bottom right: a centred MISSION COMPLETE header, the squad table with names in the graph's colours, and the next line;
- a bottom strip naming the next mission, or CAMPAIGN COMPLETE.

Additions after AS:
- **Graph tabs:** FRIENDLY FIRE, KILLS, HEALTH and AMMO, each a logged series.
  - FRIENDLY FIRE is the blast damage a marine has done to squadmates (`as_ffDealt`, counted in Weapons' explosion splash).
  - AMMO is the gun in hand's rounds as a percent of a full load.
- **READY button:** the next mission starts once every player has clicked READY, or after 15 s. The bottom strip counts down ("STARTING IN N") and says how many players it's still waiting for.
- AS's SUMMARY/STATS page switch is not reproduced: this one page carries both.

Checked in the client (`dist/screens/hud-debrief.jpg`, `hud-debrief-tabs.jpg`): the HEALTH tab redrew the graph, and READY started Cargo Elevator at once.

**Portraits are cosmetics (2026-10-23).**
- **Keys:** each marine wears a portrait key `<model>_<skin>` from `tools/hudart.py` PORTRAITS. A model is a renderer (only `marine` so far, in PORTRAIT_MODELS); a skin is a style (armour, stripe, visor glass, trim).
- **Skins:** four defaults, one per slot (`marine_steel`, `olive`, `rust`, `sand`), and two veteran skins to award (`marine_veteran`, `marine_shadow`).
- **Script side:** `build.py` writes `AS_HudPortraitDefault` and `AS_HudPortraitKnown` into the script.
- **Bank:** `src/Campaign.galaxy` reads `cosmetic/portrait` from each marine's bank, and the HUD swaps the portrait when `as_portrait[p]` changes. Nothing awards a skin yet.
- **Extending it:** a new skin is one PORTRAITS line. A non-marine squad is a renderer plus its skins.
- **Client check:** with `cosmetic/portrait = marine_veteran` in the QA bank, the HUD showed the veteran portrait (`dist/screens/hud-portrait-veteran.jpg`).

## Feel pass: movement and shooting (2026-10-23)

A pass on what matters most in Alien Swarm: smooth movement, and shooting that responds at once and shows every hit.

**Shooting**
- **The first round leaves on the click.** It used to wait for the next 1/16 s step, and a quick click let go before that step fired nothing at all (pistols, shotgun, sniper). `AS_MouseDownT` now fires at once (after Doodad Royale's "resolve shots on the input event").
- **Fire intervals are whole steps.** An interval between steps fired on one step, then two, then one, and the gun limped: the rifle 0.07 s is now 0.0625, the autogun 0.1 s is 0.125 with 9 damage (the same 70 a second), and the flamer, pistols, railgun, grenade launcher and sniper rifle are rounded to whole steps too.
- **Rounds keep their own time inside a step.** When the minigun fires two rounds in one step, the later one has already flown for the part of the step it was late by (`as_shotLead`), so a stream reads as evenly spaced tracers instead of pairs. Flame puffs do the same.
- **Hit flash:** a struck alien glows over-bright for two steps (0.12 s) and fades back over 0.15 s. Shock flashes blue-white; a shieldbug turning a round on its plates flashes dim grey. The tint pattern is Doodad Royale's, which was checked in the client there.
- **Stagger,** after AS's flinch behaviour: a hit may stop an alien for 0.22 s and knock it back 0.18. The chance is 10% plus 1.2% per point of damage, up to 70%, and 40% of that for an uber drone. There is at most one stagger per 0.8 s. Shieldbugs, boomers, mortarbugs, harvesters, eggs, biomass and leaping aliens never stagger.
- **Damage numbers:**
  - Floating numbers rise off the alien, shown only to the marine who did the damage.
  - Damage is summed per alien over a quarter second, so a stream shows its total.
  - Colours: bullets white, fire orange, blasts yellow, shock pale blue, armour grey. The killing blow is larger and red.
  - N toggles them; they're on by default.

**Movement**
- **Corners:** a body caught square on a door frame or pillar corner used to stop dead. Neither axis slide moved it, but the old code still accepted the slide along the free axis, which went nowhere. Now an axis slide counts only if it moves. Otherwise the step turns 30° and then 60° either way, shortened by the cosine, and the marine rounds the corner.

**Cost per step (lag)**
- **`AS_RayWall` walks the grid cell by cell (DDA).** That is one test per cell crossed; the old 0.2 march with a bisection took about five, and it could step over the point where two wall cells meet diagonally. The laser sight, every trace, line of sight and the camera boom use it.
- **Positions are read once per step:** `AS_AlienCache` reads every alien's position into `as_aX`/`as_aY`. Traces, aim assist, flame puffs (64 puffs × 96 aliens, three engine reads each), lobbed shells and the marines' biomass collision use the cache. The biomass test is skipped when no growth stands.
- **Effects:** sprite effects (flash, burst, flame, ring) no longer get a rotation message. Each message cost six number-to-string conversions, and every live effect resent one each step: up to about 300 a step in heavy fire. Streaks build theirs once and resend the cached string.
- **The HUD** touches the health ring's tint, the grenade count, the reload marker, the status line and the red hurt edge only when they change. The hurt edge was set every step. The muzzle light is shown or hidden only when its state changes.

**Checked:**
- **Build and static checks:** `build.py` passes its compile assertions. `galaxy_check` shows no new error kinds against the previous build; only its known local-variable false positives remain.
- **Autopilot run** (`-Auto`, run `a521f736256f`): CAMPAIGN COMPLETE at 316.4 s, against 316.4 s before.
  - Distress Beacon took 45.3 s and Cargo Elevator 225.8 s.
  - The ride was 74.6 s, and the kit reported 0 leaks.
  - No script errors were logged, so stagger, hit flash, the position cache and the new fire rates run without breaking anything.

**Demo run in the client** (`-Demo`):
- **Damage numbers first drew nothing.** `libNtve_gf_HideGameUI` hides the text-tag layer along with the rest of the game UI. `AS_Init` now turns it back on with `UISetFrameVisible(..., c_syncFrameTypeTextTag, true)`, as Doodad Royale does. A QA log had confirmed the numbers were being created.
- **Sizes:** the numbers were too small at the top-down distance, so they are now 22 (blasts 26, kills 28) with a shadow.
- **Seen working:** sums of autogun and minigun hits (27, 35, 28) and red killing blows (9, 18) rising off the drones.
- **The demo's AI marines now hold fire** (`AS_BotPulse`), so the drones are player 1's to shoot. They were killing most of them first, and those kills show no numbers.

**QA run by hand in the client** (`-Start 0`, real mouse clicks):
- **A single quick click fired:** the clip went from 98 to 97. A quick click like that is the case that could fire nothing before.
- **The hit flash:** a shieldbug under fire glows hot orange-white, where its body is normally dark. The flash now holds for two steps (0.12 s) and fades over 0.15 s. One step is about 45 ms at Faster, too brief to read, and still frames could not catch it.
- **Seen working:** a 55 number on an uber drone, and the rifle stream reading as evenly spaced tracers.

**Camera:**
- **The problem:** walking by hand (held keys do work now), the marine ran about a unit ahead of the screen centre and the camera caught up only when it stopped. That was SC2's default follow smoothing, built for RTS panning.
- **The fix:** `tools/catalog.py` now writes `CameraData.xml` with Doodad Royale's values: `TargetSmooth` 0.08 s, `FollowScrollLimit` 1000, and no screen-edge scrolling.
- **Checked:** with it, the marine stays at the screen centre while the deck moves past.
- **How it feels by hand.** Try `.\launch.ps1 -QA`: Ctrl+1 spawns drones, N toggles the numbers.

## Visual overhaul after Alien Swarm (2026-10-23)

The deck now looks like Alien Swarm's interiors instead of dark SC2 terrain under black slabs. Reference: the installed game's VPK textures (greymetalfloor, metalfloor3, metalgrate011a, swarm_metalfloorbrown, cleanwall1, colonywall1, techwall4, the crate and barrel skins), read for palette and pattern only, plus the four screenshots in the repo root. Everything is drawn from scratch with NumPy.

- **Floors (`tools/deckart.py`):** plating per room kind laid by the kit (`AS_KitFloors`, `tools/level.py floor_pieces`): 4x4 pieces in four patterns, then 2x2, then single cells, uv'd from world position so they join without seams. Bays get brown-grey plates with hatches, halls diamond tread with grilles and glowing grates, ducts orange-lit grates, the mess pale tiles, the reactor dark blue plates with cyan running lights, cargo rooms the brown deck with orange bands, labs white tiles, the hive plating grown over with alien skin. The lift keeps its own platform.
- **Walls (`tools/wallart.py`):** pale painted bays in courses (dark top rail, riveted panels, a waist band in beige, orange or hazard stripes, a dark kick plate) with fixtures that glow: lamp boxes, green screens, red alarm lamps and DANGER plates, vents, coloured pipe runs. Each wall piece now carries a pale lip along its top edge and a multiplied contact shadow at its foot. Struts with hazard-striped feet stand proud of long walls every four units. The hull tops are blue-grey plating instead of black.
- **Decals:** hazard paint across every doorway, grime, scorches and goo (multiplied), warning signs, and floor paint: each big room's stencilled name ("DOCKING BAY 09"), a landing ring under the dropship and yellow guide lines round the bays and cargo rooms. Stock flat decals the plating would hide are dropped (blood splats become goo decals).
- **Props (`tools/propart.py`):** green SynTek supply crates, grey metal crates and yellow toxic barrels replace the stock crates; barrels and crate stacks sit in room corners.
- **Lighting (`tools/catalog.py`, `src/Fx.galaxy`):** room lamps are the stock large omni light of their colour scaled 1.7 (2.2 for the big kinds), which throws AS-sized pools. The lamp boxes of lit wall bays facing the camera carry a small white light of their own (`AS_KitWallLamp`, at most 40 a level). The presets have a cooler, brighter ambient, bloom (`HDRBloomThreshold`) and a stronger emissive multiplier.
- **Camera:** pitch 60, FOV 48, distance 18 (was 40 and 24): closer and with more perspective, so wall faces read as in AS. The wheel still zooms 12 to 40.

Found in the client:
- **`Colorize=1` tints the whole picture one hue** (red at hue 0); it is a colourise, not a grade. Off.
- **An M3 point light written by the map (`LITE`, bone 0 raised) drew nothing,** whatever its intensity; stock `LightOmni*Large` scaled with `SetScale` is what lights the pools.
- **A specular layer on the kit's materials (a grey map from the diffuse, specularity 12-24, multiplier up to 4) changed nothing visible,** so it was dropped.
- **An alpha-blended quad (blend mode 1, RGBA DDS, colour channel RGBA) drew its clear parts opaque.** Floor paint is therefore two layers the client does draw: one multiplied (tints the deck where painted) and one added (lifts it).

Kit totals for Distress Beacon: 444 walls, 467 floor pieces, 333 decals and props, 2,711 actors, built in 2.6 s; pathing unchanged (0 leaks). Map: 6.3 MB. The hull terrain is all dark plates now (the plating covers every deck cell), and the derelict ambient was lowered so the lamp pools stand out.

Checked: an `-Auto` campaign run still completes (Distress Beacon 52.3 s, Cargo Elevator 225.6 s, CAMPAIGN COMPLETE), with no script errors. Screenshots: `dist/screens/overhaul-*.jpg`, with `overhaul-compare.jpg` setting two Alien Swarm shots beside the before and after. Texture previews: `dist/deck-art.png`, `dist/wall-art.png`.

**Second pass (same day).** More of Alien Swarm's dressing, each checked in the client unless noted:
- **Bulkhead frames** (`propart.py` KPDoor1-12) at every corridor-to-room doorway: chevron lintel, posts with a green status light.
- **Backlit passage signs** ("← SOUTH PASSAGE", after AS's reactorcontrolwitharrow) beside doors on the walls the camera faces.
- **Loose cables** across working rooms (multiplied decals, thick rubber with a duller core).
- **Lockers** along crew rooms' walls and **glowing consoles** in labs, offices, bays, cargo rooms and the reactor.
- **The ammo crate** is AS's ammo case (olive-grey, AMMO stencil, glowing green lid strip) instead of SC2's plasma-rounds pickup.
- **The reactor** has a glowing cyan core drum on its housing (KPReactor, in the deck's PROPS; `build.py` lays any `KP*` prop as a kit piece).
- **Light shafts** under the steady white and cold lamps: eight added quads per lamp, after asw_vol_light.
- **Lab floors** carry a faint cyan glow in their seams (first try was far too bright: a Tron grid).
- **Team colours**: the squad wears the HUD's blue, red, green and yellow; the swarm is orange-brown (`PlayerSetColorIndex` in `AS_Init`), nearer AS's drones.
- **Hull tops** darker again, so the deck stands out as in AS; two more lamps in Cargo Elevator's freight junction.
- **Viewports** onto space (the window bay, now with stars) in the docking bay's and cargo hold's north walls (`level.py VIEWPORTS`, look only; the gallery's `WINDOWS` still give way in mission 2).
- **Sputtering lamps spit sparks** now and then as they catch (`AS_LampSparks`).
- **Warm lamps** in both bays (yellow large lights, with light shafts), for AS's amber hangar look; cold light stays in the labs and reactor.
- **Corridors**: dashed cyan running lights along the walls (KDRun, added), brighter tread plate, and a steady lamp wherever a stretch had none within five units (`level.py corridor_lamps`; lamp cap 96).
- **Soft contact shadows** under crates, barrels, lockers, consoles and the ammo case.
- **Pipe runs** (yellow and grey, KPPipes) high along the corridors' camera-facing walls.
- **Painted arrows** down the middle of each corridor (KNArrow); cables thinned to one per 240 open cells.
- **Alien blood** splats carry an added yellow-green glow layer (ASFxSplatGlow1/2, laid and faded with each splat), so the goo reads as vividly as AS's.
- **EMERGENCY lighting** (the swarm alarm) is a red cast that keeps the room readable instead of flooding it red; the alarm lamps carry the rest.
- **Lab accents** are glowing blue grates.
- **Hull caps reach five cells** from the deck (was three), so the bare terrain stays out of view: 18 more cap actors, the kit builds in 3.2 s instead of 2.6 (`AS_KitBuildRest` yields every 4 rows there now).
- **Blasts leave scorch marks** (ASFxScorch, multiplied, in the splat pool; `AS_Scorch` from `AS_Explode`). Seen in the client: a rifle grenade left a sooty star burst on the bay floor (`dist/screens/overhaul-scorch.jpg`).
- **A soft dark vignette** frames the view (the HUD's vignette art in black at half opacity, under every other dialog).
- **Ceilings** (third-person view) in the pale panel style with vents.

Totals after the second pass: Distress Beacon's kit is 2,918 actors and Cargo Elevator's 3,104, each built in 3.2 s with 0 pathing leaks; the map is 7.3 MB. Autopilot campaign runs after the second pass: 44.3/238.6 s, 44.8/225.6 s, 45.0/237.8 s, 44.8/229.6 s, 44.3/225.6 s on the final build (Distress Beacon/Cargo Elevator), CAMPAIGN COMPLETE each time, no script errors.

## Landing Bay, the full first-mission experience (2026-10-23)

The deck level (Distress Beacon) is replaced by Alien Swarm's first mission, **Landing Bay** (`asi-jac1-landingbay_01`), and everything from entering the game to finishing it now follows the original. Sources: the SDK in `../AlienSwarm/src/game` and the installed game's `swarm/` data (maps, scripts, resource text), read for rules and numbers only. Nothing of Valve's is shipped; mails, bios and the commander's lines are written anew.

- **Level (`tools/landingbay.py`, 64x144):** traced from the briefing overview in the VPK and the BSP's entities: dock, freight yard, security gate (two locked doors, hack either panel), storage and pump rooms, supply room with both welders, tank room behind doors welded 8/10, north stair, junction (booth welded shut, sentry case, PDA), concourse and flight control. 37 areas, 13 doors, 46 spawners, 20 triggers, 3 PDAs, the dropship lifting off at the start, and the escape lift as the exit zone.
- **Spawning (`src/Objects.galaxy`, `src/Director.galaxy`):** Landing Bay has no AI director and no wave announcements in the original, so neither does this: every alien comes from the map's own spawners (count, live cap, interval ±25%, spawn only when no marine is within 740 units), started by its triggers, plus three sleeping drones. That includes the original's "behind you" spawners and random picks. The director (wanderers, hordes, intensity) runs only with **Onslaught** on, with AS's timings and distances.
- **Briefing (`src/Briefing.galaxy`):** MISSION PREP with mission arrows, map, objectives, Tech required, the five difficulties, Onslaught, and four squad rows (portrait, class, player level, promotion, three slots, ready, ADD AI). The roster has the 8 marines with AS's skills and bios; the item screen has all 21 regular and 17 extra items with class locks, unlock levels and stats. Loadouts are remembered per marine.
- **Weapons and items (`src/State.galaxy`, `src/Weapons.galaxy`):** AS's stats, skill formulas, alt fire, fast reload, every extra (sentries x4, heal beacon, damage amp, tesla coil, mines, welder, flares, night vision, electric armour, hornet barrage, smart bomb, ...).
- **Doors and hacking (`src/Doors.galaxy`, `src/Use.galaxy`, `src/HackUI.galaxy`):** door health and bashing, welding and cutting with the hand welder (hold 1), the wire puzzle at panels (2x5, two wires; fast-hack window; "ACCESS ATTEMPT LOGGED"), and the tumbler terminal followed by the download (15 s, twice as fast for a tech). Only techs can hack; anyone else orders the squad's AI tech to do it.
- **Death rules (`src/Mission.galaxy`, `src/Marine.galaxy`, `src/Campaign.galaxy`):** no respawns or checkpoints, as in AS. A dead marine drops their guns with ammo; the player switches to another of their marines (F1-F4) or spectates. If the last tech dies before the hack, the mission restarts in place within its first 30 s ("RESTARTING MISSION - No live Tech Marine"); after that a 5.9 s countdown ends in MISSION FAILED, as AS's `CheckTechFailure` does. A squad wipe shows MISSION FAILED with AS's fail advice, and the host restarts from the briefing.
- **Difficulty:** Easy/Normal/Hard/Insane/Brutal with AS's mission difficulty, alien health, damage and speed scaling, marine speed, infestation damage, finite spawners on Easy, and skill-gated spawners.
- **Hints (`src/Hints.galaxy`):** AS's 26 lessons (movement, reload, use, weld, hack, switch marines, ...) with its shown-count limits, saved per player.
- **Progression (`src/Progress.galaxy`):** the 27-level XP table, promotions with medals, XP breakdown in the debrief, item unlocks by level, 48 achievements and per-mission medals, best times; all saved to each player's bank.

**Testing.** `build.py` now runs two static checks and refuses to pack on findings, because the client stops at the first error: `tools/galaxy_types.py` (types: text + string, int * fixed, bool conditions, argument types, bulk copies; 0 findings on the last committed build, and it catches every injected mistake tried) and `tools/galaxy_bounds.py` (constant array indexes past their size). QA builds play every sound the script names silently at start (`AS_SoundProbe`), so the client logs any unknown ID in one run; the reference sound catalog lists IDs from mods this map doesn't load. The `-Auto` run now drives the briefing through the same actions the buttons run (mission arrows, every difficulty, Onslaught, roster and bios, every item page, an equip, achievements), takes Crash, reads a PDA's mail, and solves the wire panel and the tumbler terminal through the tiles and switches a player clicks. `--wipe` adds the death rules first.

Checked in the client (autopilot, no script errors): Landing Bay complete in 105.1 s on Normal with no deaths (panel fast-hacked in 5 s, tumblers in 3 s, download 7.5 s), XP and achievements banked, then Cargo Elevator and CAMPAIGN COMPLETE. With `--wipe`: the tech killed at 15 s gave "last tech down" and a restart 6.5 s later; the whole squad killed gave "squad wiped", MISSION FAILED 0.6 s later (no XP) and a relaunch; the third try completed in 107.1 s. Bugs found this way and fixed: a text + string promotion message and an int * fixed in reload (compile), the room-tour arrays too small for Landing Bay (load), two sound IDs from unloaded mods, the bay never entering its escape stage, and a solved wire panel firing "Access Granted" every tick.

**Second pass (same day): every difficulty, every screen, the original's spawners.**

- **Spawners checked against the original** (`tools/lbcheck_spawners.py <ents.txt>`): all 47 live asw_spawners of asi-jac1-landingbay_01 match a row of `landingbay.py` (alien, NumAliens, MaxLiveAliens, interval, infinite, skill gates, spawn rule). 13 more in the map wait for an input nothing sends them (SpawnerState 1), so they never spawn in the original either and are left out. One Insane-only ranger at flight control was missing and is added.
- **No wave popups:** Landing Bay has no AI director in the original, so aliens come only from its spawners and triggers (including the ones placed behind the squad). With Onslaught on, the director's hordes arrive with a sound cue only, as `Spawner.Horde` does.
- **Screens, without screen access:** `-Auto` builds list every label, image and button as it is made and, at set moments, write each visible one (place, size, style, image, tint, text) to the ASUi bank (`src/HUD.galaxy AS_UiDump`). `tools/uishots.py` draws those moments with the map's own UI art and font sizes and checks for overlapping labels, text too wide for its box, and controls outside their dialog. Pictures: `dist/screens/ui/` (briefing, roster, items, items_offhand, achievements, hud, hint1-2, mail, wire, tumblers, download, fullmap, help, debrief_0). They are an approximation (Arial, not Eurostile; level map art and unit-following name tags are not placed), not the client's renderer.
- **Input:** the key and mouse triggers now call `AS_KeyDown/KeyUp/MouseDown/MouseUp/Wheel`, and the autopilot presses every binding through them once (fire, R, Q, wheel, melee, alt fire, roll, drop and pick up, offhand, Tab, H, C, N, X, V, W, F1-F4) and logs what each changed.
- **Autopilot switches:** `--skill 1..5`, `--onslaught`, `--marine <name>`, `--wipe`. It logs every hint shown, the debrief's XP lines, medals, rank and a promotion at level 27.

Found and fixed this way: F1-F4 used player slots, which trade marines when you switch, so F1 never returned you to your first marine; a picked-up gun replaced the one in hand even with a slot empty; picking a marine an AI row held failed and left the roster open over the briefing (now the two rows trade marines, labelled AI SQUAD); the briefing's bio header ran into the skill list; the commander's subtitle and hints stayed on screen over the debrief; hints popped up over the hacking screens; a marine pressed into a wall by the swarm could never move again; the debrief's difficulty bonus was blank on Normal and its header repeated the place; sentry kills were credited to the gun in hand; and the last tech dying sent the squad to MISSION FAILED after 30 s. That restart-anytime rule was later corrected: the SDK restarts in place only within the first 30 s and otherwise fails the mission after a 5.9 s countdown (`asw_gamerules.cpp` CheckTechFailure, AS-PARITY.md Phase 3); a restart still restores the briefing loadouts.

Client runs (autopilot, no script errors): Normal/Crash 106-109 s, Easy+Onslaught 108.6 s (two hordes), Hard 118.8 s, Insane as Sarge 120.4 s (one tech-down retry), Brutal/Crash 116.1 s, Normal/Wildcat with the AI tech hacking 123.3 s.

Still only seen through those pictures: nobody has looked at the live screens, since screen access was declined. They need a look by hand (`.\launch.ps1 -QA`).

## Combat feel pass (2026-10-23)

Played by hand, the missions felt easy and like walking around. Alien health and gun damage already matched AS's (`asw_drone_health` 40; the rifle's `base_damage` 5 plus 1 a point of Accuracy), so the cause was elsewhere:

- **Camera (`src/Marine.galaxy`):** distance 18 → **8**. AS's camera sits 412 units out at FOV 75 (about 60° tall) and frames about 6 cells top to bottom; at 18 and FOV 48 ours framed about 16, so every alien, gib and hit flash was drawn at roughly 40% of AS's size, and swarms were seen and shot from far off. **Z** steps the distance 8 / 11 / 15 (listed in the H help). `tools/preview_lift.py` uses the new numbers.
- **Aliens (`tools/catalog.py` SIZE):** drawn 15-65% past AS's sizes (drone 1.25 → 1.45, uber 1.6, parasite 1.05, shieldbug 0.72, boomer 2.6, buzzer 0.42 → 0.7, ranger 1.0, mortarbug 0.9, harvester 0.75, ripper 0.9); collision radii are unchanged. The death, fire, gib and shaft-climber models use the same table. The **drone is now the HotS raptor** (Swarm campaign mod), spikier and nearer AS's drone; it has no torn, acid or burning death of its own, so it falls with its plain one under the gib and fire effects. QA and `-Auto` builds log whether the borrowed models are loaded (`AS_ModelProbe`): HotSRaptor, HotSRaptorDeath and PrimalZergling all ok.
- **AI squad (`src/Bots.galaxy`):** the bots locked on at 11 cells, never missed and never ran dry, so they cleared rooms before the player got there. They now follow AS's AI rules, eased a little after test runs:
  - sight 8 cells following, 10 holding (AS: 6.6 and 9.6);
  - 4-14° aim error on each new target (AS: 5-20), closing x0.9 a 0.1 s think while firing, and none inside 1.5 cells;
  - a 0.1-0.25 s turn before the first shot, none inside 2.5 cells;
  - finite ammo: a dry bot scrounges one clip every 20 s.
  
  The autopilot's own marine is exempt.
- **Story director (`src/Director.galaxy`):** with Onslaught off it now runs on Normal and up (never Easy):
  - wanderers every 8-11 s, down to 2.5 s, none while 12 drones are awake;
  - hordes of 5-9 every 75-100 s (the first 60-90 s in), held back while 15 drones are awake;
  - relax 30-45 s.
  
  `as_director` (set before but never read) is now its switch: on at each level start, off for the lift ride, the transit-car hold, failure and victory, and off for the whole of Cargo Elevator, whose set pieces bring their own swarms. The spawn-spot search went from 24 tries to 80; 24 found no spot three times running in narrow Landing Bay. Wanderers and hordes are logged.

Autopilot runs (Normal, Crash, no script errors; the autopilot marine has god mode, so every death is an AI marine):

| Run | Settings | Landing Bay | Cargo Elevator | AI deaths |
|---|---|---|---|---|
| 1 | AS's exact bot numbers | 109.6 s, 0 hordes | 257.1 s | all 3 in the lift lobby within 8 s (drones and an uber drone) |
| 2 | sight 8/10, aim error 4-14° | 110.1 s, 5 wanderers, no horde spot | 248.1 s | 1, during the ride |
| 3 | 80-try spawn search | 112.3 s, 6 wanderers, a horde of 8 at 68 s | 253.8 s | all 3 in the lobby again |
| 4 | point-blank aim | 107.1 s, 4 wanderers, hordes held (15-23 awake) | 246.1 s | 1 in Landing Bay, 3 spread over Cargo Elevator; the bots took 55 and 53 kills to the autopilot's 151 |

The original tuning lost about 2 marines a run.

Not checked: how any of it looks or feels, since nobody has looked at the screen. In particular: the new camera framing in every room and on the lift ride, the raptor's animations and its facing, and whether the bigger models clip walls in corridors.

## Alien Swarm side by side: camera, lift ride, kills (2026-10-23)

The Steam game's first two missions were played at its high effects setting, with screenshots, screen clips, demos and the maps' entity data captured. The notes are in `AS-REFERENCE.md` and the captures in `dist/asref/` (the clips are git-ignored).

- **Framing:** the top-down camera moves in from 8 to **6**. AS shows about 8.5 cells across; 8 showed 11.5 (measured against the lift's platform in both games). Z now steps 6 / 8.5 / 12.
- **The camera leans toward the cursor**, as AS's does (`asw_in_camera.cpp CalculateCameraShift`): the cursor's screen offset times 300 units across, 200 north and 380 south. The camera follows an invisible anchor unit (`ASFxAnchor`, a black additive quad) placed at the marine plus the lean. The cursor is kept as a screen offset, so the aim still lands under it as the view slides. Spectating does not lean.
- **The lift ride** is framed like AS's, with the whole platform and the shaft walls round it on screen: distance 13, centred 2 cells north of the marine (`AS_RideFrame`; `py tools/preview_lift.py` renders it). It also follows AS's sequence:
  - Sodium floodlights over the waiting platform go out as the walls start and come back at the bottom.
  - A dust burst at the start; steam jets off the shaft walls; three exit lamps chase toward the way out at the bottom.
  - The ride takes about 100 s (AS: 106 s at 25 units a second; it was 75 s), with the wave schedule stretched to match.
- **Kills** add a lingering lime-green acid flare over a wider haze (`AS_AcidCloud`); **a marine hit** throws a red spray of streaks away from the claw.

**Checked in a fresh client** (autopilot, Normal, Crash; no `ScriptError.txt` for the session):
- Landing Bay complete in 108.6 s.
- The ride lasted **100.3 s**, with the exit lintel set and the entrance gone.
- Cargo Elevator complete in 279.3 s, then CAMPAIGN COMPLETE.
- All three AI marines died during the ride, between its 40th and 60th second (the surge and the waves after it). Earlier tuning runs lost one to three, so this is the top of that range. Watch for it in the next runs.

Not checked: how any of it looks. Nobody has looked at the client's screen: the lean, the 6-distance framing, the ride's framing and lights, and the acid flares.

**Second round** (same day; details in `AS-REFERENCE.md`):
- The lift's void ring is the shaft's dim brown haze instead of black.
- The shaft panels carry red-flanged pipes, and their lamps glow orange-red.
- Brown haze drifts over the deck during the ride.
- AS's slow-motion beat comes when the first climber lands (Slower for 0.9 game seconds, logged).
- Landing Bay opens outdoors: snow from the dock to the freight yard, cold blue, red and pink light on the dock, white floods over the yard.
- "- RELOADING -" in red over the portrait.

The build passes the static checks. Its autopilot run in a fresh client (no script errors) finished Landing Bay in 108.1 s. The ride took 100.3 s; the slow motion went from speed 2 to 0 and back to 2 a game second later, so SC2 honours it. Cargo Elevator finished in 272.6 s, then CAMPAIGN COMPLETE. Three AI marines died, spread out this time: one in Landing Bay, one on the ride, one in the escape.

**Third round: Landing Bay's outdoor deck is a platform over the night, not a hallway.** In AS you stand on railed catwalks over a drop, with blue haze, trusses and lamps far below.
- **The drop:** the hull from the dock to the freight yard (`OUTDOORS`) is now open night, `o` in the deck rows and `AS_OPEN` in the kit. It gets no walls and no hull tops. A painted drop is laid there (`tools/elevator.py tex_open`, emissive): AS's exterior fog blue, girders and a lattice tower far below, lamps down there.
- **Railings:** yellow railings (`KRail`) run along every deck edge that meets it.
- **Buildings:** hull blocks next to it (the inner perimeter, the yard's crate stack) show plain walls.
- **Pathing:** collision is unchanged.
- **Check it:** `py tools/preview_dock.py` renders it from the game camera (`dist/dock-preview.png`). The depth is painted, since the drop can't sit lower than the deck: both levels share one terrain.

Checked in a fresh client (autopilot, no script errors):
- Landing Bay's kit built 3,411 actors, with 126 railings and 517 blockers. Leaks/shut 0/0, so the outdoor deck's pathing is sound.
- Landing Bay complete in 106.6 s; the ride 100.3 s; Cargo Elevator complete in 275.3 s, then CAMPAIGN COMPLETE.
- The AI squad was lost again, all three in Cargo Elevator.

Not seen on screen yet: the drop and railings.

## Visual pass: held guns, AS's lens, the colony's look (2026-10-23)

Three asks: make the map look like Alien Swarm's, give the marines real guns that aim with a smooth AS laser sight, and match AS's zoom with AI marines that don't shoot what the player can't see yet. Nobody looked at the client's screen this pass either: looks were judged with a new CPU render of the kit as it is laid out (`py tools/preview_scene.py <level> x,y,aim ...`), and every build was played through by the autopilot.

**The marines (`tools/marine.py`):**
- An original armoured trooper replaces SC2's stock marine, which carried its own rifle across its chest whatever the weapon. Pale armour, shoulder pads, a backpack with antenna, a helmet with glowing eye slits and crown lamps; about 0.88 tall, 7% of the screen like AS's.
- Suits are muted as AS's are (its Tech's steel blue, Heavy's brown-red, Sarge's camo green, Jaeger's khaki, read from its textures for reference).
- One model per weapon family (15: rifle, prototype rifle, autogun, shotgun, vindicator, dual pistols, minigun, flamer, sniper, railgun, tesla, heal gun, chainsaw, grenade launcher, and a carried case for deployables). The gun is held at the hip in both hands along the aim. The script swaps the model when the gun in hand changes (`ModelSwap`, `AS_GunShow`) and tints each squad member's suit their HUD colour.
- Every round, tracer, flame gob, grenade, tesla arc and heal beam now leaves the muzzle of the gun in hand (`AS_Muzzle`; the muzzle table is written from the models by build.py). Dual pistols alternate hands. Spent casings flick out to the right.
- A round flies several cells a step, more than its tracer streak is long, so before this the first you ever saw of it was well out in front of the marine whatever the muzzle. A round's first frame is now a line from the muzzle to it, as AS's tracers leave the barrel.
- The flamer's jet leaves the nozzle blue-white hot and turns to orange fire (the user's AS flamer screenshot).
- Reloading shows: the gun dips and turns in toward the body as the clip goes in, upper body only so the legs keep running, stretched to the reload's length.
- No laser on a chainsaw or a carried case; a small red flare glows at the emitter where the beam leaves the gun.
- The laser ends where it should: on a bulkhead at gun height, on an alien at its body, and only under a player's cursor does it come down to the deck; the end height eases, so the beam's slope never snaps.
- Weapons lying on the deck (dropped by a fallen marine, or waiting in a supply room) are the gun itself, the same parts the marines hold (`tools/marine.py gun_only`), not SC2's plasma-gun pickup, with a faint glow under them so they read on a dark deck, as AS highlights pickups.
- Animations: stand, run forward, back-pedal and side-steps picked from the run's angle to the aim (the legs go where the marine moves, the gun stays on the aim), the rifle-butt swing, and a death where the body goes over and stays (`AS_MarineCorpse`) instead of SC2's marine death.
- Second model pass: layered angular pauldrons instead of round pads, a power pack with cooling fins and a status lamp, a crested helmet with ear vents.
- The models carry SC2 attachment points (Ref_Center for the name tags, Ref_Weapon at the muzzle, and the rest).
- `dist/marine-preview.png`, `dist/marine-ingame.png`.

**The laser sight (`tools/fx.py`, `AS_Attachments`):** a hot thin core in a soft red halo, from the muzzle down to the deck under the cursor, stopped by a wall or the first alien in line, with a glowing dot where it lands. It and the marine turn by unit facing over a step instead of an actor rotation each step, so the engine draws the turn smoothly; the laser stays on the barrel. Pink motes light up along it, as dust does in AS's laser.

**Zoom:** SC2's field of view is the vertical one (measured on `dist/screens/overhaul-docking-bay.jpg`, taken at distance 18 and FOV 48: 41.7 px a cell at the screen's centre, where a vertical 48 predicts 42.2 and a horizontal one 67.6), so the camera is now AS's own lens: pitch 60, 60 degrees tall, 5.1 cells out (412 units at AS's scale). The lean and the Z presets (5.1 / 7.5 / 10.5) are rescaled; the lift ride is framed at 11.5 on the marine so the whole platform shows. Check: our 0.88-tall marine now fills 7.5% of the screen's height, AS's 72-unit marine at 412 units 7.6%.

**AI marines:** a pre-existing bug surfaced in run 20: once the leader was aboard the lift, the bots walked straight at their spot on the platform, and one that started just south of the bridge pinned itself against the drop's corner for good (the lift waits for the whole squad, so the run stalled; a player's AI squad could hit it too). A bot now takes the leader's trail when its spot isn't in clear line for its whole body (`AS_BotWay`); the same for the transit platform.

They only engage aliens on some player's screen (`AS_OnScreen`, the camera's footprint on the deck), or within 3.5 cells of themselves. The autopilot logs how often a bot held fire (`offscreen=`).

**The map:**
- Floors after AS's landing bay (its VPK textures were read for reference only): pale concrete slabs and bright galvanised grating mixed through the halls, concrete and diamond plate in the bays, and every floor given a photographic finish (grain, specks, oil stains, grime in the seams). Small floor pieces now mix the second plating too.
- Walls weathered with grime runs; the plain bays are AS's pale panels each outlined in a worn yellow frame (lb-04), the pipe bays carry a fat red flanged riser; the wall struts are AS's yellow perforated girders; the pipe runs are yellow and red.
- Hull tops are near-black, as everything outside AS's playable space is; blocks standing in rooms are machinery seen from above (plating, vents, a red pipe, a hazard rim).
- Solid crates and barrels along the walls of the big rooms, kept clear of doorways and of every point the mission uses (pathing still 0 leaks). Hatches ringed with hazard chevrons; blood pools where the crew fell; powdery snow on the outdoor deck.
- Dust motes drifting on screen, steam off the glowing grates and out of the wall pipe runs (a soft smoke sprite, not the ringed burst), one wall lamp in five failing or sputtering, light shafts under the steady lamps in their colour, and painted hard shadows (girder bands, grating cookies) under about half the room lamps.
- A big yellow perforated girder spans most bays, stores and machine rooms overhead, above the walls, dark between the camera and the deck as the foreground beams of AS's rooms are (lb-05, lb-10). No collision.
- Fat red pipes with yellow flanged joints on saddles along a north or side wall of some bays, stores and machine rooms (solid, like the crates). WATCH YOUR STEP stencils at both ends of the stair and the ramp. The drop off the dock is near-black night with a faint haze and a few distant lights, as AS's is (it was a bright blue lattice). Fan shadows turn slowly on the deck under some room lamps.
- Blasts leave smoke hanging, rising and spreading as it thins.
- Pink neon runs along the dock's edges at the railings' feet; the buildings rising out of the drop show pale concrete outer walls with a lit window here and there; damaged consoles spit sparks now and then.
- The pump room glows sodium orange. Cargo Elevator opens on a dark bay with a grating walkway lit orange from below, as AS's does.
- `dist/screens/visual-pass-compare.png` sets AS's captures beside renders of the same places.

**Autopilot runs (Normal, Crash, no script errors after the first):**

| Run | What was new | Landing Bay | Cargo Elevator | AI deaths |
|---|---|---|---|---|
| 1 | marines, laser, lens, on-screen AI | 97.8 s | 290.6 s | 6; name tags errored (no Ref_Center) |
| 2 | attachment points, 2.5-cell self-defence | complete | complete | 3, all in Cargo Elevator |
| 3 | floor mix | 112.1 s | 277.8 s | 4 |
| 4 | solid clutter, snow, girders, leg gaits | 111.1 s | 271.6 s | 6 (three at once in the flight-control hold) |
| 5 | 3.5-cell self-defence, casings, caps, blood | 109.8 s | 271.6 s | 4 |
| 6 | machinery tops, marine corpses | 111.1 s | 285.3 s | 3 |
| 7 | grating walkway, muted suits, flickering wall lamps, pipe steam, shadow bands | 109.1 s | 275.1 s | 4 |
| 8 | light shafts, turning fans | 109.1 s | 268.1 s | 5 |
| 10 | marine second pass, dark drop | 108.8 s | 275.6 s | 4 |
| 11 | tracers from the barrel, big pipes | 107.6 s | stalled at the door console (autopilot bug, fixed) | 1 |
| 12 | autopilot holds the console | 110.1 s | 287.8 s | 6 |
| 13 | paper litter | 99.8 s | 274.3 s | 3 |
| 14 | reload motion, console sparks | 108.6 s | 274.8 s | 2 |
| 16 | no laser on chainsaw or case, livelier dust | 109.3 s | 279.6 s | 4 |
| 18 | pink dock neon, concrete outer walls | 108.3 s | 275.8 s | 3 |
| 19 | laser end height | 110.3 s | 275.3 s | 5 |
| 20 | no machinery tops in the hive | 110.1 s | stalled boarding the lift (bot bug, fixed) | 3 |
| 21 | bots take the trail to the lift, guns on the deck | 109.6 s | 275.6 s | 3 |
| 22 | AS's yellow-framed pale wall panels | 110.3 s | 280.6 s | 3 |
| 23 | red flanged risers | 109.6 s | 283.8 s | 4 |
| 24 | overhead girders | 108.8 s | 280.3 s | 4 |
| 25 | smoke after blasts | 107.6 s | 279.6 s | 4 |
| 26 | laser emitter flare | 110.6 s | 280.3 s | 5 |
| 27 | a soft glow under guns on the deck | 111.3 s | 283.1 s | 5 |
| 28 | in-client asset and dressing log | 109.6 s | 280.3 s | 5 |

Run 28 checked from inside the client what the renders can't: `models: all 31 marine, gun and effect models ok` (the 15 held-gun marines, 14 guns on the deck, the laser dot, the smoke), the marines switching gun models as they change weapons (`p1 shows the Case`, then `the PRifle`), and the kit laying 743 dressing pieces in Landing Bay and 854 in Cargo Elevator (fans, steam pipes, sparking consoles, steam grates and flickering wall lamps among them), all with no script errors.

A QA build started straight into Landing Bay with a human player 1 left idle at the dock (`build.py --start 0`) ran 340 s with no script errors: the human-only paths (the laser to the cursor's deck point, the on-screen test from a real camera) held, the AI squad held off the story director's wanderers (109 kills, no deaths) and held fire 1,104 times on aliens no one could see yet.

Run 9 never started (the client sat in its menus; restarted). Run 17 raced an edit (built half-way through a change, so a wall mesh was missing: `Could not create actor ASKW9F`); run 18 is the same change built whole. A `-Demo` build fired all fifteen gun families for five minutes with no script errors.

Pictures of this pass (CPU renders of the kit as laid out, approximate lighting): `dist/screens/visual-pass-compare.png` (AS beside the port), `dist/squad-ingame.png`, `dist/marine-preview.png`, `dist/marine-ingame.png`, `dist/scene-landingbay.png`, `dist/scene-cargo.png`, `dist/lift-preview.png`. `py tools/preview_scene.py <level> x,y,aim ...` renders any spot.

Not seen on screen: all of it. In particular check by hand (`.\launch.ps1 -QA`): that the marine models and the laser turn smoothly and together, the suit tints, the gun swaps, the corpses, the new lens, and how the snow, girders, machinery tops and grating walkway look under SC2's lights.

## Parity Phase 0: real heights, packed levels, the extractor and the trigger model (2026-10-24)

The foundations of `AS-PARITY.md`'s plan. Built and checked offline (`py build.py`, `--qa`: type and bounds checks pass); not yet run in the client.

- **Extractor** (`tools/asbsp.py`, `tools/asextract.py`): reads the installed game's seven campaign BSPs and writes numbers only to `tools/asdata/<map>.json`: the walkable floor as 40-unit cells (top height, walkable height, walkable fraction; flooded from nav nodes, starts and spawners, 20-unit steps, 112 by stair props), every gameplay entity with its keys, box and outputs, and the stair and railing props. `py tools/asextract.py [map]` regenerates them.
- **Real floor heights** (`tools/heights.py`): a level opts in with `HEIGHTS = (map, hammer x and y of cell 0, units a cell)`, its trace's fit. Landing Bay does (`asi-jac1-landingbay_01`, -9007, -9513, 79.82); Cargo Elevator stays flat until its rebuild (its layout is invented). Each deck cell takes the median walkable height under it, nearby heights within 16 units merge into flat plateaus (Landing Bay: nine, 7.5 to 10.4 units), 832 is the base height 8.0 and 80 units are one unit up. SC2 stores one height per cell corner, so a step needs slope cells: where two floors of different heights share a corner, the lower cell gives way and becomes a one-cell flight rising to the higher (170 of Landing Bay's 1,993 deck cells). Each slope cell gets a stair piece instead of plating (`tools/level.py` stair_pieces, `AS_KitStairs`): `KStair`, four grating treads with yellow nosing, plate risers and solid sides (106), or the `KRamp1`/`KRamp3` corner plates where flights meet (64), turned uphill and scaled to the cell's rise; a dozen cells rise 1.9 to 2.4 units and are steep. Heights are kept to 1/64, exact in the terrain and in Galaxy's fixed point.
- **Every level has its own part of the map** (`tools/pack.py`): levels are packed into one map and overlap only where no vertex either one's floor needs has two heights (FFT correlation of the constrained-vertex masks, each level tried at a few whole-level lifts). Today: Cargo Elevator at 0,0 and Landing Bay at 114,0 in a 184x144 map (side by side would be 192). Verified: every flat deck cell's four terrain corners sit exactly at its plating height.
- **Galaxy in map coordinates:** positions are map points; the cell tables stay the level's own (`as_ox`, `as_oy` its origin, `AS_CX`/`AS_CY` map to cell). `build.py` moves every position and rectangle it writes to the level's origin (spawn, tour, lamps, vents, crates, rooms, eggs, biomass, creep, props, decals, zones, checkpoints, the route, windows, doors and panels, spawners, triggers, terminals, PDAs, the sentry spot, outdoors, the lift, its door, bridges and shaft columns, sleepers, barrels, pickups, the minimap squares, the start location); the hard-coded points in `src/Mission.galaxy` and the kit's probe add the origin. Kit pieces stand at their cell's height (`as_cz`), walls on the floor they face, tiles merge only over one height; flat dressing, actors and effects use the ground height (`AS_GroundZ`, WorldHeight). `as_floorZ` is gone.
- **Trigger model** (`src/Objects.galaxy`, all optional level data): named events with outputs (`ONS`: `alldead:`/`spawned:<spawner>`, `timer:`, `max:<counter>`, `pass:<path node>`, `arrived:<mover>`, relays), random timers (`TIMERS`), counters (`COUNTERS`), movers along path nodes (`MOVERS`), info messages (`INFO`); new inputs `spawnone`, `enable`/`disable`, `fire`, `count`, `move`/`moveback`/`movestop`, `info`; spawner options (13th field: SpawnerState 0 start, NearDistance, interval jitter, AlienOrders MoveTo / MoveToIgnoringMarines with a target, which the alien follows: `AS_AlienGoal`); trigger options (5th field: name, StartDisabled, marines needed inside or all living, alien-only). No level uses them yet: Phases 5 and 6 will.
- **Previewer:** `tools/preview_scene.py` lays pieces at their real heights, the stair pieces included.

The whole campaign (`py tools/pack.py --campaign --png dist/campaign-pack.png`): its seven maps as port levels need 113,403 cells side by side, against SC2's 65,536. They do not fit without clashes. Letting later levels give way where floors clash (the best of 12 placement orders), all seven fit in 256x256: Deima, Rydberg, Residential and Sewer Junction keep every floor vertex; Timor Station loses 2.6% of them (worst 2.7 units off), Landing Bay 12.6% (1.9 units) and Landing Bay 2 15.1% (2.7 units). The way to get those back is rotating or mirroring levels in the pack (changes the view), trimming hull margins, or a second map for the last missions.

Run in the client (2026-10-24, `-Auto`): the whole campaign completes with no script errors, the kit reports 0 leaks and 0 shut cells, and Landing Bay's stairs show (a north flight with its nosing, a side flight and a corner plate seen by the wire-panel door). Still to check by hand (`.\launch.ps1 -QA`): units walking the stairs, the camera over the steps, plating and walls flush with the floor, the dropship and effects at the right heights, the minimap, and Landing Bay working at its new origin (x 114).

## Missions 3 and 4: Deima Surface Bridge and Rydberg Reactor (2026-10-24)

Jacob's Rest's second and third missions, built the way Landing Bay was: each laid out from its map's own floor, heights, entities and triggers (`tools/asdata/<map>.json`), one module each (`tools/deima.py`, `tools/rydberg.py`), in `build.py` LEVELS after Cargo Elevator. Built and checked offline (`py build.py`, `--qa`: type and bounds checks pass; the pack still fits, map 232x240 with Deima at 0,0 and Rydberg at 0,112). Not yet run in the client.

- **Traced levels** (`tools/astrace.py`): a level crops its map's 40-unit floor cells to 80-unit port cells (median height, mean walkable fraction), keeps walkable pieces of 12 cells and up, and reads lights, spawners and entities straight from the extractor's tables. Spawners are every one the map can start, set down on the nearest deck cell.
- **Heights** run through `tools/heights.py` as Landing Bay's do, plateau merge and all. Deima keeps its streets, catwalks and bridge on a few floors, with 480 slope cells of stair flights. Rydberg has eight floors over 118 slope cells: the plant at 608, the turbine hall a step down at 544, and reactor control up at 760.
- **Scripted missions** (`src/Mission.galaxy` SCRIPTED MISSIONS, from `AS_LV_SCRIPT` on) run on their data alone:
  - objectives by key with marker spots (`OBJECTIVES`), the briefing's objectives, text and tech rule (`DESCRIPTION`, `NEEDS_TECH`);
  - mail from mail 4 on (`MAILS`) and buttons (`BUTTONS`, powered or not);
  - actions `complete`, `show`, `open`, `power`, `notech`, `boom x,y`, `lightning`, `shipguns` and `lights`;
  - events `pressed:`, `hackstart:` and `hacked:`.

  New door kinds (`src/Doors.galaxy`): `gap`, a ramp whose plates slide out over the drop; `block`, an unseen barrier; and `hover`, a drop crossed once a ship hangs over it. The autopilot's route has two new waits: 5, press the button by it; 6, wait for the door, gap or ramp by it to open.
- **Deima** (`tools/deima.py`): the colony surface at night in a snowstorm, the whole level outdoors.
  - The drops open into the blue-fogged pit (`tools/pitart.py`), and one-cell hull strips (AS's railings) are kept as railings.
  - The main pipeline (`KPitMain`) runs along the chasm beside the long pipeline bridge.
  - The flow: hack the gate, extend the ramp, set off the charges (the pipeline blows and the wreckage clears), hack the bridge gate, cross under the dropship's guns, and step off onto its hovering deck to the reactor entrance. Lightning flashes every 15 to 20 s.
  - New art: snowed concrete and tread plate, the bridge's grating deck, red colony walls, and snowed roofs on the hull tops (`KR` caps).
- **Rydberg** (`tools/rydberg.py`): the power plant, indoors.
  - The flow: from the loading dock through the pump halls and coolant galleries; hack the reactor control door while rangers come over the railings; start the reactor (the lighting goes to POWER RESTORED); open the airlock; cross the turbine hall; and hold while the north doors grind open (32 s), with boomers, drones and buzzers coming.
  - AS's fall volumes lie under real floor, so only the reactor core's well and floorless gaps are opened. The exit room is walled off but for its doors.
  - New art: a works kind (`floor_plantconc`, `floor_coregrate` lit amber from below, `wall_bluestripe`, `wall_rust`), and the reactor core (`KPitCore`) rising out of its well beside the control room.
- **Capacities raised** for the bigger levels:

  | Item | New limit |
  |---|---|
  | Kit actors | 16,384 |
  | Kit units | 4,096 |
  | Lamps | 160 |
  | Spawners | 192 |
  | Triggers | 96 |
  | Tracts | 384 |
  | Pending actions | 64 |
  | Outputs | 256 |
  | Route points | 96 |
  | Door blockers | 48 cells |

- **Renders:** `dist/scene-deima.png`, `dist/scene-rydberg.png` (`py tools/preview_scene.py deima|rydberg x,y,aim ...`).

Still to check in the client: both missions end to end on the autopilot (`-Auto`) with no script errors and 0 kit leaks. Also check by hand:
- the gap plates and the dropship's flight;
- the exit doors' wait and the reactor's glow;
- snow and lightning under SC2's lights.

## Mission 5: SynTek Residential (2026-10-24)

Jacob's Rest's fourth mission, traced from `asi-jac4-residential` as Deima and Rydberg were (`tools/residential.py`, in `build.py` LEVELS after Rydberg Reactor). Built and checked offline (`py build.py`, `--qa`: type and bounds checks pass; map 240x256, Residential at 151,72). Run in the client on the autopilot (2026-10-25, run a8346278852d, a fresh client): the whole six-mission campaign reached CAMPAIGN COMPLETE with no script errors and 0 kit leaks in every mission; SynTek Residential took 371 s.

- **Layout:** the walkable floor less the thin walls that part its rooms. The extractor now rasters the BSP's solid brushes at chest height (`wall_pct`, `wall_px`), since the offices' glass and partitions are detail brushes the floor alone does not show (`tools/astrace.py` `partitions`).
- **Heights:** the streets and offices at -56, the lobby's walkway a short flight up, and the mall's gallery 216 higher. The gallery stands over the mall behind a strip of the drop (pit skirts and a railing). Its three stairs are long flights (`FLIGHTS`, new in `tools/heights.py`, with `HEIGHT_SET` for the floors the trace could not reach). 51 slope cells.
- **The flow** (`src/Hive.galaxy`, new):
  - Destroy the 26 eggs: 22 laid round the block, plus two of the offices' four egg groups picked at random at the start.
  - Burn out the eight growths. The flamer is issued if nobody brought one (`asw_equip_req`).
  - The objectives count down "(gone/total)". Named eggs and growths fire `broken:` and `ignite:` events: lighting the mall's growth wakes the mall, and burning it takes down its walls of goo.
  - Once both counts are done the elevator has power. The call brings the lights down, an alarm, and waves from every side for a minute until the car opens.
  - The autopilot's wait 7 burns and shoots out whatever is left within 9 cells and in sight.
- **Glass** (`src/Doors.galaxy` kind 7, `tools/colony.py` `EGlass`): the office windows are panes in steel frames. They shatter for good when a marine comes up to one or a drone swipes it. The west office, which has no door, is entered through its glass.
- **New art** (`tools/wallart.py`, `tools/deckart.py`):
  - walls: sea-green and gunmetal pressed panels with a worn orange band, white tile, three lit shopfronts, and flats with a door, number and keypad;
  - floors: white tile, mossy tread tile and dark slabs;
  - room kinds `colony`, `office`, `housing` and `mall`, which dress as the ship's halls, labs, crew rooms and stores.
- **Packing** (`tools/pack.py`): when biggest-first fails, the levels are tried in campaign order and in reverse. No lift may take a level's pit floor below 0 or a gallery over 250.
- **Route:** `tools/routeplan.py` now also checks that every egg and growth lies within reach of a wait-7 stop on its own floor (`unswept`). Its clearance is 0.45, so one-cell ducts plan. The route has 80 legs, none blocked and no egg out of reach. Door1's panel is AS's 2x5 two-wire one.
- **Render:** `dist/scene-residential.png`.

From the commits alone (2026-10-25, `build.py --auto --start 4` in a clean worktree, run c6fd5b44417c): SynTek Residential complete in 399.6 s with 0 kit leaks. It took two fixes first (4ce0cb1): the hive job had counted aliens behind walls, and a wait-7 stop now stands in the bathhouse duct. Watched on screen and in the log: seven office windows gave way as the squad came up (window_01 to the two corner panes), both goo walls opened (t=109 and 110), and the elevator held the squad under attack in its lobby and opened 67 s after the call. Pressing the elevator button raised a script error, from the button sound in `src/Use.galaxy` (see below; now fixed).

With the autopilot's watchdog (2026-10-25, the commits to 2b3e9cd plus the watchdog's `src/Hive.galaxy` and `src/Bots.galaxy`, run 323ac4da55c6): SynTek Residential complete in 396.1 s and Sewer Junction B5 in 195.8 s, 0 kit leaks, no script error log, nothing forced. Four runs before it stalled in Residential on a job that could never finish: a hive stop's firing spot round a corner from its target (the vents and stop 57, 400 and 570 s), Door10 dented shut by the swarm behind it (1,400 s), and an egg at stop 53 the marine stood beside and never killed (cause not found; the new spot search stands it elsewhere). The autopilot now picks a firing spot in sight of its target, shoots down an auto door dented shut, logs a job or leg that gets no further, and forces it at 90 s (a hive target) or 150 s (a plain leg) with an `autopilot forced:` line, so a run always reaches the end; a run with a forced line is not clean. The one `autopilot stalled` line in this run is the elevator's hold (waypoint 80, wait 6). Two of the earlier runs were also cut off ("p1 left") when another project's SC2Switcher launch handed its map to this client.

With the stand-point fix and the sound probe fix (2026-10-25, run 23f59b5a6adf): SynTek Residential complete in 376.3 s and Sewer Junction B5 in 184.1 s, 0 kit leaks, no script error log, nothing forced. The run before it (e86277e93965, the watchdog's commit) finished but was not clean: the egg at stop 53 was forced at 90 s, its firing spot up a duct one cell wide that the marine's body could not enter on a slant (a spot must now be walkable straight from the waypoint, and the marine goes by way of the waypoint when it is not straight there from where it stands); and the client logged "Unknown sound id requested: 'ASBark_'", the build's sound probe taking the marine barks' id prefix for a sound (`build.py` now skips ids ending in `_`).

## Mission 6: Sewer Junction B5 (2026-10-25)

Jacob's Rest's sixth mission, traced from `asi-jac6-sewerjunction` as the others were (`tools/sewer.py`, in `build.py` LEVELS after SynTek Residential). Built and checked offline (`py build.py`, `--qa`: type and bounds checks pass; map 256x256, Sewer at 109,111). Run in the client on the autopilot (2026-10-25, run a8346278852d, a fresh client): the whole six-mission campaign reached CAMPAIGN COMPLETE with no script errors and 0 kit leaks in every mission; Sewer Junction B5 took 292 s.

- **Layout:** the traced floor, less the thin walls between rooms. AS's floor materials now come out of the BSP too (`tools/asextract.py --mats`, `floor_mat`): water, concrete, grate, metal plate, tile. They set each cell's kind (`CELL_KINDS`, new in `tools/level.py` `kind_at`): water is a channel, grate and plate a catwalk, concrete and tile the sewer's walks, and the cells round each egg cluster growth.
- **Heights:** five clean levels:
  - the channels and pump hall at -592;
  - the pump hall's raised walks at -552;
  - the tunnel hall's north walk at -544;
  - the north walkways and the yard at -480;
  - the hatch at -288, at the top of a three-cell flight.
  The walkways cross the sewer's sumps, which are a deep fogged drop here (`tools/pitart.py`). A walkway's sloping lip counts as walkway. The sump by the turbine, which AS's route dips into, is decked over at the walkway's height.
- **The flow:**
  - Collapse the tunnel: the charges at its mouth are named barrels (`HIVE_BARRELS`), and one going up brings the roof in (`TunnelCounter`). The buzzers stop, drones come from the north, the tunnel's growth dies (`kill`, new), and the objective completes five seconds later.
  - Destroy the 20 eggs.
  - With both done, the yard's wall is blown out (`blow`, new: the door breaks and stays open) and the way out opens. The first autopilot run (2026-10-25) stalled there: the wall had only been unlocked, so it shut again before the autopilot reached its wait stop 5.5 cells away.
  - Shooting the shelf over the settling channel brings it down on the container, which clears the shelf's two clips.
  - The turbine's control is a button: pressing it stops the turbine and, on Insane, wakes its buzzers.
  - Every trigger's spawns, stops, random picks and commander lines are read straight from the map.
- **New art** (`tools/wallart.py`, `tools/deckart.py`):
  - walls: stained form-course concrete with a water line, pipe runs, a lit outfall grate, slime-streaked concrete, and a work lamp with the junction's "B5" and a hazard band;
  - floors: cracked concrete, murky water with ripples and scum, glowing slime, and a drain grate;
  - on the water: drifts of scum drawn out along the flow and floating litter (`KDFoam`, `KDDebris`, decals the level lays itself through a new `SPOTS` list), so the flooded pump hall and channels read as moving water rather than a plain floor. Overhead mains were tried first and dropped: at that height they hid the marine;
  - room kinds `sewer`, `channel`, `catwalk` and `growth`.
- **Packing** (`tools/pack.py`): six levels no longer fit with bottom-left placement in any order. `search()` tries six placement rules per level and backtracks; Landing Bay goes in the top-right corner and Rydberg left-first. It runs only when the plain orders fail, and takes about 45 s.
- **Route:** 48 legs, none blocked, and every egg within reach of a wait-7 stop. The autopilot shoots a named barrel from beyond its blast (`src/Hive.galaxy`), and it leaves alone any growth that no objective counts. Sewer Junction has no `trigger_asw_button_area`, so there is no wire panel.
  A Sewer-only run (`build.py --auto --start 5`, run 29ace728390a, 2026-10-25, with the scum and litter in) was complete in 227.8 s: no script errors and 0 kit leaks. The autopilot was still pinned five times, at the catwalk bridge (42,55), the channel walks at (33,54) and (27,61), the corridor at (34,114) and the turbine catwalk (25,130). Each time, `AS_AutoUnstick` (src/Bots.galaxy, the parity session's, committed as fcbe94f) stepped it free after 4 s. Before that commit, a build of the commits alone stayed pinned at the bridge for 1,100 s (run 5ba7b412cc34). All five spots lie where the route turns into a duct one cell wide. Walls alone don't pin it: walking the whole route offline at full running speed through `AS_Move`'s collision (slides and corner rounding), the marine never gets stuck. But every spot has an alien source on it or right ahead of it: `DroneSpawnRailing4` on the bridge, the drone spawners over the channel walks, the mortar and shieldbug spawners at the corridor, and the sleeping shieldbug at the end of the turbine catwalk. So the likely cause is aliens' bodies in a one-cell pass (SC2 pushes the marine unit back). That would need the unstick, or the autopilot fighting its way through, not a different route. Not confirmed on screen.
- **Render:** `dist/scene-sewer.png`. Judged next to Landing Bay's, Deima's, Rydberg's and Residential's renders: the halls carry as much detail as Rydberg's tiled rooms, in the sewer's own palette.

From the commits alone (2026-10-25, with fcbe94f's unstick, run f2d4f2b5d4eb): Sewer Junction B5 complete in 265.1 s with 0 kit leaks. The tunnel came down at t=95.1 (its charge blew, the objective completed 5 s later), and the yard wall was blown at t=236.9; both were seen in the log, not on screen. The one script error, in this run and in Residential's, is the button sound `UI_TerranCommandCenter_Liftoff` in `src/Use.galaxy` (committed with Deima, e4d4fdc): no such sound in the mods this map loads. It fired once at start (the sound probe) and again at each button press; it is now `UI_BnetClick`.

## Marine chatter voiced (2026-10-25, in progress)

Every chatter line a marine barks over its head (16 kinds, 38 lines) is now also said aloud in that marine's own voice. The text chatter itself (AS-PARITY Phase 4: `AS_Chatter` on AS's triggers, with the squad's one-line-at-a-time timer, per-kind cooldowns and chances, after `asw_marine_speech.cpp`) is committed with it. `tools/barks.py` holds the lines (moved out of `src/Bots.galaxy`; build.py writes `AS_ChatLine(k, r)`, `AS_ChatCount`, `AS_ChatKey` and the clip lengths `as_barkLen` into Bots in place of `@BARKS@`) and voices them with Gemini TTS through the `KEY` in the repository's `.env`, a Google AI Studio key. Each marine has a prebuilt voice and a character line (Sarge Rasalgethi, Wildcat Kore, Faith Sulafat, Crash Puck, Jaeger Fenrir, Wolfe Zubenelgenubi, Bastille Iapetus, Vegas Sadachbia). One request reads all 38 lines of a marine in one take; the take is cut at its own pauses, and every clip is checked by a Gemini transcription that is not shown the script. `build.py` packs only clips that passed (`assets/barks/manifest.json` `ok`), as `ASBark_<marine>_<kind>_<n>` CSounds in the Voice category, appended to the commander's SoundData.xml. `AS_Chatter` plays the speaker's clip to every player, holds the text tag as long as the clip, and holds the squad's next line until it is said. A line with no passing clip stays text only.

Built and compile-checked offline (`py build.py`: type and bounds checks pass; 86 bark clips packed beside the commander's 18). **Not yet heard in the client.**

**Open (retry 2026-10-26):** only Sarge (38/38), Crash (38/38) and Jaeger (10/38) are voiced. The key's project is on the Gemini API free tier (the user's Google AI Pro subscription does not cover API billing): about 10 TTS requests a day for `gemini-3.8-flash-tts`, and 20 a day for the transcription model `gemini-3.5-flash`. Today's ran out. The fallback `gemini-3.1-flash-tts-preview` refuses whole takes on SAFETY (the infested and dying lines), and its half takes did not cut cleanly. To finish:
- `py tools/barks.py` once the quota resets. It voices only what is missing or failed (Wildcat, Faith, Wolfe, Bastille, Vegas, the rest of Jaeger); 6 takes and 6 checks fit one day's quota. Then `py build.py`, and hear it in the client: an `-Auto` run logs `chatter pN: <line> (<s> s voiced)`.
- Or record by hand: `py tools/barks.py --script` writes `assets/barks/AI-STUDIO.md` (each marine's voice and paste-ready prompt for AI Studio's Generate speech), and `py tools/barks.py --import <folder of <marine>.wav>` cuts and checks those takes.
- Or turn on billing for the key's project, and the same `py tools/barks.py` finishes in one run.
