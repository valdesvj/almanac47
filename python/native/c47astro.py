"""c47astro.py - the astronomy of the C47_nav suite in plain Python.

Same methods, constants and series as the C47 programs:
  sun()    SUNA  VSOP87D Earth (truncated), FK5, IAU1980 nutation, aberration
  star()   STAR  IAU2006 precession, proper motion, nutation, aberration
  moon()   MOON  Meeus ch. 47 (60+60 terms) + 55 correction terms fitted to JPL DE421
  planet() PLAN  VSOP87D truncated, light time (2 passes), FK5, aberration, nutation
  event()  SUNRISE  rise/set, twilights, meridian passage (UT hours, 99 = none)
  phase()  PHAS  Moon % illuminated and age
  hcz()    CHZ   Hc and Zn
Time: JD in UT1. Angles in degrees. Latitude N+, longitude E+.
"""
from math import sin, cos, tan, asin, acos, atan2, sqrt, radians, degrees, hypot
from c47data import VL, VB, VR, NU, ST, ML, MB, MCL, MCB
import c47data as _D

DT = 69.2                          # TT - UT1, seconds
R2D = 57.295779513082320876798154814105


def jd(y, m, d, h=0.0):
    if m <= 2:
        y -= 1; m += 12
    a = y // 100; b = 2 - a + a // 4
    return int(365.25 * (y + 4716)) + int(30.6001 * (m + 1)) + d + b - 1524.5 + h / 24.0


def _ser(rows, tau):
    """SER: sum A cos(B + C tau) tau^k, result x 1E-8 (radians or au)."""
    s = 0.0
    for k, A, B, C in rows:
        s += A * cos(B + C * tau) * tau ** int(k)
    return s * 1e-8


def dsin(x): return sin(radians(x % 360.0))
def dcos(x): return cos(radians(x % 360.0))
def dtan(x): return tan(radians(x % 360.0))
def dasin(x): return degrees(asin(x))
def datan2(y, x): return degrees(atan2(y, x))


class Sun:
    """SUNA at one JD. Keeps the values the other routines use
    (T, apparent longitude, true obliquity, nutation, GHA Aries)."""

    def __init__(self, j):
        self.jd = j
        T = (j + DT / 86400.0 - 2451545.0) / 36525.0
        tau = T / 10.0
        L, B, R = _ser(VL, tau), _ser(VB, tau), _ser(VR, tau)
        lon = (L * R2D + 180.0) % 360.0
        lat = -(B * R2D)
        lp = lon - T * 1.397
        lat += (dcos(lp) - dsin(lp)) * 0.03916 / 3600.0
        lon -= 0.09033 / 3600.0
        self.args, self.dpsi, self.deps = _nut(T)
        lon += self.dpsi / 3600.0
        lon -= 20.4898 / R / 3600.0
        eps = (84381.448 - T * 46.815 + self.deps) / 3600.0
        self.dec = dasin(dsin(lat) * dcos(eps) + dcos(lat) * dsin(eps) * dsin(lon))
        ra = datan2(dsin(lon) * dcos(eps) - dtan(lat) * dsin(eps), dcos(lon))
        d = j - 2451545.0
        aries = (d * 360.98564736629 + 280.46061837 + (d / 36525.0) ** 2 * 0.000387933
                 + self.dpsi / 3600.0 * dcos(eps)) % 360.0
        self.T, self.R, self.lam, self.eps, self.aries = T, R, lon, eps, aries
        self.gha = (aries - ra) % 360.0
        self.sd = 15.99383 / R            # SUNSD, arcmin


def _nut(T):
    a = (297.85036 + 445267.11148 * T, 357.52772 + 35999.05034 * T,
         134.96298 + 477198.867398 * T, 93.27191 + 483202.017538 * T,
         125.04452 - 1934.136261 * T)
    dp = de = 0.0
    for r in NU:
        x = r[0] * a[0] + r[1] * a[1] + r[2] * a[2] + r[3] * a[3] + r[4] * a[4]
        dp += (r[5] + r[6] * T) * dsin(x)
        de += (r[7] + r[8] * T) * dcos(x)
    return a, dp * 1e-4, de * 1e-4


