# Alien Swarm Landing Bay / Cargo Elevator: geometry extracted from the BSPs, against the SC2 port

Sources: `asi-jac1-landingbay_01.bsp` (LB01, Landing Bay) and `asi-jac1-landingbay_02.bsp` (LB02, Cargo Elevator). Both are VBSP version 21. Struct layouts come from `AlienSwarm/src/public/bspfile.h` and `gamebspfile.h`: face 56 B, texinfo 72 B, dispinfo 176 B, dworldlight_t v1 100 B, static props v9 72 B.

Scripts and outputs are in a session scratch folder that is not kept; the images and grids are copied beside this file:
- **Scripts:**
  - `bsp.py`: the reader.
  - `analyze.py`: floors, plateaus, ramps, drops, walls, materials, lights.
  - `compare.py`: walkable flood, rooms, port fit and overlay, ASCII grids.
  - `extra.py` and `extra2.py`: stair props, named lights, the shaft, tool flags.
- **Text dumps:** `lb0X-analysis.txt` and `lb0X-compare.txt`.
- **Images, at 16 u per px with axes in Hammer units:**
  - `lb01-heights.png` and `lb02-heights.png`: floor z, colour-coded, with a legend and plateau ids.
  - `lb01-floor.png` and `lb02-floor.png`: up-facing floor. Ledges are red, ramp boxes cyan, spawns green.
  - `lb01-walkable.png` and `lb02-walkable.png`: grey is floor reached from the nav nodes; dark is floor that is not.
  - `lb01-overlay.png`: the real walkable floor with the port's AREAS, port doors and AS doors drawn on it.

Method:
- A **floor** is a drawable face with normal z above 0.7, in model 0 or in a solid func_* model (origin applied), plus displacement quads.
- **Walkable floor** is flooded from 798 (LB01) and 545 (LB02) info_node, marine-hint, player-start and spawner seeds. A flood step may rise at most 20 u, or 56 u inside a ramp or stair box.
- **Plateaus** are connected floor within ±12 u.
- I mark inferences with *(inferred)*.

## Summary

| Aspect | AS Landing Bay | AS Cargo Elevator | Port | Delta |
|---|---|---|---|---|
| Walkable floor | 1,984 cells of 80 u (12.7 M u²); bbox x −8576..−4368, y −9216..1312 (52×132 cells) | 1,806 cells; bbox x −7040..−960, y −1840..8960 (76×135 cells) | LB: 2,118 cells of AREAS on 64×144. CE: 3,910 cells of AREAS on 128×112 | LB med, CE **high** |
| Elevation of the playable route | z 792..1024. Main levels: 944 dock and yard, 872 inner perimeter, 904 tank room, 832 north block, 1024 gate balcony, 952 raised pump-room deck, 792 crew office | z 792..878. Start and gallery 832, pipe hall, lobby and exit 800, lift platform 792, window alcoves 870 | One flat terrain, FLOOR 8.0 | med (steps of 40–80 u, about 1 cell, flattened) |
| Off-route depth | Pits and drops 264–3,850 u: 680 orange pit, 416 yard, 24/−64 hangar, −2000, −2904, black world floor at −3072 | 416 lower bay under the start catwalk; 24 pit under the start; lift drop faked by moving walls 2,656 u long, z +1,992 | Painted drop (`AS_OPEN`), railings | **high** for looks (port paints it) |
| Ramps and stairs | 4 walkable brush ramps (18.6° and 3× 22.6° bridges). 16 stair props (stairs01_128 ×10, _64 ×6) bridge 40–88 u | 2 elevator_landingbay_ramp props at the platform; 3 stair props; steps of about 32 u | Ramps and stairs are named areas only | med |
| Wall height | Median 192 u above floor (39% of edge in 192..224). 192 u = 2.4 cells of 80 | Median 192 (36% in 192..224) | WALL_H 2.5 cells = 200 u | **low** (matches) |
| Ceilings | None over any walkable floor (0.0%). Overhead is static pipes at about 130–200 u, scaffold beams at 120–136, catwalks at +176 | None except the shaft bottom | Overhead girders above walls, no ceilings | low |
| Wall tops and void | Wall tops capped with TOOLSNOLIGHT (unlit black) at about z 1000–1152; world floor TOOLSNOLIGHT at z −3072; sky shell at z 2112; no 3D skybox | Same; sky shell at z 3136 | Near-black hull tops, painted drop | low |
| Outdoors / snow | **Three** exterior fog and snow zones: dock to yard; a pocket south of the crew office; the whole north block (concourse, freight office, flight control) | Lobby west of the lift, the exit bay, the start | LB `OUTDOORS` covers dock to yard only; CE has none | **med-high** |
| Floor materials | concretefloor050a 32%, snowy concrete 14%, metalfloor011a 7%, metal blend 7%, grate013a 7%, grate012b 6% | concretefloor050a 45%, metalfloor011a 16%, snowy concrete 13% | Concrete and grating mix | low-med |
| Light colours | 105 lights (62 light, 43 light_spot), 124 HDR worldlights. Mostly cold 174,198,194; warm 223,206,149 floods outdoors; 7 orange 247,134,60 (mostly the z 680 pit and annex); green booth; 105 red glow sprites | 61 lights, 64 worldlights. Cold 174,198,194; yellow lift spots 249,192,0; 5 red spinners 249,0,0; 6 white b12 shaft lamps; 10 sprites 200,47,2 | Per-area preset kinds | med (orange is in the wrong room) |
| Fog | exterior 39,53,86 (256..4000, max 0.5); interior 120,90,60 (256..6000, 0.5); elevator 43,37,32 (256..4000, 0.9) | Same three controllers | Painted haze | low (already known) |
| Cargo lift | n/a | Platform 560×528 u = 7.0×6.6 cells of 80 at z 792. Shaft about 13 cells across. Exit bay directly east, about 21 cells from the platform | LIFT 12×12 cells, VOID 16×16; exit 60+ cells away, past an invented "lower level" | **high** |

## 1. Bounds and materials

**World model bounds:**
- LB01: (−9344, −10432, −3200) .. (−896, 10608, 2240).
- LB02: (−9344, −10432, −3200) .. (−336, 10608, 3264).

The bounds are mostly the sky shell. Drawn geometry spans:
- LB01: x −9472..−1536, y −10496..2816.
- LB02: x −8192..0, y −4096..10752.

LB02's start (z 832, around −6550, −1400) is LB01's escape lift (−4896, 944) moved by about (−1650, −2340). The hangar pit at z 24, 1760×1536, sits below both. *(inferred: the same instance)*

**Tools** (geometry models only; areas are of all faces):

| Material | LB01 faces / area | LB02 faces / area | Note |
|---|---|---|---|
| TOOLS/TOOLSSKYBOX (flags 0x404) | 229 / 393 M u² | 229 / 436 M u² | Sky shell only; ceiling at z 2112 (LB01) or 3136 (LB02). skyname `sky_day02_07_hdr`. **No sky_camera, so no 3D skybox.** |
| TOOLS/TOOLSNOLIGHT (flags 0x400, drawn, unlit = black) | 775 / 364 M | 651 / 309 M | Bottom of the world at z −3072, and caps on top of the walls (up-faces at z 1000–1152). This is AS's "black beyond the playable space". |
| TOOLS/TOOLSBLACK | 12 / 0.05 M | 22 / 9.8 M | Small black patches at floor level, 793–964 |
| TOOLS/TOOLSTRIGGER | 359 | 276 | Trigger brushes (not geometry) |

