# Alien Swarm level survey: Jacob's Rest, 2026-10-24

A gameplay survey of the original game's campaign. Jacob's Rest is the game's only campaign: seven missions on the SynTek colony on Vereon XII. For each mission it gives the main feature, what makes it interesting, and what else is unique about it.

**Sources:**
- The installed maps' entity lumps (objectives, spawners, hack panels, set-piece I/O), read with `tools/asbsp.py`.
- `resource/campaigns/jacob.txt` for briefings and threat levels, and `swarm_english.txt` for objective text.
- The SDK's alien class table (`asw_spawn_manager.cpp`) for spawner types.
- Landing Bay and Cargo Elevator were also played (`AS-REFERENCE.md`).
- Web sources had little mission-level detail. The SDA speedrun notes were used only where they match the maps; they seem to come from Reactive Drop.

**Alien counts** are the maps' spawner totals: "all skills" means MinSkillLevel 1 or lower, and Insane means MinSkillLevel 4. The Onslaught director adds wanderers on top of these. Infinite spawners are counted as spawners, not aliens.

## The arc at a glance

| # | Mission | Threat | Core verb | New threat introduced (all skills) |
|---|---|---|---|---|
| 1 | Landing Bay | 1 | Hack doors, download data | Drones, jumpers |
| 2 | Cargo Elevator | 1 | Ride the lift and survive | Wall-crawling drone waves |
| 3 | Deima Surface Bridge | 2 | Hold the gate, blow the pipeline | Rangers, shieldbug |
| 4 | Rydberg Reactor | 3 | Long hack holdout, restore power | Boomers, buzzers |
| 5 | SynTek Residential | 3 | Hunt eggs, burn biomass | Parasites, grubs |
| 6 | Sewer Junction B5 | 5 | Collapse a tunnel, kill eggs | Shieldbug pack, mortarbugs |
| 7 | Timor Station | 6 | Escort a warhead, timed escape | Harvesters, everything together |

The campaign teaches one alien type and one objective verb at a time. Threat climbs fastest after Residential: Sewer Junction carries a +2 difficulty modifier, against 0 for the middle missions.

## 1. Landing Bay (`asi-jac1-landingbay_01`)

**Main feature:** a security-locked landing complex that only a Tech can open. You sweep from the dock to the inner perimeter, hack an escape pod's terminal for flight data, and leave by the cargo lift to the north.

**What makes it interesting:**
- **The opening is outdoors at night.** Snowy catwalks over a fogged drop, red alarm light and pink neon set the colony's tone before the first indoor fight.
- **Tech dependence.** The perimeter doors are hack-locked button panels and the flight data is a locked computer, so the squad must protect its Tech (`asw_tech_marine_req`). It is the game's first lesson in escort-the-specialist.
- **Teaches the toolkit.** It has welders (doors can be sealed against the swarm), a sentry pickup with a holographic placement guide, explosive barrels, three PDAs to read, and drones leaping down from ledges (`trigger_asw_jump`).

**Unique:**
- Below Insane it is almost all drones: 108 finite drones from the reachable spawners (`AS-PARITY.md`; the raw entity lump totals about 180, counting spawners off the route), 5 infinite holdout spawners and a few jumpers.
- Insane quietly turns it into a different level: 12 buzzers, 5 harvesters, rangers, 3 infinite ranger spawners, parasites and a boomer at the exit.

## 2. Cargo Elevator (`asi-jac1-landingbay_02`)

**Main feature:** the freight-lift ride. Press the lift button and survive a long (about 106 s), creeping descent while the shaft walls slide past and the swarm pours onto the platform.

**What makes it interesting:**
- **A survival set piece in place of navigation.** The level has only two objectives (activate the lift, reach the exterior).
- **The lift needs all four marines aboard.** Pressing early shows an "access denied" pop-up, so the squad has to regroup first.
- **The ride is choreographed:**
  - The ramp shuts, then come a shake, a dust burst and sparks.
  - The yellow work lights die and red spinners come on.
  - Drones climb down the shaft walls as silhouettes before dropping onto the deck.
  - A slow-motion beat hits as the first wave lands.
- **Physical set pieces before the lift:**
  - A fire shaft where barrels cook off in sequence.
  - A glass observation gallery whose window alcoves may each spawn drones (40% each).
  - A pipe-and-gap puzzle: a barrel blast rolls a huge pipe, which drops a bridge across a lethal pit.

**Unique:**
- 17 infinite jumper spawners fire during the ride, picked by a random timer.
- Below Insane the mission is drones only.
- It ends outdoors, with a supply cache before the lift and a short dash through a snowy yard.

## 3. Deima Surface Bridge (`asi-jac2-deima`)

**Main feature:** the colony surface in a night snowstorm. You cross catwalks over a chasm, blow up the infested pipeline the swarm is using to get in, and cross the drawbridge to the reactor.

