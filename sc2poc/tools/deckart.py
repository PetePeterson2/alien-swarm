"""Deck art after Alien Swarm's: floor plating, grating, hazard paint, grime and contact shadows.

Alien Swarm's interiors read as bright, mid-grey metal (greymetalfloor, metalfloor3,
metalgrate011a, swarm_metalfloorbrown, cleanwall1 in its VPKs) lit by strong coloured
lamps, with dark seams, bevelled panel edges, rivets, yellow-black hazard paint and
glowing grates over lit voids. Those were looked at for palette and pattern only;
everything here is drawn from scratch with NumPy.

Floor textures cover two by two map units (256 px a unit) and tile. Decals are drawn
white where they leave the deck alone (multiplied) or with alpha (painted).
"""
import math

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from tools.shipkit import _noise, _img

S = 512                      # floor texture size: two map units
U = S // 2                   # pixels a map unit


def _bevel(a, step, dark=0.42, lite=1.16, width=3):
    """Seams every ``step`` px both ways: a dark groove with a lit lip after it."""
    for k in range(0, S, step):
        a[max(0, k - width):k + width] *= dark
        a[k + width:k + width + 2] *= lite
        a[:, max(0, k - width):k + width] *= dark
        a[:, k + width:k + width + 2] *= lite
    return a


def _scratches(a, seed, n=40, tone=1.25, length=(20, 90)):
    r = np.random.default_rng(seed)
    im = Image.new('L', (S, S), 0); d = ImageDraw.Draw(im)
    for _ in range(n):
        x, y = r.integers(0, S, 2); ang = r.uniform(0, math.pi); ln = r.uniform(*length)
        d.line([(x, y), (x + math.cos(ang) * ln, y + math.sin(ang) * ln)], fill=int(r.integers(60, 160)), width=1)
    m = np.asarray(im).astype(float)[..., None] / 255
    return a * (1 + (tone - 1) * m)


def _bolts(a, spots, tone, rad=5):
    yy, xx = np.mgrid[-rad - 2:rad + 3, -rad - 2:rad + 3]
    d = np.hypot(xx, yy)
    head = np.clip(rad - d, 0, 1)
    rim = np.clip(1 - np.abs(d - rad - 0.8), 0, 1)
    for x, y in spots:
        x0, y0 = x - rad - 2, y - rad - 2
        if x0 < 0 or y0 < 0 or x0 + yy.shape[1] > S or y0 + yy.shape[0] > S:
            continue
        sl = a[y0:y0 + yy.shape[0], x0:x0 + yy.shape[1]]
        sl *= (1 - 0.45 * rim)[..., None]
        shade = 0.85 + 0.4 * np.clip((-(xx + yy) / (rad * 2.0)), -0.5, 0.5)
        sl[:] = sl * (1 - head[..., None]) + (np.array(tone, float) * shade[..., None]) * head[..., None]
    return a


def _wear(a, seed, amount=0.25, scale=60):
    n = _noise(0, scale, seed, 4, (S, S))
    blotch = np.clip((n - 0.5) * 3, -1, 1)
    return a * (1 + amount * blotch[..., None] * 0.5)


def _dirt(a, seed, amount=0.3):
    n = _noise(0, 90, seed, 5, (S, S))
    d = np.clip((n - 0.55) * 4, 0, 1)
    return a * (1 - amount * d[..., None])


def floor_plate(seed=1, tone=(118, 110, 98)):
    """greymetalfloor: four plates of a unit each, brown-grey, scuffed, a rivet in each corner."""
    base = np.array(tone, float)
    n = _noise(0, 40, seed, 4, (S, S)); f = _noise(0, 4, seed + 1, 2, (S, S))
    a = base[None, None] * (0.86 + 0.24 * n[..., None] + 0.06 * f[..., None])
    a = _wear(a, seed + 2, 0.35)
    # Lighter worn rims along every plate edge.
    yy, xx = np.mgrid[0:S, 0:S]
    ed = np.minimum(np.minimum(xx % U, U - xx % U), np.minimum(yy % U, U - yy % U))
    a *= (1 + 0.10 * np.clip(1 - ed / 18.0, 0, 1))[..., None]
    a = _scratches(a, seed + 3, 60, 1.22)
    a = _bevel(a, U)
    a = _bolts(a, [(x, y) for px in (0, U) for py in (0, U) for x, y in
                   ((px + 16, py + 16), (px + U - 16, py + 16), (px + 16, py + U - 16), (px + U - 16, py + U - 16))], base * 1.15)
    return _img(_dirt(a, seed + 4, 0.25))


