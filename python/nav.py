# nav.py - Sun, Aries, stars, sunrise/sunset, Moon phase
# Same method as the C47 programs (SUNA, STAR, SUNRISE, PHAS).
# Runs on a computer (Python 3) and on NumWorks (MicroPython).
# Needs navdata.py in the same place. Time = UT1 (add DUT1 to UTC).
from math import sin, cos, tan, asin, acos, atan2, radians, degrees
from navdata import VL, VB, VR, NU, ST, SN

DT = 69.2   # TT-UT1 seconds


def jd(y, m, d, h=0.0):
    if m <= 2:
        y -= 1
        m += 12
    a = y // 100
    b = 2 - a + a // 4
    return int(365.25 * (y + 4716)) + int(30.6001 * (m + 1)) + d + b - 1524.5 + h / 24.0


def _ser(rows, tau):
    s = 0.0
    for k, A, B, C in rows:
        s += A * cos(B + C * tau) * tau ** k
    return s * 1e-8


def _nut(T):
    a = (297.85036 + 445267.11148 * T, 357.52772 + 35999.05034 * T,
         134.96298 + 477198.867398 * T, 93.27191 + 483202.017538 * T,
         125.04452 - 1934.136261 * T)
    dp = de = 0.0
    for r in NU:
        x = radians(r[0] * a[0] + r[1] * a[1] + r[2] * a[2] + r[3] * a[3] + r[4] * a[4])
        dp += (r[5] + r[6] * T) * sin(x)
        de += (r[7] + r[8] * T) * cos(x)
    return dp * 1e-4, de * 1e-4, a


def sun(j):
    """j = JD (UT1). Returns dict: gha, dec, aries (deg) + internals."""
    T = (j + DT / 86400.0 - 2451545.0) / 36525.0
    tau = T / 10.0
    L = degrees(_ser(VL, tau))
    B = _ser(VB, tau)
    R = _ser(VR, tau)
    lon = (L + 180.0) % 360.0
    lat = -degrees(B)
    Lp = radians(lon - 1.397 * T)
    lat += 0.03916 * (cos(Lp) - sin(Lp)) / 3600.0
    lon -= 0.09033 / 3600.0
    dp, de, args = _nut(T)
    lon += dp / 3600.0 - 20.4898 / R / 3600.0
    eps = (84381.448 - 46.815 * T + de) / 3600.0
    l, b, e = radians(lon), radians(lat), radians(eps)
    dec = degrees(asin(sin(b) * cos(e) + cos(b) * sin(e) * sin(l)))
    ra = degrees(atan2(sin(l) * cos(e) - tan(b) * sin(e), cos(l)))
    d = j - 2451545.0
    gmst = 280.46061837 + 360.98564736629 * d + 0.000387933 * (d / 36525.0) ** 2
    aries = (gmst + dp / 3600.0 * cos(e)) % 360.0
    return {'gha': (aries - ra) % 360.0, 'dec': dec, 'aries': aries, 'T': T,
            'lam': lon, 'eps': eps, 'dpsi': dp, 'deps': de, 'args': args}


def star(j, n):
    """n = almanac star number 1-57 (58 = Polaris). Returns gha, dec, sha."""
    s = sun(j)
    T = s['T']
    a0, d0, pa, pd = ST[n - 1]
    t = T * 100.0
    a = a0 + pa * t / 3.6e6 / cos(radians(d0))
    d = d0 + pd * t / 3.6e6
    ze = (2.650545 + (2306.083227 + (0.2988499 + 0.01801828 * T) * T) * T) / 3600.0
    z = (-2.650545 + (2306.077181 + (1.0927348 + 0.01826837 * T) * T) * T) / 3600.0
    th = ((2004.191903 + (-0.4294934 - 0.04182264 * T) * T) * T) / 3600.0
    az, dr, tr = radians(a + ze), radians(d), radians(th)
    dm = asin(sin(tr) * cos(dr) * cos(az) + cos(tr) * sin(dr))
    am = atan2(cos(dr) * sin(az), cos(tr) * cos(dr) * cos(az) - sin(tr) * sin(dr)) + radians(z)
    e0 = radians(s['eps'] - s['deps'] / 3600.0)
    be = asin(sin(dm) * cos(e0) - cos(dm) * sin(e0) * sin(am))
    la = atan2(sin(am) * cos(e0) + tan(dm) * sin(e0), cos(am))
    ek = 0.016708634 - 0.000042037 * T
    pi = radians(102.93735 + 1.71946 * T)
    su = radians(s['lam'])
    k = 20.49552
    dbe = -k * sin(be) * (sin(su - la) - ek * sin(pi - la))
    dla = (-k * cos(su - la) + ek * k * cos(pi - la)) / cos(be) + s['dpsi']
    la += radians(dla / 3600.0)
    be += radians(dbe / 3600.0)
    e = radians(s['eps'])
    dec = degrees(asin(sin(be) * cos(e) + cos(be) * sin(e) * sin(la)))
    ra = degrees(atan2(sin(la) * cos(e) - tan(be) * sin(e), cos(la))) % 360.0
    sha = (360.0 - ra) % 360.0
    return (s['aries'] + sha) % 360.0, dec, sha


