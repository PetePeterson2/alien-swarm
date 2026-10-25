"""Mission 3, DEIMA SURFACE BRIDGE: after Alien Swarm's asi-jac2-deima.

Traced from the map itself (tools/astrace.py): the deck is the real walkable floor in 80-unit cells, the
open drop is wherever nothing stands within reach below it, and the entity lump gave the doors, the
panels and buttons, every asw_spawner and the triggers and relays that start them. Nothing of Valve's is
shipped: these are numbers and rectangles.

The flow is the original's: the squad lands at the south end of the colony on Deima's night side, in
snow, under a lightning storm; sweeps north through the colony streets (roof drops, a truck yard) to the
colony gate, where a tech hacks the gate panel while the swarm comes over the fences (objective 1, "Gain
access to the pipeline"); north over the catwalks strung across the chasm, where a button runs the bridge
ramp out over a gap; at the pump station the miners' charges are wired to a detonator: setting them off
blows the pipeline the swarm runs through and wakes a shieldbug (objective 2, "Destroy the infested
pipeline"); up to the pipeline bridge, whose gate a tech must hack. The bridge's lights are out: the dropship
Bloodhound flies alongside it, lamps and turrets covering the squad as it crosses, then hovers over the
broken last span so the squad can cross on its back to the reactor entrance (objective 3, "Get to the
Colony Reactor entrance").

Same data shape as tools/level.py; tools/level.py `use()` swaps it in.
Coordinates are map units, x east, y north. Cells are 1 x 1.
"""
import math

import numpy as np

from tools.astrace import Trace, grow, box

_T = Trace('asi-jac2-deima', 0, 2, 164, 162)
W, H = _T.W, _T.H
FLOOR = 8.0
WALL_H = 2.5
HEIGHTS = _T.HEIGHTS
DECK_Z = -64.0                  # the colony streets and the bridge: the level's main floor

# The deck: AS's walkable floor. The pipeline beside the bridge is walkable in AS's nav mesh (its top), but it
# is the giant pipe the squad blows, so it goes into the drop and the pipe stands in it.
_walk = _T.deck()
_pipe = box(_walk & (np.nan_to_num(_T.walk_z, nan=-1e9) > 30.0), 70, 103, 164, 112)
DECK = _walk & ~_pipe
# The ramp's gap (move_ramp_*: the bridge ramps run out over it), and the railing the trace makes of its far end.
DECK[89:92, 50:55] = True
# The ship's crossing at the bridge's east end: the gap she hovers over (brush_shipbridge) is deck the squad may
# only walk once she is there (DOORS 'shipdeck').
DECK[116:121, 134:142] = True
# The drop: the chasm the colony's catwalks cross (AS's floor far below, 768 units down), out to twelve cells
# from the deck; past that the camera never looks.
OPEN = (_T.below(-400.0) | _pipe) & ~DECK & grow(DECK, 12)
# AS's railings and kerbs along the drop trace as hull a cell or two thick between deck and drop: they go into the
# drop, so the walkway's edge gets its railing (tools/level.py) instead of a slab hiding the squad.
for _ in range(2):
    _hull = ~DECK & ~OPEN
    _thick = ~grow(~_hull, 1)
    _thin = _hull & ~grow(_thick, 1) & grow(OPEN, 1) & grow(DECK, 2)
    OPEN = OPEN | _thin
OUTDOORS = (0, 0, W, H)         # under the storm: snow falls everywhere
SNOW_ROOFS = True               # the hull is the colony's buildings and the rock: snow on top (src/Kit.galaxy KR caps)

AREAS = [
    ('Landing Zone',        (6, 0, 34, 26), 'surface'),
    ('Colony Street',       (0, 26, 72, 60), 'surface'),
    ('Colony Gate',         (38, 58, 72, 72), 'surface'),
    ('West Catwalks',       (0, 60, 40, 104), 'bridge'),
    ('Gate Catwalk',        (40, 70, 66, 104), 'bridge'),
    ('Pump Station',        (66, 62, 96, 104), 'plant'),
    ('Pipeline Stair',      (66, 104, 76, 112), 'plant'),
    ('Pipeline Bridge',     (66, 112, 150, 121), 'bridge'),
    ('Reactor Approach',    (110, 121, 164, 162), 'surface'),
]
BLOCKS = []
VIEWPORTS = []
SPAWN = (16.4, 5.3)
SPAWN_FACING = 90.0
LIFT = None
VOID = None
WINDOWS = []


