"""The derelict: one deck of the colony transport USCSS Halcyon Drift.

Everything about the place lives here: the rooms and corridors (carved out of
solid hull on a one-unit grid), what each room is dressed with, where the
lamps hang, where the aliens come from. build.py turns it into terrain, hull
meshes, placed doodads, the painted pathing layer and the Galaxy tables.

Coordinates are map units, x east, y north. Cells are 1 x 1.
"""
import math
import numpy as np

W, H = 96, 80                 # map size (multiples of 8)
FLOOR = 8.0                   # terrain height of the deck
WALL_H = 2.5                  # bulkhead height above the deck

# Rooms and corridors: name, (x0, y0, x1, y1) exclusive, kind.
# Kinds drive texturing and dressing: bay, hall, mess, reactor, cargo, lab, hive, duct.
AREAS = [
    ('Docking Bay',        (8, 8, 28, 22), 'bay'),
    ('South Passage',      (15, 22, 19, 36), 'hall'),
    ('Armoury',            (19, 27, 25, 33), 'bay'),
    ('Crew Mess',          (6, 36, 26, 50), 'mess'),
    ('Mess Passage',       (26, 41, 34, 45), 'hall'),
    ('Reactor Core',       (34, 30, 58, 54), 'reactor'),
    ('Service Way',        (28, 14, 64, 18), 'hall'),
    ('Reactor Lift',       (42, 18, 46, 30), 'hall'),
    ('Cargo Hold',         (64, 8, 88, 30), 'cargo'),
    ('Cargo Spur',         (58, 40, 70, 44), 'hall'),
    ('Cargo Ramp',         (66, 30, 70, 40), 'hall'),
    ('Lab Passage',        (58, 48, 66, 52), 'hall'),
    ('Xenobiology Lab',    (64, 48, 86, 70), 'lab'),
    ('Hive Passage',       (42, 54, 46, 62), 'hive'),
    ('The Nest',           (30, 60, 56, 74), 'hive'),
    ('Lab Breach',         (56, 63, 64, 67), 'hive'),
    ('Maintenance Duct',   (10, 50, 12, 68), 'duct'),
    ('Duct Crossing',      (10, 66, 30, 68), 'duct'),
]
# Solid blocks inside rooms: pillars, the reactor's shielding, machinery.
BLOCKS = [
    (44, 40, 48, 44),                                      # reactor core housing
    (38, 34, 40, 36), (52, 34, 54, 36), (38, 48, 40, 50), (52, 48, 54, 50),   # reactor pylons
    (72, 14, 74, 24), (78, 14, 80, 24),                    # cargo racks
    (14, 42, 18, 44),                                      # mess serving counter
    (74, 58, 76, 62),                                      # lab partition
    (40, 66, 42, 68), (46, 70, 48, 72),                    # nest pillars
]

SPAWN = (20.0, 12.5)          # the marines step off the dropship here
SPAWN_FACING = 45.0

# Lamps (x, y, kind, flicker): kinds are white, cold, red, green, orange, purple. Flicker
# 0 steady, 1 failing (long dark spells), 2 sputtering, 3 alarm pulse.
LIGHTS = [
    (12.0, 10.0, 'yellow', 0), (24.0, 10.0, 'white', 2), (12.0, 20.0, 'cold', 0), (24.0, 20.0, 'yellow', 0),
    (17.0, 25.0, 'white', 1), (17.0, 31.0, 'red', 3), (22.0, 30.0, 'cold', 0),
    (9.0, 39.0, 'white', 2), (22.0, 39.0, 'white', 0), (9.0, 47.0, 'white', 1), (22.0, 47.0, 'orange', 2),
    (30.0, 43.0, 'red', 3),
    (46.0, 42.0, 'cold', 0), (37.0, 33.0, 'white', 0), (55.0, 33.0, 'white', 2), (37.0, 51.0, 'white', 1), (55.0, 51.0, 'white', 0),
    (40.0, 42.0, 'cold', 0), (52.0, 42.0, 'cold', 0),
    (33.0, 16.0, 'white', 1), (44.0, 16.0, 'white', 0), (55.0, 16.0, 'red', 3), (44.0, 24.0, 'white', 2),
    (68.0, 11.0, 'white', 0), (84.0, 11.0, 'white', 1), (68.0, 27.0, 'orange', 2), (84.0, 27.0, 'white', 0), (76.0, 19.0, 'white', 2),
    (63.0, 42.0, 'red', 3), (68.0, 35.0, 'white', 1),
    (61.0, 50.0, 'white', 2), (68.0, 52.0, 'white', 0), (82.0, 52.0, 'green', 0), (68.0, 66.0, 'cold', 1), (82.0, 66.0, 'white', 2), (75.0, 64.0, 'green', 0),
    (44.0, 58.0, 'purple', 0), (34.0, 63.0, 'purple', 1), (52.0, 63.0, 'purple', 0), (34.0, 71.0, 'purple', 2), (52.0, 71.0, 'purple', 0), (43.0, 69.0, 'orange', 2),
    (60.0, 65.0, 'red', 3),
    (11.0, 55.0, 'red', 3), (11.0, 63.0, 'white', 1), (20.0, 67.0, 'white', 2),
]

# Where the director brings aliens in from (vents, hatches, holes in the hull): x, y, room.
VENTS = [
    (27.0, 9.0), (9.0, 21.0), (24.0, 49.0), (7.0, 37.0), (35.0, 31.0), (57.0, 53.0), (57.0, 31.0),
    (87.0, 9.0), (87.0, 29.0), (65.0, 29.0), (85.0, 69.0), (65.0, 69.0), (31.0, 73.0), (55.0, 73.0),
    (31.0, 61.0), (11.0, 67.0), (63.0, 15.0), (29.0, 17.0),
]
# Egg clusters: hatch parasites when a marine comes close.
EGGS = [(36.0, 70.0), (37.5, 71.0), (50.0, 71.5), (51.0, 70.0), (49.0, 62.0), (33.0, 64.5), (80.0, 68.0), (84.0, 60.0), (70.0, 68.5)]
# Biomass growths (burn them with the flamer, or shoot them a long time): x, y, radius.
BIOMASS = [(44.0, 60.5, 1.4), (60.0, 65.0, 1.3), (70.0, 54.0, 1.0)]
# Ammo crates: walk over to refill.
AMMO = [(22.0, 30.5), (46.0, 32.0), (66.5, 12.0), (60.5, 42.0), (25.0, 38.0)]

# Room dressing: (model, x, y, facing degrees, scale, solid radius or 0)
PROPS = [
    # Docking bay: the dropship, crates, deck markings.
    ('Hercules', 13.5, 15.0, 30.0, 0.75, 1.6),
    ('DOM_Crate', 25.5, 20.0, 15.0, 0.9, 0.7), ('DOM_Crate', 26.5, 18.5, 80.0, 0.9, 0.7),
    ('StarshipContainers', 25.5, 10.5, 0.0, 0.6, 1.0),
    ('SpacePlatformCautionLights', 9.0, 15.0, 90.0, 1.0, 0.0),
    ('DOM_Groundlights', 20.0, 9.0, 0.0, 1.0, 0.0),
    # Armoury.
    ('DOM_GunRacks', 23.5, 32.2, 180.0, 0.8, 0.0), ('DOM_LabCrates', 20.5, 28.0, 0.0, 0.8, 0.0),
    # Crew mess: tables, a cabinet, signs of a last stand.
    ('ValhallaTable', 10.0, 40.0, 0.0, 0.8, 0.8), ('ValhallaTable', 10.0, 46.0, 90.0, 0.8, 0.8),
    ('ValhallaTable', 21.0, 46.0, 30.0, 0.8, 0.8), ('CastanarTable', 21.5, 40.0, 0.0, 0.8, 0.0),
    ('ValhallaCabinet', 7.0, 48.5, 90.0, 0.8, 0.0),
    ('DOM_CeilingDebris_Beams', 19.0, 37.5, 70.0, 0.8, 0.0), ('SpacePlatformWallDebris', 7.5, 43.0, 0.0, 0.8, 0.0),
    ('ZergCarcasses', 15.0, 47.0, 0.0, 0.7, 0.0),
    # Reactor core.
    ('KPReactor', 46.0, 42.0, 0.0, 1.0, 0.0),        # the glowing core on top of its housing (tools/propart.py)
    ('SpacePlatformGenerator', 36.5, 42.0, 90.0, 0.7, 0.0), ('SpacePlatformGenerator', 55.5, 42.0, 270.0, 0.7, 0.0),
    ('ElectricalArcs', 44.0, 39.5, 0.0, 0.8, 0.0), ('ElectricalArcs', 48.5, 44.5, 0.0, 0.8, 0.0),
    ('SpacePlatformSteamVent', 40.0, 32.0, 0.0, 0.8, 0.0), ('SpacePlatformSteamVent', 52.0, 52.0, 0.0, 0.8, 0.0),
    ('MoebiusLabConsoles', 35.5, 38.0, 90.0, 0.7, 0.0), ('MoebiusLabConsoles', 56.5, 46.0, 270.0, 0.7, 0.0),
    # Service way and lift.
    ('SpacePlatformSteamVent', 38.0, 15.0, 0.0, 0.7, 0.0), ('DOM_Fire_Large', 58.5, 16.5, 0.0, 0.5, 0.0),
    ('SmokeMedium', 58.5, 16.5, 0.0, 0.6, 0.0),
    # Cargo hold.
    ('StarshipContainers', 76.0, 12.0, 90.0, 0.6, 0.0), ('StarshipContainers', 76.0, 26.0, 90.0, 0.6, 0.0),
    ('DOM_Crate', 67.0, 22.0, 10.0, 1.0, 0.7), ('DOM_Crate', 68.2, 23.4, 50.0, 1.0, 0.7), ('DOM_Crate', 84.0, 16.0, 0.0, 1.0, 0.7),
    ('DOM_Crate', 85.0, 22.5, 30.0, 1.0, 0.7), ('MoebiusLabZergCrates', 83.0, 27.0, 0.0, 0.8, 0.0),
    ('DOM_RocketPallet', 69.0, 12.0, 0.0, 0.7, 0.0), ('SpacePlatformCablesLargeZerged', 87.0, 19.0, 90.0, 0.6, 0.0),
    # Xenobiology lab.
    ('CastanarStasisTube', 67.0, 58.0, 0.0, 0.7, 0.6), ('CastanarStasisTube', 67.0, 62.0, 0.0, 0.7, 0.6),
    ('CastanarStasisTubeDebris', 67.0, 66.0, 0.0, 0.7, 0.0), ('CastanarStasisTube', 84.0, 56.0, 0.0, 0.7, 0.6),
    ('MoebiusLab_DissectionTable', 80.0, 62.0, 90.0, 0.7, 0.7), ('CastanarWorkstation', 85.0, 64.0, 270.0, 0.7, 0.0),
    ('CastanarHoloProjector', 79.0, 53.0, 0.0, 0.7, 0.0), ('DOM_LabConsoles', 70.0, 49.5, 0.0, 0.7, 0.0),
    ('CastanarMonitorWall', 76.0, 69.3, 180.0, 0.7, 0.0), ('CocoonedColonists', 84.5, 68.0, 220.0, 0.6, 0.0),
    ('SplatAliveInside', 72.0, 66.0, 0.0, 0.8, 0.0),
    # The nest.
    ('CocoonedColonists', 32.0, 72.0, 160.0, 0.7, 0.0), ('CocoonedColonists', 54.0, 61.5, 20.0, 0.7, 0.0),
    ('CreepPods', 38.0, 63.0, 0.0, 0.8, 0.0), ('CreepPods', 52.0, 67.0, 0.0, 0.8, 0.0), ('CreepPods', 44.0, 72.0, 0.0, 0.8, 0.0),
    ('SpacePlatformCreepedDoodads', 47.0, 64.0, 0.0, 0.8, 0.0), ('ZergCarcasses', 36.0, 66.0, 40.0, 0.8, 0.0),
    ('SplatAliveInside', 43.0, 64.0, 0.0, 1.0, 0.0),
    # Ducts.
    ('SpacePlatformSteamVent', 11.0, 59.0, 0.0, 0.6, 0.0), ('SpaceSteamJet', 25.0, 67.0, 0.0, 0.5, 0.0),
]


