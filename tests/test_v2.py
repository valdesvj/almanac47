#!/usr/bin/env python3
"""test_v2.py - the release files of v2.0.0 (tools/build_v2.py) against v1.1.0 and against each other.

  C47 NAVFULL v2 / the release before it (branch main)   every page they share (1 ALMANAC, SPLIT, SKY, ANIM, ALLSKY, INFO),
        pixel for pixel in the C47 simulator, with the FULL and the FAST series and with the tables; after NAV the
        registers R00-R99 0 (CLREGS: NAVFULL keeps no register of yours since the one-program build) and the stack clear
  DM42 NAVLITTLE v2 / main (C47 firmware)  the ALMANAC screen, one hour later, one hour earlier; registers kept
  Free42 NAVFULL / C47 NAVFULL v2             the menu and the pages 1 2 5 6, f42run against the C47 simulator
  Free42 NAVLITTLE / C47 NAVLITTLE v2         the three screens of tests/test_f42_little.py
  Free42 registers                            SIZE 25 and R00-R24 set before NAV: the same after NAV (REGS kept)

  python3 tests/test_v2.py            (Free42 parts need tools/f42/f42run)
"""
import os, random, re, subprocess, sys, tempfile, datetime
from decimal import Decimal as D
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [os.path.join(ROOT, 'python'), os.path.join(ROOT, 'tools'), os.path.join(ROOT, 'tools', 'generators'),
                os.path.join(ROOT, 'tests')]
import c47sim                                                        # noqa: E402
import test_navopt as T                                              # noqa: E402

F42 = os.path.join(ROOT, 'tools', 'f42', 'f42run')
REF = '89404df'       # main before v2.0.0 (#50: v1.1.0 with the ATEXT fonts and the PAUSE key waits); main is v2.0.0 since #51
INPUTS = (('DATE', '2026.1004'), ('UTC', '9.30'), ('LAT', '25.20'), ('LON', '55.12'))
# C47 key codes of the digits (row * 10 + column) and of + / 0 / arrows
K = {1: 72, 2: 73, 3: 74, 4: 62, 5: 63, 6: 64, 7: 52, 8: 53, 9: 54, 0: 82, '+': 85, 'up': 51, 'down': 61}
# the pages in each menu: v2 1 ALMANAC 2 SPLIT 3 SKY 4 ANIM 5 ALLSKY 6 INFO; v1.1.0 1 ALMANAC 2 CHART 3 TEXT
# 4 SKY 5 SPLIT 6 ANIM 7 ALLSKY 8 INFO
PAGES = {'ALMANAC': (1, 1), 'SPLIT': (2, 5), 'SKY': (3, 4), 'ANIM': (4, 6), 'ALLSKY': (5, 7), 'INFO': (6, 8)}


def lines(path_or_text):
    t = path_or_text if '\n' in path_or_text else open(path_or_text, encoding='utf-8').read()
    return [l for l in t.split('\n') if l.strip()]


def git_file(tag, path):
    return subprocess.run(['git', 'show', '%s:%s' % (tag, path)], cwd=ROOT, capture_output=True, text=True, check=True).stdout


def session(L, keys, init='FULL', tables=False, inputs=INPUTS, marks=True, cleared=False):
    """NAV in the C47 simulator: frames (as sets of (x, y), y from the top), registers kept (cleared: R00-R99 0
    after NAV, the one-program NAVFULL with CLREGS), stack clear."""
    c = T.load(L, init, tables)
    for k, v in inputs:
        c.reg[k] = D(v)
    m = {'%02d' % r: D(7000 + r) + D('0.5') for r in range(100)}
    if marks:
        for r, v in m.items():
            c.rset(r, v)
    c.flags.add(81); c.s = [D(0)] * 4; c.frames = []; c.pix = []; c.keys = list(keys)
    c.run('NAV', maxsteps=10 ** 8)
    frames = [frozenset((x, 239 - y) for y, x in f if 0 <= y < 240 and 0 <= x < 400) for f in c.frames]
    kept = not marks or all(c.rget(r) == (0 if cleared else v) for r, v in m.items())
    return frames, kept, all(x == 0 for x in c.s)


