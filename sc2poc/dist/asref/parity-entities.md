# Alien Swarm entity lumps vs the SC2 port: Landing Bay and Cargo Elevator

Sources: lump 0 (entities), lump 14 (brush models) and the `sprp` game lump of `asi-jac1-landingbay_01.bsp` and `asi-jac1-landingbay_02.bsp`, parsed with the scratch scripts in `scratchpad\ents\`. Raw dumps are in `ents\lb01.txt` and `ents\lb02.txt`. Categorised tables with a reverse I/O index are in `ents\lb0?-tab.txt`. Cell tables are in `ents\lb01-cells.txt` and `ents\lb02-cells.txt`.
Port side: `tools\landingbay.py`, `tools\cargo.py`, `tools\lbcheck_spawners.py`, `AS-REFERENCE.md`, `src\Mission.galaxy`, `src\Objects.galaxy`.

Coordinates:
- **Landing Bay** cells use `cx=(X+8976)/80`, `cy=(Y+9512)/80`. The two anchors fit exactly: the computer at (-6472,1256) maps to (31.3,134.6), and the spawn centre maps to (51,7.5).
- **Cargo Elevator** cells use my own frame, `cx=(X+7200)/80`, `cy=(Y+1900)/80` (inferred). `cargo.py` is invented, so there is no port anchor to fit against.

Pract map (`asi-jac1-landingbay_pract`): 2825 entities and 151 spawners. It carries the objectives of both maps, so it is the two maps merged into a single tutorial level. It is not a third source of layout.

## Summary table

| Item | AS (lump) | Port | Delta severity |
|---|---|---|---|
| LB spawner set | 47 reachable `asw_spawner`s | 49 rows in landingbay.py; kind, count, interval, skill and near rule all match | low |
| LB spawner positions | see table | 7 spawners moved more than 1.5 cells (breakdoor_spawn by 2.8, insane_har2 by up to 4) | low |
| LB boomer/ranger at the exit door | boomer at (45.1,129.7) | boomer at (43.5,130.0); the two are swapped | low |
| LB dead spawners | 13 are never started: RandomSpawn2 x8, FirstEncounterSpawn2, DroneSpawn7, RandomParasiteSpawn5, InstanceAuto14-* | must stay inert | info |
| LB PDAs | Howe (mail1) at (38.2,48.5), Callen (mail2) at (13.6,71.4), Cain (mail3) at (9.4,111.8) | Howe at (9.4,112), Callen at (38.3,48.5), Cain at (13.6,71.5): rotated by one | med |
| LB doors | 14 `asw_door` | 13; InstanceAuto44 is missing. Seal values 8/10 and 10/10 are correct | low |
| LB control-door force | none. The door only opens after the download | `as_bayDoorForce` breaks it at 40 s | med (invented) |
| LB stair music | `AmbientMusic` target dangles, so nothing plays | `music` plays Event_Horner05sTerminalHack | low |
| LB tank-room pit | catwalks over a `trigger_hurt` pit (z 528, 999 dmg) with 3 `trigger_asw_jump` links | no pit or jump links (inferred from the tables) | med |
| LB weld hints | 3 `asw_marines_past_area` (fire when ALL marines are past) | 2 s polling timer | low |
| LB FirstDoorMover | banging door; `logic_timer` fires every 2-8 s at random until the storage trigger disables it | missing | low |
| LB dock lighting | warm (223,206,149) spots at 1100-1200; orange (247,134,60) at the pump room, tank doors, storage annex and lift | cold | med |
| CE route | tank hall, east hallway, north corridor, fireball shaft, glass gallery, burrow rooms, pipe/gap puzzle, ramp room, outdoor yard, lift | invented areas: security-door override, lower level, transit station | high |
| CE security-door override | LandingBayDoor11 is `autoopen=1`; its panel is a plain press button (`locked=0`) | hack, 9 s hold, horde at 15% | high (invented) |
| CE transit-car hold | none | 45 s hold, `AS_HoldPulse` | high (invented) |
| CE objectives | 2: cargo_elevator_objective and escape. `marker_cargo_elevator` is never enabled | 4 | high |
| CE fireball shaft | barrel → ElevatorShaftTrigger → explosions at 0, 1 and 1.4 s, shake 8 for 3 s, glass breaks, light train climbs | missing | high |
| CE pipe/gap puzzle | barrel → HugePipe rolls → MetalPlatform bridges the gap; 5000-dmg pit; GapLinkers | missing | high |
| CE glass gallery | panes on both sides (7 WindowSpawners); 8 drones inside from map start; NPC-only glass triggers | east windows only, 2 drones per pulse | med |
| CE vent blow | none | `AS_VentBlow`: 12 dmg and 3 parasites | med (invented) |
| CE lift start | button; `trigger_lift_marine_check` playersrequired=4; failure shows the `msg_lift_deny` popup | `AS_BoardPulse`: 5 s, everyone aboard | med |
| CE ride waves | drone_jumpers only (Insane adds parasites). PickRandom over 8 groups every 2-3.5 s, plus 9 climbing templates every 1.5-2 s | 11 waves: buzzers, uber/ripper, power surge at 38 s | med |
| CE ride length | 2655 u at 25 u/s; end event at 106.2 s | 100 s | low |
| CE exit | ExitSpawner x3 ordered to ElevatorExitTarget; about 19 cells to ExitZone across the yard | ? | med |

## Landing Bay (asi-jac1-landingbay_01)

### Objectives, markers, starts
- **Starts:** 9 `info_player_start` at cells (49-52.5, 6.6-8.3), z 943. A dropship `train_ship` departs on `path_1→path_3`; the movement-hint triggers fire `train_ship.StartForward` at +5.
- **Objectives:**
  - `AccessBay` (asw_objective_triggered) completes on the trigger_once at rect (25.0,47.0)-(33.4,49.2), z 1000, just past the twin gates. A `trigger_hurt` under the gates (z 784) also fires SetComplete.
  - `DownloadData` completes on the computer.
  - `ExitZone` (asw_objective_escape): the trigger_multiple at (46.0,125.7)-(54.8,134.9) z 904 calls MarineInEscapeArea.
- **Markers:** `asw_marker` at (29.7,45.0) for the gates and (31.6,134.2) for the computer; `marker_exit` at (50.6,130.7). Both mission markers are visible from the start.

### Route-ordered encounter table (trigger → spawner)
| # | Trigger (cell rect, z) | Fires | Notes |
|---|---|---|---|
| 1 | (33.0,8.5)-(38.6,8.9) z1049 | insane_buzz_spawn | Insane buzzers |
| 2 | (32.1,26.8)-(35.1,28.4) z1024 | insane_para_spawn | Insane |
| 3 | buttons Start_button_right1 (27.7,44.9) z1104 and Start_button_right (32.3,44.9) z1024 | LandingBayDoor2 / LandingBayDoor1 EnableAutoOpen | two gate lanes at z 1024 and 944 |
| 4 | (25.0,47.0)-(33.4,49.2) z1000 | AccessBay.SetComplete; insane_har_spawn | |
| 5 | (25.6,55.9)-(28.4,58.1) z929 | Storage_room_spawner | OnStartTouch |
| 6 | (16.4,61.7)-(18.3,63.5) z929 | Spawn04 | |
| 7 | (17.4,66.1)-(29.6,68.9) z1016 | storage_room_spawn_2; LogicTimerFirstDoor.Disable | stops the banging door |
| 8 | (17.9,72.8)-(18.1,74.7) z964 | Spawn05 | target DANGLES (no entity) |
| 9 | (24.7,78.7)-(30.5,80.1) z948 | storage_room_spawn_2_behind | spawns behind the squad |
| 10 | (21.8,81.2)-(23.0,92.2) z948 | tankroom_01_spawn; insane_har2_spawn | tank room |
| 11 | (23.4,83.3)-(24.2,92.1) z951 | storage_room_spawn_3 | |
| 12 | (11.9,99.5)-(15.4,102.7) z948 | tankroom_end_01_spawn; tankroom_end_04 | `_04` DANGLES |
| 13 | RandomSpawn5 trigger_asw_chance (9.7,98.1)-(12.2,98.5) z944, chance 0.1 | WallSpawner (+0.4), WallBreakDust, WallBurst | 10% wall burst; jumpers |
| 14 | (13.0,105.3)-(16.7,105.7) z930 | AmbientMusic.PlaySound; tankroom_end_02_spawn | AmbientMusic DANGLES |
| 15 | (11.4,109.1)-(17.8,109.5) z911 | case_supplyspawn.PickRandomShuffle +1 | picks one supply_spawn_0x |
| 16 | (9.9,118.0)-(16.3,118.4) z933 | tankroom_pre_02_spawn +1 | |
| 17 | (21.8,119.5)-(22.2,122.5) z927 | case_preholdout_spawn.PickRandomShuffle | |
| 18 | (27.8,125.3)-(32.6,129.7) z880 | sentry_placement.Enable | holo sentry at (29.8,128.5) |
| 19 | computer area (30.3,133.8)-(32.3,135.4) z912 | OnComputerHackCompleted → Tech_req off; download → AfterHack* | AfterHackSpawnTrigger DANGLES |
| 20 | (40.1,127.4)-(41.4,131.8) z888 | hallway_spawn_01; commander_choreo_m1_ob3 +2 | hallway_spawn_01 DANGLES in lb01 |
| 21 | ExitZone (46.0,125.7)-(54.8,134.9) | MarineInEscapeArea | |

- **Computer timings** match Mission.galaxy: hack start spawns at +5 x3, the holdout stops at +8, line co_m1_ob2 at +14. The lump also starts insane_ranger at +0 on hack start; the port is missing this.
- **dock_holdout_spawn_01** is 5 infinite spawners (6 aliens, 4 live, every 1.5 s) at (24.5,127.5), (25.8,132.2), (34.1,125.1), (23.4,122.2) and (27.4,122.2), all z 840.

### Spawner position deltas over 1.5 cells (lump → port)
- breakdoor_spawn: lump (45.2,129.1/130.2), z 832/835, behind the exit door InstanceAuto1-LandingBayDoor (45.8,129.6). Moved 2.8 cells.
- tankroom_end_01: 1.7. tankroom_end_02: 2.4. supply_spawn_02: 2.6. supply_spawn_03: 2.5. insane_har2: up to 4. insane_ranger: 1.9.
- Boomer/ranger: the lump boomer is at (45.1,129.7); the port has it at (43.5,130.0), the ranger's spot.

### Placed aliens and totals
- **Placed `asw_drone`s:** (19.2,62.7), (26.6,77.0), (28.1,77.3), all z 873. Two `prop_ragdoll` corpses and one `asw_client_corpse` at (31.8,41.5).
- **Totals across all skills:** 108 finite drones, 5 infinite holdout spawners and 3 jumpers.
  - Normal+ adds 5 drones.
  - Hard+ adds 2 jumpers.
  - Insane adds 12 buzzers, 2 parasites, 5 harvesters, 2 rangers, 3 infinite ranger spawners and 1 boomer.

### Doors (cell, z, flags)
- **Twin gates:**
  - AutoInstance1-LandingBayDoor2 (26.6,45.2) z1024
  - AutoInstance1-LandingBayDoor1 (31.2,45.2) z944
  - Both are opened by their buttons.
- **Weld doors:** WeldDoor2 (28.0,66.0) z872, WeldDoor3 (20.3,65.8) z952, WeldDoor1 (14.1,103.1) z832.
- **Sealed doors:** InstanceAuto69 (23.4,84.7) and InstanceAuto70 (23.2,91.0) are sealed 8/10. InstanceAuto94 (11.2,110.4) is sealed 10/10.
- **InstanceAuto44** (12.7,67.2) z792: doortype 2, flags 1, spawnpos 1. This is the decor door the port omits.
- **Exit pair:**
  - AutoInstance1-LandingBayDoor (36.6,129.6), autoopen 0. This is the control door, opened only by the download.
  - InstanceAuto1-LandingBayDoor (45.8,129.6), autoopen 1.
- **CeilingBlackBox:** func_movelinear at (41.2,129.5) z1032, with a BlackBoxLightSound.

### Interactables
- Welders at (27.6,91.6) and (25.4,80.2).
- Sentry pickup at (8.0,113.3), plus the holo sentry_placement.
- Explosive barrels at (25.5,78.1) and (26.6,85.6).
- PDA computer areas at (38.2,48.5), (13.6,71.4) and (9.4,111.8) (see the PDA delta).
- WallBurst `func_breakable` at (10-12,103).
- Jump links: (23.5,69.1) z1008, which is balcony→JumpSpot1, and the two tank-pit links at (16.5,100.5) z571 and (18.5,101.2) z958.

### Prompts and cues
- event_proxy hints: general hint at (39,6.3), movement success at (46.2,6.3) and (50.6,11.5).
- commander_choreo_m1_ob3, +2 after the exit hallway trigger.
- Stinger `asw_song.Stinger` at the computer.
- FirstEncounterSound1/2 door-handle sounds at (26,62) z1150.
- WallBreakSound ASW_T75.Explode.
- The lb01 instance also contains the elevator fireball sounds (45.4,155.1), (47.2,149.9). They are unreachable here.

### Lighting and fog
- Interior fog (120,90,60), 256-6000, density 0.5.
- Exterior fog (39,53,86), 256-4000, density 0.5.
- Elevator fog (43,37,32), density 0.9.
- 3 snow precipitation volumes.
- Warm and orange spots as in the table. Details are in `ents\lb01-atmo.txt`.
- 3027 `prop_static`; the most common model is pipe_64 x211.

### z plateaus
- Dock and start: 943. Gate lanes: 944 / 1024.
- Storage: 848-881. Office lower level (InstanceAuto44): 792-807.
- Tank room catwalks: 912; pit: 528.
- Supply corridor: 832-845. Computer room: 912.
- Exit dock: 832-840.

## Cargo Elevator (asi-jac1-landingbay_02)

Cell frame: `cx=(X+7200)/80`, `cy=(Y+1900)/80` (inferred). The squad starts at (-6550,-1430), z 844, which is cell (8.1,5.9).

### Objectives and markers
- `cargo_elevator_objective` completes on the lift button. `ExitZone` (asw_objective_escape) is at (66.7,111.5); its trigger_multiple is at (66.0,108.7)-(72.2,111.7).
- `marker_cargo_elevator` is never enabled.
- Line cues: co_m1_ob7 plays at the double door, co_m1_ob3 at ride end +4 s, and co_m1_ob8 on Insane only (NPC-flag trigger at (53.2,111.8)).
- The 4 objectives in the port are invented.

### Route-ordered encounter table
| # | Area | Trigger (cell rect, z) | Fires |
|---|---|---|---|
| 1 | start | (3.4,7.2)-(12.0,7.8) z896 | general hint |
| 2 | double door | (3.4,8.0)-(12.2,8.4) z952 | train_ele_bigdoor_L2/R2.Open, commander choreo (co_m1_ob7) |
| 3 | orange tank hall | (3.6,14.1)-(13.2,14.5) z952 | tankroom_01 x5 (catwalk z896 and floor z832), ins_boomer_spawn |
| 4 | tank hall | (3.6,23.9)-(13.2,24.3) z952 | tankroom_02: (9.3,12.6) n=12 and (11.4,16.8). They are behind the squad. |
| 5 | tank hall end | (3.5,27.4)-(13.1,27.8) z952 | tankroom_03 at (21.3,34), breakdoor_spawn at (25.0,34.5) (one copy MinSkill 1), ins_ranger_spawn |
| 6 | east hallway | (18.0,32.3)-(19.2,36.7) z888 | hallway_spawn_01 at (31.4,38.1) |
| 7 | east hallway | (23.4,36.2)-(26.6,37.4) z904 | hallway_spawn_02 at (25.0,29.0), MinSkill 1 |
| 8 | LandingBayDoor11 (24.9,43.6) | button area (26.2,43.2) | plain open button, autoopen=1 |
| 9 | north corridor | (21.9,50.1)-(26.7,50.3) z904 | SlomoSpawn1. The copy at (25.9,29.1) has n=20 and chases from behind. |
| 10 | shaft | ElevatorShaftTrigger (21.8,45.4)-(27.0,56.6), fired by barrels at (25,58.3) | ElevatorFireSystem start +2.7 / stop +5.5; explosions; shake; ElevatorFireGlass breaks; track_light climbs cp1..cp18 |
| 11 | gallery entry | (24.7,59.6)-(27.1,60.0) z926 | GlassExplosion1, GlassShooter4, ins_har_spawn |
| 12 | gallery | (24.8,61.1)-(27.2,61.4) z888 | WindowSpawner1 (+0.4, forced), SlomoSpawn2 |
| 13 | gallery | 6 trigger_asw_chance strips at y 60.5-68.6 z926, chance 0.4 each | WindowSpawner2-7: east x 30.4 (y 63.6, 66.8, 70.0) and west x 21.5 (y 69.5, 66.2, 63.2) |
| 14 | gallery | NPC-only strips at x 27.4-28.3 / 23.7-24.6 | Glass2-8.Break +0.4 when aliens cross |
| 15 | gallery | (24.6,64.8)-(27.2,65.1) and (24.6,68.0)-(27.2,68.4) | SlomoSpawn3, SlomoSpawn4. The burrow rooms at (21,78) and (19,73.5) have Hard+ copies. |
| 16 | ramp room 1 | (18.8,81.2)-(25.2,81.6) z929 | ramp_room_spawn_01, ins_ranger2_spawn |
| 17 | pipe puzzle | pipe_impact trigger (24.1,88.4) z882; triggerContainerRiddle (21.6,88.7) z802 | Stumble_trigger, MetalPlatform.DisableMotion +2, GapLinkers.TurnOn +2.2. Pit trigger_hurt at (21.0,86.5)-(23.6,89.1) z692. |
| 18 | ramp room 2 | (18.8,92.1)-(25.2,92.5) z928 | ramp_room_spawn_02: one copy is infinite (13.9,90.9); the others are vent burrowers |
| 19 | LandingBayDoor10 (22.1,104.2) z802 | button (23.2,104.0) | |
| 20 | outdoor yard | | supply cache: 2 medkits, autogun ammo, ammo drop |
| 21 | lift | trigger_lift_button (45.9,114.0) z839 | see the ride timeline |
| 22 | exit | (52.8,109.7)-(53.7,113.9) z872 | ins_drone_spawn x10, co_m1_ob8 |

- **Gallery:** it spans X -5244..-5011, Y 2862..3762, which is cells (24.6..27.4, 59.5..70.8). It has panes on both sides. Two `SpawnerState 0` spawners at (26.0,63.1) and (26.1,66.2), with n=4 each, put 8 drones inside at map start.
- **Dead spawners:** Spawn14 and RandomSpawn2 x4 are never started (inferred from the reverse index).

### Lift and ride (relay timeline from the button)
- **Start conditions:** `trigger_lift_marine_check` has playersrequired=4. On failure it fires `msg_lift_deny`: an asw_info_message with `#asw_landingbay_lift1`, the ASWComputer.AccessDenied sound and image LandingBayLift.
- **Relay timeline after the button:**
  - 0 s: ramp closes
  - 1 s: start sound
  - 2 s: shake 4 for 1 s, plus dust
  - 3 s: FreightElevatorWalls start at 25 u/s; top light off, red spin light 0 on
  - 4 s: elevatorMusic
  - 15 s: camera and spawn timers
  - 16 s: slomo for 16 s
  - 17 s: Insane parasites