# ---- the mission (mission 1, DISTRESS BEACON: src/Mission.galaxy) ---------
# Down the service way to the reactor, hold its console until the power comes back
# (a swarm comes while you do), then back to the dropship.
CONSOLE = (36.8, 38.0)             # where marines stand to restore power, beside the reactor consoles
EXTRACT = (16, 9, 27, 21)          # the dropship's side of the bay: everyone alive inside ends the mission
ZONES = [('reactor', (34, 30, 58, 54))]
CHECKPOINTS = [SPAWN, (44.0, 24.0)]
# The autopilot's way through: x, y, wait (1 until the power is back).
ROUTE = [
    (24.0, 16.0, 0), (30.0, 16.0, 0), (44.0, 16.0, 0), (44.0, 24.0, 0), (44.0, 31.0, 0), (42.0, 38.0, 0), (CONSOLE[0], CONSOLE[1], 1),
    (42.0, 38.0, 0), (44.0, 31.0, 0), (44.0, 24.0, 0), (44.0, 16.0, 0), (30.0, 16.0, 0), (21.5, 15.0, 0),
]

# Mission levels (tools/cargo.py) carry the same data plus the elevator and mission tables.
LEVEL = 'deck'
VOID = None
LIFT = None
WINDOWS = []
# Hull cells whose faces show the window panel for the look alone (WINDOWS are the gallery's, which give way).
VIEWPORTS = [(10, 22), (11, 22), (24, 22), (25, 22), (76, 30), (77, 30), (84, 30), (85, 30)]


_DECK = None


def use(name):
    """Swap in a level's data: every upper-case name of tools/<name>.py, or the deck's own back again."""
    global LEVEL, _DECK
    if _DECK is None:
        _DECK = {k: v for k, v in globals().items() if k.isupper() and not k.startswith(('KIT_', '_'))}
    for key in [k for k in globals() if k.isupper() and not k.startswith(('KIT_', '_')) and k not in _DECK]:
        del globals()[key]
    globals().update(_DECK)
    globals().pop('shaft_columns', None)
    if name != 'deck':
        import importlib
        mod = importlib.import_module('tools.' + name)
        for key, value in vars(mod).items():
            if key.isupper() or key == 'shaft_columns':
                globals()[key] = value
    LEVEL = name


def in_void(x, y):
    """The black drop round the elevator platform: neither deck nor hull, nothing is drawn there."""
    if VOID is None:
        return False
    x0, y0, x1, y1 = VOID
    if not (x0 <= x < x1 and y0 <= y < y1):
        return False
    lx0, ly0, lx1, ly1 = LIFT
    return not (lx0 <= x < lx1 and ly0 <= y < ly1)


def carve():
    """(floor bool[H, W], room index int[H, W] with -1 for hull). A level traced from the real map (tools/astrace.py)
    gives its floor as DECK, bool[H, W]; its AREAS then only name the rooms, and a deck cell outside them all
    belongs to the nearest."""
    deck = globals().get('DECK')
    floor = np.zeros((H, W), bool)
    room = np.full((H, W), -1, int)
    for i, (_, (x0, y0, x1, y1), _) in enumerate(AREAS):
        floor[y0:y1, x0:x1] = True
        room[y0:y1, x0:x1] = i
    # Rooms claim the cells where the corridors run into them.
    for i, (_, (x0, y0, x1, y1), kind) in enumerate(AREAS):
        if kind != 'hall' and kind != 'duct':
            room[y0:y1, x0:x1] = i
    if deck is not None:
        floor = deck.copy()
        room = _nearest(room, floor)
    for x0, y0, x1, y1 in BLOCKS:
        floor[y0:y1, x0:x1] = False
    return floor, room


def _nearest(room, floor):
    """Deck cells outside every AREAS rectangle take the room of the nearest that is in one (rings outward)."""
    room = np.where(floor, room, -1)
    seeds = room.copy()
    H_, W_ = room.shape
    todo = floor & (room < 0)
    while todo.any():
        grow = seeds.copy()
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            sh = np.full_like(seeds, -1)
            sh[max(0, dy):H_ + min(0, dy), max(0, dx):W_ + min(0, dx)] = seeds[max(0, -dy):H_ - max(0, dy), max(0, -dx):W_ - max(0, dx)]
            grow = np.where(grow < 0, sh, grow)
        if (grow == seeds).all():
            break
        seeds = grow
        room = np.where(todo & (seeds >= 0), seeds, room)
        todo = floor & (room < 0)
    return room


def kind_at(room, x, y):
    i = room[int(y), int(x)]
    return AREAS[i][2] if i >= 0 else 'hull'


def _mission_points():
    """Every point the mission uses: spawns, pickups, panels, spawners, vents, the route; clutter keeps clear of them."""
    g = globals()
    pts = [g.get('SPAWN')] + list(g.get('CHECKPOINTS') or []) + list(g.get('ROUTE') or []) + list(g.get('VENTS') or [])
    pts += [(x, y) for _, x, y in g.get('PICKUPS') or []] + [p for p, *_ in g.get('PDAS') or []]
    pts += [g.get(k) for k in ('COMPUTER', 'CONSOLE', 'SENTRY_SPOT', 'DOOR_PANEL', 'LIFT_PANEL')]
    pts += [(r[1], r[2]) for r in g.get('SPAWNERS') or []] + [(x, y) for _, x, y in g.get('SLEEPERS') or []]
    pts += list(g.get('BARRELS') or []) + list(g.get('AMMO') or []) + list(g.get('EGGS') or [])
    pts += [(r[1], r[2]) for r in PROPS]
    for d in g.get('DOORS') or []:
        x0, y0, x1, y1 = d[1]
        pts += [(x0 + 0.5 * (x1 - x0), y0 + 0.5 * (y1 - y0))]
        if d[4]:
            pts.append(d[4])
    for key in ('DOOR',):
        if g.get(key):
            x0, y0, x1, y1 = g[key]; pts.append(((x0 + x1) / 2, (y0 + y1) / 2))
    out = []
    for p in pts:
        if p and isinstance(p, (tuple, list)) and len(p) >= 2 and all(isinstance(v, (int, float)) for v in p[:2]):
            out.append((float(p[0]), float(p[1])))
    return out


