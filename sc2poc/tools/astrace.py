"""A level traced straight from the real map's walkable floor (tools/asdata/, tools/asextract.py).

Landing Bay was traced by hand from the briefing overview. The outdoor and plant levels that follow are
traced from the map itself: a level module makes a Trace over the 80-unit cells it covers, takes its deck
(the walkable floor), its open drop (where nothing stands within reach below the deck) and its entities in
level cells from it, and keeps only rectangles of its own (rooms, cuts, the mission's fittings) by hand.

    t = Trace('asi-jac2-deima', cx0, cy0, W, H)    cells of 80 units, cell (0, 0) at 80-unit cell (cx0, cy0)
    t.HEIGHTS                                       the fit tools/heights.py samples floor heights with
    t.deck()                                        bool[H, W]: walkable floor
    t.walls(pct)                                    bool[H, W]: walled at chest height over pct percent of the cell
    t.below(z)                                      bool[H, W]: nothing up-facing at z or above (the drop)
    t.at(hx, hy), t.rect(box)                       Hammer points and boxes in level cells

    py tools/astrace.py <map> cx0 cy0 W H [class ...]   the entities and their outputs in level cells

Only numbers and names are taken; nothing of Valve's is shipped.
"""
from pathlib import Path
import sys
from collections import deque

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tools import asextract  # noqa: E402

UNITS = 80.0
# asw_spawner AlienClass: an index into the SDK's spawnable list (asw_spawner.cpp), in this order.
KIND = ['AS_DRONE', 'AS_BUZZER', 'AS_PARASITE', 'AS_SHIELDBUG', 'AS_GRUB', 'AS_JUMPER', 'AS_HARVESTER', 'AS_XENOMITE',
        'AS_QUEEN', 'AS_BOOMER', 'AS_RANGER', 'AS_MORTAR', 'AS_SHAMAN']


def _num(keys, k, dflt=0.0):
    # Instanced entities carry '???' where the instance fills a value in: the default stands.
    try:
        return float(keys.get(k, dflt))
    except ValueError:
        return float(dflt)


def _halve(a, how):
    """40-unit cells to 80: each 2x2 block reduced by `how` (nan where all four are)."""
    H2, W2 = a.shape[0] // 2, a.shape[1] // 2
    b = a[:H2 * 2, :W2 * 2].astype(float).reshape(H2, 2, W2, 2).transpose(0, 2, 1, 3).reshape(H2, W2, 4)
    with np.errstate(all='ignore'):
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            return how(b, -1)


def _mode(b, axis):
    """The commonest non-zero value along the axis (0 where all are 0); ties go to the higher kind."""
    b = np.nan_to_num(b).astype(int)
    n = int(b.max()) + 1 if b.size else 1
    counts = np.stack([(b == k).sum(axis) for k in range(n)], -1)
    counts[..., 0] = 0
    best = n - 1 - np.argmax(counts[..., ::-1], -1)
    return np.where(counts.max(-1) > 0, best, 0)


def components(mask, smallest):
    """The mask without its 4-connected pieces smaller than `smallest` cells."""
    keep = np.zeros_like(mask)
    seen = np.zeros_like(mask)
    H, W = mask.shape
    for y0, x0 in np.argwhere(mask):
        if seen[y0, x0]:
            continue
        q, cells = deque([(y0, x0)]), []
        seen[y0, x0] = True
        while q:
            y, x = q.popleft()
            cells.append((y, x))
            for yy, xx in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)):
                if 0 <= yy < H and 0 <= xx < W and mask[yy, xx] and not seen[yy, xx]:
                    seen[yy, xx] = True
                    q.append((yy, xx))
        if len(cells) >= smallest:
            for c in cells:
                keep[c] = True
    return keep


def grow(mask, d):
    """The mask grown by d cells every way (Chebyshev)."""
    out = mask.copy()
    for _ in range(d):
        g = out.copy()
        g[1:, :] |= out[:-1, :]
        g[:-1, :] |= out[1:, :]
        g[:, 1:] |= out[:, :-1]
        g[:, :-1] |= out[:, 1:]
        g[1:, 1:] |= out[:-1, :-1]
        g[1:, :-1] |= out[:-1, 1:]
        g[:-1, 1:] |= out[1:, :-1]
        g[:-1, :-1] |= out[1:, 1:]
        out = g
    return out


