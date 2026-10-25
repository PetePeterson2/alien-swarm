"""Mission 7, TIMOR STATION: after Alien Swarm's asi-jac7-timorstation, the campaign's last.

Traced from the map itself (tools/astrace.py), as tools/residential.py and tools/sewer.py are: the deck is AS's
walkable floor in 80-unit cells, and the entity lump gave the doors, buttons, the computer, the spawners and the
triggers that start them. Nothing of Valve's is shipped: these are numbers and rectangles.

Same data shape as tools/level.py; tools/level.py `use()` swaps it in.
Coordinates are map units, x east, y north. Cells are 1 x 1.
"""
import math

import numpy as np

from tools.astrace import Trace, components

_T = Trace('asi-jac7-timorstation', 0, 0, 128, 170)
W, H = _T.W, _T.H
FLOOR = 8.0
WALL_H = 2.5
HEIGHTS = _T.HEIGHTS
DECK_Z = -112.0                 # the mine's galleries, the halls south of the bridge and the station
MERGE = 48.0

_Z = np.nan_to_num(_T.walk_z, nan=-1e4)
DECK = _T.open_deck()
DECK &= ~_T.partitions(DECK)
# Where AS's corridors narrow to a cell or two in the trace (pipes and trims along their walls, which the wall cut
# takes for wall): the floor under them as well, so the rail tunnel, the mine's west way and the corridor north to
# the mall are as wide as AS's.
_LOOSE = (np.nan_to_num(_T.walk_pct) >= 50) & (np.nan_to_num(_T.wall_pct) < 40) & ~np.isnan(_T.walk_z)
for _x0, _y0, _x1, _y1 in ((88, 40, 102, 60), (42, 44, 60, 60), (40, 115, 56, 133)):
    DECK[_y0:_y1, _x0:_x1] |= _LOOSE[_y0:_y1, _x0:_x1]
# What the trace takes for floor and the squad never stands on: the station's roof and the yard outside it, the
# nest's roof, a ledge over the swing bridge and a cave west of the mine that nothing opens.
for _x0, _y0, _x1, _y1 in ((66, 166, 80, 170), (88, 159, 94, 166), (74, 88, 121, 114), (66, 81, 71, 87),
                           (120, 60, 128, 72)):
    DECK[_y0:_y1, _x0:_x1] = False
DECK[75:96, 15:35] &= _Z[75:96, 15:35] > -160
DECK[150:158, 56:83] = False            # the nest's machinery roofs east of the laser rocks
DECK[81:88, 100:112] = False            # a block of the station's plant the trace reads as a floor at 128
DECK = components(DECK, 12)
# The swing bridge (func_door_rotating Bridge): an L of walkway on a pivot at its corner. Shut, one arm runs south
# to the gate off the south hall and the other east to the console's platform; swung 90 degrees, the east arm lies
# south (the same walkway) and the south arm spans the chasm west to the rooms beyond. Here the walkway is deck
# all along, the span west is a gap the bridge comes out over (DOORS 'Bridge'), and the east arm is the drop.
DECK[94:98, 26:39] = True
DECK[81, 39:43] = True
DECK[94:104, 43:59] = False
DECK[88:92, 54:58] = True               # the console's landing at the head of the east corridor
DECK[88:93, 58:60] = False
# AS's stair from the cable railway's platform down to the mine's top corridor, which the partitions cut.
DECK[55:59, 84:89] = True
# The nest: a ledge at the mine's level west of the barricade and the lair below it (the high walkway along its
# north wall is the lair's floor here). A wall row parts them but for the flight east off the ledge.
DECK[161, 42:58] = False
DECK[158:161, 58:64] = True
# The escape: the landing platform in the station's octagon and the dropship's ramp beyond its east wall, which
# the ship comes down over (DOORS 'ship', a hover).
DECK[73:81, 119:124] = True
# The chasm the bridge crosses (AS's trigger_hurt under it, 800 units down): the drop either side of the walkway
# and the span, and the night east of the station that the dropship comes down through.
_TOP = np.nan_to_num(_T.top_z, nan=-1e4)
OPEN = np.zeros((H, W), bool)
OPEN[81:110, 26:56] = ~DECK[81:110, 26:56] & (_TOP[81:110, 26:56] < -300.0) & ~_T.walls(10)[81:110, 26:56]
OPEN[70:86, 124:128] = True
HEIGHT_SET = [((38, 81, 43, 98), -112.0), ((26, 94, 39, 98), -112.0), ((54, 88, 58, 92), -112.0),
              ((42, 158, 58, 161), -112.0), ((44, 161, 88, 166), -172.0), ((64, 158, 88, 161), -172.0),
              ((111, 73, 124, 79), -48.0)]
