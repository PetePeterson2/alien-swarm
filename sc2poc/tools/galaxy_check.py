"""Static checks over the generated MapScript.galaxy.

Not a type checker. It answers the questions that actually break a Galaxy build
on this project -- a misremembered native, the wrong number of arguments, a
global that was used before it was declared, a name that never existed -- by
reading the same SC2 5.0.16 headers the Editor compiles against.

Carried over from ../Saboteur, whose notes are explicit that a clean static
pass is not proof the native compiler agrees: this is a fast filter in front
of a real client load, not a substitute for one.

    py tools/galaxy_check.py editor/GameNight-QA.SC2Map/MapScript.galaxy
"""
from pathlib import Path
import argparse, re, sys

ROOT = Path(__file__).resolve().parents[1]
HEADERS = ROOT / 'tools/galaxy/headers'
HEADER_FILES = ['natives.galaxy', 'natives_missing.galaxy', 'NativeLib_h.galaxy',
                'swarmlib_h.galaxy', 'GameData/Game.galaxy', 'GameData/Sound.galaxy',
                '../extra_natives.galaxy']

KEYWORDS = {'if', 'else', 'while', 'for', 'do', 'return', 'break', 'continue',
            'const', 'static', 'native', 'include', 'struct', 'typedef',
            'true', 'false', 'null'}


def strip(source):
    """Remove comments and string bodies, keeping line structure intact."""
    # Match strings and comments in one pass: // inside an HTTPS invite is
    # part of the string, not the beginning of a Galaxy comment.
    tokens = r'"(?:\\.|[^"\\])*"|/\*.*?\*/|//[^\n]*'
    return re.sub(tokens, lambda m: ('""' if m.group(0).startswith('"') else '')
                  + '\n' * m.group(0).count('\n'), source, flags=re.S)


def header_types(text):
    return set(re.findall(r'^\s*native\s+(\w+)\s+\w+\s*\(', text, re.M))


class Unit:
    def __init__(self):
        self.types = {'void', 'bool', 'int', 'fixed', 'string', 'text', 'point', 'color',
                      'trigger', 'timer', 'unit', 'unitgroup', 'playergroup', 'region',
                      'order', 'actor', 'actorscope', 'bank', 'camerainfo', 'doodad',
                      'abilcmd', 'soundlink', 'sound', 'transmissionsource', 'revealer',
                      'marker', 'objective', 'ping', 'portrait', 'reply', 'unitfilter',
                      'unitref', 'wave', 'waveinfo', 'wavetarget', 'texttag', 'generic',
                      'aifilter', 'handle', 'conversation', 'transmission'}
        self.functions = {}     # name -> (min_args, max_args)
        self.globals = set()

    def add_signature(self, name, params):
        params = params.strip()
        if params in ('', 'void'):
            count = 0
        else:
            count = len([p for p in params.split(',') if p.strip()])
        known = self.functions.get(name)
        if known:
            self.functions[name] = (min(known[0], count), max(known[1], count))
        else:
            self.functions[name] = (count, count)

    def load_headers(self):
        for name in HEADER_FILES:
            text = strip((HEADERS / name).read_text(encoding='utf-8', errors='replace'))
            self.types |= header_types(text)
            for ret, func, params in re.findall(
                    r'(?:native\s+)?(\w+)\s+(\w+)\s*\(([^;{)]*)\)\s*[;{]', text):
                if ret in self.types:
                    self.add_signature(func, params)
            for _type, _dims, name in re.findall(
                    r'^\s*(?:const\s+)?(\w+)((?:\[\w+\])*)\s+(\w+)\s*(?:=[^;]*)?;', text, re.M):
                if _type in self.types:
                    self.globals.add(name)


def split_functions(text):
    """Yield (name, params, body, line) for every function definition."""
    for match in re.finditer(r'^(\w+)\s+(\w+)\s*\(([^)]*)\)\s*\{', text, re.M):
        ret, name, params = match.group(1), match.group(2), match.group(3)
        depth, i = 1, match.end()
        while depth and i < len(text):
            if text[i] == '{':
                depth += 1
            elif text[i] == '}':
                depth -= 1
            i += 1
        yield ret, name, params, text[match.end():i - 1], text[:match.start()].count('\n') + 1


