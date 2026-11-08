#!/usr/bin/env python3
"""test_next_f42.py - the next version for Free42 (build/dev/next/free42/, tools/build_next_f42.py) in f42run: UT or
LT with +/- (Free42 key 15; the variables TZ and TZLT).
  NAVFULL    with TZLT 1 the pages ALMANAC, SPLIT, ALLSKY pixel for pixel the Python twin in LT
             (c47screen21.set_times), as v2.1.0 is in UT; INFO as in UT; the menu differs from UT only in its
             header line; +/- on a view and on the menu switches and redraws; TZLT kept; with no TZ / TZLT: UT
  NAVLITTLE  ALMANAC in LT: the pixels that change from UT are those of the twin; +/- switches
             python3 tests/test_next_f42.py   (needs tools/f42/f42run)"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [os.path.join(ROOT, 'python'), os.path.join(ROOT, 'python', 'native'), os.path.join(ROOT, 'tests')]
import c47screen as PS                                                        # noqa: E402
import c47screen21 as N                                                       # noqa: E402
from c47view import jd                                                        # noqa: E402

F42 = os.path.join(ROOT, 'tools', 'f42', 'f42run')
NEXT = os.path.join(ROOT, 'build', 'dev', 'next', 'free42')
KEY = {1: 29, 2: 30, 3: 31, 4: 24, 5: 25, 6: 26, 0: 34, '+': 37, '+/-': 15, 'up': 18, 'down': 23}
bad = 0


def ok(cond, what):
    global bad
    bad += not cond
    print('  %s  %s' % ('ok  ' if cond else 'FAIL', what))


def shots(name, init, inp, regs, keys):
    """f42run: INIT, the variables regs, NAV, the inputs; the screen after the inputs and after each key; TZLT left."""
    t = tempfile.mkdtemp()
    setup = os.path.join(t, 'setup.txt')
    open(setup, 'w').write('\n'.join(['LBL "SETUP"'] + ['%s\nSTO "%s"' % (v, k) for k, v in regs.items()]
                                     + ['RTN', 'END', 'LBL "SHOW"', 'SF 25', 'RCL "TZLT"', 'RTN', 'END']) + '\n')
    cmd = ['paste ' + os.path.join(ROOT, 'build', 'free42', init + '.txt'), 'paste ' + os.path.join(NEXT, name + '.txt'),
           'paste ' + setup, 'xeq INIT', 'xeq SETUP', 'xeq NAV'] + ['num ' + v for v in inp] + ['shot %s/m.pbm' % t]
    for i, k in enumerate(keys):
        cmd += ['key %d' % KEY[k], 'shot %s/s%d.pbm' % (t, i)]
    cmd += ['key %d' % KEY[0 if name == 'NAVFULL' else '+'], 'xeq SHOW', 'stack']     # NAV ends: 0 on the menu, + on LITTLE
    r = subprocess.run([F42], input='\n'.join(cmd) + '\n', text=True, capture_output=True, timeout=1800)
    out = []
    for f in ['m'] + ['s%d' % i for i in range(len(keys))]:
        rows = open('%s/%s.pbm' % (t, f)).read().split('\n')[2:242]
        out.append(frozenset((x, y) for y, row in enumerate(rows) for x, c in enumerate(row) if c == '1'))
    left = [l[3:].strip() for l in r.stdout.split('\n') if l.startswith('X:')]
    return out, (float(left[-1]) if left else None)


def twin(view, al, tz, local):
    N.set_times(tz, local)
    try:
        return N.VIEWS[view](al)[0]
    finally:
        N.set_times()


def main():
    if not os.path.exists(F42):
        print('no tools/f42/f42run (sh tools/f42/setup.sh)')
        return 0
    import t21sim
    print('== Free42 NAVFULL of the next version: UT / LT (+/-)')
    cases = [((2026, 9, 26, 14 + 57 / 60, 25 + 20 / 60, 55.2), 3), ((2027, 3, 5, 22.5, 48.85, -4.3), 5.5),
             ((2027, 1, 1, 0.25, 10.0, 100.0), -9.5)]
    for case, tz in cases:
        inp = t21sim.c47in(*case)
        al = PS.Almanac(jd(*case[:4]), case[4], case[5])
        keys = [1, '+', 2, '+', 5, '+', 6, '+']
        lt, left = shots('NAVFULL', 'NAVINIT_FULL', inp, {'TZ': tz, 'TZLT': 1}, keys)
        ut, _ = shots('NAVFULL', 'NAVINIT_FULL', inp, {'TZ': tz}, keys)
        views = [len(lt[1 + 2 * i] ^ twin(v, al, tz, True)) for i, v in enumerate(('ALMANAC', 'SPLIT', 'ALLSKY'))]
        menu = lt[0] ^ ut[0]
        ok(not any(views) and lt[7] == ut[7] and menu and all(18 <= y < 36 for x, y in menu) and left == 1,
           '%04d-%02d-%02d %05.2f h TZ %+g: ALMANAC SPLIT ALLSKY = the twin in LT %s, INFO as in UT, the menu: its '
           'header, TZLT 1' % (case[:4] + (tz, views)))
    case, tz = cases[0]
    inp = t21sim.c47in(*case)
    al = PS.Almanac(jd(*case[:4]), case[4], case[5])
    a, left = shots('NAVFULL', 'NAVINIT_FULL', inp, {'TZ': tz}, [1, '+/-', '+/-', '+'])
    ok(a[1] == twin('ALMANAC', al, tz, False) and a[2] == twin('ALMANAC', al, tz, True) and a[3] == a[1] and left == 0,
       'ALMANAC in UT, +/- LT, +/- UT again (the view redrawn), TZLT 0')
    a, left = shots('NAVFULL', 'NAVINIT_FULL', inp, {'TZ': tz}, ['+/-', 1, '+'])
    b, _ = shots('NAVFULL', 'NAVINIT_FULL', inp, {'TZ': tz, 'TZLT': 1}, [1, '+'])
    ok(a[1] == b[0] and a[2] == b[1] and left == 1, 'the menu, +/- -> the menu in LT, then ALMANAC in LT, TZLT 1')
    a, left = shots('NAVFULL', 'NAVINIT_FULL', inp, {}, [1, '+'])
    ok(a[1] == twin('ALMANAC', al, 0, False) and left == 0, 'no TZ, no TZLT: NAV makes them 0, UT')

    print('== Free42 NAVLITTLE of the next version: UT / LT (+/-)')
    for case, tz in cases:
        inp = t21sim.c47in(*case)
        al = PS.Almanac(jd(*case[:4]), case[4], case[5])
        lt, left = shots('NAVLITTLE', 'NAVINIT_LITTLE', inp, {'TZ': tz, 'TZLT': 1}, ['+/-'])
        ut, _ = shots('NAVLITTLE', 'NAVINIT_LITTLE', inp, {'TZ': tz}, [])
        tw = twin('ALMANAC', al, tz, True) ^ twin('ALMANAC', al, tz, False)
        ok((lt[0] ^ ut[0]) == tw and lt[1] == ut[0] and left == 0,
           '%04d-%02d-%02d %05.2f h TZ %+g: ALMANAC in LT (the pixels of the twin), +/- -> UT, TZLT 0' % (case[:4] + (tz,)))
    print('%d failed' % bad if bad else 'ALL PASSED')
    return bad


if __name__ == '__main__':
    sys.exit(1 if main() else 0)