No nodraw, clip or playerclip faces survive in the face lump. There are no fog materials.

**Floors by area of up-facing faces:**
- **LB01:**
  - concretefloor050a: 11.4 M u², 325 faces.
  - blendconcsnow001a: 3.6 M, snowy concrete displacement blend.
  - metalfloor011a: 1.6 M.
  - metalgrate012a: 1.0 M.
  - metalgrate013a: 0.88 M.
  - blendmetalmetal001a: 0.80 M.
  - metalfloor012a: 0.74 M.
  - metalgrate012b: 0.74 M.
  - blendmetalsnow001a: 0.67 M.
  - greymetalfloor: 0.24 M.
  - concrete_crack001a: 0.25 M.
  - metaldoor059a and metaldoor030b used as floor plate: 3.9 M and 0.56 M.
- **LB02:**
  - concretefloor050a: 15.0 M.
  - metalfloor011a: 3.8 M.
  - snowy concrete: 1.6 M.
  - metalgrate012a and metalgrate013a: about 0.5 M each.
  - metalfloor011c: 0.4 M.
  - metalfloor012a: 0.5 M.
  - swarm_glassdistortion: 0.47 M, the fire-shaft glass.

**Walls:**
- **LB01:**
  - concretewall080a: 43.8 M vertical.
  - concretewall081a: 15.6 M.
  - concretewall081c: 5.9 M.
  - concretewall080b and 080c: 1.7 M each.
  - **nature/snowwall006b**: 49.9 M. These are vertical displacement cliffs from z −2976 to 1134 round the exterior.
- **LB02:** concretewall080a 25.7 M, 081a 16.1 M, 081c 12.9 M, metalwall061f 4.3 M (the shaft), snowwall006b 24.9 M.

Dev textures (graygrid, measure) appear on a hidden box at z 576–640, and there is a sealed room at z 1152 (x −2560..−2032, y −3600..−3072) with a green light. *(inferred: a briefing or camera box, not playable)*

**Displacements:**
- LB01 has 44, LB02 has 37.
- All horizontal ones are perfectly flat (z min = z max). They are used only for blending snow, concrete and metal textures: dock 944, north block 832, flight control 872, tank room metal 904, office 792/871.
- The vertical ones are the 4,000 u snow cliffs.
- **None are terrain.**

## 2. Floor heights

### Walkable area by z (8 u bins)

| z | LB01 cells (80 u) | % | LB02 cells | % |
|---|---|---|---|---|
| 776 | – | – | 76 (lift south apron, part of the moving walls *(inferred)*) | 4.2 |
| 792 | 33 (crew office) | 1.7 | 55 (lift platform) | 3.1 |
| 800 | – | – | 799 (pipe hall, lobby, exit bay) | 44.2 |
| 832 | 674 (north block) | 34.0 | 759 (start, west hall, gallery) | 42.0 |
| 848 | 31 (supply strip) | 1.6 | – | – |
| 864–870 | – | – | 65 (window alcoves) | 3.6 |
| 872 | 497 (inner perimeter) | 25.0 | – | – |
| 904 | 242 (tank room) | 12.2 | – | – |
| 944 | 343 (dock, yard, gate) | 17.3 | – | – |
| 952 | 25 (raised pump deck, storage platform) | 1.3 | – | – |
| 1024 | 55 (gate balcony) | 2.8 | – | – |

Counting all up-facing floor, walkable or not: LB01 has 4,890 cells and LB02 4,726. Only about 40% of that floor is reachable; the rest is decorative depth. Histograms are in the `# FLOOR AREA BY Z` sections of the analysis files.

### Landing Bay plateaus

Room names come from the port's names through the fit in §5 and from entities.

| Plateau | z | Cells (80 u) | Bbox x / y | Room | Walkable |
|---|---|---|---|---|---|
| 87 | 944 | 335 | −8112..−4368 / −9216..−5392 | Dock, walkway, south lane, freight yard, security gate (BloodhoundSteam, FirstDoorMover) | yes |
| 122 | 928 | 9 | −4960..−4688 / −9040..−8832 | Spawn pad: all 9 info_player_start, rot_light | yes |
| 84 | **1024** | 49 | −6992..−6592 / −6176..−5152 | Gate **west balcony**: LandingBayDoor2, Start_button_right1. Port treats it as flat. | yes |
| 52 | 872 | 436 | −8064..−5232 / −5456..−2992 | Inner storage, annex, maintenance hall, pump room, east hall (FirstEncounterSpawn2, jump targets, TargetBalcony) | yes |
| 62 | 952 | 40 | −7584..−7104 / −4448..−3792 | Raised west pump deck: WeldDoor3 at z 952, Storage_room_spawner | yes |
| 83 | 952 | 10 | −7360..−7104 / −5408..−5152 | Raised storage platform *(inferred)* | yes |
| 58 | 792 | 37 | −8112..−7776 / −4544..−3472 | Crew office (Spawn04, a computer, InstanceAuto44 door). 80 u below. | yes |
| 43 | 848 | 30 | −6848..−6624 / −3216..−2320 | Supply-room strip (welder, barrel) | yes |
| 34 | 904 | 255 | −8208..−6544 / −3216..−1280 | Tank room (tankroom spawns, welder, WallBurst) | yes |
| 29 | 904 | 11 | −8192..−8000 / −1248..−864 | WallBurst nook | yes |
| 3 | 832 | 676 | −8576..−4592 / −1568..1280 | North block: stair hall, junction, booth, west rooms, concourse, offices, exit passage, escape lift (ExitZone, marker_exit, holdout spawns) | yes |
| 2 | 872 | 54 | −6784..−6320 / 464..1312 | **Flight control island**: computer area, holo sentry, cam1 | yes |
| 81, 88, 97, 85 | 680 | 175 + 43 + 26 + 11 | −7360..−5488 / −6672..−4896 | Pit beside the gate and storage, 264 u down, **orange-lit** (247,134,60 ×2, b250) | no |
| 99, 101 | 416 / 448 | 57 + 25 | −7680..−6880 / −8208..−7488 | Lower yard west of the freight yard, 528 u down | no |
| 4, 1 | 24 / −64 | 334 + 264 | −6048..−3568 / −256..2448 | Hangar pit east and north of the escape lift (800–900 u down; walls rise 992–1088 above it) | no |
| 126, 98, 100 | −2000 / −1976 | 137 + 9 + 24 | −8768..−5216 / −9792..−7472 | Ground far below the dock catwalks | no |
| 123 | **−2904** | 70 | −4768..−4144 / −9616..−8848 | Lowest drawn floor, under the dropship east of the dock | no |
| 39–45, 26, 12 | 160 / 144 / 312 | about 10 each | in the tank room and north block | Tank pits, 744 deep (tank-room floor 904 down to 160), and drops beside the junction | no |
| 72 | 832 | 33 | −6272..−5488 / −4688..−4416 | Unreachable ledge off the east hall *(inferred)* | no |
| 77, 79 | 1048 | 10 + 10 | over the maintenance hall | Overhead catwalks, 176 above the floor | no |
| 51 | 941 | 25 | −9216..−7104 / −3024..−2944 | A 2,112×80 girder running west into the void *(inferred)* | no |

**Connections along the real route.** Real floor z at the port's ROUTE waypoints:

