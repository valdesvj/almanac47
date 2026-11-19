#!/usr/bin/env python3
"""test_one47.py - DEV: the one-program ALMA47 (build/dev/one/, tools/build_one47.py) against v2.3.0's 26 programs
(build/v2.3.0/c47/ALMA47.txt) in the C47 firmware (the PC simulator built from the firmware sources, headless).

  1. listing   one program (one END), ALMA47 the only global label, every jump has its label, the structures VALID,
               the same steps as v2.3.0 but for the labels, the inner ENDs (RTN) and PLN3's table moved to its end;
               build/dev/one/ALMA47.txt and ALMA47_LABELS.txt are the build of today's source
  2. screens   python/c47sim.py (it finds a repeated local label as the firmware does: the first after the jump, else
               the first in the program): every page with the FULL and the FAST series at three dates and places, the
               arrows, the menu's keys, and n random dates and places, every frame pixel for pixel, the stack clear
  3. firmware  NAVINIT_FAST, the inputs, then each page (1-6, the arrows, 9 SNAP, + menu, 0 end) with both programs:
               no error, X = 0, the registers at the first screen (.REGS.TSV, SNAP) the same; the CPU time of each run
               (the simulator's start without ALMA47 taken off). The screens of SNAP are not compared: SNAP takes the
               screen of the simulator's last refresh (a timer), not the same from one run to the next

The key waits are replaced in a test copy by SNAP and the next key (tests/test_fw_c47.py testcopy).

  python3 tests/test_one47.py [n]    (n random cases, default 8)  C47SIM=/path/to/c47 (default ~/.cache/c47fw/c47)
"""
import os, re, resource, shutil, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [os.path.join(ROOT, 'tools'), os.path.join(ROOT, 'tests')]
import build_one47 as O                                              # noqa: E402
import c47struct as C                                                # noqa: E402
import test_fw_c47 as T                                              # noqa: E402

OLD = os.path.join(ROOT, 'build', 'v2.3.0', 'c47', 'ALMA47.txt')
NEW = os.path.join(O.OUT, 'ALMA47.txt')
BAD = []
PAGES = [([72, 85, 82], '1 ALMANAC'), ([73, 85, 82], '2 SPLIT'), ([74, 85, 82], '3 SKY'), ([62, 85, 82], '4 ANIM'),
         ([63, 85, 82], '5 ALLSKY'), ([64, 85, 82], '6 INFO'), ([72, 51, 61, 61, 85, 82], '1 + arrows'),
         ([74, 51, 85, 82], '3 + arrow'), ([54, 51, 72, 85, 82], '9 SNAP, arrow, 1')]


def ok(cond, what):
    print('  %s  %s' % ('ok  ' if cond else 'FAIL', what))
    if not cond:
        BAD.append(what)


def lines(f):
    return [l for l in open(f, encoding='utf-8').read().split('\n') if l.strip()]


def listing():
    print('== build/dev/one/ALMA47.txt')
    M = O.listing()
    ok(lines(NEW) == M, 'the build of programs_struct/next/ (tools/build_one47.py), %d steps' % len(M))
    ok(lines(os.path.join(O.OUT, 'ALMA47_LABELS.txt')) == [l for l in O.labels_file(M) if l.strip()],
       'ALMA47_LABELS.txt is the build')
    ok(M.count('END') == 1 and M[-1] == 'END', 'one program')
    ok([l for l in M if l.startswith('LBL "')] == ['LBL "ALMA47"'] and not any(re.match(r'(XEQ|GTO) "', l) for l in M),
       'ALMA47 the only global label, no named XEQ')
    miss = [l for l in M if re.fullmatch(r'(?:XEQ|GTO) (:.+:|\d\d|[A-La-l])', l) and 'LBL ' + l[4:] not in M]
    ok(not miss, 'every jump has its label %s' % miss[:3])
    ok(not C.check(M), 'the structures VALID')
    named = {l[4:] for l in M if l.startswith('LBL :')}
    ok(named == {':%s:' % n for g, n in O.names().items() if 'LBL "%s"' % g in lines(OLD)},
       '%d local labels, each the original name of a v2.3.0 global label' % len(named))
    strip = lambda L: sorted(l for l in L if not re.match(r'(LBL|XEQ|GTO) |END$|RTN$', l))
    ok(strip(M) == strip(lines(OLD)), 'the same steps as v2.3.0 but labels, jumps, END / RTN')