def floor_tile(seed=2, tone=(142, 146, 146), mottle=0.18):
    """greymetalfloor2: paler blue-grey plates with a mottled, water-stained finish."""
    base = np.array(tone, float)
    n = _noise(0, 30, seed, 5, (S, S))
    stain = np.abs(_noise(0, 50, seed + 5, 3, (S, S)) - 0.5) < 0.06
    a = base[None, None] * (0.9 + mottle * n[..., None])
    a[stain] *= 1.08
    a = _wear(a, seed + 2, 0.2)
    a = _scratches(a, seed + 3, 30, 1.15)
    a = _bevel(a, U, 0.5, 1.12, 2)
    return _img(_dirt(a, seed + 4, 0.15))


def floor_lab(seed=3, glow=True):
    """Clean blue-white lab tiles, a unit each, whose seams carry a faint cyan light (emissive), as the bright
    grid of Alien Swarm's lab and colony floors does."""
    base = np.array((168, 180, 190), float)
    n = _noise(0, 50, seed, 3, (S, S))
    a = base[None, None] * (0.92 + 0.12 * n[..., None])
    emis = np.zeros((S, S, 3))
    for k in range(0, S, U):
        for sl in (np.s_[max(0, k - 3):k + 3, :], np.s_[:, max(0, k - 3):k + 3]):
            a[sl] = (186, 206, 214)
            if glow:
                emis[sl] = (16, 36, 44)
        a[k + 3:k + 6] *= 0.8; a[:, k + 3:k + 6] *= 0.8
    # Half-unit scoring inside each tile, and a few tiles a shade off.
    q = U // 2
    for k in range(q, S, U):
        a[k - 1:k + 1] *= 0.86; a[:, k - 1:k + 1] *= 0.86
    r = np.random.default_rng(seed)
    for _ in range(2):
        tx, ty = r.integers(0, 2, 2) * U
        a[ty + 6:ty + U - 6, tx + 6:tx + U - 6] *= r.uniform(0.9, 1.04)
    return _img(_dirt(a, seed + 4, 0.14)), (_img(emis) if glow else None)


