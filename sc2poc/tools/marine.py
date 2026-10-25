"""The marines: an original armoured trooper holding a real gun, after Alien Swarm's squad.

Alien Swarm's marines are bulky armoured suits with a backpack and antenna, a
rounded helmet with glowing eye slits, and the gun held at the hip in both
hands, its barrel along the aim with the laser sight leaving the muzzle. The
stock SC2 marine carried its own rifle across its chest whatever the weapon,
and shots left a point in front of it; here every weapon family is its own
model (the same trooper, a different gun), swapped in as the marine changes
weapons (src/Marine.galaxy AS_GunModel), and the script fires every round,
tracer, flame and laser from that gun's muzzle (MUZZLE below, written into the
script as AS_GunMuzzle by build.py).

Built like tools/alien.py's ripper (proven in the client) and written as a
native skinned M3 in the retained crate container, but soft-bodied: the armour
is rounded boxes and shells with smooth normals, the limbs are continuous
tubes along curves, and the legs and waist blend across their joints (up to
two bones a vertex) so hips, knees and ankles bend instead of hinging apart.
The upper body, arms and gun ride one bone (Torso) so the gun holds the aim
line; the Spine under it takes the hips' turn back out, so the waist twists
while the legs run. The feet are placed by IK on a stride that matches the
script's walk rate, so they plant on the deck instead of skating. The armour
is pale so the script can tint each squad member's suit (SetTintColor), as
Alien Swarm's marines each wear their own colour.

Authored facing +X with Z up, in world units (a cell is 1), turned a quarter
turn when written: SC2 lays a unit model's -Y along the unit's facing.

    py tools/marine.py        write dist/meshes/Marine*.m3 and dist/marine-preview.png
"""
import math, sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools/m3-reader'))
sys.path.insert(0, str(ROOT))
from tools.alien import qrot, qmul, rotmat, _knots, _clone, _fixed8, _posed, TURN, CONTAINER   # noqa: E402

TEX = 'Derelict\\'

# ------------------------------------------------------------------ rig
BONES = [
    ('Root',   -1, (0.00, 0.00, 0.00)),
    ('Pelvis',  0, (0.00, 0.00, 0.47)),
    ('Spine',   1, (0.00, 0.00, 0.535)),
    ('Torso',   2, (0.00, 0.00, 0.60)),
    ('Head',    3, (0.01, 0.00, 0.79)),
    ('ThighL',  1, (0.00, 0.088, 0.455)),
    ('ShinL',   5, (0.012, 0.088, 0.265)),
    ('FootL',   6, (0.00, 0.088, 0.075)),
    ('ThighR',  1, (0.00, -0.088, 0.455)),
    ('ShinR',   8, (0.012, -0.088, 0.265)),
    ('FootR',   9, (0.00, -0.088, 0.075)),
    ('Antenna', 3, (-0.19, 0.075, 0.83)),
]
B = {name: i for i, (name, _, _) in enumerate(BONES)}
REST = {name: np.asarray(p, float) for name, _, p in BONES}

# Palette: 16 columns of 32 pixels, one material each.
SLOTS = {
    'armor': (186, 188, 182), 'armor2': (148, 152, 148), 'suit': (52, 56, 62), 'joint': (34, 36, 40),
    'trim': (224, 182, 52), 'visor': (255, 120, 60), 'pack': (118, 122, 104), 'gun': (46, 48, 52),
    'gun2': (92, 96, 100), 'gunlite': (255, 40, 30), 'glove': (40, 40, 42), 'lamp': (240, 250, 255),
    'tank': (150, 60, 40), 'health': (90, 255, 140), 'tesla': (120, 200, 255), 'saw': (200, 196, 180),
}
SLOT_INDEX = {k: i for i, k in enumerate(SLOTS)}
GLOW = {'visor': (255, 110, 50), 'gunlite': (255, 30, 20), 'lamp': (220, 240, 255), 'health': (60, 255, 120),
        'tesla': (90, 190, 255)}


def _ramp(z, lo, hi):
    f = min(1.0, max(0.0, (z - lo) / (hi - lo)))
    return f * f * (3 - 2 * f)


def leg_skin(side):
    """A leg's weights by height: pelvis into thigh at the hip, thigh into shin at the knee, shin into foot at the ankle."""
    th, sh, ft = LEGS[side]

    def weights(p):
        z = p[2]
        if z > 0.42:
            t = _ramp(z, 0.42, 0.50)
            return {'Pelvis': t, th: 1 - t}
        if z > 0.23:
            t = _ramp(z, 0.235, 0.295)
            return {th: t, sh: 1 - t}
        t = _ramp(z, 0.065, 0.115)
        return {sh: t, ft: 1 - t}
    return weights


def waist_skin(p):
    """The abdomen: pelvis into spine into torso, so the waist twists smoothly as the hips turn under the aim."""
    z = p[2]
    if z < 0.56:
        t = _ramp(z, 0.49, 0.56)
        return {'Pelvis': 1 - t, 'Spine': t}
    t = _ramp(z, 0.56, 0.64)
    return {'Spine': 1 - t, 'Torso': t}


def neck_skin(p):
    t = _ramp(p[2], 0.74, 0.80)
    return {'Torso': 1 - t, 'Head': t}


