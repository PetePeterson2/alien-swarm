# Alien Swarm reference: Landing Bay and Cargo Elevator, played 2026-10-23

Notes from playing the Steam game's first two missions (`asi-jac1-landingbay_01` and `_02`) at its high effects setting, 1920x1200 windowed, on Easy, with Crash. They record what the port should look and feel like. Numbers come from the SDK (`../AlienSwarm/src`) and from the maps' own entity lumps; everything else is from the screen.

**Captures** (in `dist/asref/`; reference only, nothing of them is shipped in the map; the clips are git-ignored for size):
- Clips (8 fps, the left 64% of the screen):
  - `lb-dock-walk.webp`: the opening dock.
  - `lb-storage-fight.webp`: the first drone fight.
  - `ce-lift-ride.webp`: the whole cargo-lift descent.
- Stills: `lb-01` to `lb-10` and `ce-01` to `ce-08`.
- Demos: `lb_run1.dem` and `ce_run1.dem` in the game's `swarm/` folder. Play them in Alien Swarm with `playdemo lb_run1`.

## Camera and framing

- **Pitch 60, 412 units out, FOV 75** (`asw_cam_marine_*`). On the deck that is about **8.5 cells across and 6.4 deep** (a cell is 97 units: 290 a second is 3 cells a second). The cargo lift's 6-cell platform fills **70% of the screen's width**, and a marine is about 7% of the screen's height.
- **The camera leans toward the cursor** (`CalculateCameraShift`). The cursor's offset from the screen's centre, as a fraction of the screen (−0.5 to 0.5), is multiplied by 300 units across, 200 north and **380 south**. Aim south and the marine rides near the top of the screen with nearly two cells more of the room below him. There is no lag beyond a 1 s fade-in, and spectating turns it off. This was the biggest single difference in feel: you look where you shoot.
- Walls between the camera and the marine are black silhouettes. Everything outside the playable space is **pure black**: there is no hull or terrain to see past a wall top.

## Lighting and map feel

- **Two extremes, not one dark mood.** Lit interiors are high-key: white and pale-grey panelled walls, yellow safety trim (perforated yellow beams), red pipe runs, bright grating with hazard chevrons, "WATCH YOUR STEP" stencils, blood pools and dead colonists. Unlit storage rooms are near-black (10–20% brightness) until a lamp or the laser picks something out.
- **Hard light and hard shadows.** Point lamps with bloom; long shadow bands from beams and girders across floors; light through grating throws a dappled cookie pattern on walls; the marine casts a long shadow from spotlights.
- **Coloured rooms.** Landing Bay opens outdoors at night: a snowy dock under blue fog, with red and pink neon trim and rotating red alarm light. Inside, one room glows sodium-orange behind black girder silhouettes, and Cargo Elevator's start has orange light coming up through floor grating.
- **Atmosphere everywhere.** Steam puffs from pipes, drifting dust motes that the red laser sight lights up, snow outdoors, and fog. The maps' fog colours are interior (120,90,60) warm brown, exterior (39,53,86) night blue, and in the lift shaft (43,37,32) dark brown at 0.9 density.

## Shooting aliens

- **Drones swarm onto the marine** and cling round him in a clump of 5+. Each claw hit throws a **bright red spray of streaks** off the marine.
- **Rifle:** a white-hot thin tracer along the red laser line, and a small yellow-white muzzle flash. The laser runs from the gun to the cursor at all times.
- **A drone's death** is the loudest effect on screen: a **bright lime-green flare of acid streaks about a cell and a half across** that hangs for a moment, then a wider green mist. Pale claw and leg gibs fly off, dark green splats stay on the floor, and some corpses stay.
- **HUD:** "- RELOADING -" in red while reloading, the fast-reload bar beside the portrait, and LOW AMMO in red. Key-cap hints appear in the world: "Move Marine", "Melee", "Watch Movement Scanner", "Deploy Ammo", "65 Ammo lost in old clip".

## The cargo lift (Cargo Elevator)

- **Waiting:** the platform sits under **warm yellow sodium light** (`light_spin_ele_top`), with yellow border paint, hazard-striped panels, crates, and a north railing with the green-screened button console.
- **The sequence, from the button** (`relay_lift_but_succeed`):
  - 0 s: entrance ramp shuts.
  - 2 s: shake, a **dust burst**, motor sparks.
  - 3 s: the walls start; the **yellow light goes out** and a **red spinning light** comes on; rail sparks; rumble loop.
  - 15 s: the climber and spawner timers start.
  - 16 s: a slow-motion beat (`env_slomo`).
  - 17 s: parasites.