FLIGHTS = [((58, 158, 64, 161), 'W', -172.0, -112.0), ((108, 73, 111, 79), 'E', -112.0, -48.0),
           ((111, 70, 118, 73), 'N', -112.0, -48.0)]

# The rooms by what AS's floor and walls are there: the mine's rock (blendrockgravel001a, minerockwall) from the
# landing zone to the nest, the gravel yards round the station between its board-formed concrete walls
# (concretewall082), and the grated gantries (metalgrate014, metal/bridge) over the chasm and through the mall.
AREAS = [
    ('Landing Zone',        (88, 0, 120, 20), 'mine'),
    ('Cable Railway',       (78, 20, 104, 60), 'mine'),
    ('Mine',                (36, 36, 78, 66), 'mine'),
    ('South Hall',          (36, 66, 62, 82), 'mine'),
    ('Bridge',              (20, 82, 62, 116), 'gantry'),
    ('Mall',                (34, 116, 60, 152), 'gantry'),
    ('Nest',                (40, 152, 90, 170), 'mine'),
    ('Exit Corridor',       (62, 66, 86, 82), 'yard'),
    ('Timor Station',       (86, 60, 126, 96), 'yard'),
]
BLOCKS = []
VIEWPORTS = []
SPAWN = (108.0, 5.0)
SPAWN_FACING = 90.0
LIFT = None
VOID = None
WINDOWS = []

# Each cell's kind from AS's floor (tools/asextract.py floor_mat): grates and steel plate are the gantries, brick and
# tile the station's halls, the swarm's slime its growth; the rest is rock, as its room has it.
_MAT_KIND = {2: 'growth', 3: 'gantry', 4: 'gantry', 6: 'station'}
CELL_KINDS = {}
for _y in range(H):
    for _x in range(W):
        # (The landing zone's class-2 cells are rain pools, water_timor, not slime.)
        if DECK[_y, _x] and int(_T.floor_mat[_y, _x]) in _MAT_KIND and not (_y < 30 and _T.floor_mat[_y, _x] == 2):
            CELL_KINDS[(_x, _y)] = _MAT_KIND[int(_T.floor_mat[_y, _x])]


# Lamps (x, y, kind, flicker), from the map's lights. The red ones are the alarm's, dark until the warhead is armed.
def _lights():
    out = []
    for e in _T.entities:
        if e['class'] not in ('light', 'light_spot') or int(e['keys'].get('spawnflags', '0') or 0) & 1:
            continue
        x, y = _T.where(e)
        if not (0 <= x < W and 0 <= y < H):
            continue
        r, g, b, a = (float(v) for v in (e['keys'].get('_light', '255 255 255 100').split() + ['100'])[:4])
        if r > 160 and g < 90:
            continue
        kind = 'orange' if r > g + 15 and b < g else 'cold' if b > r + 10 else 'white'
        if a >= 200:
            kind += 'big'
        if any(math.hypot(x - ox, y - oy) < 3.5 for ox, oy, _, _ in out):
            continue
        out.append((x, y, kind, 0))
    return out


LIGHTS = _lights()
PROPS = []
SPOTS = []


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


_TAKEN = set()


def _inside(x, y):
    """A spot with deck all round it near (x, y): the kit lays its clutter along the walls."""
    ix, iy = int(x), int(y)
    sides = sum(DECK[iy + dy, ix + dx] for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)) if 0 <= ix + dx < W and 0 <= iy + dy < H)
    if 0 <= ix < W and 0 <= iy < H and DECK[iy, ix] and sides >= 3 and (ix, iy) not in _TAKEN:
        _TAKEN.add((ix, iy))
        return (x, y)
    best = None
    for cy in range(max(1, iy - 4), min(H - 1, iy + 5)):
        for cx in range(max(1, ix - 4), min(W - 1, ix + 5)):
            if DECK[cy - 1:cy + 2, cx - 1:cx + 2].all() and (cx, cy) not in _TAKEN:
                d = math.hypot(cx + 0.5 - x, cy + 0.5 - y)
                if best is None or d < best[0]:
                    best = (d, cx, cy)
    if not best:
        return _snap(x, y) or (x, y)
    _TAKEN.add(best[1:])
    return (best[1] + 0.5, best[2] + 0.5)


