#!/usr/bin/env python3
"""c47struct.py - the C47 STRUCT commands in a listing: check and number them as VALID does, and turn GTO decisions and
loops into IF / ELSE / ENDIF, DO / WHILE / ENDDO and REPEAT / UNTIL.

The firmware (c43 src/c47/programming/structured.c, items 2920-2936, in every C47 build; the guide and the
specification in docs/appnotes/sources/AN0007_STRUCT):
  IF        the test just before it: true runs the next step, false goes past the nearest ELSE / ENDIF of its number
  ELSE      goes past the nearest ENDIF of its number          ENDIF, DO, REPEAT   nothing (the next step)
  WHILE     the test just before it: false goes past the nearest ENDDO of its number
  ENDDO     goes back to the step after its DO                 UNTIL   the test before it: false goes back after REPEAT
A STRUCT jump is the lookup a GTO to a local label makes (the structure steps are recorded after the labels). The
partner number (1-255, written "IF 01" by rejig with the STRUCT patch) is the program's own: IF, DO and REPEAT count
in three series in the order the openers appear, each closer takes its opener's number. The C47 checks only the LAST
program of a file as it loads, so the numbers are written into the file here.

VALID refuses: a closer of the wrong kind or with nothing open, a DO without WHILE, a structure open at END or across a
RTN + LBL (a new routine), no test right before IF / WHILE / UNTIL, more than 255 of a series. And here also a test
right before ELSE ENDIF DO ENDDO REPEAT: the firmware never skips those (structNoLegacySkip), so the test would not do
what it says (UNTIL, like IF and WHILE, reads the test's answer).

  check(P)        the faults of one program ([] when VALID passes)
  number(L)       every program of a listing numbered (the numbers it had are replaced); stops on a fault
  plain(L)        the steps without their numbers and indentation (a source written with STRUCT, indented)
  indent(L)       the listing indented two spaces per open structure (only to read it)
  structure(L)    GTO decisions and loops -> STRUCT, program by program (see the rules in _rewrite); numbered
"""
import re

OPENERS = {'IF': 'IF', 'DO': 'DO', 'REPEAT': 'REPEAT'}
CLOSERS = {'ELSE': 'IF', 'ENDIF': 'IF', 'WHILE': 'DO', 'ENDDO': 'DO', 'UNTIL': 'REPEAT'}
STRUCT = set(OPENERS) | set(CLOSERS)
NOSKIP = {'ELSE', 'ENDIF', 'DO', 'ENDDO', 'REPEAT'}          # no test right before them (UNTIL takes one)
MAX = 255
LIMIT = None                      # tests: stop after this many rewrites (to find a wrong one)

# the tests (structured.c structTest), as the listings write them
_TEST = re.compile(r'(X[<>=≠≤≥][Y0]\?|[xX𝑥][=≠<≤>≥]\? .+|F[SC]\?C? .+|F[SC]\?[SCF] .+|ISG .+|DSE .+|ISZ .+|DSZ .+|DSL .+|ISE .+'
                   r'|KEY\? .+|MATR\?|REAL\?|CPX\?|STRI\?|EVEN\?|ODD\?|FP\?|INT\?|BS\? .+|BC\? .+|PRIME\?)$')
_INV = {'X<Y?': 'X≥Y?', 'X≥Y?': 'X<Y?', 'X>Y?': 'X≤Y?', 'X≤Y?': 'X>Y?', 'X=Y?': 'X≠Y?', 'X≠Y?': 'X=Y?',
        'X<0?': 'X≥0?', 'X≥0?': 'X<0?', 'X>0?': 'X≤0?', 'X≤0?': 'X>0?', 'X=0?': 'X≠0?', 'X≠0?': 'X=0?'}
_INVC = {'=': '≠', '≠': '=', '<': '≥', '≥': '<', '>': '≤', '≤': '>'}


def op(l):
    return l.strip().partition(' ')[0]


def is_test(l):
    return bool(_TEST.fullmatch(l.strip()))


