#!/usr/bin/env python3
"""Parity test: the native Python version must draw exactly what the C47 programs draw.

Runs the real calculator programs (programs/*.txt) in the simulator (python/c47sim.py)
and the native Python version (python/native/) for random dates and places, and
compares every screen pixel for pixel (ALMF, HALMV, HORZ frames, HORZS) and every
ALMT text line.

    python3 tests/test_parity.py            # 12 cases
    python3 tests/test_parity.py 60 7       # 60 cases, random seed 7
    python3 tests/test_parity.py 20 1 T     # with the almanac tables (TBL loaded, flag 10)
"""
import os, random, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'python'))
sys.path.insert(0, os.path.join(ROOT, 'python', 'native'))
from c47view import Engine, jd          # simulator of the C47 programs
import c47screen as S                   # native Python version
import c47tables

VIEWS = ['ALMF', 'HALMV', 'HORZ', 'HORZS']


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 12
    seed = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    tables = len(sys.argv) > 3 and sys.argv[3].upper().startswith('T')
    random.seed(seed)
    cases = [(2026, 9, 25, 18.5, 25 + 20 / 60, 55.2),       # Dubai, Sun below the horizon
             (2026, 9, 23, 9.0, -33.9, 18.4),               # Cape Town, south
             (2026, 3, 1, 6.0, 40.0, -10.0)]                # whole-degree longitude (equator dot on the horizon)
    tb = None
    if tables:                                  # dates in and around the table period
        tb = c47tables.Tables(os.path.join(ROOT, 'programs', 'TBL.txt'))
        cases = [(2026, 9, 25, 18.5, 25 + 20 / 60, 55.2), (2026, 11, 23, 9.0, -33.9, 18.4),
                 (2027, 2, 5, 12.0, 40.0, -10.0)]
        import datetime
        while len(cases) < n:
            d = datetime.date(2026, 9, 20) + datetime.timedelta(days=random.randint(0, 140))
            cases.append((d.year, d.month, d.day, round(random.uniform(0, 24), 3),
                          round(random.uniform(-72, 72), 3), round(random.uniform(-180, 180), 3)))
    while len(cases) < n:
        cases.append((random.choice([2025, 2026, 2027, 2028]), random.randint(1, 12), random.randint(1, 28),
                      round(random.uniform(0, 24), 3), round(random.uniform(-72, 72), 3),
                      round(random.uniform(-180, 180), 3)))
    eng = Engine(os.path.join(ROOT, 'programs'), tables=tables)
    bad = 0; t0 = time.time()
    for (y, m, d, h, la, lo) in cases[:n]:
        j = jd(y, m, d, h)
        al = S.Almanac(j, la, lo, tb)
        for v in VIEWS:
            ref, _ = eng.screen(v, j, la, lo)
            mine = [f for f in S.VIEWS[v](al)]
            if ref != mine:
                bad += 1
                print('DIFF %-5s %s' % (v, (y, m, d, h, la, lo)))
        ref, _ = eng.text(j, la, lo)
        if ref != S.almt(al):
            bad += 1
            print('DIFF ALMT  %s' % ((y, m, d, h, la, lo),))
    print('%d cases%s, %d differences (%.0f s)' % (n, ' with tables' if tables else '', bad, time.time() - t0))
    sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()