EVENTS = {'rise': (-0.8333333333, -1), 'set': (-0.8333333333, 1),
          'civam': (-6.0, -1), 'civpm': (-6.0, 1),
          'nauam': (-12.0, -1), 'naupm': (-12.0, 1), 'tran': (0.0, 0)}


def event(j0, lat, lon, kind='rise'):
    """j0 = JD at 0h UT, lat N+, lon E+. Returns UT hours, or None."""
    h0, sg = EVENTS[kind]
    t = 12.0 + 6.0 * sg
    for _ in range(10):
        s = sun(j0 + t / 24.0)
        target = 0.0
        if sg:
            c = (sin(radians(h0)) - sin(radians(lat)) * sin(radians(s['dec']))) / \
                (cos(radians(lat)) * cos(radians(s['dec'])))
            if abs(c) > 1:
                return None
            target = sg * degrees(acos(c))
        dt = ((target - s['gha'] - lon + 540.0) % 360.0 - 180.0) / 15.0
        t += dt
        if abs(dt) < 1e-5:
            break
    return t


def phase(j):
    """Returns (% illuminated, age in days since true new moon)."""
    s = sun(j)
    D, M, Mp, F = s['args'][0], s['args'][1], s['args'][2], s['args'][3]
    r = radians
    i = 180 - D - 6.289 * sin(r(Mp)) + 2.1 * sin(r(M)) - 1.274 * sin(r(2 * D - Mp)) \
        - 0.658 * sin(r(2 * D)) - 0.214 * sin(r(2 * Mp)) - 0.11 * sin(r(D))
    k = (1 + cos(r(i))) * 50

    def age_from(dl):
        mn, mpn, fn = M - 0.98560028 * dl, Mp - 13.064993 * dl, F - 13.2293505 * dl
        c = (-0.4072 * sin(r(mpn)) + 0.17241 * sin(r(mn)) + 0.01608 * sin(r(2 * mpn))
             + 0.01039 * sin(r(2 * fn)) + 0.00739 * sin(r(mpn - mn)) - 0.00514 * sin(r(mpn + mn))
             + 0.00208 * sin(r(2 * mn)) - 0.00111 * sin(r(mpn - 2 * fn))
             - 0.00057 * sin(r(mpn + 2 * fn)) + 0.00056 * sin(r(2 * mpn + mn)))
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


# ---------- formatting and menu ----------
def dm(x, ns=False):
    s = ''
    if ns:
        s = 'S ' if x < 0 else 'N '
        x = abs(x)
    x = x % 360.0 if not ns else x
    d = int(x)
    m = round((x - d) * 60, 1)
    if m >= 60:
        d += 1
        m = 0.0
    return '%s%d %04.1f\'' % (s, d, m)


def hms(t):
    if t is None:
        return 'none'
    s = int(round(t * 3600))
    return '%02d:%02d:%02d' % ((s // 3600) % 24, (s % 3600) // 60, s % 60)


def ask_date():
    y = int(input('Year: '))
    m = int(input('Month: '))
    d = int(input('Day: '))
    return y, m, d


def ask_ut():
    s = input('UT hh:mm:ss: ').split(':')
    while len(s) < 3:
        s.append('0')
    return int(s[0]) + int(s[1]) / 60.0 + float(s[2]) / 3600.0


def menu():
    while True:
        print('1 Sun  2 Star  3 Rise/Set')
        print('4 Moon phase  0 Quit')
        c = input('> ')
        if c == '0':
            break
        y, m, d = ask_date()
        if c == '1':
            s = sun(jd(y, m, d, ask_ut()))
            print('GHA Sun ', dm(s['gha']))
            print('Dec Sun ', dm(s['dec'], True))
            print('GHA Aries', dm(s['aries']))
        elif c == '2':
            n = int(input('Star no 1-58: '))
            g, de, sha = star(jd(y, m, d, ask_ut()), n)
            print('%d %s' % (n, SN[n - 1]))
            print('GHA', dm(g), ' SHA', dm(sha))
            print('Dec', dm(de, True))
        elif c == '3':
            la = float(input('Lat (N+): '))
            lo = float(input('Lon (E+ W-): '))
            j0 = jd(y, m, d)
            for k in ('nauam', 'civam', 'rise', 'tran', 'set', 'civpm', 'naupm'):
                print('%-6s %s UT' % (k, hms(event(j0, la, lo, k))))
        elif c == '4':
            k, a = phase(jd(y, m, d, ask_ut()))
            print('Illum %.1f%%  age %.2f d' % (k, a))


if __name__ == '__main__':
    menu()
