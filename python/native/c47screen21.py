"""c47screen21.py - the new C47 screens (NAVFULL, Oct 2026) rebuilt in plain Python for the
native PC version: the header line (date, UT, DR, T / S) with a line under it on every view,
the text in the C47 standard font as GRFNT 21 draws it, the chart labels in the tinyFont, the
body symbols of glyphs47 (12 rows in the tables, 7 on the charts), the same 8 bodies on
ALMANAC, CHART, SKY and SPLIT (Sun; Moon above the horizon; the first planet above it, Venus
Jupiter Mars Saturn; the brightest stars higher than 10 deg), DAY / TWILIGHT / NIGHT under the
charts, the Moon phase glyph, and a MOON view (native only). Checked pixel for pixel against the
calculator programs (tests/test_parity21.py)."""
import math
import c47astro as A
from c47screen import (Screen, Almanac, chart_x, chart_ys, ut_hours, jd_to_date, moon_word,
                       body_name, ip, STAR_NAME, BRIGHT)
from c47fonts21 import F21, TINY, SYMB, SYMS

NBODY = 8
LUN = 29.530589
PHASE_NAMES = ('NEW MOON', 'WAXING CRESCENT', 'FIRST QUARTER', 'WAXING GIBBOUS', 'FULL MOON',
               'WANING GIBBOUS', 'LAST QUARTER', 'WANING CRESCENT')


def width(t, font=F21):
    return sum(font[ord(c)][0] for c in t)


# the columns of genviews_atx.py in mode 't21' (font 21)
DIG = width('0')
PDM = 4 * DIG + DIG + 2 * DIG + width('.') + DIG
ZNW, HMW, DTW = width('000.0'), width('00:00'), width('00-00-0000')
NAMEW = max(width(n) for n in STAR_NAME.values() if n)


def top_x():
    X = {'date': 2}
    X['time'] = 2 + DTW + DIG
    X['UT'] = X['time'] + HMW + DIG
    X['DR'] = X['UT'] + width('UT') + DIG
    X['N'] = X['DR'] + width('DR') + DIG
    X['lat'] = X['N'] + width('N') + DIG - 2 * DIG
    X['E'] = X['lat'] + PDM + DIG
    X['lon'] = X['E'] + width('W') + DIG - DIG
    return X


def table_x():
    X = {'num': 14, 'name': 34}
    X['gha'] = X['name'] + NAMEW
    X['ns'] = X['gha'] + PDM + 4
    X['dec'] = X['ns'] + width('N') + 6 - 2 * DIG
    X['hc'] = X['dec'] + PDM + 6 - DIG
    X['zn'] = X['hc'] + PDM + 6
    e = (398 - X['zn'] - ZNW) // 4
    for k, n in (('gha', 1), ('ns', 2), ('dec', 2), ('hc', 3), ('zn', 4)):
        X[k] += n * e
    c = lambda a, b, t: round((a + b - width(t)) / 2)
    X['hGHA'] = c(X['gha'] + DIG, X['gha'] + PDM, 'GHA')
    X['hDEC'] = c(X['ns'], X['dec'] + PDM, 'DEC')
    X['hHC'] = c(X['hc'] + DIG, X['hc'] + PDM, 'HC')
    X['hZN'] = c(X['zn'], X['zn'] + ZNW, 'ZN')
    return X


def state_x(w):
    return 200 - width(w) // 2


def bodies(al):
    """The 8 bodies of every view: (id, gha, dec, hc, zn); id 0 Sun, -1 Moon, -2..-5 planets, n star."""
    s = al.sun
    out = [(0, s.gha, s.dec) + al.hcz(s.dec, s.gha)]
    m = al.moon
    hc, zn = al.hcz(m[1], m[0])
    if hc > 0:
        out.append((-1, m[0], m[1], hc, zn))
    for p in (1, 3, 2, 4):
        g, d = al.planets[p][0], al.planets[p][1]
        hc, zn = al.hcz(d, g)
        if hc > 0:
            out.append((-(p + 1), g, d, hc, zn))
            break
    for n in BRIGHT:
        if len(out) >= NBODY:
            break
        g, d, _ = al.star(n)
        hc, zn = al.hcz(d, g)
        if hc > 10.0:
            out.append((n, g, d, hc, zn))
    return out


