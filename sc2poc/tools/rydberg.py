"""Mission 4, RYDBERG REACTOR: after Alien Swarm's asi-jac3-rydberg.

Traced from the map itself (tools/astrace.py), as tools/deima.py is: the deck is AS's walkable floor in 80-unit
cells, the drops are its asw_trigger_fall volumes (the reactor's core well, the coolant shaft, a broken floor),
and the entity lump gave the doors, panels, buttons, spawners and the triggers that start them. Nothing of
Valve's is shipped: these are numbers and rectangles.

The flow is the original's: the squad comes in at the plant's south loading dock and works north through the
pump halls and coolant galleries to the reactor control room, whose door a tech must hack while rangers come in
over the railings; inside, a button on the control panel brings the reactor back online (objective 1, "Bring the
reactor online"). With the power on, the airlock panel by the coolant shaft works: it opens the airlock into the
turbine hall, where the swarm holds the doors. At the north exit a button starts the great doors opening, and
they take their time; the squad holds until they are open and gets out (objective 2, "Get to the north exit").

Same data shape as tools/level.py; tools/level.py `use()` swaps it in.
Coordinates are map units, x east, y north. Cells are 1 x 1.
"""
import math

import numpy as np

from tools.astrace import Trace, components, grow

_T = Trace('asi-jac3-rydberg', 0, 0, 74, 122)
W, H = _T.W, _T.H
FLOOR = 8.0
WALL_H = 2.5
HEIGHTS = _T.HEIGHTS
DECK_Z = 608.0                  # the plant's main floor; the turbine hall lies a step lower (544)


def _cells(box):
    """The cells whose middles lie inside a traced box (x0, y0, x1, y1)."""
    x0, y0, x1, y1 = box
    m = np.zeros((H, W), bool)
    for y in range(H):
        for x in range(W):
            m[y, x] = x0 <= x + 0.5 <= x1 and y0 <= y + 0.5 <= y1
    return m


# The drops (asw_trigger_fall): the reactor's core well beside the control room's lower step (opened here; its north
# rows stay the walkway to the panel), the coolant shaft, and the pit beside the coolant gallery. AS's fall volumes
# lie under the floor, so the shaft and the pit open only where the trace finds no floor over them.
_WELL = _cells((17.65, 109.5, 21.65, 113.0))
_FALLS = _WELL | _cells((35.54, 62.0, 47.0, 72.76)) | _cells((21.69, 89.75, 26.68, 95.78))
DECK = _T.deck() & ~_WELL
# The north exit room (AS's exit_ceiling, x 44.4-54 y 112.8-120) walled off from the turbine hall but for its great
# doors (Exit_Block, x 46.6-48.2): the trace runs the hall's floor on round its sides.
DECK[115, 38:44] = False
DECK[114, 44:46] = False
DECK[114, 48:54] = False
# Lower floors the trace finds nothing standing on, beside the deck (the loading pits): open too.
OPEN = (_FALLS | (_T.below(400.0) & _T.known())) & ~DECK & grow(DECK, 8)
# A gap one cell across between two floors is a railing's or a wall's, not a drop: hull (twice, for the strips
# that leaves), and drops of a few cells go too.
for _ in range(2):
    _d = np.pad(DECK, 1)
    OPEN &= ~((_d[1:-1, :-2] & _d[1:-1, 2:]) | (_d[:-2, 1:-1] & _d[2:, 1:-1]))
OPEN = components(OPEN, 6)

AREAS = [
    ('Loading Dock',        (0, 8, 10, 23), 'works'),
    ('South Plant',         (0, 23, 24, 44), 'works'),
    ('Pump Hall',           (5, 44, 36, 66), 'hall'),
    ('Coolant Shaft',       (26, 62, 50, 88), 'works'),
    ('West Stores',         (0, 66, 26, 88), 'cargo'),
    ('Coolant Gallery',     (13, 88, 36, 106), 'works'),
    ('Reactor Control',     (13, 106, 34, 121), 'core'),
    ('Airlock',             (36, 86, 46, 94), 'hall'),
    ('Turbine Hall',        (40, 94, 74, 113), 'works'),
    ('North Exit',          (40, 113, 62, 122), 'hall'),
]
BLOCKS = []
VIEWPORTS = []
SPAWN = (7.5, 12.5)
SPAWN_FACING = 90.0
LIFT = None
VOID = None
WINDOWS = []
# Indoors: the plant's own lamps and the reactor's glow; no sky.


