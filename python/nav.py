# nav.py - Sun, Aries, stars, sunrise/sunset, Moon phase, Hc/Zn
# Same method as the C47 programs (SUNA, STAR, SUNRISE, PHAS, HCZ).
# Runs on a computer (Python 3), on NumWorks and on HP Prime (MicroPython).
# Needs navdata.py in the same place. Time = UT1 (add DUT1 to UTC).
from math import sin, cos, tan, asin, acos, atan2, radians, degrees
from navdata import VL, VB, VR, NU, ST, SN, BR

DT = 69.2   # TT-UT1 seconds


def jd(y, m, d, h=0.0):
    if m <= 2:
        y -= 1
        m += 12
    a = y // 100
    b = 2 - a + a // 4
    return int(365.25 * (y + 4716)) + int(30.6001 * (m + 1)) + d + b - 1524.5 + h / 24.0


def _ser(rows, tau):
    """sum A cos(B + C tau) tau^k x 1E-8: the terms of each power k summed, then the powers by Horner
    (as the C47 SER: no tau ** k per term)."""
    g = _GROUPS.get(id(rows))
    if g is None:
        g = {}
        for k, A, B, C in rows:
            g.setdefault(int(k), []).append((A, B, C))
        g = _GROUPS[id(rows)] = [g.get(k, []) for k in range(max(g) + 1)]
    s = 0.0
    for terms in reversed(g):
        s = s * tau + sum(A * cos(B + C * tau) for A, B, C in terms)
    return s * 1e-8


_GROUPS = {}


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
            'lam': lon, 'eps': eps, 'dpsi': dp, 'deps': de, 'args': args,
            'sd': 15.99383 / R}


def star(j, n, s=None):
    """n = almanac star number 1-57 (58 = Polaris). Returns gha, dec, sha.
    s = sun(j) if already computed."""
    if s is None:
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


_OBS = [None, 0.0, 1.0]            # the observer's n-vector: latitude, its sine and cosine (once per place)


def hcz(lat, lon, dec, gha):
    """HCZ: returns Hc, Zn (deg) and sin Hc (for the sine-scale charts). The observer's sin / cos of the latitude
    are kept from the last call (the C47 HCZI: one place, many bodies)."""
    if _OBS[0] != lat:
        la = radians(lat)
        _OBS[:] = [lat, sin(la), cos(la)]
    _, sl, cl = _OBS
    de, t = radians(dec), radians(gha + lon)
    sd, cd, ct = sin(de), cos(de), cos(t)
    sh = sl * sd + cl * cd * ct
    sh = max(-1.0, min(1.0, sh))
    zn = degrees(atan2(-cd * sin(t), cl * sd - sl * cd * ct))
    return degrees(asin(sh)), (zn + 360.0) % 360.0, sh


NBODY = 8      # the same bodies on every view (as the C47 views): Sun + 7 stars here


def bodies(j, lat, lon, n=NBODY, hmin=10.0):
    """Table rule of ALMF / HORZ without Moon and planets: the Sun (always), then
    the brightest stars higher than hmin, n rows in all.
    Returns (rows, sun); row = (id, gha, dec, hc, zn, sin hc), id 0 = Sun."""
    s = sun(j)
    out = [(0, s['gha'], s['dec']) + hcz(lat, lon, s['dec'], s['gha'])]
    for k in BR:
        if len(out) >= n:
            break
        g, d, _ = star(j, k, s)
        h = hcz(lat, lon, d, g)
        if h[0] > hmin:
            out.append((k, g, d) + h)
    return out, s


def cal(j):
    """JD -> (year, month, day, UT hours)."""
    z = int(j + 0.5)
    f = j + 0.5 - z
    a = int((z - 1867216.25) / 36524.25)
    a = z + 1 + a - a // 4
    b = a + 1524
    c = int((b - 122.1) / 365.25)
    d = int(365.25 * c)
    e = int((b - d) / 30.6001)
    day = b - d - int(30.6001 * e)
    m = e - 1 if e < 14 else e - 13
    return (c - 4716 if m > 2 else c - 4715), m, day, f * 24.0


def phase_index(age):
    """0 new, 1 waxing crescent, 2 first quarter, 3 waxing gibbous, 4 full, 5 waning gibbous,
    6 last quarter, 7 waning crescent: the age in eight equal steps (the glyph of the views)."""
    return int(age / 29.530589 * 8 + 0.5) % 8


def daylight(sun_hc):
    """DAY / TWILIGHT / NIGHT from the Sun's Hc (as the C47 chart views)."""
    return 'DAY' if sun_hc > 0 else 'TWILIGHT' if sun_hc > -12 else 'NIGHT'


def moonword(k, age):
    if k >= 99.5:
        return 'FULL'
    if k < 0.5:
        return 'NEW'
    return 'WANING' if age > 14.765 else 'WAXING'