def _named(cls):
    return [(e, _inside(*_T.where(e))) for e in _T.of(cls)]


# ---- the mission ---------------------------------------------------------
DOORS = [
    # The rail tunnel's door (LandingBayDoor4): its panel (door_thing) has power a second after the railway starts.
    ('rail_door',   (94, 50, 98, 51), 'jammed', 0.0, None),
    # The mine's way down to the south hall (LandingBayDoor1): the level's one wire panel.
    ('mine_door',   (44, 72, 47, 73), 'panel', 0.0, (47.7, 71.8)),
    ('mall_door',   (47, 124, 50, 125), 'auto', 0.0, None),
    ('exit_door',   (71, 74, 72, 77), 'auto', 0.0, None),
    # The swing bridge (Bridge, 90 degrees at 5 a second from two seconds after the console) and the gates at the
    # walkway's foot (BridgeGateMoverLeft/Right, 23 seconds after).
    ('bridge',      (26, 94, 39, 98), 'gap', 0.0, None),
    ('bridge_gate', (39, 81, 43, 82), 'block', 0.0, None),
    # Rock (src/Doors.galaxy kind 8, its seconds of cutting): the barricade across the way to the nest (Barricade5,
    # opened by any of its four asw_prop_laserable heaps breaking) and the fall in the mine's west way (rock01..04),
    # which AS's mining laser cuts and a marine standing at them cuts here; the slip that walls the exit corridor
    # until the warhead is armed (block_rock_exit, killed by relay_open_exit), which only the mission clears.
    ('barricade',   (51, 154, 57, 156), 'rock', 6.0, None),
    ('mine_rocks',  (50, 50, 56, 51), 'rock', 6.0, None),
    ('exit_rocks',  (60, 74, 61, 79), 'rock', 0.0, None),
    # The dropship's ramp beyond the station's east wall (brush_block ship): a drop until she sets down.
    ('ship',        (119, 73, 124, 79), 'hover', 0.0, None),
]
for _name, (_x0, _y0, _x1, _y1), *_ in DOORS:
    DECK[_y0:_y1, _x0:_x1] = True
    OPEN[_y0:_y1, _x0:_x1] = False
PANEL_WIRES = (2, 6, 3)          # trigger_asw_button_area by LandingBayDoor1: wirerows 2, wirecolumns 6, numwires 3
COMPUTER = (77.0, 164.2)         # the detonator's terminal in the nest (rocket_button_2)
COMPUTER_HACK = (5, 5, 0.5, 3.0)
CONSOLE = COMPUTER
NEEDS_TECH = True                # asw_tech_marine_req, lifted once the terminal has done its work
EXTRACT = (119, 73, 124, 79)     # the escape's trigger_multiple: the dropship's ramp
EXTRACT_NAME = 'the dropship'
OBJECTIVES = [
    ('railway', 'Activate the cable railway', True, (99.5, 46.8)),
    ('warhead', 'Detonate the warhead', True, (51.5, 120.5)),
    ('escape', 'Escape via Bloodhound', False, None),
]
COUNTDOWN = 140.0                # asw_objective_countdown countdown_escape CountdownLength
DESCRIPTION = ('Timor Station sits on the mine the swarm has made its breeding chamber. The colonists rigged an old '
               'warhead to bring it down and never got it there. Start the cable railway that carries the warhead '
               'in, clear its path, arm it from the terminal in the nest, then get to the loading dock before it '
               'goes: Bloodhound will not wait.')
DEBRIEF = ('The warhead took out the bulk of the swarm under the surface: two hundred eggs and more, and drones beyond '
           'counting. The clean-up fleet is in orbit and sweeps the atmosphere at 0500. Bloodhound is to be back by '
           '0430. Enjoy the cryo-sleep while you can.')
