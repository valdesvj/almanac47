#!/usr/bin/env python3
"""The almanac tables (TBL_1, TBL_5) on Free42 against the C47, pixel by pixel:
f42run (tools/f42: the Free42 core with the DM42 screen) against the C47 simulator.
NAVFULL: the ALMANAC view (1 on the menu) against NAVFULL_T21; NAVLITTLE: its ALMANAC screen
against t21sim.little_programs() (the screens of Oct 2026, as Free42 draws them). With the tables
the screens show T (flag 10 set by TBL).     python3 tests/test_f42_tables.py"""
import os, sys, subprocess, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [os.path.join(ROOT, 'python'), os.path.join(ROOT, 'tests')]
import c47sim
import t21sim
from decimal import Decimal as D
F42 = os.path.join(ROOT, 'tools', 'f42', 'f42run')
CASES = (('TBL_1', '2027.0315', '3.30', '-33.54', '18.25'), ('TBL_1', '2026.1203', '21.45', '25.20', '55.12'),
         ('TBL_5', '2030.0704', '12.10', '60.10', '-5.00'))


def f42(nav, init, tbl, date, utc, lat, lon, full):
    t = tempfile.mkdtemp()
    cmd = ['paste %s/build/free42/%s.txt' % (ROOT, init), 'paste %s/build/free42/%s.txt' % (ROOT, tbl),
           'paste %s/build/free42/%s.txt' % (ROOT, nav), 'xeq INIT', 'xeq TBL', 'xeq NAV',
           'num ' + date, 'num ' + utc, 'num ' + lat, 'num ' + lon]
    cmd += (['key 29'] if full else []) + ['shot %s/s.pbm' % t]
    subprocess.run([F42], input='\n'.join(cmd) + '\n', text=True, capture_output=True, timeout=900)
    rows = open('%s/s.pbm' % t).read().split('\n')[2:242]
    return {(x, y) for y, r in enumerate(rows) for x, c in enumerate(r) if c == '1'}


def split(path):
    progs, cur = [], []
    for l in open(path, encoding='utf-8').read().split('\n'):
        if not l.strip():
            continue
        cur.append(l)
        if l == 'END':
            progs.append(cur); cur = []
    return progs


def c47(nav, init, tbl, date, utc, lat, lon, full):
    t = tempfile.mkdtemp(); files = []
    for i, pr in enumerate(split(init) + split(tbl) + (split(nav) if full else t21sim.little_programs())):
        f = os.path.join(t, 'p%d.txt' % i); open(f, 'w').write('\n'.join(pr) + '\n'); files.append(f)
    c = c47sim.load(files); c.flags.add(82)
    c.run('INIT', maxsteps=10 ** 7); c.flags.add(81); c.run('TBL', maxsteps=10 ** 8)
    for k, v in (('DATE', date), ('UTC', utc), ('LAT', lat), ('LON', lon)):
        c.reg[k] = D(v)
    c.s = [D(0)] * 4; c.frames = []; c.pix = []
    c.keys = [72, 85, 82] if full else [85]              # 1 (ALMANAC), then +, 0 ends / + ends NAVLITTLE
    c.run('NAV', maxsteps=10 ** 8)
    f = c.frames[1] if full else c.frames[0]              # NAVFULL: the menu, then the view
    return {(x, 239 - y) for y, x in f if 0 <= x < 400 and 0 <= y < 240}, 10 in c.flags


bad = 0
for tbl, date, utc, lat, lon in CASES:
    for name, init, full in (('NAVFULL', 'NAVINIT_FAST', True), ('NAVLITTLE', 'NAVINIT_LITTLE', False)):
        a = f42(name, init, tbl, date, utc, lat, lon, full)
        cinit = os.path.join(ROOT, 'build', init + '.txt') if full else os.path.join(ROOT, 'build', 'dm42', init + '.txt')
        cnav = os.path.join(ROOT, 'build', 'atext', 'NAVFULL_T21.txt') if full else None
        b, f10 = c47(cnav, cinit, os.path.join(ROOT, 'build', tbl + '.txt'), date, utc, lat, lon, full)
        same = a == b
        bad += not same
        print('%-9s %s %s %s UT: Free42 = C47: %s | flag 10: %s | pixels %d' % (name, tbl, date, utc, same, f10, len(a)))
        if not same:
            print('   only Free42', sorted(a - b)[:8], 'only C47', sorted(b - a)[:8])
print('%d differences' % bad)
sys.exit(1 if bad else 0)
