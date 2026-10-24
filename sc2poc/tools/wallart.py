"""Wall bays, wall-top trim and hull caps after Alien Swarm's.

Its bulkheads (cleanwall1, colonywall1, metalwallgreyset1, metalwallskin3, techwall4 in
the VPKs, looked at for palette and layout only) are pale painted metal in courses:
a dark top rail, panels with rivets, a painted band at waist height (beige, orange, or
hazard stripes), a dark kick plate, and fixtures that glow: lamp boxes, screens,
alarm lamps. Drawn from scratch with NumPy.

A bay is two map units wide by the wall's 2.5 height (512 x 640 px); row 0 is the top.
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from tools.shipkit import _noise, _img
from tools.deckart import _font

WW, WH = 512, 640


def _wall_base(seed, tone, seams=128):
    base = np.array(tone, float)
    n = _noise(0, 50, seed, 4, (WH, WW)); f = _noise(0, 5, seed + 3, 2, (WH, WW))
    a = base[None, None] * (0.88 + 0.2 * n[..., None] + 0.05 * f[..., None])
    for x in range(0, WW, seams):
        a[:, max(0, x - 2):x + 2] *= 0.5
        a[:, x + 2:x + 4] *= 1.14
    return a


def _band(a, y0, y1, col, seed, worn=0.3):
    h = y1 - y0
    paint = np.array(col, float)[None, None] * (0.88 + 0.22 * _noise(0, 12, seed, 3, (h, WW))[..., None])
    chip = np.clip((_noise(0, 8, seed + 1, 3, (h, WW)) - (1 - worn)) * 6, 0, 1)[..., None]
    a[y0:y1] = paint * (1 - chip) + a[y0:y1] * chip
    a[y0:y0 + 3] *= 0.55; a[y1 - 3:y1] *= 0.7


def _course(a, y, depth=0.45):
    a[max(0, y - 3):y + 2] *= depth
    a[y + 2:y + 5] *= 1.18


def _rivets(a, spots, tone, rad=4):
    yy, xx = np.mgrid[-rad - 2:rad + 3, -rad - 2:rad + 3]
    head = np.clip(rad - np.hypot(xx, yy), 0, 1)[..., None]
    for x, y in spots:
        if x - rad - 2 < 0 or y - rad - 2 < 0 or x + rad + 3 > a.shape[1] or y + rad + 3 > a.shape[0]:
            continue
        sl = a[y - rad - 2:y + rad + 3, x - rad - 2:x + rad + 3]
        sl[:] = sl * (1 - head) + np.array(tone, float) * (1.0 + 0.25 * (-yy / rad)[..., None]) * head
    return a


def _hazard(a, x0, x1, y0, y1, seed, period=20):
    h, w = y1 - y0, x1 - x0
    yy, xx = np.mgrid[0:h, 0:w]
    stripe = ((xx + yy) // period) % 2 == 0
    band = np.where(stripe[..., None], np.array((206, 160, 34), float), np.array((28, 26, 24), float))
    k = np.clip((_noise(0, 10, seed, 3, (h, w)) - 0.66) * 5, 0, 1)[..., None]
    a[y0:y1, x0:x1] = band * (1 - k) + a[y0:y1, x0:x1] * k
    a[y0:y0 + 2, x0:x1] *= 0.5; a[y1 - 2:y1, x0:x1] *= 0.5


def _kick(a, y0, seed):
    a[y0:] = a[y0:] * 0.42
    a[y0:y0 + 3] *= 0.6
    a[y0 + 3:y0 + 5] *= 1.5
    g = np.clip(_noise(0, 20, seed, 3, (WH - y0, WW)) - 0.4, 0, 1)
    a[y0:] *= (1 - 0.4 * g)[..., None]


def _grime(a, seed, amount=0.3):
    n = _noise(0, 60, seed, 4, (WH, WW))
    streak = _noise(0, 6, seed + 1, 1, (1, WW)).repeat(WH, 0) * np.linspace(0.0, 1.0, WH)[:, None] ** 2
    dirt = np.clip((n - 0.5) * 2.2, 0, 1) * 0.7 + streak * 0.6
    # A dark foot: the wall meets the deck in shadow.
    foot = np.clip((np.arange(WH) - WH * 0.8) / (WH * 0.2), 0, 1)[:, None] ** 2 * 0.35
    return a * (1 - amount * np.clip(dirt, 0, 1) - foot)[..., None]


def _weather(a, seed, streaks=46, grain=0.035):
    """What years of a colony's damp leave on AS's walls: grime run down in thin streaks from every ledge and
    bolt, fine grain and small specks (soft noise alone reads as clean plastic)."""
    r = np.random.default_rng(seed)
    h, w = a.shape[:2]
    a = a * (1 + grain * r.standard_normal((h, w))[..., None])
    run = np.zeros((h, w))
    for _ in range(streaks):
        x = int(r.integers(0, w)); y = int(r.integers(0, h * 3 // 4)); ln = int(r.integers(40, 260)); wd = int(r.choice([1, 1, 2, 3]))
        k = min(h, y + ln) - y
        fade = np.linspace(1.0, 0.0, k) ** 0.7 * r.uniform(0.12, 0.3)
        run[y:y + k, x:x + wd] = np.maximum(run[y:y + k, x:x + wd], fade[:, None])
    run = np.asarray(Image.fromarray((run * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.8))).astype(float) / 255
    spk = np.zeros((h, w))
    for _ in range(500):
        x, y = r.integers(0, w), r.integers(0, h)
        spk[y, x] = r.uniform(-0.25, 0.3)
    return a * (1 - run - spk)[..., None]


def _cylinder(a, cy, rad, col, spec=0.5):
    yy = np.arange(-rad, rad)
    s = np.sqrt(np.clip(1 - (yy / rad) ** 2, 0, 1))
    light = 0.3 + 0.8 * s * (0.65 + 0.35 * (-yy / rad)) + spec * np.clip(1 - np.abs(yy / rad + 0.45) * 4, 0, 1)
    a[cy - rad:cy + rad] = np.array(col, float)[None, None] * light[:, None, None]
    a[cy + rad:cy + rad + 4] *= 0.55                  # its shadow on the wall


def _label(a, text, x0, x1, y0, y1, ink, size):
    lab = Image.new('L', (x1 - x0, y1 - y0), 0)
    ImageDraw.Draw(lab).text(((x1 - x0) / 2, (y1 - y0) / 2), text, font=_font(size), fill=255, anchor='mm')
    m = np.asarray(lab).astype(float)[..., None] / 255
    a[y0:y1, x0:x1] = a[y0:y1, x0:x1] * (1 - m) + np.array(ink, float) * m


def wall_art(kind, seed):
    """One wall bay -> (diffuse, emissive or None). Kinds: clean, colony, pipes, vent, screen, light, alarm, dark."""
    r = np.random.default_rng(seed)
    emis = np.zeros((WH, WW, 3))
    U1, M0, M1, L1, K = int(WH * 0.06), int(WH * 0.36), int(WH * 0.47), int(WH * 0.86), int(WH * 0.9)
    if kind == 'colony':
        a = _wall_base(seed, (128, 118, 104), 256)
    elif kind == 'dark':
        a = _wall_base(seed, (100, 108, 116), 128)
    else:
        a = _wall_base(seed, (150, 154, 156), 128)
    # Top rail: dark, with a lit lower lip.
    a[:U1] *= 0.48; a[U1 - 3:U1] *= 2.0
    for y in (M0, M1, L1):
        _course(a, y)
    _rivets(a, [(x, y) for y in (U1 + 10, M0 - 10, M1 + 10, L1 - 10) for x in range(20, WW, 64)],
            (150, 136, 118) if kind == 'colony' else (172, 174, 174))
    if kind == 'clean':
        _band(a, M0 + 6, M1 - 4, (196, 178, 120), seed + 5)          # cleanwall1's beige stripe
    elif kind == 'colony':
        _band(a, M0 + 4, M1 - 2, (200, 118, 36), seed + 5, 0.4)      # colonywall1's orange band
        _hazard(a, 0, WW, U1 + 24, U1 + 60, seed + 6)
        _hazard(a, 0, WW, L1 - 50, L1 - 14, seed + 7)
    elif kind == 'pipes':
        a[M0 - 30:L1] *= 0.7
        for k, (cy, rad, col) in enumerate([(M0 + 6, 20, (196, 156, 40)), (M0 + 58, 14, (160, 52, 40)), (M1 + 74, 24, (128, 134, 138)),
                                             (M1 + 126, 12, (90, 124, 156))]):
            _cylinder(a, cy, rad, col)
            for x in range(40 + k * 30, WW, 170):
                a[cy - rad - 4:cy + rad + 4, x:x + 12] = (70, 72, 74)
                a[cy - rad - 4:cy + rad + 4, x + 12:x + 14] *= 0.4
    elif kind == 'vent':
        _band(a, M0 + 6, M1 - 4, (120, 124, 126), seed + 5, 0.1)
        x0, x1, y0, y1 = WW // 2 - 110, WW // 2 + 110, M1 + 20, L1 - 20
        a[y0 - 10:y1 + 10, x0 - 10:x1 + 10] *= 0.6
        a[y0:y1, x0:x1] = (24, 25, 26)
        for y in range(y0 + 6, y1 - 6, 14):
            a[y:y + 8, x0 + 8:x1 - 8] = np.array((116, 120, 122)) * np.linspace(1.2, 0.55, 8)[:, None, None]
        for cx in (x0 - 30, x1 + 22):
            for yy in range(y0, y1, 26):
                a[yy:yy + 12, cx:cx + 8] = (210, 160, 30)
        _label(a, 'VENT  07', 0, WW, M0 - 70, M0 - 10, (40, 40, 40), 34)
    elif kind == 'screen':
        _band(a, M0 + 6, M1 - 4, (196, 178, 120), seed + 5)
        x0, x1, y0, y1 = 70, WW - 70, M1 + 22, L1 - 30
        a[y0 - 14:y1 + 14, x0 - 14:x1 + 14] = (52, 56, 60)
        a[y0 - 14:y0 - 11, x0 - 14:x1 + 14] *= 1.6
        scr = np.zeros((y1 - y0, x1 - x0, 3))
        lines = (np.arange(y1 - y0) % 5 < 2)[:, None]
        scr[..., 1] = 60 + 40 * lines; scr[..., 2] = 40 + 30 * lines; scr[..., 0] = 10
        for _ in range(10):
            gy = r.integers(6, y1 - y0 - 12); gl = r.integers(30, (x1 - x0) // 2)
            scr[gy:gy + 6, 14:14 + gl] = (90, 255, 170)
        for k in range(8):
            hgt = int(r.integers(10, (y1 - y0) // 2))
            scr[y1 - y0 - 10 - hgt:y1 - y0 - 10, (x1 - x0) - 180 + k * 20:(x1 - x0) - 166 + k * 20] = (70, 200, 255)
        a[y0:y1, x0:x1] = scr * 0.8
        emis[y0:y1, x0:x1] = scr
        for k in range(5):
            c = [(255, 40, 30), (40, 255, 60), (255, 190, 30)][k % 3]
            a[y1 + 20:y1 + 30, x0 + k * 26:x0 + k * 26 + 14] = c
            emis[y1 + 20:y1 + 30, x0 + k * 26:x0 + k * 26 + 14] = c
    elif kind == 'light':
        _band(a, M0 + 6, M1 - 4, (120, 124, 126), seed + 5, 0.1)
        for x0 in (40, WW // 2 + 40):
            bx0, bx1, by0, by1 = x0, x0 + WW // 2 - 80, U1 + 18, U1 + 92
            a[by0 - 8:by1 + 8, bx0 - 8:bx1 + 8] = (54, 56, 58)
            a[by0:by1, bx0:bx1] = (250, 250, 240)
            emis[by0:by1, bx0:bx1] = (255, 250, 230)
            _hazard(a, bx0 - 8, bx1 + 8, by1 + 10, by1 + 30, seed, 12)
        # The lamps' spill down the wall.
        ys = np.arange(WH)
        spill = np.clip(1 - (ys - (U1 + 100)) / 240.0, 0, 1) * (ys > U1 + 100)
        a *= (1 + 0.35 * spill)[:, None, None]
    elif kind == 'alarm':
        _band(a, M0 + 6, M1 - 4, (196, 178, 120), seed + 5)
        cx, cy = WW // 4, (M1 + L1) // 2
        yy, xx = np.mgrid[0:WH, 0:WW]
        d = np.hypot(xx - cx, yy - cy)
        lamp = d < 34
        a[(d < 44) & ~lamp] = (50, 50, 52)
        a[lamp] = (255, 60, 40); emis[lamp] = (255, 40, 20)
        halo = np.clip(1 - (d - 44) / 70, 0, 1) * (d >= 44)
        a *= (1 + np.array((0.5, 0.05, 0.0))[None, None] * halo[..., None])
        sx0, sx1, sy0, sy1 = WW // 2 + 10, WW - 40, cy - 46, cy + 46
        a[sy0:sy1, sx0:sx1] = (190, 40, 30)
        _label(a, 'DANGER', sx0, sx1, sy0, sy1, (240, 236, 226), 46)
    else:   # dark: metalwallgreyset1's ribbed panels
        for x in range(0, WW, 128):
            a[:, x + 54:x + 74] *= 1.15
            a[:, x + 52:x + 54] *= 0.55; a[:, x + 74:x + 76] *= 0.55
    _kick(a, K, seed + 9)
    a = _grime(a, seed + 11, 0.28)
    for _ in range(int(r.integers(0, 3))):
        cx, cy, rad = r.integers(0, WW), r.integers(WH // 4, WH), r.integers(30, 80)
        yy, xx = np.mgrid[0:WH, 0:WW]
        d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) / rad
        a *= (1 - 0.5 * np.clip(1 - d, 0, 1) ** 2 * _noise(0, 20, seed + 50, 2, (WH, WW)) * 1.6)[..., None]
    a = _weather(a, seed + 60)
    return _img(a), (_img(emis) if emis.max() > 0 else None)


def wall_hive(seed=200):
    """A bay grown over: plating under purple-brown alien skin with glowing pods."""
    plate, _ = wall_art('dark', seed)
    a = np.asarray(plate).astype(float)
    n = _noise(0, 40, seed + 4, 5, (WH, WW)); vein = np.abs(_noise(0, 18, seed + 9, 3, (WH, WW)) - 0.5) < 0.035
    cover = np.clip((n - 0.38) * 3.0 + np.linspace(-0.4, 0.5, WH)[:, None] + 0.1, 0, 1)
    skin = np.array((70, 38, 52), float)[None, None] * (0.6 + 0.8 * _noise(0, 10, seed + 2, 3, (WH, WW))[..., None])
    a = a * (1 - cover[..., None]) + skin * cover[..., None]
    a[vein & (cover > 0.3)] = (130, 66, 88)
    emis = np.zeros((WH, WW, 3))
    pods = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:WH, 0:WW]
    for _ in range(4):
        cx, cy, rad = pods.integers(20, WW - 20), pods.integers(WH // 3, WH - 30), pods.integers(10, 22)
        g = np.clip(1 - np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) / rad, 0, 1) ** 1.5
        a += g[..., None] * np.array((80, 150, 40)); emis += g[..., None] * np.array((80, 200, 30))
    return _img(a), _img(emis)


def tex_trim(seed=12):
    """The lit lip along a wall's top edge: pale brushed metal, darker toward the hull."""
    w, h = 256, 32
    a = np.array((172, 176, 180), float)[None, None] * (0.9 + 0.15 * _noise(0, 4, seed, 2, (h, w))[..., None])
    a *= np.linspace(1.15, 0.55, h)[:, None, None]
    a[:2] *= 1.2
    return _img(a)


