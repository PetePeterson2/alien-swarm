"""The ripper: an original, animated alien mesh written as a native skinned M3.

A tall, six-limbed hunter: four splayed legs, two mantis scythes folded in
front of an elongated skull, a ridged abdomen and a three-segment tail ending
in a bone stinger. Rows of bioluminescent spots along its back and flanks are
an emissive layer, so it reads in the derelict's dark before a lamp or the
flashlight finds it.

Geometry is authored here as ellipsoids and swept tubes, every part rigidly
bound to one bone of a fifteen-bone rig. Stand, Walk, Attack and Death are
authored as bone tracks. The rig follows ../../Documents/Saboteur/tools/
runner_character.py (Tunnel Run's miners, proven in the client), which uses
the same retained crate container (tools/template/container.m3) and reader:
only its format and bind data are reused.

Everything is authored facing +X with Z up, in world units, and turned a quarter
turn when written: SC2 lays a unit model's -Y along the unit's facing (seen in
the client; tools/fx.py's +X meshes correct for it in script instead).

    py tools/alien.py         write dist/meshes/Ripper.m3 and dist/ripper-preview.png
"""
import copy, math, sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools/m3-reader'))
sys.path.insert(0, str(ROOT))
CONTAINER = ROOT / 'tools/template/container.m3'
TEX = 'Derelict\\'
NAME = 'Ripper'
# Authoring frame (+X forward) -> M3 frame (-Y forward): (x, y, z) -> (y, -x, z).
TURN = np.array([[0.0, 1.0, 0.0], [-1.0, 0.0, 0.0], [0.0, 0.0, 1.0]])

# ------------------------------------------------------------------ rig
# name, parent, absolute rest pivot. No bone carries a rest rotation.
BONES = [
    ('Root',      -1, (0.00, 0.00, 0.00)),
    ('Body',       0, (0.00, 0.00, 0.80)),
    ('Head',       1, (0.48, 0.00, 0.94)),
    ('Jaw',        2, (0.70, 0.00, 0.92)),
    ('ShoulderL',  1, (0.32, 0.20, 0.95)),
    ('BladeL',     4, (0.52, 0.34, 1.30)),
    ('ShoulderR',  1, (0.32, -0.20, 0.95)),
    ('BladeR',     6, (0.52, -0.34, 1.30)),
    ('LegFL',      1, (0.20, 0.17, 0.74)),
    ('LegFR',      1, (0.20, -0.17, 0.74)),
    ('LegBL',      1, (-0.22, 0.17, 0.74)),
    ('LegBR',      1, (-0.22, -0.17, 0.74)),
    ('Tail1',      1, (-0.58, 0.00, 0.86)),
    ('Tail2',     12, (-0.95, 0.00, 0.92)),
    ('Tail3',     13, (-1.28, 0.00, 1.02)),
]
B = {name: i for i, (name, _, _) in enumerate(BONES)}
LEGS = [('LegFL', 1, 0.0), ('LegFR', -1, math.pi), ('LegBL', 1, math.pi), ('LegBR', -1, 0.0)]   # bone, side, gait phase

# Palette: 16 columns of 32 pixels; each column is one material, mottled down its length.
SLOTS = {
    'carapace': (58, 50, 70), 'limb': (76, 66, 82), 'belly': (118, 78, 82), 'bone': (206, 196, 170),
    'blade': (150, 140, 124), 'teeth': (232, 228, 210), 'mouth': (140, 34, 46), 'glow': (150, 255, 110),
    'eye': (120, 255, 235), 'ridge': (30, 26, 36), 'vein': (96, 50, 110),
}
SLOT_INDEX = {k: i for i, k in enumerate(SLOTS)}
GLOW = {'glow': (110, 255, 70), 'eye': (90, 255, 220), 'vein': (36, 10, 46)}


def quat(axis, degrees):
    a = math.radians(degrees) * 0.5
    x, y, z = np.asarray(axis, float) / np.linalg.norm(axis)
    return np.array([x * math.sin(a), y * math.sin(a), z * math.sin(a), math.cos(a)])


def qmul(a, b):
    ax, ay, az, aw = a; bx, by, bz, bw = b
    return np.array([aw * bx + ax * bw + ay * bz - az * by, aw * by - ax * bz + ay * bw + az * bx,
                     aw * bz + ax * by - ay * bx + az * bw, aw * bw - ax * bx - ay * by - az * bz])


def qrot(*parts):
    """Compose (axis, degrees) rotations, applied first to last."""
    q = np.array([0.0, 0.0, 0.0, 1.0])
    for axis, deg in parts:
        q = qmul(quat(axis, deg), q)
    return q


def rotmat(q):
    x, y, z, w = np.asarray(q, float) / np.linalg.norm(q)
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                     [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                     [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])


