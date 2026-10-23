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

**Not yet seen in the client.** The first QA launch failed to compile (`as_spin` clashed with the minigun's global). The client then stayed in that game, so later builds couldn't load. The current build passes every static check. Next: `.\launch.ps1 -Auto`, read the ASAuto bank, then look at the ride in person. The online test steps are in `TESTING-ONLINE.md`.
