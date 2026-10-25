"""Real floor heights for a level, from the Alien Swarm map it was traced from (tools/asdata/).

A level module opts in with
    HEIGHTS = ('asi-jac1-landingbay_01', hammer_x_of_cell_0, hammer_y_of_cell_0, units_per_cell)
which is the same fit its trace used. Every deck cell then takes the height of the real walkable floor
under its centre; a level without HEIGHTS stays flat at FLOOR.

Heights are terrain heights in map units. Alien Swarm's z DECK_Z (832, the height of Landing Bay's north
block and Cargo Elevator's start; a level module may set its own, its main floor) is FLOOR, and 80 Hammer
units are one unit up.

The terrain has one height per cell corner (vertex), so a step between two deck cells becomes a slope
across the two cells that meet there; those are the level's slope cells (no floor plating, the kit puts
them at their lower corner). Hull cells take the height of the lowest deck next to them, so caps never
float above a wall (src/Kit.galaxy stands each wall on the floor it faces).

Heights are kept to 1/64 of a unit, which SC2's terrain (1/2048) holds exactly and src/Kit.galaxy's
fixed-point numbers too, so plating laid at a cell's height lies on the terrain.

Floors close in height (under MERGE) are one floor, and slivers and scraps of floor (a strip one cell wide
between two others, a plateau of a few cells) join their neighbour: a step is only kept where AS's floor
really changes level, so stairs stand where AS's do rather than as gutters along every trim.

The open night beyond an outdoor deck's railing ('o') is a real drop: its terrain lies DROP below the base
height, so what stands down there (tools/pitart.py) is seen below the deck, smaller and sliding past it as the
camera moves. The ring of open cells along the deck's edge slopes from the deck down to the pit floor; the
kit covers each with a skirt piece, the deck's steel side, as it covers stair cells with a flight.
"""
import numpy as np

DECK_Z = 832.0
UNITS = 80.0
SNAP = 8.0             # real heights are snapped to 8 units: AS's plateaus sit on that grid
PLATEAU = 16.0         # cells joined within this many Hammer units of a plateau's first cell are one flat floor
                       # (less than AS's 18-unit step: grates, trims and sampling noise, not steps)
QUANTUM = 1 / 64.0     # heights in map units are kept to this
# Deck rows: a room kind's index into tools/level.py KIT_KINDS, one character (src/Kit.galaxy AS_CharIdx); the rows'
# other letters (# hull, m machinery, o open, v void, w window) are left out.
KIND_CHARS = '0123456789abcdefghijklnpqrstu'
FLOORISH = set(KIND_CHARS + 'ov')  # deck rows: room kinds, the open drop and the lift void constrain the terrain
MERGE = 28.0           # Hammer units: neighbouring floors closer than this are one floor (AS's real steps are 40 and up)
SCRAP = 8              # a plateau of fewer cells joins the neighbour it shares most edge with
SLIVER = 0.5           # ... as does one of up to SLIVER_MAX cells, more than this share of them one cell across
SLIVER_MAX = 40
DROP = 7.0             # the pit floor under the open night: this far below the base height (map units)


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
    deck = np.array([[c in KIND_CHARS for c in row] for row in rows])
    z = np.full((H, W), floor_level)
    src = level.get('HEIGHTS')
    if src:
        from tools import asextract
        name, hx0, hy0, upc = src
        data = asextract.load(name)
        raw = np.full((H, W), np.nan)
        # A level laid out in pieces (tools/seams.py) samples each cell where it came from in the map.
        sx, sy = level.get('HEIGHTS_FROM') or (None, None)
        for y in range(H):
            for x in range(W):
                if deck[y, x]:
                    fx, fy = (x, y) if sx is None else (sx[y, x], sy[y, x])
                    if fx < 0:
                        continue
                    s = _sample(data, hx0 + upc * (fx + 0.5), hy0 + upc * (fy + 0.5))
                    if s is not None:
                        raw[y, x] = round(s / SNAP) * SNAP
        have = ~np.isnan(raw)
        if have.any():
            raw = _dilate(np.nan_to_num(raw), have)
            raw = _merge(_plateaus(_mode_filter(raw, deck), deck), deck, level.get('MERGE', MERGE))
            # A level may set a few floors by hand (HEIGHT_SET: (x0, y0, x1, y1), Hammer z), where the trace has no
            # floor the squad can reach (a stair AS climbs that the flood never crossed).
            for (x0, y0, x1, y1), hz in level.get('HEIGHT_SET', []):
                raw[y0:y1, x0:x1] = np.where(deck[y0:y1, x0:x1], hz, raw[y0:y1, x0:x1])
            z = floor_level + (raw - level.get('DECK_Z', DECK_Z)) / UNITS
    z = np.round(z / QUANTUM) * QUANTUM
    # Deck heights spread into the hull, the lowest where two meet.
    z = _dilate(z, deck, np.minimum) if deck.any() else z
    # The open night is the pit, far below every deck.
    drop_cells = np.array([[c == 'o' for c in row] for row in rows])
    z[drop_cells] = np.round((floor_level - DROP) / QUANTUM) * QUANTUM
    # A lift's drop (VOID_DEPTH, map units): the shaft runs on down past the deck, so its cells lie that far below the
    # deck beside them and the walls are seen going down into the haze (tools/elevator.py lays the haze over them).
    low = drop_cells
    if level.get('VOID_DEPTH'):
        void_cells = np.array([[c == 'v' for c in row] for row in rows])
        z[void_cells] = np.round((z[void_cells] - level['VOID_DEPTH']) / QUANTUM) * QUANTUM
        low = drop_cells | void_cells
    vert, vmask, flat = _vertices(z, floorish, low, deck)
    # Flights of several cells (FLIGHTS: (x0, y0, x1, y1), the way up 'N', 'E', 'S' or 'W', Hammer z at the foot and
    # the head): their vertices rise evenly across the rectangle, so a big climb (a mall's gallery) is a long stair
    # rather than one cell as steep as a wall. The cells at the foot and head floors already hold those heights.
    for (x0, y0, x1, y1), way, lo, hi in level.get('FLIGHTS', []):
        zl = floor_level + (lo - level.get('DECK_Z', DECK_Z)) / UNITS
        zh = floor_level + (hi - level.get('DECK_Z', DECK_Z)) / UNITS
        for vy in range(y0, y1 + 1):
            for vx in range(x0, x1 + 1):
                f = {'N': (vy - y0) / (y1 - y0), 'S': (y1 - vy) / (y1 - y0), 'E': (vx - x0) / (x1 - x0), 'W': (x1 - vx) / (x1 - x0)}[way]
                vert[vy, vx] = np.round((zl + (zh - zl) * f) / QUANTUM) * QUANTUM
                vmask[vy, vx] = True
    corners = np.stack([vert[:-1, :-1], vert[:-1, 1:], vert[1:, :-1], vert[1:, 1:]])
    tilted = corners.max(0) - corners.min(0) > 1e-3
    slope = deck & tilted
    edge = drop_cells & tilted
    cellz = np.where(slope | edge, np.floor(corners.min(0) / QUANTUM) * QUANTUM, z)
    st = stairs(vert, slope)
    return {'cellz': cellz, 'slope': slope, 'edge': edge, 'vert': vert, 'vmask': vmask, 'deck': deck, 'floorish': floorish,
            'stairs': st + stair_rails(st, slope, deck) + stairs(vert, edge, SKIRTS)}