def c47_vs_v110():
    print('== C47 NAVFULL v2.0.0 against the release before it (%s): the pages they share, pixel for pixel' % REF)
    new = lines(os.path.join(ROOT, 'build', 'NAVFULL.txt'))
    old = lines(git_file(REF, 'build/NAVFULL.txt'))
    rnd = random.Random(20)
    bad = 0
    cases = [('FULL', False, ('2026.1004', '9.30', '25.20', '55.12')), ('FAST', False, ('2027.0315', '3.30', '-33.54', '18.25')),
             ('FULL', True, ('2026.1020', '22.10', '60.10', '-5.00'))]
    for init, tables, (dt, ut, la, lo) in cases:
        inp = (('DATE', dt), ('UTC', ut), ('LAT', la), ('LON', lo))
        for name, (k2, k1) in PAGES.items():
            a, kept, clear = session(new, [K[k2], K['+'], K[0]], init, tables, inp, cleared=True)
            b, _, _ = session(old, [K[k1], K['+'], K[0]], init, tables, inp, marks=False)
            same = len(a) > 1 and len(b) > 1 and a[1] == b[1] and (name != 'ANIM' or a[1:-2] == b[1:-2])
            ok = same and kept and clear
            bad += not ok
            print('  %-4s%-6s %s %5s %6s %7s  %-7s page %s, registers %s, stack %s' % (init, ' T' if tables else '', dt, ut, la, lo, name,
                  'the same' if same else 'DIFFERENT', '0 (CLREGS)' if kept else 'NOT 0', 'clear' if clear else 'NOT CLEAR'))
    return bad


def little_session(L, init_lines, keys, inputs, marks=True):
    t = tempfile.mkdtemp(); files = []
    for i, pr in enumerate(T.split(init_lines + L)):
        f = os.path.join(t, 'p%d.txt' % i); open(f, 'w', encoding='utf-8').write('\n'.join(pr) + '\n'); files.append(f)
    c = c47sim.load(files); c.flags.add(82); c.grfnt = 21
    c.run('INIT', maxsteps=10 ** 7)
    for k, v in inputs:
        c.reg[k] = D(v)
    m = {'%02d' % r: D(8000 + r) + D('0.5') for r in range(100)}
    if marks:
        for r, v in m.items():
            c.rset(r, v)
    c.flags.add(81); c.s = [D(0)] * 4; c.frames = []; c.pix = []; c.keys = list(keys)
    c.run('NAV', maxsteps=10 ** 8)
    frames = [frozenset((x, 239 - y) for y, x in f if 0 <= y < 240 and 0 <= x < 400) for f in c.frames]
    return frames, not marks or all(c.rget(r) == v for r, v in m.items()), all(x == 0 for x in c.s)


def dm42_vs_v110():
    print('\n== DM42 NAVLITTLE (C47 firmware) v2.0.0 against %s: ALMANAC, one hour later, one hour earlier' % REF)
    new = lines(os.path.join(ROOT, 'build', 'dm42', 'NAVLITTLE.txt'))
    init = lines(os.path.join(ROOT, 'build', 'dm42', 'NAVINIT_LITTLE.txt'))
    old = lines(git_file(REF, 'build/dm42/NAVLITTLE.txt'))
    oinit = lines(git_file(REF, 'build/dm42/NAVINIT_LITTLE.txt'))
    bad = 0
    for inp in (INPUTS, (('DATE', '2031.0315'), ('UTC', '3.30'), ('LAT', '-33.54'), ('LON', '18.25'))):
        keys = [K['up'], K['down'], K['down'], K['+']]
        a, kept, clear = little_session(new, init, keys, inp)
        b, _, _ = little_session(old, oinit, keys, inp, marks=False)
        same = a == b
        bad += not (same and kept and clear)
        print('  %s %s %s %s  %d screens %s, registers %s, stack %s' % (tuple(v for _, v in inp) + (len(a), 'the same' if same else 'DIFFERENT',
              'kept' if kept else 'CHANGED', 'clear' if clear else 'NOT CLEAR')))
    return bad


