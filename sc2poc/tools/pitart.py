"""The drop beyond an outdoor deck's railing, and the stairs between floors, drawn after Alien Swarm's.

AS's opening (lb-01, lb-02 and the user's captures of the dock) stands on catwalks over a real drop: steel
lattice towers and trusses going down into blue haze, fat pipes slung under the walkways, lamps and pink
sparks far below, and a bright fog at the bottom where the light pools. The port's open cells ('o') are that
pit now (tools/heights.py DROP): this module draws what is down there.

- KO<n>_<ox><oy>: the pit floor tiles (4x4, 2x2, 1x1, uv'd from world position mod 4 like the ceiling), each
  carrying HAZE added layers of thin fog stacked up the drop, so whatever stands lower is seen through more of
  them: the deeper, the bluer and the paler, as AS's fogged drop is. (Added quads are the blend that works
  on map-written M3s; alpha blending draws its clear parts opaque.)
- KSkirt, KSkirt1, KSkirt3: the deck's steel side, dropping from its edge to the pit floor over the ring of
  edge cells (the terrain's slope there), in the stair cells' three shapes.
- KPitTower*, KPitGirder, KPitPipe, KPitGlow*, KPitShaft, KPitPool: lattice towers with a lamp on top,
  trusses, a fat pipe, lamps and pink sparks hanging in the haze, a floodlight's shaft down into it, a pool of
  lit fog far down; laid by the script as dressing (AS_KitDecal at the pit floor's height) from spots().
- KPitBrace: the catwalk's outrigger under the deck's edge, a beam out over the drop with a strut under it and
  a leg from its end down out of sight, so a walkway reads as standing on steel over the drop; laid at the
  deck's height along its edges.
- KW9T<F|E|O>: a building's concrete outer wall from its roof down to the pit floor.

Stairs (tools/level.py stair_pieces uses these textures; rails here): AS's stairs (lb-04 and the user's
capture by the tech doors) are yellow-nosed steel treads over dark risers, between yellow stringers, with a
yellow handrail down each open side: KSRailW/E (and the half-rise KSRailWh/Eh) are those handrails.
"""
import math

import numpy as np

from tools.shipkit import _noise, _img

FOG = np.array((39, 53, 86), float)        # landingbay_01's exterior fog colour
HAZE = (1.0, 2.05, 3.1, 4.15, 5.2)         # added fog layers over the pit floor (the decks are 6.5 to 9.4 above it)
TOWER_H = 6.4                              # a lattice tower's top above the pit floor: below every deck
GIRDER_Z = 4.4
PIPE_Z = 3.3


# ------------------------------------------------------------------ textures
def tex_pit_floor(size=512):
    """The bottom of the drop, a 4x4-cell tile: far below and fogged, so near black but for the fog's own glow,
    the roofs of lower structures as darker slabs with paler edges, and a few lamps."""
    n = _noise(size, 90, 611, 4); f = _noise(size, 10, 613, 2)
    glow = FOG[None, None] * (0.12 + 0.3 * np.clip(n - 0.3, 0, 1)[..., None] + 0.05 * f[..., None])
    yy, xx = np.mgrid[0:size, 0:size].astype(np.float32)
    rng = np.random.default_rng(617)
    # Roofs far down, only just darker than the fog round them, their edges lost in it.
    from PIL import ImageFilter
    roofs = np.zeros((size, size), np.float32)
    for _ in range(6):
        x0, y0 = rng.integers(0, size, 2); w, h = rng.integers(70, 200, 2)
        u = (xx - x0) % size; v = (yy - y0) % size
        roofs = np.maximum(roofs, ((u < w) & (v < h)).astype(np.float32))
    roofs = np.asarray(_img(roofs * 255).convert('L').filter(ImageFilter.GaussianBlur(6))).astype(np.float32) / 255
    glow *= (1 - 0.45 * roofs)[..., None]
    # Long pipes and a girder far down, darker lines across the tile (wrapping, so tiles join).
    for c, wdt in ((140, 7), (395, 4)):
        d = np.abs(((yy - c) % size + size / 2) % size - size / 2)
        glow *= (1 - 0.5 * np.clip(1 - d / wdt, 0, 1))[..., None]
    # Two lamps a tile far down, each a soft pool of light in the fog round a small hot point.
    for k in range(2):
        cx, cy = rng.integers(0, size, 2)
        r = np.hypot(((xx - cx + size / 2) % size) - size / 2, ((yy - cy + size / 2) % size) - size / 2)
        col = np.array((150, 185, 255)) if k == 0 else np.array((255, 110, 190))
        glow += col[None, None] * (np.clip(1 - r / 90, 0, 1) ** 2 * 0.28 + np.clip(1 - r / 5, 0, 1) * 0.7)[..., None]
    return _img(np.full((8, 8, 3), 6.0)), _img(np.clip(glow, 0, 255))