- **Path events** (measured from when the walls start):
  - 13.8 s: start1, ins_para3
  - 37.3 s: start3
  - 60.4 s: start4; para2 at +5
  - 79.8 s: start5; crawlers off
  - 106.2 s: end. Sounds stop, shake 12 for 2 s, exit lights chase, ExitSpawner and para4 start, ramp opens at +1, co_m1_ob3 at +4, groups stop at +5.
- **Wall path:** elevator_walls_start is at (45.9,133.8) z-1214 and elevator_walls_end at (45.9,111.9) z778. That is dz 1992 and dy 1752, so the walls slide diagonally. The path is about 2653 u long, which matches 2655. So the shaft is inclined at about 41 degrees (inferred). The port should show slanted wall motion, not a pure vertical scroll.
- **Jumpers:** `timer_elevator_spawn` fires every 2-3.5 s → `case_elevator_spawn` PickRandom over 8 groups. These are 16 drone_jumper spawners at (42.8-49.1, 109.9-114.0): infinite, 1 live, interval 1.5.
- **Crawlers:** every 1.5-2 s, PickRandomShuffle over 9 env_entity_makers. Each template drone rides `train_drone_climb_*` up at 80 u/s (about 23 s). Its OnPass calls SpawnOneAlien, which drops a real jumper.
- **Exit:** ExitSpawner at (61.0,99.6), (69.9,110.2) and (61.0,98.5), with orders 1 to ElevatorExitTarget (56.9,110.7). The third is infinite at skill 3+. Exit doors and ramp lead about 19 cells across the yard to ExitZone.

