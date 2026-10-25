"""Build HALCYON DRIFT: tools/ + src/ -> editor/AlienPOC.SC2Map (components) -> dist/AlienPOC.SC2Map.

Every level (LEVELS) is in the one map: the terrain is a blank deck the size of the
biggest, and the script builds the level being played from its strings with the hull
kit (src/Kit.galaxy), tears it down when the mission is won and builds the next
(src/Campaign.galaxy). Players pick where to start from what their banks have unlocked.

    py build.py              playable map (script errors hidden)
    py build.py --qa         script errors shown on screen
    py build.py --start 1    QA build that skips the level menu and starts at level 1
    py build.py --auto       QA autopilot: plays the whole campaign by itself

The archive writer and MapInfo/terrain writers come from ../../Documents/GameNight
(proven in the client there); the hull kit and effect meshes from the
PUBG: Battle Royale project's city kit.
"""
from pathlib import Path
import argparse, hashlib, json, math, re, shutil, struct, subprocess, sys, zlib, xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'tools/vendor'))
sys.path.insert(0, str(ROOT))
import mpyq
import numpy as np
from tools import alien, marine, basemap, level as L, shipkit, fx, catalog, elevator, hudart, hudlayout, uiart, heights
from tools import pack as packer
from tools import colony

NAME = 'AlienPOC'
TITLE = 'Halcyon Drift'
WIPE = False
AUTO_SKILL, AUTO_ONSLAUGHT, AUTO_PROF = 2, False, 3
MARINES = ['sarge', 'wildcat', 'faith', 'crash', 'jaeger', 'wolfe', 'bastille', 'vegas']
REFERENCE_SOUNDS = Path.home() / 'OneDrive/Documents/sc2map/doodad-royale/reference/catalog/Sound.txt'
MODULES = ['State', 'Kit', 'Level', 'Fx', 'Marine', 'Weapons', 'Aliens', 'Objects', 'Doors', 'Director', 'Use', 'HackUI', 'Mission', 'Bots', 'Hive',
           'Progress', 'HUD', 'Hints', 'Briefing', 'Campaign', 'Main']
SEATS = 4
# The campaign in order, after Alien Swarm's Jacob's Rest: the level's module (tools/<name>.py), its title,
# where it is, the briefing line, and the par (speed-run) time in seconds (Landing Bay's speedruntime is 85).
LEVELS = [('landingbay', 'LANDING BAY', 'VEREON XII // SYNTEK LANDING BAY 7',
           'Sweep the landing bay and download the flight data. Press H for controls.', 85),
          ('cargo', 'CARGO ELEVATOR', 'VEREON XII // CARGO ELEVATOR',
           'Take the freight elevator down to the colony. Press H for controls.', 170),
          ('deima', 'DEIMA SURFACE BRIDGE', 'DEIMA // COLONY SURFACE, NIGHT SIDE',
           'Blow the infested pipeline and cross the bridge to the reactor. Press H for controls.', 150),
          ('rydberg', 'RYDBERG REACTOR', 'DEIMA // RYDBERG POWER PLANT',
           'Bring the colony reactor back online and get out through the north doors. Press H for controls.', 180),
          ('residential', 'SYNTEK RESIDENTIAL', 'DEIMA // SYNTEK RESIDENTIAL BLOCK',
           'Destroy the eggs, burn out the biomass and get to the elevators. Press H for controls.', 150),
          ('sewer', 'SEWER JUNCTION B5', 'DEIMA // SEWER JUNCTION B5',
           'Bring down the tunnel the swarm comes up, destroy the eggs and get out to the surface. Press H for controls.', 180)]
FLAT_PROPS = {'BattleStation_Line_Decals', 'DOM_Ground_Grate', 'BloodSplats', 'DOM_Crate'}   # stock decals the floor plating hides; crates are ours
BANK = 'HalcyonDrift'              # each marine's campaign progress (QA builds use HalcyonDriftQA)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def pack(files, target):
    """Pure-Python MPQ writer (GameNight/Saboteur); re-reads every member."""
    files = {n.replace('/', '\\'): d for n, d in files.items() if n not in ('(listfile)', '(attributes)', '(signature)')}
    files['(listfile)'] = ('\r\n'.join(sorted(files)) + '\r\n(listfile)\r\n').encode()
    crypt = mpyq.MPQArchive._prepare_encryption_table()

    def h(s, kind):
        a, b = 0x7fed7fed, 0xeeeeeeee
        for c in s.upper().encode():
            a = (crypt[(kind << 8) + c] ^ (a + b)) & 0xffffffff
            b = (c + a + b + (b << 5) + 3) & 0xffffffff
        return a

    def encrypt(data, key):
        seed, result = 0xeeeeeeee, bytearray()
        for (plain,) in struct.iter_unpack('<I', data):
            seed = (seed + crypt[0x400 + (key & 0xff)]) & 0xffffffff
            result += struct.pack('<I', plain ^ ((key + seed) & 0xffffffff))
            key = (((~key << 21) + 0x11111111) | (key >> 11)) & 0xffffffff
            seed = (plain + seed + (seed << 5) + 3) & 0xffffffff
        return result

    count = 1
    while count < len(files) * 2:
        count *= 2
    hashes, blocks, payload = [b'\xff' * 16 for _ in range(count)], [], bytearray()
    for index, (name, data) in enumerate(sorted(files.items())):
        slot = h(name, 0) % count
        while hashes[slot] != b'\xff' * 16:
            slot = (slot + 1) % count
        hashes[slot] = struct.pack('<IIHHI', h(name, 1), h(name, 2), 0, 0, index)
        compressed = b'\x02' + zlib.compress(data, 9)
        stored = compressed if len(compressed) < len(data) else data
        flags = 0x81000200 if stored is compressed else 0x81000000
        blocks.append(struct.pack('<IIII', 32 + len(payload), len(stored), len(data), flags))
        payload += stored
    hp, bp = 32 + len(payload), 32 + len(payload) + count * 16
    result = struct.pack('<4sIIHHIIII', b'MPQ\x1a', 32, bp + len(blocks) * 16, 0, 3, hp, bp, count, len(blocks))
    result += payload + encrypt(b''.join(hashes), h('(hash table)', 3))
    result += encrypt(b''.join(blocks), h('(block table)', 3))
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(result)
    check = mpyq.MPQArchive(str(target), listfile=False)
    for name, data in files.items():
        assert check.read_file(name.encode()) == data, name
    check.file.close()
    return {'path': str(target), 'sha256': sha(result), 'bytes': len(result), 'members': len(files)}


def attributes(slots=SEATS):
    """One co-op team holding every lobby slot (PUBG's lobby_variant)."""
    code = lambda s: str(int.from_bytes(s.encode('ascii'), 'big'))
    root = ET.Element('Attributes')
    ET.SubElement(root, 'DefaultVariants', Value='0')
    variant = ET.SubElement(root, 'Variant')
    for tag, value in [('Id', '1'), ('CategoryId', '1'), ('ModeId', '1'), ('ModeName', 'Variant001/ModeName'),
                       ('ModeDesc', 'Variant001/ModeDesc'), ('MaxTeamSize', str(slots))]:
        ET.SubElement(variant, tag, Value=value)
    ET.SubElement(variant, 'IsDefault')
    ET.SubElement(variant, 'AttributeHidden', Namespace='999', Id='3006')
    for ident, value in (('1001', code('no')), ('2000', code('Cust'))):
        default = ET.SubElement(ET.SubElement(variant, 'Attribute', Namespace='999', Id=ident), 'Default')
        ET.SubElement(default, 'Slot', Id='Global'); ET.SubElement(default, 'Value', Id=value); ET.SubElement(default, 'Locked')
    teams = ET.SubElement(variant, 'Attribute', Namespace='999', Id='2018')
    for slot in range(slots):
        default = ET.SubElement(teams, 'Default')
        ET.SubElement(default, 'Slot', Id=str(slot))
        value = ET.SubElement(default, 'Value', Id=code('T1'))
        if slot:
            value.set('Index', str(slot))
        ET.SubElement(default, 'Locked')
    ET.indent(root, space='    ')
    return ET.tostring(root, encoding='utf-8', xml_declaration=True)