| Leg | Real z | Real connection |
|---|---|---|
| Dock, walkway, south lane, yard, gate | 944 | Flat |
| West gate door | 1024 | stairs01_128 prop at (−6736, −6288) up to the balcony. The east door is at 944. |
| Gate to inner storage | 944 → 872 (down 72) | Through the doors; stairs01_128 props at (−6328, −5264), (−7236, −5024), (−7112, −5208) |
| Storage, maintenance hall, pump room | 872 | Flat. The west pump deck is at 952, reached by stair props at (−7366, −3672) and (−7272, −3920). The west weld door sits at 960, the east one at 872. |
| Crew office | 792 | Stair props at (−7944, −4416) and (−8052, −3760) |
| Supply room to tank-room doors | 848 → 904 | **Brush ramp** x −6992..−6848, y −2832..−2704: rise 48, run 144, 18.6°, metalfloor011c. Also stairs01_64 at (−6656, −3152) and (−6744, −2376). |
| Tank room to north stair hall | 904 → 832 (down 72) | stairs01_64 at (−7936, −1424) |
| North block to flight control | 832 → 872 | **Three metal/bridge ramps**, each rise 40, run 96, 22.6°: east (−6368..−6272, 736..864), west (−6848..−6752, 672..800), south (−6592..−6464, 416..512). The island's other edges drop 616 to z 256. |
| Flight control, exit passage, escape lift | 872 → 832 | Flat |

The brush scan found no stairs. Every stair is a static prop: stairs01_128 ×10 and stairs01_64 ×6, listed in `extra.py` output. Other near-vertical "ramps" in the scan (43–69°) are wall trim and the lift frame, not walkable.

**Ledges and drops** (adjacent floor pixels more than 24 u apart, outside ramp boxes; the longest 40 are in `lb01-analysis.txt`):

| Where | Length | From → to | Drop |
|---|---|---|---|
| Gate, storage and annex rim over the orange pit | 10,752 u | 944 → 680 | 264 |
| East rim of the escape lift and exit, over the hangar pit | 5,424 u | 902 → 24 | 878 |
| Tank room over its 6 tank pits | 4,608 u | 904 → 160 | 744 |
| Pump room and office | 5,040 u | 944/952 → 872 | 72 |
| East of the south lane | 2,336 u | 945 → −1976 | 2,921 |
| South edge of the walkway | 448 u | 944 → −2000 | 2,944 |
| Dock edge by the dropship (x −4768..−4688, y −9616..−8848) | 528 u | 928 → −2904 | 3,832 |
| West of the south ramp | 432 u | 926 → 221 | 705 |
| North of the junction | – | 832 → 144 | 688 |
| Flight control island rim | – | 872 → 256 | 616 |

### Cargo Elevator plateaus

| Plateau | z | Cells | Bbox x / y | Room | Walkable |
|---|---|---|---|---|---|
| 46 | 832 | 769 | −7040..−4016 / −1808..4320 | Start pad (6 info_player_start at about −6550, −1430), west catwalk hall, link corridors, security door (LandingBayDoor11 at −5205, 1585), fire-shaft corridor (ElevatorShaftTrigger), observation gallery (glass at x −5246 and −5011, y 2862..3762) | yes |
| 49–56 | 870 | 7 × 8.4–9 | ±384×224 bays either side of the gallery | Window alcoves, 38 u up (WindowSpawner1–7, GlassExplosion) | yes |
| 13 | 800 | 621 | −6144..−3200 / 4176..7744 | Pipe hall (HugePipe, MetalPlatform, Stumble_trigger, SlomoSpawn1) and lift lobby | yes |
| 44 | 878 | 18 | −5280..−4976 / 4720..5264 | MetalPlatform deck in the pipe hall | yes |
| (lift) | 792 | 41 | −3792..−3232 / 6832..7360 | **Lift platform** | yes |
| 33 | 776 | 81 | −4016..−3040 / 6256..6816 | Apron south of the platform; concretewall080a, part of the FreightElevatorWalls model at its start position *(inferred)* | yes |
| 21 | 800 | 234 | −3024..−960 / 5936..7264 | **Exit bay**, outdoors and snowy (ExitZone at −1862, 7022; ElevatorExitTarget; ExitSpawner ×3) | yes |
| 55, 70 | 416 | 1,184 + 181 | −7936..−5616 / −1040..3072 | Huge lower bay under and beside the start catwalk, 416 down, **orange-lit** (247,134,60 ×2) | no |
| 77 | 24 | 334 | −6960..−5200 / −2576..−1040 | Pit under the start pad, as in LB01 | no |
| 10, 6, 2, 1, 15, 17, 18, 8 | 1280 .. −2048 | 12–214 each | x −4080..−3008, y 6784..10304 | Ledges of the moving shaft walls at their start position | no |
| 59 | 1510 | 14 | over the fire shaft | ElevatorFireGlass breakables at z 1428–1509 | no |

**Connections in Cargo Elevator:**
- **Start pad to the gallery:** 832 throughout.
- **Into the pipe hall:** an edge at x −5920..−5552, y 4176..4208 drops 32, to 800.
- **Window alcoves:** 38 u up.
- **Pipe hall to the lobby:** 800, flat.
- **Onto and off the lift:** prop ramps `elevator_landingbay_ramp`, `elevator_ramp_entrance` at x −3841 (west) and `elevator_ramp_exit` at x −3213 (east), both at z 800. The platform is at 792.
- **During the ride:** `clip_elevator_entrance` and `clip_elevator_exit` block both sides. `brush_hide_elevator_start` and `brush_hide_exit` are 208/48×1464×832 boxes that hide each bay.
- **Exit bay:** 800.

**The whole playable route stays within z 792..878.** The descent is entirely the moving walls. `FreightElevatorWalls` (func_tracktrain, 207 faces, bbox at spawn x −4072..−3024, y 6272..10368, z −2112..1280) runs along `elevator_walls_start` (−3528, 8808, −1214) to `elevator_walls_end` (−3528, 7052, 778):
- 2,656 u in all: z +1,992 and y −1,756.
- It travels up and south, towards the camera.
- At AS-REFERENCE's 25 u/s that is 106 s.

Other Cargo Elevator drops:
- The start catwalk's east edge falls 416 to the lower bay (x −7056..−5616, y −1040..992; 3,616 u and 4,208 u of edge).
- The fire shaft beside the gallery corridor: the walkable strip narrows to 1 cell at x −5120..−5040 for y 2240..2800. Shaft walls slope at 60°, down to z −6.
- Exit bay edges drop 615 to z 185.

## 3. What lies beyond the playable floor

Edge classes per plateau are in `# FLOOR EDGES` of the analysis files. "sky" there means no geometry under the edge except the sky shell, which is a drop to the black floor.

- **No 3D skybox** in either map.
- The sky shell is a TOOLSSKYBOX ceiling at z 2112 (LB01) or 3136 (LB02).
- Under every open edge is the unlit black TOOLSNOLIGHT floor at **z −3072**. It is seen through fog_exterior (39,53,86, start 256, end 4000, max density 0.5) or fog_interior. So off-deck reads as dark fog over black, not as sky.
- Wall tops are capped with black TOOLSNOLIGHT, about 192 above each floor (up-faces at 1000–1152).

**LB01 dock (plateau 87, edge 19,584 u):** wall 62%, open drop 19%, drop to lower floor 17%.

Lowest decorative geometry under the dock catwalks:

