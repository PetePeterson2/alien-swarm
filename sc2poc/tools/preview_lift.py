"""A CPU render of the cargo elevator's ride from the game's top-down camera, for checking the shaft's look and
framing without the client: the lift's meshes (tools/elevator.py) z-buffered with their textures, the walls' segments
where src/Mission.galaxy puts them at each moment, lit by the ride's lamps (the red beacon, the orange cage lamps, the
amber ones at the ends) and fogged as AS's fog_elevator is. Sky-high precision is not the point: where things are and
what the camera sees is.

    py tools/preview_lift.py            writes dist/lift-preview.png (five moments of the ride, s = 0 .. RIDE)
    py tools/preview_lift.py 7.5        the same from another camera distance (Z steps out to 7.5 and 10.5)
"""
import math, sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import level as L, elevator as E

L.use('cargo')
W, H = 640, 400                           # 16:10, the shape of the test screen
PITCH, FOV = 60.0, 60.0                   # src/Marine.galaxy AS_TOP_PITCH, AS_TOP_FOV
DIST = float(sys.argv[1]) if len(sys.argv) > 1 else 5.1   # AS_TOP_DIST
FOG, FOG_START, FOG_END, FOG_MAX = np.array((43, 37, 32)) / 255, 3.2, 50.0, 0.9
SH = dict(L.SHAFT)
SH['low'], SH['out_slot'] = E.train(SH['in_slot'])


def slots(s):
    """(u at the slot's start, model) of every wall segment at ride position s, as AS_ShaftSet lays them."""
    out = []
    for k in range(E.SEG_N):
        u = (SH['low'] + k * E.SEG + s - SH['low']) % (E.SEG_N * E.SEG) + SH['low']
        # The doorway slots swap while out of sight, as each first wraps from the top of the train to the bottom.
        wrap = (E.SEG_N - k) * E.SEG
        name = 'ESeg'
        if k == SH['in_slot'] and s < wrap:
            name = 'ESegIn'
        if k == SH['out_slot'] and s >= wrap:
            name = 'ESegOut'
        out.append((u, name))
    return out


def lights(s):
    """(position, colour, reach) of the ride's lamps at s: the red beacon on its wall, the cage lamps that are up."""
    out = []
    k = sum(1 for p in SH['beacon_s'] if s >= p)
    bu = SH['beacons'][min(k, len(SH['beacons']) - 1)] + s
    out.append((np.array((SH['beacon_x'], SH['y'] + bu * E.TRAVEL[0], bu * E.TRAVEL[1])), np.array((1.0, 0.05, 0.03)) * 2.2, 9.0))
    for u, name in slots(s):
        for x in (SH['x'] - E.HALF + 0.5, SH['x'] + E.HALF - 0.5):
            lu = u + E.LAMP_U
            p = np.array((x, SH['y'] + lu * E.TRAVEL[0] + E.LAMP_T * E.INTO[0], lu * E.TRAVEL[1] + E.LAMP_T * E.INTO[1]))
            if p[2] > -1.0:
                out.append((p, np.array((0.78, 0.18, 0.01)) * 1.4, 5.0))
    if s <= 0.0:
        out.append((np.array((41.0, 114.0, 1.9)), np.array((0.98, 0.75, 0.0)) * 1.6, 7.0))
    if s >= E.RIDE:
        out.append((np.array((50.3, 114.1, 1.9)), np.array((0.98, 0.75, 0.0)) * 1.6, 7.0))
    return out


def scene(s, tex):
    """Triangles: (3x3 positions, 3x2 uvs, texture name, additive) of everything in the shaft at s."""
    tris = []
    def add(model, offset):
        for key, d in model.parts.items():
            pos = np.array(d['pos']) - model.origin + offset
            uv = np.array(d['uv'])
            for a, b, c in d['tri']:
                tris.append((pos[[a, b, c]], uv[[a, b, c]], key[0], len(key) > 3 and key[3] == 2))
    lift = E.meshes(L.LIFT, L.LIFT_NOTCH, L.BRIDGE_IN, L.BRIDGE_OUT, L.VOID, L.CONSOLE, L.DECK, L.VOID_DEPTH)
    for name in ('EPlatform', 'EVoid', 'EScreenG' if s > 0 else 'EScreenR'):
        add(lift[name], lift[name].origin)
    segs = E.shaft_models()
    for u, name in slots(s):
        add(segs[name], np.array((SH['x'], SH['y'] + u * E.TRAVEL[0], u * E.TRAVEL[1])))
    return tris


