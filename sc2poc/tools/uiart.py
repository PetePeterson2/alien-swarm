"""Art for the screens round the HUD, drawn after Alien Swarm's (nothing of Valve's is copied):

    the hacking minigames: wire tiles (straight and corner, every turn), the sockets either side of a
        wire, the wire's open light, the fast-hack marker, the tumbler's direction switches and the
        terminal's blue and red backdrops, its files and mail icons
    the briefing: a portrait for each of the eight marines, skill pips, the locked-item padlock, the
        squad slot frame, the ready tick
    progression: the level badge, the six promotion medals (Titanium Star .. Iridium Medallion), a medal
        ribbon and an achievement badge

`py tools/uiart.py` writes a contact sheet to dist/ui-sheet.png.
"""
import math
import pathlib
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from tools.hudart import SS, WHITE, draw_big, finish, S, glow, rgba, grid, shrink, marine_portrait, rounded  # noqa: E402

# ---------------------------------------------------------------- hacking: the wire puzzle
# A tile's connections as (N, E, S, W); textures are named by the set they join.
WIRE_SHAPES = {'h': 'EW', 'v': 'NS', 'ws': 'SW', 'nw': 'NW', 'ne': 'NE', 'es': 'ES'}


def wire_tile(joins, n=64):
    """A wire tile: a thick white conductor joining the given sides through the middle, rounded at the bend."""
    im, d = draw_big(n, n)
    c = n / 2
    w = int(n * 0.16 * SS)
    ends = {'N': (c, 0), 'E': (n, c), 'S': (c, n), 'W': (0, c)}
    pts = [ends[k] for k in joins]
    if len(pts) == 2 and (pts[0][0] == pts[1][0] or pts[0][1] == pts[1][1]):
        d.line(S(pts), fill=WHITE, width=w)
    else:
        # A quarter arc round the corner the two sides share.
        cx = 0 if 'W' in joins else n
        cy = 0 if 'N' in joins else n
        r = c
        box = [(cx - r) * SS, (cy - r) * SS, (cx + r) * SS, (cy + r) * SS]
        start = {(0, 0): 0, (n, 0): 90, (n, n): 180, (0, n): 270}[(cx, cy)]
        d.arc(box, start, start + 90, fill=WHITE, width=w)
    # Contact pads where the conductor meets the tile's edge.
    for k in joins:
        x, y = ends[k]
        pad = n * 0.11
        d.rectangle(S([(x - pad, y - pad), (x + pad, y + pad)]), fill=WHITE)
    return finish(im, n, n)


def wire_tile_bg(n=64):
    im, d = draw_big(n, n)
    d.rectangle([SS, SS, n * SS - SS, n * SS - SS], fill=(14, 18, 24, 255), outline=(70, 80, 100, 255), width=2 * SS)
    return finish(im, n, n)


def socket(side, n=64):
    """The plug either side of a wire: a block with three pins pointing into the grid."""
    im, d = draw_big(n, n)
    x0, x1 = (8, 40) if side == 'l' else (24, 56)
    d.rounded_rectangle(S([(x0, 14), (x1, 50)]), radius=5 * SS, fill=(220, 225, 230, 255))
    d.rectangle(S([(x0 + 6, 20), (x1 - 6, 44)]), fill=(30, 34, 40, 255))
    px0, px1 = (40, 64) if side == 'l' else (0, 24)
    d.rectangle(S([(px0, 28), (px1, 36)]), fill=WHITE)
    for py in (24, 32, 40):
        d.ellipse(S([((x0 + x1) / 2 - 2.5, py - 2.5), ((x0 + x1) / 2 + 2.5, py + 2.5)]), fill=(120, 220, 255, 255))
    return finish(im, n, n)