def star(s, n):
    """STAR / STR2. s = Sun(jd), n = almanac star 1-58. Returns (gha, dec, sha)."""
    T = s.T
    a0, d0, pa, pd = ST[n - 1]
    t = T * 100.0
    a = a0 + pa * t / 3600000.0 / dcos(d0)
    d = d0 + pd * t / 3600000.0
    ze = (((T * 0.01801828 + 0.2988499) * T + 2306.083227) * T + 2.650545) / 3600.0
    z = (((T * 0.01826837 + 1.0927348) * T + 2306.077181) * T - 2.650545) / 3600.0
    th = (((T * -0.04182264 - 0.4294934) * T + 2004.191903) * T) / 3600.0
    az = a + ze
    dm = dasin(dsin(th) * dcos(d) * dcos(az) + dcos(th) * dsin(d))
    am = datan2(dcos(d) * dsin(az), dcos(th) * dcos(d) * dcos(az) - dsin(th) * dsin(d)) + z
    e0 = s.eps - s.deps / 3600.0
    be = dasin(dsin(dm) * dcos(e0) - dcos(dm) * dsin(e0) * dsin(am))
    la = datan2(dsin(am) * dcos(e0) + dtan(dm) * dsin(e0), dcos(am))
    ek = T * -0.000042037 + 0.016708634
    pi = T * 1.71946 + 102.93735
    dbe = (dsin(s.lam - la) - dsin(pi - la) * ek) * dsin(be) * -20.49552 / 3600.0
    la += ((dcos(s.lam - la) * -20.49552 + dcos(pi - la) * ek * 20.49552) / dcos(be) + s.dpsi) / 3600.0
    be += dbe
    dec = dasin(dsin(be) * dcos(s.eps) + dcos(be) * dsin(s.eps) * dsin(la))
    ra = datan2(dsin(la) * dcos(s.eps) - dtan(be) * dsin(s.eps), dcos(la)) % 360.0
    sha = (360.0 - ra) % 360.0
    return (sha + s.aries) % 360.0, dec, sha


def _horner(c, T):
    v = c[-1]
    for k in reversed(c[:-1]):
        v = v * T + k
    return v


def moon(s):
    """MOON / MOO2. Returns (gha, dec, hp, sd); hp and sd in arcmin."""
    T = s.T
    Lp = _horner([218.3164477, 481267.8812, -0.0015786, 1.855835024E-06, -1.533883486E-08], T) % 360.0
    D = _horner([297.8501921, 445267.1114, -0.0018819, 1.831944719E-06, -8.844469995E-09], T) % 360.0
    M = _horner([357.5291092, 35999.05029, -0.0001536, 4.083299306E-08], T) % 360.0
    Mp = _horner([134.9633964, 477198.8675, 0.0087414, 1.434740814E-05, -6.797172376E-08], T) % 360.0
    F = _horner([93.272095, 483202.0175, -0.0036539, -2.836074872E-07, 1.158332465E-09], T) % 360.0
    E = _horner([1, -0.002516, -7.4E-06], T)
    acc = {6: 0.0, 7: 0.0, 8: 0.0}
    for tab, rs, rc in ((ML, 6, 7), (MB, 8, 8), (MCL, 6, 6), (MCB, 8, 8)):
        for d, m, mp, f, cs, cc in tab:
            arg = d * D + m * M + mp * Mp + f * F
            e = E ** int(abs(m)) if m == int(m) else E ** abs(m)
            acc[rs] += cs * e * dsin(arg)
            acc[rc] += cc * e * dcos(arg)
    A1 = T * 131.849 + 119.75
    acc[6] += (dsin(A1) * 3958 + dsin(Lp - F) * 1962 + dsin(T * 479264.29 + 53.09) * 318
               + (T * 367.1904613 + 56.41732779))
    acc[8] += (dsin(Lp) * -2235 + dsin(T * 481266.484 + 313.45) * 382 + dsin(A1 - F) * 175
               + dsin(A1 + F) * 175 + dsin(Lp - Mp) * 127 + dsin(Lp + Mp) * -115
               + (T * 40.04748125 + -9.463218981))
    lam = acc[6] / 1e6 + Lp + s.dpsi / 3600.0
    bet = acc[8] / 1e6
    dist = acc[7] / 1000.0 + 385000.56
    dec = dasin(dsin(bet) * dcos(s.eps) + dcos(bet) * dsin(s.eps) * dsin(lam))
    ra = datan2(dsin(lam) * dcos(s.eps) - dtan(bet) * dsin(s.eps), dcos(lam))
    gha = (s.aries - ra + 360.0) % 360.0
    hp = dasin(6378.14 / dist) * 60.0
    sd = 358473400.0 / dist / 60.0
    return gha, dec, hp, sd