def floor_diamond(seed=4, tone=(140, 140, 136)):
    """metalfloor011a: diamond tread plate, one plate of two units with a bevelled border."""
    base = np.array(tone, float)
    n = _noise(0, 50, seed, 4, (S, S))
    a = base[None, None] * (0.88 + 0.2 * n[..., None])
    yy, xx = np.mgrid[0:S, 0:S].astype(float)
    p = 24.0
    # Raised lentils, alternating ±45 degrees on a staggered grid, lit from the top left.
    cx = (xx % p) - p / 2; cy = (yy % p) - p / 2
    flip = ((xx // p + yy // p) % 2 == 0)
    u = np.where(flip, (cx + cy), (cx - cy)) / math.sqrt(2); v = np.where(flip, (cx - cy), (cx + cy)) / math.sqrt(2)
    lens = np.clip(1 - (u / 8.0) ** 2 - (v / 2.2) ** 2, 0, 1)
    light = np.where(flip, -v, v) * 0.12
    a *= (1 + (0.22 + light) * lens)[..., None]
    a *= (1 - 0.18 * np.clip(1 - ((u / 9.5) ** 2 + (v / 3.2) ** 2), 0, 1) * (lens == 0))[..., None]
    a = _wear(a, seed + 2, 0.3)
    a = _scratches(a, seed + 3, 25, 1.18)
    for k in (0,):
        a[:4] *= 0.4; a[:, :4] *= 0.4; a[4:6] *= 1.2; a[:, 4:6] *= 1.2
    return _img(_dirt(a, seed + 4, 0.28))


def floor_grille(seed=5, tone=(140, 142, 142)):
    """metalfloor3: plates of a unit punched with staggered slots over a dark void."""
    base = np.array(tone, float)
    n = _noise(0, 40, seed, 4, (S, S))
    a = base[None, None] * (0.86 + 0.24 * n[..., None])
    emis = np.zeros((S, S, 3))
    for py in (0, U):
        for px in (0, U):
            for row in range(7):
                y = py + 26 + row * 30
                off = 0 if row % 2 == 0 else 16
                for col in range(-1, 6):
                    x = px + 26 + off + col * 40
                    x0, x1 = max(px + 22, x), min(px + U - 22, x + 26)
                    if x1 - x0 < 8:
                        continue
                    a[y:y + 12, x0:x1] = (14, 14, 15)
                    a[y + 12:y + 14, x0:x1] *= 0.0
                    a[y - 2:y, x0:x1] *= 0.6
                    a[y + 14:y + 16, x0:x1] *= 1.25
    a = _wear(a, seed + 2, 0.25)
    a = _bevel(a, U, 0.35, 1.2, 4)
    a = _bolts(a, [(px + 12, py + 12) for px in (0, U) for py in (0, U)] + [(px + U - 12, py + U - 12) for px in (0, U) for py in (0, U)], base * 1.1, 4)
    return _img(_dirt(a, seed + 4, 0.2))


def floor_grate(seed=6, glow=(230, 110, 30), tone=(112, 96, 84)):
    """metalgrate011a over a lit void: rusty bars with the hot orange glow of the deck below between them."""
    base = np.array(tone, float)
    n = _noise(0, 40, seed, 4, (S, S))
    a = base[None, None] * (0.8 + 0.4 * n[..., None])
    yy, xx = np.mgrid[0:S, 0:S]
    gap = (yy % 16) >= 10
    cross = (xx % 128) < 10
    frame = (xx < 8) | (xx >= S - 8) | (yy < 8) | (yy >= S - 8)
    hot = np.array(glow, float)[None, None] * (0.35 + 0.9 * _noise(0, 120, seed + 9, 3, (S, S))[..., None])
    open_ = gap & ~cross & ~frame
    a[open_] = hot[open_] * 0.55
    # Bars round off: lit on top, shadowed toward the gaps.
    t = (yy % 16) / 10.0
    shade = np.where(gap, 1.0, 0.75 + 0.5 * np.sin(np.clip(t, 0, 1) * math.pi))
    a *= np.where(open_[..., None], 1.0, shade[..., None])
    a[cross & ~frame] *= 0.8
    a[frame] *= 0.9
    a = _wear(a, seed + 2, 0.35)
    emis = np.zeros((S, S, 3)); emis[open_] = hot[open_]
    return _img(_dirt(a, seed + 4, 0.25)), _img(emis)


def floor_hatch(seed=7):
    """metalfloor: one big access hatch over two units, dark with pale tread pads, handles and yellow corner marks."""
    a = np.array((70, 72, 74), float)[None, None] * (0.85 + 0.25 * _noise(0, 40, seed, 4, (S, S))[..., None])
    yy, xx = np.mgrid[0:S, 0:S]
    rim = 18
    inner = (xx > rim) & (xx < S - rim) & (yy > rim) & (yy < S - rim)
    corner = np.hypot(np.maximum(0, np.abs(xx - S / 2) - (S / 2 - rim - 30)), np.maximum(0, np.abs(yy - S / 2) - (S / 2 - rim - 30))) < 30
    a[~(inner & corner)] = np.array((118, 116, 110)) * (0.9 + 0.2 * _noise(0, 20, seed + 3, 2, (S, S))[~(inner & corner)][..., None])
    edge = inner & corner & ~((xx > rim + 6) & (xx < S - rim - 6) & (yy > rim + 6) & (yy < S - rim - 6))
    a[edge] *= 0.45
    for k, x0 in enumerate((S // 2 - 150, S // 2 + 40)):
        for y0 in (120, 200, 290, 370):
            a[y0:y0 + 26, x0:x0 + 110] = np.array((150, 150, 148)) * 0.95
            a[y0 + 26:y0 + 28, x0:x0 + 110] *= 0.5
    a[:, S // 2 - 3:S // 2 + 3] *= 0.4
    a[S // 2 - 3:S // 2 + 3] *= 0.6
    for hx, hy in ((S // 2, 40), (S // 2, S - 40)):
        a[hy - 10:hy + 10, hx - 50:hx + 50] = (60, 60, 62)
        a[hy - 5:hy + 5, hx - 40:hx + 40] = (28, 28, 30)
    for cx, cy in ((44, 44), (S - 44, 44), (44, S - 44), (S - 44, S - 44)):
        a[cy - 9:cy + 9, cx - 3:cx + 3] = (210, 160, 30); a[cy - 3:cy + 3, cx - 9:cx + 9] = (210, 160, 30)
    a = _bolts(a, [(x, y) for x in (30, S - 30) for y in (110, S // 2, S - 110)], (150, 150, 145), 5)
    return _img(_dirt(_scratches(a, seed + 5, 30, 1.2), seed + 4, 0.2))


def floor_brown(seed=8):
    """swarm_metalfloorbrown: a brown plate of two units with pale slats and two worn orange bands."""
    a = np.array((102, 84, 66), float)[None, None] * (0.85 + 0.3 * _noise(0, 40, seed, 4, (S, S))[..., None])
    yy, xx = np.mgrid[0:S, 0:S]
    for band in (S // 4, 3 * S // 4):
        b = (np.abs(yy - band) < 26)
        paint = _noise(0, 14, seed + 6, 3, (S, S)) > 0.32
        a[b & paint] = np.array((196, 120, 40)) * (0.85 + 0.25 * _noise(0, 10, seed + 7, 2, (S, S))[b & paint][..., None])
    for row in range(4):
        y0 = 30 + row * 128
        for col in range(10):
            x0 = 40 + col * 46
            a[y0:y0 + 60, x0:x0 + 14] *= 1.3
            a[y0 + 60:y0 + 63, x0:x0 + 14] *= 0.5
    a[:10] *= 0.5; a[:, :10] *= 0.5; a[10:13] *= 1.2; a[:, 10:13] *= 1.2
    a = _bolts(a, [(x, y) for x in (24, S - 24) for y in (24, S // 2, S - 24)], (140, 120, 100), 5)
    return _img(_dirt(_scratches(a, seed + 3, 40, 1.2), seed + 4, 0.3))


def floor_reactor(seed=9):
    """Reactor deck: dark blue-grey plates, a small cyan running light where four plates meet (emissive)."""
    a = np.asarray(floor_plate(seed, (84, 92, 102))).astype(float)
    emis = np.zeros((S, S, 3))
    yy, xx = np.mgrid[0:S, 0:S]
    d = np.maximum(np.abs(xx - U), np.abs(yy - U))
    lamp = d < 9
    a[(d < 14) & ~lamp] *= 0.4
    a[lamp] = (110, 200, 240); emis[lamp] = (40, 150, 220)
    return _img(a), _img(emis)


def floor_hive(seed=10, cover_bias=0.0):
    """The nest: dark plating grown over with brown-purple alien skin, raised veins, a few glowing pustules."""
    a = np.asarray(floor_plate(seed, (80, 78, 80))).astype(float)
    n = _noise(0, 70, seed + 4, 5, (S, S))
    cover = np.clip((n - 0.47 + cover_bias) * 3.0, 0, 1)
    skin = np.array((64, 36, 46), float)[None, None] * (0.65 + 0.7 * _noise(0, 14, seed + 2, 3, (S, S))[..., None])
    a = a * (1 - cover[..., None]) + skin * cover[..., None]
    vein = (np.abs(_noise(0, 30, seed + 9, 3, (S, S)) - 0.5) < 0.02) & (cover > 0.35)
    a[vein] = (118, 62, 82)
    emis = np.zeros((S, S, 3))
    r = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:S, 0:S]
    for _ in range(3):
        cx, cy, rad = r.integers(30, S - 30), r.integers(30, S - 30), r.integers(8, 14)
        if cover[cy, cx] < 0.5:
            continue
        g = np.clip(1 - np.hypot(xx - cx, yy - cy) / rad, 0, 1) ** 1.4
        a += g[..., None] * np.array((50, 100, 24)); emis += g[..., None] * np.array((50, 140, 20))
    return _img(a), _img(emis)


# ------------------------------------------------------------------ decals
def decal_hazard(seed=11, w=256, h=64):
    """Yellow and black hazard paint, worn through to the metal in places (opaque)."""
    yy, xx = np.mgrid[0:h, 0:w]
    stripe = ((xx + yy) // 24) % 2 == 0
    a = np.where(stripe[..., None], np.array((214, 168, 32), float), np.array((26, 24, 22), float))
    wear = _noise(0, 10, seed, 3, (h, w))
    metal = np.array((110, 106, 98), float)
    k = np.clip((wear - 0.62) * 5, 0, 1)[..., None]
    a = a * (1 - k) + metal * k
    a[:4] *= 0.5; a[-4:] *= 0.5
    return _img(a)


def decal_cable(seed, size=512):
    """Loose power cables snaking across the deck (multiplied): two thick rubber lines, a duller core where the
    light catches them, and a soft shadow."""
    r = np.random.default_rng(seed)
    im = Image.new('L', (size, size), 0); core = Image.new('L', (size, size), 0); sh = Image.new('L', (size, size), 0)
    d, dc, ds = ImageDraw.Draw(im), ImageDraw.Draw(core), ImageDraw.Draw(sh)
    for k in range(2):
        pts = []
        x, y = 0.0, r.uniform(0.3, 0.7) * size
        ang = r.uniform(-0.3, 0.3)
        while x < size:
            pts.append((x, y))
            ang += r.normal(0, 0.18); ang = float(np.clip(ang, -0.7, 0.7))
            x += 12 * np.cos(ang); y = float(np.clip(y + 12 * np.sin(ang), 40, size - 40))
        width = int(r.integers(20, 28))
        ds.line([(px + 6, py + 8) for px, py in pts], fill=140, width=width + 10)
        d.line(pts, fill=255, width=width)
        dc.line([(px, py - width * 0.18) for px, py in pts], fill=255, width=max(3, width // 4))
    c = np.asarray(im).astype(float) / 255
    hi = np.asarray(core.filter(ImageFilter.GaussianBlur(2))).astype(float) / 255
    shade = np.asarray(sh.filter(ImageFilter.GaussianBlur(6))).astype(float) / 255
    t = np.linspace(0, 1, size)[None, :]
    fade = np.clip(np.minimum(t, 1 - t) * 8, 0, 1)
    dark = np.clip(c * (0.82 - 0.3 * hi) + shade * (1 - c) * 0.35, 0, 1) * fade
    g = 255 * (1 - dark)
    return _img(np.dstack([g, g, g]))


def light_shaft(w=128, h=256, tint=(255, 244, 220)):
    """asw_vol_light: the haze under a lamp, added over the scene; brightest at the lamp (row 0), gone at the
    deck, soft at the cone's edges."""
    v = np.linspace(0, 1, h)[:, None]
    u = np.abs(np.linspace(-1, 1, w))[None, :]
    g = (1 - v) ** 1.6 * np.clip(1 - u, 0, 1) ** 1.2 * 0.3
    n = _noise(0, 30, 61, 3, (h, w))
    g *= 0.8 + 0.4 * n
    return _img(np.dstack([g * tint[0], g * tint[1], g * tint[2]]))


def decal_blob(size=128):
    """A soft contact shadow for a prop's footprint (multiplied): darkest in the middle, gone at the edge."""
    yy, xx = np.mgrid[0:size, 0:size] / (size - 1) * 2 - 1
    d = np.maximum(np.abs(xx), np.abs(yy)) * 0.6 + np.hypot(xx, yy) * 0.4
    g = 255 * (1 - 0.55 * np.clip(1 - d, 0, 1) ** 0.8)
    return _img(np.dstack([g, g, g]))


def run_light(w=128, h=32, tint=(150, 225, 255)):
    """A floor running light (added): a bright capsule with a soft halo."""
    yy, xx = np.mgrid[0:h, 0:w].astype(float)
    dx = np.maximum(0, np.abs(xx - w / 2) - (w / 2 - h / 2)) / (h / 2)
    dy = np.abs(yy - h / 2) / (h / 2)
    d = np.hypot(dx, dy)
    g = np.clip(1 - d, 0, 1) ** 2.2 + np.clip(1 - d / 0.45, 0, 1) * 0.6
    g = np.clip(g, 0, 1)
    return _img(np.dstack([g * tint[0], g * tint[1], g * tint[2]]))


def decal_shadow(w=64, h=64):
    """Contact shadow at a wall's foot: dark at row 0 (the wall), fading to white (no change)."""
    t = np.linspace(0, 1, h)[:, None] * np.ones((1, w))
    g = 255 * (0.42 + 0.58 * np.clip(t, 0, 1) ** 0.6)
    return _img(np.dstack([g, g, g * 1.02]))


def decal_grime(seed, kind='grime', size=256):
    """Multiplied stains: oily grime, scorch marks, alien goo puddles."""
    yy, xx = np.mgrid[0:size, 0:size].astype(float)
    r = np.hypot(xx - size / 2, yy - size / 2) / (size / 2)
    n = _noise(0, 40, seed, 5, (size, size))
    cover = np.clip((1 - r) * 1.6 + (n - 0.5) * 1.4 - 0.25, 0, 1)
    if kind == 'scorch':
        tint = np.array((0.3, 0.28, 0.26))
    elif kind == 'goo':
        tint = np.array((0.55, 0.7, 0.2))
        cover = np.clip(cover * 1.5, 0, 1)
    else:
        tint = np.array((0.66, 0.62, 0.54))
    rgb = 255 * (1 - cover[..., None] * (1 - tint[None, None]))
    return _img(rgb)


def _font(size, bold=True):
    for name in (('arialbd.ttf', 'Arial Bold.ttf') if bold else ('arial.ttf',)):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            pass
    return ImageFont.load_default()


def decal_text(text, w=1024, h=256, color=(226, 182, 40)):
    """Stencilled floor paint (with alpha): a room's name, worn."""
    im = Image.new('RGBA', (w, h), color + (0,))
    d = ImageDraw.Draw(im)
    f = _font(int(h * 0.62))
    box = d.textbbox((0, 0), text, font=f)
    tw, th = box[2] - box[0], box[3] - box[1]
    scale = min(1.0, (w * 0.94) / tw)
    if scale < 1.0:
        f = _font(int(h * 0.62 * scale)); box = d.textbbox((0, 0), text, font=f); tw, th = box[2] - box[0], box[3] - box[1]
    d.text(((w - tw) / 2 - box[0], (h - th) / 2 - box[1]), text, font=f, fill=color + (230,))
    a = np.asarray(im).astype(float)
    wear = _noise(0, 12, len(text) * 7, 3, (h, w))
    a[..., 3] *= np.clip(0.55 + (wear - 0.35) * 1.6, 0, 1)
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), 'RGBA')


def paint_pad(size=512, color=(226, 182, 40)):
    """A landing pad: a broad yellow ring with four inward chevrons, worn (with alpha)."""
    im = Image.new('RGBA', (size, size), color + (0,))
    d = ImageDraw.Draw(im)
    c = size / 2
    d.ellipse([c - size * 0.44, c - size * 0.44, c + size * 0.44, c + size * 0.44], outline=color + (225,), width=int(size * 0.05))
    for k in range(4):
        import math as _m
        ang = k * _m.pi / 2
        def P(r, t):
            return (c + r * _m.cos(ang + t), c + r * _m.sin(ang + t))
        d.polygon([P(size * 0.34, 0), P(size * 0.24, 0.32), P(size * 0.27, 0), P(size * 0.24, -0.32)], fill=color + (225,))
    a = np.asarray(im).astype(float)
    a[..., 3] *= np.clip(0.55 + (_noise(0, 16, 91, 3, (size, size)) - 0.35) * 1.6, 0, 1)
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), 'RGBA')


def _paint_split(im, tint=(1.0, 0.84, 0.30), lift=(64, 48, 6)):
    """An RGBA paint image as two layers the client draws (an alpha blend drew its clear parts opaque,
    2026-10-23): one multiplied over the deck (tints it yellow where painted, white elsewhere) and
    one added over that (lifts the paint's brightness)."""
    c = np.asarray(im).astype(float)[..., 3:4] / 255
    mul = 255 * (1 - c * (1 - np.array(tint)[None, None]))
    add = c * np.array(lift, float)[None, None]
    return _img(mul), _img(add)


def paint_line(w=256, h=32, color=(226, 182, 40)):
    """A worn yellow guide line (with alpha), two units long."""
    a = np.zeros((h, w, 4)); a[..., :3] = color
    a[6:h - 6, :, 3] = 225
    a[..., 3] *= np.clip(0.5 + (_noise(0, 10, 93, 3, (h, w)) - 0.35) * 1.7, 0, 1)
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), 'RGBA')


def paint_textures(names):
    """name -> image: each room's stencilled name, the landing pad and the guide line, as _m (multiplied) and _a (added) layers."""
    src = {'paint_pad': paint_pad(), 'paint_line': paint_line()}
    for slug, text in names.items():
        src['paint_' + slug.lower()] = decal_text(text, 512, 128)
    out = {}
    for k, im in src.items():
        out[k + '_m'], out[k + '_a'] = _paint_split(im)
    return out


def wall_sign(text, w=512, h=128):
    """A backlit wall sign after Alien Swarm's (reactorcontrolwitharrow, maintainancesign): white lettering and an
    arrow on a deep blue plate in a steel bezel; the plate glows (emissive)."""
    im = Image.new('RGB', (w, h), (64, 68, 72))
    d = ImageDraw.Draw(im)
    d.rectangle([8, 8, w - 9, h - 9], fill=(22, 58, 112))
    # The arrow points left: the sign hangs to the right of the door it names.
    d.polygon([(70, h * 0.3), (30, h / 2), (70, h * 0.7)], fill=(236, 240, 244))
    d.rectangle([68, h * 0.44, 110, h * 0.56], fill=(236, 240, 244))
    f = _font(52)
    box = d.textbbox((0, 0), text, font=f)
    if box[2] - box[0] > w - 160:
        f = _font(int(52 * (w - 160) / (box[2] - box[0])))
    d.text((134, h / 2), text, font=f, fill=(236, 240, 244), anchor='lm')
    a = np.asarray(im).astype(float)
    a *= (0.9 + 0.15 * _noise(0, 20, len(text), 2, (h, w)))[..., None]
    emis = np.zeros_like(a)
    inner = np.s_[8:h - 8, 8:w - 8]
    emis[inner] = a[inner] * 0.55
    return _img(a), _img(emis)


def sign_textures(names):
    """slug -> (diffuse, emissive): each passage's wall sign."""
    return {'sign_' + slug.lower(): wall_sign(text) for slug, text in names.items()}


def decal_arrow(w=256, h=256, color=(226, 182, 40)):
    im = Image.new('RGBA', (w, h), color + (0,))
    d = ImageDraw.Draw(im)
    d.polygon([(w * 0.5, h * 0.08), (w * 0.9, h * 0.5), (w * 0.64, h * 0.5), (w * 0.64, h * 0.92), (w * 0.36, h * 0.92),
               (w * 0.36, h * 0.5), (w * 0.1, h * 0.5)], fill=color + (220,))
    a = np.asarray(im).astype(float)
    a[..., 3] *= np.clip(0.6 + (_noise(0, 12, 77, 3, (h, w)) - 0.35) * 1.5, 0, 1)
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), 'RGBA')


def decal_warning(size=256):
    """swarm_warningsignfloor: a yellow square with a black border and a slip pictogram (opaque)."""
    im = Image.new('RGB', (size, size), (196, 158, 60))
    d = ImageDraw.Draw(im)
    d.rectangle([6, 6, size - 7, size - 7], outline=(30, 26, 20), width=10)
    d.text((size / 2, size * 0.22), 'WARNING', font=_font(int(size * 0.17)), fill=(24, 22, 18), anchor='mm')
    d.polygon([(size / 2, size * 0.36), (size * 0.8, size * 0.84), (size * 0.2, size * 0.84)], outline=(24, 22, 18), fill=None, width=10)
    d.text((size / 2, size * 0.68), '!', font=_font(int(size * 0.3)), fill=(24, 22, 18), anchor='mm')
    a = np.asarray(im).astype(float)
    a *= (0.8 + 0.3 * _noise(0, 20, 5, 3, (size, size)))[..., None]
    return _img(a)


FLOORS = {
    'floor_plate': lambda: (floor_plate(), None),
    'floor_plate2': lambda: (floor_plate(21, (104, 100, 94)), None),
    'floor_tile': lambda: (floor_tile(), None),
    'floor_tile2': lambda: (floor_tile(22, (126, 134, 140)), None),
    'floor_lab': lambda: floor_lab(),
    'floor_diamond': lambda: (floor_diamond(), None),
    'floor_grille': lambda: (floor_grille(), None),
    'floor_grate': lambda: floor_grate(),
    'floor_grate_blue': lambda: floor_grate(23, (40, 150, 255), (90, 98, 108)),
    'floor_hatch': lambda: (floor_hatch(), None),
    'floor_brown': lambda: (floor_brown(), None),
    'floor_reactor': lambda: floor_reactor(),
    'floor_hive': lambda: floor_hive(),
    'floor_hive2': lambda: floor_hive(24, 0.15),
}

# Each room kind's floor (tools/level.py KIT_KINDS): the main plating, the second plating mixed
# in by 2x2 block, and the accent laid at most once per 4x4 block. The lift has its own platform.
KIND_FLOORS = {
    'bay': ('floor_plate', 'floor_plate2', 'floor_hatch'),
    'hall': ('floor_diamond', 'floor_grille', 'floor_grate'),
    'duct': ('floor_grate', 'floor_grate', 'floor_grille'),
    'mess': ('floor_tile', 'floor_tile2', 'floor_tile'),
    'reactor': ('floor_reactor', 'floor_plate2', 'floor_grate_blue'),
    'cargo': ('floor_brown', 'floor_plate', 'floor_hatch'),
    'lab': ('floor_lab', 'floor_lab', 'floor_tile2'),
    'hive': ('floor_hive', 'floor_plate2', 'floor_hive2'),
}

DECALS = {
    'decal_hazard': lambda: (decal_hazard(), None),
    'decal_warning': lambda: (decal_warning(), None),
}
MUL_DECALS = {
    'decal_shadow': decal_shadow,
    'decal_blob': decal_blob,
    'decal_grime1': lambda: decal_grime(31),
    'decal_grime2': lambda: decal_grime(32),
    'decal_scorch': lambda: decal_grime(33, 'scorch'),
    'decal_goo': lambda: decal_grime(34, 'goo'),
    'decal_cable1': lambda: decal_cable(51),
    'decal_cable2': lambda: decal_cable(52),
    'shaft_warm': lambda: light_shaft(),
    'run_light': run_light,
    'shaft_cold': lambda: light_shaft(tint=(200, 226, 255)),
}


def textures():
    """name -> (diffuse, emissive or None): the floors and the opaque decals."""
    out = {k: f() for k, f in FLOORS.items()}
    out.update({k: f() for k, f in DECALS.items()})
    return out


def sheet(path):
    tex = textures()
    tex.update({k: (f(), None) for k, f in MUL_DECALS.items()})
    names = sorted(tex)
    cols = 6; T = 256
    im = Image.new('RGB', (cols * T, ((len(names) + cols - 1) // cols) * (T + 16)), (20, 20, 22))
    d = ImageDraw.Draw(im)
    for i, k in enumerate(names):
        diff, emis = tex[k]
        t = diff.convert('RGB').resize((T, T))
        if emis is not None:
            t = Image.fromarray(np.clip(np.asarray(t, float) * 0.7 + np.asarray(emis.convert('RGB').resize((T, T)), float), 0, 255).astype(np.uint8))
        x, y = (i % cols) * T, (i // cols) * (T + 16)
        im.paste(t, (x, y + 16)); d.text((x + 3, y + 2), k, fill=(255, 220, 90))
    im.save(path)


if __name__ == '__main__':
    import sys
    from pathlib import Path
    out = Path(__file__).resolve().parents[1] / 'dist/deck-art.png'
    sheet(out)
    print(out)
