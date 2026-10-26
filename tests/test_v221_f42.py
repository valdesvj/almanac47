#!/usr/bin/env python3
"""v2.2.1 for Free42 (build/v2.2.1/free42/, tools/build_release_v221.py) in f42run (tools/f42: the Free42 core with the
DM42 400 x 240 screen) against v2.1.0 (build/free42/): every screen pixel for pixel, and your X Y Z T and LASTX back
when it ends (11 12 13 14, LASTX 99), the variables S7X ... S7L deleted.
  NAVFULL (big): the menu, each view 1-6 and back (+), UP / DOWN on ALMANAC, 0 ends
  NAVLITTLE (tiny): ALMANAC, UP, DOWN DOWN, + ends
  MOON47: north, +/- south, a key ends
      python3 tests/test_v221_f42.py   (needs tools/f42/f42run: sh tools/f42/setup.sh)"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
F42 = os.path.join(ROOT, 'tools', 'f42', 'f42run')
OLD, NEW = os.path.join(ROOT, 'build', 'free42'), os.path.join(ROOT, 'build', 'v2.2.1', 'free42')
KEY = {1: 29, 2: 30, 3: 31, 4: 24, 5: 25, 6: 26, 0: 34, '+': 37, 'up': 18, 'down': 23, '+/-': 15}
INPUTS = (('2026.1004', '9.30', '25.20', '55.12'), ('2027.0315', '3.30', '-33.54', '18.25'))
BAD = []

# your stack before: X 11, Y 12, Z 13, T 14, LASTX 99; after: GETL puts LASTX in X (so X 99, Y 11, Z 12, T 13),
# CHK7 shows "S7 LEFT" if a variable S7* is still there
SETUP = ['LBL "SETS"', '99', 'ABS', '14', 'ENTER', '13', 'ENTER', '12', 'ENTER', '11', 'RTN',
         'LBL "GETL"', 'LASTX', 'RTN',
         'LBL "CHK7"', 'SF 25', 'RCL "S7X"', 'FS?C 25', 'GTO 01', 'RCL "S7L"', 'FS?C 25', 'GTO 01', 'CF 25',
         'CLA', 'RTN', 'LBL 01', '"S7 LEFT"', 'AVIEW', 'RTN', 'END']


def ok(cond, what):
    print('  %s  %s' % ('ok  ' if cond else 'FAIL', what))
    if not cond:
        BAD.append(what)


def session(files, label, before, steps):
    """f42run: paste the files and SETUP, run before (INIT ...), SETS, XEQ label, then steps (num / key, a shot after
    each key); the shots and the stack after GETL."""
    t = tempfile.mkdtemp()
    setp = os.path.join(t, 'setup.txt'); open(setp, 'w').write('\n'.join(SETUP) + '\n')
    cmd = ['paste ' + f for f in files] + ['paste ' + setp] + before + ['xeq SETS', 'xeq ' + label]
    n = 0
    for s in steps:
        if s.startswith('shot'):
            cmd.append('shot %s/s%d.pbm' % (t, n)); n += 1
        elif s.startswith('qkey'):                       # qkey K: K 4 s into the run, the screen captured first
            cmd.append('%s 4000 %s/s%d.pbm' % (s, t, n)); n += 1
        else:
            cmd.append(s)
    cmd += ['xeq CHK7', 'msg', 'xeq GETL', 'stack']
    r = subprocess.run([F42], input='\n'.join(cmd) + '\n', text=True, capture_output=True, timeout=1200)
    shots = []
    for k in range(n):
        rows = open('%s/s%d.pbm' % (t, k)).read().split('\n')[2:242]
        shots.append(frozenset((x, y) for y, row in enumerate(rows) for x, c in enumerate(row) if c == '1'))
    st = {l[0]: l[3:].strip() for l in r.stdout.split('\n') if len(l) > 2 and l[0] in 'XYZT' and l[1] == ':'}
    left = 'S7 LEFT' in r.stdout or '#' in ''.join(l for l in r.stdout.split('\n')[-30:] if l.startswith(' ') and '#' in l)
    return shots, st, r.stdout


def stack_back(st):
    try:
        return [float(st.get(k)) for k in 'XYZT'] == [99, 11, 12, 13]
    except (TypeError, ValueError):
        return False


def main():
    if not os.path.exists(F42):
        print('no tools/f42/f42run: sh tools/f42/setup.sh'); return 1
    print('== Free42 NAVFULL v2.2.1 against v2.1.0')
    for inp in INPUTS:
        steps = ['num ' + v for v in inp] + ['shot']
        for p in (1, 2, 3, 4, 5, 6):
            if p in (3, 4):                              # SKY, ANIM run: + while they run
                steps += ['qkey %d' % KEY['+'], 'key %d' % KEY[p], 'shot']
                continue
            steps += ['key %d' % KEY[p], 'shot']
            if p == 1:
                steps += ['key %d' % KEY['up'], 'shot', 'key %d' % KEY['down'], 'shot']
            steps += ['key %d' % KEY['+'], 'shot']
        steps += ['key %d' % KEY[0]]
        res = []
        for d in (OLD, NEW):
            res.append(session([os.path.join(OLD, 'NAVINIT_FAST.txt'), os.path.join(d, 'NAVFULL.txt')], 'NAV', ['xeq INIT'],
                               steps))
        (a, _, _), (b, st, log) = res
        ok(a == b and len(b) == 15 and stack_back(st) and 'S7 LEFT' not in log,
           'NAVFULL %s: %d screens pixel for pixel v2.1.0, your X Y Z T and LASTX back (%s)'
           % (' '.join(inp), len(b), ' '.join('%s %s' % (k, st.get(k)) for k in 'XYZT')))
    print('== Free42 NAVLITTLE v2.2.1 against v2.1.0')
    for inp in INPUTS:
        steps = ['num ' + v for v in inp] + ['shot', 'key %d' % KEY['up'], 'shot', 'key %d' % KEY['down'],
                                              'key %d' % KEY['down'], 'shot', 'key %d' % KEY['+']]
        res = [session([os.path.join(OLD, 'NAVINIT_LITTLE.txt'), os.path.join(d, 'NAVLITTLE.txt')], 'NAV', ['xeq INIT'],
                       steps) for d in (OLD, NEW)]
        (a, _, _), (b, st, log) = res
        ok(a == b and len(b) == 3 and stack_back(st) and 'S7 LEFT' not in log,
           'NAVLITTLE %s: %d screens pixel for pixel v2.1.0, your X Y Z T and LASTX back' % (' '.join(inp), len(b)))
    print('== Free42 MOON47 v2.2.1 against v2.1.0')
    for date, time in (('20261003', '12000000'), ('20270122', '03300000')):
        os.environ['F42_DATE'], os.environ['F42_TIME'] = date, time
        steps = ['shot', 'key %d' % KEY['+/-'], 'shot', 'key %d' % KEY['+']]
        res = [session([os.path.join(d, 'MOON47.txt')], 'MOON47', [], steps) for d in (OLD, NEW)]
        (a, _, _), (b, st, log) = res
        ok(a == b and len(b) == 2 and stack_back(st) and 'S7 LEFT' not in log,
           'MOON47 %s %s: north and south pixel for pixel v2.1.0, your X Y Z T and LASTX back' % (date, time[:4]))
    print('\n%s' % ('ALL PASSED' if not BAD else '%d FAILED' % len(BAD)))
    return 1 if BAD else 0


if __name__ == '__main__':
    sys.exit(main())