# ---------- formatting (rounding as the C47 printers PDM PZN PHM PF1) ----------
def fdm(v):
    """'174 26.9' (deg, min to 0.1'), '-' in front when negative."""
    t = int(abs(v) * 600 + 0.5)
    d = t // 600
    t -= d * 600
    return '%s%d %02d.%d' % ('-' if v < 0 else '', d, t // 10, t % 10)


def fns(v, p='NS', w=8):
    """'N 19 02.7', 'S  0 22.8' (degrees right-aligned in w - 5 digits)."""
    s = ' ' + fdm(abs(v))
    while len(s) < w:
        s = ' ' + s
    return (p[1] if v < 0 else p[0]) + s


def fzn(v):
    t = int(v * 10 + 0.5)
    if t >= 3600:
        t = 0
    return '%03d.%d' % (t // 10, t % 10)


def fhm(h):
    if h is None or h > 98:
        return '--:--'
    m = int(h * 60 + 0.5) % 1440
    return '%02d:%02d' % (m // 60, m % 60)


def f1(v):
    m = int(abs(v) * 10 + 0.5)
    return '%d.%d' % (m // 10, m % 10)


def fdate(j):
    y, m, d, h = cal(j)
    return '%02d-%02d-%04d' % (d, m, y)


def almanac(j, lat, lon, n=NBODY):
    """The ALMANAC page (ALMF) as strings.
    head: date, UT, lat, lon, GHA Aries
    rows: (id, name, GHA, Dec, Hc, Zn, hc)
    foot: naut twi am, pm, rise, set, mer pass, Sun SD, Moon %, word, age"""
    rows, s = bodies(j, lat, lon, n)
    head = (fdate(j), fhm(cal(j)[3]), fns(lat, 'NS', 0), fns(lon, 'EW', 0), fdm(s['aries']))
    tab = []
    for k, g, d, hc, zn, sh in rows:
        tab.append((k, 'SUN' if k == 0 else SN[k - 1].upper(), fdm(g), fns(d),
                    fdm(hc), fzn(zn), hc))
    j0 = int(j - 0.5) + 0.5
    foot = [fhm(event(j0, lat, lon, e)) for e in ('nauam', 'naupm', 'rise', 'set', 'tran')]
    k, a = phase(j)
    foot += [f1(s['sd']), '%d' % int(k + 0.5), moonword(k, a), f1(a)]
    return head, tab, foot


def page(j, lat, lon):
    """Text lines of the ALMANAC page (menu 5; the graphic views draw the same strings)."""
    h, tab, f = almanac(j, lat, lon)
    out = ['%s %s UT  DR %s %s' % (h[0], h[1], h[2], h[3]),
           '%-18s %9s %10s %9s %6s' % ('BODY', 'GHA', 'DEC', 'HC', 'ZN'),
           '%-18s %9s' % ('ARIES', h[4])]
    for k, nm, g, d, hc, zn, x in tab:
        out.append('%-18s %9s %10s %9s %6s' % (('%2d ' % k if k else '   ') + nm, g, d, hc, zn))
    out.append('NAUT TWI %s %s  MOON %s%% %s' % (f[0], f[1], f[6], f[7]))
    out.append('RISE/SET %s %s  AGE %s DAYS' % (f[2], f[3], f[8]))
    out.append('MER PASS %s  SD %s' % (f[4], f[5]))
    return out


# ---------- menu ----------
def dm(x, ns=False):
    if ns:
        return fns(x, 'NS', 0) + "'"
    return fdm(x % 360.0) + "'"


def hms(t):
    if t is None:
        return 'none'
    s = int(round(t * 3600))
    return '%02d:%02d:%02d' % ((s // 3600) % 24, (s % 3600) // 60, s % 60)


def _ask(p, parse):
    """input() until parse(text) works: a typing slip asks again instead of
    stopping the program with an error (the calculator apps close on an error)."""
    while True:
        try:
            return parse(input(p).strip())
        except Exception:
            print('?')


def _int_in(lo, hi):
    def f(t):
        v = int(t)
        if not lo <= v <= hi:
            raise ValueError
        return v
    return f


def ask_date():
    y = _ask('Year: ', _int_in(1900, 2100))
    m = _ask('Month: ', _int_in(1, 12))
    d = _ask('Day: ', _int_in(1, 31))
    return y, m, d


def _ut(t):
    """'14:57', '14:57:30', '14 57' or the C47 way '14.57' / '14.5730' (hh.mmss)."""
    s = t.replace(':', ' ').split()
    if len(s) == 1 and '.' in s[0]:
        h, r = s[0].split('.')
        r = (r + '0000')[:4]
        s = [h, r[:2], r[2:]]
    while len(s) < 3:
        s.append('0')
    h, m, x = int(s[0]), int(s[1]), float(s[2])
    if not (0 <= h < 24 and 0 <= m < 60 and 0 <= x < 60):
        raise ValueError
    return h + m / 60.0 + x / 3600.0


def ask_ut():
    return _ask('UT hh:mm:ss: ', _ut)


def _ang(t):
    s = t.replace(':', ' ').split()
    v = abs(float(s[0])) + (float(s[1]) / 60.0 if len(s) > 1 else 0.0)
    return -v if s[0][0] == '-' else v


def ask_ang(p):
    """'25.5' (degrees) or '25 30' (degrees minutes); '-' = S or W."""
    return _ask(p, _ang)


def menu():
    while True:
        print('1 Sun  2 Star  3 Rise/Set')
        print('4 Moon phase  5 Almanac')
        print('0 Quit')
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
            la = ask_ang('Lat (N+): ')
            lo = ask_ang('Lon (E+ W-): ')
            j0 = jd(y, m, d)
            for k in ('nauam', 'civam', 'rise', 'tran', 'set', 'civpm', 'naupm'):
                print('%-6s %s UT' % (k, hms(event(j0, la, lo, k))))
        elif c == '4':
            k, a = phase(jd(y, m, d, ask_ut()))
            print('Illum %.1f%%  age %.2f d' % (k, a))
        elif c == '5':
            j = jd(y, m, d, ask_ut())
            la = ask_ang('Lat (N+): ')
            lo = ask_ang('Lon (E+ W-): ')
            for t in page(j, la, lo):
                print(t)


if __name__ == '__main__':
    menu()
