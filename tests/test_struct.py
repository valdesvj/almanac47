#!/usr/bin/env python3
"""test_struct.py - the C47 STRUCT commands: tools/c47struct.py (VALID's check and numbers, GTO -> STRUCT) and
python/c47sim.py (IF ELSE ENDIF, DO WHILE ENDDO, REPEAT UNTIL as the firmware runs them, structured.c).

  1. c47struct: the opposite tests, the faults VALID finds, the numbers, the listing indentation
  2. c47sim: each structure true and false, the key wait DO / PAUSE / KEY? / WHILE / ENDDO, a test before ENDIF
     (never skipped), a structure without its number (stops)
  3. the rules on small programs: the same results as the GTO version for many inputs
  4. build/dev/struct/19_struct, 20_layout (the same steps in another order) and 21_pixel: every program VALID, numbers within 255, the same file again from
     18_hourglass; every page (FULL, FAST, three dates and places, hour arrows) and the menu's keys pixel for pixel
     18_hourglass, the stack clear at the end; how many structures the pages entered

  python3 tests/test_struct.py
"""
import os, random, sys
from decimal import Decimal as D
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [os.path.join(ROOT, 'python'), os.path.join(ROOT, 'tools'), os.path.join(ROOT, 'tests')]
import c47sim                                                        # noqa: E402
import c47struct as S                                                # noqa: E402

BAD = []
LAST = '41_layout'                      # the last step of build/dev/struct


def ok(cond, what):
    print('  %s  %s' % ('ok  ' if cond else 'FAIL', what))
    if not cond:
        BAD.append(what)


def run(prog, x=0, y=0, keys=None, regs=None):
    c = c47sim.Calc('\n'.join(prog))
    c.pix, c.frames, c.msgs, c.stops, c.alpha = [], [], [], [], ''
    c.s = [D(x), D(y), D(0), D(0)]
    for k, v in (regs or {}).items():
        c.rset(k, D(v))
    if keys is not None:
        c.keys = list(keys)
    c.run('T', maxsteps=10 ** 5)
    return c


def unit():
    print('== c47struct')
    for a, b in (('X<Y?', 'X≥Y?'), ('X=0?', 'X≠0?'), ('X>0?', 'X≤0?'), ('FS? 10', 'FC? 10'), ('x<? 05', 'x≥? 05')):
        ok(S.invert(a) == b and S.invert(b) == a, 'opposite tests %s / %s' % (a, b))
    ok(all(S.invert(t) is None for t in ('ISG 05', 'DSE 05', 'KEY? 39', 'MATR?')), 'ISG DSE KEY? MATR? have no opposite')
    good = ['LBL "T"', 'X<0?', 'IF', 'CHS', 'ENDIF', 'DO', 'ISG 01', 'WHILE', 'ENDDO', 'REPEAT', 'X=0?', 'UNTIL', 'END']
    ok(S.check(good) == [], 'a valid program: no fault')
    faults = {
        'IF after a step that is not a test': ['LBL "T"', 'CHS', 'IF', 'ENDIF', 'END'],
        'ENDIF closing a DO': ['LBL "T"', 'DO', 'X=0?', 'WHILE', 'ENDIF', 'END'],
        'DO without WHILE': ['LBL "T"', 'DO', 'CHS', 'ENDDO', 'END'],
        'open at END': ['LBL "T"', 'X=0?', 'IF', 'CHS', 'END'],
        'across RTN + LBL': ['LBL "T"', 'X=0?', 'IF', 'RTN', 'LBL 01', 'ENDIF', 'END'],
        'a test before ENDIF': ['LBL "T"', 'X=0?', 'IF', 'X<0?', 'ENDIF', 'END'],
        'a test before DO': ['LBL "T"', 'X=0?', 'DO', 'X<0?', 'WHILE', 'ENDDO', 'END'],
        '256 IF': ['LBL "T"'] + ['X=0?', 'IF', 'ENDIF'] * 256 + ['END'],
    }
    for what, P in faults.items():
        ok(S.check(P) != [], 'fault found: %s' % what)
    N = S.number_program(['LBL "T"', 'X=0?', 'IF', 'DO', 'ISG 01', 'WHILE', 'X<0?', 'IF', 'ENDIF', 'ENDDO', 'ELSE',
                          'X=0?', 'IF', 'ENDIF', 'ENDIF', 'END'])
    ok(N == ['LBL "T"', 'X=0?', 'IF 01', 'DO 01', 'ISG 01', 'WHILE 01', 'X<0?', 'IF 02', 'ENDIF 02', 'ENDDO 01', 'ELSE 01',
             'X=0?', 'IF 03', 'ENDIF 03', 'ENDIF 01', 'END'], 'numbers: IF / DO / REPEAT series in the order of the openers')
    ok(S.plain(S.indent(N)) == S.plain(N) and S.indent(N)[3] == '  DO 01' and S.indent(N)[5] == '  WHILE 01',
       'indentation: two spaces a level, WHILE on its DO column, plain() takes it off')