def check(path):
    unit = Unit()
    unit.load_headers()
    raw = path.read_text(encoding='utf-8')
    text = strip(raw)
    problems = []

    if text.count('{') != text.count('}'):
        problems.append((0, 'unbalanced braces: %d { vs %d }'
                         % (text.count('{'), text.count('}'))))

    # Whatever is left after removing every function body is the global section.
    bodies = list(split_functions(text))
    top = text
    for ret, name, params, body, line in sorted(bodies, key=lambda b: -len(b[3])):
        if body:
            top = top.replace(body, '', 1)
    for match in re.finditer(r'^\s*(?:const\s+)?(\w+)((?:\[\w+\])*)\s+(\w+)\s*(?:=[^;]*)?;',
                             top, re.M):
        if match.group(1) in unit.types:
            unit.globals.add(match.group(3))

    for ret, name, params, body, line in bodies:
        unit.add_signature(name, params)
    for ret, name, params in re.findall(r'^(\w+)\s+(\w+)\s*\(([^)]*)\)\s*;', text, re.M):
        if ret in unit.types:
            unit.add_signature(name, params)

    for ret, name, params, body, line in bodies:
        if ret not in unit.types:
            problems.append((line, 'unknown return type %r on %s' % (ret, name)))
        scope = set(unit.globals)
        for param in params.split(','):
            bits = param.split()
            if len(bits) >= 2:
                # The native compiler reads a type name here as a type and
                # rejects the whole script with "Invalid parameter list".
                if bits[-1] in unit.types:
                    problems.append((line, 'parameter of %s is named after the type %r'
                                     % (name, bits[-1])))
                scope.add(bits[-1].strip('[]0123456789'))
        for match in re.finditer(r'^\s*(\w+)((?:\[\w+\])*)\s+(\w+)\s*(?:=[^;]*)?;', body, re.M):
            if match.group(1) in unit.types:
                scope.add(match.group(3))
        line_no = line
        for statement_line in body.split('\n'):
            line_no += 1
            for call in re.findall(r'\b([A-Za-z_]\w*)\s*\(', statement_line):
                if call in KEYWORDS or call in unit.types:
                    continue
                if call not in unit.functions:
                    problems.append((line_no, 'call to unknown function %s' % call))
            stripped = re.sub(r'\b[A-Za-z_]\w*\s*\(', '(', statement_line)
            for ident in re.findall(r'\b([A-Za-z_]\w*)\b', stripped):
                if ident in KEYWORDS or ident in unit.types or ident in scope:
                    continue
                if ident in unit.functions:
                    continue
                problems.append((line_no, 'unknown identifier %s' % ident))

    # Argument counts, evaluated over the whole file so nested calls are seen.
    for match in re.finditer(r'\b([A-Za-z_]\w*)\s*\(', text):
        name = match.group(1)
        if name in KEYWORDS or name in unit.types or name not in unit.functions:
            continue
        depth, i, args, empty = 1, match.end(), 1, True
        while depth and i < len(text):
            ch = text[i]
            if ch in '([':
                depth += 1
            elif ch in ')]':
                depth -= 1
            elif ch == ',' and depth == 1:
                args += 1
            elif not ch.isspace():
                empty = False
            i += 1
        if empty and args == 1:
            args = 0
        low, high = unit.functions[name]
        if not low <= args <= high:
            line = text[:match.start()].count('\n') + 1
            problems.append((line, '%s takes %s args, called with %d'
                             % (name, low if low == high else '%d-%d' % (low, high), args)))

    # Escapes inside string literals. The native compiler rejects the whole
    # script for one texture path written with single backslashes, and
    # with no script the map loads as an empty world -- so it is worth a line.
    for number, source_line in enumerate(raw.split('\n'), 1):
        code_part = source_line.split('//')[0]
        for literal in re.findall(r'"((?:[^"\\]|\\.)*)"', code_part):
            for escape in re.findall(r'\\(.)', literal):
                if escape not in '\\"ntr0':
                    problems.append((number, 'illegal escape sequence (backslash %s) '
                                             'in a string' % escape))

    # A local declared after the first statement of its function. The native
    # compiler rejects the whole script for it ("Error parsing function line,
    # possibly invalid variable name/function call") and the map loads as a
    # bare world; seen in the client on 2026-09-25 over a visibility call put
    # above the rest of a function's locals.
    decl = re.compile(r'^\s+(?:const\s+)?(\w+)(?:\[\d+\])*\s+(lv_\w+)\s*(?:=[^;]*)?;\s*$')
    head = re.compile(r'^\w[\w\[\]]*\s+\w+\s*\([^;]*\)\s*\{\s*$')
    inside = False
    statement = False
    for number, source_line in enumerate(text.split('\n'), 1):
        if head.match(source_line):
            inside, statement = True, False
            continue
        if inside and source_line.startswith('}'):
            inside = False
            continue
        if not inside or not source_line.strip():
            continue
        found = decl.match(source_line)
        if found and found.group(1) in unit.types:
            if statement:
                problems.append((number, 'local %s declared after a statement' % found.group(2)))
        else:
            statement = True

    problems.extend(short_labels(raw))
    return sorted(set(problems))


