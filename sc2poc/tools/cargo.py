"""Mission 2, CARGO ELEVATOR: from the landing bay down to the colony.

After Alien Swarm's asi-jac1-landingbay_02 (its overview and entity lump were
read for the flow, not traced): deploy in the landing bay, push up the
observation gallery while aliens come through its windows, override the
security door, cross the crew quarters to the upper concourse, board the
freight elevator with the whole squad and ride it down while the swarm climbs
the shaft walls, then fight out through the infested freight junction to the
transit station.

The elevator never moves. Its platform is fixed floor ringed by a black void;
the shaft walls around it are script units that scroll upward (src/Mission.galaxy),
which is how the original does it too (FreightElevatorWalls, a tracktrain).
The lobby (upper level, west) and the freight junction (lower level, east) both
butt against the shaft; the tall shaft walls hide each from the other.

Same data shape as tools/level.py's derelict deck; tools/level.py `use()` swaps it in.
Coordinates are map units, x east, y north. Cells are 1 x 1.
"""

W, H = 128, 112
FLOOR = 8.0
WALL_H = 2.5

AREAS = [
    # Upper level.
    ('Landing Bay',          (6, 4, 30, 24), 'bay'),
    ('Bay Corridor',         (16, 24, 21, 40), 'hall'),
    ('Observation Gallery',  (15, 40, 22, 62), 'hall'),
    ('Security Office',      (6, 44, 15, 56), 'bay'),
    ('Security Door',        (16, 62, 20, 66), 'hall'),
    ('Crew Quarters',        (6, 66, 30, 82), 'mess'),
    ('North Passage',        (16, 82, 20, 92), 'duct'),
    ('Upper Concourse',      (14, 92, 62, 98), 'hall'),
    ('Cargo Office',         (30, 98, 44, 108), 'cargo'),
    ('Elevator Lobby',       (62, 88, 78, 104), 'cargo'),
    # The lift: bridges and platform (the void ring round it is not floor).
    ('Lift Bridge',          (78, 94, 80, 98), 'lift'),
    ('Cargo Elevator',       (80, 90, 92, 102), 'lift'),
    ('Exit Bridge',          (92, 94, 94, 98), 'lift'),
    # Lower level.
    ('Freight Junction',     (94, 88, 118, 104), 'hive'),
    ('Service Shaft',        (108, 60, 113, 88), 'duct'),
    ('Colony Concourse',     (96, 44, 124, 60), 'lab'),
    ('Transit Station',      (98, 12, 124, 44), 'bay'),
]
BLOCKS = [
    (24, 8, 27, 11), (24, 17, 27, 20),                          # landing bay: cargo stacks
    (10, 70, 12, 72), (10, 76, 12, 78), (24, 70, 26, 72), (24, 76, 26, 78),   # crew quarters: bunk pillars
    (68, 94, 71, 98),                                            # lobby: freight crates
    (104, 94, 107, 97), (110, 98, 112, 100),                     # junction: wreckage
    (102, 50, 104, 54), (116, 50, 118, 54),                      # colony concourse pillars
    (104, 36, 108, 38), (114, 36, 118, 38),                      # transit station: platform barriers
]

VIEWPORTS = []                 # decorative windows (tools/level.py); the gallery's WINDOWS are its own
SPAWN = (18.0, 9.0)
SPAWN_FACING = 90.0

# The elevator: platform rectangle, void ring (cells), bridges, the shaft wall columns.
LIFT = (80, 90, 92, 102)
VOID = (78, 88, 94, 104)
BRIDGE_IN = (78, 94, 80, 98)
BRIDGE_OUT = (92, 94, 94, 98)
# Shaft wall columns: (x, y, width, facing) of each column's centre on the void's outer edge.
# Facing is where the panel's face looks (into the shaft). The south side stays open so the
# camera sees the platform; its void edge reads as the drop.
def shaft_columns():
    cols = []
    for x0, x1 in [(78, 80), (80, 84), (84, 88), (88, 92), (92, 94)]:
        cols.append(((x0 + x1) / 2, 104.0, x1 - x0, 270.0, 'N'))
    for y0, y1 in [(88, 90), (90, 94), (94, 98), (98, 102), (102, 104)]:
        cols.append((78.0, (y0 + y1) / 2, y1 - y0, 0.0, 'W'))
        cols.append((94.0, (y0 + y1) / 2, y1 - y0, 180.0, 'E'))
    return cols