def open_light(n=64):
    """The wire's lamp: a ringed disc with a door symbol, lit white when its wire carries current."""
    im, d = draw_big(n, n)
    d.ellipse(S([(4, 4), (60, 60)]), fill=(255, 255, 255, 255))
    d.ellipse(S([(10, 10), (54, 54)]), fill=(26, 30, 36, 255))
    d.rectangle(S([(20, 18), (30, 46)]), fill=WHITE)
    d.rectangle(S([(34, 18), (44, 46)]), fill=WHITE)
    return finish(im, n, n)


def fast_marker(w=16, h=64):
    a = np.ones((h, w))
    return rgba((255, 40, 30), a)


def tumbler_switch(up, n=64):
    im, d = draw_big(n, n)
    d.rounded_rectangle(S([(4, 4), (60, 60)]), radius=6 * SS, fill=(20, 26, 40, 255), outline=(150, 190, 230, 255), width=2 * SS)
    if up:
        d.polygon(S([(32, 14), (50, 44), (14, 44)]), fill=WHITE)
    else:
        d.polygon(S([(14, 20), (50, 20), (32, 50)]), fill=WHITE)
    return finish(im, n, n)


def backdrop(base, n=256):
    """The terminal's screen: a dark gradient with scanlines and a faint grid."""
    y = np.linspace(0, 1, n)[:, None].repeat(n, 1)
    x = np.linspace(0, 1, n)[None, :].repeat(n, 0)
    b = np.array(base, float)
    col = b[None, None] * (0.55 + 0.45 * (1 - y))[..., None]
    col *= (1 - 0.25 * np.hypot(x - 0.5, y - 0.5))[..., None]
    scan = (np.arange(n) % 3 == 0)[:, None]
    col = col * np.where(scan, 0.82, 1.0)[..., None]
    gridline = ((np.arange(n) % 32) == 0)
    col[gridline, :] = col[gridline, :] * 1.25
    col[:, gridline] = col[:, gridline] * 1.25
    return rgba(np.clip(col, 0, 255), np.full((n, n), 0.96))


def icon_files(n=128):
    im, d = draw_big(n, n)
    d.polygon(S([(14, 34), (50, 34), (58, 44), (114, 44), (114, 106), (14, 106)]), outline=WHITE, width=3 * SS, fill=(150, 190, 220, 40))
    for k in range(3):
        d.rectangle(S([(30 + k * 8, 54 + k * 6), (96 + k * 4, 98)]), outline=WHITE, width=2 * SS)
    return glow(finish(im, n, n), 3.0, 0.5)


def icon_mail(n=128):
    im, d = draw_big(n, n)
    d.rectangle(S([(16, 32), (112, 98)]), outline=WHITE, width=3 * SS, fill=(150, 190, 220, 40))
    d.line(S([(16, 32), (64, 70), (112, 32)]), fill=WHITE, width=3 * SS)
    return glow(finish(im, n, n), 3.0, 0.5)


# ---------------------------------------------------------------- the briefing
# The eight marines' portraits: the helmet renderer with each marine's own armour, stripe and visor.
MARINE_LOOKS = {
    'sarge':    dict(armour=(110, 124, 98), stripe=(200, 170, 70), trim=(190, 160, 70)),
    'jaeger':   dict(armour=(96, 110, 122), stripe=(200, 170, 70), visor=((20, 60, 90), (120, 200, 255))),
    'wildcat':  dict(armour=(132, 90, 72), stripe=(60, 90, 160), visor=((90, 20, 10), (255, 120, 60))),
    'wolfe':    dict(armour=(84, 88, 96), stripe=(60, 90, 160)),
    'faith':    dict(armour=(190, 186, 176), stripe=(170, 40, 40), visor=((40, 70, 90), (170, 230, 255))),
    'bastille': dict(armour=(150, 146, 136), stripe=(170, 40, 40)),
    'crash':    dict(armour=(150, 130, 70), stripe=(70, 70, 76), visor=((60, 50, 10), (255, 220, 90))),
    'vegas':    dict(armour=(120, 108, 74), stripe=(70, 70, 76), trim=(210, 210, 215)),
}


