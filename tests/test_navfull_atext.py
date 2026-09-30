#!/usr/bin/env python3
"""EXPERIMENTAL NAVFULL_ATX (build/atext): one ATEXT step (in PTXS), the small font only on the charts,
and every view runs in the simulator: menu, 1 ALMANAC, 2 CHART, 4 SKY, 5 SPLIT, 6 ANIM,
7 ALLSKY, 8 INFO (no SMALL). The texts given to ATEXT are checked for a few values of the page.
    python3 tests/test_navfull_atext.py"""
import os, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'python'))
import c47sim
from decimal import Decimal as D
NAV = os.path.join(ROOT, 'build', 'atext', 'NAVFULL_ATX.txt')
INIT = os.path.join(ROOT, 'build', 'NAVINIT_FAST.txt')


def split(path):
    progs, cur = [], []
    for l in open(path, encoding='utf-8').read().split('\n'):
        if not l.strip():
            continue
        cur.append(l)
        if l == 'END':
            progs.append(cur); cur = []
    return progs


def run(keys):
    t = tempfile.mkdtemp(); files = []
    for i, pr in enumerate(split(INIT) + split(NAV)):
        f = os.path.join(t, 'p%d.txt' % i); open(f, 'w').write('\n'.join(pr) + '\n'); files.append(f)
    c = c47sim.load(files); c.flags.add(82)
    c.run('INIT', maxsteps=10 ** 7); c.flags.add(81)
    for k, v in (('DATE', '2026.1002'), ('UTC', '18.00'), ('LAT', '25.12'), ('LON', '55.18')):
        c.reg[k] = D(v)
    c.s = [D(0)] * 4; c.frames = []; c.pix = []; c.keys = list(keys)
    texts = []
    at = c.atext
    c.atext = lambda s: (texts.append(str(s)), at(s))[1]
    try:
        c.run('NAV', maxsteps=10 ** 8)
    except StopIteration:
        pass
    return c, ' '.join(texts)


L = open(NAV, encoding='utf-8').read().split('\n')
n = sum(1 for l in L if l.startswith('ATEXT '))
warn = sum(1 for l in L if 'DOES NOT REPLACE' in l or 'NOT FOR NAVIGATION' in l)
print('ATEXT steps %d, warning lines %d (menu, INFO, TEXT page)' % (n, warn))
bad = (n != 1) + (warn != 3)            # menu, INFO and the TEXT page (ALMR, in the registers)
# menu 1 ALMANAC 2 CHART 3 TEXT 4 SKY 5 SPLIT 6 ANIM 7 ALLSKY 8 INFO (no SMALL): keys 72 73 74 62 63 64 52 53
CHECK = {None: ('1 ALMANAC', '5 SPLIT', '8 INFO', 'VALID '), 72: ('FOMALHAUT', '299.6', 'WANING'), 73: ('BODY', 'HAMAL'),
         62: ('SUN', '  ZN ', ' UT'), 63: ('FOMALHAUT', 'MIRFAK'), 64: ('24', 'DAY'), 52: ('NIGHT',),
         53: ('ALMANAC 47 - INFO', '+ MENU')}
NOT = {None: ('SMALL',), 73: ('ARIES', 'MOON '), 63: ('RISE', 'TWI')}
for k, want in CHECK.items():
    c, txt = run([82] if k is None else [k, 85, 82])
    ok = all(w in txt for w in want) and not any(w in txt for w in NOT.get(k, ())) and c.frames
    bad += not ok
    print('%-5s %2d screens %6d steps: %s' % (k or 'menu', len(c.frames), c.steps, 'OK' if ok else 'FAILED %s' % [w for w in want if w not in txt]))
print('%d failed' % bad)