def invert(l):
    """The test that is true when l is false, or None (ISG, DSE, KEY?, MATR? ... have none)."""
    l = l.strip()
    if l in _INV:
        return _INV[l]
    m = re.fullmatch(r'([xX𝑥])([=≠<≤>≥])\? (.+)', l)
    if m:
        return '%s%s? %s' % (m.group(1), _INVC[m.group(2)], m.group(3))
    m = re.fullmatch(r'F([SC])\? (.+)', l)
    if m:
        return 'F%s? %s' % ('C' if m.group(1) == 'S' else 'S', m.group(2))
    return None


def plain(L):
    """The steps without indentation and without the structure numbers."""
    return [op(l) if op(l) in STRUCT else l.strip() for l in L if l.strip()]


def split(L):
    progs, cur = [], []
    for l in L:
        cur.append(l)
        if l.strip() == 'END':
            progs.append(cur)
            cur = []
    assert not [l for l in cur if l.strip()], 'c47struct: lines after the last END'
    return progs


def check(P):
    """The faults VALID (structWalkProgram) and the no-skip rule find in one program (plain or numbered steps)."""
    faults, stack, prev, prev_op = [], [], '', ''
    for i, l in enumerate(P):
        o = op(l)
        if o == 'LBL' and prev_op == 'RTN':                         # a new routine: what is open is crossed
            for s in stack:
                s[2] = True
        if o in ('IF', 'WHILE', 'UNTIL') and not is_test(prev):
            faults.append('%d %s: the step before it is not a test (%s)' % (i, o, prev))
        if o in NOSKIP and is_test(prev):
            faults.append('%d %s: a test right before it (%s) would not skip it' % (i, o, prev))
        tag = l.strip().partition(' ')[2]
        if o in OPENERS:
            stack.append([o, False, False, i, tag])                    # kind, WHILE seen, crossed, step, tag
        elif o in CLOSERS:
            if not stack or stack[-1][0] != CLOSERS[o]:
                faults.append('%d %s: closes %s' % (i, o, stack[-1][0] if stack else 'nothing'))
                break
            if tag.startswith('~') and tag != stack[-1][4]:            # structure() keeps its structures paired
                faults.append('%d %s %s: crosses %s %s' % (i, o, tag, stack[-1][0], stack[-1][4]))
                break
            if stack[-1][2]:
                faults.append('%d %s: its %s (step %d) is in another routine (RTN + LBL between)' % (i, o, stack[-1][0], stack[-1][3]))
            if o == 'WHILE':
                stack[-1][1] = True
            if o == 'ENDDO' and not stack[-1][1]:
                faults.append('%d ENDDO: its DO (step %d) has no WHILE' % (i, stack[-1][3]))
            if o in ('ENDIF', 'ENDDO', 'UNTIL'):
                stack.pop()
        if o == 'END' and stack:
            faults.append('%d END: %s of step %d still open' % (i, stack[-1][0], stack[-1][3]))
        prev = l.strip()
        if o != 'REM':
            prev_op = o
    n = {k: sum(1 for l in P if op(l) == k) for k in OPENERS}
    faults += ['%s: %d structures, at most %d a program' % (k, v, MAX) for k, v in n.items() if v > MAX]
    return faults


def number_program(P):
    """VALID's numbers: IF, DO, REPEAT in three series, in the order the openers appear; a closer takes its opener's."""
    f = check(P)
    assert not f, 'c47struct: %s: %s' % (P[0], '; '.join(f))
    nxt, stack, out = {k: 0 for k in OPENERS}, [], []
    for l in P:
        o = op(l)
        if o in OPENERS:
            nxt[o] += 1
            stack.append(nxt[o])
        if o in STRUCT:
            l = '%s %02d' % (o, stack[-1])
        if o in ('ENDIF', 'ENDDO', 'UNTIL'):
            stack.pop()
        out.append(l)
    return out


def number(L):
    return [l for P in split(plain(L)) for l in number_program(P)]


def indent(L):
    """Two spaces per open structure; ELSE and WHILE on their opener's column (the firmware's listing)."""
    out, d = [], 0
    for l in L:
        o = op(l)
        if o in ('ENDIF', 'ENDDO', 'UNTIL'):
            d -= 1
        out.append('  ' * (d - (o in ('ELSE', 'WHILE'))) + l.strip())
        if o in OPENERS:
            d += 1
    return out


# --- GTO -> STRUCT -------------------------------------------------------------------------------------------------

_ids = [0]


