"""Constant array indexes past the declared size, in the generated MapScript.galaxy.

The level data is written out as long runs of `as_x[17]=...;`; a level with
more of something than the array holds fails at load ("Trying to access an
element past the end of an array") before any of the map runs.

    py tools/galaxy_bounds.py editor/AlienPOC-QA.SC2Map/MapScript.galaxy
"""
from pathlib import Path
import re, sys

ROOT = Path(__file__).resolve().parents[1]


def main():
    path = Path(sys.argv[1] if len(sys.argv) > 1 else 'editor/AlienPOC-QA.SC2Map/MapScript.galaxy')
    if not path.is_absolute():
        path = ROOT / path
    src = path.read_text(encoding='utf-8')
    src = re.sub(r'"(?:\\.|[^"\\])*"|//[^\n]*', '""', src)
    consts = {m.group(1): int(m.group(2)) for m in re.finditer(r'^\s*const\s+int\s+(\w+)\s*=\s*(-?\d+)\s*;', src, re.M)}

    def size(expr):
        expr = expr.strip()
        if expr.isdigit():
            return int(expr)
        if expr in consts:
            return consts[expr]
        try:
            return int(eval(re.sub(r'\w+', lambda m: str(consts.get(m.group(0), m.group(0))), expr), {}))
        except Exception:
            return None

    arrays = {}
    for m in re.finditer(r'^(?:static\s+)?\w+((?:\[[^\]\n]+\])+)\s+(\w+)\s*;', src, re.M):
        dims = [size(d) for d in re.findall(r'\[([^\]]+)\]', m.group(1))]
        arrays[m.group(2)] = dims
    lines = src.split('\n')
    bad = 0
    for n, line in enumerate(lines, 1):
        for m in re.finditer(r'\b(\w+)((?:\[\s*\d+\s*\])+)', line):
            dims = arrays.get(m.group(1))
            if not dims:
                continue
            idx = [int(x) for x in re.findall(r'\d+', m.group(2))]
            for k, (i, d) in enumerate(zip(idx, dims)):
                if d is not None and i >= d:
                    print('%d: %s index %d is past size %d (dimension %d)' % (n, m.group(1), i, d, k + 1))
                    bad += 1
    print('%d out-of-bounds constant index(es)' % bad)
    sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()