BUTTONS = [('rail_button', (99.5, 46.8), 'Activate the cable railway', True),
           ('door_thing', (96.3, 49.6), 'Open the tunnel door', False),
           ('BridgeConsole', (55.8, 90.6), 'Swing the bridge', True)]
PDAS = [((95.5, 13.0), 'John Cain', 21), ((51.0, 67.4), 'Lt. Cain', 22), ((99.3, 44.2), 'Helen Young', 23),
        ((72.9, 164.1), 'Helen Young', 24)]
MAILS = {
    21: ('John Cain', 'Martial law', 'To every citizen of Vereon XII: martial law is in force from now. Go to your '
         'quarters and stay there. Anyone found outside will be shot.\nLt. Cain, SynTek Security.'),
    22: ('Laura Callen', 'This is it', 'Martial law? It is far too late for that. We need help from outside, or this '
         'whole facility is lost.'),
    23: ('Brian Howe', 'Going to the labs', 'We found the tunnel those things use to get all over the colony. We have '
         'rigged an old warhead to seal it with the blast.\nHelen, stay away from the labs. Lock yourself in until I '
         'get back.'),
    24: ('Brian Howe', 'Warhead', 'Helen, answer me. Dave and Tom are dead. We could not get the warhead into the '
         'tunnel. I am hiding, but I cannot stay here.\nI hope you are all right. I love you.'),
}
# The medkits (asw_pickup_medkit) by the north rooms' ammo and in the nest. AS's mining lasers, blink pack and jump
# jet have no item in the port.
PICKUPS = [('medkit', 50.3, 114.4), ('medkit', 79.8, 163.0), ('medkit', 79.2, 162.4)]
# The ammo (asw_ammo_drop and the rifle, PDW, autogun and vindicator ammo), one crate per heap.
AMMO = [(49.5, 114.4), (81.6, 163.3), (65.2, 162.9), (73.7, 157.6), (44.8, 142.0)]
HIVE_BARRELS = []
BARRELS = [_inside(*_T.where(e)) for e in _T.of('asw_barrel_explosive') + _T.of('asw_barrel_radioactive')]
CREEP = [(48.0, 64.0, 1.8), (60.4, 57.2, 1.4), (50.0, 120.0, 2.2), (52.0, 165.0, 1.6), (66.0, 160.0, 2.0),
         (81.0, 161.5, 2.4), (76.5, 158.0, 1.6), (46.3, 80.0, 1.2)]
EGGS = [(_x, _y) for _e, (_x, _y) in _named('asw_egg')]
# The growth (asw_alien_goo): the one on the warhead's track (goo_blocker2) holds it (count_goo, max 1); the rest wake
# the mall when burnt or lit (relay_sounds_mall).
BIOMASS = [(_x, _y, 1.2 if _e.get('name') == 'goo_blocker2' else 1.0, 'trackgoo' if _e.get('name') == 'goo_blocker2'
            else 'mallgoo' if _T.where(_e)[1] < 130 else 'nestgoo') for _e, (_x, _y) in _named('asw_alien_goo')]
# Asleep at the start: the harvesters by the mine and over the bridge, the bridge's rangers, the parasites by the
# mine's door (sleepstate 1 and 3).
_SLEEP = {'asw_harvester': 'AS_HARVESTER', 'asw_ranger': 'AS_RANGER', 'asw_parasite': 'AS_PARASITE'}
SLEEPERS = [(_SLEEP[c], _x, _y) for c in _SLEEP for _e, (_x, _y) in _named(c)]


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


# Triggers: every trigger_once a marine sets off, read from the map: what it starts and stops, the logic_case it picks
# from, the timer it turns on or off, the commander's line. trigger_rocks_fall (six) are off until the warhead is armed.
# The disabled one by the nest's west end (case_end_boomer) has nothing that turns it on, and is left out.
_CASE = {e.get('name'): [c.split(',')[0] for o, c in e.get('io', []) if o.startswith('OnCase')] for e in _T.of('logic_case')}
_ROCKS = {'rocks_fall_01_relay': '55.0,151.5', 'rocks_fall_01_relay1': '55.2,162.9', 'rocks_fall_01_relay2': '47.6,127.1',
          'rocks_fall_01_relay3': '41.2,92.1', 'rocks_fall_01_relay4': '70.8,74.6', 'rocks_fall_01_relay5': '49.0,77.9'}
