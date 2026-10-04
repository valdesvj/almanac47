#!/usr/bin/env python3
"""test_ephem.py - the Almanac 47 calculations against an independent ephemeris: JPL DE421 with ERFA
(IAU 2006/2000A precession-nutation, light time, light deflection, aberration), the reference of
tools/almanac/c47_almanac_generator.py. Apparent geocentric GHA and Dec, true equator and equinox of date.

Checked: the method of the calculator in its Python form (python/native/c47astro.py: the same formulas and
series as the RPN programs, which tests/test_parity.py shows draw the same screens), random instants:
  FULL  2000-2050  VSOP87 series (NAVINIT_FULL)
  FAST  2026-2030  the fitted series (NAVINIT_FAST)
  TBL   Oct 2026 - Sep 2031  the almanac tables (build/TBL_5.txt)
Sun, Moon (and HP, SD), Venus, Mars, Jupiter, Saturn, GHA Aries, the 58 stars (catalogue of the calculator,
ERFA atci13 for the reference), Hc and Zn from a random position, the Sun's rise, set, twilight and meridian
passage (minutes), the Moon's % lit and age.

TT - UT1: the reference uses the IERS values for 2000-2025 (the generator's table), the calculator a fixed
69.2 s: that error is part of what is measured (up to 0.05' for the Moon in 2000).

  uv run --no-project --with numpy --with pyerfa --with "jplephem==2.24" --with de421 \\
      python3 tests/test_ephem.py [N] [seed]          (N instants per mode, default 200)
"""
import math, os, random, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [os.path.join(ROOT, 'python', 'native'), os.path.join(ROOT, 'tools', 'almanac')]
try:
    import erfa
    import c47_almanac_generator as G
except ImportError as e:
    print('test_ephem: %s - run it with:\n  uv run --no-project --with numpy --with pyerfa --with "jplephem==2.24" '
          '--with de421 python3 tests/test_ephem.py' % e)
    sys.exit(0)
import c47astro as A, c47data as D, c47tables

# limits (arcmin; minutes of time for the sun times; % and hours for the Moon phase): a value over its limit fails
LIMIT = {'pos': 0.2, 'moonpos': 0.3, 'hpsd': 0.05, 'hczn': 0.3, 'time': 1.0, 'lit': 0.5, 'age': 0.25}
PLANETS = {1: 'venus', 2: 'mars', 3: 'jupiter', 4: 'saturn'}
MAS = math.pi / 180 / 3600000.0


def wrap(d):
    """difference of two angles in degrees -> arcmin, in -180 .. 180 deg."""
    return ((d + 180.0) % 360.0 - 180.0) * 60.0


def ref_star(n, j):
    """apparent GHA, Dec of star n (catalogue of the calculator, no parallax) with ERFA."""
    a0, d0, pa, pd = D.ST[n - 1]
    tt = j + G.dt(j) / 86400.0
    ri, di, _ = erfa.atci13(math.radians(a0), math.radians(d0), pa * MAS / math.cos(math.radians(d0)), pd * MAS,
                            0.0, 0.0, 2400000.5, tt - 2400000.5)
    era = math.degrees(erfa.era00(2400000.5, j - 2400000.5))
    return (era - math.degrees(ri)) % 360.0, math.degrees(di)


def ref_hcz(lat, lon, gha, dec):
    return A.hcz(lat, lon, dec, gha)


def ref_event(j0, lat, lon, kind, t_guess):
    """the sun time of the reference: Hc = h0 (or LHA = 0 for TRAN) by the secant method from the guess (UT hours)."""
    h0, sg = A.EVENTS[kind]

    def f(t):
        g, d, _ = G.apparent('sun', j0 + t / 24.0)
        if not sg:
            return ((g + lon + 180.0) % 360.0) - 180.0
        return A.hcz(lat, lon, d, g)[0] - h0
    a, b = t_guess - 0.05, t_guess + 0.05
    fa, fb = f(a), f(b)
    for _ in range(30):
        if fb == fa:
            break
        a, fa, b = b, fb, b - fb * (b - a) / (fb - fa)
        fb = f(b)
        if abs(b - a) < 1e-6:
            break
    return b