# ------------------------------------------------------------- geometry
class Mesh:
    """Indexed, rigidly skinned triangles: one bone per part."""

    def __init__(self):
        self.pos, self.nrm, self.uv, self.bone, self.tri = [], [], [], [], []

    def add(self, pos, nrm, v, tri, slot, bone):
        base = len(self.pos)
        u = (SLOT_INDEX[slot] * 32 + 16) / 512.0
        self.pos.extend(pos); self.nrm.extend(nrm)
        self.uv.extend((u, vv) for vv in v)
        self.bone.extend([B[bone]] * len(pos))
        self.tri.extend((base + a, base + b, base + c) for a, b, c in tri)

    def ellipsoid(self, center, radii, slot, bone, pitch=0.0, yaw=0.0, sides=14, rings=10):
        """``pitch`` tips the long +X axis down (degrees, about Y); ``yaw`` turns it about Z."""
        m = rotmat(qrot(((0, 1, 0), pitch), ((0, 0, 1), yaw)))
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

    def sweep(self, path, width, thick=None, slot='limb', bone='Body', up=(0, 0, 1), sides=10):
        """A tube along ``path``; ``width`` and ``thick`` are per-point radii (flat blades when they differ).
        ``up`` picks the thickness axis: the cross-section is ``width`` across it and ``thick`` along it."""
        path = [np.asarray(p, float) for p in path]
        thick = width if thick is None else thick
        pos, nrm, v, tri = [], [], [], []
        length = 0.0
        for k, p in enumerate(path):
            t = path[min(k + 1, len(path) - 1)] - path[max(k - 1, 0)]; t /= np.linalg.norm(t)
            b = np.asarray(up, float) - np.dot(up, t) * t; b /= np.linalg.norm(b)
            n = np.cross(t, b)
            if k:
                length += np.linalg.norm(p - path[k - 1])
            rw, rt = max(width[k], 1e-4), max(thick[k], 1e-4)
            for i in range(sides + 1):
                a = math.tau * i / sides
                pos.append(p + math.cos(a) * rw * n + math.sin(a) * rt * b)
                d = math.cos(a) * n / rw + math.sin(a) * b / rt; nrm.append(d / np.linalg.norm(d))
                v.append(1.0 + length * 3.0)
        for k in range(len(path) - 1):
            for i in range(sides):
                a = k * (sides + 1) + i; c = a + sides + 1
                tri.extend([(a, c, c + 1), (a, c + 1, a + 1)])
        # Close blunt ends with a fan; pointed ends already meet.
        for k, sign in ((0, -1), (len(path) - 1, 1)):
            if width[k] > 1e-3:
                t = path[min(k + 1, len(path) - 1)] - path[max(k - 1, 0)]; t /= np.linalg.norm(t)
                centre = len(pos); pos.append(path[k]); nrm.append(t * sign); v.append(v[k * (sides + 1)])
                ring = k * (sides + 1)
                tri.extend((centre, ring + i, ring + i + 1) for i in range(sides))
        self.add(pos, nrm, v, tri, slot, bone)

    def cone(self, base, tip, radius, slot, bone, up=(0, 0, 1)):
        self.sweep([base, (np.asarray(base) * 0.4 + np.asarray(tip) * 0.6), tip], [radius, radius * 0.55, 0.0],
                   slot=slot, bone=bone, up=up, sides=7)


def _on_ellipsoid(center, radii, x, angle):
    """A point on an X-aligned ellipsoid's surface at ``x``, ``angle`` degrees round from +Y toward +Z."""
    c = np.asarray(center, float); r = np.asarray(radii, float)
    f = math.sqrt(max(0.0, 1 - ((x - c[0]) / r[0]) ** 2))
    a = math.radians(angle)
    return np.array([x, c[1] + r[1] * f * math.cos(a), c[2] + r[2] * f * math.sin(a)]), f


