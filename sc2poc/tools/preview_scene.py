"""A CPU render of a level as the kit lays it out, from the game's top-down camera, with the marine in it.

The client's screen can't be looked at from here, so this is the way to judge the deck's look: it lays the
floors, walls, caps, the open drop and the railings exactly as src/Kit.galaxy does (same pieces, same
patterns, same panel picks, the same textures, each piece at its cell's real floor height, tools/heights.py;
slope cells get their stair pieces), lights them from the level's lamp list (stock omni lights,
roughly: a coloured pool round each, Lambert on the surface) over the derelict lighting preset's ambient and
key, and puts a marine (tools/marine.py, tinted as player 1) at the camera's centre with its laser sight.
It is an approximation of SC2's renderer (no shadows, no bloom, guessed light falloff), not a screenshot.

    py tools/preview_scene.py [level] [x,y,aim ...]    writes dist/scene-<level>.png
"""
import math, sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'tools/m3-reader'))
from tools import level as L  # noqa: E402
from tools import heights  # noqa: E402

W, H = 960, 600                    # 16:10
PITCH, FOV, DIST, TARGET_Z = 60.0, 60.0, 5.1, 0.4      # src/Marine.galaxy AS_TOP_*
LAMP_Z = 2.1
LAMP_RGB = {'white': (1.0, 0.96, 0.88), 'cold': (0.55, 0.82, 1.0), 'red': (1.0, 0.18, 0.12), 'orange': (1.0, 0.55, 0.2),
            'purple': (0.75, 0.3, 1.0), 'green': (0.35, 1.0, 0.45), 'yellow': (1.0, 0.82, 0.4)}
AMBIENT = np.array((0.14, 0.16, 0.21)) * 1.3          # tools/catalog.py ASDerelict, times its exposure
KEY = (np.array((0.62, 0.72, 0.90)) * 0.36 * 1.3, np.array((-0.35, -0.45, 0.82)) / np.linalg.norm((-0.35, -0.45, 0.82)))
TEX_SIZE = 256


class Camera:
    def __init__(self, tx, ty, tz=0.0):
        p = math.radians(PITCH)
        self.fwd = np.array([0.0, math.cos(p), -math.sin(p)])
        self.up = np.array([0.0, math.sin(p), math.cos(p)])
        self.right = np.array([1.0, 0.0, 0.0])
        self.eye = np.array([tx, ty, TARGET_Z + tz]) - DIST * self.fwd
        self.f = 1 / math.tan(math.radians(FOV) / 2)

    def project(self, P):
        d = np.asarray(P, float) - self.eye
        z = d @ self.fwd
        x = W / 2 + (d @ self.right) / np.maximum(z, 1e-3) * self.f * H / 2
        y = H / 2 - (d @ self.up) / np.maximum(z, 1e-3) * self.f * H / 2
        return np.stack([x, y, z], -1)