def _tag(seq):
    """The new structure steps of one rewrite with a tag of their own (~n), so that check() sees a structure that
    would cross another one (VALID would pair them the other way)."""
    _ids[0] += 1
    return [('%s ~%d' % (l, _ids[0]) if l in STRUCT else l) for l in seq]


def _num(l):
    m = re.fullmatch(r'(?:GTO|XEQ|LBL) (\d\d)', l)
    return m and m.group(1)


def _gone(P, k):
    """P[k] always leaves (RTN, GTO, END) and no test before it can skip it."""
    return (P[k] in ('RTN', 'END') or P[k].startswith('GTO ')) and not (k > 0 and is_test(P[k - 1]))


def _refs(P, n):
    return sum(1 for l in P if l in ('GTO ' + n, 'XEQ ' + n))


def _block(P, i):
    """The detached block that starts with the label P[i]: (i, j) with P[j] the step that leaves, or None. Detached:
    nothing runs into it (the step before always leaves) and it ends by leaving (RTN or GTO, not END)."""
    if i == 0 or not _gone(P, i - 1):
        return None
    j = i + 1
    while j < len(P) and P[j] != 'END':
        if _gone(P, j):
            return (i, j) if P[j] != 'END' else None
        j += 1
    return None


def _label(P, n):
    return P.index('LBL ' + n)


def _drop_label(P, n):
    """The label goes when nothing names it any more."""
    if _refs(P, n) == 0:
        del P[_label(P, n)]
    return P


def _while(P, n, x):
    """LBL n A T GTO x B GTO n LBL x -> DO A T' WHILE B ENDDO (LBL x stays when others name it)."""
    a, k, e = _label(P, n), P.index('GTO ' + n), P.index('GTO ' + x)
    Q = P[:a] + ['DO'] + P[a + 1:e - 1] + [invert(P[e - 1]), 'WHILE'] + P[e + 1:k] + ['ENDDO'] + P[k + 1:]
    return _drop_label(Q, x)


def _entered(P):
    """A structure that a GTO / XEQ from outside it enters in the middle (a label inside, named outside, or only
    reached by XEQ / GTO IND): the firmware runs it (a STRUCT step is only a jump), but it reads as one way in and is
    not made here."""
    stack, where = [], {}
    for i, l in enumerate(P):
        n = _num(l)
        if n and l.startswith(('GTO ', 'XEQ ')):
            where.setdefault(n, []).append(i)
    if [l for l in P if re.match(r'(XEQ|GTO) IND', l)]:
        for l in P:
            n = _num(l)
            if n and l.startswith('LBL ') and n not in where:
                where[n] = [-1]                                       # reached by IND: from outside
    for i, l in enumerate(P):
        o = op(l)
        if o in OPENERS:
            stack.append(i)
        elif o in ('ENDIF', 'ENDDO', 'UNTIL'):
            a = stack.pop()
            for j in range(a + 1, i):
                n = _num(P[j])
                if n and P[j].startswith('LBL ') and any(not a < r < i for r in where.get(n, [])):
                    return True
    return False


DUPMAX = 5                        # dup: a shared tail of at most this many steps is copied in place of a GTO to it


def _tailcode(P, x):
    """The steps of x's block after its label, up to and with the step that always leaves, when it is short enough to
    copy (no label, no structure step in it, not a jump back to itself): else None."""
    a = _label(P, x)
    j = a + 1
    while j < len(P) and P[j] != 'END' and not _gone(P, j):
        if P[j].startswith('LBL ') or op(P[j]) in STRUCT:
            return None
        j += 1
    if j >= len(P) or P[j] == 'END' or j - a > DUPMAX or P[j] == 'GTO ' + x:
        return None
    return P[a + 1:j + 1]