def pip(on, n=16):
    im, d = draw_big(n, n)
    d.rectangle([SS, SS, n * SS - SS, n * SS - SS], fill=(235, 240, 245, 255) if on else (40, 46, 54, 255))
    return finish(im, n, n)


def padlock(n=64):
    im, d = draw_big(n, n)
    d.arc(S([(18, 8), (46, 36)]), 180, 360, fill=WHITE, width=5 * SS)
    d.line(S([(18, 22), (18, 30)]), fill=WHITE, width=5 * SS)
    d.line(S([(46, 22), (46, 30)]), fill=WHITE, width=5 * SS)
    d.rounded_rectangle(S([(12, 28), (52, 58)]), radius=4 * SS, fill=WHITE)
    d.ellipse(S([(28, 36), (36, 44)]), fill=(20, 24, 30, 255))
    d.rectangle(S([(30, 42), (34, 50)]), fill=(20, 24, 30, 255))
    return finish(im, n, n)


def tick(n=64):
    im, d = draw_big(n, n)
    d.line(S([(12, 34), (26, 48), (54, 14)]), fill=(70, 230, 90, 255), width=8 * SS, joint='curve')
    return finish(im, n, n)


def slot_frame(w=256, h=384):
    return rounded(w, h, 8, (12, 20, 30, 225), (64, 112, 150, 255), 2)


# ---------------------------------------------------------------- progression
def level_badge(n=64):
    """A chevron badge behind the player's level number."""
    im, d = draw_big(n, n)
    d.polygon(S([(6, 10), (32, 2), (58, 10), (58, 46), (32, 62), (6, 46)]), fill=(28, 52, 76, 255), outline=(150, 200, 235, 255))
    d.line(S([(6, 10), (32, 2), (58, 10), (58, 46), (32, 62), (6, 46), (6, 10)]), fill=(150, 200, 235, 255), width=3 * SS)
    return finish(im, n, n)


PROMOTIONS = [('Titanium Star', (180, 186, 196)), ('Carbide Star', (90, 94, 104)), ('Gallium Cross', (196, 210, 226)),
              ('Platinum Star', (226, 228, 222)), ('Osmium Star', (110, 140, 190)), ('Iridium Medallion', (220, 200, 140))]


def promotion_medal(k, n=128):
    name, col = PROMOTIONS[k]
    im, d = draw_big(n, n)
    c = n / 2
    # The ribbon.
    d.polygon(S([(c - 22, 0), (c + 22, 0), (c + 14, 46), (c - 14, 46)]), fill=(40, 70, 120, 255))
    d.rectangle(S([(c - 4, 0), (c + 4, 46)]), fill=(200, 60, 50, 255))
    cy = 82
    if 'Cross' in name:
        for ang in (0, 90):
            a = math.radians(ang)
            d.polygon(S([(c + math.cos(a) * 34 - math.sin(a) * 10, cy + math.sin(a) * 34 + math.cos(a) * 10),
                         (c + math.cos(a) * 34 + math.sin(a) * 10, cy + math.sin(a) * 34 - math.cos(a) * 10),
                         (c - math.cos(a) * 34 + math.sin(a) * 10, cy - math.sin(a) * 34 - math.cos(a) * 10),
                         (c - math.cos(a) * 34 - math.sin(a) * 10, cy - math.sin(a) * 34 + math.cos(a) * 10)]), fill=col + (255,))
    elif 'Medallion' in name:
        d.ellipse(S([(c - 34, cy - 34), (c + 34, cy + 34)]), fill=col + (255,))
        d.ellipse(S([(c - 24, cy - 24), (c + 24, cy + 24)]), outline=(120, 100, 50, 255), width=3 * SS)
    pts = []
    for i in range(10):
        a = math.radians(-90 + i * 36)
        r = 30 if i % 2 == 0 else 13
        if 'Star' in name or 'Medallion' in name:
            pts.append((c + math.cos(a) * r, cy + math.sin(a) * r))
    if pts:
        d.polygon(S(pts), fill=(255, 255, 255, 255) if 'Medallion' in name else col + (255,), outline=(40, 40, 46, 255))
    return finish(im, n, n)