# A label shorter than its style's text puts "TextError: Text [..] is too tall
# for a single line. Exceeds by [n]" on screen. Minimum heights seen in the
# client: size 16 needs 22 (a 19 exceeded by 3, 2026-09-28), size 40 needs 52
# (a 46 exceeded by 6); size 20 is fine at 26, so the rest are taken as 1.3x.
LABEL_CALLS = {'gf_GnLabel': (1, 4)}   # (height, style) argument
LABEL_NEEDS = {16: 22, 40: 52}


def label_need(size):
    return LABEL_NEEDS.get(size, -(-13 * size // 10))


def call_args(text, start):
    """The top-level arguments of the call whose '(' ends just before `start`."""
    depth, out, cur, i = 0, [], [], start
    while i < len(text):
        c = text[i]
        if c == '"':
            end = i + 1
            while end < len(text) and text[end] != '"':
                end += 2 if text[end] == '\\' else 1
            cur.append(text[i:end + 1])
            i = end + 1
            continue
        if c == '(':
            depth += 1
        elif c == ')':
            if depth == 0:
                out.append(''.join(cur).strip())
                return out
            depth -= 1
        elif c == ',' and depth == 0:
            out.append(''.join(cur).strip())
            cur = []
            i += 1
            continue
        cur.append(c)
        i += 1
    return out


def short_labels(raw):
    problems = []
    for name, (h_at, style_at) in LABEL_CALLS.items():
        for match in re.finditer(r'\b%s\(' % name, raw):
            args = call_args(raw, match.end())
            if len(args) <= style_at:
                continue
            size = re.search(r'Size(\d+)', args[style_at])
            if not size:
                continue
            # Only a literal height can be judged here.
            heights = [int(h) for h in re.findall(r'\d+', args[h_at])] \
                if re.fullmatch(r'\d+', args[h_at]) else []
            need = label_need(int(size.group(1)))
            for height in heights:
                if height < need:
                    problems.append((raw.count('\n', 0, match.start()) + 1,
                                     'label %d high is too short for size %s text (needs %d)'
                                     % (height, size.group(1), need)))
    return problems


# Each mutation is a mistake that has to be caught, paired with the substring
# the report must contain. A checker that silently passes everything is worse
# than no checker, so this runs before every real check.
MUTATIONS = [
    ('gf_GnBitHas(', 'gf_GnBitHaz(', 'unknown function'),
    ('DialogControlSetVisible(', 'DialogControlSetVisibl(', 'unknown function'),
    ('gv_gnSeatCount', 'gv_gnSeetCount', 'unknown identifier'),
    ('RandomInt(0, 2)', 'RandomInt(0, 2, 9)', 'called with 3'),
    ('IntToString(c_gnFibsQuestions)', 'IntToString()', 'called with 0'),
    ('GnUI\\\\white.dds', 'GnUI\\white.dds', 'illegal escape'),
    ('bool gf_GnSeatOk (int seat) {', 'bool gf_GnSeatOk (int actor) {', 'named after the type'),
    ('    int lv_n;\n', '    lv_n = 0;\n    int lv_n;\n', 'declared after a statement'),
    ('gf_GnLabel(330, 40, 106, 30, "ModLeftSize24Bold"', 'gf_GnLabel(330, 20, 106, 30, "ModLeftSize24Bold"',
     'too short for size 24'),
]


def selftest(path):
    original = path.read_text(encoding='utf-8')
    scratch = path.with_suffix('.selftest.galaxy')
    failures = []
    try:
        for find, replace, expect in MUTATIONS:
            if find not in original:
                failures.append('mutation source %r not present' % find)
                continue
            scratch.write_text(original.replace(find, replace, 1), encoding='utf-8')
            found = [m for _, m in check(scratch) if expect in m]
            if not found:
                failures.append('%r -> %r was not reported as %r' % (find, replace, expect))
    finally:
        if scratch.exists():
            scratch.unlink()
    if failures:
        for line in failures:
            print('selftest FAILED: ' + line)
        sys.exit(2)
    print('galaxy_check selftest: %d injected mistakes all caught' % len(MUTATIONS))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('path', nargs='?', default='editor/GameNight.SC2Map/MapScript.galaxy')
    parser.add_argument('--no-selftest', action='store_true')
    args = parser.parse_args()
    path = Path(args.path)
    if not path.is_absolute():
        path = ROOT / path
    if not args.no_selftest:
        selftest(path)
    problems = check(path)
    lines = path.read_text(encoding='utf-8').split('\n')
    for line, message in problems:
        context = lines[line - 1].strip() if 0 < line <= len(lines) else ''
        print('%s:%d: %s' % (path.name, line, message))
        if context:
            print('    %s' % context)
    print('%d problem(s)' % len(problems))
    sys.exit(1 if problems else 0)


if __name__ == '__main__':
    main()
