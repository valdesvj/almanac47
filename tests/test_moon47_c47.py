#!/usr/bin/env python3
"""MOON47 for the C47 (build/MOON47.txt, tools/build_moon47.py) in the simulator against the MOON47 page of
python/moon47.py (c47screen21.moon47_screen), pixel for pixel: the clock set to a few dates, north, and
south after the +/- key (43); another key ends.
  python3 tests/test_moon47_c47.py [N]"""
import os, random, sys, tempfile, time
from decimal import Decimal as D
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [os.path.join(ROOT, 'python'), os.path.join(ROOT, 'python', 'native'), os.path.join(ROOT, 'tests')]
import c47sim, moon47 as M47, c47screen21 as V
from t21sim import _split

PROG = os.path.join(ROOT, 'build', 'MOON47.txt')


def run(j, tz=None, keys=(43, 82)):
    """The frames of MOON47 with the clock at JD j (UT) + tz hours (local time)."""
    t = tempfile.mkdtemp(); files = []
    for i, pr in enumerate(_split(PROG)):
        f = os.path.join(t, 'p%d.txt' % i); open(f, 'w').write('\n'.join(pr) + '\n'); files.append(f)
    c = c47sim.load(files)
    c.clock = j + (tz or 0) / 24.0
    if tz is not None:
        c.reg['TZ'] = D(str(tz))
    c.s = [D(0)] * 4; c.frames = []; c.pix = []; c.keys = list(keys)
    c.run('MOON47', maxsteps=10 ** 8)
    return [{(x, 239 - y) for y, x in f if 0 <= y < 240 and 0 <= x < 400} for f in c.frames], c


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 4
    random.seed(4747)
    cases = [(M47.julian(2026, 10, 3, 12.0), None), (M47.julian(2026, 10, 10, 15.0), 4.0),
             (M47.julian(2027, 1, 22, 3.5), -5.0)]
    while len(cases) < n:
        cases.append((M47.julian(random.randint(2000, 2050), random.randint(1, 12), random.randint(1, 28),
                                 random.uniform(0, 24)), None))
    bad = 0
    for j, tz in cases[:n]:
        t0 = time.time()
        frames, c = run(j, tz)
        ref = [V.moon47_screen(j, False)[0], V.moon47_screen(j, True)[0]]
        diffs = [len(a ^ b) for a, b in zip(frames, ref)]
        ok = len(frames) == 2 and not any(diffs)
        bad += not ok
        d, m, y, h = M47.from_julian(j)
        print('%02d-%02d-%04d %05.2f h tz %-5s frames %d diff %s steps %d %s (%.0f s)' % (
            d, m, y, h, tz, len(frames), diffs, c.steps, 'OK' if ok else 'DIFFERENT', time.time() - t0))
    print('%d different' % bad)
    sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()