# Lamps (x, y, kind, flicker), from the map's lights: Rydberg is lit sodium orange (its fog is orange too), with
# white work lamps, the reactor's cold blue glow and the red alarm lamps by the exit.
def _lights():
    out = []
    for e in _T.entities:
        if e['class'] not in ('light', 'light_spot'):
            continue
        x, y = _T.where(e)
        if not (0 <= x < W and 0 <= y < H):
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
    (19.8, 111.0, 'coldbig', 0), (45.0, 64.0, 'coldbig', 0),       # the core and the coolant shaft glow
    (47.5, 111.0, 'red', 3),                                        # the exit's alarm
]

# Room dressing: (model, x, y, facing degrees, scale, solid radius or 0).
PROPS = [
    # The reactor's core rising out of its well beside the control room (tools/pitart.py KPitCore), on the pit floor.
    ('KPitCore', 20.0, 111.0, 0.0, 1.0, 0.0),
    # Control room consoles, pump hall machinery, crates on the loading dock.
    ('KPConsole', 23.5, 117.5, 0.0, 1.0, 0.0), ('KPConsole', 27.5, 117.5, 0.0, 1.0, 0.0),
    ('SpacePlatformGenerator', 10.0, 50.0, 90.0, 0.6, 0.0), ('SpacePlatformGenerator', 30.0, 60.0, 270.0, 0.6, 0.0),
    ('KPReactor', 21.0, 47.0, 0.0, 0.6, 0.0), ('SpacePlatformSteamVent', 14.0, 58.0, 0.0, 0.6, 0.0),
    ('DOM_Crate', 3.0, 20.0, 20.0, 0.9, 0.0), ('DOM_Crate', 8.5, 21.0, 70.0, 0.9, 0.0),
    ('ElectricalArcs', 45.0, 100.0, 0.0, 0.7, 0.0), ('SpacePlatformSteamVent', 60.0, 105.0, 0.0, 0.7, 0.0),
]

# ---- the mission ---------------------------------------------------------
DOORS = [
    ('reactor',     (22, 109, 26, 110), 'panel', 0.0, (22.6, 108.4)),
    ('airlock',     (40, 88, 42, 89), 'jammed', 0.0, None),
    ('plant10',     (38, 94, 42, 95), 'auto', 0.0, None),
    ('exit',        (46, 114, 48, 115), 'jammed', 0.0, None),
]
PANEL_WIRES = (3, 6, 3)
CONSOLE = (22.6, 108.4)
NEEDS_TECH = True                # asw_tech_marine_req, lifted once the reactor door is open
EXTRACT = (45, 115, 54, 120)     # objective_escape's trigger_multiple
EXTRACT_NAME = 'the north exit'
OBJECTIVES = [
    ('reactor', 'Bring the reactor online', True, (22.1, 114.4)),
    ('escape', 'Get to the north exit', False, None),
]
DESCRIPTION = ('The Rydberg power plant feeds the whole colony, and it has gone dark. Fight up through the pump halls '
               'to reactor control, get a tech through its door and bring the reactor back online, then get the plant\'s '
               'north doors open and hold until they are.')
BUTTONS = [
    ('ReactorPanel', (20.6, 113.5), 'Start the reactor', True),
    ('reactor_button2', (39.8, 87.1), 'Open the airlock', False),
    ('exit_door_button', (48.7, 112.5), 'Open the exit doors', True),
]
PDAS = [((22.4, 38.7), 'Ellen Marsh', 6), ((45.5, 99.1), 'Tomas Reyes', 7)]
MAILS = {
    6: ('Ellen Marsh', 'Coolant alarms', 'Third coolant alarm tonight and nobody from reactor control is picking up. The shaft '
        'doors are jammed open and something keeps knocking the pumps off line.\nI am going up there myself. If the core '
        'scrams the whole colony goes dark.'),
    7: ('Tomas Reyes', 'North doors', 'The north doors are on the reactor bus. No power, no doors, and the hand crank is '
        'seized.\nWe are holding the turbine hall. If you get the reactor up, open the doors and do not wait for us.'),
}
PICKUPS = [('sentry', 8.1, 77.5)]
SENTRY_SPOT = (26.0, 106.0)
AMMO = [(21.5, 115.0), (30.0, 60.0)]
SLEEPERS = []
BARRELS = [(22.2, 108.0), (34.5, 77.1), (19.9, 96.6), (27.8, 106.7), (25.0, 106.6), (27.7, 67.5), (23.4, 48.8)]
EGGS = []
BIOMASS = []
CREEP = []


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