PLANET_SERIES = {1: ('VNL', 'VNB', 'VNR'), 2: ('MAL', 'MAB', 'MAR'),
                 3: ('JUL', 'JUB', 'JUR'), 4: ('SAL', 'SAB', 'SAR')}
PLANET_NAME = {1: 'VENUS', 2: 'MARS', 3: 'JUPITER', 4: 'SATURN'}


# PLN3: mean Keplerian elements (Standish, JPL "Approximate positions of the planets",
# 1800-2050): a e I L varpi Omega at J2000 and rates per century. 0 = Earth-Moon barycentre.
KEPLER = {0:((1.00000261,0.01671123,-0.00001531,100.46457166,102.93768193,0.0),(0.00000562,-0.00004392,-0.01294668,35999.37244981,0.32327364,0.0)),
1:((0.72333566,0.00677672,3.39467605,181.97909950,131.60246718,76.67984255),(0.00000390,-0.00004107,-0.00078890,58517.81538729,0.00268329,-0.27769418)),
2:((1.52371034,0.09339410,1.84969142,-4.55343205,-23.94362959,49.55953891),(0.00001847,0.00007882,-0.00813131,19140.30268499,0.44441088,-0.29257343)),
3:((5.20288700,0.04838624,1.30439695,34.39644051,14.72847983,100.47390909),(-0.00011607,-0.00013253,-0.00183714,3034.74612775,0.21252668,0.20469106)),
4:((9.53667594,0.05386179,2.48599187,49.95424423,92.59887831,113.66242448),(-0.00125060,-0.00050991,0.00193609,1222.49362201,-0.41897216,-0.28867794))}


def _helio(b, T):
    e0, r = KEPLER[b]
    a, e, I, L, w, O = [x + y * T for x, y in zip(e0, r)]
    M = L - w
    E = M
    for _ in range(4):
        E = dsin(E) * e * 57.29577951308232 + M
    xv = (dcos(E) - e) * a
    yv = sqrt(1 - e * e) * a * dsin(E)
    rr = hypot(xv, yv)
    u = datan2(yv, xv) + w - O
    z = dsin(u) * dsin(I) * rr
    si = dsin(u) * dcos(I)
    x = (dcos(u) * dcos(O) - si * dsin(O)) * rr
    y = (dcos(u) * dsin(O) + si * dcos(O)) * rr
    return x, y, z


def planet_quick(s, p):
    """PLN3 first step: geometric position from mean elements (within 0.2 deg),
    precessed in longitude. Returns (gha, dec, distance au)."""
    T = s.T
    xe, ye, ze = _helio(0, T)
    xp, yp, zp = _helio(p, T)
    x, y, z = xp - xe, yp - ye, zp - ze
    dist = sqrt(x * x + y * y + z * z)
    lam = datan2(y, x) + T * 1.3969713
    bet = datan2(z, hypot(x, y))
    dec = dasin(dsin(bet) * dcos(23.4393) + dcos(bet) * dsin(23.4393) * dsin(lam))
    ra = datan2(dsin(lam) * dcos(23.4393) - dtan(bet) * dsin(23.4393), dcos(lam))
    return (s.aries - ra) % 360.0, dec, dist


def moon_quick(s):
    """MOOQ: low-precision Moon (Astronomical Almanac), geocentric, within 0.3 deg in Hc.
    Used by BODY to list the bodies above the horizon. Returns (gha, dec)."""
    T = s.T
    lam = T * 481267.881 + 218.32
    for amp, c0, c1 in ((6.29, 135.0, 477198.87), (-1.27, 259.3, -413335.36), (0.66, 235.7, 890534.22),
                        (0.21, 269.9, 954397.74), (-0.19, 357.5, 35999.05), (-0.11, 186.5, 966404.03)):
        lam += dsin(T * c1 + c0) * amp
    bet = 0.0
    for amp, c0, c1 in ((5.13, 93.3, 483202.02), (0.28, 228.2, 960400.89), (-0.28, 318.3, 6003.15),
                        (-0.17, 217.6, -407332.21)):
        bet += dsin(T * c1 + c0) * amp
    dec = dasin(dsin(bet) * dcos(23.4393) + dcos(bet) * dsin(23.4393) * dsin(lam))
    ra = datan2(dsin(lam) * dcos(23.4393) - dtan(bet) * dsin(23.4393), dcos(lam))
    return (s.aries - ra) % 360.0, dec