class Mesh:
    """Indexed skinned triangles: each part rides one bone, or blends across joints (a weights function)."""

    def __init__(self):
        self.pos, self.nrm, self.uv, self.skin, self.tri = [], [], [], [], []

    def add(self, pos, nrm, v, tri, slot, bone):
        base = len(self.pos)
        u = (SLOT_INDEX[slot] * 32 + 16) / 512.0
        pos = [np.asarray(p, float) for p in pos]; nrm = [np.asarray(n, float) for n in nrm]
        self.pos.extend(pos); self.nrm.extend(nrm)
        self.uv.extend((u, vv) for vv in v)
        if isinstance(bone, str):
            self.skin.extend([{bone: 1.0}] * len(pos))
        else:
            self.skin.extend(bone(p) for p in pos)
        # Front faces wind counter-clockwise about the outward normal (what the client culls by).
        for a, b, c in tri:
            fn = np.cross(pos[b] - pos[a], pos[c] - pos[a])
            if np.dot(fn, nrm[a] + nrm[b] + nrm[c]) < 0:
                b, c = c, b
            self.tri.append((base + a, base + b, base + c))

    def ellipsoid(self, center, radii, slot, bone, pitch=0.0, yaw=0.0, roll=0.0, sides=16, rings=10):
        m = rotmat(qrot(((1, 0, 0), roll), ((0, 1, 0), pitch), ((0, 0, 1), yaw)))
        c = np.asarray(center, float); r = np.asarray(radii, float)
        pos, nrm, v, tri = [], [], [], []
        for j in range(rings + 1):
            t = math.pi * j / rings
            for i in range(sides + 1):
                a = math.tau * i / sides
                unit = np.array([math.cos(t), math.sin(t) * math.cos(a), math.sin(t) * math.sin(a)])
                pos.append(c + m @ (unit * r))
                n = m @ (unit / r); nrm.append(n / np.linalg.norm(n))
                v.append(1.0 + 2.0 * j / rings + (c[0] + c[2]) * 0.7)
        for j in range(rings):
            for i in range(sides):
                a = j * (sides + 1) + i; b = a + sides + 1
                tri.extend([(a, b, b + 1), (a, b + 1, a + 1)])
        self.add(pos, nrm, v, tri, slot, bone)

    def box(self, center, size, slot, bone, pitch=0.0, yaw=0.0, roll=0.0, taper=1.0, bevel=None, basis=None):
        """A box with rounded edges and smooth normals (a box core inflated by ``bevel``, by default 40% of its
        thinnest half-size); ``taper`` narrows its +X end (a wedge for gun stocks and boot toes); ``basis`` (columns
        the box's axes) places it along a limb instead of by angles."""
        m = basis if basis is not None else rotmat(qrot(((1, 0, 0), roll), ((0, 1, 0), pitch), ((0, 0, 1), yaw)))
        c = np.asarray(center, float); h = np.asarray(size, float) / 2
        r = min(h) * 0.4 if bevel is None else min(bevel, min(h) * 0.98)
        core = h - r
        seg = 2 if r > 0.02 else 1
        band = [r * math.tan(math.pi / 4 * i / seg) for i in range(seg + 1)]
        coords = [sorted({-(core[k] + b) for b in band} | {core[k] + b for b in band}) for k in range(3)]
        slope = (taper - 1.0) / (2 * h[0])
        pos, nrm, v, tri = [], [], [], []
        for axis in range(3):
            o1, o2 = [k for k in range(3) if k != axis]
            for sign in (-1, 1):
                base = len(pos)
                n1, n2 = len(coords[o1]), len(coords[o2])
                for a in coords[o1]:
                    for b in coords[o2]:
                        q = np.zeros(3); q[axis] = sign * h[axis]; q[o1] = a; q[o2] = b
                        cc = np.clip(q, -core, core); d = q - cc; d /= np.linalg.norm(d)
                        p = cc + r * d
                        s = 1.0 + slope * (p[0] + h[0])
                        n = np.array([d[0] - slope * (p[1] * d[1] + p[2] * d[2]) / s, d[1] / s, d[2] / s])
                        pos.append(c + m @ np.array([p[0], p[1] * s, p[2] * s]))
                        nrm.append(m @ (n / np.linalg.norm(n)))
                        v.append(1.0 + 0.8 * (p[2] + 0.3 * p[0]) + (c[0] + c[2]))
                for i in range(n1 - 1):
                    for j in range(n2 - 1):
                        a = base + i * n2 + j
                        tri.extend([(a - 0, a + n2, a + n2 + 1), (a, a + n2 + 1, a + 1)])
        self.add(pos, nrm, v, tri, slot, bone)

    def along(self, a, b, width, height, slot, bone, at=0.5, length=None, bevel=None, taper=1.0):
        """A rounded box laid along a limb from a to b (an armour plate on a forearm)."""
        a = np.asarray(a, float); b = np.asarray(b, float)
        x = b - a; span = np.linalg.norm(x); x /= span
        ref = np.array([0, 0, 1.0]) if abs(x[2]) < 0.8 else np.array([1.0, 0, 0])
        z = ref - x * np.dot(ref, x); z /= np.linalg.norm(z); y = np.cross(z, x)
        self.box(a + (b - a) * at, (length or span * 0.6, width, height), slot, bone, bevel=bevel, taper=taper,
                 basis=np.column_stack((x, y, z)))

    def tube(self, a, b, r0, r1=None, slot='gun', bone='Torso', sides=12, caps=True):
        """A straight cylinder (or cone frustum) from a to b."""
        a = np.asarray(a, float); b = np.asarray(b, float); r1 = r0 if r1 is None else r1
        t = b - a; length = np.linalg.norm(t); t /= length
        up = np.array([0, 0, 1.0]) if abs(t[2]) < 0.9 else np.array([1.0, 0, 0])
        n1 = np.cross(t, up); n1 /= np.linalg.norm(n1); n2 = np.cross(t, n1)
        tilt = (r0 - r1) / length
        pos, nrm, v, tri = [], [], [], []
        for k, (p, r) in enumerate(((a, r0), (b, r1))):
            for i in range(sides + 1):
                ang = math.tau * i / sides
                d = math.cos(ang) * n1 + math.sin(ang) * n2
                n = d + t * tilt
                pos.append(p + d * r); nrm.append(n / np.linalg.norm(n)); v.append(1.0 + k * length * 3)
        for i in range(sides):
            tri.extend([(i, sides + 1 + i, sides + 2 + i), (i, sides + 2 + i, i + 1)])
        if caps:
            for p, sign, ring in ((a, -1, 0), (b, 1, sides + 1)):
                centre = len(pos); pos.append(p); nrm.append(t * sign); v.append(1.0)
                rim = len(pos)
                for i in range(sides + 1):
                    pos.append(pos[ring + i]); nrm.append(t * sign); v.append(1.0)
                for i in range(sides):
                    tri.append((centre, rim + i, rim + i + 1))
        self.add(pos, nrm, v, tri, slot, bone)

    def sweep(self, points, radii, slot, bone, sides=14, sub=4, caps=(True, True)):
        """A smooth limb: a tube along a Catmull-Rom curve through ``points``, its radius easing through ``radii``,
        closed with rounded ends."""
        P = [np.asarray(p, float) for p in points]; R = [float(r) for r in radii]
        ext = [2 * P[0] - P[1]] + P + [2 * P[-1] - P[-2]]; extR = [R[0]] + R + [R[-1]]
        cr = lambda p0, p1, p2, p3, t: 0.5 * (2 * p1 + (p2 - p0) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t
                                              + (3 * p1 - p0 - 3 * p2 + p3) * t ** 3)
        path, rad = [], []
        for i in range(len(P) - 1):
            for k in range(sub):
                path.append(cr(*ext[i:i + 4], k / sub)); rad.append(max(0.003, cr(*extR[i:i + 4], k / sub)))
        path.append(P[-1]); rad.append(R[-1])
        n = len(path)
        tang = [path[min(i + 1, n - 1)] - path[max(i - 1, 0)] for i in range(n)]
        tang = [t / np.linalg.norm(t) for t in tang]
        up = np.array([0, 0, 1.0]) if abs(tang[0][2]) < 0.9 else np.array([1.0, 0, 0])
        frame = np.cross(tang[0], up); frame /= np.linalg.norm(frame)
        rings = []          # (centre, radius, tangent, side vector, tilt of the normal along the tangent)
        for i in range(n):
            frame = frame - tang[i] * np.dot(frame, tang[i]); frame /= np.linalg.norm(frame)
            ds = np.linalg.norm(path[min(i + 1, n - 1)] - path[max(i - 1, 0)])
            tilt = math.atan2(rad[max(i - 1, 0)] - rad[min(i + 1, n - 1)], ds)
            rings.append((path[i], rad[i], tang[i], frame.copy(), tilt))
        if caps[0]:
            c, r, t, f, _ = rings[0]
            rings = [(c - t * r * 0.8 * math.sin(a), r * math.cos(a), t, f, -a) for a in (math.pi / 2, math.pi / 3, math.pi / 6)] + rings
        if caps[1]:
            c, r, t, f, _ = rings[-1]
            rings += [(c + t * r * 0.8 * math.sin(a), r * math.cos(a), t, f, a) for a in (math.pi / 6, math.pi / 3, math.pi / 2)]
        pos, nrm, v, tri = [], [], [], []
        run = 0.0
        for j, (c, r, t, f, tilt) in enumerate(rings):
            g = np.cross(t, f)
            if j:
                run += np.linalg.norm(c - rings[j - 1][0])
            for i in range(sides + 1):
                ang = math.tau * i / sides
                d = math.cos(ang) * f + math.sin(ang) * g
                pos.append(c + d * r); nrm.append(d * math.cos(tilt) + t * math.sin(tilt)); v.append(1.0 + run * 2.5)
        for j in range(len(rings) - 1):
            for i in range(sides):
                a = j * (sides + 1) + i; b = a + sides + 1
                tri.extend([(a, b, b + 1), (a, b + 1, a + 1)])
        self.add(pos, nrm, v, tri, slot, bone)

    def limb(self, a, b, r0, r1, slot, bone, sides=12):
        """A straight limb segment with rounded ends."""
        self.sweep([a, b], [r0, r1], slot, bone, sides=sides, sub=2)


# --------------------------------------------------------------- the body
GUN_Y = -0.075        # the gun rides at the right hip
GUN_Z = 0.59          # barrel height above the deck
LEGS = {1: ('ThighL', 'ShinL', 'FootL'), -1: ('ThighR', 'ShinR', 'FootR')}


