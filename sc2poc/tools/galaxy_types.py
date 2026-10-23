"""A type checker for the generated MapScript.galaxy.

galaxy_check.py answers "does this name exist"; this answers "does this
expression have the type the place it sits in needs" -- the errors the client
reports as "Implicit cast not allowed" or "Parameter type does not match the
function definition". The client stops at the first of those, so one bad
line costs a whole relaunch to find; this finds them all in one pass.

Rules, as the 5.0 compiler applies them (calibrated on builds the client ran):
  - no implicit casts between int, fixed, bool, string and text, except that
    an int literal may stand where a fixed is wanted;
  - string + string and text + text concatenate, string + text does not;
  - conditions (if, while, for, &&, ||, !) take bool only;
  - null stands for any handle, string or text.

    py tools/galaxy_types.py editor/AlienPOC-QA.SC2Map/MapScript.galaxy
"""
from pathlib import Path
import re, sys

ROOT = Path(__file__).resolve().parents[1]
HEADERS = ROOT / 'tools/galaxy/headers'
HEADER_FILES = ['natives.galaxy', 'natives_missing.galaxy', 'NativeLib_h.galaxy',
                'swarmlib_h.galaxy', 'GameData/Game.galaxy', 'GameData/Sound.galaxy',
                '../extra_natives.galaxy']

TOKEN = re.compile(r'''
    (?P<ws>\s+|//[^\n]*|/\*.*?\*/)
  | (?P<str>"(?:\\.|[^"\\])*")
  | (?P<chr>'(?:\\.|[^'\\])*')
  | (?P<num>0[xX][0-9a-fA-F]+|\d+\.\d*|\.\d+|\d+)
  | (?P<id>[A-Za-z_]\w*)
  | (?P<op><<=|>>=|==|!=|<=|>=|&&|\|\||\+=|-=|\*=|/=|%=|&=|\|=|\^=|<<|>>|->|[-+*/%<>=!&|^~?:;,.(){}\[\]])
''', re.S | re.X)

PRIM = {'int', 'fixed', 'bool', 'string', 'text', 'byte', 'void', 'char'}
NUM = {'int', 'fixed', 'byte'}
UNKNOWN = ('?', 0)
NULL = ('null', 0)


class Tok:
    __slots__ = ('kind', 'val', 'line')

    def __init__(self, kind, val, line):
        self.kind, self.val, self.line = kind, val, line


def tokenize(src):
    out, pos, line = [], 0, 1
    while pos < len(src):
        m = TOKEN.match(src, pos)
        if not m:
            raise SyntaxError('bad character %r at line %d' % (src[pos], line))
        kind = m.lastgroup
        val = m.group(kind)
        if kind != 'ws':
            out.append(Tok(kind, val, line))
        line += val.count('\n')
        pos = m.end()
    out.append(Tok('eof', '', line))
    return out


def tname(t):
    if t[0] == '?':
        return '?'
    return t[0] + '[]' * t[1]


