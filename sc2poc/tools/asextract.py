"""Extract reference numbers from Alien Swarm's installed maps into tools/asdata/<map>.json.

    py tools/asextract.py              every campaign map in the Steam install
    py tools/asextract.py asi-jac1-landingbay_01

For each map it writes:
* the floor, rasterised from the BSP's up-facing faces (ramps by their planes, displacements as quads),
  and the walkable part of it, flooded from the map's nav nodes, player starts and spawners (a step
  may rise 20 units, or 112 by a stair prop), as 40-unit cells: the top floor height of every cell,
  and the walkable fraction;
* the gameplay entities (spawners, triggers, doors, buttons, logic, paths, lights, templates ...) with
  their keys, world boxes and output connections;
* the stair and railing props.

Only numbers and names go into the files; nothing of Valve's is shipped in the SC2 map.
"""
from pathlib import Path
import base64, json, sys, zlib
from collections import deque
import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tools.asbsp import BSP, SURF_NODRAW

MAPS_DIR = Path(r'C:\Program Files (x86)\Steam\steamapps\common\Alien Swarm\swarm\maps')
CAMPAIGN = ['asi-jac1-landingbay_01', 'asi-jac1-landingbay_02', 'asi-jac2-deima', 'asi-jac3-rydberg',
            'asi-jac4-residential', 'asi-jac6-sewerjunction', 'asi-jac7-timorstation']
OUT = Path(__file__).resolve().parent / 'asdata'
PX = 10            # raster units per pixel
CELL = 40          # units per stored cell (half a port cell)
STEP = 20          # a walkable step
STAIR_STEP = 112   # across a stair prop
GEOM = {'func_brush', 'func_door', 'func_movelinear', 'func_tracktrain', 'func_breakable', 'func_physbox', 'func_wall',
        'func_illusionary', 'func_rotating', 'func_breakable_surf', 'func_door_rotating', 'func_lookdoor'}
SEEDS = ('info_node', 'info_node_marine_hint', 'info_node_hint', 'info_player_start', 'asw_spawner')
DROP = ('info_node', 'info_overlay', 'keyframe_rope', 'move_rope', 'func_detail', 'infodecal', 'info_lighting',
        'env_cubemap', 'info_null', 'worldspawn', 'prop_detail')
KEEP_PROPS = ('stair', 'railing')


def pack_grid(a, dtype):
    return base64.b64encode(zlib.compress(np.ascontiguousarray(a, dtype=dtype).tobytes(), 9)).decode()


def unpack_grid(s, dtype, shape):
    return np.frombuffer(zlib.decompress(base64.b64decode(s)), dtype=dtype).reshape(shape)


def floor_raster(b):
    """(z per pixel or nan, x0, y1): the top up-facing floor at each pixel; ramps follow their planes."""
    morg = b.model_origin()
    geom = {0} | {int(e['model'][1:]) for e in b.entities if e.get('classname') in GEOM and e.get('model', '').startswith('*')}
    disp = {int(d['mapface']) for d in b.dispinfo}
    polys = []
    for i, poly in enumerate(b.face_polys):
        name = b.face_name[i]
        if (b.face_model[i] not in geom or i in disp or len(poly) < 3 or name.startswith('tools/')
                or b.face_flags[i] & SURF_NODRAW or b.face_normal[i][2] <= 0.3):
            continue
        p = poly + morg[b.face_model[i]]
        polys.append((p, b.face_normal[i].astype(np.float64)))
    for q in b.displacement_quads():
        n = np.cross(q[1] - q[0], q[3] - q[0])
        if np.linalg.norm(n) and abs(n[2] / np.linalg.norm(n)) > 0.7:
            polys.append((q, n / np.linalg.norm(n) * np.sign(n[2])))
    allp = np.concatenate([p for p, _ in polys])
    x0, y0 = np.floor(allp[:, :2].min(0) / CELL) * CELL - CELL
    x1, y1 = np.ceil(allp[:, :2].max(0) / CELL) * CELL + CELL
    W, H = int((x1 - x0) / PX), int((y1 - y0) / PX)
    img = Image.new('I', (W, H), 0)
    d = ImageDraw.Draw(img)
    polys.sort(key=lambda pn: pn[0][:, 2].mean())
    for k, (p, _) in enumerate(polys):
        pts = [((x - x0) / PX, (y1 - y) / PX) for x, y, _ in p]
        d.polygon(pts, fill=k + 1)
    ids = np.array(img, dtype=np.int64)
    # z from the winning face's plane at each pixel centre.
    planes = np.array([[n[0], n[1], n[2], float(np.dot(n, p[0]))] for p, n in polys])
    yy, xx = np.mgrid[0:H, 0:W]
    wx, wy = x0 + (xx + 0.5) * PX, y1 - (yy + 0.5) * PX
    pl = planes[np.maximum(ids - 1, 0)]
    z = (pl[..., 3] - pl[..., 0] * wx - pl[..., 1] * wy) / pl[..., 2]
    z[ids == 0] = np.nan
    return z, x0, y1