def sim():
    print('== c47sim')
    P = ['LBL "T"', 'X<0?', 'IF 01', '1', 'ELSE 01', '2', 'ENDIF 01', 'RTN', 'END']
    ok(run(P, -5).s[0] == 1 and run(P, 5).s[0] == 2, 'IF ELSE ENDIF: true and false')
    P = ['LBL "T"', '0', 'STO 02', '1.005', 'STO 01', 'DO 01', 'RCL 01', 'IP', 'STO+ 02', 'ISG 01', 'WHILE 01', 'ENDDO 01',
         'RCL 02', 'RTN', 'END']
    ok(run(P).s[0] == 15, 'DO ... ISG WHILE ENDDO: 1 + 2 + 3 + 4 + 5')
    P = ['LBL "T"', 'REPEAT 01', '2', '×', '100', 'X<>Y', 'X>Y?', 'UNTIL 01', 'RTN', 'END']
    ok(run(P, 3).s[0] == 192, 'REPEAT ... X>Y? UNTIL: doubled until over 100')
    P = ['LBL "T"', 'DO 01', 'PAUSE 50', 'KEY? 05', 'WHILE 01', 'ENDDO 01', 'RCL 05', 'RTN', 'END']
    c = run(P, keys=[73])
    ok(c.s[0] == 73 and len(c.frames) == 1, 'key wait DO PAUSE KEY? WHILE ENDDO: the key, one frame')
    P = ['LBL "T"', 'X=0?', 'IF 01', '7', 'X<0?', 'ENDIF 01', '8', 'RTN', 'END']
    ok(run(P, 0).s[0] == 8, 'a false test before ENDIF does not skip it (structNoLegacySkip)')
    P = ['LBL "T"', 'X=0?', 'IF', '7', 'ENDIF', 'RTN', 'END']
    try:
        run(P, 0)
        ok(False, 'IF without its number stops')
    except ValueError:
        ok(True, 'IF without its number stops')
    P = ['LBL "T"', 'X=0?', 'IF 01', 'DO 01', 'ISG 01', 'WHILE 01', 'ENDDO 01', 'ELSE 01', '5', 'ENDIF 01', 'RTN', 'END']
    ok(run(P, 1).s[0] == 5 and run(P, 0, regs={'01': '1.003'}).rget('01') == D('4.003'),
       'IF 01 and DO 01 in one program: each finds its own partner')


TOYS = {
    'skip': ['LBL "T"', 'X<0?', 'GTO 01', '10', '+', 'LBL 01', '2', '×', 'RTN', 'END'],
    'if-else': ['LBL "T"', 'X>0?', 'GTO 01', 'CHS', 'GTO 02', 'LBL 01', '3', '+', 'LBL 02', 'RTN', 'END'],
    'chain': ['LBL "T"', 'X=0?', 'GTO 01', 'X<0?', 'GTO 02', '1', 'GTO 03', 'LBL 01', '0', 'GTO 03', 'LBL 02', '-1',
              'LBL 03', 'RTN', 'END'],
    'loop': ['LBL "T"', 'STO 01', '0', 'LBL 01', 'RCL+ 01', '1', 'STO- 01', 'RCL 01', 'X>0?', 'GTO 01', 'R↓', 'RTN', 'END'],
    'isg': ['LBL "T"', 'ABS', '1000', '÷', '1', '+', 'STO 01', '0', 'LBL 05', 'RCL 01', 'IP', '+', 'ISG 01', 'GTO 05',
            'RTN', 'END'],
    'while': ['LBL "T"', 'ABS', 'STO 01', '0', 'LBL 01', 'RCL 01', 'X=0?', 'GTO 02', '1', 'STO- 01', 'R↓', '3', '+',
              'GTO 01', 'LBL 02', 'R↓', 'RTN', 'END'],
    'exit block': ['LBL "T"', 'ABS', 'STO 01', 'LBL 01', 'RCL 01', '10', 'X<Y?', 'GTO 02', 'R↓', '2', '+', 'STO 01',
                   'GTO 01', 'LBL 02', 'R↓', 'RTN', 'END'],
    'rtn': ['LBL "T"', 'X<0?', 'GTO 01', '5', '+', 'LBL 01', 'RTN', 'END'],
    'break': ['LBL "T"', 'ABS', 'STO 02', '1.010', 'STO 01', '0', 'LBL 01', 'RCL 01', 'IP', '+', 'RCL 02', 'X<Y?', 'GTO 02',
              'R↓', 'ISG 01', 'GTO 01', 'LBL 02', 'RTN', 'END'],
    'all-of': ['LBL "T"', 'STO 01', 'X<0?', 'GTO 05', '5', 'X<Y?', 'GTO 05', 'RCL 01', '2', '×', 'RTN', 'LBL 05', 'RCL 01',
               'CHS', 'RTN', 'END'],
    'dup': ['LBL "T"', 'X<0?', 'XEQ 01', 'X≥0?', 'XEQ 02', 'RTN', 'LBL 01', '1', '+', 'GTO 03', 'LBL 02', '2', '+', 'LBL 03',
            '10', '×', 'RTN', 'END'],
}