def screens(n):
    import random
    import test_v2 as V
    print('== python/c47sim.py: every frame of the one program against v2.3.0')
    nav = lambda f: ['LBL "NAV"'] + lines(f)[1:]
    A, M = nav(OLD), nav(NEW)
    K = V.K
    cases = [('FULL', ('2026.1004', '9.30', '25.20', '55.12')), ('FAST', ('2027.0315', '3.30', '-33.54', '18.25')),
             ('FULL', ('2026.1020', '22.10', '60.10', '-5.00'))]
    rnd = random.Random(47)
    for t in range(n):
        cases.append(('FAST' if t % 2 else 'FULL', ('%d.%02d%02d' % (rnd.randint(2000, 2049), rnd.randint(1, 12),
                      rnd.randint(1, 28)), '%d.%02d' % (rnd.randint(0, 23), rnd.randint(0, 59)),
                      '%.2f' % rnd.uniform(-65, 65), '%.2f' % rnd.uniform(-179, 179))))
    for init, (dt, ut, la, lo) in cases:
        inp = (('DATE', dt), ('UTC', ut), ('LAT', la), ('LON', lo))
        res = []
        for p in (1, 2, 3, 4, 5, 6):
            keys = [K[p], K['up'], K['down'], K['down'], K['+'], K[0]] if p in (1, 3, 5) else [K[p], K['+'], K[0]]
            a = V.session(A, keys, init, False, inp, marks=False)
            b = V.session(M, keys, init, False, inp, marks=False)
            res.append((a[0] == b[0] and b[2], len(b[0])))
        ok(all(r for r, _ in res), '%s %s %s %s %s: pages 1-6 (%s frames) pixel for pixel, stack clear'
           % (init, dt, ut, la, lo, '+'.join(str(k) for _, k in res)))
    for keys, what in (([K['up'], K['down'], K['down'], K[1], K['+'], K[0]], 'menu: arrows, ALMANAC'),
                       ([54, 52, 53, 85, K[3], K['+'], K[0]], 'menu: 9 SNAP, 7, 8, +, SKY'),
                       ([K[6], K['up'], K['+'], K[0]], 'INFO, arrow'),
                       ([K[2], K['down'], K[0], K[9], K['up'], K['+'], K[4], K['+'], K[0]], 'SPLIT, 0 and 9, ANIM'),
                       ([K[1], 72, K[0]], 'ALMANAC, key 1 picks the Sun'),
                       ([K[2], 53, K[0]], 'SPLIT, key 8 picks a body'),
                       ([11, 21, 31, 41, 71, 81, K[1], K['+'], K[0]], 'menu: keys that are no view')):
        a = V.session(A, keys, 'FULL', False, marks=False)
        b = V.session(M, keys, 'FULL', False, marks=False)
        ok(a[0] == b[0] and b[2] == a[2], '%s: %d frames pixel for pixel' % (what, len(b[0])))


def run(src, keys):
    d = T.tmp()
    files = [T.p47(os.path.join(T.INIT_C47, 'NAVINIT_FAST.txt'), d, copy=True)]
    if src:
        files.append(T.p47(src, d, name='ALMA47'))
    files.append(T.helper(d, T.INPUTS, keys))
    tcl = ['readp %s' % f for f in files] + ['xeq NAVINIT', 'xeq TSET']
    if src:
        tcl += ['xeq ALMA47'] + ['press R/S'] * 4
    tcl += ['puts "X=[reg X]"']
    r0 = resource.getrusage(resource.RUSAGE_CHILDREN).ru_utime
    out, err = T.sim(d, tcl)
    cpu = resource.getrusage(resource.RUSAGE_CHILDREN).ru_utime - r0
    # SNAP names its files with the clock (yyyymmdd-hhmmssNN.bmp, NN the count in that second): ordered by the
    # time, then each kind apart (a run over a second's change gives the REGS.TSV another name)
    snap = sorted((f for f in os.listdir(d) if f.endswith(('.bmp', '.TSV'))), key=lambda f: (f.endswith('.TSV'), f))
    shots = [open(os.path.join(d, f), 'rb').read() for f in snap]
    x = next((l[2:] for l in out if l.startswith('X=')), None)
    shutil.rmtree(d, ignore_errors=True)
    return shots, err, x, cpu


def firmware():
    print('== the C47 firmware (%s): v2.3.0 (26 programs) and one program' % T.SIM)
    base = min(run(None, [82])[3] for _ in range(3))
    told = tnew = 0
    for keys, what in PAGES:
        a, ea, xa, ca = run(OLD, keys)
        b, eb, xb, cb = run(NEW, keys)
        ca, cb = ca - base, cb - base
        told += ca; tnew += cb
        ta = [s for s in a if s[:2] != b'BM'][:1]
        tb = [s for s in b if s[:2] != b'BM'][:1]
        ok(ta == tb and ta and not ea and not eb and xa == xb == '0',
           '%-18s no error, X = 0, registers the same   CPU %.2f s -> %.2f s (%+.0f %%)'
           % (what, ca, cb, 100 * (cb / ca - 1) if ca > 0 else 0))
    print('  CPU all pages: v2.3.0 %.2f s, one program %.2f s (%+.0f %%)' % (told, tnew, 100 * (tnew / told - 1)))


def main():
    listing()
    screens(int(sys.argv[1]) if len(sys.argv) > 1 else 8)
    firmware()
    print('ALL PASSED' if not BAD else '%d FAILED' % len(BAD))
    return 1 if BAD else 0


if __name__ == '__main__':
    sys.exit(main())