def walkable(b, z, x0, y1):
    H, W = z.shape
    to_px = lambda x, y: (int((x - x0) / PX), int((y1 - y) / PX))
    stair = np.zeros_like(z, bool)
    for (x, y, _), _, model in b.static_props:
        if 'stair' in model:
            cx, cy = to_px(x, y)
            r = 112 // PX
            stair[max(0, cy - r):cy + r + 1, max(0, cx - r):cx + r + 1] = True
    walk = np.zeros_like(z, bool)
    q = deque()
    for e in b.entities:
        if e.get('classname') in SEEDS:
            o = b.origin(e)
            if o is None:
                continue
            px, py = to_px(o[0], o[1])
            if 0 <= px < W and 0 <= py < H and not np.isnan(z[py, px]) and abs(z[py, px] - o[2]) <= 80 and not walk[py, px]:
                walk[py, px] = True
                q.append((py, px))
    seeds = len(q)
    while q:
        y, x = q.popleft()
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            yy, xx = y + dy, x + dx
            if 0 <= yy < H and 0 <= xx < W and not walk[yy, xx] and not np.isnan(z[yy, xx]):
                tol = STAIR_STEP if (stair[yy, xx] or stair[y, x]) else STEP
                if abs(z[yy, xx] - z[y, x]) <= tol:
                    walk[yy, xx] = True
                    q.append((yy, xx))
    return walk, seeds


def cells(z, walk, x0, y1):
    """40-unit cells, south row first: top floor z (int16, -32768 none), median walkable z, walkable fraction (0..100)."""
    k = CELL // PX
    H, W = z.shape[0] // k, z.shape[1] // k
    # The raster's row 0 is its north edge; flip so row 0 is the south edge, then group k x k pixels a cell.
    zz = z[:H * k, :W * k][::-1].reshape(H, k, W, k).transpose(0, 2, 1, 3).reshape(H, W, k * k)
    ww = walk[:H * k, :W * k][::-1].reshape(H, k, W, k).transpose(0, 2, 1, 3).reshape(H, W, k * k)
    has = ~np.isnan(zz).all(-1)
    top = np.where(has, np.round(np.where(np.isnan(zz), -1e9, zz).max(-1)), -32768)
    frac = (ww.mean(-1) * 100).round()
    wz = np.where(ww, zz, np.nan)
    anyw = ww.any(-1)
    with np.errstate(all='ignore'):
        med = np.nanmedian(np.where(anyw[..., None], wz, 0.0), -1)
    walkz = np.where(anyw, np.round(med), -32768)
    y0 = y1 - H * k * PX
    return top.astype(np.int16), walkz.astype(np.int16), frac.astype(np.uint8), y0


def entity_table(b):
    out = []
    for e in b.entities:
        cl = e.get('classname', '')
        if not cl or cl.startswith(DROP) or cl in DROP:
            continue
        row = {'class': cl}
        if e.get('targetname'):
            row['name'] = e['targetname']
        o = b.origin(e)
        if o:
            row['origin'] = [round(v, 1) for v in o]
        box = b.bounds(e)
        if box:
            row['box'] = list(box)
        keys = {k: v for k, v in e.items() if k not in ('classname', 'targetname', 'origin', 'model', 'hammerid', '_io')}
        if keys:
            row['keys'] = keys
        if e['_io']:
            row['io'] = [[k, v] for k, v in e['_io']]
        out.append(row)
    return out


def extract(name):
    b = BSP(MAPS_DIR / (name + '.bsp'))
    z, x0, y1 = floor_raster(b)
    walk, seeds = walkable(b, z, x0, y1)
    top, walkz, frac, y0 = cells(z, walk, x0, y1)
    H, W = top.shape
    props = [{'model': m.rsplit('/', 1)[-1], 'origin': [round(v, 1) for v in o], 'yaw': round(a[1], 1)}
             for o, a, m in b.static_props if any(k in m for k in KEEP_PROPS)]
    data = {
        'map': name,
        'cell': CELL, 'x0': float(x0), 'y0': float(y0), 'w': W, 'h': H,
        'note': 'Grids are row-major from the south-west cell; cell (i, j) spans x0+CELL*i .. +CELL, y0+CELL*j .. +CELL.',
        'walkable_cells80': round(float(walk.sum()) * PX * PX / 6400, 1),
        'seeds': seeds,
        'top_z': pack_grid(top, '<i2'), 'walk_z': pack_grid(walkz, '<i2'), 'walk_pct': pack_grid(frac, 'u1'),
        'entities': entity_table(b),
        'props': props,
    }
    OUT.mkdir(exist_ok=True)
    (OUT / (name + '.json')).write_text(json.dumps(data, separators=(',', ':')), encoding='utf-8')
    return data


def load(name):
    """A map's extracted data, with the grids unpacked to numpy (h, w) arrays (row 0 is the south edge)."""
    d = json.loads((OUT / (name + '.json')).read_text(encoding='utf-8'))
    shape = (d['h'], d['w'])
    d['top_z'] = unpack_grid(d['top_z'], '<i2', shape).astype(float)
    d['walk_z'] = unpack_grid(d['walk_z'], '<i2', shape).astype(float)
    d['walk_pct'] = unpack_grid(d['walk_pct'], 'u1', shape)
    for k in ('top_z', 'walk_z'):
        d[k][d[k] == -32768] = np.nan
    return d


def main():
    names = sys.argv[1:] or CAMPAIGN
    for name in names:
        d = extract(name)
        size = (OUT / (name + '.json')).stat().st_size
        print('%-28s %4dx%-4d cells of %d u, walkable %6.1f cells of 80 u, %4d seeds, %4d entities, %3d props, %6.1f KB'
              % (name, d['w'], d['h'], CELL, d['walkable_cells80'], d['seeds'], len(d['entities']), len(d['props']), size / 1024))


if __name__ == '__main__':
    main()
