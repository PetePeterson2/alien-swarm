"""Hull kit for the derelict: procedural textures and static M3 meshes.

The M3 writer is ../../Documents/sc2map/doodad-royale/tools/battleground_citykit.py's
``write_m3`` (proven in the client for PUBG's city arena), with two additions:
an optional emissive layer per part (light strips and screens that glow in the
dark) and per-part material flags (the ceilings cast no shadow). The geometry
container is a retained crate model (tools/template/container.m3) whose mesh,
materials and bounds are all replaced: only its bind data is reused.

Textures are drawn here with NumPy and packed as DXT1 DDS with mips. Row 0 of
an image is the TOP of a wall.
"""
import copy, io, math, struct, sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools/m3-reader'))
CONTAINER = ROOT / 'tools/template/container.m3'
TEX_DIR = 'Derelict\\'
NO_SHADOW_CAST = 0x20
UNLIT = 0x4 | 0x8 | 0x10 | 0x20 | 0x40 | 0x80     # tools/fx.py's: unshaded, two-sided, no shadows, no hit test
MULTIPLY = 4
ADD = 2


# ------------------------------------------------------------------ DDS
def dds_bytes(image, mips=True):
    image = image.convert('RGB')
    w, h = image.size
    levels = []
    while True:
        buffer = io.BytesIO(); image.save(buffer, format='DDS', pixel_format='DXT1')
        data = buffer.getvalue()
        assert data[:4] == b'DDS '
        levels.append(data[128:])
        if not mips or (image.size[0] <= 4 and image.size[1] <= 4):
            break
        image = image.resize((max(4, image.size[0] // 2), max(4, image.size[1] // 2)), Image.Resampling.BOX)
    buffer = io.BytesIO(); Image.new('RGB', (w, h)).save(buffer, format='DDS', pixel_format='DXT1')
    head = bytearray(buffer.getvalue()[:128])
    struct.pack_into('<I', head, 8, struct.unpack_from('<I', head, 8)[0] | 0x20000)
    struct.pack_into('<I', head, 28, len(levels))
    struct.pack_into('<I', head, 108, struct.unpack_from('<I', head, 108)[0] | 0x400008)
    return bytes(head) + b''.join(levels)


def dds_rgba(image):
    """Uncompressed 32-bit DDS (UI art that needs alpha)."""
    image = image.convert('RGBA'); w, h = image.size
    head = bytearray(128)
    head[0:4] = b'DDS '
    struct.pack_into('<7I', head, 4, 124, 0x1 | 0x2 | 0x4 | 0x1000 | 0x8, h, w, w * 4, 0, 1)
    struct.pack_into('<2I', head, 76, 32, 0x41)                       # pixel format: RGB | ALPHAPIXELS
    struct.pack_into('<5I', head, 84, 0, 32, 0x00ff0000, 0x0000ff00, 0x000000ff)
    struct.pack_into('<I', head, 104, 0xff000000)
    struct.pack_into('<I', head, 108, 0x1000)
    a = np.asarray(image)
    bgra = a[:, :, [2, 1, 0, 3]].copy()
    return bytes(head) + bgra.tobytes()


# ------------------------------------------------------------- textures
def _noise(size, scale, seed, octaves=4, shape=None):
    """Tileable value noise in [0, 1]; ``shape`` (h, w) for non-square tiles."""
    h, w = shape or (size, size)
    r = np.random.default_rng(seed)
    out = np.zeros((h, w)); amp = 1.0; total = 0.0
    for o in range(octaves):
        cy = max(2, int(h / scale * 2 ** o)); cx = max(2, int(w / scale * 2 ** o))
        grid = r.random((cy, cx))
        grid = np.vstack([grid, grid[:1]]); grid = np.hstack([grid, grid[:, :1]])
        ty = np.linspace(0, cy, h, endpoint=False); tx = np.linspace(0, cx, w, endpoint=False)
        iy = ty.astype(int); fy = ty - iy; fy = fy * fy * (3 - 2 * fy)
        ix = tx.astype(int); fx = tx - ix; fx = fx * fx * (3 - 2 * fx)
        a = grid[iy][:, ix] * (1 - fx)[None] + grid[iy][:, ix + 1] * fx[None]
        b = grid[iy + 1][:, ix] * (1 - fx)[None] + grid[iy + 1][:, ix + 1] * fx[None]
        out += amp * (a * (1 - fy)[:, None] + b * fy[:, None]); total += amp; amp *= 0.5
    return out / total


def _img(a):
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def _grime(a, seed, strength=0.35):
    h, w = a.shape[:2]
    n = _noise(0, 48, seed, 4, (h, w))
    streak = _noise(0, 5, seed + 1, 1, (1, w)).repeat(h, 0) * np.linspace(0.2, 1.0, h)[:, None] ** 1.5
    dirt = np.clip(n - 0.45, 0, 1) * 1.6 + streak * 0.5
    return a * (1 - strength * np.clip(dirt, 0, 1))[..., None]


def _hazard(a, y0, y1, seed=0):
    h, w = a.shape[:2]
    yy, xx = np.mgrid[y0:y1, 0:w]
    stripe = ((xx + yy) // 18) % 2 == 0
    band = np.where(stripe[..., None], np.array((150, 118, 30), float), np.array((22, 22, 20), float))
    wear = _noise(0, 12, seed + 7, 2, (y1 - y0, w))[..., None]
    a[y0:y1] = band * (0.6 + 0.5 * wear)


def tex_ceiling(seed=6, size=512):
    """The ceiling the third-person camera sees: pale grey panels a unit square with bevelled seams, a vent grille
    in some, and one long recessed lamp across the four-unit tile (lit in the 'ceiling' variant)."""
    n = _noise(size, 60, seed)
    a = np.array((96, 102, 108), float)[None, None] * (0.8 + 0.3 * n[..., None])
    emis = np.zeros((size, size, 3))
    q = size // 4
    for k in range(0, size, q):
        a[k:k + 3] *= 0.45; a[:, k:k + 3] *= 0.45
        a[k + 3:k + 5] *= 1.2; a[:, k + 3:k + 5] *= 1.2
    r = np.random.default_rng(seed)
    for _ in range(3):
        tx, ty = r.integers(0, 4) * q, r.choice([0, 3]) * q
        for y in range(ty + 24, ty + q - 24, 9):
            a[y:y + 4, tx + 24:tx + q - 24] *= 0.35
    a[size // 2 - 20:size // 2 + 20, 60:size - 60] = (40, 42, 44)
    a[size // 2 - 12:size // 2 + 12, 70:size - 70] = (200, 208, 214)
    emis[size // 2 - 12:size // 2 + 12, 70:size - 70] = (150, 160, 170)
    return _img(_grime(a, seed + 3, 0.25)), _img(emis)


def tex_plain(rgb, size=16):
    return Image.new('RGB', (size, size), rgb)


def hull_textures():
    """name -> (diffuse, emissive or None): wall bays, trim and caps (tools/wallart.py), the floors and
    decals (tools/deckart.py), and the ceilings seen from the third-person camera."""
    from tools import wallart, deckart, propart
    t = wallart.textures()
    t.update(deckart.textures())
    t.update(propart.textures())
    t['ceiling'] = tex_ceiling()
    t['ceiling_dark'] = (tex_ceiling(7)[0], None)
    return t


def multiply_textures():
    """name -> image: decals multiplied over the deck (white leaves it alone)."""
    from tools import deckart
    return {k: f() for k, f in deckart.MUL_DECALS.items()}


def texture_path(name):
    return TEX_DIR + name + '.dds'


def pack_textures(files, textures, multiply=None):
    for name, image in (multiply or {}).items():
        files['Base.SC2Assets/' + (TEX_DIR + name + '.dds').replace('\\', '/')] = dds_bytes(image)
    for name, (diffuse, emissive) in textures.items():
        files['Base.SC2Assets/' + (TEX_DIR + name + '.dds').replace('\\', '/')] = dds_bytes(diffuse)
        if emissive is not None:
            files['Base.SC2Assets/' + (TEX_DIR + name + '_e.dds').replace('\\', '/')] = dds_bytes(emissive)


# ------------------------------------------------------------------ mesh
class ShipModel:
    """Polygons of one M3 grouped by material key (texture, two-sided, flags), in map coordinates."""

    def __init__(self, name, origin):
        self.name = name
        self.origin = np.array(origin, float)
        self.parts = {}

    def poly(self, key, p, uv):
        p = np.asarray(p, float); uv = np.asarray(uv, float)
        n = np.cross(p[1] - p[0], p[-1] - p[0]); length = np.linalg.norm(n)
        if length < 1e-9:
            return
        uv = uv - np.floor(uv.min(0))
        part = self.parts.setdefault(key, dict(pos=[], nrm=[], uv=[], tri=[]))
        base = len(part['pos'])
        part['pos'].extend(p); part['nrm'].extend([n / length] * len(p)); part['uv'].extend(uv)
        part['tri'].extend((base, base + i, base + i + 1) for i in range(1, len(p) - 1))

    def quad(self, key, a, b, c, d, uv):
        self.poly(key, [a, b, c, d], uv)

    def export(self, emissive):
        out = []
        for key, d in self.parts.items():
            tex, two, flags = key[:3]
            blend = key[3] if len(key) > 3 else 0
            if not d['pos']:
                continue
            out.append((texture_path(tex), texture_path(tex + '_e') if tex in emissive else '', two, flags,
                        np.array(d['pos']) - self.origin, np.array(d['nrm']), np.array(d['uv']), np.array(d['tri']), blend))
        return out


def _fixed8(v):
    return np.clip(np.rint((np.asarray(v, float) + 1) / 2 * 255), 0, 255).astype(np.uint8)


def _clone(value, m3):
    if isinstance(value, m3.M3Structure):
        out = copy.copy(value)
        for key, item in value.__dict__.items():
            if key != 'structureDescription':
                setattr(out, key, _clone(item, m3))
        return out
    if isinstance(value, list):
        return [_clone(item, m3) for item in value]
    if isinstance(value, bytearray):
        return bytearray(value)
    return value


def write_m3(name, parts, path=None):
    """Static multi-material M3 -> bytes. ``parts``: (diffuse, emissive, two-sided, flags, pos, nrm, uv, tri)."""
    import m3
    model = m3.loadModel(str(CONTAINER))
    for value in [model.bones[0].scale.initValue, model.bones[0].scale.nullValue]:
        value.x = 1.0; value.y = 1.0; value.z = 1.0
    matrix = model.absoluteInverseBoneRestPositions[0].matrix
    for row in 'xyzw':
        for col in 'xyzw':
            setattr(getattr(matrix, row), col, float(row == col))
    desc = m3.structures['VertexFormat' + hex(model.vFlags)].getVersion(0)
    assert desc.size == 32
    division = model.divisions[0]
    region0, object0, material0, reference0 = division.regions[0], division.objects[0], model.standardMaterials[0], model.materialReferences[0]
    blobs, faces, regions, objects, materials, references, everything = [], [], [], [], [], [], []
    first = 0
    chunks = []
    for tex, etex, two, flags, pos, normal, uv, tri, *rest in parts:
        blend = rest[0] if rest else 0
        tri = np.asarray(tri, int)
        if len(pos) <= 60000:
            chunks.append((tex, etex, two, flags, pos, normal, uv, tri, blend)); continue
        for k in range(0, len(tri), 20000):
            t = tri[k:k + 20000]; used = np.unique(t); remap = np.full(len(pos), -1); remap[used] = np.arange(len(used))
            chunks.append((tex, etex, two, flags, pos[used], normal[used], uv[used], remap[t], blend))
    for index, (tex, etex, two, flags, pos, normal, uv, tri, blend) in enumerate(chunks):
        pos = np.asarray(pos, '<f4'); n = len(pos)
        assert 0 < n <= 65535 and tri.min() >= 0 and tri.max() < n
        uv = np.asarray(uv, float)
        assert np.abs(uv).max() < 15.9, (name, tex, float(np.abs(uv).max()))
        vertex = np.zeros((n, 32), np.uint8)
        vertex[:, 0:12] = pos.view(np.uint8).reshape(n, 12)
        vertex[:, 12] = 255
        vertex[:, 20:23] = _fixed8(normal)
        vertex[:, 23] = 255
        vertex[:, 24:28] = np.rint(uv * 2048).astype('<i2').view(np.uint8).reshape(n, 4)
        vertex[:, 28:31] = _fixed8(np.tile([1.0, 0.0, 0.0], (n, 1)))
        vertex[:, 31] = 255
        blobs.append(vertex.tobytes())
        r = _clone(region0, m3)
        r.firstVertexIndex = first; r.numberOfVertices = n
        r.firstFaceVertexIndexIndex = len(faces); r.numberOfFaceVertexIndices = tri.size
        r.numberOfBones = 1; r.firstBoneLookupIndex = 0; r.numberOfBoneLookupIndices = 1; r.rootBoneIndex = 0
        regions.append(r)
        faces.extend(int(v) for v in tri.reshape(-1))
        o = _clone(object0, m3); o.regionIndex = index; o.materialReferenceIndex = index; objects.append(o)
        mat = _clone(material0, m3)
        mat.name = 'AS%s_%d' % (name, index)
        mat.flags = (mat.flags | 8) if two else (mat.flags & ~8)
        mat.flags |= flags
        mat.blendMode = blend
        for key, value in mat.__dict__.items():
            if key.endswith('Layer'):
                for layer in value:
                    layer.imagePath = ''
        mat.diffuseLayer[0].imagePath = tex
        mat.diffuseLayer[0].flags |= 0xc
        if etex and mat.emissiveLayer:
            mat.emissiveLayer[0].imagePath = etex
            mat.emissiveLayer[0].flags |= 0xc
            mat.emisMult = 1.6
        materials.append(mat)
        ref = _clone(reference0, m3); ref.materialType = 1; ref.materialIndex = index; references.append(ref)
        first += n
        everything.append(pos.astype(float))
    model.vertices = bytearray(b''.join(blobs))
    division.faces = faces; division.regions = regions; division.objects = objects
    model.standardMaterials = materials; model.materialReferences = references
    bounds = np.concatenate(everything)

    def bound(b):
        for key, low, high in zip('xyz', bounds.min(0) - .1, bounds.max(0) + .1):
            setattr(b.minBorder, key, float(low)); setattr(b.maxBorder, key, float(high))
        b.radius = float(np.linalg.norm(bounds, axis=1).max() + .1)
    bound(model.boundings)
    for seq in model.sequences:
        bound(seq.boundingSphere)
    bound(division.msec[0].bounding.initValue); bound(division.msec[0].bounding.nullValue)
    model.modelName = 'AS' + name
    out = Path(path) if path else ROOT / 'dist/meshes' / (name + '.m3')
    out.parent.mkdir(parents=True, exist_ok=True)
    m3.saveAndInvalidateModel(model, str(out))
    m3.loadModel(str(out))
    return out.read_bytes()

