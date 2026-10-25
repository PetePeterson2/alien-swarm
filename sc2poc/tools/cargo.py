"""Mission 2, CARGO ELEVATOR: after Alien Swarm's asi-jac1-landingbay_02.

Traced from the map itself (tools/astrace.py), as tools/deima.py and tools/rydberg.py are: the deck is AS's walkable
floor in 80-unit cells, and the entity lump gave the doors, spawners, triggers, timers and the lift's own logic.
Nothing of Valve's is shipped: these are numbers and rectangles.

The flow is the original's. The squad steps off the tram into the tank room, where drones climb down off the tanks,
crosses to the long corridor up past the elevator shaft (shoot the barrel at its top and the shaft beside it goes up
in a chain of blasts), and walks the glass observation gallery while drones break in through its windows. North of it
the ramp rooms' floor vents burst open under more drones, and past them is the lift lobby. Everyone on the cargo
elevator and it starts down (objective 1): the shaft walls slide up past the platform while jumpers drop onto it from
the walls (timer_elevator_spawn picks one of eight groups every 2-3.5 s) and drones climb down them (the crawlers,
every 1.5-2 s, until three quarters of the way down). At the bottom the exit ramp opens; the squad gets off and out to
the exit (objective 2). Below Insane it is drones and jumpers all the way: AS's rangers, boomers, harvesters and
parasites here are on Insane only (MinSkillLevel 4).

The elevator never moves, in AS or here: its walls slide past a fixed platform (FreightElevatorWalls, a tracktrain
running 2655 units at 25 a second up an incline toward the camera; src/Mission.galaxy AS_RideMove, tools/elevator.py).
The platform is AS's, 8 by 6 cells with the console's notch in its north edge, and the ride runs as
relay_lift_but_succeed has it: the console starts it once everyone alive (up to four) is aboard, and refuses until then.

Same data shape as tools/level.py; tools/level.py `use()` swaps it in.
Coordinates are map units, x east, y north. Cells are 1 x 1.
"""
import math

import numpy as np

from tools.astrace import Trace, components

_T = Trace('asi-jac1-landingbay_02', 10, 22, 80, 124)
W, H = _T.W, _T.H
FLOOR = 8.0
WALL_H = 2.5
HEIGHTS = _T.HEIGHTS
DECK_Z = 800.0                  # the lift's level: the lobby, the platform and the way out (the upper rooms are 832)

# The elevator: platform rectangle and the console's notch in its north edge, the drop round it (cells), the
# bridges over the drop (AS's ramps, in the doorways of the shaft's west and east walls).
LIFT = (42, 109, 50, 115)
LIFT_NOTCH = (45, 115, 47, 116)
VOID = (40, 107, 52, 124)
VOID_DEPTH = 6.0                 # how far the shaft is seen to run on below the deck (tools/heights.py)
BRIDGE_IN = (40, 110, 42, 114)
BRIDGE_OUT = (50, 110, 52, 114)
# The shaft (tools/elevator.py): its middle across, where its walls' top edge meets the deck (y), the doorway slot,
# AS's red beacons (light_spin_ele_0 .. 4) along the west wall's top, where each stands along the walls when the ride
# begins, and how far the walls have gone when each hands on to the next (the path_tracks at 13, 35, 57 and 75%).
SHAFT = {'x': 46.0, 'y': 119.35, 'in_slot': 3, 'speed': 0.3125, 'beacon_x': 41.9, 'beacon_t': 0.4,
         'beacons': (2.08, -1.95, -9.16, -16.67, -23.92), 'beacon_s': (4.31, 11.65, 18.875, 24.94)}


DECK = _T.deck()
# The observation gallery: a walkway three cells wide between glass (the panes stand at x 24.4 and 27.4). The rooms
# behind the glass are the shaft's and a store's; drones come through the panes, nobody goes in.
DECK[60:73, :24] = False
DECK[60:73, 27:] = False
DECK[60:73, 24:27] = True
# The corridor past the shaft's glass box narrows to one cell in the trace: two, so a squad gets by.
DECK[56:60, 25:27] = True
# The overhead catwalk across the way out (z 842-948) is not floor; the passage under it is.
DECK[100:102, 50:] = False
DECK[100:102, 59:63] = True
# The lift: the platform, the drop round it, the bridges.
DECK[VOID[1]:VOID[3], VOID[0]:VOID[2]] = False
DECK[LIFT[1]:LIFT[3], LIFT[0]:LIFT[2]] = True
DECK[LIFT_NOTCH[1]:LIFT_NOTCH[3], LIFT_NOTCH[0]:LIFT_NOTCH[2]] = True
DECK[BRIDGE_IN[1]:BRIDGE_IN[3], BRIDGE_IN[0]:BRIDGE_IN[2]] = True
DECK[BRIDGE_OUT[1]:BRIDGE_OUT[3], BRIDGE_OUT[0]:BRIDGE_OUT[2]] = True
DECK = components(DECK, 6)

