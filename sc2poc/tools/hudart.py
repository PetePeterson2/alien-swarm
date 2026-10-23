"""HUD art drawn after Alien Swarm's own HUD (asw_hud_master and friends in the SDK, the shapes and colours of
its vgui/hud/sheet1 and sheet_stencil, scripts/HudLayout.res): nothing is copied, every texture is drawn here.

    the portrait: a black backplate (a circle squared off at the bottom right, where the ammo bar runs on),
        a 270-degree health ring from six o'clock clockwise round to three, 37 fill frames of it, a round
        helmet portrait per marine and the class medallions (officer, special weapons, medic, tech, dead,
        infested)
    the stencil icons: bullets, grenade, full and empty clips, the squad ammo tick
    line-art icons for the ten guns and the sentry, medkit and flare, glowing white (inactive ones are
        tinted light blue by the script, as in AS)
    the squad panel, its health bar, the objectives' black bar and tick boxes, the use panel and its key
        cap and progress bar, panels and buttons for the menus, blips and a minimap per level

`py tools/hudart.py` writes a contact sheet and a 1920x1200 mockup of the HUD over an in-game frame
(dist/hud-sheet.png, dist/hud-mockup.png). The mockup places everything with the numbers src/HUD.galaxy uses.
"""
import math
import pathlib
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from tools import shipkit  # noqa: E402

SS = 4                       # supersampling for every drawn shape
RING_N = 36                  # health ring frames: hp00 .. hp36, fill k/36 of the 270 degrees
RING_PX = 256
R_OUT, R_IN = 0.455, 0.338   # the ring's radii as a fraction of its box (sheet1's ring: 233 and 173 of 256)
WHITE = (255, 255, 255, 255)
BLUE_INACTIVE = (66, 142, 192)
CLASSES = ['officer', 'sw', 'medic', 'tech']   # marine slots 1..4 wear these (cosmetic, as AS's class icons)


# ---------------------------------------------------------------- helpers
def grid(n):
    """Pixel centres of an n*SS square in [-0.5, 0.5], y up."""
    m = n * SS
    v = (np.arange(m) + 0.5) / m - 0.5
    x, y = np.meshgrid(v, -v)
    return x, y


def shrink(a, n):
    """Box-filter an (n*SS, n*SS[, c]) array down to n."""
    if a.ndim == 2:
        return a.reshape(n, SS, n, SS).mean((1, 3))
    return a.reshape(n, SS, n, SS, a.shape[2]).mean((1, 3))


def rgba(color, alpha):
    """Straight-alpha RGBA image from a (h, w, 3) or rgb tuple colour and an (h, w) alpha in 0..1."""
    alpha = np.clip(alpha, 0, 1)
    if np.ndim(color) == 1 or isinstance(color, tuple):
        color = np.broadcast_to(np.array(color[:3], float), alpha.shape + (3,))
    out = np.dstack([np.clip(color, 0, 255), alpha * 255]).astype(np.uint8)
    return Image.fromarray(out, 'RGBA')


def draw_big(w, h):
    im = Image.new('RGBA', (w * SS, h * SS), (0, 0, 0, 0))
    return im, ImageDraw.Draw(im)


def finish(im, w, h):
    return im.resize((w, h), Image.Resampling.LANCZOS)


def S(points, sx=1.0, sy=1.0, ox=0.0, oy=0.0):
    return [((x + ox) * sx * SS, (y + oy) * sy * SS) for x, y in points]


