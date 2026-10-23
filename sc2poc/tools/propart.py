"""Alien Swarm's own dressing, drawn from scratch: green supply crates, grey metal crates, toxic barrels.

After swarm_supplycrateskin, metalcrate and swarm_bigtoxicbarrelskin in its VPKs (looked at for
palette and markings only). Each prop is a kit piece (KP*) laid by the script like a decal
(AS_KitDecal), origin at its footprint's centre on the deck.
"""
import math

import numpy as np
from PIL import Image, ImageDraw

from tools.shipkit import _noise, _img
from tools.deckart import _font

T = 256


def _edges(a, w=10, dark=0.5, lite=1.25):
    a[:w] *= lite; a[-w:] *= dark; a[:, :w] *= lite; a[:, -w:] *= dark
    a[w:w + 2] *= 0.6; a[-w - 2:-w] *= 0.6; a[:, w:w + 2] *= 0.6; a[:, -w - 2:-w] *= 0.6


def _stencil(a, text, y, size, ink):
    lab = Image.new('L', (T, size + 10), 0)
    ImageDraw.Draw(lab).text((T / 2, (size + 10) / 2), text, font=_font(size), fill=255, anchor='mm')
    m = np.asarray(lab).astype(float)[..., None] / 255
    a[y:y + size + 10] = a[y:y + size + 10] * (1 - m) + np.array(ink, float) * m