def body(m, grip, fore, twohanded=True):
    """The trooper: ``grip`` the right hand on the pistol grip, ``fore`` the left hand on the foregrip."""
    # Legs: one continuous undersuit tube from hip to ankle each, blended across hip, knee and ankle, with
    # rounded armour over it: a thigh plate, a knee cap, a shin guard and a heavy boot.
    for side in (1, -1):
        y = side * 0.088
        th, sh, ft = LEGS[side]
        m.sweep([(0.0, y * 0.9, 0.51), (0.005, y, 0.455), (0.022, y, 0.36), (0.012, y, 0.265), (0.0, y, 0.17),
                 (-0.004, y, 0.09)], [0.058, 0.062, 0.058, 0.045, 0.047, 0.036], 'suit', leg_skin(side), sides=14, sub=4)
        m.box((0.03, y + side * 0.012, 0.37), (0.10, 0.10, 0.14), 'armor', th, pitch=-4, bevel=0.035)          # thigh plate
        m.box((0.0, y + side * 0.05, 0.38), (0.11, 0.025, 0.10), 'armor2', th, bevel=0.01)                     # its outer guard
        m.ellipsoid((0.058, y, 0.27), (0.034, 0.046, 0.048), 'armor2', sh, sides=14, rings=8)                 # knee cap
        m.box((0.042, y, 0.175), (0.06, 0.082, 0.15), 'armor', sh, pitch=-5, bevel=0.026)                      # shin guard
        m.box((-0.025, y, 0.19), (0.05, 0.07, 0.11), 'armor2', sh, bevel=0.02)                                # calf plate
        m.box((0.0, y, 0.105), (0.095, 0.094, 0.05), 'armor2', sh, bevel=0.02)                                # ankle cuff
        m.box((0.035, y, 0.048), (0.21, 0.098, 0.085), 'armor', ft, taper=0.82, bevel=0.032)                  # boot
        m.box((0.037, y, 0.012), (0.22, 0.104, 0.024), 'joint', ft, taper=0.85, bevel=0.01)                   # its sole
        m.ellipsoid((0.112, y, 0.042), (0.036, 0.044, 0.027), 'armor2', ft, sides=14, rings=8)                # toe cap
    # Hips: a padded core under a belt, a groin plate and flared tassets.
    m.ellipsoid((0.0, 0.0, 0.48), (0.088, 0.125, 0.07), 'suit', 'Pelvis')
    m.box((0.0, 0.0, 0.505), (0.17, 0.235, 0.042), 'joint', 'Pelvis', bevel=0.016)
    m.box((0.075, 0.0, 0.46), (0.035, 0.11, 0.085), 'armor2', 'Pelvis', pitch=10, taper=0.85, bevel=0.012)
    for side in (1, -1):
        m.box((0.0, side * 0.128, 0.455), (0.10, 0.03, 0.10), 'armor2', 'Pelvis', roll=-side * 12, bevel=0.012)
        m.box((-0.07, side * 0.06, 0.505), (0.04, 0.05, 0.05), 'pack', 'Pelvis', bevel=0.012)                # belt pouches
    # The waist, blended from the hips to the chest.
    m.sweep([(0.0, 0.0, 0.49), (0.0, 0.0, 0.56), (0.005, 0.0, 0.63)], [0.098, 0.088, 0.105], 'suit', waist_skin, sides=16, sub=3)
    # The chest: a barrel cuirass, a trimmed chest plate, a neck seal.
    m.box((0.005, 0.0, 0.665), (0.20, 0.27, 0.17), 'armor', 'Torso', bevel=0.065)
    m.box((0.072, 0.0, 0.672), (0.08, 0.22, 0.13), 'armor', 'Torso', pitch=-8, bevel=0.035)
    m.box((0.106, 0.0, 0.625), (0.014, 0.16, 0.02), 'trim', 'Torso', pitch=-8, bevel=0.006)
    m.box((0.108, 0.05, 0.69), (0.01, 0.035, 0.035), 'lamp', 'Torso', bevel=0.004)                          # chest lamp
    m.box((0.108, -0.05, 0.69), (0.012, 0.045, 0.02), 'joint', 'Torso', bevel=0.005)
    m.tube((0.005, 0.0, 0.73), (0.008, 0.0, 0.765), 0.062, 0.055, slot='joint', bone='Torso', sides=16)
    # Pauldrons: big rounded shells over the shoulder balls, a flared rim plate with a coloured edge under each.
    for side in (1, -1):
        m.ellipsoid((0.0, side * 0.165, 0.70), (0.055, 0.05, 0.055), 'suit', 'Torso', sides=12, rings=8)
        m.ellipsoid((-0.005, side * 0.182, 0.742), (0.09, 0.068, 0.042), 'armor', 'Torso', roll=side * 24)
        m.box((-0.005, side * 0.222, 0.69), (0.15, 0.03, 0.075), 'armor', 'Torso', roll=side * 22, bevel=0.013)
        m.box((-0.005, side * 0.236, 0.655), (0.135, 0.014, 0.016), 'trim', 'Torso', roll=side * 22, bevel=0.006)
    # The backpack: a rounded power pack with a ribbed cooling plate and a status lamp, twin tanks, the antenna.
    m.box((-0.155, 0.0, 0.67), (0.12, 0.23, 0.23), 'pack', 'Torso', bevel=0.04)
    m.box((-0.214, 0.0, 0.67), (0.022, 0.18, 0.17), 'armor2', 'Torso', bevel=0.009)
    for k in range(4):
        m.box((-0.226, 0.0, 0.615 + k * 0.03), (0.01, 0.13, 0.013), 'joint', 'Torso', bevel=0.004)
    m.box((-0.155, 0.0, 0.783), (0.10, 0.19, 0.016), 'armor2', 'Torso', bevel=0.007)                        # its lid
    for side in (1, -1):
        m.sweep([(-0.175, side * 0.088, 0.56), (-0.175, side * 0.088, 0.77)], [0.042, 0.042], 'armor2', 'Torso', sides=14, sub=1)
        m.tube((-0.175, side * 0.088, 0.745), (-0.175, side * 0.088, 0.758), 0.045, slot='trim', bone='Torso', sides=14)
    m.box((-0.226, -0.05, 0.745), (0.012, 0.04, 0.018), 'lamp', 'Torso', bevel=0.005)
    m.tube((-0.19, 0.075, 0.78), (-0.21, 0.075, 1.08), 0.006, 0.003, slot='joint', bone='Antenna', sides=6)
    m.ellipsoid((-0.21, 0.075, 1.08), (0.011, 0.011, 0.011), 'gunlite', 'Antenna', sides=8, rings=5)
    # Helmet: a round shell, a crown cap and crest, ear discs, a face plate with two glowing eye slits.
    m.sweep([(0.0, 0.0, 0.72), (0.008, 0.0, 0.79)], [0.046, 0.046], 'joint', neck_skin, sides=12, sub=2, caps=(False, False))
    m.ellipsoid((0.012, 0.0, 0.845), (0.09, 0.08, 0.08), 'armor', 'Head', sides=18, rings=12)
    m.ellipsoid((0.0, 0.0, 0.874), (0.076, 0.068, 0.052), 'armor2', 'Head')
    m.box((0.0, 0.0, 0.922), (0.15, 0.024, 0.024), 'armor', 'Head', pitch=-6, bevel=0.011)                  # crest ridge
    for side in (1, -1):
        m.tube((-0.005, side * 0.07, 0.84), (-0.005, side * 0.086, 0.84), 0.03, 0.026, slot='joint', bone='Head', sides=14)
    m.box((0.066, 0.0, 0.808), (0.05, 0.11, 0.06), 'joint', 'Head', pitch=10, bevel=0.02)                   # face plate
    for side in (1, -1):
        m.box((0.09, side * 0.03, 0.845), (0.014, 0.05, 0.02), 'visor', 'Head', yaw=side * 14, bevel=0.006)
        # Two lamps on the crown, the lights AS's helmets show from above.
        m.ellipsoid((0.042, side * 0.035, 0.905), (0.014, 0.012, 0.009), 'visor', 'Head', sides=8, rings=5)
    # Arms reaching to the gun, each one smooth tube through shoulder and elbow, with an armoured bracer and glove.
    shoulder_r, shoulder_l = np.array((0.0, -0.165, 0.70)), np.array((0.0, 0.165, 0.70))
    elbow_r = np.array((0.03, -0.205, 0.565)) if twohanded else np.array((0.05, -0.21, 0.575))
    elbow_l = (shoulder_l + np.asarray(fore)) / 2 + (-0.06, 0.06, -0.08)
    for shoulder, elbow, hand in ((shoulder_r, elbow_r, np.asarray(grip, float)), (shoulder_l, elbow_l, np.asarray(fore, float))):
        wrist = hand + (elbow - hand) / np.linalg.norm(elbow - hand) * 0.03
        m.sweep([shoulder, elbow, wrist], [0.046, 0.041, 0.033], 'suit', 'Torso', sides=12, sub=4)
        m.ellipsoid(elbow, (0.042, 0.042, 0.042), 'joint', 'Torso', sides=12, rings=7)
        m.along(elbow, wrist, 0.072, 0.072, 'armor2', 'Torso', at=0.5, bevel=0.024)
        m.ellipsoid(hand, (0.04, 0.033, 0.035), 'glove', 'Torso', sides=12, rings=7)


# ---------------------------------------------------------------- the guns
# Each family: (geometry builder, right hand, left hand, muzzle) in the authoring frame.
def _rifle(m, z=GUN_Z, y=GUN_Y):
    m.box((0.06, y, z - 0.01), (0.12, 0.04, 0.06), 'gun', 'Torso', taper=0.8)            # stock at the hip
    m.box((0.24, y, z), (0.24, 0.05, 0.075), 'gun', 'Torso')                            # receiver
    m.box((0.24, y, z + 0.045), (0.14, 0.03, 0.02), 'gun2', 'Torso')                    # top rail and sight
    m.box((0.21, y, z - 0.07), (0.05, 0.035, 0.08), 'gun2', 'Torso', pitch=12)          # magazine
    m.box((0.40, y, z), (0.12, 0.045, 0.055), 'gun2', 'Torso')                          # handguard
    m.tube((0.44, y, z - 0.045), (0.58, y, z - 0.045), 0.018, slot='gun', sides=8)      # under-barrel grenade tube
    m.tube((0.46, y, z + 0.005), (0.66, y, z + 0.005), 0.012, slot='gun', sides=8)      # barrel
    m.tube((0.64, y, z + 0.005), (0.68, y, z + 0.005), 0.017, slot='gun2', sides=8)     # muzzle brake
    m.box((0.50, y + 0.03, z + 0.01), (0.04, 0.015, 0.02), 'gunlite', 'Torso')          # the laser sight's emitter
    return (0.15, y - 0.005, z - 0.03), (0.40, y + 0.01, z - 0.045), (0.69, y, z + 0.005)


def _prifle(m):
    z, y = GUN_Z, GUN_Y
    m.box((0.07, y, z - 0.01), (0.14, 0.045, 0.06), 'gun', 'Torso', taper=0.75)
    m.box((0.27, y, z + 0.005), (0.30, 0.06, 0.085), 'gun2', 'Torso')
    m.box((0.27, y + 0.032, z + 0.005), (0.24, 0.006, 0.03), 'tesla', 'Torso')        # a lit charge strip
    m.box((0.23, y, z - 0.075), (0.05, 0.04, 0.08), 'gun', 'Torso')
    m.tube((0.42, y, z + 0.005), (0.64, y, z + 0.005), 0.02, 0.016, slot='gun', sides=8)
    m.box((0.50, y + 0.03, z + 0.02), (0.04, 0.015, 0.02), 'gunlite', 'Torso')
    return (0.16, y, z - 0.03), (0.40, y + 0.01, z - 0.04), (0.66, y, z + 0.005)


def _autogun(m):
    z, y = GUN_Z - 0.03, GUN_Y - 0.01
    m.box((0.16, y, z), (0.30, 0.07, 0.10), 'gun', 'Torso')                            # body slung on the harness
    m.tube((0.0, y, z + 0.02), (0.0, -0.13, 0.69), 0.012, slot='joint', sides=6)        # harness arm to the shoulder
    m.box((0.12, y - 0.05, z), (0.12, 0.04, 0.12), 'gun2', 'Torso')                    # side drum
    for k, dz in enumerate((-0.02, 0.02)):
        m.tube((0.30, y, z + dz), (0.64, y, z + dz), 0.014, slot='gun', sides=6)         # twin barrels
    m.box((0.46, y, z), (0.12, 0.06, 0.08), 'gun2', 'Torso')
    m.box((0.52, y + 0.035, z + 0.02), (0.04, 0.015, 0.02), 'gunlite', 'Torso')
    return (0.10, y + 0.02, z - 0.04), (0.36, y + 0.03, z - 0.05), (0.66, y, z)