AREAS = [
    ('Tram Platform',       (2, 2, 13, 11), 'bay'),
    ('Tank Room',           (2, 11, 13, 32), 'works'),
    ('Cross Passage',       (2, 32, 27, 37), 'hall'),
    ('South Corridor',      (23, 17, 27, 32), 'duct'),
    ('Store Room',          (27, 37, 40, 40), 'cargo'),
    ('Shaft Corridor',      (23, 37, 27, 60), 'hall'),
    ('Observation Gallery', (24, 60, 27, 77), 'hall'),
    ('Ramp Rooms',          (13, 77, 30, 105), 'works'),
    ('Lift Lobby',          (18, 105, 40, 120), 'cargo'),
    ('Lift Bridge',         BRIDGE_IN, 'lift'),
    ('Cargo Elevator',      LIFT, 'lift'),
    ('Lift Console',        LIFT_NOTCH, 'lift'),
    ('Exit Bridge',         BRIDGE_OUT, 'lift'),
    ('Lower Landing',       (52, 96, 78, 116), 'hall'),
]
BLOCKS = []
VIEWPORTS = []
SPAWN = (8.0, 6.5)              # the tram platform (info_player_start)
SPAWN_FACING = 90.0
# The gallery's panes (func_breakable_surf Glass2-8): hull cells that show glass and give way.
WINDOWS = ([(23, y) for y in (60, 61, 63, 64, 66, 67, 69, 70)] +
           [(27, y) for y in (60, 61, 63, 64, 66, 67, 70, 71)])


# Lamps (x, y, kind, flicker), from the map's lights, as tools/rydberg.py reads them.
def _lights():
    out = []
    for e in _T.entities:
        if e['class'] not in ('light', 'light_spot'):
            continue
        x, y = _T.where(e)
        if not (0 <= x < W and 0 <= y < H) or not DECK[min(H - 1, int(y)), min(W - 1, int(x))]:
            continue
        # The lift's lights are the ride's own (src/Mission.galaxy): its beacons and the shaft's lamps.
        if VOID[0] <= x < VOID[2] and VOID[1] <= y < VOID[3]:
            continue
        r, g, b, a = (float(v) for v in (e['keys'].get('_light', '255 255 255 100').split() + ['100'])[:4])
        if r > 160 and g < 90:
            kind = 'red'
        elif r > 170 and g > 90 and b < 110:
            kind = 'orange'
        elif b > r + 30:
            kind = 'cold'
        else:
            kind = 'white'
        if a >= 200:
            kind += 'big'
        if any(math.hypot(x - ox, y - oy) < 3.5 for ox, oy, _, _ in out):
            continue
        out.append((x, y, kind, 0))
    return out


LIGHTS = _lights() + [
    # The alarm by the way out.
    (56.0, 112.0, 'red', 3),
]

# Room dressing: (model, x, y, facing degrees, scale, solid radius or 0).
PROPS = [
    ('DOM_Crate', 4.0, 30.0, 20.0, 0.8, 0.0), ('DOM_Crate', 11.5, 4.0, 70.0, 0.8, 0.0),
    ('SpacePlatformSteamVent', 25.0, 47.0, 0.0, 0.5, 0.0),
    ('DOM_LabConsoles', 31.0, 118.5, 0.0, 0.6, 0.0), ('StarshipContainers', 33.5, 116.0, 90.0, 0.4, 0.0),
    ('SpacePlatformCautionLights', 38.5, 112.5, 90.0, 0.8, 0.0), ('SpacePlatformCautionLights', 53.5, 112.5, 270.0, 0.8, 0.0),
    ('DOM_Crate', 75.0, 108.5, 45.0, 0.8, 0.0),
    # The crates along the platform's south edge.
    ('DOM_Crate', 42.7, 109.55, 0.0, 0.55, 0.0), ('DOM_Crate', 49.3, 109.55, 90.0, 0.55, 0.0),
]