| Feature | z | Depth below the dock | Location |
|---|---|---|---|
| Lowest drawn floor | −2904 | 3,848 | x −4768..−4144, y −9616..−8848, under the dropship, east of the spawn pad |
| Ground plates | −2000 / −1976 | about 2,920–2,950 | South of the walkway (x −7168..−5216, y −9792..−9344) and east of the lane (x −6208..−5664, y −8896..−7488) |
| Lower yard | 416 / 448 | 528 | West of the freight yard |
| Black world floor | −3072 | about 4,000 | Under everything |

Further decorative detail in the drops:
- **Truss columns:** crossbeam_02 static props, 194 in all. The 42 standing in the drops reach a median of 2,132 u above the local floor, so they are truss columns rising out of the drop.
- **Pipelines:** outside_oilpipeline props.
- **Snow cliffs:** snowwall006b displacements, z −2976..1134, close the exterior on the south, east and north.
- **Railings:** about 300 railing static props (straight_tall_128 ×119, straight_128 ×65, straight_tall_64 ×43, and so on) line the catwalk edges.

The dock and catwalk edges, by position:
- The east edge of the spawn pad and dock at x about −4700 (drop 3,832).
- The south edge of the walkway at y about −9344 (drop 2,944).
- The east edge of the south lane at x about −6200, y −8896..−7488 (drop 2,921).
- The west edge of the south lane at x about −6500, y −8272..−7856 (drop 705, to geometry at 221).

**LB01 elsewhere:**
- The inner perimeter looks onto the z 680 pit (264 down). It is orange-lit.
- The tank room has 6 tank pits (744 down).
- The flight control island stands over a z 256 pit (616 down).
- The escape lift and exit passage border the z 24 / −64 hangar pit (about 800–900 down; its walls stand 992–1088 u tall).

**LB02:**
- The start catwalk overlooks the z 416 lower bay, 1,184 cells big and orange-lit. This is the port's "orange through the grating".
- Under the start pad is the z 24 pit.
- The exit bay is half open drop (49%), to z 185.
- The shaft void round the platform is the moving walls' interior.

## 4. Walls and ceilings

- **Wall top above the adjacent floor:** I measured it on boundary pixels next to vertical faces.
  - LB01: median 192 u. 39% of the edge length is 192..224; 6.5% is 256..288; 7% is 64..96 (rails and low walls).
  - Per plateau: dock 192, inner perimeter 192 (p25 128), tank room 192, north block 192 (p25 160), office 192, balcony 192.
  - LB02: median 192 (36% in 192..224, 13% in 160..192). The gallery alcoves are 96..160.
  - The tall readings are pit and hangar faces: 992–1120 round the hangar pit, 3,100+ round the −2000 floors.
- **Against the port:** 192 u is 2.4 cells of 80 u. The port's WALL_H of 2.5 cells (200 u) **matches**. The port's level cell is 80 u: the fit below gives 79.8 u per cell, and the camera's 412 u is 5.1 cells.
- **Ceilings:** no drawn ceiling over any walkable floor in either map (LB01 0.0%; LB02 0.9%, all at the shaft bottom).
- **Overhead clutter (static props more than 96 u above the local floor):**
  - LB01: pipeset_8 pipe_64 ×112 (median 199 u), pipe_corner ×60 (198), pipe_160 ×50 (128), pipeset_32 straight ×32 (128), outsidesupportbeam2 ×30 (202), scaffold thinbeam64 ×25 (122), cagedlight01 ×20 (138), scaffold crossbeam ×14 (204).
  - LB02: outsidesupportbeam2/2a ×50 (160–204), pipeset_32 ×25 (132–150), ventwall01 ×13 (166), cagedlight01 ×12 (160).
  - There are also the two func_illusionary beams (z 1113–1196) and the overhead catwalks at 1048 over the maintenance hall.
  - Overhead clutter therefore sits at or just below the wall tops. The camera, at pitch 60 and 412 out, is about 357 u above the deck.

## 5. Footprint against the port

### Landing Bay fit

- `info_player_start` mean is (−4936, −8914); `marker_exit` is (−4928, 944).
- Matching them to SPAWN (51.0, 7.5) and the EXTRACT centre (51.5, 131) along y gives **79.82 u per cell**.
- **The port's cell (0, 0) corner is at Hammer (−9007, −9513).** There is no rotation; x is east and y north, as in the port.
- The exit then lands within 32 u (0.4 cell) in x. The port grid, 64×144, covers x −9007..−3898 and y −9513..1982.
- The overlay is `lb01-overlay.png`. The port's rectangles sit on the real rooms closely in the south and middle and diverge in the north.

**Coverage of each port AREA by real walkable floor:**

| Area | Coverage | Real z | Note |
|---|---|---|---|
| Dropship Dock | 51% | 944 | The real dock is L-shaped: about 11×5 cells at rows 9..13 plus a 4-cell stem. The port's 12×11 is about twice as big. |
| Dock Walkway | 56% | 945 | |
| South Ramp | 54% | 945 | Not a ramp; flat at 945, 4 cells wide |
| Freight Yard | 50% | 944 | Real yard about 8×7 cells (cols 27..36, rows 25..31), with 4-wide lanes north and south. Port has 10×17. |
| Security Gate | 66% | 944 | West door is up at 1024 on a balcony |
| Inner Storage | 67% | 873 | 72 below the gate; the z 680 pit takes its east and west margins |
| Storage Annex | 73% | 872 | |
| Maintenance Hall | 91% | 872 | |
| Crew Office | 66% | 797 | Real office at 792, 80 below |
| Pump Room | 98% | 872 | West third raised to 952 |
| Supply Room | 79% | 848–872 | |
| Tank Room | 66% | 904 | The 6 tank pits are holes; the port's BLOCKS are right |
| North Stair | 100% | 832 | |
| Junction | 67% | 832 | |
| Security Booth | 56% | 832 | |
| Spine, West Service Way, West Concourse | 85–100% | 832 | |
| Upper Concourse | 81% | 832 | |
| Freight Office | 48% | 832 | |
| Records Room | 71% | 832 | |
| Flight Control | 75% | 872 | Raised island |
| Control Door, Exit Passage, Exit Door | 53% | 832 | The real passage is 2–4 cells further south (rows 125..130) and wider |
| Escape Lift | 68% | 832 | Real lift area cols 46..55, rows 126..134 |

Totals:
- The union of the port's rectangles is 2,118 cells; 69% of it is real walkable floor.
- **The real walkable floor outside every port rectangle is 518 cells (26%).**

**Where the real map is bigger or different** (port cells):

| Port cells | Real hammer x / y | z | Cells | What it is |
|---|---|---|---|---|
| x 16.8..33.7, y 104..110 | −7664..−6320 / −1200..−720 | 832 | 92 | The "North Stair" is a **wide east–west hall** about 24×6 cells, not a 4-cell stair. It is entered from the tank room down 72 u. |
| x 29.8..47.3, y 66..77.5 | −6624..−5232 / −4240..−3328 | 872 | 91 | An **east hall** running from the pump room and maintenance hall out to x −5232. The port has nothing there. |
| x 7.6..16.8, y 117..133 | −8400..−7664 / −160..1088 | 832 | 88 | A **big west room**, about 9×15 cells, beside the port's narrow West Service Way and West Concourse |
| x 18.8..37.5, y 117..124 | −7504..−6016 / −144..400 | 832 | 77 | The real concourse is **6–7 cells deep** (rows 117..123). The port has a 3-cell Upper Concourse and a 3-wide Spine. |
| x 11..26, y 38.6..45 | −8112..−6944 / −6432..−5920 | 944 | 43 | A **corridor running west** from the security gate, missing in the port |
| x 11.8..15.8, y 115..121 | – | 832 | 24 | Floor round the west service way |
| x 7.8..12.8, y 103..110 | – | 904 | 18 | Tank-room level west of the stair (WallBurst) |
| x 38..46, y 125..129 | −5984..−5344 / 496..800 | 832 | 18 | South half of the exit passage |
| x 22.8..29, y 92..103 | – | 904 | 13 | East strip of the tank room |
| x 18..23.8, y 77..79 | – | 872 | 12 | – |

