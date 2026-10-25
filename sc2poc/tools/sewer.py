"""Mission 6, SEWER JUNCTION B5: after Alien Swarm's asi-jac6-sewerjunction.

Traced from the map itself (tools/astrace.py), as tools/deima.py, tools/rydberg.py and tools/residential.py are: the
deck is AS's walkable floor in 80-unit cells, and the entity lump gave the eggs, the tunnel's charges, the spawners and
the triggers that start them. AS's floor materials (tools/asextract.py --mats) say which cells are channels of water,
which grates and which concrete. Nothing of Valve's is shipped: these are numbers and rectangles.

Same data shape as tools/level.py; tools/level.py `use()` swaps it in.
Coordinates are map units, x east, y north. Cells are 1 x 1.
"""
import math

import numpy as np

from tools.astrace import Trace

_T = Trace('asi-jac6-sewerjunction', 0, 0, 90, 140)
W, H = _T.W, _T.H
FLOOR = 8.0
WALL_H = 2.5
HEIGHTS = _T.HEIGHTS
DECK_Z = -592.0                 # the channels and the pump hall; the north walkways stand 112 higher
MERGE = 40.0                    # the channels' kerbs and the walks' lips (16-32 units) are one floor here

# The walkable floor less what its walls stand on, and a cell of hull wherever a thin wall parts two rooms.
DECK = _T.open_deck()
DECK &= ~_T.partitions(DECK)
_Z = np.nan_to_num(_T.walk_z, nan=-1e4)
# North of the tunnel hall the walkways (-480) cross the sewer's sumps on piers: AS's floor down there (-656) is
# sludge the swarm keeps to. Here the sumps are the drop, deep and fogged under the walkways (tools/pitart.py), and a
# walkway's sloping lip (its cells half over the sump) is walkway.
OPEN = np.zeros((H, W), bool)
HEIGHT_SET = []
_high = DECK & (_Z >= -500.0)
_lip = np.zeros((H, W), bool)
for _y in range(100, H):
    for _x in range(W):
        if not DECK[_y, _x] or _high[_y, _x]:
            continue
        if _Z[_y, _x] >= -600.0 and any(0 <= _x + dx < W and _high[_y + dy, _x + dx] for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))
                                        if _y + dy < H):
            _lip[_y, _x] = True
            HEIGHT_SET.append(((_x, _y, _x + 1, _y + 1), -480.0))
        else:
            DECK[_y, _x] = False
            OPEN[_y, _x] = True
# The sump north of the turbine, which AS's walk to the yard dips into (down off the walkway's end, up a ramp to a
# landing under the yard): decked over here at the walkway's height, the turbine's pit open to the south of it.
DECK[126:135, 27:34] = True
OPEN[126:135, 27:34] = False
DECK[131:135, 32:34] = False
HEIGHT_SET.append(((27, 126, 34, 135), -480.0))
# A dead-end store off the tunnel hall that the trace cut off from it, and a speck by the yard: hull.
DECK[85:88, 31:35] = False
DECK[132, 10] = False
# The squad comes down the drain at the south end (info_player_start): a passage one cell wide in the trace, three here.
DECK[4:12, 68:71] = True
# The tunnel east of the tunnel hall: the swarm's way in, which the squad brings down (Objective_Tunnel). Its far side
# is rock from the start; the mouth is where the charges stand.
DECK[80:90, 56:66] = False
# The west corridor out to the buzzers' nest: one corridor three wide round a pipe at chest height, on the yard's floor.
DECK[130, 1:12] = True
HEIGHT_SET.append(((1, 124, 27, 134), -480.0))
# A pipe's top along the west sump and a crate by the tunnel hall's east door read as floor: they are hull here.
DECK[52:60, 23] = False
DECK[78:80, 49] = False
# The ramp from the yard up to the hatch (AS's stairs to the surface, 176 up): one flight north, three cells long,
# and the hatch's floor level behind it.
DECK[133:136, 13:17] = True
DECK[133:135, 11:13] = False
FLIGHTS = [((13, 133, 17, 136), 'N', -480.0, -288.0)]
HEIGHT_SET.append(((11, 136, 17, 139), -288.0))

