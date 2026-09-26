"""c47screen.py - the C47_nav screens rebuilt in plain Python.

A Screen is the C47 LCD: 400 x 240 pixels, origin bottom-left (like PIXEL / AGRAPH).
The text routines copy PTXB (5x7 font), PTXT (3x5 font) and their number printers
(PDM PZN PHM PDAT PINB PF1 PHL PTNS PT1); the layouts copy ALMF, HALMV, HORZ, HORZS;
almt() gives the ALMT text lines (STXT formats).
"""
import c47astro as A

from c47font import BIG, SMALL
from c47data import STAR_NAME, BRIGHT

W, H = 400, 240
SYM = {1: '<', 2: '>', 3: '=', 4: '?'}                 # Venus Mars Jupiter Saturn glyphs
PNAME = {1: 'VENUS', 2: 'MARS', 3: 'JUPITER', 4: 'SATURN'}
WARNING = 'DOES NOT REPLACE THE NAUTICAL ALMANAC'


def ip(x):
    return int(x)                                       # C47 IP: truncate toward zero


class Screen:
    def __init__(self):
        self.pix = set()                                 # (x, y), y from the bottom

    # --- drawing primitives
    def pixel(self, y, x):
        """PIXEL: y, x >= 0 one dot; x < 0 vertical line at -x; y < 0 horizontal line at -y."""
        y, x = ip(y), ip(x)
        if x >= 0 and y >= 0:
            self.pix.add((x, y))
        if x < 0:
            self.pix.update((-x, yy) for yy in range(240))
        if y < 0:
            self.pix.update((xx, -y) for xx in range(400))

    def hline(self, y, x, n):                            # PHL
        for i in range(ip(n)):
            self.pix.add((ip(x) + i, ip(y)))
        return x + n

    def glyph(self, font, ch, y, x):
        adv, yoff, cols = font[ord(ch)]
        for cx, mask in cols:
            i = 0
            while mask:
                if mask & 1:
                    self.pix.add((x + cx, y + yoff + i))
                mask >>= 1; i += 1
        return x + adv

    def text(self, y, x, s, font=BIG):                   # PTXB / PTXT
        for ch in s:
            x = self.glyph(font, ch, y, x)
        return x

    def small(self, y, x, s):
        return self.text(y, x, s, SMALL)

    # --- number printers (big font)
    def _digits(self, y, x, n, font=BIG):
        if n > 99:
            x = self.glyph(font, chr(48 + ip(n / 100)), y, x)
        if n > 9:
            x = self.glyph(font, chr(48 + ip(n / 10) % 10), y, x)
        return self.glyph(font, chr(48 + n % 10), y, x)

    def pinb(self, y, x, v):
        return self._digits(y, x, ip(abs(v) + 0.5))

    def pf1(self, y, x, v):
        m = ip(abs(v) * 10 + 0.5)
        x = self._digits(y, x, ip(m / 10))
        x = self.glyph(BIG, '.', y, x)
        return self.glyph(BIG, chr(48 + m % 10), y, x)

    def phm(self, y, x, h):
        if h > 98:
            return self.text(y, x, '--:--')
        m = ip(h * 60 + 0.5)
        hh = ip(m / 60) % 24
        mm = m % 60
        return self.text(y, x, '%d%d:%d%d' % (ip(hh / 10), hh % 10, ip(mm / 10), mm % 10))

    def pdm(self, y, x, v):
        """Degrees and minutes, right-aligned in 3 digits, with a sign cell."""
        t = ip(abs(v) * 600 + 0.5)
        d = ip(t / 600)
        t -= d * 600
        if not d > 99:
            x += 6
        if not d > 9:
            x += 6
        x = self.glyph(BIG, '-' if v < 0 else ' ', y, x)
        x = self._digits(y, x, d)
        x = self.glyph(BIG, ' ', y, x)
        return self.text(y, x, '%d%d.%d' % (ip(t / 100), ip(t / 10) % 10, t % 10))

    def pzn(self, y, x, v):
        t = ip(v * 10 + 0.5)
        if 3600 <= t:
            t = 0
        return self.text(y, x, '%d%d%d.%d' % (ip(t / 1000), ip(t / 100) % 10, ip(t / 10) % 10, t % 10))

    def pdat(self, y, x, j):
        d, m, yr = jd_to_date(j)
        return self.text(y, x, '%02d-%02d-%02d%02d' % (d, m, ip(yr / 100), yr % 100))

    # --- small font numbers
    def ptns(self, y, x, v):
        return self._digits(y, x, ip(abs(v) + 0.5), SMALL)

    def pt1(self, y, x, v):
        m = ip(abs(v) * 10 + 0.5)
        x = self._digits(y, x, ip(m / 10), SMALL)
        x = self.glyph(SMALL, '.', y, x)
        return self.glyph(SMALL, chr(48 + m % 10), y, x)

    # --- output
    def rows(self):
        """Lit pixels as (x, row) with row 0 at the top, clipped to the screen."""
        return {(x, H - 1 - y) for x, y in self.pix if 0 <= x < W and 0 <= y < H}