### Totals
- **All skills:** 128 drones, 1 infinite drone spawner and 17 infinite jumper spawners.
- **Normal+** adds 11 drones.
- **Hard+** adds 16 drones.
- **Insane** adds 10 drones, 9 parasites, 2 harvesters, 2 rangers, 3 infinite ranger spawners, 2 mortars (one at z -1175 in the shaft) and 1 boomer.

### Doors
- AutoInstance1-LandingBayDoor (3.1,5.4): doortype 2, autoopen 0. This is the start bulkhead.
- AutoInstance1-LandingBayDoor1 at (2.3,33.0) and (35.4,37.8): doortype 2, locked decor.
- LandingBayDoor11 (24.9,43.6): autoopen 1.
- LandingBayDoor10 (22.1,104.2): autoopen 1.
- train_ele_bigdoor_L2/R2 is the double door.
- Lift ramp: func_movelinear Open/Close.

### z plateaus
- Start: 844. Tank hall: floor 832, catwalk 896.
- Hallways: 832-841. Gallery: 880-888.
- Burrow rooms: 808-841. Ramp rooms: 801-810. Puzzle pit: 692.
- Yard: 809. Lift deck: 792-800. Ride walls: -1214 to 778.

### Lighting
- Interior fog (120,90,60). Elevator fog (43,37,32) at 0.9.
- Orange spots in the tank hall. The red spin light is on during the ride, and the exit lights chase at the end.
- Details are in `ents\lb02-atmo.txt`.