def medal_ribbon(n=96):
    """The debrief's medal: a white star on a disc under a ribbon, tinted by the script."""
    im, d = draw_big(n, n)
    c = n / 2
    d.polygon(S([(c - 16, 0), (c + 16, 0), (c + 10, 34), (c - 10, 34)]), fill=(200, 200, 200, 255))
    d.ellipse(S([(c - 26, 34), (c + 26, 86)]), fill=WHITE)
    pts = [(c + math.cos(math.radians(-90 + i * 36)) * (18 if i % 2 == 0 else 8), 60 + math.sin(math.radians(-90 + i * 36)) * (18 if i % 2 == 0 else 8)) for i in range(10)]
    d.polygon(S(pts), fill=(40, 44, 52, 255))
    return finish(im, n, n)


def achievement_badge(n=96):
    im, d = draw_big(n, n)
    c = n / 2
    d.polygon(S([(c, 4), (n - 8, 22), (n - 14, 70), (c, 92), (14, 70), (8, 22)]), fill=(30, 50, 70, 255))
    d.line(S([(c, 4), (n - 8, 22), (n - 14, 70), (c, 92), (14, 70), (8, 22), (c, 4)]), fill=(240, 200, 80, 255), width=4 * SS)
    pts = [(c + math.cos(math.radians(-90 + i * 36)) * (22 if i % 2 == 0 else 9), 48 + math.sin(math.radians(-90 + i * 36)) * (22 if i % 2 == 0 else 9)) for i in range(10)]
    d.polygon(S(pts), fill=(240, 200, 80, 255))
    return finish(im, n, n)