def jd_to_date(j):
    z = ip(j + 0.5)
    al = ip((z - 1867216.25) / 36524.25)
    b = z + 1 + al - ip(al / 4) + 1524
    c = ip((b - 122.1) / 365.25)
    b -= ip(c * 365.25)
    e = ip(b / 30.6001)
    day = b - ip(e * 30.6001)
    mon = e - 1
    if 12 < mon:
        mon -= 12
    yr = c - 4716
    if 2 >= mon:
        yr += 1
    return day, mon, yr


def ut_hours(j):
    return (j + 0.5) % 1 * 24


# ---------------------------------------------------------------- shared data
class Almanac:
    """Everything the screens show for one JD and position."""

    def __init__(self, j, lat, lon):
        self.j, self.lat, self.lon = j, lat, lon
        j0 = A.day0(j)
        self.times = {k: A.event(j0, lat, lon, k) for k in ('NTWA', 'RISE', 'TRAN', 'SET', 'NTWP')}
        self.sun = s = A.Sun(j)
        self.illum, self.age = A.phase(s)
        self.moon = A.moon(s)
        self.planets = {p: A.planet(s, p) for p in (1, 2, 3, 4)}
        self._stars = {}

    def star(self, n):
        if n not in self._stars:
            self._stars[n] = A.star(self.sun, n)
        return self._stars[n]

    def hcz(self, dec, gha):
        return A.hcz(self.lat, self.lon, dec, gha)

    def bodies(self, star_min=10.0, max_rows=10, max_stars=99):
        """Table rule of ALMF / HALMV / ALMT: Sun; Moon and planets above the horizon;
        then the brightest stars higher than star_min until max_rows.
        Rows: (id, gha, dec, hc, zn); id 0 Sun, -1 Moon, -2..-5 planets, n star."""
        s = self.sun
        out = [(0, s.gha, s.dec) + self.hcz(s.dec, s.gha)]
        m = self.moon
        hc, zn = self.hcz(m[1], m[0])
        if hc > 0:
            out.append((-1, m[0], m[1], hc, zn))
        for p in (1, 2, 3, 4):
            g, d = self.planets[p][0], self.planets[p][1]
            hc, zn = self.hcz(d, g)
            if hc > 0:
                out.append((-(p + 1), g, d, hc, zn))
        for n in BRIGHT:
            if len(out) >= max_rows:
                break
            g, d, _ = self.star(n)
            hc, zn = self.hcz(d, g)
            if hc > star_min:
                out.append((n, g, d, hc, zn))
        return out


def mark(sc, y, x, ident):
    """Symbol of a body in the big font."""
    ch = '@' if ident == 0 else '(' if ident == -1 else SYM[-ident - 1] if ident < 0 else '*'
    return sc.glyph(BIG, ch, y, x)


def body_name(ident):
    return 'SUN' if ident == 0 else 'MOON' if ident == -1 else PNAME[-ident - 1] if ident < 0 else STAR_NAME[ident]


