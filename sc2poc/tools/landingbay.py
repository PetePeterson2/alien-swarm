"""Mission 1, LANDING BAY: after Alien Swarm's asi-jac1-landingbay_01.

Traced from the game's own briefing overview (materials/vgui/swarm/overviews/
landingbay01briefingoverview, read from the installed game's VPK for reference
only) at 7 overview pixels, about 80 world units, to a cell; its entity lump gave
the doors, the door panels, the computer, the pickups, every asw_spawner and the
triggers that start them (converted with the same mapping, then fitted to the
traced rooms). Nothing of Valve's is shipped: these are numbers and rectangles.

The flow is the original's: the dropship Bloodhound docks at the outer landing
bay; sweep north up the freight yard to the security gate, where a tech hacks a
door panel (objective 1, "Access the inner perimeter"); through the storage rooms
and the pump room (doors you may weld behind you), pick up a welder in the supply
room and cut through the sealed doors into the tank room; up the north stair and
the spine to flight control, where a tech hacks the escape pod's computer and the
squad holds while it downloads (objective 2, "Download the flight data"); the
aliens break down the east door, and the squad leaves by it for the cargo lift
(objective 3, "Get to the Landing Bay exit").

Same data shape as tools/level.py; tools/level.py `use()` swaps it in.
Coordinates are map units, x east, y north. Cells are 1 x 1.
"""

W, H = 64, 144
FLOOR = 8.0
WALL_H = 2.5

AREAS = [
    ('Dropship Dock',      (47, 3, 59, 14), 'bay'),
    ('Dock Walkway',       (35, 4, 47, 9), 'hall'),
    ('South Ramp',         (33, 8, 38, 18), 'hall'),
    ('Freight Yard',       (28, 17, 38, 34), 'cargo'),
    ('Security Gate',      (26, 34, 34, 44), 'hall'),
    ('Gate Door West',     (26, 44, 29, 45), 'hall'),
    ('Gate Door East',     (31, 44, 34, 45), 'hall'),
    ('Inner Storage',      (20, 45, 35, 60), 'cargo'),
    ('Storage Annex',      (35, 48, 41, 58), 'cargo'),
    ('Maintenance Hall',   (18, 60, 35, 66), 'hall'),
    ('Crew Office',        (11, 60, 17, 76), 'mess'),
    ('Office Door South',  (17, 62, 18, 65), 'hall'),
    ('Office Door North',  (17, 72, 18, 75), 'hall'),
    ('Weld Door West',     (19, 66, 22, 67), 'hall'),
    ('Weld Door East',     (27, 66, 30, 67), 'hall'),
    ('Pump Room',          (18, 67, 31, 77), 'reactor'),
    ('Supply Room',        (24, 77, 32, 93), 'cargo'),
    ('Tank Door South',    (23, 83, 24, 86), 'hall'),
    ('Tank Door North',    (23, 89, 24, 92), 'hall'),
    ('Tank Room',          (10, 80, 23, 103), 'reactor'),
    ('Stair Door',         (13, 103, 17, 104), 'hall'),
    ('North Stair',        (13, 104, 17, 110), 'hall'),
    ('Junction',           (12, 110, 21, 115), 'hall'),
    ('Booth Door',         (11, 110, 12, 113), 'hall'),
    ('Security Booth',     (4, 110, 11, 117), 'lab'),
    ('West Service Way',   (9, 115, 12, 121), 'duct'),
    ('Spine Corridor',     (16, 115, 19, 121), 'hall'),
    ('West Concourse',     (9, 121, 15, 124), 'hall'),
    ('Concourse Door',     (15, 121, 16, 124), 'hall'),
    ('Upper Concourse',    (16, 121, 35, 124), 'hall'),
    ('Freight Office',     (17, 124, 23, 134), 'lab'),
    ('Records Room',       (24, 124, 28, 133), 'lab'),
    ('Flight Control',     (29, 124, 38, 136), 'lab'),
    ('Control Door',       (38, 129, 39, 133), 'hall'),
    ('Exit Passage',       (39, 129, 45, 133), 'hall'),
    ('Exit Door',          (45, 129, 46, 133), 'hall'),
    ('Escape Lift',        (46, 126, 57, 136), 'bay'),
]
BLOCKS = [
    # The tank room's six tanks.
    (13, 97, 16, 100), (19, 97, 22, 100), (13, 92, 16, 95), (19, 92, 22, 95), (13, 86, 16, 89), (19, 86, 22, 89),
    (20, 45, 25, 52),          # inner storage: its south-west corner is the gate house
    (29, 46, 31, 54),          # inner storage: the rack between the two gate lanes
    (31, 22, 34, 29),          # freight yard: a crate stack
    (24, 67, 26, 72),          # pump room: the pump housing between the two weld doors
]

