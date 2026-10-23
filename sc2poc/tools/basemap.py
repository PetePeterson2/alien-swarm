"""The blank SC2 map under the derelict: MapInfo, DocumentHeader and terrain layers.

Carried over from ../../Documents/GameNight/tools/basemap.py (which came from
Saboteur, where the binary layouts -- MapInfo v39, the t3 terrain layers and
DocumentHeader -- were decoded and proved in the client). Two changes:

* two dependencies (Swarm mod + Swarm campaign, as PUBG: Battle Royale ships
  with), so the campaign tileset doodads (Castanar, Moebius lab, Space
  Platform, Dominion lab ...) and every zerg model are available;
* players 1-4 are people and player 15 is the hostile owner of the aliens.
"""
import struct, xml.etree.ElementTree as ET
import numpy as np

DEPENDENCIES = ['bnet:Swarm (Mod)/0.0/999,file:Mods/Swarm.SC2Mod',
                'bnet:Swarm (Campaign)/0.0/999,file:Campaigns/Swarm.SC2Campaign']
EDITOR_QUAD = bytes([1, 5, 0, 16])
EDITOR_BUILD = 97563
QUANTIZE_BIAS = 1.0
QUANTIZE_SCALE = 1.0 / 2048.0
SYNC_CONSTANT = 4096
MASK = 8                      # texture-mask texels per map unit

u32 = lambda n: struct.pack('<I', n)
s32 = lambda n: struct.pack('<i', n)
cs = lambda s: s.encode() + b'\0'
ls = lambda s: struct.pack('<H', len(s.encode())) + s.encode()


def map_info(width, height, description, playable, options, players, base_height):
    """MapInfo v39. `playable` is (left, bottom, right, top)."""
    left, bottom, right, top = playable
    dx, dy = right - left, top - bottom
    # SC2 recomputes this from the parsed fields and refuses the map on a mismatch.
    integrity = (len(description) + 7 * height + 2 * (dx * dx + dy * dy)
                 + 3 * width - options.bit_count() - 17)
    b = b'IpaM' + u32(39) + struct.pack('<Q', integrity) + u32(width) + u32(height)
    b += u32(1) + u32(1)
    b += cs('') + cs('')
    b += u32(1) + u32(0)
    b += cs('Dark') + cs(description)
    b += s32(left) + s32(bottom) + s32(right) + s32(top) + u32(base_height)
    b += u32(0) + cs('') + ls('')
    b += s32(0) + s32(-1)
    b += u32(0) + u32(0) + u32(800) + u32(600)
    b += cs('') + ls('') + ls('')
    b += u32(options)
    b += u32(1) + u32(2) + u32(8192) + u32(0) + u32(0)
    b += bytes([16])
    b += u32(0)
    b += ls('')
    b += u32(len(players))
    for controller, control_type, team, ai_name in players:
        b += bytes([controller]) + s32(control_type) + s32(team) + cs(ai_name)
        b += s32(0) + s32(0) + u32(0) + cs('')
    b += u32(0) * 9
    b += s32(left) + s32(bottom) + s32(right) + s32(top)
    return b


def document_header(title, short, long_desc, player_names):
    b = b'H2CS' + u32(8) + b'2S\0\0' + EDITOR_QUAD + u32(EDITOR_BUILD) + u32(EDITOR_BUILD)
    b += u32(0) * 3 + u32(4) + u32(0)
    b += u32(len(DEPENDENCIES)) + b''.join(d.encode() + b'\0' for d in DEPENDENCIES)
    texts = {'DocInfo/Name': title, 'DocInfo/DescShort': short, 'DocInfo/DescLong': long_desc,
             'MapInfo/Player00/Name': 'Neutral'}
    for seat, name in enumerate(player_names, 1):
        texts['MapInfo/Player%02d/Name' % seat] = name
    b += u32(len(texts))
    for key, value in texts.items():
        kb, vb = key.encode(), value.encode()
        b += struct.pack('<H', len(kb)) + kb + b'SUne' + struct.pack('<H', len(vb)) + vb
    return b


def document_info():
    deps = ''.join('<Value>%s</Value>' % d for d in DEPENDENCIES)
    return ('<?xml version="1.0" encoding="utf-8"?><DocInfo><Dependencies>%s</Dependencies></DocInfo>' % deps).encode()