# ---------------------------------------------------------------- equipment icons
# Every item of the equipment list (src/State.galaxy AS_IT_*), as line art: weapons on a 128 x 64 grid
# (drawn 256 x 128), extras on 64 x 64 (drawn 128 x 128). The ten guns the HUD already had keep their drawings.
def _equip_specs():
    from tools.hudart import GUNS, ITEMS, _rect, _circle, _stock, _grip
    R, C = _rect, _circle
    sentry_wide = ([R(46, 6, 74, 16), R(74, 9, 90, 13), C(58, 28, 9), [(58, 36), (40, 58), (46, 58), (58, 42), (70, 58), (76, 58), (58, 36)], R(54, 16, 62, 22)],
                   [[(52, 25), (64, 25)], [(52, 28), (64, 28)], [(52, 31), (64, 31)]])

    def sentry_variant(mark):
        shapes, strokes = sentry_wide
        return (shapes + mark[0], strokes + mark[1])
    w = {
        1: GUNS[1],
        2: (GUNS[1][0] + [C(96, 20, 5)], GUNS[1][1] + [[(92, 20), (100, 20)], [(96, 16), (96, 24)]]),
        3: GUNS[2],
        4: ([[(6, 36), (14, 26), (38, 24), (38, 34), (24, 36), (14, 44), (8, 44)], R(38, 22, 66, 35), _grip(44, 35), R(66, 23, 122, 27), R(66, 28, 116, 32),
             R(70, 32, 100, 39), R(52, 12, 66, 22)],
            [[(74, 35), (96, 35)], [(55, 17), (63, 17)]]),
        5: GUNS[5],
        6: sentry_wide,
        7: ([R(46, 40, 82, 52), [(52, 40), (56, 14), (72, 14), (76, 40)], C(64, 10, 5)],
            [[(60, 24), (68, 24)], [(64, 20), (64, 28)], [(40, 30), (34, 26)], [(88, 30), (94, 26)], [(42, 20), (34, 14)], [(86, 20), (94, 14)]]),
        8: ([[(36, 18), (92, 18), (98, 26), (98, 54), (30, 54), (30, 26)], R(48, 10, 80, 18)],
            [[(30, 34), (98, 34)], [(56, 40), (56, 48)], [(64, 40), (64, 48)], [(72, 40), (72, 48)]]),
        9: GUNS[3],
        10: GUNS[9],
        11: GUNS[6],
        12: ([[(8, 34), (20, 24), (48, 24), (48, 40), (20, 40)], R(48, 26, 84, 38), _grip(56, 38), [(84, 28), (108, 22), (112, 32), (108, 42), (84, 36)], C(30, 32, 5)],
             [[(26, 32), (34, 32)], [(30, 28), (30, 36)], [(112, 32), (124, 32)]]),
        13: ([[(10, 22), (44, 22), (44, 28), (26, 28), (22, 40), (14, 40), (16, 28), (10, 28)], R(44, 23, 60, 27), R(20, 28, 26, 46),
              [(64, 32), (98, 32), (98, 38), (80, 38), (76, 50), (68, 50), (70, 38), (64, 38)], R(98, 33, 114, 37), R(74, 38, 80, 56)],
             [[(14, 25), (40, 25)], [(68, 35), (94, 35)]]),
        14: GUNS[4],
        15: sentry_variant(([C(84, 11, 5)], [[(80, 11), (88, 11)], [(84, 7), (84, 15)], [(81, 8), (87, 14)], [(87, 8), (81, 14)]])),
        16: GUNS[7],
        17: GUNS[10],
        18: sentry_variant(([[(84, 4), (88, 10), (86, 16), (82, 16), (80, 10)]], [])),
        19: ([[(6, 34), (14, 24), (36, 24), (36, 42), (14, 44)], R(36, 22, 56, 42), [(56, 26), (116, 26), (122, 32), (116, 38), (56, 38)], _grip(40, 42)],
             [[(60, 29), (114, 29)], [(60, 35), (114, 35)], [(64, 26), (66, 22)], [(74, 26), (76, 22)], [(84, 26), (86, 22)], [(94, 26), (96, 22)], [(104, 26), (106, 22)]]),
        20: sentry_variant(([R(74, 7, 96, 15)], [])),
        21: GUNS[8],
    }
    e = {
        22: ITEMS['medkit'],
        23: ([[(8, 40), (30, 40), (34, 34), (44, 34), (44, 46), (34, 46), (30, 44), (8, 44)], R(14, 44, 22, 58), [(44, 37), (54, 33), (56, 36), (46, 41)]],
             [[(56, 34), (62, 28)], [(58, 38), (63, 40)], [(55, 31), (58, 24)]]),
        24: ITEMS['flare'],
        25: ([R(18, 20, 46, 44), C(32, 32, 6)], [[(46, 32), (62, 32)], [(8, 20), (18, 26)], [(8, 44), (18, 38)]]),
        26: ([[(14, 10), (50, 10), (54, 22), (48, 56), (16, 56), (10, 22)]], [[(32, 10), (32, 56)], [(16, 30), (48, 30)], [(18, 44), (46, 44)]]),
        27: ([R(24, 36, 40, 56), [(26, 36), (28, 18), (36, 18), (38, 36)], C(32, 12, 5)],
             [[(14, 18), (8, 12)], [(50, 18), (56, 12)], [(12, 30), (4, 30)], [(52, 30), (60, 30)]]),
        28: ([[(8, 40), (40, 40), (46, 44), (40, 48), (8, 48)], [(14, 28), (46, 28), (52, 32), (46, 36), (14, 36)], [(20, 16), (52, 16), (58, 20), (52, 24), (20, 24)]],
             [[(8, 44), (2, 44)], [(14, 32), (6, 32)], [(20, 20), (12, 20)]]),
        29: ([C(30, 36, 16), R(26, 14, 38, 21)], [[(38, 16), (48, 10), (50, 16)], [(22, 36), (38, 36)], [(30, 28), (30, 44)], [(24, 30), (36, 42)], [(36, 30), (24, 42)]]),
        30: ([R(24, 8, 40, 18), R(20, 18, 44, 46), [(28, 46), (36, 46), (32, 60)]], [[(26, 26), (38, 26)], [(26, 32), (38, 32)], [(26, 38), (38, 38)]]),
        31: ([[(20, 56), (44, 56), (40, 44), (24, 44)], R(28, 14, 36, 44), C(32, 10, 6)],
             [[(22, 22), (42, 22)], [(22, 30), (42, 30)], [(22, 38), (42, 38)], [(14, 10), (8, 4)], [(50, 10), (56, 4)]]),
        32: ([[(14, 10), (50, 10), (54, 22), (48, 56), (16, 56), (10, 22)]], [[(34, 16), (26, 32), (36, 32), (28, 50)]]),
        33: ([C(32, 40, 14), R(28, 22, 36, 28)], [[(18, 40), (46, 40)], [(24, 18), (20, 8)], [(32, 18), (32, 6)], [(40, 18), (44, 8)]]),
        34: ([R(10, 24, 34, 40), [(34, 22), (54, 12), (54, 52), (34, 42)]], [[(56, 20), (62, 16)], [(57, 32), (63, 32)], [(56, 44), (62, 48)]]),
        35: ([[(14, 30), (14, 18), (22, 14), (30, 18), (38, 14), (46, 18), (50, 26), (50, 46), (42, 56), (20, 56), (12, 46)]],
             [[(22, 14), (22, 30)], [(30, 18), (30, 30)], [(38, 14), (38, 30)], [(14, 30), (50, 30)]]),
        36: ITEMS['grenade'],
        37: ([C(20, 34, 10), C(44, 34, 10), R(14, 20, 50, 26)], [[(30, 34), (34, 34)], [(8, 26), (4, 34)], [(56, 26), (60, 34)]]),
        38: ([[(16, 14), (48, 14), (52, 20), (52, 54), (12, 54), (12, 20)]],
             [[(20, 22), (20, 46)], [(28, 22), (28, 46)], [(36, 22), (36, 46)], [(44, 22), (44, 46)], [(16, 8), (16, 14)], [(48, 8), (48, 14)]]),
    }
    return w, e


