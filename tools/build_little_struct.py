#!/usr/bin/env python3
"""build_little_struct.py - ONCE: v2.1.0's NAVLITTLE (build/dm42/NAVLITTLE.txt, GTO) -> its STRUCT source
programs_struct/little/NAVLITTLE.txt (indented, no partner numbers), for the old DM42 with the C47 firmware.

  1. tools/c47struct.structure: GTO decisions and loops -> IF / DO / REPEAT
  2. by hand, the four jumps it leaves: N03 (the tables, else on into N04: an IF around the table part, ENDIF right
     after LBL "N04", as SUNG / SUNF of ALMA47), N23 / N24 (GTO IND -> XEQ IND, RTN), N36 (the key wait of the view:
     REPEAT ... DO PAUSE 50 KEY? WHILE ENDDO ... 0 X≠0? UNTIL, as WPLS of ALMA47)
  3. tools/build_struct.layout with the profile of the NAVLITTLE pages (ALMANAC, an hour later, two earlier, + end; three
     dates and places): the routines and programs ordered for the searches, labels 01, 02 ... in order
  4. NAV named ALMA47, INIT named NAVINIT
The pages are those of v2.1.0 pixel for pixel (tests/test_struct_src.py). tools/build_release_c47.py builds from the
source (numbers, the DM42 limits: 10 a series per program, 10 open at once).

  python3 tools/build_little_struct.py     (slow: the profile runs the pages in python/c47sim.py)
"""
import collections, os, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path[:0] = [HERE, os.path.join(ROOT, 'python'), os.path.join(ROOT, 'tests')]
import c47struct as C                                                         # noqa: E402
import build_struct as BS                                                     # noqa: E402
from decimal import Decimal as D                                              # noqa: E402

OUT = os.path.join(ROOT, 'programs_struct', 'little', 'NAVLITTLE.txt')
CASES = ((('DATE', '2026.1004'), ('UTC', '9.30'), ('LAT', '25.20'), ('LON', '55.12')),
         (('DATE', '2031.0315'), ('UTC', '3.30'), ('LAT', '-33.54'), ('LON', '18.25')),
         (('DATE', '2044.0521'), ('UTC', '18.43'), ('LAT', '41.85'), ('LON', '-77.11')))
KEYS = [51, 61, 61, 85]


def lines(p):
    return [l for l in open(p, encoding='utf-8').read().split('\n') if l.strip()]


def _replace(P, old, new):
    hits = [i for i in range(len(P) - len(old) + 1) if P[i:i + len(old)] == old]
    assert len(hits) == 1, (old, len(hits))
    return P[:hits[0]] + new + P[hits[0] + len(old):]


def convert(L):
    S = C.plain(C.structure(L, quiet=True))
    a, b = S.index('LBL "N03"'), S.index('LBL "N04"')
    assert S[a + 1:a + 3] == ['FC? 10', 'GTO "N04"']
    S = S[:a + 1] + ['FS? 10', 'IF'] + S[a + 3:b + 1] + ['ENDIF'] + S[b + 1:]
    for n in ('N23', 'N24'):
        S = _replace(S, ['LBL "%s"' % n, 'STO 12', 'GTO IND 12'], ['LBL "%s"' % n, 'STO 12', 'XEQ IND 12', 'RTN'])
    S = _replace(S, ['LBL "N36"', 'LBL 01', 'PAUSE 50', 'KEY? 00', 'GTO 01'],
                 ['LBL "N36"', 'REPEAT', 'DO', 'PAUSE 50', 'KEY? 00', 'WHILE', 'ENDDO'])
    S = _replace(S, ['RCL 00', '54', 'X=Y?', 'SNAP', 'GTO 01', 'END'],
                 ['RCL 00', '54', 'X=Y?', 'SNAP', '0', 'X≠0?', 'UNTIL', 'END'])
    return C.number(S)


def profile(L, I):
    """build_struct.profile for the NAVLITTLE pages: {kind: Counter(line of L)}."""
    import c47sim, test_navopt as T
    out = {k: collections.Counter() for k in ('label', 'named', 'rtn', 'struct', 'back')}
    for inp in CASES:
        t = tempfile.mkdtemp(); files = []
        for i, pr in enumerate(T.split(I + L)):
            f = os.path.join(t, 'p%d.txt' % i); open(f, 'w', encoding='utf-8').write('\n'.join(pr) + '\n'); files.append(f)
        c = c47sim.load(files); c.flags.add(82); c.grfnt = 21
        c.run('INIT', maxsteps=10 ** 7)
        for k, v in inp:
            c.reg[k] = D(v)
        a = c.lines.index(L[0]); calls = []

        def count(op, x, c=c, a=a, calls=calls):
            i = c.at
            if op in ('GTO', 'XEQ') and not c.lines[i][4:].startswith('IND'):
                arg = c.lines[i][4:]
                out['named' if arg.startswith('"') else 'label'][c.labels[arg.strip('"')] - a] += 1
            if op == 'XEQ':
                calls.append(i)
            if op in ('RTN', 'END') and calls:
                out['rtn'][calls.pop() - a] += 1
        c.count = count
        jump = c.struct

        def struct(op, arg, pc, jump=jump, a=a):
            r = jump(op, arg, pc)
            if r != pc:
                out['back' if op in ('ENDDO', 'UNTIL') else 'struct'][(pc - 1 if op in ('ENDDO', 'UNTIL') else r - 1) - a] += 1
            return r
        c.struct = struct
        c.flags.add(81); c.s = [D(0)] * 4; c.frames = []; c.pix = []; c.keys = list(KEYS)
        c.run('NAV', maxsteps=10 ** 8)
    return out


def main():
    L = lines(os.path.join(ROOT, 'build', 'dm42', 'NAVLITTLE.txt'))
    I = lines(os.path.join(ROOT, 'build', 'dm42', 'NAVINIT_LITTLE.txt'))
    S = convert(L)
    BS.profile = lambda Lx: profile(Lx, I)
    S = BS.layout(S)
    assert S[0] == 'LBL "NAV"' and S.count('"INIT"') == 1
    S = ['LBL "ALMA47"'] + ['"NAVINIT"' if l == '"INIT"' else l for l in S[1:]]
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(OUT, 'w', encoding='utf-8').write('\n'.join(C.indent(C.plain(S))) + '\n')
    print('  %s: %d steps' % (os.path.relpath(OUT, ROOT), len(S)))


if __name__ == '__main__':
    main()
