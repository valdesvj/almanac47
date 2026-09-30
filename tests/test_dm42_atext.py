#!/usr/bin/env python3
"""The EXPERIMENTAL DM42 builds with ATEXT (build/dm42/atext): each has one ATEXT step (in PTXS),
runs in the simulator (NAV12: menu, ALMANAC, CHART), and the strings given to ATEXT, put
together row by row, show the page (the first rows of NAVLITTLE_ATX are printed).
    python3 tests/test_dm42_atext.py"""
import os, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'python'))
import c47sim
from decimal import Decimal as D
DM = os.path.join(ROOT, 'build', 'dm42')


def split(path):
    progs, cur = [], []
    for l in open(path, encoding='utf-8').read().split('\n'):
        if not l.strip():
            continue
        cur.append(l)
        if l == 'END':
            progs.append(cur); cur = []
    return progs


def run(nav, keys, spy=None):
    t = tempfile.mkdtemp(); files = []
    for i, pr in enumerate(split(os.path.join(DM, 'NAVINIT_LITTLE.txt')) + split(nav)):
        f = os.path.join(t, 'p%d.txt' % i); open(f, 'w').write('\n'.join(pr) + '\n'); files.append(f)
    c = c47sim.load(files); c.flags.add(82)
    c.run('INIT', maxsteps=10 ** 7); c.flags.add(81)
    for k, v in (('DATE', '2026.1002'), ('UTC', '18.00'), ('LAT', '25.12'), ('LON', '55.18')):
        c.reg[k] = D(v)
    c.s = [D(0)] * 4; c.frames = []; c.pix = []; c.keys = list(keys)
    texts = []
    if spy:
        at = c.atext
        c.atext = lambda s: (texts.append((int(c.s[1]) + 4, int(c.s[0]), str(s))), at(s))[1]
    try:
        c.run('NAV', maxsteps=10 ** 8)
    except StopIteration:
        pass
    return c, texts


bad = 0
for name, keys in (('NAVLITTLE_ATX', [85]), ('NAV1T_ATX', [85]), ('NAV12_ATX', [72, 85, 73, 85, 82])):
    path = os.path.join(DM, 'atext', name + '.txt')
    n = sum(1 for l in open(path, encoding='utf-8') if l.startswith('ATEXT '))
    c, texts = run(path, keys, spy=True)
    rows = {}
    for r, x, s in texts:
        rows.setdefault(r, []).append((x, s))
    table = [' '.join(s for x, s in sorted(v)) for r, v in sorted(rows.items(), reverse=True)]
    ok = n == 1 and c.frames and any('FOMALHAUT' in t for t in table) and any('299.6' in t for t in table)
    bad += not ok
    print('%-14s ATEXT steps %d, %d texts, %d screens, %d steps: %s' % (name, n, len(texts), len(c.frames), c.steps,
                                                                     'OK' if ok else 'FAILED'))
    if name == 'NAVLITTLE_ATX':
        print('   ' + '\n   '.join(table[:6]))
print('%d failed' % bad)