VIEWPORTS = [(50, 2), (51, 2), (55, 2), (56, 2)]   # the dock's outer wall looks onto the landing field
OUTDOORS = (26, 0, 64, 34)                          # under the night sky: the dock, its walkway, the ramp and the freight yard
SPAWN = (51.0, 7.5)
SPAWN_FACING = 180.0
LIFT = None
VOID = None
WINDOWS = []

# Lamps (x, y, kind, flicker): 0 steady, 1 failing, 2 sputtering, 3 alarm pulse.
LIGHTS = [
    # Outside, as AS's opening is (seen 2026-10-23): a snowy night dock in cold blue light with a red alarm
    # turning and pink neon on the walkway, then hard white floodlights over the freight yard. Snow falls
    # here (src/Objects.galaxy AS_SnowPulse, OUTDOORS below).
    (50.0, 5.0, 'cold', 0), (56.0, 5.0, 'red', 3), (50.0, 12.0, 'coldbig', 0), (56.0, 12.0, 'cold', 0),
    (41.0, 6.5, 'purple', 0), (35.5, 12.0, 'cold', 0),
    (30.0, 19.0, 'whitebig', 0), (36.0, 21.0, 'orange', 2), (30.0, 31.0, 'white', 1), (36.0, 31.0, 'whitebig', 0),
    (30.0, 37.0, 'red', 3), (30.0, 42.0, 'white', 0),
    (27.0, 54.0, 'white', 0), (33.0, 48.0, 'white', 2), (33.0, 58.0, 'cold', 0), (38.0, 53.0, 'white', 1), (23.0, 56.0, 'white', 0),
    (22.0, 63.0, 'white', 2), (31.0, 63.0, 'white', 0),
    (14.0, 63.0, 'white', 0), (14.0, 72.0, 'orange', 2),
    (21.0, 74.0, 'cold', 0), (28.0, 70.0, 'white', 1), (28.0, 75.0, 'red', 3),
    (28.0, 80.0, 'white', 0), (28.0, 88.0, 'white', 2), (28.0, 91.0, 'yellow', 0),
    (12.0, 82.0, 'cold', 0), (17.5, 91.0, 'cold', 1), (17.5, 101.0, 'white', 0), (12.0, 95.0, 'red', 3), (21.0, 82.0, 'white', 2),
    (15.0, 107.0, 'white', 1), (16.5, 112.5, 'white', 0), (7.0, 113.0, 'green', 0),
    (10.5, 119.0, 'cold', 1), (17.5, 118.0, 'white', 0),
    (12.0, 122.5, 'white', 2), (25.0, 122.5, 'white', 0),
    (20.0, 130.0, 'cold', 0), (26.0, 129.0, 'white', 2), (31.0, 129.0, 'cold', 0), (35.0, 133.0, 'green', 0), (33.0, 126.0, 'white', 0),
    (42.0, 131.0, 'red', 3), (51.0, 128.0, 'yellow', 0), (51.0, 134.0, 'whitebig', 0),
]

# Where the director brings its hordes and wanderers in: vents and holes along the whole route.
VENTS = [
    (37.0, 33.0), (28.5, 18.0), (39.0, 5.0), (33.5, 15.0),
    (21.0, 58.0), (40.0, 57.0), (34.0, 45.5), (19.0, 65.0), (34.0, 61.0),
    (11.5, 75.0), (19.0, 76.0), (30.0, 68.0),
    (31.0, 92.0), (31.0, 78.0),
    (10.5, 81.0), (22.0, 102.0), (10.5, 102.0), (16.0, 84.0),
    (20.0, 114.0), (13.0, 114.0), (10.5, 120.0),
    (34.0, 121.5), (18.0, 133.0), (25.0, 132.0), (37.0, 125.0),
]
EGGS = []
BIOMASS = []
AMMO = []
CREEP = []