def geometry():
    m = Mesh()
    # Thorax, back plates and belly.
    thorax = ((0.12, 0, 0.82), (0.36, 0.22, 0.20))
    m.ellipsoid(*thorax, 'carapace', 'Body')
    for x, ry in ((0.30, 0.17), (0.09, 0.19), (-0.12, 0.18)):
        m.ellipsoid((x, 0, 0.93), (0.16, ry, 0.10), 'carapace', 'Body', pitch=-6)
        m.ellipsoid((x - 0.13, 0, 0.955), (0.025, ry * 0.8, 0.06), 'ridge', 'Body')
    m.ellipsoid((0.12, 0, 0.71), (0.30, 0.16, 0.10), 'belly', 'Body')
    # Abdomen with ridged segments.
    abdomen = ((-0.36, 0, 0.86), (0.30, 0.25, 0.23))
    m.ellipsoid(*abdomen, 'carapace', 'Body')
    for k in range(4):
        x = -0.17 - 0.12 * k
        _, f = _on_ellipsoid(*abdomen, x, 0)
        m.ellipsoid((x, 0, 0.86), (0.03, 0.25 * f * 1.07 + 0.005, 0.23 * f * 1.07 + 0.005), 'ridge', 'Body')
    # Bioluminescent spots: two rows down the flanks, a line along the spine.
    for k in range(5):
        x = -0.11 - 0.105 * k
        for side in (1, -1):
            p, _ = _on_ellipsoid(*abdomen, x + 0.05, 40 if side > 0 else 140)
            m.ellipsoid(p, (0.030, 0.030, 0.030), 'glow', 'Body', sides=8, rings=6)
    for x in (0.22, 0.0):
        p, _ = _on_ellipsoid((x, 0, 0.93), (0.16, 0.18, 0.10), x, 90)
        m.ellipsoid(p + (0, 0, 0.005), (0.035, 0.022, 0.02), 'glow', 'Body', sides=8, rings=6)
    # Dorsal spines, raked back.
    for x, h in ((0.30, 0.13), (0.09, 0.17), (-0.12, 0.16), (-0.33, 0.12), (-0.52, 0.09)):
        top = 1.02 if x > -0.25 else 0.86 + 0.23 * math.sqrt(max(0, 1 - ((x + 0.36) / 0.30) ** 2)) - 0.01
        m.cone((x, 0, top - 0.02), (x - h * 0.7, 0, top + h), 0.035, 'bone', 'Body', up=(0, 1, 0))
    # Neck.
    m.sweep([(0.34, 0, 0.86), (0.44, 0, 0.91), (0.54, 0, 0.95)], [0.10, 0.09, 0.08], slot='limb', bone='Head')

    # Skull: a long dome raked back over the neck, a crest, a narrow snout.
    m.ellipsoid((0.66, 0, 1.00), (0.25, 0.13, 0.11), 'carapace', 'Head', pitch=16)
    m.ellipsoid((0.46, 0, 1.11), (0.24, 0.085, 0.07), 'carapace', 'Head', pitch=24)
    m.ellipsoid((0.40, 0, 1.15), (0.14, 0.03, 0.05), 'ridge', 'Head', pitch=24)
    m.ellipsoid((0.84, 0, 0.945), (0.15, 0.09, 0.06), 'limb', 'Head', pitch=8)
    m.ellipsoid((0.83, 0, 0.905), (0.12, 0.072, 0.03), 'mouth', 'Head')
    for x, y, z in ((0.81, 0.083, 0.985), (0.745, 0.103, 1.015), (0.68, 0.113, 1.04)):
        for side in (1, -1):
            m.ellipsoid((x, side * y, z), (0.024, 0.02, 0.02), 'eye', 'Head', sides=8, rings=6)
    for k in range(6):
        x = 0.95 - 0.035 * k
        for side in (1, -1):
            y = side * (0.025 + 0.012 * k)
            m.cone((x, y, 0.925), (x + 0.008, y, 0.865), 0.012, 'teeth', 'Head')
    # Jaw: lower mandible, teeth and two tusks.
    m.ellipsoid((0.84, 0, 0.875), (0.15, 0.078, 0.035), 'limb', 'Jaw', pitch=4)
    for k in range(5):
        x = 0.93 - 0.04 * k
        for side in (1, -1):
            y = side * (0.022 + 0.012 * k)
            m.cone((x, y, 0.885), (x - 0.005, y, 0.93), 0.011, 'teeth', 'Jaw')
    for side in (1, -1):
        m.sweep([(0.86, side * 0.07, 0.89), (0.95, side * 0.11, 0.875), (1.03, side * 0.12, 0.84)], [0.022, 0.016, 0.0],
                slot='bone', bone='Jaw', sides=7)

    # Scythes: shoulder, upper arm, then a flat bone blade curling forward and down past the snout.
    for side, sh, bl in ((1, 'ShoulderL', 'BladeL'), (-1, 'ShoulderR', 'BladeR')):
        s = lambda x, y, z: (x, side * y, z)
        m.ellipsoid(s(0.32, 0.20, 0.95), (0.075, 0.075, 0.075), 'limb', sh)
        m.sweep([s(0.32, 0.20, 0.95), s(0.42, 0.28, 1.14), s(0.52, 0.34, 1.30)], [0.065, 0.055, 0.045], slot='limb', bone=sh)
        m.cone(s(0.47, 0.31, 1.22), s(0.36, 0.34, 1.36), 0.03, 'bone', sh)
        m.ellipsoid(s(0.52, 0.34, 1.30), (0.058, 0.058, 0.058), 'carapace', bl)
        m.sweep([s(0.52, 0.34, 1.30), s(0.62, 0.335, 1.30), s(0.70, 0.33, 1.28)], [0.05, 0.048, 0.045], slot='limb', bone=bl)
        blade = [s(0.66, 0.33, 1.29), s(0.80, 0.325, 1.255), s(0.92, 0.32, 1.17), s(1.03, 0.315, 1.04), s(1.10, 0.31, 0.90),
                 s(1.12, 0.305, 0.78), s(1.10, 0.30, 0.70)]
        m.sweep(blade, [0.065, 0.075, 0.07, 0.06, 0.045, 0.025, 0.0], [0.024, 0.022, 0.018, 0.015, 0.011, 0.007, 0.0],
                slot='bone', bone=bl, up=(0, 1, 0))
        m.sweep(blade[:5], [0.03, 0.035, 0.03, 0.025, 0.0], [0.03, 0.028, 0.024, 0.018, 0.0], slot='blade', bone=bl, up=(0, 1, 0))

    # Legs: spider-like, knees high and out, each rigid on its hip.
    for bone, side, _ in LEGS:
        hx = BONES[B[bone]][2][0]; fwd = 1 if hx > 0 else -1
        s = lambda x, y, z: (hx + fwd * x, side * y, z)
        hip, knee, ankle, foot = s(0, 0.17, 0.74), s(0.12, 0.50, 0.98), s(0.25, 0.68, 0.26), s(0.29, 0.73, 0.0)
        m.ellipsoid(hip, (0.07, 0.07, 0.07), 'limb', bone)
        m.sweep([hip, knee], [0.06, 0.05], slot='limb', bone=bone)
        m.ellipsoid(knee, (0.06, 0.06, 0.06), 'carapace', bone)
        m.cone(knee, (np.asarray(knee) + (fwd * -0.05, side * 0.05, 0.12)), 0.03, 'bone', bone)
        mid = (np.asarray(knee) + np.asarray(ankle)) / 2 + (0, side * 0.03, 0)
        m.sweep([knee, mid, ankle], [0.05, 0.042, 0.032], slot='carapace', bone=bone)
        m.sweep([ankle, foot], [0.032, 0.0], slot='bone', bone=bone, sides=7)

    # Tail: three segments with ridges and glow, ending in a bone stinger.
    segs = [('Tail1', (-0.58, 0, 0.86), (-0.95, 0, 0.92), 0.13, 0.095), ('Tail2', (-0.95, 0, 0.92), (-1.28, 0, 1.02), 0.095, 0.07),
            ('Tail3', (-1.28, 0, 1.02), (-1.55, 0, 1.17), 0.07, 0.045)]
    for bone, a, b, ra, rb in segs:
        a = np.asarray(a); b = np.asarray(b)
        m.ellipsoid(a, (ra, ra, ra), 'carapace', bone)
        m.sweep([a, (a + b) / 2, b], [ra, (ra + rb) / 2, rb], slot='carapace', bone=bone)
        for t in (0.35, 0.75):
            p = a + (b - a) * t; r = ra + (rb - ra) * t
            m.sweep([p - (b - a) * 0.03, p + (b - a) * 0.03], [r * 1.12, r * 1.12], slot='ridge', bone=bone)
            m.ellipsoid(p + (0, 0, r * 0.95), (0.022, 0.022, 0.018), 'glow', bone, sides=8, rings=6)
    m.ellipsoid((-1.55, 0, 1.17), (0.05, 0.05, 0.05), 'carapace', 'Tail3')
    m.sweep([(-1.55, 0, 1.17), (-1.66, 0, 1.27), (-1.73, 0, 1.40), (-1.72, 0, 1.53)], [0.06, 0.055, 0.035, 0.0],
            [0.022, 0.02, 0.012, 0.0], slot='bone', bone='Tail3', up=(0, 1, 0))
    m.ellipsoid((-1.6, 0, 1.22), (0.03, 0.03, 0.03), 'glow', 'Tail3', sides=8, rings=6)
    return m