COMPONENT_LIST = b'''<?xml version="1.0" encoding="utf-8"?>
<Components>
    <DataComponent Type="info">DocumentInfo</DataComponent>
    <DataComponent Type="mapi">MapInfo</DataComponent>
    <DataComponent Type="terr">t3Terrain.xml</DataComponent>
    <DataComponent Type="plob">Objects</DataComponent>
    <DataComponent Type="regi">Regions</DataComponent>
    <DataComponent Type="gada">GameData</DataComponent>
    <DataComponent Type="text" Locale="enUS">GameText</DataComponent>
    <DataComponent Type="attr">Attributes</DataComponent>
</Components>'''


# The level being written sits at this origin in the map (tools/pack.py): every position and rectangle
# build.py writes for it is moved there. The cell tables (rows, heights) stay the level's own.
OX, OY = 0, 0


def at(x, y):
    return x + OX, y + OY


def rect(r):
    x0, y0, x1, y1 = r
    return x0 + OX, y0 + OY, x1 + OX, y1 + OY


def objects(spawn):
    """Placed objects: only the start locations. The deck itself is built by the script (src/Kit.galaxy)."""
    root = ET.Element('PlacedObjects', Version='27')
    # Start locations: the camera's first frames look at the first level's bay, not the map's corner.
    for i in range(SEATS):
        ET.SubElement(root, 'ObjectPoint', Id=str(60000 + i), Position='%g,%g,0' % spawn, Scale='1,1,1', Type='StartLoc',
                      Name='Start Location %03d' % (i + 1))
    ET.indent(root, space='    ')
    return ET.tostring(root, encoding='utf-8', xml_declaration=True)


def tour_spots(solid):
    """One open cell per room, the nearest to its middle, for the QA room tour (Ctrl+N)."""
    spots = []
    for name, (x0, y0, x1, y1), kind in L.AREAS:
        mx, my = (x0 + x1) / 2, (y0 + y1) / 2
        cells = [(math.hypot(x + 0.5 - mx, y + 0.5 - my), x, y) for y in range(y0, y1) for x in range(x0, x1) if not solid[y, x]]
        _, x, y = min(cells)
        spots.append((x + 0.5, y + 0.5))
    return spots


def pad(rows, width, height, fill):
    """A level's rows widened and lengthened to the map's size with `fill` (hull)."""
    rows = [r + fill * (width - len(r)) for r in rows]
    return rows + [fill * width] * (height - len(rows))


def level_galaxy(n, solid, room, floor, MW, MH, place, hts):
    """Level n (the one tools/level.py has in use), at place (ox, oy, lift) in the map: AS_LevelRows<n>, its origin,
    collision, the deck for the kit and the cells' floor heights; AS_LevelData<n>, the spawn, lamps, vents, ammo,
    rooms, eggs, biomass and creep; AS_KitProps<n>, the dressing."""
    ox, oy, dz = place[:3]
    base = L.FLOOR + dz
    out = ['void AS_LevelRows%d () {' % n,
           '    as_ox=%d;as_oy=%d;as_oxF=%d.0;as_oyF=%d.0;as_lw=%d;as_lh=%d;' % (ox, oy, ox, oy, L.W, L.H),
           '    AS_HeightsClear(%.6f);' % base]
    # Slope cells: the stairs' and the drop's edge ring (no plating there, and no haze tiles over the edge).
    for y, x0, x1, z, slope in heights.runs(hts['cellz'] + dz, hts['slope'] | hts['edge']):
        if z != base or slope:
            out.append('    AS_HeightRun(%d,%d,%d,%.6f,%s);' % (y, x0, x1, z, 'true' if slope else 'false'))
    for x, y, piece, turn, z, rise in hts['stairs']:
        out.append('    AS_HeightStair(%d,%d,"%s",%.1f,%.6f,%.6f);' % (x, y, piece, turn, z + dz, rise))
    for y, row in enumerate(pad(L.galaxy_tables(solid), MW, MH, '1')):
        out.append('    AS_WallRow(%d,"%s");' % (y, row))
    for y, row in enumerate(pad(hts['rows'], MW, MH, '#')):
        out.append('    AS_DeckRow(%d,"%s");' % (y, row))
    out += ['}', 'void AS_KitProps%d () {' % n]
    for model, x, y, rot, scale, rad in L.PROPS:
        # Flat stock decals would lie under the floor plating: blood becomes goo, the rest goes.
        x, y = at(x, y)
        if model == 'BloodSplats':
            out.append('    AS_KitDecal("KDGoo",%.2f,%.2f,%.1f);' % (x, y, rot))
        elif model.startswith('KP'):
            out.append('    AS_KitDecal("%s",%.2f,%.2f,%.1f);' % (model, x, y, rot))
        elif model == 'DOM_Crate':
            out.append('    AS_KitDecal("%s",%.2f,%.2f,%.1f);' % ('KPCrateG' if int(x + y) % 3 else 'KPCrateM', x, y, rot))
        elif model not in FLAT_PROPS:
            out.append('    AS_KitProp("%s",%.2f,%.2f,%.1f,%.3f);' % (model, x, y, rot, scale))
    for piece, x, y, rot in L.decal_spots(floor, room, solid):
        out.append('    AS_KitDecal("%s",%.2f,%.2f,%.1f);' % ((piece,) + at(x, y) + (rot,)))
    out += ['}', 'void AS_LevelData%d () {' % n, '    int i;']
    out.append('    as_spawnX=%.2f;as_spawnY=%.2f;as_spawnFacing=%.1f;' % (at(*L.SPAWN) + (L.SPAWN_FACING,)))
    out.append('    as_kitSnowRoof=%s;' % ('true' if getattr(L, 'SNOW_ROOFS', False) else 'false'))
    spots = [at(x, y) for x, y in tour_spots(solid)[:64]]
    for i, (x, y) in enumerate(spots):
        out.append('    as_tourX[%d]=%.2f;as_tourY[%d]=%.2f;' % (i, x, i, y))
    out.append('    as_tourCount=%d;as_tourAt= -1;' % len(spots))
    for x, y, kind, flick in L.LIGHTS + L.corridor_lamps(floor, room) + L.pit_lamps(floor, room):
        out.append('    AS_Lamp(%.2f,%.2f,"%s",%d);' % (at(x, y) + (kind, flick)))
    for i, (x, y) in enumerate(L.VENTS):
        out.append('    as_vent[%d]=Point(%.2f,%.2f);' % ((i,) + at(x, y)))
    out.append('    as_ventCount=%d;' % len(L.VENTS))
    for i, (x, y) in enumerate(L.AMMO):
        out.append('    AS_AmmoCrate(%d,%.2f,%.2f);' % ((i,) + at(x, y)))
    out.append('    as_ammoCount=%d;' % len(L.AMMO))
    for i, (name, r, kind) in enumerate(L.AREAS):
        x0, y0, x1, y1 = rect(r)
        out.append('    as_roomX0[%d]=%d.0;as_roomY0[%d]=%d.0;as_roomX1[%d]=%d.0;as_roomY1[%d]=%d.0;as_roomKind[%d]="%s";as_roomName[%d]="%s";'
                   % (i, x0, i, y0, i, x1, i, y1, i, kind, i, name))
    out.append('    as_roomCount=%d;' % len(L.AREAS))
    # Eggs (x, y), or (x, y, group, name): group one of AS's egg templates (EGG_PICK (n, k) picks k of groups 1..n at
    # the start, 0 none), name what its going fires (src/Hive.galaxy). Biomass (x, y, r), or (x, y, r, name).
    out.append('    AS_HiveStart();')
    if hasattr(L, 'EGG_PICK'):
        out.append('    AS_HivePick(%d,%d);' % L.EGG_PICK)
    for x, y, *more in L.EGGS:
        group, name = (list(more) + [0, ''])[:2]
        spawn = 'i=AS_SpawnAlien(AS_EGG,%.2f,%.2f,false);' % at(x, y) + ('AS_HiveName(i,"%s");' % name if name else '')
        out.append('    if(AS_HivePicked(%d)) {%s}' % (group, spawn) if group else '    ' + spawn)
    for x, y, r, *name in L.BIOMASS:
        x, y = at(x, y)
        out.append('    i=AS_SpawnAlien(AS_BIOMASS,%.2f,%.2f,false);if(i>=0) {as_aRadius[i]=%.2f;}' % (x, y, r))
        if name:
            out.append('    AS_HiveName(i,"%s");' % name[0])
    if getattr(L, 'EQUIP_REQ', None):
        out.append('    AS_HiveNeed(%s);' % L.EQUIP_REQ)
        out.append('    AS_Creep(%.2f,%.2f,%.2f);' % (x, y, r + 1.5))
    for x, y, r in getattr(L, 'CREEP', [(43.0, 67.0, 9.0), (36.0, 70.0, 3.0), (50.0, 70.0, 3.0), (75.0, 63.0, 4.0), (81.0, 66.0, 3.0), (60.0, 65.0, 2.5)]):
        out.append('    AS_Creep(%.2f,%.2f,%.2f);' % (at(x, y) + (r,)))
    out.append('}')
    return '\n'.join(out)


