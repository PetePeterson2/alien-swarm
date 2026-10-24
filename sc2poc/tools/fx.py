"""Unlit additive effect meshes: tracers, muzzle flashes, hit bursts, flame puffs, laser sight, tesla arcs.

After ../../Documents/sc2map/doodad-royale/tools/battleground_fx.py, whose
finding was that pooled units carrying unshaded, two-sided additive meshes draw
on every graphics setting where small native effect models may not. A model's
+X is its unit's facing; tracers and the laser are one unit long along +X so
the script stretches them with UnitSetScale.
"""
import math, sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools/m3-reader'))
UNLIT = 0x4 | 0x8 | 0x10 | 0x20 | 0x40 | 0x80
ADD = 2
MULTIPLY = 4                      # darkens what is under it: PUBG's night side proved it draws
TEX = 'Derelict\\Fx\\'


def mesh(name, triangles, texture, blend=ADD):
    import m3
    model = m3.loadModel(str(ROOT / 'tools/template/container.m3'))
    for value in [model.bones[0].scale.initValue, model.bones[0].scale.nullValue]:
        value.x = 1.0; value.y = 1.0; value.z = 1.0
    matrix = model.absoluteInverseBoneRestPositions[0].matrix
    for row in 'xyzw':
        for col in 'xyzw':
            setattr(getattr(matrix, row), col, float(row == col))
    desc = m3.structures['VertexFormat' + hex(model.vFlags)].getVersion(0)
    vertices = []
    for tri in triangles:
        positions = np.array([p for p, uv in tri])
        normal = np.cross(positions[1] - positions[0], positions[2] - positions[0])
        normal /= max(1e-9, np.linalg.norm(normal))
        for pos, uv in tri:
            v = desc.createInstance()
            for key, val in zip('xyz', pos):
                setattr(v.position, key, float(val))
            for key, val in zip('xyz', normal):
                setattr(v.normal, key, float(val))
            v.boneWeight0 = 255; v.boneLookupIndex0 = 0; v.tangent.x = 1.0; v.sign = 1.0
            v.uv0.x = int(uv[0] * 2048); v.uv0.y = int(uv[1] * 2048)
            vertices.append(v)
    model.vertices = bytearray(desc.instancesToBytes(vertices))
    d = model.divisions[0]; r = d.regions[0]; o = d.objects[0]
    r.firstVertexIndex = 0; r.numberOfVertices = len(vertices); r.firstFaceVertexIndexIndex = 0; r.numberOfFaceVertexIndices = len(vertices)
    r.numberOfBones = 1; r.firstBoneLookupIndex = 0; r.numberOfBoneLookupIndices = 1
    d.faces = list(range(len(vertices))); d.regions = [r]; d.objects = [o]; o.regionIndex = 0; o.materialReferenceIndex = 0
    bounds = np.array([pos for tri in triangles for pos, uv in tri])

    def bound(b):
        for key, low, high in zip('xyz', bounds.min(0) - .1, bounds.max(0) + .1):
            setattr(b.minBorder, key, float(low)); setattr(b.maxBorder, key, float(high))
        b.radius = float(np.linalg.norm(bounds, axis=1).max() + .1)
    bound(model.boundings)
    for seq in model.sequences:
        bound(seq.boundingSphere)
    bound(d.msec[0].bounding.initValue); bound(d.msec[0].bounding.nullValue)
    mat = model.standardMaterials[0]; mat.name = 'ASFx' + name; mat.flags = UNLIT; mat.blendMode = blend
    for key, value in mat.__dict__.items():
        if key.endswith('Layer'):
            for layer in value:
                layer.imagePath = ''
    mat.diffuseLayer[0].imagePath = TEX + texture
    model.standardMaterials = [mat]; model.materialReferences = model.materialReferences[:1]; model.materialReferences[0].materialIndex = 0
    model.modelName = 'ASFx' + name
    out = ROOT / 'dist/meshes' / ('Fx' + name + '.m3')
    out.parent.mkdir(parents=True, exist_ok=True)
    m3.saveAndInvalidateModel(model, str(out))
    m3.loadModel(str(out))
    return out.read_bytes()