# ----------------------------------------------------------- animation
def _knots(t, knots):
    """Piecewise smooth interpolation through (t, value) knots."""
    for (a, av), (b, bv) in zip(knots, knots[1:]):
        if a <= t <= b:
            f = (t - a) / (b - a) if b > a else 1.0
            f = f * f * (3 - 2 * f)
            return av + (bv - av) * f
    return knots[-1][1]


def pose(name, t):
    """Bone index -> (location offset, rotation quaternion) at ``t`` in [0, 1] through sequence ``name``."""
    out = {}
    ph = t * math.tau
    X, Y, Z = (1, 0, 0), (0, 1, 0), (0, 0, 1)

    def put(bone, loc=(0, 0, 0), *rot):
        out[B[bone]] = (np.asarray(loc, float), qrot(*rot))

    if name == 'Stand':
        put('Body', (0, 0, 0.014 * math.sin(ph)), (Y, 1.5 * math.sin(ph)))
        put('Head', (0, 0, 0), (Z, 7 * math.sin(ph + 0.6)), (Y, -3 * math.sin(ph)))
        put('Jaw', (0, 0, 0), (Y, 6 + 6 * math.sin(ph * 2)))
        for sh, bl, side in (('ShoulderL', 'BladeL', 1), ('ShoulderR', 'BladeR', -1)):
            put(sh, (0, 0, 0), (Y, -3 * math.sin(ph + side)))
            put(bl, (0, 0, 0), (Y, 4 * math.sin(ph + side + 0.5)))
        for bone, side, _ in LEGS:
            put(bone, (0, 0, 0), (X, side * 1.2 * math.sin(ph)))
        for k, bone in enumerate(('Tail1', 'Tail2', 'Tail3')):
            put(bone, (0, 0, 0), (Z, (6 + 3 * k) * math.sin(ph - k * 0.8)), (Y, -3 * math.sin(ph - k * 0.8)))
    elif name == 'Walk':
        put('Body', (0, 0, 0.022 * abs(math.sin(ph))), (X, 3 * math.sin(ph)), (Z, 3 * math.sin(ph)))
        put('Head', (0, 0, 0), (Z, -3 * math.sin(ph)), (Y, 2 * math.sin(ph * 2)))
        put('Jaw', (0, 0, 0), (Y, 8))
        for sh, bl in (('ShoulderL', 'BladeL'), ('ShoulderR', 'BladeR')):
            put(sh, (0, 0, 0), (Y, -6 + 3 * math.sin(ph * 2)))
            put(bl, (0, 0, 0), (Y, -4 + 3 * math.sin(ph * 2 + 0.7)))
        for bone, side, phase in LEGS:
            p = ph + phase
            swing = 30 * math.sin(p); lift = 16 * max(0.0, math.cos(p))
            put(bone, (0, 0, 0), (X, side * lift), (Z, -side * swing))
        for k, bone in enumerate(('Tail1', 'Tail2', 'Tail3')):
            put(bone, (0, 0, 0), (Z, (7 + 4 * k) * math.sin(ph - k * 0.9)))
    elif name == 'Attack':
        lunge = _knots(t, [(0, 0), (0.3, -0.06), (0.5, 0.16), (0.75, 0.10), (1, 0)])
        put('Body', (lunge, 0, _knots(t, [(0, 0), (0.3, 0.05), (0.5, -0.04), (1, 0)])), (Y, _knots(t, [(0, 0), (0.3, -10), (0.5, 14), (1, 0)])))
        put('Head', (0, 0, 0), (Y, _knots(t, [(0, 0), (0.3, -18), (0.5, 12), (1, 0)])))
        put('Jaw', (0, 0, 0), (Y, _knots(t, [(0, 4), (0.25, 38), (0.55, 32), (0.8, 4), (1, 4)])))
        for sh, bl, lag in (('ShoulderL', 'BladeL', 0.0), ('ShoulderR', 'BladeR', 0.04)):
            put(sh, (0, 0, 0), (Y, _knots(t, [(0, 0), (0.3 + lag, -42), (0.5 + lag, 30), (0.8, 10), (1, 0)])))
            put(bl, (0, 0, 0), (Y, _knots(t, [(0, 0), (0.3 + lag, -70), (0.5 + lag, 55), (0.8, 15), (1, 0)])))
        for bone, side, _ in LEGS:
            put(bone, (0, 0, 0), (X, side * _knots(t, [(0, 0), (0.3, -6), (0.5, 8), (1, 0)])))
        for k, bone in enumerate(('Tail1', 'Tail2', 'Tail3')):
            put(bone, (0, 0, 0), (Y, _knots(t, [(0, 0), (0.3, -8 - 6 * k), (0.5, 10 + 4 * k), (1, 0)])))
    elif name == 'Death':
        # Legs give, the body drops onto its belly with a roll, scythes fold, a last twitch.
        f = _knots(t, [(0, 0), (0.12, -0.15), (0.45, 1.0), (0.55, 0.93), (0.65, 1.0), (1, 1)])
        tw = math.sin(t * 40) * max(0.0, 1 - abs(t - 0.85) / 0.1) * 4
        put('Body', (0, 0, -0.52 * f), (Y, 6 * f), (X, 11 * f))
        put('Head', (0, 0, 0), (Y, 26 * f + tw), (Z, -14 * f))
        put('Jaw', (0, 0, 0), (Y, 34 * f))
        for sh, bl, side in (('ShoulderL', 'BladeL', 1), ('ShoulderR', 'BladeR', -1)):
            put(sh, (0, 0, 0), (Y, 48 * f), (X, side * 14 * f))
            put(bl, (0, 0, 0), (Y, 40 * f - tw * 2))
        for bone, side, _ in LEGS:
            put(bone, (0, 0, 0), (X, side * (62 * f + tw)), (Z, side * 8 * f))
        for k, bone in enumerate(('Tail1', 'Tail2', 'Tail3')):
            put(bone, (0, 0, 0), (Y, (16 - 4 * k) * f), (Z, (14 + 8 * k) * f + tw))
    return out