# Triggers: rectangle, once, chance, [(action, argument, delay)], options (trigger_asw_chance's chance is 0.5).
TRIGGERS = [
    ((4.5, 18.0, 9.5, 19.5), True, 1.0, [('line', 'co_m3_ob1', 0.5)]),
    ((15.5, 26.0, 18.5, 27.5), True, 1.0, [('spawn', 'DroneSpawnStart', 0.0)]),
    ((6.0, 23.5, 9.5, 24.5), True, 0.5, [('spawn', 'DroneSpawnRandom6', 0.0)]),
    ((6.0, 22.5, 9.5, 23.5), True, 0.5, [('spawn', 'DroneSpawnRandom5', 0.0)]),
    ((6.0, 21.5, 9.5, 22.5), True, 0.5, [('spawn', 'DroneSpawnRandom4', 0.0)]),
    ((14.5, 40.5, 18.5, 42.0), True, 1.0, [('spawn', 'DroneSpawn1', 0.0), ('spawn', 'DroneSpawnPipes', 2.0),
                                           ('pick', 'Insane_Drone_Spawn02|Insane_Drone_Spawn01', 0.0)]),
    ((22.5, 45.0, 24.5, 51.0), True, 0.5, [('spawn', 'DroneHole1', 0.0)]),
    ((14.5, 47.5, 29.0, 49.5), True, 0.5, [('spawn', 'randomspawn2', 0.0)]),
    ((14.5, 49.3, 22.0, 51.0), True, 0.5, [('spawn', 'randomspawnleft', 0.0)]),
    ((19.0, 52.0, 28.5, 53.5), True, 1.0, [('spawn', 'DroneSpawn2', 0.0)]),
    ((19.0, 53.5, 28.5, 54.5), True, 0.5, [('spawn', 'DroneHole2', 1.0)]),
    ((18.0, 56.5, 30.0, 57.5), True, 1.0, [('spawn', 'DroneSpawn3', 0.0), ('pick', 'Insane_spawner4|Insane_spawner3', 0.0)]),
    ((24.5, 62.0, 28.0, 63.0), True, 0.5, [('spawn', 'DroneSpawnRandom1', 1.0)]),
    ((24.5, 63.0, 28.0, 64.0), True, 0.5, [('spawn', 'DroneSpawnRandom3', 0.0)]),
    ((34.5, 75.0, 44.0, 76.0), True, 1.0, [('spawn', 'InfiniteSpawn1', 0.0)]),
    ((35.0, 79.5, 44.5, 80.5), True, 1.0, [('spawn', 'BuzzerSpawn2', 0.0), ('pick', 'Insane_spawner6|Insane_spawner5', 0.0)]),
    ((15.0, 81.0, 19.0, 82.5), True, 0.5, [('spawn', 'DroneRandomSpawn1', 0.0)]),
    ((35.0, 82.5, 37.5, 83.5), True, 1.0, [('spawn', 'platform_drone_attack01', 0.0)]),
    ((17.0, 99.5, 25.0, 100.7), True, 1.0, [('stop', 'platform_drone_attack01', 0.0)]),
    # Reactor control's approach: rangers over the railings once a hand is on the door panel (random_ranger_trigger).
    ((21.0, 106.0, 32.5, 109.7), True, 1.0, [('fire', 'spawn_group_04', 0.0)], {'name': 'random_ranger_trigger', 'off': True}),
    ((22.5, 109.8, 25.5, 111.0), True, 1.0, [('stop', 'DroneSpawn12', 0.0), ('stop', 'ranger_spawn01', 0.0)]),
    # Once the reactor is on (trigger_reactor_activated, trigger_reactor_online: enabled by the panel).
    ((32.5, 83.5, 34.0, 87.0), True, 1.0, [('spawn', 'DroneSpawn10', 0.0)], {'name': 'trigger_reactor_activated', 'off': True}),
    ((29.0, 104.5, 32.5, 106.0), True, 1.0, [('spawn', 'DroneSpawn8', 0.0)], {'name': 'trigger_reactor_online', 'off': True}),
    ((38.5, 84.5, 44.0, 86.0), True, 1.0, [('spawn', 'DroneSpawn9', 0.0)], {'name': 'trigger_reactor_online', 'off': True}),
    ((35.0, 83.5, 37.0, 87.0), True, 1.0, [('spawn', 'InfiniteSpawn3', 0.0)], {'name': 'trigger_reactor_online', 'off': True}),
    # Through the airlock: the holdout at its doors stops.
    ((38.5, 94.5, 44.0, 96.5), True, 1.0, [('spawn', 'DroneSpawn9', 0.0), ('stop', 'door_holdout01', 0.0),
                                           ('stop', 'door_holdout02', 0.0), ('stop', 'door_holdout03', 0.0)]),
    ((37.5, 95.5, 49.5, 97.0), True, 0.5, [('spawn', 'DroneSpawn13', 6.0)]),
    ((52.5, 97.5, 54.0, 101.5), True, 1.0, [('music', 'finale', 0.0)]),
    ((61.0, 105.5, 69.0, 106.5), True, 1.0, [('spawn', 'ranger_window', 0.0), ('spawn', 'drone_hole3', 0.0),
                                             ('spawn', 'drone_hole4', 0.0), ('spawn', 'Insane_spawner7', 0.0)]),
]
ONS = [
    # The reactor door's panel: rangers come over the railings while it is hacked (spawn_group_04, one each).
    ('hackstart:reactor', 'enable', 'random_ranger_trigger', 0.0),
    ('spawn_group_04', 'spawnone', 'ranger_reactor_spawn_01a', 0.0), ('spawn_group_04', 'spawnone', 'ranger_reactor_spawn_01b', 1.0),
    ('spawn_group_04', 'spawnone', 'ranger_reactor_spawn_01c', 3.0),
    ('hacked:reactor', 'spawn', 'reactor_boomer_spawn', 0.0), ('hacked:reactor', 'notech', '', 0.0),
    # The reactor panel: the reactor online, the airlock powered, the escape shown.
    ('pressed:ReactorPanel', 'complete', 'reactor', 2.0), ('pressed:ReactorPanel', 'power', 'reactor_button2', 0.0),
    ('pressed:ReactorPanel', 'enable', 'trigger_reactor_activated', 0.0), ('pressed:ReactorPanel', 'enable', 'trigger_reactor_online', 0.0),
    ('pressed:ReactorPanel', 'spawn', 'DroneSpawnRandom3', 0.0),
    ('pressed:ReactorPanel', 'pick', 'Insane_parasites1|Insane_parasites2', 0.0),
    ('pressed:ReactorPanel', 'line', 'co_m3_ob2', 3.5), ('pressed:ReactorPanel', 'line', 'co_m3_ob3', 17.0),
    ('pressed:ReactorPanel', 'lights', '3', 1.0),
    # The airlock (reactor_button2): it opens, the swarm comes at its doors.
    ('pressed:reactor_button2', 'open', 'airlock', 0.0), ('pressed:reactor_button2', 'stop', 'InfiniteSpawn3', 0.0),
    ('pressed:reactor_button2', 'spawn', 'DroneSpawn14', 0.0), ('pressed:reactor_button2', 'spawn', 'door_holdout01', 0.0),
    ('pressed:reactor_button2', 'spawn', 'door_holdout02', 1.5), ('pressed:reactor_button2', 'spawn', 'door_holdout03', 2.0),
    # The north doors (Exit_door_relay, Exit_door_relay2): steam, then the great doors grind open while the swarm
    # comes for the squad holding them.
    ('pressed:exit_door_button', 'spawn', 'boomer_hole_spawn', 5.0), ('pressed:exit_door_button', 'spawn', 'exit_spawner', 25.0),
    ('pressed:exit_door_button', 'spawn', 'exit_buzzers', 44.0),
    ('pressed:exit_door_button', 'boom', '47.5,113.5', 0.5),
    ('pressed:exit_door_button', 'open', 'exit', 32.0),
]
TIMERS = []
MOVERS = []