_CHOREO = {'commander_choreo_bomb': 'co_m6_ob1', 'commander_choreo_railsytem': 'co_m6_ob3',
           'commander_choreo_extractionzone': 'co_m6_ob6', 'commander_choreo_clock': 'co_m6_ob7',
           'commander_choreo_highspeed': 'co_m6_ob9', 'commander_choreo_onmyway': 'co_m6_onmyway'}


def _triggers():
    out = []
    for e in _T.of('trigger_once'):
        k = e.get('keys', {})
        name = e.get('name') or ''
        if k.get('StartDisabled') == '1' and name != 'trigger_rocks_fall':
            continue
        acts = []
        for o, c in e.get('io', []):
            if o != 'OnTrigger':
                continue
            target, inp, _, delay = (c.split(',') + ['', '', '', ''])[:4]
            d = float(delay or 0)
            if inp == 'StartSpawning':
                acts.append(('spawn', target, d))
            elif inp == 'StopSpawning':
                acts.append(('stop', target, d))
            elif inp == 'SpawnOneAlien':
                acts.append(('spawnone', target, d))
            elif inp.startswith('PickRandom') and target in _CASE:
                acts.append(('pick', '|'.join(_CASE[target]), d))
            elif inp in ('Enable', 'Disable') and target.startswith('timer_'):
                acts.append((inp.lower(), target, d))
            elif target in _ROCKS:
                acts.append(('rockfall', _ROCKS[target], d))
            elif target in _CHOREO and inp == 'Start':
                acts.append(('line', _CHOREO[target], d))
        if acts:
            r = tuple(round(v, 1) for v in _T.rect(e['box']))
            out.append((r, True, 1.0, acts, {'name': name, 'off': True}) if name == 'trigger_rocks_fall' else (r, True, 1.0, acts))
    return out


TRIGGERS = _triggers() + [
    # asw_marines_past_area 'area' (a point at 110, 76 in the extracted data, no bounds): every living marine past the
    # station's middle, east of it up to the dock's edge (NumMarines -1), and Bloodhound starts down four seconds
    # later (MarinesPast: train_ship StartForward).
    ((110.2, 66.5, 119.0, 88.3), True, 1.0, [('move', 'ship', 4.0)], {'name': 'marines_past', 'off': True, 'need': -1}),
]
# timer_insane_drone: on as the squad enters the mall's north rooms, off at the nest's ledge; every 30-50 s one of the
# six Insane drone spawners (case_insane_drone).
TIMERS = [('timer_insane_drone', 30.0, 50.0, False)]
ONS = [
    # The cable railway (the substation's button): the warhead starts in, the tunnel door's panel has power.
    ('pressed:rail_button', 'complete', 'railway', 0.0), ('pressed:rail_button', 'power', 'door_thing', 1.0),
    ('pressed:door_thing', 'open', 'rail_door', 0.0),
    # The mine's door hacked: drones come back down the mine (back_drone_spawn_02).
    ('hacked:mine_door', 'spawn', 'back_drone_spawn_02', 0.0),
    # The bridge's console: the span swings out over the chasm, the gates part.
    ('pressed:BridgeConsole', 'open', 'bridge', 18.0), ('pressed:BridgeConsole', 'open', 'bridge_gate', 23.0),
    # The growth on the warhead's track (count_goo): burnt away, the warhead goes on and the marker moves on to the
    # nest's terminal. Any growth here burnt or lit wakes the mall (relay_sounds_mall).
    ('broken:trackgoo', 'count', 'count_goo', 0.0), ('max:count_goo', 'mark', 'warhead,77.0,164.2', 0.0),
    ('broken:trackgoo', 'fire', 'mall_wakes', 0.0), ('broken:mallgoo', 'fire', 'mall_wakes', 0.0),
    ('ignite:nestgoo', 'fire', 'mall_wakes', 2.0),
    ('mall_wakes', 'spawn', 'bio_drone_01', 0.0), ('mall_wakes', 'spawn', 'bio_ranger_spawn_01', 0.0),
    ('mall_wakes', 'spawn', 'bio_buzzer_spawn_01', 2.0),
    ('timer:timer_insane_drone', 'pick', '|'.join(_CASE.get('case_insane_drone', [])), 0.0),
    # The terminal's download: the warhead is armed. The tech is no longer needed, the rock slip in the exit corridor
    # comes down, rocks start to fall along the way back, the alarm, Bloodhound's countdown and its music.
    ('downloaded:terminal', 'complete', 'warhead', 0.0), ('downloaded:terminal', 'notech', '', 0.0),
    ('downloaded:terminal', 'open', 'exit_rocks', 0.0), ('downloaded:terminal', 'enable', 'trigger_rocks_fall', 0.0),
    ('downloaded:terminal', 'enable', 'marines_past', 0.0), ('downloaded:terminal', 'line', 'co_m6_ob7', 1.0),
    ('downloaded:terminal', 'countdown', '140', 4.0), ('downloaded:terminal', 'musicloop', 'ASMus_Combat', 4.0),
    # Bloodhound coming down (train_ship, path_1 .. path_2): drones out of the station as she passes path_4; at
    # path_2 she has set down, the ramp is open and her guns cover the squad.
    ('pass:path_4', 'spawn', 'esc_drone_8', 2.0), ('pass:path_2', 'open', 'ship', 0.0),
    ('pass:path_2', 'shipguns', 'ship', 0.0),
]
COUNTERS = [('count_goo', 1)]
# Bloodhound (train_ship): from 840 above the dock down her path to the ramp, 50 a second (startspeed).
MOVERS = [('ship', 'ASR_Hercules', 50.0 / 80.0, [(122.9, 77.7, 10.6, 'path_1'), (123.0, 78.0, 9.4, 'path_5'),
                                                  (122.8, 78.4, 7.4, 'path_3'), (122.7, 78.5, 6.6, 'path_6'),
                                                  (122.6, 78.6, 5.7, 'path_7'), (122.5, 78.4, 4.9, 'path_4'),
                                                  (122.4, 78.2, 0.6, 'path_2')])]
