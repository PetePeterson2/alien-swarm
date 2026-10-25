"""The autopilot's way through a level (ROUTE), worked out over the deck the way src/Bots.galaxy walks it.

The autopilot walks straight at each waypoint (src/Bots.galaxy AS_RouteGoal), so every leg must keep a marine's
body clear of the walls, the drops and the corners it passes: the leg itself and a line either side of it at the
marine's radius must not cross a solid cell (src/Marine.galaxy AS_RayWall), and no point of it may come closer to
a solid cell than CLEAR. Between the stops a level gives (where the autopilot has a job, or must pass), the way is
the cheapest walk over the open cells, dearer the nearer it runs to a wall, cut into the fewest clear legs.

    py tools/routeplan.py <level>            check the level's ROUTE leg by leg
    py tools/routeplan.py <level> --plan     plan it from the level's ROUTE_STOPS and print the rows

ROUTE_STOPS: [(x, y, wait)], the waits as ROUTE's (src/Bots.galaxy): 1 the panel by it hacked, 5 the button by it
pressed, 6 the door by it open, 7 the eggs and growths in sight of it gone.

The check also names any egg or growth no wait-7 stop takes in: within 9 of it, on its floor and in sight of it to a
cell short (src/Hive.galaxy AS_HiveNear), since the mission's count waits on every one.
"""
from pathlib import Path
import heapq
import math
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tools import level as L  # noqa: E402

BODY = 0.35        # either side of the leg (src/Bots.galaxy AS_BotWay tests 0.3)
CLEAR = 0.45       # nearest a leg's points may come to a solid cell's edge (a duct one cell wide gives 0.5 down its middle)


def grid():
    """Solid cells as the game has them (tools/level.py blocked), with every door open but the goo's blocks."""
    floor, room = L.carve()
    solid = L.blocked(floor)
    for name, (x0, y0, x1, y1), kind, *_ in getattr(L, 'DOORS', []):
        if kind != 'block':
            solid[y0:y1, x0:x1] = False
    return solid


def ray_clear(solid, x0, y0, x1, y1):
    """src/Marine.galaxy AS_RayWall over the cells: does the segment cross no solid cell?"""
    H, W = solid.shape
    d = math.hypot(x1 - x0, y1 - y0)
    if d < 1e-6:
        return True
    c, s = (x1 - x0) / d, (y1 - y0) / d
    cx, cy = int(math.floor(x0)), int(math.floor(y0))
    if not (0 <= cx < W and 0 <= cy < H) or solid[cy, cx]:
        return False
    sx = 1 if c > 0 else -1
    sy = 1 if s > 0 else -1
    dx = 1 / abs(c) if abs(c) > 1e-4 else 1e9
    dy = 1 / abs(s) if abs(s) > 1e-4 else 1e9
    tx = ((cx + 1 - x0) if c > 0 else (x0 - cx)) * dx if abs(c) > 1e-4 else 1e9
    ty = ((cy + 1 - y0) if s > 0 else (y0 - cy)) * dy if abs(s) > 1e-4 else 1e9
    while True:
        if tx < ty:
            t = tx; cx += sx; tx += dx
        else:
            t = ty; cy += sy; ty += dy
        if t >= d:
            return True
        if not (0 <= cx < W and 0 <= cy < H) or solid[cy, cx]:
            return False


def edge_dist(solid, x, y):
    """Distance from a point to the nearest solid cell's edge (within three cells; 3 if none)."""
    H, W = solid.shape
    best = 3.0
    ix, iy = int(math.floor(x)), int(math.floor(y))
    for cy in range(iy - 3, iy + 4):
        for cx in range(ix - 3, ix + 4):
            if 0 <= cx < W and 0 <= cy < H and not solid[cy, cx]:
                continue
            nx, ny = max(cx, min(x, cx + 1)), max(cy, min(y, cy + 1))
            best = min(best, math.hypot(nx - x, ny - y))
    return best


def leg_clear(solid, a, b):
    """The leg a-b: its line and a line either side at BODY clear, and no point of it within CLEAR of a solid cell."""
    (x0, y0), (x1, y1) = a, b
    d = math.hypot(x1 - x0, y1 - y0)
    if d < 1e-6:
        return True
    ox, oy = -(y1 - y0) / d * BODY, (x1 - x0) / d * BODY
    if not all(ray_clear(solid, x0 + k * ox, y0 + k * oy, x1 + k * ox, y1 + k * oy) for k in (0, 1, -1)):
        return False
    n = max(2, int(d / 0.25))
    return all(edge_dist(solid, x0 + (x1 - x0) * i / n, y0 + (y1 - y0) * i / n) >= CLEAR for i in range(n + 1))


def clearance(solid):
    """Chessboard distance in cells from each open cell to the nearest solid one."""
    H, W = solid.shape
    dist = np.where(solid, 0, 10 ** 6)
    frontier = list(zip(*np.nonzero(solid)))
    k = 0
    while frontier:
        k += 1
        nxt = []
        for y, x in frontier:
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    yy, xx = y + dy, x + dx
                    if 0 <= yy < H and 0 <= xx < W and dist[yy, xx] > k:
                        dist[yy, xx] = k
                        nxt.append((yy, xx))
        frontier = nxt
    return dist