LINES = {
    'co_m3_ob1': 'This is the Rydberg plant. Get to the reactor core and bring the power back up: the colony\'s running on batteries.',
    'co_m3_ob2': 'Reactor\'s online, power is coming back across the colony. Don\'t stop now, keep moving.',
    'co_m3_ob3': 'Squad, listen. We\'ve lost the colony. Command is drawing up a plan to nuke the site from orbit. Get through the north doors and head for the residential sector.',
}

CHECKPOINTS = [SPAWN, (20.0, 52.0), (40.0, 78.0), (24.0, 104.0), (41.5, 90.0), (48.0, 108.0)]
ZONES = []
# The autopilot's way through (worked out over the deck, breadth first between the stops): x, y, wait (1 the panel by
# it hacked, 5 the button by it pressed, 6 the door by it open).
ROUTE = [
    (7.5, 26.5, 0), (8.5, 31.5, 0), (14.5, 33.5, 0), (16.5, 46.5, 0), (23.5, 60.5, 0), (26.5, 65.5, 0),
    (31.5, 79.5, 0), (31.5, 84.5, 0), (23.5, 86.5, 0), (23.5, 100.5, 0), (22.6, 108.4, 1), (23.5, 111.5, 0),
    (22.5, 114.5, 0), (21.5, 113.5, 5), (22.5, 113.5, 0), (22.5, 99.5, 0), (24.5, 86.5, 0), (31.5, 83.5, 0),
    (36.5, 78.5, 0), (38.5, 78.5, 0), (39.5, 86.5, 5), (40.8, 87.2, 6), (41.0, 95.5, 0), (46.5, 109.5, 0),
    (48.5, 111.5, 5), (47.0, 113.5, 6), (48.5, 117.5, 0),
]