- **The walls move, not the platform** (`FreightElevatorWalls`, a func_tracktrain at 25 units a second over 2,655 units): **a 106 s descent that creeps.** Its path runs up and south, almost straight at the camera, so the wall mostly looms rather than scrolls.
- **What is visible:** the **whole platform plus the shaft walls on three sides**, with no black void on screen. The north wall fills the top 35–40% of the screen: concrete, big horizontal pipes with red flanges, steel trusses, and caged lamps with orange-red glows (200,47,2) every 380 units, riding up with the walls.
- **During the ride:**
  - Rotating red beacons sweep red light across the deck.
  - Steam jets vent from the pipes.
  - Beige-brown dust haze fills the shaft.
  - Passing lamps wash yellow across the platform.
  - **Drones crawl down the north wall** as dark silhouettes (bigger the higher they are, since that is nearer the camera), then drop onto the deck in waves of 10+.
- **Arrival:** yellow light again, and three exit lamps blink in sequence, 0.3 s apart, to point the way out.

## What the port took from this (2026-10-23)

- **Camera:** distance 8 → **6**, so the screen shows what AS's does (8 showed about 11.5 cells across; 6 shows 8.5). Z steps 8.5 and 12.
- **The lean:** AS's camera shift, with the same constants and the cursor kept as a screen offset, so the gun still points at the cursor while the view slides (`src/Marine.galaxy` `AS_LeanUpdate`; the camera follows an invisible anchor unit).
- **The ride:**
  - Framed like AS's: distance 13 and 2 cells north of the marine (the platform is twice AS's size), so the whole deck and the walls round it show (`AS_RideFrame`; `tools/preview_lift.py` renders it).
  - Sodium floodlights that die as the walls move and come back at the bottom; a dust burst at the start; steam jets off the shaft walls; exit lamps chasing at the bottom.
  - About 100 s long at 1.1 cells a second (was 75 s), with the wave schedule stretched to match.
- **Kills:** every non-burning kill adds a lingering lime-green acid flare over a wider green haze (`AS_AcidCloud`).
- **Hits on a marine:** a red spray of streaks thrown away from the claw.

**Second round, the same day:**
- **The shaft:**
  - The void ring round the platform is the shaft's brown haze (43,37,32, glowing faintly, with cables and girders as darker streaks) instead of black.
  - The plain shaft panels carry a big pipe with red flanged joints, and the lamp panels' glow is AS's orange-red.
  - Dim brown haze drifts over the deck during the ride.
  - The first alien to land on the deck brings AS's slow-motion beat: the game slows to Slower for 0.9 game seconds, then goes back to its speed.
- **Landing Bay's opening is outdoors:** snow falls round each player from the dock to the freight yard (`OUTDOORS`, `AS_SnowPulse`). The dock is lit cold blue with a red alarm and pink light on the walkway, the yard by hard white floods.
- **HUD:** "- RELOADING -" in red over the portrait while a clip goes in.

**Third round, the map:**
- AS's opening is not a hallway. You stand on catwalks and platforms over a drop, with railings at the edges, blue haze, steel trusses and a few lamps far below, and snow falling through.
- The port's outdoor stretch (Landing Bay's `OUTDOORS`, from the dock to the freight yard) is built that way now:
  - **The drop:** hull cells there become open night (`o` in the deck rows, `AS_OPEN` in the kit). They get no walls and no hull tops; instead they get a painted drop: blue haze in AS's exterior fog colour, girders and a lattice tower far below, lamps down there (`tex_open`).
  - **Railings:** yellow railings run along every edge where the deck meets the drop (`KRail`).
  - **Buildings:** hull blocks bordering the drop show plain walls, so the inner perimeter stands as a building rising out of the night.
  - **Pathing:** collision and alien pathing are unchanged; they come from the same hull cells.
- The drop can't be truly lower than the deck: both levels share one terrain. So the depth is painted, and the railings, snow and haze sell it. `py tools/preview_dock.py` renders it from the game camera.

**Still open:** AS's high-contrast lit and unlit rooms everywhere else, and real fog. SC2 lighting is one preset for all players, so it can't be set per room.