def walk(solid, clear, a, b):
    """The cheapest 8-way walk over open cells from cell a to cell b, dearer near walls; [(x, y)] cell middles."""
    H, W = solid.shape
    cost = {a: 0.0}
    came = {}
    q = [(0.0, a)]
    while q:
        c, (x, y) = heapq.heappop(q)
        if (x, y) == b:
            break
        if c > cost[(x, y)]:
            continue
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                if not dx and not dy:
                    continue
                xx, yy = x + dx, y + dy
                if not (0 <= xx < W and 0 <= yy < H) or solid[yy, xx]:
                    continue
                if dx and dy and (solid[y, xx] or solid[yy, x]):
                    continue
                k = clear[yy, xx]
                step = math.hypot(dx, dy) * (1.0 + (6.0 if k <= 1 else 2.0 if k == 2 else 0.0))
                if c + step < cost.get((xx, yy), 1e18):
                    cost[(xx, yy)] = c + step
                    came[(xx, yy)] = (x, y)
                    heapq.heappush(q, (c + step, (xx, yy)))
    if b not in cost:
        raise SystemExit('no way from %s to %s' % (a, b))
    path = [b]
    while path[-1] != a:
        path.append(came[path[-1]])
    return [(x + 0.5, y + 0.5) for x, y in reversed(path)]


def legs(solid, pts):
    """The fewest clear legs along a walk: from each point, the farthest one further on still in a clear leg."""
    out = [pts[0]]
    i = 0
    while i < len(pts) - 1:
        j = len(pts) - 1
        while j > i + 1 and not leg_clear(solid, pts[i], pts[j]):
            j -= 1
        out.append(pts[j])
        i = j
    return out


def plan(stops):
    solid = grid()
    clear = clearance(solid)
    rows = []
    here = L.SPAWN
    for x, y, wait in stops:
        a = (int(here[0]), int(here[1]))
        b = (int(x), int(y))
        way = legs(solid, [here] + walk(solid, clear, a, b)[1:-1] + [(x, y)])
        rows += [(round(px, 1), round(py, 1), 0) for px, py in way[1:-1]] + [(x, y, wait)]
        here = (x, y)
    return rows


def piece(x, y):
    """A level laid out in pieces (tools/seams.py): the piece the cell is in."""
    return L.PIECE_ROWS[int(y)][int(x)]


def check(route, seams=None):
    """The legs that are not clear. A leg from one piece to the next (tools/seams.py) goes through the seam, not
    across the map between them: those go into `seams` instead."""
    solid = grid()
    bad = []
    here = L.SPAWN
    for i, (x, y, wait) in enumerate(route):
        if getattr(L, 'PIECE_ROWS', None) and piece(*here) != piece(x, y):
            if seams is not None:
                seams.append((i, here, (x, y)))
        elif not leg_clear(solid, here, (x, y)):
            bad.append((i, here, (x, y)))
        here = (x, y)
    return bad


def hive_sight(solid, x0, y0, x1, y1):
    """src/Hive.galaxy AS_HiveSight: in sight up to a cell short of the target."""
    d = math.hypot(x1 - x0, y1 - y0)
    f = max(0.0, (d - 1.0) / max(d, 0.01))
    return ray_clear(solid, x0, y0, x0 + (x1 - x0) * f, y0 + (y1 - y0) * f)


def unswept(route):
    """The eggs and growths no wait-7 stop of the route takes in."""
    from tools import heights
    floor, room = L.carve()
    cz = heights.level_heights(vars(L), L.deck_rows(floor, room), L.FLOOR)['cellz']
    solid = grid()
    stops = [(x, y) for x, y, wait in route if wait == 7]
    things = [('egg', e[0], e[1]) for e in getattr(L, 'EGGS', [])] + [('goo', b[0], b[1]) for b in getattr(L, 'BIOMASS', [])]
    out = []
    for kind, ex, ey in things:
        z = cz[int(ey), int(ex)]
        if not any(math.hypot(ex - x, ey - y) <= 9.0 and abs(cz[int(y), int(x)] - z) <= 1.0 and hive_sight(solid, x, y, ex, ey)
                   for x, y in stops):
            out.append((kind, ex, ey))
    return out


def main():
    name = sys.argv[1]
    L.use(name)
    if '--plan' in sys.argv:
        rows = plan(L.ROUTE_STOPS)
        print('ROUTE = [')
        for k in range(0, len(rows), 6):
            print('    ' + ' '.join('(%s, %s, %d),' % r for r in rows[k:k + 6]))
        print(']')
        return
    seams = []
    bad = check(L.ROUTE, seams)
    for i, a, b in bad:
        print('leg %d from %s to %s is not clear' % (i, a, b))
    print('%s: %d legs, %d not clear' % (name, len(L.ROUTE), len(bad)) + (', %d through a seam' % len(seams) if seams else ''))
    left = unswept(L.ROUTE)
    for kind, x, y in left:
        print("%s at (%.1f, %.1f) is in no wait-7 stop's reach" % (kind, x, y))
    if getattr(L, 'EGGS', None) or getattr(L, 'BIOMASS', None):
        print("%s: %d eggs and growths out of the route's reach" % (name, len(left)))


if __name__ == '__main__':
    main()
