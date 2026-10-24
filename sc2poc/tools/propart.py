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
    """A wall girder after Alien Swarm's landing bay: a yellow-painted steel web punched with a row of round
    lightening holes, dark flanges either side, paint chipped to bare metal at the edges and the foot
    (row 0 the top). The face is the middle 80% of the width, the flanges the outer tenths."""
    w, h = 128, 640
    r = np.random.default_rng(seed)
    a = np.array((214, 168, 40), float)[None, None] * (0.86 + 0.2 * _noise(0, 20, seed, 3, (h, w))[..., None])
    yy, xx = np.mgrid[0:h, 0:w]
    # Holes: a dark void with a lit lower rim and a shadowed upper one, every 92 px.
    for cy in range(70, h - 90, 92):
        d = np.hypot(xx - w / 2, yy - cy)
        hole = d < 26
        a[hole] = (18, 18, 20)
        rim = (d >= 26) & (d < 31)
        a[rim & (yy > cy)] *= 1.25; a[rim & (yy <= cy)] *= 0.55
    # Flanges: dark steel edges standing proud of the web.
    a[:, :13] = a[:, :13] * 0.35 + 30; a[:, -13:] = a[:, -13:] * 0.3 + 24
    a[:, 13:16] *= 1.3; a[:, -16:-13] *= 0.6
    # Chipped paint: bare grey metal where the noise says, more at the foot.
    chip = (_noise(0, 9, seed + 2, 3, (h, w)) + np.linspace(0, 0.25, h)[:, None]) > 0.82
    a[chip] = a[chip] * 0.3 + np.array((92, 94, 96)) * 0.7
    # Grime run down from each hole and a dark foot.
    for cy in range(70, h - 90, 92):
        a[cy + 30:cy + 90, int(w / 2) - 18:int(w / 2) + 18] *= np.linspace(0.75, 1.0, 60)[:, None, None]
    a[h - 40:] *= np.linspace(1.0, 0.45, 40)[:, None, None]
    a[:18] *= 0.5
    a *= (1 + 0.04 * r.standard_normal((h, w)))[..., None]
    return _img(a)


