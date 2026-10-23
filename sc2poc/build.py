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
import argparse, hashlib, json, math, re, shutil, struct, sys, zlib, xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'tools/vendor'))
sys.path.insert(0, str(ROOT))
import mpyq
import numpy as np
from tools import alien, basemap, level as L, shipkit, fx, catalog, elevator, hudart, hudlayout

NAME = 'AlienPOC'
TITLE = 'Halcyon Drift'
MODULES = ['State', 'Kit', 'Level', 'Fx', 'Marine', 'Weapons', 'Aliens', 'Director', 'Mission', 'Bots', 'HUD', 'Campaign', 'Main']
SEATS = 4
# The campaign in order: the level's module (tools/level.py's deck, else tools/<name>.py), its title,
# where it is, and the briefing line shown as it starts.
LEVELS = [('deck', 'DISTRESS BEACON', 'USCSS HALCYON DRIFT  //  DECK 3',
           'Distress beacon traced to deck 3. Get the reactor running again. Press H for controls.'),
          ('cargo', 'CARGO ELEVATOR', 'COLONY LANDING BAY',
           'Take the freight elevator down to the colony. Press H for controls.')]
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


def level_galaxy(n, solid, room, floor, MW, MH):
    """Level n (the one tools/level.py has in use): AS_LevelRows<n>, collision and the deck for the kit;
    AS_LevelData<n>, the spawn, lamps, vents, ammo, rooms, eggs, biomass and creep; AS_KitProps<n>, the dressing."""
    out = ['void AS_LevelRows%d () {' % n]
    for y, row in enumerate(pad(L.galaxy_tables(solid), MW, MH, '1')):
        out.append('    AS_WallRow(%d,"%s");' % (y, row))
    for y, row in enumerate(pad(L.deck_rows(floor, room), MW, MH, '#')):
        out.append('    AS_DeckRow(%d,"%s");' % (y, row))
    out += ['}', 'void AS_KitProps%d () {' % n]
    for model, x, y, rot, scale, rad in L.PROPS:
        # Flat stock decals would lie under the floor plating: blood becomes goo, the rest goes.
        if model == 'BloodSplats':
            out.append('    AS_KitDecal("KDGoo",%.2f,%.2f,%.1f);' % (x, y, rot))
        elif model.startswith('KP'):
            out.append('    AS_KitDecal("%s",%.2f,%.2f,%.1f);' % (model, x, y, rot))
        elif model == 'DOM_Crate':
            out.append('    AS_KitDecal("%s",%.2f,%.2f,%.1f);' % ('KPCrateG' if int(x + y) % 3 else 'KPCrateM', x, y, rot))
        elif model not in FLAT_PROPS:
            out.append('    AS_KitProp("%s",%.2f,%.2f,%.1f,%.3f);' % (model, x, y, rot, scale))
    for piece, x, y, rot in L.decal_spots(floor, room, solid):
        out.append('    AS_KitDecal("%s",%.2f,%.2f,%.1f);' % (piece, x, y, rot))
    out += ['}', 'void AS_LevelData%d () {' % n, '    int i;']
    out.append('    as_spawnX=%.2f;as_spawnY=%.2f;as_spawnFacing=%.1f;' % (L.SPAWN + (L.SPAWN_FACING,)))
    for i, (x, y) in enumerate(tour_spots(solid)):
        out.append('    as_tourX[%d]=%.2f;as_tourY[%d]=%.2f;' % (i, x, i, y))
    out.append('    as_tourCount=%d;as_tourAt= -1;' % len(L.AREAS))
    for x, y, kind, flick in L.LIGHTS + L.corridor_lamps(floor, room):
        out.append('    AS_Lamp(%.2f,%.2f,"%s",%d);' % (x, y, kind, flick))
    for i, (x, y) in enumerate(L.VENTS):
        out.append('    as_vent[%d]=Point(%.2f,%.2f);' % (i, x, y))
    out.append('    as_ventCount=%d;' % len(L.VENTS))
    for i, (x, y) in enumerate(L.AMMO):
        out.append('    AS_AmmoCrate(%d,%.2f,%.2f);' % (i, x, y))
    out.append('    as_ammoCount=%d;' % len(L.AMMO))
    for i, (name, (x0, y0, x1, y1), kind) in enumerate(L.AREAS):
        out.append('    as_roomX0[%d]=%d.0;as_roomY0[%d]=%d.0;as_roomX1[%d]=%d.0;as_roomY1[%d]=%d.0;as_roomKind[%d]="%s";as_roomName[%d]="%s";'
                   % (i, x0, i, y0, i, x1, i, y1, i, kind, i, name))
    out.append('    as_roomCount=%d;' % len(L.AREAS))
    for x, y in L.EGGS:
        out.append('    AS_SpawnAlien(AS_EGG,%.2f,%.2f,false);' % (x, y))
    for x, y, r in L.BIOMASS:
        out.append('    i=AS_SpawnAlien(AS_BIOMASS,%.2f,%.2f,false);if(i>=0) {as_aRadius[i]=%.2f;}' % (x, y, r))
        out.append('    AS_Creep(%.2f,%.2f,%.2f);' % (x, y, r + 1.5))
    for x, y, r in getattr(L, 'CREEP', [(43.0, 67.0, 9.0), (36.0, 70.0, 3.0), (50.0, 70.0, 3.0), (75.0, 63.0, 4.0), (81.0, 66.0, 3.0), (60.0, 65.0, 2.5)]):
        out.append('    AS_Creep(%.2f,%.2f,%.2f);' % (x, y, r))
    out.append('}')
    return '\n'.join(out)


