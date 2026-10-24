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