AREAS = [
    ('Drop Zone',           (60, 0, 82, 26), 'sewer'),
    ('Outfall Tunnel',      (60, 26, 72, 41), 'sewer'),
    ('East Main',           (70, 38, 90, 50), 'sewer'),
    ('Pump Hall',           (28, 50, 66, 64), 'sewer'),
    ('West Sump',           (17, 50, 28, 64), 'sewer'),
    ('Settling Channel',    (17, 64, 56, 72), 'sewer'),
    ('Tunnel Hall',         (36, 72, 62, 95), 'sewer'),
    ('Egg Gallery',         (40, 95, 70, 116), 'sewer'),
    ('North Walk',          (26, 95, 40, 116), 'sewer'),
    ('Turbine Room',        (17, 116, 42, 128), 'sewer'),
    ('Exit Yard',           (0, 128, 26, 135), 'sewer'),
    ('Exit',                (10, 135, 20, 140), 'surface'),
]
BLOCKS = []
VIEWPORTS = []
SPAWN = (69.3, 8.0)
SPAWN_FACING = 90.0
LIFT = None
VOID = None
WINDOWS = []

# Each cell's kind from AS's own floor (tools/asextract.py floor_mat): water is a channel, grates and steel plate are
# catwalks, concrete and tile the sewer's walks. The galleries round the egg clusters are the swarm's growth.
_MAT_KIND = {1: 'sewer', 2: 'channel', 3: 'catwalk', 4: 'catwalk', 6: 'sewer'}
_EGG_AT = [_T.where(e) for e in _T.of('asw_egg')]
CELL_KINDS = {}
for _y in range(H):
    for _x in range(W):
        if not DECK[_y, _x] or (10 <= _x < 20 and _y >= 135):
            continue
        if any(math.hypot(_x + 0.5 - ex, _y + 0.5 - ey) < 2.6 for ex, ey in _EGG_AT):
            CELL_KINDS[(_x, _y)] = 'growth'
        elif _lip[_y, _x]:
            CELL_KINDS[(_x, _y)] = 'catwalk'
        elif int(_T.floor_mat[_y, _x]) in _MAT_KIND:
            CELL_KINDS[(_x, _y)] = _MAT_KIND[int(_T.floor_mat[_y, _x])]


# Lamps (x, y, kind, flicker), from the map's lights: the sewer is lit by sodium lamps and cold work lights.
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


# Scum and litter riding the flooded halls and channels (KDFoam, KDDebris, decals: nothing solid), the scum drawn
# out along whichever way the water runs longer at that cell.
def _water():
    import random
    rng = random.Random(61)
    wet = sorted(c for c, k in CELL_KINDS.items() if k == 'channel')
    wetset = set(wet)
    out = []
    for x, y in wet:
        roll = rng.random()
        if roll < 0.15:
            run_x = sum((x + d, y) in wetset for d in range(-3, 4))
            run_y = sum((x, y + d) in wetset for d in range(-3, 4))
            rot = (0.0 if run_x >= run_y else 90.0) + rng.uniform(-14, 14) + rng.choice([0.0, 180.0])
            out.append((rng.choice(['KDFoam1', 'KDFoam2']), x + rng.random(), y + rng.random(), rot))
        elif roll < 0.21:
            out.append((rng.choice(['KDDebris1', 'KDDebris2']), x + rng.random(), y + rng.random(), rng.uniform(0, 360)))
    return out


SPOTS = _water()


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
# No asw_door in the sewer. The exit is walled up until both jobs are done (exit_wall, a func_breakable the relay
# blows), and the container's two clips across the settling channel's shelf go when the shelf comes down on it.
DOORS = [
    ('exit_wall',       (13, 136, 17, 137), 'jammed', 0.0, None),
    ('container_clip',  (27, 69, 32, 71), 'block', 0.0, None),
    ('container_clip2', (32, 68, 36, 71), 'block', 0.0, None),
]
for _name, (_x0, _y0, _x1, _y1), *_ in DOORS:
    DECK[_y0:_y1, _x0:_x1] = True
    OPEN[_y0:_y1, _x0:_x1] = False