def symbol(ident):
    return '@' if ident == 0 else '(' if ident == -1 else '<>=?'[-ident - 2] if ident < 0 else '*'


def phase_index(age):
    return ip(age / LUN * 8 + 0.5) % 8


def daylight(sun_hc):
    return 'DAY' if sun_hc > 0 else 'TWILIGHT' if sun_hc > -12 else 'NIGHT'


def header(sc, al, j=None, lat=None, lon=None, source=None, uth=None):
    """date, time UT, DR, N lat, E lon at row 226, T / S at 388, the line under (221)."""
    T = top_x()
    j = al.j if j is None else j
    lat = al.lat if lat is None else lat
    lon = al.lon if lon is None else lon
    sc.pdat(226, T['date'], j)
    sc.phm(226, T['time'], ut_hours(j) if uth is None else uth); sc.text(226, T['UT'], 'UT')
    sc.text(226, T['DR'], 'DR')
    sc.text(226, T['N'], 'S' if lat < 0 else 'N'); sc.pdm(226, T['lat'], abs(lat))
    sc.text(226, T['E'], 'W' if lon < 0 else 'E'); sc.pdm(226, T['lon'], abs(lon))
    sc.text(226, 388, al.source if source is None else source)
    sc.pixel(-221, 0)


def tiny(sc, y, x, s):
    return sc.text(y, x, s, TINY)


def tiny_num(sc, y, x, v):
    return sc._digits(y, x, ip(abs(v) + 0.5), TINY)


# ---------------------------------------------------------------- 1 ALMANAC
def almanac(al):
    sc = Screen(F21)
    X = table_x()
    NX, GX, NSX, DX, HX, ZX = X['name'], X['gha'], X['ns'], X['dec'], X['hc'], X['zn']
    TOP, PITCH, ROWS = 193, 16, NBODY + 1
    s, t = al.sun, al.times
    header(sc, al)
    for k, w in (('name', 'BODY'), ('hGHA', 'GHA'), ('hDEC', 'DEC'), ('hHC', 'HC'), ('hZN', 'ZN')):
        sc.text(207, X[k], w)
    sc.text(TOP, NX, 'ARIES'); sc.pdm(TOP, GX, s.aries)
    y = TOP - PITCH
    for ident, g, d, hc, zn in bodies(al):
        sc.glyph(SYMB, symbol(ident), y, 0)
        if ident > 0:
            sc.pinb(y, X['num'], ident)
        sc.text(y, NX, body_name(ident))
        sc.pdm(y, GX, g)
        sc.text(y, NSX, 'S' if d < 0 else 'N'); sc.pdm(y, DX, abs(d))
        sc.pdm(y, HX, hc); sc.pzn(y, ZX, zn)
        if hc < 0:
            sc.xor_box(y - 1, HX + 7, PDM - 6, 14)
        y -= PITCH
    FY = TOP - PITCH * ROWS
    sc.pixel(-(FY + 8), 0)
    y1, y2, y3 = FY - 6, FY - 20, FY - 34
    t1 = 2 + max(width(w) for w in ('NAUT TWI', 'RISE/SET', 'MER PASS')) + 8
    t2 = t1 + HMW + 8
    sc.text(y1, 2, 'NAUT TWI'); sc.phm(y1, t1, t['NTWA']); sc.phm(y1, t2, t['NTWP'])
    sc.text(y2, 2, 'RISE/SET'); sc.phm(y2, t1, t['RISE']); sc.phm(y2, t2, t['SET'])
    sc.text(y3, 2, 'MER PASS'); sc.phm(y3, t1, t['TRAN']); x = sc.text(y3, t2, 'SD '); sc.pf1(y3, x, s.sd)
    MX = 212
    x = sc.text(y1, MX, 'MOON '); x = sc.pinb(y1, x, al.illum); x = sc.text(y1, x, '% ')
    x = sc.glyph(SYMB, str(phase_index(al.age)), y1, x); x = sc.text(y1, x, ' '); sc.text(y1, x, moon_word(al))
    x = sc.text(y2, MX, 'AGE '); x = sc.pf1(y2, x, al.age); sc.text(y2, x, ' DAYS')
    x = sc.text(y3, MX, 'HP '); x = sc.pf1(y3, x, al.moon[2]); x = sc.text(y3, x, ' SD '); sc.pf1(y3, x, al.moon[3])
    return [sc.rows()]