class Scene:
    """Deferred: opaque triangles write albedo, emissive, normal, world position; then lamps; then blended layers."""

    def __init__(self, cam):
        self.cam = cam
        self.z = np.full((H, W), np.inf)
        self.alb = np.zeros((H, W, 3)); self.emi = np.zeros((H, W, 3)); self.nrm = np.zeros((H, W, 3)); self.pos = np.zeros((H, W, 3))
        self.unlit = np.zeros((H, W), bool)
        self.blend = []           # (mode, tris...) drawn after lighting

    def tri(self, P, UV, tex, emis=None, tint=None, normal=None, unlit=False, mode=0):
        S = self.cam.project(P)
        if np.any(S[:, 2] < 0.2):
            return
        lo = np.maximum(np.floor(S[:, :2].min(0)).astype(int), 0); hi = np.minimum(np.ceil(S[:, :2].max(0)).astype(int), [W - 1, H - 1])
        if np.any(hi < lo):
            return
        a, b, c = S[:, :2]
        den = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
        if abs(den) < 1e-9:
            return
        if normal is None:
            normal = np.cross(P[1] - P[0], P[2] - P[0]); normal = normal / (np.linalg.norm(normal) + 1e-12)
        # One-sided: faces turned away from the camera are not drawn (ceilings seen from above, wall backs).
        if mode == 0 and np.dot(normal, self.cam.eye - P[0]) < 0:
            return
        gx, gy = np.meshgrid(np.arange(lo[0], hi[0] + 1) + 0.5, np.arange(lo[1], hi[1] + 1) + 0.5)
        w0 = ((b[1] - c[1]) * (gx - c[0]) + (c[0] - b[0]) * (gy - c[1])) / den
        w1 = ((c[1] - a[1]) * (gx - c[0]) + (a[0] - c[0]) * (gy - c[1])) / den
        w = np.stack((w0, w1, 1 - w0 - w1), -1)
        inside = w.min(-1) >= -1e-6
        if not inside.any():
            return
        iz = 1 / S[:, 2]
        pw = w * iz; den2 = pw.sum(-1, keepdims=True)
        pc = pw / den2                          # perspective-correct weights
        z = 1 / den2[..., 0]
        sl = np.s_[lo[1]:hi[1] + 1, lo[0]:hi[0] + 1]
        uv = pc @ UV
        th, tw = tex.shape[:2]
        ti = ((uv[..., 0] % 1) * tw).astype(int) % tw; tj = ((uv[..., 1] % 1) * th).astype(int) % th
        col = tex[tj, ti]
        if tint is not None:
            col = col * tint
        if mode:
            self.blend.append((mode, sl, inside & (z < self.z[sl] + 0.02), col))
            return
        mask = inside & (z < self.z[sl])
        if not mask.any():
            return
        self.z[sl][mask] = z[mask]
        self.alb[sl][mask] = col[mask]
        self.emi[sl][mask] = (emis[tj, ti][mask] if emis is not None else 0)
        nn = normal if np.ndim(normal) == 1 else None
        self.nrm[sl][mask] = nn if nn is not None else 0
        self.pos[sl][mask] = (pc @ P)[mask]
        self.unlit[sl][mask] = unlit

    def shade(self, lamps):
        light = np.zeros((H, W, 3)) + AMBIENT
        n = self.nrm
        light += KEY[0] * np.clip(n @ KEY[1], 0, 1)[..., None]
        for x, y, kind, big, z in lamps:
            r = 7.0 if big else 5.4
            d = np.array([x, y, LAMP_Z + z]) - self.pos
            dist = np.linalg.norm(d, axis=-1)
            near = dist < r
            if not near.any():
                continue
            lam = np.clip((d * n).sum(-1) / np.maximum(dist, 1e-6), 0, 1)
            att = np.clip(1 - (dist / r) ** 2, 0, 1) ** 2
            light += np.array(LAMP_RGB[kind]) * (1.9 * att * lam)[..., None]
        img = self.alb * np.where(self.unlit[..., None], 1.0, light) + self.emi * 1.7
        img[np.isinf(self.z)] = 0
        for mode, sl, mask, col in self.blend:
            region = img[sl]
            if mode == 4:
                region[mask] = region[mask] * col[mask]
            else:
                region[mask] = region[mask] + col[mask]
        # A soft filmic shoulder rather than a hard clip.
        img = img / (1 + 0.25 * np.maximum(img - 0.8, 0))
        return img


def load_textures():
    from tools import shipkit, elevator, deckart
    tex = shipkit.hull_textures()
    tex.update(elevator.textures())
    tex.update(deckart.sign_textures(L.sign_names()))
    mul = shipkit.multiply_textures()
    mul.update(deckart.paint_textures(L.paint_names()))
    out = {}
    for k, (d, e) in tex.items():
        dd = np.asarray(d.convert('RGB').resize((TEX_SIZE, TEX_SIZE)), float) / 255
        ee = np.asarray(e.convert('RGB').resize((TEX_SIZE, TEX_SIZE)), float) / 255 if e is not None else None
        out[k] = (dd, ee)
    for k, f in mul.items():
        im = f() if callable(f) else f
        if isinstance(im, tuple):
            im = im[0]
        out[k] = (np.asarray(im.convert('RGB').resize((TEX_SIZE, TEX_SIZE)), float) / 255, None)
    return out


def place(scene, tex, model, x, y, turn=0.0, z=0.0, zscale=1.0):
    c, s = math.cos(math.radians(turn)), math.sin(math.radians(turn))
    R = np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]]) @ np.diag((1.0, 1.0, zscale))
    for key, part in model.parts.items():
        name, two, flags = key[:3]
        mode = key[3] if len(key) > 3 else 0
        if name not in tex:
            continue
        d, e = tex[name]
        P = np.asarray(part['pos']) @ R.T + (x, y, z); UV = np.asarray(part['uv'])
        N = np.asarray(part['nrm']) @ np.linalg.inv(R); N = N / np.linalg.norm(N, axis=1, keepdims=True)
        unlit = bool(flags & 0x4) and mode == 0
        for t in part['tri']:
            t = list(t)
            scene.tri(P[t], UV[t], d, e, normal=N[t[0]], unlit=unlit, mode=mode)


