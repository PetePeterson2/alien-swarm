"""A minimal reader for Alien Swarm's maps (Valve BSP version 20/21), for reference numbers only.

Struct layouts come from the SDK's public/bspfile.h and gamebspfile.h (face 56 bytes, texinfo 72,
dispinfo 176, static props v9+). Nothing read here is shipped in the SC2 map: tools/asextract.py
turns it into floor heights and entity tables (tools/asdata/), which the level tools read.
"""
import re, struct, math
import numpy as np

SURF_NODRAW = 0x80


class BSP:
    def __init__(self, path):
        self.path = str(path)
        with open(path, 'rb') as f:
            self.data = f.read()
        ident, self.version = struct.unpack_from('<4si', self.data, 0)
        assert ident == b'VBSP', 'not a Valve BSP: %s' % path
        self.lumps = [struct.unpack_from('<iii4s', self.data, 8 + 16 * i) for i in range(64)]
        self._entities()
        self._geometry()
        self._static_props()

    def lump(self, i):
        ofs, ln, _, _ = self.lumps[i]
        return self.data[ofs:ofs + ln]

    def _arr(self, i, dtype):
        b = self.lump(i)
        n = len(b) // dtype.itemsize
        return np.frombuffer(b[:n * dtype.itemsize], dtype=dtype)

    def _entities(self):
        """Every entity as a dict; repeated keys (outputs) gather in lists under '_io'."""
        txt = self.lump(0).split(b'\0')[0].decode('latin-1')
        self.entities = []
        for block in re.findall(r'\{(.*?)\}', txt, re.S):
            e = {'_io': []}
            for k, v in re.findall(r'"([^"]*)"\s*"([^"]*)"', block):
                # Outputs look like "OnTrigger" "target,Input,param,delay,times" (comma or 0x1b separated).
                if k.startswith('On') and (',' in v or '\x1b' in v):
                    e['_io'].append((k, v.replace('\x1b', ',')))
                elif k not in e:
                    e[k] = v
            self.entities.append(e)

    def _geometry(self):
        self.planes = self._arr(1, np.dtype([('n', '<f4', 3), ('d', '<f4'), ('t', '<i4')]))
        self.verts = self._arr(3, np.dtype('<f4')).reshape(-1, 3)
        self.edges = self._arr(12, np.dtype('<u2')).reshape(-1, 2)
        self.surfedges = self._arr(13, np.dtype('<i4'))
        face_dt = np.dtype([('planenum', '<u2'), ('side', 'u1'), ('onNode', 'u1'), ('firstedge', '<i4'), ('numedges', '<i2'),
                            ('texinfo', '<i2'), ('dispinfo', '<i2'), ('fogvol', '<i2'), ('styles', 'u1', 4), ('lightofs', '<i4'),
                            ('area', '<f4'), ('lmmins', '<i4', 2), ('lmsize', '<i4', 2), ('origFace', '<i4'), ('numPrims', '<u2'),
                            ('firstPrimID', '<u2'), ('smoothing', '<u4')])
        assert face_dt.itemsize == 56 and self.lumps[7][1] % 56 == 0
        self.faces = self._arr(7, face_dt)
        texinfo = self._arr(6, np.dtype([('tv', '<f4', (2, 4)), ('lv', '<f4', (2, 4)), ('flags', '<i4'), ('texdata', '<i4')]))
        texdata = self._arr(2, np.dtype([('refl', '<f4', 3), ('nameid', '<i4'), ('w', '<i4'), ('h', '<i4'), ('vw', '<i4'), ('vh', '<i4')]))
        strdata, strtab = self.lump(43), self._arr(44, np.dtype('<i4'))
        names = [strdata[o:strdata.index(b'\0', o)].decode('latin-1') for o in strtab]
        tname = [names[texdata[t['texdata']]['nameid']] if t['texdata'] >= 0 else '' for t in texinfo]
        self.models = self._arr(14, np.dtype([('mins', '<f4', 3), ('maxs', '<f4', 3), ('origin', '<f4', 3), ('headnode', '<i4'),
                                              ('firstface', '<i4'), ('numfaces', '<i4')]))
        self.dispinfo = self._arr(26, np.dtype([('start', '<f4', 3), ('vstart', '<i4'), ('tstart', '<i4'), ('power', '<i4'),
                                                ('minTess', '<i4'), ('smooth', '<f4'), ('contents', '<i4'), ('mapface', '<u2'),
                                                ('pad', '<u2'), ('lmalpha', '<i4'), ('lmsample', '<i4'), ('rest', 'u1', 128)]))
        self.dispverts = self._arr(33, np.dtype([('v', '<f4', 3), ('dist', '<f4'), ('alpha', '<f4')]))
        n = len(self.faces)
        self.face_name = [tname[t].lower() for t in self.faces['texinfo']]
        self.face_flags = np.array([texinfo[t]['flags'] for t in self.faces['texinfo']])
        self.face_model = np.full(n, -1, np.int32)
        for mi, m in enumerate(self.models):
            self.face_model[m['firstface']:m['firstface'] + m['numfaces']] = mi
        self.face_polys, self.face_normal = [], np.zeros((n, 3), np.float32)
        for i, f in enumerate(self.faces):
            se = self.surfedges[f['firstedge']:f['firstedge'] + f['numedges']]
            vidx = np.where(se >= 0, self.edges[np.abs(se), 0], self.edges[np.abs(se), 1])
            self.face_polys.append(self.verts[vidx].astype(np.float64))
            nrm = self.planes['n'][f['planenum']]
            self.face_normal[i] = -nrm if f['side'] else nrm

    def _static_props(self):
        """(origin, angles, model) per static prop, from the 'sprp' game lump."""
        self.static_props = []
        gl = self.lump(35)
        if len(gl) < 4:
            return
        for i in range(struct.unpack_from('<i', gl, 0)[0]):
            gid, flags, ver, ofs, ln = struct.unpack_from('<iHHii', gl, 4 + 16 * i)
            if gid != 0x73707270:
                continue
            b, p = self.data[ofs:ofs + ln], 0
            nd = struct.unpack_from('<i', b, p)[0]; p += 4
            names = [b[p + 128 * k:p + 128 * (k + 1)].split(b'\0')[0].decode('latin-1').lower() for k in range(nd)]
            p += 128 * nd
            nl = struct.unpack_from('<i', b, p)[0]; p += 4 + 2 * nl
            count = struct.unpack_from('<i', b, p)[0]; p += 4
            stride = (len(b) - p) // count if count else 0
            for k in range(count):
                x, y, z, pa, ya, ra, pt = struct.unpack_from('<6fH', b, p + k * stride)
                self.static_props.append(((x, y, z), (pa, ya, ra), names[pt]))

    def model_origin(self):
        """The origin each brush entity moves its model to (models are stored round 0,0,0 when they have one)."""
        out = np.zeros((len(self.models), 3))
        for e in self.entities:
            m = e.get('model', '')
            if m.startswith('*') and 'origin' in e:
                out[int(m[1:])] = [float(v) for v in e['origin'].split()]
        return out

    def origin(self, e):
        if 'origin' in e:
            try:
                return tuple(float(v) for v in e['origin'].split()[:3])
            except ValueError:
                return None
        m = e.get('model', '')
        if m.startswith('*'):
            mm = self.models[int(m[1:])]
            return tuple(((mm['mins'] + mm['maxs']) / 2).tolist())
        return None

    def bounds(self, e):
        """World box (x0, y0, z0, x1, y1, z1) of a brush entity, else None."""
        m = e.get('model', '')
        if not m.startswith('*'):
            return None
        mm = self.models[int(m[1:])]
        o = np.array([float(v) for v in e['origin'].split()]) if 'origin' in e else np.zeros(3)
        lo, hi = mm['mins'] + o, mm['maxs'] + o
        return tuple(round(float(v), 1) for v in (*lo, *hi))

    def displacement_quads(self):
        """Every displacement as small quads in world space."""
        quads = []
        for di in self.dispinfo:
            poly = self.face_polys[int(di['mapface'])]
            if len(poly) != 4:
                continue
            k = int(np.argmin(np.linalg.norm(poly - np.array(di['start']), axis=1)))
            c = np.roll(poly, -k, axis=0)
            n = (1 << int(di['power'])) + 1
            grid = np.zeros((n, n, 3))
            for i in range(n):
                e0 = c[0] + (c[1] - c[0]) * (i / (n - 1))
                e1 = c[3] + (c[2] - c[3]) * (i / (n - 1))
                for j in range(n):
                    dv = self.dispverts[int(di['vstart']) + i * n + j]
                    grid[i, j] = e0 + (e1 - e0) * (j / (n - 1)) + np.array(dv['v']) * dv['dist']
            for i in range(n - 1):
                for j in range(n - 1):
                    quads.append(np.array([grid[i, j], grid[i, j + 1], grid[i + 1, j + 1], grid[i + 1, j]]))
        return quads
