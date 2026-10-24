"""A rough CPU render of the cargo elevator from the game's top-down camera, for checking
framing and the shaft's look without the client: textured quads (panels, lintels, gates,
platform, bridges, void) drawn back to front with flat shading. No lights or shadows.

    py tools/preview_lift.py            writes dist/lift-preview.png (four moments of the ride)
    py tools/preview_lift.py 6          the same from another camera distance (the ride frames at AS_RIDE_FRAME)
"""
import math, sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import level as L, elevator as E

L.use('cargo')
W, H = 960, 600                           # 16:10, the shape of the test screen
PITCH, FOV = 60.0, 48.0                   # src/Marine.galaxy AS_TOP_PITCH, AS_TOP_FOV
DIST = float(sys.argv[1]) if len(sys.argv) > 1 else 13.0   # src/Mission.galaxy AS_RIDE_FRAME


def camera(tx, ty):
    p = math.radians(PITCH)
    fwd = np.array([0.0, math.cos(p), -math.sin(p)])
    up = np.array([0.0, math.sin(p), math.cos(p)])
    right = np.array([1.0, 0.0, 0.0])
    eye = np.array([tx, ty, 0.4]) - DIST * fwd
    f = 1 / math.tan(math.radians(FOV) / 2)
    def proj(P):
        d = np.asarray(P, float) - eye
        z = d @ fwd
        return (W / 2 + (d @ right) / z * f * H / 2, H / 2 - (d @ up) / z * f * H / 2, z)
    return proj


def coeffs(dst, src):
    """PIL PERSPECTIVE coefficients mapping output points dst to input points src."""
    A, b = [], []
    for (x, y), (u, v) in zip(dst, src):
        A.append([x, y, 1, 0, 0, 0, -u * x, -u * y]); b.append(u)
        A.append([0, 0, 0, x, y, 1, -v * x, -v * y]); b.append(v)
    return np.linalg.solve(np.array(A, float), np.array(b, float))


def draw(canvas, proj, corners, tex, uv, shade=1.0):
    pts = [proj(c) for c in corners]
    if min(p[2] for p in pts) < 0.5:
        return
    dst = [(p[0], p[1]) for p in pts]
    tw, th = tex.size
    src = [(u * (tw - 1), v * (th - 1)) for u, v in uv]
    try:
        c = coeffs(dst, src)
    except np.linalg.LinAlgError:
        return
    img = tex.transform((W, H), Image.Transform.PERSPECTIVE, tuple(c), Image.Resampling.BILINEAR)
    if shade != 1.0:
        img = Image.eval(img, lambda v: int(v * shade))
    mask = Image.new('L', (W, H), 0)
    ImageDraw.Draw(mask).polygon(dst, fill=255)
    canvas.paste(img, (0, 0), mask)