def _shotgun(m, long=False):
    z, y = GUN_Z, GUN_Y
    m.box((0.06, y, z - 0.015), (0.13, 0.04, 0.065), 'gun', 'Torso', taper=0.8)
    m.box((0.22, y, z), (0.20, 0.055, 0.08), 'gun', 'Torso')
    m.box((0.38 if not long else 0.40, y, z - 0.04), (0.12, 0.05, 0.035), 'gun2', 'Torso')   # pump
    end = 0.62 if not long else 0.68
    m.tube((0.30, y, z + 0.01), (end, y, z + 0.01), 0.019, slot='gun', sides=8)
    m.tube((0.30, y, z - 0.03), (end - 0.08, y, z - 0.03), 0.014, slot='gun2', sides=7)        # magazine tube
    if long:
        m.box((0.18, y, z - 0.08), (0.10, 0.06, 0.07), 'gun2', 'Torso')                        # vindicator's drum
        m.tube((end - 0.06, y, z + 0.01), (end + 0.01, y, z + 0.01), 0.026, slot='gun', sides=8)
    m.box((0.46, y + 0.03, z + 0.02), (0.04, 0.015, 0.02), 'gunlite', 'Torso')
    return (0.14, y, z - 0.03), (0.38 if not long else 0.40, y + 0.01, z - 0.05), (end + 0.02, y, z + 0.01)


def _pistols(m):
    """Dual pistols: one in each hand, arms forward."""
    z = GUN_Z + 0.03
    for y in (-0.10, 0.10):
        m.box((0.30, y, z), (0.14, 0.035, 0.05), 'gun', 'Torso')
        m.box((0.26, y, z - 0.045), (0.04, 0.03, 0.06), 'gun2', 'Torso', pitch=14)
        m.tube((0.36, y, z + 0.008), (0.40, y, z + 0.008), 0.01, slot='gun2', sides=6)
    m.box((0.33, -0.08, z + 0.03), (0.03, 0.012, 0.015), 'gunlite', 'Torso')
    return (0.25, -0.10, z - 0.02), (0.25, 0.10, z - 0.02), (0.41, -0.10, z + 0.008)


def _minigun(m):
    z, y = GUN_Z - 0.04, GUN_Y - 0.02
    m.box((0.12, y, z), (0.22, 0.09, 0.12), 'gun', 'Torso')                            # motor housing
    m.box((0.06, y - 0.06, z + 0.0), (0.12, 0.05, 0.1), 'tank', 'Torso')               # ammo box
    m.box((0.22, y + 0.02, z + 0.08), (0.10, 0.02, 0.03), 'gun2', 'Torso')             # carry handle
    for k in range(6):
        a = math.tau * k / 6
        dy, dz = math.cos(a) * 0.028, math.sin(a) * 0.028
        m.tube((0.22, y + dy, z + dz), (0.66, y + dy, z + dz), 0.009, slot='gun2', sides=5, caps=False)
    for x in (0.30, 0.56):
        m.tube((x, y, z), (x + 0.03, y, z), 0.045, slot='gun', sides=10)
    m.box((0.40, y + 0.05, z + 0.02), (0.04, 0.015, 0.02), 'gunlite', 'Torso')
    return (0.10, y + 0.03, z - 0.06), (0.30, y + 0.06, z + 0.07), (0.67, y, z)


def _flamer(m):
    z, y = GUN_Z - 0.01, GUN_Y
    m.box((0.12, y, z), (0.22, 0.06, 0.08), 'gun', 'Torso')
    m.tube((0.12, y - 0.045, z - 0.05), (0.30, y - 0.045, z - 0.05), 0.035, slot='tank', sides=10)   # fuel tank
    m.tube((0.22, y, z + 0.01), (0.56, y, z + 0.01), 0.02, slot='gun2', sides=8)
    m.tube((0.56, y, z + 0.01), (0.62, y, z + 0.01), 0.028, 0.022, slot='gun', sides=8)
    m.ellipsoid((0.625, y, z - 0.02), (0.012, 0.012, 0.012), 'visor', 'Torso', sides=6, rings=4)     # pilot flame
    m.tube((-0.175, -0.088, 0.58), (0.12, y - 0.04, z - 0.04), 0.01, slot='joint', sides=5)          # hose to the pack
    return (0.10, y, z - 0.04), (0.40, y + 0.01, z - 0.02), (0.63, y, z + 0.01)


def _sniper(m):
    z, y = GUN_Z + 0.01, GUN_Y
    m.box((0.05, y, z - 0.02), (0.14, 0.04, 0.07), 'gun', 'Torso', taper=0.7)
    m.box((0.24, y, z), (0.26, 0.05, 0.07), 'gun', 'Torso')
    m.tube((0.18, y, z + 0.07), (0.34, y, z + 0.07), 0.022, slot='gun2', sides=8)      # scope
    m.ellipsoid((0.345, y, z + 0.07), (0.006, 0.018, 0.018), 'tesla', 'Torso', sides=6, rings=4)
    m.box((0.22, y, z - 0.065), (0.04, 0.035, 0.06), 'gun2', 'Torso')
    m.tube((0.37, y, z + 0.005), (0.78, y, z + 0.005), 0.012, slot='gun', sides=7)
    m.tube((0.74, y, z + 0.005), (0.80, y, z + 0.005), 0.018, slot='gun2', sides=7)
    m.box((0.48, y + 0.03, z + 0.02), (0.04, 0.015, 0.02), 'gunlite', 'Torso')
    return (0.15, y, z - 0.03), (0.42, y + 0.01, z - 0.03), (0.81, y, z + 0.005)


def _railgun(m):
    z, y = GUN_Z, GUN_Y
    m.box((0.08, y, z - 0.01), (0.16, 0.05, 0.07), 'gun', 'Torso', taper=0.8)
    m.box((0.28, y, z), (0.24, 0.07, 0.10), 'gun2', 'Torso')
    for dz in (-0.03, 0.03):
        m.box((0.54, y, z + dz), (0.30, 0.03, 0.018), 'gun', 'Torso')                  # the two rails
    m.box((0.50, y, z), (0.24, 0.012, 0.03), 'tesla', 'Torso')                         # the charge between them
    m.box((0.36, y + 0.04, z + 0.02), (0.04, 0.015, 0.02), 'gunlite', 'Torso')
    return (0.17, y, z - 0.03), (0.40, y + 0.01, z - 0.05), (0.70, y, z)


def _tesla(m):
    z, y = GUN_Z, GUN_Y
    m.box((0.14, y, z), (0.24, 0.07, 0.09), 'gun', 'Torso')
    for x in (0.34, 0.42, 0.50):
        m.tube((x, y, z), (x + 0.03, y, z), 0.04, slot='gun2', sides=10)               # coils
        m.tube((x + 0.03, y, z), (x + 0.06, y, z), 0.03, slot='tesla', sides=10)
    m.ellipsoid((0.60, y, z), (0.03, 0.03, 0.03), 'tesla', 'Torso', sides=8, rings=6)
    return (0.12, y, z - 0.04), (0.36, y + 0.01, z - 0.05), (0.62, y, z)


def _healgun(m):
    z, y = GUN_Z, GUN_Y
    m.box((0.16, y, z), (0.26, 0.06, 0.08), 'armor', 'Torso')
    m.box((0.16, y + 0.032, z), (0.06, 0.004, 0.05), 'health', 'Torso')               # the cross
    m.box((0.16, y + 0.032, z), (0.02, 0.005, 0.016), 'armor', 'Torso')
    m.tube((0.29, y, z), (0.48, y, z), 0.02, slot='gun2', sides=8)
    m.ellipsoid((0.50, y, z), (0.022, 0.022, 0.022), 'health', 'Torso', sides=8, rings=6)
    m.tube((0.12, y - 0.04, z - 0.04), (0.24, y - 0.04, z - 0.04), 0.03, slot='health', sides=8)   # the vial
    return (0.13, y, z - 0.04), (0.33, y + 0.01, z - 0.03), (0.52, y, z)


def _chainsaw(m):
    z, y = GUN_Z - 0.02, GUN_Y
    m.box((0.12, y, z), (0.18, 0.08, 0.12), 'tank', 'Torso')                           # motor
    m.box((0.40, y, z), (0.40, 0.012, 0.07), 'saw', 'Torso')                           # bar
    for k in range(9):
        m.box((0.22 + k * 0.045, y, z + 0.04), (0.02, 0.02, 0.012), 'gun', 'Torso')   # teeth
        m.box((0.22 + k * 0.045, y, z - 0.04), (0.02, 0.02, 0.012), 'gun', 'Torso')
    m.box((0.12, y, z + 0.08), (0.10, 0.02, 0.03), 'gun', 'Torso')
    return (0.10, y, z - 0.03), (0.13, y + 0.04, z + 0.09), (0.60, y, z)


def _launcher(m):
    z, y = GUN_Z, GUN_Y
    m.box((0.06, y, z - 0.01), (0.12, 0.04, 0.065), 'gun', 'Torso', taper=0.8)
    m.box((0.20, y, z), (0.16, 0.06, 0.08), 'gun', 'Torso')
    m.tube((0.26, y, z - 0.01), (0.36, y, z - 0.01), 0.06, slot='gun2', sides=10)      # revolving cylinder
    m.tube((0.36, y, z), (0.62, y, z), 0.03, slot='gun', sides=10)
    m.tube((0.60, y, z), (0.64, y, z), 0.036, slot='trim', sides=10)
    m.box((0.44, y + 0.04, z + 0.02), (0.04, 0.015, 0.02), 'gunlite', 'Torso')
    return (0.15, y, z - 0.03), (0.46, y + 0.01, z - 0.04), (0.65, y, z)


def _case(m):
    """Carrying a deployable (a sentry case, the ammo bag): a case in the right hand, a pistol-light in the left."""
    m.box((0.02, -0.20, 0.41), (0.22, 0.07, 0.16), 'pack', 'Torso', bevel=0.02)
    m.box((0.02, -0.20, 0.50), (0.08, 0.02, 0.02), 'joint', 'Torso')
    m.box((0.02, -0.236, 0.41), (0.12, 0.004, 0.04), 'trim', 'Torso')
    z, y = GUN_Z + 0.03, 0.08
    m.box((0.30, y, z), (0.12, 0.035, 0.05), 'gun', 'Torso')
    m.box((0.33, y + 0.022, z + 0.01), (0.03, 0.01, 0.015), 'gunlite', 'Torso')
    return (0.02, -0.20, 0.51), (0.26, y, z - 0.02), (0.37, y, z)