class Checker:
    def __init__(self):
        self.funcs = {}      # name -> (ret, [param types], variadic)
        self.globals = {}    # name -> type
        self.structs = {}    # name -> {field: type}
        self.types = set(PRIM) | {'null'}
        self.problems = []
        self.where = ''

    # ---- token stream ------------------------------------------------
    def load(self, toks, report=True):
        self.t, self.i, self.report = toks, 0, report

    def peek(self, k=0):
        return self.t[min(self.i + k, len(self.t) - 1)]

    def next(self):
        tok = self.t[self.i]
        self.i += 1
        return tok

    def accept(self, val):
        if self.peek().val == val and self.peek().kind in ('op', 'id'):
            self.i += 1
            return True
        return False

    def expect(self, val):
        tok = self.next()
        if tok.val != val:
            raise SyntaxError('line %d: expected %r, got %r' % (tok.line, val, tok.val))
        return tok

    def problem(self, line, msg):
        if self.report:
            self.problems.append((line, '%s: %s' % (self.where, msg) if self.where else msg))

    # ---- types -------------------------------------------------------
    def is_type_start(self):
        tok = self.peek()
        if tok.kind != 'id':
            return False
        if tok.val in self.types:
            return True
        # A handle type seen in no declaration yet: "name name" or "name[...] name".
        nxt = self.peek(1)
        return False

    def parse_type(self):
        tok = self.next()
        base = tok.val
        if base == 'struct':
            base = self.next().val
        if self.peek().val == '<':     # structref<X>, arrayref<..>, funcref<..>
            depth = 0
            while True:
                v = self.next().val
                if v == '<':
                    depth += 1
                elif v == '>':
                    depth -= 1
                    if depth == 0:
                        break
                elif v == '>>':
                    depth -= 2
                    if depth <= 0:
                        break
            base = '?'
        dims = 0
        while self.peek().val == '[':
            self.skip_brackets()
            dims += 1
        self.types.add(base)
        return (base, dims)

    def skip_brackets(self):
        self.expect('[')
        depth = 1
        while depth:
            v = self.next().val
            if v == '[':
                depth += 1
            elif v == ']':
                depth -= 1

    def skip_to(self, val):
        depth = 0
        while True:
            tok = self.next()
            if tok.kind == 'eof':
                return
            if tok.val in '({[':
                depth += 1
            elif tok.val in ')}]':
                depth -= 1
            elif tok.val == val and depth <= 0:
                return

    # ---- top level ---------------------------------------------------
    def parse_unit(self, toks, report):
        """Declarations of one file. Function bodies are recorded, checked later."""
        self.load(toks, report)
        bodies = []
        while self.peek().kind != 'eof':
            tok = self.peek()
            if tok.val == 'include':
                self.next(); self.next()
                continue
            if tok.val == ';':
                self.next()
                continue
            if tok.val == 'typedef':
                self.next()
                t = self.parse_type()
                name = self.next().val
                self.types.add(name)
                self.alias = getattr(self, 'alias', {})
                self.alias[name] = t
                self.expect(';')
                continue
            if tok.val == 'struct' and self.peek(2).val == '{':
                self.next()
                name = self.next().val
                self.types.add(name)
                self.expect('{')
                fields = {}
                while not self.accept('}'):
                    ft = self.parse_type()
                    fname = self.next().val
                    while self.peek().val == '[':
                        self.skip_brackets()
                        ft = (ft[0], ft[1] + 1)
                    fields[fname] = ft
                    self.expect(';')
                self.accept(';')
                self.structs[name] = fields
                continue
            native = False
            while tok.val in ('native', 'static', 'const'):
                if tok.val == 'native':
                    native = True
                self.next()
                tok = self.peek()
            t = self.parse_type()
            name_tok = self.next()
            name = name_tok.val
            if self.peek().val == '(':
                params, variadic = self.parse_params()
                self.funcs[name] = (t, params, variadic)
                if self.peek().val == '{':
                    start = self.i
                    self.skip_block()
                    bodies.append((name, start, params))
                else:
                    self.expect(';')
                continue
            while self.peek().val == '[':
                self.skip_brackets()
                t = (t[0], t[1] + 1)
            self.globals[name] = t
            if self.accept('='):
                start = self.i
                self.skip_to(';')
                bodies.append(('=' + name, start, None))
            else:
                self.expect(';')
        return bodies

    def parse_params(self):
        self.expect('(')
        params, variadic = [], False
        if self.accept(')'):
            return params, variadic
        while True:
            if self.peek().val == '.':
                while self.accept('.'):
                    pass
                variadic = True
            else:
                self.accept('const')
                t = self.parse_type()
                pname = self.next().val
                while self.peek().val == '[':
                    self.skip_brackets()
                    t = (t[0], t[1] + 1)
                params.append((pname, t))
            if self.accept(')'):
                return params, variadic
            self.expect(',')

    def skip_block(self):
        self.expect('{')
        depth = 1
        while depth:
            v = self.next()
            if v.kind == 'eof':
                return
            if v.val == '{':
                depth += 1
            elif v.val == '}':
                depth -= 1

    # ---- bodies ------------------------------------------------------
    def check_body(self, name, start, params):
        self.i = start
        if name.startswith('='):
            self.where = 'global ' + name[1:]
            self.locals = {}
            want = self.globals[name[1:]]
            got, line = self.expr_line()
            self.assignable(want, got, line, 'initialiser')
            return
        self.where = name
        self.ret = self.funcs[name][0]
        self.locals = {p: t for p, t in params}
        self.block()

    def block(self):
        self.expect('{')
        while not self.accept('}'):
            if self.peek().kind == 'eof':
                return
            self.statement()

    def is_decl(self):
        tok = self.peek()
        if tok.kind != 'id' or tok.val not in self.types:
            return False
        if tok.val in self.locals or tok.val in self.globals:
            return False
        nxt = self.peek(1)
        return nxt.kind == 'id' or nxt.val in ('[', '<')

    def statement(self):
        tok = self.peek()
        v = tok.val
        if v == '{':
            self.block()
        elif v == ';':
            self.next()
        elif v == 'if' and tok.kind == 'id':
            self.next(); self.expect('(')
            self.cond(self.expr(), tok.line, 'if')
            self.expect(')')
            self.statement()
            if self.accept('else'):
                self.statement()
        elif v == 'while' and tok.kind == 'id':
            self.next(); self.expect('(')
            self.cond(self.expr(), tok.line, 'while')
            self.expect(')')
            self.statement()
        elif v == 'do' and tok.kind == 'id':
            self.next(); self.statement(); self.expect('while'); self.expect('(')
            self.cond(self.expr(), tok.line, 'do-while')
            self.expect(')'); self.expect(';')
        elif v == 'for' and tok.kind == 'id':
            self.next(); self.expect('(')
            if not self.accept(';'):
                self.simple(); self.expect(';')
            if not self.accept(';'):
                self.cond(self.expr(), tok.line, 'for'); self.expect(';')
            if not self.accept(')'):
                self.simple(); self.expect(')')
            self.statement()
        elif v == 'return' and tok.kind == 'id':
            self.next()
            if self.accept(';'):
                if self.ret[0] != 'void':
                    self.problem(tok.line, 'return with no value from %s function' % tname(self.ret))
                return
            got = self.expr()
            if self.ret[0] == 'void':
                self.problem(tok.line, 'void function returns a value')
            else:
                self.assignable(self.ret, got, tok.line, 'return')
            self.expect(';')
        elif v in ('break', 'continue') and tok.kind == 'id':
            self.next(); self.expect(';')
        elif self.is_decl():
            self.accept('const')
            t = self.parse_type()
            while True:
                n = self.next()
                tt = t
                while self.peek().val == '[':
                    self.skip_brackets()
                    tt = (tt[0], tt[1] + 1)
                self.locals[n.val] = tt
                if self.accept('='):
                    got = self.expr()
                    self.assignable(tt, got, n.line, 'initialiser of ' + n.val)
                if not self.accept(','):
                    break
            self.expect(';')
        else:
            self.simple()
            self.expect(';')

    def simple(self):
        line = self.peek().line
        lhs = self.expr()
        op = self.peek().val
        if self.peek().kind == 'op' and op in ('=', '+=', '-=', '*=', '/=', '%=', '&=', '|=', '^=', '<<=', '>>='):
            self.next()
            rhs = self.expr()
            if op == '=':
                self.assignable(lhs, rhs, line, 'assignment')
            elif op == '+=':
                res = self.binop('+', lhs, rhs, line)
                if res != UNKNOWN:
                    self.assignable(lhs, res, line, '+=')
            else:
                res = self.binop(op[:-1], lhs, rhs, line)
                if res != UNKNOWN:
                    self.assignable(lhs, res, line, op)

    # ---- expressions -------------------------------------------------
    PREC = [('||',), ('&&',), ('|',), ('^',), ('&',), ('==', '!='), ('<', '>', '<=', '>='), ('<<', '>>'), ('+', '-'), ('*', '/', '%')]

    def expr_line(self):
        line = self.peek().line
        return self.expr(), line

    def expr(self, level=0):
        if level == len(self.PREC):
            return self.unary()
        left = self.expr(level + 1)
        while self.peek().kind == 'op' and self.peek().val in self.PREC[level]:
            tok = self.next()
            right = self.expr(level + 1)
            left = self.binop(tok.val, left, right, tok.line)
        return left

    def binop(self, op, a, b, line):
        if a == UNKNOWN or b == UNKNOWN:
            return UNKNOWN
        sa, sb = a[1] == 0, b[1] == 0
        if op in ('&&', '||'):
            for x in (a, b):
                if x != ('bool', 0):
                    self.problem(line, '%s takes bool, got %s' % (op, tname(x)))
            return ('bool', 0)
        if op in ('==', '!='):
            if not self.comparable(a, b):
                self.problem(line, 'compares %s %s %s' % (tname(a), op, tname(b)))
            return ('bool', 0)
        if op in ('<', '>', '<=', '>='):
            if not (sa and sb and a[0] in NUM and b[0] in NUM):
                self.problem(line, 'orders %s %s %s' % (tname(a), op, tname(b)))
            return ('bool', 0)
        if op in ('<<', '>>', '&', '|', '^'):
            if a == ('bool', 0) and b == ('bool', 0) and op in ('&', '|', '^'):
                return ('bool', 0)
            if a != ('int', 0) or b != ('int', 0):
                self.problem(line, '%s takes int, got %s and %s' % (op, tname(a), tname(b)))
            return ('int', 0)
        # + - * / %
        if sa and sb and a[0] in NUM and b[0] in NUM:
            if a[0] != b[0]:
                self.problem(line, 'mixes %s %s %s (no implicit cast)' % (tname(a), op, tname(b)))
                return ('fixed', 0)
            return a
        if op == '+' and a == b and a[0] in ('string', 'text'):
            return a
        self.problem(line, 'bad operands %s %s %s' % (tname(a), op, tname(b)))
        return UNKNOWN

    def comparable(self, a, b):
        a, b = fold_intlit(a), fold_intlit(b)
        if a[0] in NUM and b[0] in NUM and not a[1] and not b[1] and a[0] != b[0]:
            return False
        if a == b:
            return True
        if a == NULL:
            return b[0] not in NUM | {'bool'} or b[1] > 0
        if b == NULL:
            return a[0] not in NUM | {'bool'} or a[1] > 0
        return False

    def unary(self):
        tok = self.peek()
        if tok.kind == 'op' and tok.val in ('-', '!', '~', '+'):
            self.next()
            t = self.unary()
            if t == UNKNOWN:
                return t
            if tok.val == '!':
                if t != ('bool', 0):
                    self.problem(tok.line, '! takes bool, got %s' % tname(t))
                return ('bool', 0)
            if tok.val == '~':
                return ('int', 0)
            if t[0] == 'intlit':
                return t
            if t[0] not in NUM or t[1]:
                self.problem(tok.line, 'unary %s on %s' % (tok.val, tname(t)))
            return t
        return self.postfix()

    def postfix(self):
        t, lit = self.primary()
        while True:
            v = self.peek().val
            if v == '[' and self.peek().kind == 'op':
                tok = self.next()
                idx = self.expr()
                self.expect(']')
                if idx != UNKNOWN and fold_intlit(idx) != ('int', 0):
                    self.problem(tok.line, 'array index is %s' % tname(idx))
                if t == UNKNOWN:
                    continue
                if t[1] == 0:
                    self.problem(tok.line, 'indexes non-array %s' % tname(t))
                    t = UNKNOWN
                else:
                    t = (t[0], t[1] - 1)
            elif v in ('.', '->') and self.peek().kind == 'op':
                tok = self.next()
                field = self.next().val
                if t == UNKNOWN:
                    continue
                fields = self.structs.get(t[0])
                if fields is None or t[1]:
                    self.problem(tok.line, '.%s on %s' % (field, tname(t)))
                    t = UNKNOWN
                elif field not in fields:
                    self.problem(tok.line, 'struct %s has no field %s' % (t[0], field))
                    t = UNKNOWN
                else:
                    t = fields[field]
            else:
                return t

    def primary(self):
        tok = self.next()
        if tok.kind == 'num':
            if '.' in tok.val:
                return ('fixed', 0), True
            self.last_int_literal = True
            return ('intlit', 0), True
        if tok.kind == 'str':
            return ('string', 0), True
        if tok.kind == 'chr':
            return ('char', 0), True
        if tok.val == '(':
            t = self.expr()
            self.expect(')')
            return t, False
        if tok.kind == 'id':
            if tok.val in ('true', 'false'):
                return ('bool', 0), True
            if tok.val == 'null':
                return NULL, True
            if self.peek().val == '(':
                return self.call(tok), False
            if tok.val in self.locals:
                return self.locals[tok.val], False
            if tok.val in self.globals:
                return self.globals[tok.val], False
            if tok.val in self.funcs:
                return UNKNOWN, False
            self.problem(tok.line, 'unknown name %s' % tok.val)
            return UNKNOWN, False
        raise SyntaxError('line %d: unexpected %r' % (tok.line, tok.val))

    def call(self, tok):
        self.expect('(')
        args = []
        if not self.accept(')'):
            while True:
                line = self.peek().line
                args.append((self.expr(), line))
                if self.accept(')'):
                    break
                self.expect(',')
        f = self.funcs.get(tok.val)
        if f is None:
            self.problem(tok.line, 'unknown function %s' % tok.val)
            return UNKNOWN
        ret, params, variadic = f
        if len(args) < len(params) or (len(args) > len(params) and not variadic):
            self.problem(tok.line, '%s takes %d argument(s), given %d' % (tok.val, len(params), len(args)))
        for (got, line), (pname, want) in zip(args, params):
            self.assignable(want, got, line, '%s(%s)' % (tok.val, pname))
        return ret

    def cond(self, t, line, what):
        if t != UNKNOWN and t != ('bool', 0):
            self.problem(line, '%s condition is %s' % (what, tname(t)))

    def assignable(self, want, got, line, what):
        if want == UNKNOWN or got == UNKNOWN or want[0] == '?':
            return
        want = getattr(self, 'alias', {}).get(want[0], None) and (self.alias[want[0]][0], want[1] + self.alias[want[0]][1]) or want
        if got[0] == 'intlit':
            if want in (('int', 0), ('fixed', 0), ('byte', 0)):
                return
            got = ('int', 0)
        if want == got:
            if want[1] > 0 or want[0] in self.structs:
                self.problem(line, '%s copies a whole %s (bulk copy not supported)' % (what, tname(want)))
            return
        if got == NULL and (want[0] not in NUM | {'bool'} or want[1] > 0):
            return
        if want == ('byte', 0) and got == ('int', 0):
            return
        self.problem(line, '%s wants %s, given %s' % (what, tname(want), tname(got)))