def frame(s, tx=86.0, ty=95.0, gates=0.0):
    tex = {k: (d.convert('RGB')) for k, (d, e) in E.textures().items()}
    emis = {k: e.convert('RGB') for k, (d, e) in E.textures().items() if e is not None}
    for k, e in emis.items():
        tex[k] = Image.fromarray(np.clip(np.asarray(tex[k], float) * 0.55 + np.asarray(e, float) * 0.9, 0, 255).astype(np.uint8))
    proj = camera(tx, ty)
    canvas = Image.new('RGB', (W, H), (8, 9, 11))
    quads = []          # (depth, corners, texture, uv, shade)
    floor_t = Image.new('RGB', (8, 8), (46, 50, 54))
    hull_t = Image.new('RGB', (8, 8), (18, 19, 21))
    floor, room = L.carve()
    for y in range(int(ty) - 16, int(ty) + 18):
        for x in range(int(tx) - 22, int(tx) + 23):
            if not (0 <= x < L.W and 0 <= y < L.H):
                continue
            if L.in_void(x, y):
                t = tex['void']
            elif floor[y, x]:
                t = floor_t if L.kind_at(room, x, y) != 'lift' else None
            else:
                t = hull_t
            if t is None:
                continue
            c = [(x, y, 0), (x + 1, y, 0), (x + 1, y + 1, 0), (x, y + 1, 0)]
            quads.append((proj((x + .5, y + .5, 0))[2] + 50, c, t, [(0, 1), (1, 1), (1, 0), (0, 0)], 1.0))
    x0, y0, x1, y1 = L.LIFT
    quads.append((proj(((x0 + x1) / 2, (y0 + y1) / 2, 0))[2] + 40, [(x0, y0, .03), (x1, y0, .03), (x1, y1, .03), (x0, y1, .03)], tex['lift_deck'],
                  [(0, 1), (1, 1), (1, 0), (0, 0)], 0.8))
    # Shaft panels: slot k at height h = (6k + s) mod 24, covering z h-6 .. h.
    out_slot = int(((E.PANEL_H - 108 + 300) % 30) / E.PANEL_H) % 5
    for cx, cy, w, face, side in L.shaft_columns():
        fa = math.radians(face)
        ax, ay = math.cos(fa + math.pi / 2), math.sin(fa + math.pi / 2)
        for k in range(5):
            h = (6 * k + s) % 30
            z0, z1 = h - E.DROP, h - E.DROP + E.PANEL_H
            if z1 <= 0:
                continue
            name = 'shaft_b' if (k + len(quads)) % 3 == 0 else 'shaft_a'
            v0, v1 = 1.0, 0.0
            if side == 'W' and abs(cy - 96) < .1 and k == 1 and s < 18:
                name, z0, v0 = 'lintel', h - E.DROP + E.GATE_H, 1 - E.GATE_H / E.PANEL_H
            if side == 'E' and abs(cy - 96) < .1 and k == out_slot and s > 102:
                name, z0, v0 = 'lintel', h - E.DROP + E.GATE_H, 1 - E.GATE_H / E.PANEL_H
            zc0 = max(z0, 0.0)
            vc0 = v0 + (v1 - v0) * (zc0 - z0) / (z1 - z0)
            hw = w / 2
            c = [(cx - ax * hw, cy - ay * hw, zc0), (cx + ax * hw, cy + ay * hw, zc0), (cx + ax * hw, cy + ay * hw, z1), (cx - ax * hw, cy - ay * hw, z1)]
            mid = proj((cx, cy, (zc0 + z1) / 2))
            shade = 0.75 if side == 'N' else 0.55
            quads.append((mid[2], c, tex[name], [(0, vc0), (w / 4, vc0), (w / 4, v1), (0, v1)], shade))
    for d, c, t, uv, sh in sorted(quads, key=lambda q: -q[0]):
        u = np.array(uv); u[:, 0] = u[:, 0] / max(1e-6, u[:, 0].max()) if u[:, 0].max() > 1 else u[:, 0]
        draw(canvas, proj, c, t, [tuple(p) for p in u], sh)
    d = ImageDraw.Draw(canvas)
    for i, (mx, my) in enumerate([(84, 94), (88, 94), (84, 98), (88, 98)]):
        p = proj((mx, my, 0.5))
        d.ellipse([p[0] - 6, p[1] - 6, p[0] + 6, p[1] + 6], fill=(60, 120, 255))
    d.text((10, 10), 'scroll %.0f' % s, fill=(255, 200, 90))
    return canvas


def main():
    # The ride's camera centres 2 north of the marine (src/Mission.galaxy AS_RIDE_BIAS); a marine mid-deck, then left.
    x0, y0, x1, y1 = L.LIFT
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2 + 2.0
    shots = [frame(0.0, cx, cy), frame(14.0, cx, cy), frame(52.0, cx - 4.0, cy + 1.0), frame(108.0, cx, cy)]
    sheet = Image.new('RGB', (W * 2, H * 2))
    for i, im in enumerate(shots):
        sheet.paste(im, ((i % 2) * W, (i // 2) * H))
    out = ROOT / 'dist/lift-preview.png'
    sheet.save(out)
    print(out)


if __name__ == '__main__':
    main()