**What makes it interesting:**
- **The first real holdout.** Hacking the gate's locked drawer panel starts holdout spawners and music. Windows shatter as aliens break in, and on Insane boomers join.
- **The drawbridge.** Its button runs the ramps out over the gap and switches on a `point_camera` aimed at the bridge for 6 s. That entity feeds a monitor texture, so it is probably not a cut of the player's view. Drones then climb up over the bridge railings (`ACT_CLIMB_OFF_RAIL`) at random points, so attacks come from the drop, not from corridors.
- **Demolition objective.** You plant charges with a detonator panel to destroy the pipeline. The wreckage reshapes the route.
- **Extraction by air.** The dropship flies in with mounted guns over the last gap.

**Unique:**
- First mission with **rangers** (22 finite plus 4 infinite) and a **shieldbug** on every skill level. Both force the squad out of "everyone faces forward and holds the trigger".
- 19 infinite drone spawners, the most so far.
- A jump-jet pickup.
- No parasites on any skill.

## 4. Rydberg Reactor (`asi-jac3-rydberg`)

**Main feature:** a power plant lit sodium orange. You fight north to reactor control, break into it, bring the reactor online, and sweep to the north exit.

**What makes it interesting:**
- **The campaign's big hack.** The reactor control door's wire puzzle is 3×6 with 3 wires, against 2×5 with 2 or 3 elsewhere. The map sets its `hacklevel` to 25, but the shipped code ignores that key: its keyfield is commented out in `asw_button_area.cpp`, so every panel uses 6. While the Tech works, a timer fires every 2.5 to 5.5 s, picking one of three groups (drones over the railings or out of the wall), and rangers come once. After the door opens, a second timer keeps it up every 4 to 7 s until the squad is inside. It is the clearest "defend the hacker" moment in the game.
- **Power changes the map.** Turning the reactor on switches the plant's lights and wakes new spawners behind you. The airlock door then triggers three staggered door holdouts.
- **A slow exit.** The north doors take their time to open while boomers pour out of a hole (`boomer_hole_spawn`).
- **Hazards and tools:**
  - Fall pits (`asw_trigger_fall`).
  - A remote-controlled security turret.
  - Flamer, chainsaw and fire extinguisher pickups.
  - Explosive barrels.

**Unique:**
- First mission with **boomers** (20 finite plus an infinite spawner) and **buzzers** (12 infinite spawners) below Insane. Boomers punish close-range packs, and buzzers come in the air over cover.
- Heights matter: reactor control is raised and the turbine hall is a step down.

## 5. SynTek Residential (`asi-jac4-residential`)

**Main feature:** an infestation-cleansing mission. You destroy all the swarm eggs and burn all the biomass in a housing block and its mall, then leave by the elevators.

**What makes it interesting:**
- **The objectives are a hunt, not a route.** 30 eggs and 8 biomass growths are spread through offices, the mall and the ventilation ducts ("eggs gather round warm-air sources"). The map shows markers, but you have to sweep it.
- **Fire is mandatory.** The mission requires a flamer in the loadout (`asw_equip_req`), because biomass only dies to heat. Flamer ammo and five fire extinguishers are placed, for when you set your own squad alight.
- **Biomass blocks the way.** Burning certain growths opens blocked paths and sets off new spawns in the mall.
- **The vents fight back.**
  - Burrowed rangers and drones burst out of vents, blowing grates off.
  - Once you are in the ducts, a timer spawns a parasite from one of three vents every 8 s.
- **The elevator stays dead until both objectives are done.** Then it powers up with a bell and a light countdown, and mortarbugs wait by the exit.

**Unique:**
- First mission with **parasites on all skills** (eggs hatch them) and **grubs**: 21 grubs plus 9 grub sacs.
- On Insane, 42 infinite xenomite spawners and 15 infinite parasite spawners.
- A sweeping red laser-scanner light at the entrance.
- 45 breakable windows and panes of glass, some of them used for ambushes.
- The tightest, most claustrophobic spaces in the campaign.

## 6. Sewer Junction B5 (`asi-jac6-sewerjunction`)

**Main feature:** dark, wet sewers. You seal a maintenance tunnel the swarm is using by collapsing it, destroy all the eggs, then escape through a breach in the water processing plant.

**What makes it interesting:**
- **Environmental demolition.** You seal the tunnel by shooting out its four supports. That collapses the tunnel in slow motion, crushes its biomass and stops the buzzer spawns.
- **Physics set pieces:**
  - **The I-beam:** shoot loose a shelf and an I-beam hung on cables swings free, with another slow-motion beat. It smashes a wall, freeing a container and sewer bars to open the way.
  - **The turbine:** a turbine works as a meat grinder that blocks a passage until its control housing is knocked loose. That jams the motor and opens the route.
