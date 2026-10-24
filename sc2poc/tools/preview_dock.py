"""A rough CPU render of Landing Bay's outdoor deck from the game's top-down camera (distance 6): the deck,
the open drop past its railings (tools/elevator.py tex_open), hull caps with their faces, and the rails.
No lights. Prints the deck rows of the outdoor stretch too.

    py tools/preview_dock.py            writes dist/dock-preview.png (the dock, the walkway, the ramp, the yard)
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.argv = sys.argv[:1]                     # preview_lift reads a distance from the command line
from tools import preview_lift as P          # noqa: E402  (it also switches the level to cargo: switch back below)
from tools import level as L, elevator as E  # noqa: E402
from PIL import Image                         # noqa: E402

P.DIST = 6.0                                  # src/Marine.galaxy AS_TOP_DIST
L.use('landingbay')
floor, room = L.carve()
rows = L.deck_rows(floor, room)
opn = E.tex_open()[1].convert('RGB')
deck_t = Image.new('RGB', (8, 8), (110, 114, 118)); cap_t = Image.new('RGB', (8, 8), (14, 15, 17))
wall_t = Image.new('RGB', (8, 8), (150, 152, 150)); rail_t = Image.new('RGB', (8, 8), (200, 160, 40))
Z = L.WALL_H
UV = [(0, 1), (1, 1), (1, 0), (0, 0)]


def cell(x, y):
    return rows[y][x] if 0 <= x < L.W and 0 <= y < L.H else '#'


def frame(tx, ty):
    proj = P.camera(tx, ty)
    canvas = Image.new('RGB', (P.W, P.H), (0, 0, 0))
    quads = []
    for y in range(int(ty) - 10, int(ty) + 14):
        for x in range(int(tx) - 12, int(tx) + 13):
            c = cell(x, y)
            if c == 'o':
                u0, v0 = (x % 4) / 4, (y % 4) / 4
                quads.append((proj((x + .5, y + .5, 0))[2] + 60, [(x, y, 0), (x + 1, y, 0), (x + 1, y + 1, 0), (x, y + 1, 0)], opn,
                              [(u0, v0 + .25), (u0 + .25, v0 + .25), (u0 + .25, v0), (u0, v0)], 1.0))
            elif c in '#w':
                quads.append((proj((x + .5, y + .5, Z))[2], [(x, y, Z), (x + 1, y, Z), (x + 1, y + 1, Z), (x, y + 1, Z)], cap_t, UV, 1.0))
                if cell(x, y - 1) not in '#wv':   # the face toward the camera
                    quads.append((proj((x + .5, y, Z / 2))[2] - .01, [(x, y, 0), (x + 1, y, 0), (x + 1, y, Z), (x, y, Z)], wall_t, UV, 0.8))
            else:
                quads.append((proj((x + .5, y + .5, 0))[2] + 50, [(x, y, 0), (x + 1, y, 0), (x + 1, y + 1, 0), (x, y + 1, 0)], deck_t, UV, 1.0))
                for dx, dy, ((ax, ay), (bx, by)) in ((0, -1, ((x, y), (x + 1, y))), (0, 1, ((x, y + 1), (x + 1, y + 1))),
                                                     (-1, 0, ((x, y), (x, y + 1))), (1, 0, ((x + 1, y), (x + 1, y + 1)))):
                    if cell(x + dx, y + dy) == 'o':
                        for z in (0.55, 1.0):
                            quads.append((proj(((ax + bx) / 2, (ay + by) / 2, z))[2] - .05,
                                          [(ax, ay, z - .06), (bx, by, z - .06), (bx, by, z), (ax, ay, z)], rail_t, UV, 1.0))
    for d, c, t, uv, sh in sorted(quads, key=lambda q: -q[0]):
        P.draw(canvas, proj, c, t, uv, sh)
    return canvas


def main():
    shots = [frame(51.0, 7.5), frame(41.0, 6.5), frame(35.5, 14.0), frame(32.0, 25.0)]
    sheet = Image.new('RGB', (P.W * 2, P.H * 2))
    for i, im in enumerate(shots):
        sheet.paste(im, ((i % 2) * P.W, (i // 2) * P.H))
    out = ROOT / 'dist/dock-preview.png'
    sheet.save(out)
    x0, y0, x1, y1 = L.OUTDOORS
    print('\n'.join(rows[y][x0 - 2:x1] for y in range(y1 + 1, y0 - 1, -1)))
    print(out)


if __name__ == '__main__':
    main()