def equipment_icons():
    from tools.hudart import line_icon
    w, e = _equip_specs()
    t = {}
    for i, spec in w.items():
        t['it%d' % i] = line_icon(spec, 256, 128, 128, 64)
    for i, spec in e.items():
        t['it%d' % i] = line_icon(spec, 128, 128, 64, 64)
    return t


def textures():
    t = {}
    t.update(equipment_icons())
    for name, joins in WIRE_SHAPES.items():
        t['wire_' + name] = wire_tile(joins)
    t['wire_bg'] = wire_tile_bg()
    t['sock_l'] = socket('l')
    t['sock_r'] = socket('r')
    t['wire_open'] = open_light()
    t['fastmark'] = fast_marker()
    t['tumb_up'] = tumbler_switch(True)
    t['tumb_dn'] = tumbler_switch(False)
    t['comp_blue'] = backdrop((24, 52, 88))
    t['comp_red'] = backdrop((96, 18, 16))
    t['icon_files'] = icon_files()
    t['icon_mail'] = icon_mail()
    for key, style in MARINE_LOOKS.items():
        t['face_m_' + key] = marine_portrait(style)
    t['pip1'] = pip(True)
    t['pip0'] = pip(False)
    t['padlock'] = padlock()
    t['tickok'] = tick()
    t['slot'] = slot_frame()
    t['lvlbadge'] = level_badge()
    for k in range(len(PROMOTIONS)):
        t['promo%d' % (k + 1)] = promotion_medal(k)
    t['medal'] = medal_ribbon()
    t['achieve'] = achievement_badge()
    return t


if __name__ == '__main__':
    from tools.hudart import sheet
    t = textures()
    (ROOT / 'dist').mkdir(exist_ok=True)
    sheet(t, ROOT / 'dist' / 'ui-sheet.png')
    print(len(t), 'textures')