def lay_level(scene, tex, pieces, rows, tx, ty, hts):
    # The pit's floor shows a wider stretch than the deck does: lay further out.
    x0, x1, y0, y1 = int(tx) - 15, int(tx) + 16, int(ty) - 6, int(ty) + 14
    Wd, Hd = len(rows[0]), len(rows)
    cz, slope, vert = hts['cellz'] - L.FLOOR, hts['slope'], hts['vert'] - L.FLOOR
    edge = hts['edge']

    def zat(x, y):
        x, y = int(math.floor(x)), int(math.floor(y))
        return float(cz[min(max(y, 0), Hd - 1), min(max(x, 0), Wd - 1)])

    def cell(x, y):
        if not (0 <= x < Wd and 0 <= y < Hd):
            return '#'
        return rows[y][x]

    def floor(x, y):
        return cell(x, y) in heights.KIND_CHARS

    def kind(x, y):
        return heights.KIND_CHARS.index(cell(x, y)) if floor(x, y) and not slope[y, x] else -1
    LIFT_KIND = L.KIT_KINDS.index('lift')       # the lift's platform is its own (AS_KitFloorKind)
    # Floors (AS_KitFloors): aligned 4x4 pieces where a block is all one kind, else 2x2, else single cells.
    done = set()

    def second(k, x, y):
        h = ((x // 2) * 3 + (y // 2) * 5 + ((x // 2) * (y // 2)) % 7) % 9
        return h in ((1, 2, 5, 6) if k == 1 else (2, 6))

    def fits(x, y, n, k):
        return all(kind(x + i, y + j) == k and (x + i, y + j) not in done and zat(x + i, y + j) == zat(x, y) for i in range(n) for j in range(n))
    for by in range(max(0, y0 - y0 % 4), y1 + 4, 4):
        for bx in range(max(0, x0 - x0 % 4), x1 + 4, 4):
            k = kind(bx, by)
            if k >= 0 and k != LIFT_KIND and fits(bx, by, 4, k):
                done.update((bx + i, by + j) for i in range(4) for j in range(4))
                place(scene, tex, pieces['KF%d%d' % (k, (bx // 4 * 7 + by // 4 * 13 + (bx // 4) * (by // 4)) % 4)], bx, by, z=zat(bx, by))
                continue
            for i in (0, 2):
                for j in (0, 2):
                    k = kind(bx + i, by + j)
                    if k >= 0 and k != LIFT_KIND and fits(bx + i, by + j, 2, k):
                        done.update((bx + i + a, by + j + b) for a in range(2) for b in range(2))
                        place(scene, tex, pieces['KF%d%s' % (k, 'U' if second(k, bx + i, by + j) else 'T')], bx + i, by + j, z=zat(bx + i, by + j))
                        continue
                    for a in range(2):
                        for b in range(2):
                            k = kind(bx + i + a, by + j + b)
                            if k >= 0 and k != LIFT_KIND and (bx + i + a, by + j + b) not in done:
                                done.add((bx + i + a, by + j + b))
                                place(scene, tex, pieces['KF%d%s%d%d' % (k, 'R' if second(k, bx + i + a, by + j + b) else 'S', (bx + i + a) % 2, (by + j + b) % 2)], bx + i + a, by + j + b, z=zat(bx + i + a, by + j + b))
    # Slope cells: the terrain between its four corner heights, and over it the stair or ramp piece (AS_KitStairs).
    ground = np.full((8, 8, 3), 0.23)
    for y in range(max(0, y0), min(Hd, y1)):
        for x in range(max(0, x0), min(Wd, x1)):
            if floor(x, y) and slope[y, x]:
                P = np.array([[x, y, vert[y, x]], [x + 1, y, vert[y, x + 1]], [x + 1, y + 1, vert[y + 1, x + 1]], [x, y + 1, vert[y + 1, x]]])
                n = np.cross(P[1] - P[0], P[3] - P[0]); n = n / np.linalg.norm(n)
                UV = np.array([[0, 0], [1, 0], [1, 1], [0, 1]], float)
                scene.tri(P[[0, 1, 2]], UV[[0, 1, 2]], ground, normal=n)
                scene.tri(P[[0, 2, 3]], UV[[0, 2, 3]], ground, normal=n)
    for x, y, piece, turn, z, rise in hts['stairs']:
        if x0 <= x < x1 and y0 <= y < y1:
            place(scene, tex, pieces[piece], x + 0.5, y + 0.5, turn, z - L.FLOOR + 0.004, rise)
    # Caps on hull and the drawn drop on open cells, one cell at a time (the kit merges them into bigger tiles).
    for y in range(y0, y1):
        for x in range(x0, x1):
            c = cell(x, y)
            if c in '#w':
                place(scene, tex, pieces['KR1' if getattr(L, 'SNOW_ROOFS', False) else 'KK1'], x, y, z=zat(x, y))
            elif c == 'o' and not edge[y, x]:
                place(scene, tex, pieces['KO1_%d%d' % (x % 4, y % 4)], x, y, z=zat(x, y))
            elif c == 'm':
                place(scene, tex, pieces['KM1_%d%d' % (x % 4, y % 4)], x, y, z=zat(x, y))
    # Walls in two-unit bays (AS_KitBay, AS_FacePanel, AS_KitPanel).
    panels = {L.KIT_KINDS.index(k): v for k, v in L.KIT_PANELS.items()}

    def face(x, y, s):
        c = cell(x, y)
        if floor(x, y) or c in 'vo':
            return -1
        nx, ny = x + (0, 1, 0, -1)[s], y + (-1, 0, 1, 0)[s]
        if cell(nx, ny) == 'o':
            return 9
        if not floor(nx, ny):
            return -1
        if c == 'w':
            return 8
        kk = heights.KIND_CHARS.index(cell(nx, ny)); bx, by = nx // 2, ny // 2
        h = (bx * 37 + by * 101 + s * 59 + (bx * by) % 13) % 211
        p = panels[kk]
        if kk == 6 and h % 5 == 0:
            return 7
        return p[h % len(p)]

    def face_z(x, y, s):
        # AS_FaceZ: a wall stands on the floor it faces.
        return zat(x + (0, 1, 0, -1)[s], y + (-1, 0, 1, 0)[s])

    def bay(xa, ya, xb, yb, s, mx, my):
        pa, pb = face(xa, ya, s), face(xb, yb, s)
        # A building's wall across the drop runs from its roof down to the pit floor (KW9T, AS_KitBay).
        za = zat(xa, ya) if pa == 9 else face_z(xa, ya, s)
        zb = zat(xb, yb) if pb == 9 else face_z(xb, yb, s)
        ka, kb = ('9T' if pa == 9 else str(pa)), ('9T' if pb == 9 else str(pb))
        if pa >= 0 and pa == pb and za == zb:
            place(scene, tex, pieces['KW%sF' % ka], mx, my, s * 90.0, za); return
        if pa >= 0:
            place(scene, tex, pieces['KW%sE' % ka], mx, my, s * 90.0, za)
        if pb >= 0:
            place(scene, tex, pieces['KW%sO' % kb], mx, my, s * 90.0, zb)
    for y in range(y0, y1):
        for x in range(x0 - x0 % 2, x1, 2):
            bay(x, y, x + 1, y, 0, x + 1, y)
            bay(x + 1, y, x, y, 2, x + 1, y + 1)
    for x in range(x0, x1):
        for y in range(y0 - y0 % 2, y1, 2):
            bay(x, y, x, y + 1, 1, x + 1, y + 1)
            bay(x, y + 1, x, y, 3, x, y + 1)
    # The level's dressing as the kit lays it (AS_KitDecal): door frames, struts, pipes, crates, paint, grime, signs.
    solid = L.blocked(L.carve()[0])
    spots = L.decal_spots(L.carve()[0], L.carve()[1], solid)
    for model, px, py, rot, *_ in L.PROPS:
        if model.startswith('KP'):
            spots.append((model, px, py, rot))
        elif model == 'DOM_Crate':
            spots.append(('KPCrateG' if int(px + py) % 3 else 'KPCrateM', px, py, rot))
    for piece, px, py, rot in spots:
        if piece in pieces and x0 - 3 <= px <= x1 + 3 and y0 - 3 <= py <= y1 + 3:
            place(scene, tex, pieces[piece], px, py, rot, zat(px, py))
    # Railings where the deck meets the open night.
    for y in range(y0, y1):
        for x in range(x0, x1):
            if cell(x, y) != 'o':
                continue
            for s, (nx, ny, mx, my) in enumerate(((x, y - 1, x + .5, y), (x + 1, y, x + 1, y + .5), (x, y + 1, x + .5, y + 1), (x - 1, y, x, y + .5))):
                if floor(nx, ny):
                    place(scene, tex, pieces['KRail'], mx, my, s * 90.0, zat(nx, ny))


def draw_marine(scene, x, y, aim, gun='Rifle', tint=(0.62, 0.72, 0.84), seq='Stand', t=0.0, z=0.0):
    import m3
    from tools import marine as M
    from tools.alien import _posed
    model = m3.loadModel(str(ROOT / ('dist/meshes/Marine%s.m3' % gun)))
    d, e = M.textures()
    dd = np.asarray(d, float) / 255; ee = np.asarray(e, float) / 255
    pos, nrm, uv = _posed(model, seq, t)
    c, s = math.cos(math.radians(aim)), math.sin(math.radians(aim))
    R = np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])
    P = pos @ R.T + (x, y, z); N = nrm @ R.T
    faces = np.asarray(model.divisions[0].faces).reshape(-1, 3)
    for f in faces:
        nn = N[f].mean(0); nn /= np.linalg.norm(nn) + 1e-9
        scene.tri(P[f], uv[f], dd, ee, tint=np.array(tint), normal=nn)
    _, muzzle = M.geometry(gun)
    return np.array([x, y, z]) + R @ np.asarray(muzzle)


def laser(img, cam, start, aim, length, deck=0.0):
    """The laser sight as the script lays it: from the muzzle down to the deck at its far end, with its dot."""
    end = start + np.array([math.cos(math.radians(aim)) * length, math.sin(math.radians(aim)) * length, deck + 0.03 - start[2]])
    a, b = cam.project(start), cam.project(end)
    glow = Image.new('RGB', (W, H)); d = ImageDraw.Draw(glow)
    d.line([tuple(a[:2]), tuple(b[:2])], fill=(150, 18, 14), width=7)
    glow = glow.filter(ImageFilter.GaussianBlur(3))
    core = Image.new('RGB', (W, H)); d = ImageDraw.Draw(core)
    d.line([tuple(a[:2]), tuple(b[:2])], fill=(255, 140, 120), width=1)
    d.ellipse([b[0] - 9, b[1] - 6, b[0] + 9, b[1] + 6], fill=(170, 30, 25))
    dot = core.filter(ImageFilter.GaussianBlur(1.2))
    return img + (np.asarray(glow, float) + np.asarray(dot, float)) / 255


def render(level, tx, ty, aim, gun='Rifle', laser_len=3.5):
    L.use(level)
    floor, room = L.carve()
    rows = L.deck_rows(floor, room)
    from tools import heights
    hts = heights.extend(rows, heights.level_heights(vars(L), rows, L.FLOOR), L.FLOOR)
    rows = hts['rows']
    cz = hts['cellz'] - L.FLOOR

    def zat(x, y):
        return float(cz[min(max(int(y), 0), cz.shape[0] - 1), min(max(int(x), 0), cz.shape[1] - 1)])
    tex = load_textures()
    pieces = L.kit_pieces()
    pieces.update(L.paint_pieces(sorted(L.paint_names())))
    pieces.update(L.sign_pieces(sorted(L.sign_names())))
    # The camera leans toward the cursor (AS_LeanUpdate): with the cursor laser_len ahead, about this much.
    cam = Camera(tx + math.cos(math.radians(aim)) * 0.6, ty + math.sin(math.radians(aim)) * 0.6, zat(tx, ty))
    scene = Scene(cam)
    lay_level(scene, tex, pieces, rows, tx, ty, hts)
    muzzle = draw_marine(scene, tx, ty, aim, gun, z=zat(tx, ty))
    lamps = [(x, y, k.replace('big', ''), 'big' in k, zat(x, y)) for x, y, k, _ in L.LIGHTS + L.corridor_lamps(*L.carve()) + L.pit_lamps(*L.carve()) if abs(x - tx) < 16 and abs(y - ty) < 16]
    img = scene.shade(lamps)
    ex, ey = tx + math.cos(math.radians(aim)) * laser_len, ty + math.sin(math.radians(aim)) * laser_len
    img = laser(img, cam, muzzle, aim, laser_len, zat(ex, ey))
    return Image.fromarray(np.clip(img * 255, 0, 255).astype(np.uint8))


def main():
    args = sys.argv[1:]
    level = args[0] if args else 'landingbay'
    shots = [tuple(float(v) for v in a.split(',')) for a in args[1:]] or [(51.0, 8.0, 135.0), (36.0, 7.0, 0.0), (31.0, 40.0, 60.0), (30.0, 64.0, 200.0)]
    frames = [render(level, *s) for s in shots]
    cols = 2
    sheet = Image.new('RGB', (W * cols, H * ((len(frames) + 1) // cols)))
    for i, im in enumerate(frames):
        sheet.paste(im, ((i % cols) * W, (i // cols) * H))
    out = ROOT / ('dist/scene-%s.png' % level)
    sheet.save(out)
    print(out)


if __name__ == '__main__':
    main()