# ---------------------------------------------------------------- ALMF
def almf(al):
    sc = Screen()
    GX, DX, HX, ZX = 112, 184, 256, 330
    s, t = al.sun, al.times
    sc.pdat(229, 4, al.j)
    sc.phm(229, 76, ut_hours(al.j)); sc.text(229, 112, 'UT')
    sc.text(229, 142, 'DR')
    sc.text(229, 160, 'S' if al.lat < 0 else 'N'); sc.pdm(229, 160, abs(al.lat))
    sc.text(229, 220, 'W' if al.lon < 0 else 'E'); sc.pdm(229, 226, abs(al.lon))
    sc.text(229, 292, 'ARIES'); sc.pdm(229, 328, s.aries)
    sc.pixel(-219, 0)
    sc.text(207, 34, 'BODY'); sc.text(207, GX + 36, 'GHA'); sc.text(207, DX + 36, 'DEC')
    sc.text(207, HX + 42, 'HC'); sc.text(207, ZX + 18, 'ZN')
    y = 194
    for ident, g, d, hc, zn in al.bodies():
        mark(sc, y, 4, ident)
        if ident > 0:
            sc.pinb(y, 16, ident)
        sc.text(y, 34, body_name(ident))
        sc.pdm(y, GX, g)
        sc.text(y, DX, 'S' if d < 0 else 'N'); sc.pdm(y, DX, abs(d))
        sc.pdm(y, HX, hc); sc.pzn(y, ZX, zn)
        if hc < 0:
            sc.hline(y - 1, HX, 54)
        y -= 11
    sc.pixel(-80, 0)
    sc.text(69, 4, 'SUN UT'); sc.text(69, 94, 'AM'); sc.text(69, 136, 'PM')
    sc.text(69, 184, 'MOON'); x = sc.pinb(69, 220, al.illum); sc.text(69, x, '%')
    sc.text(69, 262, 'WANING' if 14.765 < al.age else 'WAXING')
    sc.text(57, 4, 'NAUT TWI'); sc.phm(57, 85, t['NTWA']); sc.phm(57, 127, t['NTWP'])
    x = sc.text(57, 184, 'AGE '); x = sc.pf1(57, x, al.age); sc.text(57, x, ' DAYS')
    sc.text(45, 4, 'RISE/SET'); sc.phm(45, 85, t['RISE']); sc.phm(45, 127, t['SET'])
    x = sc.text(45, 184, 'SUN SD '); sc.pf1(45, x, s.sd)
    sc.text(33, 4, 'MER PASS'); sc.phm(33, 106, t['TRAN'])
    x = sc.text(33, 184, 'MOON HP '); x = sc.pf1(33, x, al.moon[2]); x = sc.text(33, x, ' SD '); sc.pf1(33, x, al.moon[3])
    sc.pixel(-22, 0)
    sc.text(8, 89, WARNING)
    return [sc.rows()]