# the menu key line (rows from the top) and the x where its last word starts: 9 SNAP on the C47, 9 PRLCD on Free42
HINT_ROWS, HINT_X = range(190, 206), 324
HINT_WORD = frozenset((x, y) for x in range(HINT_X, 400) for y in HINT_ROWS)
F42KEY = {1: 29, 2: 30, 3: 31, 4: 24, 5: 25, 6: 26, 0: 34, '+': 37}


def f42_shots(nav, init, inputs, keys):
    """f42run: INIT, NAV, the inputs; a picture after each key of keys (the menu first)."""
    t = tempfile.mkdtemp()
    cmd = ['paste ' + init, 'paste ' + nav, 'xeq INIT', 'xeq NAV'] + ['num ' + v for _, v in inputs] + ['shot %s/m.pbm' % t]
    for i, k in enumerate(keys):
        cmd += ['key %d' % k, 'shot %s/s%d.pbm' % (t, i)]
    cmd += ['stack']
    r = subprocess.run([F42], input='\n'.join(cmd) + '\n', text=True, capture_output=True, timeout=1800)
    out = []
    for f in ['m'] + ['s%d' % i for i in range(len(keys))]:
        rows = open('%s/%s.pbm' % (t, f)).read().split('\n')[2:242]
        out.append(frozenset((x, y) for y, row in enumerate(rows) for x, c in enumerate(row) if c == '1'))
    return out, r.stdout


def f42_vs_c47():
    if not os.path.exists(F42):
        print('\n== Free42: no tools/f42/f42run (sh tools/f42/setup.sh)')
        return 0
    print('\n== Free42 NAVFULL against the C47 NAVFULL v2.0.0: the menu and the pages 1 2 5 6, pixel for pixel')
    nav = os.path.join(ROOT, 'build', 'free42', 'NAVFULL.txt')
    init = os.path.join(ROOT, 'build', 'free42', 'NAVINIT_FULL.txt')
    c47 = lines(os.path.join(ROOT, 'build', 'NAVFULL.txt'))
    bad = 0
    for inp in (INPUTS, (('DATE', '2031.0315'), ('UTC', '3.30'), ('LAT', '-33.54'), ('LON', '18.25'))):
        pages = [1, 2, 5, 6]                       # 3 SKY and 4 ANIM run until a key (f42run waits for a stop)
        fkeys, ckeys = [], []
        for p in pages:
            fkeys += [F42KEY[p], F42KEY['+']]; ckeys += [K[p], K['+']]
        f, _ = f42_shots(nav, init, inp, fkeys)
        c, kept, clear = session(c47, ckeys + [K[0]], 'FULL', False, inp)
        # the menus (every other screen) differ only in the last word of the key line: 9 PRLCD / 9 SNAP
        diffs = [len(a ^ b) if i % 2 else len({(x, y) for x, y in a ^ b if not (y in HINT_ROWS and x >= HINT_X)})
                 for i, (a, b) in enumerate(zip(f, c))]
        word = len(f[0] & HINT_WORD) > 0 and len(c[0] & HINT_WORD) > 0 and f[0] & HINT_WORD != c[0] & HINT_WORD
        diffs[0] += not word
        ok = len(f) == len(c) - 1 or len(f) <= len(c)
        ok = ok and not any(diffs)
        bad += not ok
        print('  %s %s %s %s  screens %d / %d, pixels different per screen %s  %s' % (tuple(v for _, v in inp) + (len(f), len(c), diffs,
              'OK' if ok else 'DIFFERENT')))
    print('== Free42 NAVLITTLE against the C47 NAVLITTLE v2.0.0 (tests/test_f42_little.py)')
    r = subprocess.run([sys.executable, os.path.join(ROOT, 'tests', 'test_f42_little.py')], capture_output=True, text=True, timeout=3600)
    print('  ' + '\n  '.join(r.stdout.strip().split('\n')[-4:]))
    bad += r.returncode != 0
    return bad


