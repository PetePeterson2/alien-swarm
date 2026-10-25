"""Mission 5, SYNTEK RESIDENTIAL: after Alien Swarm's asi-jac4-residential.

Traced from the map itself (tools/astrace.py), as tools/deima.py and tools/rydberg.py are: the deck is AS's walkable
floor in 80-unit cells, and the entity lump gave the doors, panels, buttons, eggs, biomass, spawners and the triggers
that start them. Nothing of Valve's is shipped: these are numbers and rectangles.

Same data shape as tools/level.py; tools/level.py `use()` swaps it in.
Coordinates are map units, x east, y north. Cells are 1 x 1.
"""
import math

import numpy as np

from tools.astrace import Trace, components, grow

_T = Trace('asi-jac4-residential', 0, 0, 84, 114)
W, H = _T.W, _T.H
FLOOR = 8.0
WALL_H = 2.5
HEIGHTS = _T.HEIGHTS
DECK_Z = -56.0                  # the colony block's streets and offices; the mall's gallery stands 216 higher

MERGE = 40.0                    # the street's curbs and the lobby's steps (16-48 units) are one floor here

# The walkable floor less what its walls stand on (the floor runs on under AS's detail walls and the clips along them),
# and a cell of hull wherever a thin wall parts two rooms (the offices' glass, the hallway's partitions).
DECK = _T.open_deck()
DECK &= ~_T.partitions(DECK)
OPEN = np.zeros((H, W), bool)
# The mall's gallery (160) runs along its west side over the mall floor: AS keeps a railing between them, here a strip
# of the drop, so the gallery's steel side stands over the mall (tools/pitart.py skirts) with a railing along its top.
DECK[67:95, 14] = False
OPEN[67:95, 14] = True
# The gallery's two stairs (stairs_160_top and stairs01_128noends): at its south end a flight west from the hallway to
# a landing and on north up to the gallery, and at the mall's north end a flight west up onto it.
DECK[60:63, 1:9] = True
DECK[60:65, 9:13] = True        # its foot off the hallway, where AS's stair props stand (their clips read as wall)
DECK[61:67, 1:3] = True
DECK[66:68, 1:9] = True
DECK[95:98, 15:19] = True
DECK[95:98, 14] = True          # its head onto the gallery, over AS's railing ledge
DECK[94, 15:19] = False
DECK[98, 15:19] = False
OPEN[94, 15:19] = True
OPEN[98, 15:19] = True
# The lobby's stairs up to the walkway along the hallway's south side (AS's stairs_48 behind the lobby's desk).
DECK[42, 37:40] = True
HEIGHT_SET = [((3, 60, 9, 63), -56.0), ((1, 60, 3, 63), 96.0), ((1, 63, 3, 66), 96.0), ((1, 66, 9, 68), 160.0),
              ((15, 95, 19, 98), -56.0), ((37, 41, 40, 43), -40.0), ((9, 60, 13, 65), -56.0), ((14, 95, 15, 98), 160.0)]
FLIGHTS = [((3, 60, 9, 63), 'W', -56.0, 96.0), ((1, 63, 3, 66), 'N', 96.0, 160.0), ((15, 95, 19, 98), 'W', -56.0, 160.0),
           ((37, 41, 40, 43), 'N', -40.0, 8.0)]

AREAS = [
    ('Entrance',            (30, 0, 48, 14), 'colony'),
    ('Security Hall',       (30, 14, 48, 28), 'colony'),
    ('Lobby',               (20, 28, 52, 46), 'colony'),
    ('West Block',          (0, 34, 15, 58), 'housing'),
    ('Snow Yard',           (15, 38, 22, 48), 'surface'),     # open to the sky: AS floors it in snow (snowfloor006a)
    ('Hallway',             (14, 48, 32, 64), 'colony'),
    ('Offices',             (28, 54, 46, 76), 'office'),
    ('Living Quarters',     (44, 56, 64, 74), 'housing'),
    ('Bathhouse',           (46, 74, 66, 94), 'housing'),
    ('Vents',               (64, 58, 84, 90), 'duct'),
    ('Mall',                (16, 64, 34, 100), 'mall'),
    ('Mall Gallery',        (0, 58, 16, 114), 'mall'),
    ('Elevators',           (30, 90, 46, 106), 'colony'),
]
BLOCKS = []
VIEWPORTS = []
SPAWN = (39.7, 3.5)
SPAWN_FACING = 90.0
LIFT = None
VOID = None
WINDOWS = []