# Walk's speed is the feet's ground speed (a 30 degree swing on a 0.56 reach, half a cycle):
# SC2 plays it faster as the unit moves faster, so the feet do not skate.
WALK_SPEED = 1.75
SEQUENCES = [('Stand', 2400, 0.0, False), ('Walk', 640, WALK_SPEED, False), ('Attack', 500, 0.0, True), ('Death', 1400, 0.0, True)]
ANIMATED = {'location': {B['Body']}, 'rotation': set(range(1, len(BONES)))}


# ------------------------------------------------------------------ M3
def _clone(value):
    if isinstance(value, list):
        return [_clone(v) for v in value]
    if hasattr(value, 'structureDescription'):
        result = value.structureDescription.createInstance()
        for key, field in vars(value).items():
            if key != 'structureDescription':
                setattr(result, key, _clone(field))
        return result
    return copy.copy(value)


def _fixed8(v):
    return np.clip(np.rint((np.asarray(v, float) + 1) / 2 * 255), 0, 255).astype(np.uint8)


def rig(model, m3):
    source = _clone(model.bones[0]); inverse = _clone(model.absoluteInverseBoneRestPositions[0])
    bones, inverses = [], []
    for i, (name, parent, pivot) in enumerate(BONES):
        bone = _clone(source); bone.name = NAME + '_' + name; bone.parent = parent
        local = TURN @ (np.asarray(pivot) - (np.asarray(BONES[parent][2]) if parent >= 0 else 0))
        for field in ('location', 'rotation', 'scale'):
            ref = getattr(bone, field)
            ref.header.animId = 0x12000000 + i * 16 + {'location': 1, 'rotation': 2, 'scale': 3}[field]
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
    region = model.divisions[0].regions[0]
    region.numberOfBones = region.numberOfBoneLookupIndices = len(BONES); region.firstBoneLookupIndex = 0; region.rootBoneIndex = 0
    model.sequences, model.sequenceTransformationCollections, model.sequenceTransformationGroups, model.sts = [], [], [], []
    steps = 24
    for si, (name, duration, speed, once) in enumerate(SEQUENCES):
        seq = _clone(seq_t); seq.name = name; seq.animStartInMS = 0; seq.animEndInMS = duration
        seq.movementSpeed = speed; seq.frequency = 100; seq.flags = 1 if once else 0
        # Bounds cover the whole sweep of the limbs, the lunge and the collapse.
        b = seq.boundingSphere
        b.minBorder.x, b.minBorder.y, b.minBorder.z = -2.0, -1.1, -0.3
        b.maxBorder.x, b.maxBorder.y, b.maxBorder.z = 1.5, 1.1, 1.8
        b.radius = 2.6
        stc = _clone(stc_t); stc.name = name + '_full'; stc.stsIndex = stc.stsIndexCopy = si
        for key, value in vars(stc).items():
            if isinstance(value, list):
                setattr(stc, key, [])
        frames = [round(duration * k / steps) for k in range(steps + 1)]
        poses = [pose(name, k / steps) for k in range(steps + 1)]
        ids, refs = [], []
        for field in ('location', 'rotation'):
            for bi in sorted(ANIMATED[field]):
                ids.append(getattr(bones[bi], field).header.animId)
                track = m3.structures['SD3V' if field == 'location' else 'SD4Q'].getVersion(0).createInstance()
                track.frames = frames; track.flags = 1; track.fend = duration; track.keys = []
                for p in poses:
                    loc, rot = p.get(bi, (np.zeros(3), np.array([0.0, 0.0, 0.0, 1.0])))
                    value = _clone(getattr(bones[bi], field).initValue)
                    if field == 'location':
                        loc = TURN @ loc
                        value.x, value.y, value.z = (float(getattr(value, k) + loc[j]) for j, k in enumerate('xyz'))
                    else:
                        # Turning the frame turns each rotation's axis; its angle is unchanged.
                        value.x, value.y, value.z = (float(c) for c in TURN @ rot[:3]); value.w = float(rot[3])
                    track.keys.append(value)
                if field == 'location':
                    refs.append((2 << 16) | len(stc.sd3v)); stc.sd3v.append(track)
                else:
                    refs.append((3 << 16) | len(stc.sd4q)); stc.sd4q.append(track)
        stc.animIds = ids; stc.animRefs = refs
        stg = _clone(stg_t); stg.name = name; stg.stcIndices = [si]
        sts = _clone(sts_t); sts.animIds = ids[:]
        model.sequences.append(seq); model.sequenceTransformationCollections.append(stc)
        model.sequenceTransformationGroups.append(stg); model.sts.append(sts)


