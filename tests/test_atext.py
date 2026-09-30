#!/usr/bin/env python3
"""ATEXT in the simulator (python/c47sim.py, font python/stdfont.py) against the C47: the
ATEXTing demonstration (tests/data/ATEXTing.txt) and its screen on the calculator
(tests/data/ATEXTing_C47.png, 400 x 240). Then the two ATEXT programs of extras/ run.
    python3 tests/test_atext.py"""
import os, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'python'))
import c47sim
from PIL import Image


def files(path):
    progs, cur = [], []
    for l in open(path, encoding='utf-8').read().split('\n'):
        if not l.strip():
            continue
        cur.append(l)
        if l == 'END':
            progs.append(cur); cur = []
    t = tempfile.mkdtemp(); out = []
    for i, p in enumerate(progs):
        f = os.path.join(t, 'p%d.txt' % i); open(f, 'w').write('\n'.join(p) + '\n'); out.append(f)
    return out


def run(path, label, keys=()):
    c = c47sim.load(files(path)); c.ws = 64; c.keys = list(keys); c.steps = 0
    try:
        c.run(label, maxsteps=10 ** 7)
    except StopIteration:
        pass
    return c


c = run(os.path.join(ROOT, 'tests', 'data', 'ATEXTing.txt'), 'ATDEMO')
sim = {(x, 239 - y) for y, x in c.frames[-1] if 0 <= x < 400 and 0 <= y < 240}
im = Image.open(os.path.join(ROOT, 'tests', 'data', 'ATEXTing_C47.png')).convert('L'); px = im.load()
real = {(x, y) for x in range(400) for y in range(240) if px[x, y] < 128}
print('ATEXTing: %d pixels on the C47, %d the same in the simulator, %d only in the simulator'
      % (len(real), len(real & sim), len(sim - real)))
c = run(os.path.join(ROOT, 'extras', 'C64_ATEXT.txt'), 'C64', keys=[0, 0, 0, 0, 11])
print('C64_ATEXT: %d steps, %d screens, ends cleared: %s' % (c.steps, len(c.frames), not c.pix))
c = run(os.path.join(ROOT, 'extras', 'DEMOATX.txt'), 'DEMO')
print('DEMOATX: %d steps, %d pixels on the page' % (c.steps, len(c.frames[-1])))