def tex_cap(seed=5, size=512):
    """The top of the hull as the camera sees it: dark blue-grey plating, conduits and vents."""
    n = _noise(size, 50, seed)
    a = np.array((28, 32, 37), float)[None, None] * (0.8 + 0.4 * n[..., None])
    q = size // 4
    for k in range(0, size, q):
        a[k:k + 3] *= 0.45; a[:, k:k + 3] *= 0.45
        a[k + 3:k + 5] *= 1.3; a[:, k + 3:k + 5] *= 1.3
    r = np.random.default_rng(seed)
    for _ in range(4):
        tx, ty = r.integers(0, 4, 2) * q
        a[ty + 20:ty + q - 20, tx + 20:tx + q - 20] *= 0.6
        for y in range(ty + 28, ty + q - 28, 10):
            a[y:y + 4, tx + 26:tx + q - 26] *= 1.6
    for k in range(2):
        y = int(r.integers(20, size - 20))
        yy = np.arange(-9, 9); s = np.sqrt(np.clip(1 - (yy / 9.0) ** 2, 0, 1))
        a[y - 9:y + 9] = np.array((46, 50, 54))[None, None] * (0.4 + 0.8 * s)[:, None, None]
    return _img(a)


# tools/level.py KIT_WALLS names -> the bay drawn for it.
WALLS = {'wall_plain0': ('clean', 100), 'wall_plain1': ('colony', 101), 'wall_pipes2': ('pipes', 102), 'wall_vent3': ('vent', 103),
         'wall_screen4': ('screen', 104), 'wall_light5': ('light', 105), 'wall_alarm6': ('alarm', 106)}


def textures():
    out = {name: wall_art(kind, seed) for name, (kind, seed) in WALLS.items()}
    out['wall_hive'] = wall_hive()
    out['wall_trim'] = (tex_trim(), None)
    out['cap'] = (tex_cap(), None)
    return out


if __name__ == '__main__':
    from pathlib import Path
    tex = textures()
    names = list(tex)
    T = 256
    im = Image.new('RGB', (4 * T, 2 * (T * 5 // 4 + 16)), (20, 20, 22))
    d = ImageDraw.Draw(im)
    for i, k in enumerate(names[:8]):
        diff, emis = tex[k]
        t = diff.convert('RGB').resize((T, T * 5 // 4))
        if emis is not None:
            t = Image.fromarray(np.clip(np.asarray(t, float) * 0.8 + np.asarray(emis.convert('RGB').resize((T, T * 5 // 4)), float) * 0.6, 0, 255).astype(np.uint8))
        x, y = (i % 4) * T, (i // 4) * (T * 5 // 4 + 16)
        im.paste(t, (x, y + 16)); d.text((x + 3, y + 2), k, fill=(255, 220, 90))
    out = Path(__file__).resolve().parents[1] / 'dist/wall-art.png'
    im.save(out); print(out)