# Room dressing: (model, x, y, facing degrees, scale, solid radius or 0).
PROPS = [
    # The dock: cargo and the bay's caution lights (the dropship Bloodhound at the clamps is the mission's own).
    ('SpacePlatformCautionLights', 47.5, 11.5, 90.0, 1.0, 0.0), ('SpacePlatformCautionLights', 58.5, 11.5, 270.0, 1.0, 0.0),
    ('DOM_Crate', 48.5, 4.5, 15.0, 0.9, 0.0), ('StarshipContainers', 49.0, 12.5, 90.0, 0.5, 0.0),
    ('DOM_Groundlights', 52.0, 3.6, 0.0, 1.0, 0.0),
    # Freight yard and gate.
    ('DOM_Crate', 36.5, 25.0, 30.0, 0.9, 0.0), ('DOM_Crate', 29.0, 32.0, 70.0, 0.9, 0.0), ('DOM_RocketPallet', 36.0, 18.5, 0.0, 0.7, 0.0),
    ('SpacePlatformSteamVent', 34.5, 12.0, 0.0, 0.6, 0.0),
    # Inner storage and annex.
    ('MoebiusLabZergCrates', 26.0, 57.5, 0.0, 0.8, 0.0), ('DOM_Crate', 33.5, 56.0, 20.0, 0.9, 0.0),
    ('DOM_LabConsoles', 39.5, 49.0, 270.0, 0.7, 0.0), ('BloodSplats', 27.0, 52.0, 0.0, 1.0, 0.0),
    # Crew office: a last stand.
    ('ValhallaTable', 14.0, 66.0, 0.0, 0.8, 0.0), ('ValhallaCabinet', 11.6, 70.0, 90.0, 0.8, 0.0),
    ('ZergCarcasses', 14.5, 69.5, 0.0, 0.6, 0.0), ('BloodSplats', 13.0, 73.0, 0.0, 1.0, 0.0),
    # Pump room.
    ('SpacePlatformSteamVent', 21.0, 72.0, 0.0, 0.7, 0.0), ('SpacePlatformGenerator', 29.5, 73.0, 270.0, 0.6, 0.0),
    ('ElectricalArcs', 25.0, 72.5, 0.0, 0.7, 0.0),
    # Supply room: shelves, the welders on the bench.
    ('DOM_GunRacks', 31.4, 86.0, 270.0, 0.8, 0.0), ('DOM_LabCrates', 30.0, 81.0, 0.0, 0.8, 0.0),
    # Tank room.
    ('KPReactor', 14.5, 98.5, 0.0, 0.6, 0.0), ('KPReactor', 20.5, 98.5, 0.0, 0.6, 0.0), ('KPReactor', 14.5, 93.5, 0.0, 0.6, 0.0),
    ('KPReactor', 20.5, 93.5, 0.0, 0.6, 0.0), ('KPReactor', 14.5, 87.5, 0.0, 0.6, 0.0), ('KPReactor', 20.5, 87.5, 0.0, 0.6, 0.0),
    ('SpacePlatformSteamVent', 11.0, 90.0, 0.0, 0.6, 0.0), ('SmokeMedium', 21.5, 84.0, 0.0, 0.5, 0.0),
    # Security booth.
    ('MoebiusLabConsoles', 6.0, 115.5, 0.0, 0.6, 0.0), ('DOM_GunRacks', 4.5, 112.0, 90.0, 0.7, 0.0),
    # Offices and flight control.
    ('CastanarWorkstation', 18.0, 131.0, 90.0, 0.7, 0.0), ('DOM_LabConsoles', 26.0, 132.0, 0.0, 0.7, 0.0),
    ('CastanarMonitorWall', 33.5, 135.6, 180.0, 0.7, 0.0), ('CastanarHoloProjector', 33.0, 129.0, 0.0, 0.7, 0.0),
    # The escape lift.
    ('SpacePlatformCautionLights', 47.0, 131.0, 90.0, 0.8, 0.0), ('BattleStation_Line_Decals', 52.0, 131.0, 0.0, 1.0, 0.0),
]