# Lamps (x, y, kind, flicker), from the map's lights: the colony block is lit a pale cold white with warm lamps in the
# housing and offices; the red alarm lamps by the elevators start dark (the alarm brings them up) and are left out.
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


# ---- the mission ---------------------------------------------------------
# The doors (asw_door: autoopen 1 opens for a marine; the one at the gallery's far end is locked behind a hack panel,
# hacklevel 6, its trigger_asw_button_area 2 rows of 5 with 2 wires). A door's yaw says which way its wall runs: 90 an
# east-west wall, 0 or 180 north-south. The entrance behind the squad and the right-hand elevator stay shut.
def _door(x, y, yaw, wide=2):
    if yaw in (90.0, 270.0):
        ix, iy = int(round(x)), int(y)
        return (ix - wide // 2, iy, ix - wide // 2 + wide, iy + 1)
    ix, iy = int(x), int(round(y))
    return (ix, iy - wide // 2, ix + 1, iy - wide // 2 + wide)


DOORS = [
    ('entrance',    _door(39.7, 0.4, 90.0), 'jammed', 0.0, None),
    ('Door6',       _door(40.5, 16.4, 90.0), 'auto', 0.0, None),
    ('Door4',       _door(36.9, 56.5, 90.0), 'auto', 0.0, None),
    ('Door7',       _door(23.4, 61.8, 90.0), 'auto', 0.0, None),
    ('Door11',      _door(16.9, 61.8, 90.0), 'auto', 0.0, None),
    ('MallDoor',    _door(16.9, 66.0, 90.0), 'auto', 0.0, None),
    ('Door8',       _door(42.9, 66.0, 90.0), 'auto', 0.0, None),
    ('Door9',       _door(36.7, 78.2, 90.0), 'auto', 0.0, None),
    ('Door10',      _door(31.9, 88.5, 0.0), 'auto', 0.0, None),
    ('Door2',       _door(51.1, 88.3, 180.0), 'auto', 0.0, None),
    ('Door1',       _door(12.9, 108.3, 90.0), 'panel', 0.0, (14.0, 107.7)),
    # The goo's walls across the mall (func_brush blocker_1, blocker_2): gone once the growth on each is burnt away.
    ('blocker_1',   (17, 75, 21, 76), 'block', 0.0, None),
    ('blocker_2',   (14, 74, 17, 76), 'block', 0.0, None),
    # The two elevator cars (ElevatorModelLeft and Right): the left one comes down for the squad.
    ('elevator',    (35, 98, 38, 99), 'jammed', 0.0, None),
    ('elevator2',   (38, 98, 41, 99), 'jammed', 0.0, None),
    # The office glass (func_breakable window_01 .. window_14): gives way as a marine comes up to it. The west office,
    # its growth and its eggs, has no door at all: in through its windows.
    ('window_01',   (31, 56, 34, 57), 'glass', 0.0, None),
    ('window_03',   (39, 56, 43, 57), 'glass', 0.0, None),
    ('window_06',   (30, 61, 33, 62), 'glass', 0.0, None),
    ('window_08',   (41, 61, 44, 62), 'glass', 0.0, None),
    ('window_11',   (38, 67, 39, 69), 'glass', 0.0, None),
    ('window_12',   (34, 67, 35, 72), 'glass', 0.0, None),
]
for _name, (_x0, _y0, _x1, _y1), *_ in DOORS:
    if not _name.startswith('blocker'):
        DECK[_y0:_y1, _x0:_x1] = True
# The left car's floor: the escape area (Objective_Escape's trigger_multiple) once the car is down.
DECK[99:103, 35:38] = True
PANEL_WIRES = (2, 5, 2)
CONSOLE = (14.0, 107.7)
NEEDS_TECH = False
EQUIP_REQ = 'AS_IT_FLAMER'       # asw_equip_req equipclass1 asw_weapon_flamer
EXTRACT = (35, 99, 38, 103)
EXTRACT_NAME = 'the elevator'
OBJECTIVES = [
    ('eggs', 'Destroy the alien eggs', True, None),
    ('goo', 'Burn out the biomass', True, None),
    ('escape', 'Get to the elevator', False, None),
]
DESCRIPTION = ('SynTek\'s residential block is overrun. The swarm has laid eggs through the offices, the mall and the '
               'vents, and biomass grows over the corridors: only fire kills it. Clear out every egg and burn out every '
               'growth, then call the elevator down and hold until it comes.')
BUTTONS = [('ElevatorButtons', (38.0, 98.0), 'Call the elevator', False)]
PDAS = [((21.5, 37.5), 'Brian Howe', 8), ((19.3, 95.9), 'John Cain', 9), ((46.5, 76.8), 'Alex Tanner', 10)]
MAILS = {
    8: ('Brian Howe', 'The yard', 'Something is nesting out in the yard behind the lobby, under the snow. Maintenance went '
        'out with a torch and came back without one.\nI have locked the lobby doors at night. Do not prop them open again.'),
    9: ('John Cain', 'Mall gallery', 'The gallery is shut. There are things in the shop windows that were not there last '
        'week, white and soft, and the vents over the mall keep thumping.\nIf you are reading this, take the stairs by '
        'the hallway, not the north ones.'),
    10: ('Alex Tanner', 'Fire crews', 'The growth in the quarters will not cut and will not shoot. Burn it. The crew took '
         'the flamers to the bathhouse and that is the last we heard of them.\nThe elevators are on the alarm circuit: '
         'once called they take a minute to come down. Hold the lobby until they do.'),
}
# The medkits in the bathhouse and the vents (asw_pickup_medkit). AS's fire extinguishers and the spare pistol have no
# item in the port.
PICKUPS = [('medkit', 55.3, 89.8), ('medkit', 79.1, 63.4)]
# The ammo drops (asw_ammo_drop) and the flamer ammo (asw_ammo_flamer).
AMMO = [(28.5, 90.3), (53.7, 84.6), (55.4, 90.4)]
BARRELS = []
CREEP = [(71.0, 71.3, 3.0), (16.8, 75.2, 3.5), (31.5, 72.8, 2.5), (67.1, 86.2, 2.0), (67.5, 77.0, 2.5), (11.5, 70.0, 2.5)]


def _named(cls):
    """The entities of a class and where they stand; one on the deck's edge (where the kit lays its clutter along the
    walls) moves to the nearest free cell with deck all round it."""
    return [(e, _inside(*_T.where(e))) for e in _T.of(cls)]


_TAKEN = set()


def _inside(x, y):
    ix, iy = int(x), int(y)
    sides = sum(DECK[iy + dy, ix + dx] for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)) if 0 <= ix + dx < W and 0 <= iy + dy < H)
    if DECK[iy, ix] and sides >= 3 and (ix, iy) not in _TAKEN:
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
        return (x, y)
    _TAKEN.add(best[1:])
    return (best[1] + 0.5, best[2] + 0.5)