- **The shieldbug fights.** Six shieldbugs are placed, more than any other map. One encounter sits over four big holes in the floor, so thrown or deployed items fall through. Two more guard the end. (The wiki lists killing them as optional.)

**Unique:**
- The biggest difficulty jump: +2 modifier and threat 5.
- Mortarbugs on every skill, 21 jumpers and 20 eggs.
- A radioactive barrel among 11 explosive ones.
- The most varied weapon pickups in the campaign: rifle, shotgun, PDW, chainsaw, and ammo for several guns.

## 7. Timor Station (`asi-jac7-timorstation`)

**Main feature:** the finale in the colony's mine, where the swarm is breeding. You find a warhead, power the cable railway that carries it to the breeding chamber, detonate it, and escape to the Bloodhound before the countdown runs out.

**What makes it interesting:**
- **Mining lasers and breakable rock.** Three mining-laser pickups cut through 12 breakable rock formations (`asw_prop_laserable`). Some rocks open barricades and others open alternate links, so you choose your route by digging.
- **An escort that doesn't walk.** The warhead rides a rail mover and stops at biomass in its path. An alarm sounds and a warning light flashes until the squad burns the growth and it moves on.
- **The bridge.** A console extends a bridge, then its gates crawl open for about 20 s under pressure. Harvesters wait on it.
- **The finale:**
  - Detonating the warhead starts a **140-second countdown** and rocks start falling.
  - The squad has to reach the southeast loading dock, where the dropship lands with mounted turrets.
  - If the countdown runs out, the mission fails with a screen shake and a white-out.

**Unique:**
- The only timed objective in the campaign.
- Every alien type appears on normal skills, including **harvesters** (7 spawners plus 5 placed), 24 parasites and 33 eggs.
- Insane adds about 50 more drones, 17 rangers, 24 parasites and 4 infinite ranger spawners.
- A blink pack and jump jets are placed.
- It only unlocks after every other mission is done.

## In the SC2 port (checked 2026-10-24)

Missions 1 to 4 against the port's level modules (`tools/landingbay.py`, `cargo.py`, `deima.py`, `rydberg.py`) and `src/Mission.galaxy`. This was checked by reading the code, not by playing.

Updated the same day after items 1 to 5 and 7 of the ranking were built. The map builds and passes the type and bounds checks; none of it has been played in the client yet.

### Landing Bay: present, with two gaps

| Survey detail | Port |
|---|---|
| Night outdoor dock: snow, fogged drop, railings, red alarm, pink neon | Yes (`OUTDOORS`, lights, `AS_SnowPulse`, drop and railings) |
| Hack-locked gate panels; a Tech is required | Yes: two alternative panels; `as_needTech`, and the mission restarts with no live Tech |
| Flight data download from the escape pod's computer | Yes (`COMPUTER_HACK` 4/7/0.5/15 s) |
| Welders and weldable doors | Yes: 2 welders, weld hints, pre-sealed tank doors |
| Sentry pickup and holo sentry spot | Yes (`SENTRY_SPOT`) |
| Explosive barrels, 3 PDAs, sleeping drones | Yes |
| Drones leaping down from ledges (3 × `trigger_asw_jump`) | Yes: `JUMPS` (`AS_JumpLink`); an awake drone in the box leaps to the target when a marine is far enough off |
| Spawner mix by skill, including Insane's buzzers, harvesters, rangers, parasites and boomer | Yes, row for row. One Insane-only infinite spawner (`RandomParasiteSpawn5`, a drone despite its name) is not in the port; probably off the route |

### Cargo Elevator: rebuilt from the map

`tools/cargo.py` is now traced from `asi-jac1-landingbay_02` (80×124 cells, real heights) and runs on the same data-driven mission code as Deima and Rydberg. The hack, the hive lower level, the transit hold and the invented surge are gone.

| Survey detail | Port |
|---|---|
| Lift ride, about 106 s, walls moving instead of the platform | Yes: about 100 s, scrolling shaft walls |
| Whole squad aboard to start | Yes: every living marine, with a 5 s countdown. AS wants exactly 4 marines (`playersrequired 4`) |
| "Access denied" pop-up when pressed early | **Missing**. The port shows a text line instead |
| Ramp shuts, dust burst, sparks, yellow lights out, red spinners | Yes |
| Drones climbing down the shaft walls, slow-motion beat on the first landing | Yes |
| Ride spawns: drones only (17 infinite jumper spawners plus crawlers) | Yes: `timer_elevator_spawn` (2 to 3.5 s) picks one of the 8 jumper groups; `timer_elevator_crawlers_1` (1.5 to 2 s) sends crawlers down the walls; parasites on Insane from the path_track marks |
| Drones only below Insane | Yes: every spawner is traced. Below Insane there are only drones and jumpers; Insane adds rangers, parasites, harvesters, a boomer and a mortar |
| Fire shaft where barrels cook off in sequence | Yes: shooting the barrel at the corridor's top arms `ElevatorShaftTrigger`: four blasts down the shaft, then the glass box blows out |
| Glass gallery: 7 alcoves, 40% chance each | Yes: a 40% trigger per walkway strip; the panes shatter as their drones come through |
| Pipe-and-gap puzzle (a barrel rolls a pipe, which drops a bridge) | **Partly**: the barrel stops the Insane rangers (`ins_ranger2_spawn`) as in AS, but no pipe falls and the way across never depends on it |
| Supply cache, then a short outdoor snowy exit beside the shaft | **Partly**: the cache's ammo is in the lobby and the exit is traced, but the exit is drawn indoors, with no snow |

