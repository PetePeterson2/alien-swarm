# Halcyon Drift: Alien Swarm combat proof of concept (work in progress)

**Status (2026-10-20): the source is written, but nothing has been built or run yet.**

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