def _snap(x, y, reach=8):
    """The nearest deck cell's middle to (x, y) within `reach` (AS's spawners stand on roofs and in alcoves the
    trace leaves out); None when there is none."""
    ix, iy = int(x), int(y)
    if 0 <= ix < W and 0 <= iy < H and DECK[iy, ix]:
        return (x, y)
    best = None
    for dy in range(-reach, reach + 1):
        for dx in range(-reach, reach + 1):
            cx, cy = ix + dx, iy + dy
            if 0 <= cx < W and 0 <= cy < H and DECK[cy, cx] and not (134 <= cx < 142 and 116 <= cy < 121):
                d = dx * dx + dy * dy
                if best is None or d < best[0]:
                    best = (d, cx + 0.5, cy + 0.5)
    return best and best[1:]


# Lamps (x, y, kind, flicker), from the map's own lights above the drop: the colony's cyan floods (140 215 205),
# the pale-blue big lamps (137 214 218), the red lamps strung along the bridge (175 41 27), one sodium yellow.
def _lights():
    out = []
    for e in _T.entities:
        if e['class'] not in ('light', 'light_spot') or e['origin'][2] < -300:
            continue
        x, y = _T.where(e)
        if not (0 <= x < W and 0 <= y < H):
            continue
        r, g, b, a = (float(v) for v in e['keys'].get('_light', '255 255 255 100').split()[:4])
        if r > 160 and g < 80:
            kind = 'red'
        elif r > 130 and b < 120:
            kind = 'yellow'
        else:
            kind = 'coldbig' if a >= 200 else 'cold'
        if any(math.hypot(x - ox, y - oy) < 3.5 for ox, oy, _, _ in out):
            continue
        out.append((x, y, kind, 1 if kind == 'red' else 0))
    return out


LIGHTS = _lights() + [
    # The pump station's sodium work lamps and the gate's alarm (AS's gate_controller), turning while it is hacked.
    (72.0, 80.0, 'orangebig', 0), (74.0, 92.0, 'orange', 2), (50.0, 63.5, 'red', 3),
]

# Room dressing: (model, x, y, facing degrees, scale, solid radius or 0).
PROPS = [
    # The landing pad and the colony street: freight left in the snow, the caution lights round the pad.
    ('SpacePlatformCautionLights', 12.8, 5.0, 90.0, 0.8, 0.0), ('SpacePlatformCautionLights', 19.8, 5.0, 270.0, 0.8, 0.0),
    ('DOM_Crate', 10.5, 17.5, 25.0, 0.9, 0.0), ('DOM_Crate', 25.5, 20.0, 70.0, 0.9, 0.0),
    ('StarshipContainers', 9.5, 30.0, 0.0, 0.5, 0.0), ('StarshipContainers', 26.0, 31.0, 90.0, 0.5, 0.0),
    ('DOM_RocketPallet', 38.0, 40.0, 30.0, 0.7, 0.0), ('DOM_Crate', 41.0, 46.5, 10.0, 0.9, 0.0),
    ('SpacePlatformSteamVent', 22.0, 52.0, 0.0, 0.6, 0.0), ('DOM_Crate', 60.0, 46.0, 50.0, 0.9, 0.0),
    # The gate: its controller and floodlights.
    ('SpacePlatformCautionLights', 42.2, 66.0, 90.0, 0.8, 0.0), ('SpacePlatformCautionLights', 46.8, 66.0, 270.0, 0.8, 0.0),
    ('DOM_LabConsoles', 52.5, 60.0, 0.0, 0.6, 0.0),
    # The pump station: generators, the miners' charges by the detonator, arcing cable.
    ('SpacePlatformGenerator', 70.0, 72.0, 0.0, 0.6, 0.0), ('SpacePlatformGenerator', 76.0, 72.0, 0.0, 0.6, 0.0),
    ('KPReactor', 70.5, 84.0, 0.0, 0.6, 0.0), ('KPReactor', 76.5, 84.0, 0.0, 0.6, 0.0),
    ('ElectricalArcs', 73.5, 78.0, 0.0, 0.7, 0.0), ('SpacePlatformSteamVent', 67.5, 96.0, 0.0, 0.7, 0.0),
    ('DOM_RocketPallet', 59.0, 88.0, 90.0, 0.6, 0.0), ('DOM_Crate', 57.0, 86.5, 15.0, 0.8, 0.0),
    # The reactor approach.
    ('SpacePlatformCautionLights', 136.0, 123.0, 0.0, 0.8, 0.0), ('DOM_Crate', 150.0, 128.0, 40.0, 0.9, 0.0),
    ('SpacePlatformGenerator', 152.0, 138.0, 90.0, 0.6, 0.0),
] + [
    # The main pipeline in the drop beside the bridge (tools/pitart.py KPitMain), laid on the pit floor.
    ('KPitMain', x + 2.0, 107.5, 0.0, 1.0, 0.0) for x in range(76, 160, 4)
]