# Model name, builder, two-handed (both hands on one gun). Script weapon ids map to these (AS_GunModel).
GUNS = [('Rifle', _rifle, True), ('PRifle', _prifle, True), ('Autogun', _autogun, True), ('Shotgun', _shotgun, True),
        ('Vindicator', lambda m: _shotgun(m, True), True), ('Pistols', _pistols, False), ('Minigun', _minigun, True),
        ('Flamer', _flamer, True), ('Sniper', _sniper, True), ('Railgun', _railgun, True), ('Tesla', _tesla, True),
        ('Healgun', _healgun, True), ('Chainsaw', _chainsaw, True), ('Launcher', _launcher, True), ('Case', _case, False)]


def gun_only(gun):
    """The gun alone, lying on the deck: the same parts the marine holds, centred and set down, all on the still
    root bone (a weapon dropped by a fallen marine or waiting in a supply room)."""
    m = Mesh()
    builder = dict((n, b) for n, b, _ in GUNS)[gun]
    builder(m)
    pos = np.asarray(m.pos)
    lo, hi = pos.min(0), pos.max(0)
    shift = np.array([-(lo[0] + hi[0]) / 2, -(lo[1] + hi[1]) / 2, -lo[2] + 0.01])
    m.pos = [p + shift for p in m.pos]
    m.skin = [{'Root': 1.0}] * len(m.skin)
    return m


def geometry(gun):
    m = Mesh()
    builder = dict((n, b) for n, b, _ in GUNS)[gun]
    two = dict((n, t) for n, _, t in GUNS)[gun]
    grip, fore, muzzle = builder(m)
    body(m, grip, fore, two)
    return m, muzzle


# ----------------------------------------------------------- animation
X3, Y3, Z3 = (1, 0, 0), (0, 1, 0), (0, 0, 1)
BALL, HEEL, ANKLE_Z = 0.105, 0.05, 0.075       # the boot's ball and heel from the ankle, the ankle's height
STANCE = 0.3          # of a run cycle each foot is down (a run: both feet are off the deck between steps)
RATE = 2.2            # src/Marine.galaxy AS_Walk plays the gaits at time scale rate/2.2: 2.2 cells a second at 1x


def _conj(q):
    return np.array([-q[0], -q[1], -q[2], q[3]])


def _loop(t, knots):
    """Periodic Catmull-Rom through (phase, value) knots: smooth through every knot, never stopping at one."""
    ts = [k[0] for k in knots]; vs = [k[1] for k in knots]; n = len(knots)
    t %= 1.0
    i = max([j for j in range(n) if ts[j] <= t], default=n - 1)
    t0 = ts[i] - (1.0 if t < ts[i] else 0.0); t1 = ts[(i + 1) % n] + (1.0 if i + 1 >= n else 0.0) - (1.0 if t < ts[i] else 0.0)
    u = (t - t0) / (t1 - t0)
    p0, p1, p2, p3 = (vs[(i + k) % n] for k in (-1, 0, 1, 2))
    return 0.5 * (2 * p1 + (p2 - p0) * u + (2 * p0 - 5 * p1 + 4 * p2 - p3) * u * u + (3 * p1 - p0 - 3 * p2 + p3) * u ** 3)


def _foot(flat, yaw, pitch):
    """(ankle, world rotation) of a boot whose flat-footed ankle would stand over ``flat``, turned ``yaw``, rolled
    ``pitch`` (+ heel up, rolling over the ball; - toe up, rocking on the heel)."""
    f = np.array([math.cos(math.radians(yaw)), math.sin(math.radians(yaw)), 0.0])
    a = np.array([flat[0], flat[1], ANKLE_Z])
    pivot = a + f * (BALL if pitch >= 0 else -HEEL); pivot[2] = 0.0
    turn = rotmat(qrot((Z3, -yaw), (Y3, pitch), (Z3, yaw)))
    return pivot + turn @ (a - pivot), qrot((Y3, pitch), (Z3, yaw))


def _leg(side, pel_loc, pel_q, ankle, foot_q):
    """Two-bone IK: thigh, shin and foot rotations that put this leg's ankle at ``ankle`` with the boot at ``foot_q``."""
    th, sh, ft = LEGS[side]
    R = rotmat(pel_q)
    hip = REST['Pelvis'] + np.asarray(pel_loc, float) + R @ (REST[th] - REST['Pelvis'])
    v = R.T @ (np.asarray(ankle, float) - hip)
    a = REST[sh] - REST[th]; b = REST[ft] - REST[sh]
    L1, L2 = np.linalg.norm(a), np.linalg.norm(b)
    roll = math.atan2(v[1], -v[2])
    vx, vz = v[0], -math.hypot(v[1], v[2])
    D = min(max(math.hypot(vx, vz), abs(L1 - L2) + 1e-4), (L1 + L2) * 0.9995)
    aim = math.atan2(vx, -vz)
    thf = aim + math.acos(max(-1.0, min(1.0, (L1 * L1 + D * D - L2 * L2) / (2 * L1 * D))))      # the knee bends forward
    kx, kz = L1 * math.sin(thf), -L1 * math.cos(thf)
    shf = math.atan2(D * math.sin(aim) - kx, -(-D * math.cos(aim) - kz))
    th0, sh0 = math.atan2(a[0], -a[2]), math.atan2(b[0], -b[2])
    q_th = qrot((Y3, -math.degrees(thf - th0)), (X3, math.degrees(roll)))
    q_sh = qrot((Y3, -math.degrees((shf - thf) - (sh0 - th0))))
    q_ft = qmul(_conj(qmul(qmul(pel_q, q_th), q_sh)), foot_q)
    zero = np.zeros(3)
    return {B[th]: (zero, q_th), B[sh]: (zero, q_sh), B[ft]: (zero, q_ft)}


def _upright(out, pel_q, upper_q):
    """The Spine takes the hips' turn and tilt back out, so the chest (and the gun on it) sits at ``upper_q``."""
    out[B['Spine']] = (np.zeros(3), qmul(_conj(pel_q), upper_q))
    out[B['Torso']] = (np.zeros(3), np.array([0.0, 0.0, 0.0, 1.0]))


def _planted(out, pel_loc, pel_q, feet):
    """Both boots planted flat: ``feet`` is {side: (x, y, yaw)}."""
    for side, (x, y, yaw) in feet.items():
        out.update(_leg(side, pel_loc, pel_q, *_foot((x, y), yaw, 0.0)))


def _gait(t, travel, hips, duration):
    """A run cycle along ``travel`` degrees (0 ahead, 90 to the left), the hips turned ``hips`` toward it while the
    chest keeps the aim. The left foot lands at t=0 and the right at t=0.5; each boot is down for STANCE of the
    cycle, sliding back exactly as fast as the deck passes at the rate the script plays the cycle, then swings
    through high and lands reaching, heel first."""
    out = {}
    stride = RATE * duration / 1000.0                 # cells the body covers a cycle
    reach = stride * STANCE                           # how far a planted boot passes under the body
    u = np.array([math.cos(math.radians(travel)), math.sin(math.radians(travel))])
    mid = STANCE / 2
    bob = -0.03 - 0.012 * math.cos(2 * math.tau * (t - mid))          # lowest mid-stance, highest in the air
    twist = -7.0 * math.cos(math.tau * t)                               # the leading leg's hip comes forward
    roll = 3.0 * math.cos(math.tau * (t - mid))                         # the hip over the planted foot rides high
    sway = 0.008 * math.cos(math.tau * (t - mid))                       # and the body sways over it
    yaw = math.radians(hips)
    pel_loc = np.array([-math.sin(yaw) * sway, math.cos(yaw) * sway, bob])
    pel_q = qrot((Y3, 7.0), (X3, roll), (Z3, hips + twist))
    out[B['Pelvis']] = (pel_loc, pel_q)
    bounce = math.cos(2 * math.tau * (t - mid - 0.07))
    _upright(out, pel_q, qrot((Y3, 2.5 + 1.2 * bounce), (X3, 0.25 * roll)))
    out[B['Head']] = (np.zeros(3), qrot((Y3, -3.0 - 0.6 * bounce), (Z3, 2.0 * math.sin(math.tau * t))))
    out[B['Antenna']] = (np.zeros(3), qrot((Y3, -10.0 - 7.0 * math.cos(2 * math.tau * (t - mid - 0.15))),
                                           (X3, 5.0 * math.sin(math.tau * t - 1.0))))
    pitch_knots = [(0.0, -11.0), (0.07, 0.0), (0.16, 0.0), (STANCE, 26.0), (0.42, 44.0), (0.62, 14.0), (0.85, -6.0), (0.94, -12.0)]
    for side, offset in ((1, 0.0), (-1, 0.5)):
        ph = (t - offset) % 1.0
        centre = np.array([-math.sin(yaw) * side * 0.098, math.cos(yaw) * side * 0.098]) - u * 0.012
        fyaw = hips * 0.85 + side * 5.0
        land, lift = centre + u * reach / 2, centre - u * reach / 2
        pitch = _loop(ph, pitch_knots)
        if ph < STANCE:
            pitch = min(pitch, 0.0) if ph < mid else max(pitch, 0.0)
            flat = land + (lift - land) * (ph / STANCE)
            ankle, fq = _foot(flat, fyaw, pitch)
        else:
            s = (ph - STANCE) / (1 - STANCE)
            # Hermite from lift-off to landing, leaving and arriving with the deck's speed (the boot keeps sweeping
            # back a moment after it leaves and is pulled back under as it lands), arcing up early in the swing.
            v = -(reach / STANCE) * (1 - STANCE) * 0.5
            h00, h10, h01, h11 = 2 * s ** 3 - 3 * s * s + 1, s ** 3 - 2 * s * s + s, -2 * s ** 3 + 3 * s * s, s ** 3 - s * s
            flat = lift * h00 + land * h01 + u * v * (h10 + h11)
            ankle, fq = _foot(flat, fyaw, pitch)
            ankle = ankle + np.array([0, 0, 0.09 * math.sin(math.pi * s) * (1 + 0.45 * math.cos(math.pi * s))])
        out.update(_leg(side, pel_loc, pel_q, ankle, fq))
    return out