def level_script_text():
    """A scripted mission's briefing (tools/<level>.py OBJECTIVES, DESCRIPTION, NEEDS_TECH) and its crew's mail
    (MAILS {n: (from, subject, body)}, n from 4: Landing Bay's are src/HackUI.galaxy's own)."""
    def q(s):
        return s.replace('"', "'").replace('\n', '<n/>')
    briefs, mails, was = [], [], L.LEVEL
    for n, (name, *_) in enumerate(LEVELS):
        L.use(name)
        if hasattr(L, 'OBJECTIVES'):
            objs = '<n/>'.join('<c val=\\"FFD24A\\">%d.</c> %s' % (i + 1, q(o[1])) for i, o in enumerate(L.OBJECTIVES))
            briefs.append((n, objs, q(L.DESCRIPTION), getattr(L, 'NEEDS_TECH', False)))
        mails += [(k, q(who), q(subject), q(body)) for k, (who, subject, body) in getattr(L, 'MAILS', {}).items()]
    L.use(was)
    out = ['string AS_LevelObjectives (int m) {']
    out += ['    if(m==%d) {return "%s";}' % (n, objs) for n, objs, _, _ in briefs]
    out += ['    return "";', '}', 'string AS_LevelDesc (int m) {']
    out += ['    if(m==%d) {return "%s";}' % (n, desc) for n, _, desc, _ in briefs]
    out += ['    return "";', '}', 'bool AS_LevelTech (int m) {']
    out += ['    if(m==%d) {return %s;}' % (n, 'true' if tech else 'false') for n, _, _, tech in briefs]
    out += ['    return false;', '}', 'string AS_LevelMail (int n) {']
    out += ['    if(n==%d) {return "<c val=\\"8CC8F0\\">From:</c> %s<n/><c val=\\"8CC8F0\\">Subject:</c> %s<n/><n/>%s";}' % m
            for m in mails]
    return out + ['    return "";', '}']


def level_common():
    """What every level shares: the row readers, and the dispatch by level number."""
    out = ['void AS_WallRow (int y, string s) {', '    int x;', '    for(x=0;x<AS_W;x+=1) {as_wall[x][y]=StringSub(s,x+1,x+1)=="1";}', '}',
           'void AS_LevelNames () {']
    for n, (name, title, place, brief, par) in enumerate(LEVELS):
        out.append('    as_levelTitle[%d]="%s";as_levelPlace[%d]="%s";as_levelBrief[%d]="%s";as_levelPar[%d]=%d;' % (n, title, n, place, n, brief, n, par))
    out.append('    as_kitMode=true;')
    for k, kind in enumerate(L.KIT_KINDS):
        out.append('    as_kitPanels[%d]="%s";' % (k, ''.join(heights.KIND_CHARS[i] for i in L.KIT_PANELS[kind])))
    out += ['}'] + level_script_text()
    out += ['// The level\'s tables, its lamps, crates, eggs and biomass; then the kit builds its deck.',
            'void AS_LevelLoad (int n) {']
    for n in range(len(LEVELS)):
        out.append('    %sif(n==%d) {AS_LevelRows%d();AS_LevelData%d();}' % ('else ' if n else '', n, n, n))
    out += ['    AS_KitStart();', '}', 'void AS_KitProps () {']
    for n in range(len(LEVELS)):
        out.append('    %sif(as_level==%d) {AS_KitProps%d();}' % ('else ' if n else '', n, n))
    out.append('}')
    return '\n'.join(out)