def box(mask, x0, y0, x1, y1):
    """A copy of the mask with only the cells inside the rectangle kept."""
    out = np.zeros_like(mask)
    out[y0:y1, x0:x1] = mask[y0:y1, x0:x1]
    return out


class Trace:
    def __init__(self, name, cx0, cy0, W, H):
        self.name, self.cx0, self.cy0, self.W, self.H = name, cx0, cy0, W, H
        d = self.data = asextract.load(name)
        assert d['cell'] * 2 == UNITS
        self.hx0, self.hy0 = d['x0'] + UNITS * cx0, d['y0'] + UNITS * cy0
        self.HEIGHTS = (name, self.hx0, self.hy0, UNITS)
        self.walk_z = self._crop(_halve(d['walk_z'], np.nanmedian))
        self.walk_pct = self._crop(_halve(d['walk_pct'], np.nanmean))
        self.top_z = self._crop(_halve(d['top_z'], np.nanmax))
        self.wall_pct = self._crop(_halve(d['wall_pct'], np.nanmean)) if 'wall_pct' in d else np.zeros((H, W))
        # The walls in 10-unit pixels, 8 to a cell, south row first.
        self.wall_px = np.zeros((H * 8, W * 8), bool)
        if 'wall_px' in d:
            px = d['wall_px']
            ys, xs = slice(max(0, cy0 * 8), min(px.shape[0], (cy0 + H) * 8)), slice(max(0, cx0 * 8), min(px.shape[1], (cx0 + W) * 8))
            self.wall_px[ys.start - cy0 * 8:ys.stop - cy0 * 8, xs.start - cx0 * 8:xs.stop - cx0 * 8] = px[ys, xs]
        # The floor's material kind (tools/asextract.py FLOOR_MATS), the commonest of a cell's four, 0 none.
        self.floor_mat = np.nan_to_num(self._crop(_halve(d['floor_mat'], _mode))).astype(int) if 'floor_mat' in d else np.zeros((H, W), int)
        self.entities = d['entities']

    def _crop(self, a):
        out = np.full((self.H, self.W), np.nan)
        H2, W2 = a.shape
        ys, xs = slice(max(0, self.cy0), min(H2, self.cy0 + self.H)), slice(max(0, self.cx0), min(W2, self.cx0 + self.W))
        out[ys.start - self.cy0:ys.stop - self.cy0, xs.start - self.cx0:xs.stop - self.cx0] = a[ys, xs]
        return out

    def deck(self, pct=50, smallest=12, zmin=-1e9, zmax=1e9):
        """Walkable floor: at least `pct` percent of the cell walkable, its floor within zmin..zmax, in pieces of
        at least `smallest` cells (nav nodes on ledges and props make specks)."""
        with np.errstate(invalid='ignore'):
            m = (np.nan_to_num(self.walk_pct) >= pct) & ~np.isnan(self.walk_z) & (self.walk_z >= zmin) & (self.walk_z <= zmax)
        return components(m, smallest)

    def walls(self, pct=10):
        """Cells a solid brush stands in at chest height over at least `pct` percent of the cell (tools/asextract.py
        wall_pct): the rooms' walls, which the floor alone does not show where they are detail brushes."""
        return np.nan_to_num(self.wall_pct) >= pct

    def open_deck(self, pct=50, smallest=12):
        """The deck without the floor the walls stand on: a cell is deck when at least `pct` percent of it is walkable
        and not walled (detail blocks the floor runs on under, and the clips along the walls, go)."""
        free = np.nan_to_num(self.walk_pct) - np.nan_to_num(self.wall_pct)
        return components(self.deck(pct, smallest) & (free >= pct), smallest)

    def partitions(self, deck, fill=6):
        """Deck cells a thin wall crosses with deck on both sides of it: a band of wall pixels `fill` of 8 long across
        the cell, east-west with deck north and south, or north-south with deck east and west. These are the walls
        between rooms, too thin to take half a cell, that the port makes a cell of hull."""
        H, W = deck.shape
        b = self.wall_px[:H * 8, :W * 8].reshape(H, 8, W, 8)
        across = b.sum(3).max(1) >= fill            # a pixel row nearly full: a wall running east-west
        along = b.sum(1).max(2) >= fill             # a pixel column nearly full: north-south
        d = np.pad(deck, 1)
        ns = d[:-2, 1:-1] & d[2:, 1:-1]
        ew = d[1:-1, :-2] & d[1:-1, 2:]
        return deck & ((across & ns) | (along & ew))

    def below(self, z):
        """Cells where the highest up-facing surface lies below z, or there is none at all inside the map's floor."""
        with np.errstate(invalid='ignore'):
            return np.nan_to_num(self.top_z, nan=-1e9) < z

    def known(self):
        """Cells with any up-facing surface (the rest is solid, or outside the map)."""
        return ~np.isnan(self.top_z)

    def at(self, hx, hy):
        return ((hx - self.hx0) / UNITS, (hy - self.hy0) / UNITS)

    def rect(self, box):
        x0, y0 = self.at(box[0], box[1])
        x1, y1 = self.at(box[3], box[4])
        return (x0, y0, x1, y1)

    def named(self, name):
        return [e for e in self.entities if e.get('name') == name]

    def of(self, cls):
        return [e for e in self.entities if e['class'] == cls]

    def where(self, e):
        if 'box' in e and e['class'].startswith(('trigger', 'func_')):
            x0, y0, x1, y1 = self.rect(e['box'])
            return (round((x0 + x1) / 2, 1), round((y0 + y1) / 2, 1))
        if 'origin' in e:
            x, y = self.at(*e['origin'][:2])
            return (round(x, 1), round(y, 1))
        return None

    def spawner(self, e):
        """A SPAWNERS row (build.py mission_galaxy) for one asw_spawner, options and all."""
        k = e.get('keys', {})
        cls = k.get('AlienClass', '0')
        x, y = self.at(*e['origin'][:2])
        row = [e.get('name', ''), round(x, 1), round(y, 1), KIND[int(cls)] if cls.isdigit() else 'AS_DRONE',
               int(_num(k, 'NumAliens', 1)), int(_num(k, 'MaxLiveAliens', 1)), round(_num(k, 'SpawnInterval', 1), 2),
               int(_num(k, 'InfiniteAliens')), int(_num(k, 'MinSkillLevel')), int(_num(k, 'MaxSkillLevel')),
               int(_num(k, 'SpawnIfMarinesAreNear')), int(_num(k, 'StartBurrowed'))]
        o = {}
        if _num(k, 'SpawnerState', 1) == 0:
            o['start'] = True
        near = _num(k, 'NearDistance', 740)
        if near != 740:
            o['near'] = round(near / UNITS, 2)
        jit = _num(k, 'SpawnIntervalJitter', 25) / 100.0
        if abs(jit - 0.25) > 1e-6:
            o['jitter'] = round(jit, 2)
        order = int(_num(k, 'AlienOrders', 0))
        target = k.get('AlienOrderTargetName', '')
        if order in (1, 2) and target and self.named(target):
            o['order'] = order
            o['target'] = tuple(round(v, 1) for v in self.at(*self.named(target)[0]['origin'][:2]))
        if o:
            row.append(o)
        return tuple(row)

    def spawners(self, only=None):
        """Every asw_spawner something can start (or that starts by itself), as SPAWNERS rows."""
        targets = {conn.split(',')[0] for e in self.entities for _, conn in e.get('io', [])}
        out = []
        for e in self.of('asw_spawner'):
            k = e.get('keys', {})
            if _num(k, 'SpawnerState', 1) != 0 and e.get('name', '') not in targets:
                continue
            if only and not only(e):
                continue
            out.append(self.spawner(e))
        return out


def main():
    name, cx0, cy0, W, H = sys.argv[1], *map(int, sys.argv[2:6])
    classes = set(sys.argv[6:])
    t = Trace(name, cx0, cy0, W, H)
    for e in t.entities:
        if classes and e['class'] not in classes:
            continue
        if not e.get('io') and not classes:
            continue
        box = ''
        if 'box' in e:
            box = ' box=(%.1f,%.1f,%.1f,%.1f)' % t.rect(e['box'])
        keys = {a: b for a, b in e.get('keys', {}).items() if a not in ('spawnflags', 'angles', 'origin')}
        print('%s %s @%s%s %s' % (e['class'], e.get('name', ''), t.where(e), box, keys if classes else ''))
        for out, conn in e.get('io', []):
            print('    %s -> %s' % (out, conn))


if __name__ == '__main__':
    main()