def clutter(floor, room):
    """Crates and barrels standing against the walls of the big rooms, as Alien Swarm's storage and bays are
    crowded with them: (piece, x, y, facing, cell). Each is solid (blocked() adds its cell, so marines and aliens
    go round it); none within two cells of a doorway or of anything the mission uses, none beside another."""
    import random
    rng = random.Random(W * 131 + H * 7)
    keep = _mission_points()
    taken = set(); out = []
    for i, (name, (x0, y0, x1, y1), kind) in enumerate(AREAS):
        if kind not in ('bay', 'cargo', 'reactor', 'mess') or x1 - x0 < 7 or y1 - y0 < 7:
            continue
        cells = [(x, y) for y in range(y0, y1) for x in range(x0, x1) if floor[y, x] and room[y, x] == i]
        cellset = set(cells)
        # Where this room opens onto another (or onto anything but itself), and the cells near it.
        opening = [(x, y) for x, y in cells for dx, dy in ((0, 1), (1, 0), (0, -1), (-1, 0))
                   if 0 <= x + dx < W and 0 <= y + dy < H and floor[y + dy, x + dx] and room[y + dy, x + dx] != i]
        # One fat red pipe along a wall in some of the machine rooms, bays and stores: four wall-side cells in a row
        # under one stretch of wall, all clear as above.
        if kind in ('reactor', 'cargo', 'bay') and rng.random() < 0.7:
            for x, y in cells:
                runs = []
                # North and side walls only: a pipe against a south wall hides behind its top from this camera.
                for dx, dy, hx, hy, rot in ((1, 0, 0, 1, 0.0), (0, 1, 1, 0, 90.0), (0, 1, -1, 0, 90.0)):
                    run = [(x + dx * k, y + dy * k) for k in range(4)]
                    if all(c in cellset and c not in taken and not (0 <= c[0] + hx < W and 0 <= c[1] + hy < H and floor[c[1] + hy, c[0] + hx])
                           for c in run):
                        runs.append((run, hx, hy, rot))
                ok = None
                for run, hx, hy, rot in runs:
                    if any(abs(cx - ox) <= 2 and abs(cy - oy) <= 2 for cx, cy in run for ox, oy in opening):
                        continue
                    if any(math.hypot(cx + 0.5 - px, cy + 0.5 - py) < 2.2 for cx, cy in run for px, py in keep):
                        continue
                    if any((cx + ex, cy + ey) in taken for cx, cy in run for ex in (-1, 0, 1) for ey in (-1, 0, 1)):
                        continue
                    if not all((cx - hx * k, cy - hy * k) in cellset for cx, cy in run for k in (1, 2, 3)):
                        continue
                    ok = (run, hx, hy, rot); break
                if ok:
                    run, hx, hy, rot = ok
                    taken.update(run)
                    mx = sum(c[0] for c in run) / 4.0 + 0.5 + hx * 0.12; my = sum(c[1] for c in run) / 4.0 + 0.5 + hy * 0.12
                    out.append(('KPBigPipe', mx, my, rot, run))
                    break
        for x, y in cells:
            hull = [not (0 <= x + dx < W and 0 <= y + dy < H) or not floor[y + dy, x + dx] for dx, dy in ((0, -1), (1, 0), (0, 1), (-1, 0))]
            if sum(hull) != 1:
                continue
            if any(abs(x - ox) <= 2 and abs(y - oy) <= 2 for ox, oy in opening):
                continue
            if any(math.hypot(x + 0.5 - px, y + 0.5 - py) < 2.2 for px, py in keep):
                continue
            # Never in the space the squad must all reach to finish (the escape lift, the transit platform).
            ex = globals().get('EXTRACT')
            if ex and ex[0] - 1 <= x < ex[2] + 1 and ex[1] - 1 <= y < ex[3] + 1:
                continue
            if any((x + dx, y + dy) in taken for dx in (-1, 0, 1) for dy in (-1, 0, 1)):
                continue
            # The three cells inward stay open, so the room never pinches.
            dx, dy = ((0, 1), (-1, 0), (0, -1), (1, 0))[hull.index(True)]
            if not all((x + dx * k, y + dy * k) in cellset for k in (1, 2, 3)):
                continue
            if rng.random() > 0.34:
                continue
            taken.add((x, y))
            piece = rng.choice(['KPCrateG', 'KPCrateM', 'KPCrateM', 'KPBarrel', 'KPBarrel'])
            # Pushed a little toward its wall, squared to it with a slight skew.
            ox, oy = -dx * 0.08, -dy * 0.08
            out.append((piece, x + 0.5 + ox, y + 0.5 + oy, rng.choice([0.0, 90.0]) + rng.uniform(-9, 9), [(x, y)]))
    return out


def blocked(floor):
    """Collision cells: the hull plus every solid prop's footprint, and the rooms' wall clutter."""
    solid = ~floor
    if 'AREAS' in globals():
        _, room = carve()
        for *_, cells in clutter(floor, room):
            for cx, cy in cells:
                solid[cy, cx] = True
    for model, x, y, rot, scale, rad in PROPS:
        if rad <= 0:
            continue
        for cy in range(int(y - rad), int(y + rad) + 1):
            for cx in range(int(x - rad), int(x + rad) + 1):
                nx, ny = max(cx, min(x, cx + 1)), max(cy, min(y, cy + 1))
                if math.hypot(nx - x, ny - y) < rad - 0.15:
                    solid[cy, cx] = True
    return solid


