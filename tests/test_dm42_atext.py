#!/usr/bin/env python3
"""The DM42 builds with ATEXT (build/dm42/NAVLITTLE, dev/NAV1T_DM42, dev/NAV12_DM42): the ATEXT steps
(PTXS; NAV12 also PTTY for the tinyFont of its chart), no Moon, each runs in the simulator (NAV12: menu,
ALMANAC, CHART), and the strings given to ATEXT, put together row by row, show the page (the first
rows of NAVLITTLE are printed).
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
for name, keys, atx in (('NAVLITTLE', [85], 1), ('dev/NAV1T_DM42', [85], 1), ('dev/NAV12_DM42', [72, 85, 73, 85, 82], 2)):
    path = os.path.join(DM, name + '.txt')
    n = sum(1 for l in open(path, encoding='utf-8') if l.startswith('ATEXT '))
    c, texts = run(path, keys, spy=True)
    rows = {}
    for r, x, s in texts:
        rows.setdefault(r, []).append((x, s))
    table = [' '.join(s for x, s in sorted(v)) for r, v in sorted(rows.items(), reverse=True)]
    ok = n == atx and not any('MOON' in t for t in table) and c.frames and any('FOMALHAUT' in t for t in table) and any('299.6' in t for t in table)
    bad += not ok
    print('%-14s ATEXT steps %d, %d texts, %d screens, %d steps: %s' % (name, n, len(texts), len(c.frames), c.steps,
                                                                     'OK' if ok else 'FAILED'))
    if name == 'NAVLITTLE':
        print('   ' + '\n   '.join(table[:6]))
print('%d failed' % bad)