# ---- the mission ---------------------------------------------------------
# Doors: name, cells (x0, y0, x1, y1), kind, seal (0..1 of a full weld), panel or None.
# kind 'auto' opens for anyone near; 'panel' stays locked until its panel is hacked (then opens);
# 'bash' is locked and opens only when the aliens behind it break it down; 'jammed' never opens.
DOORS = [
    ('gate_west',   (26, 44, 29, 45), 'panel', 0.0, (29.6, 43.3)),
    ('gate_east',   (31, 44, 34, 45), 'panel', 0.0, (33.4, 43.3)),
    ('office_s',    (17, 62, 18, 65), 'auto', 0.0, None),
    ('office_n',    (17, 72, 18, 75), 'auto', 0.0, None),
    ('weld_west',   (19, 66, 22, 67), 'auto', 0.0, None),
    ('weld_east',   (27, 66, 30, 67), 'auto', 0.0, None),
    ('tank_s',      (23, 83, 24, 86), 'auto', 0.8, None),
    ('tank_n',      (23, 89, 24, 92), 'auto', 0.8, None),
    ('stair',       (13, 103, 17, 104), 'auto', 0.0, None),
    ('booth',       (11, 110, 12, 113), 'auto', 1.0, None),
    ('concourse',   (15, 121, 16, 124), 'auto', 0.0, None),
    ('control',     (38, 129, 39, 133), 'bash', 0.0, None),
    ('exit',        (45, 129, 46, 133), 'auto', 0.0, None),
]
# The door panels are alternatives (AS's Start_button_right / right1): hacking either opens its own door.
# Wire puzzle per panel: rows, columns, wires (trigger_asw_button_area wirerows / wirecolumns / numwires).
PANEL_WIRES = (2, 5, 2)
# The escape pod's computer (trigger_asw_computer_area: HackDifficulty 4, EntriesPerTumbler 7,
# TumblerMoveInterval 0.5, DownloadTime 15).
COMPUTER = (31.3, 134.6)
COMPUTER_HACK = (4, 7, 0.5, 15.0)
CONSOLE = COMPUTER
# PDAs left by the crew: position, owner, mail key (resource text after the original's landingbaymail1-3).
PDAS = [((9.4, 112.0), 'Brian Howe', 1), ((38.3, 48.5), 'Laura Callen', 2), ((13.6, 71.5), 'John Cain', 3)]
# Pickups lying about: welders on the supply room's bench, a sentry gun in the sealed security booth.
PICKUPS = [('welder', 27.7, 91.4), ('welder', 25.4, 80.3), ('sentry', 8.0, 113.5)]
SENTRY_SPOT = (29.8, 128.7)      # the holo sentry: where the briefing suggests setting the sentry for the hold
# Asleep where the squad finds them (asw_drone, sleepstate 1).
SLEEPERS = [('AS_DRONE', 19.2, 62.7), ('AS_DRONE', 26.6, 78.1), ('AS_DRONE', 28.1, 78.3)]
BARRELS = [(25.5, 79.0), (26.6, 85.7)]
EXTRACT = (47, 127, 56, 135)     # the escape lift: every living marine inside ends the mission

