"""The colony's own look (SynTek Residential, Sewer Junction B5), drawn after Alien Swarm's.

- EGlass: an office window (asi-jac4's func_breakable window_01 .. window_15), 2 wide (scaled by the script to the
  window) and chest-to-head high in a steel frame: a sill and a head rail, a post at each end. The pane is a
  multiplied layer that tints what stands behind it a cold green-grey and an added one for the glare streaks
  (map-written M3s draw alpha's clear parts opaque, so glass is the blend of the two). src/Doors.galaxy kind 7
  (glass) stands one in each window and shatters it for good once a marine comes up to it.
- ERockfall: a heap of Timor Station's mine rock fallen across a way (its asw_prop_laserable heaps, Barricade5,
  block_rock_exit), 2 wide (scaled to the way) and up to a marine's height: broken slabs of the green-grey rock with
  rust veins, the biggest at the foot. src/Doors.galaxy kind 8 (rock) stands one in each fall and takes it away when
  the fall is cut through or cleared.
"""
import math

import numpy as np

from tools.shipkit import ShipModel, NO_SHADOW_CAST, UNLIT, MULTIPLY, ADD, _noise, _img, _grime

GLASS_Z0 = 0.0        # the pane from the floor (AS's office glass runs from the floor, -36 .. 92 units over it)
GLASS_Z1 = 2.4
FRAME = 0.10          # the frame's sill, head and posts: this thick each way


