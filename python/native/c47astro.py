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


def planet(s, p):
    """PLAN / PLN2. p = 1 Venus, 2 Mars, 3 Jupiter, 4 Saturn.
    Returns (gha, dec, sha, hp) with hp in arcmin."""
    T = s.T
    tau = T / 10.0
    L0, B0, R0 = _ser(_D.EEL, tau), _ser(_D.EEB, tau), _ser(_D.EER, tau)
    sl, sb, sr = (getattr(_D, n) for n in PLANET_SERIES[p])
    lt = 0.0
    for _ in range(2):
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


EVENTS = {'RISE': (-0.8333333333333333, -1), 'SET': (-0.8333333333333333, 1),
          'NTWA': (-12.0, -1), 'NTWP': (-12.0, 1), 'CTWA': (-6.0, -1), 'CTWP': (-6.0, 1),
          'TRAN': (0.0, 0)}


def event(j0, lat, lon, kind, sun=None):
    """SUNRISE. j0 = JD at 0h UT. Returns UT hours, 99 if the event does not happen.
    sun(jd) -> (gha, dec) replaces the series (SUNG with almanac tables)."""
    h0, sg = EVENTS[kind]
    t = sg * 6 + 12.0
    for _ in range(10):
        if sun:
            gha, dec = sun(t / 24.0 + j0)
        else:
            s = Sun(t / 24.0 + j0)
            gha, dec = s.gha, s.dec
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