# ---- the mission ---------------------------------------------------------
# Doors: name, cells (x0, y0, x1, y1), kind, seal, panel or None (tools/level.py). Beside the colony's own:
# 'gap' the ramp runs out over once opened; 'block' an unseen barrier (the pump station's wreckage until the
# charges go); 'hover' a drop the squad crosses once the dropship hangs over it.
DOORS = [
    ('gate',        (43, 67, 46, 68), 'panel', 0.0, (51.7, 61.2)),
    ('ramp',        (50, 89, 55, 92), 'gap', 0.0, None),
    ('debris',      (62, 85, 64, 92), 'block', 0.0, None),
    ('bridgegate',  (71, 112, 72, 116), 'panel', 0.0, (70.4, 115.2)),
    ('shipdeck',    (134, 116, 142, 121), 'hover', 0.0, None),
]
PANEL_WIRES = (2, 5, 3)            # the gate panel (trigger_asw_button_area: wirerows 2, wirecolumns 5, numwires 3)
CONSOLE = (51.7, 61.2)
NEEDS_TECH = True                # asw_tech_marine_req, lifted once the bridge gate is hacked
EXTRACT = (141, 133, 145, 137)   # the reactor entrance (objective_escape's trigger_multiple)
EXTRACT_NAME = 'the reactor entrance'
# Objectives in order (asw_objective_triggered, asw_objective_escape): key, title, shown at the start, marker spot.
OBJECTIVES = [
    ('gate', 'Gain access to the pipeline', True, (49.3, 57.2)),
    ('pipe', 'Destroy the infested pipeline', True, (60.7, 90.8)),
    ('escape', 'Get to the Colony Reactor entrance', True, None),
]
DESCRIPTION = ('Deima\'s surface, night side, in a snowstorm. The swarm is moving through the colony\'s main pipeline: '
               'get through the colony gate, set off the miners\' charges at the pump station, and cross the pipeline '
               'bridge to the reactor. A tech must open the gates.')
# Buttons (trigger_asw_button_area, no lock): name, spot, label, powered.
BUTTONS = [
    ('openBridgeButton', (48.5, 91.0), 'Extend the bridge', True),
    ('DetonateBridgeButton', (60.7, 90.9), 'Detonate the charges', True),
]
PDAS = [((11.0, 19.3), 'John Cain', 4), ((73.8, 95.5), 'Brian Howe', 5)]
MAILS = {
    4: ('John Cain', 'Pipeline crews', 'The pump crews stopped answering at the start of night shift. Whatever is in the line '
        'is coming up through the filters faster than we can shut them.\nMaintenance has left charges on the main pipe by '
        'the pump station. If it comes to it, somebody has to blow it.'),
    5: ('Brian Howe', 'Detonator', 'Charges are set and wired. The detonator is on the catwalk past the ramp.\nI pulled the '
        'bridge lights to keep them off us. If you are reading this, I did not make the reactor. Do not go across in the dark.'),
}
PICKUPS = [('sentry', 25.5, 46.5)]
SENTRY_SPOT = (48.5, 63.5)
AMMO = [(68.3, 114.4), (20.0, 9.5)]
SLEEPERS = [('AS_SHIELDBUG', 66.2, 89.4)]
BARRELS = [(19.9, 27.3), (18.9, 32.3), (34.7, 92.3)]
EGGS = []
BIOMASS = []
CREEP = []


# asw_spawner, one per row (tools/landingbay.py), every one the map can start, set down on the nearest deck.
def _spawners():
    out = []
    for row in _T.spawners():
        at = _snap(row[1], row[2])
        if at is None:
            continue
        out.append((row[0], round(at[0], 1), round(at[1], 1)) + tuple(row[3:]))
    return out


