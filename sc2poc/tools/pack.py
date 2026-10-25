"""Pack every level into one SC2 map, overlapping them where their terrain does not clash.

SC2's terrain is one height per vertex and cannot change while the game runs, so levels with real floor
heights each need their own terrain. Levels may still overlap: a vertex constrains the terrain only when
one of a level's deck, drop or void cells touches it (tools/heights.py). Hull is covered by the kit's wall
caps, so whatever height lies under it does not show. Two levels can share a vertex when at most one of
them constrains it, or both want the same height there.

Each level may also be lifted or lowered as a whole (its heights only matter relative to each other), which
lets a flat level sit on another level's main floor.

When the levels do not fit without clashes, place(clash=...) lets a level land where some of its
constrained vertices clash: the level placed first keeps its height there, and check() measures what
the others lose.

    py tools/pack.py --campaign [--png out.png]     fit Alien Swarm's whole campaign (tools/asdata/) in 256x256:
                                                    without clashes if it can, else the fewest of several orders

The build (build.py) packs the levels it has with pack().
"""
from pathlib import Path
import argparse, sys
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

MAX = 256          # SC2's largest map
STEP = 8           # map sizes are multiples of 8 (terrain texture blocks)
Q = 16             # heights compare equal to 1/16 of a unit (5 Hammer units)


def _corr(big, small):
    """Valid correlation: out[oy, ox] = sum(big[oy:oy+h, ox:ox+w] * small)."""
    H, W = big.shape
    h, w = small.shape
    fh, fw = H + h, W + w
    F = np.fft.rfft2(big, (fh, fw)) * np.conj(np.fft.rfft2(small, (fh, fw)))
    full = np.fft.irfft2(F, (fh, fw))
    return np.rint(full[:H - h + 1, :W - w + 1]).astype(np.int64)


def _keys(h):
    return np.rint(h * Q).astype(np.int64)


def _conflicts(occ_mask, occ_key, mask, key):
    """Clashing vertices for every placement of the level's vertex grid in the map's."""
    total = _corr(occ_mask.astype(float), mask.astype(float))
    same = np.zeros_like(total)
    for k in np.unique(key[mask]):
        a = mask & (key == k)
        b = occ_mask & (occ_key == k)
        if b.any():
            same += _corr(b.astype(float), a.astype(float))
    return total - same


def _shifts(level, base):
    """Whole-level lifts to try: none, then each of its most common heights moved onto the base height; none that
    takes a pit's floor below SC2's lowest terrain or a gallery over its highest (build.py checks 0 .. 250)."""
    v = level['vert'][level['vmask']]
    u, n = np.unique(np.rint(v * Q) / Q, return_counts=True)
    out = [0.0] + [base - h for h in u[np.argsort(-n)][:6]]
    out = [s for s in out if v.min() + s >= 0.0 and v.max() + s < 250.0]
    return list(dict.fromkeys(round(s, 6) for s in out))


def place(levels, MW, MH, base, order=None, clash=0):
    """Bottom-left placement in this map size, or None. Each level: dict(w, h, vert[h+1, w+1], vmask).
    With clash > 0 a level may land where up to that many of its constrained vertices clash with levels
    placed before it (the fewest clashes wins); those vertices keep the earlier level's height.
    Returns [(ox, oy, lift, clashes)] in the levels' own order."""
    occ_mask = np.zeros((MH + 1, MW + 1), bool)
    occ_key = np.zeros((MH + 1, MW + 1), np.int64)
    out = [None] * len(levels)
    order = order or sorted(range(len(levels)), key=lambda i: -levels[i]['vmask'].sum())
    for i in order:
        lv = levels[i]
        if lv['w'] > MW or lv['h'] > MH:
            return None
        best = None
        for dz in _shifts(lv, base):
            key = _keys(lv['vert'] + dz)
            bad = _conflicts(occ_mask, occ_key, lv['vmask'], key)
            m = int(bad.min())
            if m > clash:
                continue
            oy, ox = np.argwhere(bad == m)[0]          # bottom row first, then left
            if best is None or m < best[0]:
                best = (m, int(ox), int(oy), dz, key)
            if m == 0:
                break
        if best is None:
            return None
        m, ox, oy, dz, key = best
        h1, w1 = lv['vmask'].shape
        sub = (slice(oy, oy + h1), slice(ox, ox + w1))
        take = lv['vmask'] & ~occ_mask[sub]
        occ_key[sub] = np.where(take, key, occ_key[sub])
        occ_mask[sub] |= lv['vmask']
        out[i] = (ox, oy, dz, m)
    return out, order