# ---------------------------------------------------------------- HALMV
def halmv(al):
    sc = Screen()
    X0 = 206
    s, t = al.sun, al.times
    sc.pixel(0, -201)
    sc.hline(14, 18, 179)
    for y in range(14, 215):
        sc.pixel(y, 17)
    for y in (80, 147, 214):
        sc.pixel(y, 15); sc.pixel(y, 16)
    for y, v in ((77, 30), (144, 60), (211, 90)):
        sc.pinb(y, 2, v)
    off = 180 if al.lat < 0 else 0
    for x, l in zip((16, 60, 105, 149, 192), 'SWNES' if off else 'NESWN'):
        sc.text(3, x, l)

    def pos(dec, gha):
        hc, zn = al.hcz(dec, gha)
        return hc, zn, ip((zn + off) % 360 * 178 / 360 + 18), ip(hc * 200 / 90 + 14)

    for g in range(0, 358, 3):                               # celestial equator
        hc, zn, x, y = pos(0, g)
        if hc > 0:
            sc.pixel(y, x)
    sc.text(230, X0, 'DR')
    sc.text(230, X0 + 18, 'S' if al.lat < 0 else 'N'); sc.pdm(230, X0 + 18, abs(al.lat))
    sc.text(230, X0 + 78, 'W' if al.lon < 0 else 'E'); sc.pdm(230, X0 + 84, abs(al.lon))
    sc.pdat(220, X0, al.j); sc.phm(220, X0 + 66, ut_hours(al.j)); sc.text(220, X0 + 102, 'UT')
    sc.text(210, X0, 'ARIES'); sc.pdm(210, X0 + 36, s.aries); sc.text(210, X0 + 102, 'SUN SD'); sc.pf1(210, X0 + 144, s.sd)
    sc.text(200, X0, 'SUN GHA'); sc.pdm(200, X0 + 48, s.gha)
    sc.text(200, X0 + 108, 'S' if s.dec < 0 else 'N'); sc.pdm(200, X0 + 108, abs(s.dec))
    sc.text(188, X0 + 30, 'BODY'); sc.text(188, X0 + 132, 'HC'); sc.text(188, X0 + 168, 'ZN')
    y = 178
    for ident, g, d, hc, zn in al.bodies():
        _, _, cx, cy = pos(d, g)
        if ident == 0:
            if hc > 0:
                sc.glyph(BIG, '@', cy - 3, cx - 5)
        elif ident < 0:
            mark(sc, cy - 3, cx - 3, ident)
        else:
            sc.glyph(BIG, '*', cy - 3, cx - 3)
            lx = cx + 6
            if lx > 187:
                lx -= 22
            sc.pinb(cy - 3, lx, ident)
        mark(sc, y, X0, ident)
        if ident > 0:
            sc.pinb(y, X0 + 12, ident)
        sc.text(y, X0 + 30, body_name(ident))
        sc.pdm(y, X0 + 90, hc); sc.pzn(y, X0 + 150, zn)
        if hc < 0:
            sc.hline(y - 1, X0 + 90, 54)
        y -= 10
    sc.hline(86, 204, 196)
    sc.text(76, X0, 'SUN UT'); sc.text(76, X0 + 93, 'AM'); sc.text(76, X0 + 135, 'PM')
    sc.text(66, X0, 'NAUT TWI'); sc.phm(66, X0 + 84, t['NTWA']); sc.phm(66, X0 + 126, t['NTWP'])
    sc.text(56, X0, 'RISE/SET'); sc.phm(56, X0 + 84, t['RISE']); sc.phm(56, X0 + 126, t['SET'])
    sc.text(46, X0, 'MER PASS'); sc.phm(46, X0 + 105, t['TRAN'])
    sc.hline(39, 204, 196)
    x = sc.text(29, X0, 'MOON '); x = sc.pinb(29, x, al.illum); x = sc.text(29, x, '% ')
    x = sc.text(29, x, 'WANING' if 14.765 < al.age else 'WAXING'); x = sc.text(29, x, ' AGE '); sc.pf1(29, x, al.age)
    x = sc.text(19, X0, 'MOON HP '); x = sc.pf1(19, x, al.moon[2]); x = sc.text(19, x, ' SD '); sc.pf1(19, x, al.moon[3])
    sc.small(8, X0 + 24, WARNING)
    return [sc.rows()]


# ---------------------------------------------------------------- HORZ / HORZS
def horz(al, info=True, nstars=5):
    """Horizon chart. With info (HORZ) returns one frame per object, the top line
    naming it; without (HORZS) one frame."""
    sc = Screen()
    sc.hline(16, 20, 376)
    for y in range(18, 217, 3):
        sc.pixel(y, 18)
    for c in (20, 51, 82, 113, 145, 176, 207, 238, 270, 301, 332, 363, 395):
        for y in (15, 14, 13):
            sc.pixel(y, c)
    for y in (83, 150, 216):
        for x in (15, 16, 17):
            sc.pixel(y, x)
    for y, v in ((81, 30), (148, 60), (214, 90)):
        sc.ptns(y, 2, v)
    off = 180 if al.lat < 0 else 0
    for x, l in zip((19, 112, 206, 300, 394), 'SWNES' if off else 'NESWN'):
        sc.small(7, x, l)

    def pos(dec, gha):
        hc, zn = al.hcz(dec, gha)
        return hc, zn, ip((zn + off) % 360 * 375 / 360 + 20), ip(225 - hc * 200 / 90)

    for g in range(0, 359, 2):
        hc, zn, x, y = pos(0, g)
        if hc >= 0:
            sc.pixel(241 - y, x)
    objs = []

    def record(ident, zn, hc, dec):
        objs.append((ident, zn, hc))

    s = al.sun
    hc, zn, x, y = pos(s.dec, s.gha)
    if hc > 0:
        sc.glyph(BIG, '@', 238 - y, x - 5); record(0, zn, hc, s.dec)
    m = al.moon
    hc, zn, x, y = pos(m[1], m[0])
    if hc > 0:
        sc.glyph(BIG, '(', 241 - y - 3, x - 3); record(-1, zn, hc, m[1])
    for p in (1, 2, 3, 4):
        g, d = al.planets[p][0], al.planets[p][1]
        hc, zn, x, y = pos(d, g)
        if hc > 0:
            sc.glyph(BIG, SYM[p], 241 - y - 3, x - 3); record(-(p + 1), zn, hc, d)
    cnt = 0
    for n in BRIGHT:
        g, d, _ = al.star(n)
        hc, zn, x, y = pos(d, g)
        if hc > 10:
            sc.glyph(BIG, '*', 241 - y - 3, x - 3)
            lx = x + 5
            if lx > 385:
                lx -= 17
            sc.ptns(239 - y, lx, n)
            record(n, zn, hc, d); cnt += 1
        if cnt >= nstars:
            break
    if not info or not objs:
        return [sc.rows()]
    frames = []
    for ident, zn, hc in objs:
        sc.pix = {p for p in sc.pix if p[1] < 228}
        if ident > 0:
            x = sc.ptns(234, 2, ident); x = sc.small(234, x, ' '); x = sc.small(234, x, STAR_NAME[ident])
        else:
            x = sc.small(234, 2, body_name(ident))
        x = sc.small(234, x, ' ZN '); x = sc.pt1(234, x, zn); x = sc.small(234, x, ' HC '); sc.pt1(234, x, hc)
        frames.append(sc.rows())
    return frames