# asw_spawner, one per row: name, x, y, alien, NumAliens, MaxLiveAliens, SpawnInterval, InfiniteAliens,
# MinSkillLevel, MaxSkillLevel (0 any), SpawnIfMarinesAreNear, StartBurrowed. Positions converted from the
# entity lump and nudged into the traced rooms where the trace is coarser than the original.
SPAWNERS = [
    ('breakdoor_spawn', 42.5, 131.0, 'AS_DRONE', 5, 3, 2.0, 0, 1, 0, 0, 0),
    ('breakdoor_spawn', 42.5, 130.0, 'AS_DRONE', 5, 3, 2.0, 0, 0, 0, 0, 0),
    ('dock_holdout_spawn_01', 25.5, 128.0, 'AS_DRONE', 6, 4, 1.5, 1, 0, 0, 1, 1),
    ('dock_holdout_spawn_01', 26.0, 132.0, 'AS_DRONE', 6, 4, 1.5, 1, 0, 0, 1, 1),
    ('dock_holdout_spawn_01', 34.1, 125.3, 'AS_DRONE', 6, 4, 1.5, 1, 0, 0, 1, 1),
    ('dock_holdout_spawn_01', 23.4, 122.4, 'AS_DRONE', 6, 4, 1.5, 1, 0, 0, 1, 1),
    ('dock_holdout_spawn_01', 27.5, 122.4, 'AS_DRONE', 6, 4, 1.5, 1, 0, 0, 1, 1),
    ('dock_preholdout_spawn_01', 32.7, 130.6, 'AS_DRONE', 3, 2, 3.0, 0, 0, 0, 0, 1),
    ('dock_preholdout_spawn_01', 31.8, 126.6, 'AS_DRONE', 3, 2, 2.0, 0, 0, 0, 1, 1),
    ('tankroom_pre_02_spawn', 25.5, 130.7, 'AS_DRONE', 5, 5, 1.0, 0, 0, 0, 1, 1),
    ('tankroom_pre_02_spawn', 32.4, 126.1, 'AS_DRONE', 3, 3, 1.0, 0, 0, 0, 1, 1),
    ('tankroom_01_spawn', 13.3, 90.0, 'AS_DRONE', 4, 1, 2.0, 0, 0, 0, 1, 1),
    ('tankroom_01_spawn', 21.4, 98.4, 'AS_DRONE', 4, 2, 2.0, 0, 0, 0, 1, 1),
    ('tankroom_01_spawn', 11.8, 86.3, 'AS_DRONE', 6, 3, 2.0, 0, 0, 0, 1, 1),
    ('tankroom_01_spawn', 14.2, 109.0, 'AS_DRONE', 4, 8, 2.0, 0, 0, 0, 0, 1),
    ('tankroom_end_01_spawn', 13.4, 101.5, 'AS_DRONE', 2, 1, 2.0, 0, 0, 0, 1, 1),
    ('tankroom_end_01_spawn', 23.6, 122.0, 'AS_DRONE', 6, 6, 3.0, 0, 0, 0, 1, 1),
    ('tankroom_end_02_spawn', 18.9, 90.5, 'AS_DRONE', 4, 2, 3.0, 0, 0, 0, 1, 1),
    ('tankroom_end_02_spawn', 12.0, 94.1, 'AS_DRONE', 15, 2, 3.0, 0, 0, 0, 1, 1),
    ('supply_spawn_01', 23.0, 108.5, 'AS_JUMPER', 2, 2, 1.0, 0, 2, 0, 1, 0),
    ('supply_spawn_02', 14.7, 122.5, 'AS_DRONE', 2, 1, 3.0, 0, 0, 0, 1, 1),
    ('supply_spawn_03', 11.5, 94.1, 'AS_DRONE', 2, 1, 3.0, 0, 0, 0, 1, 1),
    ('WallSpawner', 11.5, 106.5, 'AS_JUMPER', 3, 2, 1.0, 0, 0, 0, 1, 0),
    ('storage_room_spawn_2', 28.2, 88.1, 'AS_DRONE', 2, 2, 2.0, 0, 0, 0, 1, 1),
    ('storage_room_spawn_2', 28.8, 86.3, 'AS_DRONE', 10, 2, 2.0, 0, 0, 0, 1, 1),
    ('storage_room_spawn_2', 12.8, 69.5, 'AS_DRONE', 4, 3, 2.0, 0, 0, 0, 1, 1),
    ('storage_room_spawn_2_behind', 27.2, 61.0, 'AS_DRONE', 3, 2, 2.0, 0, 0, 0, 1, 1),
    ('storage_room_spawn_3', 22.1, 92.0, 'AS_DRONE', 8, 3, 4.0, 0, 0, 0, 1, 1),
    ('Storage_room_spawner', 20.2, 68.4, 'AS_DRONE', 3, 2, 2.0, 0, 0, 0, 1, 1),
    ('Storage_room_spawner', 36.3, 53.1, 'AS_DRONE', 5, 2, 3.0, 0, 0, 0, 1, 1),
    ('Storage_room_spawner', 27.2, 67.9, 'AS_DRONE', 3, 2, 2.0, 0, 0, 0, 1, 1),
    ('Spawn04', 12.6, 71.3, 'AS_DRONE', 2, 3, 2.0, 0, 0, 0, 0, 0),
    # Insane only (MinSkillLevel 4 = MaxSkillLevel 4).
    ('insane_buzz_spawn', 25.4, 26.4, 'AS_BUZZER', 6, 2, 2.0, 0, 4, 4, 1, 0),
    ('insane_buzz_spawn', 24.2, 26.4, 'AS_BUZZER', 6, 2, 2.0, 0, 4, 4, 1, 0),
    ('insane_para_spawn', 30.7, 43.0, 'AS_PARASITE', 1, 1, 4.0, 0, 4, 4, 1, 0),
    ('insane_para_spawn', 28.2, 43.0, 'AS_PARASITE', 1, 1, 4.0, 0, 4, 4, 1, 0),
    ('insane_ranger_spawn', 24.6, 122.0, 'AS_RANGER', 4, 1, 4.0, 1, 4, 4, 1, 0),
    ('insane_ranger_spawn', 35.4, 127.1, 'AS_RANGER', 4, 1, 4.0, 1, 4, 4, 1, 1),
    ('insane_ranger_spawn', 26.2, 130.5, 'AS_RANGER', 4, 1, 4.0, 1, 4, 4, 1, 1),
    ('insane_ranger_spawn', 43.5, 130.0, 'AS_BOOMER', 1, 1, 4.0, 0, 4, 4, 1, 0),
    ('insane_ranger_spawn', 43.5, 131.5, 'AS_RANGER', 1, 1, 4.0, 0, 4, 4, 1, 0),
    ('insane_ranger_spawn', 44.3, 130.3, 'AS_RANGER', 1, 1, 4.0, 0, 4, 4, 1, 0),
    ('insane_har_spawn', 31.4, 64.5, 'AS_HARVESTER', 1, 1, 4.0, 0, 4, 4, 1, 0),
    ('insane_har_spawn', 22.0, 62.6, 'AS_HARVESTER', 1, 1, 4.0, 0, 4, 4, 1, 0),
    ('insane_har2_spawn', 16.4, 90.4, 'AS_HARVESTER', 1, 1, 4.0, 0, 4, 4, 1, 0),
    ('insane_har2_spawn', 12.0, 89.2, 'AS_HARVESTER', 1, 1, 4.0, 0, 4, 4, 1, 0),
    ('insane_har2_spawn', 12.0, 83.3, 'AS_HARVESTER', 1, 1, 4.0, 0, 4, 4, 1, 0),
]

