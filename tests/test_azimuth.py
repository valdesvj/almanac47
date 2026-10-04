#!/usr/bin/env python3
"""test_azimuth.py - Hc and Zn (sight reduction) against independent references.

1. The formula: the calculator's HCZ (RPN, build/dev/src/NAVFULL.txt via CHZ, run in python/c47sim.py: v2 does it
   with n-vectors, →REC / →POL) and c47astro.hcz (Python, ASIN / ATAN2) against ERFA hd2ae, for random latitude,
   declination and LHA (poles and zenith included), and for cases with a known answer: on the meridian north and
   south of the observer, lower transit, east and west, the horizon, the zenith.
2. The whole chain: Sun, planets and stars of the calculator (c47astro: series, catalogue, Hc and Zn) against
   Skyfield (DE421, its own precession, nutation, aberration and Delta T) for observers at sea level, no
   refraction. Hc is geocentric, as in the almanac (the navigator corrects the parallax with HP): Skyfield's
   apparent position from the Earth's centre turned into the observer's horizon frame (rotation_at), so the
   parallax of the Moon, Venus and Mars is not in the difference. The Moon is in it too. Planets within 1 deg of the
   Sun are skipped: they cannot be seen, and the references bend their light around the Sun (the calculator leaves
   the light bending out: under 0.01' farther than 1 deg from the Sun).

Zn is compared as Zn x cos Hc (the distance on the sky, arcmin): near the zenith Zn itself is undefined.

  ~/.venvs/almanac47-ephem/bin/python tests/test_azimuth.py [N] [seed]
  (or uv run --no-project --with numpy --with pyerfa --with skyfield --with "jplephem==2.24" python3 ...)
  Skyfield reads de421.bsp from ~/.skyfield-data (downloads it there once).
"""
import math, os, random, sys
from decimal import Decimal as D
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [os.path.join(ROOT, 'python'), os.path.join(ROOT, 'python', 'native')]
try:
    import erfa
    from skyfield.api import Loader, Star, wgs84
    from skyfield.functions import mxv
except ImportError as e:
    print('test_azimuth: %s - run it with ~/.venvs/almanac47-ephem/bin/python (skyfield, pyerfa)' % e)
    sys.exit(0)
import c47sim, c47astro as A, c47data as CD

LIMIT_FORMULA = 0.001       # arcmin: the formula, exact up to rounding
LIMIT_CHAIN = 0.3           # arcmin: the whole chain (series + Sun parallax)
NAV = os.path.join(ROOT, 'build', 'dev', 'src', 'NAVFULL.txt')


def wrap(d):
    return ((d + 180.0) % 360.0 - 180.0) * 60.0


def ref(lat, lon, dec, gha):
    """ERFA: hour angle west positive, azimuth from north through east."""
    az, el = erfa.hd2ae(math.radians((gha + lon) % 360.0), math.radians(dec), math.radians(lat))
    return math.degrees(el), math.degrees(az) % 360.0


class RPN:
    """CHZ of the calculator: X = GHA, Y = Dec, Z = longitude, T = latitude -> X = Hc, R06 = Zn."""
    def __init__(self):
        self.c = c47sim.load([NAV])

    def hcz(self, lat, lon, dec, gha):
        c = self.c
        c.s = [D(repr(gha)), D(repr(dec)), D(repr(lon)), D(repr(lat))]
        c.run('CHZ', maxsteps=10 ** 5)
        return float(c.s[0]), float(c.reg.get('6', 0))


