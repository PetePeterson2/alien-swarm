"""The freight elevator's art: the shaft's wall segments, gates, bridges, the platform, the drop round it, and the
security door; textures drawn here, meshes written with tools/shipkit.py's M3 writer.

The shaft is the trick of the mission, as it is in Alien Swarm (src/Mission.galaxy): the platform is fixed floor
and the walls move. AS's walls (FreightElevatorWalls, a func_tracktrain) run 2655 units at 25 a second up and SOUTH
past the platform, along an incline (dz 1992 against dy -1752): the tube runs down to the north under the deck, so
from the top-down camera the walls loom toward it rather than scroll. Here the walls are SEG_N segments of SEG along
that incline, model actors the script slides along TRAVEL; whatever is under the deck is hidden by the terrain, so a
segment comes up out of the floor at the north edge of the drop, climbs past the camera and drops back to the bottom
of the train out of sight. A segment carries what AS's walls carry where the camera sees them (measured from the
walls' brushes and models/props/elevator_shaft/shaft01a/b in asi-jac1-landingbay_02, read for layout only): a fat
flanged pipe along the top of each wall with yellow conduits under it (and hanging cables on the east), X-braced
trusses between, and a caged lamp with an orange-red glow (200,47,2) on each wall, one a segment.

Segment meshes are authored in the shaft's own frame: origin on the walls' top edge at the shaft's middle, u along
TRAVEL, t from the top edge into the tube (INTO), x across. Two of the slots are special: the one standing at the
platform when the ride begins has the entrance doorway in its west wall, and the one that arrives there after the
ride's five segments has the exit doorway in its east wall.
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from tools.shipkit import ShipModel, _noise, _grime, _hazard, _img, NO_SHADOW_CAST, UNLIT, ADD

TRAVEL = (-0.6604, 0.7509)     # (dy, dz) of the walls' travel, per cell: up and south
INTO = (-0.7509, -0.6604)      # (dy, dz) from the walls' top edge into the tube: down and south
RIDE = 33.19                   # 2655 units in 80-unit cells
SEG = RIDE / 5                 # a wall segment: the ride is five, so the exit doorway lands where the entrance stood
SEG_N = 7                      # the train: from deep under the deck (out of sight in the haze) to past the camera
TUBE = 8.4                     # the walls' depth from the top pipe to the tube's floor (672 units)
DOOR_U = 2.6                   # where the doorway segment starts along the travel when it stands at the platform
DOOR_H = 2.3                   # the doorways' height (AS's heavy doors, 184 units)
LAMP_U, LAMP_T = 3.08, 4.25    # each wall's caged lamp in its segment (AS: every 6.43 along, 4.1-4.4 deep)
PIPE_T, PIPE_R, PIPE_IN = 0.55, 0.5, 0.62   # the top pipe: depth, radius, how far in from its wall


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


def train(in_slot):
    """(where along the travel slot 0 starts when the ride begins, the slot that brings the exit to the platform):
    slot in_slot stands at the platform with the entrance, and the ride is five segments."""
    return DOOR_U - in_slot * SEG, (in_slot - 5) % SEG_N


def shaft_point(x, u, t):
    """A point of the shaft's frame in a segment's local coordinates (x across, y north, z up)."""
    return (x, u * TRAVEL[0] + t * INTO[0], u * TRAVEL[1] + t * INTO[1])


# ------------------------------------------------------------- textures
def tex_shaftwall(w=1024, h=1024):
    """One segment of a shaft wall, SEG along (u, across) by TUBE deep (t, down): AS's concrete between two truss
    chords, one X of bracing a segment (the segments' X's meet in its diamond lattice), the shadow under the top
    pipe, the lower pipe run near the tube's floor, panel seams and wet streaks."""
    su, st = w / SEG, h / TUBE
    n = _noise(0, 70, 211, 4, (h, w)); f = _noise(0, 9, 213, 2, (h, w))
    a = np.array((104, 100, 92), float)[None, None] * (0.72 + 0.34 * n[..., None] + 0.08 * f[..., None])
    for x in (0, w // 2):
        a[:, max(0, x - 3):x + 3] *= 0.45
    a[int(4.2 * st) - 2:int(4.2 * st) + 2] *= 0.5
    # Under the top pipe: shadowed, and the pipe's brackets.
    rows = np.arange(h)[:, None] / st
    a *= (0.55 + 0.45 * np.clip((rows - 0.2) / 1.1, 0, 1))[..., None]
    for x in range(int(0.4 * su), w, int(SEG / 3 * su)):
        a[int(0.2 * st):int(1.15 * st), x:x + 14] = (52, 52, 54)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    steel = np.zeros((h, w), np.float32)
    # The bracing: corner to corner of the band between the chords.
    t0, t1 = 1.65 * st, 7.0 * st
    for sgn in (1, -1):
        ty = t0 + (t1 - t0) * (xx / w) if sgn > 0 else t1 - (t1 - t0) * (xx / w)
        steel = np.maximum(steel, np.clip(1 - np.abs(yy - ty) / 11, 0, 1))
    for tc in (t0, t1):
        steel = np.maximum(steel, (np.abs(yy - tc) < 12).astype(np.float32))
    edge = np.clip(steel - np.roll(steel, 3, axis=0), 0, 1)
    beam = np.array((84, 86, 90))[None, None] * (0.8 + 0.3 * n[..., None])
    a = a * (1 - steel[..., None]) + beam * steel[..., None]
    a *= (1 - 0.45 * edge)[..., None]
    for tc in (t0, t1):
        for x in range(10, w, 26):
            a[int(tc) - 5:int(tc) - 1, x:x + 4] = (150, 146, 136)
    # Yellow conduits clipped along under the top pipe (their own geometry runs in front; this is their shadow line).
    a[int(1.33 * st):int(1.38 * st)] *= 0.6
    # The lower pipe run by the tube's floor, with red flanges.
    p0, p1 = int(7.35 * st), int(8.15 * st)
    prow = np.linspace(-1, 1, p1 - p0)[:, None]
    a[p0:p1] = np.array((66, 60, 56))[None, None] * (0.45 + 0.65 * np.sqrt(np.clip(1 - prow ** 2, 0, 1)))[..., None]
    for x in range(int(0.5 * su), w, int(SEG / 1 * su)):
        a[p0 - 8:p1 + 8, x:x + 18] = (150, 36, 26)
    _hazard(a, int(8.2 * st), h, 211)
    streak = _noise(0, 4, 219, 1, (1, w)).repeat(h, 0)
    a *= (1 - 0.25 * np.clip(streak - 0.4, 0, 1) * np.linspace(0.3, 1, h)[:, None])[..., None]
    return _img(_grime(a, 223, 0.35)), None


def tex_pipe(w=256, h=128):
    """The shaft's fat pipes: dark gunmetal gone brown with rust, a weld seam along the top (u along, v round)."""
    n = _noise(0, 40, 231, 4, (h, w)); r = _noise(0, 12, 233, 3, (h, w))
    a = np.array((80, 72, 66), float)[None, None] * (0.75 + 0.3 * n[..., None])
    rust = np.clip(r - 0.55, 0, 1)[..., None] * 2.2
    a = a * (1 - rust) + np.array((120, 62, 34))[None, None] * rust
    a[h // 4 - 2:h // 4 + 2] *= 0.5
    return _img(_grime(a, 235, 0.3)), None


def tex_solid(rgb, seed, size=64, grime=0.25):
    n = _noise(0, 20, seed, 3, (size, size))
    a = np.array(rgb, float)[None, None] * (0.8 + 0.3 * n[..., None])
    return _img(_grime(a, seed + 1, grime)), None


def tex_glow(rgb, size=128, core=0.25):
    """A lamp's glow, added over the scene (AS's light_glow03 sprites): a hot core and a soft halo."""
    yy, xx = np.mgrid[0:size, 0:size] / (size - 1) * 2 - 1
    r = np.hypot(xx, yy)
    g = np.clip(1 - r, 0, 1) ** 2.2 * 0.75 + np.clip(1 - r / core, 0, 1) ** 1.5 * 0.9
    c = np.array(rgb, float)
    return _img(np.clip(g[..., None] * c[None, None] + np.clip(1 - r / core, 0, 1)[..., None] ** 2 * 120, 0, 255)), None


def tex_screen(rgb, w=128, h=96):
    """The lift console's screen (panel02's skins 1 and 2): red while the squad is not all aboard, green when it is."""
    a = np.zeros((h, w, 3)) + np.array(rgb, float) * 0.25
    yy, xx = np.mgrid[0:h, 0:w]
    a[(yy % 6) < 2] *= 0.6
    a[10:h - 10, 12:w - 12] += np.array(rgb, float) * 0.55
    img = _img(a)
    _stencil(img, 'LIFT', (w // 2, h // 2), 34, (255, 255, 255))
    return img, img


def tex_ceil(w=256, h=256):
    n = _noise(0, 40, 241, 3, (h, w))
    a = np.array((46, 46, 48), float)[None, None] * (0.75 + 0.35 * n[..., None])
    for k in range(0, w, 64):
        a[:, k:k + 3] *= 0.5; a[k:k + 3] *= 0.5
    return _img(a), None


def tex_deck(w=1024, h=896):
    """AS's lift platform (asi-jac1-landingbay_02's floor brushes there): galvanised grating plates parted by
    worn yellow trim into a south band, a middle band whose side plates carry hazard stripes, and a north band
    of three plates, the middle one running into the console's notch. 8 by 7 cells, row 0 at the north (y 116)."""
    yy, xx = np.mgrid[0:h, 0:w]
    n = _noise(0, 80, 41, 4, (h, w))
    a = np.array((92, 94, 90), float)[None, None] * (0.72 + 0.32 * n[..., None])
    diamond = (((xx + yy) // 6) % 8 == 0) | (((xx - yy) // 6) % 8 == 0)
    a[diamond] *= 1.22
    holes = ((xx % 12) < 5) & ((yy % 12) < 5)
    a[holes] *= 0.72
    P = 128
    px = lambda x: int(round((x - 42) * P))
    py = lambda y: int(round((116 - y) * P))
    yel = np.array((176, 140, 40), float)
    def hline(y, x0, x1, wdt=12):
        a[py(y) - wdt // 2:py(y) + wdt // 2, px(x0):px(x1)] = yel * (0.65 + 0.4 * n[py(y) - wdt // 2:py(y) + wdt // 2, px(x0):px(x1), None])
    def vline(x, y0, y1, wdt=12):
        a[py(y1):py(y0), px(x) - wdt // 2:px(x) + wdt // 2] = yel * (0.65 + 0.4 * n[py(y1):py(y0), px(x) - wdt // 2:px(x) + wdt // 2, None])
    # The middle band's side plates: hazard stripes.
    for x0, x1 in ((42, 43.8), (48.2, 50)):
        sub = a[py(112.7):py(111.3), px(x0):px(x1)]
        sy, sx = np.mgrid[0:sub.shape[0], 0:sub.shape[1]]
        stripe = ((sx + sy) // 26) % 2 == 0
        sub[:] = np.where(stripe[..., None], yel, np.array((30, 30, 28), float)) * (0.6 + 0.45 * n[py(112.7):py(111.3), px(x0):px(x1), None])
    for y in (109.06, 111.3, 112.7, 114.94):
        hline(y, 42, 50)
    vline(42.06, 109, 115); vline(49.94, 109, 115)
    vline(43.8, 111.3, 112.7); vline(48.2, 111.3, 112.7)
    vline(45.06, 112.7, 116); vline(46.94, 112.7, 116)
    hline(115.94, 45, 47)
    img = _img(_grime(a, 43, 0.35))
    a = np.asarray(img).astype(float) * (1 - 0.35 * np.clip(_noise(0, 30, 47, 3, (h, w)) - 0.5, 0, 1))[..., None]
    return _img(a), None


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
    # Distant stars beyond the glass.
    r = np.random.default_rng(seed)
    for _ in range(70):
        sy, sx = int(r.integers(2, y1 - y0 - 2)), int(r.integers(2, w - 42))
        b = r.uniform(0.3, 1.0) * np.array((200, 210, 230))
        glass[sy:sy + 3, sx:sx + 3] += b; emis[y0 + sy:y0 + sy + 3, 20 + sx:20 + sx + 3] += b * 0.8
    a[y0:y1, 20:w - 20] = glass
    return _img(a), _img(emis)


def tex_asdoor(w=256, h=320):
    """Alien Swarm's heavy door (models/props/doors/heavy_doors): dark plating in two ribbed halves, yellow and
    black hazard bands top and bottom, a status lamp strip down the middle seam."""
    n = _noise(0, 40, 71, 4, (h, w))
    a = np.array((84, 88, 92), float)[None, None] * (0.8 + 0.3 * n[..., None])
    for x in range(16, w, 32):
        a[:, x:x + 4] *= 0.62
    for y in range(int(h * 0.2), int(h * 0.8), 40):
        a[y:y + 3] *= 0.5
    a[:, w // 2 - 3:w // 2 + 3] = (24, 24, 26)
    _hazard(a, 0, int(h * 0.12), 5)
    _hazard(a, int(h * 0.88), h, 6)
    emis = np.zeros((h, w, 3))
    for y in range(int(h * 0.3), int(h * 0.7), 24):
        a[y:y + 10, w // 2 - 10:w // 2 + 10] = (60, 220, 120); emis[y:y + 10, w // 2 - 10:w // 2 + 10] = (40, 180, 90)
    return _img(_grime(a, 73, 0.3)), _img(emis)


def tex_seam(w=64, h=256):
    """A weld seam: a jagged glowing orange bead down the door's middle."""
    rng = np.random.default_rng(9)
    a = np.zeros((h, w, 3))
    xs = (w / 2 + np.cumsum(rng.normal(0, 2.0, h))).clip(10, w - 10)
    for y in range(h):
        x0 = int(xs[y]) - 5
        a[y, x0:x0 + 10] = (255, 140, 40)
        a[y, x0 + 3:x0 + 7] = (255, 230, 160)
    return _img(a * 0.4), _img(a)


def tex_open(size=512):
    """Under the night sky (Landing Bay's dock): the drop off a catwalk's edge, as AS's opening shows it.
    Deep blue haze in its exterior fog colour (39,53,86), steel lattice towers and girders far below in
    darker and paler blue, and a few lamps down there. Emissive only, tileable over 4x4 cells."""
    n = _noise(size, 48, 501, 4); f = _noise(size, 8, 507, 2)
    # Mostly black, as AS's drop is: the haze only thickens here and there, and is faint where it does.
    haze = np.array((39, 53, 86), float)[None, None] * (0.08 + 0.34 * np.clip(n - 0.35, 0, 1)[..., None] + 0.05 * f[..., None])
    yy, xx = np.mgrid[0:size, 0:size].astype(np.float32)
    # Girders far below, nothing lined up with the deck's cells: two long diagonal beams across the tile
    # and one lattice tower (twin legs with zigzag bracing) running its height.
    lat = np.zeros((size, size), np.float32)
    for c, wdt in ((90, 9), (330, 6)):
        u = (xx - yy - c) % size
        lat = np.maximum(lat, np.clip(1 - np.minimum(u, size - u) / 1.414 / wdt, 0, 1))
    tx = 371
    for leg in (tx, tx + 46):
        lat = np.maximum(lat, np.clip(1 - np.abs(xx - leg) / 3.5, 0, 1))
    zig = tx + 23 + 23 * np.abs(((yy / 46) % 2) - 1) * 2 - 23
    lat = np.maximum(lat, np.clip(1 - np.abs(xx - zig) / 2.5, 0, 1) * ((xx > tx) & (xx < tx + 46)))
    blur = np.asarray(Image.fromarray((lat * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.5))).astype(np.float32) / 255
    # Dark steel against the haze, its upper edge catching a little of the light from above.
    rim = np.clip(blur - np.roll(blur, 3, axis=0), 0, 1)
    a = haze * (1 - 0.75 * blur[..., None]) + np.array((90, 115, 160))[None, None] * 0.18 * rim[..., None]
    # Lamps far below: soft points, mostly cold white, a few red beacons.
    rng = np.random.default_rng(509)
    for k in range(4):
        cx, cy = rng.integers(0, size, 2); r = np.hypot(((xx - cx + size / 2) % size) - size / 2, ((yy - cy + size / 2) % size) - size / 2)
        col = np.array((255, 70, 50)) if k % 3 == 0 else np.array((170, 200, 255))
        a += col[None, None] * (np.clip(1 - r / 12, 0, 1) ** 2 * 0.35 + np.clip(1 - r / 2.5, 0, 1) * 0.8)[..., None]
    return _img(np.zeros((8, 8, 3))), _img(np.clip(a, 0, 255))




def tex_void(w=256, h=256):
    """The drop between platform and walls. AS's shaft is not black but full of dark brown haze (its
    fog_elevator is 43,37,32 at 0.9): an unlit floor of nothing glowing in the fog colour, brightest to the north
    where the tube runs on down into the fog (row 0 is the drop's north edge), drifting as fog does."""
    n = _noise(0, 60, 91, 3, (h, w))
    grad = 0.18 + 0.32 * np.linspace(1, 0, h)[:, None] ** 1.8
    haze = np.array((43, 37, 32), float)[None, None] * ((0.6 + 0.5 * n) * grad)[..., None]
    return _img(np.zeros((h, w, 3))), _img(haze)


def tex_veil(size=256):
    """A veil of the shaft's haze, added over what lies below it: faint, uneven."""
    n = _noise(size, 64, 97, 3)
    return _img(np.array((43, 37, 32), float)[None, None] * (0.15 + 0.22 * n)[..., None]), None


def tex_frame(w=64, h=256):
    """The doorways' frames: yellow and black hazard bands (AS's heavy door surrounds)."""
    a = np.zeros((h, w, 3)) + 60
    _hazard(a, 0, h, 17)
    a[:, :4] *= 0.4; a[:, -4:] *= 0.4
    return _img(_grime(a, 19, 0.3)), None


def tex_rail(w=64, h=64):
    """The platform's railing: AS's orange-red paint, chipped."""
    n = _noise(0, 10, 251, 3, (h, w))
    a = np.array((176, 64, 26), float)[None, None] * (0.75 + 0.35 * n[..., None])
    a[np.clip(n - 0.62, 0, 1) > 0.05] = (90, 84, 78)
    return _img(a), None


def tex_cage(w=64, h=64):
    """A caged lamp: a hot orange bulb behind bars, the bracket round it."""
    yy, xx = np.mgrid[0:h, 0:w] / (h - 1) * 2 - 1
    r = np.hypot(xx, yy)
    a = np.zeros((h, w, 3)) + 40
    bulb = np.clip(1 - r / 0.7, 0, 1)
    a += bulb[..., None] * np.array((255, 150, 60))
    bars = (np.abs(((xx + 1) * 3.5) % 1 - 0.5) > 0.38) & (r < 0.85)
    a[bars] = (30, 28, 26)
    e = a * (r < 0.75)[..., None]
    e[bars] = 0
    return _img(a), _img(e * 0.9)


def textures():
    t = {'asdoor': tex_asdoor(), 'doorseam': tex_seam(), 'gate': tex_gate(),
         'lift_deck': tex_deck(), 'bridge': tex_bridge(), 'door': tex_door(), 'wall_window': tex_window(),
         'void': tex_void(), 'voidtop': (Image.new('RGB', (16, 16), (0, 0, 0)), None), 'voidveil': tex_veil(), 'rail': (Image.new('RGB', (16, 16), (150, 118, 34)), None),
         'shaftwall': tex_shaftwall(), 'shaftpipe': tex_pipe(), 'liftceil': tex_ceil(), 'liftframe': tex_frame(),
         'flange': tex_solid((150, 40, 28), 261), 'conduit': tex_solid((190, 150, 40), 263, 32, 0.15),
         'cable': tex_solid((26, 26, 26), 265, 32, 0.1), 'liftrail': tex_rail(), 'liftconsole': tex_solid((58, 62, 66), 267),
         'lampcage': tex_cage(), 'lampglow': tex_glow((200, 47, 2)), 'glowamber': tex_glow((249, 192, 0), core=0.3), 'glowred': tex_glow((249, 0, 0), core=0.3),
         'screen_r': tex_screen((230, 40, 30)), 'screen_g': tex_screen((60, 220, 70))}
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


def _face(m, key, pts, uv, toward):
    """A polygon, wound so its face looks along ``toward``."""
    p = np.asarray(pts, float)
    if np.dot(np.cross(p[1] - p[0], p[-1] - p[0]), toward) < 0:
        pts, uv = list(pts)[::-1], list(uv)[::-1]
    m.poly(key, pts, uv)


def _clip(poly, axis, sign, c):
    """Sutherland-Hodgman: the part of a convex (y, z) polygon where sign * (p[axis] - c) >= 0."""
    out = []
    for i, p in enumerate(poly):
        q = poly[i - 1]
        dp, dq = sign * (p[axis] - c), sign * (q[axis] - c)
        if (dp >= 0) != (dq >= 0):
            k = dq / (dq - dp)
            out.append((q[0] + (p[0] - q[0]) * k, q[1] + (p[1] - q[1]) * k))
        if dp >= 0:
            out.append(p)
    return out


def doorway():
    """The doorway's hole in a wall segment's own (y, z): AS's doorways are cells 110-114 by 2.3 high, and the
    doorway segment starts DOOR_U along the travel when it stands at the platform."""
    y0, z0 = shaft_point(0, DOOR_U, 0)[1:]
    return 110 - 119.35 - y0, 114 - 119.35 - y0, DOOR_H - z0, -z0


def _wall(m, x, cut):
    """One wall of a segment at x (local), the doorway cut out of it if ``cut``."""
    corners = [shaft_point(x, u, t)[1:] for u, t in ((0, 0), (SEG, 0), (SEG, TUBE), (0, TUBE))]
    pieces = [corners]
    if cut:
        dy0, dy1, dz1, _ = doorway()
        mid = _clip(_clip(corners, 0, 1, dy0), 0, -1, dy1)
        pieces = [_clip(corners, 0, -1, dy0), _clip(corners, 0, 1, dy1), _clip(mid, 1, 1, dz1)]
    for poly in pieces:
        if len(poly) < 3:
            continue
        pts = [(x, y, z) for y, z in poly]
        uv = [((TRAVEL[0] * y + TRAVEL[1] * z) / SEG, (INTO[0] * y + INTO[1] * z) / TUBE) for y, z in poly]
        _face(m, ('shaftwall', True, 0), pts, uv, (-np.sign(x), 0, 0))


def _tube(m, key, x, t, r, u0, u1, sides=8, caps=False):
    """A pipe of radius r along the travel, its axis at (x, t), from u0 to u1."""
    ring = [2 * np.pi * k / sides for k in range(sides + 1)]
    for k in range(sides):
        a0, a1, am = ring[k], ring[k + 1], (ring[k] + ring[k + 1]) / 2
        p = lambda a, u: shaft_point(x + r * np.cos(a), u, t + r * np.sin(a))
        out = (np.cos(am), np.sin(am) * INTO[0], np.sin(am) * INTO[1])
        _face(m, key, [p(a0, u0), p(a0, u1), p(a1, u1), p(a1, u0)],
              [(0, k / sides), ((u1 - u0) / 2, k / sides), ((u1 - u0) / 2, (k + 1) / sides), (0, (k + 1) / sides)], out)
    if caps:
        for u, s in ((u0, -1), (u1, 1)):
            pts = [shaft_point(x + r * np.cos(a), u, t + r * np.sin(a)) for a in ring[:-1]]
            _face(m, key, pts, [(0.5 + 0.5 * np.cos(a), 0.5 + 0.5 * np.sin(a)) for a in ring[:-1]], (0, s * TRAVEL[0], s * TRAVEL[1]))


def _sbox(m, key, x0, x1, u0, u1, t0, t1):
    """A box in the shaft's frame (x, u, t ranges)."""
    c = np.array(shaft_point((x0 + x1) / 2, (u0 + u1) / 2, (t0 + t1) / 2))
    P = lambda x, u, t: shaft_point(x, u, t)
    faces = [
        [P(x0, u0, t0), P(x0, u1, t0), P(x0, u1, t1), P(x0, u0, t1)], [P(x1, u0, t0), P(x1, u1, t0), P(x1, u1, t1), P(x1, u0, t1)],
        [P(x0, u0, t0), P(x1, u0, t0), P(x1, u0, t1), P(x0, u0, t1)], [P(x0, u1, t0), P(x1, u1, t0), P(x1, u1, t1), P(x0, u1, t1)],
        [P(x0, u0, t0), P(x1, u0, t0), P(x1, u1, t0), P(x0, u1, t0)], [P(x0, u0, t1), P(x1, u0, t1), P(x1, u1, t1), P(x0, u1, t1)]]
    for f in faces:
        _face(m, key, f, [(0, 0), (1, 0), (1, 1), (0, 1)], np.mean(f, 0) - c)


def _glow(m, key, centre, size):
    """A glow sprite facing the camera (pitch 60: normal 0, -0.5, 0.866)."""
    c = np.array(centre, float); X = np.array((size, 0, 0)); V = np.array((0, 0.866, 0.5)) * size
    m.quad(key, tuple(c - X - V), tuple(c + X - V), tuple(c + X + V), tuple(c - X + V), [(0, 1), (1, 1), (1, 0), (0, 0)])


def _lamp(m, x, u, t, glow=True):
    """A caged lamp on the wall at x (local), its glow sprite in front of it."""
    s = -np.sign(x)
    _sbox(m, ('lampcage', False, 0), x, x + s * 0.28, u - 0.2, u + 0.2, t - 0.2, t + 0.2)
    if glow:
        _glow(m, ('lampglow', True, UNLIT, ADD), np.array(shaft_point(x + s * 0.35, u, t)), 0.85)


HALF = 6.0          # the walls stand HALF either side of the shaft's middle (x 40 and 52 in CARGO ELEVATOR's cells)


def segment(name, door=None):
    """A wall segment: both walls, the ceiling, the top pipes with a flange each, conduits, the east wall's hanging
    cables, a caged lamp on each wall. ``door`` 'in' cuts the entrance in the west wall, 'out' the exit in the east,
    each with its frame and the amber cage lamp AS hangs by it."""
    m = ShipModel(name, (0, 0, 0))
    for x in (-HALF, HALF):
        _wall(m, x, (door == 'in' and x < 0) or (door == 'out' and x > 0))
        s = -np.sign(x)
        px = x + s * PIPE_IN
        _tube(m, ('shaftpipe', False, 0), px, PIPE_T, PIPE_R, 0, SEG)
        _tube(m, ('flange', False, 0), px, PIPE_T, PIPE_R * 1.28, SEG * 0.55, SEG * 0.55 + 0.32, caps=True)
        for k, ct in enumerate((1.48, 1.62, 1.76) if x > 0 else (1.6,)):
            _tube(m, ('conduit', False, 0), x + s * (0.1 + 0.04 * k), ct, 0.055, 0, SEG, sides=4)
        _lamp(m, x, LAMP_U, LAMP_T)
    # The east wall's festoon: cables slung between brackets, three a segment.
    ex = HALF - 0.2
    for k in range(3):
        u0 = SEG * k / 3
        pts = [(u0 + SEG / 3 * i / 8, 1.95 + 0.35 * (1 - (2 * i / 8 - 1) ** 2)) for i in range(9)]
        for (ua, ta), (ub, tb) in zip(pts, pts[1:]):
            _face(m, ('cable', True, NO_SHADOW_CAST), [shaft_point(ex, ua, ta - 0.03), shaft_point(ex, ub, tb - 0.03),
                                                      shaft_point(ex, ub, tb + 0.03), shaft_point(ex, ua, ta + 0.03)],
                  [(0, 0), (1, 0), (1, 1), (0, 1)], (-1, 0, 0))
        _sbox(m, ('liftconsole', False, 0), HALF - 0.25, HALF, u0 - 0.06, u0 + 0.06, 1.85, 2.05)
    # The ceiling, seen only from inside the tube.
    _face(m, ('liftceil', False, 0), [shaft_point(-HALF, 0, 0), shaft_point(HALF, 0, 0), shaft_point(HALF, SEG, 0), shaft_point(-HALF, SEG, 0)],
          [(0, 0), (3, 0), (3, 1.6), (0, 1.6)], (0, INTO[0], INTO[1]))
    if door:
        x = -HALF if door == 'in' else HALF
        s = -np.sign(x)
        dy0, dy1, dz1, dz0 = doorway()
        key = ('liftframe', False, 0)
        xi = x + s * 0.03
        for y in (dy0, dy1):
            _face(m, key, [(xi, y - 0.25, dz0 - 1.0), (xi, y + 0.25, dz0 - 1.0), (xi, y + 0.25, dz1 + 0.25), (xi, y - 0.25, dz1 + 0.25)],
                  [(0, 1), (1, 1), (1, 0), (0, 0)], (s, 0, 0))
        _face(m, key, [(xi, dy0 - 0.25, dz1), (xi, dy1 + 0.25, dz1), (xi, dy1 + 0.25, dz1 + 0.3), (xi, dy0 - 0.25, dz1 + 0.3)],
              [(0, 4), (0, 0), (1, 0), (1, 4)], (s, 0, 0))
        # The amber lamps: light_spin_ele_top's on the west wall over the entrance (AS's walls u 4.87), the bottom
        # beacon on its arm off the east wall by the exit (u 4.97 when the walls stop).
        if door == 'in':
            _lamp(m, x, 4.87 - DOOR_U, 2.82, glow=False)
        else:
            _sbox(m, ('lampcage', False, 0), 4.3 - 0.18, 4.3 + 0.18, 4.97 - DOOR_U - 0.18, 4.97 - DOOR_U + 0.18, 2.68 - 0.18, 2.68 + 0.18)
            _sbox(m, ('liftconsole', False, 0), 4.3 + 0.18, HALF, 4.97 - DOOR_U - 0.06, 4.97 - DOOR_U + 0.06, 2.68 - 0.06, 2.68 + 0.06)
    return m


def shaft_models():
    """{name: ShipModel} of the shaft's model actors (src/Mission.galaxy slides them): the plain segment, the
    entrance's and the exit's, a gate leaf, and the amber and red glow sprites the script lays on its beacons."""
    out = {'ESeg': segment('ESeg'), 'ESegIn': segment('ESegIn', 'in'), 'ESegOut': segment('ESegOut', 'out')}
    # A gate leaf: two wide along the wall (y), the doorway's height, two-sided, origin at its foot's middle.
    m = out['EGateLeaf'] = ShipModel('EGateLeaf', (0, 0, 0))
    key = ('asdoor', True, 0)
    m.quad(key, (0, -1, 0), (0, 1, 0), (0, 1, DOOR_H), (0, -1, DOOR_H), [(0, 1), (1, 1), (1, 0), (0, 0)])
    for name, tex, size in (('EGlowAmber', 'glowamber', 1.3), ('EGlowRed', 'glowred', 1.1)):
        m = out[name] = ShipModel(name, (0, 0, 0))
        _glow(m, (tex, True, UNLIT, ADD), (0, 0, 0), size)
    return out


def door_meshes():
    """EDoorAS: an Alien Swarm heavy door leaf, 2 wide (scaled by the script to the doorway), wall height,
    0.3 thick, origin at its middle on the floor. EDoorSeam: its weld bead, just proud of both faces."""
    out = {}
    m = out['EDoorAS'] = ShipModel('EDoorAS', (0, 0, 0))
    key = ('asdoor', False, 0)
    m.quad(key, (-1, -0.15, 0), (1, -0.15, 0), (1, -0.15, 2.5), (-1, -0.15, 2.5), [(0, 1), (1, 1), (1, 0), (0, 0)])
    m.quad(key, (1, 0.15, 0), (-1, 0.15, 0), (-1, 0.15, 2.5), (1, 0.15, 2.5), [(0, 1), (1, 1), (1, 0), (0, 0)])
    m.quad(key, (-1, -0.15, 2.5), (1, -0.15, 2.5), (1, 0.15, 2.5), (-1, 0.15, 2.5), [(0, 0), (1, 0), (1, 0.05), (0, 0.05)])
    m = out['EDoorSeam'] = ShipModel('EDoorSeam', (0, 0, 0))
    key = ('doorseam', True, NO_SHADOW_CAST)
    m.quad(key, (-0.12, -0.17, 0.05), (0.12, -0.17, 0.05), (0.12, -0.17, 2.45), (-0.12, -0.17, 2.45), [(0, 1), (1, 1), (1, 0), (0, 0)])
    m.quad(key, (0.12, 0.17, 0.05), (-0.12, 0.17, 0.05), (-0.12, 0.17, 2.45), (0.12, 0.17, 2.45), [(0, 1), (1, 1), (1, 0), (0, 0)])
    return out


def _railrun(m, key, pts):
    """A railing along a polyline on the deck: posts at the corners and every cell or so, two bars."""
    for (xa, ya), (xb, yb) in zip(pts, pts[1:]):
        n = max(1, int(round(np.hypot(xb - xa, yb - ya))))
        for i in range(n + 1):
            x, y = xa + (xb - xa) * i / n, ya + (yb - ya) * i / n
            _box(m, key, x - 0.05, y - 0.05, 0, x + 0.05, y + 0.05, 1.0)
        for z in (0.5, 1.0):
            _box(m, key, min(xa, xb) - 0.04, min(ya, yb) - 0.04, z - 0.07, max(xa, xb) + 0.04, max(ya, yb) + 0.04, z)


def meshes(lift, notch, bridge_in, bridge_out, void, console, deck=None, depth=0.0):
    """{name: ShipModel} of the lift's units: the platform (deck, the north railing round the console's notch, the
    short rails either side of the doorways, the console), its red and green screens, the bridge, the void, and a
    security door leaf. ``deck`` (bool[H, W]) and ``depth`` give the drop's shape: its terrain lies depth below the
    deck except where a corner touches deck (tools/heights.py VOID_DEPTH), and the haze follows it."""
    out = {}
    # Bridges: grating plates over the drop, centred on their unit, long along x (turned by the script).
    for name, (x0, y0, x1, y1) in (('EBridge', bridge_in),):
        m = out[name] = ShipModel(name, (0, 0, 0))
        hx, hy = (x1 - x0) / 2, (y1 - y0) / 2
        # Over the drop's haze, which lies on the floor under the bridges (the EVoid mesh below).
        m.quad(('bridge', False, 0), (-hx, -hy, 0.07), (hx, -hy, 0.07), (hx, hy, 0.07), (-hx, hy, 0.07), [(0, 1), (1, 1), (1, 0), (0, 0)])
        _box(m, ('rail', False, 0), -hx, -hy, 0.0, hx, -hy + 0.12, 0.25)
        _box(m, ('rail', False, 0), -hx, hy - 0.12, 0.0, hx, hy, 0.25)
    x0, y0, x1, y1 = lift
    nx0, ny0, nx1, ny1 = notch
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    m = out['EPlatform'] = ShipModel('EPlatform', (cx, cy, 0))
    # The deck texture spans the platform and the notch: x0..x1 across, y0..ny1 down from its top row.
    uv = lambda x, y: ((x - x0) / (x1 - x0), (ny1 - y) / (ny1 - y0))
    for rx0, ry0, rx1, ry1 in ((x0, y0, x1, y1), (nx0, ny0, nx1, ny1)):
        c = [(rx0, ry0), (rx1, ry0), (rx1, ry1), (rx0, ry1)]
        m.quad(('lift_deck', False, 0), *[(x, y, 0.03) for x, y in c], [uv(x, y) for x, y in c])
    rail = ('liftrail', False, NO_SHADOW_CAST)
    e = 0.08
    _railrun(m, rail, [(x0 + e, y1 - e), (nx0 + e, y1 - e), (nx0 + e, ny1 - e), (nx1 - e, ny1 - e), (nx1 - e, y1 - e), (x1 - e, y1 - e)])
    for xv in (x0 + e, x1 - e):
        _railrun(m, rail, [(xv, y1 - e), (xv, bridge_in[3])])
        _railrun(m, rail, [(xv, bridge_in[1]), (xv, y0 + e)])
    # The console in the notch (lift_buttonpanel): a pedestal, its screen on the slope facing the deck.
    kx, ky = console
    _box(m, ('liftconsole', False, 0), kx - 0.55, ky - 0.3, 0, kx + 0.55, ky + 0.25, 0.9)
    for name, tex in (('EScreenR', 'screen_r'), ('EScreenG', 'screen_g')):
        s = out[name] = ShipModel(name, (kx, ky, 0))
        s.quad((tex, False, NO_SHADOW_CAST), (kx - 0.45, ky - 0.3, 0.92), (kx + 0.45, ky - 0.3, 0.92), (kx + 0.45, ky + 0.15, 1.2), (kx - 0.45, ky + 0.15, 1.2),
               [(0, 1), (1, 1), (1, 0), (0, 0)])
    # The void: the haze lying on the drop's floor, cell by cell down its sides from the deck's edge (the bridges
    # are drawn over it), and two veils of it added over the drop deeper down, so what is below fades into it as
    # AS's fog_elevator has it.
    vx0, vy0, vx1, vy1 = void
    m = out['EVoid'] = ShipModel('EVoid', (cx, cy, 0))
    def on_lift(x, y):
        return (x0 <= x < x1 and y0 <= y < y1) or (nx0 <= x < nx1 and ny0 <= y < ny1)
    def solid(x, y):
        # Deck as the terrain has it: the bridges' cells are walkable floor at the deck's height, so the terrain
        # under them runs flat across the drop to the walls. The void's cover lies over them too, so in the ride
        # the gaps either side of the platform read as the drop and not as a floor the walls slide through.
        if deck is None:
            return not (vx0 <= x < vx1 and vy0 <= y < vy1) or on_lift(x, y)
        return on_lift(x, y) or (0 <= y < deck.shape[0] and 0 <= x < deck.shape[1] and deck[y, x])
    def vz(x, y):
        return 0.02 if any(solid(xx, yy) for xx in (x - 1, x) for yy in (y - 1, y)) else -depth + 0.12
    for y in range(vy0, vy1):
        for x in range(vx0, vx1):
            if on_lift(x, y):
                continue
            c = [(x, y), (x + 1, y), (x + 1, y + 1), (x, y + 1)]
            zs = [vz(px, py) for px, py in c]
            # Where the terrain rises to the deck (the bridges' floor and the slopes off it) the haze would glow
            # as a flat floor at the deck's height: there the drop is plain black, the haze only lies deep down.
            key = ('void', False, NO_SHADOW_CAST) if max(zs) < 0 else ('voidtop', False, UNLIT)
            m.quad(key, *[(px, py, z) for (px, py), z in zip(c, zs)],
                   [((px - vx0) / (vx1 - vx0), (vy1 - py) / (vy1 - vy0)) for px, py in c])
    if depth > 0:
        for k, z in enumerate((-0.35 * depth, -0.65 * depth)):
            c = [(vx0, vy0), (vx1, vy0), (vx1, vy1), (vx0, vy1)]
            m.quad(('voidveil', True, UNLIT, ADD), *[(px, py, z) for px, py in c], [(k * 0.37 + (px - vx0) / 6, (vy1 - py) / 6) for px, py in c])
    # Security door leaf: 2 wide, wall height, 0.3 thick, origin at its middle on the floor.
    m = out['EDoor'] = ShipModel('EDoor', (0, 0, 0))
    key = ('door', False, 0)
    m.quad(key, (-1, -0.15, 0), (1, -0.15, 0), (1, -0.15, 2.5), (-1, -0.15, 2.5), [(0, 1), (1, 1), (1, 0), (0, 0)])
    m.quad(key, (1, 0.15, 0), (-1, 0.15, 0), (-1, 0.15, 2.5), (1, 0.15, 2.5), [(0, 1), (1, 1), (1, 0), (0, 0)])
    m.quad(key, (-1, -0.15, 2.5), (1, -0.15, 2.5), (1, 0.15, 2.5), (-1, 0.15, 2.5), [(0, 0), (1, 0), (1, 0.05), (0, 0.05)])
    m.quad(key, (1, -0.15, 0), (1, 0.15, 0), (1, 0.15, 2.5), (1, -0.15, 2.5), [(0, 1), (0.05, 1), (0.05, 0), (0, 0)])
    m.quad(key, (-1, 0.15, 0), (-1, -0.15, 0), (-1, -0.15, 2.5), (-1, 0.15, 2.5), [(0, 1), (0.05, 1), (0.05, 0), (0, 0)])
    return out