# Eggs: 22 laid round the level, and the offices' four templates of two (ptemplate_egg_office_1..4), two of them spawned
# at random at the start (case_office_eggspawn PickRandomShuffle, twice): 26, Objective_KillEggs NumEggs.
# Each fires 'broken:egg' (commander_count); the bathhouse egg by the vents, 'broken:bathegg', wakes the mortarbugs on
# Insane (insane_spawn_mortar01).
EGGS = []
for _e, (_x, _y) in _named('asw_egg'):
    _n = _e.get('name', '')
    EGGS.append((_x, _y, int(_n[-1]) if _n.startswith('eggs_office_') else 0, 'bathegg' if _T.where(_e) == (65.7, 86.3) else 'egg'))
EGG_PICK = (4, 2)
# Biomass (asw_alien_goo, 8: Objective_BurnGoo NumGoo): (x, y, radius, name). The mall's three hold its goo walls up
# and wake the mall when lit; the office's wake the offices.
_GOO = {(15.1, 73.9): 'mall1', (17.0, 75.7): 'mall2', (19.4, 74.7): 'mall3', (31.4, 71.8): 'office1', (31.5, 73.8): 'office2'}
BIOMASS = [(_x, _y, 1.4 if _GOO.get(_T.where(_e), '').startswith('mall') else 1.1, _GOO.get(_T.where(_e), 'goo'))
           for _e, (_x, _y) in _named('asw_alien_goo')]