def wall_texture(kind, x, y, side):
    """Which panel a wall face shows: chosen per two-unit bay so panels continue."""
    if kind in ('hive',):
        return 'wall_hive'
    h = (int(x // 2) * 73856093 ^ int(y // 2) * 19349663 ^ side * 83492791) & 0xffff
    if kind == 'lab' and h % 5 == 0:
        return 'wall_hive'
    table = {'bay': ['wall_plain0', 'wall_plain0', 'wall_pipes2', 'wall_light5', 'wall_vent3', 'wall_alarm6'],
             'hall': ['wall_plain0', 'wall_pipes2', 'wall_vent3', 'wall_plain1', 'wall_light5', 'wall_pipes2'],
             'duct': ['wall_pipes2', 'wall_vent3', 'wall_pipes2', 'wall_plain1'],
             'mess': ['wall_plain1', 'wall_plain1', 'wall_screen4', 'wall_light5', 'wall_plain0'],
             'reactor': ['wall_pipes2', 'wall_vent3', 'wall_screen4', 'wall_light5', 'wall_alarm6', 'wall_pipes2'],
             'cargo': ['wall_plain1', 'wall_plain0', 'wall_vent3', 'wall_light5', 'wall_plain1'],
             'lab': ['wall_plain0', 'wall_screen4', 'wall_light5', 'wall_screen4', 'wall_plain0']}
    names = table.get(kind, table['hall'])
    return names[h % len(names)]


CHUNK = 24


def hull_meshes(floor, room):
    """{chunk name: ShipModel} for walls, caps and ceilings; plus the chunk origins."""
    from tools.shipkit import ShipModel, NO_SHADOW_CAST
    models = {}
    def model_for(x, y):
        cx, cy = int(x) // CHUNK, int(y) // CHUNK
        key = 'Hull%d_%d' % (cx, cy)
        if key not in models:
            models[key] = ShipModel(key, (cx * CHUNK, cy * CHUNK, 0.0))
        return models[key]
    # Distance (in cells) from each hull cell to the nearest floor, to cap only what is seen.
    near = np.zeros((H, W), bool)
    for dy in range(-3, 4):
        for dx in range(-3, 4):
            near |= np.roll(np.roll(floor, dy, 0), dx, 1)
    Z = WALL_H
    for y in range(H):
        for x in range(W):
            if in_void(x, y):
                continue
            if floor[y, x]:
                if kind_at(room, x, y) == 'lift':
                    continue
                # Ceiling over the deck, facing down: seen from a camera under it, culled from above.
                m = model_for(x, y)
                k = room[y, x]
                tex = 'ceiling' if (x * 7 + y * 13) % 5 == 0 and kind_at(room, x, y) not in ('hive',) else 'ceiling_dark'
                m.quad((tex, False, NO_SHADOW_CAST), (x, y, Z), (x, y + 1, Z), (x + 1, y + 1, Z), (x + 1, y, Z),
                       [((x % 4) / 4, (y % 4) / 4), ((x % 4) / 4, (y % 4 + 1) / 4), ((x % 4 + 1) / 4, (y % 4 + 1) / 4), ((x % 4 + 1) / 4, (y % 4) / 4)])
                continue
            if not near[y, x]:
                continue
            m = model_for(x, y)
            m.quad(('cap', False, 0), (x, y, Z), (x + 1, y, Z), (x + 1, y + 1, Z), (x, y + 1, Z),
                   [(0, 0), (0.5, 0), (0.5, 0.5), (0, 0.5)])
            # Faces toward each open neighbour (counter-clockwise seen from the open side).
            for side, (dx, dy) in enumerate([(0, -1), (1, 0), (0, 1), (-1, 0)]):
                nx, ny = x + dx, y + dy
                if not (0 <= nx < W and 0 <= ny < H) or not floor[ny, nx] or in_void(nx, ny):
                    continue
                kind = kind_at(room, nx, ny)
                if side == 0:   # face south at y
                    a, b = (x, y, 0), (x + 1, y, 0); along = x
                elif side == 1:  # face east at x+1
                    a, b = (x + 1, y, 0), (x + 1, y + 1, 0); along = y
                elif side == 2:  # face north at y+1
                    a, b = (x + 1, y + 1, 0), (x, y + 1, 0); along = -x - 1
                else:           # face west at x
                    a, b = (x, y + 1, 0), (x, y, 0); along = -y - 1
                tex = 'wall_window' if (x, y) in WINDOWS else wall_texture(kind, nx, ny, side)
                u0 = (along % 2) / 2.0
                c = (b[0], b[1], Z); d = (a[0], a[1], Z)
                m.quad((tex, False, 0), a, b, c, d, [(u0, 1.0), (u0 + 0.5, 1.0), (u0 + 0.5, 0.0), (u0, 0.0)])
    return models


# ---- the modular hull kit (build.py --kit) -----------------------------------
# The same walls, caps and ceiling as hull_meshes, but as a few reusable pieces
# the script places when a level loads (src/Kit.galaxy), so the map carries no
# per-level geometry. Walls come in two-unit bays: the full bay (F) and its
# viewer-left (E) and viewer-right (O) halves, authored facing south with the
# origin at the bay's midpoint on the face and turned by the script in 90-degree
# steps. Ceiling and cap tiles are 4x4, 2x2 and 1x1, origin at their south-west
# corner, uv'd from world position mod 4 so the three sizes join without seams.
KIT_WALLS = ['wall_plain0', 'wall_plain1', 'wall_pipes2', 'wall_vent3', 'wall_screen4', 'wall_light5', 'wall_alarm6', 'wall_hive',
             'wall_window', 'wall_concrete', 'wall_red']
# Room kinds as the script numbers them, and the wall panels each draws from (indexes into KIT_WALLS).
# A lift cell (the elevator platform and its bridges) gets no ceiling; the camera looks down the shaft.
# Past the lift: a colony's open ground under the sky and the catwalks and bridges over its drop (no ceiling over
# either, src/Kit.galaxy AS_KIND_SURFACE, AS_KIND_BRIDGE), a plant's industrial decks and its reactor core.
KIT_KINDS = ['bay', 'hall', 'duct', 'mess', 'reactor', 'cargo', 'lab', 'hive', 'lift', 'surface', 'bridge', 'plant', 'core']
KIT_PANELS = {'bay': [0, 0, 2, 5, 3, 6], 'hall': [0, 2, 3, 1, 5, 2], 'duct': [2, 3, 2, 1], 'mess': [1, 1, 4, 5, 0],
              'reactor': [2, 3, 4, 5, 6, 2], 'cargo': [1, 0, 3, 5, 1], 'lab': [0, 4, 5, 4, 0], 'hive': [7], 'lift': [0],
              'surface': [10, 10, 9, 10, 5, 10], 'bridge': [10, 2, 10, 10], 'plant': [2, 3, 2, 6, 5, 1], 'core': [2, 4, 5, 2, 6]}


def _lit(x, y):
    return (x * 7 + y * 13) % 5 == 0


def kit_pieces():
    """{piece name: ShipModel}: AS<name> catalog ids, Derelict/<name>.m3 meshes."""
    from tools.shipkit import ShipModel, NO_SHADOW_CAST, UNLIT, MULTIPLY
    out = {}
    Z = WALL_H
    for t, tex in enumerate(KIT_WALLS):
        for part, (x0, x1) in {'F': (-1, 1), 'E': (-1, 0), 'O': (0, 1)}.items():
            m = out.setdefault('KW%d%s' % (t, part), ShipModel('KW%d%s' % (t, part), (0, 0, 0)))
            u0, u1 = (x0 + 1) / 2.0, (x1 + 1) / 2.0
            m.quad((tex, False, 0), (x0, 0, 0), (x1, 0, 0), (x1, 0, Z), (x0, 0, Z), [(u0, 1.0), (u1, 1.0), (u1, 0.0), (u0, 0.0)])
            # A pale lip along the top edge, so every wall reads as a solid edge against the dark hull top.
            m.quad(('wall_trim', False, NO_SHADOW_CAST), (x0, 0, Z + 0.012), (x1, 0, Z + 0.012), (x1, LIP, Z + 0.012), (x0, LIP, Z + 0.012),
                   [(u0, 0.0), (u1, 0.0), (u1, 1.0), (u0, 1.0)])
            # The contact shadow at its foot (multiplied over the deck).
            m.quad(('decal_shadow', False, UNLIT, MULTIPLY), (x0, -SHADOW, 0.016), (x1, -SHADOW, 0.016), (x1, 0, 0.016), (x0, 0, 0.016),
                   [(u0, 1.0), (u1, 1.0), (u1, 0.0), (u0, 0.0)])
    floor_pieces(out)
    stair_pieces(out)
    decal_pieces(out)
    from tools import propart, pitart
    propart.pieces(out)
    # The drop beyond an outdoor deck's railing: its floor tiles and haze (KO*), edge skirts, towers, trusses,
    # pipes and lamps, the buildings' walls down to it; and the stairs' handrails.
    pitart.pieces(out)
    for size in (4, 2, 1):
        # Lit panels sit at fixed spots of the 4x4 pattern, so a tile is only placed where its corner's
        # position mod 4 matches what it was authored for: 4x4 at 0, 2x2 at 0 or 2, 1x1 anywhere.
        for ox in range(0, 4, size):
            for oy in range(0, 4, size):
                for hive in (False, True):
                    name = 'K%s%d_%d%d' % ('D' if hive else 'C', size, ox, oy)
                    m = out[name] = ShipModel(name, (0, 0, 0))
                    for x in range(size):
                        for y in range(size):
                            gx, gy = ox + x, oy + y
                            tex = 'ceiling' if _lit(gx, gy) and not hive else 'ceiling_dark'
                            m.quad((tex, False, NO_SHADOW_CAST), (x, y, Z), (x, y + 1, Z), (x + 1, y + 1, Z), (x + 1, y, Z),
                                   [(gx / 4, gy / 4), (gx / 4, (gy + 1) / 4), ((gx + 1) / 4, (gy + 1) / 4), ((gx + 1) / 4, gy / 4)])
        # The hull's top: dark plating indoors (KK), a snowed-over roof outdoors (KR, SNOW_ROOFS).
        for cap, tex in (('KK', 'cap'), ('KR', 'cap_snow')):
            name = '%s%d' % (cap, size)
            m = out[name] = ShipModel(name, (0, 0, 0))
            m.quad((tex, False, 0), (0, 0, Z), (size, 0, Z), (size, size, Z), (0, size, Z),
                   [(0, 0), (0.5 * size, 0), (0.5 * size, 0.5 * size), (0, 0.5 * size)])
        # Machinery tops over the blocks standing in rooms, at the wall's height: 4x4-patterned like the ceiling.
        for ox in range(0, 4, size):
            for oy in range(0, 4, size):
                name = 'KM%d_%d%d' % (size, ox, oy)
                m = out[name] = ShipModel(name, (0, 0, 0))
                m.quad(('machine_top', False, 0), (0, 0, Z), (size, 0, Z), (size, size, Z), (0, size, Z),
                       [(ox / 4, 1 - oy / 4), ((ox + size) / 4, 1 - oy / 4), ((ox + size) / 4, 1 - (oy + size) / 4), (ox / 4, 1 - (oy + size) / 4)])
    # A one-unit run of railing along an outdoor deck's edge, authored facing south like the walls
    # (origin at the edge's midpoint): yellow posts, two rails and a kick plate, as AS's dock catwalks have.
    from tools.elevator import _box
    m = out['KRail'] = ShipModel('KRail', (0, 0, 0))
    rail = ('rail', False, 0)
    _box(m, rail, -0.5, 0.0, 0.0, -0.44, 0.06, 1.05)
    for z in (0.55, 1.0):
        _box(m, rail, -0.5, 0.0, z - 0.05, 0.5, 0.05, z)
    _box(m, ('wall_trim', False, 0), -0.5, 0.0, 0.0, 0.5, 0.03, 0.14)
    # The pink neon edge strip AS's dock has along its drops, glowing on the deck at the railing's foot.
    from tools.shipkit import UNLIT, ADD
    m.quad(('run_pink', False, UNLIT, ADD), (-0.5, -0.13, 0.022), (0.5, -0.13, 0.022), (0.5, -0.01, 0.022), (-0.5, -0.01, 0.022),
           [(0, 1), (1, 1), (1, 0), (0, 0)])
    return out


LIP = 0.16                  # wall-top lip depth into the hull
SHADOW = 0.55               # contact shadow depth out over the deck
FLOOR_Z = 0.004             # the floor plating sits just over the terrain
FLOOR_PATTERNS = 4          # 4x4 floor pieces per room kind


def _floor_pick(kind, pattern, bx, by):
    """Which of the kind's floors (tools/deckart.py KIND_FLOORS) covers 2x2 block (bx, by) of a 4x4 pattern."""
    from tools.deckart import KIND_FLOORS
    main, second, accent = KIND_FLOORS[kind]
    if pattern == 3 and (bx, by) == (1, 1):
        return accent
    h = (pattern * 7 + bx * 3 + by * 5 + pattern * bx * 11) % 9
    # Halls mix their grating and concrete about evenly, as AS's landing bay walkways do; rooms keep one plating.
    return second if h in ((1, 2, 5, 6) if kind == 'hall' else (2, 6)) else main


def floor_pieces(out):
    """KF<k><p> (4x4, pattern p), KF<k>T (2x2), KF<k>S<px><py> (1x1 at x%2, y%2): floor plating per room kind k.
    Floor textures repeat every two units, so uv is world position / 2 and the pieces join without seams."""
    from tools.shipkit import ShipModel
    from tools.deckart import KIND_FLOORS
    z = FLOOR_Z

    def cell(m, tex, x, y, gx, gy):
        m.quad((tex, False, 0), (x, y, z), (x + 1, y, z), (x + 1, y + 1, z), (x, y + 1, z),
               [(gx / 2, 1 - gy / 2), ((gx + 1) / 2, 1 - gy / 2), ((gx + 1) / 2, 1 - (gy + 1) / 2), (gx / 2, 1 - (gy + 1) / 2)])
    for kind in KIND_FLOORS:
        k = KIT_KINDS.index(kind)
        for p in range(FLOOR_PATTERNS):
            name = 'KF%d%d' % (k, p)
            m = out[name] = ShipModel(name, (0, 0, 0))
            for x in range(4):
                for y in range(4):
                    cell(m, _floor_pick(kind, p, x // 2, y // 2), x, y, x, y)
        # 2x2 and single-cell pieces in the main plating (T, S) and the second (U, R): src/Kit.galaxy AS_KitFloorTile
        # mixes them by position, so narrow halls get the same mix as the big 4x4 pieces.
        for t2, s1, tex in (('T', 'S', KIND_FLOORS[kind][0]), ('U', 'R', KIND_FLOORS[kind][1])):
            name = 'KF%d%s' % (k, t2)
            m = out[name] = ShipModel(name, (0, 0, 0))
            for x in range(2):
                for y in range(2):
                    cell(m, tex, x, y, x, y)
            for px in range(2):
                for py in range(2):
                    name = 'KF%d%s%d%d' % (k, s1, px, py)
                    m = out[name] = ShipModel(name, (0, 0, 0))
                    cell(m, tex, 0, 0, px, py)


STAIR_STEPS = 5             # risers in a one-cell flight, a fifth of the rise each; the top tread is the upper floor


def stair_pieces(out):
    """The slope cells' pieces (tools/heights.py stairs), one cell with the origin at its centre, rising one unit:
    the script turns them and scales them up by the cell's rise, so the flight follows the terrain under it.
    Each tread stands on or above the terrain's slope everywhere (a tread at the height of its back edge), so
    the bare slope never shows between them, whichever diagonal SC2 splits the cell on.
    KStair is a flight rising north, as AS's stair props are (lb-04): yellow-nosed steel treads, dark risers and
    yellow stringers. KRamp1 (north-east corner up) and KRamp3 (south-west corner down) are the corner flights
    where two meet, their treads turning the corner, so a flight runs on round it without a seam."""
    from tools.shipkit import ShipModel
    n = STAIR_STEPS
    tread, riser, side = ('stair_tread', False, 0), ('stair_riser', False, 0), ('stair_stringer', False, 0)
    c = [-0.5 + k / n for k in range(n + 1)]
    m = out['KStair'] = ShipModel('KStair', (0, 0, 0))
    for i in range(n):
        y0, y1, z = c[i], c[i + 1], (i + 1) / n
        m.quad(tread, (-0.5, y0, z), (0.5, y0, z), (0.5, y1, z), (-0.5, y1, z), [(0, 0), (1, 0), (1, 1), (0, 1)])
        m.quad(riser, (-0.5, y0, z - 1 / n), (0.5, y0, z - 1 / n), (0.5, y0, z), (-0.5, y0, z), [(0, 1), (1, 1), (1, 0), (0, 0)])
        m.quad(side, (0.5, y0, 0), (0.5, y1, 0), (0.5, y1, z), (0.5, y0, z), [(0, 1), (1 / n, 1), (1 / n, 1 - z), (0, 1 - z)])
        m.quad(side, (-0.5, y1, 0), (-0.5, y0, 0), (-0.5, y0, z), (-0.5, y1, z), [(0, 1), (1 / n, 1), (1 / n, 1 - z), (0, 1 - z)])
    # KRamp1: the north-east corner up. The terrain lies at or under min(x, y) + 1/2; tread k is the L between
    # c[k] and c[k+1] round that corner, its risers facing west and south.
    m = out['KRamp1'] = ShipModel('KRamp1', (0, 0, 0))
    for k in range(n):
        a0, a1, z = c[k], c[k + 1], (k + 1) / n
        m.quad(tread, (a0, a0, z), (0.5, a0, z), (0.5, a1, z), (a0, a1, z), [(0, 0), (1, 0), (1, 1), (0, 1)])
        m.quad(tread, (a1, a1, z), (a1, 0.5, z), (a0, 0.5, z), (a0, a1, z), [(0, 1), (1, 1), (1, 0), (0, 0)])
        m.quad(riser, (a0, a0, z - 1 / n), (0.5, a0, z - 1 / n), (0.5, a0, z), (a0, a0, z), [(0, 1), (1, 1), (1, 0), (0, 0)])
        m.quad(riser, (a0, 0.5, z - 1 / n), (a0, a0, z - 1 / n), (a0, a0, z), (a0, 0.5, z), [(0, 1), (1, 1), (1, 0), (0, 0)])
    # KRamp3: the south-west corner down. The terrain lies at or under min(1, x + y + 1); tread k is the band
    # between the diagonals x + y + 1 = k/n and (k+1)/n, its riser facing south-west; the rest is the upper floor.
    m = out['KRamp3'] = ShipModel('KRamp3', (0, 0, 0))

    def band(t0, t1):
        """The cell square clipped to t0 <= x + y + 1 <= t1, counter-clockwise from above."""
        pts = [(-0.5, -0.5), (0.5, -0.5), (0.5, 0.5), (-0.5, 0.5)]
        for t, keep in ((t0, 1), (t1, -1)):
            res = []
            for i in range(len(pts)):
                p0, p1 = pts[i], pts[(i + 1) % len(pts)]
                f0, f1 = (p0[0] + p0[1] + 1 - t) * keep, (p1[0] + p1[1] + 1 - t) * keep
                if f0 >= 0:
                    res.append(p0)
                if (f0 >= 0) != (f1 >= 0):
                    w = f0 / (f0 - f1)
                    res.append((p0[0] + w * (p1[0] - p0[0]), p0[1] + w * (p1[1] - p0[1])))
            pts = res
        return pts
    for k in range(n + 1):
        t0, t1 = k / n, ((k + 1) / n if k < n else 2.0)
        z = min(1.0, (k + 1) / n)
        pts = band(t0, t1)
        if len(pts) >= 3:
            m.poly(tread if k < n else ('floor_plate2', False, 0), [(x, y, z) for x, y in pts],
                   [((x - y + 1) / 2, (x + y + 1 - t0) * n) for x, y in pts])
        if k < n:
            edge = [q for q in band(t0 - 1e-6, t0 + 1e-6)]
            if len(edge) >= 2:
                (xa, ya), (xb, yb) = min(edge, key=lambda q: q[0] - q[1]), max(edge, key=lambda q: q[0] - q[1])
                if abs(xa - xb) + abs(ya - yb) > 1e-6:
                    m.quad(riser, (xa, ya, z - 1 / n), (xb, yb, z - 1 / n), (xb, yb, z), (xa, ya, z), [(0, 1), (1, 1), (1, 0), (0, 0)])


# Decal pieces, origin at their centre, laid by the script (AS_KitDecal) from each level's decal_spots.
DECAL_PIECES = {
    'KDHaz': ('decal_hazard', 1.0, 0.36, False),      # name: texture, length, width, multiplied
    'KDWarn': ('decal_warning', 1.0, 1.0, False),
    'KDWatch': ('decal_watchstep', 2.4, 0.45, False),
    'KDGrime1': ('decal_grime1', 2.4, 2.4, True),
    'KDGrime2': ('decal_grime2', 1.8, 1.8, True),
    'KDScorch': ('decal_scorch', 2.0, 2.0, True),
    'KDGoo': ('decal_goo', 2.2, 2.2, True),
    'KDCable1': ('decal_cable1', 3.0, 3.0, True),
    'KDCable2': ('decal_cable2', 3.0, 3.0, True),
    'KDFan': ('decal_fan', 3.6, 3.6, True),
    'KDCookie1': ('decal_cookie1', 5.0, 5.0, True),
    'KDCookie2': ('decal_cookie2', 5.0, 5.0, True),
    'KDCookie3': ('decal_cookie3', 4.4, 4.4, True),
    'KDBlood1': ('decal_blood1', 1.8, 1.8, True),
    'KDBlood2': ('decal_blood2', 1.6, 1.6, True),
}


def decal_pieces(out):
    from tools.shipkit import ShipModel, NO_SHADOW_CAST, UNLIT, MULTIPLY, ADD
    m = out['KDRun'] = ShipModel('KDRun', (0, 0, 0))
    m.quad(('run_light', False, UNLIT, ADD), (-0.42, -0.09, 0.024), (0.42, -0.09, 0.024), (0.42, 0.09, 0.024), (-0.42, 0.09, 0.024),
           [(0, 1), (1, 1), (1, 0), (0, 0)])
    for name, (tex, ln, wd, mul) in DECAL_PIECES.items():
        m = out[name] = ShipModel(name, (0, 0, 0))
        z = 0.02 if mul else 0.008
        key = (tex, False, UNLIT, MULTIPLY) if mul else (tex, False, NO_SHADOW_CAST)
        a, b = ln / 2, wd / 2
        m.quad(key, (-a, -b, z), (a, -b, z), (a, b, z), (-a, b, z), [(0, 1), (1, 1), (1, 0), (0, 0)])
    # A two-by-two section of grating over the lit under-deck, laid over the plating (GRATES walkways).
    m = out['KDGrate'] = ShipModel('KDGrate', (0, 0, 0))
    m.quad(('floor_grate', False, NO_SHADOW_CAST), (-1, -1, 0.012), (1, -1, 0.012), (1, 1, 0.012), (-1, 1, 0.012),
           [(0, 1), (1, 1), (1, 0), (0, 0)])
    # Loose paper scattered over the deck, a few sheets to a piece, each turned its own way.
    import random as _r
    for k in (1, 2, 3):
        m = out['KDPapers%d' % k] = ShipModel('KDPapers%d' % k, (0, 0, 0))
        rr = _r.Random(k * 31)
        for j in range(rr.randint(4, 7)):
            cx, cy = rr.uniform(-0.6, 0.6), rr.uniform(-0.6, 0.6); a = rr.uniform(0, 2 * math.pi); z = 0.006 + 0.0015 * j
            ca, sa = math.cos(a), math.sin(a)
            pts = [(cx + ca * u - sa * v, cy + sa * u + ca * v, z) for u, v in ((-0.09, -0.12), (0.09, -0.12), (0.09, 0.12), (-0.09, 0.12))]
            m.quad(('decal_paper', False, NO_SHADOW_CAST), pts[0], pts[1], pts[2], pts[3], [(0, 1), (1, 1), (1, 0), (0, 0)])
    # Snow drifts on the outdoor deck, added over it.
    for k in (1, 2):
        m = out['KDSnow%d' % k] = ShipModel('KDSnow%d' % k, (0, 0, 0))
        m.quad(('decal_snow%d' % k, False, UNLIT, ADD), (-1.3, -1.3, 0.022), (1.3, -1.3, 0.022), (1.3, 1.3, 0.022), (-1.3, 1.3, 0.022),
               [(0, 1), (1, 1), (1, 0), (0, 0)])


def paint_names():
    """Stencilled names for the level's big rooms: slug -> text, after Alien Swarm's LANDING BAY 7 floor paint."""
    out = {}
    for name, (x0, y0, x1, y1), kind in AREAS:
        if kind in ('bay', 'cargo', 'mess', 'reactor', 'lab') and x1 - x0 >= 12:
            n = (sum(map(ord, name)) * 7) % 19 + 1
            out[name.replace(' ', '').upper()] = '%s %02d' % (name.upper(), n)
    return out


def sign_names():
    """Wall signs for the level's passages: slug -> text."""
    return {name.replace(' ', '').upper(): name.upper() for name, rect, kind in AREAS if kind in ('hall', 'duct') and not name.endswith('Door')}


def sign_pieces(slugs):
    """KS<slug>: a sign plate 1.6 x 0.4 standing just proud of a wall that faces -Y, its middle 1.7 up."""
    from tools.shipkit import ShipModel
    out = {}
    for slug in slugs:
        m = out['KS' + slug] = ShipModel('KS' + slug, (0, 0, 0))
        m.quad(('sign_' + slug.lower(), False, 0), (-0.8, -0.035, 1.5), (0.8, -0.035, 1.5), (0.8, -0.035, 1.9), (-0.8, -0.035, 1.9),
               [(0, 1), (1, 1), (1, 0), (0, 0)])
    return out


def shaft_pieces():
    """KVWarm / KVCold / KVOrange: a lamp's light shaft, a ring of eight added quads from a narrow top at the lamp to a wide
    foot on the deck (the lamps hang 2.1 up, src/Fx.galaxy AS_Lamp)."""
    import math
    from tools.shipkit import ShipModel, UNLIT, ADD
    out = {}
    for name, tex in (('KVWarm', 'shaft_warm'), ('KVCold', 'shaft_cold'), ('KVOrange', 'shaft_orange')):
        m = out[name] = ShipModel(name, (0, 0, 0))
        top, foot, z = 0.25, 1.5, 2.15
        for k in range(8):
            t0, t1 = 2 * math.pi * k / 8, 2 * math.pi * (k + 1) / 8
            m.quad((tex, True, UNLIT, ADD), (foot * math.cos(t0), foot * math.sin(t0), 0.03), (foot * math.cos(t1), foot * math.sin(t1), 0.03),
                   (top * math.cos(t1), top * math.sin(t1), z), (top * math.cos(t0), top * math.sin(t0), z), [(0, 1), (1, 1), (1, 0), (0, 0)])
    return out


def pit_lamps(floor, room):
    """The lights down in the pit beyond an outdoor deck (tools/pitart.py lamps): (x, y, kind, flicker)."""
    from tools import pitart
    return pitart.lamps(deck_rows(floor, room))


def corridor_lamps(floor, room):
    """Steady lamps added along the corridors wherever no lamp hangs within five units, one every six, as Alien
    Swarm keeps its passages lit between the rooms' pools."""
    lamps = [(x, y) for x, y, k, f in LIGHTS]
    out = []
    for name, (x0, y0, x1, y1), kind in AREAS:
        if kind not in ('hall', 'duct'):
            continue
        cx, cy = (x0 + x1) / 2.0, (y0 + y1) / 2.0
        steps = ([(x + 0.5, cy) for x in range(x0 + 3, x1 - 2, 6)] if x1 - x0 >= y1 - y0
                 else [(cx, y + 0.5) for y in range(y0 + 3, y1 - 2, 6)])
        for x, y in steps:
            if not floor[int(y), int(x)] or in_void(int(x), int(y)):
                continue
            if all(math.hypot(x - lx, y - ly) > 5.0 for lx, ly in lamps):
                out.append((x, y, 'cold' if kind == 'duct' else 'white', 0))
                lamps.append((x, y))
    return out


def paint_spots():
    """(piece, x, y, facing): each big room's name inside its south edge, a pad under the dropship."""
    spots = []
    for name, (x0, y0, x1, y1), kind in AREAS:
        if name.replace(' ', '').upper() in paint_names():
            spots.append(('KN' + name.replace(' ', '').upper(), (x0 + x1) / 2.0, y0 + 2.9, 0.0))
    for model, x, y, rot, scale, rad in PROPS:
        if model == 'Hercules':
            spots.append(('KNPad', x, y, 0.0))
    # A haze of light under each steady white, yellow or cold lamp.
    for x, y, kind, flick in LIGHTS:
        if flick == 0 and kind in ('white', 'whitebig', 'yellow', 'cold'):
            spots.append(('KVCold' if kind == 'cold' else 'KVWarm', x, y, 0.0))
    # A painted arrow down the middle of each corridor, along its length.
    for name, (x0, y0, x1, y1), kind in AREAS:
        if kind == 'hall' and max(x1 - x0, y1 - y0) >= 8:
            cx, cy = (x0 + x1) / 2.0, (y0 + y1) / 2.0
            spots.append(('KNArrow', cx, cy, 270.0 if x1 - x0 >= y1 - y0 else 0.0))
    # Yellow guide lines round the bays and cargo rooms, a unit and a half in from the walls.
    floor, room = carve()
    solid = blocked(floor)
    for name, (x0, y0, x1, y1), kind in AREAS:
        if kind not in ('bay', 'cargo') or x1 - x0 < 10 or y1 - y0 < 10:
            continue
        lx0, ly0, lx1, ly1 = x0 + 1.5, y0 + 1.5, x1 - 1.5, y1 - 1.5
        for cx in np.arange(lx0 + 1, lx1 - 0.5, 2.0):
            for cy in (ly0, ly1):
                if not solid[int(cy), int(cx)] and not solid[int(cy), min(W - 1, int(cx + 0.9))] and not solid[int(cy), int(cx - 0.9)]:
                    spots.append(('KNLine', float(cx), float(cy), 0.0))
        for cy in np.arange(ly0 + 1, ly1 - 0.5, 2.0):
            for cx in (lx0, lx1):
                if not solid[int(cy), int(cx)] and not solid[min(H - 1, int(cy + 0.9)), int(cx)] and not solid[int(cy - 0.9), int(cx)]:
                    spots.append(('KNLine', float(cx), float(cy), 90.0))
    return spots


def paint_pieces(slugs):
    """KN<slug> (a 6 x 1.5 name) and KNPad (a 4 x 4 landing ring): paint just over the plating, a multiplied
    layer that tints the deck and an added one that brightens it (tools/deckart.py paint_textures)."""
    from tools.shipkit import ShipModel, UNLIT, MULTIPLY, ADD
    out = {}
    for slug, tex, a, b in [(s_, 'paint_' + s_.lower(), 3.0, 0.75) for s_ in slugs] + [('Pad', 'paint_pad', 2.0, 2.0), ('Line', 'paint_line', 1.0, 0.12), ('Arrow', 'paint_arrow', 0.6, 0.6)]:
        m = out['KN' + slug] = ShipModel('KN' + slug, (0, 0, 0))
        for layer, blend, z in (('_m', MULTIPLY, 0.012), ('_a', ADD, 0.014)):
            m.quad((tex + layer, False, UNLIT, blend), (-a, -b, z), (a, -b, z), (a, b, z), (-a, b, z), [(0, 1), (1, 1), (1, 0), (0, 0)])
    return out


def decal_spots(floor, room, solid, seed=7):
    """(piece, x, y, facing) for every decal of the level in use: hazard paint across each doorway
    (where a corridor meets a room), a warning sign beside a few, and grime, scorches and alien goo."""
    import random
    rng = random.Random(seed * 7919 + W * 31 + H)
    spots = []
    corridor = ('hall', 'duct')

    def kind(x, y):
        return kind_at(room, x, y) if 0 <= x < W and 0 <= y < H and floor[y, x] and not in_void(x, y) else None

    def door(a, b):
        return a and b and a != b and 'lift' not in (a, b) and 'hive' not in (a, b) and ((a in corridor) != (b in corridor))
    for y in range(1, H):
        for x in range(W):
            a, b = kind(x, y - 1), kind(x, y)
            if door(a, b):
                spots.append(('KDHaz', x + 0.5, y + 0.18 if b in corridor else y - 0.18, 0.0))
    for x in range(1, W):
        for y in range(H):
            a, b = kind(x - 1, y), kind(x, y)
            if door(a, b):
                spots.append(('KDHaz', x + 0.18 if b in corridor else x - 0.18, y + 0.5, 90.0))
    # A bulkhead frame round each doorway: runs of threshold cells along a row or a column, with hull at both ends
    # on the corridor's side.
    def frame(a, b):
        return a and b and a != b and 'lift' not in (a, b) and ((a in corridor) != (b in corridor))
    for y in range(1, H):
        run = []
        for x in range(W + 1):
            if x < W and frame(kind(x, y - 1), kind(x, y)):
                run.append(x); continue
            cy = y if run and kind(run[0], y) in corridor else y - 1
            if run and len(run) <= 12 and all(not (0 <= xx < W) or not floor[cy, xx] for xx in (run[0] - 1, run[-1] + 1)):
                spots.append(('KPDoor%d' % len(run), (run[0] + run[-1] + 1) / 2.0, float(y), 0.0))
                # The passage beyond named on the room's wall beside the door, where it faces the camera.
                if cy == y and 0 <= y - 1 and AREAS[room[y, run[0]]][2] in corridor and not AREAS[room[y, run[0]]][0].endswith('Door'):
                    sx = run[-1] + 2.2
                    if sx + 1 < W and all(0 <= sx + dx < W and not floor[y, int(sx + dx)] and floor[y - 1, int(sx + dx)] for dx in (-0.8, 0.0, 0.79)):
                        spots.append(('KS' + AREAS[room[y, run[0]]][0].replace(' ', '').upper(), sx, float(y), 0.0))
            run = []
    for x in range(1, W):
        run = []
        for y in range(H + 1):
            if y < H and frame(kind(x - 1, y), kind(x, y)):
                run.append(y); continue
            cx = x if run and kind(x, run[0]) in corridor else x - 1
            if run and len(run) <= 12 and all(not (0 <= yy < H) or not floor[yy, cx] for yy in (run[0] - 1, run[-1] + 1)):
                spots.append(('KPDoor%d' % len(run), float(x), (run[0] + run[-1] + 1) / 2.0, 90.0))
            run = []
    # Pipe runs high along the corridors' walls that face the camera (south), two units a piece.
    for y in range(1, H):
        for x in range(1, W - 1, 2):
            if all(kind(x + i, y - 1) in corridor and not floor[y, x + i] and not in_void(x + i, y) for i in (0, 1)):
                spots.append(('KPPipes', x + 1.0, float(y), 0.0))
    # Dashed running lights along the corridors' walls, every other cell.
    for y in range(1, H - 1):
        for x in range(1, W - 1):
            if kind(x, y) != 'hall':
                continue
            if x % 2 == 0 and not floor[y + 1, x] and not in_void(x, y + 1):
                spots.append(('KDRun', x + 0.5, y + 0.8, 0.0))
            if x % 2 == 0 and not floor[y - 1, x] and not in_void(x, y - 1):
                spots.append(('KDRun', x + 0.5, y + 0.2, 0.0))
            if y % 2 == 0 and not floor[y, x + 1] and not in_void(x + 1, y):
                spots.append(('KDRun', x + 0.8, y + 0.5, 90.0))
            if y % 2 == 0 and not floor[y, x - 1] and not in_void(x - 1, y):
                spots.append(('KDRun', x + 0.2, y + 0.5, 90.0))
    # WATCH YOUR STEP at both ends of every stair and ramp, across its width, as AS paints them.
    for name, (x0, y0, x1, y1), k in AREAS:
        if ('Stair' not in name and 'Ramp' not in name) or name.endswith('Door'):
            continue
        if y1 - y0 >= x1 - x0:
            for yy in (y0 + 0.35, y1 - 0.35):
                spots.append(('KDWatch', (x0 + x1) / 2.0, yy, 0.0))
        else:
            for xx in (x0 + 0.35, x1 - 0.35):
                spots.append(('KDWatch', xx, (y0 + y1) / 2.0, 90.0))
    # Grime everywhere, goo near the hives and labs, scorches where the fighting was.
    open_cells = [(x, y) for y in range(H) for x in range(W) if kind(x, y) and kind(x, y) != 'lift' and not solid[y, x]]
    for x, y in rng.sample(open_cells, len(open_cells) // 36):
        k = kind(x, y)
        if k in ('hive', 'lab') and rng.random() < 0.6:
            piece = 'KDGoo'
        elif rng.random() < 0.18:
            piece = 'KDScorch'
        else:
            piece = rng.choice(['KDGrime1', 'KDGrime2'])
        spots.append((piece, x + rng.random(), y + rng.random(), rng.uniform(0, 360)))
    # Struts standing proud of the long walls every four units, as Alien Swarm's bulkheads have, on the
    # faces the camera sees (south, east and west); not near a corner, a door or the lift.
    def wall(x, y):
        return not (0 <= x < W and 0 <= y < H) or (not floor[y, x] and not in_void(x, y))

    def deck(x, y):
        return kind(x, y) is not None and kind(x, y) != 'lift'
    for y in range(1, H):
        for x in range(4, W - 2, 4):
            if all(wall(x + i, y) and deck(x + i, y - 1) for i in (-2, -1, 0, 1)):
                spots.append(('KPCol', float(x), float(y), 0.0))
    for x in range(W - 1):
        for y in range(4, H - 2, 4):
            if all(wall(x, y + i) and deck(x + 1, y + i) for i in (-2, -1, 0, 1)):
                spots.append(('KPCol', float(x + 1), float(y), 90.0))
            if x > 0 and all(wall(x, y + i) and deck(x - 1, y + i) for i in (-2, -1, 0, 1)):
                spots.append(('KPCol', float(x), float(y), 270.0))
    # Lockers along the crew rooms' walls and consoles in the labs, offices and the reactor, between the struts on
    # the walls the camera faces.
    for y in range(1, H):
        for x in range(2, W - 2, 4):
            k = kind(x, y - 1)
            if k not in ('mess', 'lab', 'reactor', 'bay', 'cargo') or not all(wall(x + i, y) and deck(x + i, y - 1) for i in (-1, 0)):
                continue
            if any(solid[y - 1 - dy, x + dx] for dx in (-1, 0) for dy in (0, 1) if y - 1 - dy >= 0):
                continue
            if k == 'mess' and rng.random() < 0.7:
                spots.append(('KPLockers', float(x), float(y), 0.0))
            elif k in ('lab', 'reactor') and rng.random() < 0.5 or k in ('bay', 'cargo') and rng.random() < 0.2:
                spots.append(('KPConsole', float(x), float(y), 0.0))
    # Barrels and crate stacks tucked into the rooms' corners (cells with hull on two sides).
    for x, y in open_cells:
        if kind(x, y) not in ('bay', 'cargo', 'reactor', 'mess', 'lab'):
            continue
        n = [solid[y + dy, x + dx] if 0 <= x + dx < W and 0 <= y + dy < H else True for dx, dy in ((0, -1), (1, 0), (0, 1), (-1, 0))]
        if sum(n) == 2 and ((n[0] or n[2]) and (n[1] or n[3])) and rng.random() < 0.55:
            ox = 0.12 if n[3] else -0.12
            oy = 0.12 if n[0] else -0.12
            piece = rng.choice(['KPBarrels', 'KPBarrels', 'KPCrateStack', 'KPBarrel', 'KPCrateM'])
            spots.append((piece, x + 0.5 + ox, y + 0.5 + oy, rng.choice([0.0, 90.0, 180.0, 270.0]) + rng.uniform(-12, 12)))
    # The haze lit under each steady lamp (AS's asw_vol_light), in the lamp's colour.
    for lx, ly, lk, fl in LIGHTS:
        if fl != 0 or not kind(int(lx), int(ly)):
            continue
        shaft = {'white': 'KVWarm', 'whitebig': 'KVWarm', 'yellow': 'KVWarm', 'yellowbig': 'KVWarm', 'cold': 'KVCold', 'coldbig': 'KVCold',
                 'orange': 'KVOrange', 'orangebig': 'KVOrange'}.get(lk)
        if shaft:
            spots.append((shaft, lx, ly, 0.0))
    # An overhead girder across most big rooms, wall top to wall top, between the camera and the deck as AS's are.
    for name, (x0, y0, x1, y1), k in AREAS:
        if k not in ('bay', 'cargo', 'reactor') or x1 - x0 < 8 or y1 - y0 < 8 or rng.random() < 0.25:
            continue
        if (x1 - x0) >= (y1 - y0) or rng.random() < 0.3:
            by = rng.randint(y0 + 2, y1 - 3) + 0.5
            for bx in range(x0, x1, 2):
                spots.append(('KPBeam', bx + 1.0, by, 0.0))
        else:
            bx = rng.randint(x0 + 2, x1 - 3) + 0.5
            for by in range(y0, y1, 2):
                spots.append(('KPBeam', bx, by + 1.0, 90.0))
    # A turning fan's shadow under a steady lamp in a few of the bigger rooms (the script turns it).
    for lx, ly, lk, fl in LIGHTS:
        if fl == 0 and kind(int(lx), int(ly)) in ('bay', 'cargo', 'reactor') and lk not in ('red', 'redbig') and rng.random() < 0.3:
            spots.append(('KDFan', lx, ly, 0.0))
    # Hard shadows under the steady lamps of the rooms (AS's girder bands and grating cookies): about half of them.
    for lx, ly, lk, fl in LIGHTS:
        k = kind(int(lx), int(ly))
        if k in ('bay', 'cargo', 'reactor', 'mess', 'lab', 'hall') and fl == 0 and lk not in ('red', 'redbig') and rng.random() < 0.55:
            spots.append((rng.choice(['KDCookie1', 'KDCookie2', 'KDCookie3']), lx + rng.uniform(-0.6, 0.6), ly + rng.uniform(-0.6, 0.6),
                          rng.uniform(0, 360)))
    # Where the crew fell: a few blood pools in the rooms and passages, as AS's landing bay has, often with the
    # papers they dropped scattered round; and more loose paper through the offices and labs.
    for x, y in rng.sample(open_cells, len(open_cells) // 110):
        if kind(x, y) in ('bay', 'cargo', 'mess', 'lab', 'hall', 'reactor'):
            spots.append((rng.choice(['KDBlood1', 'KDBlood2']), x + rng.random(), y + rng.random(), rng.uniform(0, 360)))
            if rng.random() < 0.6:
                spots.append((rng.choice(['KDPapers1', 'KDPapers2', 'KDPapers3']), x + rng.uniform(-0.8, 1.8), y + rng.uniform(-0.8, 1.8), rng.uniform(0, 360)))
    for x, y in rng.sample(open_cells, len(open_cells) // 70):
        if kind(x, y) in ('mess', 'lab'):
            spots.append((rng.choice(['KDPapers1', 'KDPapers2', 'KDPapers3']), x + rng.random(), y + rng.random(), rng.uniform(0, 360)))
    # Loose cables across the deck in the working rooms.
    for x, y in rng.sample(open_cells, len(open_cells) // 240):
        if kind(x, y) in ('bay', 'cargo', 'reactor', 'lab', 'mess', 'hall'):
            spots.append((rng.choice(['KDCable1', 'KDCable2']), x + 0.5, y + 0.5, rng.uniform(0, 360)))
    # A warning sign in a few of the big rooms, clear of the walls.
    rooms = [(x, y) for x, y in open_cells if kind(x, y) in ('bay', 'cargo', 'reactor') and not any(
        solid[y + dy, x + dx] for dx in (-2, 0, 2) for dy in (-2, 0, 2) if 0 <= x + dx < W and 0 <= y + dy < H)]
    signed = set()
    for x, y in rng.sample(rooms, len(rooms)):
        if room[y, x] in signed or len(signed) >= 3:
            continue
        signed.add(room[y, x])
        spots.append(('KDWarn', x + 0.5, y + 0.5, rng.choice([0.0, 90.0, 180.0, 270.0])))
    spots += [(piece, x, y, rot) for piece, x, y, rot, _ in clutter(floor, room)]
    # Grating walkways over the lit under-deck (GRATES), as AS's cargo-lift level opens on one.
    for x0, y0, x1, y1 in globals().get('GRATES') or []:
        for gy in range(y0, y1, 2):
            for gx in range(x0, x1, 2):
                spots.append(('KDGrate', gx + 1.0, gy + 1.0, 0.0))
    # Snow over the outdoor deck, banked up against its edges, rails and walls.
    out_rect = globals().get('OUTDOORS')
    if out_rect:
        for y in range(out_rect[1], out_rect[3]):
            for x in range(out_rect[0], out_rect[2]):
                if not kind(x, y):
                    continue
                edge = any(not (0 <= x + dx < W and 0 <= y + dy < H) or not floor[y + dy, x + dx] for dx, dy in ((0, 1), (1, 0), (0, -1), (-1, 0)))
                if rng.random() < (0.4 if edge else 0.1):
                    spots.append(('KDSnow%d' % rng.choice([1, 2]), x + rng.random(), y + rng.random(), rng.uniform(0, 360)))
    # The pit beyond an outdoor deck's railing: towers, trusses, pipes and lamps down in the haze.
    from tools import pitart
    return spots + paint_spots() + pitart.spots(deck_rows(floor, room))


def deck_rows(floor, room):
    """The deck for the kit loader: one string per row, the room kind's digit (KIT_KINDS) on the deck, else
    '#' hull, 'm' a block of hull standing in a room (machinery seen from above), 'w' hull showing a window panel
    (WINDOWS), 'v' the drop round a lift (no wall, no cap),
    'o' the open night beyond an outdoor deck's railing (OUTDOORS; a prop block in it stays hull; a traced level
    gives its drop as OPEN, bool[H, W], and OUTDOORS is then only where the sky is)."""
    from tools.heights import KIND_CHARS
    out_rect = globals().get('OUTDOORS')
    open_mask = globals().get('OPEN')
    blocks = set((x, y) for x0, y0, x1, y1 in BLOCKS for x in range(x0, x1) for y in range(y0, y1))

    def floor_near(x, y):
        # A block standing inside a room (machinery, a crate stack): deck on at least two sides of it.
        x0, y0, x1, y1 = next(b for b in BLOCKS if b[0] <= x < b[2] and b[1] <= y < b[3])
        sides = [x0 - 1 >= 0 and any(floor[yy, x0 - 1] for yy in range(y0, y1)),
                 x1 < W and any(floor[yy, x1] for yy in range(y0, y1)),
                 y0 - 1 >= 0 and any(floor[y0 - 1, xx] for xx in range(x0, x1)),
                 y1 < H and any(floor[y1, xx] for xx in range(x0, x1))]
        # Wreckage inside a hive stays a dark mass under the creep, not clean machinery.
        near = [room[yy, xx] for xx in range(x0 - 1, x1 + 1) for yy in range(y0 - 1, y1 + 1)
                if 0 <= xx < W and 0 <= yy < H and floor[yy, xx]]
        if any(AREAS[k][2] == 'hive' for k in near if k >= 0):
            return False
        return sum(sides) >= 2

    def cell(x, y):
        if floor[y, x]:
            return KIND_CHARS[KIT_KINDS.index(kind_at(room, x, y))]
        if in_void(x, y):
            return 'v'
        if open_mask is not None:
            if open_mask[y, x] and (x, y) not in blocks:
                return 'o'
        elif out_rect and out_rect[0] <= x < out_rect[2] and out_rect[1] <= y < out_rect[3] and (x, y) not in blocks:
            return 'o'
        if (x, y) in blocks and floor_near(x, y):
            return 'm'
        return 'w' if (x, y) in WINDOWS or (x, y) in VIEWPORTS else '#'
    return [''.join(cell(x, y) for x in range(W)) for y in range(H)]


def generic_masks(W=W, H=H):
    """Terrain for a level-agnostic map. The kit plates every deck cell, so the terrain only shows in the hull
    beyond the wall caps, where Alien Swarm shows black: dark plates everywhere."""
    M = 8
    masks = np.zeros((8, H * M, W * M), np.uint8)
    masks[DARK] = 15
    return masks, np.full((H, W), DARK, np.uint8)


# Terrain layers: index -> texture (all stock).
TEXTURES = ['BraxisAlphaDarkPlates', 'BraxisAlphaPlates', 'CastanarGrating', 'BraxisAlphaRust',
            'BraxisAlphaWreckedPlates', 'AvernusPanels', 'BraxisAlphaMesh', 'CharSponge']
DARK, PLATES, GRATE, RUST, WRECK, PANEL, MESH, ORGANIC = range(8)
ROOM_FLOOR = {'lift': GRATE, 'void': DARK, 'bay': PLATES, 'hall': GRATE, 'duct': MESH, 'mess': PANEL, 'reactor': DARK, 'cargo': PLATES, 'lab': PANEL, 'hive': WRECK, 'hull': DARK,
              'surface': PLATES, 'bridge': GRATE, 'plant': DARK, 'core': DARK}


def terrain_masks(floor, room):
    from tools.shipkit import _noise
    M = 8
    masks = np.zeros((8, H * M, W * M), np.float32)
    base = np.zeros((H, W), int)
    for y in range(H):
        for x in range(W):
            base[y, x] = ROOM_FLOOR[kind_at(room, x, y)] if floor[y, x] and not in_void(x, y) else DARK
    big = np.repeat(np.repeat(base, M, 0), M, 1)
    for k in range(8):
        masks[k] = (big == k).astype(np.float32)
    # Soften room edges a little.
    from PIL import Image, ImageFilter
    for k in range(8):
        im = Image.fromarray((masks[k] * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(3))
        masks[k] = np.asarray(im).astype(np.float32) / 255
    # Rust and wreckage in patches everywhere; organic growth around the nest and lab.
    rust = np.clip((_noise(0, 120, 31, 4, (H * M, W * M)) - 0.58) * 4, 0, 1)
    wreck = np.clip((_noise(0, 90, 32, 4, (H * M, W * M)) - 0.62) * 4, 0, 1)
    masks *= (1 - 0.8 * rust)[None]; masks[RUST] += 0.8 * rust
    masks *= (1 - 0.7 * wreck)[None]; masks[WRECK] += 0.7 * wreck
    yy, xx = np.mgrid[0:H * M, 0:W * M] / M
    org = np.zeros((H * M, W * M), np.float32)
    for cx, cy, r in [(43, 67, 14), (75, 62, 7), (60, 65, 4), (44, 58, 4)]:
        org = np.maximum(org, np.clip(1 - np.hypot(xx - cx, yy - cy) / r, 0, 1))
    org = np.clip(org * 1.6 * (0.5 + _noise(0, 40, 33, 3, (H * M, W * M))), 0, 1)
    masks *= (1 - org)[None]; masks[ORGANIC] += org
    total = masks.sum(0) + 1e-6
    masks = masks / total[None]
    q = np.rint(masks * 15).astype(np.uint8)
    dominant = np.zeros((H, W), np.uint8)
    for y in range(H):
        for x in range(W):
            dominant[y, x] = int(np.argmax(masks[:, y * M + 4, x * M + 4]))
    return q, dominant


def galaxy_tables(solid):
    """Collision rows for the script: one string per row, '1' blocked."""
    return [''.join('1' if solid[y, x] else '0' for x in range(W)) for y in range(H)]
