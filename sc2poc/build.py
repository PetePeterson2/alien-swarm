"""Build HALCYON DRIFT: tools/ + src/ -> editor/AlienPOC.SC2Map (components) -> dist/AlienPOC.SC2Map.

    py build.py              playable map (script errors hidden)
    py build.py --qa         script errors shown on screen
    py build.py --kit        QA build whose deck is placed from strings at load (src/Kit.galaxy)

The archive writer and MapInfo/terrain writers come from ../../Documents/GameNight
(proven in the client there); the hull kit and effect meshes from the
PUBG: Battle Royale project's city kit.
"""
from pathlib import Path
import argparse, hashlib, json, math, re, shutil, struct, sys, zlib, xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'tools/vendor'))
sys.path.insert(0, str(ROOT))
import mpyq
import numpy as np
from tools import alien, basemap, level as L, shipkit, fx, catalog, elevator

NAME = 'AlienPOC'
TITLE = 'Halcyon Drift: Cargo Elevator'
MODULES = ['State', 'Kit', 'Level', 'Fx', 'Marine', 'Weapons', 'Aliens', 'Director', 'Mission', 'Bots', 'HUD', 'Main']
SEATS = 4


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


def objects(hull_names, props):
    """Placed doodads; the kit build passes neither, so only the start locations remain."""
    root = ET.Element('PlacedObjects', Version='27')
    n = 1
    for name in hull_names:
        cx, cy = (int(v) for v in name[4:].split('_'))
        e = ET.SubElement(root, 'ObjectDoodad', Id=str(n), Position='%g,%g,%g' % (cx * L.CHUNK, cy * L.CHUNK, L.FLOOR),
                          Scale='1,1,1', Type='AS' + name)
        ET.SubElement(e, 'Flag', Index='HeightAbsolute', Value='1'); ET.SubElement(e, 'Flag', Index='ForcePlacement', Value='1')
        n += 1
    for model, x, y, rot, scale, rad in props:
        e = ET.SubElement(root, 'ObjectDoodad', Id=str(n), Position='%g,%g,%g' % (x, y, L.FLOOR),
                          Rotation='%.4f' % math.radians(rot % 360), Scale='%g,%g,%g' % (scale, scale, scale), Type='ASP_' + model)
        ET.SubElement(e, 'Flag', Index='HeightAbsolute', Value='1'); ET.SubElement(e, 'Flag', Index='ForcePlacement', Value='1')
        n += 1
    # Start locations: the camera's first frames look at the bay, not the map's corner.
    for i in range(SEATS):
        ET.SubElement(root, 'ObjectPoint', Id=str(60000 + i), Position='%g,%g,0' % L.SPAWN, Scale='1,1,1', Type='StartLoc',
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


def level_galaxy(solid, room, floor, kit=False):
    """AS_LevelInit: collision rows, lamps, vents, ammo, rooms, eggs, biomass, creep; the kit build adds the deck rows."""
    out = ['void AS_WallRow (int y, string s) {', '    int x;', '    for(x=0;x<AS_W;x+=1) {as_wall[x][y]=StringSub(s,x+1,x+1)=="1";}', '}',
           'void AS_KitProps () {']
    if kit:
        for model, x, y, rot, scale, rad in L.PROPS:
            out.append('    AS_KitProp("%s",%.2f,%.2f,%.1f,%.3f);' % (model, x, y, rot, scale))
    out += ['}', 'void AS_LevelInit () {', '    int i;']
    for y, row in enumerate(L.galaxy_tables(solid)):
        out.append('    AS_WallRow(%d,"%s");' % (y, row))
    if kit:
        out.append('    as_kitMode=true;')
        for y, row in enumerate(L.deck_rows(floor, room)):
            out.append('    AS_DeckRow(%d,"%s");' % (y, row))
        for k, kind in enumerate(L.KIT_KINDS):
            out.append('    as_kitPanels[%d]="%s";' % (k, ''.join(map(str, L.KIT_PANELS[kind]))))
    for i, (x, y) in enumerate(tour_spots(solid)):
        out.append('    as_tourX[%d]=%.2f;as_tourY[%d]=%.2f;' % (i, x, i, y))
    out.append('    as_tourCount=%d;' % len(L.AREAS))
    for x, y, kind, flick in L.LIGHTS:
        out.append('    AS_Lamp(%.2f,%.2f,"%s",%d);' % (x, y, kind, flick))
    for i, (x, y) in enumerate(L.VENTS):
        out.append('    as_vent[%d]=Point(%.2f,%.2f);' % (i, x, y))
    out.append('    as_ventCount=%d;' % len(L.VENTS))
    for i, (x, y) in enumerate(L.AMMO):
        out.append('    as_ammoAt[%d]=Point(%.2f,%.2f);UnitCreate(1,"ASAmmo",c_unitCreateIgnorePlacement,0,as_ammoAt[%d],0.0);' % (i, x, y, i))
    out.append('    as_ammoCount=%d;' % len(L.AMMO))
    rooms = [a for a in L.AREAS]
    for i, (name, (x0, y0, x1, y1), kind) in enumerate(rooms):
        out.append('    as_roomX0[%d]=%d.0;as_roomY0[%d]=%d.0;as_roomX1[%d]=%d.0;as_roomY1[%d]=%d.0;as_roomKind[%d]="%s";as_roomName[%d]="%s";'
                   % (i, x0, i, y0, i, x1, i, y1, i, kind, i, name))
    out.append('    as_roomCount=%d;' % len(rooms))
    for x, y in L.EGGS:
        out.append('    AS_SpawnAlien(AS_EGG,%.2f,%.2f,false);' % (x, y))
    for x, y, r in L.BIOMASS:
        out.append('    i=AS_SpawnAlien(AS_BIOMASS,%.2f,%.2f,false);if(i>=0) {as_aRadius[i]=%.2f;}' % (x, y, r))
        out.append('    CreepModify(Point(%.2f,%.2f),%.2f,true,true);' % (x, y, r + 1.5))
    for x, y, r in getattr(L, 'CREEP', [(43.0, 67.0, 9.0), (36.0, 70.0, 3.0), (50.0, 70.0, 3.0), (75.0, 63.0, 4.0), (81.0, 66.0, 3.0), (60.0, 65.0, 2.5)]):
        out.append('    CreepModify(Point(%.2f,%.2f),%.2f,true,true);' % (x, y, r))
    if kit:
        out.append('    AS_KitStart();')
    out.append('}')
    return '\n'.join(out)


def mission_galaxy():
    """AS_MissionData: the mission's tables from tools/cargo.py (an empty function for the deck)."""
    out = ['void AS_MissionData () {']
    if L.LEVEL == 'deck':
        return '\n'.join(out + ['}'])
    out.append('    as_mission=true;')
    for i, (name, (x0, y0, x1, y1)) in enumerate(L.ZONES):
        out.append('    as_zoneName[%d]="%s";as_zoneX0[%d]=%d.0;as_zoneY0[%d]=%d.0;as_zoneX1[%d]=%d.0;as_zoneY1[%d]=%d.0;' % (i, name, i, x0, i, y0, i, x1, i, y1))
    out.append('    as_zoneCount=%d;' % len(L.ZONES))
    for i, (x, y) in enumerate(L.CHECKPOINTS):
        out.append('    as_cpX[%d]=%.2f;as_cpY[%d]=%.2f;' % (i, x, i, y))
    out.append('    as_cpCount=%d;' % len(L.CHECKPOINTS))
    for i, (x, y) in enumerate(L.WINDOWS):
        out.append('    as_winX[%d]=%d.0;as_winY[%d]=%d.0;' % (i, x, i, y))
    out.append('    as_winCount=%d;' % len(L.WINDOWS))
    out.append('    as_liftX0=%d.0;as_liftY0=%d.0;as_liftX1=%d.0;as_liftY1=%d.0;' % L.LIFT)
    out.append('    as_extX0=%d.0;as_extY0=%d.0;as_extX1=%d.0;as_extY1=%d.0;' % L.EXTRACT)
    out.append('    as_doorX0=%d;as_doorY0=%d;as_doorX1=%d;as_doorY1=%d;' % L.DOOR)
    out.append('    as_doorPanel=Point(%.2f,%.2f);as_liftPanel=Point(%.2f,%.2f);' % (L.DOOR_PANEL + L.LIFT_PANEL))
    for k in range(4):
        out.append('    as_brIn[%d]=%d;as_brOut[%d]=%d;' % (k, L.BRIDGE_IN[k], k, L.BRIDGE_OUT[k]))
    for i, (x, y, w, face, side) in enumerate(L.shaft_columns()):
        out.append('    as_colX[%d]=%.2f;as_colY[%d]=%.2f;as_colW[%d]=%d.0;as_colFace[%d]=%.1f;as_colSide[%d]="%s";' % (i, x, i, y, i, w, i, face, i, side))
    out.append('    as_colCount=%d;' % len(L.shaft_columns()))
    for i, (x, y, wait) in enumerate(L.ROUTE):
        out.append('    as_routeX[%d]=%.2f;as_routeY[%d]=%.2f;as_routeWait[%d]=%d;' % (i, x, i, y, i, wait))
    out.append('    as_routeN=%d;' % len(L.ROUTE))
    out.append('}')
    return '\n'.join(out)


SIGNATURE = re.compile(r'^(void|bool|int|fixed|string|point|unit|actor|playergroup|trigger|text|color)\s+(AS_\w+)\s*\(([^;{)]*)\)\s*\{', re.M)


def script(solid, room, floor, qa, demo=False, kit=False, auto=False):
    bodies = []
    for name in MODULES:
        if name == 'Level':
            bodies.append(level_galaxy(solid, room, floor, kit))
        elif name == 'Mission':
            bodies.append((ROOT / 'src' / 'Mission.galaxy').read_text(encoding='utf-8') + '\n' + mission_galaxy())
        else:
            bodies.append((ROOT / 'src' / (name + '.galaxy')).read_text(encoding='utf-8'))
    decls, seen = [], set()
    for n, src in enumerate(bodies):
        for ret, func, params in SIGNATURE.findall(src):
            assert func not in seen, 'defined twice: ' + func
            seen.add(func)
            # State's functions are defined above the declarations: the compiler refuses a declaration after a definition.
            if n:
                decls.append('%s %s (%s);' % (ret, func, ' '.join(params.split())))
    code = bodies[0] + '\n// ---- forward declarations ----\n' + '\n'.join(decls) + '\n' + '\n'.join(bodies[1:])
    for key, value in {'spawnX': L.SPAWN[0], 'spawnY': L.SPAWN[1], 'spawnFacing': L.SPAWN_FACING}.items():
        code = code.replace('@%s@' % key, '%.2f' % value)
    code = code.replace('@W@', str(L.W)).replace('@H@', str(L.H))
    assert '@' not in code.replace('"@', '').replace('@"', ''), 'unreplaced placeholder'
    code = code.replace('bool as_qa = false;', 'bool as_qa = %s;' % str(qa).lower())
    code = code.replace('bool as_demo = false;', 'bool as_demo = %s;' % str(demo).lower())
    code = code.replace('bool as_auto = false;', 'bool as_auto = %s;' % str(auto).lower())
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
    unresolved = sorted(set(re.findall(r'\b(AS_[A-Z]\w*)\s*\(', code)) - seen)
    assert not unresolved, 'called but never defined: %s' % unresolved
    return 'include "TriggerLibs/NativeLib"\n' + code + '\nvoid InitMap () {\n    libNtve_InitLib();\n    AS_Init();\n}\n'


def ui_textures():
    from PIL import Image
    white = Image.new('RGBA', (32, 32), (255, 255, 255, 255))
    size = 256
    yy, xx = np.mgrid[0:size, 0:size] / (size - 1) * 2 - 1
    r = np.sqrt(xx * xx + yy * yy)
    a = (np.clip((r - 0.55) / 0.6, 0, 1) ** 1.6 * 255).astype(np.uint8)
    vig = Image.fromarray(np.dstack([np.full_like(a, 255)] * 3 + [a]), 'RGBA')
    return {'Base.SC2Assets/Derelict/UI/white.dds': shipkit.dds_rgba(white),
            'Base.SC2Assets/Derelict/UI/vignette.dds': shipkit.dds_rgba(vig)}


def compose(qa, demo=False, kit=False, painted=False, auto=False):
    W, H = L.W, L.H
    files = {}
    floor, room = L.carve()
    solid = L.blocked(floor)
    # Terrain: flat deck, painted per room.
    heights = np.full((H + 1, W + 1), L.FLOOR)
    # The kit build's map knows nothing of the level: one floor everywhere, every cell open until the script shuts the hull.
    masks, dominant = L.generic_masks() if kit else L.terrain_masks(floor, room)
    files.update(basemap.terrain_binaries(W, H, heights, masks, L.TEXTURES, dominant))
    files['t3Terrain.xml'] = basemap.terrain_xml(W, H, 'Korhal', 'KorhalCliff0', L.TEXTURES, L.FLOOR)
    files['PaintedPathingLayer'] = basemap.painted_pathing(np.ones_like(solid) if kit and not painted else ~solid)
    players = [(0, 3, 0, '')] + [(s, 1, -1, 'Terr') for s in range(1, SEATS + 1)] + [(15, 4, 0, '')]
    options = 0x1000 if qa else 0x20
    files['MapInfo'] = basemap.map_info(W, H, 'Korhal', (2, 2, W - 2, H - 2), options, players,
                                        round(L.FLOOR / basemap.QUANTIZE_SCALE))
    files['DocumentHeader'] = basemap.document_header(TITLE, 'Alien Swarm combat test in SC2', 'Top-down and third-person combat on a derelict ship.',
                                                      ['Marine %d' % s for s in range(1, SEATS + 1)])
    files['DocumentInfo'] = basemap.document_info()
    files['ComponentList.SC2Components'] = COMPONENT_LIST
    files['Attributes'] = attributes()
    files['Regions'] = b'<?xml version="1.0" encoding="utf-8"?><Regions></Regions>'
    files['Preload.xml'] = b'<?xml version="1.0" encoding="utf-8"?><Preload></Preload>'
    files['enUS.SC2Data/LocalizedData/GameStrings.txt'] = (
        'DocInfo/Name=%s\nDocInfo/Author=drink\nDocInfo/DescShort=Alien Swarm combat test\nDocInfo/DescLong=Top-down and third-person combat on a derelict ship.\n'
        'DocInfo/Website=\nDocInfo/Category=Other\nVariant001/ModeName=Co-op\nVariant001/ModeDesc=Up to four marines\n' % TITLE).encode()
    # Hull meshes and their textures.
    models = L.kit_pieces() if kit else L.hull_meshes(floor, room)
    textures = shipkit.hull_textures()
    mission = L.LEVEL != 'deck'
    if mission:
        textures.update(elevator.textures())
    shipkit.pack_textures(files, textures)
    emissive = {k for k, (d, e) in textures.items() if e is not None}
    for name, model in sorted(models.items()):
        files['Base.SC2Assets/Derelict/%s.m3' % name] = shipkit.write_m3(name, model.export(emissive))
    pieces = elevator.meshes(L.LIFT, L.BRIDGE_IN, L.BRIDGE_OUT, L.VOID, L.DOOR) if mission else {}
    for name, model in sorted(pieces.items()):
        files['Base.SC2Assets/Derelict/%s.m3' % name] = shipkit.write_m3(name, model.export(emissive))
    fx_files, _ = fx.build()
    files.update(fx_files)
    files.update(alien.build())
    files.update(ui_textures())
    props = {p[0] for p in L.PROPS}
    if kit:
        catalog.build(files, [], set(), kit_models=sorted(models), runtime_props=props, mesh_units=sorted(pieces))
        files['Objects'] = objects([], [])
    else:
        catalog.build(files, sorted(models), props, mesh_units=sorted(pieces))
        files['Objects'] = objects(sorted(models), L.PROPS)
    code = script(solid, room, floor, qa, demo, kit, auto)
    if painted:
        code = code.replace('bool as_kitScriptPath = true;', 'bool as_kitScriptPath = false;')
    files['MapScript.galaxy'] = code.encode()
    return files


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--level', default='cargo', help='cargo (the Cargo Elevator mission) or deck (the derelict combat test)')
    ap.add_argument('--qa', action='store_true')
    ap.add_argument('--auto', action='store_true', help='QA autopilot: player 1 plays the mission by itself and logs to the ASAuto bank')
    ap.add_argument('--demo', action='store_true', help='scripted firing range for screenshots (shows script errors too)')
    ap.add_argument('--kit', action='store_true', help='deck placed from strings at load by the hull kit (shows script errors too)')
    ap.add_argument('--kit-painted', action='store_true', help='the kit build, but alien pathing painted into the map as the baked build does')
    args = ap.parse_args()
    L.use(args.level)
    kit = args.kit or args.kit_painted
    name = NAME + ('-KitP' if args.kit_painted else '-Kit' if kit else '-Demo' if args.demo else '-Auto' if args.auto else '-QA' if args.qa else '')
    files = compose(args.qa or args.demo or kit or args.auto, args.demo, kit, args.kit_painted, args.auto)
    editable = ROOT / 'editor' / (name + '.SC2Map')
    if editable.exists():
        shutil.rmtree(editable)
    for member, data in files.items():
        dest = editable / member
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
    report = pack(files, ROOT / 'dist' / (name + '.SC2Map'))
    # What the level geometry costs in the archive: the baked hull chunks, or the kit's pieces.
    hull = [d for n, d in files.items() if re.match(r'Base\.SC2Assets/Derelict/(Hull|K)\w*\.m3$', n)]
    report['hullMeshes'] = len(hull)
    report['hullMeshBytesPacked'] = sum(min(len(d), len(zlib.compress(d, 9)) + 1) for d in hull)
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