def render(s, tex, target=(46.0, 112.0)):
    p = math.radians(PITCH)
    fwd = np.array([0.0, math.cos(p), -math.sin(p)]); up = np.array([0.0, math.sin(p), math.cos(p)]); right = np.array([1.0, 0, 0])
    eye = np.array([target[0], target[1], 0.4]) - DIST * fwd
    f = (H / 2) / math.tan(math.radians(FOV) / 2)
    zb = np.full((H, W), 1e9); img = np.zeros((H, W, 3)); glow = np.zeros((H, W, 3))
    lamps = lights(s)
    # Opaque first, then what is added over it (glows, the haze's veils), each against the finished depths.
    for P, U, name, additive in sorted(scene(s, tex), key=lambda t: t[3]):
        d = P - eye; z = d @ fwd
        if (z < 0.2).any():
            continue
        sx = W / 2 + (d @ right) / z * f; sy = H / 2 - (d @ up) / z * f
        x0, x1 = int(max(0, np.floor(sx.min()))), int(min(W - 1, np.ceil(sx.max())))
        y0, y1 = int(max(0, np.floor(sy.min()))), int(min(H - 1, np.ceil(sy.max())))
        if x0 > x1 or y0 > y1:
            continue
        den = (sy[1] - sy[2]) * (sx[0] - sx[2]) + (sx[2] - sx[1]) * (sy[0] - sy[2])
        if abs(den) < 1e-9:
            continue
        yy, xx = np.mgrid[y0:y1 + 1, x0:x1 + 1] + 0.5
        l0 = ((sy[1] - sy[2]) * (xx - sx[2]) + (sx[2] - sx[1]) * (yy - sy[2])) / den
        l1 = ((sy[2] - sy[0]) * (xx - sx[2]) + (sx[0] - sx[2]) * (yy - sy[2])) / den
        l2 = 1 - l0 - l1
        m = (l0 >= -1e-4) & (l1 >= -1e-4) & (l2 >= -1e-4)
        if not m.any():
            continue
        iz = l0 / z[0] + l1 / z[1] + l2 / z[2]
        depth = 1 / iz
        sub = zb[y0:y1 + 1, x0:x1 + 1]
        m &= depth < sub
        if not m.any():
            continue
        w0, w1, w2 = (l0 / z[0] / iz)[m], (l1 / z[1] / iz)[m], (l2 / z[2] / iz)[m]
        u = w0 * U[0, 0] + w1 * U[1, 0] + w2 * U[2, 0]; v = w0 * U[0, 1] + w1 * U[1, 1] + w2 * U[2, 1]
        diff, emis = tex[name]
        th, tw = diff.shape[:2]
        c = diff[(np.mod(v, 1) * (th - 1)).astype(int), (np.mod(u, 1) * (tw - 1)).astype(int)]
        if additive:
            glow[y0:y1 + 1, x0:x1 + 1][m] += c
            continue
        sub[m] = depth[m]
        n = np.cross(P[1] - P[0], P[2] - P[0]); n /= np.linalg.norm(n) or 1
        cen = P.mean(0)
        light = np.array((0.16, 0.07, 0.06))
        for lp, col, reach in lamps:
            L_ = lp - cen; dist = np.linalg.norm(L_)
            light = light + col * abs(n @ (L_ / max(dist, 1e-3))) * max(0.0, 1 - dist / reach) ** 1.5
        out = c * light
        if emis is not None:
            out = out + emis[(np.mod(v, 1) * (th - 1)).astype(int), (np.mod(u, 1) * (tw - 1)).astype(int)] * 1.6
        img[y0:y1 + 1, x0:x1 + 1][m] = out
    ff = np.clip((zb - FOG_START) / (FOG_END - FOG_START), 0, FOG_MAX)[..., None]
    ff[zb >= 1e8] = FOG_MAX
    out = img * (1 - ff) + FOG * ff + glow
    return Image.fromarray((np.clip(out, 0, 1) * 255).astype(np.uint8))


def main():
    tex = {k: (np.asarray(d.convert('RGB')).astype(float) / 255, None if e is None else np.asarray(e.convert('RGB')).astype(float) / 255)
           for k, (d, e) in E.textures().items()}
    moments = [0.0, E.RIDE * 0.13, E.RIDE * 0.5, E.RIDE * 0.9, E.RIDE]
    sheet = Image.new('RGB', (W * 3, H * 2))
    for i, s in enumerate(moments):
        im = render(s, tex)
        ImageDraw.Draw(im).text((8, 8), 's %.1f (%d s)' % (s, round(s / SH['speed'])), fill=(255, 255, 255))
        sheet.paste(im, ((i % 3) * W, (i // 3) * H))
        print('moment', round(s, 2))
    out = ROOT / 'dist' / 'lift-preview.png'
    sheet.save(out)
    print(out)


if __name__ == '__main__':
    main()