_FULL = {}
FAST_JD = None          # (first JD, end JD) of the FAST series in use, None = FULL


def fast_out(j):
    """True when FAST series are in use and j is outside their period (flag 12: X)."""
    return FAST_JD is not None and not (FAST_JD[0] <= j <= FAST_JD[1])


def use_series(path=None):
    """Switch the Sun and planet series: None = FULL (VSOP87, as MATA/MATP), or the
    fast_series.json written by tools/almanac/fastseries.py (as MATF). Returns the period."""
    global VL, VB, VR, FAST_JD
    names = ['VL', 'VB', 'VR', 'EEL', 'EEB', 'EER', 'VNL', 'VNB', 'VNR', 'MAL', 'MAB', 'MAR',
             'JUL', 'JUB', 'JUR', 'SAL', 'SAB', 'SAR']
    if not _FULL:
        _FULL.update({n: getattr(_D, n) for n in names})
    if path is None:
        data, period = _FULL, 'FULL'
        FAST_JD = None
    else:
        import json
        with open(path) as fh:
            j = json.load(fh)
        data = {k: [tuple(r) for r in v] for k, v in j['series'].items()}
        period = j['period']
        FAST_JD = tuple(j['jd'])
    for n in names:
        setattr(_D, n, data[n])
    VL, VB, VR = data['VL'], data['VB'], data['VR']
    return period


def planet(s, p, lt=None):
    """PLAN / PLN2. p = 1 Venus, 2 Mars, 3 Jupiter, 4 Saturn.
    Returns (gha, dec, sha, hp) with hp in arcmin. Light time: two passes of the
    series, or one pass when lt (days) is given (PLN3: from the quick distance)."""
    T = s.T
    tau = T / 10.0
    L0, B0, R0 = _ser(_D.EEL, tau), _ser(_D.EEB, tau), _ser(_D.EER, tau)
    sl, sb, sr = (getattr(_D, n) for n in PLANET_SERIES[p])
    passes = 2 if lt is None else 1
    lt = lt or 0.0
    for _ in range(passes):
        tp = tau - lt / 365250.0
        L, B, R = _ser(sl, tp), _ser(sb, tp), _ser(sr, tp)
        x = R * cos(B) * cos(L) - R0 * cos(B0) * cos(L0)
        y = R * cos(B) * sin(L) - R0 * cos(B0) * sin(L0)
        z = R * sin(B) - R0 * sin(B0)
        dist = (x * x + y * y + z * z) ** 0.5
        lt = dist * 0.0057755183
    rho = hypot(x, y)
    lam = (datan2(y, x) + 360.0) % 360.0
    bet = datan2(z, rho)
    lp = lam - T * 1.397                                   # FK5
    lam += ((dcos(lp) + dsin(lp)) * dtan(bet) * 0.03916 - 0.09033) / 3600.0
    bet += (dcos(lp) - dsin(lp)) * 0.03916 / 3600.0
    sun = L0 * 57.29577951308232 + 180.0                   # aberration
    e = T * -0.000042037 + 0.016708634
    pi = T * 1.71946 + 102.93735
    lam += ((dcos(sun - lam) * -20.49552 + dcos(pi - lam) * e * 20.49552) / dcos(bet) + s.dpsi) / 3600.0
    bet += (dsin(sun - lam) - dsin(pi - lam) * e) * dsin(bet) * -20.49552 / 3600.0
    dec = dasin(dsin(bet) * dcos(s.eps) + dcos(bet) * dsin(s.eps) * dsin(lam))
    ra = (datan2(dsin(lam) * dcos(s.eps) - dtan(bet) * dsin(s.eps), dcos(lam)) + 360.0) % 360.0
    gha = (s.aries - ra + 360.0) % 360.0
    sha = (360.0 - ra) % 360.0
    hp = 8.794 / dist / 60.0
    return gha, dec, sha, hp


