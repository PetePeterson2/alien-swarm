"""Pictures of the screens an -Auto run saw, drawn from the ASUi bank, with layout checks.

In -Auto builds the script lists every label and image it makes (src/HUD.galaxy AS_UiReg) and, at set
moments, writes each visible one's dialog, anchor, offset, size, style, image, tint and text to the
ASUi bank (AS_UiDump). This draws each of those moments at SC2's 1920x1200 UI frame with the map's own
UI art (tools/hudart.py, tools/uiart.py) and font sizes (tools/catalog.py styles), and reports:

  - a label whose text is wider than its box (it would be cut or wrap past it);
  - a control that sticks out of its dialog, or a dialog off the screen;
  - two labels with text in one dialog that overlap.

It is a stand-in for looking at the screen, not the client's renderer: fonts are Arial at the style's
height, and markup other than colour and line breaks is ignored.

    py tools/uishots.py [ASUi.SC2Bank] [out dir]
"""
from pathlib import Path
import glob, os, re, sys, xml.etree.ElementTree as ET

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
W, H = 1920, 1200


def styles():
    src = (ROOT / 'tools/catalog.py').read_text(encoding='utf-8')
    colors = dict(re.findall(r"(\w+) = '(\d+,\d+,\d+,\d+)'", src))
    out = {}
    for name, size, align, color in re.findall(r"\('(AS\w+)', \w+, (\d+), '(\w+)', ('[\d,]+'|\w+), (?:True|False)\)", src):
        c = color.strip("'") if color.startswith("'") else colors.get(color, '255,255,255,255')
        a, r, g, b = (int(v) for v in c.split(','))
        out[name] = (int(size), align, (r, g, b))
    return out


def textures():
    import hudart, uiart
    t = {}
    t.update(hudart.textures(())[0])
    t.update(uiart.textures())
    t['white'] = Image.new('RGBA', (32, 32), (255, 255, 255, 255))
    return {k: v.convert('RGBA') for k, v in t.items()}


def place(anchor, ox, oy, w, h, pw, ph):
    col, row = anchor % 3, anchor // 3
    x = ox if col == 0 else (pw - w) // 2 + ox if col == 1 else pw - w - ox
    y = oy if row == 0 else (ph - h) // 2 + oy if row == 1 else ph - h - oy
    return x, y


