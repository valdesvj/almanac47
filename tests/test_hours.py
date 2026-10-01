#!/usr/bin/env python3
"""test_hours.py - UP / DOWN (one hour later / earlier) give the same screen as NAV started at
that hour, in the three date formats and across midnight, a month end and a year end.
C47: NAVLITTLE (build/dm42) in the simulator (date format Y.MD / D.MY / M.DY); Free42:
NAVLITTLE and the NAVFULL ALMANAC view in tools/f42/f42run (YMD / DMY / MDY; skipped without it).
    python3 tests/test_hours.py"""
import os, sys, subprocess, tempfile, datetime
from decimal import Decimal as D
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [os.path.join(ROOT, 'python'), os.path.join(ROOT, 'tests')]
import c47sim
import t21sim

F42 = os.path.join(ROOT, 'tools', 'f42', 'f42run')
# start (UT): one hour later / earlier crosses the day, the month, the year
STARTS = (datetime.datetime(2026, 9, 26, 14, 57), datetime.datetime(2026, 9, 30, 23, 30),
          datetime.datetime(2026, 12, 31, 23, 15), datetime.datetime(2027, 1, 1, 0, 40))
POS = ('25.20', '55.12')


def date_in(t, fmt):
    if fmt == 'YMD':
        return '%04d.%02d%02d' % (t.year, t.month, t.day)
    a, b = (t.day, t.month) if fmt == 'DMY' else (t.month, t.day)
    return '%d.%02d%04d' % (a, b, t.year)


def ut_in(t):
    return '%d.%02d' % (t.hour, t.minute)


# ---- C47 NAVLITTLE in the simulator: frames at the start, after UP, DOWN, DOWN
def c47(t, fmt, keys):
    d = tempfile.mkdtemp(); files = []
    progs = (t21sim._split(os.path.join(ROOT, 'build', 'dm42', 'NAVINIT_LITTLE.txt'))
             + t21sim._split(os.path.join(ROOT, 'build', 'dm42', 'NAVLITTLE.txt')))
    for i, pr in enumerate(progs):
        f = os.path.join(d, 'p%d.txt' % i); open(f, 'w').write('\n'.join(pr) + '\n'); files.append(f)
    c = c47sim.load(files); c.flags.add(82)
    c.run('INIT', maxsteps=10 ** 7); c.flags.add(81)
    c.datefmt = fmt
    for k, v in (('DATE', date_in(t, fmt)), ('UTC', ut_in(t)), ('LAT', POS[0]), ('LON', POS[1])):
        c.reg[k] = D(v)
    c.s = [D(0)] * 4; c.frames = []; c.pix = []; c.keys = keys
    c.run('NAV', maxsteps=10 ** 8)
    return [set(f) for f in c.frames]


# ---- Free42 in f42run: NAVLITTLE (screen at once) or NAVFULL (1 = ALMANAC first)
F42KEYS = {'UP': 'key 18', 'DOWN': 'key 23'}


def f42(t, fmt, nav, steps):
    d = tempfile.mkdtemp()
    open(os.path.join(d, 'fl.txt'), 'w').write('LBL "FL"\n%s\nEND\n' % fmt)
    init = 'NAVINIT_LITTLE' if nav == 'NAVLITTLE' else 'NAVINIT_FAST'
    cmd = ['paste %s/build/free42/%s.txt' % (ROOT, init), 'paste %s/build/free42/%s.txt' % (ROOT, nav),
           'paste %s/fl.txt' % d, 'xeq FL', 'xeq INIT', 'xeq NAV', 'num ' + date_in(t, fmt), 'num ' + ut_in(t),
           'num ' + POS[0], 'num ' + POS[1]] + (['key 29'] if nav == 'NAVFULL' else [])
    for k, s in enumerate(steps):
        cmd += ([F42KEYS[s]] if s else []) + ['shot %s/s%d.pbm' % (d, k)]
    subprocess.run([F42], input='\n'.join(cmd) + '\n', text=True, capture_output=True, timeout=900)
    return [open('%s/s%d.pbm' % (d, k)).read() for k in range(len(steps))]


bad = 0
H = datetime.timedelta(hours=1)
for t in STARTS:
    for fmt in ('YMD', 'DMY', 'MDY'):
        fr = c47(t, fmt, [51, 61, 61, 85])                   # UP, DOWN, DOWN, + ends
        up, down = c47(t + H, fmt, [85])[0], c47(t - H, fmt, [85])[0]
        ok = fr[1] == up and fr[3] == down and fr[2] == fr[0]
        bad += not ok
        print('C47    NAVLITTLE %s %s  +1 h = %s, -1 h = %s: %s' % (t, fmt, t + H, t - H, 'OK' if ok else 'DIFFERENT'))
        if not os.path.exists(F42):
            continue
        for nav in ('NAVLITTLE', 'NAVFULL'):
            a = f42(t, fmt, nav, [None, 'UP', 'DOWN', 'DOWN'])
            up, down = f42(t + H, fmt, nav, [None])[0], f42(t - H, fmt, nav, [None])[0]
            ok = a[1] == up and a[3] == down and a[2] == a[0]
            bad += not ok
            print('Free42 %-9s %s %s  +1 h, -1 h: %s' % (nav, t, fmt, 'OK' if ok else 'DIFFERENT'))
print('%d different' % bad)
sys.exit(1 if bad else 0)