**Fourth round: the visual pass (2026-10-23/24).** Taken from the captures above and from the game's own textures (read from its VPKs for palette and pattern only; nothing of Valve's is shipped):
- **The camera** is AS's lens exactly: pitch 60, about 60 degrees tall (Source's 75 is horizontal at 4:3), 412 units out, which is 5.1 cells here. SC2's field of view turned out to be the vertical one (measured on an old screenshot). A marine fills 7.5% of the screen's height, AS's 7.6%.
- **The marines** hold real guns at the hip along the aim, one model per weapon family, and every round leaves the muzzle; the laser runs from the gun's emitter to the deck under the cursor (or to the bulkhead or alien in the way), a hot core in a soft red halo with a dot where it lands. Suits take the muted colours of AS's class textures (Tech steel blue, Heavy brown-red, Sarge camo, Jaeger khaki).
- **The colony's look:** pale concrete slabs and galvanised grating (concretefloor050a, metalgrate012a), pale wall panels outlined in worn yellow, fat red flanged pipes, yellow perforated girders on the walls and overhead, hazard chevrons round hatches, WATCH YOUR STEP at the stairs, blood and paper where the crew fell, near-black beyond the playable space, pink neon along the dock's edges, a sodium-orange pump room, and Cargo Elevator's walkway lit orange from below (ce-01).
- **Life:** dust in the air and motes lit by the laser, steam from grates and pipes, flickering and sparking lamps and consoles, turning fan shadows, smoke after blasts.
- **The AI squad** only fights what a player can see (or what is at its elbow), as AS's marines back the player up.

## Deima Surface Bridge and Rydberg Reactor (2026-10-24)

