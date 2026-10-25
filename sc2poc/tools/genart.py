"""Art painted outside the build (Nano Banana; the prompts and file names are in ART-PROMPTS.md), keyed and
fitted for the map's UI.

Each image in assets/ui-gen/ is cut out of its flat background, cropped to what is left and fitted:

    magenta key   the subject on pure #FF00FF: alpha from how magenta each pixel is, measured against the
                  background's own colour (read off the image's border), and the fringe un-mixed from it
    black key     glow on pure black: alpha from brightness, colour divided back out (reads as additive)

A missing image leaves the drawn art as it is. Some images replace a drawn texture of the same name
(portraits face_m_*, class medallions cls_*, the squad card teambg, the ticked box obj1, the objective blip
blipobj); the rest are new names the map script uses only when they exist (AS_Painted, written by build.py):
gi<item> (the briefing's loadout art), mis_<level> (the briefing's picture), starchart (behind the briefing),
k_<kit>_<bucket> (panels and buttons, pre-sliced per aspect ratio), hudbezel, hudplate and ico_<name>.

`py tools/genart.py [dir]` writes dist/genart-sheet.png (every texture made, over the briefing navy and over
a checker, with warnings) and dist/genart-hud.png (the HUD's portrait corner with the bezel and plate on).
"""
import math
import os
import pathlib
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from tools import hudart, hudlayout as Y  # noqa: E402
from tools.uiart import MARINE_LOOKS  # noqa: E402

GEN_DIR = pathlib.Path(os.environ.get('AS_GENART_DIR') or ROOT / 'assets' / 'ui-gen')   # AS_GENART_DIR: another folder, for tests
NAVY = (12, 20, 30)

# Loadout art by file stem (gun_<stem>.png or item_<stem>.png) -> item id (src/State.galaxy AS_IT_*).
# Ids up to 21 sit in a weapon slot (2:1 art); 22 on are offhand items (square), as the drawn icons.
ITEMS = {'rifle': 1, 'prifle': 2, 'autogun': 3, 'vindicator': 4, 'pistols': 5, 'sentry': 6, 'healbeacon': 7,
         'ammosatchel': 8, 'shotgun': 9, 'tesla': 10, 'railrifle': 11, 'medgun': 12, 'pdw': 13, 'flamer': 14,
         'sentryfreeze': 15, 'minigun': 16, 'marksman': 17, 'sentryfire': 18, 'chainsaw': 19, 'sentrycannon': 20,
         'grenadelauncher': 21, 'medkit': 22, 'welder': 23, 'flares': 24, 'lasermines': 25, 'heavyarmor': 26,
         'damageamp': 27, 'hornet': 28, 'freezegrenades': 29, 'adrenaline': 30, 'teslacoil': 31,
         'electricarmor': 32, 'incmines': 33, 'flashlight': 34, 'powerfist': 35, 'grenades': 36,
         'nightvision': 37, 'smartbomb': 38}
CLASSES = ['officer', 'sw', 'medic', 'tech']
EXTS = ['.png', '.jpg', '.jpeg', '.webp']      # what Gemini saves; PNG wins when there are two
# The objective sheet's cells, left to right, top to bottom (ART-PROMPTS.md section 10).
ICONS = ['done', 'target', 'door', 'weld', 'hack', 'power', 'eggs', 'biomass', 'extract', 'warning', 'lowammo', 'infested']
# Panel and button art is pre-sliced (nine-slice) at these width:height ratios; the script picks the nearest.
RATIOS = [0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 3.0, 4.0, 5.0, 6.0, 8.0, 12.0]
KITS = {'frame': ('frame_panel', 256, 0.12), 'button': ('frame_button', 64, 0.3),
        'buttonhi': ('frame_button_hover', 64, 0.3), 'buttonoff': ('frame_button', 64, 0.3)}


# ---------------------------------------------------------------- keying
def _f(im):
    return np.asarray(im.convert('RGB')).astype(float)