STAND_DROP = 0.022    # the stance's knee bend lowers the gun this far from the model's rest pose


def pose(name, t):
    out = {}
    ph = t * math.tau

    def put(bone, loc=(0, 0, 0), *rot):
        out[B[bone]] = (np.asarray(loc, float), qrot(*rot))

    if name == 'Stand':
        # A ready stance, knees soft and boots apart, the left a little ahead; the weight drifts from foot to foot,
        # the chest breathes and the head looks about while the gun stays on the line.
        pel_loc = np.array([0.0, 0.006 * math.sin(ph), -STAND_DROP + 0.003 * math.sin(2 * ph)])
        pel_q = qrot((Y3, 3.0), (X3, -1.2 * math.sin(ph)), (Z3, -6.0))
        out[B['Pelvis']] = (pel_loc, pel_q)
        _upright(out, pel_q, qrot((Y3, 1.0 + 0.8 * math.sin(2 * ph)), (X3, 0.4 * math.sin(ph))))
        _planted(out, pel_loc, pel_q, {1: (0.035, 0.105, 10.0), -1: (-0.04, -0.10, -16.0)})
        put('Head', (0, 0, 0), (Z3, 7 * math.sin(ph)), (Y3, -2 * math.sin(2 * ph)))
        put('Antenna', (0, 0, 0), (X3, 3 * math.sin(2 * ph + 0.5)), (Y3, -2 + 2 * math.sin(ph)))
    elif name == 'Walk':
        # The run forward.
        return _gait(t, 0.0, 0.0, WALK_MS)
    elif name == 'Work':
        # Backing off while aiming ahead: the run played backwards (the boots land toe first and leave heel last).
        return pose('Walk', 1.0 - t)
    elif name in ('Spell', 'Cover'):
        # Side-steps (Spell to the marine's left, Cover to its right): the hips turn toward the run and the legs
        # run that way while the waist twists the chest back onto the aim.
        side = 1 if name == 'Spell' else -1
        return _gait(t, side * 90.0, side * 50.0, WALK_MS)
    elif name == 'Attack':
        # A rifle-butt swing: boots planted wide, the chest winds back, then drives across from the hips.
        twist = _knots(t, [(0, 0), (0.25, 30), (0.5, -38), (0.8, -10), (1, 0)])
        lean = _knots(t, [(0, 0), (0.25, -6), (0.5, 14), (1, 0)])
        lunge = _knots(t, [(0, 0), (0.5, 0.04), (1, 0)])
        pel_loc = np.array([lunge, 0.0, -0.035 - 0.5 * lunge])
        pel_q = qrot((Y3, 4.0 + 0.3 * lean), (Z3, 0.4 * twist))
        out[B['Pelvis']] = (pel_loc, pel_q)
        _upright(out, pel_q, qrot((Y3, lean), (Z3, twist)))
        _planted(out, pel_loc, pel_q, {1: (0.08, 0.115, 15.0), -1: (-0.085, -0.105, -25.0)})
        put('Head', (0, 0, 0), (Z3, -twist * 0.5))
        put('Antenna', (0, 0, 0), (Y3, -twist * 0.2), (X3, twist * 0.15))
    elif name == 'Morph':
        # The reload (stock name Morph, so the client's lookup finds it): the gun dips and turns in toward the body
        # as the old clip drops and a new one goes in, then comes back up onto the aim. Upper body only (see
        # SEQ_BONES), so the legs keep running under it.
        dip = _knots(t, [(0, 0), (0.18, 1), (0.75, 1), (1, 0)])
        jolt = _knots(t, [(0, 0), (0.55, 0), (0.62, 1), (0.72, 0), (1, 0)])
        put('Torso', (0, 0, -0.01 * dip), (Y3, 16 * dip + 4 * jolt), (Z3, 22 * dip), (X3, -8 * dip))
        put('Head', (0, 0, 0), (Y3, 14 * dip), (Z3, -10 * dip))
    elif name == 'Death':
        # Shot down: the knees buckle, the marine goes over backwards and lands on its pack, legs out in front,
        # the gun still in its hands; a last twitch, then still.
        f = _knots(t, [(0, 0), (0.15, 0.12), (0.55, 1.0), (0.62, 0.95), (0.7, 1.0), (1, 1)])
        buckle = _knots(t, [(0, 0), (0.18, 1), (0.5, 0.3), (1, 0.15)])
        tw = math.sin(t * 50) * max(0.0, 1 - abs(t - 0.8) / 0.08) * 3
        put('Pelvis', (-0.12 * f, 0, -0.05 * buckle - DEATH_DROP * f), (Y3, -80 * f))
        put('Spine', (0, 0, 0), (Y3, -6 * f + 10 * buckle))
        put('Torso', (0, 0, 0), (Y3, -4 * f + tw), (Z3, 74 * f))     # turned onto its side, so the gun lies along the deck
        put('Head', (0, 0, 0), (Y3, 20 * f), (Z3, 25 * f))
        put('Antenna', (0, 0, 0), (Y3, 30 * f))
        put('ThighL', (0, 0, 0), (Y3, -30 * f - 35 * buckle), (X3, 8 * f)); put('ShinL', (0, 0, 0), (Y3, 40 * f + 60 * buckle))
        put('FootL', (0, 0, 0), (Y3, -10 * f - 20 * buckle))
        put('ThighR', (0, 0, 0), (Y3, -12 * f - 30 * buckle), (X3, -10 * f)); put('ShinR', (0, 0, 0), (Y3, 14 * f + 55 * buckle + tw))
        put('FootR', (0, 0, 0), (Y3, 20 * f - 20 * buckle))
    elif name == 'Fire':
        # Recoil: a short kick back through the shoulders.
        k = _knots(t, [(0, 0), (0.15, 1), (1, 0)])
        put('Torso', (-0.02 * k, 0, 0), (Y3, -4 * k))
    return out


WALK_MS = 500
DEATH_DROP = 0.235
WALK_SPEED = RATE
# Walk runs forward; Work backs off, Spell and Cover side-step left and right (stock animation names, so the
# client's lookup finds them: src/Marine.galaxy AS_Walk picks one from the run's angle to the aim).
SEQUENCES = [('Stand', 3000, 0.0, False), ('Walk', WALK_MS, WALK_SPEED, False), ('Work', WALK_MS, 0.0, False),
             ('Spell', WALK_MS, 0.0, False), ('Cover', WALK_MS, 0.0, False), ('Attack', 600, 0.0, True),
             ('Fire', 160, 0.0, True), ('Death', 1300, 0.0, True), ('Morph', 1000, 0.0, True)]
ANIMATED = {'location': {B['Pelvis'], B['Torso']}, 'rotation': set(range(1, len(BONES)))}
# Sequences that move only part of the body: the client blends them over whatever the rest is playing.
SEQ_BONES = {'Morph': {'location': {B['Torso']}, 'rotation': {B['Torso'], B['Head']}}}


def fk(posed):
    """World (position, rotation) of every rig bone in a pose from pose(): for checks."""
    out = []
    for i, (name, parent, pivot) in enumerate(BONES):
        loc, q = posed.get(i, (np.zeros(3), np.array([0.0, 0.0, 0.0, 1.0])))
        local = REST[name] - (REST[BONES[parent][0]] if parent >= 0 else 0) + loc
        if parent < 0:
            out.append((local, q))
        else:
            pp, pq = out[parent]
            out.append((pp + rotmat(pq) @ local, qmul(pq, q)))
    return out


# ------------------------------------------------------------------ M3
# SC2's attachment points (name tags float on Ref_Center, effects find Ref_Weapon at the muzzle): each on a
# still bone of its own, a child of the bone it rides with.
ATTACH = [('Ref_Origin', 'Root', (0.0, 0.0, 0.0)), ('Ref_Center', 'Torso', (0.0, 0.0, 0.55)), ('Ref_Target', 'Torso', (0.0, 0.0, 0.55)),
          ('Ref_Chest', 'Torso', (0.09, 0.0, 0.65)), ('Ref_Head', 'Head', (0.02, 0.0, 0.82)), ('Ref_Overhead', 'Torso', (0.0, 0.0, 1.0)),
          ('Ref_Hardpoint', 'Torso', (-0.16, 0.0, 0.7))]


def all_bones(muzzle):
    """The rig plus one bone per attachment point (Ref_Weapon at this gun's muzzle)."""
    out = list(BONES)
    for name, parent, pos in ATTACH + [('Ref_Weapon', 'Torso', tuple(muzzle))]:
        out.append(('Att' + name[4:], B[parent], pos))
    return out


