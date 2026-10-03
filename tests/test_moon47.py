#!/usr/bin/env python3
"""MOON47 (python/moon47.py, the standalone formulas of every calculator version) against the full series of
NAV (python/native/c47astro.py: Meeus 47 + the DE421 corrections, the Sun from VSOP87), 2000-2050:
phase times and age within 5 minutes, HP within 0.05', SD within 0.02', lit within 0.2 %.
  python3 tests/test_moon47.py"""
import math, os, random, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [os.path.join(ROOT, 'python'), os.path.join(ROOT, 'python', 'native')]
import moon47 as M47
import c47astro as A
from c47astro import dsin, dcos


def full(j):
    """(elongation, lit %, hp, sd) of the full series at JD j (UT)."""
    s = A.Sun(j); T = s.T; h = A._horner
    Lp = h([218.3164477, 481267.8812, -0.0015786, 1.855835024E-06, -1.533883486E-08], T) % 360
    D = h([297.8501921, 445267.1114, -0.0018819, 1.831944719E-06, -8.844469995E-09], T) % 360
    M = h([357.5291092, 35999.05029, -0.0001536, 4.083299306E-08], T) % 360
    Mp = h([134.9633964, 477198.8675, 0.0087414, 1.434740814E-05, -6.797172376E-08], T) % 360
    F = h([93.272095, 483202.0175, -0.0036539, -2.836074872E-07, 1.158332465E-09], T) % 360
    E = h([1, -0.002516, -7.4E-06], T)
    acc = {6: 0.0, 7: 0.0, 8: 0.0}
    for tab, rs, rc in ((A.ML, 6, 7), (A.MB, 8, 8), (A.MCL, 6, 6), (A.MCB, 8, 8)):
        for d, m, mp, f, cs, cc in tab:
            e = E ** int(abs(m)) if m == int(m) else E ** abs(m)
            acc[rs] += cs * e * dsin(d * D + m * M + mp * Mp + f * F)
            acc[rc] += cc * e * dcos(d * D + m * M + mp * Mp + f * F)
    A1 = T * 131.849 + 119.75
    acc[6] += dsin(A1) * 3958 + dsin(Lp - F) * 1962 + dsin(T * 479264.29 + 53.09) * 318 + (T * 367.1904613 + 56.41732779)
    acc[8] += (dsin(Lp) * -2235 + dsin(T * 481266.484 + 313.45) * 382 + dsin(A1 - F) * 175 + dsin(A1 + F) * 175
               + dsin(Lp - Mp) * 127 + dsin(Lp + Mp) * -115 + (T * 40.04748125 + -9.463218981))
    lam = acc[6] / 1e6 + Lp + s.dpsi / 3600.0
    bet = acc[8] / 1e6
    dist = acc[7] / 1000.0 + 385000.56
    el = (lam - s.lam) % 360.0
    psi = math.degrees(math.acos(dcos(bet) * dcos(lam - s.lam)))
    r = s.R * 149597870.7
    i = math.degrees(math.atan2(r * dsin(psi), dist - r * dcos(psi)))
    return el, (1 + dcos(i)) * 50, A.dasin(6378.14 / dist) * 60, 358473400.0 / dist / 60.0


def exact_time(t, target):
    for _ in range(8):
        t += ((target - full(t)[0] + 180) % 360 - 180) / M47.RATE
    return t


def main():
    random.seed(47)
    worst = {'phase': 0, 'age': 0, 'hp': 0, 'sd': 0, 'lit': 0}
    for _ in range(150):
        j = 2451545.0 + random.uniform(0, 365.25 * 50)
        p = M47.page(j)
        el, lit, hp, sd = full(j)
        worst['lit'] = max(worst['lit'], abs(p['lit'] - lit))
        worst['hp'] = max(worst['hp'], abs(p['hp'] - hp))
        worst['sd'] = max(worst['sd'], abs(p['sd'] - sd))
        for t, name in p['next']:
            target = dict((n, a) for a, n in M47.PHASES)[name]
            worst['phase'] = max(worst['phase'], abs(t - exact_time(t, target)) * 1440)
            assert j <= t < j + 29.9, (j, name, t)
        new = exact_time(j - p['age'], 0.0)
        worst['age'] = max(worst['age'], abs(p['age'] - (j - new)) * 1440)
    print('worst: phases %.1f min, age %.1f min, HP %.3f\', SD %.3f\', lit %.2f %%' % (
        worst['phase'], worst['age'], worst['hp'], worst['sd'], worst['lit']))
    assert worst['phase'] < 5 and worst['age'] < 5, worst
    assert worst['hp'] < 0.05 and worst['sd'] < 0.02 and worst['lit'] < 0.2, worst
    print('ok')


if __name__ == '__main__':
    main()