def pack(levels, base=8.0, min_size=(0, 0), clash=0, sizes=None):
    """The smallest map (by area, then squareness) holding every level: dict(size, places, order, terrain)."""
    minW = max([lv['w'] for lv in levels] + [min_size[0]])
    minH = max([lv['h'] for lv in levels] + [min_size[1]])
    up = lambda n: -(-n // STEP) * STEP
    sizes = sizes or sorted({(w, h) for w in range(up(minW), MAX + 1, STEP) for h in range(up(minH), MAX + 1, STEP)},
                            key=lambda s: (s[0] * s[1], abs(s[0] - s[1])))
    # A width that failed at some height fails at every smaller one.
    tried_fail = {}
    for MW, MH in sizes:
        if tried_fail.get(MW, 0) >= MH:
            continue
        # Biggest first, bottom-left, as a rule; when that leaves no room, the levels in their own (campaign) order
        # and in reverse, which can fit where the rule does not.
        got = None
        for order in (None, list(range(len(levels))), list(range(len(levels)))[::-1]):
            got = place(levels, MW, MH, base, order=order, clash=clash)
            if got is not None:
                break
        if got is None:
            tried_fail[MW] = max(tried_fail.get(MW, 0), MH)
            continue
        places, order = got
        return {'size': (MW, MH), 'places': places, 'order': order,
                'terrain': terrain(levels, places, order, MW, MH, base)}
    # Last, the biggest map with several rules for where each level goes, backtracking when a level finds no room.
    for order in (None, list(range(len(levels))), list(range(len(levels)))[::-1]):
        got = search(levels, MAX, MAX, base, order=order)
        if got is not None:
            places, order = got
            return {'size': (MAX, MAX), 'places': places, 'order': order,
                    'terrain': terrain(levels, places, order, MAX, MAX, base)}
    raise SystemExit('the levels do not fit one %dx%d map, even overlapped' % (MAX, MAX))


# Where a level may go among the spots where nothing clashes: the lowest row's leftmost (place()'s rule), the
# top-right corner, the leftmost column's lowest, and the other corners.
RULES = ('bl', 'tr', 'lb', 'rt', 'tl', 'br')


def _spot(bad, rule):
    ys, xs = np.nonzero(bad == 0)
    k = {'bl': (xs, ys), 'tr': (-xs, -ys), 'lb': (ys, xs), 'rt': (-ys, -xs), 'tl': (xs, -ys), 'br': (-xs, ys)}[rule]
    i = np.lexsort(k)[0]
    return int(xs[i]), int(ys[i])


def search(levels, MW, MH, base, order=None):
    """place() without clashes, trying each of RULES for each level in turn and backing up when one has no room
    left: (places, order) or None. Six levels where bottom-left alone leaves none for the last."""
    order = order or sorted(range(len(levels)), key=lambda i: -levels[i]['vmask'].sum())
    out = [None] * len(levels)

    def go(d, occ_mask, occ_key):
        if d == len(order):
            return True
        lv = levels[order[d]]
        if lv['w'] > MW or lv['h'] > MH:
            return False
        tried = set()
        for dz in _shifts(lv, base):
            key = _keys(lv['vert'] + dz)
            bad = _conflicts(occ_mask, occ_key, lv['vmask'], key)
            if bad.min() > 0:
                continue
            for rule in RULES:
                ox, oy = _spot(bad, rule)
                if (ox, oy, dz) in tried:
                    continue
                tried.add((ox, oy, dz))
                h1, w1 = lv['vmask'].shape
                sub = (slice(oy, oy + h1), slice(ox, ox + w1))
                mask, keys = occ_mask.copy(), occ_key.copy()
                keys[sub] = np.where(lv['vmask'] & ~mask[sub], key, keys[sub])
                mask[sub] |= lv['vmask']
                out[order[d]] = (ox, oy, dz, 0)
                if go(d + 1, mask, keys):
                    return True
        return False

    if go(0, np.zeros((MH + 1, MW + 1), bool), np.zeros((MH + 1, MW + 1), np.int64)):
        return out, order
    return None


def terrain(levels, places, order, MW, MH, base):
    """Vertex heights [MH+1, MW+1]: each level's constrained vertices (the first placed wins a clash);
    elsewhere the first level whose rectangle covers the vertex (its hull heights); elsewhere the base height."""
    t = np.full((MH + 1, MW + 1), base)
    filled = np.zeros_like(t, bool)
    for i in order:
        lv, (ox, oy, dz, _) = levels[i], places[i]
        h1, w1 = lv['vmask'].shape
        sub = (slice(oy, oy + h1), slice(ox, ox + w1))
        take = lv['vmask'] & ~filled[sub]
        t[sub] = np.where(take, lv['vert'] + dz, t[sub])
        filled[sub] |= lv['vmask']
    soft = filled.copy()
    for i in order:
        lv, (ox, oy, dz, _) = levels[i], places[i]
        h1, w1 = lv['vmask'].shape
        sub = (slice(oy, oy + h1), slice(ox, ox + w1))
        take = ~soft[sub]
        t[sub] = np.where(take, lv['vert'] + dz, t[sub])
        soft[sub] |= take
    return t


def check(levels, places, t):
    """Per level: (constrained vertices whose terrain is not the level's own height, the largest such error)."""
    out = []
    for lv, (ox, oy, dz, _) in zip(levels, places):
        h1, w1 = lv['vmask'].shape
        got = t[oy:oy + h1, ox:ox + w1][lv['vmask']]
        err = np.abs(got - (lv['vert'] + dz)[lv['vmask']])
        out.append((int((err > 1.0 / Q).sum()), float(err.max()) if len(err) else 0.0))
    return out


# ---- the whole campaign, from the real maps --------------------------------------------------------------
def campaign_levels(margin=6, units=80.0, deck_z=832.0, base=8.0):
    """Each campaign map as a port level would be: its walkable floor in 80-unit cells, framed by `margin`
    cells of hull, heights as tools/heights.py makes them."""
    from tools import asextract
    out = []
    for name in asextract.CAMPAIGN:
        d = asextract.load(name)
        wz, pct = d['walk_z'], d['walk_pct']
        # 40-unit cells to 80: a cell is deck when at least half of it is walkable.
        H2, W2 = wz.shape[0] // 2, wz.shape[1] // 2
        p = pct[:H2 * 2, :W2 * 2].reshape(H2, 2, W2, 2).astype(float).mean((1, 3))
        z = wz[:H2 * 2, :W2 * 2].reshape(H2, 2, W2, 2)
        with np.errstate(all='ignore'):
            z = np.nanmedian(z.transpose(0, 2, 1, 3).reshape(H2, W2, 4), -1)
        deck = np.pad(_components((p >= 50) & ~np.isnan(z), 12), margin)
        z = np.pad(np.nan_to_num(z), margin)
        ys, xs = np.nonzero(deck)
        deck_c = deck[ys.min() - margin:ys.max() + 1 + margin, xs.min() - margin:xs.max() + 1 + margin]
        z_c = z[ys.min() - margin:ys.max() + 1 + margin, xs.min() - margin:xs.max() + 1 + margin]
        from tools import heights
        zz = np.where(deck_c, base + (np.round(z_c / heights.SNAP) * heights.SNAP - deck_z) / units, base)
        hv = _vertices(zz, deck_c)
        # The main floor (the commonest height) goes onto the base height; the rest keeps its height above it.
        u, n = np.unique(np.rint(hv[0][hv[1]] * Q) / Q, return_counts=True)
        hv = (np.where(hv[1], hv[0] + base - u[n.argmax()], base), hv[1])
        zz = zz + base - u[n.argmax()]
        out.append({'name': name, 'w': deck_c.shape[1], 'h': deck_c.shape[0], 'vert': hv[0], 'vmask': hv[1],
                    'deck': int(deck_c.sum()), 'spread': float(np.ptp(zz[deck_c]))})
    return out


def _vertices(z, deck):
    H, W = z.shape
    vert = np.zeros((H + 1, W + 1))
    vmask = np.zeros((H + 1, W + 1), bool)
    zp = np.pad(np.where(deck, z, 0.0), 1)
    dp = np.pad(deck, 1).astype(float)
    s = zp[:-1, :-1] * dp[:-1, :-1] + zp[:-1, 1:] * dp[:-1, 1:] + zp[1:, :-1] * dp[1:, :-1] + zp[1:, 1:] * dp[1:, 1:]
    n = dp[:-1, :-1] + dp[:-1, 1:] + dp[1:, :-1] + dp[1:, 1:]
    vmask = n > 0
    vert = np.where(vmask, s / np.maximum(n, 1), 8.0)
    return vert, vmask


def _components(mask, smallest):
    """The mask without its 4-connected pieces smaller than `smallest` cells (nav nodes on walls, lone ledges)."""
    from collections import deque
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--campaign', action='store_true', help='pack the seven campaign maps from tools/asdata/')
    ap.add_argument('--png', help='write the packed footprints to this image')
    ap.add_argument('--tries', type=int, default=24, help='placement orders to try')
    args = ap.parse_args()
    if not args.campaign:
        ap.print_help()
        return
    levels = campaign_levels()
    for lv in levels:
        print('%-26s %3d x %3d cells, %5d deck cells, heights spread %.2f units' % (lv['name'], lv['w'], lv['h'], lv['deck'], lv['spread']))
    print('side by side, without overlap: %d cells of %d' % (sum(lv['w'] * lv['h'] for lv in levels), MAX * MAX))
    strict = place(levels, MAX, MAX, 8.0)
    print('without clashes in %dx%d: %s' % (MAX, MAX, 'fits' if strict else 'does not fit'))
    rng = np.random.default_rng(7)
    first = sorted(range(len(levels)), key=lambda i: -levels[i]['vmask'].sum())
    orders = [first] + [list(rng.permutation(len(levels))) for _ in range(args.tries - 1)]
    best = None
    for order in orders:
        got = place(levels, MAX, MAX, 8.0, order=[int(i) for i in order], clash=10 ** 9)
        if got is None:
            continue
        places, order = got
        total = sum(c for *_, c in places)
        if best is None or total < best[0]:
            best = (total, places, order)
    total, places, order = best
    t = terrain(levels, places, order, MAX, MAX, 8.0)
    print('best of %d orders in %dx%d: %d clashing vertices' % (len(orders), MAX, MAX, total))
    for lv, (ox, oy, dz, c), (n, worst) in zip(levels, places, check(levels, places, t)):
        print('  %-26s origin (%3d, %3d)  lift %+6.2f  %4d of %5d floor vertices take another level\'s height (%.1f%%), worst %.2f units = %d Hammer units'
              % (lv['name'], ox, oy, dz, n, lv['vmask'].sum(), 100.0 * n / lv['vmask'].sum(), worst, round(worst * 80)))
    if args.png:
        from PIL import Image
        img = np.zeros((MAX, MAX, 3), np.uint8)
        colours = [(230, 90, 70), (90, 170, 230), (120, 210, 90), (230, 200, 70), (200, 110, 220), (80, 220, 200), (240, 150, 60)]
        for lv, (ox, oy, dz, _), c in zip(levels, places, colours):
            cells = lv['vmask'][:-1, :-1] & lv['vmask'][1:, 1:]
            region = img[oy:oy + lv['h'], ox:ox + lv['w']]
            region[cells] = np.clip(region[cells] * 0.5 + np.array(c) * 0.6, 0, 255).astype(np.uint8)
        Image.fromarray(img[::-1]).resize((MAX * 3, MAX * 3), Image.NEAREST).save(args.png)
        print('wrote', args.png)


if __name__ == '__main__':
    main()