# Lamps (x, y, kind, flicker): 0 steady, 1 failing, 2 sputtering, 3 alarm pulse.
LIGHTS = [
    (10.0, 8.0, 'yellow', 0), (22.0, 8.0, 'white', 2), (10.0, 20.0, 'cold', 0), (22.0, 20.0, 'yellow', 0), (16.0, 14.0, 'whitebig', 0),
    (18.5, 28.0, 'white', 1), (18.5, 36.0, 'red', 3),
    (18.5, 43.0, 'cold', 0), (18.5, 49.0, 'white', 2), (18.5, 55.0, 'cold', 1), (18.5, 60.0, 'red', 3),
    (9.0, 47.0, 'white', 0), (12.0, 54.0, 'green', 0),
    (18.0, 64.5, 'orange', 3),
    (9.0, 69.0, 'white', 1), (18.0, 74.0, 'white', 0), (27.0, 69.0, 'white', 2), (9.0, 79.0, 'orange', 2), (27.0, 79.0, 'white', 1),
    (18.0, 85.0, 'red', 3), (18.0, 90.0, 'white', 2),
    (20.0, 95.0, 'white', 0), (30.0, 95.0, 'white', 1), (40.0, 95.0, 'cold', 0), (50.0, 95.0, 'white', 2), (58.0, 95.0, 'white', 0),
    (34.0, 103.0, 'white', 0), (40.0, 106.0, 'orange', 2),
    (65.0, 91.0, 'white', 0), (65.0, 101.0, 'white', 1), (75.0, 91.0, 'yellow', 0), (75.0, 101.0, 'yellow', 0),
    # The platform's own work lights.
    (82.0, 92.0, 'yellow', 0), (90.0, 92.0, 'yellow', 0), (82.0, 100.0, 'yellow', 0), (90.0, 100.0, 'yellow', 0),
    # Lower level: dark, failing, organic.
    (98.0, 92.0, 'purple', 1), (106.0, 101.0, 'green', 2), (114.0, 92.0, 'purple', 0), (101.0, 98.0, 'orange', 2), (112.0, 99.0, 'cold', 0), (110.0, 84.0, 'red', 3),
    (110.5, 75.0, 'white', 2), (110.5, 66.0, 'cold', 1),
    (100.0, 52.0, 'green', 0), (110.0, 48.0, 'white', 2), (120.0, 56.0, 'green', 1),
    (104.0, 40.0, 'white', 0), (118.0, 40.0, 'white', 1), (104.0, 18.0, 'cold', 0), (118.0, 18.0, 'white', 0), (111.0, 28.0, 'whitebig', 0),
]

# Director vents (where hordes and wanderers come in).
VENTS = [
    (7.0, 5.0), (29.0, 23.0), (7.0, 55.0), (21.0, 30.0), (7.0, 81.0), (29.0, 67.0), (19.0, 91.0),
    (36.0, 97.0), (61.0, 93.0), (43.0, 107.0), (63.0, 103.0), (63.0, 89.0),
    (117.0, 103.0), (95.0, 89.0), (112.0, 61.0), (97.0, 59.0), (123.0, 45.0), (99.0, 13.0), (123.0, 13.0),
]
EGGS = [(115.0, 101.0), (116.0, 100.0), (99.0, 101.0), (122.0, 57.0), (121.5, 46.0), (97.0, 46.5)]
BIOMASS = [(112.0, 90.0, 1.2), (98.0, 55.0, 1.0)]
AMMO = [(13.0, 45.5), (32.0, 106.0), (65.0, 102.0), (100.0, 42.0)]

