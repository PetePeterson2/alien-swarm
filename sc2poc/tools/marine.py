"""The marines: an original armoured trooper holding a real gun, after Alien Swarm's squad.

Alien Swarm's marines are bulky armoured suits with a backpack and antenna, a
helmet with glowing eye slits, and the gun held at the hip in both hands, its
barrel along the aim with the laser sight leaving the muzzle. The stock SC2
marine carried its own rifle across its chest whatever the weapon, and shots
left a point in front of it; here every weapon family is its own model (the
same trooper, a different gun), swapped in as the marine changes weapons
(src/Marine.galaxy AS_GunModel), and the script fires every round, tracer,
flame and laser from that gun's muzzle (MUZZLE below, written into the script
as AS_GunMuzzle by build.py).

Built like tools/alien.py's ripper (proven in the client): ellipsoids, swept
tubes and boxes, each rigidly bound to one bone of a small rig, written as a
native skinned M3 in the retained crate container. The upper body, arms and
gun ride one bone (Torso) so the gun holds the aim line while the legs run.
The armour is pale so the script can tint each squad member's suit
(SetTintColor), as Alien Swarm's marines each wear their own colour.

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
from tools.alien import qrot, rotmat, _knots, _clone, _fixed8, _posed, TURN, CONTAINER   # noqa: E402

TEX = 'Derelict\\'

# ------------------------------------------------------------------ rig
BONES = [
    ('Root',   -1, (0.00, 0.00, 0.00)),
    ('Pelvis',  0, (0.00, 0.00, 0.44)),
    ('Torso',   1, (0.00, 0.00, 0.50)),
    ('Head',    2, (0.01, 0.00, 0.76)),
    ('ThighL',  1, (0.00, 0.085, 0.43)),
    ('ShinL',   4, (0.01, 0.085, 0.25)),
    ('ThighR',  1, (0.00, -0.085, 0.43)),
    ('ShinR',   6, (0.01, -0.085, 0.25)),
    ('Antenna', 2, (-0.17, 0.07, 0.80)),
]
B = {name: i for i, (name, _, _) in enumerate(BONES)}

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


class Mesh:
    """Indexed, rigidly skinned triangles: one bone per part (tools/alien.py's, with boxes)."""

    def __init__(self):
        self.pos, self.nrm, self.uv, self.bone, self.tri = [], [], [], [], []

    def add(self, pos, nrm, v, tri, slot, bone):
        base = len(self.pos)
        u = (SLOT_INDEX[slot] * 32 + 16) / 512.0
        self.pos.extend(np.asarray(p, float) for p in pos); self.nrm.extend(np.asarray(n, float) for n in nrm)
        self.uv.extend((u, vv) for vv in v)
        self.bone.extend([B[bone]] * len(pos))
        self.tri.extend((base + a, base + b, base + c) for a, b, c in tri)

    def ellipsoid(self, center, radii, slot, bone, pitch=0.0, yaw=0.0, roll=0.0, sides=12, rings=8):
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

    def box(self, center, size, slot, bone, pitch=0.0, yaw=0.0, roll=0.0, taper=1.0):
        """A flat-shaded box; ``taper`` shrinks its +X end (a wedge for gun stocks and boots)."""
        m = rotmat(qrot(((1, 0, 0), roll), ((0, 1, 0), pitch), ((0, 0, 1), yaw)))
        c = np.asarray(center, float); h = np.asarray(size, float) / 2
        pos, nrm, v, tri = [], [], [], []
        corner = lambda sx, sy, sz: c + m @ np.array([sx * h[0], sy * h[1] * (taper if sx > 0 else 1), sz * h[2] * (taper if sx > 0 else 1)])
        for axis in range(3):
            for sign in (-1, 1):
                n = np.zeros(3); n[axis] = sign
                o = [a for a in range(3) if a != axis]
                quad = []
                for su, sv in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
                    s = np.zeros(3); s[axis] = sign; s[o[0]] = su; s[o[1]] = sv
                    quad.append(corner(*s))
                base = len(pos)
                fn = np.cross(quad[1] - quad[0], quad[2] - quad[0]); fn /= np.linalg.norm(fn) + 1e-12
                want = m @ n
                if np.dot(fn, want) < 0:
                    quad = quad[::-1]
                    fn = -fn
                pos.extend(quad); nrm.extend([want] * 4)
                v.extend([1.0 + 0.3 * k + (c[0] + c[2]) for k in range(4)])
                tri.extend([(base, base + 1, base + 2), (base, base + 2, base + 3)])
        self.add(pos, nrm, v, tri, slot, bone)

    def tube(self, a, b, r0, r1=None, slot='gun', bone='Torso', sides=8, caps=True):
        """A straight cylinder (or cone frustum) from a to b."""
        a = np.asarray(a, float); b = np.asarray(b, float); r1 = r0 if r1 is None else r1
        t = b - a; length = np.linalg.norm(t); t /= length
        up = np.array([0, 0, 1.0]) if abs(t[2]) < 0.9 else np.array([1.0, 0, 0])
        n1 = np.cross(t, up); n1 /= np.linalg.norm(n1); n2 = np.cross(t, n1)
        pos, nrm, v, tri = [], [], [], []
        for k, (p, r) in enumerate(((a, r0), (b, r1))):
            for i in range(sides + 1):
                ang = math.tau * i / sides
                d = math.cos(ang) * n1 + math.sin(ang) * n2
                pos.append(p + d * r); nrm.append(d); v.append(1.0 + k * length * 3)
        for i in range(sides):
            tri.extend([(i, sides + 1 + i, sides + 2 + i), (i, sides + 2 + i, i + 1)])
        if caps:
            for p, sign, ring in ((a, -1, 0), (b, 1, sides + 1)):
                centre = len(pos); pos.append(p); nrm.append(t * sign); v.append(1.0)
                rim = len(pos)
                for i in range(sides + 1):
                    pos.append(pos[ring + i]); nrm.append(t * sign); v.append(1.0)
                for i in range(sides):
                    tri.append((centre, rim + i + 1, rim + i) if sign > 0 else (centre, rim + i, rim + i + 1))
        self.add(pos, nrm, v, tri, slot, bone)

    def limb(self, a, b, r0, r1, slot, bone, sides=8):
        """A limb segment with rounded joints at both ends."""
        self.tube(a, b, r0, r1, slot, bone, sides, caps=False)
        self.ellipsoid(a, (r0, r0, r0), slot, bone, sides=sides, rings=5)
        self.ellipsoid(b, (r1, r1, r1), slot, bone, sides=sides, rings=5)


# --------------------------------------------------------------- the body
GUN_Y = -0.075        # the gun rides at the right hip
GUN_Z = 0.56          # barrel height above the deck


def body(m, grip, fore, twohanded=True):
    """The trooper: ``grip`` the right hand on the pistol grip, ``fore`` the left hand on the foregrip."""
    # Boots and shins (each leg rigid on its two bones).
    for side, thigh, shin in ((1, 'ThighL', 'ShinL'), (-1, 'ThighR', 'ShinR')):
        y = side * 0.085
        m.box((0.035, y, 0.04), (0.17, 0.085, 0.08), 'joint', shin, taper=0.8)
        m.box((0.05, y, 0.075), (0.11, 0.075, 0.03), 'armor2', shin)
        m.limb((0.0, y, 0.08), (0.01, y, 0.25), 0.042, 0.046, 'suit', shin)
        m.box((0.035, y, 0.16), (0.05, 0.075, 0.15), 'armor', shin, pitch=-4)        # shin plate
        m.ellipsoid((0.05, y, 0.255), (0.04, 0.045, 0.045), 'armor2', shin)          # knee pad
        m.limb((0.01, y, 0.25), (0.0, y, 0.43), 0.05, 0.06, 'suit', thigh)
        m.box((0.02, y + side * 0.018, 0.35), (0.09, 0.05, 0.13), 'armor', thigh)    # thigh plate
    # Hips and belt.
    m.box((0.0, 0.0, 0.44), (0.15, 0.21, 0.09), 'suit', 'Pelvis')
    m.box((0.0, 0.0, 0.47), (0.16, 0.225, 0.035), 'joint', 'Pelvis')
    m.box((0.075, 0.0, 0.43), (0.03, 0.11, 0.08), 'armor2', 'Pelvis')               # groin plate
    for side in (1, -1):
        m.box((0.0, side * 0.12, 0.43), (0.08, 0.03, 0.09), 'armor2', 'Pelvis')      # hip plates
    # Torso: a bulky cuirass, a trimmed chest plate, the abdomen.
    m.ellipsoid((0.0, 0.0, 0.55), (0.10, 0.12, 0.08), 'suit', 'Torso')
    m.ellipsoid((0.0, 0.0, 0.645), (0.12, 0.15, 0.10), 'armor', 'Torso')
    m.box((0.075, 0.0, 0.645), (0.06, 0.20, 0.13), 'armor', 'Torso', pitch=-8)
    m.box((0.103, 0.0, 0.60), (0.012, 0.15, 0.022), 'trim', 'Torso', pitch=-8)
    m.box((0.104, 0.05, 0.665), (0.008, 0.035, 0.035), 'lamp', 'Torso')             # chest lamp
    m.box((0.104, -0.05, 0.665), (0.010, 0.045, 0.02), 'joint', 'Torso')
    # Pauldrons: layered angular plates sloping off the shoulder, a coloured edge on the lower one, over a
    # rounded cap (AS's are plates, not balls).
    for side in (1, -1):
        m.ellipsoid((-0.005, side * 0.16, 0.70), (0.07, 0.06, 0.04), 'armor2', 'Torso', sides=10, rings=5)
        m.box((-0.005, side * 0.175, 0.725), (0.15, 0.09, 0.035), 'armor', 'Torso', roll=side * 24)
        m.box((-0.01, side * 0.205, 0.68), (0.14, 0.06, 0.03), 'armor', 'Torso', roll=side * 48)
        m.box((-0.01, side * 0.232, 0.655), (0.14, 0.012, 0.02), 'trim', 'Torso', roll=side * 48)
    # The backpack: a power pack with ribbed cooling fins and a status lamp on its back, twin tanks, the antenna.
    m.box((-0.15, 0.0, 0.64), (0.11, 0.21, 0.20), 'pack', 'Torso')
    m.box((-0.207, 0.0, 0.64), (0.02, 0.17, 0.16), 'armor2', 'Torso')
    for k in range(4):
        m.box((-0.219, 0.0, 0.585 + k * 0.03), (0.008, 0.13, 0.012), 'joint', 'Torso')
    m.box((-0.15, 0.0, 0.745), (0.09, 0.17, 0.012), 'armor2', 'Torso')                 # its lid, seen from above
    for side in (1, -1):
        m.tube((-0.17, side * 0.075, 0.53), (-0.17, side * 0.075, 0.75), 0.04, slot='armor2', bone='Torso', sides=10)
        m.ellipsoid((-0.17, side * 0.075, 0.75), (0.04, 0.04, 0.015), 'trim', 'Torso', sides=10, rings=4)
    m.box((-0.218, -0.05, 0.715), (0.012, 0.04, 0.018), 'lamp', 'Torso')
    m.tube((-0.17, 0.07, 0.75), (-0.19, 0.07, 1.05), 0.006, 0.003, slot='joint', bone='Antenna', sides=5)
    m.ellipsoid((-0.19, 0.07, 1.05), (0.01, 0.01, 0.01), 'gunlite', 'Antenna', sides=6, rings=4)
    # Helmet: a domed shell, a jaw guard and two glowing eye slits.
    m.limb((0.0, 0.0, 0.70), (0.005, 0.0, 0.76), 0.045, 0.045, 'joint', 'Head')
    m.ellipsoid((0.01, 0.0, 0.81), (0.085, 0.075, 0.075), 'armor', 'Head')
    m.ellipsoid((0.0, 0.0, 0.84), (0.075, 0.065, 0.05), 'armor2', 'Head')
    m.box((0.0, 0.0, 0.89), (0.15, 0.022, 0.02), 'armor', 'Head', pitch=-6)        # a crest ridge front to back
    for side in (1, -1):
        m.box((-0.005, side * 0.074, 0.81), (0.07, 0.012, 0.045), 'joint', 'Head')  # ear vents
    m.box((0.06, 0.0, 0.775), (0.05, 0.10, 0.05), 'joint', 'Head', pitch=10)
    for side in (1, -1):
        m.box((0.083, side * 0.03, 0.81), (0.014, 0.05, 0.02), 'visor', 'Head', yaw=side * 14)
        # Two lamps on the crown, the lights AS's helmets show from above.
        m.ellipsoid((0.04, side * 0.035, 0.875), (0.014, 0.012, 0.009), 'visor', 'Head', sides=6, rings=4)
    # Arms reaching to the gun: upper arm, elbow, forearm and armoured glove.
    shoulder_r, shoulder_l = np.array((0.0, -0.155, 0.665)), np.array((0.0, 0.155, 0.665))
    elbow_r = np.array((0.02, -0.19, 0.53)) if twohanded else np.array((0.04, -0.20, 0.54))
    elbow_l = (shoulder_l + np.asarray(fore)) / 2 + (-0.06, 0.06, -0.08)
    for shoulder, elbow, hand in ((shoulder_r, elbow_r, np.asarray(grip)), (shoulder_l, elbow_l, np.asarray(fore))):
        m.limb(shoulder, elbow, 0.042, 0.04, 'suit', 'Torso', sides=7)
        m.limb(elbow, hand, 0.042, 0.034, 'armor2', 'Torso', sides=7)
        m.ellipsoid(hand, (0.035, 0.03, 0.03), 'glove', 'Torso', sides=7, rings=5)


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
    m.tube((0.0, y, z + 0.02), (0.0, -0.13, 0.66), 0.012, slot='joint', sides=6)        # harness arm to the shoulder
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
    m.tube((-0.17, -0.075, 0.55), (0.12, y - 0.04, z - 0.04), 0.01, slot='joint', sides=5)          # hose to the pack
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
    m.box((0.02, -0.20, 0.38), (0.22, 0.07, 0.16), 'pack', 'Torso')
    m.box((0.02, -0.20, 0.47), (0.08, 0.02, 0.02), 'joint', 'Torso')
    m.box((0.02, -0.235, 0.38), (0.12, 0.004, 0.04), 'trim', 'Torso')
    z, y = GUN_Z + 0.03, 0.08
    m.box((0.30, y, z), (0.12, 0.035, 0.05), 'gun', 'Torso')
    m.box((0.33, y + 0.022, z + 0.01), (0.03, 0.01, 0.015), 'gunlite', 'Torso')
    return (0.02, -0.20, 0.48), (0.26, y, z - 0.02), (0.37, y, z)


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
    m.bone = [B['Root']] * len(m.bone)
    return m


def geometry(gun):
    m = Mesh()
    builder = dict((n, b) for n, b, _ in GUNS)[gun]
    two = dict((n, t) for n, _, t in GUNS)[gun]
    grip, fore, muzzle = builder(m)
    body(m, grip, fore, two)
    return m, muzzle


# ----------------------------------------------------------- animation
def pose(name, t):
    out = {}
    ph = t * math.tau
    X, Y, Z = (1, 0, 0), (0, 1, 0), (0, 0, 1)

    def put(bone, loc=(0, 0, 0), *rot):
        out[B[bone]] = (np.asarray(loc, float), qrot(*rot))

    if name == 'Stand':
        # Breathing: the chest rises, the head looks about a little; the gun stays on the line.
        put('Pelvis', (0, 0, -0.004 + 0.004 * math.sin(ph)))
        put('Torso', (0, 0, 0.003 * math.sin(ph)), (Y, 0.8 * math.sin(ph)))
        put('Head', (0, 0, 0), (Z, 6 * math.sin(ph * 0.5)), (Y, -2 * math.sin(ph)))
        put('Antenna', (0, 0, 0), (X, 4 * math.sin(ph * 2)))
        for leg in ('ThighL', 'ThighR', 'ShinL', 'ShinR'):
            put(leg)
    elif name == 'Walk':
        # A run: long strides, knees lifting, the hips bobbing; the torso keeps the gun level.
        bob = 0.022 * abs(math.cos(ph))
        put('Pelvis', (0, 0, -0.012 + bob), (Z, 6 * math.sin(ph)))
        put('Torso', (0, 0, 0), (Z, -6 * math.sin(ph)), (Y, 5))
        put('Head', (0, 0, 0), (Y, -4))
        put('Antenna', (0, 0, 0), (Y, -8 - 6 * abs(math.sin(ph))))
        for thigh, shin, phase in (('ThighL', 'ShinL', 0.0), ('ThighR', 'ShinR', math.pi)):
            p = ph + phase
            swing = 34 * math.sin(p)                    # + forward
            knee = 12 + 46 * max(0.0, math.sin(p + 1.3)) # the shin folds back as the foot comes through
            put(thigh, (0, 0, 0), (Y, -swing))
            put(shin, (0, 0, 0), (Y, knee))
    elif name == 'Work':
        # Backing off while aiming ahead: the run's stride played backwards.
        return pose('Walk', 1.0 - t)
    elif name in ('Spell', 'Cover'):
        # Side-steps (Spell to the marine's left, Cover to its right): the legs reach sideways in turn,
        # the hips sway over the planted foot, the torso keeps the gun on its line.
        side = 1 if name == 'Spell' else -1
        put('Pelvis', (0, side * 0.012 * math.sin(ph), -0.01 + 0.012 * abs(math.cos(ph))))
        put('Torso', (0, 0, 0), (Y, 4))
        put('Head', (0, 0, 0), (Y, -3))
        put('Antenna', (0, 0, 0), (X, -side * 6 * math.sin(ph)))
        # Step and close: the leading leg reaches out (lifting as it goes), the other follows it in; never crossing.
        spread = 0.5 - 0.5 * math.cos(ph)
        lead, trail = (('ThighL', 'ShinL'), ('ThighR', 'ShinR')) if side > 0 else (('ThighR', 'ShinR'), ('ThighL', 'ShinL'))
        put(lead[0], (0, 0, 0), (X, side * 19 * spread), (Y, -6))
        put(lead[1], (0, 0, 0), (Y, 10 + 34 * max(0.0, math.sin(ph))))
        put(trail[0], (0, 0, 0), (X, -side * 5 * spread), (Y, -6))
        put(trail[1], (0, 0, 0), (Y, 10 + 30 * max(0.0, -math.sin(ph))))
    elif name == 'Attack':
        # A rifle-butt swing: the torso winds back, then drives across.
        twist = _knots(t, [(0, 0), (0.25, 30), (0.5, -38), (0.8, -10), (1, 0)])
        lean = _knots(t, [(0, 0), (0.25, -6), (0.5, 14), (1, 0)])
        put('Torso', (_knots(t, [(0, 0), (0.5, 0.05), (1, 0)]), 0, 0), (Z, twist), (Y, lean))
        put('Pelvis', (0, 0, -0.01), (Z, twist * 0.3))
        put('Head', (0, 0, 0), (Z, -twist * 0.5))
        put('ThighL', (0, 0, 0), (Y, -18)); put('ShinL', (0, 0, 0), (Y, 22))
        put('ThighR', (0, 0, 0), (Y, 10)); put('ShinR', (0, 0, 0), (Y, 8))
    elif name == 'Morph':
        # The reload (stock name Morph, so the client's lookup finds it): the gun dips and turns in toward the body
        # as the old clip drops and a new one goes in, then comes back up onto the aim. Upper body only (see
        # SEQ_BONES), so the legs keep running under it.
        dip = _knots(t, [(0, 0), (0.18, 1), (0.75, 1), (1, 0)])
        jolt = _knots(t, [(0, 0), (0.55, 0), (0.62, 1), (0.72, 0), (1, 0)])
        put('Torso', (0, 0, -0.01 * dip), (Y, 16 * dip + 4 * jolt), (Z, 22 * dip), (X, -8 * dip))
        put('Head', (0, 0, 0), (Y, 14 * dip), (Z, -10 * dip))
    elif name == 'Death':
        # Shot down: the knees buckle, the marine goes over backwards and lands on its pack, legs out in front,
        # the gun still in its hands; a last twitch, then still.
        f = _knots(t, [(0, 0), (0.15, 0.12), (0.55, 1.0), (0.62, 0.95), (0.7, 1.0), (1, 1)])
        tw = math.sin(t * 50) * max(0.0, 1 - abs(t - 0.8) / 0.08) * 3
        put('Pelvis', (-0.12 * f, 0, -0.36 * f), (Y, -82 * f))
        put('Torso', (0, 0, 0), (Y, -8 * f + tw), (Z, 78 * f))     # turned onto its side, so the gun lies along the deck
        put('Head', (0, 0, 0), (Y, 20 * f), (Z, 25 * f))
        put('Antenna', (0, 0, 0), (Y, 30 * f))
        put('ThighL', (0, 0, 0), (Y, -30 * f), (X, 8 * f)); put('ShinL', (0, 0, 0), (Y, 40 * f))
        put('ThighR', (0, 0, 0), (Y, -12 * f), (X, -10 * f)); put('ShinR', (0, 0, 0), (Y, 14 * f + tw))
    elif name == 'Fire':
        # Recoil: a short kick back through the shoulders.
        k = _knots(t, [(0, 0), (0.15, 1), (1, 0)])
        put('Torso', (-0.02 * k, 0, 0), (Y, -4 * k))
    return out


WALK_SPEED = 2.6
# Walk runs forward; Work backs off, Spell and Cover side-step left and right (stock animation names, so the
# client's lookup finds them: src/Marine.galaxy AS_Walk picks one from the run's angle to the aim).
SEQUENCES = [('Stand', 3000, 0.0, False), ('Walk', 560, WALK_SPEED, False), ('Work', 600, 0.0, False), ('Spell', 600, 0.0, False),
             ('Cover', 600, 0.0, False), ('Attack', 600, 0.0, True), ('Fire', 160, 0.0, True), ('Death', 1300, 0.0, True),
             ('Morph', 1000, 0.0, True)]
ANIMATED = {'location': {B['Pelvis'], B['Torso']}, 'rotation': set(range(1, len(BONES)))}
# Sequences that move only part of the body: the client blends them over whatever the rest is playing.
SEQ_BONES = {'Morph': {'location': {B['Torso']}, 'rotation': {B['Torso'], B['Head']}}}


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
                for p in poses:
                    loc, rot = p.get(bi, (np.zeros(3), np.array([0.0, 0.0, 0.0, 1.0])))
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


def muzzles():
    """{gun: (forward, left, height)} of each model's muzzle, for the script."""
    return {name: tuple(round(float(v), 3) for v in geometry(name)[1]) for name, _, _ in GUNS}


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
        sheet.paste(render(model, diffuse, emissive, 'Stand', 0.0, -50, 35, (W, H), tint=tints[k % 4], muzzle=muzzle), (x, y))
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


if __name__ == '__main__':
    files = build()
    print({k: len(v) for k, v in files.items()})
    print(muzzles())
    print(preview())
