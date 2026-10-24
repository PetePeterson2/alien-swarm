"""Real floor heights for a level, from the Alien Swarm map it was traced from (tools/asdata/).

A level module opts in with
    HEIGHTS = ('asi-jac1-landingbay_01', hammer_x_of_cell_0, hammer_y_of_cell_0, units_per_cell)
which is the same fit its trace used. Every deck cell then takes the height of the real walkable floor
under its centre; a level without HEIGHTS stays flat at FLOOR.

Heights are terrain heights in map units. Alien Swarm's z DECK_Z (832, the height of Landing Bay's north
block and Cargo Elevator's start) is FLOOR, and 80 Hammer units are one unit up.

The terrain has one height per cell corner (vertex), so a step between two deck cells becomes a slope
across the two cells that meet there; those are the level's slope cells (no floor plating, the kit puts
them at their lower corner). Hull cells take the height of the lowest deck next to them, so caps never
float above a wall (src/Kit.galaxy stands each wall on the floor it faces).

Heights are kept to 1/64 of a unit, which SC2's terrain (1/2048) holds exactly and src/Kit.galaxy's
fixed-point numbers too, so plating laid at a cell's height lies on the terrain.
"""
import numpy as np

DECK_Z = 832.0
UNITS = 80.0
SNAP = 8.0             # real heights are snapped to 8 units: AS's plateaus sit on that grid
PLATEAU = 16.0         # cells joined within this many Hammer units of a plateau's first cell are one flat floor
                       # (less than AS's 18-unit step: grates, trims and sampling noise, not steps)
QUANTUM = 1 / 64.0     # heights in map units are kept to this
FLOORISH = set('0123456789ov')   # deck rows: room kinds, the open drop and the lift void constrain the terrain


def _sample(data, hx, hy, rings=4):
    """Median walkable z near Hammer point (hx, hy), searching outward ring by ring of 40-unit cells; None if none."""
    c = data['cell']
    i, j = int((hx - data['x0']) // c), int((hy - data['y0']) // c)
    wz = data['walk_z']
    for r in range(rings + 1):
        vals = wz[max(0, j - r):j + r + 1, max(0, i - r):i + r + 1]
        vals = vals[~np.isnan(vals)]
        if len(vals):
            return float(np.median(vals))
    return None


def _mode_filter(z, mask):
    out = z.copy()
    H, W = z.shape
    for y in range(H):
        for x in range(W):
            if not mask[y, x]:
                continue
            vals = [z[yy, xx] for yy in range(max(0, y - 1), min(H, y + 2)) for xx in range(max(0, x - 1), min(W, x + 2)) if mask[yy, xx]]
            u, n = np.unique(vals, return_counts=True)
            best = u[n == n.max()]
            out[y, x] = z[y, x] if z[y, x] in best else best[0]
    return out


def _plateaus(z, mask, tol=PLATEAU):
    """Flat floors: the commonest height first, each plateau grown over neighbouring cells within tol of its
    seed, then set to its members' commonest height. A ramp comes out as steps of about tol."""
    from collections import deque
    out = z.copy()
    done = ~mask.copy()
    H, W = z.shape
    while not done.all():
        vals, counts = np.unique(z[~done], return_counts=True)
        seed_z = vals[counts.argmax()]
        seeds = np.argwhere(~done & (z == seed_z))
        for y0, x0 in seeds:
            if done[y0, x0]:
                continue
            q, members = deque([(y0, x0)]), []
            done[y0, x0] = True
            while q:
                y, x = q.popleft()
                members.append((y, x))
                for yy, xx in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)):
                    if 0 <= yy < H and 0 <= xx < W and not done[yy, xx] and abs(z[yy, xx] - seed_z) <= tol:
                        done[yy, xx] = True
                        q.append((yy, xx))
            mv, mc = np.unique([z[c] for c in members], return_counts=True)
            for c in members:
                out[c] = mv[mc.argmax()]
    return out


def _dilate(z, known, pick=np.maximum):
    """Fill unknown cells from their nearest known neighbours, ring by ring (ties: `pick`, the highest by default)."""
    z, known = z.copy(), known.copy()
    H, W = z.shape
    while not known.all():
        empty = -np.inf if pick is np.maximum else np.inf
        grow = np.full(z.shape, empty)
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)):
            sh = np.full(z.shape, empty)
            src = np.where(known, z, empty)
            ys, yd = (slice(0, H - dy), slice(dy, H)) if dy >= 0 else (slice(-dy, H), slice(0, H + dy))
            xs, xd = (slice(0, W - dx), slice(dx, W)) if dx >= 0 else (slice(-dx, W), slice(0, W + dx))
            sh[yd, xd] = src[ys, xs]
            grow = pick(grow, sh)
        new = ~known & np.isfinite(grow)
        if not new.any():
            z[~known] = z[known].min() if known.any() else 0.0
            break
        z[new] = grow[new]
        known |= new
    return z


