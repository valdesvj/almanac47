"""c47screen.py - the C47_nav screens rebuilt in plain Python.

A Screen is the C47 LCD: 400 x 240 pixels, origin bottom-left (like PIXEL / AGRAPH).
The text routines copy PTXS (C47 status-bar font; PTXB 5x7 for older views), PTXT (3x5) and their number printers
(PDM PZN PHM PDAT PINB PF1 PHL PTNS PT1); the layouts copy ALMF, HALMV, HORZ, HORZS;
almt() gives the ALMT text lines (STXT formats).
"""
import re
import c47astro as A
from decimal import Decimal as _D, localcontext as _lc

from c47font import BIG, SMALL
from c47fonts2 import STD
from c47data import STAR_NAME, BRIGHT

W, H = 400, 240
SYM = {1: '<', 2: '>', 3: '=', 4: '?'}                 # Venus Mars Jupiter Saturn glyphs
PNAME = {1: 'VENUS', 2: 'MARS', 3: 'JUPITER', 4: 'SATURN'}
WARNING = 'DOES NOT REPLACE THE NAUTICAL ALMANAC'


def ip(x):
    return int(x)                                       # C47 IP: truncate toward zero


def chart_x(zn, off, width, x0):
    """IP(((Zn + off) MOD 360) * width / 360 + x0) in 34-digit decimals, like the C47."""
    with _lc() as c:
        c.prec = 34
        v = _D(repr(zn)) + off
        v = v - 360 * (v / 360).__floor__()
        return int(v * width / 360 + x0)


def chart_y(hc, base, sign, scale=200):
    """HALMV: IP(Hc*200/90 + 14); HORZ: IP(225 - Hc*200/90); HALMH: IP(Hc*96/90 + 118),
    in 34-digit decimals."""
    with _lc() as c:
        c.prec = 34
        h = _D(repr(hc)) * scale / 90
        return int(h + base) if sign > 0 else int(base - h)


def chart_ys(sh, base, sign, scale):
    """Sine altitude scale: IP(base + sin(Hc)*scale) (sign > 0) or IP(base - sin(Hc)*scale),
    34-digit decimals like the C47 (sin Hc = "SHC" kept by HCZ / HCZR)."""
    with _lc() as c:
        c.prec = 34
        h = _D(repr(sh)) * scale
        return int(h + base) if sign > 0 else int(base - h)


def sine_ticks(hs):
    """Altitude marks of the sine-scale charts: (deg, pixels above the horizon)."""
    import math
    return [(v, int(hs * math.sin(math.radians(v)))) for v in (10, 20, 30, 45, 60, 90)]


class Screen:
    def __init__(self, font=None):
        self.pix = set()                                 # (x, y), y from the bottom
        self.font = font or BIG                          # font of text() and the number printers

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

    def dot4(self, y, x):
        """Equator dot: 2 x 2 pixels (y, x) to (y + 1, x + 1)."""
        for dy in (0, 1):
            for dx in (0, 1):
                self.pixel(y + dy, x + dx)

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

    def text(self, y, x, s, font=None):                  # PTXB / PTXS / PTXT
        font = font or self.font
        for ch in s:
            x = self.glyph(font, ch, y, x)
        return x

    def small(self, y, x, s):
        return self.text(y, x, s, SMALL)

    # --- number printers (big font)
    def _digits(self, y, x, n, font=None):
        font = font or self.font
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
        x = self.glyph(self.font, '.', y, x)
        return self.glyph(self.font, chr(48 + m % 10), y, x)

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
        w = self.font[48][0]
        if not d > 99:
            x += w
        if not d > 9:
            x += w
        x = self.glyph(self.font, '-' if v < 0 else ' ', y, x)
        x = self._digits(y, x, d)
        x = self.glyph(self.font, ' ', y, x)
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
    """Everything the screens show for one JD and position.
    tables: c47tables.Tables (almanac tables, like TBL + flag 10 on the C47) or None.
    Inside the table period the Sun, Aries, Moon and planets come from the tables
    (SUNA end, SUNG, MOO2, PLN2); stars always from the series. moon_t = flag 11."""

    def __init__(self, j, lat, lon, tables=None):
        self.j, self.lat, self.lon, self.tables = j, lat, lon, tables
        j0 = A.day0(j)
        sung = None
        if tables:
            def sung(jj):                                     # SUNG
                t = tables.get(jj, 0)
                if t:
                    return t
                return A.sun_fast(jj)
        self.times = {k: A.event(j0, lat, lon, k, sung) for k in ('NTWA', 'RISE', 'TRAN', 'SET', 'NTWP')}
        self.sun = s = A.Sun(j)
        self.illum, self.age = A.phase(s)
        if tables:                                            # SUNA, LBL 45
            t = tables.get(j, 0)
            if t:
                s.gha, s.dec = t
                a = tables.get(j, 6)
                if a:
                    s.aries = a[0]
        t = tables.get(j, 5) if tables else None              # MOO2
        self.moon_t = bool(t)
        self.moon = t if t else A.moon(s)
        self.planets = {}
        for p in (1, 2, 3, 4):                                # PLN2
            t = tables.get(j, p) if tables else None
            if t:
                self.planets[p] = (t[0], t[1], (t[0] - s.aries + 360) % 360, 0.0)
            elif tables:                                      # outside the tables: PLN2
                self.planets[p] = A.planet(s, p)
            else:                                             # PLN3
                g, d, dist = A.planet_quick(s, p)
                if A.hcz(lat, lon, d, g)[0] > -1:
                    self.planets[p] = A.planet(s, p, dist * 0.0057755183)
                else:                                         # clearly below the horizon
                    self.planets[p] = (g, d, 0.0, 0.0)
        self._stars = {}

    @property
    def source(self):
        """'T' when the Moon (and so everything but the stars) came from the tables."""
        if A.fast_out(self.j):
            return 'X'                                        # FAST series outside their years
        return 'T' if self.moon_t else 'S'

    def star(self, n):
        if n not in self._stars:
            self._stars[n] = A.star(self.sun, n)
        return self._stars[n]

    def hcz(self, dec, gha):
        return A.hcz(self.lat, self.lon, dec, gha)

    def hczs(self, dec, gha):
        return A.hczs(self.lat, self.lon, dec, gha)

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


    def bodies_short(self):
        """ALMS / HALMH: Sun; Moon if above the horizon; the first planet above the
        horizon in the order Venus, Jupiter, Mars, Saturn; the 3 brightest stars higher
        than 10 deg."""
        s = self.sun
        out = [(0, s.gha, s.dec) + self.hcz(s.dec, s.gha)]
        m = self.moon
        hc, zn = self.hcz(m[1], m[0])
        if hc > 0:
            out.append((-1, m[0], m[1], hc, zn))
        for p in (1, 3, 2, 4):
            g, d = self.planets[p][0], self.planets[p][1]
            hc, zn = self.hcz(d, g)
            if hc > 0:
                out.append((-(p + 1), g, d, hc, zn))
                break
        k = 0
        for n in BRIGHT:
            if k >= 3:
                break
            g, d, _ = self.star(n)
            hc, zn = self.hcz(d, g)
            if hc > 10.0:
                out.append((n, g, d, hc, zn))
                k += 1
        return out