def _allof(P, x, ks):
    """The GTO x in ks (each after a test with an opposite) before one step U that always leaves:
    T1 GTO x A T2 GTO x B ... U  ->  T1' IF A T2' IF B ... U ENDIF ENDIF ..., then x's code: it was right after U,
    or its detached block moves there (ks are all that name x), else one GTO x."""
    for k in ks:
        if not (k > 1 and is_test(P[k - 1]) and invert(P[k - 1]) and not is_test(P[k - 2])):
            return None
    u = ks[-1] + 1
    while u < len(P) and not _gone(P, u):
        if P[u] == 'END':
            return None
        u += 1
    if u >= len(P) or P[u] == 'END':
        return None
    lx = _label(P, x)
    if ks[0] <= lx <= u:
        return None
    every = _refs(P, x) == len(ks)
    Q = list(P)
    for k in ks:
        Q[k - 1:k + 1] = [invert(P[k - 1]), 'IF']
    tail = ['ENDIF'] * len(ks)
    if lx == u + 1 and every:
        return Q[:u + 1] + tail + Q[u + 2:]
    blk = _block(P, lx)
    if every and blk and not (blk[0] <= ks[0] <= blk[1]):
        body = Q[blk[0] + 1:blk[1] + 1]
        if blk[0] > u:
            return Q[:u + 1] + tail + body + Q[u + 1:blk[0]] + Q[blk[1] + 1:]
        return Q[:blk[0]] + Q[blk[1] + 1:u + 1] + tail + body + Q[u + 1:]
    if len(ks) < 2 and not _tailcode(P, x):
        return None                                     # one GTO for one GTO: only when that one can be copied (dup)
    return Q[:u + 1] + tail + ['GTO ' + x] + Q[u + 1:]


def _groups(P, x):
    """The GTO x after a test, in runs that no step that always leaves divides (one all-of each)."""
    ks = [k for k, l in enumerate(P) if l == 'GTO ' + x and k > 0 and is_test(P[k - 1])]
    out = []
    while ks:
        u = ks[0] + 1
        while u < len(P) and P[u] != 'END' and not _gone(P, u):
            u += 1
        g = [k for k in ks if k < u]
        out.append(g)
        ks = ks[len(g):]
    return out


def _opener(P, k):
    """The index of the innermost structure open at P[k] (None at depth 0)."""
    stack = []
    for i in range(k):
        o = op(P[i])
        if o in OPENERS:
            stack.append(i)
        elif o in ('ENDIF', 'ENDDO', 'UNTIL'):
            stack.pop()
    return stack[-1] if stack else None


def _closer(P, a):
    """The index of the step that closes the structure opened at P[a]."""
    d = 0
    for i in range(a, len(P)):
        o = op(P[i])
        if o in OPENERS:
            d += 1
        elif o in ('ENDIF', 'ENDDO', 'UNTIL'):
            d -= 1
            if d == 0:
                return i
    return None