def ref_phase(j):
    """% lit and age (days since the last new Moon) from DE421: the elongation in ecliptic longitude of date."""
    def lon_ecl(name, jj):
        g, d, r = G.apparent(name, jj)
        ra = G.gha_aries(jj) - g
        tt = jj + G.dt(jj) / 86400.0
        e = math.degrees(erfa.obl06(2400000.5, tt - 2400000.5))
        lam = math.degrees(math.atan2(A.dsin(ra) * A.dcos(e) + A.dtan(d) * A.dsin(e), A.dcos(ra)))
        return lam, ra, d, r
    lm, ram, dm, rm = lon_ecl('moon', j)
    ls, ras, ds, rs = lon_ecl('sun', j)
    psi = math.acos(A.dsin(dm) * A.dsin(ds) + A.dcos(dm) * A.dcos(ds) * A.dcos(ram - ras))
    i = math.atan2(rs * math.sin(psi), rm - rs * math.cos(psi))
    lit = (1 + math.cos(i)) * 50

    def el(jj):
        return (lon_ecl('moon', jj)[0] - lon_ecl('sun', jj)[0]) % 360.0
    t = j - el(j) / 12.19                                  # the new Moon, then the secant method on the elongation
    for _ in range(20):
        e1 = (el(t) + 180.0) % 360.0 - 180.0
        e2 = (el(t + 0.01) + 180.0) % 360.0 - 180.0
        if e2 == e1:
            break
        dt = -e1 * 0.01 / (e2 - e1)
        t += dt
        if abs(dt) < 1e-6:
            break
    return lit, j - t


class Stat:
    def __init__(self):
        self.v = {}

    def add(self, key, x):
        self.v.setdefault(key, []).append(abs(x))

    def show(self, limits):
        bad = 0
        for key, xs in self.v.items():
            lim = limits(key)
            mx = max(xs)
            rms = math.sqrt(sum(x * x for x in xs) / len(xs))
            fail = mx > lim
            bad += fail
            print('  %-22s n %5d  max %8.4f  rms %8.4f  limit %5.2f  %s' % (key, len(xs), mx, rms, lim, 'FAIL' if fail else 'ok'))
        return bad


def limit_of(key):
    if 'HP' in key or 'SD' in key:
        return LIMIT['hpsd']
    if key.startswith('MOON'):
        return LIMIT['moonpos']
    if key.startswith(('Hc', 'Zn')):
        return LIMIT['hczn']
    if key.startswith('sun '):
        return LIMIT['time']
    if key.startswith('phase lit'):
        return LIMIT['lit']
    if key.startswith('phase age'):
        return LIMIT['age']
    return LIMIT['pos']


def instants(n, j1, j2, rnd):
    return [(rnd.uniform(j1, j2), rnd.uniform(-60, 60), rnd.uniform(-180, 180)) for _ in range(n)]


