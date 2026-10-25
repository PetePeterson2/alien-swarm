"""A level too long for the room the packed map has left, cut at a few corridors into pieces that sit apart in the
map (tools/pack.py), and the seams that join them again in play.

A cut is ('x' or 'y', line, lo, hi): the boundary in front of column (or row) `line`, across rows (columns) lo..hi-1.
Each piece takes its own cells and, past every cut it meets, `overlap` cells more of the corridor beyond (a band,
cut short at a door): from inside a piece the corridor is seen going on, and a unit that walks half a cell past the
line is moved to the same spot in the piece beyond (src/Seams.galaxy), which is laid out the same there.

    S = Seams(cells, CUTS, OVERLAP, PLACES)   cells: the level's deck and drop, bool[H, W], in its own coordinates
    S.grid(a, fill)      a cell table moved into the packed layout (every copy of a band)
    S.point(x, y)        a point moved with the piece it lies in
    S.copies(x, y)       the point in every piece that shows it (lamps, dressing)
    S.rect(r)            a rectangle moved with the piece its middle lies in
    S.seams()            the crossings for src/Seams.galaxy
"""
from collections import deque

import numpy as np


def _label(cells, cuts):
    """Pieces of `cells` (4-connected) with the cuts' boundaries closed; int[H, W], -1 off the cells."""
    H, W = cells.shape
    shut_y = np.zeros((H + 1, W), bool)      # shut_y[y, x]: no step between rows y-1 and y at column x
    shut_x = np.zeros((H, W + 1), bool)
    for ax, ln, lo, hi in cuts:
        if ax == 'y':
            shut_y[ln, lo:hi] = True
        else:
            shut_x[lo:hi, ln] = True
    lab = np.full((H, W), -1, int)
    n = 0
    for y0, x0 in zip(*np.nonzero(cells)):
        if lab[y0, x0] >= 0:
            continue
        lab[y0, x0] = n
        q = deque([(y0, x0)])
        while q:
            y, x = q.popleft()
            for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                ny, nx = y + dy, x + dx
                if not (0 <= ny < H and 0 <= nx < W) or not cells[ny, nx] or lab[ny, nx] >= 0:
                    continue
                if dy and shut_y[max(y, ny), x] or dx and shut_x[y, max(x, nx)]:
                    continue
                lab[ny, nx] = n
                q.append((ny, nx))
        n += 1
    return lab, n