def _candidates(P):
    """Every rewrite that applies, as (rule, new program); the caller keeps the first one VALID accepts."""
    for k, l in enumerate(P):
        # steps no jump reaches: after a step that always leaves, up to the next label or structure step
        if _gone(P, k) and k + 1 < len(P) and P[k + 1] != 'END' and not P[k + 1].startswith('LBL ') \
                and op(P[k + 1]) not in STRUCT:
            j = k + 1
            while P[j] != 'END' and not P[j].startswith('LBL ') and op(P[j]) not in STRUCT:
                j += 1
            Q = P[:k + 1] + P[j:]
            for x in {_num(m) for m in P[k + 1:j] if _num(m) and not m.startswith('LBL ')}:
                Q = _drop_label(Q, x)                           # a label only the dead steps named goes too
            yield 'dead', Q
    for x in sorted({_num(l) for l in P if re.fullmatch(r'GTO \d\d', l)}):
        for g in _groups(P, x):
            Q = _allof(P, x, g)
            if Q:
                yield 'all-of', Q
    for k, l in enumerate(P):
        n = _num(l)
        if n and l.startswith('GTO ') and not (k > 0 and is_test(P[k - 1])):
            code = _tailcode(P, n)
            if code:
                # dup: GTO x to a short shared tail -> the tail's steps
                yield 'dup', _drop_label(P[:k] + code + P[k + 1:], n)
        if n and l.startswith('GTO ') and k > 1 and is_test(P[k - 1]) and invert(P[k - 1]) and not is_test(P[k - 2]) \
                and _refs(P, n) == 1:
            o = _opener(P, k)
            if o is not None and op(P[o]) == 'DO':
                e = _closer(P, o)
                tag = P[o].partition(' ')[2]
                if P[e + 1:e + 2] == ['LBL ' + n]:
                    # break: T GTO x inside DO ... ENDDO LBL x -> T' WHILE (a DO may hold several WHILE). Only when
                    # x is right after the ENDDO: the loop's own end goes there too (no block may be moved in between)
                    yield 'break', _drop_label(P[:k - 1] + [invert(P[k - 1]), ('WHILE ' + tag).strip()] + P[k + 1:], n)
        if n and l.startswith('GTO ') and k > 0 and is_test(P[k - 1]) and _refs(P, n) == 1:
            a = _label(P, n)
            g = k + 1
            while g < len(P) and P[g] != 'END' and not _gone(P, g):
                g += 1
            blk = _block(P, a) if a > g else None
            if blk and P[g].startswith('GTO ') and a != g + 1 and _num(P[g]) and \
                    any(P[i] == 'LBL ' + _num(P[g]) for i in range(blk[0], blk[1] + 1)):
                # pull: T GTO a B GTO b ... LBL a C LBL b D: a's block right after GTO b (then if-else)
                yield 'pull', P[:g + 1] + P[blk[0]:blk[1] + 1] + P[g + 1:blk[0]] + P[blk[1] + 1:]
    for k, l in enumerate(P):
        n = _num(l)
        if not n or not l.startswith('GTO '):
            continue
        a = _label(P, n)
        cond = k > 0 and is_test(P[k - 1])
        T = P[k - 1] if cond else None
        chained = cond and k > 1 and is_test(P[k - 2])               # a test before the test: it can skip the test
        if chained:
            continue
        if a + 1 < len(P) and P[a + 1] == 'RTN':
            # GTO x to LBL x RTN -> RTN
            yield 'rtn', _drop_label(P[:k] + ['RTN'] + P[k + 1:], n)
        if a + 1 < len(P) and re.fullmatch(r'GTO (\d\d|".+")', P[a + 1]) and P[a + 1] != l:
            # GTO x to LBL x GTO y -> GTO y
            yield 'thread', _drop_label(P[:k] + [P[a + 1]] + P[k + 1:], n)
        if not cond and a > k:
            blk = _block(P, a)
            # R5 fall-through: GTO x to a block only it names -> the block in its place
            if blk and _refs(P, n) == 1 and not (blk[0] <= k <= blk[1]):
                body = P[blk[0] + 1:blk[1] + 1]
                Q = P[:blk[0]] + P[blk[1] + 1:]
                k2 = k if k < blk[0] else k - len(body) - 1
                yield 'fall-through', Q[:k2] + body + Q[k2 + 1:]
            # GTO x right before LBL x
            if a == k + 1:
                yield 'next', _drop_label(P[:k] + P[k + 1:], n)
        if cond and a < k and _refs(P, n) == 1:
            # R1 the loop LBL a ... T GTO a -> REPEAT ... T' UNTIL, or DO ... T WHILE ENDDO when T has no opposite
            body = P[a + 1:k - 1]
            inv = invert(T)
            new = ['REPEAT'] + body + [inv, 'UNTIL'] if inv else ['DO'] + body + [T, 'WHILE', 'ENDDO']
            yield 'loop', P[:a] + new + P[k + 1:]
        if not cond and a < k and _refs(P, n) == 1 and not (k > 0 and is_test(P[k - 1])):
            # R4 the loop LBL a A T GTO x B GTO a, with LBL x right after it -> DO A T' WHILE B ENDDO
            for e in range(a + 1, k - 1):
                x = _num(P[e])
                if not (x and P[e].startswith('GTO ') and is_test(P[e - 1]) and invert(P[e - 1])):
                    continue
                if e > a + 1 and is_test(P[e - 2]):
                    continue
                xl = _label(P, x)
                if xl == k + 1:
                    yield 'while', _while(P, n, x)
                else:
                    blk = _block(P, xl)
                    if blk and _refs(P, x) == 1 and not (blk[0] <= k <= blk[1]) and not (blk[0] <= a <= blk[1]):
                        body = P[blk[0]:blk[1] + 1]          # the exit block moved right after the loop
                        Q = P[:k + 1] + body + P[k + 1:]
                        s = len(body) if blk[0] > k else 0
                        yield 'while', _while(Q[:blk[0] + s] + Q[blk[1] + 1 + s:], n, x)
        if cond and a > k:
            m = a
            # R3 if-else: T GTO a B GTO b LBL a C LBL b -> T' IF B ELSE C ENDIF (LBL b stays when others name it)
            if _refs(P, n) == 1 and m >= 2 and _num(P[m - 1]) and P[m - 1].startswith('GTO ') and not is_test(P[m - 2]):
                b = _num(P[m - 1])
                bl = _label(P, b)
                if bl > m:
                    B, C = P[k + 1:m - 1], P[m + 1:bl]
                    inv = invert(T)
                    new = [inv, 'IF'] + B + ['ELSE'] + C + ['ENDIF'] if inv else [T, 'IF'] + C + ['ELSE'] + B + ['ENDIF']
                    yield 'if-else', _drop_label(P[:k - 1] + new + P[bl:], b)
            # R2 skip: T GTO a A LBL a -> T' IF A ENDIF, or T IF ELSE A ENDIF
            if _refs(P, n) == 1:
                A = P[k + 1:a]
                inv = invert(T)
                new = [inv, 'IF'] + A + ['ENDIF'] if inv else [T, 'IF', 'ELSE'] + A + ['ENDIF']
                if A:
                    yield 'if', P[:k - 1] + new + P[a + 1:]
            # R6 T GTO x to a block only it names -> T IF block ENDIF
            blk = _block(P, a)
            if blk and _refs(P, n) == 1 and not (blk[0] <= k <= blk[1]):
                body = P[blk[0] + 1:blk[1] + 1]
                Q = P[:k] + ['IF'] + body + ['ENDIF'] + P[k + 1:]
                Q = Q[:blk[0] + len(body) + 1] + Q[blk[1] + len(body) + 2:] if blk[0] > k else Q[:blk[0]] + Q[blk[1] + 1:]
                yield 'if block', Q