def write_m3(mesh, path):
    import m3
    model = m3.loadModel(str(CONTAINER))
    pos = np.asarray(np.asarray(mesh.pos) @ TURN.T, '<f4'); n = len(pos)
    tri = np.asarray(mesh.tri, int)
    assert 0 < n <= 65535 and tri.max() < n, n
    uv = np.asarray(mesh.uv, float)
    assert np.abs(uv).max() < 15.9
    vertex = np.zeros((n, 32), np.uint8)
    vertex[:, 0:12] = pos.view(np.uint8).reshape(n, 12)
    vertex[:, 12] = 255
    vertex[:, 16] = np.asarray(mesh.bone, np.uint8)
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
    obj.regionIndex = obj.materialReferenceIndex = 0

    def bound(b, lo, hi):
        for key, l, h in zip('xyz', lo, hi):
            setattr(b.minBorder, key, float(l)); setattr(b.maxBorder, key, float(h))
        b.radius = float(np.linalg.norm(np.maximum(np.abs(lo), np.abs(hi))))
    lo, hi = pos.min(0) - 0.1, pos.max(0) + 0.1
    bound(model.boundings, lo, hi)
    bound(div.msec[0].bounding.initValue, lo, hi); bound(div.msec[0].bounding.nullValue, lo, hi)
    mat = model.standardMaterials[0]; mat.name = 'AS' + NAME; mat.flags |= 8
    for key, value in mat.__dict__.items():
        if key.endswith('Layer'):
            for layer in value:
                layer.imagePath = ''
    mat.diffuseLayer[0].imagePath = TEX + 'ripper.dds'; mat.diffuseLayer[0].flags |= 0xc
    mat.emissiveLayer[0].imagePath = TEX + 'ripper_e.dds'; mat.emissiveLayer[0].flags |= 0xc
    mat.emisMult = 2.0
    model.standardMaterials = [mat]; model.materialReferences = model.materialReferences[:1]
    model.materialReferences[0].materialIndex = 0; model.modelName = 'AS' + NAME
    rig(model, m3)
    path.parent.mkdir(parents=True, exist_ok=True)
    m3.saveAndInvalidateModel(model, str(path))
    check = m3.loadModel(str(path))
    assert len(check.divisions[0].faces) == tri.size and [s.name for s in check.sequences] == [s[0] for s in SEQUENCES]
    return path.read_bytes()


