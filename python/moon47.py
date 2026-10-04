#!/usr/bin/env python3
"""moon47.py - MOON47, the Moon's phase page, standalone: no INIT tables and no NAV routines.

This is the reference for the calculator versions of MOON47 (C47 / R47, DM42, Free42, NumWorks,
HP Prime): every one uses these formulas, these 20 terms and these steps.

  One table of 20 terms of the Moon (Meeus, Astronomical Algorithms, ch. 47, the largest of table 47.A):
  multiples of D, M, M', F, the longitude term (1e-6 deg, sine) and the distance term (1e-3 km, cosine;
  0 for the 7 longitude-only rows). E^|M| for the terms with M.
  Elongation (Moon - Sun longitude) = D + sum(longitude terms) - the Sun's equation of the centre
  + 20.5" (the Sun's aberration). Distance = 385000.56 km + sum(distance terms).
  Phases: the secant method on the elongation (0 new, 90 first quarter, 180 full, 270 last quarter),
  from the guess of the mean rate (12.190749 deg a day), three steps. Age: the time since the last new Moon.
  % lit: the phase angle from the elongation, the Moon's latitude (5.128 deg sin F) and the two distances.
  HP = asin(6378.14 km / distance), SD = 358473400 / distance (arcmin, as NAV).
Accuracy against the full series of NAV (Meeus 47 + DE421 corrections), 2000-2050: phase times and age
within 4 minutes (median under 1), HP within 0.03', SD within 0.01', lit within 0.1 %.

  python3 python/moon47.py [--date 2026-10-03 --ut 12:00] [--tz 4] [--south] [--png FILE]
  The phase does not depend on the place: MOON47 takes the date and time from the clock (UT; on the
  calculators the clock is local time, minus the variable TZ if it exists) and asks nothing. The latitude
  only turns the picture: northern view, or the southern one (the +/- key on the calculators).
"""
import math

# D, M, M', F, longitude (1e-6 deg), distance (1e-3 km)
TERMS = (
    (0, 0, 1, 0, 6288774, -20905355),
    (2, 0, -1, 0, 1274027, -3699111),
    (2, 0, 0, 0, 658314, -2955968),
    (0, 0, 2, 0, 213618, -569925),
    (0, 1, 0, 0, -185116, 48888),
    (0, 0, 0, 2, -114332, 0),
    (2, 0, -2, 0, 58793, 246158),
    (2, -1, -1, 0, 57066, -152138),
    (2, 0, 1, 0, 53322, -170733),
    (2, -1, 0, 0, 45758, -204586),
    (0, 1, -1, 0, -40923, -129620),
    (1, 0, 0, 0, -34720, 108743),
    (0, 1, 1, 0, -30383, 104755),
    (2, 0, 0, -2, 15327, 0),
    (0, 0, 1, 2, -12528, 0),
    (0, 0, 1, -2, 10980, 79661),
    (4, 0, -1, 0, 10675, 0),
    (0, 0, 3, 0, 10034, 0),
    (4, 0, -2, 0, 8548, 0),
    (2, 1, -1, 0, -7888, 0),
)
LUN = 29.530589          # synodic month, days
RATE = 12.190749         # mean elongation, deg a day
DT = 69.0 / 86400.0      # TT - UT (2000-2050: 64-75 s), days
PHASES = ((0.0, 'NEW MOON'), (90.0, 'FIRST QUARTER'), (180.0, 'FULL MOON'), (270.0, 'LAST QUARTER'))
NAMES = ('NEW MOON', 'WAXING CRESCENT', 'FIRST QUARTER', 'WAXING GIBBOUS', 'FULL MOON',
         'WANING GIBBOUS', 'LAST QUARTER', 'WANING CRESCENT')


def sind(x):
    return math.sin(math.radians(x))


def cosd(x):
    return math.cos(math.radians(x))


def julian(y, m, d, ut):
    """JD of the date (Gregorian) at ut hours."""
    if m <= 2:
        y, m = y - 1, m + 12
    a = y // 100
    return int(365.25 * (y + 4716)) + int(30.6001 * (m + 1)) + d + 2 - a + a // 4 - 1524.5 + ut / 24.0


def from_julian(j):
    """(day, month, year, ut hours) of JD j."""
    z = int(j + 0.5); f = j + 0.5 - z
    a = int((z - 1867216.25) / 36524.25)
    a = z + 1 + a - a // 4
    b = a + 1524; c = int((b - 122.1) / 365.25); d = int(365.25 * c); e = int((b - d) / 30.6001)
    day = b - d - int(30.6001 * e)
    mon = e - 1 if e < 14 else e - 13
    return day, mon, (c - 4716 if mon > 2 else c - 4715), f * 24.0


def moon(j):
    """(elongation deg 0-360, distance km, latitude deg, M deg) at JD j (UT)."""
    T = (j + DT - 2451545.0) / 36525.0
    D = 297.8501921 + 445267.1114 * T
    M = 357.5291092 + 35999.05029 * T
    Mp = 134.9633964 + 477198.8675 * T
    F = 93.272095 + 483202.0175 * T
    E = 1.0 - 0.002516 * T
    lon = dist = 0.0
    for d, m, mp, f, cl, cr in TERMS:
        a = d * D + m * M + mp * Mp + f * F
        e = E if m else 1.0
        lon += cl * e * sind(a)
        dist += cr * e * cosd(a)
    c = (1.914602 - 0.004817 * T) * sind(M) + 0.019993 * sind(2 * M) + 0.000289 * sind(3 * M)
    return (D + lon / 1e6 - c + 0.00569) % 360.0, 385000.56 + dist / 1000.0, 5.128189 * sind(F), M