def level_heights(level, rows, floor_level):
    """For one level (its module globals as `level`, its deck rows from tools/level.py deck_rows):
    cell heights [H, W], slope cells [H, W], vertex heights [H+1, W+1] and which vertices are constrained."""
    H, W = len(rows), len(rows[0])
    floorish = np.array([[c in FLOORISH for c in row] for row in rows])
    deck = np.array([[c.isdigit() for c in row] for row in rows])
    z = np.full((H, W), floor_level)
    src = level.get('HEIGHTS')
    if src:
        from tools import asextract
        name, hx0, hy0, upc = src
        data = asextract.load(name)
        raw = np.full((H, W), np.nan)
        for y in range(H):
            for x in range(W):
                if deck[y, x]:
                    s = _sample(data, hx0 + upc * (x + 0.5), hy0 + upc * (y + 0.5))
                    if s is not None:
                        raw[y, x] = round(s / SNAP) * SNAP
        have = ~np.isnan(raw)
        if have.any():
            raw = _dilate(np.nan_to_num(raw), have)
            raw = _plateaus(_mode_filter(raw, deck), deck)
            z = floor_level + (raw - DECK_Z) / UNITS
    z = np.round(z / QUANTUM) * QUANTUM
    # Deck heights spread into the hull, the lowest where two meet.
    z = _dilate(z, deck, np.minimum) if deck.any() else z
    vert, vmask, flat = _vertices(z, floorish)
    corners = np.stack([vert[:-1, :-1], vert[:-1, 1:], vert[1:, :-1], vert[1:, 1:]])
    slope = deck & (corners.max(0) - corners.min(0) > 1e-3)
    cellz = np.where(slope, np.floor(corners.min(0) / QUANTUM) * QUANTUM, z)
    return {'cellz': cellz, 'slope': slope, 'vert': vert, 'vmask': vmask, 'deck': deck, 'floorish': floorish,
            'stairs': stairs(vert, slope)}


def _vertices(z, floorish):
    """Vertex heights. Flat deck-like cells hold all four corners at their own height; where two of different
    heights share a corner, the lower one gives way and becomes a stair cell rising to the higher, so a step is
    one cell of stairs on its low side, as AS's stair props stand. Corners of stair cells alone are filled from
    their neighbours; vertices clear of the deck take the mean of the hull round them."""
    H, W = z.shape
    flat = floorish.copy()
    while True:
        give = np.zeros_like(flat)
        for vy in range(H + 1):
            for vx in range(W + 1):
                near = [(y, x) for y in (vy - 1, vy) for x in (vx - 1, vx) if 0 <= y < H and 0 <= x < W and flat[y, x]]
                if len(near) > 1:
                    top = max(z[c] for c in near)
                    for c in near:
                        if z[c] < top - 1e-6:
                            give[c] = True
        if not give.any():
            break
        flat &= ~give
    vert = np.zeros((H + 1, W + 1))
    vmask = np.zeros((H + 1, W + 1), bool)
    known = np.zeros((H + 1, W + 1), bool)
    for vy in range(H + 1):
        for vx in range(W + 1):
            near = [(y, x) for y in (vy - 1, vy) for x in (vx - 1, vx) if 0 <= y < H and 0 <= x < W]
            fl = [z[c] for c in near if flat[c]]
            vmask[vy, vx] = any(floorish[c] for c in near)
            if fl:
                vert[vy, vx], known[vy, vx] = fl[0], True
            elif not vmask[vy, vx]:
                vert[vy, vx], known[vy, vx] = np.mean([z[c] for c in near]), True
    # Corners only stair cells touch: the mean of their settled neighbours, ring by ring.
    while not known.all():
        new = []
        for vy, vx in zip(*np.nonzero(~known)):
            nb = [vert[p] for p in ((vy + 1, vx), (vy - 1, vx), (vy, vx + 1), (vy, vx - 1))
                  if 0 <= p[0] <= H and 0 <= p[1] <= W and known[p]]
            if nb:
                new.append(((vy, vx), np.round(np.mean(nb) / QUANTUM) * QUANTUM))
        if not new:
            break
        for p, v in new:
            vert[p], known[p] = v, True
    return vert, vmask, flat


# Stair cell shapes (src/Kit.galaxy AS_KitStairs, tools/level.py stair_pieces), by which corners are up:
# a straight flight rising north at turn 0, one corner up (north-east at turn 0), three up (south-west down).
STAIR, RAMP1, RAMP3 = 'KStair', 'KRamp1', 'KRamp3'


def stairs(vert, slope):
    """Each slope cell's piece: (x, y, piece, turn, z, rise). The turn is counter-clockwise from the authored
    piece; z is its foot and rise its height. Corners are snapped up or down at half the rise, so a cell
    whose corners are uneven (where flights meet) takes the nearest shape."""
    out = []
    for y, x in zip(*np.nonzero(slope)):
        sw, se, nw, ne = vert[y, x], vert[y, x + 1], vert[y + 1, x], vert[y + 1, x + 1]
        lo, hi = min(sw, se, nw, ne), max(sw, se, nw, ne)
        up = tuple(c - lo > (hi - lo) / 2 for c in (sw, se, ne, nw))     # counter-clockwise from south-west
        n = sum(up)
        if n == 2 and up[0] != up[2]:
            # Two neighbouring corners up: a flight rising toward that side (north, west, south, east).
            side = {(False, False, True, True): 0, (True, False, False, True): 90,
                    (True, True, False, False): 180, (False, True, True, False): 270}[up]
            out.append((x, y, STAIR, side, lo, hi - lo))
        elif n == 1:
            out.append((x, y, RAMP1, {2: 0, 3: 90, 0: 180, 1: 270}[up.index(True)], lo, hi - lo))
        elif n == 3:
            out.append((x, y, RAMP3, {0: 0, 1: 90, 2: 180, 3: 270}[up.index(False)], lo, hi - lo))
        else:
            # Opposite corners up: a saddle no piece follows; the higher plate covers it.
            out.append((x, y, RAMP3, {0: 0, 1: 90, 2: 180, 3: 270}[up.index(False)], lo, hi - lo))
    return out


def runs(cellz, slope):
    """Each row as runs of equal cells: (y, x0, x1, z, slope)."""
    out = []
    H, W = cellz.shape
    for y in range(H):
        x0 = 0
        for x in range(1, W + 1):
            if x == W or cellz[y, x] != cellz[y, x0] or slope[y, x] != slope[y, x0]:
                out.append((y, x0, x, float(cellz[y, x0]), bool(slope[y, x0])))
                x0 = x
    return out