def quad(tris, a, b, c, d, uvs=((0, 0), (1, 0), (1, 1), (0, 1))):
    tris.extend([[(a, uvs[0]), (b, uvs[1]), (c, uvs[2])], [(a, uvs[0]), (c, uvs[2]), (d, uvs[3])]])


def streak(tris, half):
    """Two crossed quads from x=0 to x=1, ``half`` wide: reads from above and from behind."""
    quad(tris, (0, -half, 0), (1, -half, 0), (1, half, 0), (0, half, 0), ((0, 0), (1, 0), (1, 1), (0, 1)))
    quad(tris, (0, 0, -half), (1, 0, -half), (1, 0, half), (0, 0, half), ((0, 0), (1, 0), (1, 1), (0, 1)))


LASER_DROP = 0.52


def beam(tris, half, drop):
    """Two crossed quads from the origin to (0, -1, -drop): along a unit model's forward, sloping down."""
    quad(tris, (-half, 0, 0), (-half, -1, -drop), (half, -1, -drop), (half, 0, 0), ((0, 0), (1, 0), (1, 1), (0, 1)))
    quad(tris, (0, 0, -half), (0, -1, -drop - half), (0, -1, -drop + half), (0, 0, half), ((0, 0), (1, 0), (1, 1), (0, 1)))


def sprite(tris, r=0.5):
    quad(tris, (-r, 0, r), (r, 0, r), (r, 0, -r), (-r, 0, -r))
    quad(tris, (0, -r, r), (0, r, r), (0, r, -r), (0, -r, -r))
    quad(tris, (-r, r, 0), (r, r, 0), (r, -r, 0), (-r, -r, 0))