# ------------------------------------------------------------------ textures
def tex_frame(w=128, h=128):
    """The window frame: dark anodised steel, a groove down its middle."""
    n = _noise(0, 24, 411, 3, (h, w))
    a = np.array((58, 64, 66), float)[None, None] * (0.85 + 0.25 * n[..., None])
    a[:, w // 2 - 3:w // 2 + 3] *= 0.55
    return _img(_grime(a, 412, 0.25)), None


def tex_glass_mul(w=128, h=256):
    """The pane's tint: a cold green-grey over whatever is behind, a little darker toward the foot."""
    a = np.zeros((h, w, 3)) + np.array((176, 204, 206))
    a *= np.linspace(1.0, 0.86, h)[:, None, None]
    n = _noise(0, 32, 413, 3, (h, w))
    a *= (0.95 + 0.08 * n)[..., None]
    return _img(a)


def tex_glass_add(w=128, h=256):
    """The pane's glare: two soft diagonal streaks and a faint sheen, black elsewhere (added)."""
    yy, xx = np.mgrid[0:h, 0:w].astype(float)
    a = np.zeros((h, w, 3))
    for off, width, k in ((40, 14, 1.0), (92, 6, 0.7)):
        d = np.abs(((xx + yy * 0.55) - off) % 200 - 100)
        a += (np.clip(1 - np.abs(d - 50) / width, 0, 1) ** 2 * k)[..., None] * np.array((70, 92, 96))
    a += np.array((10, 14, 15))
    return _img(a)


def tex_rock(w=256, h=256):
    """The fall's rock (minerockwall): green-grey, rust-brown veins, dark cracks, paler on its broken faces."""
    n = _noise(0, 40, 421, 5, (h, w)); f = _noise(0, 6, 422, 3, (h, w))
    a = np.array((92, 98, 84), float)[None, None] * (0.75 + 0.4 * n[..., None] + 0.12 * f[..., None])
    vein = np.clip(1 - np.abs(_noise(0, 36, 423, 4, (h, w)) - 0.5) * 16, 0, 1)
    a = a * (1 - 0.5 * vein[..., None]) + np.array((120, 84, 50), float) * 0.5 * vein[..., None]
    crack = np.clip(1 - np.abs(_noise(0, 22, 424, 3, (h, w)) - 0.5) * 30, 0, 1)
    a *= (1 - 0.55 * crack)[..., None]
    return _img(_grime(a, 425, 0.3)), None


def textures():
    """name -> (diffuse, emissive) for tools/shipkit.py pack_textures."""
    return {'cglass_frame': tex_frame(), 'crock': tex_rock()}


def multiply_textures():
    """name -> image for the blended layers (packed as they are, no emissive)."""
    return {'cglass_mul': tex_glass_mul(), 'cglass_add': tex_glass_add()}


# ------------------------------------------------------------------ meshes
def _box(m, key, x0, y0, z0, x1, y1, z1):
    u = [(0, 1), (1, 1), (1, 0), (0, 0)]
    m.quad(key, (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1), u)
    m.quad(key, (x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1), u)
    m.quad(key, (x1, y1, z0), (x0, y1, z0), (x0, y1, z1), (x1, y1, z1), u)
    m.quad(key, (x1, y0, z0), (x1, y1, z0), (x1, y1, z1), (x1, y0, z1), u)
    m.quad(key, (x0, y1, z0), (x0, y0, z0), (x0, y0, z1), (x0, y1, z1), u)


def glass_mesh():
    """EGlass: the window, x -1..1 (the script scales it to the window's width), the pane at y 0."""
    m = ShipModel('EGlass', (0, 0, 0))
    frame = ('cglass_frame', False, 0)
    _box(m, frame, -1.0, -FRAME, GLASS_Z0, 1.0, FRAME, GLASS_Z0 + FRAME)
    _box(m, frame, -1.0, -FRAME, GLASS_Z1 - FRAME, 1.0, FRAME, GLASS_Z1)
    for x in (-1.0, 1.0 - FRAME * 2):
        _box(m, frame, x, -FRAME, GLASS_Z0, x + FRAME * 2, FRAME, GLASS_Z1)
    uv = [(0, 1), (1, 1), (1, 0), (0, 0)]
    for tex, blend, y in (('cglass_mul', MULTIPLY, 0.0), ('cglass_add', ADD, 0.004)):
        key = (tex, True, UNLIT | NO_SHADOW_CAST, blend)
        m.quad(key, (-1.0, y, GLASS_Z0 + FRAME), (1.0, y, GLASS_Z0 + FRAME), (1.0, y, GLASS_Z1 - FRAME), (-1.0, y, GLASS_Z1 - FRAME), uv)
    return m


def _slab(m, key, cx, cy, z0, sx, sy, hgt, ang, top=0.6):
    """A broken slab: a block narrowing to `top` of its foot, turned `ang` degrees, its top tilted a little."""
    c, s = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    def at(x, y, z):
        return (cx + x * c - y * s, cy + x * s + y * c, z)
    lo = [at(-sx, -sy, z0), at(sx, -sy, z0), at(sx, sy, z0), at(-sx, sy, z0)]
    tilt = (0.0, 0.12 * hgt, -0.08 * hgt, 0.05 * hgt)
    hi = [at(x * top, y * top, z0 + hgt + t) for (x, y), t in zip(((-sx, -sy), (sx, -sy), (sx, sy), (-sx, sy)), tilt)]
    u = [(0, 1), (1, 1), (1, 0), (0, 0)]
    m.quad(key, hi[0], hi[1], hi[2], hi[3], u)
    for k in range(4):
        j = (k + 1) % 4
        m.quad(key, lo[k], lo[j], hi[j], hi[k], u)


def rockfall_mesh():
    """ERockfall: the heap, x -1..1 (the script scales it to the way's width), y -0.9..0.9 across the way."""
    m = ShipModel('ERockfall', (0, 0, 0))
    key = ('crock', False, 0)
    r = np.random.default_rng(426)
    for x in np.linspace(-0.8, 0.8, 5):
        _slab(m, key, x + r.uniform(-0.08, 0.08), r.uniform(-0.25, 0.25), 0.0, 0.32, r.uniform(0.45, 0.65),
              r.uniform(0.9, 1.4), r.uniform(-25, 25))
    for x in np.linspace(-0.6, 0.6, 4):
        _slab(m, key, x + r.uniform(-0.1, 0.1), r.uniform(-0.3, 0.3), r.uniform(0.7, 1.0), 0.24, r.uniform(0.3, 0.45),
              r.uniform(0.5, 0.8), r.uniform(0, 180), 0.5)
    for k in range(10):
        _slab(m, key, r.uniform(-1.0, 1.0), r.choice((-1, 1)) * r.uniform(0.6, 0.9), 0.0, r.uniform(0.08, 0.16),
              r.uniform(0.08, 0.16), r.uniform(0.1, 0.25), r.uniform(0, 180), 0.5)
    return m


def meshes():
    """{name: ShipModel}: the colony's script-placed pieces."""
    return {'EGlass': glass_mesh(), 'ERockfall': rockfall_mesh()}