JUMPS = []

LINES = {
    'co_m6_ob1': 'Timor Station. The colonists rigged a warhead to bury the swarm\'s breeding chamber. Get it there.',
    'co_m6_ob3': 'That\'s the cable railway. Get power to it and the warhead goes in on its own.',
    'co_m6_ob6': 'You\'re in the nest. Find the terminal and arm that warhead.',
    'co_m6_ob7': 'It\'s armed. You have two minutes twenty: get to the loading dock, now.',
    'co_m6_ob9': 'Keep moving! Don\'t stop for anything.',
    'co_m6_onmyway': 'Bloodhound is on her way down. Hold the dock.',
}

CHECKPOINTS = [SPAWN, (97.0, 45.0), (60.0, 56.0), (46.0, 76.0), (40.5, 92.0), (47.5, 112.0), (47.5, 140.0),
               (50.0, 159.0)]
ZONES = []
# The autopilot's way (in AS's cells; layout() moves it), planned over the cells the game leaves open (walls and
# clutter solid, doors open) between these stops, with a point two cells either side of every cut so that a leg
# from one piece to the next is a short one through the seam: the substation's button and the tunnel door's, the mine's rock fall cut, its eggs, the wire panel, the eggs by the bridge's foot, the bridge's console, the
# gates, the growth on the warhead's track and the eggs by it, the barricade cut, the nest's eggs, the terminal, back
# the way it came through the exit corridor to Bloodhound's ramp.
ROUTE_STOPS = [(108.0, 5.0, 0), (98.8, 46.3, 5), (95.8, 48.8, 5), (54.0, 48.6, 6), (46.5, 65.0, 7), (46.0, 70.5, 1),
               (44.0, 79.0, 7), (55.5, 89.8, 5), (41.0, 79.8, 6), (48.5, 117.0, 7), (54.0, 153.3, 6),
               (70.0, 161.5, 7), (79.0, 162.5, 7), (76.0, 163.2, 4), (117.5, 76.0, 6), (121.5, 76.0, 0)]