def build():
    """{archive path: bytes} of every effect model and texture."""
    from tools.shipkit import dds_bytes
    out = {}
    size = 128
    yy, xx = np.mgrid[0:size, 0:size].astype(np.float32)
    u = (xx - 63.5) / 63.5; v = (yy - 63.5) / 63.5
    r = np.sqrt(u * u + v * v); ang = np.arctan2(v, u)

    def save(name, rgb):
        out['Base.SC2Assets/' + (TEX + name).replace('\\', '/')] = dds_bytes(Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8)))

    # Tracer: bright head at +X fading back along the length, hot white core.
    w, h = 128, 16
    along = np.linspace(0, 1, w)[None, :]; across = 1 - np.abs(np.linspace(-1, 1, h))[:, None]
    g = (along ** 1.4) * across ** 1.5
    save('tracer.dds', np.dstack([255 * g, 235 * g, 170 * g * (0.6 + 0.4 * across)]))
    # Laser sight, after Alien Swarm's: a hot thin core in a soft red halo, even down its length and
    # easing out only at the very end, where its dot sits. Smooth across, so it never shimmers as it turns.
    w2, h2 = 128, 64
    along2 = np.linspace(0, 1, w2)[None, :]; x2 = np.linspace(-1, 1, h2)[:, None]
    core = np.exp(-(x2 / 0.07) ** 2); halo = np.exp(-(x2 / 0.38) ** 2)
    ends = np.clip(along2 / 0.03, 0, 1) * np.clip((1 - along2) / 0.06, 0, 1) ** 0.6
    save('laser.dds', np.dstack([(255 * core + 170 * halo) * ends, (150 * core + 18 * halo) * ends, (130 * core + 14 * halo) * ends]))
    # Its dot where it lands: a small hot point in a red glow.
    g = np.exp(-(r / 0.16) ** 2) + 0.5 * np.exp(-(r / 0.5) ** 2)
    save('laserdot.dds', np.dstack([255 * np.clip(g, 0, 1), 90 * np.clip(g - 0.6, 0, 1) + 20 * g, 70 * np.clip(g - 0.6, 0, 1) + 14 * g]))
    # Tesla arc: jagged bright lines across the strip.
    arc = np.zeros((32, 256))
    rng = np.random.default_rng(4)
    for k in range(3):
        y = 16.0
        for x in range(256):
            y = np.clip(y + rng.normal(0, 2.2), 3, 28)
            arc[int(y) - 1:int(y) + 2, x] += 1.0 - 0.25 * k
    arc = np.clip(arc, 0, 1)
    out['Base.SC2Assets/' + (TEX + 'arc.dds').replace('\\', '/')] = dds_bytes(Image.fromarray(np.dstack([140 * arc, 200 * arc, 255 * arc]).astype(np.uint8)))
    # Muzzle flash: star with hot core.
    core = np.clip(1 - r / 0.42, 0, 1) ** 1.6
    spikes = np.clip(1 - r / (0.34 + 0.62 * np.abs(np.cos(ang * 3)) ** 10), 0, 1) ** 1.2
    glow = np.clip(1 - r, 0, 1) ** 3 * 0.45
    g = np.clip(core * 1.2 + spikes * 0.9 + glow, 0, 1)
    save('flash.dds', np.dstack([g * 255, g * (175 + 80 * core), g * (95 + 160 * core)]))
    # Burst: soft round, tinted per use.
    g = np.clip(np.clip(1 - r, 0, 1) ** 1.5 + np.clip(1 - np.abs(r - 0.55) / 0.2, 0, 1) * 0.6, 0, 1)
    save('burst.dds', np.dstack([g * 255, g * 255, g * 255]))
    # Flame puff: ragged orange ball.
    n = np.random.default_rng(9).random((16, 16))
    n = np.asarray(Image.fromarray((n * 255).astype(np.uint8)).resize((size, size), Image.Resampling.BICUBIC)).astype(np.float32) / 255
    g = np.clip(1 - r / (0.6 + 0.35 * n), 0, 1) ** 1.3
    save('flame.dds', np.dstack([255 * g, (90 + 120 * g) * g, 30 * g ** 3]))
    # Ground ring for blasts.
    ring = np.clip(1 - np.abs(r - 0.9) / 0.08, 0, 1) + np.clip(1 - r, 0, 1) ** 2 * 0.25
    save('ring.dds', np.dstack([255 * ring, 255 * ring, 255 * ring]))

    # Floor splats of alien blood: multiplied over the deck, so white leaves it untouched and
    # the blotches darken it toward a sick yellow-green. Two shapes for variety.
    for k, seed in ((1, 21), (2, 37)):
        rng = np.random.default_rng(seed)
        size2 = 256
        yy2, xx2 = np.mgrid[0:size2, 0:size2].astype(np.float32)
        cover = np.zeros((size2, size2), np.float32)
        blobs = [(128, 128, 54)] + [(128 + rng.normal(0, 40), 128 + rng.normal(0, 40), rng.uniform(10, 34)) for _ in range(7)]
        blobs += [(128 + rng.normal(0, 85), 128 + rng.normal(0, 85), rng.uniform(3, 9)) for _ in range(26)]
        # A spray streak off to one side (+X: the direction the shot travelled).
        blobs += [(128 + d, 128 + rng.normal(0, 6), 14 - d * 0.1) for d in range(20, 120, 8)]
        for bx, by, br in blobs:
            cover = np.maximum(cover, np.clip(1.4 - np.hypot(xx2 - bx, yy2 - by) / br, 0, 1))
        ragged = np.asarray(Image.fromarray((np.random.default_rng(seed + 1).random((32, 32)) * 255).astype(np.uint8)).resize((size2, size2), Image.Resampling.BICUBIC)).astype(np.float32) / 255
        cover = np.clip(cover * (0.75 + 0.5 * ragged), 0, 1)
        edge = np.clip(1 - np.abs(cover - 0.5) * 4, 0, 1) * 0.25
        tint = np.array((0.42, 0.55, 0.12))
        rgb = 255 * (1 - cover[..., None] * (1 - tint[None, None]) - edge[..., None] * 0.3)
        save('splat%d.dds' % k, rgb)
        # Its glow, added over the darkened deck: Alien Swarm's alien blood is a vivid yellow-green.
        save('splatglow%d.dds' % k, cover[..., None] ** 1.5 * np.array((50, 54, 4)))
    # Blast scorch: a sooty star burst multiplied over the deck.
    rng = np.random.default_rng(71)
    size3 = 256
    yy3, xx3 = np.mgrid[0:size3, 0:size3].astype(np.float32)
    rr = np.hypot(xx3 - 128, yy3 - 128) / 128; aa = np.arctan2(yy3 - 128, xx3 - 128)
    spikes = 0.55 + 0.35 * np.abs(np.sin(aa * 7 + 1.3)) ** 3 + 0.1 * np.sin(aa * 23)
    ragged = np.asarray(Image.fromarray((rng.random((32, 32)) * 255).astype(np.uint8)).resize((size3, size3), Image.Resampling.BICUBIC)).astype(np.float32) / 255
    soot = np.clip((spikes - rr) * 2.2, 0, 1) * (0.7 + 0.5 * ragged)
    soot = np.clip(soot, 0, 1)
    save('scorch.dds', 255 * (1 - soot[..., None] * (1 - np.array((0.16, 0.14, 0.13)))[None, None]))
    # The camera's anchor (src/Marine.galaxy as_camAnchor): black added to the picture draws nothing.
    save('anchor.dds', np.zeros((8, 8, 3)))
    models = {}
    t = []; streak(t, 0.035); models['Tracer'] = (t, 'tracer.dds')
    # The laser runs along the unit's facing (a model's -Y), from the muzzle down to the deck at its far end
    # (LASER_DROP below the muzzle, which sits LASER_DROP + 0.03 up): the script turns it by unit facing,
    # which the engine draws smoothly between steps, and stretches its length with the scale's Y.
    t = []; beam(t, 0.032, LASER_DROP); models['Laser'] = (t, 'laser.dds')
    t = []; quad(t, (-.13, .13, 0), (.13, .13, 0), (.13, -.13, 0), (-.13, -.13, 0)); sprite(t, 0.05); models['LaserDot'] = (t, 'laserdot.dds')
    t = []; streak(t, 0.18); models['Arc'] = (t, 'arc.dds')
    t = []; sprite(t); models['Flash'] = (t, 'flash.dds')
    t = []; sprite(t); models['Burst'] = (t, 'burst.dds')
    t = []; sprite(t); models['Flame'] = (t, 'flame.dds')
    t = []; quad(t, (-1, 1, .04), (1, 1, .04), (1, -1, .04), (-1, -1, .04)); models['Ring'] = (t, 'ring.dds')
    for k in (1, 2):
        t = []; quad(t, (-1, 1, .03), (1, 1, .03), (1, -1, .03), (-1, -1, .03)); models['Splat%d' % k] = (t, 'splat%d.dds' % k, MULTIPLY)
        t = []; quad(t, (-1, 1, .034), (1, 1, .034), (1, -1, .034), (-1, -1, .034)); models['SplatGlow%d' % k] = (t, 'splatglow%d.dds' % k, ADD)
    t = []; quad(t, (-1, 1, .028), (1, 1, .028), (1, -1, .028), (-1, -1, .028)); models['Scorch'] = (t, 'scorch.dds', MULTIPLY)
    t = []; quad(t, (-.01, .01, 0), (.01, .01, 0), (.01, -.01, 0), (-.01, -.01, 0)); models['Anchor'] = (t, 'anchor.dds')
    for name, spec in models.items():
        tris, tex = spec[0], spec[1]
        blend = spec[2] if len(spec) > 2 else ADD
        out['Base.SC2Assets/' + (TEX + name + '.m3').replace('\\', '/')] = mesh(name, tris, tex, blend)
    return out, sorted(models)
