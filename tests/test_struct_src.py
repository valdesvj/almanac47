#!/usr/bin/env python3
"""test_struct_src.py - the STRUCT source programs_struct/ (tools/build_struct_src.py) against 18_hourglass.

  1. the source: one program a file, every program VALID, no GTO of any kind, no partner numbers written in it,
     indented two spaces per open structure; build/dev/struct_src/NAVFULL.txt is the build of it
  2. every page (FULL, FAST, three dates and places, hour arrows) and the menu's keys pixel for pixel
     build/dev/struct/18_hourglass, the stack clear at the end; how many structures the pages entered
  3. 16 random dates (2000-2049), times and places (65 S - 65 N), FULL and FAST, pages 1-5 with an hour arrow

  python3 tests/test_struct_src.py [n]      (n random cases, default 16)
"""
import os, random, re, sys
from decimal import Decimal as D
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [os.path.join(ROOT, 'python'), os.path.join(ROOT, 'tools'), os.path.join(ROOT, 'tests')]
import c47struct as S                                                # noqa: E402
import build_struct_src as B                                         # noqa: E402

BAD = []
REF = os.path.join(ROOT, 'build', 'dev', 'struct', '18_hourglass', 'NAVFULL.txt')


def ok(cond, what):
    print('  %s  %s' % ('ok  ' if cond else 'FAIL', what))
    if not cond:
        BAD.append(what)


def lines(f):
    return [l for l in open(f, encoding='utf-8').read().split('\n') if l.strip()]


def source():
    print('== programs_struct/')
    L = B.build()
    built = lines(os.path.join(B.OUT, 'NAVFULL.txt'))
    ok(L == built, 'build/dev/struct_src/NAVFULL.txt is the build of programs_struct/ (tools/build_struct_src.py)')
    ok(S.number(L) == L, 'numbered as VALID numbers them')
    gto = numbered = indent = 0
    for name in B.ORDER:
        src = open(os.path.join(B.SRC, name + '.txt'), encoding='utf-8').read().split('\n')
        steps = [l for l in src if l.strip()]
        gto += sum(1 for l in steps if l.strip().startswith('GTO'))
        numbered += sum(1 for l in steps if S.op(l) in S.STRUCT and l.strip() != S.op(l))
        code = [l for l in steps if not l.strip().startswith('REM ')]
        want = S.indent([l.strip() for l in code])
        indent += sum(1 for a, b in zip(code, want) if a != b)
    ok(gto == 0, 'no GTO of any kind in the source')
    ok(numbered == 0, 'no partner numbers in the source (the build writes them)')
    ok(indent == 0, 'two spaces per open structure (ELSE and WHILE on their opener\'s column): %d lines off' % indent)
    st = B.stats(L)
    print('  %d steps (18_hourglass %d), %d labels, IF %d, DO %d, REPEAT %d, GTO %d'
          % (st['steps'], len(lines(REF)), st['labels'], st['IF'], st['DO'], st['REPEAT'], st['GTO']))
    return L


def pages(B_):
    import test_v2 as V
    print('== build/dev/struct_src against 18_hourglass')
    A = V.lines(REF)
    ran = set()
    cases = [('FULL', ('2026.1004', '9.30', '25.20', '55.12')), ('FAST', ('2027.0315', '3.30', '-33.54', '18.25')),
             ('FULL', ('2026.1020', '22.10', '60.10', '-5.00'))]
    for init, (dt, ut, la, lo) in cases:
        inp = (('DATE', dt), ('UTC', ut), ('LAT', la), ('LON', lo))
        for p, name in ((1, 'ALMANAC'), (2, 'SPLIT'), (3, 'SKY'), (4, 'ANIM'), (5, 'ALLSKY'), (6, 'INFO')):
            keys = [V.K[p], V.K['up'], V.K['down'], V.K['down'], V.K['+'], V.K[0]] if p in (1, 3, 5) else [V.K[p], V.K['+'], V.K[0]]
            a = V.session(A, keys, init, False, inp, marks=False)
            c = V.T.load(B_, init)
            for k, v in inp:
                c.reg[k] = D(v)
            at = c.lines.index(B_[0])
            c.count = lambda op, x: ran.add(c.at - at)
            c.flags.add(81); c.s = [D(0)] * 4; c.frames = []; c.pix = []; c.keys = list(keys)
            c.run('NAV', maxsteps=10 ** 8)
            frames = [frozenset((x, 239 - y) for y, x in f if 0 <= y < 240 and 0 <= x < 400) for f in c.frames]
            ok(frames == a[0] and all(x == 0 for x in c.s), '%s %s %s %s %s: %d screens pixel for pixel, stack clear'
               % (init, dt, la, lo, name, len(frames)))
    K = V.K
    for keys, what in (([K['up'], K['down'], K['down'], K[1], K['+'], K[0]], 'menu: arrows, ALMANAC'),
                       ([54, 52, 53, 85, K[3], K['+'], K[0]], 'menu: 9 SNAP, 7, 8, +, SKY'),
                       ([K[6], K['up'], K['+'], K[0]], 'INFO, arrow'),
                       ([K[2], K['down'], K[4], K[4], K['up'], K['+'], K[0]], 'SPLIT, a digit back to the menu, ANIM'),
                       ([11, 21, 31, 41, 71, 81, K[1], K['+'], K[0]], 'menu: keys that are no view')):
        a = V.session(A, keys, 'FULL', False, marks=False)
        b = V.session(B_, keys, 'FULL', False, marks=False)
        ok(a[0] == b[0] and b[2], '%s: %d screens pixel for pixel, stack clear' % (what, len(b[0])))
    st = [i for i, l in enumerate(B_) if S.op(l) in S.OPENERS]
    print('  structures entered on these pages: %d of %d' % (len([i for i in st if i in ran]), len(st)))


def places(B_, n):
    import test_v2 as V
    print('== build/dev/struct_src against 18_hourglass at %d random dates and places' % n)
    A = V.lines(REF)
    rnd = random.Random(7)
    for t in range(n):
        inp = (('DATE', '%d.%02d%02d' % (rnd.randint(2000, 2049), rnd.randint(1, 12), rnd.randint(1, 28))),
               ('UTC', '%d.%02d' % (rnd.randint(0, 23), rnd.randint(0, 59))), ('LAT', '%.2f' % rnd.uniform(-65, 65)),
               ('LON', '%.2f' % rnd.uniform(-179, 179)))
        init = 'FAST' if t % 2 else 'FULL'
        same = []
        for p in (1, 2, 3, 4, 5):
            keys = [V.K[p], V.K['up'], V.K['+'], V.K[0]]
            a = V.session(A, keys, init, False, inp, marks=False)
            b = V.session(B_, keys, init, False, inp, marks=False)
            same.append(a[0] == b[0] and b[2])
        ok(all(same), '%s %s %s %s %s: pages 1-5 pixel for pixel' % ((init,) + tuple(v for _, v in inp)))


def main():
    n = int(sys.argv[1]) if sys.argv[1:] else 16
    L = source()
    pages(L)
    places(L, n)
    print('\n%s' % ('ALL PASSED' if not BAD else '%d FAILED: %s' % (len(BAD), '; '.join(BAD))))
    return 1 if BAD else 0


if __name__ == '__main__':
    sys.exit(main())