# Asleep at the start: the grubs (asw_grub, 21) and the vent parasites (asw_parasite, 4). AS's grub sacs, which burst
# into grubs as a marine passes, are not in the port.
SLEEPERS = ([('AS_GRUB', _x, _y) for _e, (_x, _y) in _named('asw_grub')] +
            [('AS_PARASITE', _x, _y) for _e, (_x, _y) in _named('asw_parasite')])


def _spawners():
    out = []
    for row in _T.spawners():
        at = _snap(row[1], row[2])
        if at is not None:
            out.append((row[0], round(at[0], 1), round(at[1], 1)) + tuple(row[3:]))
    # The elevator's mortarbug comes in a template (template_morter_elev, 30 s after the call): a spawner of one here.
    out.append(('template_morter_elev', 33.5, 81.5, 'AS_MORTAR', 1, 1, 1.0, 0, 0, 0, 1, 0))
    return out


SPAWNERS = _spawners()
VENTS = []
for _s in sorted(SPAWNERS, key=lambda s: s[2]):
    if len(VENTS) < 32 and all(math.hypot(_s[1] - vx, _s[2] - vy) >= 6.0 for vx, vy in VENTS):
        VENTS.append((_s[1], _s[2]))


def _glass(x, y):
    return ('shatter', '%.1f,%.1f' % (x, y), 0.0)