# ------------------------------------------------------------- textures
def textures():
    """(diffuse, emissive): one mottled column per palette slot."""
    from tools.shipkit import _noise
    w, h = 512, 256
    n = _noise(0, 24, 31, 4, (h, w)); fine = _noise(0, 4, 32, 2, (h, w))
    diffuse = np.zeros((h, w, 3)); emissive = np.zeros((h, w, 3))
    for name, rgb in SLOTS.items():
        x0 = SLOT_INDEX[name] * 32
        col = np.array(rgb, float)[None, None]
        shade = 0.72 + 0.42 * n[:, x0:x0 + 32, None] + 0.12 * fine[:, x0:x0 + 32, None]
        if name in ('carapace', 'limb', 'ridge'):
            # Chitin: faint bands and a sickly purple sheen in the cracks.
            band = (np.sin(np.arange(h) / h * math.tau * 6)[:, None, None] > 0.8) * 0.18
            col = col * (1 - band) + np.array((70, 30, 80))[None, None] * band
        diffuse[:, x0:x0 + 32] = col * shade
        if name in GLOW:
            pulse = 0.75 + 0.25 * n[:, x0:x0 + 32, None]
            emissive[:, x0:x0 + 32] = np.array(GLOW[name], float)[None, None] * pulse
    to = lambda a: Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    return to(diffuse), to(emissive)


def build():
    """{archive path: bytes}: the mesh and its two textures."""
    from tools.shipkit import dds_bytes
    diffuse, emissive = textures()
    mesh = geometry()
    return {'Base.SC2Assets/Derelict/Ripper.m3': write_m3(mesh, ROOT / 'dist/meshes/Ripper.m3'),
            'Base.SC2Assets/Derelict/ripper.dds': dds_bytes(diffuse),
            'Base.SC2Assets/Derelict/ripper_e.dds': dds_bytes(emissive)}


# -------------------------------------------------------------- preview
def _posed(model, seq_name, t):
    """World positions and normals of every vertex, read back from the written M3."""
    import m3
    seq = next(s for s in model.sequences if s.name == seq_name)
    stc = next(s for s in model.sequenceTransformationCollections if s.name == seq_name + '_full')
    time = t * seq.animEndInMS
    tracks = {}
    for aid, ref in zip(stc.animIds, stc.animRefs):
        track = (stc.sd3v if ref >> 16 == 2 else stc.sd4q)[ref & 0xffff]
        size = 4 if ref >> 16 == 3 else 3
        keys = [np.array([getattr(k, c) for c in 'xyzw'[:size]]) for k in track.keys]
        i = max(1, min(len(track.frames) - 1, int(np.searchsorted(track.frames, time))))
        f = (time - track.frames[i - 1]) / max(1, track.frames[i] - track.frames[i - 1])
        tracks[aid] = keys[i - 1] * (1 - f) + keys[i] * f
    mats = []
    for bone in model.bones:
        loc = tracks.get(bone.location.header.animId, np.array([getattr(bone.location.initValue, c) for c in 'xyz']))
        q = tracks.get(bone.rotation.header.animId, np.array([getattr(bone.rotation.initValue, c) for c in 'xyzw']))
        mat = np.eye(4); mat[:3, :3] = rotmat(q); mat[:3, 3] = loc
        mats.append(mats[bone.parent] @ mat if bone.parent >= 0 else mat)
    skin = []
    for mat, rest in zip(mats, model.absoluteInverseBoneRestPositions):
        inv = np.array([[getattr(getattr(rest.matrix, r), c) for c in 'xyzw'] for r in 'xyzw']).T
        skin.append(mat @ inv)
    raw = np.frombuffer(bytes(model.vertices), np.uint8).reshape(-1, 32)
    pos = raw[:, 0:12].copy().view('<f4').astype(float)
    nrm = raw[:, 20:23].astype(float) / 255 * 2 - 1
    uv = raw[:, 24:28].copy().view('<i2').astype(float) / 2048
    bone = np.asarray(model.boneLookup)[raw[:, 16]]
    out_p = np.zeros_like(pos); out_n = np.zeros_like(nrm)
    for b in np.unique(bone):
        sel = bone == b
        out_p[sel] = pos[sel] @ skin[b][:3, :3].T + skin[b][:3, 3]
        out_n[sel] = nrm[sel] @ skin[b][:3, :3].T
    return out_p @ TURN, (out_n / np.linalg.norm(out_n, axis=1, keepdims=True)) @ TURN, uv