def _vertices(z, floorish, low=None, deck=None):
    """Vertex heights. Flat deck-like cells hold all four corners at their own height; where two of different
    heights share a corner, the lower one gives way and becomes a stair cell rising to the higher, so a step is
    one cell of stairs on its low side, as AS's stair props stand. Corners of stair cells alone are filled from
    their neighbours; vertices clear of the deck take the mean of the hull round them. A corner of the pit
    (`low`) that no deck cell touches lies on the pit floor, so the deck's edge drops in one cell."""
    H, W = z.shape
    low = np.zeros(z.shape, bool) if low is None else low
    deck = np.zeros(z.shape, bool) if deck is None else deck
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
            elif any(low[c] for c in near) and not any(deck[c] for c in near):
                vert[vy, vx], known[vy, vx] = min(z[c] for c in near if low[c]), True
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
# The pit's edge cells take the same shapes (tools/pitart.py): the deck's steel side dropping to the pit floor.
SKIRTS = ('KSkirt', 'KSkirt1', 'KSkirt3')
# Handrails up an exposed side of a flight (tools/pitart.py), authored for a rise of 1 and of 0.5: the nearer is
# scaled to the flight's rise, so the rail keeps about its height.
RAILS = {('W', 1.0): 'KSRailW', ('E', 1.0): 'KSRailE', ('W', 0.5): 'KSRailWh', ('E', 0.5): 'KSRailEh'}


def stairs(vert, slope, names=(STAIR, RAMP1, RAMP3)):
    """Each slope cell's piece: (x, y, piece, turn, z, rise). The turn is counter-clockwise from the authored
    piece; z is its foot and rise its height. Corners are snapped up or down at half the rise, so a cell
    whose corners are uneven (where flights meet) takes the nearest shape."""
    STAIR, RAMP1, RAMP3 = names
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


def stair_rails(st, slope, deck):
    """Handrails where a straight flight's side is open to a flat floor beside it (not a wall, not more of the
    flight, not the corner pieces where flights meet): (x, y, rail piece, turn, z, scale), as AS's stairs
    have railings down their open sides. The rail is laid with the flight's turn and foot."""
    import math
    H, W = slope.shape
    out = []
    for x, y, piece, turn, z, rise in st:
        if piece != STAIR:
            continue
        c, s = round(math.cos(math.radians(turn))), round(math.sin(math.radians(turn)))
        for side, (lx, ly) in (('W', (-1, 0)), ('E', (1, 0))):
            nx, ny = x + lx * c - ly * s, y + lx * s + ly * c
            if not (0 <= nx < W and 0 <= ny < H) or not deck[ny, nx] or slope[ny, nx]:
                continue
            nominal = 0.5 if rise < 0.7 else 1.0
            out.append((x, y, RAILS[(side, nominal)], turn, z, rise / nominal))
    return out