def runs(text, base):
    """Markup to [(line, [(segment, colour)])]: <c val="RRGGBB"> colours, <n/> breaks, other tags dropped."""
    lines, cur, stack = [], [], [base]
    for tok in re.split(r'(<[^>]*>)', text or ''):
        if not tok:
            continue
        if tok.startswith('<'):
            m = re.match(r'<c val="#?([0-9A-Fa-f]{6})"', tok)
            if m:
                h = m.group(1)
                stack.append((int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)))
            elif tok.startswith('</c'):
                if len(stack) > 1:
                    stack.pop()
            elif tok.startswith('<n'):
                lines.append(cur)
                cur = []
            continue
        cur.append((tok.replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&'), stack[-1]))
    lines.append(cur)
    return lines


FONTS = {}


def font(size):
    if size not in FONTS:
        try:
            FONTS[size] = ImageFont.truetype('arial.ttf', size)
        except OSError:
            FONTS[size] = ImageFont.load_default()
    return FONTS[size]


def load(bank):
    root = ET.parse(bank).getroot()
    shots = {}
    global hidden
    hidden = {}
    for sec in root.findall('Section'):
        vals = {}
        for k in sec.findall('Key'):
            v = k.find('Value')
            vals[k.get('name')] = v.get('string') if v.get('string') is not None else v.get('text') if v.get('text') is not None else v.get('int')
        n = int(vals.get('n') or 0)
        rows = []
        for i in range(n):
            raw = vals.get(str(i))
            if raw is None:
                continue
            f = raw.split('|')
            vis, f = f[0], f[1:]
            if vis != '11':
                hidden[sec.get('name')] = hidden.get(sec.get('name'), 0) + 1
                continue
            d = dict(dialog=int(f[0]), dw=int(f[1]), dh=int(f[2]), da=int(f[3]), dx=int(f[4]), dy=int(f[5]), pri=int(f[6]),
                     type=int(f[7]), anchor=int(f[8]), x=int(f[9]), y=int(f[10]), w=int(f[11]), h=int(f[12]),
                     what=f[13] if len(f) > 13 else '', tint=f[14] if len(f) > 14 else '', text=vals.get(str(i) + 't'), order=i)
            rows.append(d)
        shots[sec.get('name')] = rows
    return shots


def draw(rows, tex, sty):
    im = Image.new('RGBA', (W, H), (18, 22, 26, 255))
    dr = ImageDraw.Draw(im)
    problems = []
    dialogs = {}
    for r in rows:
        dx, dy = place(r['da'], r['dx'], r['dy'], r['dw'], r['dh'], W, H)
        dialogs[r['dialog']] = (dx, dy, r['dw'], r['dh'], r['pri'])
    for d, (dx, dy, dw, dh, _) in dialogs.items():
        # Wider or taller than the frame on purpose: full-bleed backgrounds for wide screens.
        if dw < W and dh < H and (dx < -2 or dy < -2 or dx + dw > W + 2 or dy + dh > H + 2):
            problems.append('dialog %d (%dx%d) is off the screen at %d,%d' % (d, dw, dh, dx, dy))
    boxes = []
    for r in sorted(rows, key=lambda r: (dialogs[r['dialog']][4], r['order'])):
        dx, dy, dw, dh, _ = dialogs[r['dialog']]
        x, y = place(r['anchor'], r['x'], r['y'], r['w'], r['h'], dw, dh)
        X, Y, w, h = dx + x, dy + y, max(1, r['w']), max(1, r['h'])
        # Backgrounds wider than their dialog bleed past it on purpose (wide screens).
        if (w < dw or h < dh) and not (w >= dw and x <= 0) and (x < -2 or y < -2 or x + w > dw + 2 or y + h > dh + 2):
            label = (r['text'] or r['what'] or '')[:40]
            problems.append('control in dialog %d sticks out of it (%d,%d %dx%d in %dx%d): %s' % (r['dialog'], x, y, w, h, dw, dh, label))
        if r['type'] == 2:
            name = re.sub(r'.*\\', '', r['what']).replace('.dds', '')
            t = tex.get(name)
            if t is None:
                dr.rectangle([X, Y, X + w, Y + h], outline=(120, 120, 120, 255))
                continue
            t = t.resize((w, h))
            if r['tint']:
                k = [int(v) for v in r['tint'].split(',')]
                if k != [255, 255, 255]:
                    t = _tint(t, k)
            _paste_clipped(im, t, X, Y)
        else:
            size, align, color = sty.get(r['what'], (18, 'Left', (255, 255, 255)))
            lines = runs(r['text'], color)
            if not any(seg.strip() for line in lines for seg, _ in line):
                continue
            f = font(size)
            lh = int(size * 1.15)
            # A box two lines tall or more wraps at word boundaries, as the client does.
            if h >= lh * 1.8:
                lines = wrap(lines, w, f, dr)
            total = lh * len(lines)
            ty = Y + (h - total) // 2
            widest = 0
            top = ty
            for line in lines:
                lw = sum(dr.textlength(seg, font=f) for seg, _ in line)
                widest = max(widest, lw)
                tx = X if align == 'Left' else X + (w - lw) // 2 if align == 'Center' else X + w - lw
                for seg, c in line:
                    dr.text((tx, ty), seg, font=f, fill=c + (255,))
                    tx += dr.textlength(seg, font=f)
                ty += lh
            plain = ' / '.join(''.join(seg for seg, _ in line) for line in lines)
            if widest > w + 4 and len(lines) == 1:
                problems.append('text wider than its box (%d > %d px) in dialog %d: %r' % (widest, w, r['dialog'], plain[:60]))
            if total > h + lh * 0.6 and len(lines) > 1:
                problems.append('text taller than its box (%d > %d px) in dialog %d: %r' % (total, h, r['dialog'], plain[:60]))
            left = X if align == 'Left' else X + (w - widest) // 2 if align == 'Center' else X + w - widest
            boxes.append((r['dialog'], left, top + lh * 0.15, left + widest, top + total - lh * 0.15, plain))
    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            a, b = boxes[i], boxes[j]
            if a[0] != b[0]:
                continue
            ix = min(a[3], b[3]) - max(a[1], b[1]); iy = min(a[4], b[4]) - max(a[2], b[2])
            if ix > 6 and iy > 6:
                small = min((a[3] - a[1]) * (a[4] - a[2]), (b[3] - b[1]) * (b[4] - b[2]))
                if small > 0 and ix * iy > 0.3 * small:
                    problems.append('labels overlap in dialog %d: %r and %r' % (a[0], a[5][:40], b[5][:40]))
    return im, problems


def wrap(lines, width, f, dr):
    out = []
    for line in lines:
        cur, cw = [], 0.0
        for seg, c in line:
            for word in re.split(r'(\s+)', seg):
                if not word:
                    continue
                ww = dr.textlength(word, font=f)
                if cw + ww > width and cur and word.strip():
                    out.append(cur)
                    cur, cw = [], 0.0
                    if not word.strip():
                        continue
                cur.append((word, c))
                cw += ww
        out.append(cur)
    return out


def _tint(t, k):
    r, g, b, a = t.split()
    r = r.point(lambda v: v * k[0] // 255); g = g.point(lambda v: v * k[1] // 255); b = b.point(lambda v: v * k[2] // 255)
    return Image.merge('RGBA', (r, g, b, a))


def _paste_clipped(im, t, X, Y):
    box = (max(0, -X), max(0, -Y), min(t.width, W - X), min(t.height, H - Y))
    if box[2] > box[0] and box[3] > box[1]:
        im.alpha_composite(t.crop(box), (max(0, X), max(0, Y)))


def main():
    bank = sys.argv[1] if len(sys.argv) > 1 else max(glob.glob(r'C:\Users\drink\OneDrive\Documents\StarCraft II\**\ASUi.SC2Bank', recursive=True), key=os.path.getmtime)
    out = Path(sys.argv[2] if len(sys.argv) > 2 else ROOT / 'dist/screens/ui')
    out.mkdir(parents=True, exist_ok=True)
    tex, sty = textures(), styles()
    total = 0
    for name, rows in load(bank).items():
        im, problems = draw(rows, tex, sty)
        im.convert('RGB').save(out / (name + '.png'))
        print('%s: %d controls shown, %d hidden, %d problem(s) -> %s' % (name, len(rows), hidden.get(name, 0), len(problems), out / (name + '.png')))
        for p in problems:
            print('    ' + p)
        total += len(problems)
    print('%d problem(s)' % total)


if __name__ == '__main__':
    main()