ORDER = ('dead', 'next', 'rtn', 'thread', 'dup', 'fall-through', 'loop', 'while', 'break', 'if-else', 'all-of', 'if',
         'pull', 'if block')


def _rewrite(P, stats):
    """The rules, until none applies (each result must pass check()):
      fall-through  GTO x (always taken) to a detached block only it names: the block in its place
      next          GTO x right before LBL x: gone
      loop          LBL a ... T GTO a (only GTO a names a): REPEAT ... T' UNTIL with the opposite test, else
                    DO ... T WHILE ENDDO
      while         LBL a A T GTO x B GTO a LBL x: DO A T' WHILE B ENDDO; when x is a detached block only that GTO
                    names, the block moves right after the loop first
      if-else       T GTO a B GTO b LBL a C LBL b: T' IF B ELSE C ENDIF, else T IF C ELSE B ENDIF
      if            T GTO a A LBL a: T' IF A ENDIF, else T IF ELSE A ENDIF
      if block      T GTO x to a detached block only it names: T IF block ENDIF
      all-of        T1 GTO x A T2 GTO x ... U: T1' IF A T2' IF ... U ENDIF ENDIF, then x's code (right after U, or
                    its block moved there) or one GTO x
      dead          the steps after one that always leaves, up to a label or a structure step: gone
      thread        GTO x to LBL x GTO y: GTO y
      dup           GTO x (always taken) to a shared tail of at most DUPMAX steps: the tail's steps
      break         T GTO x in a DO ... ENDDO with x right after it: T' WHILE;
                    the firmware takes several WHILE in one DO (fnWhile: the nearest ENDDO of its number)
      pull          T GTO a B GTO b with b inside a's detached block: the block right after GTO b (for if-else)
    A test right before the test is left alone (it can skip the test). A label goes when nothing names it any more."""
    tried, stack, T = set(), [], []
    for l in P:                                   # the structures already there: tagged as VALID pairs them
        if op(l) in OPENERS:
            _ids[0] += 1
            stack.append(_ids[0])
        if op(l) in STRUCT:
            l = '%s ~%d' % (op(l), stack[-1])
            if op(l) in ('ENDIF', 'ENDDO', 'UNTIL'):
                stack.pop()
        T.append(l)
    P = T
    while True:
        for rule, Q in sorted(_candidates(P), key=lambda c: ORDER.index(c[0])):
            Q = _tag(Q)
            key = tuple(op(l) if op(l) in STRUCT else l for l in Q)
            if key in tried:
                continue
            tried.add(key)
            if not check(Q) and not _entered(Q):
                if LIMIT is not None and sum(stats.values()) >= LIMIT:
                    return P
                stats[rule] = stats.get(rule, 0) + 1
                P = Q
                break
        else:
            return P