# Room dressing: (model, x, y, facing degrees, scale, solid radius or 0).
PROPS = [
    # Landing bay: the dropship that brought them, crates, deck markings.
    ('Hercules', 12.0, 12.0, 60.0, 0.8, 2.0),
    ('BattleStation_Line_Decals', 18.0, 16.0, 0.0, 1.0, 0.0),
    ('SpacePlatformCautionLights', 7.5, 14.0, 90.0, 1.0, 0.0), ('SpacePlatformCautionLights', 28.5, 14.0, 270.0, 1.0, 0.0),
    ('DOM_Crate', 25.5, 12.5, 15.0, 0.9, 0.0), ('StarshipContainers', 25.5, 9.5, 0.0, 0.5, 0.0), ('StarshipContainers', 25.5, 18.5, 0.0, 0.5, 0.0),
    ('DOM_Groundlights', 18.0, 22.0, 0.0, 1.0, 0.0),
    # Gallery and security office.
    ('BloodSplats', 18.0, 52.0, 0.0, 1.0, 0.0), ('ZergCarcasses', 19.5, 58.0, 30.0, 0.6, 0.0),
    ('DOM_LabConsoles', 10.0, 55.0, 180.0, 0.7, 0.0), ('DOM_GunRacks', 7.0, 50.0, 90.0, 0.8, 0.0),
    ('MoebiusLabConsoles', 21.2, 61.3, 180.0, 0.6, 0.0),
    # Crew quarters: a last stand.
    ('ValhallaTable', 18.0, 72.0, 0.0, 0.8, 0.8), ('ValhallaTable', 14.0, 77.0, 90.0, 0.8, 0.8), ('CastanarTable', 22.0, 77.0, 0.0, 0.8, 0.0),
    ('ValhallaCabinet', 7.0, 74.0, 90.0, 0.8, 0.0), ('ValhallaCabinet', 29.0, 74.0, 270.0, 0.8, 0.0),
    ('DOM_CeilingDebris_Beams', 20.0, 68.5, 60.0, 0.8, 0.0), ('BloodSplats', 13.0, 69.0, 0.0, 1.3, 0.0),
    ('SpacePlatformWallDebris', 27.0, 80.0, 0.0, 0.8, 0.0), ('ZergCarcasses', 16.0, 80.0, 0.0, 0.7, 0.0),
    # North passage: the vent that blows.
    ('SpacePlatformSteamVent', 17.0, 87.0, 0.0, 0.6, 0.0),
    # Concourse and cargo office.
    ('DOM_Crate', 27.0, 93.5, 10.0, 0.8, 0.0), ('DOM_Crate', 48.0, 96.5, 40.0, 0.8, 0.0), ('SpacePlatformSteamVent', 44.0, 93.0, 0.0, 0.6, 0.0),
    ('DOM_RocketPallet', 33.0, 101.0, 0.0, 0.7, 0.0), ('MoebiusLabZergCrates', 41.0, 104.0, 0.0, 0.8, 0.0), ('DOM_LabConsoles', 37.0, 107.3, 0.0, 0.7, 0.0),
    # Lobby: freight waiting for the lift.
    ('StarshipContainers', 69.5, 96.0, 90.0, 0.5, 0.0), ('DOM_Crate', 66.0, 90.0, 0.0, 0.9, 0.0), ('DOM_Crate', 74.5, 102.0, 45.0, 0.9, 0.0),
    ('SpacePlatformCautionLights', 76.5, 92.5, 0.0, 0.8, 0.0), ('SpacePlatformCautionLights', 76.5, 99.5, 0.0, 0.8, 0.0),
    ('BattleStation_Line_Decals', 72.0, 96.0, 90.0, 0.8, 0.0),
    # Freight junction: the colony's lower level, overrun.
    ('CocoonedColonists', 116.0, 102.5, 200.0, 0.6, 0.0), ('CreepPods', 100.0, 101.0, 0.0, 0.8, 0.0), ('CreepPods', 114.0, 90.0, 0.0, 0.8, 0.0),
    ('SpacePlatformCreepedDoodads', 103.0, 90.0, 0.0, 0.8, 0.0), ('SplatAliveInside', 108.0, 92.0, 0.0, 1.0, 0.0),
    ('DOM_Fire_Large', 105.5, 95.5, 0.0, 0.5, 0.0), ('SmokeMedium', 105.5, 95.5, 0.0, 0.6, 0.0),
    ('ZergCarcasses', 98.0, 97.0, 0.0, 0.7, 0.0),
    # Service shaft and colony concourse.
    ('SpacePlatformSteamVent', 109.0, 70.0, 0.0, 0.6, 0.0), ('SpaceSteamJet', 112.0, 80.0, 0.0, 0.5, 0.0),
    ('CastanarStasisTube', 99.0, 47.0, 0.0, 0.7, 0.0), ('CastanarStasisTubeDebris', 121.0, 48.0, 0.0, 0.7, 0.0),
    ('CastanarMonitorWall', 110.0, 59.3, 180.0, 0.7, 0.0), ('CocoonedColonists', 122.0, 58.0, 220.0, 0.6, 0.0),
    ('SplatAliveInside', 112.0, 52.0, 0.0, 0.8, 0.0),
    # Transit station: the way out.
    ('BattleStation_Line_Decals', 111.0, 28.0, 0.0, 1.2, 0.0), ('DOM_Groundlights', 111.0, 20.0, 0.0, 1.0, 0.0),
    ('SpacePlatformCautionLights', 99.5, 28.0, 90.0, 1.0, 0.0), ('SpacePlatformCautionLights', 122.5, 28.0, 270.0, 1.0, 0.0),
    ('DOM_Crate', 101.0, 40.0, 20.0, 0.9, 0.0), ('DOM_Crate', 121.0, 41.0, 70.0, 0.9, 0.0), ('Hercules', 111.0, 18.0, 90.0, 0.8, 0.0),
]