def level_common():
    """What every level shares: the row readers, and the dispatch by level number."""
    out = ['void AS_WallRow (int y, string s) {', '    int x;', '    for(x=0;x<AS_W;x+=1) {as_wall[x][y]=StringSub(s,x+1,x+1)=="1";}', '}',
           'void AS_LevelNames () {']
    for n, (name, title, place, brief) in enumerate(LEVELS):
        out.append('    as_levelTitle[%d]="%s";as_levelPlace[%d]="%s";as_levelBrief[%d]="%s";' % (n, title, n, place, n, brief))
    out.append('    as_kitMode=true;')
    for k, kind in enumerate(L.KIT_KINDS):
        out.append('    as_kitPanels[%d]="%s";' % (k, ''.join(map(str, L.KIT_PANELS[kind]))))
    out += ['}', '// The level\'s tables, its lamps, crates, eggs and biomass; then the kit builds its deck.',
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
    for i, (name, (x0, y0, x1, y1)) in enumerate(L.ZONES):
        out.append('    as_zoneName[%d]="%s";as_zoneX0[%d]=%d.0;as_zoneY0[%d]=%d.0;as_zoneX1[%d]=%d.0;as_zoneY1[%d]=%d.0;as_zoneHit[%d]=false;'
                   % (i, name, i, x0, i, y0, i, x1, i, y1, i))
    out.append('    as_zoneCount=%d;' % len(L.ZONES))
    for i, (x, y) in enumerate(L.CHECKPOINTS):
        out.append('    as_cpX[%d]=%.2f;as_cpY[%d]=%.2f;' % (i, x, i, y))
    out.append('    as_cpCount=%d;' % len(L.CHECKPOINTS))
    out.append('    as_extX0=%d.0;as_extY0=%d.0;as_extX1=%d.0;as_extY1=%d.0;' % L.EXTRACT)
    out.append('    as_doorPanel=Point(%.2f,%.2f);' % L.CONSOLE)
    for i, (x, y, wait) in enumerate(L.ROUTE):
        out.append('    as_routeX[%d]=%.2f;as_routeY[%d]=%.2f;as_routeWait[%d]=%d;' % (i, x, i, y, i, wait))
    out.append('    as_routeN=%d;as_routeAt=0;' % len(L.ROUTE))
    for i, (x, y) in enumerate(L.WINDOWS):
        out.append('    as_winX[%d]=%d.0;as_winY[%d]=%d.0;' % (i, x, i, y))
    out.append('    as_winCount=%d;' % len(L.WINDOWS))
    if L.LIFT is not None:
        out.append('    as_liftX0=%d.0;as_liftY0=%d.0;as_liftX1=%d.0;as_liftY1=%d.0;' % L.LIFT)
        out.append('    as_doorX0=%d;as_doorY0=%d;as_doorX1=%d;as_doorY1=%d;' % L.DOOR)
        out.append('    as_liftPanel=Point(%.2f,%.2f);' % L.LIFT_PANEL)
        for k in range(4):
            out.append('    as_brIn[%d]=%d;as_brOut[%d]=%d;' % (k, L.BRIDGE_IN[k], k, L.BRIDGE_OUT[k]))
        for i, (x, y, w, face, side) in enumerate(L.shaft_columns()):
            out.append('    as_colX[%d]=%.2f;as_colY[%d]=%.2f;as_colW[%d]=%d.0;as_colFace[%d]=%.1f;as_colSide[%d]="%s";' % (i, x, i, y, i, w, i, face, i, side))
        out.append('    as_colCount=%d;' % len(L.shaft_columns()))
    else:
        out.append('    as_colCount=0;')
    out.append('}')
    return '\n'.join(out)


def mission_common():
    out = ['void AS_MissionData () {']
    for n in range(len(LEVELS)):
        out.append('    %sif(as_level==%d) {AS_MissionData%d();}' % ('else ' if n else '', n, n))
    out.append('}')
    return '\n'.join(out)


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
    code = code.replace('@W@', str(MW)).replace('@H@', str(MH)).replace('@LEVELS@', str(len(LEVELS)))
    assert '@' not in code.replace('"@', '').replace('@"', ''), 'unreplaced placeholder'
    for line, value in [('bool as_qa = false;', str(qa).lower()), ('bool as_demo = false;', str(demo).lower()),
                        ('bool as_auto = false;', str(auto).lower()), ('int as_startLevel = -1;', str(start)),
                        ('string as_bankName = "%s";' % BANK, '"%s"' % bank)]:
        assert line in code, 'build switch line missing: ' + line
        code = code.replace(line, line.rsplit('=', 1)[0] + '= ' + value + ';')
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
    files.update({'Base.SC2Assets/Derelict/UI/white.dds': shipkit.dds_rgba(white),
                  'Base.SC2Assets/Derelict/UI/vignette.dds': shipkit.dds_rgba(vig)})
    return files, frames


def compose(qa, demo=False, auto=False, start=-1):
    """Every level in one map: the terrain is a blank floor the size of the biggest level, and the script
    builds whichever level is being played from its strings (src/Kit.galaxy), then the next."""
    levels, missions, pieces, props, floors, report, maps = [], [], {}, set(), set(), [], []
    paint, signs = {}, {}
    sizes = []
    for name, *_ in LEVELS:
        L.use(name)
        sizes.append((L.W, L.H))
    MAP_SIZE = (max(w for w, h in sizes), max(h for w, h in sizes))
    for n, (name, *_) in enumerate(LEVELS):
        L.use(name)
        floor, room = L.carve()
        solid = L.blocked(floor)
        levels.append(level_galaxy(n, solid, room, floor, *MAP_SIZE))
        maps.append((floor, np.array([[L.in_void(x, y) for x in range(L.W)] for y in range(L.H)])))
        missions.append(mission_galaxy(n))
        props |= {p[0] for p in L.PROPS if p[0] not in FLAT_PROPS and not p[0].startswith('KP')}
        paint.update(L.paint_names())
        signs.update(L.sign_names())
        floors.add(L.FLOOR)
        if L.LIFT is not None:
            pieces.update(elevator.meshes(L.LIFT, L.BRIDGE_IN, L.BRIDGE_OUT, L.VOID, L.DOOR))
        report.append('%s %dx%d' % (name, L.W, L.H))
    assert len(floors) == 1, 'levels at different deck heights share one terrain: %s' % floors
    W, H = MAP_SIZE
    L.use(LEVELS[0][0])
    files = {}
    # Terrain: one flat deck for every level, plates with rust and wreckage, every cell open until the script shuts the hull.
    heights = np.full((H + 1, W + 1), L.FLOOR)
    masks, dominant = L.generic_masks(W, H)
    files.update(basemap.terrain_binaries(W, H, heights, masks, L.TEXTURES, dominant))
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
    textures = shipkit.hull_textures()
    textures.update(elevator.textures())
    from tools import deckart
    textures.update(deckart.sign_textures(signs))
    from tools import deckart
    shipkit.pack_textures(files, textures, {**shipkit.multiply_textures(), **deckart.paint_textures(paint)})
    emissive = {k for k, (d, e) in textures.items() if e is not None}
    for name, model in sorted(models.items()):
        files['Base.SC2Assets/Derelict/%s.m3' % name] = shipkit.write_m3(name, model.export(emissive))
    for name, model in sorted(pieces.items()):
        files['Base.SC2Assets/Derelict/%s.m3' % name] = shipkit.write_m3(name, model.export(emissive))
    fx_files, _ = fx.build()
    files.update(fx_files)
    files.update(alien.build())
    ui, frames = ui_textures(maps)
    files.update(ui)
    catalog.build(files, [], set(), kit_models=sorted(models), runtime_props=props, mesh_units=sorted(pieces))
    files['Objects'] = objects(L.SPAWN)
    files['MapScript.galaxy'] = script(levels, missions, W, H, qa, demo, auto, start, bank, frames).encode()
    return files, report


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--qa', action='store_true')
    ap.add_argument('--auto', action='store_true', help='QA autopilot: player 1 plays the campaign by itself and logs to the ASAuto bank')
    ap.add_argument('--demo', action='store_true', help='scripted firing range for screenshots (shows script errors too)')
    ap.add_argument('--start', type=int, default=-1, help='QA: skip the level menu and start at this level (0 the deck, 1 the cargo elevator)')
    args = ap.parse_args()
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
    report = pack(files, ROOT / 'dist' / (name + '.SC2Map'))
    report['levels'] = levels
    report['scriptBytes'] = len(files['MapScript.galaxy'])
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