def structure(L, quiet=False):
    """Every program of L with its GTO decisions and loops as STRUCT, numbered. GTO "name" (a tail call to another
    program) and GTO nn followed by a RTN that never runs (a tail call to a local routine) stay."""
    out, stats = [], {}
    for P in split(plain(L)):
        out += number_program(_rewrite(P, stats))
    return (out, stats) if not quiet else out


def gotos(L):
    """GTO nn left: (decisions and loops, tail calls). A tail call is a GTO no test can skip, to a routine: a label
    right after a step that always leaves, whose code ends with RTN (XEQ x + RTN made shorter, build_struct step 1)."""
    dec = tail = 0
    for P in split(plain(L)):
        for k, l in enumerate(P):
            n = _num(l)
            if not (n and l.startswith('GTO ')):
                continue
            a = _label(P, n)
            j = a + 1
            while not _gone(P, j):
                j += 1
            if not is_test(P[k - 1]) and _gone(P, a - 1) and (P[j] in ('RTN', 'END') or P[j].startswith('GTO "')):
                tail += 1
            else:
                dec += 1
    return dec, tail


# --- fewer calls -------------------------------------------------------------------------------------------------

def _routine(P, n):
    """(a, b, body) of the routine LBL n ... RTN when it is plain: its body (between them) has no label, no jump, no
    return, no structure, no local register, and does not end with a test; else None."""
    a = _label(P, n)
    b = a + 1
    while b < len(P) and P[b] not in ('RTN', 'END'):
        l = P[b]
        if l.startswith(('LBL ', 'GTO ', 'LocR', 'PopLR')) or op(l) in STRUCT or 'R.' in l:
            return None
        b += 1
    if b >= len(P) or P[b] != 'RTN' or (b > a + 1 and is_test(P[b - 1])):
        return None
    return a, b, P[a + 1:b]


def inline(L, hot=None, short=2, small=6, often=10, single=40):
    """XEQ n replaced by the steps of n (a plain routine of the same program, _routine) where the call is not after a
    test (one step after a test is fine): when n has that one caller (up to `single` steps), when n has at most
    `short` steps, or at most `small` steps and the call runs at least `often` times (hot: {line of L: times run},
    the PROFILE). A routine no XEQ names any more goes (label, steps and RTN) when no step runs into it.
    Returns (L, calls inlined, routines removed)."""
    out, done, gone, base = [], 0, 0, 0
    for P in split(plain(L)):
        runs = {i: (hot or {}).get(base + i, 0) for i in range(len(P))}
        base += len(P)
        changed = True
        while changed:
            changed = False
            for k, l in enumerate(P):
                n = _num(l)
                if not (n and l.startswith('XEQ ')) or 'LBL ' + n not in P:
                    continue
                r = _routine(P, n)
                if not r:
                    continue
                a, b, body = r
                if a <= k <= b or (k > 0 and is_test(P[k - 1]) and len(body) != 1) or not body:
                    continue
                callers = sum(1 for x in P if x == 'XEQ ' + n)
                gotos = sum(1 for x in P if x == 'GTO ' + n)
                if not ((callers == 1 and gotos == 0 and len(body) <= single) or len(body) <= short
                        or (len(body) <= small and runs.get(k, 0) >= often)):
                    continue
                P = P[:k] + body + P[k + 1:]
                runs = {(i if i < k else i + len(body) - 1): v for i, v in runs.items() if i != k}
                done += 1
                if _refs(P, n) == 0:
                    a = _label(P, n)
                    if a > 0 and _gone(P, a - 1):
                        b = a + 1
                        while P[b] != 'RTN':
                            b += 1
                        P = P[:a] + P[b + 1:]
                        runs = {(i if i < a else i - (b + 1 - a)): v for i, v in runs.items() if not a <= i <= b}
                        gone += 1
                changed = True
                break
        out += P
    return number(out), done, gone

