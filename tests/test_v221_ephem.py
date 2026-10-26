#!/usr/bin/env python3
"""test_v221_ephem.py - ALMA47 v2.2.1 (build/v2.2.1/c47/ALMA47.txt) in the C47 simulator against JPL DE421 + ERFA, with
the reference and the limits of tests/test_ephem.py (as part 2 of tests/test_fw_c47.py, which runs the firmware).
Random instants and positions, FULL (NAVINIT_FULL, 2000-2050) and FAST (NAVINIT_FAST, 2026-2030): the inputs,
1 ALMANAC, + and 0; then the cache ALMC: rows 1 Sun, 2 Moon, 3-6 Venus Mars Jupiter Saturn (GHA Dec Hc Zn), 7-64
the stars (-98 not asked, -99 below the horizon), 65 GHA Aries, Moon HP, SD; 67 JD. A planet within 1 deg of the
Sun or below -0.5 deg Hc is not compared (the quick position, by design). Also: your stack back after each run.
      python3 tests/test_v221_ephem.py [n]      (needs pyerfa, jplephem 2.24, de421)"""
import os, random, sys
from decimal import Decimal as D
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [os.path.join(ROOT, 'tests'), os.path.join(ROOT, 'python'), os.path.join(ROOT, 'python', 'native')]
import erfa                                                                  # noqa: E402
import test_ephem as T                                                       # noqa: E402
import test_navopt as NO                                                     # noqa: E402
import c47astro as A                                                         # noqa: E402

ALMA = os.path.join(ROOT, 'build', 'v2.2.1', 'c47', 'ALMA47.txt')


def dms(x):
    m = round(abs(x) * 60)
    return '%s%d.%02d' % ('-' if x < 0 else '', m // 60, m % 60)


def ephem(mode, init, j1, j2, n, rnd, L):
    G = T.G
    st = T.Stat()
    stack_ok = 0
    for k in range(n):
        j = rnd.uniform(j1, j2)
        y, mo, dd, fd = erfa.jd2cal(j, 0.0)
        mins = int(round(fd * 1440)) % 1440
        j = A.jd(int(y), int(mo), int(dd)) + mins / 1440.0
        lat = round(rnd.uniform(-60, 60) * 60) / 60
        lon = round(rnd.uniform(-180, 180) * 60) / 60
        c = NO.load(L, init)
        for name, val in (('DATE', '%d.%02d%02d' % (y, mo, dd)), ('UTC', '%d.%02d' % (mins // 60, mins % 60)),
                          ('LAT', dms(lat)), ('LON', dms(lon))):
            c.reg[name] = D(val)
        c.flags.add(81); c.s = [D(11), D(12), D(13), D(14)]; c.lastx = D(99); c.frames = []; c.pix = []
        c.keys = [72, 85, 82]
        c.run('NAV', maxsteps=10 ** 8)
        stack_ok += c.s == [D(11), D(12), D(13), D(14)] and c.lastx == D(99)
        M = c.mats['ALMC']
        v = {(r, cc): float(M[r - 1][cc - 1]) for r in list(range(1, 66)) + [67] for cc in range(1, 5)}
        if abs(v[(67, 1)] - j) > 1e-6:
            st.add('RUNS (failed)', 99)
            continue

        def hz(row, g, dc):
            h2, z2 = A.hcz(lat, lon, dc, g)
            st.add('Hc (all bodies)', (v[(row, 3)] - h2) * 60)
            st.add('Zn (all bodies) x cos Hc', T.wrap(v[(row, 4)] - z2) * A.dcos(h2))
        g, dc, r = G.apparent('sun', j)
        st.add('SUN GHA', T.wrap(v[(1, 1)] - g)); st.add('SUN Dec', (v[(1, 2)] - dc) * 60); hz(1, g, dc)
        st.add('ARIES GHA', T.wrap(v[(65, 1)] - G.gha_aries(j)))
        gs, ds = g, dc
        g, dc, r = G.apparent('moon', j)
        st.add('MOON GHA', T.wrap(v[(2, 1)] - g)); st.add('MOON Dec', (v[(2, 2)] - dc) * 60); hz(2, g, dc)
        import math
        st.add('MOON HP', v[(65, 2)] - math.degrees(math.asin(G.REQ / r)) * 60)
        st.add('MOON SD', v[(65, 3)] - math.degrees(math.asin(0.272481 * G.REQ / r)) * 60)
        for p, name in T.PLANETS.items():
            g, dc, r = G.apparent(name, j)
            if A.dsin(dc) * A.dsin(ds) + A.dcos(dc) * A.dcos(ds) * A.dcos(g - gs) > A.dcos(1.0) or v[(2 + p, 3)] < -0.5:
                continue
            st.add('%s GHA' % name.upper(), T.wrap(v[(2 + p, 1)] - g)); st.add('%s Dec' % name.upper(), (v[(2 + p, 2)] - dc) * 60)
            hz(2 + p, g, dc)
        for s in range(1, 59):
            if v.get((6 + s, 3), -98) in (-98, -99):
                continue
            g2, d2 = T.ref_star(s, j)
            st.add('STARS GHA x cos Dec', T.wrap(v[(6 + s, 1)] - g2) * A.dcos(d2))
            st.add('STARS Dec', (v[(6 + s, 2)] - d2) * 60)
            hz(6 + s, g2, d2)
        print('  %s %d/%d %d.%02d%02d %02d:%02d %s %s' % (mode, k + 1, n, y, mo, dd, mins // 60, mins % 60, dms(lat),
                                                       dms(lon)), flush=True)
    print('== %s: %d instants (ALMA47 v2.2.1 in the C47 simulator against DE421 + ERFA); your stack back in %d of %d'
          % (mode, n, stack_ok, n))
    return st.show(T.limit_of) + (n - stack_ok)


def main():
    n = int(sys.argv[1]) if sys.argv[1:] else 8
    L = NO.lines(ALMA) if hasattr(NO, 'lines') else [l.rstrip('\n') for l in open(ALMA, encoding='utf-8') if l.strip()]
    L = ['LBL "NAV"'] + L[1:]
    rnd = random.Random(2210)
    bad = ephem('FULL', 'FULL', 2451545.0, 2469807.0, n, rnd, L)
    bad += ephem('FAST', 'FAST', 2461041.5, 2462867.5, n, rnd, L)
    print('\n%s' % ('ALL WITHIN THE LIMITS' if not bad else '%d OUT OF THE LIMITS' % bad))
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