class Seams:
    def __init__(self, cells, cuts, overlap, places, doors=(), smallest=40, margin=2):
        self.cells, self.cuts, self.overlap = cells, cuts, overlap
        H, W = cells.shape
        lab, n = _label(cells, cuts)
        sizes = np.bincount(lab[lab >= 0], minlength=n)
        # The big pieces in order from the south-west; a scrap the cuts or the trace left on its own joins the
        # piece nearest it.
        big = sorted((k for k in range(n) if sizes[k] >= smallest),
                     key=lambda k: (np.nonzero(lab == k)[0].min(), np.nonzero(lab == k)[1].min()))
        own = np.full((H, W), -1, int)
        for i, k in enumerate(big):
            own[lab == k] = i
        ys, xs = np.nonzero(own >= 0)
        for y, x in zip(*np.nonzero(cells & (own < 0))):
            j = np.argmin((ys - y) ** 2 + (xs - x) ** 2)
            own[y, x] = own[ys[j], xs[j]]
        self.own, self.n = own, len(big)
        assert len(places) == self.n, 'cuts give %d pieces, %d places' % (self.n, len(places))
        # Each piece's region: its own cells and the band past each cut it meets.
        region = [own == i for i in range(self.n)]
        self.links = []           # (cut, low-side piece, high-side piece)
        self.bands = []           # (down, up): the low side's band runs up to `up`, the high side's down to `down`
        for c, (ax, ln, lo, hi) in enumerate(cuts):
            if ax == 'y':
                low, high = own[ln - 1, lo:hi], own[ln, lo:hi]
            else:
                low, high = own[lo:hi, ln - 1], own[lo:hi, ln]
            pairs = {(a, b) for a, b in zip(low, high) if a >= 0 and b >= 0 and a != b}
            assert len(pairs) == 1, 'cut %s does not part two pieces: %s' % ((ax, ln, lo, hi), pairs)
            a, b = pairs.pop()
            self.links.append((c, a, b))
            # Each side's band, cut short at the first door in it.
            up, down = ln + overlap, ln - overlap
            for _, (x0, y0, x1, y1), *_ in doors:
                if ax == 'y' and x1 > lo and x0 < hi or ax == 'x' and y1 > lo and y0 < hi:
                    d0, d1 = (y0, y1) if ax == 'y' else (x0, x1)
                    if d0 >= ln:
                        up = min(up, d0)
                    elif d1 <= ln:
                        down = max(down, d1)
            self.bands.append((down, up))
            for side, (s0, s1) in ((a, (ln, up)), (b, (down, ln))):
                box = np.zeros((H, W), bool)
                if ax == 'y':
                    box[s0:s1, lo:hi] = True
                else:
                    box[lo:hi, s0:s1] = True
                other = b if side == a else a
                seed = np.zeros((H, W), bool)
                if ax == 'y':
                    row = ln if side == a else ln - 1
                    seed[row, lo:hi] = own[row, lo:hi] == other
                else:
                    col = ln if side == a else ln - 1
                    seed[lo:hi, col] = own[lo:hi, col] == other
                region[side] |= _grow(seed & box, cells & box)
        self.region = region
        # Where each piece goes: places are its region's corner (lower left) in the packed layout.
        corners = []
        for r in region:
            ys, xs = np.nonzero(r)
            corners.append((xs.min(), ys.min()))
        shift = [(px - cx, py - cy) for (cx, cy), (px, py) in zip(corners, places)]
        lo_x = min(min(np.nonzero(r)[1]) + dx for r, (dx, dy) in zip(region, shift))
        lo_y = min(min(np.nonzero(r)[0]) + dy for r, (dx, dy) in zip(region, shift))
        self.shift = [(int(dx - lo_x + margin), int(dy - lo_y + margin)) for dx, dy in shift]
        self.origin = (int(lo_x - margin), int(lo_y - margin))     # the packed layout's cell 0, as a place in the map
        self.W = int(max(max(np.nonzero(r)[1]) + dx for r, (dx, dy) in zip(region, self.shift)) + 1 + margin)
        self.H = int(max(max(np.nonzero(r)[0]) + dy for r, (dx, dy) in zip(region, self.shift)) + 1 + margin)
        taken = np.zeros((self.H, self.W), int)
        for r, (dx, dy) in zip(region, self.shift):
            ys, xs = np.nonzero(r)
            taken[ys + dy, xs + dx] += 1
        assert taken.max() <= 1, 'pieces overlap in the packed layout'

    # ---- moving things into the layout
    def grid(self, a, fill):
        a = np.asarray(a)
        out = np.full((self.H, self.W) + a.shape[2:], fill, dtype=a.dtype)
        for r, (dx, dy) in zip(self.region, self.shift):
            ys, xs = np.nonzero(r)
            out[ys + dy, xs + dx] = a[ys, xs]
        return out

    def piece(self, x, y):
        """The piece a point lies in: the cell's own, or the nearest cell's."""
        H, W = self.own.shape
        ix, iy = min(max(int(x), 0), W - 1), min(max(int(y), 0), H - 1)
        if self.own[iy, ix] >= 0:
            return self.own[iy, ix]
        ys, xs = np.nonzero(self.own >= 0)
        j = np.argmin((ys + 0.5 - y) ** 2 + (xs + 0.5 - x) ** 2)
        return self.own[ys[j], xs[j]]

    def point(self, x, y):
        dx, dy = self.shift[self.piece(x, y)]
        return (x + dx, y + dy)

    def copies(self, x, y):
        H, W = self.own.shape
        ix, iy = int(x), int(y)
        out = [(x + dx, y + dy) for r, (dx, dy) in zip(self.region, self.shift) if 0 <= ix < W and 0 <= iy < H and r[iy, ix]]
        return out or [self.point(x, y)]

    def rect(self, r):
        x0, y0, x1, y1 = r
        dx, dy = self.shift[self.piece((x0 + x1) / 2, (y0 + y1) / 2)]
        return (x0 + dx, y0 + dy, x1 + dx, y1 + dy)

    def rect_copies(self, r):
        """The rectangle in every piece whose region holds all of its cells (a stair flight seen down a band)."""
        x0, y0, x1, y1 = r
        out = []
        for reg, (dx, dy) in zip(self.region, self.shift):
            mine = reg[y0:y1, x0:x1] | ~self.cells[y0:y1, x0:x1]
            if (reg[y0:y1, x0:x1]).any() and mine.all():
                out.append((x0 + dx, y0 + dy, x1 + dx, y1 + dy))
        return out or [self.rect(r)]

    def source(self):
        """For each cell of the layout, the level cell it shows: (x, y) int[H, W], -1 for none."""
        sx = np.full((self.H, self.W), -1, int)
        sy = np.full((self.H, self.W), -1, int)
        for r, (dx, dy) in zip(self.region, self.shift):
            ys, xs = np.nonzero(r)
            sx[ys + dy, xs + dx] = xs
            sy[ys + dy, xs + dx] = ys
        return sx, sy

    # ---- the crossings
    def seams(self):
        """(x0, y0, x1, y1, dx, dy, piece, to, gx, gy) in the layout: a unit of `piece` inside the rectangle (the
        band past the line, from half a cell on) is moved by (dx, dy) into piece `to`; (gx, gy) is where a unit of
        `piece` walks to cross (the corridor's middle, a cell past the line)."""
        out = []
        for c, a, b in self.links:
            ax, ln, lo, hi = self.cuts[c]
            down, up = self.bands[c]
            for side, other, sgn in ((a, b, 1), (b, a, -1)):
                (sx, sy), (ox, oy) = self.shift[side], self.shift[other]
                if ax == 'y':
                    cols = [x for x in range(lo, hi) if self.cells[ln - 1, x] and self.cells[ln, x]]
                    gx = (min(cols) + max(cols) + 1) / 2
                    y0, y1 = (ln + 0.5, up) if sgn > 0 else (down, ln - 0.5)
                    rect = (min(cols), y0, max(cols) + 1, y1)
                    go = (gx, ln + sgn * 1.0)
                else:
                    rows = [y for y in range(lo, hi) if self.cells[y, ln - 1] and self.cells[y, ln]]
                    gy = (min(rows) + max(rows) + 1) / 2
                    x0, x1 = (ln + 0.5, up) if sgn > 0 else (down, ln - 0.5)
                    rect = (x0, min(rows), x1, max(rows) + 1)
                    go = (ln + sgn * 1.0, gy)
                out.append((rect[0] + sx, rect[1] + sy, rect[2] + sx, rect[3] + sy, ox - sx, oy - sy, side, other,
                            go[0] + sx, go[1] + sy))
        return out

    def piece_rows(self):
        """Each layout row as a string of piece digits, every cell (hull too) the piece nearest it."""
        near = np.full((self.H, self.W), -1, int)
        for i, (r, (dx, dy)) in enumerate(zip(self.region, self.shift)):
            ys, xs = np.nonzero(r)
            near[ys + dy, xs + dx] = i
        seeds = near.copy()
        while (seeds < 0).any():
            grow = seeds.copy()
            for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                sh = np.roll(seeds, (dy, dx), (0, 1))
                grow = np.where(grow < 0, sh, grow)
            seeds = grow
        return [''.join(str(v) for v in row) for row in seeds]

    def next_hop(self):
        """next[a][b]: the seam (index into seams()) a unit in piece a takes toward piece b, -1 when a == b."""
        crossings = self.seams()
        nxt = [[-1] * self.n for _ in range(self.n)]
        for a in range(self.n):
            first = {a: -1}
            q = deque([a])
            while q:
                p = q.popleft()
                for s, cr in enumerate(crossings):
                    if cr[6] == p and cr[7] not in first:
                        first[cr[7]] = s if p == a else first[p]
                        q.append(cr[7])
            for b in range(self.n):
                nxt[a][b] = first.get(b, -1)
        return nxt


def _grow(seed, within):
    out = seed.copy()
    while True:
        g = out.copy()
        g[1:] |= out[:-1]
        g[:-1] |= out[1:]
        g[:, 1:] |= out[:, :-1]
        g[:, :-1] |= out[:, 1:]
        g &= within
        if (g == out).all():
            return out
        out = g