# Gallery windows: hull cells on the gallery's east wall that show glass (aliens burst through them).
WINDOWS = [(22, y) for y0 in (43, 47, 51, 55) for y in (y0, y0 + 1)]

# ---- the mission ----------------------------------------------------------
# Security door across the door passage: cells, and which way its halves slide (x).
DOOR = (16, 63, 20, 64)
DOOR_PANEL = (21.0, 60.6)          # the console marines stand at to override it
CONSOLE = DOOR_PANEL               # the mission's console (src/Mission.galaxy as_doorPanel)
LIFT_PANEL = (86.0, 100.6)         # the elevator controls at the platform's north rail
EXTRACT = (104, 22, 118, 34)       # the transit platform: everyone alive inside ends the mission

# Trigger zones, in route order: name, (x0, y0, x1, y1).
ZONES = [
    ('gallery', (15, 42, 22, 47)),
    ('door', (15, 56, 22, 62)),
    ('quarters', (6, 66, 30, 80)),
    ('vent', (16, 84, 20, 89)),
    ('concourse', (24, 92, 44, 98)),
    ('lobby', (62, 88, 78, 104)),
    ('lift', LIFT),
    ('junction', (94, 88, 118, 104)),
    ('shaft', (108, 60, 113, 80)),
    ('station', (98, 12, 124, 44)),
]
# Checkpoints (respawn spots after a squad wipe), by mission stage.
CHECKPOINTS = [(18.0, 9.0), (18.5, 58.0), (18.0, 90.0), (70.0, 92.0), (86.0, 95.0), (110.5, 70.0)]
# The autopilot's way through (build.py --auto): x, y, wait (1 until the door opens, 2 until the ride is over).
ROUTE = [
    (18.0, 14.0, 0), (18.5, 30.0, 0), (18.5, 45.0, 0), (18.5, 57.0, 0), (20.6, 60.0, 1),
    (18.0, 63.5, 0), (18.0, 67.0, 0), (21.0, 69.5, 0), (21.0, 80.0, 0), (18.0, 84.0, 0), (18.0, 95.0, 0),
    (40.0, 95.0, 0), (61.0, 95.0, 0), (66.0, 91.0, 0), (75.0, 92.0, 0), (77.0, 96.0, 0), (82.0, 96.0, 0), (86.0, 95.0, 2),
    (93.0, 96.0, 0), (99.0, 92.0, 0), (110.5, 91.0, 0), (110.5, 80.0, 0), (110.5, 62.0, 0), (110.5, 50.0, 0),
    (111.0, 40.0, 0), (111.0, 30.0, 0), (111.0, 28.0, 0),
]
# Creep on the lower level: the colony is overrun below the lift.
CREEP = [(106.0, 96.0, 6.0), (113.0, 90.0, 3.5), (100.0, 100.0, 3.0), (110.5, 70.0, 2.5), (110.0, 52.0, 5.0), (98.0, 55.0, 2.5), (121.0, 48.0, 3.0)]