# Triggers: rectangle, once, chance, [(action, argument, delay)], options.
TRIGGERS = [
    ((37.8, 8.3, 42.5, 9.6), True, 1.0, [('line', 'co_m5_ob1', 0.5)]),
    ((38.1, 29.9, 46.1, 30.3), True, 1.0, [('spawn', 'spawn_intro_drone', 0.0), ('spawn', 'spawn_intro_buzzer', 0.0)]),
    ((32.5, 32.7, 32.9, 36.5), True, 1.0, [('line', 'co_m5_parasite', 0.0)]),
    ((26.2, 49.2, 26.5, 55.9), True, 1.0, [('spawn', 'spawn_intro_computer', 0.0)]),
    # The hallway: one of two ambushes, picked at the start (case_hallway_spawn).
    ((14.5, 51.5, 19.3, 51.9), True, 1.0, [('spawn', 'spawn_hall_bommer1', 0.0), ('spawn', 'spawn_hall_buzzer_1', 0.0),
                                           ('spawn', 'spawn_hall_bommer1a', 0.5)], {'name': 'hallway_spawn_01', 'off': True}),
    ((14.9, 52.3, 19.3, 55.9), True, 1.0, [('spawn', 'spawn_hall_bommer2', 0.0), ('spawn', 'spawn_hall_drone2', 0.0),
                                           ('spawn', 'spawn_hall_bommer2a', 0.5)], {'name': 'hallway_spawn_02', 'off': True}),
    ((14.9, 54.3, 18.9, 55.9), True, 1.0, [('stop', 'spawn_hall_bommer1a', 0.0)]),
    ((30.7, 55.1, 43.7, 55.7), True, 1.0, [('spawn', 'spawner_office_base', 0.0)]),
    ((14.5, 61.9, 30.7, 65.7), True, 1.0, [('spawn', 'spawner_office_base', 0.0), ('stop', 'spawn_hall_drone2', 0.0)]),
    # The offices wake once their growth is lit (relay_sounds_mall1 enables trigger_spawning_office).
    ((29.6, 57.5, 44.1, 74.3), True, 1.0, [('spawn', 'spawner_office_ranger', 0.0), ('spawn', 'spawn_boomer_office', 0.0)],
     {'name': 'trigger_spawning_office', 'off': True}),
    # The office glass across the corners (window_15, window__10) breaks as the squad passes; the rest are glass doors.
    ((33.7, 65.6, 35.2, 67.0), True, 1.0, [_glass(34.5, 66.3)]), ((38.5, 65.7, 39.9, 67.1), True, 1.0, [_glass(39.1, 66.4)]),
    # The mall: a ranger on the gallery as the squad comes up, the word about more growth, the boomers on the catwalk.
    ((8.9, 65.9, 14.3, 66.3), True, 1.0, [('spawn', 'spawner_ranger_mall_top', 0.0)]),
    ((8.9, 66.7, 20.5, 67.1), True, 1.0, [('line', 'co_m5_more_bio', 0.0)]),
    ((12.1, 88.3, 14.5, 88.7), True, 1.0, [('pick', 'spawn_mall_topBommer_1|spawn_mall_topBommer_2', 0.0),
                                           ('disable', 'trigger_boomer_caltwalk', 0.0)], {'name': 'trigger_boomer_caltwalk'}),
    ((12.1, 94.3, 16.5, 97.9), True, 1.0, [('pick', 'spawn_mall_topBommer_1|spawn_mall_topBommer_2', 0.0),
                                           ('disable', 'trigger_boomer_caltwalk', 0.0)], {'name': 'trigger_boomer_caltwalk'}),
    ((12.1, 66.7, 25.5, 97.8), True, 1.0, [('spawn', 'spawner_mall_ranger', 2.0), ('spawn', 'spawner_drone_mall', 0.0),
                                           ('spawn', 'spawner_buzzer_mall_post', 0.0)], {'name': 'trigger_mallspawn_north', 'off': True}),
    # The quarters burn as the squad comes in (FireSouth, FireQuarter), and buzzers come through the bathhouse windows.
    ((50.9, 59.5, 52.2, 71.6), True, 1.0, [('spawn', 'spawner_bath_drone', 0.0), ('spawn', 'spawner_buzzer_bath', 2.0),
                                           ('boom', '61.4,68.5', 0.0), ('shatter', '53.3,68.5', 2.0)]),
    ((52.1, 67.1, 60.4, 71.7), True, 1.0, [('boom', '58.0,76.7', 0.0)]),
    ((63.1, 84.6, 63.4, 91.3), True, 1.0, [('spawn', 'spawner_bath_top', 0.0)], {'name': 'trigger_bath_spawn'}),
    # The vents: drones out of the ducts on a timer once the squad is in them (timer_vent_spawn, every 8 s).
    ((66.2, 83.8, 68.5, 84.9), False, 1.0, [('disable', 'trigger_bath_spawn', 0.0), ('enable', 'timer_vent_spawn', 0.0)]),
    ((71.8, 63.0, 72.9, 64.0), False, 1.0, [('enable', 'timer_vent_spawn', 0.0)]),
    ((72.1, 63.0, 74.0, 64.0), True, 1.0, [('spawn', 'insane_spawn_ranger01', 6.0)]),
]
TIMERS = [('timer_vent_spawn', 8.0, 8.0, False), ('hall_pick', 0.1, 0.1, True)]
ONS = [
    # The hallway's ambush, picked as the level starts.
    ('timer:hall_pick', 'disable', 'hall_pick', 0.0), ('timer:hall_pick', 'pickfire', 'hall_pick_1|hall_pick_2', 0.0),
    ('hall_pick_1', 'enable', 'hallway_spawn_01', 0.0), ('hall_pick_2', 'enable', 'hallway_spawn_02', 0.0),
    ('timer:timer_vent_spawn', 'pickfire', 'vent_spawn_1|vent_spawn_2|vent_spawn_3', 0.0),
    ('vent_spawn_1', 'spawnone', 'spawner_vent_1', 0.0), ('vent_spawn_2', 'spawnone', 'spawner_vent_2', 0.0),
    ('vent_spawn_3', 'spawnone', 'spawner_vent_3', 0.0),
    # The growth: the mall's, lit, wakes the mall (and its shieldbug on Insane); burnt, its walls of goo go.
    ('ignite:mall1', 'enable', 'trigger_mallspawn_north', 4.0), ('ignite:mall2', 'enable', 'trigger_mallspawn_north', 4.0),
    ('ignite:mall3', 'enable', 'trigger_mallspawn_north', 4.0), ('ignite:mall2', 'spawn', 'insane_spawn_shieldbug01', 0.0),
    ('broken:mall2', 'open', 'blocker_2', 4.0), ('broken:mall3', 'open', 'blocker_1', 0.0),
    ('ignite:office1', 'enable', 'trigger_spawning_office', 2.0),
    # The commander's word when most eggs are gone (commander_count, 18).
    ('broken:egg', 'count', 'commander_count', 0.0), ('max:commander_count', 'line', 'co_m5_almost', 0.0),
    ('broken:bathegg', 'count', 'commander_count', 0.0), ('broken:bathegg', 'spawn', 'insane_spawn_mortar01', 0.0),
    # Both done (count_completed): the elevator has power.
    ('done:eggs', 'count', 'count_completed', 0.0), ('done:goo', 'count', 'count_completed', 0.0),
    ('max:count_completed', 'power', 'ElevatorButtons', 0.0), ('max:count_completed', 'line', 'co_m5_elevator', 1.0),
    # The call (relay_lighting, relay_elevator): the lights go, the alarm, the swarm from every side, and the left car's
    # doors open 58 + 9 s later.
    ('pressed:ElevatorButtons', 'lights', '2', 0.0), ('pressed:ElevatorButtons', 'stop', 'spawner_office_base', 0.0),
    ('pressed:ElevatorButtons', 'spawn', 'spawner_elev_drone', 2.0), ('pressed:ElevatorButtons', 'spawn', 'spawn_elev_boomer', 10.0),
    ('pressed:ElevatorButtons', 'spawn', 'spawner_elev_ranger', 20.0), ('pressed:ElevatorButtons', 'spawn', 'template_morter_elev', 30.0),
    ('pressed:ElevatorButtons', 'spawn', 'insane_spawn_shieldbug02', 35.0),
    ('pressed:ElevatorButtons', 'open', 'elevator', 67.0),
]
# Insane's parasite bursts (InstanceAuto5..11): five seconds of a timer picking defanged or full parasites as the squad
# walks in (their spawners are Insane only, MinSkillLevel 4).
_INSANE = [(5, (26.6, 28.6, 33.7, 36.5)), (6, (15.9, 50.8, 23.0, 58.8)), (7, (4.8, 59.4, 11.9, 67.3)), (8, (11.4, 95.0, 18.6, 103.0)),
           (9, (31.2, 66.3, 38.4, 74.3)), (10, (10.2, 58.1, 17.2, 66.2)), (11, (22.9, 48.5, 30.0, 56.5))]