def _snap(x, y, reach=6):
    ix, iy = int(x), int(y)
    if 0 <= ix < W and 0 <= iy < H and DECK[iy, ix]:
        return (x, y)
    best = None
    for dy in range(-reach, reach + 1):
        for dx in range(-reach, reach + 1):
            cx, cy = ix + dx, iy + dy
            if 0 <= cx < W and 0 <= cy < H and DECK[cy, cx]:
                d = dx * dx + dy * dy
                if best is None or d < best[0]:
                    best = (d, cx + 0.5, cy + 0.5)
    return best and best[1:]


# asw_spawner, every one the map can start, set down on the nearest deck: the gallery's window spawners land on the
# walkway beside their panes. ins_mortar_spawn, up on the shaft walls, has no deck near it and is left out.
def _spawners():
    out = []
    for row in _T.spawners():
        at = _snap(row[1], row[2])
        if at is not None:
            out.append((row[0], round(at[0], 1), round(at[1], 1)) + tuple(row[3:]))
    return out


SPAWNERS = _spawners()
VENTS = []
for _s in sorted(SPAWNERS, key=lambda s: s[2]):
    if len(VENTS) < 32 and all(math.hypot(_s[1] - vx, _s[2] - vy) >= 6.0 for vx, vy in VENTS):
        VENTS.append((_s[1], _s[2]))

# ---- the mission ----------------------------------------------------------
DOORS = [
    ('LandingBayDoor11', (23, 44, 27, 45), 'auto', 0.0, None),
]
CONSOLE = (46.0, 115.6)          # lift_buttonpanel, in the platform's notch
LIFT_PANEL = CONSOLE
# trigger_lift_button: "Activate Panel" starts the lift if the squad is aboard (src/Mission.galaxy AS_LiftButton).
BUTTONS = [('lift', CONSOLE, 'Activate Panel', True)]
INFO = {'msg_lift_deny': ('LIFT LOCKED', 'All unregistered personnel must be on the lift before it can be activated.')}
NEEDS_TECH = False
EXTRACT = (66, 109, 73, 113)     # ExitZone's trigger_multiple
EXTRACT_NAME = 'the exit'
OBJECTIVES = [
    ('elevator', 'Take the cargo elevator down', True, (46.0, 115.2)),
    ('escape', 'Get to the exit', False, None),
]
DESCRIPTION = ('The landing bay\'s lower levels are cut off from the colony but for the freight lift. Get through the tank '
               'room and the observation gallery to the cargo elevator, ride it down with the whole squad aboard, and '
               'get out at the bottom.')
PICKUPS = [('medkit', 17.1, 74.6), ('medkit', 32.5, 115.9), ('medkit', 32.2, 114.7)]
SENTRY_SPOT = (34.0, 112.0)
# The supply cache in the lobby: the ammo drop and the autogun's ammo (asw_ammo_drop, asw_ammo_autogun).
AMMO = [(33.2, 115.1), (34.1, 115.1)]
SLEEPERS = []
BARRELS = [(59.6, 107.2), (60.7, 110.4)]
# Explosive barrels something hangs on going up (src/Hive.galaxy fires "broken:<name>"): the one at the top of the
# shaft corridor sets off the shaft (ElevatorShaftTrigger), the one by the pipes in the ramp room brings the big pipe
# down and stops the rangers there (ins_ranger2_spawn, Insane).
HIVE_BARRELS = [(24.9, 59.0, 'shaftbarrel'), (26.5, 89.5, 'pipebarrel')]
EGGS = []
BIOMASS = []
CREEP = []