def _border(a, k=6):
    return np.concatenate([a[:k].reshape(-1, 3), a[-k:].reshape(-1, 3), a[:, :k].reshape(-1, 3), a[:, -k:].reshape(-1, 3)])


def key_magenta(im, warn):
    """RGBA from an image on flat magenta. A pixel's magenta excess e = min(R, B) - G is ~255 on the key and
    near 0 on the subject; an edge pixel mixing the two has alpha (eK - e) / (eK - e0), and its colour is the
    mix with the key taken back out."""
    a = _f(im)
    edge = _border(a)
    K = np.median(edge, axis=0)
    off = np.abs(edge - K).max(axis=1) > 40
    top = a[:6].reshape(-1, 3)                          # subjects reach the bottom and sides, not the top
    grey = (np.ptp(top, axis=1) < 24) & (top.min(axis=1) > 120)
    if np.mean(grey) > 0.2:
        warn('a grey checkerboard round the edge (Nano Banana painted "transparency"): ask for flat magenta')
    elif np.mean(off) > 0.5:
        warn('most of the border is not the background colour: keying may leave patches')
    eK = min(K[0], K[2]) - K[1]
    if eK < 120:
        warn('background is not magenta (%d,%d,%d)' % tuple(K))
    e = np.minimum(a[..., 0], a[..., 2]) - a[..., 1]
    e0 = 40.0
    # The background's own grain (compression, painted noise) stays fully clear.
    eb = np.minimum(edge[:, 0], edge[:, 2]) - edge[:, 1]
    eK -= 3 * np.std(eb[~off]) + 6 if (~off).any() else 6
    alpha = np.clip((eK - e) / max(eK - e0, 1), 0, 1)
    alpha[alpha < 0.04] = 0
    safe = np.maximum(alpha, 0.05)[..., None]
    rgb = (a - (1 - alpha[..., None]) * K) / safe
    # Despill what magenta is left on the subject's edge.
    m = np.minimum(rgb[..., 0], rgb[..., 2])
    spill = np.clip(m - rgb[..., 1], 0, None) * np.clip((e - 10) / 60, 0, 1)
    rgb[..., 0] -= spill
    rgb[..., 2] -= spill
    return _rgba(rgb, alpha)


def key_black(im, warn, floor=10):
    """RGBA from glow on black: alpha is the brightest channel (less a noise floor), colour un-premultiplied."""
    a = _f(im)
    K = np.median(_border(a), axis=0)
    if K.max() > 40:
        warn('background is not black (%d,%d,%d)' % tuple(K))
    alpha = np.clip((a.max(axis=2) - floor) / (255 - floor), 0, 1)
    rgb = a / np.maximum(alpha, 1 / 255)[..., None]
    return _rgba(rgb, alpha)


def _rgba(rgb, alpha):
    out = np.dstack([np.clip(rgb, 0, 255), alpha * 255]).astype(np.uint8)
    return Image.fromarray(out, 'RGBA')


def crop(im, thresh=8):
    box = im.getchannel('A').point(lambda v: 255 if v > thresh else 0).getbbox()
    return im.crop(box) if box else im