for _n, _r in _INSANE:
    _a = 'InstanceAuto%d-' % _n
    TRIGGERS.append((_r, True, 1.0, [('enable', _a + 'timer', 0.0), ('disable', _a + 'timer', 5.0)]))
    TIMERS.append((_a + 'timer', 0.1, 0.1, False))
    ONS += [('timer:' + _a + 'timer', 'pickfire', _a + 'depara|' + _a + 'para', 0.0),
            (_a + 'depara', 'spawnone', _a + 'insane_spawn_depara', 0.0), (_a + 'para', 'spawnone', _a + 'insane_spawn_para', 0.0)]
COUNTERS = [('count_completed', 2), ('commander_count', 18)]
MOVERS = []
JUMPS = []

LINES = {
    'co_m5_ob1': 'This is the SynTek residential block, eggs and biomass right through it. Burn the growth, smash every egg, then get to the elevators.',
    'co_m5_parasite': 'Careful round those eggs: whatever hatches goes straight for a marine.',
    'co_m5_more_bio': 'More biomass in the mall. Bullets won\'t touch it: use the flamer.',
    'co_m5_almost': 'Nearly there. A few eggs left, keep looking.',
    'co_m5_elevator': 'That\'s the lot. Get to the elevators and call one down.',
}

CHECKPOINTS = [SPAWN, (40.0, 36.0), (20.0, 58.0), (37.0, 64.0), (57.0, 86.0), (37.0, 95.0)]
ZONES = []
# The autopilot's stops (tools/routeplan.py --plan cuts the walk between them into clear legs): the washroom's egg,
# the offices, the mall's growth from the south before its walls of goo come down, the gallery by its south-west
# stairs, the locked door at its north end and the eggs behind it, down the north stairs, the bathhouse and the
# vents, and back to call the elevator.
ROUTE_STOPS = [
    (40.0, 30.0, 0), (16.5, 49.5, 7), (41.5, 58.5, 7), (33.0, 58.5, 7), (36.5, 69.5, 7), (32.0, 70.0, 7),
    (42.5, 68.5, 7), (18.0, 70.5, 7), (10.0, 67.5, 7), (12.5, 83.0, 7), (12.5, 106.5, 1), (12.5, 105.5, 7),
    (35.0, 92.0, 0), (58.0, 88.0, 7), (68.5, 84.5, 7), (68.5, 81.5, 7), (66.5, 77.5, 7), (68.5, 76.5, 7),
    (74.0, 75.5, 7), (78.5, 73.5, 7), (77.5, 63.5, 7), (72.5, 67.5, 7), (72.5, 64.5, 7), (70.5, 70.5, 7),
    (66.5, 63.5, 7), (38.5, 96.5, 5), (36.5, 96.5, 6), (36.5, 101.0, 0),
]
ROUTE = [
    (40.0, 30.0, 0), (37.5, 50.5, 0), (29.5, 51.5, 0), (23.5, 54.5, 0), (18.5, 53.5, 0), (16.5, 49.5, 7),
    (18.5, 53.5, 0), (40.5, 55.5, 0), (41.5, 58.5, 7), (33.0, 58.5, 7), (35.5, 58.5, 0), (36.5, 68.5, 0),
    (36.5, 69.5, 7), (32.0, 70.0, 7), (37.5, 64.5, 0), (42.5, 65.5, 0), (42.5, 68.5, 7), (42.5, 65.5, 0),
    (32.5, 63.5, 0), (17.5, 65.5, 0), (17.5, 70.5, 0), (18.0, 70.5, 7), (16.5, 65.5, 0), (7.5, 61.5, 0),
    (2.5, 62.5, 0), (2.5, 66.5, 0), (10.0, 67.5, 7), (12.5, 78.5, 0), (12.5, 83.0, 7), (12.5, 106.5, 1),
    (12.5, 105.5, 7), (13.5, 97.5, 0), (19.5, 95.5, 0), (19.5, 88.5, 0), (37.5, 88.5, 0), (35.5, 93.5, 0),
    (35.0, 92.0, 0), (44.5, 88.5, 0), (58.0, 88.0, 7), (66.5, 87.5, 0), (66.5, 84.5, 0), (68.5, 84.5, 7),
    (68.5, 81.5, 7), (66.5, 81.5, 0), (66.5, 77.5, 7), (68.5, 77.5, 0), (68.5, 76.5, 7), (69.5, 75.5, 0),
    (74.0, 75.5, 7), (77.5, 75.5, 0), (77.5, 74.5, 0), (78.5, 73.5, 7), (78.5, 64.5, 0), (77.5, 63.5, 7),
    (77.5, 67.5, 0), (72.5, 67.5, 7), (72.5, 64.5, 7), (72.5, 70.5, 0), (70.5, 70.5, 7), (69.5, 71.5, 0),
    (68.5, 84.5, 0), (66.5, 84.5, 0), (66.5, 87.5, 0), (56.5, 87.5, 0), (56.5, 70.5, 0), (60.5, 69.5, 0),
    (61.5, 67.5, 0), (65.5, 67.5, 0), (66.5, 66.5, 0), (66.5, 63.5, 7), (66.5, 66.5, 0), (65.5, 67.5, 0),
    (61.5, 67.5, 0), (55.5, 72.5, 0), (52.5, 75.5, 0), (37.5, 77.5, 0), (37.5, 95.5, 0), (38.5, 96.5, 5),
    (36.5, 96.5, 6), (36.5, 101.0, 0),
]