ROUTE = [
    (108.5, 5.5, 0), (100.5, 11.5, 0), (88.5, 14.5, 0), (81.5, 22.5, 0), (81.5, 23.5, 0), (80.5, 28.5, 0),
    (81.5, 35.5, 0), (82.5, 36.5, 0), (92.5, 37.5, 0), (96.5, 41.5, 0), (98.5, 46.5, 5), (95.5, 48.5, 5),
    (95.5, 56.5, 0), (94.5, 57.5, 0), (91.5, 57.5, 0), (72.5, 55.5, 0), (71.5, 54.5, 0), (70.5, 47.5, 0),
    (60.5, 44.5, 0), (59.5, 45.5, 0), (56.5, 46.5, 0), (54.5, 48.5, 6), (48.5, 59.5, 0), (47.5, 62.5, 0),
    (47.5, 64.5, 0), (46.5, 65.5, 7), (46.5, 70.5, 1), (46.5, 74.5, 0), (49.5, 77.5, 0), (47.5, 79.5, 0),
    (44.5, 79.5, 7), (54.5, 80.5, 0), (55.5, 89.5, 5), (54.5, 79.5, 0), (41.5, 79.5, 6), (40.5, 93.5, 0),
    (38.5, 95.5, 0), (24.5, 97.5, 0), (25.5, 99.5, 0), (29.5, 101.5, 0), (32.5, 110.5, 0), (45.5, 110.5, 0),
    (47.5, 112.5, 0), (47.5, 114.5, 0), (48.5, 115.5, 0), (48.5, 117.5, 7), (49.5, 117.5, 0), (49.5, 123.5, 0),
    (47.5, 130.5, 0), (47.5, 139.5, 0), (56.5, 139.5, 0), (56.5, 148.5, 0), (55.5, 149.5, 0), (54.5, 153.5, 6),
    (55.5, 158.5, 0), (68.5, 163.5, 0), (70.5, 161.5, 7), (79.5, 162.5, 7), (76.5, 163.5, 4), (61.5, 161.5, 0),
    (55.5, 158.5, 0), (54.5, 154.5, 0), (55.5, 149.5, 0), (57.5, 144.5, 0), (56.5, 139.5, 0), (47.5, 139.5, 0),
    (47.5, 126.5, 0), (50.5, 117.5, 0), (48.5, 115.5, 0), (47.5, 114.5, 0), (47.5, 112.5, 0), (45.5, 110.5, 0),
    (32.5, 110.5, 0), (29.5, 101.5, 0), (25.5, 99.5, 0), (25.5, 97.5, 0), (40.5, 94.5, 0), (41.5, 81.5, 0),
    (43.5, 79.5, 0), (58.5, 78.5, 0), (61.5, 76.5, 0), (66.5, 76.5, 0), (117.5, 76.5, 6), (121.5, 76.5, 0),
]


# ---- the pieces ------------------------------------------------------------------------------------------------------
# Timor Station is longer than any room the six levels packed before it left in the map (tools/pack.py PINNED). It is
# cut at five corridors into six pieces that sit apart in the map (tools/seams.py), each showing its corridors on
# OVERLAP cells past the cut (short of a door), and the squad, the swarm and the camera step from piece to piece
# where a corridor crosses a cut (src/Seams.galaxy). Everything above is in AS's own cells; layout() moves it.
#   the rail tunnel (y 26), the mine's way down to the south hall (y 62), the exit corridor between its rock slip and
#   its door (x 64), the corridor north to the mall (y 113) and the way up to the barricade (y 152)
CUTS = [('y', 26, 74, 92), ('y', 62, 38, 62), ('x', 64, 66, 90), ('y', 113, 40, 60), ('y', 152, 48, 60)]
OVERLAP = 10
# Each piece's lower-left corner in the map, from `py tools/pack.py --seams timor`.
PIECES = [(218, 162), (199, 187), (89, 166), (121, 177), (174, 116), (151, 226)]
_AS = {k: v for k, v in globals().items() if k.isupper()}