SPAWNERS = _spawners()
# The director's vents: the spawners' spots six cells apart at least, south to north.
VENTS = []
for _s in sorted(SPAWNERS, key=lambda s: s[2]):
    if len(VENTS) < 32 and all(math.hypot(_s[1] - vx, _s[2] - vy) >= 6.0 for vx, vy in VENTS):
        VENTS.append((_s[1], _s[2]))

# Triggers: rectangle, once, chance, [(action, argument, delay)], options. AS's thin brush triggers are widened
# to span the street or walkway they cross.
TRIGGERS = [
    ((13.0, 6.5, 20.0, 8.5), True, 1.0, [('line', 'co_m2_start', 1.5)]),
    ((19.5, 13.5, 32.5, 15.5), True, 1.0, [('spawn', 'start_roof_spawn', 0.0)]),
    ((14.5, 15.5, 16.5, 22.0), True, 1.0, [('spawn', 'start_roof_spawn_02', 0.5)]),
    ((15.5, 22.5, 28.5, 24.5), True, 1.0, [('spawn', 'start_roof_spawn_03', 0.0), ('pick', 'WindowSpawner6|WindowSpawner5', 0.0),
                                           ('pick', 'start_roof_spawn_03_back1a|start_roof_spawn_03_back1b', 0.0)]),
    ((6.5, 34.0, 21.0, 36.0), True, 1.0, [('pick', 'truck_spawn_01|truck_spawn_02|truck_spawn_03', 0.0)]),
    ((22.0, 36.5, 29.5, 42.0), True, 1.0, [('pick', 'truck_spawn_04|truck_spawn_05', 0.0)]),
    ((15.5, 42.5, 29.5, 44.5), True, 1.0, [('pick', 'path_1_spawn_01|path_1_spawn_02', 1.0), ('pick', 'WindowSpawner7|WindowSpawner8', 1.0),
                                           ('spawn', 'spawn_ins_mortar', 0.0)]),
    ((26.5, 59.5, 28.0, 67.5), True, 1.0, [('spawn', 'distance_ranger', 0.0)]),
    # Past the gate: one of three ambushes on the catwalk is armed.
    ((42.5, 67.0, 46.5, 68.5), True, 1.0, [('pickfire', 'ambush_01|ambush_02|ambush_03', 1.0), ('line', 'co_m2_ob1b', 0.0),
                                           ('spawn', 'spawn_ins_mortarbrig', 0.0)]),
    ((42.5, 78.5, 46.5, 80.0), True, 1.0, [('spawn', 'bridge_spawn_04a', 0.0)], {'name': 'trigger_ambush_01', 'off': True}),
    ((39.5, 86.5, 46.5, 88.0), True, 1.0, [('spawn', 'bridge_spawn_04b', 0.0)], {'name': 'trigger_ambush_02', 'off': True}),
    ((44.0, 88.5, 45.5, 92.5), True, 1.0, [('spawn', 'bridge_spawn_04c', 0.0)], {'name': 'trigger_ambush_03', 'off': True}),
    ((42.5, 80.5, 46.5, 81.5), True, 1.0, [('spawn', 'bridge_jumper', 0.0)]),
    ((36.5, 72.5, 38.0, 76.5), True, 1.0, [('pick', 'bridge_spawn_01|bridge_spawn_2', 0.0)]),
    ((31.5, 72.5, 33.0, 76.5), True, 1.0, [('pick', 'bridge_spawn_3|bridge_spawn_2|bridge_spawn_01', 0.0)]),
    ((46.5, 88.5, 48.0, 92.5), True, 1.0, [('line', 'co_m2_pipeline', 0.0)]),
    # Up the pump stair: the power's out on the bridge; at the top the Bloodhound comes in alongside.
    ((66.0, 104.5, 76.0, 106.0), True, 1.0, [('line', 'co_m2_powerout', 0.0), ('stop', 'spawner_pipe_drone', 0.0)]),
    ((66.0, 110.5, 79.0, 112.0), True, 1.0, [('move', 'ship', 0.1), ('shipguns', 'ship', 0.1), ('line', 'co_m2_stayinlight', 2.5)]),
    # Through the bridge gate: she runs on east with the squad; drones come up over both rails.
    ((71.5, 112.0, 72.5, 116.0), True, 1.0, [('move', 'ship', 0.0)]),
    ((72.5, 112.0, 74.0, 116.0), True, 1.0, [('spawn', 'bridge_spawn', 0.0)]),
    ((78.5, 112.0, 80.0, 116.0), True, 1.0, [('spawn', 'bridge_spawn_back', 0.0)]),
    ((84.5, 112.0, 86.0, 116.0), True, 1.0, [('stop', 'bridge_spawn', 0.0)]),
    ((89.0, 112.0, 90.5, 116.0), True, 1.0, [('spawn', 'bridge_jumper_01', 1.0), ('stop', 'bridge_spawn_back', 0.0)]),
    ((95.5, 112.0, 97.0, 116.0), True, 1.0, [('spawn', 'bridge_jumper_02', 0.0), ('spawn', 'bridge_spawn_back2', 3.0),
                                             ('spawn', 'spawn_ins_mortar2', 0.0)]),
    ((102.0, 112.0, 103.5, 116.0), True, 1.0, [('spawn', 'bridge_spawn2', 0.0)]),
    ((108.0, 112.0, 109.5, 116.0), True, 1.0, [('spawn', 'bridge_spawn_shield_2', 0.0)]),
    ((126.0, 112.0, 127.5, 116.0), True, 1.0, [('stop', 'bridge_jumper_02', 0.0), ('stop', 'bridge_spawn_back2', 2.0)]),
    # The squad at the broken span, with her over it.
    ((134.0, 112.0, 142.0, 116.0), True, 1.0, [('line', 'co_m2_getaccross', 0.0)]),
    ((131.5, 112.0, 134.0, 116.0), True, 1.0, [('stop', 'bridge_spawn2', 0.0), ('stop', 'bridge_spawn_shield_2', 0.0)]),
    ((134.0, 120.0, 142.0, 122.0), True, 1.0, [('spawn', 'bridge_accross', 0.0)]),
]
# The map's outputs: (event, action, argument, delay).
ONS = [
    ('timer:lightning', 'lightning', '', 0.0),
    ('ambush_01', 'enable', 'trigger_ambush_01', 0.0), ('ambush_02', 'enable', 'trigger_ambush_02', 0.0),
    ('ambush_03', 'enable', 'trigger_ambush_03', 0.0),
    # The colony gate's panel: the swarm comes over the fences while it is hacked.
    ('hackstart:gate', 'spawn', 'holdout_spawn', 3.0),
    ('hacked:gate', 'complete', 'gate', 0.0), ('hacked:gate', 'stop', 'holdout_spawn', 18.0),
    ('hacked:gate', 'spawn', 'spawn_ins_boomer', 0.0),
    # The hold's music (jukebox: from two seconds into the hack until twenty after it), and the gatehouse windows
    # blowing in five and eight seconds after the gate opens (window_5b, window_5).
    ('hackstart:gate', 'musicloop', 'Ambience_CharDistantBattle', 2.0), ('hacked:gate', 'musicstop', '', 20.0),
    ('hacked:gate', 'shatter', '51.2,51.5', 5.0), ('hacked:gate', 'shatter', '45.2,56.4', 8.0),
    # The roadside windows the first drones come through (WindowSpawner5-8 break theirs as they spawn).
    ('spawned:WindowSpawner5', 'shatter', '16.0,24.5', 0.0), ('spawned:WindowSpawner6', 'shatter', '16.0,27.7', 0.0),
    ('spawned:WindowSpawner7', 'shatter', '16.0,44.7', 0.0), ('spawned:WindowSpawner8', 'shatter', '16.0,47.9', 0.0),
    # The ramp (relay_bridge: the ramps run out over a second and a half), and the charges (relay_bomb: they go
    # 1.9 s after the button; the wreckage is gone, the shieldbug wakes and the pipe drones come).
    ('pressed:openBridgeButton', 'open', 'ramp', 0.5),
    ('pressed:DetonateBridgeButton', 'complete', 'pipe', 0.0),
    ('pressed:DetonateBridgeButton', 'boom', '64.0,90.0', 1.9), ('pressed:DetonateBridgeButton', 'boom', '68.0,106.0', 2.3),
    ('pressed:DetonateBridgeButton', 'open', 'debris', 1.9),
    ('pressed:DetonateBridgeButton', 'spawn', 'spawner_pipe_drone', 4.0),
    ('pressed:DetonateBridgeButton', 'spawn', 'spawn_ins_shield', 9.5),
    ('hacked:bridgegate', 'notech', '', 0.0),
    # The Bloodhound: she holds at the bridge gate (relay_stoptrain_1) until the squad is through, then keeps pace
    # with it to the broken span (AS holds her there too, relay_stoptrain_2, until the squad comes up: here she
    # flies on at walking pace) and over the gap (path_12) stops for good: the squad crosses on her back.
    ('pass:path_4', 'movestop', 'ship', 0.0),
    ('pass:path_12', 'movestop', 'ship', 0.0), ('pass:path_12', 'open', 'shipdeck', 0.0),
    ('pass:path_12', 'line', 'co_m2_onback', 0.5),
]
TIMERS = [('lightning', 15.0, 20.0, True)]      # timer_lightening
# trigger_asw_jump: (rect, destination, minimum marine distance in cells, toward the quarry only). The bridge's
# lower walkway: drones leap the gap up onto the east catwalk (jump_target, set on its nearest deck). AS's other
# jump here (a forced leap south off the ramp's end) is left out: it only throws back drones chasing north.
JUMPS = [((33.5, 89.6, 35.7, 92.0), (40.5, 89.5), 0.0, False)]
# The dropship (train_ship along path_1 .. path_12), her height over the drop she flies above.
_SHIP_Z = 8.8
MOVERS = [
    ('ship', 'ASR_Hercules', 1.4, [
        (69.3, 121.2, _SHIP_Z, ''), (69.3, 120.0, _SHIP_Z, ''), (70.5, 119.0, _SHIP_Z, ''), (72.1, 118.2, _SHIP_Z, 'path_4'),
        (88.5, 118.2, _SHIP_Z, ''), (92.9, 118.6, _SHIP_Z, ''), (97.5, 118.2, _SHIP_Z, ''), (106.3, 118.0, _SHIP_Z, ''),
        (131.2, 118.0, _SHIP_Z, 'path_9'), (135.2, 118.2, _SHIP_Z, ''), (138.0, 118.4, _SHIP_Z - 1.0, 'path_12'),
    ]),
]