def mission_galaxy(n):
    """AS_MissionData<n>: level n's mission tables (tools/level.py and tools/cargo.py)."""
    out = ['void AS_MissionData%d () {' % n]
    for i, (name, r) in enumerate(L.ZONES):
        x0, y0, x1, y1 = rect(r)
        out.append('    as_zoneName[%d]="%s";as_zoneX0[%d]=%d.0;as_zoneY0[%d]=%d.0;as_zoneX1[%d]=%d.0;as_zoneY1[%d]=%d.0;as_zoneHit[%d]=false;'
                   % (i, name, i, x0, i, y0, i, x1, i, y1, i))
    out.append('    as_zoneCount=%d;' % len(L.ZONES))
    for i, (x, y) in enumerate(L.CHECKPOINTS):
        x, y = at(x, y)
        out.append('    as_cpX[%d]=%.2f;as_cpY[%d]=%.2f;' % (i, x, i, y))
    out.append('    as_cpCount=%d;' % len(L.CHECKPOINTS))
    out.append('    as_extX0=%d.0;as_extY0=%d.0;as_extX1=%d.0;as_extY1=%d.0;' % rect(L.EXTRACT))
    out.append('    as_doorPanel=Point(%.2f,%.2f);' % at(*L.CONSOLE))
    for i, (x, y, wait) in enumerate(L.ROUTE):
        x, y = at(x, y)
        out.append('    as_routeX[%d]=%.2f;as_routeY[%d]=%.2f;as_routeWait[%d]=%d;' % (i, x, i, y, i, wait))
    out.append('    as_routeN=%d;as_routeAt=0;' % len(L.ROUTE))
    # A scripted mission's own (src/Mission.galaxy SCRIPTED MISSIONS): where it extracts, whether it needs a tech,
    # its objectives by key with the spot each marker shows, and its buttons.
    if hasattr(L, 'OBJECTIVES'):
        out.append('    AS_GenLevel("%s",%s);' % (L.EXTRACT_NAME, 'true' if getattr(L, 'NEEDS_TECH', False) else 'false'))
        for key, name, shown, spot in L.OBJECTIVES:
            mx, my = at(*spot) if spot else (0.0, 0.0)
            out.append('    AS_GenObjective("%s","%s",%s,%.2f,%.2f);' % (key, name, 'true' if shown else 'false', mx, my))
    for name, (x, y), label, powered in getattr(L, 'BUTTONS', []):
        out.append('    AS_Button("%s",%.2f,%.2f,"%s",%s);' % ((name,) + at(x, y) + (label, 'true' if powered else 'false')))
    kinds = {'auto': 0, 'panel': 1, 'bash': 2, 'jammed': 3, 'gap': 4, 'block': 5, 'hover': 6, 'glass': 7}
    for name, r, kind, seal, panel in getattr(L, 'DOORS', []):
        x0, y0, x1, y1 = rect(r)
        px, py = at(*panel) if panel else (0.0, 0.0)
        out.append('    AS_Door("%s",%d,%d,%d,%d,%d,%.2f,%.2f,%.2f);' % (name, x0, y0, x1, y1, kinds[kind], seal, px, py))
    # A spawner's 13th field and a trigger's 5th, when there, are options (src/Objects.galaxy AS_SpawnerOpts,
    # AS_TriggerOpts): spawners {start, near (cells), jitter, order (1 MoveTo, 2 MoveToIgnoringMarines), target (x, y)},
    # triggers {name, off, need (marines inside: n, or -1 all living), aliens}.
    for sp in getattr(L, 'SPAWNERS', []):
        out.append('    AS_Spawner("%s",%.2f,%.2f,%s,%d,%d,%.2f,%d,%d,%d,%d,%d);' % ((sp[0],) + at(sp[1], sp[2]) + tuple(sp[3:12])))
        if len(sp) > 12:
            o = sp[12]
            tx, ty = at(*o['target']) if 'target' in o else (0.0, 0.0)
            out.append('    AS_SpawnerOpts(%s,%.2f,%.2f,%d,%.2f,%.2f);' % ('true' if o.get('start') else 'false', o.get('near', 9.3),
                                                                     o.get('jitter', 0.25), o.get('order', 0), tx, ty))
    for r, once, chance, acts, *opts in getattr(L, 'TRIGGERS', []):
        x0, y0, x1, y1 = rect(r)
        out.append('    AS_Trigger(%.2f,%.2f,%.2f,%.2f,%s,%.2f);' % (x0, y0, x1, y1, 'true' if once else 'false', chance))
        for act, arg, delay in acts:
            out.append('    AS_TriggerDo("%s","%s",%.2f);' % (act, arg, delay))
        if opts:
            o = opts[0]
            out.append('    AS_TriggerOpts("%s",%s,%d,%s);' % (o.get('name', ''), 'true' if o.get('off') else 'false', o.get('need', 1),
                                                              'true' if o.get('aliens') else 'false'))
    # The map's other logic (src/Objects.galaxy): outputs on named events, random timers, counters, movers on paths.
    for ev, act, arg, delay in getattr(L, 'ONS', []):
        out.append('    AS_On("%s","%s","%s",%.2f);' % (ev, act, arg, delay))
    for name, lo, hi, on in getattr(L, 'TIMERS', []):
        out.append('    AS_Timer("%s",%.2f,%.2f,%s);' % (name, lo, hi, 'true' if on else 'false'))
    for name, top in getattr(L, 'COUNTERS', []):
        out.append('    AS_Counter("%s",%d);' % (name, top))
    for name, model, speed, nodes in getattr(L, 'MOVERS', []):
        out.append('    AS_Mover("%s","%s",%.2f);' % (name, model, speed))
        for x, y, z, node in nodes:
            out.append('    AS_MoverPoint(%.2f,%.2f,%.2f,"%s");' % (at(x, y) + (z, node)))
    if hasattr(L, 'COMPUTER'):
        hd, ent, interval, download = L.COMPUTER_HACK
        out.append('    AS_Terminal(%.2f,%.2f,true,%d,%d,%.2f,%.2f,true);' % (at(*L.COMPUTER) + (hd, ent, interval, download)))
    for (x, y), owner, mail in getattr(L, 'PDAS', []):
        x, y = at(x, y)
        out.append('    AS_Pda(%.2f,%.2f,"%s",%d);' % (x, y, owner, mail))
    rows, cols, wires = getattr(L, 'PANEL_WIRES', (2, 5, 2))
    out.append('    as_pnRows=%d;as_pnCols=%d;as_pnWires=%d;' % (rows, cols, wires))
    sx, sy = at(*L.SENTRY_SPOT) if hasattr(L, 'SENTRY_SPOT') else (0.0, 0.0)
    out.append('    as_sentrySpotX=%.2f;as_sentrySpotY=%.2f;' % (sx, sy))
    out.append('    as_outX0=%d.0;as_outY0=%d.0;as_outX1=%d.0;as_outY1=%d.0;' % (rect(L.OUTDOORS) if hasattr(L, 'OUTDOORS') else (0, 0, 0, 0)))
    if L.LIFT is not None:
        out.append('    as_liftX0=%d.0;as_liftY0=%d.0;as_liftX1=%d.0;as_liftY1=%d.0;' % rect(L.LIFT))
        out.append('    as_liftPanel=Point(%.2f,%.2f);' % at(*L.LIFT_PANEL))
        bridge_in, bridge_out = rect(L.BRIDGE_IN), rect(L.BRIDGE_OUT)
        for k in range(4):
            out.append('    as_brIn[%d]=%d;as_brOut[%d]=%d;' % (k, bridge_in[k], k, bridge_out[k]))
        # The shaft (tools/elevator.py): where its walls' top edge meets the deck, its segment train and beacons.
        sh = L.SHAFT
        x, y = at(sh['x'], sh['y'])
        low, out_slot = elevator.train(sh['in_slot'])
        out.append('    as_shX=%.2f;as_shY=%.2f;as_shLow=%.4f;as_shIn=%d;as_shOut=%d;as_shV=%.4f;as_shBx=%.2f;as_shBt=%.2f;'
                   % (x, y, low, sh['in_slot'], out_slot, sh['speed'], at(sh['beacon_x'], 0)[0], sh['beacon_t']))
        assert abs(elevator.RIDE - 33.19) < 1e-6, 'src/Mission.galaxy AS_RIDE_LEN is tools/elevator.py RIDE'
        out.append('    as_shSeg=%.4f;as_shN=%d;as_shHalf=%.2f;as_shLampU=%.2f;as_shLampT=%.2f;as_shDoorU=%.2f;'
                   % (elevator.SEG, elevator.SEG_N, elevator.HALF, elevator.LAMP_U, elevator.LAMP_T, elevator.DOOR_U))
        for k, u in enumerate(sh['beacons']):
            out.append('    as_shBu[%d]=%.2f;' % (k, u))
        for k, u in enumerate(sh['beacon_s']):
            out.append('    as_shBs[%d]=%.3f;' % (k, u))
        nx0, ny0, nx1, ny1 = rect(L.LIFT_NOTCH)
        out.append('    as_liftNotchY1=%d.0;as_hasLift=true;' % ny1)
    else:
        out.append('    as_hasLift=false;')
    out.append('}')
    # What lies on the deck at the start: drones asleep, explosive barrels, pickups.
    out.append('void AS_LevelThings%d () {' % n)
    out.append('    int i;')
    for kind, x, y in getattr(L, 'SLEEPERS', []):
        out.append('    i=AS_SpawnAlien(%s,%.2f,%.2f,false);' % ((kind,) + at(x, y)))
    for x, y in getattr(L, 'BARRELS', []):
        out.append('    i=AS_SpawnAlien(AS_BARREL,%.2f,%.2f,false);' % at(x, y))
    # Barrels a mission counts (x, y, name): their going up fires "broken:<name>" (src/Hive.galaxy).
    for x, y, name in getattr(L, 'HIVE_BARRELS', []):
        out.append('    i=AS_SpawnAlien(AS_BARREL,%.2f,%.2f,false);AS_HiveName(i,"%s");' % (at(x, y) + (name,)))
    for kind, x, y in getattr(L, 'PICKUPS', []):
        out.append('    AS_LevelPickup("%s",%.2f,%.2f);' % ((kind,) + at(x, y)))
    out.append('}')
    return '\n'.join(out)