PANEL_WIRES = (2, 5, 2)          # no trigger_asw_button_area in the sewer: no panel
CONSOLE = (69.3, 8.0)
NEEDS_TECH = False
EXTRACT = (11, 137, 17, 139)
EXTRACT_NAME = 'the way out'
OBJECTIVES = [
    ('tunnel', 'Collapse the tunnel', True, (54.9, 84.9)),
    ('eggs', 'Destroy the alien eggs', True, None),
    ('escape', 'Get out of the sewers', False, None),
]
DESCRIPTION = ('Sewer Junction B5 drains the colony, and the swarm is using it. The aliens come up a tunnel off the '
               'junction\'s east side: bring it down with the charges at its mouth. The eggs they have laid along '
               'the north walkways must all be destroyed. Then the way out to the surface can be opened.')
BUTTONS = [('Turbine_Control', (25.6, 123.4), 'Stop the turbine', True)]
PDAS = [((60.5, 58.3), 'Brian Howe', 11), ((34.1, 105.9), 'Brian Howe', 12), ((44.0, 106.2), 'Shaun Ming', 13)]
MAILS = {
    11: ('Brian Howe', 'B5 pumps', 'Pump three is fouled again. Whatever is in the outfall, it is not silt: it moves '
         'when the lamps come on.\nI have shut the grate on the settling channel. Nobody goes down to the turbine '
         'without a second man.'),
    12: ('Brian Howe', 'North walks', 'The sumps under the north walkways have filled up with something white. It '
         'is warm to stand over.\nThe crew wanted to drain them. I told them to leave it and get topside.'),
    13: ('Shaun Ming', 'The east tunnel', 'The east tunnel is where they come from. There are charges stacked at its '
         'mouth from the dig. If anyone can still hold a rifle: shoot the charges and the roof will come in.\nThe '
         'yard hatch to the surface is welded shut. It will take a blast to open it.'),
}
# The medkit by the pump hall (asw_pickup_medkit), the chainsaw by the settling channel (asw_pickup_chainsaw). AS's
# PDW, shotgun and rifle have no item in the port.
PICKUPS = [('medkit', 53.0, 65.1), ('chainsaw', 53.0, 71.9)]
# The ammo (asw_ammo_drop and the rifle, autogun, PDW and vindicator ammo), one crate per heap.
AMMO = [(53.8, 73.7), (39.1, 54.1), (51.8, 91.8), (38.6, 122.9), (33.0, 126.8), (26.3, 127.1)]
# The tunnel's charges (asw_barrel_explosive tunnel_barrel and the two beside it), and the two by the shelf over the
# container. The rest stand where AS has them.
HIVE_BARRELS = [(54.5, 83.8, 'tunnel'), (54.5, 85.0, 'tunnel'), (54.5, 86.2, 'tunnel'),
                (24.6, 69.1, 'shelf'), (24.2, 68.4, 'shelf')]
BARRELS = [_inside(*_T.where(e)) for e in _T.of('asw_barrel_explosive') + _T.of('asw_barrel_radioactive')
           if not any(math.hypot(_T.where(e)[0] - x, _T.where(e)[1] - y) < 1.2 for x, y, _ in HIVE_BARRELS)]
CREEP = [(53.3, 90.4, 2.0), (42.1, 94.5, 1.6), (33.0, 107.6, 2.0), (23.6, 117.5, 2.0), (44.6, 104.9, 2.0),
         (61.5, 102.4, 1.6), (34.9, 126.3, 2.2), (54.6, 85.6, 2.4)]

# Eggs: the 20 Objective_Eggs counts (Egg_Counter, max 20), in seven clusters each with its own marker.
EGGS = [(_x, _y) for _e, (_x, _y) in _named('asw_egg')]
# The tunnel's biomass (asw_alien_goo bio_mass, 5): it dies with the tunnel (TunnelCounter OnHitMax bio_mass Kill).
# AS grows it over the mouth and into the tunnel, which is rock here: it stands on the mouth's flanks, clear of the
# line from the hall to the charges.
BIOMASS = [(53.3, 82.5, 1.1, 'bio_mass'), (51.8, 82.4, 1.1, 'bio_mass'), (53.5, 88.3, 1.1, 'bio_mass'),
           (51.9, 88.4, 1.1, 'bio_mass'), (54.3, 82.9, 0.8, 'bio_mass')]