def rig(model, m3, name, muzzle):
    import m3 as m3mod
    source = _clone(model.bones[0]); inverse = _clone(model.absoluteInverseBoneRestPositions[0])
    bones, inverses = [], []
    rig_bones = all_bones(muzzle)
    for i, (bname, parent, pivot) in enumerate(rig_bones):
        bone = _clone(source); bone.name = name + '_' + bname; bone.parent = parent
        local = TURN @ (np.asarray(pivot) - (np.asarray(rig_bones[parent][2]) if parent >= 0 else 0))
        for field in ('location', 'rotation', 'scale'):
            ref = getattr(bone, field)
            ref.header.animId = 0x13000000 + i * 16 + {'location': 1, 'rotation': 2, 'scale': 3}[field]
            ref.header.animFlags = 6 if i in ANIMATED.get(field, ()) else 0
            ref.header.interpolationType = 1
            for value in (ref.initValue, ref.nullValue):
                for j, key in enumerate('xyz'):
                    setattr(value, key, float(local[j]) if field == 'location' else 1.0 if field == 'scale' else 0.0)
                if field == 'rotation':
                    value.w = 1.0
        bones.append(bone)
        inv = _clone(inverse)
        for row in 'xyzw':
            for col in 'xyzw':
                setattr(getattr(inv.matrix, row), col, float(row == col))
        inv.matrix.w.x, inv.matrix.w.y, inv.matrix.w.z = (-float(v) for v in TURN @ np.asarray(pivot))
        inverses.append(inv)
    seq_t, stc_t = _clone(model.sequences[0]), _clone(model.sequenceTransformationCollections[0])
    stg_t, sts_t = _clone(model.sequenceTransformationGroups[0]), _clone(model.sts[0])
    model.bones = bones; model.absoluteInverseBoneRestPositions = inverses
    model.boneLookup = list(range(len(BONES))); model.numberOfBonesToCheckForSkin = len(BONES)
    atts = []
    for k, (aname, _, _) in enumerate(ATTACH + [('Ref_Weapon', None, None)]):
        att = m3mod.structures['ATT_'].getVersion(1).createInstance()
        att.unknown = -1; att.name = aname; att.boneIndex = len(BONES) + k
        atts.append(att)
    model.attachmentPoints = atts
    model.attachmentPointAddons = [0xffff] * len(atts)
    region = model.divisions[0].regions[0]
    region.numberOfBones = region.numberOfBoneLookupIndices = len(BONES); region.firstBoneLookupIndex = 0; region.rootBoneIndex = 0
    model.sequences, model.sequenceTransformationCollections, model.sequenceTransformationGroups, model.sts = [], [], [], []
    steps = 24
    for si, (seq_name, duration, speed, once) in enumerate(SEQUENCES):
        seq = _clone(seq_t); seq.name = seq_name; seq.animStartInMS = 0; seq.animEndInMS = duration
        seq.movementSpeed = speed; seq.frequency = 100; seq.flags = 1 if once else 0
        b = seq.boundingSphere
        b.minBorder.x, b.minBorder.y, b.minBorder.z = -0.9, -0.6, -0.1
        b.maxBorder.x, b.maxBorder.y, b.maxBorder.z = 0.9, 0.6, 1.2
        b.radius = 1.2
        stc = _clone(stc_t); stc.name = seq_name + '_full'; stc.stsIndex = stc.stsIndexCopy = si
        for key, value in vars(stc).items():
            if isinstance(value, list):
                setattr(stc, key, [])
        frames = [round(duration * k / steps) for k in range(steps + 1)]
        poses = [pose(seq_name, k / steps) for k in range(steps + 1)]
        ids, refs = [], []
        for field in ('location', 'rotation'):
            for bi in sorted(SEQ_BONES.get(seq_name, ANIMATED)[field]):
                ids.append(getattr(bones[bi], field).header.animId)
                track = m3.structures['SD3V' if field == 'location' else 'SD4Q'].getVersion(0).createInstance()
                track.frames = frames; track.flags = 1; track.fend = duration; track.keys = []
                prev = None
                for p in poses:
                    loc, rot = p.get(bi, (np.zeros(3), np.array([0.0, 0.0, 0.0, 1.0])))
                    if field == 'rotation':
                        # Keep each key in the previous key's hemisphere, so the client never turns the long way.
                        rot = rot / np.linalg.norm(rot)
                        if prev is not None and np.dot(rot, prev) < 0:
                            rot = -rot
                        prev = rot
                    value = _clone(getattr(bones[bi], field).initValue)
                    if field == 'location':
                        loc = TURN @ loc
                        value.x, value.y, value.z = (float(getattr(value, k) + loc[j]) for j, k in enumerate('xyz'))
                    else:
                        value.x, value.y, value.z = (float(c) for c in TURN @ rot[:3]); value.w = float(rot[3])
                    track.keys.append(value)
                if field == 'location':
                    refs.append((2 << 16) | len(stc.sd3v)); stc.sd3v.append(track)
                else:
                    refs.append((3 << 16) | len(stc.sd4q)); stc.sd4q.append(track)
        stc.animIds = ids; stc.animRefs = refs
        stg = _clone(stg_t); stg.name = seq_name; stg.stcIndices = [si]
        sts = _clone(sts_t); sts.animIds = ids[:]
        model.sequences.append(seq); model.sequenceTransformationCollections.append(stc)
        model.sequenceTransformationGroups.append(stg); model.sts.append(sts)


def write_m3(mesh, name, path, muzzle):
    import m3
    model = m3.loadModel(str(CONTAINER))
    pos = np.asarray(np.asarray(mesh.pos) @ TURN.T, '<f4'); n = len(pos)
    tri = np.asarray(mesh.tri, int)
    assert 0 < n <= 65535 and tri.max() < n, n
    uv = np.asarray(mesh.uv, float)
    assert np.abs(uv).max() < 15.9
    vertex = np.zeros((n, 32), np.uint8)
    vertex[:, 0:12] = pos.view(np.uint8).reshape(n, 12)
    # Up to four (bone, weight) pairs a vertex, heaviest first, the weights in bytes summing to 255.
    pairs = 1
    for i, skin in enumerate(mesh.skin):
        ranked = sorted(((w, B[b]) for b, w in skin.items() if w > 1e-3), reverse=True)[:4]
        total = sum(w for w, _ in ranked)
        q = [int(round(255 * w / total)) for w, _ in ranked]
        q[0] += 255 - sum(q)
        ranked = [(w, b) for w, (_, b) in zip(q, ranked) if w > 0]
        pairs = max(pairs, len(ranked))
        for k, (w, b) in enumerate(ranked):
            vertex[i, 12 + k] = w; vertex[i, 16 + k] = b
    vertex[:, 20:23] = _fixed8(np.asarray(mesh.nrm) @ TURN.T)
    vertex[:, 23] = 255
    vertex[:, 24:28] = np.rint(uv * 2048).astype('<i2').view(np.uint8).reshape(n, 4)
    vertex[:, 28:31] = _fixed8(np.tile([1.0, 0.0, 0.0], (n, 1)))
    vertex[:, 31] = 255
    model.vertices = bytearray(vertex.tobytes())
    div = model.divisions[0]; region = div.regions[0]; obj = div.objects[0]
    region.firstVertexIndex = 0; region.numberOfVertices = n
    region.firstFaceVertexIndexIndex = 0; region.numberOfFaceVertexIndices = tri.size
    div.faces = [int(v) for v in tri.reshape(-1)]; div.regions = [region]; div.objects = [obj]
    region.numberOfBoneWeightPairsPerVertex = pairs
    obj.regionIndex = obj.materialReferenceIndex = 0

    def bound(b, lo, hi):
        for key, l, h in zip('xyz', lo, hi):
            setattr(b.minBorder, key, float(l)); setattr(b.maxBorder, key, float(h))
        b.radius = float(np.linalg.norm(np.maximum(np.abs(lo), np.abs(hi))))
    lo, hi = pos.min(0) - 0.1, pos.max(0) + 0.1
    bound(model.boundings, lo, hi)
    bound(div.msec[0].bounding.initValue, lo, hi); bound(div.msec[0].bounding.nullValue, lo, hi)
    mat = model.standardMaterials[0]; mat.name = 'AS' + name; mat.flags |= 8
    for key, value in mat.__dict__.items():
        if key.endswith('Layer'):
            for layer in value:
                layer.imagePath = ''
    mat.diffuseLayer[0].imagePath = TEX + 'marine.dds'; mat.diffuseLayer[0].flags |= 0xc
    mat.emissiveLayer[0].imagePath = TEX + 'marine_e.dds'; mat.emissiveLayer[0].flags |= 0xc
    mat.emisMult = 2.2
    model.standardMaterials = [mat]; model.materialReferences = model.materialReferences[:1]
    model.materialReferences[0].materialIndex = 0; model.modelName = 'AS' + name
    rig(model, m3, name, muzzle)
    path.parent.mkdir(parents=True, exist_ok=True)
    m3.saveAndInvalidateModel(model, str(path))
    check = m3.loadModel(str(path))
    assert len(check.divisions[0].faces) == tri.size and [s.name for s in check.sequences] == [s[0] for s in SEQUENCES]
    assert [a.name for a in check.attachmentPoints][:2] == ['Ref_Origin', 'Ref_Center'], [a.name for a in check.attachmentPoints]
    return path.read_bytes()


