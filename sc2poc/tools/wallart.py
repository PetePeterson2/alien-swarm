"""Wall bays, wall-top trim and hull caps after Alien Swarm's.

Its bulkheads (cleanwall1, colonywall1, metalwallgreyset1, metalwallskin3, techwall4 in
the VPKs, looked at for palette and layout only) are pale painted metal in courses:
a dark top rail, panels with rivets, a painted band at waist height (beige, orange, or
hazard stripes), a dark kick plate, and fixtures that glow: lamp boxes, screens,
alarm lamps. Drawn from scratch with NumPy.

A bay is two map units wide by the wall's 2.5 height (512 x 640 px); row 0 is the top.
"""
import math

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
        # The lit halls of AS's landing bay: pale panels, each outlined in a worn yellow frame stripe.
        a[U1:L1] = a[U1:L1] * 0.35 + np.array((200, 202, 200)) * 0.65 * (0.92 + 0.12 * _noise(0, 30, seed + 4, 3, (L1 - U1, WW))[..., None])
        for x0 in (0, WW // 2):
            fx0, fx1, fy0, fy1 = x0 + 22, x0 + WW // 2 - 22, U1 + 26, L1 - 26
            frame = np.zeros((WH, WW), bool)
            frame[fy0:fy1, fx0:fx0 + 9] = True; frame[fy0:fy1, fx1 - 9:fx1] = True
            frame[fy0:fy0 + 9, fx0:fx1] = True; frame[fy1 - 9:fy1, fx0:fx1] = True
            chip = _noise(0, 7, seed + 8 + x0, 3, (WH, WW)) > 0.72
            a[frame & ~chip] = np.array((214, 170, 36)) * (0.9 + 0.15 * _noise(0, 12, seed + 9, 2, (WH, WW))[frame & ~chip][:, None])
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
        # A fat red riser climbing the bay from deck to rail, flanged, as AS's lit halls have (lb-04).
        cx, rad = WW - 70, 24
        xx = np.arange(-rad, rad)
        sh = np.sqrt(np.clip(1 - (xx / rad) ** 2, 0, 1))
        light = 0.3 + 0.8 * sh * (0.65 + 0.35 * (-xx / rad)) + 0.5 * np.clip(1 - np.abs(xx / rad + 0.45) * 4, 0, 1)
        a[U1:K, cx - rad:cx + rad] = np.array((176, 40, 30), float)[None, None] * light[None, :, None]
        a[U1:K, cx + rad:cx + rad + 6] *= 0.5
        for y in range(U1 + 40, K - 20, 150):
            a[y:y + 14, cx - rad - 5:cx + rad + 5] = np.array((214, 170, 36)) * (0.6 + 0.5 * np.r_[sh[:5] * 0, sh, sh[:5] * 0][None, :, None] + 0.25)
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


def wall_concrete(seed=210):
    """A building's outer wall seen across the dock's drop (AS's concretewall080a): pale poured concrete in form
    panels with tie holes and rain streaks, a lit window or two (the colony is still awake), a dark plinth."""
    r = np.random.default_rng(seed)
    n = _noise(0, 60, seed, 4, (WH, WW)); f = _noise(0, 6, seed + 1, 2, (WH, WW))
    a = np.array((168, 166, 160), float)[None, None] * (0.88 + 0.14 * n[..., None] + 0.06 * f[..., None])
    emis = np.zeros((WH, WW, 3))
    for x in range(0, WW, 256):
        a[:, max(0, x - 1):x + 2] *= 0.6
    for y in (WH // 3, 2 * WH // 3):
        a[y - 1:y + 2] *= 0.65
    for x in range(64, WW, 128):
        for y in (WH // 6, WH // 2, 5 * WH // 6):
            yy, xx = np.mgrid[-5:6, -5:6]
            hole = (np.hypot(xx, yy) < 4.5)[..., None]
            a[y - 5:y + 6, x - 5:x + 6] = a[y - 5:y + 6, x - 5:x + 6] * (1 - 0.55 * hole)
    # A window: dark glass, a warm lit room behind it in one bay of two.
    if r.random() < 0.6:
        x0 = int(r.integers(60, WW - 220)); y0 = int(WH * 0.28)
        a[y0 - 6:y0 + 106, x0 - 6:x0 + 166] = (70, 72, 74)
        warm = np.array((255, 196, 120), float) * r.uniform(0.5, 0.9)
        a[y0:y0 + 100, x0:x0 + 160] = warm * 0.35
        emis[y0:y0 + 100, x0:x0 + 160] = warm * 0.55
        a[y0:y0 + 100, x0 + 78:x0 + 82] = (60, 62, 64); emis[y0:y0 + 100, x0 + 78:x0 + 82] = 0
    a[int(WH * 0.9):] *= 0.45
    a = _weather(a, seed + 3, 70, 0.04)
    return _img(a), (_img(emis) if emis.max() > 0 else None)


def wall_red(seed=220):
    """Deima's colony buildings (metalwall008c): red-painted corrugated steel panels between grey steel posts and
    rails, a riveted seam down each panel, rust and grime run from the rails, snow lying on the ledges."""
    yy, xx = np.mgrid[0:WH, 0:WW].astype(float)
    n = _noise(0, 40, seed, 4, (WH, WW))
    red = np.array((128, 38, 32), float)
    corr = 0.9 + 0.1 * np.sin(xx / 128.0 * np.pi * 16)
    a = red[None, None] * (0.82 + 0.3 * n[..., None]) * corr[..., None]
    # Paint worn to grey-brown steel in patches.
    worn = np.clip((_noise(0, 26, seed + 1, 4, (WH, WW)) - 0.62) * 4, 0, 1)
    a = a * (1 - worn[..., None]) + np.array((96, 84, 76))[None, None] * worn[..., None]
    steel = np.array((132, 136, 138), float)
    rails = (14, int(WH * 0.22), int(WH * 0.9))
    post = (np.abs(((xx + 64) % 128) - 64) < 7)
    for y in rails:
        a[y - 7:y + 7] = steel * (0.85 + 0.25 * n[y - 7:y + 7, :, None])
        a[y + 7:y + 10] *= 0.5
    a[post] = steel * (0.85 + 0.25 * n[post][:, None])
    a[(np.abs(((xx + 64) % 128) - 64) >= 7) & (np.abs(((xx + 64) % 128) - 64) < 9)] *= 0.55
    _rivets(a, [(x, y) for x in range(64, WW, 128) for y in range(40, WH - 40, 36)], (150, 150, 150), 3)
    a[int(WH * 0.9) + 7:] *= 0.55
    # Snow on the ledges: each rail carries a soft white line, a little spilt down.
    for y in rails[1:]:
        lip = np.clip(1 - np.abs(yy - (y - 8)) / 5.0, 0, 1) * (0.6 + 0.4 * _noise(0, 10, seed + y, 3, (WH, WW)))
        a = a * (1 - lip[..., None]) + np.array((210, 222, 236))[None, None] * lip[..., None]
    a = _weather(a, seed + 3, 60, 0.04)
    return _img(a), None


def wall_bluestripe(seed=230):
    """Rydberg's halls (concretewall082a): pale board-formed concrete, the planks' grain running across, a broad
    slate-blue band at head height with a pale pinstripe, a dark plinth stained by the floor's wash."""
    yy, xx = np.mgrid[0:WH, 0:WW].astype(float)
    n = _noise(0, 60, seed, 4, (WH, WW)); f = _noise(0, 4, seed + 1, 2, (WH, WW))
    a = np.array((176, 178, 172), float)[None, None] * (0.86 + 0.14 * n[..., None] + 0.05 * f[..., None])
    # Boards: a hairline every 40 px and a wood grain streaking each.
    grain = _noise(0, 3, seed + 2, 2, (WH, WW)) * 0.5 + 0.5 * np.sin(xx / 9.0 + _noise(0, 30, seed + 5, 2, (WH, WW)) * 8)
    a *= (0.95 + 0.06 * grain[..., None])
    for y in range(0, WH, 40):
        a[y:y + 2] *= 0.7
    y0, y1 = int(WH * 0.2), int(WH * 0.36)
    blue = np.array((62, 88, 108), float)
    worn = np.clip((_noise(0, 16, seed + 7, 3, (WH, WW)) - 0.68) * 4, 0, 1)
    band = blue[None, None] * (0.85 + 0.25 * n[y0:y1, :, None])
    a[y0:y1] = band * (1 - worn[y0:y1, :, None]) + a[y0:y1] * worn[y0:y1, :, None]
    a[y1 + 10:y1 + 16] = np.array((196, 200, 198)) * 0.95
    for x in range(0, WW, 256):
        a[:, max(0, x - 1):x + 2] *= 0.55
    for x in range(64, WW, 128):
        for y in (WH // 2, int(WH * 0.72)):
            a[y - 4:y + 4, x - 4:x + 4] *= 0.5
    a[int(WH * 0.88):] = a[int(WH * 0.88):] * 0.5 + np.array((50, 52, 50)) * 0.2
    a = _weather(a, seed + 3, 70, 0.04)
    return _img(a), None


def wall_rust(seed=240):
    """Rydberg's machinery bays (metalwall059a): heavy steel plate in orange primer gone to rust, welded seams,
    drips of rust under every bolt row, a hazard-striped kick plate."""
    yy, xx = np.mgrid[0:WH, 0:WW].astype(float)
    n = _noise(0, 40, seed, 4, (WH, WW))
    a = np.array((166, 78, 44), float)[None, None] * (0.8 + 0.35 * n[..., None])
    rust = np.clip((_noise(0, 22, seed + 1, 4, (WH, WW)) - 0.55) * 3, 0, 1)
    a = a * (1 - rust[..., None]) + np.array((92, 52, 34))[None, None] * (0.8 + 0.4 * n[..., None]) * rust[..., None]
    for x in range(0, WW, 256):
        a[:, max(0, x - 3):x + 3] *= 0.45
        a[:, x + 3:x + 5] *= 1.2
    for y in (int(WH * 0.12), int(WH * 0.55)):
        a[y - 3:y + 3] *= 0.45
        _rivets(a, [(x, y + 14) for x in range(20, WW, 40)], (150, 92, 60), 3)
        # rust run down from the bolts
        r = np.random.default_rng(seed + y)
        for x in range(20, WW, 40):
            ln = int(r.integers(30, 90))
            a[y + 18:y + 18 + ln, x - 1:x + 2] *= 0.75
    _hazard(a, 0, WW, int(WH * 0.86), WH, seed + 4)
    a = _weather(a, seed + 3, 50, 0.045)
    return _img(a), None


def tex_cap_snow(seed=6, size=512):
    """A colony roof under snow, as the camera sees Deima's buildings: drifted snow, the roof's seams and a vent box
    showing dark through it, grey where the wind has scoured it thin."""
    n = _noise(size, 70, seed); f = _noise(size, 8, seed + 1)
    a = np.array((182, 196, 214), float)[None, None] * (0.8 + 0.18 * n[..., None] + 0.04 * f[..., None])
    thin = np.clip((_noise(size, 30, seed + 2) - 0.6) * 3, 0, 1)
    a = a * (1 - 0.45 * thin[..., None])
    q = size // 2
    for k in range(0, size, q):
        a[k:k + 4] *= 0.78; a[:, k:k + 4] *= 0.78
    r = np.random.default_rng(seed)
    tx, ty = r.integers(40, size - 140, 2)
    a[ty:ty + 90, tx:tx + 110] *= 0.42
    a[ty + 6:ty + 84, tx + 6:tx + 104] *= 1.25
    return _img(a)


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
    # Dim: AS shows nothing past the walls but black, so the wall top is only a faint steel edge going dark.
    a = np.array((96, 100, 106), float)[None, None] * (0.9 + 0.15 * _noise(0, 4, seed, 2, (h, w))[..., None])
    a *= np.linspace(1.0, 0.2, h)[:, None, None]
    a[:2] *= 1.25
    return _img(a)


def tex_cap(seed=5, size=512):
    """The top of the hull as the camera sees it: dark blue-grey plating, conduits and vents."""
    n = _noise(size, 50, seed)
    # Near black, as everything outside AS's playable space is: only a ghost of plating catches the light.
    a = np.array((11, 12, 14), float)[None, None] * (0.8 + 0.4 * n[..., None])
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
        a[y - 9:y + 9] = np.array((20, 22, 24))[None, None] * (0.4 + 0.8 * s)[:, None, None]
    return _img(a)


def tex_machine(seed=31, size=512):
    """The top of machinery standing in a room (pump housings, tanks, crate stacks), four units square: lit grey
    plating in panels with vents, pipe runs, bolted hatches and a hazard-striped rim, as AS's rooms show from above."""
    r = np.random.default_rng(seed)
    a = np.array((104, 108, 110), float)[None, None] * (0.85 + 0.25 * _noise(size, 40, seed)[..., None])
    q = size // 4
    for k in range(0, size, q):
        a[k:k + 3] *= 0.4; a[:, k:k + 3] *= 0.4
        a[k + 3:k + 5] *= 1.25; a[:, k + 3:k + 5] *= 1.25
    for _ in range(5):
        tx, ty = r.integers(0, 4, 2) * q
        kind = r.integers(0, 3)
        if kind == 0:      # a vent grille
            a[ty + 18:ty + q - 18, tx + 18:tx + q - 18] *= 0.55
            for y in range(ty + 24, ty + q - 24, 9):
                a[y:y + 3, tx + 22:tx + q - 22] *= 1.7
        elif kind == 1:    # a bolted hatch with a yellow rim
            a[ty + 14:ty + q - 14, tx + 14:tx + q - 14] = np.array((190, 150, 34))
            a[ty + 22:ty + q - 22, tx + 22:tx + q - 22] = np.array((80, 82, 84)) * (0.9 + 0.2 * r.random())
        else:              # a dark access well
            a[ty + 26:ty + q - 26, tx + 26:tx + q - 26] *= 0.25
    for k in range(3):     # pipe runs across the top
        y = int(r.integers(24, size - 24))
        yy = np.arange(-10, 10); sh = np.sqrt(np.clip(1 - (yy / 10.0) ** 2, 0, 1))
        col = np.array((170, 44, 34) if k == 0 else (150, 152, 150))
        a[y - 10:y + 10] = col[None, None] * (0.35 + 0.85 * sh)[:, None, None]
    # The hazard-striped rim where it meets the deck below.
    yy, xx = np.mgrid[0:size, 0:size]
    band = (xx < 14) | (xx >= size - 14) | (yy < 14) | (yy >= size - 14)
    stripe = ((xx + yy) // 16) % 2 == 0
    a[band] = np.where(stripe[band][:, None], np.array((206, 160, 34)), np.array((30, 28, 26)))
    a = _weather(a, seed + 3, 30)
    return _img(a)


# ---- SynTek Residential (asi-jac4-residential: res_metalwall001a/b, concretefloor051c on its walls) ----
def _panels(a, x_step, y0, y1, seed, inset=14, depth=0.6, lite=1.15):
    """Framed panels between y0 and y1, x_step wide: a dark groove round each with a lit lower-right lip, a slight
    bulge in the middle (pressed sheet), a riveted corner each side."""
    for x in range(0, WW, x_step):
        x0, x1 = x + inset, x + x_step - inset
        a[y0:y1, x0 - 3:x0] *= depth; a[y0:y1, x1:x1 + 3] *= depth
        a[y0 - 3:y0, x0:x1] *= depth; a[y1:y1 + 3, x0:x1] *= depth
        a[y0:y1, x1 - 2:x1] *= lite; a[y1 - 2:y1, x0:x1] *= lite
        yy, xx = np.mgrid[y0:y1, x0:x1]
        bulge = 1 + 0.05 * np.sin((xx - x0) / max(1, x1 - x0) * math.pi) * np.sin((yy - y0) / max(1, y1 - y0) * math.pi)
        a[y0:y1, x0:x1] *= bulge[..., None]
        _rivets(a, [(x0 + 10, y0 + 10), (x1 - 10, y0 + 10), (x0 + 10, y1 - 10), (x1 - 10, y1 - 10)], (150, 160, 158), 3)


def wall_seagreen(seed=250, tone=(116, 160, 150), stripe=(214, 150, 74)):
    """res_metalwall001a: SynTek's housing blocks, pale sea-green pressed-steel panels two to a bay in a frame
    of flat bars, a worn orange band low down, a dark rubbed kick plate; damp grime run down from every ledge."""
    a = _wall_base(seed, tone, 256)
    U1, M0, L1 = int(WH * 0.05), int(WH * 0.62), int(WH * 0.88)
    a[:U1] *= 0.5; a[U1 - 3:U1] *= 1.6
    _panels(a, 256, U1 + 18, M0 - 8, seed)
    # The frame's flat bars: a vertical one between the panels, a little darker, each with its bolt line.
    for x in range(0, WW, 256):
        a[:, max(0, x - 10):x + 10] *= 0.86
        _rivets(a, [(x + 0, y) for y in range(U1 + 30, M0, 60)], (130, 146, 142), 3)
    _band(a, M0, M0 + 34, stripe, seed + 5, worn=0.35)
    _panels(a, 256, M0 + 42, L1 - 6, seed + 1)
    _kick(a, L1, seed + 2)
    a = _weather(a, seed + 3, 70, 0.04)
    return _img(a), None


def wall_seadark(seed=260):
    """res_metalwall001b: the same panels in dark gunmetal, where the block's service runs and back rooms are."""
    a = _wall_base(seed, (76, 82, 84), 256)
    U1, M0, L1 = int(WH * 0.05), int(WH * 0.62), int(WH * 0.88)
    a[:U1] *= 0.55; a[U1 - 3:U1] *= 1.7
    _panels(a, 256, U1 + 18, L1 - 8, seed, depth=0.55, lite=1.3)
    for x in range(0, WW, 256):
        a[:, max(0, x - 10):x + 10] *= 0.8
    a[M0:M0 + 6] *= 0.6
    _kick(a, L1, seed + 2)
    a = _weather(a, seed + 3, 60, 0.045)
    return _img(a), None


def wall_whitetile(seed=270):
    """concretefloor051c on the offices' and mall's walls: glazed white tiles a quarter unit square in grey grout,
    a few a shade off or cracked, grime gathered low and a steel skirting."""
    r = np.random.default_rng(seed)
    a = np.zeros((WH, WW, 3)) + np.array((206, 210, 208), float)
    a *= (0.95 + 0.06 * _noise(0, 40, seed, 3, (WH, WW)))[..., None]
    T = 64
    L1 = int(WH * 0.9)
    for ty in range(0, L1, T):
        for tx in range(0, WW, T):
            a[ty:ty + T, tx:tx + T] *= r.uniform(0.93, 1.04)
            if r.random() < 0.05:
                y = ty + int(r.integers(8, T - 8))
                a[y:y + 1, tx + 4:tx + T - 10] *= 0.7
    yy, xx = np.mgrid[0:WH, 0:WW]
    g = (xx % T < 3) | (yy % T < 3)
    a[g] = a[g] * 0.55 + np.array((60, 62, 60)) * 0.1
    gloss = np.clip(1 - np.abs((xx % T) - (yy % T) - 8) / 10.0, 0, 1) * ((xx % T) > 6) * ((yy % T) > 6)
    a *= (1 + 0.06 * gloss)[..., None]
    a[L1:] = np.array((96, 100, 102)) * (0.9 + 0.2 * _noise(0, 20, seed + 4, 3, (WH - L1, WW)))[..., None]
    a[L1:L1 + 3] *= 0.5
    foot = np.clip((yy - WH * 0.6) / (WH * 0.3), 0, 1) * _noise(0, 30, seed + 5, 3, (WH, WW))
    a *= (1 - 0.25 * foot)[..., None]
    a = _weather(a, seed + 3, 40, 0.025)
    return _img(a), None


SHOPS = [('PHARMACY', (40, 190, 120)), ('NOODLES', (230, 120, 50)), ('SYNTEK STORE', (60, 150, 230)), ('BAR', (220, 60, 90)),
         ('TOOLS', (230, 190, 60)), ('MED', (90, 220, 200))]


def wall_shop(seed=280, shop=0):
    """The mall's shopfronts: a lit sign box over a dark window full of shelves, a steel frame and a shutter
    rail, white tile beside it."""
    a = np.asarray(wall_whitetile(seed)[0]).astype(float)
    emis = np.zeros((WH, WW, 3))
    name, col = SHOPS[shop % len(SHOPS)]
    x0, x1 = 36, WW - 36
    sy0, sy1 = int(WH * 0.08), int(WH * 0.2)
    wy0, wy1 = int(WH * 0.26), int(WH * 0.84)
    a[sy0 - 8:wy1 + 8, x0 - 10:x1 + 10] = (52, 56, 58)
    # Sign: the colour behind white letters, lit.
    sign = np.array(col, float) * 0.85
    a[sy0:sy1, x0:x1] = sign; emis[sy0:sy1, x0:x1] = sign * 0.55
    _label(a, name, x0, x1, sy0, sy1, (250, 250, 240), 44)
    _label(emis, name, x0, x1, sy0, sy1, (200, 200, 190), 44)
    # Window: dark glass, shelves of goods in muted colours behind, a glare streak.
    r = np.random.default_rng(seed + shop)
    win = np.zeros((wy1 - wy0, x1 - x0, 3)) + np.array((22, 28, 32))
    for sh in range(4):
        y = 30 + sh * ((wy1 - wy0 - 40) // 4)
        win[y:y + 6] = (60, 62, 60)
        x = 10
        while x < x1 - x0 - 30:
            w = int(r.integers(14, 34)); h = int(r.integers(20, 60))
            c = np.array(r.choice([(150, 60, 50), (60, 110, 150), (200, 180, 90), (90, 140, 80), (180, 180, 170)]), float) * r.uniform(0.35, 0.6)
            win[max(0, y - h):y, x:x + w] = c
            x += w + int(r.integers(4, 14))
    yy, xx = np.mgrid[0:wy1 - wy0, 0:x1 - x0]
    glare = np.clip(1 - np.abs(((xx + yy * 0.7) % 260) - 70) / 18, 0, 1) * 0.25
    win = win * 0.8 + glare[..., None] * np.array((150, 170, 175))
    a[wy0:wy1, x0:x1] = win
    emis[wy0:wy1, x0:x1] = win * 0.25 + np.array(col) * 0.05
    # The shutter rail under the sign and the steel frame's mullions.
    a[wy0 - 10:wy0, x0:x1] = (90, 94, 96); a[wy0 - 10:wy0 - 8, x0:x1] *= 1.3
    for x in (x0, (x0 + x1) // 2, x1):
        a[wy0:wy1, x - 4:x + 4] = (70, 74, 76)
    a = _weather(a, seed + 3, 30, 0.03)
    return _img(a), _img(emis)


def wall_housing(seed=290, unit=4):
    """The block's flats along a corridor: a recessed apartment door with its number and a lit keypad, a small
    frosted window beside it, on the sea-green panels and orange band."""
    a = np.asarray(wall_seagreen(seed)[0]).astype(float)
    emis = np.zeros((WH, WW, 3))
    dx0, dx1, dy0, dy1 = 70, 250, int(WH * 0.12), int(WH * 0.88)
    a[dy0 - 10:dy1, dx0 - 10:dx1 + 10] = (58, 66, 66)
    door = np.array((150, 156, 150), float) * (0.85 + 0.2 * _noise(0, 20, seed + 6, 3, (dy1 - dy0, dx1 - dx0)))[..., None]
    a[dy0:dy1, dx0:dx1] = door
    a[dy0:dy1, (dx0 + dx1) // 2 - 2:(dx0 + dx1) // 2 + 2] *= 0.5
    a[dy0 + 60:dy0 + 66, dx0 + 12:dx1 - 12] *= 0.6
    _label(a, '%d%02d' % (2 + seed % 3, unit), dx0 + 20, dx1 - 20, dy0 + 14, dy0 + 56, (40, 46, 46), 34)
    # Keypad: a small lit green screen on the frame.
    a[int(WH * 0.45):int(WH * 0.52), dx1 + 16:dx1 + 40] = (30, 160, 90); emis[int(WH * 0.45):int(WH * 0.52), dx1 + 16:dx1 + 40] = (20, 140, 70)
    # Frosted window, the flat's light behind it.
    wx0, wx1, wy0, wy1 = 320, 470, int(WH * 0.16), int(WH * 0.44)
    a[wy0 - 8:wy1 + 8, wx0 - 8:wx1 + 8] = (70, 78, 78)
    lit = unit % 3 != 0
    glass = np.array((200, 196, 170) if lit else (70, 84, 90), float) * (0.85 + 0.2 * _noise(0, 16, seed + 7, 3, (wy1 - wy0, wx1 - wx0)))[..., None]
    a[wy0:wy1, wx0:wx1] = glass
    a[wy0:wy1, (wx0 + wx1) // 2 - 3:(wx0 + wx1) // 2 + 3] = (70, 78, 78)
    if lit:
        emis[wy0:wy1, wx0:wx1] = glass * 0.5
    a = _weather(a, seed + 3, 30, 0.03)
    return _img(a), _img(emis)



def _sewer_base(seed, tone=(126, 124, 114)):
    """concrete_sewers04: a sewer's poured walls, grey-beige concrete in form courses, the lower third stained dark
    by the water line with green-black algae over it, cracks and rust run from the form ties, the foot wet and
    darker still."""
    r = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:WH, 0:WW].astype(float)
    n = _noise(0, 60, seed, 5, (WH, WW)); f = _noise(0, 5, seed + 1, 3, (WH, WW))
    a = np.array(tone, float)[None, None] * (0.86 + 0.18 * n[..., None] + 0.08 * f[..., None])
    # Form courses: a faint joint every quarter of the height, each course its own shade.
    for k, y in enumerate(range(0, WH, WH // 4)):
        a[y:y + WH // 4] *= r.uniform(0.94, 1.05)
        a[max(0, y - 1):y + 2] *= 0.72
        a[y + 2:y + 3] *= 1.08
    # Patches of render fallen away: lighter rough blotches with a dark lip.
    spall = _noise(0, 40, seed + 2, 4, (WH, WW))
    sp = np.clip((spall - 0.66) * 6, 0, 1)
    lip = np.clip(1 - np.abs(spall - 0.66) * 40, 0, 1)
    a = a * (1 + 0.06 * sp[..., None]) * (1 - 0.12 * lip[..., None])
    # Cracks, mostly up and down.
    im = Image.new('L', (WW, WH), 0); d = ImageDraw.Draw(im)
    for _ in range(5):
        x, y = r.uniform(0, WW), r.uniform(0, WH * 0.6); pts = [(x, y)]
        for _ in range(int(r.integers(6, 18))):
            x += r.normal(0, 5); y += r.uniform(6, 16); pts.append((x, y))
        d.line(pts, fill=int(r.integers(140, 230)), width=int(r.choice([1, 1, 2])))
    a *= (1 - 0.45 * np.asarray(im).astype(float)[..., None] / 255)
    # Form ties, each weeping rust.
    for x in range(64, WW, 128):
        for y in (WH // 8, 3 * WH // 8):
            yy2, xx2 = np.mgrid[-5:6, -5:6]
            hole = (np.hypot(xx2, yy2) < 4.0)[..., None]
            a[y - 5:y + 6, x - 5:x + 6] *= (1 - 0.5 * hole)
            ln = int(r.integers(40, 140))
            run = np.linspace(0.4, 0.0, ln)[:, None] * np.clip(1 - np.abs(np.arange(-4, 5)) / 4.5, 0, 1)[None]
            ys, ye = y + 5, min(WH, y + 5 + ln)
            sl = a[ys:ye, x - 4:x + 5]
            k = run[:ye - ys, :, None]
            sl[:] = sl * (1 - k) + np.array((120, 64, 30), float) * k
    # The water line: below it the wall is dark and slimy, the line itself ragged, with tide marks above.
    wl = WH * 0.62 + (_noise(0, 30, seed + 3, 3, (1, WW))[0] - 0.5) * 30
    below = np.clip((yy - wl[None, :]) / 10.0, 0, 1)
    algae = np.array((44, 56, 36), float)
    blot = 0.35 + 0.9 * _noise(0, 14, seed + 4, 4, (WH, WW)) * (0.7 + 0.3 * _noise(0, 3, seed + 6, 2, (WH, WW)))
    a = a * (1 - 0.62 * below[..., None]) + algae * blot[..., None] * 0.62 * below[..., None]
    # Drips of it run up the wall's pores above the line and down from every ledge.
    drip = _noise(0, 3, seed + 7, 1, (1, WW)).repeat(WH, 0)
    drip = np.clip((drip - 0.62) * 5, 0, 1) * np.clip(1 - (wl[None, :] - yy) / 90.0, 0, 1) * (yy < wl[None, :])
    a *= (1 - 0.35 * drip)[..., None]
    for k in (14, 30, 52):
        tide = np.clip(1 - np.abs(yy - (wl[None, :] - k)) / 2.5, 0, 1) * (0.5 + 0.5 * _noise(0, 10, seed + k, 3, (WH, WW)))
        a *= (1 - 0.18 * tide)[..., None]
    a[int(WH * 0.92):] *= 0.55
    return _weather(a, seed + 5, 90, 0.045)


def wall_sewer(seed=300):
    return _img(_sewer_base(seed)), None


def wall_sewerpipe(seed=310):
    """The sewer wall with its mains: two great pipes along it, dark green paint gone to rust, flanged and bolted
    every bay, a valve wheel on the lower one, brackets into the concrete."""
    r = np.random.default_rng(seed)
    a = _sewer_base(seed)
    for cy, rad, col in ((int(WH * 0.3), 46, (62, 84, 66)), (int(WH * 0.55), 34, (90, 84, 70))):
        _cylinder(a, cy, rad, col, 0.35)
        rust = np.clip((_noise(0, 16, seed + cy, 4, (2 * rad, WW)) - 0.55) * 3, 0, 1)
        a[cy - rad:cy + rad] = a[cy - rad:cy + rad] * (1 - 0.6 * rust[..., None]) + np.array((110, 62, 32)) * 0.6 * rust[..., None]
        for x in (int(WW * 0.25), int(WW * 0.75)):
            fl = a[cy - rad - 6:cy + rad + 6, x - 9:x + 9]
            fl *= 0.8
            fl[:, :3] *= 0.6; fl[:, -3:] *= 1.25
            _rivets(a, [(x, cy - rad - 2), (x, cy + rad + 2), (x, cy)], (110, 108, 100), 3)
        for x in (int(WW * 0.5),):
            a[cy + rad:cy + rad + 40, x - 8:x + 8] = (70, 68, 64)
            a[cy + rad:cy + rad + 40, x - 8:x - 5] *= 0.6
    # The valve wheel.
    cx, cy = int(WW * 0.62), int(WH * 0.55)
    yy, xx = np.mgrid[-40:41, -40:41]
    d = np.hypot(xx, yy)
    ring = (np.abs(d - 32) < 4) | ((np.abs(xx) < 3) | (np.abs(yy) < 3)) & (d < 32) | (d < 7)
    sl = a[cy - 40:cy + 41, cx - 40:cx + 41]
    sl[ring] = np.array((150, 40, 30), float) * (0.8 + 0.4 * (-yy[ring] / 40.0))[:, None]
    return _img(_weather(a, seed + 7, 30, 0.02)), None


def wall_seweroutlet(seed=320):
    """An outfall in the sewer wall: a round culvert mouth barred with a rusted grate, black inside, a trickle of
    water and slime run from its lip down the wall to the channel, the concrete round it stained."""
    a = _sewer_base(seed)
    yy, xx = np.mgrid[0:WH, 0:WW].astype(float)
    cx, cy, rad = WW / 2, WH * 0.55, 120
    d = np.hypot(xx - cx, yy - cy)
    collar = (d < rad + 22) & (d >= rad)
    a[collar] *= 0.78
    a[(d < rad + 24) & (d >= rad + 20)] *= 0.6
    inside = d < rad
    depth = np.clip(1 - d / rad, 0, 1)
    a[inside] = (np.array((20, 22, 18), float)[None] * (1.2 - 0.8 * depth[inside][:, None]))
    bars = inside & ((np.abs((xx - cx) % 36 - 18) < 4) | (np.abs(yy - cy) < 5))
    a[bars] = np.array((88, 60, 40), float)[None] * (0.7 + 0.5 * _noise(0, 10, seed + 1, 3, (WH, WW))[bars][:, None])
    # The trickle: from the lip down, slime-green, widening.
    lip = cy + rad
    run = np.clip(1 - np.abs(xx - cx - (_noise(0, 40, seed + 2, 3, (WH, WW)) - 0.5) * 30) / np.maximum(1.0, 10 + (yy - lip) * 0.05), 0, 1) * (yy > lip - 10)
    slime = np.array((92, 120, 40), float)
    a = a * (1 - 0.6 * run[..., None]) + slime * 0.6 * run[..., None]
    emis = slime[None, None] * (0.12 * run)[..., None]
    stain = np.clip(1 - np.abs(d - rad - 30) / 30, 0, 1) * (yy > cy)
    a *= (1 - 0.25 * stain)[..., None]
    return _img(a), _img(emis)


def wall_sewerslime(seed=330):
    """The swarm in the sewer: its growth spread over the concrete, slick yellow-green slime and dark veined skin,
    pale sacs glowing in it (asw_alien_goo, toxicslime)."""
    a = _sewer_base(seed)
    yy, xx = np.mgrid[0:WH, 0:WW].astype(float)
    n = _noise(0, 70, seed, 5, (WH, WW))
    # More growth low down, where it climbs out of the channel.
    cover = np.clip((n + (yy / WH) * 0.5 - 0.55) * 3, 0, 1)
    vein = np.clip(1 - np.abs(_noise(0, 14, seed + 1, 4, (WH, WW)) - 0.5) * 14, 0, 1)
    skin = np.array((52, 40, 46), float) * (0.8 + 0.4 * _noise(0, 8, seed + 2, 3, (WH, WW)))[..., None]
    skin = skin * (1 - 0.5 * vein[..., None]) + np.array((120, 60, 90), float) * 0.5 * vein[..., None]
    slick = np.clip((_noise(0, 30, seed + 3, 4, (WH, WW)) - 0.55) * 4, 0, 1) * cover
    col = skin * (1 - slick[..., None]) + np.array((150, 190, 40), float) * slick[..., None]
    a = a * (1 - cover[..., None]) + col * cover[..., None]
    emis = np.array((150, 200, 40), float)[None, None] * (0.35 * slick ** 2)[..., None]
    r = np.random.default_rng(seed)
    for _ in range(9):
        x, y = r.uniform(30, WW - 30), r.uniform(WH * 0.35, WH * 0.9)
        if cover[int(y), int(x)] < 0.5:
            continue
        rad = r.uniform(8, 20)
        d = np.hypot(xx - x, (yy - y) * 1.3)
        sac = np.clip(1 - d / rad, 0, 1)
        a = a * (1 - sac[..., None]) + np.array((210, 220, 150), float) * sac[..., None] * (0.6 + 0.4 * sac[..., None])
        emis += np.array((140, 220, 60), float)[None, None] * (0.6 * sac ** 2)[..., None]
    return _img(a), _img(emis)


def wall_sewerlamp(seed=340):
    """A junction's marked bay: a caged bulkhead lamp burning sodium-yellow over a stencilled section number and
    a band of hazard stripes at the walkway's edge."""
    a = _sewer_base(seed)
    emis = np.zeros((WH, WW, 3))
    cx, cy = WW // 2, int(WH * 0.2)
    yy, xx = np.mgrid[0:WH, 0:WW].astype(float)
    a[cy - 34:cy + 34, cx - 60:cx + 60] = (60, 60, 56)
    glass = (np.abs(yy - cy) < 26) & (np.abs(xx - cx) < 50)
    warm = np.array((255, 200, 110), float)
    a[glass] = warm * 0.85
    emis[glass] = warm
    cage = glass & (((xx - cx) % 20 < 3) | (np.abs(yy - cy) < 2))
    a[cage] = (50, 50, 46); emis[cage] = 0
    halo = np.clip(1 - np.hypot((xx - cx) / 200, (yy - cy) / 150), 0, 1) ** 2
    a *= (1 + 0.5 * halo)[..., None]
    _label(a, 'B5', cx - 120, cx + 120, int(WH * 0.33), int(WH * 0.48), (226, 220, 200), 82)
    _hazard(a, 0, WW, int(WH * 0.56), int(WH * 0.6), seed + 1)
    return _img(a), _img(emis)


# ---- Timor Station (tools/timor.py) ---------------------------------------------------------------------------------
def _minerock_base(seed, tone=(92, 98, 84)):
    """minerockwall: the mine's hewn rock, green-grey with rust-brown veins, in rough benches where the drills cut
    it, cracked, darker in its hollows, gravel heaped at the foot."""
    r = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:WH, 0:WW].astype(float)
    n = _noise(0, 50, seed, 5, (WH, WW)); f = _noise(0, 5, seed + 1, 3, (WH, WW))
    a = np.array(tone, float)[None, None] * (0.72 + 0.4 * n[..., None] + 0.12 * f[..., None])
    # Benches: a few ragged ledges across the face, lit on top, shadowed under.
    for y in sorted(r.uniform(WH * 0.12, WH * 0.75, 3)):
        edge = y + (_noise(0, 40, seed + int(y), 3, (1, WW))[0] - 0.5) * 40
        under = np.clip((yy - edge[None, :]) / 22.0, 0, 1) * np.clip(1 - (yy - edge[None, :]) / 60.0, 0, 1)
        a *= (1 - 0.35 * under)[..., None]
        a *= (1 + 0.1 * np.clip(1 - np.abs(yy - edge[None, :] + 4) / 5.0, 0, 1))[..., None]
    vein = np.clip(1 - np.abs(_noise(0, 40, seed + 2, 4, (WH, WW)) - 0.5) * 16, 0, 1) * np.clip((_noise(0, 70, seed + 3, 3, (WH, WW)) - 0.45) * 3, 0, 1)
    a = a * (1 - 0.5 * vein[..., None]) + np.array((126, 84, 48), float) * 0.5 * vein[..., None]
    im = Image.new('L', (WW, WH), 0); d = ImageDraw.Draw(im)
    for _ in range(9):
        x, y = r.uniform(0, WW), r.uniform(0, WH * 0.8); pts = [(x, y)]
        for _ in range(int(r.integers(5, 14))):
            x += r.normal(0, 9); y += r.uniform(5, 14); pts.append((x, y))
        d.line(pts, fill=int(r.integers(140, 240)), width=int(r.choice([1, 2, 2, 3])))
    a *= (1 - 0.55 * np.asarray(im).astype(float)[..., None] / 255)
    hollow = np.clip((_noise(0, 30, seed + 4, 4, (WH, WW)) - 0.62) * 4, 0, 1)
    a *= (1 - 0.4 * hollow)[..., None]
    # Gravel heaped along the foot.
    foot = WH * 0.86 + (_noise(0, 30, seed + 5, 3, (1, WW))[0] - 0.5) * 30
    pile = yy > foot[None, :]
    a[pile] = a[pile] * 0.55 + np.array((86, 82, 72), float) * 0.45 * (0.7 + 0.6 * f[pile])[..., None]
    return _weather(a, seed + 6, 20, 0.06)


def wall_minerock(seed=350):
    return _img(_minerock_base(seed)), None


def wall_minebeam(seed=360):
    """A mine bay shored up: a steel portal set against the rock, two I-beam legs and a header, their paint gone to
    rust, chocked with timber, a caged lamp burning yellow on the header and a cable slung along it."""
    a = _minerock_base(seed)
    emis = np.zeros((WH, WW, 3))
    yy, xx = np.mgrid[0:WH, 0:WW].astype(float)
    steel = np.array((96, 84, 60), float)
    top = int(WH * 0.12)
    for x0 in (14, WW - 62):
        leg = a[top:, x0:x0 + 48]
        leg[:] = steel * (0.85 + 0.3 * _noise(0, 10, seed + x0, 3, (WH - top, 48))[..., None])
        leg[:, :8] *= 1.25; leg[:, 40:] *= 0.6; leg[:, 20:28] *= 0.8
    hdr = a[top:top + 46]
    hdr[:] = steel * (0.85 + 0.3 * _noise(0, 10, seed + 9, 3, (46, WW))[..., None])
    hdr[:8] *= 1.25; hdr[38:] *= 0.55
    a[top + 46:top + 56] *= 0.5
    rust = np.clip((_noise(0, 20, seed + 3, 4, (WH, WW)) - 0.55) * 3, 0, 1)
    metal = np.zeros((WH, WW), bool); metal[top:, 14:62] = True; metal[top:, WW - 62:WW - 14] = True; metal[top:top + 46] = True
    k = (rust * metal)[..., None] * 0.6
    a = a * (1 - k) + np.array((118, 62, 30), float) * k
    _rivets(a, [(x, top + 23) for x in range(40, WW - 30, 48)], (120, 108, 84), 4)
    # Timber chocks between header and rock.
    for x in range(90, WW - 90, 70):
        a[top - 30:top, x:x + 34] = np.array((96, 70, 44), float) * (0.8 + 0.4 * _noise(0, 4, seed + x, 2, (30, 34))[..., None])
        a[top - 30:top, x + 30:x + 34] *= 0.6
    # The cable, sagging between hangers.
    for x in range(WW):
        y = int(top + 70 + 16 * (1 - ((x % 170) / 85.0 - 1) ** 2))
        a[y:y + 5, x] = (30, 30, 28)
    _hazard(a, 62, WW - 62, top + 46, top + 56, seed + 1, 14)
    cx, cy = WW // 2, top + 90
    a[cy - 22:cy + 22, cx - 34:cx + 34] = (52, 50, 44)
    glass = (np.abs(yy - cy) < 16) & (np.abs(xx - cx) < 26)
    warm = np.array((255, 196, 100), float)
    a[glass] = warm * 0.85; emis[glass] = warm
    cage = glass & ((((xx - cx) % 13) < 2) | (np.abs(yy - cy) < 2))
    a[cage] = (44, 42, 38); emis[cage] = 0
    halo = np.clip(1 - np.hypot((xx - cx) / 220, (yy - cy) / 170), 0, 1) ** 2
    a *= (1 + 0.6 * halo)[..., None]
    return _img(_weather(a, seed + 7, 30, 0.03)), _img(emis)


def _boards(seed, tone=(138, 138, 134)):
    """concretewall082: board-formed concrete, the grain of each plank pressed into it in level courses, tie holes
    in a grid, the odd course a shade off, rain streaks and the mine's dust low down."""
    r = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:WH, 0:WW].astype(float)
    n = _noise(0, 60, seed, 4, (WH, WW)); f = _noise(0, 5, seed + 1, 2, (WH, WW))
    a = np.array(tone, float)[None, None] * (0.86 + 0.14 * n[..., None] + 0.06 * f[..., None])
    step = WH // 12
    for y in range(0, WH, step):
        a[y:y + step] *= r.uniform(0.93, 1.06)
        a[y:y + 2] *= 0.72
        grain = _noise(0, 3, seed + y, 2, (step, WW // 8))
        grain = np.asarray(Image.fromarray((grain * 255).astype(np.uint8)).resize((WW, step), Image.BICUBIC)).astype(float) / 255
        a[y:y + step] *= (0.95 + 0.1 * grain[:a[y:y + step].shape[0]])[..., None]
    for x in (0, WW // 2):
        a[:, max(0, x - 1):x + 2] *= 0.75
    for x in range(64, WW, 128):
        for y in range(step * 2, WH, step * 4):
            hole = (np.hypot(xx[y - 6:y + 7, x - 6:x + 7] - x, yy[y - 6:y + 7, x - 6:x + 7] - y) < 4.5)[..., None]
            a[y - 6:y + 7, x - 6:x + 7] *= (1 - 0.6 * hole)
    dust = np.clip((yy - WH * 0.7) / (WH * 0.3), 0, 1) ** 1.5 * (0.6 + 0.6 * n)
    a = a * (1 - 0.35 * dust[..., None]) + np.array((110, 98, 80), float) * 0.35 * dust[..., None]
    return a


def wall_timorconc(seed=370):
    a = _boards(seed)
    a[int(WH * 0.92):] *= 0.5
    return _img(_weather(a, seed + 3, 60, 0.04)), None


def wall_timorband(seed=380):
    """concretewall080c: the station's halls, smooth concrete in two panels with a painted steel-blue band across
    it at hand height, chipped to the concrete along its edges, TIMOR stencilled over it."""
    n = _noise(0, 60, seed, 4, (WH, WW)); f = _noise(0, 6, seed + 1, 2, (WH, WW))
    a = np.array((170, 170, 166), float)[None, None] * (0.88 + 0.12 * n[..., None] + 0.05 * f[..., None])
    a[:, WW // 2 - 2:WW // 2 + 2] *= 0.7
    y0, y1 = int(WH * 0.5), int(WH * 0.8)
    _band(a, y0, y1, (66, 112, 146), seed + 2, 0.18)
    for x in range(64, WW, 128):
        for y in (int(WH * 0.12), int(WH * 0.38)):
            yy, xx = np.mgrid[-5:6, -5:6]
            a[y - 5:y + 6, x - 5:x + 6] *= (1 - 0.55 * (np.hypot(xx, yy) < 4.5))[..., None]
    _label(a, 'TIMOR', 40, WW - 40, int(WH * 0.22), int(WH * 0.34), (60, 70, 78), 70)
    a[int(WH * 0.9):] *= 0.5
    return _img(_weather(a, seed + 3, 70, 0.04)), None


# tools/level.py KIT_WALLS names -> the bay drawn for it.
WALLS = {'wall_plain0': ('clean', 100), 'wall_plain1': ('colony', 101), 'wall_pipes2': ('pipes', 102), 'wall_vent3': ('vent', 103),
         'wall_screen4': ('screen', 104), 'wall_light5': ('light', 105), 'wall_alarm6': ('alarm', 106)}


def textures():
    out = {name: wall_art(kind, seed) for name, (kind, seed) in WALLS.items()}
    out['wall_hive'] = wall_hive()
    out['wall_concrete'] = wall_concrete()
    out['wall_red'] = wall_red()
    out['cap_snow'] = (tex_cap_snow(), None)
    out['wall_bluestripe'] = wall_bluestripe()
    out['wall_rust'] = wall_rust()
    out['wall_seagreen'] = wall_seagreen()
    out['wall_seadark'] = wall_seadark()
    out['wall_whitetile'] = wall_whitetile()
    for k in range(3):
        out['wall_shop%d' % k] = wall_shop(280 + k, k * 2 + (k > 0))
    out['wall_housing'] = wall_housing()
    out['wall_sewer'] = wall_sewer()
    out['wall_sewerpipe'] = wall_sewerpipe()
    out['wall_seweroutlet'] = wall_seweroutlet()
    out['wall_sewerslime'] = wall_sewerslime()
    out['wall_sewerlamp'] = wall_sewerlamp()
    out['wall_minerock'] = wall_minerock()
    out['wall_minebeam'] = wall_minebeam()
    out['wall_timorconc'] = wall_timorconc()
    out['wall_timorband'] = wall_timorband()
    out['wall_trim'] = (tex_trim(), None)
    out['cap'] = (tex_cap(), None)
    out['machine_top'] = (tex_machine(), None)
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