def tex_doorframe(seed=46):
    """swarm_bulkheaddoorframeskin: a dark steel beam with a band of yellow chevrons and bolted ends."""
    w, h = 512, 64
    a = np.array((84, 88, 92), float)[None, None] * (0.85 + 0.25 * _noise(0, 20, seed, 3, (h, w))[..., None])
    yy, xx = np.mgrid[0:h - 24, 0:w]
    stripe = ((xx + yy) // 14) % 2 == 0
    a[12:h - 12] = np.where(stripe[..., None], np.array((214, 166, 34), float), np.array((30, 28, 26), float))
    a[:12] *= 1.25; a[-12:] *= 0.6; a[10:12] *= 0.5; a[h - 12:h - 10] *= 0.5
    k = np.clip((_noise(0, 8, seed + 1, 3, (h, w)) - 0.7) * 5, 0, 1)[..., None]
    a = a * (1 - k) + np.array((96, 92, 86)) * k
    return _img(a)


def tex_doorpost(seed=47):
    """The frame's posts: dark steel with a lit edge, bolts and a small green status light (row 0 the top)."""
    w, h = 128, 640
    a = np.array((78, 82, 88), float)[None, None] * (0.85 + 0.25 * _noise(0, 20, seed, 3, (h, w))[..., None])
    a[:, :12] *= 1.4; a[:, -12:] *= 0.5
    for y in range(40, h - 40, 60):
        a[y:y + 8, 50:58] = (150, 150, 150)
    a[300:330, 40:88] = (30, 32, 34)
    emis = np.zeros((h, w, 3))
    a[306:324, 48:80] = (60, 255, 120); emis[306:324, 48:80] = (40, 230, 90)
    return _img(a), _img(emis)


def tex_ammo(seed=48, top=False):
    """Alien Swarm's ammo supply case: olive-grey steel, a yellow band, an AMMO stencil and rounds; the lid
    carries a green status strip that glows (emissive) so the crate is found in the dark."""
    a = np.array((96, 102, 88), float)[None, None] * (0.85 + 0.25 * _noise(0, 24, seed, 3, (T, T))[..., None])
    _edges(a, 12)
    emis = np.zeros((T, T, 3))
    if top:
        a[T // 2 - 10:T // 2 + 10, 30:T - 30] = (40, 42, 40)
        a[T // 2 - 5:T // 2 + 5, 40:T - 40] = (90, 255, 120); emis[T // 2 - 5:T // 2 + 5, 40:T - 40] = (50, 230, 90)
        for cx in (40, T - 52):
            a[30:60, cx:cx + 12] *= 0.6; a[T - 60:T - 30, cx:cx + 12] *= 0.6
    else:
        a[30:56, 12:T - 12] = (206, 164, 40)
        _stencil(a, 'AMMO', 90, 46, (226, 214, 160))
        for k in range(6):
            x = 50 + k * 28
            a[176:226, x:x + 14] = (190, 150, 60); a[168:178, x + 2:x + 12] = (150, 110, 60)
    return _img(a), (_img(emis) if top else None)


def tex_locker(seed=49):
    """swarm_lockerskin: a pair of tall grey-blue locker doors with vents, handles and name strips (row 0 the top)."""
    w, h = 256, 512
    a = np.array((104, 118, 132), float)[None, None] * (0.85 + 0.25 * _noise(0, 24, seed, 3, (h, w))[..., None])
    a[:, w // 2 - 3:w // 2 + 3] *= 0.4
    a[:, :6] *= 1.3; a[:, -6:] *= 0.5; a[:8] *= 1.3; a[-30:] *= 0.45
    for x0 in (20, w // 2 + 20):
        for y in range(40, 130, 12):
            a[y:y + 5, x0:x0 + 88] *= 0.35
        a[160:176, x0 + 20:x0 + 68] = (220, 220, 210)
        a[250:300, x0 + 76:x0 + 84] = (60, 62, 64)
    a *= (1 - 0.3 * np.clip(_noise(0, 30, seed + 3, 3, (h, w)) - 0.55, 0, 1) * 3)[..., None]
    return _img(a)


def tex_console(seed=50, top=False):
    """A wall console: dark casing, a keyboard deck and a glowing green-blue screen (emissive)."""
    a = np.array((58, 62, 66), float)[None, None] * (0.85 + 0.25 * _noise(0, 24, seed, 3, (T, T))[..., None])
    _edges(a, 8)
    emis = np.zeros((T, T, 3))
    if top:
        a[40:T - 40, 24:T - 24] = (24, 28, 30)
        for y in range(52, T - 52, 18):
            for x in range(36, T - 36, 22):
                a[y:y + 10, x:x + 14] = (80, 86, 90)
        for k, c in enumerate([(255, 60, 40), (60, 255, 90), (255, 200, 40), (60, 160, 255)]):
            a[20:30, 30 + k * 24:44 + k * 24] = c; emis[20:30, 30 + k * 24:44 + k * 24] = c
    else:
        scr = np.zeros((150, T - 40, 3))
        lines = (np.arange(150) % 6 < 3)[:, None]
        scr[..., 1] = 70 + 50 * lines; scr[..., 2] = 90 + 40 * lines; scr[..., 0] = 15
        r = np.random.default_rng(seed)
        for _ in range(8):
            gy = r.integers(6, 140); gl = r.integers(20, 150)
            scr[gy:gy + 5, 10:10 + gl] = (120, 255, 200)
        a[30:180, 20:T - 20] = scr * 0.8; emis[30:180, 20:T - 20] = scr
    return _img(a), _img(emis)


def tex_reactor(seed=51):
    """The reactor core's drum, unrolled: dark ribbed steel with three bright cyan coolant bands (emissive)."""
    w, h = 512, 256
    a = np.array((70, 78, 88), float)[None, None] * (0.85 + 0.25 * _noise(0, 24, seed, 3, (h, w))[..., None])
    for x in range(0, w, 32):
        a[:, x:x + 4] *= 0.5; a[:, x + 4:x + 7] *= 1.3
    emis = np.zeros((h, w, 3))
    for y0 in (40, 120, 200):
        band = np.s_[y0:y0 + 18]
        a[band] = (150, 230, 255); emis[band] = (60, 200, 255)
        a[y0 - 4:y0] *= 0.4; a[y0 + 18:y0 + 22] *= 0.4
    return _img(a), _img(emis)


def tex_reactor_top(seed=52):
    """The core seen from above: a glowing cyan iris in a heavy steel ring."""
    a = np.array((60, 66, 74), float)[None, None] * (0.85 + 0.25 * _noise(0, 20, seed, 3, (T, T))[..., None])
    yy, xx = np.mgrid[0:T, 0:T]
    d = np.hypot(xx - T / 2, yy - T / 2) / (T / 2)
    ang = np.arctan2(yy - T / 2, xx - T / 2)
    emis = np.zeros((T, T, 3))
    core = d < 0.55
    glow = np.clip(1 - d / 0.55, 0, 1) ** 0.6 * (0.75 + 0.25 * np.cos(ang * 8))
    a[core] = (np.array((120, 220, 255)) * (0.5 + 0.5 * glow[core][..., None]))
    emis[core] = np.array((70, 210, 255)) * glow[core][..., None]
    a[(d > 0.55) & (d < 0.62)] = (30, 32, 36)
    for k in range(12):
        t = k * np.pi / 6
        a[(np.abs(((ang - t + np.pi) % (2 * np.pi)) - np.pi) < 0.06) & (d > 0.65) & (d < 0.95)] *= 1.5
    return _img(a), _img(emis)


def tex_pipe(seed=53, col=(196, 156, 40)):
    """A painted pipe, unrolled around its circumference (rows): a lit top, a shaded underside, and a dark
    coupling band every unit along it."""
    w, h = 256, 64
    shade = 0.45 + 0.75 * np.sin(np.linspace(0, np.pi, h))[:, None] * np.ones((1, w))
    a = np.array(col, float)[None, None] * shade[..., None] * (0.9 + 0.15 * _noise(0, 16, seed, 2, (h, w))[..., None])
    for x in (0, w // 2):
        a[:, x:x + 10] = np.array((70, 72, 74))[None, None] * shade[:, :1, None]
    return _img(a)


TEXTURES = {
    'prop_pipe_yellow': lambda: (tex_pipe(), None),
    'prop_pipe_grey': lambda: (tex_pipe(54, (176, 40, 30)), None),          # AS's red pipe runs
    'prop_reactor': tex_reactor,
    'prop_reactor_top': tex_reactor_top,
    'prop_locker': lambda: (tex_locker(), None),
    'prop_console': lambda: tex_console(),
    'prop_console_top': lambda: tex_console(top=True),
    'prop_ammo': lambda: tex_ammo(),
    'prop_ammo_top': lambda: tex_ammo(top=True),
    'prop_doorframe': lambda: (tex_doorframe(), None),
    'prop_doorpost': tex_doorpost,
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


def _door(m, width, hgt=2.5, lintel=0.38, post=0.3, depth=0.45):
    """A bulkhead frame round an opening ``width`` wide, centred on the wall plane (y = 0) and seen from both
    sides: a post either side standing in the hull, and a chevron lintel across the top."""
    a = width / 2
    d = depth / 2
    kp, kl = ('prop_doorpost', False, 0), ('prop_doorframe', False, 0)
    for x0, x1 in ((-a - post, -a), (a, a + post)):
        m.quad(kp, (x0, -d, 0), (x1, -d, 0), (x1, -d, hgt), (x0, -d, hgt), [(0, 1), (1, 1), (1, 0), (0, 0)])
        m.quad(kp, (x1, d, 0), (x0, d, 0), (x0, d, hgt), (x1, d, hgt), [(0, 1), (1, 1), (1, 0), (0, 0)])
        # The jamb facing the opening.
        jx = x1 if x0 < 0 else x0
        sgn = 1 if x0 < 0 else -1
        p0, p1 = ((jx, -d), (jx, d)) if sgn > 0 else ((jx, d), (jx, -d))
        m.quad(kp, (p0[0], p0[1], 0), (p1[0], p1[1], 0), (p1[0], p1[1], hgt), (p0[0], p0[1], hgt), [(0, 1), (0.3, 1), (0.3, 0), (0, 0)])
        m.quad(('wall_trim', False, 0), (x0, -d, hgt + 0.014), (x1, -d, hgt + 0.014), (x1, d, hgt + 0.014), (x0, d, hgt + 0.014),
               [(0, 0), (1, 0), (1, 1), (0, 1)])
    z0 = hgt - lintel
    u = (width + 2 * post) / 4.0
    m.quad(kl, (-a, -d, z0), (a, -d, z0), (a, -d, hgt), (-a, -d, hgt), [(0, 1), (u, 1), (u, 0), (0, 0)])
    m.quad(kl, (a, d, z0), (-a, d, z0), (-a, d, hgt), (a, d, hgt), [(0, 1), (u, 1), (u, 0), (0, 0)])
    m.quad(kl, (-a, d, z0), (a, d, z0), (a, -d, z0), (-a, -d, z0), [(0, 1), (u, 1), (u, 0), (0, 0)])
    m.quad(('wall_trim', False, 0), (-a, -d, hgt + 0.014), (a, -d, hgt + 0.014), (a, d, hgt + 0.014), (-a, d, hgt + 0.014),
           [(0, 0), (u, 0), (u, 1), (0, 1)])


def _wallbox(m, side, top, w, d, hgt, front_uv=((0, 1), (1, 1), (1, 0), (0, 0))):
    """A box standing against a wall that faces -Y: its back on y = 0, its front at y = -d."""
    a = w / 2
    m.quad((side, False, 0), (-a, -d, 0), (a, -d, 0), (a, -d, hgt), (-a, -d, hgt), list(front_uv))
    m.quad((side, False, 0), (a, -d, 0), (a, 0, 0), (a, 0, hgt), (a, -d, hgt), [(0.9, 1), (1, 1), (1, 0), (0.9, 0)])
    m.quad((side, False, 0), (-a, 0, 0), (-a, -d, 0), (-a, -d, hgt), (-a, 0, hgt), [(0, 1), (0.1, 1), (0.1, 0), (0, 0)])
    m.quad((top, False, 0), (-a, -d, hgt), (a, -d, hgt), (a, 0, hgt), (-a, 0, hgt), [(0, 1), (1, 1), (1, 0), (0, 0)])


def _drum(m, side, top, r, z0, hgt, n=20):
    """An upright drum of radius r from z0 to z0 + hgt, its top a disc."""
    for i in range(n):
        t0, t1 = 2 * math.pi * i / n, 2 * math.pi * (i + 1) / n
        p0, p1 = (r * math.cos(t0), r * math.sin(t0)), (r * math.cos(t1), r * math.sin(t1))
        m.quad((side, False, 0), (p0[0], p0[1], z0), (p1[0], p1[1], z0), (p1[0], p1[1], z0 + hgt), (p0[0], p0[1], z0 + hgt),
               [(2 * i / n, 1), (2 * (i + 1) / n, 1), (2 * (i + 1) / n, 0), (2 * i / n, 0)])
    m.poly((top, False, 0), [(r * math.cos(2 * math.pi * i / n), r * math.sin(2 * math.pi * i / n), z0 + hgt) for i in range(n)],
           [(0.5 + 0.5 * math.cos(2 * math.pi * i / n), 0.5 - 0.5 * math.sin(2 * math.pi * i / n)) for i in range(n)])


def _blob(m, w, d, y0=None):
    """A soft multiplied shadow on the deck round a footprint w by d (centred, or from y0 to the wall at y = 0)."""
    from tools.shipkit import UNLIT, MULTIPLY
    a = w / 2 + 0.25
    if y0 is None:
        b0, b1 = -d / 2 - 0.25, d / 2 + 0.25
    else:
        b0, b1 = y0 - 0.3, 0.05
    m.quad(('decal_blob', False, UNLIT, MULTIPLY), (-a, b0, 0.018), (a, b0, 0.018), (a, b1, 0.018), (-a, b1, 0.018),
           [(0, 1), (1, 1), (1, 0), (0, 0)])


def _pipe(m, tex, y, z, r, x0=-1.0, x1=1.0, n=8):
    """A pipe along x from x0 to x1, its axis at (y, z), radius r."""
    import math as _m
    for i in range(n):
        t0, t1 = 2 * _m.pi * i / n, 2 * _m.pi * (i + 1) / n
        a0 = (y + r * _m.cos(t0), z + r * _m.sin(t0)); a1 = (y + r * _m.cos(t1), z + r * _m.sin(t1))
        m.quad((tex, False, 0), (x0, a1[0], a1[1]), (x1, a1[0], a1[1]), (x1, a0[0], a0[1]), (x0, a0[0], a0[1]),
               [(0, (i + 1) / n), (1, (i + 1) / n), (1, i / n), (0, i / n)])


def _bigpipe(m, length=4.0, r=0.3, z=0.4):
    """AS's fat red pipe lying along a room's wall (lb-05): four units of it along x, flanged at every joint,
    resting on grey saddles, capped at both ends."""
    import math as _m
    a = length / 2
    k = -a
    while k < a - 1e-6:
        _pipe(m, 'prop_pipe_grey', 0.0, z, r, k, k + 1.0, 12)
        k += 1.0
    for fx in [-a + 0.04 + i for i in range(int(length) + 1)]:
        x0, x1 = max(-a, fx - 0.05), min(a, fx + 0.05)
        _pipe(m, 'prop_column', 0.0, z, r * 1.18, x0, x1, 12)
    from tools.shipkit import ShipModel
    for sx in (-a * 0.5, a * 0.5):
        t = ShipModel('t', (0, 0, 0)); _box(t, 'prop_crate_metal', 'prop_crate_metal_top', 0.16, r * 2.3, z - r * 0.4, 0.0)
        for key, part in t.parts.items():
            dst = m.parts.setdefault(key, dict(pos=[], nrm=[], uv=[], tri=[]))
            base = len(dst['pos'])
            dst['pos'].extend(np.array(v) + (sx, 0, 0) for v in part['pos']); dst['nrm'].extend(part['nrm']); dst['uv'].extend(part['uv'])
            dst['tri'].extend((i + base, j + base, k2 + base) for i, j, k2 in part['tri'])
    n = 12
    for xe, sgn in ((-a, -1), (a, 1)):
        pts = [(xe, r * 1.18 * _m.cos(2 * _m.pi * i / n), z + r * 1.18 * _m.sin(2 * _m.pi * i / n)) for i in range(n)]
        if sgn < 0:
            pts = pts[::-1]
        m.poly(('prop_reactor_top', False, 0), pts, [(0.5 + 0.5 * _m.cos(2 * _m.pi * i / n), 0.5 + 0.5 * _m.sin(2 * _m.pi * i / n)) for i in range(n)])


DOOR_WIDTHS = range(1, 13)


def pieces(out):
    """KPPipes (two pipes two units long, high along a wall facing -Y), KPAmmo (the ammo supply case, the ASAmmo unit's model), KPLockers and KPConsole (against a wall facing -Y), KPDoor<w> (a bulkhead frame round an opening w wide), KPCol (a wall strut), KPCrateG / KPCrateM (one crate), KPCrateStack (two and one on top), KPBarrel, KPBarrels (a cluster of three)."""
    from tools.shipkit import ShipModel
    m = out['KPCol'] = ShipModel('KPCol', (0, 0, 0)); _column(m)
    m = out['KPPipes'] = ShipModel('KPPipes', (0, 0, 0))
    _pipe(m, 'prop_pipe_yellow', -0.14, 2.18, 0.09)
    _pipe(m, 'prop_pipe_grey', -0.32, 2.26, 0.07)
    m = out['KPReactor'] = ShipModel('KPReactor', (0, 0, 0))
    _drum(m, 'prop_reactor', 'prop_reactor_top', 1.55, 2.5, 0.9)
    _drum(m, 'prop_column', 'prop_reactor_top', 1.75, 2.5, 0.18)
    m = out['KPAmmo'] = ShipModel('KPAmmo', (0, 0, 0)); _box(m, 'prop_ammo', 'prop_ammo_top', 0.95, 0.65, 0.5); _blob(m, 0.95, 0.65)
    m = out['KPLockers'] = ShipModel('KPLockers', (0, 0, 0)); _wallbox(m, 'prop_locker', 'prop_crate_metal_top', 1.3, 0.42, 1.85); _blob(m, 1.3, 0.42, -0.42)
    m = out['KPConsole'] = ShipModel('KPConsole', (0, 0, 0))
    _wallbox(m, 'prop_console', 'prop_console_top', 1.2, 0.55, 0.95); _blob(m, 1.2, 0.55, -0.55)
    for w in DOOR_WIDTHS:
        m = out['KPDoor%d' % w] = ShipModel('KPDoor%d' % w, (0, 0, 0)); _door(m, w)
    m = out['KPCrateG'] = ShipModel('KPCrateG', (0, 0, 0)); _box(m, 'prop_crate_green', 'prop_crate_green_top', 1.1, 1.1, 0.9); _blob(m, 1.1, 1.1)
    m = out['KPCrateM'] = ShipModel('KPCrateM', (0, 0, 0)); _box(m, 'prop_crate_metal', 'prop_crate_metal_top', 0.9, 0.9, 0.8); _blob(m, 0.9, 0.9)
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
    _blob(out['KPCrateStack'], 2.2, 1.1)
    m = out['KPBarrel'] = ShipModel('KPBarrel', (0, 0, 0)); _barrel(m); _blob(m, 0.6, 0.6)
    m = out['KPBigPipe'] = ShipModel('KPBigPipe', (0, 0, 0)); _bigpipe(m); _blob(m, 4.2, 0.8)
    m = out['KPBarrels'] = ShipModel('KPBarrels', (0, 0, 0))
    for off in ((-0.33, -0.2), (0.33, -0.2), (0.0, 0.36)):
        b = ShipModel('t', (0, 0, 0)); _barrel(b)
        for key, p in b.parts.items():
            dst = m.parts.setdefault(key, dict(pos=[], nrm=[], uv=[], tri=[]))
            base = len(dst['pos'])
            dst['pos'].extend(np.array(v) + (off[0], off[1], 0) for v in p['pos']); dst['nrm'].extend(p['nrm']); dst['uv'].extend(p['uv'])
            dst['tri'].extend((a + base, b2 + base, c + base) for a, b2, c in p['tri'])
    _blob(m, 1.3, 1.2)