VOICE = ROOT / 'assets' / 'vo'


def voice_clips():
    """{line key: seconds} for every campaign line whose clip in assets/vo was voiced from its current text."""
    manifest = VOICE / 'manifest.json'
    have = json.loads(manifest.read_text(encoding='utf-8')) if manifest.exists() else {}
    clips, stale = {}, []
    for name, *_ in LEVELS:
        L.use(name)
        for key, text in getattr(L, 'LINES', {}).items():
            entry = have.get(key)
            if entry and entry['text'] == text and (VOICE / (key + '.ogg')).exists():
                clips[key] = entry['seconds']
            else:
                stale.append(key)
    if stale:
        print('not voiced (subtitle only until py tools/voice.py): %s' % ', '.join(stale), file=sys.stderr)
    return clips


def voice_files(files):
    """The commander's clips into the map, each a CSound ASVo_<key> in the Voice category (the dialogue slider)."""
    root = ET.Element('Catalog')
    for key in sorted(voice_clips()):
        files['Base.SC2Assets/Derelict/Vo/%s.ogg' % key] = (VOICE / (key + '.ogg')).read_bytes()
        s = ET.SubElement(root, 'CSound', id='ASVo_' + key)
        ET.SubElement(s, 'AssetArray', File='Derelict\\Vo\\%s.ogg' % key)
        ET.SubElement(s, 'Category', value='Voice')
        ET.SubElement(s, 'Volume', value='0.000000,0.000000')
    ET.indent(root, space='    ')
    files['Base.SC2Data/GameData/SoundData.xml'] = ET.tostring(root, encoding='utf-8', xml_declaration=True)


BARKS = ROOT / 'assets' / 'barks'


_bark_clips = None


def bark_clips():
    """{clip key: (profile, kind, line, seconds)} for every marine's chatter clip in assets/barks voiced from its
    line's current text (tools/barks.py)."""
    global _bark_clips
    if _bark_clips is not None:
        return _bark_clips
    from tools import barks
    manifest = BARKS / 'manifest.json'
    have = json.loads(manifest.read_text(encoding='utf-8')) if manifest.exists() else {}
    faces = [face for face, _, _ in barks.MARINES]
    kinds = [kind for kind, _, _ in barks.BARKS]
    out = {}
    for key, (face, kind, n, text, _, _) in barks.clips().items():
        entry = have.get(key)
        # Only a clip the transcription heard right: one cut in the wrong place would say the wrong words.
        if entry and entry['text'] == text and entry['ok'] and (BARKS / (key + '.ogg')).exists():
            out[key] = (faces.index(face), kinds.index(kind), n, entry['seconds'])
    missing = len(barks.clips()) - len(out)
    if missing:
        print('%d chatter lines not voiced (text only until py tools/barks.py)' % missing, file=sys.stderr)
    _bark_clips = out
    return out


def bark_files(files):
    """The marines' chatter clips into the map, each a CSound ASBark_<marine>_<kind>_<n> in the Voice category,
    added to whatever SoundData.xml the map already has (the commander's clips, when there are any)."""
    path = 'Base.SC2Data/GameData/SoundData.xml'
    root = ET.fromstring(files[path]) if path in files else ET.Element('Catalog')
    for key in sorted(bark_clips()):
        files['Base.SC2Assets/Derelict/Barks/%s.ogg' % key] = (BARKS / (key + '.ogg')).read_bytes()
        s = ET.SubElement(root, 'CSound', id='ASBark_' + key)
        ET.SubElement(s, 'AssetArray', File='Derelict\\Barks\\%s.ogg' % key)
        ET.SubElement(s, 'Category', value='Voice')
        ET.SubElement(s, 'Volume', value='-2.000000,-2.000000')
    ET.indent(root, space='    ')
    files[path] = ET.tostring(root, encoding='utf-8', xml_declaration=True)


MUSIC = ROOT / 'assets' / 'music'


def music_files(files):
    """The score's loops (assets/music, tools/music.py) into the map, each a CSound ASMus_<id> in the Music
    category (the music slider) that loops until stopped, added to the SoundData.xml voice_files wrote."""
    manifest = MUSIC / 'manifest.json'
    have = json.loads(manifest.read_text(encoding='utf-8')) if manifest.exists() else {}
    path = 'Base.SC2Data/GameData/SoundData.xml'
    root = ET.fromstring(files[path]) if path in files else ET.Element('Catalog')
    for key in sorted(have):
        if not (MUSIC / (key + '.ogg')).exists():
            continue
        files['Base.SC2Assets/Derelict/Music/%s.ogg' % key] = (MUSIC / (key + '.ogg')).read_bytes()
        s = ET.SubElement(root, 'CSound', id='ASMus_' + key.capitalize())
        ET.SubElement(s, 'AssetArray', File='Derelict\\Music\\%s.ogg' % key)
        ET.SubElement(s, 'Category', value='Music')
        ET.SubElement(s, 'Volume', value='-3.000000,-3.000000')
        ET.SubElement(s, 'LoopCount', value='-1')
    ET.indent(root, space='    ')
    files[path] = ET.tostring(root, encoding='utf-8', xml_declaration=True)


def barks_galaxy():
    """The chatter lines of each kind (tools/barks.py BARKS, in AS_CH_* order) and each marine's clip lengths."""
    from tools import barks
    assert len(barks.MARINES) == 8 and len(barks.BARKS) == 16 and max(len(t) for _, _, t in barks.BARKS) <= 3, 'as_barkLen size'
    out = ['int AS_ChatCount (int k) {']
    out += ['    if(k==%d) {return %d;}' % (k, len(texts)) for k, (_, _, texts) in enumerate(barks.BARKS)]
    out += ['    return 1;', '}', 'string AS_ChatKey (int k) {']
    out += ['    if(k==%d) {return "%s";}' % (k, kind) for k, (kind, _, _) in enumerate(barks.BARKS)]
    out += ['    return "";', '}', 'string AS_ChatLine (int k, int r) {']
    for k, (_, _, texts) in enumerate(barks.BARKS):
        out.append('    if(k==%d) {%s}' % (k, ''.join('if(r==%d) {return "%s";}' % (n, t.replace('"', "'")) for n, t in enumerate(texts))))
    out += ['    return "";', '}', 'fixed[8][16][3] as_barkLen;', 'bool as_barkReady;', 'void AS_BarkInit () {']
    out += ['    as_barkLen[%d][%d][%d]=%.2f;' % (pf, k, n, secs) for pf, k, n, secs in sorted(bark_clips().values())]
    out += ['    as_barkReady=true;', '}']
    return '\n'.join(out)