def render(model, diffuse, emissive, seq='Stand', t=0.0, yaw=-35.0, pitch=22.0, size=(420, 380), scale=105.0):
    """A small CPU rasteriser: an asset preview, not an SC2 screenshot."""
    pos, nrm, uv = _posed(model, seq, t)
    faces = np.asarray(model.divisions[0].faces).reshape(-1, 3)
    cy, sy, cp, sp = math.cos(math.radians(yaw)), math.sin(math.radians(yaw)), math.cos(math.radians(pitch)), math.sin(math.radians(pitch))
    cam = np.array([cy * cp, sy * cp, sp])
    right = np.cross((0, 0, 1), cam); right /= np.linalg.norm(right); up = np.cross(cam, right)
    light = np.array([0.5, -0.6, 0.9]); light /= np.linalg.norm(light)
    W, H = size
    centre = np.array([-0.2, 0.0, 0.7])
    px = np.column_stack(((pos - centre) @ right * scale + W / 2, -(pos - centre) @ up * scale + H * 0.55))
    depth = pos @ cam
    dif = np.asarray(diffuse.convert('RGB'), float); emi = np.asarray(emissive.convert('RGB'), float)
    img = np.zeros((H, W, 3)); img[:] = (14, 18, 24)
    zbuf = np.full((H, W), -np.inf)
    # Floor shadow ellipse for scale.
    yy, xx = np.mgrid[0:H, 0:W]
    floor = (((xx - W / 2) / (scale * 0.9)) ** 2 + ((yy - (H * 0.55 + 0.6 * scale * up[2])) / (scale * 0.9 * sp + 1)) ** 2) < 1
    img[floor] = (8, 10, 14)
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
        n = wts @ nrm[f]; n /= np.linalg.norm(n, axis=-1, keepdims=True) + 1e-9
        n = np.where((n @ cam)[..., None] < 0, -n, n)
        shade = 0.28 + 0.85 * np.maximum(0, n @ light) + 0.25 * np.maximum(0, n @ cam) ** 8
        u, v = (wts @ uv[f]).transpose(2, 0, 1)
        ti = np.clip((u * 512).astype(int), 0, 511); tj = ((v % 1) * 256).astype(int) % 256
        col = dif[tj, ti] * shade[..., None] + emi[tj, ti] * 1.2
        img[lo[1]:hi[1] + 1, lo[0]:hi[0] + 1][mask] = col[mask]; zb[mask] = z[mask]
    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))


def preview(out=ROOT / 'dist/ripper-preview.png'):
    import m3
    from PIL import ImageDraw
    model = m3.loadModel(str(ROOT / 'dist/meshes/Ripper.m3'))
    diffuse, emissive = textures()
    shots = [('Stand', 0.0, -35, 22, 'Stand  3/4 front'), ('Stand', 0.25, 90, 8, 'Stand  side'), ('Stand', 0.5, -150, 30, 'Stand  rear'),
             ('Stand', 0.0, 0, 70, 'top-down (game camera)'), ('Walk', 0.0, -40, 18, 'Walk  0%'), ('Walk', 0.25, -40, 18, 'Walk  25%'),
             ('Walk', 0.5, -40, 18, 'Walk  50%'), ('Walk', 0.75, -40, 18, 'Walk  75%'), ('Attack', 0.3, 80, 10, 'Attack  wind-up'),
             ('Attack', 0.52, 80, 10, 'Attack  slash'), ('Death', 0.3, -40, 25, 'Death  falling'), ('Death', 1.0, -40, 25, 'Death  final')]
    W, H = 420, 380
    sheet = Image.new('RGB', (W * 4, (H + 26) * 3 + 40), (10, 12, 16)); d = ImageDraw.Draw(sheet)
    d.text((14, 12), 'RIPPER  /  original M3, %d bones, %d triangles  /  CPU preview of the written file' % (len(model.bones), len(model.divisions[0].faces) // 3),
           fill=(230, 190, 100))
    for k, (seq, t, yaw, pitch, label) in enumerate(shots):
        x, y = (k % 4) * W, (k // 4) * (H + 26) + 40
        sheet.paste(render(model, diffuse, emissive, seq, t, yaw, pitch, (W, H)), (x, y))
        d.text((x + 10, y + H + 6), label, fill=(190, 205, 210))
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out)
    return out


if __name__ == '__main__':
    files = build()
    print({k: len(v) for k, v in files.items()})
    print(preview())