def terrain_xml(width, height, tileset, cliffset, textures, floor):
    terrain = ET.Element('terrain', version='115')
    hm = ET.SubElement(terrain, 'heightMap', tileSet=tileset,
                       uvtiling='%f %f 0.000000 0.000000 ' % (width * 3 / 32, height * 3 / 32),
                       dim='%d %d ' % (width + 1, height + 1),
                       offset='0.000000 0.000000 0.000000 ',
                       scale='1.000000e+00 1.000000e+00 1.000000e+00 ')
    cliffs = ET.SubElement(hm, 'cliffSetList', num='1')
    ET.SubElement(cliffs, 'cliffSet', i='0', name=cliffset)
    ET.SubElement(hm, 'vertData', quantizeBias=repr(QUANTIZE_BIAS), quantizeScale=repr(QUANTIZE_SCALE),
                  standardHeight='%f' % floor, name='t3HeightMap')
    ET.SubElement(hm, 'masks', name='t3TextureMasks')
    sets = ET.SubElement(hm, 'textureSetList', num='8')
    for i in range(8):
        ET.SubElement(sets, 'textureSet', i=str(i), name=tileset if i == 0 else '')
    tl = ET.SubElement(hm, 'textureList', num='64')
    for i in range(64):
        ET.SubElement(tl, 'texture', i=str(i), name=textures[i] if i < len(textures) else '')
    blocks = ET.SubElement(hm, 'blockTextureSetList', num=str((width // 8) * (height // 8)))
    for i in range((width // 8) * (height // 8)):
        ET.SubElement(blocks, 'blockTextureSet', i=str(i), tileSet='0')
    ET.SubElement(hm, 'cliffCellList', num=str((width // 2) * (height // 2)), numOccupied='0')
    ET.indent(terrain, space='    ')
    return ET.tostring(terrain, encoding='utf-8', xml_declaration=True)


def terrain_binaries(width, height, heights, masks, textures, dominant):
    """Height, texture and sim layers. `dominant` is the footstep texture index per cell [h, w]."""
    cells = width * height
    files = {}
    assert heights.shape == (height + 1, width + 1)
    assert masks.shape == (8, height * MASK, width * MASK)
    anchor = round(QUANTIZE_BIAS / QUANTIZE_SCALE)
    total = np.rint((heights + 2 * QUANTIZE_BIAS) / QUANTIZE_SCALE).astype(np.int64)
    value = total - anchor
    assert value.min() >= 0 and value.max() <= 0xffff
    packed = np.zeros((height + 1, width + 1, 3), dtype='<u2')
    packed[:, :, 0] = value
    packed[:, :, 1] = anchor
    files['t3HeightMap'] = b'HMAP' + u32(101) + u32(width + 1) + u32(height + 1) + bytes(16) + packed.tobytes()
    sync = np.zeros((height + 1, width + 1, 2), dtype='<u2')
    sync[:, :, 0] = np.rint(np.clip(heights, 0.0, 255.99) * 256).astype(np.int64)
    files['t3SyncHeightMap'] = (b'SMAP' + u32(102) + u32(width + 1) + u32(height + 1) + bytes(12)
                                + u32(SYNC_CONSTANT) * 3 + bytes(24) + sync.tobytes())
    files['t3SyncCliffLevel'] = b'CLIF' + u32(100) + u32(width) + u32(height) + bytes(16) + bytes(cells * 2)
    files['t3CellFlags'] = b'LFCT' + u32(102) + bytes(16) + u32(width) + u32(height) + bytes(cells)
    mh, mw = masks.shape[1], masks.shape[2]
    tiled = masks.reshape(8, mh // 64, 64, mw // 64, 64).transpose(0, 1, 3, 2, 4)
    body = ((tiled[..., ::2] << 4) | tiled[..., 1::2]).astype(np.uint8).tobytes()
    files['t3TextureMasks'] = b'MASK' + u32(102) + u32(0) + u32(mw) + u32(mh) + bytes(44) + body
    names = b''.join(cs(n) for n in textures[:8])
    info = np.zeros((height, width, 8), np.uint8)
    info[:, :, 0] = dominant
    files['t3SyncTextureInfo'] = b'RTXT' + u32(101) + u32(width) + u32(height) + u32(1) + names + info.tobytes()
    files['t3VertCol'] = b'VTCL' + u32(104) + bytes(24)
    files['t3Water'] = b'WATR' + u32(110) + bytes(24)
    files['t3HardTile'] = b'HRDT' + u32(102) + bytes(20)
    files['t3FluffDoodad'] = b'DLFT' + u32(103) + bytes(20)
    return files


def painted_pathing(open_cells):
    """PaintedPathingLayer: 512 x 512 half-cells of two bytes, (1, 1) open and (0, 0) shut.

    Both bytes matter. With (1, 0) for open, PathingType still reads every cell back
    correctly, but native movers stall in open floor (seen in the client, 2026-10-22).
    The Editor-saved and doodad-royale/heist layers only use (1, 1), (0, 0) and (128, 128).
    `open_cells` is a bool array [h, w] of whole map cells.
    """
    h, w = open_cells.shape
    path = np.zeros((512, 512, 2), np.uint8)
    half = np.repeat(np.repeat(open_cells, 2, 0), 2, 1)
    path[:h * 2, :w * 2, :] = half.astype(np.uint8)[:, :, None]
    return struct.pack('<4I', 0, 0, 512, 512) + path.tobytes()


def selftest():
    data = map_info(128, 128, 'MoebiusLab', (4, 4, 124, 124), 0x1000,
                    [(p, 3 if p == 0 else 1, 0 if p == 0 else -1, '') for p in range(5)], 16384)
    assert struct.unpack_from('<Q', data, 8)[0] == 58872