Not played: taken from the installed maps (`asi-jac2-deima`, `asi-jac3-rydberg`) through `tools/asextract.py` and `tools/astrace.py`, and from their materials in the VPKs (looked at for palette and pattern only; nothing of Valve's is shipped). Captures of the other missions are still to do.

**Deima: what AS has.**
- The colony surface at night in a snowstorm, on catwalks and streets above a chasm. The main pipeline runs along the chasm, and the long pipeline bridge crosses it to the reactor.
- Floors:
  - `blendconcsnow001b`: grey poured slabs (`concretefloor050a`) with snow packed into the joints.
  - `blendmetalsnow002a`: diamond tread (`metalfloor011a`) under snow.
  - `snowfloor001a`: drifts.
  - The bridge and catwalks are dark steel grating on riveted beams.
- Walls: `metalwall008c`, red-painted corrugated panels between grey posts.
- Lights: cyan floods (140,215,205), pale-blue big lamps (137,214,218), red lamps strung along the bridge (175,41,27) and one sodium yellow.
- The flow: the gate hack, the bridge ramp button, the detonator that blows the pipeline and the wreckage blocking the pump station, then the dropship hovering over the last gap.

**Deima: what the port took.**
- The traced floor, with every drop opened into the blue-fogged pit and one-cell railings left as railings.
- The pipeline as pit pieces (`KPitMain`) along the chasm.
- New art:
  - `floor_snowcrete`, `floor_snowplate`, `floor_bridgedeck`.
  - `wall_red`.
  - Snowed roofs on the hull tops (`cap_snow`, the `KR` caps).
- The lights by colour.
- The script's order, with these door kinds:
  - the ramp as a gap whose plates slide out;
  - the wreckage as an unseen block;
  - the dropship's deck as a hover gap.
- The commander's lines are paraphrased and the crew's mail is invented.

**Rydberg: what AS has.**
- An indoor power plant lit sodium orange, with orange interior fog. The squad works north from the loading dock through pump halls and coolant galleries to reactor control, hacks its door, and brings the reactor online. The airlock then opens on the turbine hall, and the north doors take their time opening while the swarm comes.
- Floors:
  - `concretefloor051`: green-grey cast tiles.
  - `metalgrate014`: dark slatted grating.
  - `metalfloor012a`.
- Walls:
  - `concretewall082a`: pale board-formed concrete with a slate-blue band.
  - `metalwall059a`: rust-orange primer plate.
- Sign: `reactorcontrolsign`, white on navy.
- Heights: the plant floor is at 608, the turbine hall a step lower at 544, and reactor control is raised to 760.
- The drops: AS's `asw_trigger_fall` volumes mostly lie under real floor (the gallery's and the shaft's sit 100 to 300 units below it). They are not holes in the walkway.

**Rydberg: what the port took.**
- The traced floor, opening only where no floor stands over a fall volume, and the reactor core's well beside reactor control.
- New art:
  - `floor_plantconc`, and `floor_coregrate` with amber light coming up through its slats.
  - `wall_bluestripe`, `wall_rust`.
  - The reactor core (`KPitCore`): a banded column with blue-white slits, rising out of its well.
- The plant's lights by colour.
- The lighting goes to POWER RESTORED when the reactor comes online.
- The exit room is walled off from the turbine hall except for its great doors, as AS's `exit_ceiling` brush outlines it.

## SynTek Residential (2026-10-25)

Not played: taken from the installed map (`asi-jac4-residential`) through `tools/asextract.py` (now with the BSP's solid brushes rastered at chest height, `wall_pct`/`wall_px`, since its offices' glass and partitions are detail brushes the floor alone does not show) and `tools/astrace.py`, and from its materials in the VPKs, which were looked at for palette and pattern only.

**What AS has.**
- SynTek's residential block on Deima: an entrance and security hall, a lobby with a walkway up behind its desk, a hallway to the offices, a mall with a gallery along its west side, living quarters, a bathhouse, the vents behind them and the elevator lobby. A small yard behind the lobby lies open to the snow (`snowfloor006a`).
- Materials, by the area they cover:
  - `concretefloor051a` (28%): green-grey cast tiles through the halls, quarters and elevators.
  - `res_metalwall001a` (27%): the block's walls, pale sea-green pressed-steel panels in a flat-bar frame with a worn orange band low down; `res_metalwall001b` is the same in dark gunmetal.
  - `metalwall045a` (16%): the vents' ductwork, floors and walls.
  - `concretefloor051c`: glazed white tiles, on the offices' and mall's walls as much as on their floors; `concretefloor051d` is the damp green version with tread-pressed panels.
  - `greymetalfloor2` in the mall, `swarm_grillefloorbsp` on the lobby and gallery, `concretefloor050a` dark slabs, `brickfloor001a`.
  - The office glass: `func_breakable` windows `window_01` to `window_15` (`swarm_glassdistortion`). The west office has no door at all; you go in through its glass.
- Stairs are props (`stairs_160_top`, `stairs01_128noends`, `stairs01_64noends`) whose clip brushes read as wall in the raster; the gallery is 216 units over the mall floor.
- The flow (`Objective_KillEggs`, `Objective_BurnGoo`, `Objective_Escape`): 26 eggs (22 placed, and two of four office templates picked at random), eight growths that only fire burns (`asw_equip_req` issues a flamer), the mall's walls of goo (`blocker_1`, `blocker_2`) gone once their growth burns, Door1 on the gallery behind a 2x5 two-wire panel (hack level 6). Once both counts are done the elevator buttons power up; calling the car brings alarms and waves for a minute before its doors open.

**What the port took.**
- The traced floor (`open_deck` less the thin `partitions` that part rooms) on real heights with the plateau merge. Stair flights where AS's stair props stand: the gallery's south-west flights off the hallway, its north flight down to the mall, and the lobby's flight up to the walkway.
- Egg groups picked at random at the start, named eggs and growths firing `broken:`/`ignite:` events, the counting objectives showing "(gone/total)", the flamer issued when nobody brought one (`src/Hive.galaxy`).
- The office windows as a new door kind, glass (`src/Doors.galaxy` kind 7, `tools/colony.py` `EGlass`): a pane in a steel frame that shatters for good when a marine comes up to it or a drone swipes it.
- New art:
  - Walls: `wall_seagreen` and `wall_seadark` (res_metalwall001a/b), `wall_whitetile` (051c on walls), `wall_shop0..2` (the mall's lit shopfronts), `wall_housing` (a flat's door, number, keypad and frosted window on the sea-green panels).
  - Floors: `floor_whitetile`, `floor_mosstile`, `floor_slab`, with the existing green-grey tile (`floor_plantconc`, the same 051a), grey plate and grille.
  - Room kinds `colony`, `office`, `housing` and `mall`, which dress as the ship's halls, labs, crew rooms and stores.
- Not ported: the grub sacs, the fire extinguishers' physics, the laser scanner, and the second elevator mortarbug template (`template_morter_elev1`).