def glow(im, radius, strength):
    """Soft halo under white line art (the equipment icons' glow)."""
    a = np.asarray(im)[:, :, 3].astype(float) / 255
    halo = np.asarray(Image.fromarray((a * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(radius))).astype(float) / 255
    alpha = np.clip(a + halo * strength, 0, 1)
    rgb = np.asarray(im)[:, :, :3].astype(float)
    tint = np.array([200, 225, 245], float)
    mix = np.where(a[..., None] > 0.02, rgb, tint)
    return rgba(mix, alpha)


# ---------------------------------------------------------------- portrait
def ring_frame(fill, bg=False):
    """The health ring, filled `fill` of its 270 degrees from six o'clock clockwise (AS draws progress 0..0.75
    from the bottom round through nine and twelve to three). Grey-scale, lighter to the top right: the script
    tints it blue (health), white (the health just lost) or green (infestation). `bg` is the dark track."""
    x, y = grid(RING_PX)
    r = np.hypot(x, y)
    th = np.degrees(np.arctan2(y, x)) % 360
    band = (r >= R_IN) & (r <= R_OUT)
    if bg:
        a = shrink(band & (th <= 270.0), RING_PX)
        a = np.asarray(Image.fromarray((a * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.2))).astype(float) / 255
        rr = shrink(r, RING_PX)
        edge = 1 - np.clip(np.abs(rr - (R_IN + R_OUT) / 2) / ((R_OUT - R_IN) / 2), 0, 1) ** 2
        lum = 38 + 26 * edge
        return rgba(np.dstack([lum, lum, lum]), a)
    lo = 270.0 - 270.0 * fill
    a = shrink(band & (th >= lo - 1e-6) & (th <= 270.0), RING_PX) if fill > 0 else np.zeros((RING_PX, RING_PX))
    xs, ys = shrink(x, RING_PX), shrink(y, RING_PX)
    t = np.clip((xs + ys) / 0.9 + 0.5, 0, 1)            # bottom left 0 .. top right 1
    rr = np.hypot(xs, ys)
    bevel = 1 - 0.18 * np.clip(np.abs(rr - (R_IN + R_OUT) / 2) / ((R_OUT - R_IN) / 2), 0, 1) ** 3
    lum = (150 + 105 * t) * bevel
    return rgba(np.dstack([lum, lum, lum]), a)


def backplate():
    """sheet1's portrait backdrop: a black circle with its bottom-right quarter squared off so it runs into
    the ammo bar; AS draws it at asw_hud_alpha 192."""
    x, y = grid(128)
    circle = np.hypot(x, y) <= 0.49
    corner = (x >= 0) & (y <= 0) & (x <= 0.5) & (y >= -0.5)
    a = shrink(circle | corner, 128) * (192 / 255)
    return rgba((0, 0, 0), a)


# Portraits are cosmetics: each marine wears a portrait key "<model>_<skin>", the default per slot or one
# their bank unlocks (src/Campaign.galaxy, section "cosmetic", key "portrait"). A model is a renderer below;
# a skin is its colours. Adding a skin is a line here; adding a model (a squad that is not marines) is a
# renderer plus its skins. build.py writes the keys into the script, which ignores a bank key it does not know.
PORTRAITS = {
    # The defaults, one per slot.
    'marine_steel': ('marine', dict(armour=(118, 128, 140), stripe=(70, 96, 70))),
    'marine_olive': ('marine', dict(armour=(112, 122, 92), stripe=(60, 80, 130))),
    'marine_rust': ('marine', dict(armour=(142, 98, 82), stripe=(130, 60, 52))),
    'marine_sand': ('marine', dict(armour=(128, 118, 96), stripe=(130, 120, 60))),
    # Veteran skins, for players to earn.
    'marine_veteran': ('marine', dict(armour=(196, 200, 206), stripe=(210, 170, 60), trim=(220, 180, 70),
                                      visor=((40, 90, 160), (150, 220, 255)))),
    'marine_shadow': ('marine', dict(armour=(44, 46, 52), stripe=(170, 30, 30), visor=((60, 4, 4), (255, 70, 50)))),
}
PORTRAIT_DEFAULTS = ['marine_steel', 'marine_olive', 'marine_rust', 'marine_sand']


def portrait(key):
    model, style = PORTRAITS[key]
    return PORTRAIT_MODELS[model](style)


def marine_portrait(style):
    """A round portrait of a helmeted marine, lit from the top left like AS's studio portraits. The style
    sets the armour, the helmet stripe, an optional trim round the visor, and the visor glass (dark, light)."""
    n = 128
    x, y = grid(n)
    u, v = x * 2, y * 2
    base = np.array(style['armour'], float)
    stripe = np.array(style['stripe'], float)
    L = np.array([-0.45, 0.55, 0.70]); L = L / np.linalg.norm(L)
    rad = np.hypot(u, v)
    img = np.dstack([62 - 30 * rad, 72 - 34 * rad, 84 - 38 * rad])                  # studio backdrop
    # Shoulders and collar.
    for sx in (-1, 1):
        cx, cy, rx, ry = 0.66 * sx, -1.0, 0.62, 0.42
        q = ((u - cx) / rx) ** 2 + ((v - cy) / ry) ** 2
        m = q <= 1
        nz = np.sqrt(np.clip(1 - q, 0, 1))
        nx, ny = (u - cx) / rx * 0.8, (v - cy) / ry * 0.8
        d = np.clip(nx * L[0] + ny * L[1] + nz * L[2], 0, 1)
        img = np.where(m[..., None], base * (0.22 + 0.7 * d)[..., None], img)
    collar = (np.abs(u) < 0.42 - (v + 0.55) * 0.25) & (v < -0.48) & (v > -1.1)
    img = np.where(collar[..., None], np.array([34, 36, 40.0]) * (1 + 0.3 * v[..., None] + 0.3), img)
    # The helmet: a lit ellipsoid.
    hx, hy, hrx, hry = 0.0, 0.14, 0.56, 0.64
    q = ((u - hx) / hrx) ** 2 + ((v - hy) / hry) ** 2
    helm = q <= 1
    nz = np.sqrt(np.clip(1 - q, 0, 1))
    nx, ny = (u - hx) / hrx, (v - hy) / hry
    d = np.clip(nx * L[0] + ny * L[1] + nz * L[2], 0, 1)
    spec = np.clip(nx * -0.35 + ny * 0.55 + nz * 0.76, 0, 1) ** 24
    shade = (0.18 + 0.8 * d)[..., None]
    hcol = base * shade + 255 * 0.45 * spec[..., None]
    ridge = helm & (np.abs(u) < 0.07) & (v > hy + 0.18)
    hcol = np.where(ridge[..., None], stripe * shade * 1.2, hcol)
    img = np.where(helm[..., None], hcol, img)
    # Ear pieces.
    for sx in (-1, 1):
        e = np.hypot((u - 0.5 * sx) / 0.13, (v - 0.02) / 0.2) <= 1
        img = np.where(e[..., None], np.array([46, 48, 54.0]) * (0.8 + 0.5 * d[..., None]), img)
    # The visor: an orange glass band, darker below, with a streak of reflection.
    top = hy + 0.06 - 0.22 * (u / 0.5) ** 2
    bot = hy - 0.30 + 0.10 * (u / 0.5) ** 2
    visor = helm & (v < top) & (v > bot) & (np.abs(u) < 0.5)
    t = np.clip((v - bot) / np.maximum(top - bot, 1e-3), 0, 1)
    lo, hi = [np.array(c, float) for c in style.get('visor', ((70, 26, 8), (255, 146, 48)))]
    glass = lo + (hi - lo) * np.dstack([t, t ** 1.4, t ** 2])
    streak = np.exp(-((u * 0.8 + v * 0.6 - 0.05) / 0.05) ** 2) * (u < 0.1)
    glass = glass + 140 * streak[..., None]
    img = np.where(visor[..., None], glass, img)
    rim = helm & ~visor & (np.abs(v - top) < 0.035) & (np.abs(u) < 0.5)
    img = np.where(rim[..., None], np.array(style.get('trim', (30, 30, 34)), float) * (0.6 + 0.5 * d[..., None]), img)
    # Chin guard and breathing grille.
    chin = helm & (v < bot) & (v > bot - 0.2) & (np.abs(u) < 0.32)
    img = np.where(chin[..., None], base * 0.45, img)
    grille = chin & (np.abs(((u + 1) * 14) % 1 - 0.5) < 0.18) & (np.abs(u) < 0.2)
    img = np.where(grille[..., None], np.array([20, 20, 22.0]), img)
    img = shrink(np.clip(img, 0, 255), n)
    a = shrink((np.hypot(x, y) <= 0.5).astype(float), n)
    return rgba(img, a)


PORTRAIT_MODELS = {'marine': marine_portrait}


CLASS_BG = {'officer': (59, 74, 58), 'sw': (45, 57, 92), 'medic': (84, 62, 60), 'tech': (96, 90, 56),
            'dead': (38, 38, 40), 'infested': (78, 108, 52)}


def medallion(kind):
    """sheet1's class icons: a coloured disc with a light rim and a white symbol."""
    n = 64
    im, d = draw_big(n, n)
    c = n * SS / 2
    R = n * SS * 0.47
    d.ellipse([c - R, c - R, c + R, c + R], fill=(200, 205, 210, 255))
    R2 = R * 0.9
    d.ellipse([c - R2, c - R2, c + R2, c + R2], fill=CLASS_BG[kind] + (255,))
    ink = (215, 218, 222, 255)
    k = n * SS / 64.0

    def P(pts):
        return [(c + px * k, c + py * k) for px, py in pts]
    if kind == 'officer':
        for oy in (-12, -3):
            d.polygon(P([(-16, oy + 5), (0, oy - 4), (16, oy + 5), (16, oy + 10), (0, oy + 1), (-16, oy + 10)]), fill=ink)
        pts = []
        for i in range(10):
            ang = math.radians(-90 + i * 36)
            rr = 8 if i % 2 == 0 else 3.4
            pts.append((math.cos(ang) * rr, 14 + math.sin(ang) * rr))
        d.polygon(P(pts), fill=ink)
    elif kind == 'sw':
        for oy in (-7, 0, 7):
            d.rectangle(P([(-18, oy - 2.2), (-9, oy + 2.2)]), fill=ink)
        d.rounded_rectangle(P([(-7, -11), (17, 11)]), radius=3 * k, fill=ink)
        d.rectangle(P([(-1, -6), (11, 6)]), fill=CLASS_BG[kind] + (255,))
    elif kind == 'medic':
        d.rectangle(P([(-5.5, -17), (5.5, 17)]), fill=ink)
        d.rectangle(P([(-17, -5.5), (17, 5.5)]), fill=ink)
    elif kind == 'tech':
        for i, ox in enumerate((-10, -2, 6)):
            top = -12 + i * 8
            d.line(P([(ox - 6, 20), (ox - 6, 4 + i * 2), (ox + 1, top + 4)]), fill=ink, width=int(2.6 * k))
            d.ellipse(P([(ox - 1, top - 4), (ox + 7, top + 4)]), fill=ink)
    elif kind == 'dead':
        d.ellipse(P([(-13, -17), (13, 7)]), fill=ink)
        d.rounded_rectangle(P([(-8, 2), (8, 14)]), radius=2 * k, fill=ink)
        for ex in (-6, 6):
            d.ellipse(P([(ex - 4.5, -8), (ex + 4.5, 0)]), fill=CLASS_BG[kind] + (255,))
        d.polygon(P([(0, 1), (-2, 5), (2, 5)]), fill=CLASS_BG[kind] + (255,))
        for tx in (-4, 0, 4):
            d.line(P([(tx, 8), (tx, 14)]), fill=CLASS_BG[kind] + (255,), width=int(1.4 * k))
    elif kind == 'infested':
        body = (232, 210, 60, 255)
        for i in range(4):
            for sx in (-1, 1):
                y0 = -8 + i * 6
                d.line(P([(0, y0), (sx * 12, y0 - 6 + i * 3), (sx * 17, y0 - 2 + i * 4)]), fill=body, width=int(2.4 * k))
        d.ellipse(P([(-5, -16), (5, 18)]), fill=body)
        d.line(P([(0, -16), (0, -22)]), fill=body, width=int(2 * k))
    return finish(im, n, n)


# ---------------------------------------------------------------- stencil icons
def icon_bullets():
    im, d = draw_big(32, 32)
    for i in range(3):
        x0 = 5 + i * 8
        d.polygon(S([(x0, 12), (x0 + 2.5, 5), (x0 + 5, 12), (x0 + 5, 28), (x0, 28)]), fill=WHITE)
        d.line(S([(x0, 14), (x0 + 5, 14)]), fill=(0, 0, 0, 0), width=SS)
    return finish(im, 32, 32)


def icon_grenade():
    im, d = draw_big(32, 32)
    d.rounded_rectangle(S([(10, 5), (22, 28)]), radius=6 * SS, fill=WHITE)
    d.line(S([(10, 13), (22, 13)]), fill=(0, 0, 0, 0), width=SS)
    return finish(im, 32, 32)


def icon_clip(full):
    """sheet_stencil's clip: a slanted magazine, filled when there is a clip to load, outlined when not."""
    im, d = draw_big(32, 32)
    outer = [(11, 30), (16, 3), (26, 3), (21, 30)]
    if full:
        d.polygon(S(outer), fill=WHITE)
    else:
        d.line(S(outer + outer[:1]), fill=WHITE, width=int(1.6 * SS))
    return finish(im, 32, 32)


def solid(w, h, color, alpha):
    return Image.new('RGBA', (w, h), tuple(color) + (int(alpha * 255),))


def rounded(w, h, radius, fill, border=None, bw=0, left_round_only=False):
    im, d = draw_big(w, h)
    box = [0, 0, w * SS - 1, h * SS - 1]
    if left_round_only:
        d.rounded_rectangle(box, radius=radius * SS, fill=fill)
        d.rectangle([w * SS // 2, 0, w * SS - 1, h * SS - 1], fill=fill)
    else:
        d.rounded_rectangle(box, radius=radius * SS, fill=fill, outline=border, width=bw * SS if border else 0)
    return finish(im, w, h)


def team_bar(fg):
    """The squad health bar (sheet1 team_health_bar): grey-scale left dark to right light for the script to
    tint, its left end cut concave where it tucks against the class medallion."""
    w, h = 128, 16
    yy, xx = np.mgrid[0:h * SS, 0:w * SS] / SS
    cut = (xx - (-h * 0.55)) ** 2 + (yy - h / 2) ** 2 > (h * 0.9) ** 2
    a = shrink_rect(cut.astype(float), w, h)
    if fg:
        t = np.linspace(0.62, 1.0, w)[None, :].repeat(h, 0)
        top = np.linspace(1.08, 0.86, h)[:, None]
        lum = np.clip(255 * t * top, 0, 255)
        return rgba(np.dstack([lum, lum, lum]), a)
    return rgba((46, 48, 52), a * 0.95)


def shrink_rect(a, w, h):
    return a.reshape(h, SS, w, SS).mean((1, 3))


def tick_box(done):
    """vgui/swarm/HUD/TickBoxEmpty and TickBoxTicked: a dark navy rounded square with a cyan rim, and the
    green tick."""
    n = 64
    im, d = draw_big(n, n)
    d.rounded_rectangle([6 * SS, 6 * SS, 58 * SS, 58 * SS], radius=9 * SS, fill=(22, 40, 54, 235), outline=(70, 170, 205, 255), width=3 * SS)
    if done:
        d.line(S([(16, 32), (28, 45), (54, 12)]), fill=(48, 220, 70, 255), width=8 * SS, joint='curve')
    return finish(im, n, n)


def black_bar():
    """vgui/swarm/HUD/ASWHUDBlackBar as the objectives draw it: black, its right end slanted."""
    w, h = 512, 64
    im, d = draw_big(w, h)
    d.polygon(S([(0, 0), (w, 0), (w - h, h), (0, h)]), fill=(0, 0, 0, 192))
    return finish(im, w, h)


def key_cap():
    n = 64
    im, d = draw_big(n, n)
    d.rounded_rectangle([5 * SS, 5 * SS, 59 * SS, 59 * SS], radius=8 * SS, fill=(235, 240, 245, 255))
    d.rounded_rectangle([10 * SS, 10 * SS, 54 * SS, 54 * SS], radius=5 * SS, fill=(20, 28, 36, 255))
    return finish(im, n, n)


def bar_fill(w=256, h=16):
    """Progress fill, grey-scale (the script tints it): light along the top like vgui/swarm/HUD/HorizProgressBar."""
    lum = np.linspace(255, 170, h)[:, None].repeat(w, 1)
    return rgba(np.dstack([lum, lum, lum]), np.ones((h, w)))


def panel(w, h, fill, border, bw=2, radius=6):
    return rounded(w, h, radius, fill, border, bw)


def button(fill, border):
    """A menu button's box (drawn as an image under the button control itself)."""
    return rounded(512, 64, 5, fill, border, 2)


def header(w, h):
    """The briefing and debrief frames' header strip: steel blue, lighter at the top edge."""
    y = np.linspace(0, 1, h)[:, None].repeat(w, 1)
    col = np.dstack([46 + 20 * (1 - y), 86 + 26 * (1 - y), 120 + 30 * (1 - y)])
    col[:2] = (120, 175, 215)
    return rgba(col, np.full((h, w), 0.95))


def blip(n=32, soft=True):
    x, y = grid(n)
    r = shrink(np.hypot(x, y), n)
    a = np.clip((0.5 - r) / 0.18, 0, 1) if soft else shrink((np.hypot(x, y) <= 0.45).astype(float), n)
    return rgba((255, 255, 255), a)


def blip_ring(n=32):
    x, y = grid(n)
    r = np.hypot(x, y)
    a = shrink(((r <= 0.48) & (r >= 0.36)).astype(float), n)
    return rgba((255, 255, 255), a)


def blip_diamond(n=32):
    x, y = grid(n)
    q = np.abs(x) + np.abs(y)
    a = shrink(((q <= 0.46) & (q >= 0.3)).astype(float), n)
    return rgba((255, 255, 255), a)


def crosshair(n=64):
    """vgui/swarm/HUD/ASWCrosshair: a broken white cross round an open centre."""
    im, d = draw_big(n, n)
    c = n / 2
    for a0, a1 in ((4, 11), (14, 22)):
        for sx, sy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            d.line(S([(c + sx * a0, c + sy * a0), (c + sx * a1, c + sy * a1)]), fill=WHITE, width=int(2.2 * SS))
    d.ellipse(S([(c - 1.6, c - 1.6), (c + 1.6, c + 1.6)]), fill=WHITE)
    return finish(im, n, n)


# ---------------------------------------------------------------- equipment line art
# Each icon is a list of closed outlines (and open strokes) on a 128 x 64 grid (items on 64 x 64), drawn as
# white lines with a faint fill and a blue-white glow, after the look of vgui/swarm/EquipIcons.
def _rect(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def _circle(cx, cy, r, n=28):
    return [(cx + r * math.cos(2 * math.pi * i / n), cy + r * math.sin(2 * math.pi * i / n)) for i in range(n)]


def _stock(x=8):
    return [(x, 33), (x + 4, 25), (x + 22, 25), (x + 22, 34), (x + 12, 36), (x + 6, 44), (x, 44)]


def _grip(x, y=36):
    return [(x, y), (x + 8, y), (x + 5, y + 14), (x - 3, y + 14)]


GUNS = {
    1: ([_stock(), _rect(30, 24, 80, 35), [(40, 24), (44, 18), (70, 18), (73, 24)], _grip(46), [(60, 35), (68, 35), (71, 50), (63, 51)],
         _rect(80, 26, 104, 33), _rect(104, 28, 121, 31), _rect(80, 33, 100, 39)],
        [[(84, 29), (100, 29)], [(34, 28), (54, 28)]]),
    2: ([[(6, 40), (10, 22), (18, 22), (22, 18), (34, 18), (34, 24), (20, 28), (16, 40)], _rect(34, 20, 74, 38), _grip(40, 38),
         [(56, 38), (66, 38), (64, 48), (54, 48)], _rect(74, 22, 104, 36), _rect(104, 25, 122, 29), _rect(104, 30, 122, 34),
         [(46, 20), (50, 10), (60, 10), (62, 20)]],
        [[(78, 26), (100, 26)], [(78, 32), (100, 32)], [(38, 25), (70, 25)]]),
    3: ([[(6, 36), (14, 26), (40, 24), (40, 34), (24, 36), (14, 44), (8, 44)], _rect(40, 23, 62, 34), _grip(44, 34),
         _rect(62, 24, 122, 28), _rect(62, 29, 118, 33), _rect(70, 33, 94, 38)],
        [[(74, 35), (90, 35)]]),
    4: ([_stock(6), _rect(28, 28, 82, 38), _grip(40, 38), _rect(36, 8, 46, 28), _rect(48, 8, 58, 28), [(82, 30), (110, 30), (114, 26), (122, 24), (122, 30), (114, 36), (82, 36)],
         _rect(60, 38, 76, 46)],
        [[(36, 13), (46, 13)], [(48, 13), (58, 13)], [(36, 23), (58, 23)], [(114, 33), (124, 38)]]),
    5: ([[(14, 20), (54, 20), (54, 27), (30, 27), (26, 42), (16, 42), (20, 27), (14, 27)], [(62, 30), (102, 30), (102, 37), (78, 37), (74, 52), (64, 52), (68, 37), (62, 37)]],
        [[(18, 23), (50, 23)], [(66, 33), (98, 33)]]),
    6: ([_stock(), _rect(30, 26, 60, 38), _grip(40, 38), [(60, 24), (122, 24), (122, 28), (60, 28)], [(60, 34), (118, 34), (118, 38), (60, 38)],
         _rect(36, 15, 62, 21), [(64, 28), (110, 28), (110, 34), (64, 34)]],
        [[(40, 21), (40, 26)], [(56, 21), (56, 26)], [(70, 31), (106, 31)]]),
    7: ([[(6, 40), (12, 24), (24, 24), (24, 30), (16, 32), (12, 40)], _rect(24, 22, 66, 40), _grip(30, 40), _circle(45, 46, 7),
         _rect(66, 24, 120, 28), _rect(66, 29, 120, 33), _rect(66, 34, 120, 38), _rect(80, 21, 90, 41), [(36, 22), (42, 10), (52, 10), (54, 22)]],
        [[(28, 27), (62, 27)], [(28, 35), (62, 35)]]),
    8: ([_stock(), _rect(30, 25, 50, 37), _grip(36, 37), _rect(50, 18, 76, 42), _rect(76, 24, 108, 34), _rect(108, 26, 116, 32), _rect(84, 34, 92, 46)],
        [[(50, 24), (76, 24)], [(50, 30), (76, 30)], [(50, 36), (76, 36)], [(56, 18), (56, 42)], [(70, 18), (70, 42)]]),
    9: ([_stock(), [(30, 24), (78, 16), (120, 28), (120, 34), (78, 40), (30, 38)], _grip(40, 38), _rect(54, 20, 72, 36), [(63, 22), (70, 34), (56, 34)]],
        [[(78, 22), (114, 30)], [(78, 34), (114, 32)], [(63, 26), (63, 30)]]),
    10: ([[(4, 38), (12, 26), (36, 26), (36, 34), (22, 34), (12, 44), (6, 44)], _rect(36, 25, 70, 34), _grip(44, 34), _rect(70, 27, 124, 30),
          _rect(38, 15, 70, 21), _circle(38, 18, 4.5), _circle(70, 18, 4.5), [(58, 34), (66, 34), (67, 44), (59, 44)]],
         [[(46, 21), (46, 25)], [(62, 21), (62, 25)], [(110, 25), (110, 32)]]),
}
ITEMS = {
    'sentry': ([_rect(22, 6, 46, 16), _rect(46, 9, 60, 13), _circle(32, 30, 9), [(32, 38), (14, 58), (20, 58), (32, 44), (44, 58), (50, 58), (32, 38)],
                _rect(28, 16, 36, 22)],
               [[(26, 27), (38, 27)], [(26, 30), (38, 30)], [(26, 33), (38, 33)]]),
    'medkit': ([[(12, 18), (52, 18), (54, 22), (54, 56), (10, 56), (10, 22)], [(24, 18), (24, 10), (40, 10), (40, 18)], _circle(32, 37, 11)],
               [[(32, 30), (32, 44)], [(25, 37), (39, 37)], [(10, 48), (54, 48)]]),
    'flare': ([_circle(32, 30, 8)],
              [[(32, 6), (32, 18)], [(32, 42), (32, 54)], [(8, 30), (20, 30)], [(44, 30), (56, 30)], [(26, 36), (12, 52)], [(15, 54), (10, 49)]]),
    'grenade': ([_circle(30, 36, 16), _rect(26, 14, 38, 21)], [[(38, 16), (48, 10), (50, 16)]]),
}


def line_icon(spec, w, h, gw, gh, pad=0.1):
    """The outlines scaled into the icon with `pad` of it left round the edge, as AS's icons sit in theirs."""
    shapes, strokes = spec
    im, d = draw_big(w, h)
    k = 1 - 2 * pad
    shapes = [[(gw * pad + x * k, gh * pad + y * k) for x, y in poly] for poly in shapes]
    strokes = [[(gw * pad + x * k, gh * pad + y * k) for x, y in line] for line in strokes]
    sx, sy = w / gw, h / gh
    lw = max(2, int(1.25 * sx * SS))
    for poly in shapes:
        d.polygon(S(poly, sx, sy), fill=(150, 190, 220, 40))
    for poly in shapes:
        pts = S(poly, sx, sy)
        d.line(pts + pts[:1], fill=WHITE, width=lw, joint='curve')
    for line in strokes:
        d.line(S(line, sx, sy), fill=WHITE, width=lw, joint='curve')
    return glow(finish(im, w, h), 3.0 * sx, 0.55)


# ---------------------------------------------------------------- minimap
MM_PX = 256


def minimap(floor, void_cells, margin=3):
    """A level from above in the minimap's colours: deck a dark steel blue with a faint grid, the walls round
    it a bright cyan edge, the lift's drop black. Returns (image, x0, y0, size): the square of the world it
    shows, y up."""
    H, W = floor.shape
    ys, xs = np.nonzero(floor)
    x0, x1, y0, y1 = xs.min() - margin, xs.max() + 1 + margin, ys.min() - margin, ys.max() + 1 + margin
    size = max(x1 - x0, y1 - y0)
    x0 -= (size - (x1 - x0)) // 2
    y0 -= (size - (y1 - y0)) // 2
    k = MM_PX / size
    n = MM_PX * SS
    v = (np.arange(n) + 0.5) / n * size
    gx = np.floor(x0 + v).astype(int)
    gy = np.floor(y0 + size - v).astype(int)                        # image rows top down = world y descending
    GX, GY = np.meshgrid(gx, gy)
    inside = (GX >= 0) & (GX < W) & (GY >= 0) & (GY < H)
    f = np.zeros_like(GX, bool)
    f[inside] = floor[GY[inside], GX[inside]]
    vd = np.zeros_like(GX, bool)
    vd[inside] = void_cells[GY[inside], GX[inside]]
    fi = Image.fromarray((f * 255).astype(np.uint8))
    edge = np.asarray(fi.filter(ImageFilter.MaxFilter(int(SS * k * 0.5) | 1))).astype(bool) & ~f
    fx = (np.arange(n) + 0.5) / n * size
    gridline = (np.abs(((x0 + fx) % 4) - 2) > 1.9)[None, :] | (np.abs(((y0 + size - fx) % 4) - 2) > 1.9)[:, None]
    col = np.zeros((n, n, 3))
    col[f] = (34, 66, 88)
    col[f & gridline] = (44, 82, 106)
    col[edge] = (150, 218, 240)
    alpha = np.where(f, 0.9, 0.0) + np.where(edge, 1.0, 0.0) + np.where(vd & ~f, 0.95, 0.0)
    col[vd & ~f] = (2, 4, 6)
    img = shrink(col, MM_PX)
    a = shrink(np.clip(alpha, 0, 1), MM_PX)
    scan = (np.arange(MM_PX) % 2 == 0)[:, None]                     # the scanner's scanlines
    img = img * np.where(scan, 1.0, 0.86)[..., None]
    return rgba(img, a), int(x0), int(y0), int(size)


# ---------------------------------------------------------------- the set
def textures(levels=()):
    """{name: PIL image} for Base.SC2Assets/Derelict/UI/<name>.dds, plus the minimap frames per level."""
    t = {}
    t['ringbg'] = ring_frame(0, bg=True)
    for k in range(RING_N + 1):
        t['hp%02d' % k] = ring_frame(k / RING_N)
    t['plate'] = backplate()
    for key in PORTRAITS:
        t['face_' + key] = portrait(key)
    for kind in CLASS_BG:
        t['cls_' + kind] = medallion(kind)
    t['bullets'] = icon_bullets()
    t['grenade'] = icon_grenade()
    t['clip1'] = icon_clip(True)
    t['clip0'] = icon_clip(False)
    t['black75'] = solid(8, 8, (0, 0, 0), 0.75)
    t['shade50'] = solid(8, 8, (255, 255, 255), 0.5)
    t['shade75'] = solid(8, 8, (255, 255, 255), 0.75)
    t['teambg'] = rounded(256, 64, 32, (0, 0, 0, 192), left_round_only=True)
    t['tbar0'] = team_bar(False)
    t['tbar1'] = team_bar(True)
    t['tick'] = solid(4, 16, (255, 255, 255), 1.0)
    t['objbar'] = black_bar()
    t['obj0'] = tick_box(False)
    t['obj1'] = tick_box(True)
    t['usebox'] = rounded(512, 128, 14, (32, 57, 82, 200))
    t['msgbox'] = rounded(512, 64, 12, (0, 0, 0, 192))
    t['keycap'] = key_cap()
    t['barbg'] = rounded(256, 16, 3, (12, 16, 20, 230), (90, 120, 140, 255), 1)
    t['barfg'] = bar_fill()
    t['frame'] = panel(512, 512, (14, 24, 34, 236), (64, 112, 150, 255), 2, 6)
    t['header'] = header(512, 64)
    t['button'] = button((20, 40, 60, 245), (72, 122, 160, 255))
    t['buttonhi'] = button((36, 70, 100, 250), (130, 196, 235, 255))
    t['buttonoff'] = button((16, 22, 28, 220), (44, 56, 66, 255))
    t['clear'] = solid(8, 8, (0, 0, 0), 0.0)
    t['hover'] = solid(8, 8, (160, 215, 245), 0.16)
    t['blip'] = blip()
    t['blipring'] = blip_ring()
    t['blipobj'] = blip_diamond()
    t['cross'] = crosshair()
    for w, spec in GUNS.items():
        t['gun%d' % w] = line_icon(spec, 256, 128, 128, 64)
    for name, spec in ITEMS.items():
        t['item_' + name] = line_icon(spec, 128, 128, 64, 64)
    frames = []
    for n, (floor, void_cells) in enumerate(levels):
        img, x0, y0, size = minimap(floor, void_cells)
        t['map%d' % n] = img
        frames.append((x0, y0, size))
    return t, frames


def files(levels):
    t, frames = textures(levels)
    return {'Base.SC2Assets/Derelict/UI/%s.dds' % k: shipkit.dds_rgba(v) for k, v in t.items()}, frames


# ---------------------------------------------------------------- preview
def font(size, bold=False):
    for name in (['eurostileb.ttf', 'arialbd.ttf'] if bold else ['eurostile.ttf', 'arial.ttf']):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def sheet(t, path):
    keys = [k for k in t if not k.startswith('hp') or k in ('hp00', 'hp18', 'hp36')]
    cell = 140
    cols = 10
    rows = (len(keys) + cols - 1) // cols
    out = Image.new('RGBA', (cols * cell, rows * (cell + 16)), (70, 76, 88, 255))
    d = ImageDraw.Draw(out)
    for i, k in enumerate(keys):
        im = t[k].copy()
        im.thumbnail((cell - 8, cell - 8))
        x, y = (i % cols) * cell, (i // cols) * (cell + 16)
        out.alpha_composite(im, (x + 4, y + 4))
        d.text((x + 4, y + cell), k, fill=(255, 255, 0, 255))
    out.save(path)


def mockup(t, frames, path, backdrop=None):
    """The HUD of src/HUD.galaxy at 1920x1200 (SC2's 1200-high UI units 1:1): marine 1 with the rifle, three
    squadmates, the objectives, the use panel and the minimap."""
    from tools import hudlayout as Y
    Wd, Hd = 1920, 1200
    if backdrop and pathlib.Path(backdrop).exists():
        bg = Image.open(backdrop).convert('RGBA').resize((Wd, Hd))
    else:
        bg = Image.new('RGBA', (Wd, Hd), (24, 26, 30, 255))
    out = bg.copy()
    d = ImageDraw.Draw(out)

    def put(name, x, y, w, h, tint=None):
        im = t[name].resize((max(1, int(w)), max(1, int(h))), Image.Resampling.LANCZOS)
        if tint is not None:
            a = np.asarray(im).astype(float)
            a[:, :, :3] *= np.array(tint[:3], float) / 255
            im = Image.fromarray(a.astype(np.uint8), 'RGBA')
        out.alpha_composite(im, (int(x), int(y)))

    def text(s, x, y, size, color=(255, 255, 255), anchor='la', bold=False):
        d.text((x + 1, y + 1), s, font=font(size, bold), fill=(0, 0, 0, 200), anchor=anchor)
        d.text((x, y), s, font=font(size, bold), fill=color + (255,), anchor=anchor)

    # The bottom strip's dialog: bottom left, Y.STRIP_H tall.
    oy = Hd - Y.STRIP_H
    P = (Y.PX, oy + Y.PY)
    put('gun1', Y.PX, oy + Y.GUN1_Y, Y.GUN_W, Y.GUN_H)
    put('gun3', Y.PX, oy + Y.GUN2_Y, Y.GUN_W, Y.GUN_H, BLUE_INACTIVE)
    put('plate', *P, Y.RING, Y.RING)
    put('black75', P[0] + Y.RING, P[1] + Y.RING / 2, Y.BAR_W, Y.RING / 2)
    fx, fy = P[0] + Y.FACE_X - Y.FACE_R, P[1] + Y.FACE_Y - Y.FACE_R
    put('face_marine_steel', fx, fy, 2 * Y.FACE_R, 2 * Y.FACE_R)
    put('ringbg', *P, Y.RING, Y.RING)
    put('hp30', *P, Y.RING, Y.RING, (255, 255, 255))
    put('hp27', *P, Y.RING, Y.RING, Y.HP_TINT)
    put('cls_officer', P[0] + Y.CLS_X, P[1] + Y.CLS_Y, Y.CLS, Y.CLS)
    text('Assault Rifle', P[0] + Y.NAME_X, P[1] + Y.NAME_Y, Y.F_SMALL)
    put('bullets', P[0] + Y.BUL_X, P[1] + Y.BUL_Y, Y.ICON, Y.ICON)
    text('073', P[0] + Y.AMMO_X, P[1] + Y.AMMO_Y - 6, Y.F_LARGE)
    put('grenade', P[0] + Y.GREN_X, P[1] + Y.BUL_Y, Y.ICON, Y.ICON)
    text('5', P[0] + Y.GREN_TX, P[1] + Y.AMMO_Y - 6, Y.F_LARGE)
    for i in range(5):
        put('clip1' if i < 3 else 'clip0', P[0] + Y.CLIP_X + Y.CLIP_GAP * i, P[1] + Y.CLIP_Y, Y.CLIP, Y.CLIP, None if i < 3 else (128, 128, 128))
    for i, (item, key, n) in enumerate([('item_sentry', 'Q', 1), ('item_medkit', 'E', 2), ('item_flare', 'X', 4)]):
        x = P[0] + Y.ITEM_X + Y.ITEM_GAP * i
        put(item, x, P[1] + Y.ITEM_Y, Y.ITEM, Y.ITEM, BLUE_INACTIVE)
        text(key, x + Y.ITEM - 2, P[1] + Y.ITEM_Y + 2, Y.F_DEFAULT, anchor='ra')
        text('x%d' % n, x + Y.ITEM - 2, P[1] + Y.ITEM_Y + Y.ITEM - 2, Y.F_SMALL, BLUE_INACTIVE, anchor='rd')
    text('- LOW AMMO -', P[0] + Y.LOW_X, P[1] + Y.LOW_Y, Y.F_DEFAULT, (200, 25, 25))
    # Squadmates.
    for i, (name, cls, hp, ammo, clips) in enumerate([('drink', 'sw', 0.8, 0.6, 4), ('Marine 3', 'medic', 0.35, 0.9, 2), ('Marine 4', 'tech', 0.0, 0, 0)]):
        x, y = Y.SQ_X + Y.SQ_GAP * i, oy + Y.SQ_Y
        text(name, x + Y.SQ_NAME_X, y + Y.SQ_NAME_Y, Y.F_SMALL, (255, 255, 255) if hp > 0 else (128, 128, 128))
        put('teambg', x + Y.SQ_BG_X, y + Y.SQ_BG_Y, Y.SQ_BG_W, Y.SQ_BG_H)
        put('tbar0', x + Y.SQ_HP_X, y + Y.SQ_HP_Y, Y.SQ_HP_W, Y.SQ_HP_H)
        if hp > 0:
            put('tbar1', x + Y.SQ_HP_X, y + Y.SQ_HP_Y, Y.SQ_HP_W * hp, Y.SQ_HP_H, Y.HP_TINT if hp > 0.3 else Y.HP_LOW)
            for k in range(Y.SQ_TICKS):
                on = k < round(ammo * Y.SQ_TICKS)
                put('tick', x + Y.SQ_AM_X + k * Y.SQ_TICK_GAP, y + Y.SQ_AM_Y, Y.SQ_TICK_W, Y.SQ_AM_H, (200, 200, 200) if on else (96, 96, 96))
            for k in range(5):
                put('clip1' if k < clips else 'clip0', x + Y.SQ_CLIP_X + Y.SQ_CLIP_GAP * k, y + Y.SQ_CLIP_Y, Y.SQ_CLIP, Y.SQ_CLIP, (200, 200, 200) if k < clips else (96, 96, 96))
            put('item_medkit', x + Y.SQ_ITEM_X, y + Y.SQ_ITEM_Y, Y.SQ_ITEM, Y.SQ_ITEM, BLUE_INACTIVE)
            text(str(i + 2), x + Y.SQ_ITEM_X + Y.SQ_ITEM, y + Y.SQ_ITEM_Y, Y.F_SMALL, anchor='ra')
            text('x2', x + Y.SQ_ITEM_X + Y.SQ_ITEM, y + Y.SQ_ITEM_Y + Y.SQ_ITEM + 4, Y.F_SMALL, BLUE_INACTIVE, anchor='rd')
        put('cls_' + (cls if hp > 0 else 'dead'), x + Y.SQ_CLS_X, y + Y.SQ_CLS_Y, Y.SQ_CLS, Y.SQ_CLS)
    # Objectives, top left.
    put('objbar', Y.OBJ_X - 6, Y.OBJ_Y - 6, Y.OBJ_BAR_W, Y.OBJ_HEAD + 12)
    text(' Objectives', Y.OBJ_X, Y.OBJ_Y, Y.F_DEFAULT, (255, 255, 255))
    for i, (s, done) in enumerate([('Restore power at the reactor console', True), ('Return to the dropship', False)]):
        yy = Y.OBJ_Y + Y.OBJ_HEAD + 6 + i * Y.OBJ_ROW
        put('obj1' if done else 'obj0', Y.OBJ_X, yy, Y.OBJ_TICK, Y.OBJ_TICK)
        text(s, Y.OBJ_X + Y.OBJ_TICK + 8, yy, Y.F_DEFAULT, (255, 255, 255))
    text('Objective complete!', Y.OBJ_X + Y.OBJ_TICK + 8, Y.OBJ_Y + Y.OBJ_HEAD + 6 + 2 * Y.OBJ_ROW + 8, Y.F_DEFAULT, (35, 214, 250))
    # Use panel, bottom centre.
    ux, uy = Wd / 2 - Y.USE_W / 2, Hd - Y.USE_B - Y.USE_H
    put('usebox', ux, uy, Y.USE_W, Y.USE_H)
    put('keycap', ux + 12, uy + 12, Y.KEY, Y.KEY)
    text('E', ux + 12 + Y.KEY / 2, uy + 12 + Y.KEY / 2, Y.F_DEFAULT, anchor='mm')
    text('Overriding door lock', ux + 24 + Y.KEY, uy + 16, Y.F_DEFAULT, (255, 255, 255))
    put('barbg', ux + 24 + Y.KEY, uy + Y.USE_H - 30, Y.USE_W - 40 - Y.KEY, 14)
    put('barfg', ux + 26 + Y.KEY, uy + Y.USE_H - 28, (Y.USE_W - 44 - Y.KEY) * 0.63, 10, Y.BAR_TINT)
    # Minimap, bottom right.
    mx, my = Wd - Y.MM_R - Y.MM, Hd - Y.MM_B - Y.MM
    put('black75', mx - Y.MM_BORDER, my - Y.MM_BORDER, Y.MM + 2 * Y.MM_BORDER, Y.MM + 2 * Y.MM_BORDER)
    if 'map1' in t:
        put('map1', mx, my, Y.MM, Y.MM)
        x0, y0, size = frames[1]
        for wx, wy, c, nb in [(60, 70, (0, 192, 0), 'blip'), (63, 66, (0, 192, 0), 'blip'), (75, 72, (255, 30, 20), 'blip'), (80, 64, (255, 30, 20), 'blip'), (40, 40, (230, 192, 0), 'blipobj')]:
            bx = mx + (wx - x0) / size * Y.MM
            by = my + (1 - (wy - y0) / size) * Y.MM
            s = Y.BLIP if nb == 'blip' else Y.BLIP_OBJ
            put(nb, bx - s / 2, by - s / 2, s, s, c)
        put('blipring', mx + (60 - x0) / size * Y.MM - Y.BLIP, my + (1 - (70 - y0) / size) * Y.MM - Y.BLIP, 2 * Y.BLIP, 2 * Y.BLIP, (0, 255, 0))
    out.convert('RGB').save(path)


if __name__ == '__main__':
    sys.path.insert(0, str(ROOT))
    from tools import level as L
    levels = []
    for name in ('deck', 'cargo'):
        L.use(name)
        floor, room = L.carve()
        void = np.zeros_like(floor)
        for y in range(L.H):
            for x in range(L.W):
                void[y, x] = L.in_void(x, y)
        levels.append((floor, void))
    t, frames = textures(levels)
    print('frames', frames, 'textures', len(t), 'bytes', sum(len(shipkit.dds_rgba(v)) for v in t.values()))
    (ROOT / 'dist').mkdir(exist_ok=True)
    sheet(t, ROOT / 'dist' / 'hud-sheet.png')
    mockup(t, frames, ROOT / 'dist' / 'hud-mockup.png', ROOT / 'dist' / 'screens' / 'kit-compare-kit.jpg')
