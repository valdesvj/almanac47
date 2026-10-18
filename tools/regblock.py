#!/usr/bin/env python3
"""regblock.py - the numbered registers of a C47 STRUCT listing renumbered into one block at the top (R(99-k)..R98),
so that NAV clears only that block (R-CLR) and the registers below it stay the user's.

tools/regalloc.py does the work (one web per value, the conflicts, DSatur): its control flow knows GTO, XEQ and the
skip of a test, not the STRUCT commands, so Flow here adds them (structured.c):
  a test right before IF / WHILE / UNTIL does not skip: IF, WHILE, UNTIL read its answer (the next line only)
  IF       the next line, or past its ELSE (the line after it) or its ENDIF
  ELSE     past its ENDIF                      ENDIF, DO, REPEAT   the next line
  WHILE    the next line, or past its ENDDO    ENDDO   the line after its DO
  UNTIL    the next line, or the line after its REPEAT
Local registers (R.nn), lettered registers and named variables are not touched; GRMOD nn is no register (rejig writes
GRMOD and then the number nn).

  python3 tools/regblock.py LISTING         how many registers the listing needs, and the block it would take
  python3 tools/regblock.py --write         programs_struct/ (NAV) renumbered into the block, its R-CLR set: only when
                                            a register below the block is in use (renumbering a numbered listing again
                                            finds other webs: other numbers for nothing); --force to do it anyway
"""
import os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE]
import regalloc as R                                                            # noqa: E402
import c47struct as C                                                           # noqa: E402

TOP = 98                                    # the block ends at R98 (R99 stays the user's, as in v2.2.0)


def partners(L):
    """{line: partner line} for the STRUCT steps: IF -> its ELSE or ENDIF, ELSE -> ENDIF, WHILE -> ENDDO,
    ENDDO -> DO, UNTIL -> REPEAT (one program at a time, nested as VALID nests them)."""
    out, stack = {}, []
    for i, l in enumerate(L):
        o = C.op(l)
        if o == 'END':
            assert not stack, 'regblock: a structure open at END (line %d)' % i
        if o in C.OPENERS:
            stack.append([o, i, None, []])                 # kind, opener, ELSE, WHILEs
        elif o == 'ELSE':
            stack[-1][2] = i
        elif o == 'WHILE':
            stack[-1][3].append(i)
        elif o in ('ENDIF', 'ENDDO', 'UNTIL'):
            kind, a, els, whiles = stack.pop()
            if o == 'ENDIF':
                out[a] = els if els is not None else i
                if els is not None:
                    out[els] = i
            elif o == 'ENDDO':
                out[i] = a
                for w in whiles:
                    out[w] = i
            else:
                out[i] = a
    return out


class Flow(R.Flow):
    def __init__(self, L, *a, **k):
        super().__init__(L, *a, **k)
        P = partners(L)
        n = len(L)
        for i, l in enumerate(L):
            o = C.op(l)
            if i + 1 < n and C.op(L[i + 1]) in ('IF', 'WHILE', 'UNTIL') and C.is_test(l):
                self.succ[i] = [i + 1]                     # the test's answer goes to the next step, no skip
            elif o == 'IF':
                self.succ[i] = [i + 1, P[i] + 1]
            elif o == 'ELSE':
                self.succ[i] = [P[i] + 1]
            elif o == 'WHILE':
                self.succ[i] = [i + 1, P[i] + 1]
            elif o == 'ENDDO':
                self.succ[i] = [P[i] + 1]
            elif o == 'UNTIL':
                self.succ[i] = [i + 1, P[i] + 1]
        self.preds = [[] for _ in L]
        for i in range(n):
            for j in self.succ[i]:
                self.preds[j].append(i)
        self.bodies = {e: self.body(e) for e in self.entries}
        self.owners = R.collections.defaultdict(list)
        for e, b in self.bodies.items():
            for i in b:
                self.owners[i].append(e)


R.Flow = Flow
# GRMOD nn is not a register: rejig writes GRMOD (the mode from X) and then the number nn (c47sim.py)
R.READ = re.compile(R.READ.pattern.replace('GRMOD|', ''))
R.ANY = re.compile(R.ANY.pattern.replace('|GRMOD|', '|'))
assert 'GRMOD' not in R.READ.pattern + R.ANY.pattern