# Commander lines (subtitles), after the original's co_m2_* scenes, said anew.
LINES = {
    'co_m2_start': 'This is Deima. The swarm is using the colony\'s main pipeline as a highway between the hives. Find that pipe and shut it down.',
    'co_m2_ob1b': 'Gate\'s open. Take the catwalks north to the pump station, and watch the drop.',
    'co_m2_pipeline': 'The miners wired the main pipe with charges before they were overrun. Get to the detonator and finish the job.',
    'co_m2_powerout': 'Power\'s gone on the bridge ahead. It\'ll be dark out there.',
    'co_m2_stayinlight': 'Bloodhound will run alongside and light the way. Stay inside her lamps.',
    'co_m2_onback': 'The last span is down. She\'s bringing herself in over the gap: you\'ll cross on her back.',
    'co_m2_getaccross': 'She can\'t hold there long. Get across, now!',
}

CHECKPOINTS = [SPAWN, (49.0, 62.0), (47.0, 90.5), (69.0, 108.0), (100.0, 114.0), (138.0, 124.0)]
ZONES = []
# The autopilot's way through (worked out over the deck, breadth first between the stops): x, y, wait (1 the panel by it
# hacked, 5 the button by it pressed, 6 the door, gap or ramp by it open).
ROUTE = [
    (21.5, 12.5, 0), (22.5, 26.5, 0), (29.5, 36.5, 0), (42.5, 48.5, 0), (47.5, 51.5, 0), (49.5, 58.5, 0), (51.2, 62.0, 1),
    (44.5, 67.5, 0), (44.5, 69.5, 0), (43.5, 83.5, 0), (41.5, 88.5, 0), (44.5, 90.5, 0), (48.5, 90.5, 5),
    (49.0, 90.5, 6), (60.3, 90.5, 5), (61.0, 89.5, 6), (67.5, 92.5, 0), (67.5, 106.5, 0), (69.5, 108.0, 0),
    (70.0, 114.0, 1), (73.5, 114.0, 0), (87.5, 114.5, 0), (101.5, 114.5, 0), (115.5, 114.5, 0), (129.5, 114.5, 0),
    (137.5, 114.0, 6), (138.0, 119.0, 0), (141.5, 133.5, 0), (143.0, 135.0, 0),
]