def rules():
    print('== the rules on small programs')
    rnd = random.Random(47)
    for name, P in TOYS.items():
        Q, stats = S.structure(P)
        left = S.gotos(Q)[0]
        same = all(run(P, x).s[0] == run(Q, x).s[0] for x in [rnd.randint(-20, 20) for _ in range(40)] + [0])
        ok(same and left == 0 and not S.check(Q), '%-10s no GTO left, the same results  %s' % (name, ' '.join(sorted(stats))))


def box():
    """The SINKING box (steps 23, 29) and the menu's highlight bar (step 29) of the last step against the code they
    replace, on a random screen: the same pixels, GRMOD and counters."""
    import build_struct as B
    print('== the SINKING box and the highlight bar: the last step against the code before 23')
    E, O = B.EDGE30, B.ONES30
    old = ['LBL "T"', 'WSIZE 32', 'RCL 44', 'XEQ 08', 'RCL 62', 'STO 04', 'R↓', 'DO 01', 'AGRAPH 03', 'DSE 04', 'WHILE 01',
           'ENDDO 01', 'RCL 46', 'XEQ 08', 'AGRAPH 03', 'AGRAPH 03', E, 'STO 03', 'R↓', 'RCL 63', 'STO 07', 'R↓', 'DO 02',
           'AGRAPH 03', 'DSE 07', 'WHILE 02', 'ENDDO 02', O, 'STO 03', 'R↓', 'AGRAPH 03', 'AGRAPH 03', 'WSIZE 64', 'RTN',
           'LBL 08', 'STO 03', 'GRMOD 03', '105', '110', O, 'STO 03', 'R↓', 'RTN', 'END']
    P = S.plain(V_lines(LAST))
    k = P.index('"SINKING....ABOUT"')
    a = k
    while not P[a].startswith('LBL '):
        a -= 1
    new = ['LBL "T"'] + P[a + 1:k] + ['RTN', 'END']
    bar_old = ['LBL "T"', 'WSIZE 18', 'RCL 51', 'STO 01', 'GRMOD 01', '1111111111111111#2', 'STO 01', 'RCL 12', 'RCL 02',
               '170', 'STO 02', 'R↓', 'DO 01', 'AGRAPH 01', 'DSE 02', 'WHILE 01', 'ENDDO 01', 'RCL 46', 'STO 01',
               'GRMOD 01', 'WSIZE 64', 'RTN', 'END']
    b = P.index('1111111111111111#2') - 4
    e = b
    while P[e] != 'RTN':
        e += 1
    bar_new = ['LBL "T"'] + P[b:e + 1] + ['END']
    rnd = random.Random(1)
    scr = [(y, x) for y in range(240) for x in range(400) if rnd.random() < 0.4]
    for what, pair in (('the SINKING box', (old, new)), ('the highlight bar (XOR, 170 columns)', (bar_old, bar_new))):
        res = []
        for prog in pair:
            c = c47sim.Calc('\n'.join(S.number(prog))); c.pix = list(scr); c.frames = []; c.grmod = 0; c.ws = 64
            for r, v in ((43, 1), (44, 2), (46, 0), (51, 3), (62, 180), (63, 176), (12, 160), (2, 202)):
                c.rset(str(r), D(v))
            c.run('T')
            res.append((set(c.pix), c.grmod, c.rget('04') if what.startswith('the S') else 0, c.rget('07'), c.rget('03'),
                        c.rget('02'), c.rget('01')))
        ok(res[0] == res[1], '%s: pixel for pixel on a random screen; GRMOD and the registers as before' % what)