# Triggers: rectangle, once, chance, [(action, argument, delay)]. Thin brush triggers are widened to
# span the traced passage. Actions: spawn <spawner>, stop <spawner>, pick <a|b|c|> (one at random,
# '' for none), complete <objective>, line <commander line>, hint <hint>, wall <wall burst>,
# weld <door> (suggest welding it once the whole squad is past), sentry (show the sentry spot).
TRIGGERS = [
    ((47.0, 3.0, 59.0, 14.0), True, 1.0, [('hint', 'movement', 0.0), ('line', 'co_m1_ob1', 6.0), ('dropship', '', 5.0)]),
    ((38.0, 4.0, 40.0, 9.0), True, 1.0, [('hint', 'general', 0.0)]),
    ((33.0, 8.0, 39.0, 10.0), True, 1.0, [('spawn', 'insane_buzz_spawn', 0.0)]),
    ((28.0, 26.0, 38.0, 29.0), True, 1.0, [('spawn', 'insane_para_spawn', 0.0)]),
    ((26.0, 34.0, 34.0, 44.0), True, 1.0, [('hint', 'hack_panel', 0.0)]),
    ((25.0, 46.5, 35.0, 49.5), True, 1.0, [('complete', 'AccessBay', 0.0), ('spawn', 'insane_har_spawn', 0.0)]),
    ((25.0, 55.5, 29.0, 58.5), True, 1.0, [('spawn', 'Storage_room_spawner', 0.0)]),
    ((16.0, 61.5, 19.0, 64.0), True, 1.0, [('spawn', 'Spawn04', 0.0)]),
    ((18.0, 66.0, 31.0, 69.0), True, 1.0, [('spawn', 'storage_room_spawn_2', 0.0), ('weld', 'weld_west|weld_east', 0.0)]),
    ((24.0, 78.0, 32.0, 80.5), True, 1.0, [('spawn', 'storage_room_spawn_2_behind', 0.0), ('hint', 'welder', 0.5)]),
    ((23.0, 82.0, 25.0, 93.0), True, 1.0, [('spawn', 'storage_room_spawn_3', 0.0), ('hint', 'cut_door', 0.0)]),
    ((20.5, 81.0, 23.0, 93.0), True, 1.0, [('spawn', 'tankroom_01_spawn', 0.0), ('spawn', 'insane_har2_spawn', 0.0)]),
    ((11.5, 99.5, 16.5, 103.0), True, 1.0, [('spawn', 'tankroom_end_01_spawn', 0.0), ('weld', 'stair', 0.0)]),
    ((9.5, 97.5, 13.0, 99.5), True, 0.1, [('wall', 'tank_west', 0.4), ('spawn', 'WallSpawner', 0.4)]),
    ((13.0, 104.5, 17.0, 106.5), True, 1.0, [('spawn', 'tankroom_end_02_spawn', 0.0), ('music', 'ambient', 0.0)]),
    ((13.0, 108.5, 17.0, 110.0), True, 1.0, [('pick', 'supply_spawn_01|supply_spawn_02|supply_spawn_03|', 1.0)]),
    ((9.0, 117.0, 19.0, 119.5), True, 1.0, [('spawn', 'tankroom_pre_02_spawn', 1.0)]),
    ((21.0, 121.0, 23.0, 124.0), True, 1.0, [('pick', 'dock_preholdout_spawn_01|', 0.0)]),
    ((28.0, 124.5, 33.0, 130.0), True, 1.0, [('sentry', '', 0.0), ('hint', 'computer', 0.0)]),
    ((40.0, 129.0, 42.0, 133.0), True, 1.0, [('line', 'co_m1_ob3', 2.0)]),
]