# ------------------------------------------------------------- textures
def textures():
    """(diffuse, emissive): one column per palette slot, with panel seams and wear on the armour."""
    from tools.shipkit import _noise
    w, h = 512, 256
    n = _noise(0, 24, 71, 4, (h, w)); fine = _noise(0, 4, 72, 2, (h, w))
    diffuse = np.zeros((h, w, 3)); emissive = np.zeros((h, w, 3))
    rows = np.arange(h)[:, None, None]
    for name, rgb in SLOTS.items():
        x0 = SLOT_INDEX[name] * 32
        col = np.array(rgb, float)[None, None]
        shade = 0.86 + 0.20 * n[:, x0:x0 + 32, None] + 0.08 * fine[:, x0:x0 + 32, None]
        if name in ('armor', 'armor2', 'pack'):
            # Panel seams every so often down the column, scuffed darker edges.
            seam = ((rows % 61) < 2) * 0.14
            shade = shade * (1 - seam)
        if name in ('gun', 'gun2'):
            shade = 0.8 + 0.35 * fine[:, x0:x0 + 32, None]
        diffuse[:, x0:x0 + 32] = col * shade
        if name in GLOW:
            emissive[:, x0:x0 + 32] = np.array(GLOW[name], float)[None, None] * (0.85 + 0.15 * n[:, x0:x0 + 32, None])
    to = lambda a: Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    return to(diffuse), to(emissive)


def stand_muzzle(muzzle):
    """Where a rest-pose muzzle sits in the ready stance (knees bent, chest breathing out), what the script fires from."""
    tp, tq = fk(pose('Stand', 0.0))[B['Torso']]
    return tp + rotmat(tq) @ (np.asarray(muzzle, float) - REST['Torso'])


def muzzles():
    """{gun: (forward, left, height)} of each model's muzzle, for the script."""
    return {name: tuple(round(float(v), 3) for v in stand_muzzle(geometry(name)[1])) for name, _, _ in GUNS}


def build():
    """{archive path: bytes}: every gun's model and the two shared textures."""
    from tools.shipkit import dds_bytes
    diffuse, emissive = textures()
    files = {}
    for name, _, _ in GUNS:
        mesh, muzzle = geometry(name)
        files['Base.SC2Assets/Derelict/Marine%s.m3' % name] = write_m3(mesh, 'Marine' + name, ROOT / ('dist/meshes/Marine%s.m3' % name), muzzle)
    for name, _, _ in GUNS:
        if name != 'Case':
            files['Base.SC2Assets/Derelict/Gun%s.m3' % name] = write_m3(gun_only(name), 'Gun' + name, ROOT / ('dist/meshes/Gun%s.m3' % name), (0, 0, 0))
    files['Base.SC2Assets/Derelict/marine.dds'] = dds_bytes(diffuse)
    files['Base.SC2Assets/Derelict/marine_e.dds'] = dds_bytes(emissive)
    return files


# -------------------------------------------------------------- preview
def render(model, diffuse, emissive, seq='Stand', t=0.0, yaw=-35.0, pitch=22.0, size=(300, 300), scale=260.0,
           centre=(0.2, 0.0, 0.48), tint=(1.0, 1.0, 1.0), muzzle=None):
    """A small CPU rasteriser of the written file (an asset preview, not an SC2 screenshot)."""
    pos, nrm, uv = _posed(model, seq, t)
    faces = np.asarray(model.divisions[0].faces).reshape(-1, 3)
    cy, sy, cp, sp = math.cos(math.radians(yaw)), math.sin(math.radians(yaw)), math.cos(math.radians(pitch)), math.sin(math.radians(pitch))
    cam = np.array([cy * cp, sy * cp, sp])
    right = np.cross((0, 0, 1), cam); right /= np.linalg.norm(right); up = np.cross(cam, right)
    light = np.array([0.4, -0.5, 0.9]); light /= np.linalg.norm(light)
    W, H = size
    centre = np.asarray(centre)
    proj = lambda p: np.column_stack(((p - centre) @ right * scale + W / 2, -(p - centre) @ up * scale + H * 0.5))
    px = proj(pos)
    depth = pos @ cam
    dif = np.asarray(diffuse.convert('RGB'), float) * np.asarray(tint)[None, None]
    emi = np.asarray(emissive.convert('RGB'), float)
    img = np.zeros((H, W, 3)); img[:] = (40, 44, 50)
    zbuf = np.full((H, W), -np.inf)
    for f in faces:
        tri = px[f]
        lo = np.maximum(np.floor(tri.min(0)).astype(int), 0); hi = np.minimum(np.ceil(tri.max(0)).astype(int), [W - 1, H - 1])
        if np.any(hi < lo):
            continue
        a, b, c = tri
        den = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
        if abs(den) < 1e-9:
            continue
        gx, gy = np.meshgrid(np.arange(lo[0], hi[0] + 1) + 0.5, np.arange(lo[1], hi[1] + 1) + 0.5)
        w0 = ((b[1] - c[1]) * (gx - c[0]) + (c[0] - b[0]) * (gy - c[1])) / den
        w1 = ((c[1] - a[1]) * (gx - c[0]) + (a[0] - c[0]) * (gy - c[1])) / den
        wts = np.stack((w0, w1, 1 - w0 - w1), -1)
        inside = wts.min(-1) >= -1e-6
        z = wts @ depth[f]
        zb = zbuf[lo[1]:hi[1] + 1, lo[0]:hi[0] + 1]
        mask = inside & (z > zb)
        if not mask.any():
            continue
        nn = wts @ nrm[f]; nn /= np.linalg.norm(nn, axis=-1, keepdims=True) + 1e-9
        nn = np.where((nn @ cam)[..., None] < 0, -nn, nn)
        shade = 0.30 + 0.80 * np.maximum(0, nn @ light) + 0.2 * np.maximum(0, nn @ cam) ** 8
        u, v = (wts @ uv[f]).transpose(2, 0, 1)
        ti = np.clip((u * 512).astype(int), 0, 511); tj = ((v % 1) * 256).astype(int) % 256
        col = dif[tj, ti] * shade[..., None] + emi[tj, ti] * 1.1
        img[lo[1]:hi[1] + 1, lo[0]:hi[0] + 1][mask] = col[mask]; zb[mask] = z[mask]
    out = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))
    if muzzle is not None:
        # The laser sight from the muzzle the script uses, to check it leaves the barrel.
        d = ImageDraw.Draw(out)
        a = proj(np.array([muzzle]))[0]; b = proj(np.array([np.asarray(muzzle) + (1.2, 0, 0)]))[0]
        d.line([tuple(a), tuple(b)], fill=(255, 40, 30), width=1)
    return out


def preview(out=ROOT / 'dist/marine-preview.png'):
    import m3
    diffuse, emissive = textures()
    tints = [(0.62, 0.72, 0.84), (0.86, 0.6, 0.52), (0.62, 0.74, 0.54), (0.86, 0.78, 0.56)]   # src/Marine.galaxy AS_SuitTint
    W, H = 300, 300
    names = [n for n, _, _ in GUNS]
    cols = 5
    rows = (len(names) + cols - 1) // cols + 1
    sheet = Image.new('RGB', (W * cols, (H + 22) * rows + 34), (10, 12, 16)); d = ImageDraw.Draw(sheet)
    d.text((12, 10), 'MARINES  /  one trooper per weapon family, CPU preview of the written files, red line = laser from the scripted muzzle',
           fill=(230, 190, 100))
    for k, name in enumerate(names):
        model = m3.loadModel(str(ROOT / ('dist/meshes/Marine%s.m3' % name)))
        _, muzzle = geometry(name)
        x, y = (k % cols) * W, (k // cols) * (H + 22) + 34
        sheet.paste(render(model, diffuse, emissive, 'Stand', 0.0, -50, 35, (W, H), tint=tints[k % 4], muzzle=stand_muzzle(muzzle)), (x, y))
        d.text((x + 8, y + H + 4), name, fill=(190, 205, 210))
    # The last row: the rifleman from the game camera (pitch 60), walking, and the melee swing.
    model = m3.loadModel(str(ROOT / 'dist/meshes/MarineRifle.m3'))
    y = (rows - 1) * (H + 22) + 34
    for k, (seq, t, yaw, pitch, label) in enumerate([('Stand', 0.0, 180, 60, 'game camera, aiming north'),
                                                      ('Walk', 0.0, -60, 20, 'Walk 0%'), ('Walk', 0.25, -60, 20, 'Walk 25%'),
                                                      ('Walk', 0.5, -60, 20, 'Walk 50%'), ('Attack', 0.5, -60, 25, 'melee swing')]):
        sheet.paste(render(model, diffuse, emissive, seq, t, yaw, pitch, (W, H)), (k * W, y))
        d.text((k * W + 8, y + H + 4), label, fill=(190, 205, 210))
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out)
    return out


def motion(out=ROOT / 'dist/marine-motion.png'):
    """Filmstrips of the gaits (eight frames a cycle) and the idle, to judge the motion: side-on and from the game camera."""
    import m3
    diffuse, emissive = textures()
    model = m3.loadModel(str(ROOT / 'dist/meshes/MarineRifle.m3'))
    W, H = 200, 220
    strips = [('Walk', -90, 8, 'Walk (run), side'), ('Walk', -40, 12, 'Walk, three-quarter'), ('Spell', 180, 60, 'Spell (strafe left), game camera'),
              ('Cover', -40, 15, 'Cover (strafe right)'), ('Work', -90, 8, 'Work (back-pedal), side'), ('Stand', -50, 20, 'Stand (idle)'),
              ('Death', -60, 25, 'Death')]
    sheet = Image.new('RGB', (W * 8, (H + 20) * len(strips)), (10, 12, 16)); d = ImageDraw.Draw(sheet)
    for r, (seq, yaw, pitch, label) in enumerate(strips):
        for k in range(8):
            img = render(model, diffuse, emissive, seq, k / 8, yaw, pitch, (W, H), scale=170.0, centre=(0.1, 0.0, 0.5))
            sheet.paste(img, (k * W, r * (H + 20) + 20))
        d.text((8, r * (H + 20) + 4), label, fill=(230, 190, 100))
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out)
    return out


if __name__ == '__main__':
    files = build()
    print({k: len(v) for k, v in files.items()})
    print(muzzles())
    print(preview())
    print(motion())
