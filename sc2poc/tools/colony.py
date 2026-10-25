"""The colony's own look (SynTek Residential, Sewer Junction B5), drawn after Alien Swarm's.

- EGlass: an office window (asi-jac4's func_breakable window_01 .. window_15), 2 wide (scaled by the script to the
  window) and chest-to-head high in a steel frame: a sill and a head rail, a post at each end. The pane is a
  multiplied layer that tints what stands behind it a cold green-grey and an added one for the glare streaks
  (map-written M3s draw alpha's clear parts opaque, so glass is the blend of the two). src/Doors.galaxy kind 7
  (glass) stands one in each window and shatters it for good once a marine comes up to it.
"""
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


def textures():
    """name -> (diffuse, emissive) for tools/shipkit.py pack_textures."""
    return {'cglass_frame': tex_frame()}


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


def meshes():
    """{name: ShipModel}: the colony's script-placed pieces."""
    return {'EGlass': glass_mesh()}