def tex_pit_haze(size=512):
    """One added fog layer, tileable over 4x4 cells: thin cloud, never quite gone, never thick."""
    n = _noise(size, 150, 631, 4); f = _noise(size, 40, 633, 3)
    g = 0.2 + 1.0 * np.clip(n * 0.9 + f * 0.3 - 0.25, 0, 1) ** 1.3
    tint = FOG * 0.36 + np.array((3, 5, 10))
    return _img(g[..., None] * tint[None, None])


def tex_pit_glow(tint, size=64):
    """A lamp far down in the haze, added: a hot point in a wide soft halo."""
    yy, xx = np.mgrid[0:size, 0:size] / (size - 1) * 2 - 1
    r = np.hypot(xx, yy)
    g = np.clip(1 - r, 0, 1) ** 2.2 * 0.55 + np.clip(1 - r / 0.18, 0, 1) * 0.95
    return _img(np.dstack([g * tint[0], g * tint[1], g * tint[2]]))


def tex_pit_skirt(w=128, h=1024):
    """The deck's side, top (v 0) at its edge down to the pit floor (v 1), one cell wide: the edge plate in worn
    yellow and black, a heavy I-beam with a pipe slung under it, then the steel lattice holding the walkway up,
    a column at the cell's edge with cross bracing, going dark and then blue into the haze below."""
    v = np.linspace(0, 1, h)[:, None] * np.ones((1, w))
    u = np.linspace(0, 1, w)[None, :] * np.ones((h, 1))
    n = _noise(0, 30, 641, 3, (h, w))
    steel = np.array((62, 68, 80), float)
    a = np.zeros((h, w, 3)) + np.array((14, 17, 24))
    lat = np.zeros((h, w))
    # The column at the cell's west edge, and the bracing in bays a unit tall (the piece spans about eight).
    lat = np.maximum(lat, np.clip(1 - np.abs(u - 0.06) / 0.05, 0, 1))
    bay = 1.0 / 8.0
    t = (v % bay) / bay
    for d in (u, 1 - u):
        lat = np.maximum(lat, np.clip(1 - np.abs(t - d) * 10, 0, 1) * 0.9)
    lat = np.maximum(lat, np.clip(1 - np.abs(t - 0.02) / 0.02, 0, 1))
    lit = np.clip(1 - v * 1.25, 0.15, 1)
    a = a * (1 - lat[..., None]) + steel[None, None] * (0.75 + 0.35 * n[..., None]) * lit[..., None] * lat[..., None]
    # The fat pipe slung along the top, shaded round.
    py, pr = 0.135, 0.032
    d = np.abs(v - py) / pr
    pipe = d < 1
    shade = np.sqrt(np.clip(1 - d ** 2, 0, 1))
    a[pipe] = (np.array((92, 96, 104))[None] * (0.35 + 0.75 * shade[pipe][:, None]))
    # The I-beam under the edge plate: lit top flange, dark web, a bottom flange.
    beam = (v > 0.03) & (v < 0.095)
    a[beam] = steel * 0.55 * (0.85 + 0.3 * n[beam][:, None])
    a[(v > 0.03) & (v < 0.04)] = steel * 1.25
    a[(v > 0.085) & (v < 0.095)] = steel * 0.9
    # The edge plate: worn hazard stripes, the deck's frame seen from the side.
    top = v < 0.03
    stripe = (((u * w + v * h) // 14) % 2 == 0)
    a[top] = np.where(stripe[top][:, None], np.array((168, 132, 36)), np.array((26, 26, 24))) * (0.75 + 0.35 * n[top][:, None])
    # Rivets along the beam.
    for x in range(8, w, 20):
        a[int(0.045 * h):int(0.045 * h) + 3, x:x + 3] = (150, 150, 150)
    # The haze takes over going down: emissive fog that thickens toward the bottom.
    deep = np.clip((v - 0.12) / 0.88, 0, 1) ** 1.1
    e = FOG[None, None] * (0.12 + 0.95 * deep[..., None]) * (0.85 + 0.3 * n[..., None]) * (1 - 0.55 * lat[..., None])
    e[v < 0.1] = 0
    return _img(a), _img(e)


def tex_pit_pool(size=128):
    """Lit fog far down round a lamp, added flat: wide and faint, brightest in the middle."""
    yy, xx = np.mgrid[0:size, 0:size] / (size - 1) * 2 - 1
    r = np.hypot(xx, yy)
    n = _noise(size, 30, 691, 3)
    g = np.clip(1 - r, 0, 1) ** 1.8 * (0.75 + 0.5 * n) * 0.34
    tint = np.array((150, 185, 240))
    return _img(g[..., None] * tint[None, None])


def tex_pit_steel(size=64):
    """The towers' and trusses' steel: dark blue-grey paint, worn."""
    n = _noise(size, 16, 651, 3)
    a = np.array((70, 78, 94), float)[None, None] * (0.8 + 0.35 * n[..., None])
    return _img(a), None


def tex_stair_tread(size=128):
    """A stair tread (v 0 at its front edge): a yellow-painted nosing with a black grip strip, then pale diamond
    plate, the back in the shadow of the next riser."""
    from tools.shipkit import _grime
    yy, xx = np.mgrid[0:size, 0:size]
    n = _noise(size, 20, 661, 3)
    plate = np.array((118, 118, 112), float)[None, None] * (0.85 + 0.25 * n[..., None])
    dia = ((xx + yy) % 16 < 3) | ((xx - yy) % 16 < 3)
    plate[dia] *= 1.3
    a = plate
    nose = yy < size * 0.45
    a[nose] = np.array((214, 168, 40)) * (0.82 + 0.28 * n[nose][:, None])
    grip = (yy > size * 0.2) & (yy < size * 0.27)
    a[grip] = (34, 32, 28)
    a[yy < 3] *= 1.3
    a[yy > size * 0.9] *= 0.55
    return _img(_grime(a, 663, 0.25)), None


def tex_stair_riser(size=64):
    """A riser: dark steel, darker toward the tread below."""
    v = np.linspace(0, 1, size)[:, None, None]
    n = _noise(size, 12, 671, 2)[..., None]
    a = np.array((58, 58, 56), float)[None, None] * (0.75 + 0.3 * n) * (1.1 - 0.5 * v)
    return _img(a), None


def tex_stair_stringer(size=128):
    """A stair's side: yellow-painted channel steel, bolted, grimed."""
    from tools.shipkit import _grime
    n = _noise(size, 24, 681, 3)
    a = np.array((178, 138, 34), float)[None, None] * (0.8 + 0.3 * n[..., None])
    for x in range(10, size, 32):
        a[8:12, x:x + 4] = (90, 80, 60)
    a[:4] *= 1.25
    return _img(_grime(a, 683, 0.4)), None


def textures():
    """name -> (diffuse, emissive or None)."""
    return {'pit_floor': tex_pit_floor(), 'pit_skirt': tex_pit_skirt(), 'pit_steel': tex_pit_steel(),
            'stair_tread': tex_stair_tread(), 'stair_riser': tex_stair_riser(), 'stair_stringer': tex_stair_stringer()}


# Added (blend 2) textures: name -> function, alongside tools/deckart.py MUL_DECALS.
ADDED = {
    'pit_haze': tex_pit_haze,
    'pit_glow_w': lambda: tex_pit_glow((190, 215, 255)),
    'pit_glow_r': lambda: tex_pit_glow((255, 64, 40)),
    'pit_glow_p': lambda: tex_pit_glow((255, 96, 196)),
    'pit_pool': tex_pit_pool,
}


# ------------------------------------------------------------------ meshes
def _beam(m, key, p0, p1, w):
    """A square steel member w across from p0 to p1, its four long faces."""
    p0, p1 = np.asarray(p0, float), np.asarray(p1, float)
    d = p1 - p0
    L = np.linalg.norm(d)
    d = d / L
    a = np.cross(d, (0, 0, 1)) if abs(d[2]) < 0.9 else np.cross(d, (1, 0, 0))
    a = a / np.linalg.norm(a) * w / 2
    b = np.cross(d, a)
    b = b / np.linalg.norm(b) * w / 2
    ring = [a + b, -a + b, -a - b, a - b]
    for i in range(4):
        c0, c1 = ring[i], ring[(i + 1) % 4]
        m.quad(key, p0 + c0, p1 + c0, p1 + c1, p0 + c1, [(0, 0), (L, 0), (L, 0.25), (0, 0.25)])


def _glow(m, tex, x, y, z, r):
    """A lamp's halo, added: one flat quad and two crossed upright ones, so it reads from the camera's angle."""
    from tools.shipkit import UNLIT, ADD
    key = (tex, True, UNLIT, ADD)
    uv = [(0, 1), (1, 1), (1, 0), (0, 0)]
    m.quad(key, (x - r, y - r, z), (x + r, y - r, z), (x + r, y + r, z), (x - r, y + r, z), uv)
    m.quad(key, (x - r, y, z - r), (x + r, y, z - r), (x + r, y, z + r), (x - r, y, z + r), uv)
    c = r * 0.707
    m.quad(key, (x - c, y - c, z - r), (x + c, y + c, z - r), (x + c, y + c, z + r), (x - c, y - c, z + r), uv)


def _tower(m, glow):
    """A lattice tower a unit square from the pit floor to TOWER_H: four legs, a ring every 1.1 units, X bracing
    on every face, a deck plate on top with its lamp."""
    steel = ('pit_steel', False, 0)
    h = 0.42
    legs = [(-h, -h), (h, -h), (h, h), (-h, h)]
    for x, y in legs:
        _beam(m, steel, (x, y, 0.0), (x, y, TOWER_H), 0.1)
    levels = np.linspace(0.0, TOWER_H, 7)
    for z in levels[1:]:
        for i in range(4):
            (x0, y0), (x1, y1) = legs[i], legs[(i + 1) % 4]
            _beam(m, steel, (x0, y0, z), (x1, y1, z), 0.07)
    for z0, z1 in zip(levels[:-1], levels[1:]):
        for i in range(4):
            (x0, y0), (x1, y1) = legs[i], legs[(i + 1) % 4]
            _beam(m, steel, (x0, y0, z0), (x1, y1, z1), 0.05)
            _beam(m, steel, (x1, y1, z0), (x0, y0, z1), 0.05)
    top = TOWER_H
    m.quad(steel, (-0.55, -0.55, top + 0.02), (0.55, -0.55, top + 0.02), (0.55, 0.55, top + 0.02), (-0.55, 0.55, top + 0.02),
           [(0, 0), (1, 0), (1, 1), (0, 1)])
    _glow(m, glow, 0.3, -0.3, top + 0.25, 0.55)


def _girder(m, length=4.0):
    """A Warren truss along x, length units, 0.7 deep, two webs 0.4 apart, its middle at the origin."""
    steel = ('pit_steel', False, 0)
    a, hz = length / 2, 0.35
    for y in (-0.2, 0.2):
        for z in (-hz, hz):
            _beam(m, steel, (-a, y, z), (a, y, z), 0.09)
        k = int(length / 0.7)
        xs = np.linspace(-a, a, k + 1)
        for i in range(k):
            z0, z1 = (-hz, hz) if i % 2 == 0 else (hz, -hz)
            _beam(m, steel, (xs[i], y, z0), (xs[i + 1], y, z1), 0.06)
    for x in np.linspace(-a, a, 5):
        _beam(m, steel, (x, -0.2, hz), (x, 0.2, hz), 0.05)
        _beam(m, steel, (x, -0.2, -hz), (x, 0.2, -hz), 0.05)


def _pipe(m, length=4.0, r=0.3):
    """A fat pipe along x with flanged joints every unit, hung in the drop."""
    def ring(tex, x0, x1, rr, n=12):
        for i in range(n):
            t0, t1 = 2 * math.pi * i / n, 2 * math.pi * (i + 1) / n
            a0 = (rr * math.cos(t0), rr * math.sin(t0)); a1 = (rr * math.cos(t1), rr * math.sin(t1))
            m.quad((tex, False, 0), (x0, a1[0], a1[1]), (x1, a1[0], a1[1]), (x1, a0[0], a0[1]), (x0, a0[0], a0[1]),
                   [(0, (i + 1) / n), (1, (i + 1) / n), (1, i / n), (0, i / n)])
    a = length / 2
    k = -a
    while k < a - 1e-6:
        ring('prop_pipe_grey', k, k + 1.0, r)
        k += 1.0
    for fx in np.arange(-a + 0.5, a, 1.0):
        ring('pit_steel', fx - 0.06, fx + 0.06, r * 1.2)


def skirt_pieces(out):
    """KSkirt (the deck to the north at turn 0, a plane from the pit floor up to its edge), KSkirt1 (the deck off
    the north-east corner), KSkirt3 (the deck on the north and east): one cell, origin at its centre, a rise of 1,
    scaled by the script to the drop. Each takes the fold the stair pieces take (tools/level.py stair_pieces),
    which lies over the terrain's slope whichever diagonal it is split on, and stands a little out from it."""
    from tools.shipkit import ShipModel
    key = ('pit_skirt', False, 0)
    sw, se, ne, nw = (-0.5, -0.5), (0.5, -0.5), (0.5, 0.5), (-0.5, 0.5)
    out_ = 0.03
    shapes = {
        'KSkirt': ({ne, nw}, ((sw, se, ne), (sw, ne, nw)), (0.0, -out_)),
        'KSkirt1': ({ne}, ((sw, se, ne), (sw, ne, nw)), (-out_, -out_)),
        'KSkirt3': ({se, ne, nw}, ((sw, se, nw), (se, ne, nw)), (-out_, -out_)),
    }
    for name, (up, tris, (dx, dy)) in shapes.items():
        m = out[name] = ShipModel(name, (0, 0, 0))
        for tri in tris:
            pts = [(x + dx, y + dy, 1.0 if (x, y) in up else 0.0) for x, y in tri]
            if all(p[2] == 1.0 for p in pts):
                m.poly(('decal_hazard', False, 0), [(x, y, 1.0) for x, y, _ in pts], [((x + 0.5), 1 - (y + 0.5)) for x, y, _ in pts])
                continue
            # u along the edge the triangle hangs from, v down from the deck.
            m.poly(key, pts, [(((x + y) if name != 'KSkirt' else x) + 0.5, 1.0 - z) for x, y, z in pts])


def pieces(out):
    """Every pit piece, into out (tools/level.py kit_pieces)."""
    from tools.shipkit import ShipModel, NO_SHADOW_CAST, UNLIT, ADD
    for size in (4, 2, 1):
        for ox in range(0, 4, size):
            for oy in range(0, 4, size):
                name = 'KO%d_%d%d' % (size, ox, oy)
                m = out[name] = ShipModel(name, (0, 0, 0))

                def uv(dx, dy):
                    return [((ox + dx) / 4, 1 - (oy + dy) / 4), ((ox + size + dx) / 4, 1 - (oy + dy) / 4),
                            ((ox + size + dx) / 4, 1 - (oy + size + dy) / 4), ((ox + dx) / 4, 1 - (oy + size + dy) / 4)]
                m.quad(('pit_floor', False, NO_SHADOW_CAST), (0, 0, 0.02), (size, 0, 0.02), (size, size, 0.02), (0, size, 0.02), uv(0, 0))
                # Each layer's cloud shifted against the others (whole cells, so tiles still join), so they never line up.
                for k, z in enumerate(HAZE):
                    m.quad(('pit_haze', False, UNLIT, ADD), (0, 0, z), (size, 0, z), (size, size, z), (0, size, z),
                           uv((k * 7) % 4 * 1.0 + k * 0.37, (k * 5) % 4 * 1.0 + k * 0.61))
    skirt_pieces(out)
    for name, glow in (('KPitTowerR', 'pit_glow_r'), ('KPitTowerW', 'pit_glow_w'), ('KPitTowerP', 'pit_glow_p')):
        m = out[name] = ShipModel(name, (0, 0, 0)); _tower(m, glow)
    m = out['KPitGirder'] = ShipModel('KPitGirder', (0, 0, 0)); _girder(m)
    for p in m.parts.values():
        p['pos'] = [np.array(v) + (0, 0, GIRDER_Z) for v in p['pos']]
    m = out['KPitPipe'] = ShipModel('KPitPipe', (0, 0, 0)); _pipe(m)
    for p in m.parts.values():
        p['pos'] = [np.array(v) + (0, 0, PIPE_Z) for v in p['pos']]
    for name, tex, z, r in (('KPitGlowP', 'pit_glow_p', 2.6, 0.45), ('KPitGlowW', 'pit_glow_w', 1.4, 0.7), ('KPitGlowR', 'pit_glow_r', 3.8, 0.4)):
        m = out[name] = ShipModel(name, (0, 0, 0)); _glow(m, tex, 0, 0, z, r)
    # Lit fog round a lamp far down, lying flat over the pit floor.
    m = out['KPitPool'] = ShipModel('KPitPool', (0, 0, 0))
    m.quad(('pit_pool', False, UNLIT, ADD), (-2.4, -2.4, 0.6), (2.4, -2.4, 0.6), (2.4, 2.4, 0.6), (-2.4, 2.4, 0.6), [(0, 1), (1, 1), (1, 0), (0, 0)])
    # The catwalk's outrigger: authored on a deck edge facing south (the drop toward -y), origin on the edge at the
    # deck's height. Its leg runs on below the pit floor, where the terrain hides it, whatever the drop's depth.
    m = out['KPitBrace'] = ShipModel('KPitBrace', (0, 0, 0))
    steel = ('pit_steel', False, 0)
    _beam(m, steel, (0, 0.05, -0.62), (0, -1.55, -0.62), 0.22)
    _beam(m, steel, (0, -0.02, -2.1), (0, -1.42, -0.72), 0.1)
    _beam(m, steel, (0, -1.5, -0.6), (0, -1.5, -10.5), 0.16)
    _beam(m, steel, (-0.5, -1.5, -0.7), (0.5, -1.5, -0.7), 0.08)
    # A floodlight's shaft from the deck's edge down into the drop (deckart's light shaft, added).
    m = out['KPitShaft'] = ShipModel('KPitShaft', (0, 0, 0))
    top, foot, z = 0.3, 2.4, 6.0
    for k in range(8):
        t0, t1 = 2 * math.pi * k / 8, 2 * math.pi * (k + 1) / 8
        m.quad(('shaft_cold', True, UNLIT, ADD), (foot * math.cos(t0), foot * math.sin(t0), 0.05), (foot * math.cos(t1), foot * math.sin(t1), 0.05),
               (top * math.cos(t1), top * math.sin(t1), z), (top * math.cos(t0), top * math.sin(t0), z), [(0, 1), (1, 1), (1, 0), (0, 0)])
    # A building's outer wall down to the pit floor: the concrete bay, its texture repeating down the drop.
    from tools.level import WALL_H, LIP
    tall = WALL_H + 9.5
    for part, (x0, x1) in {'F': (-1, 1), 'E': (-1, 0), 'O': (0, 1)}.items():
        name = 'KW9T' + part
        m = out[name] = ShipModel(name, (0, 0, 0))
        u0, u1 = (x0 + 1) / 2.0, (x1 + 1) / 2.0
        m.quad(('wall_concrete', False, 0), (x0, 0, WALL_H - tall), (x1, 0, WALL_H - tall), (x1, 0, WALL_H), (x0, 0, WALL_H),
               [(u0, tall / WALL_H), (u1, tall / WALL_H), (u1, 0.0), (u0, 0.0)])
        m.quad(('wall_trim', False, NO_SHADOW_CAST), (x0, 0, WALL_H + 0.012), (x1, 0, WALL_H + 0.012), (x1, LIP, WALL_H + 0.012), (x0, LIP, WALL_H + 0.012),
               [(u0, 0.0), (u1, 0.0), (u1, 1.0), (u0, 1.0)])
    rail_pieces(out)


def rail_pieces(out):
    """KSRailW / KSRailE: the handrail up a flight's west or east side (a flight rising north at turn 0, rise 1);
    KSRailWh / KSRailEh the same for a rise of 0.5. Posts at the foot, the middle and the head, the rail and a
    knee rail parallel to the treads, a kick plate along the stringer."""
    from tools.shipkit import ShipModel
    from tools.elevator import _box
    rail = ('rail', False, 0)
    for nominal, suffix in ((1.0, ''), (0.5, 'h')):
        for side, sx in (('W', -0.44), ('E', 0.44)):
            name = 'KSRail' + side + suffix
            m = out[name] = ShipModel(name, (0, 0, 0))
            hgt = 0.95
            for y, zf in ((-0.46, 0.0), (0.0, nominal * 0.5), (0.46, nominal)):
                _box(m, rail, sx - 0.03, y - 0.03, zf, sx + 0.03, y + 0.03, zf + hgt)
            for zr in (hgt, hgt * 0.55):
                _beam(m, rail, (sx, -0.5, zr), (sx, 0.5, nominal + zr), 0.05)
            _beam(m, ('stair_stringer', False, 0), (sx, -0.5, 0.06), (sx, 0.5, nominal + 0.06), 0.06)


# ------------------------------------------------------------------ where things stand
def _dist(open_, H, W):
    """Chebyshev distance of each open cell from the nearest cell that is not open (deck or hull)."""
    from collections import deque
    d = np.full((H, W), 99)
    q = deque()
    for y in range(H):
        for x in range(W):
            if not open_[y][x]:
                d[y, x] = 0
                q.append((y, x))
    while q:
        y, x = q.popleft()
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                yy, xx = y + dy, x + dx
                if 0 <= yy < H and 0 <= xx < W and d[yy, xx] > d[y, x] + 1:
                    d[yy, xx] = d[y, x] + 1
                    q.append((yy, xx))
    return d


def _hash(x, y, k=0):
    return ((x * 73856093) ^ (y * 19349663) ^ (k * 83492791)) & 0xffff


def spots(rows):
    """(piece, x, y, facing) for the pit's dressing: towers on a jittered grid clear of the deck's edge, trusses
    from some of them, fat pipes along the edges two cells out, lamps and sparks in the haze, floodlight shafts."""
    H, W = len(rows), len(rows[0])
    open_ = [[c == 'o' for c in row] for row in rows]
    if not any(any(r) for r in open_):
        return []
    d = _dist(open_, H, W)
    deck = [[c.isdigit() for c in row] for row in rows]
    out = []
    taken = set()
    G = 5
    for gy in range(0, H, G):
        for gx in range(0, W, G):
            h = _hash(gx, gy, 1)
            x, y = gx + h % G, gy + (h >> 4) % G
            if not (0 <= x < W and 0 <= y < H) or d[y, x] < 2 or h % 7 == 0:
                continue
            piece = ('KPitTowerR', 'KPitTowerW', 'KPitTowerP', 'KPitTowerW')[(h >> 8) % 4]
            out.append((piece, x + 0.5, y + 0.5, float((h >> 3) % 4 * 90)))
            taken.add((x, y))
            # A truss off the tower, along x or y, where it stays over the drop.
            if (h >> 10) % 3 == 0:
                for ang, (ux, uy) in ((0.0, (1, 0)), (90.0, (0, 1)), (180.0, (-1, 0)), (270.0, (0, -1)))[(h >> 12) % 4:] + \
                        ((0.0, (1, 0)), (90.0, (0, 1)), (180.0, (-1, 0)), (270.0, (0, -1)))[:(h >> 12) % 4]:
                    ends = [(x + ux * k, y + uy * k) for k in (1, 2, 3, 4)]
                    if all(0 <= ex < W and 0 <= ey < H and d[ey, ex] >= 1 for ex, ey in ends):
                        out.append(('KPitGirder', x + 0.5 + ux * 2.0, y + 0.5 + uy * 2.0, ang))
                        break
    # Fat pipes two cells out from straight deck edges, four cells at a time, every other run.
    for horiz in (True, False):
        n_a, n_b = (H, W) if horiz else (W, H)
        for a in range(n_a):
            run = []
            for b in range(n_b + 1):
                x, y = (b, a) if horiz else (a, b)
                ok = b < n_b and d[y, x] == 2 and any(
                    0 <= y + s * 2 < H and 0 <= x < W and deck[y + s * 2][x] if horiz else 0 <= x + s * 2 < W and deck[y][x + s * 2]
                    for s in (-1, 1))
                if ok:
                    run.append(b)
                    continue
                k = 0
                while k + 4 <= len(run):
                    mid = run[k] + 2.0
                    if _hash(a, run[k], 3) % 2 == 0:
                        out.append(('KPitPipe',) + ((mid, a + 0.5, 0.0) if horiz else (a + 0.5, mid, 90.0)))
                    k += 5
                run = []
    # Outriggers under the deck's edge, every third cell along it: a beam out over the drop, a leg down from its end.
    for y in range(H):
        for x in range(W):
            if not deck[y][x]:
                continue
            for s, (dx, dy) in enumerate(((0, -1), (1, 0), (0, 1), (-1, 0))):
                nx, ny = x + dx, y + dy
                along = x if dy else y
                if 0 <= nx < W and 0 <= ny < H and open_[ny][nx] and along % 3 == 1:
                    out.append(('KPitBrace', x + 0.5 + dx * 0.47, y + 0.5 + dy * 0.47, s * 90.0))
    # Lamps and sparks hanging in the haze, and a floodlight's shaft off the deck here and there.
    for y in range(H):
        for x in range(W):
            if not open_[y][x] or (x, y) in taken:
                continue
            h = _hash(x, y, 5)
            if d[y, x] >= 2 and h % 23 == 0:
                out.append((('KPitGlowP', 'KPitGlowW', 'KPitGlowR', 'KPitGlowP')[(h >> 5) % 4], x + 0.5, y + 0.5, 0.0))
            elif d[y, x] == 2 and h % 41 == 0:
                out.append(('KPitShaft', x + 0.5, y + 0.5, 0.0))
    # Pools of lit fog under the lamps down there.
    for x, y, kind, flick in lamps(rows, out):
        out.append(('KPitPool', x, y, 0.0))
    return out


def lamps(rows, dressing=None):
    """Real lights down in the pit, to pick the towers and the floor out of the haze: (x, y, kind, flicker),
    cold, pink and a red alarm, about one per tower in three, no more than six."""
    out = []
    for piece, x, y, rot in (dressing if dressing is not None else spots(rows)):
        if piece.startswith('KPitTower') and _hash(int(x), int(y), 9) % 3 == 0 and len(out) < 6:
            out.append((x, y, {'KPitTowerR': 'red', 'KPitTowerP': 'purple'}.get(piece, 'cold'), 3 if piece == 'KPitTowerR' else 0))
    return out