def check(mode, cases, tables=None, events=0, phases=0):
    """one mode: positions for every case, the sun times and the Moon phase for the first events / phases cases."""
    st = Stat()
    for k, (j, lat, lon) in enumerate(cases):
        s = A.Sun(j)
        sun = (s.gha, s.dec)
        aries = s.aries
        moon = A.moon(s)
        pl = {p: A.planet(s, p)[:2] for p in PLANETS}
        if tables:
            t = tables.get(j, 0); sun = t if t else sun
            t = tables.get(j, 6); aries = t[0] if t else aries
            t = tables.get(j, 5); moon = t if t else moon
            for p in PLANETS:
                t = tables.get(j, p); pl[p] = t[:2] if t else pl[p]
        g, d, r = G.apparent('sun', j)
        st.add('SUN GHA', wrap(sun[0] - g)); st.add('SUN Dec', (sun[1] - d) * 60)
        h1, z1 = A.hcz(lat, lon, sun[1], sun[0]); h2, z2 = A.hcz(lat, lon, d, g)
        st.add('Hc (all bodies)', (h1 - h2) * 60)
        st.add('Zn (all bodies) x cos Hc', wrap(z1 - z2) * A.dcos(h2))
        st.add('ARIES GHA', wrap(aries - G.gha_aries(j)))
        g, d, r = G.apparent('moon', j)
        st.add('MOON GHA', wrap(moon[0] - g)); st.add('MOON Dec', (moon[1] - d) * 60)
        st.add('MOON HP', moon[2] - math.degrees(math.asin(G.REQ / r)) * 60)
        st.add('MOON SD', moon[3] - math.degrees(math.asin(0.272481 * G.REQ / r)) * 60)
        h1, z1 = A.hcz(lat, lon, moon[1], moon[0]); h2, z2 = A.hcz(lat, lon, d, g)
        st.add('Hc (all bodies)', (h1 - h2) * 60)
        gs, ds, _ = G.apparent('sun', j)
        for p, name in PLANETS.items():
            g, d, r = G.apparent(name, j)
            if A.dsin(d) * A.dsin(ds) + A.dcos(d) * A.dcos(ds) * A.dcos(g - gs) > A.dcos(1.0):
                continue          # within 1 deg of the Sun: not observable; ERFA bends its light (the calculator does not)
            st.add('%s GHA' % name.upper(), wrap(pl[p][0] - g)); st.add('%s Dec' % name.upper(), (pl[p][1] - d) * 60)
        if mode == 'TBL':
            continue                                        # the stars do not come from the tables
        for n in range(1, 59):
            g1, d1, _ = A.star(s, n)
            g2, d2 = ref_star(n, j)
            st.add('STARS GHA x cos Dec', wrap(g1 - g2) * A.dcos(d2)); st.add('STARS Dec', (d1 - d2) * 60)
            h1, z1 = A.hcz(lat, lon, d1, g1); h2, z2 = A.hcz(lat, lon, d2, g2)
            st.add('Hc (all bodies)', (h1 - h2) * 60)
            st.add('Zn (all bodies) x cos Hc', wrap(z1 - z2) * A.dcos(h2))
        if k < events:
            j0 = A.day0(j)
            sung = None
            if tables:
                def sung(jj):
                    return tables.get(jj, 0) or A.sun_fast(jj)
            for kind in ('NTWA', 'RISE', 'TRAN', 'SET', 'NTWP'):
                t = A.event(j0, lat, lon, kind, sung)
                if t == 99.0:
                    continue
                st.add('sun %s (min)' % kind, (t - ref_event(j0, lat, lon, kind, t)) * 60)
        if k < phases:
            lit, age = A.phase(s)
            rl, ra = ref_phase(j)
            st.add('phase lit (%)', lit - rl)
            st.add('phase age (h)', (age - ra) * 24)
    print('== %s: %d instants' % (mode, len(cases)))
    return st.show(limit_of)


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 200
    rnd = random.Random(int(sys.argv[2]) if len(sys.argv) > 2 else 1)
    bad = check('FULL 2000-2050', instants(n, A.jd(2000, 1, 1), A.jd(2050, 12, 31), rnd), events=n // 4, phases=n // 4)
    period = A.use_series(os.path.join(ROOT, 'python', 'native', 'fast_series.json'))
    j1, j2 = A.FAST_JD
    bad += check('FAST %s' % period, instants(n, j1, j2, rnd), events=n // 8, phases=0)
    A.use_series(None)
    tb = c47tables.Tables(os.path.join(ROOT, 'build', 'TBL_5.txt'))
    bad += check('TBL', instants(n, A.jd(2026, 10, 1), A.jd(2031, 9, 30), rnd), tables=tb, events=n // 8)
    print('%d over the limit' % bad)
    return bad


if __name__ == '__main__':
    sys.exit(1 if main() else 0)
