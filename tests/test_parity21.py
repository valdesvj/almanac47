#!/usr/bin/env python3
"""test_parity21.py - the native PC screens of the new C47 views (python/native/c47screen21.py)
against NAVFULL_T21 run in the simulator, pixel for pixel.
    python3 tests/test_parity21.py [VIEW ...] [-n CASES]"""
import os, sys, random, time
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [os.path.join(ROOT, 'tests'), os.path.join(ROOT, 'python', 'native'), os.path.join(ROOT, 'python')]
import t21sim
import c47screen as S
import c47screen21 as N
from c47view import jd

args = [a for a in sys.argv[1:] if not a.startswith('-')]
n = int(sys.argv[sys.argv.index('-n') + 1]) if '-n' in sys.argv else 3
views = [a for a in args if a in N.VIEWS] or list(N.VIEWS)
random.seed(47)
cases = [(2026, 9, 26, 14 + 57 / 60, 25 + 20 / 60, 55.2), (2026, 10, 2, 18.0, -33.9, 18.4), (2027, 3, 5, 5.5, 48.85, -4.3)]
while len(cases) < n:
    cases.append((random.choice((2026, 2027, 2028, 2029)), random.randint(1, 12), random.randint(1, 28),
                  random.randint(0, 23) + random.randint(0, 59) / 60, round(random.uniform(-65, 65) * 60) / 60,
                  round(random.uniform(-179, 179) * 60) / 60))
bad = 0
for v in views:
    for case in cases[:n]:
        t0 = time.time()
        ref = t21sim.frames(v, case, keyskip=True, maxpauses=12) if v == 'SKY' else t21sim.frames(v, case)
        al = S.Almanac(jd(*case[:4]), case[4], case[5])
        mine = N.VIEWS[v](al)
        k = len(ref) if v != 'SKY' else len(mine)
        diffs = [len(ref[i] ^ mine[i]) for i in range(min(len(ref), len(mine), k))]
        ok = len(ref) >= len(mine) and not any(diffs)
        bad += not ok
        print('%-8s %s frames %d/%d diff %s %s (%.0f s)' % (v, case, len(mine), len(ref), diffs[:6], 'OK' if ok else 'DIFFERENT', time.time() - t0))
print('%d different' % bad)
sys.exit(1 if bad else 0)