# ---------------------------------------------------------------- fitting
def fit(im, w, h, pad=0.05):
    """Contain: scaled to fit inside w x h less a margin, centred."""
    im = crop(im)
    s = min(w * (1 - 2 * pad) / im.width, h * (1 - 2 * pad) / im.height)
    sm = im.resize((max(1, round(im.width * s)), max(1, round(im.height * s))), Image.Resampling.LANCZOS)
    out = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    out.alpha_composite(sm, ((w - sm.width) // 2, (h - sm.height) // 2))
    return out


def cover(im, w, h):
    """Fill w x h, cropping the overflow, centred."""
    s = max(w / im.width, h / im.height)
    sm = im.resize((math.ceil(im.width * s), math.ceil(im.height * s)), Image.Resampling.LANCZOS)
    x, y = (sm.width - w) // 2, (sm.height - h) // 2
    return sm.crop((x, y, x + w, y + h))


def pow2(n, cap=1024):
    return min(cap, 1 << max(3, math.ceil(math.log2(max(n, 1)))))


def round_portrait(bust, n=256, head=0.62):
    """The briefing's round portrait: the studio backdrop of tools/hudart.marine_portrait and the marine framed
    on the head (it has to read at the HUD's 136 px): the helmet, found as the top fifth of the cut-out, is
    scaled to `head` of the circle's width, centred, its top just inside the circle; the shoulders run off."""
    yy, xx = (np.mgrid[0:n, 0:n] + 0.5) / n * 2 - 1
    r = np.hypot(xx, yy)
    back = np.dstack([62 - 30 * r, 72 - 34 * r, 84 - 38 * r, np.full_like(r, 255)]).clip(0, 255).astype(np.uint8)
    out = Image.fromarray(back, 'RGBA')
    bust = crop(bust)
    A = np.asarray(bust.getchannel('A'))[:max(1, bust.height // 5)] > 128
    cols = np.nonzero(A.any(axis=0))[0]
    hx0, hx1 = (cols[0], cols[-1]) if len(cols) else (0, bust.width - 1)
    s = head * n / max(hx1 - hx0 + 1, 1)
    sm = bust.resize((round(bust.width * s), round(bust.height * s)), Image.Resampling.LANCZOS)
    layer = Image.new('RGBA', (n, n), (0, 0, 0, 0))
    layer.paste(sm, (round(n / 2 - (hx0 + hx1) / 2 * s), round(0.07 * n)), sm)
    out.alpha_composite(layer)
    disc = np.clip((1 - r) * n / 2 + 0.5, 0, 1)                      # anti-aliased circle
    a = np.asarray(out).copy()
    a[..., 3] = (a[..., 3] * disc).astype(np.uint8)
    return Image.fromarray(a, 'RGBA')


def edge_fade(im, frac=0.08, color=NAVY):
    """Flatten onto `color`, then fade alpha out over the outer `frac` of each side."""
    w, h = im.size
    base = Image.new('RGBA', (w, h), color + (255,))
    base.alpha_composite(im)
    yy, xx = np.mgrid[0:h, 0:w]
    d = np.minimum(np.minimum(xx, w - 1 - xx) / (w * frac), np.minimum(yy, h - 1 - yy) / (h * frac))
    a = np.asarray(base).copy()
    a[..., 3] = (255 * np.clip(d, 0, 1) ** 1.5).astype(np.uint8)
    return Image.fromarray(a, 'RGBA')


def bezel(im, warn, n=512):
    """The portrait housing scaled and centred so its hole is the health ring's outer edge: the script draws
    it Y.BEZEL wide, centred on the ring Y.RING wide (src/HUD.galaxy)."""
    im = crop(im)
    solid = im.getchannel('A').point(lambda v: 255 if v > 128 else 0)
    c = (im.width // 2, im.height // 2)
    if solid.getpixel(c):
        warn('no hole in the middle of the bezel')
        return fit(im, n, n, 0)
    ImageDraw.floodfill(solid, c, 128)
    hole = np.asarray(solid) == 128
    if hole[0].any() or hole[-1].any() or hole[:, 0].any() or hole[:, -1].any():
        warn('the bezel\'s hole is open to the outside')
        return fit(im, n, n, 0)
    ys, xs = np.nonzero(hole)
    cx, cy, rh = xs.mean(), ys.mean(), math.sqrt(len(xs) / math.pi)
    want = hudart.R_OUT * 1.02 * Y.RING / Y.BEZEL * n               # the hole's radius in this texture
    s = want / rh
    sm = im.resize((round(im.width * s), round(im.height * s)), Image.Resampling.LANCZOS)
    out = Image.new('RGBA', (n, n), (0, 0, 0, 0))
    out.paste(sm, (round(n / 2 - cx * s), round(n / 2 - cy * s)), sm)
    return out


def slice9(src, w, h, cs, d):
    """A nine-slice of `src` (corners `cs` px) laid out at w x h with corners `d` px."""
    W, H = src.size
    cs = int(min(cs, W / 2 - 1, H / 2 - 1))
    d = int(min(d, w / 2, h / 2))
    out = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    xs, xd = [0, cs, W - cs, W], [0, d, w - d, w]
    ys, yd = [0, cs, H - cs, H], [0, d, h - d, h]
    for i in range(3):
        for j in range(3):
            sw, sh = xs[i + 1] - xs[i], ys[j + 1] - ys[j]
            dw, dh = xd[i + 1] - xd[i], yd[j + 1] - yd[j]
            if min(sw, sh, dw, dh) <= 0:
                continue
            piece = src.crop((xs[i], ys[j], xs[i + 1], ys[j + 1])).resize((dw, dh), Image.Resampling.LANCZOS)
            out.paste(piece, (xd[i], yd[j]))
    return out


def kit(src, ratio, base, corner):
    """One bucket: drawn at the bucket's true proportions, then squeezed to a power-of-two texture (the
    stretch to the control's size undoes the squeeze)."""
    src = crop(src, 128)
    if ratio >= 1:
        w, h = round(base * ratio), base
    else:
        w, h = base, round(base / ratio)
    cs = 0.14 * min(src.size) if corner < 0.2 else 0.3 * min(src.size)
    im = slice9(src, w, h, cs, corner * min(w, h))
    return im.resize((pow2(w), pow2(h)), Image.Resampling.LANCZOS)


def dull(im, k=0.55, sat=0.3):
    a = np.asarray(im).astype(float)
    g = a[..., :3].mean(axis=2, keepdims=True)
    a[..., :3] = (g + (a[..., :3] - g) * sat) * k
    return Image.fromarray(a.clip(0, 255).astype(np.uint8), 'RGBA')


def brighten(im, k=1.35):
    a = np.asarray(im).astype(float)
    a[..., :3] = a[..., :3] * k + 20
    return Image.fromarray(a.clip(0, 255).astype(np.uint8), 'RGBA')


def cells(sheet, cols, rows, warn):
    """Cut a glow sheet into cols x rows icons, splitting at the darkest line near each expected boundary."""
    A = np.asarray(sheet.getchannel('A')).astype(float)

    def cuts(profile, n):
        L = len(profile)
        out = [0]
        for k in range(1, n):
            c = round(L * k / n)
            r = L // (3 * n)
            out.append(c - r + int(np.argmin(profile[c - r:c + r])))
        return out + [L]

    xs, ys = cuts(A.sum(axis=0), cols), cuts(A.sum(axis=1), rows)
    out = []
    for j in range(rows):
        for i in range(cols):
            cell = sheet.crop((xs[i], ys[j], xs[i + 1], ys[j + 1]))
            ca = np.asarray(cell.getchannel('A'))
            if (ca[0] > 40).any() or (ca[-1] > 40).any() or (ca[:, 0] > 40).any() or (ca[:, -1] > 40).any():
                warn('icon %d touches its cell\'s edge (uneven grid?)' % (len(out) + 1))
            out.append(cell)
    return out


# ---------------------------------------------------------------- the set
def textures(src=None, levels=None, report=None):
    """{texture name: PIL image} for whatever images are in `src` (default assets/ui-gen). `levels` are the
    level ids (build.py LEVELS; None: every mission_* image). `report` collects (file, warning) pairs."""
    src = pathlib.Path(src or GEN_DIR)
    report = report if report is not None else []
    t = {}

    def find(stem):
        for ext in EXTS:
            if (src / (stem + ext)).exists():
                return src / (stem + ext)
        return None

    def load(stem, black=False):
        p = find(stem)
        if p is None:
            return None
        im = Image.open(p)
        im.load()
        return (key_black if black else key_magenta)(im, lambda m: report.append((p.name, m)))

    def warner(stem):
        return lambda m: report.append((find(stem).name, m))

    for name in MARINE_LOOKS:
        im = load('portrait_' + name)
        if im is not None:
            t['face_m_' + name] = round_portrait(im)
    for k in CLASSES:
        im = load('class_' + k)
        if im is not None:
            t['cls_' + k] = fit(im, 128, 128, 0.02)
    for stem, it in ITEMS.items():
        im = load('gun_' + stem)
        if im is None:
            im = load('item_' + stem)
        if im is not None:
            t['gi%d' % it] = fit(im, 256, 128) if it <= 21 else fit(im, 128, 128)
    if levels is None:                                   # every level that has a picture
        levels = sorted({q.stem[len('mission_'):] for q in src.glob('mission_*') if q.suffix.lower() in EXTS})
    for lid in levels:
        p = find('mission_' + lid)
        if p is not None:
            t['mis_' + lid] = edge_fade(cover(Image.open(p).convert('RGBA'), 512, 512))
    im = load('starchart', black=True)
    if im is not None:
        t['starchart'] = fit(im, 1024, 512, 0.02)
    loaded = {}
    for name, (stem, base, corner) in KITS.items():
        if stem not in loaded:
            loaded[stem] = load(stem)
        im = loaded[stem]
        if im is None and name == 'buttonhi' and loaded.get('frame_button') is not None:
            im = brighten(loaded['frame_button'])
        if im is None:
            continue
        if name == 'buttonoff':
            im = dull(im)
        for b, r in enumerate(RATIOS):
            t['k_%s_%d' % (name, b)] = kit(im, r, base, corner)
    im = load('hud_bezel')
    if im is not None:
        t['hudbezel'] = bezel(im, warner('hud_bezel'))
    im = load('hud_plate_player')
    if im is not None:
        t['hudplate'] = crop(im).resize((512, 128), Image.Resampling.LANCZOS)
    im = load('hud_plate_squad')
    if im is not None:
        t['teambg'] = crop(im).resize((256, 64), Image.Resampling.LANCZOS)
    im = load('icons_objectives', black=True)
    if im is not None:
        for name, cell in zip(ICONS, cells(im, 4, 3, warner('icons_objectives'))):
            t['ico_' + name] = fit(cell, 128, 128, 0.06)
        box = hudart.tick_box(False).resize((128, 128), Image.Resampling.LANCZOS)
        box.alpha_composite(fit(t['ico_done'], 128, 128, 0.12))
        t['obj1'] = box
        t['blipobj'] = fit(t['ico_target'], 32, 32, 0.0)
    return t


# Names the script tests with AS_Painted before using (the rest replace a drawn texture of the same name).
def new_names(t):
    return sorted(k for k in t if k.startswith(('gi', 'mis_', 'k_', 'ico_')) or k in ('starchart', 'hudbezel', 'hudplate'))


# ---------------------------------------------------------------- previews
def _checker(w, h, n=16):
    yy, xx = np.mgrid[0:h, 0:w]
    v = np.where(((xx // n) + (yy // n)) % 2 == 0, 90, 60).astype(np.uint8)
    return Image.fromarray(np.dstack([v, v, v, np.full_like(v, 255)]), 'RGBA')


def sheet(t, report, path):
    from tools.hudart import font
    keys = [k for k in sorted(t) if not k.startswith('k_') or k.endswith(('_2', '_6'))]
    cell, cols = 180, 8
    rows = (len(keys) + cols - 1) // cols
    head = 24 * (len(report) + 1)
    out = Image.new('RGBA', (cols * cell, head + rows * (cell + 18)), (40, 44, 52, 255))
    d = ImageDraw.Draw(out)
    d.text((8, 4), '%d textures from %s' % (len(t), GEN_DIR), font=font(18), fill=(255, 255, 255, 255))
    for i, (f, m) in enumerate(report):
        d.text((8, 4 + 24 * (i + 1)), '%s: %s' % (f, m), font=font(16), fill=(255, 190, 80, 255))
    for i, k in enumerate(keys):
        x, y = (i % cols) * cell, head + (i // cols) * (cell + 18)
        half = (cell - 8) // 2
        im = t[k].copy()
        im.thumbnail((cell - 8, half - 4))
        bg1 = Image.new('RGBA', (cell - 8, half), NAVY + (255,))
        bg2 = _checker(cell - 8, half)
        for bg in (bg1, bg2):
            bg.alpha_composite(im, ((bg.width - im.width) // 2, (bg.height - im.height) // 2))
        out.alpha_composite(bg1, (x + 4, y + 4))
        out.alpha_composite(bg2, (x + 4, y + 4 + half))
        d.text((x + 4, y + cell - 2), k, font=font(14), fill=(255, 255, 0, 255))
    out.save(path)


def hud_corner(t, path):
    """The HUD's bottom-left as src/HUD.galaxy lays it, with whichever new art there is."""
    drawn, _ = hudart.textures(())
    from tools import uiart
    T = dict(drawn)
    T.update(uiart.textures())
    T.update(t)
    W, H = 900, 300
    out = Image.new('RGBA', (W, H), (34, 36, 40, 255))

    def put(name, x, y, w, h, tint=None):
        im = T[name].resize((max(1, int(w)), max(1, int(h))), Image.Resampling.LANCZOS)
        if tint:
            a = np.asarray(im).astype(float)
            a[..., :3] *= np.array(tint, float) / 255
            im = Image.fromarray(a.astype(np.uint8), 'RGBA')
        out.alpha_composite(im, (int(x), int(y)))

    x, y = 40, 60
    R = Y.RING
    put('plate', x, y, R, R)
    if 'hudplate' in T:
        put('hudplate', x + R // 2, y + R // 2, Y.BAR_W + R // 2, R - R // 2)
    else:
        put('black75', x + R, y + R // 2, Y.BAR_W, R - R // 2)
    face = 'face_m_sarge'
    put(face, x + Y.FACE_X - Y.FACE_R, y + Y.FACE_Y - Y.FACE_R, 2 * Y.FACE_R, 2 * Y.FACE_R)
    put('ringbg', x, y, R, R)
    put('hp%02d' % (hudart.RING_N * 3 // 4), x, y, R, R, Y.HP_TINT)
    if 'hudbezel' in T:
        o = (Y.BEZEL - R) // 2
        put('hudbezel', x - o, y - o, Y.BEZEL, Y.BEZEL)
    put('cls_officer', x + Y.CLS_X, y + Y.CLS_Y, Y.CLS, Y.CLS)
    sx = x + 520
    put('teambg', sx, y + 40, Y.SQ_BG_W, Y.SQ_BG_H)
    put('cls_medic', sx + Y.SQ_CLS_X, y + 40 + Y.SQ_CLS_Y - Y.SQ_BG_Y, Y.SQ_CLS, Y.SQ_CLS)
    put('obj0', sx, y + 160, 44, 44)
    put('obj1', sx + 60, y + 160, 44, 44)
    out.save(path)


if __name__ == '__main__':
    import build  # noqa: E402  (the level ids)
    src = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else GEN_DIR
    GEN_DIR = src.resolve()
    rep = []
    tex = textures(src, [lv[0] for lv in build.LEVELS], rep)
    (ROOT / 'dist').mkdir(exist_ok=True)
    sheet(tex, rep, ROOT / 'dist' / 'genart-sheet.png')
    hud_corner(tex, ROOT / 'dist' / 'genart-hud.png')
    print('%d textures from %s; %d warnings' % (len(tex), src, len(rep)))
    for f, m in rep:
        print('  %s: %s' % (f, m))