Topology is preserved overall: the same chain of rooms and doors in the same order. The differences:
- **North third:** much wider halls than the port's 3-cell corridors, and a big west room.
- **Two unmodelled side wings:** the east hall and the west gate corridor.
- **Rooms the port draws too big:** the dock and freight yard, where the real floors are catwalk-sized.
- **A non-walkable band:** cols 37..63, rows 117..143 east of the escape lift. It is the hangar pit 800 u below. The port has nothing there either, which is right.

### Real LB01 footprint on the port's grid

80 u per cell, origin (−9007, −9513). `#` is walkable, `+` partly walkable, `.` floor not reached by nav (lower decorative floor), and a space means nothing. Columns are port x 0..63 and rows port y, with north at the top. The port's own AREAS in the same grid follow it in `lb01-compare.txt`.

```
     0         1         2         3         4         5         6   
     0123456789012345678901234567890123456789012345678901234567890123
143 |                                     ..................         |
142 |                                     ..................         |
141 |                                     ..................         |
140 |                                     ..................         |
139 |                                     ..................         |
138 |                                     ..................         |
137 |                                     ..................         |
136 |                                     ..................         |
135 |                               ++    ..................         |
134 |                               ##+   .........#########+........|
133 |                  ..       +######   .........#########+........|
132 |       +++++++++++..    ++++######++++........#########+........|
131 |       +############+   +############+........#########+........|
130 |       +############+   +##############################+........|
129 |       +############+   +#############################++........|
128 |       +############+...##############################.+........|
127 |       +############+...##############################++........|
126 |       +############+...+#############++++++++#+++++++++........|
125 |       +############+...+#############        +.................|
124 |       +############+...+##+####++###+        ..................|
123 |       +############+   +##++###  ###+        ..................|
122 |       +#############+++########++###+        ..................|
121 |       +#############################+        ..................|
120 |       +#############################+        ..................|
119 |       +#############################+        ..................|
118 |       +#############################+        ..................|
117 |       +#############################+        ..................|
116 |       +##########...                         ..................|
115 |       +##########...                                           |
114 |       +##########...                                           |
113 |     .++##########...                                           |
112 |     .############...                                           |
111 |     .############...                                           |
110 |     +############++.                                           |
109 |     ..+############++++++++++++++                              |
108 |           +######################                              |
107 |          ########################                              |
106 |          ########################                              |
105 |          ########################                              |
104 |          ########################                              |
103 |          ######++++++++++++++++++                              |
102 |          ######+.######                                        |
101 |          ######+.######                                        |
100 |          #######.######                                        |
 99 |          #######.######                                        |
 98 |          ###...#....###                                        |
 97 |          ###...#....###                                        |
 96 |          ###...#....###                                        |
 95 |          ##############                                        |
 94 |          ##############                                        |
 93 |          ##############+++++                                   |
 92 |          ###..+##+..########++                                 |
 91 |          ###..+##+..#########+                                 |
 90 |          ###+++###++##########                                 |
 89 |          #####################                                 |
 88 |          #####################                                 |
 87 |          #####################                                 |
 86 |          ###..+##+..#########.                                 |
 85 |          ###..+##+..#########.                                 |
 84 |          ###++####++#########+                                 |
 83 |          ####################+                                 |
 82 |          ####################.                                 |
 81 |..........+++........+++.#####+                                 |
 80 |                        .######                                 |
 79 |                        .######                                 |
 78 |                  #############                                 |
 77 |                  #############+++++++++++++++++                |
 76 |             .....#############################+                |
 75 |           +++++++#############################+                |
 74 |           +###################################+                |
 73 |           +###################################+                |
 72 |           +###.+#################+                             |
 71 |           +###.+#######+#########+                             |
 70 |           +###..+################+                             |
 69 |           +###..+################+                             |
 68 |           +###..+################+                             |
 67 |           +###..+################+                             |
 66 |           ####+ +################+                             |
 65 |           ####+ +################+                             |
 64 |           #######################+                             |
 63 |           #######################+.........                    |
 62 |           #######################..........                    |
 61 |           #######++##############..........                    |
 60 |           +++###++ ##############+.........                    |
 59 |                    ++++++###++++++                             |
 58 |                    +.....##+.....+                             |
 57 |                    ###############+++......                    |
 56 |                    ##################......                    |
 55 |                    ##################......                    |
 54 |                    ##################+++...                    |
 53 |                    #########.###########...                    |
 52 |                    #########.###########...                    |
 51 |                    +########.###########...                    |
 50 |                     ....####.############+.                    |
 49 |                     ....####.############+.                    |
 48 |                     ....####.#####++###+++.                    |
 47 |                     ....####.####+..##+....                    |
 46 |                     ....####.####+..##+....                    |
 45 |                     ....####.####+.........                    |
 44 |                     ....#########+.........                    |
 43 |                     ....########+..........                    |
 42 |                     ....########+..........                    |
 41 |           ################+#####+..........                    |
 40 |           ################++####+..........                    |
 39 |           #################+####+..........                    |
 38 |                     ....+#######+..........                    |
 37 |                     .......####............                    |
 36 |                     .......####............                    |
 35 |                     .......####............                    |
 34 |                            ####                                |
 33 |                            ####                                |
 32 |                            ####                                |
 31 |                           +#######+                            |
 30 |                           +########                            |
 29 |                           +########                            |
 28 |                           +########                            |
 27 |                           +########                            |
 26 |                           +########                            |
 25 |                           +########                            |
 24 |                 ......         +##+                            |
 23 |                 ......         +##+                            |
 22 |                 ..........     +##+                            |
 21 |                 ..........     +##+                            |
 20 |                 ..........   ++###+                            |
 19 |                 ..........   +####+                            |
 18 |                 ..........   ++###+                            |
 17 |                 .........    ++###+                            |
 16 |                 .........    +####+                            |
 15 |                              +####+                            |
 14 |                                +##+                            |
 13 |                                +##.           +++++++++++      |
 12 |                                +##.           ###########      |
 11 |                                +##.           ###########      |
 10 |                              +#####+          ###########      |
  9 |                              +######+         ####+++++++      |
  8 |                                 #####+.       ####+++          |
  7 |                                  +###################.......   |
  6 |                                   +##################.......   |
  5 |                                    +##############+++.......   |
  4 |                                               +###  ........   |
  3 |                                                +++  ........   |
  2 |                                                ...  ........   |
  1 |                       ............................  ........   |
  0 |                       ......................................   |
```

### Cargo Elevator against cargo.py

cargo.py says it was invented, and it is far from the real map.

**Size:**

| | Real | Port |
|---|---|---|
| Walkable area | 1,806 cells | 3,910 cells of AREAS (2.2×) |
| Bbox | 76×135 cells, a north-running spine | 128×112 grid; north, then east, then south |