def mark(sc, y, x, ident, font=None):
    """Symbol of a body (PTXB font, or the one given)."""
    ch = '@' if ident == 0 else '(' if ident == -1 else SYM[-ident - 1] if ident < 0 else '*'
    return sc.glyph(font or BIG, ch, y, x)


def moon_word(al):
    """FULL when the Moon shows 100 %, NEW at 0 %, else WAXING / WANING (age 14.765 d)."""
    if 99.5 <= al.illum:
        return 'FULL'
    if 0.5 > al.illum:
        return 'NEW'
    return 'WANING' if 14.765 < al.age else 'WAXING'


def body_name(ident):
    return 'SUN' if ident == 0 else 'MOON' if ident == -1 else PNAME[-ident - 1] if ident < 0 else STAR_NAME[ident]


# ---------------------------------------------------------------- ALMF
def almf(al, short=False):
    """ALMF / ALMS in the status-bar font (PTXS, narrow): ARIES row, then the bodies (9 rows
    ALMF), stars with their number."""
    sc = Screen(STD)
    NX, GX, DX, HX, ZX = 36, 128, 196, 262, 338
    TOP, PITCH = 193, 14
    s, t = al.sun, al.times
    sc.pdat(226, 2, al.j)
    sc.phm(226, 80, ut_hours(al.j)); sc.text(226, 116, 'UT')
    sc.text(226, 150, 'DR')
    sc.text(226, 174, 'S' if al.lat < 0 else 'N'); sc.pdm(226, 176, abs(al.lat))
    sc.text(226, 244, 'W' if al.lon < 0 else 'E'); sc.pdm(226, 246, abs(al.lon))
    sc.text(226, 388, al.source)                             # T tables / S series / X
    sc.pixel(-221, 0)
    sc.text(207, NX, 'BODY'); sc.text(207, GX + 26, 'GHA'); sc.text(207, DX + 28, 'DEC')
    sc.text(207, HX + 30, 'HC'); sc.text(207, ZX + 6, 'ZN')
    sc.text(TOP, NX, 'ARIES'); sc.pdm(TOP, GX, s.aries)
    y = TOP - PITCH
    for ident, g, d, hc, zn in (al.bodies_short() if short else al.bodies(max_rows=9)):
        _row(sc, y, ident, g, d, hc, zn, NX, GX, DX, HX, ZX)
        y -= PITCH
    FY = TOP - PITCH * 10
    sc.pixel(-(FY + 8), 0)
    y1, y2, y3 = FY - 6, FY - 20, FY - 34
    sc.text(y1, 2, 'NAUT TWI'); sc.phm(y1, 80, t['NTWA']); sc.phm(y1, 118, t['NTWP'])
    sc.text(y2, 2, 'RISE/SET'); sc.phm(y2, 80, t['RISE']); sc.phm(y2, 118, t['SET'])
    sc.text(y3, 2, 'MER PASS'); sc.phm(y3, 80, t['TRAN']); x = sc.text(y3, 122, 'SD '); sc.pf1(y3, x, s.sd)
    x = sc.text(y1, 196, 'MOON '); x = sc.pinb(y1, x, al.illum); x = sc.text(y1, x, '% '); sc.text(y1, x, moon_word(al))
    x = sc.text(y2, 196, 'AGE '); x = sc.pf1(y2, x, al.age); sc.text(y2, x, ' DAYS')
    x = sc.text(y3, 196, 'HP '); x = sc.pf1(y3, x, al.moon[2]); x = sc.text(y3, x, ' SD '); sc.pf1(y3, x, al.moon[3])
    sc.small(1, 126, WARNING)
    return [sc.rows()]