### Deima Surface Bridge: traced, mostly present

| Survey detail | Port |
|---|---|
| Night snowstorm, chasm, catwalks, lightning | Yes (`OUTDOORS`, `SNOW_ROOFS`, lightning timer) |
| Gate hack starts a holdout | Yes (`holdout_spawn`, the Insane boomer) |
| Music during the gate hack; two windows shattering 5 and 8 s after it | Yes: a stinger and a battle loop from the hack until 20 s after it, and the two panes shatter at 5 and 8 s; the window spawners break theirs too |
| Bridge ramp button, pipeline detonation, wreckage cleared, shieldbug waking | Yes |
| Drones climbing up over the bridge railings (`ACT_CLIMB_OFF_RAIL`) | Yes: a spawner whose drone starts burrowed with a climb or jump activity now brings it in from behind (`AS_AlienEnter`): up over the rail, out of or down a wall, or a leap in |
| Dropship with guns, crossing on her back | Yes: a stand-in model on path nodes, guns scripted |
| Rangers and shieldbug on all skills, 19 infinite drone spawners, no parasites | Yes: every spawner is traced from the map |
| Jump-jet pickup | **Missing**. The port has no jump-jet item |
| 2 × `trigger_asw_jump` | **Partly**: the jump across the gap is in; the forced jump south is left out (its target is off the deck) |

### Rydberg Reactor: traced, but its signature holdout is thin

| Survey detail | Port |
|---|---|
| Sodium-orange plant; heights 608/544/760; fall pits | Yes |
| Reactor door's 3×6, 3-wire puzzle; Tech required | Yes (`PANEL_WIRES (3, 6, 3)`, `NEEDS_TECH`) |
| During the hack, a timer every 2.5 to 5.5 s picks a railing or wall drone group | Yes: `reactor_holdout_choreo_timer` picks `spawn_group_01` to `03` |
| After the hack, a timer every 4 to 7 s until the squad is inside | Yes: `reactor_holdout_choreo_timer2` sends the buzzers from left or right until the squad steps inside |
| Reactor panel turns the lights to power restored and wakes the spawners behind | Yes |
| Airlock door holdouts; slow north doors with boomers from the hole | Yes. The doors open after a fixed 32 s |
| Boomers and buzzers on all skills | Yes (traced spawners) |
| Remote-controlled security turret | **Missing** |
| Flamer, chainsaw, fire extinguisher, medkit, jump jets, 4 rifle-ammo pickups | **Partly**: flamer, chainsaw, sentry, medkit and the 4 ammo spots are placed. The jump jets and extinguisher have no port item |
| 1 × `trigger_asw_jump` | Yes |

### Ranked by how much they change play

Status after the 2026-10-24 build is in brackets.


1. **Cargo Elevator's level outside the lift.** Everything except the ride: the fire shaft, the gallery's chances, the pipe puzzle, the outdoor exit, and drones only below Insane. This is the Phase 6 rebuild already planned. [Built, apart from the falling pipe and the outdoor exit.]
2. **Rydberg's hack holdout timers.** It takes two random timers plus railing and wall spawn groups, and without them the campaign's big "defend the hacker" moment is quiet. The trigger model already has `TIMERS` and `pick`, so this is data work in `tools/rydberg.py`. [Built.]
3. **Map pickups.** Flamer, chainsaw and extinguisher items exist in the port but can't be placed (`AS_LevelPickup`). Jump jets and the remote turret don't exist at all. [Placeable now, and placed in Rydberg. Jump jets, the extinguisher and the turret are still missing.]
4. **Alien jump links** (`trigger_asw_jump`) in Landing Bay, Deima and Rydberg. [Built, except Deima's forced jump.]
5. **Small staging:** Deima's hack music and breaking windows; drones climbing over the bridge railings; Cargo Elevator's access-denied pop-up and the 4-marine rule. [The first three are built; the pop-up and the 4-marine rule are not.]

## Also installed

- **`asi-jac1-landingbay_pract`:** a practice copy of Landing Bay for offline training. It is not a campaign mission.
- **`lobby`:** the menu backdrop.