**Real rooms** (about 9; the port has 17 areas):
1. **Start pad:** about 9×9 cells, z 832. It is LB01's escape lift, over the z 24 pit.
2. **West catwalk hall:** about 9×25 cells, x −6960..−6240, y −1040..880. It runs along the orange-lit z 416 lower bay. The port's Landing Bay with its grating walkway is the closest match.
3. **East–west link and security-door corridor:**
   - A link about 25×5 cells at y 560..880.
   - A corridor 4 cells wide, x −5360..−5040, north to y 2800, with a branch east at y 960..1280 to a closed door at x −4366.
   - The security door `LandingBayDoor11` is at (−5205, 1585) with its button area.
4. **Fire-shaft corridor:** y 2240..2800, narrowing to 1 cell beside the shaft hole (the ElevatorFireGlass scene).
5. **Observation gallery:** the block x −5920..−4080, y 2800..4080, about 23×16 cells. Its 3-cell walkway runs between glass at x −5246 and −5011, with seven window alcoves 38 u up. The port's Observation Gallery (7×22) is too long and too thin. The real security office is not a separate room *(inferred)*.
6. **Pipe hall:** x −6160..−5040, y 4160..6080, about 14×24 cells, z 800. It holds HugePipe, the MetalPlatform deck at 878, and the knockback trigger. The port's Crew Quarters stand in its place; the real map has no crew quarters.
7. **Lift lobby:** x −6160..−3840, y 6080..7280, about 29×15 cells. It is outdoors, under exterior fog and snow precipitation.
8. **Lift platform:** **x −3792..−3232, y 6832..7360 = 560×528 u = 7.0×6.6 cells of 80 (5.8×5.4 of 97), z 792, 41 cells.**
   - The moving shaft assembly is 1,048 u (13 cells) across.
   - The entrance ramp is on the west (x −3841) and the exit ramp on the east (x −3213), the same topology as the port's bridges.
   - The port's LIFT is **12×12 cells**, 1.7× per side and 3.5× the area, with a VOID ring of 16×16.
9. **Exit bay:** x −3024..−960, y 5936..7264, **26×17 cells**, z 800, directly east of the shaft. It is outdoors and snowy: concrete 50% snow-blended, exterior fog volume *66, snow precipitation *65. ExitZone is at (−1862, 7022), about 21 cells east of the platform centre.
   - The port instead sends the squad 60+ cells further, through an invented hive "lower level" (Freight Junction, Service Shaft, Colony Concourse, Transit Station; 94..124 × 12..104).
   - **None of that exists**, and nothing in the real map is lower than the start.

**Elevation:** the real ride is fake (walls move; start and exit floors are both at 800). The port's flat ride matches that.

### Real LB02 footprint

80 u per cell; origin Hammer (−7040, −1840); 76×135 cells; north at the top.

```
     0         1         2         3         4         5         6         7     
     0123456789012345678901234567890123456789012345678901234567890123456789012345
134 |                                     ..........+##                          |
133 |                                     ..........+##                          |
132 |                                     ..........+##                          |
131 |                                     ..........+++                          |
130 |                                     .............                          |
129 |                                     .............                          |
128 |                                     .............                          |
127 |                                     .............                          |
126 |                                     .............                          |
125 |                                     .............                          |
124 |                                     .............                          |
123 |                                     .............                          |
122 |                                     .............                          |
121 |                     ...             ..............                         |
120 |                     ...             ..............                         |
119 |                     ...   +#####+   +.............                         |
118 |                           ######+   +.............                         |
117 |                           ######+   +.............                         |
116 |                           ######+   +.............                         |
115 |           .....           ######+   +.............                         |
114 |           .....           ###########.....##......                         |
113 |           .....         #############++########..#+++++####################|
112 |           .....         #######################..##########################|
111 |           .....         #######################..##########################|
110 |                         #######################..########  +###############|
109 |                  ++++     #####################..#######+..+###############|
108 |                  +##+ ++++###########..########..+++#####  +###############|
107 |                  +##+ +##+#######+++#############.  #######################|
106 |                +################+   +############.  #######################|
105 |                #################+   +############.  #######################|
104 |                #################+   +############.  ########               |
103 |        ...+++++#################+...+############.      ####               |
102 |           ###############           +############.      ####               |
101 |           ###############           +############.      ####               |
100 |           ###############                        .      ####               |
 99 |           ###############                        .......####......         |
 98 |           ################+                             ####               |
 97 |           #################                             +###               |
 96 |           #################                                                |
 95 |           #####++##########                                                |
 94 |           ###############++                                                |
 93 |           ###############                                                  |
 92 |           ###############                                                  |
 91 |           ###############                                                  |
 90 |           ###############                                                  |
 89 |           ###############                                                  |
 88 |           ###############                                                  |
 87 |           ########+.#####                                                  |
 86 |           ########+.#####                                                  |
 85 |           ###############                                                  |
 84 |           ###############                                                  |
 83 |           ###############                                                  |
 82 |           ###############                                                  |
 81 |           ###############                                                  |
 80 |           ###############                                                  |
 79 |           ###############                                                  |
 78 |           ###############                                                  |
 77 |           ###############                                                  |
 76 |           ###########++++                                                  |
 75 |           ##############+                                                  |
 74 |              ############                                                  |
 73 |              ############                                                  |
 72 |              ############                                                  |
 71 |              ############++++++++++++                                      |
 70 |              ########################                                      |
 69 |              ########################                                      |
 68 |              ########################                                      |
 67 |              ########################                                      |
 66 |              ########################                                      |
 65 |              ########################                                      |
 64 |              ########################                                      |
 63 |              ########################                                      |
 62 |              ########################                                      |
 61 |              ########################                                      |
 60 |...........   ########################                                      |
 59 |...........   +#######################                                      |
 58 |...........        +##################                                      |
 57 |...........        ++...#                                                   |
 56 |...........         ....#                                                   |
 55 |...........         ....#                                                   |
 54 |...........        +++++#                                                   |
 53 |...........        +#####                                                   |
 52 |...........        +#####                                                   |
 51 |...........        ++####                                                   |
 50 |...........         +####                                                   |
 49 |............       ++####                                                   |
 48 |..................   ####                                                   |
 47 |..................   ####                                                   |
 46 |..................   ####                                                   |
 45 |..................   ####                                                   |
 44 |..................   ####                                                   |
 43 |..................   ####                                                   |
 42 |..................   ####                                                   |
 41 |..................   ####                                                   |
 40 |..................   ####                                                   |
 39 |..................   ####                                                   |
 38 |..................   ########+#######+                                      |
 37 |..................   #################                                      |
 36 |..................   #################                                      |
 35 |++................   ####+++++++++++++                                      |
 34 |#########################                                                   |
 33 |#########################                                                   |
 32 |#########################                                                   |
 31 |#########################                                                   |
 30 |############+++++++++####                                                   |
 29 |###########+......   ####                                                   |
 28 |.+######..........   ####                                                   |
 27 |.+###.##..........   ####                                                   |
 26 |.+###+##+++.......   ####                                                   |
 25 |.+########+.......   ####                                                   |
 24 |.+########+.......   ####                                                   |
 23 |.+########+.......   ####                                                   |
 22 |.+######+++.......   ####                                                   |
 21 |.+######..........   ####                                                   |
 20 |.+######..........   ####                                                   |
 19 |.+######..........   ####                                                   |
 18 |.+###.##..........   ####                                                   |
 17 |.+######..........   ####                                                   |
 16 |.+########+.......   +###                                                   |
 15 |.+########+.......                                                          |
 14 |.+########+.......                                                          |
 13 |.+########+.......                                                          |
 12 |.+######..........                                                          |
 11 |.+######..........                                                          |
 10 |.+######..........                                                          |
  9 | #########+............                                                     |
  8 | #########+............                                                     |
  7 | #########+............                                                     |
  6 | #########+............                                                     |
  5 | #########+............                                                     |
  4 | ########.+............                                                     |
  3 | ########.+............                                                     |
  2 | ########++............                                                     |
  1 | ++++++++++............                                                     |
  0 | +.....................                                                     |
```