def places(n=8):
    """The last step against 18_hourglass at random dates (2000-2049), times and places (65 S - 65 N), FULL and FAST:
    ALMANAC, SPLIT, SKY, ANIM, ALLSKY with an hour arrow, pixel for pixel (the planets / stars below the horizon, the
    loops' ends: what three fixed places can miss)."""
    import test_v2 as V
    print('== %s against 18_hourglass at %d random dates and places' % (LAST, n))
    A = V.lines(os.path.join(ROOT, 'build', 'dev', 'struct', '18_hourglass', 'NAVFULL.txt'))
    B = V_lines(LAST)
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
            b = V.session(B, keys, init, False, inp, marks=False)
            same.append(a[0] == b[0] and b[2])
        ok(all(same), '%s %s %s %s %s: pages 1-5 pixel for pixel' % ((init,) + tuple(v for _, v in inp)))


def V_lines(step):
    return [l for l in open(os.path.join(ROOT, 'build', 'dev', 'struct', step, 'NAVFULL.txt'), encoding='utf-8').read()
            .split('\n') if l.strip()]


def navfull(step='19_struct'):
    import test_v2 as V
    print('== build/dev/struct/%s against 18_hourglass' % step)
    A = V.lines(os.path.join(ROOT, 'build', 'dev', 'struct', '18_hourglass', 'NAVFULL.txt'))
    B = V.lines(os.path.join(ROOT, 'build', 'dev', 'struct', step, 'NAVFULL.txt'))
    faults = [f for P in S.split(B) for f in S.check(P)]
    ok(not faults, 'every program VALID%s' % (': ' + '; '.join(faults[:3]) if faults else ''))
    import build_struct
    again = build_struct.struct(A)
    steps = [x for x in build_struct.STEPS if int(x[0].split('_')[0]) >= 20]
    chain = tuple(x[0] for x in steps)
    for name, fn in [(x[0], x[1]) for x in steps]:
        if step in chain[chain.index(name):]:
            again = fn(again)
    if step == '20_layout':
        P19 = V.lines(os.path.join(ROOT, 'build', 'dev', 'struct', '19_struct', 'NAVFULL.txt'))
        ok(len(B) == len(P19) and len(S.split(B)) == len(S.split(P19)), 'as many programs and steps as 19_struct')
    ok(again == B, 'the same file again from 18_hourglass (tools/build_struct.py)')
    ok(S.number(B) == B, 'numbered as VALID numbers them')
    print('  GTO nn for decisions and loops %d -> %d, tail calls %d -> %d'
          % (S.gotos(A)[0], S.gotos(B)[0], S.gotos(A)[1], S.gotos(B)[1]))
    ran = set()
    cases = [('FULL', ('2026.1004', '9.30', '25.20', '55.12')), ('FAST', ('2027.0315', '3.30', '-33.54', '18.25')),
             ('FULL', ('2026.1020', '22.10', '60.10', '-5.00'))]
    for init, (dt, ut, la, lo) in cases:
        inp = (('DATE', dt), ('UTC', ut), ('LAT', la), ('LON', lo))
        for p, name in ((1, 'ALMANAC'), (2, 'SPLIT'), (3, 'SKY'), (4, 'ANIM'), (5, 'ALLSKY'), (6, 'INFO')):
            keys = [V.K[p], V.K['up'], V.K['down'], V.K['down'], V.K['+'], V.K[0]] if p in (1, 3, 5) else [V.K[p], V.K['+'], V.K[0]]
            a = V.session(A, keys, init, False, inp, marks=False)
            c = V.T.load(B, init)
            for k, v in inp:
                c.reg[k] = D(v)
            at = c.lines.index(B[0])
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
        b = V.session(B, keys, 'FULL', False, marks=False)
        ok(a[0] == b[0] and b[2], '%s: %d screens pixel for pixel, stack clear' % (what, len(b[0])))
    st = [i for i, l in enumerate(B) if S.op(l) in S.OPENERS]
    print('  structures entered on these pages: %d of %d' % (len([i for i in st if i in ran]), len(st)))


def main():
    unit()
    sim()
    rules()
    navfull('19_struct')
    navfull('20_layout')
    navfull(LAST)
    box()
    places()
    print('\n%s' % ('ALL PASSED' if not BAD else '%d FAILED: %s' % (len(BAD), '; '.join(BAD))))
    return 1 if BAD else 0


if __name__ == '__main__':
    sys.exit(main())