def hc_box(sc, y, x):
    """A negative Hc white on black: XOR box over the Hc field."""
    sc.xor_box(y - 1, x + 7, PDM - 6, 14)


def alt_axis(sc, HY, HS, x_tick=(15, 16), label=True):
    for v in (10, 20, 30, 45, 60, 90):
        y = HY + int(HS * math.sin(math.radians(v)))
        for x in x_tick:
            sc.pixel(y, x)
        if label:
            tiny_num(sc, y - 2, 2, v)


# ---------------------------------------------------------------- 2 CHART
def chart(al):
    sc = Screen(F21)
    X0, CW, HY, HS = 176, 150, 14, 200
    for y in range(0, 221):
        sc.pixel(y, X0 - 4)
    sc.pixel(-221, 0)
    sc.hline(HY, 18, CW + 1)
    for y in range(HY, HY + HS + 1):
        sc.pixel(y, 17)
    alt_axis(sc, HY, HS)
    off = 180 if al.lat < 0 else 0
    for x, l in zip([16 + CW * k // 4 for k in range(5)], 'SWNES' if off else 'NESWN'):
        tiny(sc, 5, x, l)

    def pos(dec, gha):
        hc, zn, sh = al.hczs(dec, gha)
        return hc, chart_x(zn, off, CW, 18), chart_ys(sh, HY, 1, HS)

    for g in range(0, 358, 3):
        hc, x, y = pos(0, g)
        if hc > 1e-4:
            sc.dot4(y, x)
    header(sc, al)
    ZX = 398 - ZNW
    HX = ZX - 6 - PDM
    NM = X0 + 14
    sc.text(207, NM, 'BODY'); sc.text(207, round(HX + 8 + (PDM - 8 - width('HC')) / 2), 'HC')
    sc.text(207, round(ZX + (ZNW - width('ZN')) / 2), 'ZN')
    y = 193
    for ident, g, d, hc, zn in bodies(al):
        h, cx, cy = pos(d, g)
        if hc > 0:
            sc.glyph(SYMS, symbol(ident), cy - 3, cx - 3)
            if ident > 0:
                lx = cx + 5
                if lx > 18 + CW - 20:
                    lx -= 22
                tiny_num(sc, cy - 3, lx, ident)
        sc.glyph(SYMB, symbol(ident), y, X0)
        if ident > 0:
            sc.pinb(y, NM, ident)
            sc.text(y, NM + width('00 '), body_name(ident))
        else:
            sc.text(y, NM, body_name(ident))
        sc.pdm(y, HX, hc); sc.pzn(y, ZX, zn)
        if hc < 0:
            hc_box(sc, y, HX)
        y -= 16
    return [sc.rows()]


# ---------------------------------------------------------------- 4 SKY
def sky_frames(al):
    """The SKY chart, and the frames of its name loop: one per body, the name of each body
    above the horizon next to it (XOR), every second on the calculator."""
    sc = Screen(F21)
    HB, HS = 28, 184
    sc.hline(HB, 20, 376)
    for y in range(HB + 2, 213, 3):
        sc.pixel(y, 18)
    for c in (20, 51, 82, 113, 145, 176, 207, 238, 270, 301, 332, 363, 395):
        for y in (HB - 1, HB - 2, HB - 3):
            sc.pixel(y, c)
    alt_axis(sc, HB, HS, (15, 16, 17))
    off = 180 if al.lat < 0 else 0
    for x, l in zip((19, 112, 206, 300, 394), 'SWNES' if off else 'NESWN'):
        tiny(sc, HB - 9, x, l)

    def pos(sh, zn):
        x = chart_x(zn, off, 375, 20)
        return 241 - chart_ys(sh, 241 - HB, -1, HS), x

    for g in range(0, 359, 2):
        hc, zn, sh = al.hczs(0, g)
        if hc > 1e-4:
            r, x = pos(sh, zn)
            sc.dot4(r, x)
    rows = bodies(al)
    for ident, g, d, hc, zn in rows:
        if ident == 0 or hc > 0:
            _, _, sh = al.hczs(d, g)
            r, x = pos(sh, zn)
            if hc > 0:
                sc.glyph(SYMS, symbol(ident), r - 3, x - 3)
            if ident > 0:
                lx = x + 5
                if lx > 380:
                    lx -= 22
                tiny_num(sc, r - 3, lx, ident)
            if ident == 0:
                w = daylight(hc)
                sc.text(4, state_x(w), w)
    header(sc, al, al.j)
    names = []
    for ident, g, d, hc, zn in rows:
        if hc <= 0:
            names.append(None)
            continue
        r, x = pos(math.sin(math.radians(hc)), zn)
        nx = x + 8 + (14 if ident > 0 else 0)
        t = body_name(ident)
        if nx + 8 * len(t) > 380:
            nx = x - 28 - 8 * len(t)
        n = Screen(F21)
        n.text(r - 3, nx, t)
        names.append(n.pix)
    base = sc.rows()
    out = []
    for p in names:
        f = base if p is None else base ^ {(x, 239 - y) for x, y in p if 0 <= x < 400 and 0 <= y < 240}
        if not out or out[-1] != f:
            out.append(f)
    return out


# ---------------------------------------------------------------- 5 SPLIT
def split(al):
    sc = Screen(F21)
    X = table_x()
    NX, GX, NSX, DX, HX, ZX = X['name'], X['gha'], X['ns'], X['dec'], X['hc'], X['zn']
    HY, HS, TOP = 144, 68, 107
    header(sc, al)
    sc.hline(HY, 20, 376)
    for y in range(HY, HY + HS + 1, 3):
        sc.pixel(y, 18)
    alt_axis(sc, HY, HS, (15, 16, 17))
    for c in (20, 51, 82, 113, 145, 176, 207, 238, 270, 301, 332, 363, 395):
        sc.pixel(HY - 1, c); sc.pixel(HY - 2, c)
    off = 180 if al.lat < 0 else 0
    for x, l in zip((19, 112, 206, 300, 394), 'SWNES' if off else 'NESWN'):
        tiny(sc, HY - 9, x, l)

    def pos(dec, gha):
        hc, zn, sh = al.hczs(dec, gha)
        return hc, chart_x(zn, off, 375, 20), chart_ys(sh, HY, 1, HS)

    for g in range(0, 358, 3):
        hc, x, y = pos(0, g)
        if hc > 1e-4:
            sc.dot4(y, x)
    for t, k in (('BODY', 'name'), ('GHA', 'hGHA'), ('DEC', 'hDEC'), ('HC', 'hHC'), ('ZN', 'hZN')):
        sc.text(TOP + 14, X[k], t)
    y = TOP
    for ident, g, d, hc, zn in bodies(al):
        if y < 9:
            break
        h, cx, cy = pos(d, g)
        if hc > 0:
            sc.glyph(SYMS, symbol(ident), cy - 3, cx - 3)
            if ident > 0:
                lx = cx + 5
                if lx > 380:
                    lx -= 22
                tiny_num(sc, cy - 3, lx, ident)
        sc.glyph(SYMB, symbol(ident), y, 0)
        if ident > 0:
            sc.pinb(y, X['num'], ident)
        sc.text(y, NX, body_name(ident))
        sc.pdm(y, GX, g)
        sc.text(y, NSX, 'S' if d < 0 else 'N'); sc.pdm(y, DX, abs(d))
        sc.pdm(y, HX, hc); sc.pzn(y, ZX, zn)
        if hc < 0:
            hc_box(sc, y, HX)
        y -= 14
    return [sc.rows()]


# ---------------------------------------------------------------- 6 ANIM and 7 ALLSKY
HYA, HSA = 118, 94


def sky_chart(sc, off, HY=HYA, HS=HSA):
    """The whole-sky chart: horizon across the middle, marks up and down (tinyFont), N E S W."""
    sc.pixel(-HY, 0)
    for y in range(HY - HS, HY + HS + 1, 3):
        sc.pixel(y, 18)
    for v in (10, 20, 30, 45, 60, 90):
        dy = int(HS * math.sin(math.radians(v)))
        for y in (HY + dy, HY - dy):
            sc.pixel(y, 15); sc.pixel(y, 16); sc.pixel(y, 17)
            tiny_num(sc, y - 2, 2, v)
    for c in (20, 51, 82, 113, 145, 176, 207, 238, 270, 301, 332, 363, 395):
        sc.pixel(HY - 1, c); sc.pixel(HY - 2, c)
    for x, l in zip((19, 112, 206, 300, 394), 'SWNES' if off else 'NESWN'):
        tiny(sc, HY - 10, x, l)


def anim(al, frames=24, step=0.5):
    """ANIM: the Sun and the Moon (SUNF, MOOQ) every `step` hours on the whole-sky chart;
    the header shows the time of the frame, DAY / TWILIGHT / NIGHT at the bottom."""
    from c47screen import _Quick, _D, _lc
    lat, lon = al.lat, al.lon
    off = 180 if lat < 0 else 0

    def pos(dec, gha):
        hc, zn, sh = A.hczs(lat, lon, dec, gha)
        return hc, chart_x(zn, off, 375, 20), chart_ys(sh, HYA, 1, HSA)

    sc = Screen(F21)
    sky_chart(sc, off)
    sc.pixel(-221, 0)
    for g in range(0, 359, 2):
        _, x, y = pos(0, g)
        sc.dot4(y, x)
    out = []
    for k in range(max(1, int(frames))):
        with _lc() as ctx:
            ctx.prec = 34
            jdec = _D(repr(al.j)) + _D(k) * _D(repr(float(step))) / 24
            uth = float((jdec + _D('0.5')) % 1 * 24)
        j = float(jdec)
        g, d = A.sun_fast(j)
        hs, xs, ys = pos(d, g)
        g, d = A.moon_quick(_Quick(j))
        _, xm, ym = pos(d, g)
        sc.pix = {p for p in sc.pix if p[1] < 224 and p[1] > 15}
        header(sc, al, j, uth=uth)
        w = daylight(hs)
        sc.text(4, state_x(w), w)
        sc.glyph(SYMS, '@', ys - 3, xs - 3)
        sc.glyph(SYMS, '(', ym - 3, xm - 3)
        out.append(sc.rows())
    return out


def allsky(al):
    """ALLSKY: the whole sky; every star (small star, number), the planets, the Moon, the Sun;
    DAY / TWILIGHT / NIGHT at the bottom."""
    sc = Screen(F21)
    off = 180 if al.lat < 0 else 0
    sky_chart(sc, off)
    s = al.sun
    header(sc, al)

    def pos(dec, gha):
        hc, zn, sh = al.hczs(dec, gha)
        return hc, chart_x(zn, off, 375, 20), chart_ys(sh, HYA, 1, HSA)

    for g in range(0, 358, 3):
        _, x, y = pos(0, g)
        sc.dot4(y, x)
    ty = (al.j - 2451545.0) / 365.25 / 3600.0
    for n in range(1, 59):
        ra, dec = A.ST[n - 1][0], A.ST[n - 1][1]
        dec2 = A.dcos(ra) * 20.0431 * ty + dec
        ra2 = (A.dsin(ra) * A.dtan(dec) * 20.0431 + 46.1244) * ty + ra
        _, x, y = pos(dec2, (s.aries - ra2) % 360.0)
        sc.glyph(SYMS, '*', y - 3, x - 3)
        lx = x + 5
        if lx > 388:
            lx -= 17
        tiny_num(sc, y - 3, lx, n)
    for p in (1, 2, 3, 4):
        g, d = al.planets[p][0], al.planets[p][1]
        _, x, y = pos(d, g)
        sc.glyph(SYMS, '<>=?'[p - 1], y - 3, x - 3)
    m = al.moon
    _, x, y = pos(m[1], m[0])
    sc.glyph(SYMS, '(', y - 3, x - 3)
    hs, x, y = pos(s.dec, s.gha)
    sc.glyph(SYMS, '@', y - 3, x - 3)
    w = daylight(hs)
    sc.text(4, state_x(w), w)
    return [sc.rows()]


# ---------------------------------------------------------------- MOON (native only)
QUARTERS = ((0.0, 'NEW MOON'), (90.0, 'FIRST QUARTER'), (180.0, 'FULL MOON'), (270.0, 'LAST QUARTER'))


def elongation(j):
    """The Moon's phase angle 0 - 360 (0 new, 90 first quarter, 180 full, 270 last quarter):
    180 - i, i the phase angle of PHAS (c47astro.phase: D, M, M' with the main terms)."""
    D, M, Mp = A.Sun(j).args[:3]
    i = (180 - D - 6.289 * A.dsin(Mp) + 2.1 * A.dsin(M) - 1.274 * A.dsin(2 * D - Mp)
         - 0.658 * A.dsin(2 * D) - 0.214 * A.dsin(2 * Mp) - 0.11 * A.dsin(D))
    return (180.0 - i) % 360.0


def next_phases(j):
    """The next new Moon, first quarter, full Moon and last quarter after JD j: (JD, name),
    in time order (Newton steps on the phase angle, 12.19 deg a day)."""
    out = []
    e0 = elongation(j)
    for target, name in QUARTERS:
        t = j + ((target - e0) % 360.0) / 12.190749
        for _ in range(6):
            d = (target - elongation(t) + 180.0) % 360.0 - 180.0
            t += d / 12.190749
        if t < j:
            t += LUN
        out.append((t, name))
    return sorted(out)


def moon_disc(sc, cx, cy, r, age, south=False):
    """The Moon as a disc of radius r: the lit part filled, the dark part as its outline;
    waxing lit on the right (northern view), mirrored for the south."""
    th = math.radians(age / LUN * 360.0)
    ct = math.cos(th)
    for y in range(-r, r + 1):
        w = math.sqrt(max(r * r - y * y, 0))
        for x in range(-r, r + 1):
            d = math.hypot(x, y)
            if d > r + 0.3:
                continue
            xx = -x if south else x
            lit = xx > w * ct if age <= LUN / 2 else xx < -w * ct
            if lit or d > r - 1.2:
                sc.pixel(cy + y, cx + x)


def moon_view(al):
    """MOON: the phase as a disc, its name, % lit, age, Moon HP and SD, the next four phases
    and the eight phase glyphs with today's one inverted."""
    sc = Screen(F21)
    header(sc, al)
    south = al.lat < 0
    moon_disc(sc, 80, 120, 62, al.age, south)
    p = phase_index(al.age)
    sc.text(200, 168, PHASE_NAMES[p])
    x = sc.text(183, 168, 'LIT '); x = sc.pinb(183, x, al.illum); x = sc.text(183, x, '%   AGE ')
    x = sc.pf1(183, x, al.age); sc.text(183, x, ' DAYS')
    x = sc.text(166, 168, 'HP '); x = sc.pf1(166, x, al.moon[2]); x = sc.text(166, x, "'  SD ")
    x = sc.pf1(166, x, al.moon[3]); sc.text(166, x, "'")
    sc.hline(156, 168, 230)
    sc.text(139, 168, 'NEXT PHASES (UT)')
    y = 121
    for t, name in next_phases(al.j):
        d, m, yr = jd_to_date(t)
        sc.text(y, 168, name)
        x = sc.text(y, 300, '%02d-%02d ' % (d, m))
        sc.phm(y, x, ut_hours(t))
        y -= 16
    for k in range(8):
        x = 168 + k * 29
        sc.glyph(SYMB, str(k), 26, x)
        if k == p:
            sc.xor_box(23, x - 3, 18, 18)
    sc.text(6, 168, 'AS SEEN FROM THE SOUTH' if south else 'AS SEEN FROM THE NORTH')
    return [sc.rows()]


VIEWS = {'ALMANAC': almanac, 'CHART': chart, 'SKY': sky_frames, 'SPLIT': split, 'ANIM': anim, 'ALLSKY': allsky,
         'MOON': moon_view}
