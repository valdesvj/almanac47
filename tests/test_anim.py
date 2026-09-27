#!/usr/bin/env python3
"""HANIM (animation of the Sun and the Moon on the horizon chart): calculator program in the
simulator vs native Python, frame by frame, pixel for pixel. Also prints the steps and
trigonometric functions per frame (time estimate for the C47).
  python3 tests/test_anim.py [cases] [seed]"""
import os, random, sys, time
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [os.path.join(ROOT, 'python'), os.path.join(ROOT, 'python', 'native')]
from c47view import Engine, jd, W, H
import c47screen as S
import c47sim


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 4
    random.seed(int(sys.argv[2]) if len(sys.argv) > 2 else 1)
    cases = [(2026, 9, 27, 14.0, 25.2, 55.3), (2026, 12, 3, 16.0, -33.9, 18.4)]
    while len(cases) < n:
        cases.append((random.randint(2025, 2030), random.randint(1, 12), random.randint(1, 28),
                      round(random.uniform(0, 24), 3), round(random.uniform(-70, 70), 3), round(random.uniform(-180, 180), 3)))
    E = Engine(os.path.join(ROOT, 'programs')); c = E.c
    ntrig = [0]
    orig = c47sim.Calc.trig
    def trig(self, fn, x):
        ntrig[0] += 1
        return orig(self, fn, x)
    c47sim.Calc.trig = trig
    bad = 0
    for (y, m, d, h, la, lo) in cases[:n]:
        j = jd(y, m, d, h)
        E._start(j, la, lo); c.maxpauses = 24; ntrig[0] = 0
        try:
            c.run('HANIM', maxsteps=10 ** 8)
        except StopIteration:
            pass
        got = [{(x, H - 1 - yy) for yy, x in fr if 0 <= x < W and 0 <= yy < H} for fr in c.frames[:24]]
        want, _ = S.hanim(j, la, lo, 24, 0.5)
        diff = [k for k in range(24) if k >= len(got) or got[k] != want[k]]
        if diff:
            bad += 1
            print('DIFF', (y, m, d, h, la, lo), 'frames', diff)
        print('  %s  steps %d (%.0f per frame)  trig %d' % ((y, m, d, h, la, lo), c.steps, c.steps / 24, ntrig[0]))
    print('%d cases x 24 frames, %d differences' % (n, bad))
    sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()