# (lat, LHA, dec) -> (Hc, Zn) known without a formula; Zn None = undefined (zenith)
KNOWN = [((40, 0, 10), (60, 180)),          # on the meridian, south of the observer
         ((10, 0, 40), (60, 0)),            # on the meridian, north of the observer
         ((-30, 0, -50), (70, 180)),        # southern latitude, body further south
         ((-30, 0, 10), (50, 0)),           # southern latitude, body to the north
         ((40, 180, 60), (10, 0)),          # lower transit of a circumpolar body
         ((-40, 180, -60), (10, 180)),      # lower transit, southern sky
         ((0, 90, 0), (0, 270)),            # on the equator, west, on the horizon
         ((0, 270, 0), (0, 90)),            # east
         ((0, 0, 0), (90, None)),           # zenith
         ((25, 0, 25), (90, None)),         # zenith
         ((90 - 1e-9, 37, 20), (20, None)), # at the pole: Hc = Dec
         ((50, 0, -40), (0, 180)),          # on the horizon, south
         ((60, 180, 30), (0, 0))]           # on the horizon, north (lower transit)


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 2000
    rnd = random.Random(int(sys.argv[2]) if len(sys.argv) > 2 else 1)
    rpn = RPN()
    bad = 0
    print('== 1. the formula: known cases (Hc, Zn in degrees)')
    for (lat, lha, dec), (hc, zn) in KNOWN:
        out = []
        for name, f in (('RPN', rpn.hcz), ('Python', A.hcz)):
            h, z = f(lat, 0.0, dec, float(lha))
            ok = abs(h - hc) * 60 < LIMIT_FORMULA and (zn is None or abs(wrap(z - zn)) < LIMIT_FORMULA)
            bad += not ok
            out.append('%s %8.4f %8.4f %s' % (name, h, z, 'ok' if ok else 'WRONG'))
        print('  lat %6.1f LHA %5.1f dec %6.1f  expected Hc %5.1f Zn %5s   %s' % (lat, lha, dec, hc, zn, '   '.join(out)))
    print('== 1. the formula: %d random cases against ERFA hd2ae (arcmin)' % n)
    worst = {}
    for k in range(n):
        lat = rnd.uniform(-90, 90) if k % 10 else rnd.choice((-1, 1)) * rnd.uniform(89, 90)    # 1 in 10 near a pole
        dec = rnd.uniform(-90, 90) if k % 7 else lat + rnd.uniform(-0.01, 0.01)                 # 1 in 7 near the zenith
        lon, gha = rnd.uniform(-180, 180), rnd.uniform(0, 360)
        if k % 13 == 0:
            gha = (-lon + rnd.choice((0, 180, 90, 270)) + rnd.uniform(-1e-6, 1e-6)) % 360           # on the meridian / prime vertical
        h0, z0 = ref(lat, lon, dec, gha)
        for name, f in (('RPN', rpn.hcz), ('Python', A.hcz)):
            h, z = f(lat, lon, dec, gha)
            w = worst.setdefault(name, [0, 0, None])
            dh, dz = abs(h - h0) * 60, abs(wrap(z - z0)) * math.cos(math.radians(h0))
            if dh > w[0]:
                w[0] = dh
            if dz > w[1]:
                w[1], w[2] = dz, (lat, lon, dec, gha)
    for name, (dh, dz, case) in worst.items():
        ok = dh < LIMIT_FORMULA and dz < LIMIT_FORMULA
        bad += not ok
        print('  %-6s Hc max %.6f  Zn x cos Hc max %.6f  %s' % (name, dh, dz, 'ok' if ok else 'FAIL at lat lon dec gha %s' % (case,)))

    print('== 2. the whole chain against Skyfield: Sun, planets, stars (arcmin)')
    load = Loader(os.path.expanduser('~/.skyfield-data'))
    ts, eph = load.timescale(), load('de421.bsp')
    earth = eph['earth']
    bodies = [('SUN', eph['sun'], None), ('MOON', eph['moon'], None), ('VENUS', eph['venus'], 1), ('MARS', eph['mars'], 2),
              ('JUPITER', eph['jupiter barycenter'], 3), ('SATURN', eph['saturn barycenter'], 4)]
    stars = [Star(ra_hours=a / 15.0, dec_degrees=d, ra_mas_per_year=pa, dec_mas_per_year=pd) for a, d, pa, pd in CD.ST]
    stat = {}
    for k in range(max(n // 20, 20)):
        j = rnd.uniform(A.jd(2000, 1, 1), A.jd(2050, 12, 31))
        lat, lon = rnd.uniform(-70, 70), rnd.uniform(-180, 180)
        t = ts.ut1_jd(j)
        R = wgs84.latlon(lat, lon).rotation_at(t)         # GCRS -> north, east, up of the observer
        geo = earth.at(t)
        s = A.Sun(j)
        mine = {'SUN': (s.gha, s.dec), 'MOON': A.moon(s)[:2]}
        for name, _, p in bodies[2:]:
            mine[name] = A.planet(s, p)[:2]
        pairs = [(name, mine[name], geo.observe(b).apparent()) for name, b, _ in bodies]
        for i in rnd.sample(range(58), 10):
            g, d, _ = A.star(s, i + 1)
            pairs.append(('STARS', (g, d), geo.observe(stars[i]).apparent()))
        sun_app = pairs[0][2]
        for name, (g, d), app in pairs:
            if name not in ('SUN', 'MOON', 'STARS') and app.separation_from(sun_app).degrees < 1:
                continue          # behind or at the Sun: not observable; the light bending there (up to 1') is left out
            x, y, z = mxv(R, app.position.au)
            alt = math.degrees(math.atan2(z, math.hypot(x, y)))
            az = math.degrees(math.atan2(y, x)) % 360.0
            h, zn = A.hcz(lat, lon, d, g)
            st = stat.setdefault(name, [0, 0, 0, None])
            if abs(h - alt) * 60 > st[0]:
                st[3] = 'JD %.4f lat %.2f lon %.2f' % (j, lat, lon)
            st[0] = max(st[0], abs(h - alt) * 60)
            st[1] = max(st[1], abs(wrap(zn - az)) * math.cos(math.radians(alt)))
            st[2] += 1
    for name, (dh, dz, cnt, case) in stat.items():
        ok = dh < LIMIT_CHAIN and dz < LIMIT_CHAIN
        bad += not ok
        print('  %-8s n %4d  Hc max %.4f  Zn x cos Hc max %.4f  %s' % (name, cnt, dh, dz, 'ok' if ok else 'FAIL (Hc max at %s)' % case))
    print('%d failed' % bad)
    return bad


if __name__ == '__main__':
    sys.exit(1 if main() else 0)