def mission_common():
    out = ['void AS_MissionData () {']
    for n in range(len(LEVELS)):
        out.append('    %sif(as_level==%d) {AS_MissionData%d();}' % ('else ' if n else '', n, n))
    out += ['}', 'void AS_LevelThings () {']
    for n in range(len(LEVELS)):
        out.append('    %sif(as_level==%d) {AS_LevelThings%d();}' % ('else ' if n else '', n, n))
    # The commander's lines of every level (tools/<level>.py LINES), by key.
    out += ['}', 'string AS_LineText (string key) {']
    for name, *_ in LEVELS:
        L.use(name)
        for key, text in getattr(L, 'LINES', {}).items():
            out.append('    if(key=="%s") {return "%s";}' % (key, text.replace('"', "'")))
    # The length of each line's radio clip (assets/vo, tools/voice.py): 0 for a line not voiced yet.
    clips = voice_clips()
    out += ['    return "";', '}', 'fixed AS_LineVoice (string key) {']
    out += ['    if(key=="%s") {return %.2f;}' % (key, secs) for key, secs in sorted(clips.items())]
    out += ['    return 0.0;', '}', 'void AS_VoiceProbe () {']
    out += ['    SoundLengthQuery(SoundLink("ASVo_%s",-1));' % key for key in sorted(clips)]
    out += ['    AS_Log("voice: %d commander clips queried");' % len(clips)]
    # asw_info_message texts (tools/<level>.py INFO {key: (title, body)}), as "title|body".
    out += ['}', 'string AS_InfoText (string key) {']
    for name, *_ in LEVELS:
        L.use(name)
        for key, (title, body) in getattr(L, 'INFO', {}).items():
            out.append('    if(key=="%s") {return "%s|%s";}' % (key, title.replace('"', "'"), body.replace('"', "'")))
    out += ['    return "";', '}']
    return '\n'.join(out)


# Words the Galaxy compiler will not take as a name: its keywords and types, and C's (near is; far is not).
RESERVED = set('''near auto break breakpoint case catch char class const continue default delete do double else enum extern
false float for friend goto if include inline int long mutable namespace native new null operator private protected public
register return short signed sizeof static struct switch template this throw true try typedef typename union unsigned using
virtual void volatile while abilcmd actor actorscope aifilter bank bool byte camerainfo color datetime doodad fixed handle
generichandle marker order playergroup point region revealer sound soundlink string text timer transmissionsource trigger
unit unitfilter unitgroup unitref wave waveinfo wavetarget'''.split())


SIGNATURE = re.compile(r'^(void|bool|int|fixed|string|point|unit|actor|playergroup|trigger|text|color)\s+(AS_\w+)\s*\(([^;{)]*)\)\s*\{', re.M)


def hud_galaxy(frames):
    """tools/hudlayout.py as AS_HUD_* constants (tints as colour functions), and each level's minimap square."""
    out = ['// ---- generated by build.py from tools/hudlayout.py and tools/hudart.py ----',
           'const int AS_HUD_RING_N = %d;' % hudart.RING_N]
    for key, value in vars(hudlayout).items():
        if not key.isupper():
            continue
        if isinstance(value, tuple):
            out.append('color AS_HUD_%s () {return Color(%s);}' % (key, ','.join('%.2f' % (c / 2.55) for c in value)))
        else:
            out.append('const int AS_HUD_%s = %d;' % (key, value))
    # Portraits (cosmetics): the default per slot, and the keys a bank may name.
    out.append('string AS_HudPortraitDefault (int q) {')
    for k, key in enumerate(hudart.PORTRAIT_DEFAULTS):
        out.append('    if((q-1)%%%d==%d) {return "%s";}' % (len(hudart.PORTRAIT_DEFAULTS), k, key))
    out += ['    return "%s";' % hudart.PORTRAIT_DEFAULTS[0], '}', 'bool AS_HudPortraitKnown (string key) {']
    for key in hudart.PORTRAITS:
        out.append('    if(key=="%s") {return true;}' % key)
    out += ['    return false;', '}']
    out.append('void AS_HudMaps () {')
    for n, (x0, y0, size) in enumerate(frames):
        out.append('    as_mmX0[%d]=%d.0;as_mmY0[%d]=%d.0;as_mmSize[%d]=%d.0;' % (n, x0, n, y0, n, size))
    out.append('}')
    return '\n'.join(out)


def guns_galaxy():
    """The gun families' ids, model names and muzzles (tools/marine.py), for src/Marine.galaxy."""
    muzzles = marine.muzzles()
    names = [name for name, _, _ in marine.GUNS]
    out = ['const int AS_GUN_%s = %d;' % (name.upper(), k) for k, name in enumerate(names)]
    out += ['string[%d] as_gunName;' % len(names), 'fixed[%d] as_gunFwd;' % len(names), 'fixed[%d] as_gunLeft;' % len(names),
            'fixed[%d] as_gunZ;' % len(names), 'void AS_GunInit () {']
    for k, name in enumerate(names):
        f, l, z = muzzles[name]
        out.append('    as_gunName[%d]="%s";as_gunFwd[%d]=%.3f;as_gunLeft[%d]=%.3f;as_gunZ[%d]=%.3f;' % (k, name, k, f, k, l, k, z))
    out.append('}')
    return '\n'.join(out)