# values that keep a number of their own: the DR of the run, which the routines you can call read (ALMA47_LABELS.txt):
# the value read by the first such step after the global label
PIN = {13: ('N32', 'RCL 13'), 14: ('N01', 'RCL 14')}


def block(L, keep=43, pin=PIN):
    """(listing with the numbered registers in R(TOP-k+1)..R(TOP), k). The values: one web each, as regalloc finds
    them; webs that never meet share a register. A register from Rkeep up that holds one value for the whole run (NAV's
    constants R43-R98) keeps its number (a value that never meets it may share it), the values of PIN theirs; the other values take the free numbers of the block from its bottom."""
    P = C.plain(L)
    A = R.analyse(P)
    assert not A['uninit'], 'regblock: reads with no write before them: %s' % [(i, P[i]) for i in A['uninit']]
    col = R.colour(A['graph'])
    k = max(col.values()) + 1 if col else 0
    base = TOP - k + 1
    webs = {}
    for w, c in col.items():
        webs.setdefault(c, set()).add(w)
    byreg = {}
    for w in col:
        byreg.setdefault(A['regs'][w], set()).add(w)
    num = {}
    for c, ws in webs.items():
        high = {A['regs'][w] for w in ws} & set(range(keep, TOP + 1))
        if len(high) == 1:
            r = high.pop()
            if byreg[r] <= ws and r not in num.values():
                num[c] = r                     # its webs keep their number (values that never meet it may share it)
    for c, ws in sorted(webs.items()):                 # a value already in the block keeps its number (stable)
        olds = {A['regs'][w] for w in ws}
        if c not in num and len(olds) == 1:
            r = next(iter(olds))
            if base <= r <= TOP and r not in num.values() and r not in pin:
                num[c] = r
    free = iter(n for n in range(base, TOP + 1) if n not in num.values())
    for c in sorted(webs):
        if c not in num:
            num[c] = next(free)
    for r, (lab, step) in pin.items():                # a permutation of the numbers: still no conflict
        i = P.index(step, P.index('LBL "%s"' % lab))
        c = col[A['webs'][i]]
        other = next(d for d, n in num.items() if n == r)
        num[c], num[other] = r, num[c]
    out = list(P)
    for i, w in A['webs'].items():
        m = R.ANY.match(P[i])
        out[i] = '%s %02d' % (m.group(1), num[col[w]])
    return C.number(out), k


def write():
    """programs_struct/ renumbered in place: NAV's registers into the block, R-CLR set to it; a REGS of
    build_struct_src.py that does not match is reported (it must be changed by hand)."""
    import build_struct_src as B
    L0 = B.build_unchecked()
    used = {int(m.group(2)) for l in L0 for m in [B.REG.match(l)] if m}
    if '--force' not in sys.argv and min(used) >= B.REGS[0]:
        # the analysis of an already numbered listing finds other webs: renumbered again it changes for nothing
        print('programs_struct/: NAV already in R%02d-R%02d, unchanged (--force to renumber anyway)' % (min(used), max(used)))
        return
    L, k = block(L0)
    P = C.plain(L)
    i = P.index('R-CLR')
    P[i - 1] = '%d.%02d' % (TOP - k + 1, k)
    for name, prog in zip(B.ORDER, C.split(P)):
        open(os.path.join(B.SRC, name + '.txt'), 'w', encoding='utf-8').write('\n'.join(C.indent(prog)) + '\n')
    print('programs_struct/: NAV in R%02d-R%02d, R-CLR %s%s' % (TOP - k + 1, TOP, P[i - 1],
          '' if (TOP - k + 1, k) == B.REGS else '  (set REGS = (%d, %d) in build_struct_src.py)' % (TOP - k + 1, k)))


if __name__ == '__main__':
    if sys.argv[1:2] == ['--write']:
        write()
        sys.exit()
    L = [l for l in open(sys.argv[1], encoding='utf-8').read().split('\n') if l.strip()]
    _, k = block(L)
    print('%d registers: R%02d-R%02d' % (k, TOP - k + 1, TOP))
