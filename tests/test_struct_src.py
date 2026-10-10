#!/usr/bin/env python3
"""test_struct_src.py - the STRUCT source programs_struct/ (tools/build_struct_src.py) against 18_hourglass.

  1. the source: one program a file, code only (no REM), every program VALID, no GTO of any kind, no partner numbers
     written in it, indented two spaces per open structure; build/dev/struct_src/NAVFULL.txt is the build of it and
     NAVFULL_COMMENTED.txt the same steps with REM lines
  2. every page (FULL, FAST, three dates and places, hour arrows) and the menu's keys pixel for pixel
     build/dev/struct/18_hourglass, the stack clear at the end; how many structures the pages entered
  3. build/forum/NAV.p47u and NAVINIT.p47u (tools/build_forum.py): the header, the main label, the same steps
  4. MOON47 (programs_struct/MOON47.txt, one program): the build, the page pixel for pixel build/dev/moon/1_labels
     and python/moon47.py at 16 dates and time zones, north and south
  5. 16 random dates (2000-2049), times and places (65 S - 65 N), FULL and FAST, pages 1-5 with an hour arrow

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
    com = lines(os.path.join(B.OUT, 'NAVFULL_COMMENTED.txt'))
    ok(com == [l for l in B.commented(L) if l.strip()], 'build/dev/struct_src/NAVFULL_COMMENTED.txt is the commented build')
    ok([l.strip() for l in com if not l.strip().startswith('REM ')] == L,
       'NAVFULL_COMMENTED.txt without its REM lines is NAVFULL.txt step for step')
    gto = numbered = indent = rem = 0
    for name in B.ORDER:
        src = open(os.path.join(B.SRC, name + '.txt'), encoding='utf-8').read().split('\n')
        steps = [l for l in src if l.strip()]
        gto += sum(1 for l in steps if l.strip().startswith('GTO'))
        rem += sum(1 for l in steps if l.strip().startswith('REM '))
        numbered += sum(1 for l in steps if S.op(l) in S.STRUCT and l.strip() != S.op(l))
        code = [l for l in steps if not l.strip().startswith('REM ')]
        want = S.indent([l.strip() for l in code])
        indent += sum(1 for a, b in zip(code, want) if a != b)
    ok(gto == 0, 'no GTO of any kind in the source')
    ok(rem == 0, 'no REM in the source (code only; the comments are in NAVFULL_COMMENTED.txt)')
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


def forum(L):
    """build/forum/*.p47u (tools/build_forum.py): the release's PROGRAMS format; the steps those of NAVFULL.txt and
    NAVINIT_FAST.txt (its label INIT named NAVINIT)."""
    import build_forum as F
    print('== build/forum/ (the PROGRAMS folder of the C47 release)')
    for fname, want in (('NAV.p47u', L), ('NAVINIT.p47u', ['LBL "NAVINIT"'] + lines(os.path.join(ROOT, 'build', 'NAVINIT_FAST.txt'))[1:]),
                        ('MOON47.p47u', B.build_moon())):
        p = os.path.join(F.OUT, fname)
        txt = open(p, encoding='utf-8').read().split('\n')
        head = [l for l in txt if l.startswith('@')]
        steps = [l.strip() for l in txt if l.strip() and not l.startswith('@') and not l.strip().startswith('#')]
        ok(any(re.match(r'@ Index:\s+\S', l) for l in head) and txt[0].startswith('@ Index:'), '%s: @ Index: first' % fname)
        glob = [l for l in steps if l.startswith('LBL "')]
        ok(glob[0] == 'LBL "%s"' % fname[:-5] and (fname != 'MOON47.p47u' or glob == ['LBL "MOON47"']),
           '%s: the main label is the file name%s' % (fname, ' (and the only global one)' if fname == 'MOON47.p47u' else ''))
        ok(steps == want, '%s: the steps of the build (%d)' % (fname, len(steps)))
        ok(not any(l.startswith('GTO') for l in steps), '%s: no GTO' % fname)


def moon(n):
    """MOON47 (programs_struct/MOON47.txt): one program, LBL "MOON47" the only global label, no GTO, no REM; the build
    and its commented listing; the page pixel for pixel build/dev/moon/1_labels (the three programs, checked on the
    firmware) and the Python reference (python/moon47.py), X = Y = 0 at the end."""
    import tempfile
    import c47sim
    import moon47 as M47
    sys.path.insert(0, os.path.join(ROOT, 'python', 'native'))
    import c47screen21 as V21
    print('== MOON47 (programs_struct/MOON47.txt)')
    M = B.build_moon()
    ok(M == lines(os.path.join(B.OUT, 'MOON47.txt')), 'build/dev/struct_src/MOON47.txt is the build of programs_struct/MOON47.txt')
    com = lines(os.path.join(B.OUT, 'MOON47_COMMENTED.txt'))
    ok([l.strip() for l in com if not l.strip().startswith('REM ')] == M, 'MOON47_COMMENTED.txt without its REM lines is MOON47.txt')
    P = S.plain(M)
    ok(len(S.split(P)) == 1 and [l for l in P if l.startswith('LBL "')] == ['LBL "MOON47"'], 'one program, LBL "MOON47" the only global label')
    ok(not [l for l in P if l.startswith(('GTO', 'XEQ "'))], 'no GTO, no call by name')
    src = [l for l in open(os.path.join(B.SRC, 'MOON47.txt'), encoding='utf-8').read().split('\n') if l.strip()]
    ok(src == S.indent([l.strip() for l in src]) and not [l for l in src if l.strip().startswith('REM ')], 'the source indented, code only')
    print('  %d steps (1_labels %d in three programs), %d labels, %d structures'
          % (len(P), len(lines(os.path.join(ROOT, 'build', 'dev', 'moon', '1_labels', 'MOON47.txt'))),
             sum(l.startswith('LBL ') for l in P), sum(S.op(l) in S.OPENERS for l in P)))

    def frames(L, j, tz):
        t = tempfile.mkdtemp(); files = []
        for i, pr in enumerate(S.split(L)):
            f = os.path.join(t, 'p%d.txt' % i); open(f, 'w', encoding='utf-8').write('\n'.join(pr) + '\n'); files.append(f)
        c = c47sim.load(files)
        c.clock = j + (tz or 0) / 24.0
        if tz is not None:
            c.reg['TZ'] = D(str(tz))
        c.s = [D(0)] * 4; c.frames = []; c.pix = []; c.keys = [43, 82]
        c.run('MOON47', maxsteps=10 ** 8)
        return [{(x, 239 - y) for y, x in f if 0 <= y < 240 and 0 <= x < 400} for f in c.frames], c
    ref = lines(os.path.join(ROOT, 'build', 'dev', 'moon', '1_labels', 'MOON47.txt'))
    rnd = random.Random(4747)
    cases = [(M47.julian(2026, 10, 3, 12.0), None), (M47.julian(2026, 10, 10, 15.0), 4.0), (M47.julian(2027, 1, 22, 3.5), -5.0),
             (M47.julian(2028, 6, 5, 20.2), 5.5), (M47.julian(2029, 3, 1, 1.0), -9.5)]
    while len(cases) < n:
        cases.append((M47.julian(rnd.randint(2000, 2050), rnd.randint(1, 12), rnd.randint(1, 28), rnd.uniform(0, 24)),
                      rnd.choice([None, -3.5, 2.0, 9.0])))
    for j, tz in cases:
        a, _ = frames(ref, j, tz)
        b, c = frames(M, j, tz)
        py = [V21.moon47_screen(j, False, tz or 0)[0], V21.moon47_screen(j, True, tz or 0)[0]]
        d, m, y, h = M47.from_julian(j)
        ok(len(b) == 2 and a == b and b == py and c.s[0] == 0 and c.s[1] == 0,
           '%02d-%02d-%04d %05.2f h TZ %-5s north and south pixel for pixel 1_labels and the Python page, X = Y = 0'
           % (d, m, y, h, tz))


def main():
    n = int(sys.argv[1]) if sys.argv[1:] else 16
    L = source()
    forum(L)
    moon(n)
    pages(L)
    places(L, n)
    print('\n%s' % ('ALL PASSED' if not BAD else '%d FAILED: %s' % (len(BAD), '; '.join(BAD))))
    return 1 if BAD else 0


if __name__ == '__main__':
    sys.exit(main())