def script(levels, missions, MW, MH, qa, demo=False, auto=False, start=-1, bank=BANK, frames=()):
    bodies = []
    for name in MODULES:
        if name == 'HUD':
            src = (ROOT / 'src' / 'HUD.galaxy').read_text(encoding='utf-8')
            # The constants go above the module's globals, the minimap squares after them.
            head, cut, rest = src.partition('int[5] as_dHurt;')
            gen = hud_galaxy(frames).split('void AS_HudMaps () {')
            bodies.append(head + gen[0] + cut + rest + '\nvoid AS_HudMaps () {' + gen[1])
        elif name == 'Level':
            bodies.append(level_common() + '\n' + '\n'.join(levels))
        elif name == 'Mission':
            bodies.append((ROOT / 'src' / 'Mission.galaxy').read_text(encoding='utf-8') + '\n' + mission_common() + '\n' + '\n'.join(missions))
        else:
            bodies.append((ROOT / 'src' / (name + '.galaxy')).read_text(encoding='utf-8').replace('@GUNS@', guns_galaxy()).replace('@BARKS@', barks_galaxy()))
    decls, seen = [], set()
    for n, src in enumerate(bodies):
        for ret, func, params in SIGNATURE.findall(src):
            assert func not in seen, 'defined twice: ' + func
            seen.add(func)
            # State's functions are defined above the declarations: the compiler refuses a declaration after a definition.
            if n:
                decls.append('%s %s (%s);' % (ret, func, ' '.join(params.split())))
    code = bodies[0] + '\n// ---- forward declarations ----\n' + '\n'.join(decls) + '\n' + '\n'.join(bodies[1:])
    code = code.replace('@W@', str(MW)).replace('@H@', str(MH)).replace('@LEVELS@', str(len(LEVELS)))
    assert '@' not in code.replace('"@', '').replace('@"', ''), 'unreplaced placeholder'
    for line, value in [('bool as_qa = false;', str(qa).lower()), ('bool as_demo = false;', str(demo).lower()),
                        ('bool as_auto = false;', str(auto).lower()), ('bool as_autoWipe = false;', str(WIPE).lower()),
                        ('int as_autoSkill = 2;', str(AUTO_SKILL)), ('bool as_autoOnslaught = false;', str(AUTO_ONSLAUGHT).lower()),
                        ('int as_autoProf = 3;', str(AUTO_PROF)),
                        ('int as_startLevel = -1;', str(start)),
                        ('string as_bankName = "%s";' % BANK, '"%s"' % bank)]:
        assert line in code, 'build switch line missing: ' + line
        code = code.replace(line, line.rsplit('=', 1)[0] + '= ' + value + ';')
    if qa:
        # Every string literal that names a sound, called or listed: probed at start (src/Main.galaxy AS_SoundProbe).
        known = set((REFERENCE_SOUNDS.read_text(encoding='utf-8').split()) if REFERENCE_SOUNDS.exists() else ())
        ids = set(re.findall(r'SoundLink\("(\w+)"', code)) | set(re.findall(r'AS_\w*Sound\w*\([^;"]*"(\w+)"', code))
        ids |= {s for s in re.findall(r'"(\w+)"', code) if s in known and len(s) > 3}
        # Not a prefix the script builds an id on ("ASBark_"+marine+...): the client logs it as an unknown sound.
        ids = {s for s in ids if not s.endswith('_')}
        probe = ''.join('    SoundPlay(SoundLink("%s",-1),PlayerGroupSingle(1),0.0,0.0);\n' % s for s in sorted(ids))
        stub = 'void AS_SoundProbe () {\n}'
        assert stub in code, 'AS_SoundProbe stub missing'
        code = code.replace(stub, 'void AS_SoundProbe () {\n' + probe + '}')
    code = code.replace('string as_runId = "unset";', 'string as_runId = "%s";' % sha(code.encode())[:12])
    # The compiler refuses a global declared twice ("Invalid global variable name"); galaxy_check does not see it.
    names = re.findall(r'^(?:const\s+)?\w+(?:\[[^\]]*\])*\s+((?:as|AS)_\w+)\s*[=;]', code, re.M)
    twice = sorted({n for n in names if names.count(n) > 1})
    assert not twice, 'global declared twice: %s' % twice
    # Nor a global used above its declaration (MODULES order): reported as odd parse errors in the client.
    bare = re.sub(r'//[^\n]*', '', re.sub(r'"(?:\\.|[^"\\])*"', '""', code))
    early = []
    for m in re.finditer(r'^(?:const\s+)?\w+(?:\[[^\]]*\])*\s+((?:as|AS)_\w+)\s*[=;]', bare, re.M):
        first = re.search(r'\b%s\b' % m.group(1), bare)
        if first.start() < m.start(1):
            early.append('%s (line %d)' % (m.group(1), bare.count('\n', 0, first.start()) + 1))
    assert not early, 'global used before its declaration: %s' % early
    # Locals must all be declared before a function's first statement.
    decl = re.compile(r'^\s*(?:int|fixed|bool|string|point|unit|actor|bank|text|color|timer|trigger|playergroup|unitgroup|region|abilcmd|order)(?:\[[^\]]*\])*\s+\w+\s*[=;]')
    late, inside, stated = [], None, False
    for n, line in enumerate(bare.split('\n'), 1):
        if SIGNATURE.match(line) or re.match(r'^bool\s+\w+\s*\(bool testConds, bool runActions\)\s*\{', line):
            inside, stated = (None if line.rstrip().endswith('}') else n), False
            continue
        if inside is None:
            continue
        if line.startswith('}'):
            inside = None
            continue
        if not line.strip():
            continue
        if decl.match(line):
            if stated:
                late.append(n)
        else:
            stated = True
    assert not late, 'local declared after a statement at MapScript lines %s' % late[:10]
    # Nor a parameter or local named with a reserved word or a type ("Invalid parameter" for `fixed near`).
    named = re.findall(r'\b(?:int|fixed|bool|string|point|unit|actor|bank|text|color|timer|trigger|playergroup|unitgroup|region|abilcmd|order|sound)'
                       r'(?:\[[^\]]*\])*\s+(\w+)\s*[=;,)]', bare)
    reserved = sorted(set(named) & RESERVED)
    assert not reserved, 'reserved word used as a name: %s' % reserved
    unresolved = sorted(set(re.findall(r'\b(AS_[A-Z]\w*)\s*\(', code)) - seen)
    assert not unresolved, 'called but never defined: %s' % unresolved
    return 'include "TriggerLibs/NativeLib"\n' + code + '\nvoid InitMap () {\n    libNtve_InitLib();\n    AS_Init();\n}\n'


def ui_textures(levels):
    """The HUD art (tools/hudart.py) with each level's minimap, plus the vignette and a white square."""
    from PIL import Image
    white = Image.new('RGBA', (32, 32), (255, 255, 255, 255))
    size = 256
    yy, xx = np.mgrid[0:size, 0:size] / (size - 1) * 2 - 1
    r = np.sqrt(xx * xx + yy * yy)
    a = (np.clip((r - 0.55) / 0.6, 0, 1) ** 1.6 * 255).astype(np.uint8)
    vig = Image.fromarray(np.dstack([np.full_like(a, 255)] * 3 + [a]), 'RGBA')
    files, frames = hudart.files(levels)
    files.update({'Base.SC2Assets/Derelict/UI/%s.dds' % k: shipkit.dds_rgba(v) for k, v in uiart.textures().items()})
    files.update({'Base.SC2Assets/Derelict/UI/white.dds': shipkit.dds_rgba(white),
                  'Base.SC2Assets/Derelict/UI/vignette.dds': shipkit.dds_rgba(vig)})
    return files, frames