def f42_exits():
    """Free42 NAVFULL: every page goes back to the menu with + (SKY and ANIM too, which run until a key): a + is
    queued 4 s after the key of SKY and ANIM (pressed after the others), then 0 ends NAV. A page that misses the + keeps f42run running: timeout."""
    if not os.path.exists(F42):
        return 0
    print('\n== Free42 NAVFULL: + back to the menu from every page, then 0')
    bad = 0
    for p in (1, 2, 3, 4, 5, 6):
        cmd = ['paste %s/build/free42/NAVINIT_FAST.txt' % ROOT, 'paste %s/build/free42/NAVFULL.txt' % ROOT, 'xeq INIT',
               'xeq NAV'] + ['num ' + v for _, v in INPUTS] + (
              ['qkey %d 4000' % F42KEY['+'], 'key %d' % F42KEY[p]] if p in (3, 4) else       # SKY, ANIM: + while they run
              ['key %d' % F42KEY[p], 'key %d' % F42KEY['+']]) + ['key %d' % F42KEY[0], 'stack']
        try:
            o = subprocess.run([F42], input='\n'.join(cmd) + '\n', text=True, capture_output=True, timeout=180).stdout
            ok = 'running 0' in o
        except subprocess.TimeoutExpired:
            ok = False
        bad += not ok
        print('  page %d  %s' % (p, 'menu, then the end' if ok else 'NO WAY BACK (+ not seen)'))
    return bad


def f42_registers():
    if not os.path.exists(F42):
        return 0
    print('\n== Free42: SIZE 25 and R00-R24 set before NAV, the same after it (NAVFULL, NAVLITTLE)')
    bad = 0
    t = tempfile.mkdtemp()
    setp = os.path.join(t, 'set.txt')
    prog = ['LBL "TSET"', '25', 'SIZE'] + [x for r in range(25) for x in ('%d.5' % (100 + r), 'STO %02d' % r)] + \
           ['RTN', 'LBL "TCHK"', 'RCL "REGS"', 'DIM?', 'RTN', 'END']          # Y: the rows of REGS = SIZE
    open(setp, 'w').write('\n'.join(prog) + '\n')
    for name, init, nkeys in (('NAVFULL', 'NAVINIT_FULL', ['key 29', 'key 37', 'key 34']), ('NAVLITTLE', 'NAVINIT_LITTLE', ['key 37'])):
        cmd = ['paste %s/build/free42/%s.txt' % (ROOT, init), 'paste %s/build/free42/%s.txt' % (ROOT, name), 'paste ' + setp,
               'xeq INIT', 'xeq TSET', 'xeq NAV'] + ['num ' + v for _, v in INPUTS] + nkeys + ['regs 0 24', 'xeq TCHK', 'stack']
        r = subprocess.run([F42], input='\n'.join(cmd) + '\n', text=True, capture_output=True, timeout=1800)
        o = r.stdout
        vals = re.findall(r'^R(\d\d)\s+([-0-9.]+)', o, re.M)
        got = {int(k): float(v) for k, v in vals}
        ok_regs = all(abs(got.get(rr, -1) - (100 + rr + 0.5)) < 1e-9 for rr in range(25))
        size = re.findall(r'Y: ([0-9.]+)', o)
        ok_size = bool(size) and float(size[-1]) == 25
        bad += not (ok_regs and ok_size)
        print('  %-9s registers R00-R24 %s, SIZE after NAV %s' % (name, 'as before' if ok_regs else 'CHANGED %s' % got,
              size[-1] if size else '?'))
    return bad


def main():
    bad = c47_vs_v110()
    bad += dm42_vs_v110()
    bad += f42_vs_c47()
    bad += f42_exits()
    bad += f42_registers()
    print('\n%d differences' % bad)
    sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()
