"""The freight elevator's art: scrolling shaft panels, gates, bridges, the platform,
the black drop round it, and the security door; textures drawn here, meshes written
with tools/shipkit.py's M3 writer.

The shaft is the trick of the mission (src/Mission.galaxy): the platform is fixed
floor and these panels slide upward past it. Every panel hangs BELOW its unit's
origin (z from -DROP to -DROP + PANEL_H), so a panel unit at height h shows from
h - DROP up to h - DROP + PANEL_H; whatever is under the deck is hidden by the
terrain, so panels rise out of the floor line and scroll up out of the camera.
Panels are authored facing south (face normal -Y, the way SC2 lays -Y along a
unit's facing), origin at the top middle of the face, and are two-sided so the
lobby and junction see the shaft's back.
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from tools.shipkit import ShipModel, _noise, _grime, _hazard, _img, NO_SHADOW_CAST

PANEL_H = 6.0          # height of one shaft panel
DROP = 6.0             # how far a panel hangs below its unit's origin
GATE_H = 3.5           # the lift gates' opening height


def _font(size):
    for name in ('C:/Windows/Fonts/bahnschrift.ttf', 'C:/Windows/Fonts/arialbd.ttf', 'C:/Windows/Fonts/arial.ttf'):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _stencil(img, text, xy, size, fill, anchor='mm'):
    d = ImageDraw.Draw(img)
    d.text(xy, text, font=_font(size), fill=fill, anchor=anchor)
    return img


# ------------------------------------------------------------- textures
def tex_shaft(seed, lights=False, w=512, h=768):
    """One shaft panel, 4 units wide by 6 tall: guide rails at the edges, two heavy girders,
    rivets, grime; the lit variant carries a run of amber caged lamps on its girder."""
    base = np.array((64, 66, 62), float)
    n = _noise(0, 60, seed, 4, (h, w)); f = _noise(0, 7, seed + 3, 2, (h, w))
    a = base[None, None] * (0.78 + 0.3 * n[..., None] + 0.08 * f[..., None])
    emis = np.zeros((h, w, 3))
    # Vertical guide rails, the lift's rollers run in them.
    for x0 in (0, w - 34):
        a[:, x0:x0 + 34] = np.array((48, 50, 50)) * (0.85 + 0.25 * n[:, x0:x0 + 34, None])
        a[:, x0 + 8:x0 + 26] *= 1.35
        a[:, x0 + 15:x0 + 19] *= 0.5
    # Plate seams every half panel, horizontal.
    for y in (0, h // 2):
        a[y:y + 4] *= 0.35
    # Girders: an I-beam across the top third and one across the bottom.
    for gy in (int(h * 0.18), int(h * 0.70)):
        a[gy - 26:gy + 26] = np.array((70, 64, 52)) * (0.8 + 0.3 * n[gy - 26:gy + 26, :, None])
        a[gy - 26:gy - 20] *= 1.4; a[gy + 20:gy + 26] *= 0.45; a[gy - 6:gy + 6] *= 0.75
        for x in range(40, w - 40, 28):
            a[gy - 16:gy - 11, x:x + 6] = (150, 140, 120); a[gy + 11:gy + 16, x:x + 6] = (150, 140, 120)
        if lights:
            for x in range(70, w - 60, 124):
                a[gy - 14:gy + 14, x - 4:x + 34] = (30, 28, 24)
                a[gy - 10:gy + 10, x:x + 30] = (255, 190, 90)
                emis[gy - 10:gy + 10, x:x + 30] = (255, 160, 60)
                for k in range(3):
                    a[gy - 12:gy + 12, x + 4 + k * 10:x + 6 + k * 10] = (40, 36, 30)
    # Hazard band low down, where the platform's edge runs past.
    _hazard(a, int(h * 0.88), int(h * 0.94), seed)
    # Wet streaks running down from the girders.
    streak = _noise(0, 4, seed + 9, 1, (1, w)).repeat(h, 0)
    a *= (1 - 0.25 * np.clip(streak - 0.4, 0, 1) * np.linspace(0.3, 1, h)[:, None])[..., None]
    a = _grime(a, seed + 11, 0.4)
    return _img(a), (_img(emis) if emis.max() > 0 else None)


def tex_sign(seed=83, w=512, h=768):
    """A signed panel: downward chevrons and a stencilled warning, bundled cables down one side.
    Big shapes scrolling past read as speed better than repeated girders."""
    img, _ = tex_shaft(seed)
    a = np.asarray(img).astype(float)
    emis = np.zeros((h, w, 3))
    # Cable bundle down the left of the guide rail.
    for k, col in enumerate([(30, 30, 28), (70, 20, 16), (24, 40, 60), (36, 36, 30)]):
        x0 = 44 + k * 9
        a[:, x0:x0 + 7] = np.array(col) * (0.8 + 0.4 * _noise(0, 30, seed + k, 2, (h, 7))[..., None])
        a[:, x0 + 2:x0 + 3] *= 1.6
    # A sign board with chevrons pointing down and amber edge lights.
    y0, y1, x0, x1 = int(h * 0.30), int(h * 0.62), 110, w - 60
    a[y0:y1, x0:x1] = (24, 24, 22)
    a[y0:y0 + 6, x0:x1] = (255, 170, 60); emis[y0:y0 + 6, x0:x1] = (255, 140, 40)
    a[y1 - 6:y1, x0:x1] = (255, 170, 60); emis[y1 - 6:y1, x0:x1] = (255, 140, 40)
    img = _img(a)
    d = ImageDraw.Draw(img)
    cx = (x0 + x1) // 2
    for k in range(3):
        top = y0 + 30 + k * 40
        d.polygon([(cx - 90, top), (cx - 60, top), (cx, top + 34), (cx + 60, top), (cx + 90, top), (cx, top + 64)], fill=(190, 140, 30))
    d.text((cx, y1 - 60), 'CAUTION', font=_font(48), fill=(220, 210, 190), anchor='mm')
    d.text((cx, y1 - 22), 'MOVING PLATFORM', font=_font(28), fill=(220, 210, 190), anchor='mm')
    return img, _img(emis)


def tex_lintel(w=512, h=768):
    """The door piece: the lower 3.5 units are the opening; above it a hazard lintel and the lift's sign."""
    img, _ = tex_shaft(91)
    a = np.asarray(img).astype(float)
    top = int(h * (1 - GATE_H / PANEL_H))
    a[top - 70:top] = np.array((40, 40, 36))
    _hazard(a, top - 60, top - 10, 3)
    emis = np.zeros((h, w, 3))
    a[top - 190:top - 90, 90:w - 90] = (16, 18, 18)
    img = _img(a)
    _stencil(img, 'CARGO LIFT 01', (w // 2, top - 140), 44, (255, 180, 60))
    e = Image.fromarray(emis.astype(np.uint8))
    _stencil(e, 'CARGO LIFT 01', (w // 2, top - 140), 44, (255, 150, 40))
    return img, e


def tex_gate(seed=7, w=256, h=448):
    """One gate leaf: heavy plating with a hazard chevron and a status lamp."""
    n = _noise(0, 40, seed, 4, (h, w))
    a = np.array((78, 76, 66), float)[None, None] * (0.8 + 0.3 * n[..., None])
    for y in range(0, h, h // 6):
        a[y:y + 3] *= 0.4
    a[:, :6] *= 0.4; a[:, -6:] *= 0.4
    _hazard(a, int(h * 0.42), int(h * 0.58), seed)
    emis = np.zeros((h, w, 3))
    a[30:54, w // 2 - 12:w // 2 + 12] = (255, 70, 40); emis[30:54, w // 2 - 12:w // 2 + 12] = (255, 50, 20)
    return _img(_grime(a, seed + 2, 0.35)), _img(emis)


def tex_deck(w=1024, h=1024):
    """The platform: diamond plate, a hazard border, painted arrows and the lift number."""
    yy, xx = np.mgrid[0:h, 0:w]
    n = _noise(0, 80, 41, 4, (h, w))
    a = np.array((84, 86, 80), float)[None, None] * (0.75 + 0.3 * n[..., None])
    diamond = (((xx + yy) // 6) % 8 == 0) | (((xx - yy) // 6) % 8 == 0)
    a[diamond] *= 1.22
    for k in range(0, w, w // 3):
        a[:, k:k + 4] *= 0.4; a[k:k + 4] *= 0.4
    border = 40
    for y0, y1, x0, x1 in [(0, border, 0, w), (h - border, h, 0, w), (0, h, 0, border), (0, h, w - border, w)]:
        sub = a[y0:y1, x0:x1]
        ys, xs = np.mgrid[y0:y1, x0:x1]
        stripe = ((xs + ys) // 22) % 2 == 0
        sub[:] = np.where(stripe[..., None], np.array((170, 130, 30), float), np.array((26, 26, 24), float)) * (0.6 + 0.5 * n[y0:y1, x0:x1, None])
    img = _img(_grime(a, 43, 0.3))
    d = ImageDraw.Draw(img)
    # Lift number and load marking, worn.
    d.text((w // 2, h // 2), '01', font=_font(300), fill=(150, 120, 40), anchor='mm')
    d.text((w // 2, h // 2 + 200), 'MAX LOAD 40 T', font=_font(54), fill=(150, 120, 40), anchor='mm')
    for cx in (w // 2 - 330, w // 2 + 330):
        d.polygon([(cx - 50, h // 2 + 40), (cx + 50, h // 2 + 40), (cx, h // 2 - 60)], fill=(150, 120, 40))
    a = np.asarray(img).astype(float) * (1 - 0.35 * np.clip(_noise(0, 30, 47, 3, (h, w)) - 0.5, 0, 1))[..., None]
    return _img(a), None


def tex_bridge(w=256, h=512):
    yy, xx = np.mgrid[0:h, 0:w]
    a = np.full((h, w, 3), 30.0)
    grate = ((xx % 16) < 3) | ((yy % 16) < 3)
    a[grate] = (96, 96, 90)
    a[:, :24] = (150, 120, 30); a[:, -24:] = (150, 120, 30)
    a[:, :24][((yy[:, :24] + xx[:, :24]) // 16) % 2 == 0] = (26, 26, 24)
    a[:, -24:][((yy[:, -24:] + xx[:, -24:]) // 16) % 2 == 0] = (26, 26, 24)
    return _img(_grime(a, 51, 0.3)), None


def tex_door(w=256, h=320):
    """Security door leaf: plating, a stencilled warning, a red lock lamp."""
    n = _noise(0, 40, 61, 4, (h, w))
    a = np.array((72, 78, 84), float)[None, None] * (0.8 + 0.3 * n[..., None])
    for y in range(0, h, h // 5):
        a[y:y + 3] *= 0.45
    a[:, :5] *= 0.4; a[:, -5:] *= 0.4
    _hazard(a, int(h * 0.80), int(h * 0.90), 4)
    emis = np.zeros((h, w, 3))
    a[24:44, 20:60] = (255, 50, 30); emis[24:44, 20:60] = (255, 40, 20)
    img = _img(_grime(a, 63, 0.3))
    _stencil(img, 'SECURITY', (w // 2, int(h * 0.45)), 34, (210, 210, 200))
    return img, _img(emis)


def tex_window(seed=301, size=(512, 640)):
    """A hull wall with a long observation window: dark glass, reflections, the hangar's faint lights."""
    from tools.wallart import wall_art
    plate, _ = wall_art('dark', seed)            # the deck's own bulkhead (tools/wallart.py)
    a = np.asarray(plate).astype(float)
    w, h = size
    y0, y1 = int(h * 0.30), int(h * 0.62)
    a[y0 - 10:y1 + 10, 14:w - 14] = (34, 36, 38)
    glass = np.zeros((y1 - y0, w - 40, 3)) + np.array((10, 16, 20))
    yy, xx = np.mgrid[0:y1 - y0, 0:w - 40]
    glare = np.clip(1 - np.abs((xx - yy * 1.6) % 220 - 60) / 30, 0, 1) * 0.35
    glass += glare[..., None] * np.array((90, 110, 120))
    emis = np.zeros((h, w, 3))
    for gx in (80, 260, 420):
        if gx < w - 40:
            spot = np.clip(1 - np.hypot(xx - gx, yy - (y1 - y0) * 0.7) / 26, 0, 1) ** 2
            glass += spot[..., None] * np.array((60, 120, 90))
            emis[y0:y1, 20:w - 20] += spot[..., None] * np.array((30, 80, 60))
    a[y0:y1, 20:w - 20] = glass
    return _img(a), _img(emis)


def textures():
    t = {'shaft_a': tex_shaft(81), 'shaft_b': tex_shaft(82, lights=True), 'shaft_c': tex_sign(), 'lintel': tex_lintel(), 'gate': tex_gate(),
         'lift_deck': tex_deck(), 'bridge': tex_bridge(), 'door': tex_door(), 'wall_window': tex_window(),
         'void': (Image.new('RGB', (16, 16), (0, 0, 0)), None), 'rail': (Image.new('RGB', (16, 16), (150, 118, 34)), None)}
    return t


# ------------------------------------------------------------- meshes
def _box(m, key, x0, y0, z0, x1, y1, z1, uvs=1.0):
    """An axis-aligned box without a bottom."""
    u = [(0, 0), (uvs, 0), (uvs, uvs), (0, uvs)]
    m.quad(key, (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1), u)          # top
    m.quad(key, (x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1), u)          # south
    m.quad(key, (x1, y1, z0), (x0, y1, z0), (x0, y1, z1), (x1, y1, z1), u)          # north
    m.quad(key, (x1, y0, z0), (x1, y1, z0), (x1, y1, z1), (x1, y0, z1), u)          # east
    m.quad(key, (x0, y1, z0), (x0, y0, z0), (x0, y0, z1), (x0, y1, z1), u)          # west


def _panel(name, tex, width, z0=-DROP, z1=-DROP + PANEL_H, v0=1.0, v1=0.0):
    """A face from x -w/2..w/2, normal -Y, z0..z1; texture v0 at the bottom, v1 at the top."""
    m = ShipModel(name, (0, 0, 0))
    hw = width / 2
    u1 = width / 4.0
    m.quad((tex, True, 0), (-hw, 0, z0), (hw, 0, z0), (hw, 0, z1), (-hw, 0, z1), [(0, v0), (u1, v0), (u1, v1), (0, v1)])
    return m


def meshes(lift, bridge_in, bridge_out, void, door):
    """{name: ShipModel}: shaft panels (4 and 2 wide, plain and lit), the door lintel, gate leaves,
    bridges, the platform with its rails, the void, and a security door leaf."""
    out = {}
    for width in (4, 2):
        out['EShaftA%d' % width] = _panel('EShaftA%d' % width, 'shaft_a', width)
        out['EShaftB%d' % width] = _panel('EShaftB%d' % width, 'shaft_b', width)
        out['EShaftC%d' % width] = _panel('EShaftC%d' % width, 'shaft_c', width)
    # Door piece: only the lintel above the opening.
    top = -DROP + GATE_H
    out['ELintel'] = _panel('ELintel', 'lintel', 4, top, -DROP + PANEL_H, 1 - GATE_H / PANEL_H, 0.0)
    # Gate leaf: 2 wide, the opening's height, a hand's width thick.
    m = out['EGate'] = ShipModel('EGate', (0, 0, 0))
    m.quad(('gate', True, 0), (-1, 0, -DROP), (1, 0, -DROP), (1, 0, top), (-1, 0, top), [(0, 1), (1, 1), (1, 0), (0, 0)])
    m.quad(('gate', True, 0), (-1, 0.12, -DROP), (1, 0.12, -DROP), (1, 0.12, top), (-1, 0.12, top), [(0, 1), (1, 1), (1, 0), (0, 0)])
    # Bridges: grating plates over the drop, centred on their unit, long along x (turned by the script).
    for name, (x0, y0, x1, y1) in (('EBridge', bridge_in),):
        m = out[name] = ShipModel(name, (0, 0, 0))
        hx, hy = (x1 - x0) / 2, (y1 - y0) / 2
        m.quad(('bridge', False, 0), (-hx, -hy, 0.03), (hx, -hy, 0.03), (hx, hy, 0.03), (-hx, hy, 0.03), [(0, 1), (1, 1), (1, 0), (0, 0)])
        _box(m, ('rail', False, 0), -hx, -hy, 0.0, hx, -hy + 0.12, 0.25)
        _box(m, ('rail', False, 0), -hx, hy - 0.12, 0.0, hx, hy, 0.25)
    # The platform: the deck plate, a kick rail and posted handrails, gaps where the bridges meet it.
    x0, y0, x1, y1 = lift
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    m = out['EPlatform'] = ShipModel('EPlatform', (cx, cy, 0))
    m.quad(('lift_deck', False, 0), (x0, y0, 0.03), (x1, y0, 0.03), (x1, y1, 0.03), (x0, y1, 0.03), [(0, 1), (1, 1), (1, 0), (0, 0)])
    gaps = [(bridge_in[1], bridge_in[3]), (bridge_out[1], bridge_out[3])]
    rail = ('rail', False, NO_SHADOW_CAST)
    for side in 'NSWE':
        if side in 'NS':
            yv = y1 - 0.08 if side == 'N' else y0 + 0.08
            segs = [(x0, x1)]
        else:
            yv = None
            segs = [(y0, gaps[0][0]), (gaps[0][1], y1)]
        for a0, a1 in segs:
            for t in np.arange(a0, a1 + 0.01, 2.0):
                if side in 'NS':
                    _box(m, rail, t - 0.06, yv - 0.06, 0, t + 0.06, yv + 0.06, 1.0)
                else:
                    xv = x0 + 0.08 if side == 'W' else x1 - 0.08
                    _box(m, rail, xv - 0.06, t - 0.06, 0, xv + 0.06, t + 0.06, 1.0)
            for z in (0.55, 1.0):
                if side in 'NS':
                    _box(m, rail, a0, yv - 0.05, z - 0.07, a1, yv + 0.05, z)
                else:
                    xv = x0 + 0.08 if side == 'W' else x1 - 0.08
                    _box(m, rail, xv - 0.05, a0, z - 0.07, xv + 0.05, a1, z)
    # The void: black over the drop, a ring round the platform (the bridges are drawn over it).
    vx0, vy0, vx1, vy1 = void
    m = out['EVoid'] = ShipModel('EVoid', (cx, cy, 0))
    for rx0, ry0, rx1, ry1 in [(vx0, vy0, vx1, y0), (vx0, y1, vx1, vy1), (vx0, y0, x0, y1), (x1, y0, vx1, y1)]:
        m.quad(('void', False, NO_SHADOW_CAST), (rx0, ry0, 0.02), (rx1, ry0, 0.02), (rx1, ry1, 0.02), (rx0, ry1, 0.02), [(0, 1), (1, 1), (1, 0), (0, 0)])
    # Security door leaf: 2 wide, wall height, 0.3 thick, origin at its middle on the floor.
    m = out['EDoor'] = ShipModel('EDoor', (0, 0, 0))
    key = ('door', False, 0)
    m.quad(key, (-1, -0.15, 0), (1, -0.15, 0), (1, -0.15, 2.5), (-1, -0.15, 2.5), [(0, 1), (1, 1), (1, 0), (0, 0)])
    m.quad(key, (1, 0.15, 0), (-1, 0.15, 0), (-1, 0.15, 2.5), (1, 0.15, 2.5), [(0, 1), (1, 1), (1, 0), (0, 0)])
    m.quad(key, (-1, -0.15, 2.5), (1, -0.15, 2.5), (1, 0.15, 2.5), (-1, 0.15, 2.5), [(0, 0), (1, 0), (1, 0.05), (0, 0.05)])
    m.quad(key, (1, -0.15, 0), (1, 0.15, 0), (1, 0.15, 2.5), (1, -0.15, 2.5), [(0, 1), (0.05, 1), (0.05, 0), (0, 0)])
    m.quad(key, (-1, 0.15, 0), (-1, -0.15, 0), (-1, -0.15, 2.5), (-1, 0.15, 2.5), [(0, 1), (0.05, 1), (0.05, 0), (0, 0)])
    return out
