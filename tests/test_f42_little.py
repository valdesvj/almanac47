#!/usr/bin/env python3
"""Free42 NAVLITTLE (build/free42/) vs the same screens on the C47 pixel by pixel: f42run
(tools/f42, the Free42 core with the DM42 400 x 240 screen) against the C47 simulator running
the C47 NAVLITTLE (build/dm42/: no menu, the T21 ALMANAC view with Sun and stars and the Moon
line from the mean lunation, build_dm42.little_almf; Free42 has the same view).
ALMANAC screen at the start, after UP (one hour later) and after DOWN DOWN (one hour earlier),
then + ends.       python3 tests/test_f42_little.py   (needs tools/f42/f42run)"""
import os, sys, subprocess, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [os.path.join(ROOT, 'python'), os.path.join(ROOT, 'tests')]
import c47sim
import t21sim
from decimal import Decimal as D
F42 = os.path.join(ROOT, 'tools', 'f42', 'f42run')
CASES = (('2026.0926', '14.57', '25.20', '55.12'), ('2031.0315', '3.30', '-33.54', '18.25'),
         ('2045.1201', '22.10', '60.10', '-5.00'))


def f42_frames(date, utc, lat, lon):
    t = tempfile.mkdtemp()
    cmd = ['paste %s/build/free42/NAVINIT_LITTLE.txt' % ROOT, 'paste %s/build/free42/NAVLITTLE.txt' % ROOT,
           'xeq INIT', 'xeq NAV', 'num ' + date, 'num ' + utc, 'num ' + lat, 'num ' + lon, 'shot %s/s0.pbm' % t,
           'key 18', 'shot %s/s1.pbm' % t, 'key 23', 'key 23', 'shot %s/s2.pbm' % t, 'key 37', 'msg']
    r = subprocess.run([F42], input='\n'.join(cmd) + '\n', text=True, capture_output=True, timeout=600)
    out = []
    for k in range(3):
        rows = open('%s/s%d.pbm' % (t, k)).read().split('\n')[2:242]
        out.append({(x, y) for y, r in enumerate(rows) for x, c in enumerate(r) if c == '1'})
    return out, r.stdout


def split(path):
    progs, cur = [], []
    for l in open(path, encoding='utf-8').read().split('\n'):
        if not l.strip():
            continue
        cur.append(l)
        if l == 'END':
            progs.append(cur); cur = []
    return progs


def c47_frames(date, utc, lat, lon):
    t = tempfile.mkdtemp(); files = []
    for i, pr in enumerate(split(os.path.join(ROOT, 'build', 'dm42', 'NAVINIT_LITTLE.txt')) + t21sim.little_programs()):
        f = os.path.join(t, 'p%d.txt' % i); open(f, 'w').write('\n'.join(pr) + '\n'); files.append(f)
    c = c47sim.load(files); c.flags.add(82)
    c.run('INIT', maxsteps=10 ** 7)
    for k, v in (('DATE', date), ('UTC', utc), ('LAT', lat), ('LON', lon)):
        c.reg[k] = D(v)
    c.s = [D(0)] * 4; c.keys = [51, 61, 61, 85]; c.frames = []; c.pix = []
    c.run('NAV', maxsteps=10 ** 8)
    return [{(x, 239 - y) for y, x in f if 0 <= x < 400 and 0 <= y < 240} for f in c.frames]


bad = 0
for case in CASES:
    a, log = f42_frames(*case)
    b = c47_frames(*case)
    b = [b[0], b[1], b[3]]                  # b[2]: after the first DOWN (the start hour again)
    same = [a[k] == b[k] for k in range(3)]
    bad += same.count(False)
    print(case, 'ALMANAC start / +1 h / -1 h same as the C47:', same,
          '| pixels', [len(x) for x in a])
    for k in range(3):
        if a[k] != b[k]:
            print('   frame', k, 'only Free42:', sorted(a[k] - b[k])[:8], 'only C47:', sorted(b[k] - a[k])[:8])
print('%d differences' % bad)
sys.exit(1 if bad else 0)