def _row(sc, y, ident, g, d, hc, zn, NX, GX, DX, HX, ZX):
    """Table row (ALMF, ALMS, HALMH): symbol, star number, name, GHA, Dec, Hc, Zn."""
    mark(sc, y, 1, ident, STD)
    if ident > 0:
        sc.pinb(y, 17, ident)
    sc.text(y, NX, body_name(ident))
    sc.pdm(y, GX, g)
    sc.text(y, DX, 'S' if d < 0 else 'N'); sc.pdm(y, DX + 2, abs(d))
    sc.pdm(y, HX, hc); sc.pzn(y, ZX, zn)
    if hc < 0:
        sc.hline(y + 5, HX + 7, 56)


# ---------------------------------------------------------------- HALMV
def halmv(al):
    """Chart on the left (sine scale), panel in the status-bar font: symbol, star number,
    name, HC, ZN of 10 bodies."""
    sc = Screen(STD)
    X0, HY, HS, CW = 176, 14, 200, 150
    s = al.sun
    sc.pixel(0, -(X0 - 4))
    sc.hline(HY, 18, CW + 1)
    for y in range(HY, HY + HS + 1):
        sc.pixel(y, 17)
    for v, dy in sine_ticks(HS):
        y = HY + dy
        sc.pixel(y, 15); sc.pixel(y, 16)
        sc.ptns(y - 2, 2, v)
    off = 180 if al.lat < 0 else 0
    for x, l in zip([16 + CW * k // 4 for k in range(5)], 'SWNES' if off else 'NESWN'):
        sc.small(5, x, l)

    def pos(dec, gha):
        hc, zn, sh = al.hczs(dec, gha)
        return hc, zn, chart_x(zn, off, CW, 18), chart_ys(sh, HY, 1, HS)

    for g in range(0, 358, 3):                               # celestial equator
        hc, zn, x, y = pos(0, g)
        if hc > 1e-4:
            sc.dot4(y, x)
    sc.pdat(226, X0, al.j); sc.phm(226, X0 + 78, ut_hours(al.j)); sc.text(226, X0 + 114, 'UT')
    sc.text(226, 388, al.source)
    sc.text(212, X0, 'S' if al.lat < 0 else 'N'); sc.pdm(212, X0 + 2, abs(al.lat))
    sc.text(212, X0 + 70, 'W' if al.lon < 0 else 'E'); sc.pdm(212, X0 + 72, abs(al.lon))
    sc.text(198, X0, 'ARIES'); sc.pdm(198, X0 + 50, s.aries)
    sc.text(184, X0 + 34, 'BODY'); sc.text(184, X0 + 148, 'HC'); sc.text(184, X0 + 194, 'ZN')
    y = 170
    for ident, g, d, hc, zn in al.bodies():
        _, _, cx, cy = pos(d, g)
        if ident == 0:
            if hc > 0:
                sc.glyph(STD, '@', cy - 6, cx - 6)
        elif ident < 0:
            mark(sc, cy - 6, cx - 6, ident, STD)
        else:
            sc.glyph(STD, '*', cy - 6, cx - 6)
            lx = cx + 8
            if lx > 18 + CW - 16:
                lx -= 32
            sc.pinb(cy - 6, lx, ident)
        mark(sc, y, X0, ident, STD)
        if ident > 0:
            sc.pinb(y, X0 + 16, ident)
        sc.text(y, X0 + 34, body_name(ident))
        sc.pdm(y, X0 + 120, hc); sc.pzn(y, X0 + 188, zn)
        if hc < 0:
            sc.hline(y + 5, X0 + 127, 56)
        y -= 14
    x = sc.text(24, X0, 'MOON '); x = sc.pinb(24, x, al.illum); x = sc.text(24, x, '% '); sc.text(24, x, moon_word(al))
    sc.small(8, X0 + 38, WARNING)
    return [sc.rows()]


# ---------------------------------------------------------------- HORZ / HORZS
def horz(al, info=True):
    """Horizon chart, sine altitude scale, bodies in the status-bar font. With info (HORZ)
    returns one frame per object, the top line naming it; without (HORZS) one frame."""
    sc = Screen(STD)
    HS = 196
    sc.hline(16, 20, 376)
    for y in range(18, 213, 3):
        sc.pixel(y, 18)
    for c in (20, 51, 82, 113, 145, 176, 207, 238, 270, 301, 332, 363, 395):
        for y in (15, 14, 13):
            sc.pixel(y, c)
    for v, dy in sine_ticks(HS):
        y = 16 + dy
        for x in (15, 16, 17):
            sc.pixel(y, x)
        sc.ptns(y - 2, 2, v)
    off = 180 if al.lat < 0 else 0
    for x, l in zip((19, 112, 206, 300, 394), 'SWNES' if off else 'NESWN'):
        sc.small(7, x, l)

    def pos(dec, gha):
        hc, zn, sh = al.hczs(dec, gha)
        return hc, zn, chart_x(zn, off, 375, 20), chart_ys(sh, 225, -1, HS)

    for g in range(0, 359, 2):
        hc, zn, x, y = pos(0, g)
        if hc > 1e-4:
            sc.dot4(241 - y, x)
    # same bodies as ALMF / HALMV / ALMT (Sun always, drawn only above the horizon)
    objs = []
    for ident, g, d, hc, zn in al.bodies():
        hc, zn, x, y = pos(d, g)
        yb = 241 - y - 6
        if ident == 0:
            if hc > 0:
                sc.glyph(STD, '@', yb, x - 6)
        elif ident == -1:
            sc.glyph(STD, '(', yb, x - 6)
        elif ident < 0:
            sc.glyph(STD, SYM[-ident - 1], yb, x - 6)
        else:
            sc.glyph(STD, '*', yb, x - 6)
            lx = x + 8
            if lx > 380:
                lx -= 32
            sc.pinb(yb, lx, ident)
        objs.append((ident, zn, hc))
    sc.small(7, 2, al.source)                                # T tables / S series
    if not info or not objs:
        return [sc.rows()]
    frames = []
    for ident, zn, hc in objs:
        sc.pix = {p for p in sc.pix if p[1] < 224}
        if ident > 0:
            x = sc.pinb(227, 2, ident); x = sc.text(227, x, ' '); x = sc.text(227, x, STAR_NAME[ident])
        else:
            x = sc.text(227, 2, body_name(ident))
        x = sc.text(227, x, '  ZN '); x = sc.pf1(227, x, zn); x = sc.text(227, x, '  HC ')
        if hc < 0:
            x = sc.text(227, x, '-')
        sc.pf1(227, x, hc)
        frames.append(sc.rows())
    return frames


class _Quick:
    """Time for the quick formulas (HANIM LBL 71): T (centuries TT), mean GHA Aries."""

    def __init__(self, j):
        d = j - 2451545.0
        self.T = (d + A.DT / 86400.0) / 36525.0
        self.aries = (d * 360.98564736629 + 280.46061837) % 360.0


def _allsky_chart(sc, off, HY=118, HS=100):
    """ALLSKY / HANIM background: horizon across the middle, marks up and down, letters."""
    sc.pixel(-HY, 0)
    for y in range(HY - HS, HY + HS + 1, 3):
        sc.pixel(y, 18)
    for v, dy in sine_ticks(HS):
        for y in (HY + dy, HY - dy):
            sc.pixel(y, 15); sc.pixel(y, 16); sc.pixel(y, 17)
            sc.ptns(y - 2, 2, v)
    for c in (20, 51, 82, 113, 145, 176, 207, 238, 270, 301, 332, 363, 395):
        sc.pixel(HY - 1, c); sc.pixel(HY - 2, c)
    for x, l in zip((19, 112, 206, 300, 394), 'SWNES' if off else 'NESWN'):
        sc.small(HY - 8, x, l)
    sc.small(HY + HS + 1, 150, 'OVER HORIZON'); sc.small(2, 150, 'UNDER HORIZON')


def hanim(j0, lat, lon, frames=24, step=0.5):
    """HANIM: the Sun and the Moon on the ALLSKY chart (over the horizon above, under it
    below) for `frames` times `step` hours apart. The chart is drawn once and every frame
    adds the Sun and the Moon (their paths build up, through setting and rising); only the
    top line is rewritten: date, UT, frame number, DAY / TWILIGHT / NIGHT.
    Sun: SUNF, Moon: MOOQ, for the time of each frame. Returns (list of frames, list of JD)."""
    frames = max(1, int(frames))
    HY, HS = 118, 100
    off = 180 if lat < 0 else 0

    def pos(dec, gha):
        hc, zn, sh = A.hczs(lat, lon, dec, gha)
        return hc, chart_x(zn, off, 375, 20), chart_ys(sh, HY, 1, HS)

    sc = Screen(STD)
    _allsky_chart(sc, off)
    for g in range(0, 359, 2):                               # celestial equator, all of it
        _, x, y = pos(0, g)
        sc.dot4(y, x)
    out, times = [], []
    for k in range(frames):
        with _lc() as ctx:                                   # frame time in 34 digits, as the C47
            ctx.prec = 34
            jdec = _D(repr(j0)) + _D(k) * _D(repr(float(step))) / 24
            jday = int(jdec + _D('0.5')) - 0.5               # for the date
            uth = float((jdec + _D('0.5')) % 1 * 24)         # UT hours
        j = float(jdec)
        g, d = A.sun_fast(j)
        hs, xs, ys = pos(d, g)
        g, d = A.moon_quick(_Quick(j))
        _, xm, ym = pos(d, g)
        sc.pix = {p for p in sc.pix if p[1] < 224}           # clear the top line only
        sc.pdat(227, 2, jday); x = sc.phm(227, 88, uth); sc.text(227, x, ' UT')
        x = sc.pinb(227, 200, k + 1); x = sc.text(227, x, '/'); sc.pinb(227, x, frames)
        sc.text(227, 300, 'DAY' if hs > 0 else 'TWILIGHT' if hs > -12 else 'NIGHT')
        sc.glyph(STD, '@', ys - 6, xs - 6)
        sc.glyph(STD, '(', ym - 6, xm - 6)
        out.append(sc.rows()); times.append(j)
    return out, times


def allsky(al):
    """ALLSKY: the whole sky, horizon across the middle; OVER HORIZON above, UNDER HORIZON
    below (sine scale both ways). Every body: Sun, Moon, planets (big symbols), all 58
    stars (small star and number, catalogue + first-order precession). Top line: date, UT,
    DAY / TWILIGHT / NIGHT from the Sun's altitude."""
    sc = Screen(STD)
    HY, HS = 118, 100
    off = 180 if al.lat < 0 else 0
    _allsky_chart(sc, off)
    s = al.sun
    sc.pdat(227, 2, al.j); x = sc.phm(227, 88, ut_hours(al.j)); sc.text(227, x, ' UT')

    def pos(dec, gha):
        hc, zn, sh = al.hczs(dec, gha)
        return hc, chart_x(zn, off, 375, 20), chart_ys(sh, HY, 1, HS)

    for g in range(0, 358, 3):                               # celestial equator, all of it
        _, x, y = pos(0, g)
        sc.dot4(y, x)
    ty = (al.j - 2451545.0) / 365.25 / 3600.0
    for n in range(1, 59):                                   # every star
        ra, dec = A.ST[n - 1][0], A.ST[n - 1][1]
        dec2 = A.dcos(ra) * 20.0431 * ty + dec
        ra2 = (A.dsin(ra) * A.dtan(dec) * 20.0431 + 46.1244) * ty + ra
        _, x, y = pos(dec2, (s.aries - ra2) % 360.0)
        sc.small(y - 2, x - 2, '*')
        lx = x + 5
        if lx > 388:
            lx -= 17
        sc.ptns(y - 2, lx, n)
    for p in (1, 2, 3, 4):
        g, d = al.planets[p][0], al.planets[p][1]
        _, x, y = pos(d, g)
        sc.glyph(STD, SYM[p], y - 6, x - 6)
    m = al.moon
    _, x, y = pos(m[1], m[0])
    sc.glyph(STD, '(', y - 6, x - 6)
    hs, x, y = pos(s.dec, s.gha)
    sc.glyph(STD, '@', y - 6, x - 6)
    sc.text(227, 300, 'DAY' if hs > 0 else 'TWILIGHT' if hs > -12 else 'NIGHT')
    return [sc.rows()]


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


# Pixel widths of the C47 standard font (PROMPT). The font is proportional and PROMPT
# wraps at a space when the next word does not fit in 400 px.
CHAR_W = {' ': 8, ':': 5, '.': 5, '%': 13, "'": 8, '-': 8, '/': 8, '*': 8, '\u00b0': 8,
          'A': 11, 'I': 6, 'J': 8, 'K': 11, 'L': 9, 'M': 12, 'N': 11, 'Q': 11, 'W': 12}
for _c in '0123456789':
    CHAR_W[_c] = 8
for _c in 'BCDEFGHOPRSTUVXYZ':
    CHAR_W[_c] = 10
PROMPT_W = 400


def text_width(t):
    return sum(CHAR_W[c] for c in t)


class _Line:
    """A PROMPT line built piece by piece, with its width in pixels (R43 on the C47)."""
    def __init__(self):
        self.t, self.w = '', 0

    def add(self, t):
        self.t += t; self.w += text_width(t); return self

    def pad(self, px):
        while self.w + 8 <= px:
            self.add(' ')
        return self


def almt(al):
    """ALMT pages: two lines per R/S. Line 1 is padded with spaces to 400 px so that
    line 2 starts at the left edge; columns are placed by pixels. Same strings as the
    C47 program."""
    s, t = al.sun, al.times
    B = PROMPT_W

    def page(l1, l2):
        return l1.pad(B).t + l2.t

    P = [page(_Line().add(sdat(al.j) + ' ' + shm(ut_hours(al.j)) + ' UT  DR ' + sns(al.lat) + '  ' + sew(al.lon)),
              _Line().add('ARIES ' + sdm(s.aries)).pad(390).add(al.source))]
    for ident, g, d, hc, zn in al.bodies():
        name = sint(ident) + ' ' + STAR_NAME[ident] if ident > 0 else body_name(ident)
        l1 = _Line().add(('* ' if hc < 0 else '') + name).pad(136).add('HC' + sdm(hc).rjust(10) + '  ZN  ' + szn(zn))
        l2 = _Line().pad(125).add('GHA' + sdm(g).rjust(10) + '  DEC ' + ('S' if d < 0 else 'N') + sdm(abs(d)).rjust(9))
        P.append(page(l1, l2))
    P.append(page(_Line().add('NAUT TWI ' + shm(t['NTWA']) + ' ' + shm(t['NTWP'])).pad(180)
                  .add('RISE/SET ' + shm(t['RISE']) + ' ' + shm(t['SET'])),
                  _Line().add('MER PASS ' + shm(t['TRAN'])).pad(180).add('SUN SD ' + sf1(s.sd) + "'")))
    P.append(page(_Line().add('MOON ' + sint(al.illum) + '% ' + moon_word(al)).pad(180)
                  .add('AGE ' + sf1(al.age) + ' DAYS'),
                  _Line().add('MOON HP ' + sf1(al.moon[2]) + "'").pad(180).add('MOON SD ' + sf1(al.moon[3]) + "'")))
    P.append('   ' + WARNING + '    ')                  # 44 characters
    P = Pages(P)
    P.mono = almt_mono(al)
    return P


class Pages(list):
    """ALMT pages (the C47 strings); .mono = the same pages laid out for a monospace
    text file (fixed columns)."""
    mono = None


def almt_mono(al):
    """ALMT pages as [line 1, line 2] for a monospace text file (44 columns)."""
    s, t = al.sun, al.times
    P = [[sdat(al.j) + ' ' + shm(ut_hours(al.j)) + ' UT  DR ' + sns(al.lat) + '  ' + sew(al.lon),
          ('ARIES ' + sdm(s.aries)).ljust(43) + al.source]]
    for ident, g, d, hc, zn in al.bodies():
        name = sint(ident) + ' ' + STAR_NAME[ident] if ident > 0 else body_name(ident)
        P.append([(('* ' if hc < 0 else '') + name).ljust(13) + '  HC' + sdm(hc).rjust(10) + '  ZN  ' + szn(zn),
                  ' ' * 14 + 'GHA' + sdm(g).rjust(10) + '  DEC ' + ('S' if d < 0 else 'N') + sdm(abs(d)).rjust(9)])
    P.append([('NAUT TWI ' + shm(t['NTWA']) + ' ' + shm(t['NTWP'])).ljust(22) + 'RISE/SET ' + shm(t['RISE']) + ' ' + shm(t['SET']),
              ('MER PASS ' + shm(t['TRAN'])).ljust(22) + 'SUN SD ' + sf1(s.sd) + "'"])
    P.append([('MOON ' + sint(al.illum) + '% ' + moon_word(al)).ljust(22) + 'AGE ' + sf1(al.age) + ' DAYS',
              ('MOON HP ' + sf1(al.moon[2]) + "'").ljust(22) + 'MOON SD ' + sf1(al.moon[3]) + "'"])
    P.append(['   ' + WARNING])
    return P


def prompt_lines(text, width=PROMPT_W):
    """How the C47 PROMPT splits text into lines: a word that does not fit starts a new
    line; spaces that do not fit are carried to the new line."""
    lines, cur, w = [], '', 0
    for tok in re.findall(r' +|[^ ]+', text):
        tw = text_width(tok)
        if tok[0] == ' ':
            fit = 0
            while fit < len(tok) and w + 8 * (fit + 1) <= width:
                fit += 1
            cur += tok[:fit]; w += 8 * fit
            if fit < len(tok):
                lines.append(cur); cur, w = tok[fit:], 8 * (len(tok) - fit)
        elif w + tw > width and cur.strip():
            lines.append(cur); cur, w = tok, tw
        else:
            cur += tok; w += tw
    return lines + [cur]


# ---------------------------------------------------------------- HALMH
def halmh(al):
    """Horizon chart on top (full width, sine scale), short almanac table below (PTXS)."""
    sc = Screen(STD)
    NX, GX, DX, HX, ZX = 36, 128, 196, 262, 338
    HY, HS, TOP = 129, 89, 107
    s, t = al.sun, al.times
    sc.pdat(226, 2, al.j)
    sc.phm(226, 80, ut_hours(al.j)); sc.text(226, 116, 'UT')
    sc.text(226, 150, 'S' if al.lat < 0 else 'N'); sc.pdm(226, 152, abs(al.lat))
    sc.text(226, 222, 'W' if al.lon < 0 else 'E'); sc.pdm(226, 224, abs(al.lon))
    sc.text(226, 388, al.source)
    sc.hline(HY, 20, 376)
    for y in range(HY, HY + HS + 1, 3):
        sc.pixel(y, 18)
    for v, dy in sine_ticks(HS):
        y = HY + dy
        sc.pixel(y, 15); sc.pixel(y, 16); sc.pixel(y, 17)
        sc.ptns(y - 2, 2, v)
    for c in (20, 51, 82, 113, 145, 176, 207, 238, 270, 301, 332, 363, 395):
        sc.pixel(HY - 1, c); sc.pixel(HY - 2, c)
    off = 180 if al.lat < 0 else 0
    for x, l in zip((19, 112, 206, 300, 394), 'SWNES' if off else 'NESWN'):
        sc.small(HY - 8, x, l)

    def pos(dec, gha):
        hc, zn, sh = al.hczs(dec, gha)
        return hc, zn, chart_x(zn, off, 375, 20), chart_ys(sh, HY, 1, HS)

    for g in range(0, 358, 3):
        hc, zn, x, y = pos(0, g)
        if hc > 1e-4:
            sc.dot4(y, x)
    y = TOP
    for ident, g, d, hc, zn in al.bodies_short():
        _, _, cx, cy = pos(d, g)
        if ident == 0:
            if hc > 0:
                sc.glyph(STD, '@', cy - 6, cx - 6)
        elif ident < 0:
            mark(sc, cy - 6, cx - 6, ident, STD)
        else:
            sc.glyph(STD, '*', cy - 6, cx - 6)
            lx = cx + 8
            if lx > 380:
                lx -= 32
            sc.pinb(cy - 6, lx, ident)
        _row(sc, y, ident, g, d, hc, zn, NX, GX, DX, HX, ZX)
        y -= 14
    sc.text(23, 2, 'RISE'); sc.phm(23, 44, t['RISE']); sc.text(23, 92, 'SET'); sc.phm(23, 128, t['SET'])
    sc.text(23, 176, 'MER'); sc.phm(23, 214, t['TRAN']); sc.text(23, 262, 'ARIES'); sc.pdm(23, 312, s.aries)
    sc.text(9, 2, 'TWI'); sc.phm(9, 36, t['NTWA']); sc.phm(9, 78, t['NTWP'])
    x = sc.text(9, 176, 'MOON '); x = sc.pinb(9, x, al.illum); x = sc.text(9, x, '% '); sc.text(9, x, moon_word(al))
    sc.small(1, 126, WARNING)
    return [sc.rows()]


# ---------------------------------------------------------------- BODY (one body)
BODY_NAMES = {60: 'SUN', 61: 'MOON', 62: 'VENUS', 63: 'MARS', 64: 'JUPITER', 65: 'SATURN'}
BODY_LEGEND = ('BODY NO.  STARS 1-58  SUN 60  MOON 61', 'VENUS 62  MARS 63  JUPITER 64  SATURN 65')


def _pad(t, w, target=PROMPT_W):
    while w + 8 <= target:
        t += ' '; w += 8
    return t


def body_entry(code):
    return '%d %s' % (code, STAR_NAME[code] if code < 60 else BODY_NAMES[code])


def body_list(al):
    """BODY step 1: codes above the horizon (quick positions) and the PROMPT pages."""
    s = al.sun
    codes = []
    if al.hcz(s.dec, s.gha)[0] > 0:
        codes.append(60)
    g, d = A.moon_quick(s)
    if al.hcz(d, g)[0] > -1:
        codes.append(61)
    for p in (1, 2, 3, 4):
        g, d, _ = A.planet_quick(s, p)
        if al.hcz(d, g)[0] > -1:
            codes.append(61 + p)
    for n in BRIGHT:
        a0, d0 = A.ST[n - 1][0], A.ST[n - 1][1]
        if al.hcz(d0, s.aries - a0)[0] > 9:
            codes.append(n)
    pages, page, w, line = [], '', 0, 1
    for c in codes:
        e = body_entry(c); ew = text_width(e)
        if w == 0:
            page, w, line = e, ew, 1
        elif w + 16 + ew <= PROMPT_W:
            page += '  ' + e; w += 16 + ew
        elif line == 1:
            page = _pad(page, w) + e; w, line = ew, 2
        else:
            pages.append(page); page, w, line = e, ew, 1
    if w:
        pages.append(page)
    return codes, pages


def body_legend():
    l1 = BODY_LEGEND[0]
    return _pad(l1, text_width(l1)) + BODY_LEGEND[1]


def body_values(al, code):
    """GHA, Dec, SHA or HP, SD of the chosen body in full precision (as BODY)."""
    s, tb, j = al.sun, al.tables, al.j
    extra = (0.0, 0.0)
    if code == 60:
        g, d = s.gha, s.dec; extra = (0.0, s.sd)
    elif code == 61:
        g, d, hp, sd = al.moon; extra = (hp, sd)
    elif code > 61:
        p = code - 61
        t = tb.get(j, p) if tb else None
        if t:
            g, d = t[0], t[1]; extra = ((t[0] - s.aries + 360) % 360, 0.0)
        else:
            g, d, sha, _ = A.planet(s, p); extra = (sha, 0.0)
    else:
        g, d, sha = al.star(code); extra = (sha, 0.0)
    hc, zn = al.hcz(d, g)
    letter = 'X' if A.fast_out(j) else 'T' if tb and tb.get(j, 6) else 'S'
    return g, d, extra, hc, zn, letter


def body_pages(al, code):
    g, d, extra, hc, zn, letter = body_values(al, code)
    name = body_entry(code) if code < 60 else BODY_NAMES[code]
    l1 = name + '  ' + sdat(al.j) + ' ' + shm(ut_hours(al.j)) + ' UT'
    p1 = _pad(l1, text_width(l1)) + 'GHA ' + sdm(g) + '  DEC ' + ('S' if d < 0 else 'N') + ' ' + sdm(abs(d))
    l1 = 'HC ' + sdm(hc) + '  ZN ' + szn(zn)
    if code == 60:
        l2 = 'SUN SD ' + sf1(extra[1]) + "'"
    elif code == 61:
        l2 = 'HP ' + sf1(extra[0]) + "'  SD " + sf1(extra[1]) + "'"
    else:
        l2 = 'SHA ' + sdm(extra[0])
    p2 = _pad(l1, text_width(l1)) + l2 + '  ' + letter
    return [p1, p2]


def body_chart(al, code):
    """BODY chart: sine altitude scale, the body and its data in the status-bar font."""
    g, d, extra, hc, zn, letter = body_values(al, code)
    sc = Screen(STD)
    HY, HS = 86, 132
    s = al.sun
    sc.pdat(226, 2, al.j)
    sc.phm(226, 88, ut_hours(al.j)); sc.text(226, 129, 'UT')
    sc.text(226, 162, 'S' if al.lat < 0 else 'N'); sc.pdm(226, 164, abs(al.lat))
    sc.text(226, 244, 'W' if al.lon < 0 else 'E'); sc.pdm(226, 246, abs(al.lon))
    sc.text(226, 388, letter)
    sc.hline(HY, 20, 376)
    for y in range(HY, HY + HS + 1, 3):
        sc.pixel(y, 18)
    for v, dy in sine_ticks(HS):
        y = HY + dy
        sc.pixel(y, 15); sc.pixel(y, 16); sc.pixel(y, 17)
        sc.ptns(y - 2, 2, v)
    for c in (20, 51, 82, 113, 145, 176, 207, 238, 270, 301, 332, 363, 395):
        sc.pixel(HY - 1, c); sc.pixel(HY - 2, c)
    off = 180 if al.lat < 0 else 0
    for x, l in zip((19, 112, 206, 300, 394), 'SWNES' if off else 'NESWN'):
        sc.small(HY - 8, x, l)

    def pos(dec, gha):
        h, z, sh = al.hczs(dec, gha)
        return h, chart_x(z, off, 375, 20), chart_ys(sh, HY, 1, HS)

    for gg in range(0, 355, 6):
        h, x, y = pos(0, gg)
        if h > 1e-4:
            sc.dot4(y, x)
    sym = '*' if code < 60 else '@(<>=?'[code - 60]
    h, cx, cy = pos(d, g)
    if h > 0:
        sc.glyph(STD, sym, cy - 6, cx - 6)
        if code < 60:
            lx = cx + 8
            if lx > 380:
                lx -= 32
            sc.pinb(cy - 6, lx, code)
    sc.text(62, 2, sym)
    sc.text(62, 20, body_entry(code) if code < 60 else BODY_NAMES[code])
    sc.text(47, 2, 'GHA'); sc.pdm(47, 40, g)
    sc.text(47, 184, 'DEC'); sc.text(47, 220, 'S' if d < 0 else 'N'); sc.pdm(47, 222, abs(d))
    sc.text(33, 2, 'HC'); sc.pdm(33, 40, hc)
    sc.text(33, 184, 'ZN'); sc.pzn(33, 230, zn)
    if code == 60:
        sc.text(19, 2, 'SD'); sc.pf1(19, 40, extra[1])
        sc.text(19, 184, 'ARIES'); sc.pdm(19, 232, s.aries)
    elif code == 61:
        sc.text(19, 2, 'HP'); sc.pf1(19, 40, extra[0]); sc.text(19, 184, 'SD'); sc.pf1(19, 230, extra[1])
    else:
        sc.text(19, 2, 'SHA'); sc.pdm(19, 40, extra[0])
        sc.text(19, 184, 'ARIES'); sc.pdm(19, 232, s.aries)
    sc.small(2, 126, WARNING)
    return [sc.rows()]


VIEWS = {'ALLSKY': allsky, 'ALMS': lambda al: almf(al, True), 'HALMH': halmh, 'ALMF': almf, 'HALMV': halmv, 'HORZ': lambda al: horz(al, True), 'HORZS': lambda al: horz(al, False)}