# Asleep at the start: the shieldbugs in the tunnel hall and the exit yard, the mortarbugs over the north sump, a
# drone by the turbine room's stairs, and the parasites among the eggs (sleepstate 1, all of them).
_SLEEP = {'asw_shieldbug': 'AS_SHIELDBUG', 'asw_mortarbug': 'AS_MORTAR', 'asw_drone': 'AS_DRONE', 'asw_parasite': 'AS_PARASITE'}
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


# Triggers: every trigger_once, trigger_asw_chance and supplies chatter a marine sets off, read straight from the map:
# what it starts and stops, the logic_case it picks from, the commander's line it plays. The physics triggers of the
# container riddle (spawnflags 64) and the hints are left out.
def _triggers():
    cases = {e.get('name'): [c.split(',')[0] for o, c in e.get('io', []) if o.startswith('OnCase')] for e in _T.of('logic_case')}
    out = []
    for e in _T.entities:
        if e['class'] not in ('trigger_once', 'trigger_asw_chance', 'trigger_asw_supplies_chatter') or 'box' not in e:
            continue
        k = e.get('keys', {})
        if not int(k.get('spawnflags', '0') or 0) & (2 | 16):
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
            elif inp == 'PickRandom' and target in cases:
                acts.append(('pick', '|'.join(cases[target]), d))
            elif target.startswith('commander_choreo_') and inp == 'Start':
                acts.append(('line', 'co_sj_' + target.split('_')[-1], d))
        if acts:
            x0, y0, x1, y1 = _T.rect(e['box'])
            r = tuple(round(v, 1) for v in (x0, y0, x1, y1))
            out.append((r, True, float(k.get('TriggerChance', 1) or 1), acts))
    return out


TRIGGERS = _triggers()
TIMERS = []
ONS = [
    # The exit's mortarbugs come one after another (OnAllSpawnedDead).
    ('alldead:exit_mortar_spawner', 'spawn', 'exit_mortar_spawner2', 5.0),
    ('alldead:exit_mortar_spawner2', 'spawn', 'exit_mortar_spawner3', 6.0),
    # The tunnel: a charge goes up and the roof comes in (TunnelCounter OnHitMax). The buzzers stop coming, drones
    # come out of the north instead, the tunnel's growth dies, and the objective is done five seconds later.
    ('broken:tunnel', 'count', 'TunnelCounter', 0.0),
    ('max:TunnelCounter', 'boom', '56.0,85.0', 0.0), ('max:TunnelCounter', 'stop', 'BuzzerSpawn1', 0.0),
    ('max:TunnelCounter', 'spawn', 'DroneSpawn10', 0.0), ('max:TunnelCounter', 'kill', 'bio_mass', 0.0),
    ('max:TunnelCounter', 'complete', 'tunnel', 5.0),
    # The shelf over the container: its barrels bring it down, the container slides and the clips go.
    ('broken:shelf', 'count', 'BeamCounter', 0.0), ('max:BeamCounter', 'open', 'container_clip', 1.2),
    ('max:BeamCounter', 'open', 'container_clip2', 2.0),
    # Every egg gone (Egg_Counter OnHitMax): the exit's buzzers stop and the drones start.
    ('done:eggs', 'stop', 'BuzzerSpawn2', 0.0), ('done:eggs', 'spawn', 'DroneSpawn11', 0.0),
    # Both done (escape_obj_counter): the yard's wall is blown four seconds later and the way out shows.
    ('done:tunnel', 'count', 'escape_obj_counter', 0.0), ('done:eggs', 'count', 'escape_obj_counter', 0.0),
    ('max:escape_obj_counter', 'boom', '15.0,135.0', 4.0), ('max:escape_obj_counter', 'blow', 'exit_wall', 4.0),
    # The turbine's control, shot (OnAwakened): it stops, and on Insane its buzzers come (HardSpawner7, MinSkill 4).
    ('pressed:Turbine_Control', 'boom', '26.0,123.0', 0.2), ('pressed:Turbine_Control', 'spawn', 'HardSpawner7', 0.0),
]
COUNTERS = [('TunnelCounter', 1), ('BeamCounter', 1), ('escape_obj_counter', 2)]
MOVERS = []
# trigger_asw_jump: drones chasing a marine leap the settling channel's fence onto FenceJumpTarget (MinMarineDist 400,
# CheckEnemyDirection).
JUMPS = [((35.2, 63.9, 35.9, 66.9), (28.3, 65.3), 5.0, True)]

