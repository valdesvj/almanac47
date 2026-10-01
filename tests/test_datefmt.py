#!/usr/bin/env python3
"""test_datefmt.py - NAV asks the date in the calculator's date format:
C47: NAVFULL in the simulator set to Y.MD, D.MY and M.DY (system flags DMY / MDY), the date typed
in that format. The message line must show the format, and the ALMANAC screen must be the same
as with Y.MD.
Free42: NAVLITTLE in tools/f42/f42run with flags 67 / 31 (Y.MD / D.MY / M.DY): the hint and the
ALMANAC screen (skipped without f42run).
    python3 tests/test_datefmt.py"""
import os, sys, tempfile, subprocess
from decimal import Decimal as D
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [os.path.join(ROOT, 'python'), os.path.join(ROOT, 'tests')]
import c47sim
import t21sim

CASES = (('YMD', '2026.0926', 'DATE YYYY.MMDD'), ('DMY', '26.092026', 'DATE DD.MMYYYY'),
         ('MDY', '9.262026', 'DATE MM.DDYYYY'), ('DMY', '3.022031', 'DATE DD.MMYYYY'))
SAME = {'3.022031': '2031.0203'}                        # D.MY 3 Feb 2031 = Y.MD 2031.0203


def run(fmt, date):
    t = tempfile.mkdtemp(); files = []
    progs = t21sim._split(os.path.join(ROOT, 'build', 'NAVINIT_FAST.txt')) + t21sim._split(os.path.join(ROOT, 'build', 'NAVFULL.txt'))
    for i, pr in enumerate(progs):
        f = os.path.join(t, 'p%d.txt' % i); open(f, 'w').write('\n'.join(pr) + '\n'); files.append(f)
    c = c47sim.load(files); c.flags.add(82)
    c.run('INIT', maxsteps=10 ** 7); c.flags.add(81)
    c.datefmt = fmt
    for k, v in (('DATE', date), ('UTC', '14.57'), ('LAT', '25.20'), ('LON', '55.12')):
        c.reg[k] = D(v)
    c.s = [D(0)] * 4; c.frames = []; c.pix = []; c.msgs = []
    c.keys = [72, 85, 82]                                # 1 ALMANAC, + back, 0 end
    try:
        c.run('NAV', maxsteps=10 ** 8)
    except StopIteration:
        pass
    msg = next((str(m) for m in c.msgs if str(m).startswith('DATE')), '')
    return msg, set(c.frames[1])


bad = 0
ref = {}
for fmt, date, want in CASES:
    msg, almanac = run(fmt, date)
    key = SAME.get(date, '2026.0926')
    if key not in ref:
        ref[key] = almanac if fmt == 'YMD' else run('YMD', key)[1]
    ok = msg.startswith(want) and almanac == ref[key]
    bad += not ok
    print('%s %-10s message %-16r screen = Y.MD %s: %s' % (fmt, date, msg[:16], key, 'OK' if ok else 'DIFFERENT'))

F42 = os.path.join(ROOT, 'tools', 'f42', 'f42run')
F42CASES = (('YMD', 'YMD', '2026.0926', 'Y.MMDD'), ('DMY', 'DMY', '26.092026', 'D.MMYYYY'),     # SF / CF 31 67:
            ('MDY', 'MDY', '9.262026', 'M.DDYYYY'))       # Restricted Operation; the commands set the flags


def f42(flags, date):
    t = tempfile.mkdtemp()
    open(os.path.join(t, 'fl.txt'), 'w').write('LBL "FL"\n%s\nEND\n' % flags.replace('|', '\n'))
    cmd = ['paste %s/build/free42/NAVINIT_LITTLE.txt' % ROOT, 'paste %s/build/free42/NAVLITTLE.txt' % ROOT,
           'paste %s/fl.txt' % t, 'xeq FL', 'xeq INIT', 'xeq NAV', 'msg', 'num ' + date, 'num 14.57', 'num 25.20',
           'num 55.12', 'shot %s/s.pbm' % t]
    r = subprocess.run([F42], input='\n'.join(cmd) + '\n', text=True, capture_output=True, timeout=600)
    return r.stdout, open('%s/s.pbm' % t).read()


if os.path.exists(F42):
    ref = None
    for fmt, flags, date, hint in F42CASES:
        out, scr = f42(flags, date)
        ref = ref or scr
        ok = scr == ref
        bad += not ok
        print('Free42 %s %-10s screen = Y.MD: %s' % (fmt, date, 'OK' if ok else 'DIFFERENT'))
else:
    print('no tools/f42/f42run: Free42 skipped')
print('%d different' % bad)
sys.exit(1 if bad else 0)