# ---------------------------------------------------------------- ALMT (text)
def _int_str(n):
    s = ''
    if n > 99:
        s += chr(48 + ip(n / 100))
    if n > 9:
        s += chr(48 + ip(n / 10) % 10)
    return s + chr(48 + n % 10)


def sdm(v):
    t = ip(abs(v) * 600 + 0.5)
    d = ip(t / 600); t -= d * 600
    return ('-' if v < 0 else '') + _int_str(d) + '°%d%d.%d\'' % (ip(t / 100), ip(t / 10) % 10, t % 10)


def sns(v): return ('S ' if v < 0 else 'N ') + sdm(abs(v))
def sew(v): return ('W ' if v < 0 else 'E ') + sdm(abs(v))


def szn(v):
    t = ip(v * 10 + 0.5) % 3600
    return '%d%d%d.%d°' % (ip(t / 1000), ip(t / 100) % 10, ip(t / 10) % 10, t % 10)


def shm(h):
    if h > 98:
        return '--:--'
    m = ip(h * 60 + 0.5)
    hh = ip(m / 60) % 24; mm = m % 60
    return '%d%d:%d%d' % (ip(hh / 10), hh % 10, ip(mm / 10), mm % 10)


def sf1(v):
    m = ip(abs(v) * 10 + 0.5)
    return _int_str(ip(m / 10)) + '.' + chr(48 + m % 10)


def sint(v): return _int_str(ip(abs(v) + 0.5))


def sdat(j):
    d, m, y = jd_to_date(j)
    return '%02d-%02d-%02d%02d' % (d, m, ip(y / 100), y % 100)


def almt(al):
    s, t = al.sun, al.times
    L = [sdat(al.j) + '  ' + shm(ut_hours(al.j)) + ' UT',
         'DR ' + sns(al.lat) + '  ' + sew(al.lon),
         'GHA ARIES ' + sdm(s.aries)]
    for ident, g, d, hc, zn in al.bodies():
        name = sint(ident) + ' ' + STAR_NAME[ident] if ident > 0 else body_name(ident)
        L.append(('* ' if hc < 0 else '') + name + ' HC ' + sdm(hc) + ' ZN ' + szn(zn))
        L.append('   GHA ' + sdm(g) + ' DEC ' + sns(d))
        if ident == -1:
            L.append('   HP ' + sf1(al.moon[2]) + "' SD " + sf1(al.moon[3]) + "'")
    L.append('NAUT TWI ' + shm(t['NTWA']) + '  ' + shm(t['NTWP']) + ' UT')
    L.append('SUNRISE ' + shm(t['RISE']) + '  SUNSET ' + shm(t['SET']))
    L.append('MER PASS ' + shm(t['TRAN']) + ' UT   SUN SD ' + sf1(s.sd) + "'")
    L.append('MOON ' + sint(al.illum) + '% ' + ('WANING' if 14.765 < al.age else 'WAXING') + ' AGE ' + sf1(al.age) + ' D')
    L.append(WARNING)
    return L


VIEWS = {'ALMF': almf, 'HALMV': halmv, 'HORZ': lambda al: horz(al, True), 'HORZS': lambda al: horz(al, False)}