def fold_intlit(t):
    return ('int', 0) if t and t[0] == 'intlit' else t


# int literals act as int everywhere but in an assignment to fixed: wrap binop/comparable.
_binop = Checker.binop
def _binop_lit(self, op, a, b, line):
    la, lb = a[0] == 'intlit', b[0] == 'intlit'
    if la and lb:
        res = _binop(self, op, ('int', 0), ('int', 0), line)
        return ('intlit', 0) if res == ('int', 0) else res
    # an int literal beside a fixed reads as a fixed literal
    if la and b == ('fixed', 0):
        a = b
    if lb and a == ('fixed', 0):
        b = a
    return _binop(self, op, fold_intlit(a), fold_intlit(b), line)
Checker.binop = _binop_lit

_unary = Checker.unary
def _unary_lit(self):
    return _unary(self)
Checker.unary = _unary_lit

_cond = Checker.cond
Checker.cond = lambda self, t, line, what: _cond(self, fold_intlit(t), line, what)


def main():
    path = Path(sys.argv[1] if len(sys.argv) > 1 else 'editor/AlienPOC-QA.SC2Map/MapScript.galaxy')
    if not path.is_absolute():
        path = ROOT / path
    c = Checker()
    for name in HEADER_FILES:
        f = HEADERS / name
        if f.exists():
            c.parse_unit(tokenize(f.read_text(encoding='utf-8', errors='replace')), False)
    c.globals.update({})
    toks = tokenize(path.read_text(encoding='utf-8'))
    bodies = c.parse_unit(toks, True)
    c.load(toks, True)
    for name, start, params in bodies:
        try:
            c.check_body(name, start, params)
        except SyntaxError as e:
            c.problems.append((0, '%s: parse error %s' % (name, e)))
    lines = path.read_text(encoding='utf-8').split('\n')
    for line, msg in sorted(c.problems):
        print('%d: %s' % (line, msg))
        if 0 < line <= len(lines):
            print('    ' + lines[line - 1].strip()[:200])
    print('%d type problem(s)' % len(c.problems))
    sys.exit(1 if c.problems else 0)


if __name__ == '__main__':
    main()