# Commander lines (subtitles), after the original's co_m1_ob1..3 and its closecaption text.
LINES = {
    'co_m1_ob1': 'Bloodhound has docked. Sweep the landing bay and get through the security gate to the inner perimeter. You\'ll need your tech to bypass the door locks.',
    'co_m1_ob2': 'Good work, we have the flight data. The lift to the lower level is past flight control. Get your squad to the exit.',
    'co_m1_ob3': 'That\'s the cargo lift ahead. Get everyone aboard.',
}

# Checkpoints are not Alien Swarm's: a wiped squad restarts the mission. Kept for the QA skip (Ctrl+L).
CHECKPOINTS = [SPAWN, (30.0, 40.0), (28.0, 85.0), (16.5, 118.0), (33.0, 128.0)]
ZONES = []
# The autopilot's way through: x, y, wait (1 until the gate panel is hacked, 3 the tank doors cut,
# 4 the download done and the control door open).
ROUTE = [
    (44.0, 6.5, 0), (36.0, 6.5, 0), (35.5, 14.0, 0), (35.5, 20.0, 0), (36.0, 31.0, 0), (32.5, 38.0, 0), (33.4, 43.3, 1),
    (32.5, 46.5, 0), (33.0, 56.0, 0), (28.5, 62.0, 0), (28.5, 68.0, 0), (28.0, 76.0, 0), (27.5, 84.5, 0), (24.5, 84.5, 3),
    (21.0, 84.5, 0), (17.0, 84.0, 0), (17.0, 90.5, 0), (17.5, 96.0, 0), (16.5, 101.5, 0), (15.0, 105.0, 0), (15.0, 109.0, 0),
    (17.5, 112.5, 0), (17.5, 118.0, 0), (17.5, 122.5, 0), (30.0, 122.5, 0), (31.3, 133.5, 4),
    (36.5, 131.0, 0), (41.0, 131.0, 0), (48.0, 131.0, 0), (51.5, 131.0, 0),
]
