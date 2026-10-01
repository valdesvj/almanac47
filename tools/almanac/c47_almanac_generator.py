#!/usr/bin/env python3
"""Generate Chebyshev GHA/Dec coefficient tables for the C47 (Method B).

Reference: JPL DE421 + IAU 2006/2000A (ERFA). Apparent geocentric, true equator & equinox of date.
Time argument UT1; dT = TT - UT1 set below.

  pip install numpy pyerfa jplephem==2.24 de421
  python c47_almanac_generator.py 2028-01-01 2029-01-01 > tables_2028.csv
(DE421 covers 1900-2050.)
"""
import sys, csv
import numpy as np, erfa, math, de421
from jplephem.ephem import Ephemeris

E = Ephemeris(de421)
C = E.CLIGHT * 86400.0          # km/day
AU = E.AU
EMR = E.EMRAT
DT = 69.2                        # TT-UT1 seconds from 2025 on (the future cannot be known)
# TT-UT1 at the start of each year 2000-2025 (IERS / USNO, rounded to 0.1 s); linear in between
DT_YEARS = {2000: 63.8, 2001: 64.1, 2002: 64.3, 2003: 64.5, 2004: 64.6, 2005: 64.7, 2006: 64.8,
            2007: 65.1, 2008: 65.5, 2009: 65.8, 2010: 66.1, 2011: 66.3, 2012: 66.6, 2013: 66.9,
            2014: 67.3, 2015: 67.6, 2016: 68.1, 2017: 68.6, 2018: 69.0, 2019: 69.2, 2020: 69.4,
            2021: 69.4, 2022: 69.3, 2023: 69.2, 2024: 69.2, 2025: DT}


def dt(jd_ut1):
    """TT-UT1 (s) for a date: the table above for 2000-2025, DT before and after."""
    y = 2000.0 + (jd_ut1 - 2451544.5) / 365.25
    k = int(math.floor(y))
    if k < 2000 or k >= 2025:
        return DT_YEARS[2000] if k < 2000 else DT
    return DT_YEARS[k] + (DT_YEARS[k + 1] - DT_YEARS[k]) * (y - k)
REQ = 6378.137

def _pv(name, tdb):
    p, v = E.position_and_velocity(name, tdb)
    return p[:, 0] if p.ndim > 1 else p, v[:, 0] if v.ndim > 1 else v

def earth_bary(tdb):
    pe, ve = _pv('earthmoon', tdb); pm, vm = _pv('moon', tdb)
    return pe - pm / (1 + EMR), ve - vm / (1 + EMR)

def body_bary(name, tdb):
    if name == 'moon':
        pe, ve = _pv('earthmoon', tdb); pm, vm = _pv('moon', tdb)
        return pe + pm * EMR / (1 + EMR)
    return _pv(name, tdb)[0]

def apparent(name, jd_ut1):
    """returns GHA deg, Dec deg, distance km"""
    tt = jd_ut1 + dt(jd_ut1) / 86400.0
    eb, ev = earth_bary(tt)
    tau = 0.0
    for _ in range(4):
        p = body_bary(name, tt - tau) - eb
        tau = np.linalg.norm(p) / C
    d = np.linalg.norm(p); u = p / d
    ps, _ = _pv('sun', tt); s = np.linalg.norm(eb - ps) / AU
    v = ev / C
    bm1 = math.sqrt(1 - v @ v)
    # light deflection by the Sun (skip for Sun itself)
    if name not in ('sun', 'moon'):
        q = (p + eb - ps); q /= np.linalg.norm(q)
        e = (eb - ps); e /= np.linalg.norm(e)
        u = erfa.ld(1.0, u, q, e, s, 1e-9)
    ua = erfa.ab(u, v, s, bm1)
    uc = erfa.c2i06a(2400000.5, tt - 2400000.5) @ ua
    ri = math.degrees(math.atan2(uc[1], uc[0]))
    di = math.degrees(math.asin(uc[2]))
    era = math.degrees(erfa.era00(2400000.5, jd_ut1 - 2400000.5))
    return (era - ri) % 360.0, di, d

def gha_aries(jd_ut1):
    tt = jd_ut1 + dt(jd_ut1) / 86400.0
    return math.degrees(erfa.gst06a(2400000.5, jd_ut1 - 2400000.5, 2400000.5, tt - 2400000.5)) % 360

def jd(y, m, d, h=0.0):
    a, b = erfa.cal2jd(y, m, d)
    return a + b + h / 24.0
from numpy.polynomial import chebyshev as Ch
CFG = {'sun':(8,4), 'aries':(8,4), 'moon':(1,5), 'venus':(8,4), 'mars':(8,4), 'jupiter':(8,4), 'saturn':(8,4)}
def vals(body, j):
    if body=='aries': return gha_aries(j), None, None
    g,d,r = apparent(body, j)
    if body=='moon': return g, d, math.degrees(math.asin(REQ/r))*60     # HP arcmin
    if body=='sun': return g, d, 959.63/(r/1.495978707e8)/60            # SD arcmin
    return g, d, None
def fit(body, j0, span, deg, nn=24):
    x = np.cos(np.pi*(np.arange(nn)+0.5)/nn)[::-1]
    V = [vals(body, j0+(xi+1)/2*span) for xi in x]
    rate = {'sun':360.0,'moon':347.81}.get(body, 360.9856)
    tt = (x+1)/2*span
    g = np.array([v[0] for v in V]); r = g - rate*tt; r = r[0] + ((r - r[0] + 180) % 360 - 180); g = rate*tt + r
    out = {'gha': Ch.chebfit(x, g, deg)}
    if V[0][1] is not None: out['dec'] = Ch.chebfit(x, [v[1] for v in V], deg)
    if body=='moon': out['hp'] = Ch.chebfit(x, [v[2] for v in V], 3)
    if body=='sun': out['sd'] = float(np.mean([v[2] for v in V]))
    return out

def main():
    y0, m0, d0 = map(int, sys.argv[1].split('-')); y1, m1, d1 = map(int, sys.argv[2].split('-'))
    start, end = jd(y0, m0, d0), jd(y1, m1, d1)
    w = csv.writer(sys.stdout)
    w.writerow(['body', 'start_0h_UT1', 'span_h', 'quantity', 'c0', 'c1', 'c2', 'c3', 'c4', 'c5'])
    for body, (span, deg) in CFG.items():
        j0 = start
        while j0 < end:
            f = fit(body, j0, span, deg)
            y, m, d, _ = erfa.jd2cal(j0, 0.0); date = '%04d-%02d-%02d' % (y, m, d)
            for q in ('gha', 'dec', 'hp'):
                if q in f: w.writerow([body, date, span*24, q] + ['%.5f' % v for v in f[q]])
            if 'sd' in f: w.writerow([body, date, span*24, 'sd_arcmin', '%.2f' % f['sd']])
            j0 += span

if __name__ == '__main__':
    main()
