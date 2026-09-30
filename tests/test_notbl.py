#!/usr/bin/env python3
"""NAVFULL_NOTBL (no almanac tables) vs NAVFULL, both in the simulator without tables:
every view must give the same pixels / PROMPT text; also prints the steps saved.
  python3 tests/test_notbl.py [cases] [seed] [F]      F = FAST matrices (NAVINIT_FAST)"""
import os, random, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [os.path.join(ROOT, 'python'), os.path.join(ROOT, 'python', 'native')]
import c47sim
from c47pc import jd
from decimal import Decimal as D


def split(path):
    progs, cur = [], []
    for l in open(path, encoding='utf-8').read().split('\n'):
        if not l.strip():
            continue
        cur.append(l)
        if l == 'END':
            progs.append(cur); cur = []
    return progs


def load(paths):
    tmp = tempfile.mkdtemp(); files = []
    for p in paths:
        for i, pr in enumerate(split(os.path.join(ROOT, p))):
            f = os.path.join(tmp, '%s_%d.txt' % (os.path.basename(p), i))
            open(f, 'w').write('\n'.join(pr) + '\n'); files.append(f)
    c = c47sim.load(files)
    c.run('INIT', maxsteps=10 ** 7)
    return c


def run(c, view, j, la, lo, answers=None, pauses=None, prompts=None):
    c.steps = 0; c.pix = []; c.frames = []; c.msgs = []; c.s = [D(0)] * 4; c.lift = True
    c.answers = list(answers or []); c.maxpauses = pauses; c.maxprompts = prompts if prompts else 10 ** 9
    c.keys = [85] if view == 'BODY' else []; c.keyskip = (view == 'HORZ')
    for v in (j, la, lo):
        c.push(D(repr(v)))
    try:
        c.run(view, maxsteps=10 ** 8)
    except StopIteration:
        pass
    return (sorted(c.pix), [sorted(f) for f in c.frames], [str(m) for m in c.msgs]), c.steps


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 4
    random.seed(int(sys.argv[2]) if len(sys.argv) > 2 else 1)
    fast = len(sys.argv) > 3 and 'F' in sys.argv[3].upper()
    init = 'build/NAVINIT_FAST.txt' if fast else 'build/NAVINIT_FULL.txt'
    a = load([init, 'build/dev/src/NAVFULL.txt'])
    b = load([init, 'build/dev/src/NAVFULL_NOTBL.txt'])
    bad = 0; saved = {}
    for k in range(n):
        y = random.randint(2025, 2032) if fast else random.randint(2025, 2050)
        j = jd(y, random.randint(1, 12), random.randint(1, 28), random.uniform(0, 24))
        la = random.uniform(-65, 65); lo = random.uniform(-180, 180)
        code = random.choice([60, 61, 62, 63, 64, 65, random.randint(1, 58)])
        cases = [('ALMF', {}), ('HALMV', {}), ('HALMH', {}), ('HORZ', {'pauses': 3})]
        for view, kw in cases:
            ra, sa = run(a, view, j, la, lo, **kw)
            rb, sb = run(b, view, j, la, lo, **kw)
            saved.setdefault(view, []).append(sa - sb)
            if ra != rb:
                bad += 1; print('DIFF', view, y, round(la, 2), round(lo, 2))
    for v, s in saved.items():
        print('  %-6s steps saved per screen: %d' % (v, max(s)))
    print('%d cases x %d views%s, %d differences' % (n, len(saved), ' (FAST)' if fast else '', bad))
    sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()