How to read the grid:
- **The lift** is cols 40..47, rows 108..114; the two columns of `.` beside it at cols 48..49 are the shaft gap.
- **The `#` from col 50 eastward** (rows 104..113) is the exit bay.
- **Cols 11..40, rows 99..114** are the lift lobby; the pipe hall is below it at rows 75..98.
- **Rows 101..108, cols 37..50** are the moving walls' south apron at z 776.
- **The `.` field at rows 114..134, cols 37..50** is shaft-wall ledges at their start position.
- **The `##` at cols 48..49, rows 132..134** is nav nodes on the drone-climb path. It is an artifact.

## 6. Lighting, fog, props and the pakfile

### Lights

**LB01:**
- **Counts:** 105 light entities (62 `light`, 43 `light_spot`, no `light_dynamic`) and 1 `light_environment`.
  - The environment light is _light 67,82,120 at 75 (night blue), with ambient 56,73,99 at 40, pitch −45, yaw 146.
  - The HDR worldlights lump (54) holds 124 lights; the LDR lump 15 is empty.
- **Colours by `_light`:**

  | Colour | Count | Brightness / use |
  |---|---|---|
  | **174,198,194** (pale cyan-white) | 61 | Mostly brightness 20–40 fills in every interior room, plus 400–700 spots |
  | **223,206,149** (warm white) | 32 | Dock, yard, upper concourse and flight control; floods at 800–1,200 in the dock and yard |
  | **247,134,60** (sodium orange) | 7, brightness 250–500 | The z 680 pit beside storage (2), the storage annex, the crew office and the lower bays |
  | 139,193,85 (green) | 2 | Security booth |
  | 20,65,101 (deep blue) | 1 | Crew office |
  | 254,216,146 | 1 | – |
  | 0,183,0 | 1 | The sealed z 1152 box |

- **Projected textures:**
  - Red 249,0,0 at the dock (the rotating `rot_light` alarm at −4740, −9038).
  - Warm 223,206,149 at 400 over the gate (−6680, −6816).
  - Pale 234,219,166 at flight control.
  - Three cold 174,198,194.
- **Glow sprites:** light_glow03 in 205,73,73 (red) ×105, 199,216,213 ×23, 200,170,68 ×8, and green ×1.

Real lights inside each port area (`lb01-compare.txt`):
- **Pump Room:** 5 × cold 174,198,194. **No orange.**
- **Inner Storage:** 10 cold, brightness 10–500.
- **Supply and Tank Rooms:** 8 cold each, with 400–700 spots.
- **Security Booth:** green.
- **Flight Control:** 3 warm, dim (10–30).
- **Dock and Freight Yard:** warm floods (up to 1,100).
- **No light at all:** Junction, West Service Way, Spine, Freight Office, Records Room, Escape Lift.

**LB02:**
- **Counts:** 61 lights (35 `light`, 26 `light_spot`), 64 HDR worldlights, and the same light_environment.
- **Colours:**

  | Colour | Count | Where / brightness |
  |---|---|---|
  | 174,198,194 | 34 | – |
  | 223,206,149 | 14 | Warm; the exit bay is 4 at about 18 |
  | 255,255,255 at brightness 12 | 6 | Stepping down the shaft at x −3532, z 965 → −1040 |
  | 204,152,94 | 3 | The fire shaft |
  | 247,134,60 | 3 | 2 over the z 416 lower bay under the start |

- **Projected textures:**
  - `light_spin_ele_top` / `_bottom`: 249,192,0 (yellow).
  - `light_spin_ele_0..4`: 249,0,0 (red), on func_rotating.
  - `light_explo`: 235,158,54.