def tex_crate_green(seed=41, top=False):
    """swarm_supplycrateskin: olive-green painted panel, a pale frame, a worn yellow stripe and a stencil."""
    a = np.array((84, 104, 66), float)[None, None] * (0.85 + 0.3 * _noise(0, 30, seed, 4, (T, T))[..., None])
    _edges(a, 14)
    if top:
        a[T // 2 - 18:T // 2 + 18, 60:T - 60] *= 0.6
        a[T // 2 - 10:T // 2 + 10, 70:T - 70] = (40, 42, 40)
    else:
        a[150:170, 14:T - 14] = np.array((200, 170, 50)) * (0.8 + 0.3 * _noise(0, 8, seed + 1, 2, (20, T - 28))[..., None])
        _stencil(a, 'SynTek', 60, 34, (220, 224, 210))
        _stencil(a, 'SUPPLY', 100, 20, (200, 204, 190))
    a *= (1 - 0.3 * np.clip(_noise(0, 40, seed + 2, 4, (T, T)) - 0.55, 0, 1) * 3)[..., None]
    return _img(a)


def tex_crate_metal(seed=42, top=False):
    """metalcrate: grey steel with corner brackets, a NOTICE plate and a purple band."""
    a = np.array((132, 136, 138), float)[None, None] * (0.85 + 0.25 * _noise(0, 30, seed, 4, (T, T))[..., None])
    _edges(a, 12)
    for cx, cy in ((0, 0), (T - 40, 0), (0, T - 40), (T - 40, T - 40)):
        a[cy:cy + 40, cx:cx + 40] *= 0.72
    if not top:
        a[170:182, 30:T - 30] = (92, 80, 150)
        a[60:130, 70:T - 70] = (210, 210, 200)
        _stencil(a, 'NOTICE', 64, 20, (40, 60, 160))
        _stencil(a, 'WARNING', 96, 20, (180, 140, 20))
    else:
        a[T // 2 - 30:T // 2 + 30, T // 2 - 30:T // 2 + 30] *= 0.7
    return _img(a)


def tex_barrel(seed=43):
    """swarm_bigtoxicbarrelskin, unrolled: yellow drum, ribs, a black hazard band and a trefoil-ish mark."""
    w, h = 512, 256
    a = np.array((214, 170, 40), float)[None, None] * (0.85 + 0.25 * _noise(0, 30, seed, 4, (h, w))[..., None])
    for y in (36, 128, 220):
        a[y - 6:y + 6] *= 0.7; a[y - 6:y - 3] *= 1.3
    a[70:100] = (30, 28, 26)
    yy, xx = np.mgrid[0:h, 0:w]
    for cx in (128, 384):
        d = np.hypot(xx - cx, yy - 170)
        ring = (d > 20) & (d < 34)
        a[ring] = (30, 28, 26); a[d < 9] = (30, 28, 26)
    a *= (1 - 0.35 * np.clip(_noise(0, 30, seed + 2, 4, (h, w)) - 0.5, 0, 1) * 3)[..., None]
    a *= (1 - 0.4 * np.clip((yy - h * 0.75) / (h * 0.25), 0, 1) ** 2)[..., None]
    return _img(a)


def tex_barrel_top(seed=44):
    a = np.array((70, 66, 58), float)[None, None] * (0.85 + 0.3 * _noise(0, 20, seed, 3, (T, T))[..., None])
    yy, xx = np.mgrid[0:T, 0:T]
    d = np.hypot(xx - T / 2, yy - T / 2) / (T / 2)
    a[(d > 0.86) & (d < 0.98)] *= 1.6
    a[np.hypot(xx - T * 0.68, yy - T * 0.4) < 14] = (40, 38, 34)
    return _img(a)


def tex_column(seed=45):
    """A wall strut: dark steel channel with rivets, a lit edge and a hazard-striped foot (row 0 the top)."""
    w, h = 128, 640
    a = np.array((96, 102, 108), float)[None, None] * (0.85 + 0.25 * _noise(0, 20, seed, 3, (h, w))[..., None])
    a[:, :10] *= 1.35; a[:, -10:] *= 0.55
    a[:, 54:74] *= 0.75
    for y in range(30, h - 80, 46):
        for x in (24, w - 28):
            a[y:y + 6, x:x + 6] = (150, 152, 154)
    yy, xx = np.mgrid[0:70, 0:w]
    stripe = ((xx + yy) // 14) % 2 == 0
    a[h - 80:h - 10] = np.where(stripe[..., None], np.array((206, 160, 34), float), np.array((28, 26, 24), float))
    a[h - 10:] *= 0.35
    a[:18] *= 0.5
    return _img(a)


TEXTURES = {
    'prop_column': lambda: (tex_column(), None),
    'prop_crate_green': lambda: (tex_crate_green(), None), 'prop_crate_green_top': lambda: (tex_crate_green(top=True), None),
    'prop_crate_metal': lambda: (tex_crate_metal(), None), 'prop_crate_metal_top': lambda: (tex_crate_metal(top=True), None),
    'prop_barrel': lambda: (tex_barrel(), None), 'prop_barrel_top': lambda: (tex_barrel_top(), None),
}


def textures():
    return {k: f() for k, f in TEXTURES.items()}


def _box(m, side, top, sx, sy, sz, z0=0.0):
    a, b = sx / 2, sy / 2
    key, kt = (side, False, 0), (top, False, 0)
    c = [(-a, -b), (a, -b), (a, b), (-a, b)]
    for i in range(4):
        (x0, y0), (x1, y1) = c[i], c[(i + 1) % 4]
        m.quad(key, (x0, y0, z0), (x1, y1, z0), (x1, y1, z0 + sz), (x0, y0, z0 + sz), [(0, 1), (1, 1), (1, 0), (0, 0)])
    m.quad(kt, (-a, -b, z0 + sz), (a, -b, z0 + sz), (a, b, z0 + sz), (-a, b, z0 + sz), [(0, 1), (1, 1), (1, 0), (0, 0)])


def _barrel(m, r=0.3, hgt=0.85, n=14):
    key, kt = ('prop_barrel', False, 0), ('prop_barrel_top', False, 0)
    for i in range(n):
        t0, t1 = 2 * math.pi * i / n, 2 * math.pi * (i + 1) / n
        p0, p1 = (r * math.cos(t0), r * math.sin(t0)), (r * math.cos(t1), r * math.sin(t1))
        u0, u1 = i / n, (i + 1) / n
        m.quad(key, (p0[0], p0[1], 0), (p1[0], p1[1], 0), (p1[0], p1[1], hgt), (p0[0], p0[1], hgt), [(u0, 1), (u1, 1), (u1, 0), (u0, 0)])
    m.poly(kt, [(r * math.cos(2 * math.pi * i / n), r * math.sin(2 * math.pi * i / n), hgt) for i in range(n)],
           [(0.5 + 0.5 * math.cos(2 * math.pi * i / n), 0.5 - 0.5 * math.sin(2 * math.pi * i / n)) for i in range(n)])


def _column(m, w=0.34, d=0.22, hgt=2.5):
    """A strut standing proud of a wall that faces -Y: its face and sides out to y = -d, a cap on top."""
    a = w / 2
    key = ('prop_column', False, 0)
    m.quad(key, (-a, -d, 0), (a, -d, 0), (a, -d, hgt), (-a, -d, hgt), [(0.1, 1), (0.9, 1), (0.9, 0), (0.1, 0)])
    m.quad(key, (a, -d, 0), (a, 0, 0), (a, 0, hgt), (a, -d, hgt), [(0.0, 1), (0.25, 1), (0.25, 0), (0.0, 0)])
    m.quad(key, (-a, 0, 0), (-a, -d, 0), (-a, -d, hgt), (-a, 0, hgt), [(0.75, 1), (1.0, 1), (1.0, 0), (0.75, 0)])
    m.quad(('wall_trim', False, 0), (-a, -d, hgt + 0.013), (a, -d, hgt + 0.013), (a, 0.16, hgt + 0.013), (-a, 0.16, hgt + 0.013),
           [(0, 0), (1, 0), (1, 1), (0, 1)])


def pieces(out):
    """KPCol (a wall strut), KPCrateG / KPCrateM (one crate), KPCrateStack (two and one on top), KPBarrel, KPBarrels (a cluster of three)."""
    from tools.shipkit import ShipModel
    m = out['KPCol'] = ShipModel('KPCol', (0, 0, 0)); _column(m)
    m = out['KPCrateG'] = ShipModel('KPCrateG', (0, 0, 0)); _box(m, 'prop_crate_green', 'prop_crate_green_top', 1.1, 1.1, 0.9)
    m = out['KPCrateM'] = ShipModel('KPCrateM', (0, 0, 0)); _box(m, 'prop_crate_metal', 'prop_crate_metal_top', 0.9, 0.9, 0.8)
    m = out['KPCrateStack'] = ShipModel('KPCrateStack', (0, 0, 0))
    _box(m, 'prop_crate_green', 'prop_crate_green_top', 1.1, 1.1, 0.9)
    for p in m.parts.values():
        p['pos'] = [np.array(v) + (-0.6, 0, 0) for v in p['pos']]
    m2 = ShipModel('t', (0, 0, 0)); _box(m2, 'prop_crate_metal', 'prop_crate_metal_top', 0.9, 0.9, 0.8)
    m3 = ShipModel('t', (0, 0, 0)); _box(m3, 'prop_crate_green', 'prop_crate_green_top', 1.0, 1.0, 0.8, 0.9)
    for src, off in ((m2, (0.55, 0.05, 0)), (m3, (-0.55, 0.0, 0))):
        for key, p in src.parts.items():
            dst = m.parts.setdefault(key, dict(pos=[], nrm=[], uv=[], tri=[]))
            base = len(dst['pos'])
            dst['pos'].extend(np.array(v) + off for v in p['pos']); dst['nrm'].extend(p['nrm']); dst['uv'].extend(p['uv'])
            dst['tri'].extend((a + base, b + base, c + base) for a, b, c in p['tri'])
    m = out['KPBarrel'] = ShipModel('KPBarrel', (0, 0, 0)); _barrel(m)
    m = out['KPBarrels'] = ShipModel('KPBarrels', (0, 0, 0))
    for off in ((-0.33, -0.2), (0.33, -0.2), (0.0, 0.36)):
        b = ShipModel('t', (0, 0, 0)); _barrel(b)
        for key, p in b.parts.items():
            dst = m.parts.setdefault(key, dict(pos=[], nrm=[], uv=[], tri=[]))
            base = len(dst['pos'])
            dst['pos'].extend(np.array(v) + (off[0], off[1], 0) for v in p['pos']); dst['nrm'].extend(p['nrm']); dst['uv'].extend(p['uv'])
            dst['tri'].extend((a + base, b2 + base, c + base) for a, b2, c in p['tri'])