LINES = {
    'co_sj_ob1': 'Sewer Junction B5. The swarm is coming up a tunnel on the east side: find it and bring it down. Then clear the eggs.',
    'co_sj_ob3': 'That\'s the tunnel. There are charges stacked at its mouth: shoot them from a distance.',
    'co_sj_ob4': 'Eggs all along these walkways. Smash every one.',
}

CHECKPOINTS = [SPAWN, (66.0, 45.0), (45.0, 66.0), (46.0, 88.0), (45.0, 106.0), (34.0, 120.0)]
ZONES = []
# The autopilot's stops (tools/routeplan.py --plan cuts the walk between them into clear legs): up the outfall to the
# pump hall and the tunnel hall, the tunnel's charges shot from across the hall, the eggs on the hall's north walk,
# up the east stair to the gallery's eggs, along the walkways west and north to the clusters by the turbine and back
# down the long walkway, then up past the turbine to the yard and out through the blown wall.
ROUTE_STOPS = [
    (69.5, 12.0, 0), (77.0, 20.0, 0), (65.0, 45.0, 0), (45.0, 66.0, 0), (47.5, 85.5, 7), (52.5, 93.5, 7),
    (41.0, 92.0, 7), (59.5, 99.0, 0), (58.5, 105.5, 7), (44.5, 110.0, 7), (44.5, 119.5, 0), (34.5, 123.5, 7),
    (30.5, 129.5, 7), (34.5, 118.0, 0), (25.5, 114.5, 7), (34.8, 109.2, 7), (34.5, 120.0, 0), (30.0, 129.0, 0),
    (14.5, 131.0, 6), (14.0, 137.5, 0),
]
ROUTE = [
    (69.5, 12.0, 0), (76.5, 15.5, 0), (77.0, 20.0, 0), (75.5, 29.5, 0), (67.5, 35.5, 0), (65.0, 45.0, 0),
    (63.5, 55.5, 0), (46.5, 58.5, 0), (42.5, 55.5, 0), (35.5, 55.5, 0), (33.5, 54.5, 0), (29.5, 54.5, 0),
    (27.5, 59.5, 0), (27.5, 67.5, 0), (45.0, 66.0, 0), (47.5, 85.5, 7), (52.5, 93.5, 7), (48.5, 90.5, 0),
    (41.0, 92.0, 7), (52.5, 92.5, 0), (53.5, 93.5, 0), (58.5, 94.5, 0), (59.5, 99.0, 0), (58.5, 105.5, 7),
    (50.5, 105.5, 0), (48.5, 108.5, 0), (44.5, 110.0, 7), (44.5, 119.5, 0), (44.5, 120.5, 0), (35.5, 120.5, 0),
    (34.5, 123.5, 7), (34.5, 125.5, 0), (30.5, 129.5, 7), (34.5, 125.5, 0), (34.5, 118.0, 0), (33.5, 114.5, 0),
    (25.5, 114.5, 7), (34.5, 114.5, 0), (34.5, 110.5, 0), (34.8, 109.2, 7), (34.5, 113.5, 0), (34.5, 120.0, 0),
    (34.5, 125.5, 0), (30.0, 129.0, 0), (25.5, 130.5, 0), (14.5, 130.5, 0), (14.5, 131.0, 6), (14.0, 137.5, 0),
]