## Trigger-model gaps (Objects.galaxy / Mission.galaxy)
`AS_Trigger(x0,y0,x1,y1,once,chance)` plus `AS_TriggerDo(spawn|stop|pick|mission)` cannot express:
- **Timers:** repeating random-interval timers (logic_timer with PickRandom), as used by FirstDoorMover and the elevator spawn timer.
- **Spawner outputs:** OnSpawned, OnAllSpawnedDead and SpawnOneAlien (crawler templates).
- **Activators:** prop, physics and barrel activators (the shaft barrel, the pipe puzzle), filters, and NPC-only triggers (glass, co_m1_ob8).
- **Squad checks:**
  - playersrequired / OnRequirementFailed (the lift check)
  - all-marines-past counters (`asw_marines_past_area`)
- **Spawner state:** SpawnerState 0 (pre-populated rooms).
- **Alien orders:** AlienOrders with an explicit target (ExitSpawner to ElevatorExitTarget).
- **Spawn tuning:** per-spawner NearDistance (512 vs 740; the port uses one global AS_NEAR_DIST of 9.3 cells) and spawn jitter of 20/50 (vs 25 percent in the port).
- **Movers:** func_movelinear Open/Close; path_track OnPass events.
- **Popups and hints:** asw_info_message popups and hint success events.