- **Sprites:** 200,47,2 ×10 (the shaft's orange-red lamps), red 205,73,73 ×42, green 71,183,23 ×6.

### Fog and environment (identical controllers in both maps)

| env_fog_controller | Colour | Start..end | Max density |
|---|---|---|---|
| `fog_exterior` | 39,53,86 | 256..4000 | 0.5 |
| `fog_interior` (start enabled) | 120,90,60 | 256..6000 | 0.5 |
| `fog_elevator` | 43,37,32 | 256..4000 | 0.9 |

Fog volumes switch between them.

**LB01 exterior zones:**
- *44: x −7168..−3840, y −9984..−6976 (dock to yard).
- *43: x −8100..−7632, y −4672..−4160, south of the crew office, with snow_drift_through_door particles.
- *45: x −8232..−6016, y 0..1664, the north block: concourse, freight office, flight control.

Snow (func_precipitation, type 7) falls over *29 (the dock and yard), *42 (the office pocket) and *46 (the north block).

**LB02:**
- *62: elevator fog over the shaft.
- *64: exterior over the lobby, x −6016..−4360, y 6368..7834, with precipitation `precip_end`.
- *66: exterior over the exit bay, with precipitation *65.

**Post-process and colour:**
- `fx_settings_exterior`: grain **100**. `fx_settings_interior`: grain 1.5. Both have depth blur 0.75 and screen blur 0.1.
- Colour correction: `landingbay_interior.raw` and `landingbay_exterior.raw`.
- `shadow_control`: colour 157,159,162, distance 100.

### Static props

LB01 has 3,027 static props of 139 models. Top 30:

| Model | Count |
|---|---|
| pipeset_8 pipe_64 | 211 |
| crossbeam_02 | 194 |
| scaffold beam128 | 188 |
| scaffold thinbeam64 | 180 |
| pipeset_32 straight_128 | 161 |
| floor panel_06 | 159 |
| crossbeam03b | 127 |
| railing straight_tall_128 | 119 |
| pipe_160 | 96 |
| pipe_corner (8) | 80 |
| railing straight_128 | 65 |
| pipe_corner (32) | 58 |
| cross_beam_square_128 | 55 |
| metal_flashing_128 | 49 |
| crate001 | 47 |
| oilpipeline straight | 46 |
| railing straight_tall_64 | 43 |
| metal_flashing_64 | 42 |
| trash_01b | 39 |
| outsidesupportbeam2 | 38 |
| panel_01 | 35 |
| metal_flashing_256 | 33 |
| crate002 | 32 |
| beam64 | 32 |
| outsidesupportbeam2a | 31 |
| pipe_8_regulator | 28 |
| outsidewall_128_thinpipe3 | 28 |
| railing small_bend_8 | 28 |
| crossbeam03c | 25 |
| railing cap_128 | 24 |

LB02 has 1,634 props of 104 models. The top of the list is pipe_64 138, beam128 110, panel_06 107, crossbeam_02 93, metal_flashing_128 90, pipe_straight_128 88, thinbeam64 80, straight_tall_128 71, pipe_corner 56, outsidesupportbeam2a 47, walltrim01c 43 and outsidesupportbeam2 42. It continues with walltrim and wire, crossbeam03a, crates, pallets and concrete_pipe001b.

Entity props:
- LB01: cardbox1breakable 48, buttonpanel panel02 26, supplycrate 22, oildrum_phys 15.
- LB02: cardbox 17, supplycrate 12, light_cagelight01_off 10, doorlight 6, elevator_landingbay_ramp 2, elevator_shaft shaft01a/01b.

### Particles and atmosphere

There is **no `func_dustmotes`, no `env_steam`** in either map; steam and drips are info_particle_system.

**LB01** has 79 particle systems:

| Effect | Count |
|---|---|
| steam_low_vent_1 | 14 |
| vent_steam_light_64x64 | 8 |
| leaky_roof_sml_180h | 7 |
| pipe_drips_a_180x256 | 6 |
| steam_simple_directional_sml | 4 |
| steam_jet_80 | 4 |
| snow_drift_through_door_1 | 4 |
| Scripted sparks and smoke at weld and door points | 27 |
| immolate_hover_main (dropship jets) | 2 |

Plus one env_smokestack `BloodhoundSteam` at the dock and one env_dustpuff.

**LB02** has 27:

| Effect | Count |
|---|---|
| landingbay_lift_fog_volume | 4 |
| landingbay_lift_steam_jet | 3 |
| landingbay_lift_start_dust | 2 |
| vent_steam_light_64x64 | 2 |
| landingbay_slime_gas_top / _bottom | 1 each |
| ElevatorShaftFire | 1 |
| pipe_drips_a_180x256 | 1 |
| Scripted sparks and smoke | 12 |

Plus 2 asw_emitter `smokejet1` in the fire shaft.

Steam sources in LB01 cluster in:
- The storage and pump rooms (x −7500..−6500, y −5300..−3400).
- The tank room (steam_jet_80 at the tank pits).
- The north block vents.

### Pakfile

| | LB01 | LB02 |
|---|---|---|
| Files | 3,639 | 1,860 |
| Patched cubemap `.vmt`s | 482 | 182 |
| Cubemap `.vtf`s (c*x*_*y*_*z*) | 144 | 46 |
| cubemapdefault (LDR and HDR) | yes | yes |
| Static prop vertex lighting `sp_hdr_*.vhv` | 3,010 | 1,629 |
| `.dct` | 1 | 1 |

No custom textures or models are embedded. The patched base materials (LB01) are:
- **Concrete:** concretefloor050a, concretewall080a–d, concretewall081a–e, concrete_crack001a, blendconcsnow001a.
- **Metal:** metalfloor001a/011a/011b/011c/012a, metalgrate012a/b, metaldoor018a/030a/030b/059a, blendmetalmetal001a, blendmetalsnow001a/002a.
- **Glass:** glasswindowbreak070a/b.
- **Other:** toxicslime002a, swarm/bsp/blendswarm_snow, greymetalbsp.

## 7. Appearance deltas against the port (AS-REFERENCE.md, STATUS.md "Visual pass")

1. **Outdoor zones (med-high).**
   - The port marks only LB dock to yard as OUTDOORS (cells 26..64 × 0..34).
   - The real map also has exterior fog and snow over a pocket south of the crew office (port cells about x 11..17, y 61..67) and over the whole north block (port cells about x 10..37, y 119..140): concourse, freight office and flight control. Flight control's floor is 91% snow-blended concrete.
   - In Cargo Elevator, the lobby west of the lift and the exit bay are outdoors and snowy. The port lights its exit as a purple and green hive.
2. **Sodium orange is in the wrong place (med).**
   - Real orange (247,134,60) lights the z 680 **pit beside the gate and inner storage** (port cells about 32..44 × 36..58) and the storage annex. Looked down into from the storage rims, that is AS's "orange room behind girder silhouettes" *(inferred)*.
   - The real pump room is lit cold 174,198,194.
   - In LB02, orange lights the z 416 lower bay under the start catwalk. The port's orange-under-grating start is right.
3. **Base light colour (med).**
   - About 60% of interior lights are one pale cyan-white (174,198,194) at low brightness (20–40), punctuated by 400–700 spots.
   - The warm 223,206,149 floods are outdoors: dock, yard, concourse.
   - Red comes from 105 red glow sprites and the rotating red projected light at the dock, not from many red lamps.
   - The pink neon has no `_light` source. It is likely the 205,73,73 sprites *(inferred)*.
4. **Elevations the port flattens (med).** Each step is 40–80 u (0.5–1 cell):

   | Real level | z | Relative to the next room |
   |---|---|---|
   | Gate balcony | 1024 | 80 above the gate |
   | Raised west pump deck | 952 | 80 above the pump room |
   | Inner perimeter | 872 | 72 below the gate |
   | Crew office | 792 | 80 below |
   | Tank room | 904 | 32–56 up from the supply room via an 18.6° ramp |
   | North block | 832 | 72 below the tank room |
   | Flight control island | 872 | 40 up, on 3 bridge ramps over a 616 u pit |

   In the port these would read as stair, ramp and ledge dressing. The playable spread is 112 u (LB01) and 86 u (LB02).
5. **Depth the port paints (high for looks).**

   | Real drop | Depth |
   |---|---|
   | Dock edge to −2904 | 3,850 u |
   | Walkway to −2000 | 2,944 u |
   | Storage rim to the orange pit | 264 u |
   | Tank pits | 744 u |
   | Escape lift to the hangar pit | 800–900 u |
   | Flight control rim | 616 u |
   | LB02 start catwalk to the lower bay | 416 u |

   All of them are fogged over a black unlit floor at −3072, with truss columns (crossbeam_02, up to 3,800 u tall), oil pipelines and snow cliffs down there.
6. **Wall tops and void (low, matches).** Walls are 192 u (port 200). Wall tops are unlit black caps. There are no ceilings. Overhead pipes and beams hang at 120–200 u, just under the wall tops. The port's girder "above the walls" is slightly higher than AS's clutter.
7. **Floor material mix (low-med).**

   | Real area | Floor mix | Port note |
   |---|---|---|
   | Dock and yard | Snowy concrete 33%, concrete 21%, snowy metal 15%, grate012b 14%, metalfloor011a 12% | – |
   | Inner perimeter | Concrete 54%, metaldoor030b plate 20%, metalfloor011a 8%, grate 6%, crack 5% | – |
   | Tank room | blendmetalmetal 48%, **grate013a 42%** | Mostly metal and grating; the port's "concrete and diamond plate in the bays" does not fit here |
   | North block | Concrete 43%, snowy concrete 19%, metalfloor012a 12%, snowy metal 8%, grate 5% | – |
   | LB02 start hall and gallery | Concrete 72% | – |
   | LB02 pipe hall | Concrete 40%, metalfloor011a 26%, snowy concrete 20% | – |
   | LB02 exit | Snowy concrete 50%, metalfloor011a 48% | – |

   Walls are concretewall080a/081a/081c throughout; there are no painted-panel wall materials in the BSP. The pale panels with yellow frames are likely concretewall080/081 textures and wall_trim props *(inferred)*.
8. **Atmosphere (low).**
   - AS uses steam vents, drips and leaky-roof particles, and snow drifting through doors. It has no dust-mote entities: the motes come from the fog and post-process (exterior grain 100) *(inferred)*.
   - The lift has its own fog, steam-jet and start-dust systems, which the port already mirrors.
9. **Cargo lift scale (high).**
   - The real platform is 7×6.6 cells; the port's is 12×12.
   - The real exit bay is right beside the shaft, 21 cells from the platform centre, outdoors in snow.
   - The port has a 60-cell hive "lower level" that does not exist.