def phase_time(j, target):
    """JD of the first time at or after about j when the elongation is target (deg): the secant method,
    from j and the mean rate's guess, three steps (within 0.01 minute of the converged time)."""
    d = (target - moon(j)[0]) % 360.0
    t0, f0 = j, -d
    t1 = j + d / RATE
    for _ in range(3):
        f1 = (moon(t1)[0] - target + 180.0) % 360.0 - 180.0
        if f1 == f0:
            break
        t0, t1, f0 = t1, t1 - f1 * (t1 - t0) / (f1 - f0), f1
    return t1


def tz_text(tz):
    """The offset of the header: 0, +4, -5, +5:30 (hours, minutes)."""
    if tz == 0:
        return '0'
    a = abs(tz); h = int(a); m = int(a * 60 - h * 60 + 0.5)
    if m == 60:
        h, m = h + 1, 0
    return ('+' if tz > 0 else '-') + str(h) + (':%02d' % m if m else '')


def header_text(j, tz):
    """The top line: the clock's date and time (UT when TZ = 0, else LT = UT + TZ) and TZ."""
    d, m, y, h = from_julian(j + tz / 24.0 + 0.5 / 1440)
    return '%02d-%02d-%04d %02d:%02d %s TZ=%s' % (d, m, y, int(h), int(h * 60) % 60, 'LT' if tz else 'UT', tz_text(tz))


def disc_runs(r, age, south, dx):
    """The disc, one column at a time (what AGRAPH draws): for column dx (-r..r) the runs (a, b) of rows,
    a <= |y| <= b above and below the centre. The lit part is filled, the dark part is the outline;
    waxing lit on the right (northern view), mirrored for the south. Same pixels as the test
    'lit or outline' of every pixel (x right of the terminator x = w cos(age), w the half width)."""
    ct = cosd(age / LUN * 360.0) or 1e-30
    v = (-dx if south else dx) * (1 if age <= LUN / 2 else -1)
    ymax = math.floor(math.sqrt((r + 0.3) ** 2 - dx * dx))
    qi = (r - 1.2) ** 2 - dx * dx
    out = [(0 if qi < 0 else math.floor(math.sqrt(qi)) + 1, ymax)]          # the outline
    q = r * r - (v / ct) ** 2
    if ct >= 0:
        if v > 0:
            out.append((0 if q < 0 else math.floor(math.sqrt(q)) + 1, ymax))
    elif v >= 0:
        out.append((0, ymax))
    elif q > 0:
        out.append((0, min(ymax, math.floor(math.sqrt(q)))))
    return [(a, b) for a, b in out if a <= b]


def page(j, south=False):
    """Everything MOON47 shows, at JD j (UT)."""
    e, dist, beta, M = moon(j)
    psi = math.degrees(math.acos(cosd(beta) * cosd(e)))                       # Sun-Moon angle
    r = 149597870.7 * (1.000140 - 0.016708 * cosd(M) - 0.000141 * cosd(2 * M))  # Sun distance, km
    i = math.degrees(math.atan2(r * sind(psi), dist - r * cosd(psi)))           # phase angle
    new = phase_time(j - e / RATE - 1.0, 0.0)                                   # the last new Moon
    if new > j:
        new = phase_time(new - LUN - 1.0, 0.0)
    age = j - new
    nxt = []
    for a, name in PHASES:
        t = phase_time(j, a)
        if t < j:                                                               # just passed: the next one
            t = phase_time(t + LUN - 2.0, a)
        nxt.append((t, name))
    nxt.sort()
    return {'jd': j, 'lit': (1.0 + cosd(i)) * 50.0, 'age': age,
            'hp': math.degrees(math.asin(6378.14 / dist)) * 60.0, 'sd': 358473400.0 / dist / 60.0,
            'index': int(age / LUN * 8 + 0.5) % 8, 'next': nxt, 'south': south, 'elongation': e}


def main():
    import argparse, datetime, os, sys
    ap = argparse.ArgumentParser(description='MOON47: the Moon phase page (standalone), now from the clock (UT).')
    ap.add_argument('--date', help='YYYY-MM-DD UT instead of the clock')
    ap.add_argument('--ut', default='12:00', help='HH:MM UT with --date (default 12:00)')
    ap.add_argument('--tz', type=float, help='hours between local time and UT for the header (default: the PC\'s own '
                    'offset with the clock, 0 with --date)')
    ap.add_argument('--south', action='store_true', help='the view from the south (the +/- key on the calculators)')
    ap.add_argument('--png', help='write the C47 screen to this PNG file')
    a = ap.parse_args()
    if a.date:
        y, m, d = map(int, a.date.split('-')); hh, mm = map(int, a.ut.split(':')); ut = hh + mm / 60.0
        tz = a.tz or 0.0
    else:
        now = datetime.datetime.now(datetime.timezone.utc)
        y, m, d, ut = now.year, now.month, now.day, now.hour + now.minute / 60.0 + now.second / 3600.0
        tz = a.tz if a.tz is not None else datetime.datetime.now().astimezone().utcoffset().total_seconds() / 3600.0
    j = julian(y, m, d, ut)
    p = page(j, a.south)
    print(header_text(j, tz))
    print('%s  lit %.0f %%  age %.1f days  HP %.1f\'  SD %.1f\'' % (NAMES[p['index']], p['lit'], p['age'], p['hp'], p['sd']))
    for t, name in p['next']:
        dd, mo, yy, h = from_julian(t + 0.5 / 1440)
        print('  %-14s %02d-%02d-%04d %02d:%02d UT' % (name, dd, mo, yy, int(h), int(h * 60) % 60))
    if a.png:
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'native'))
        import c47screen21, c47pc
        c47pc.write_png(a.png, *c47pc.render_rgb(c47screen21.moon47_screen(j, a.south, tz)[0]))
        print(a.png, 'written')


if __name__ == '__main__':
    main()