def hcz(lat, lon, dec, gha):
    """CHZ / HCZ. Returns (hc, zn)."""
    lha = gha + lon
    hc = dasin(dsin(lat) * dsin(dec) + dcos(lat) * dcos(dec) * dcos(lha))
    zn = (datan2(-(dcos(dec) * dsin(lha)), dcos(lat) * dsin(dec) - dsin(lat) * dcos(dec) * dcos(lha))
          + 360.0) % 360.0
    return hc, zn


def hczs(lat, lon, dec, gha):
    """HCZ with sin Hc (the value HCZ keeps in "SHC" for the sine-scale charts).
    Returns (hc, zn, sin hc)."""
    lha = gha + lon
    sh = dsin(lat) * dsin(dec) + dcos(lat) * dcos(dec) * dcos(lha)
    sh = max(-1.0, min(1.0, sh))
    zn = (datan2(-(dcos(dec) * dsin(lha)), dcos(lat) * dsin(dec) - dsin(lat) * dcos(dec) * dcos(lha))
          + 360.0) % 360.0
    return dasin(sh), zn, sh


EVENTS = {'RISE': (-0.8333333333333333, -1), 'SET': (-0.8333333333333333, 1),
          'NTWA': (-12.0, -1), 'NTWP': (-12.0, 1), 'CTWA': (-6.0, -1), 'CTWP': (-6.0, 1),
          'TRAN': (0.0, 0)}


def sun_fast(j):
    """SUNF: low-precision Sun (Astronomical Almanac formula) for the SUNRISE
    iterations: (GHA, Dec) within 0.01 deg, event times within about 15 s."""
    d = j - 2451545.0
    g = d * 0.9856003 + 357.528
    lam = dsin(g) * 1.915 + dsin(g * 2) * 0.02 + d * 0.9856474 + 280.46
    eps = d * -0.0000004 + 23.439
    dec = dasin(dsin(eps) * dsin(lam))
    ra = datan2(dcos(eps) * dsin(lam), dcos(lam))
    return (d * 360.98564736629 + 280.46061837 - ra) % 360.0, dec


def event(j0, lat, lon, kind, sun=None):
    """SUNRISE. j0 = JD at 0h UT. Returns UT hours, 99 if the event does not happen.
    sun(jd) -> (gha, dec) replaces the low-precision Sun (SUNG with almanac tables)."""
    h0, sg = EVENTS[kind]
    t = sg * 6 + 12.0
    for _ in range(10):
        gha, dec = (sun or sun_fast)(t / 24.0 + j0)
        target = 0.0
        if sg:
            c = (dsin(h0) - dsin(lat) * dsin(dec)) / (dcos(lat) * dcos(dec))
            if abs(c) > 1:
                return 99.0
            target = degrees(acos(c)) * sg
        dt = ((target - gha - lon + 540.0) % 360.0 - 180.0) / 15.0
        t += dt
        if abs(dt) <= 0.0003:
            break
    return t


def day0(j):
    """JD of 0h UT of the date of j (LBL 26 in the screens)."""
    return int(j - 0.5) + 0.5


def phase(s):
    """PHAS. s = Sun(jd). Returns (% illuminated, age in days)."""
    D, M, Mp, F = s.args[0], s.args[1], s.args[2], s.args[3]
    i = (180 - D - 6.289 * dsin(Mp) + 2.1 * dsin(M) - 1.274 * dsin(2 * D - Mp)
         - 0.658 * dsin(2 * D) - 0.214 * dsin(2 * Mp) - 0.11 * dsin(D))
    k = (1 + dcos(i)) * 50

    def age_from(dl):
        mn, mpn, fn = M - 0.98560028 * dl, Mp - 13.064993 * dl, F - 13.2293505 * dl
        c = (-0.4072 * dsin(mpn) + 0.17241 * dsin(mn) + 0.01608 * dsin(2 * mpn)
             + 0.01039 * dsin(2 * fn) + 0.00739 * dsin(mpn - mn) - 0.00514 * dsin(mpn + mn)
             + 0.00208 * dsin(2 * mn) - 0.00111 * dsin(mpn - 2 * fn)
             - 0.00057 * dsin(mpn + 2 * fn) + 0.00056 * dsin(2 * mpn + mn))
        return dl - c

    syn = 29.530589
    dl = (D % 360.0) / 12.190749
    age = age_from(dl)
    if age < 0:
        age = age_from(dl + syn)
    elif age > 27:
        a2 = age_from(dl - syn)
        if a2 >= 0:
            age = a2
    return k, age