def compose(qa, demo=False, auto=False, start=-1):
    """Every level in one map. Each level has its own part of the map and its real floor heights in the terrain
    (tools/heights.py); levels overlap where their floors agree (tools/pack.py). The script builds whichever
    level is being played from its strings (src/Kit.galaxy), then the next."""
    global OX, OY
    levels, missions, pieces, props, floors, report, maps = [], [], {}, set(), set(), [], []
    paint, signs = {}, {}
    sizes, hts = [], []
    for name, *_ in LEVELS:
        L.use(name)
        floor, room = L.carve()
        rows = L.deck_rows(floor, room)
        # A level whose drop runs off its east edge carries it on a few cells (heights.extend): its tables are that wide.
        h = heights.extend(rows, heights.level_heights(vars(L), rows, L.FLOOR), L.FLOOR)
        sizes.append((h['cellz'].shape[1], h['cellz'].shape[0]))
        hts.append(h)
        floors.add(L.FLOOR)
    assert len(floors) == 1, 'levels with different base heights: %s' % floors
    # The cell tables are as big as the biggest level; the map holds every level, packed.
    TABLES = (max(w for w, h in sizes), max(h for w, h in sizes))
    packed = packer.pack([{'w': w, 'h': h, 'vert': t['vert'], 'vmask': t['vmask']} for (w, h), t in zip(sizes, hts)], base=L.FLOOR)
    W, H = packed['size']
    places = packed['places']
    for n, (name, *_) in enumerate(LEVELS):
        L.use(name)
        OX, OY = places[n][:2]
        floor, room = L.carve()
        solid = L.blocked(floor)
        levels.append(level_galaxy(n, solid, room, floor, *TABLES, places[n], hts[n]))
        maps.append((floor, np.array([[L.in_void(x, y) for x in range(L.W)] for y in range(L.H)])))
        missions.append(mission_galaxy(n))
        props |= {p[0] for p in L.PROPS if p[0] not in FLAT_PROPS and not p[0].startswith('KP')}
        props |= {m[1][4:] for m in getattr(L, 'MOVERS', []) if m[1].startswith('ASR_')}
        paint.update(L.paint_names())
        signs.update(L.sign_names())
        if L.LIFT is not None:
            pieces.update(elevator.meshes(L.LIFT, L.LIFT_NOTCH, L.BRIDGE_IN, L.BRIDGE_OUT, L.VOID, L.CONSOLE, floor, L.VOID_DEPTH))
        pieces.update(elevator.door_meshes())
        pieces.update(colony.meshes())
        report.append('%s %dx%d at %d,%d, lifted %+.2f, %d slope cells'
                      % (name, L.W, L.H, places[n][0], places[n][1], places[n][2], hts[n]['slope'].sum()))
    report.append('map %dx%d' % (W, H))
    OX, OY = places[0][:2]
    L.use(LEVELS[0][0])
    files = {}
    # Terrain: every level's floor heights, plates with rust and wreckage, every cell open until the script shuts the hull.
    terrain = packed['terrain']
    assert 0.0 <= terrain.min() and terrain.max() < 250.0, 'terrain heights out of range'
    masks, dominant = L.generic_masks(W, H)
    files.update(basemap.terrain_binaries(W, H, terrain, masks, L.TEXTURES, dominant))
    files['t3Terrain.xml'] = basemap.terrain_xml(W, H, 'Korhal', 'KorhalCliff0', L.TEXTURES, L.FLOOR)
    files['PaintedPathingLayer'] = basemap.painted_pathing(np.ones((H, W), bool))
    players = [(0, 3, 0, '')] + [(s, 1, -1, 'Terr') for s in range(1, SEATS + 1)] + [(15, 4, 0, '')]
    options = 0x1000 if qa else 0x20
    files['MapInfo'] = basemap.map_info(W, H, 'Korhal', (2, 2, W - 2, H - 2), options, players,
                                        round(L.FLOOR / basemap.QUANTIZE_SCALE))
    files['DocumentHeader'] = basemap.document_header(TITLE, 'Alien Swarm in SC2', 'Top-down co-op missions on a derelict ship and the colony below.',
                                                      ['Marine %d' % s for s in range(1, SEATS + 1)])
    # Each marine's campaign progress (src/Campaign.galaxy) and the QA log, preloaded so every player's bank is there at start.
    bank = BANK + 'QA' if qa else BANK
    banks = [(bank, s) for s in range(1, SEATS + 1)] + [('ASAuto', 1)]
    files['DocumentInfo'] = basemap.document_info(banks)
    bank_list = ET.Element('BankList')
    for name, player in banks:
        ET.SubElement(bank_list, 'Bank', Name=name, Player=str(player))
    ET.indent(bank_list, space='    ')
    files['BankList.xml'] = ET.tostring(bank_list, encoding='utf-8', xml_declaration=True)
    files['ComponentList.SC2Components'] = COMPONENT_LIST
    files['Attributes'] = attributes()
    files['Regions'] = b'<?xml version="1.0" encoding="utf-8"?><Regions></Regions>'
    files['Preload.xml'] = b'<?xml version="1.0" encoding="utf-8"?><Preload></Preload>'
    files['enUS.SC2Data/LocalizedData/GameStrings.txt'] = (
        'DocInfo/Name=%s\nDocInfo/Author=drink\nDocInfo/DescShort=Alien Swarm in SC2\nDocInfo/DescLong=Top-down co-op missions on a derelict ship and the colony below.\n'
        'DocInfo/Website=\nDocInfo/Category=Other\nVariant001/ModeName=Co-op\nVariant001/ModeDesc=Up to four marines\n' % TITLE).encode()
    # The hull kit's pieces, every level's set pieces, and their textures.
    models = L.kit_pieces()
    models.update(L.paint_pieces(sorted(paint)))
    models.update(L.sign_pieces(sorted(signs)))
    models.update(L.shaft_pieces())
    models.update(elevator.shaft_models())
    textures = shipkit.hull_textures()
    textures.update(elevator.textures())
    textures.update(colony.textures())
    from tools import deckart
    textures.update(deckart.sign_textures(signs))
    from tools import deckart
    shipkit.pack_textures(files, textures, {**shipkit.multiply_textures(), **deckart.paint_textures(paint), **colony.multiply_textures()})
    emissive = {k for k, (d, e) in textures.items() if e is not None}
    for name, model in sorted(models.items()):
        files['Base.SC2Assets/Derelict/%s.m3' % name] = shipkit.write_m3(name, model.export(emissive))
    for name, model in sorted(pieces.items()):
        files['Base.SC2Assets/Derelict/%s.m3' % name] = shipkit.write_m3(name, model.export(emissive))
    fx_files, _ = fx.build()
    files.update(fx_files)
    files.update(alien.build())
    files.update(marine.build())
    ui, frames = ui_textures(maps)
    # The minimap squares are in each level's own cells: moved to its place in the map.
    frames = [(x0 + p[0], y0 + p[1], size) for (x0, y0, size), p in zip(frames, places)]
    files.update(ui)
    catalog.build(files, [], set(), kit_models=sorted(models), runtime_props=props, mesh_units=sorted(pieces))
    voice_files(files)
    bark_files(files)
    files['Objects'] = objects(at(*L.SPAWN))
    files['MapScript.galaxy'] = script(levels, missions, *TABLES, qa, demo, auto, start, bank, frames).encode()
    return files, report


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--qa', action='store_true')
    ap.add_argument('--auto', action='store_true', help='QA autopilot: player 1 plays the campaign by itself and logs to the ASAuto bank')
    ap.add_argument('--skill', type=int, default=2, help='with --auto: difficulty picked in the briefing, 1 Easy .. 5 Brutal')
    ap.add_argument('--onslaught', action='store_true', help='with --auto: Onslaught on')
    ap.add_argument('--marine', default='crash', choices=MARINES, help='with --auto: the marine the autopilot plays')
    ap.add_argument('--wipe', action='store_true', help='with --auto: Landing Bay loses its tech first (restart), then the whole squad (failed), then plays through')
    ap.add_argument('--demo', action='store_true', help='scripted firing range for screenshots (shows script errors too)')
    ap.add_argument('--start', type=int, default=-1, help='QA: skip the briefing and start at this level (0 Landing Bay, 1 the cargo elevator)')
    args = ap.parse_args()
    global WIPE, AUTO_SKILL, AUTO_ONSLAUGHT, AUTO_PROF
    WIPE = args.wipe
    AUTO_SKILL, AUTO_ONSLAUGHT, AUTO_PROF = args.skill, args.onslaught, MARINES.index(args.marine)
    args.auto = args.auto or args.wipe
    qa = args.qa or args.demo or args.auto or args.start >= 0
    start = args.start if args.start >= 0 else (0 if args.auto or args.demo else -1)
    name = NAME + ('-Demo' if args.demo else '-Auto' if args.auto else '-QA' if qa else '')
    files, levels = compose(qa, args.demo, args.auto, start)
    editable = ROOT / 'editor' / (name + '.SC2Map')
    if editable.exists():
        shutil.rmtree(editable)
    for member, data in files.items():
        dest = editable / member
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
    # The client stops at the first compile or load error: catch types and constant bounds here, all at once.
    for tool in ('galaxy_types.py', 'galaxy_bounds.py'):
        check = subprocess.run([sys.executable, str(ROOT / 'tools' / tool), str(editable / 'MapScript.galaxy')], capture_output=True, text=True)
        if check.returncode != 0:
            print(check.stdout[-4000:])
            sys.exit('%s found problems; nothing was packed.' % tool)
    report = pack(files, ROOT / 'dist' / (name + '.SC2Map'))
    report['levels'] = levels
    report['scriptBytes'] = len(files['MapScript.galaxy'])
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