# Triggers: rectangle, once, chance, [(action, argument, delay)], options (trigger_asw_chance's chance here is 0.4).
_WALK = (24.7, 27.3)             # the gallery walkway's width, for its strips
TRIGGERS = [
    ((3.4, 8.7, 12.2, 9.1), True, 1.0, [('line', 'co_m1_ob7', 0.5)]),
    # The tank room: drones climb down off the tanks (StartBurrowed, ACT_CLIMB_OFF_RAIL).
    ((3.6, 14.9, 13.2, 15.3), True, 1.0, [('spawn', 'tankroom_01', 0.0), ('spawn', 'ins_boomer_spawn', 0.0)]),
    ((3.6, 24.7, 13.2, 25.1), True, 1.0, [('spawn', 'tankroom_02', 0.0)]),
    ((3.5, 28.2, 13.1, 28.6), True, 1.0, [('spawn', 'tankroom_03', 0.0), ('spawn', 'breakdoor_spawn', 0.0),
                                          ('spawn', 'ins_ranger_spawn', 3.0)]),
    ((18.0, 33.0, 19.3, 37.4), True, 1.0, [('spawn', 'hallway_spawn_01', 0.0)]),
    ((23.4, 36.9, 26.6, 38.1), True, 1.0, [('spawn', 'hallway_spawn_02', 0.0)]),
    ((21.9, 50.9, 26.8, 51.1), True, 1.0, [('spawn', 'SlomoSpawn1', 0.0)]),
    # The shaft goes up (ElevatorShaftTrigger, armed by the barrel at the corridor's top): three blasts down the shaft
    # behind the gallery's west glass, the big one, and the glass box by the corridor blown out.
    ((21.8, 48.9, 26.9, 60.1), True, 1.0, [('boom', '23.1,60.3', 0.0), ('boom', '23.1,61.9', 1.0), ('boom', '23.1,63.6', 1.4),
                                           ('boom', '23.1,64.2', 2.2), ('shatter', '24.2,57.6', 2.5), ('spawn', 'SlomoSpawn1', 0.0)],
     {'name': 'ElevatorShaftTrigger', 'off': True}),
    # The gallery: drones behind the panes (a 40% chance for each strip of the walkway), more at its far end.
    ((24.7, 60.3, 27.1, 60.7), True, 1.0, [('shatter', '24.1,61.1', 0.0), ('spawn', 'ins_har_spawn', 0.0)]),
    ((24.8, 61.9, 27.2, 62.2), True, 1.0, [('spawn', 'WindowSpawner1', 0.4), ('spawn', 'SlomoSpawn2', 0.0)]),
    ((_WALK[0], 61.2, _WALK[1], 61.5), True, 0.4, [('spawn', 'WindowSpawner2', 0.0)]),
    ((_WALK[0], 62.5, _WALK[1], 62.8), True, 0.4, [('spawn', 'WindowSpawner7', 0.0)]),
    ((_WALK[0], 65.2, _WALK[1], 65.5), True, 0.4, [('spawn', 'WindowSpawner6', 0.0)]),
    ((_WALK[0], 65.6, _WALK[1], 65.9), True, 0.4, [('spawn', 'WindowSpawner3', 0.0)]),
    ((_WALK[0], 68.6, _WALK[1], 68.9), True, 0.4, [('spawn', 'WindowSpawner4', 0.0)]),
    ((_WALK[0], 69.0, _WALK[1], 69.3), True, 0.4, [('spawn', 'WindowSpawner5', 0.0)]),
    ((24.6, 65.5, 27.2, 65.8), True, 1.0, [('spawn', 'SlomoSpawn3', 0.0)]),
    ((24.6, 68.8, 27.2, 69.1), True, 1.0, [('spawn', 'SlomoSpawn4', 0.0)]),
    # The ramp rooms: drones up through the floor vents.
    ((18.8, 82.0, 25.2, 82.3), True, 1.0, [('spawn', 'ins_ranger2_spawn', 0.0), ('spawn', 'ramp_room_spawn_01', 0.0)]),
    ((18.8, 92.9, 25.2, 93.2), True, 1.0, [('spawn', 'ramp_room_spawn_02', 0.0)]),
    # The lobby: the lift is in sight.
    ((26.0, 105.0, 40.0, 120.0), True, 1.0, [('board', '', 0.0)]),
    # Off the lift at the bottom.
    ((52.8, 110.5, 53.7, 114.7), True, 1.0, [('spawn', 'ins_drone_spawn', 0.0), ('line', 'co_m1_ob8', 0.0)]),
]
_GROUPS = '|'.join('ElevatorSpawn_group_%d' % k for k in range(1, 9))
ONS = [
    ('broken:shaftbarrel', 'enable', 'ElevatorShaftTrigger', 0.0),
    ('broken:pipebarrel', 'stop', 'ins_ranger2_spawn', 0.1),
    # The gallery's panes go as their drones come through (GlassExplosion2, 5-10).
    ('spawned:WindowSpawner1', 'shatter', '27.6,61.4', 0.0), ('spawned:WindowSpawner2', 'shatter', '27.7,64.4', 0.0),
    ('spawned:WindowSpawner3', 'shatter', '27.7,67.4', 0.0), ('spawned:WindowSpawner4', 'shatter', '27.6,70.6', 0.0),
    ('spawned:WindowSpawner5', 'shatter', '24.2,70.3', 0.0), ('spawned:WindowSpawner6', 'shatter', '24.3,67.0', 0.0),
    ('spawned:WindowSpawner7', 'shatter', '24.2,64.0', 0.0),
    # The ramp rooms' floor vents blow open under the first drone out of each (relay_vent_explo_01).
    ('spawned:ramp_room_spawn_01', 'vent', '19.6,74.7', 0.0),
    ('spawned:ramp_room_spawn_02', 'vent', '22.6,97.0', 0.0), ('spawned:ramp_room_spawn_02', 'vent', '17.0,98.7', 0.0),
    ('spawned:ramp_room_spawn_02', 'vent', '21.0,103.5', 0.0),
    # The console (trigger_lift_button): pressing it is the objective; the lift starts if the squad is aboard.
    ('pressed:lift', 'complete', 'elevator', 0.0), ('pressed:lift', 'liftbutton', '', 0.0),
    # The ride (relay_lift_but_succeed, from the press that starts it): the elevator's music, fifteen seconds in the
    # swarm starts dropping onto the platform and climbing down the walls, a second later 16 s of slow motion
    # (ElevatorSlomo, an adrenaline stim for everyone), and on Insane the parasites.
    ('ride:go', 'musicloop', 'Ambience_CharDistantBattle', 4.0),
    ('ride:go', 'enable', 'timer_elevator_spawn', 15.0), ('ride:go', 'enable', 'timer_elevator_crawlers_1', 15.0),
    ('ride:go', 'slomo', '', 16.0), ('ride:go', 'spawn', 'ins_para_spawn', 17.0),
    # timer_elevator_spawn: every group stopped, one picked again a tenth later (case_elevator_spawn).
    ('timer:timer_elevator_spawn', 'stop', 'ElevatorSpawn_group*', 0.0),
    ('timer:timer_elevator_spawn', 'pick', _GROUPS, 0.1),
    # timer_elevator_crawlers_1: a drone climbs down a shaft wall and drops onto the deck (ElevatorSpawn_crawl_*).
    ('timer:timer_elevator_crawlers_1', 'crawl', 'ElevatorSpawn_crawl_1|ElevatorSpawn_crawl_2', 0.1),
    # The walls' path_tracks, as parts of the ride: parasites on Insane, the crawlers stop at three quarters.
    ('ride:13', 'spawn', 'ins_para3_spawn', 0.0), ('ride:57', 'spawn', 'ins_para2_spawn', 5.0),
    ('ride:75', 'disable', 'timer_elevator_crawlers_1', 0.0),
    # elevator_walls_end: the exit's drones, the groups stop five seconds later.
    ('ride:end', 'spawn', 'ExitSpawner', 0.0), ('ride:end', 'spawn', 'ins_para_spawn4', 0.5),
    ('ride:end', 'stop', 'ElevatorSpawn_group*', 5.0), ('ride:end', 'disable', 'timer_elevator_spawn', 5.0),
    ('ride:end', 'musicstop', '', 12.0),
]
TIMERS = [('timer_elevator_spawn', 2.0, 3.5, False), ('timer_elevator_crawlers_1', 1.5, 2.0, False)]
MOVERS = []

LINES = {
    'co_m1_ob7': 'The cargo elevator at the end of this section is your way down to the colony. Move.',
    'co_m1_ob8': 'You\'re down. Get to the exit, the colony is through there.',
}

CHECKPOINTS = [SPAWN, (24.5, 40.0), (25.5, 74.5), (32.0, 112.0), (46.0, 113.0), (56.0, 112.0)]
ZONES = []
# The autopilot's way through: x, y, wait (2 until the ride is over).
ROUTE = [
    (7.5, 12.5, 0), (5.5, 16.5, 0), (5.5, 29.5, 0), (10.5, 33.5, 0), (24.5, 34.5, 0), (24.5, 45.5, 0), (26.0, 54.5, 0), (26.0, 58.5, 0),
    (25.5, 66.5, 0), (25.5, 74.5, 0), (21.5, 79.5, 0), (21.5, 101.5, 0), (24.5, 106.5, 0), (31.5, 106.5, 0), (31.5, 110.5, 0),
    (38.5, 112.5, 0), (41.0, 113.0, 0), (46.0, 113.0, 2), (51.0, 113.0, 0), (56.5, 112.5, 0), (57.5, 108.5, 0),
    (66.5, 108.5, 0), (69.0, 111.0, 0),
]