def _components(z, mask):
    """Plateaus: 4-connected cells of one height. (labels [H, W], -1 off the mask; [cells per plateau])."""
    from collections import deque
    H, W = z.shape
    lab = np.full((H, W), -1)
    comps = []
    for y0, x0 in zip(*np.nonzero(mask)):
        if lab[y0, x0] >= 0:
            continue
        k = len(comps)
        q, cells = deque([(y0, x0)]), []
        lab[y0, x0] = k
        while q:
            y, x = q.popleft()
            cells.append((y, x))
            for yy, xx in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)):
                if 0 <= yy < H and 0 <= xx < W and mask[yy, xx] and lab[yy, xx] < 0 and z[yy, xx] == z[y0, x0]:
                    lab[yy, xx] = k
                    q.append((yy, xx))
        comps.append(cells)
    return lab, comps


def _merge(z, mask, merge=MERGE):
    """Plateaus that are not real levels join a neighbour, smallest first, until none is left: one within MERGE
    of a neighbour at least its size takes that one's height; a scrap of floor, or a sliver one cell across,
    takes the height of the neighbour it shares the longest edge with."""
    z = z.copy()
    H, W = z.shape
    while True:
        lab, comps = _components(z, mask)
        best = None
        for k, cells in enumerate(comps):
            edges, thin = {}, 0
            for y, x in cells:
                same = [0 <= yy < H and 0 <= xx < W and lab[yy, xx] == k for yy, xx in ((y, x - 1), (y, x + 1), (y - 1, x), (y + 1, x))]
                thin += (not same[0] and not same[1]) or (not same[2] and not same[3])
                for yy, xx in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)):
                    if 0 <= yy < H and 0 <= xx < W and lab[yy, xx] >= 0 and lab[yy, xx] != k:
                        edges[lab[yy, xx]] = edges.get(lab[yy, xx], 0) + 1
            if not edges:
                continue
            zk = z[cells[0]]
            near = [j for j in edges if abs(z[comps[j][0]] - zk) < merge and len(comps[j]) >= len(cells)]
            if near:
                to = max(near, key=lambda j: (edges[j], len(comps[j])))
            elif len(cells) < SCRAP or (len(cells) <= SLIVER_MAX and thin > SLIVER * len(cells)):
                to = max(edges, key=lambda j: (edges[j], -abs(z[comps[j][0]] - zk)))
            else:
                continue
            if best is None or len(cells) < best[0]:
                best = (len(cells), k, to)
        if best is None:
            return z
        _, k, to = best
        target = z[comps[to][0]]
        for c in comps[k]:
            z[c] = target


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


EXT = 6                # cells of open night carried on past a level's east edge, out of the camera's sight


def extend(rows, hts, floor_level, ext=EXT):
    """A level whose east edge is open night, carried EXT cells further east: a row ending in the open goes on as
    open (at the pit floor), any other as hull at its last cell's height, so the pit runs on out of sight rather
    than stopping at a black edge. Returns hts with the wider arrays and the wider rows as hts['rows']."""
    out = dict(hts)
    out['rows'] = list(rows)
    if not any(r[-1] == 'o' for r in rows):
        return out
    H, W = len(rows), len(rows[0])
    pit = np.round((floor_level - DROP) / QUANTUM) * QUANTUM
    is_open = np.array([r[-1] == 'o' for r in rows])
    out['rows'] = [r + ('o' if r[-1] == 'o' else '#') * ext for r in rows]
    wide = lambda a, fill: np.concatenate([a, np.full((a.shape[0], ext), fill, a.dtype)], 1)
    cz = np.concatenate([hts['cellz'], np.repeat(hts['cellz'][:, -1:], ext, 1)], 1)
    cz[is_open, W:] = pit
    out['cellz'] = cz
    for k in ('slope', 'edge', 'deck'):
        out[k] = wide(hts[k], False)
    out['floorish'] = wide(hts['floorish'], False)
    out['floorish'][is_open, W:] = True
    vert = np.concatenate([hts['vert'], np.repeat(hts['vert'][:, -1:], ext, 1)], 1)
    vmask = wide(hts['vmask'], False)
    for vy in range(H + 1):
        near = [y for y in (vy - 1, vy) if 0 <= y < H and is_open[y]]
        if near:
            vert[vy, W + 1:] = pit
            vmask[vy, W + 1:] = True
    out['vert'], out['vmask'] = vert, vmask
    return out
