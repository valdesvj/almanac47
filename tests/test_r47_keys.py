#!/usr/bin/env python3
"""test_r47_keys.py - the R47 ALMA47 of v2.3.0 (tools/build_r47_v230.py, build/v2.3.0/r47/): with the R47 keys (up 61,
down 71) every screen pixel for pixel the C47 ALMA47 with the C47 keys (up 51, down 61), on the menu and on each view
1-8 (the arrows, +/-, + and 0), the stack back; on the R47 build the C47 up arrow's place (51: XEQ on the R47) moves
no hour; the listing differs from the C47 one only in the 12 key steps; the p47u is the listing.
  python3 tools/build_release_v230.py && python3 tools/build_r47_v230.py && python3 tests/test_r47_keys.py
  REL=2.4.0 python3 tests/test_r47_keys.py: v2.4.0's (tools/build_release_v240.py builds its r47/ too)"""
import os, sys
from decimal import Decimal as D
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [os.path.join(ROOT, 'tests'), os.path.join(ROOT, 'tools'), os.path.join(ROOT, 'python')]
import test_v2 as V                                                           # noqa: E402
import build_r47_v230 as R                                                    # noqa: E402

REL = os.path.join(ROOT, 'build', 'v' + os.environ.get('REL', '2.3.0'))
C47K = dict(V.K)
R47K = dict(V.K, up=61, down=71)
bad = 0


def ok(cond, what):
    global bad
    bad += not cond
    print('  %s  %s' % ('ok  ' if cond else 'FAIL', what))


def nav(L):
    """the release listing (LBL "ALMA47") as the simulator's NAV"""
    return ['LBL "NAV"'] + L[1:]


def run(L, keys, init, inp, tz=None):
    c = V.T.load(L, init)
    for k, v in inp:
        c.reg[k] = D(v)
    if tz is not None:
        c.reg['TZ'] = D(tz)
    c.flags.add(81); c.s = [D(11), D(12), D(13), D(14)]; c.lastx = D(99); c.frames = []; c.pix = []; c.keys = list(keys)
    c.run('NAV', maxsteps=10 ** 8)
    return [frozenset((x, 239 - y) for y, x in f if 0 <= y < 240 and 0 <= x < 400) for f in c.frames], c


def main():
    print('== the R47 ALMA47 (%s/r47/)' % os.path.relpath(REL, ROOT))
    C = R.lines(os.path.join(REL, 'c47', 'ALMA47.txt'))
    Rl = R.lines(os.path.join(REL, 'r47', 'ALMA47.txt'))
    diff = [(a, b) for a, b in zip(C, Rl) if a != b]
    ok(len(C) == len(Rl) and sorted(set(diff)) == [('56', '66'), ('61', '71'), ('RCL 67', '61')] and len(diff) == 12
       and Rl == R.r47(C), 'the C47 listing with the 12 key steps changed (8 x 56 -> 66, 2 x RCL 67 -> 61, 2 x 61 -> 71)')
    P = [R.step(l) for l in R.lines(os.path.join(REL, 'r47', 'p47u', 'ALMA47.p47u')) if l.strip() and not l.startswith('@')]
    ok(P == Rl, 'p47u/ALMA47.p47u: the same steps')
    Cn, Rn = nav(C), nav(Rl)
    cases = [('FULL', ('2026.1004', '9.30', '25.20', '55.12'), None), ('FAST', ('2027.0315', '3.30', '-33.54', '18.25'), 3)]
    for init, (dt, ut, la, lo), tz in cases:
        inp = (('DATE', dt), ('UTC', ut), ('LAT', la), ('LON', lo))
        seqs = [(['up', 'down', 'down', 43, 'up', 1, '+', 0], 'menu: arrows, +/-, ALMANAC')]
        seqs += [([p, 'up', 'down', 'down', 43, '+', 0], 'view %d: arrows, +/-' % p) for p in range(1, 9)]
        for seq, what in seqs:
            ck = [C47K[k] if k in C47K else k for k in seq]
            rk = [R47K[k] if k in R47K else k for k in seq]
            a, ca = run(Cn, ck, init, inp, tz)
            b, cb = run(Rn, rk, init, inp, tz)
            ok(a == b and len(a) > 1 and cb.s == ca.s and cb.lastx == ca.lastx,
               '%s %s %s: %s, %d screens pixel for pixel the C47 build' % (init, dt, la, what, len(b)))
        a, _ = run(Rn, [C47K[1], C47K['+'], C47K[0]], init, inp, tz)
        b, _ = run(Rn, [51, C47K[1], C47K['+'], C47K[0]], init, inp, tz)
        ok(a[-2] == b[-2], '%s %s: R47 build, key 51 (XEQ) then ALMANAC: the same hour' % (init, dt))
    print('%d failed' % bad if bad else 'ALL OK')
    return bad


if __name__ == '__main__':
    sys.exit(1 if main() else 0)