def layout(places, margin=1):
    """The level's data with its pieces at `places` (tools/seams.py): a dict of the same names, and the seams'."""
    from tools.seams import Seams
    a = _AS
    S = Seams(a['DECK'] | a['OPEN'], CUTS, OVERLAP, places, doors=a['DOORS'], margin=margin)
    P = lambda x, y: tuple(round(v, 2) for v in S.point(x, y))

    def pt_str(s):
        *head, x, y = s.split(',')
        return ','.join(head + ['%.1f' % v for v in S.point(float(x), float(y))])

    def acts(lst):
        return [(k, pt_str(v) if k == 'rockfall' else v, d) for k, v, d in lst]

    out = {'W': S.W, 'H': S.H, 'DECK': S.grid(a['DECK'], False), 'OPEN': S.grid(a['OPEN'], False),
           'HEIGHTS_FROM': S.source(), 'SEAM_LAYOUT': S, 'PLACE': S.origin,
           'SEAMS': S.seams(), 'PIECE_ROWS': S.piece_rows(), 'SEAM_NEXT': S.next_hop()}
    out['HEIGHT_SET'] = [(r2, z) for r, z in a['HEIGHT_SET'] for r2 in S.rect_copies(r)]
    out['FLIGHTS'] = [(r2, w, lo, hi) for r, w, lo, hi in a['FLIGHTS'] for r2 in S.rect_copies(r)]
    areas = []
    for name, (x0, y0, x1, y1), kind in a['AREAS']:
        for reg, (dx, dy) in zip(S.region, S.shift):
            ys, xs = np.nonzero(reg[y0:y1, x0:x1])
            if len(xs):
                areas.append((name, (x0 + xs.min() + dx, y0 + ys.min() + dy, x0 + xs.max() + 1 + dx, y0 + ys.max() + 1 + dy), kind))
    out['AREAS'] = areas
    out['SPAWN'] = P(*a['SPAWN'])
    out['CELL_KINDS'] = {(int(cx), int(cy)): k for (x, y), k in a['CELL_KINDS'].items() for cx, cy in S.copies(x + 0.5, y + 0.5)}
    out['LIGHTS'] = [(round(cx, 2), round(cy, 2), k, f) for x, y, k, f in a['LIGHTS'] for cx, cy in S.copies(x, y)]
    out['DOORS'] = [(n, S.rect(r), k, v, spot and P(*spot)) for n, r, k, v, spot in a['DOORS']]
    out['COMPUTER'] = P(*a['COMPUTER'])
    out['CONSOLE'] = out['COMPUTER']
    out['EXTRACT'] = S.rect(a['EXTRACT'])
    out['OBJECTIVES'] = [(k, t, f, xy and P(*xy)) for k, t, f, xy in a['OBJECTIVES']]
    out['BUTTONS'] = [(n, P(*xy), t, on) for n, xy, t, on in a['BUTTONS']]
    out['PDAS'] = [(P(*xy), who, n) for xy, who, n in a['PDAS']]
    out['PICKUPS'] = [(k,) + P(x, y) for k, x, y in a['PICKUPS']]
    for key in ('AMMO', 'BARRELS', 'EGGS', 'VENTS', 'CHECKPOINTS'):
        out[key] = [P(x, y) for x, y in a[key]]
    out['CREEP'] = [(round(cx, 2), round(cy, 2), r) for x, y, r in a['CREEP'] for cx, cy in S.copies(x, y)]
    out['BIOMASS'] = [P(x, y) + tuple(rest) for x, y, *rest in a['BIOMASS']]
    out['SLEEPERS'] = [(k,) + P(x, y) for k, x, y in a['SLEEPERS']]
    out['SPAWNERS'] = [(r[0],) + P(r[1], r[2]) + tuple(r[3:]) for r in a['SPAWNERS']]
    out['TRIGGERS'] = [(S.rect(t[0]),) + tuple(t[1:3]) + (acts(t[3]),) + tuple(t[4:]) for t in a['TRIGGERS']]
    out['ONS'] = [(e, k, pt_str(v) if k in ('mark', 'rockfall') else v, d) for e, k, v, d in a['ONS']]
    out['MOVERS'] = [(n, m, s, [P(x, y) + (z, nm) for x, y, z, nm in path]) for n, m, s, path in a['MOVERS']]
    out['ROUTE_STOPS'] = [P(x, y) + (w,) for x, y, w in a['ROUTE_STOPS']]
    out['ROUTE'] = [P(x, y) + (w,) for x, y, w in a['ROUTE']]
    return out


if PIECES is not None:
    globals().update(layout(PIECES))
