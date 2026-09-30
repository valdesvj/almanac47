#!/usr/bin/env python3
"""genviews_atx.py - EXPERIMENTAL: the NAV views with ATEXT (the C47's standard font) for the texts
and numbers; the body symbols (Sun, Moon, planets, stars) through PSYM (AGRAPH glyphs).

The views are those of genf.py (ALMF, ALMS), genv.py (HALMV), genh2.py (HORZ), genhh.py (HALMH),
genanim.py (HANIM) and genallsky.py (ALLSKY), with the same calculation steps (the sky cache,
gencache.swap, still finds them) and new columns and rows for the standard font. No warning line
on the views (it stays in the menu and INFO).

Two variants:
  programs/atext/      (SMALL = True, NAVFULL_ATX) the charts as NAVFULL: axes, altitude marks,
                       N E S W, OVER / UNDER HORIZON, the ALLSKY stars and numbers, the SKY DR
                       line and T / S in the small font (PTXT, PTNS)
  programs/atext/big/  (SMALL = False, the DM42 _ATX builds) ALMF and HALMV all in ATEXT: the
                       altitude labels and letters in the standard font (the chart horizon 4 rows
                       higher so the letters fit under it)

The text routines keep their stack (Z row of the base line, Y column, X text or number; they
return Y row, X next column); the standard font is proportional, so every column is its own call
at a fixed x, numbers apart from letters, and a chained text must not start after x 380.

  python3 genviews_atx.py      -> programs/atext/*.txt and programs/atext/big/*.txt
"""
import math, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path[:0] = [os.path.join(ROOT, 'python'), os.path.join(ROOT, 'python', 'native')]
from stdfont import STD, code
OUT = os.path.join(ROOT, 'programs', 'atext')
SYM = 'PSYM'                                  # the AGRAPH symbols
SMALL = True      # True (NAVFULL_ATX): chart axes, letters and the ALLSKY stars in the small font, as NAVFULL


def width(t):
    return sum(sum(STD[code(c)][:3]) for c in t)


# a number printer: 4 places for sign and degrees, then ' mm.m' (the degrees end at place 4)
PDM = 4 * 8 + 8 + 16 + width('.') + 8        # 69 px
ZNW = width('000.0')
HMW = width('00:00')
DTW = width('00-00-0000')
NAMEW = max(width(n) for n in __import__('c47data').STAR_NAME.values() if n)     # 102 px


class Gen:
    def __init__(self):
        self.P = []

    def a(self, *xs):
        for x in xs:
            self.P.extend(str(x).split('\n'))

    def txt(self, y, x, s):
        self.a(y, x, '"%s"' % s, 'XEQ "PTXS"')

    def num(self, y, x, reg, fn):
        self.a(y, x, 'RCL %s' % reg, 'XEQ "%s"' % fn)


def top_x():
    """The top line: date, time, UT, DR, N lat, E lon (lat and lon: printer fields)."""
    X = {'date': 2}
    X['time'] = 2 + DTW + 8
    X['UT'] = X['time'] + HMW + 8
    X['DR'] = X['UT'] + width('UT') + 8
    X['N'] = X['DR'] + width('DR') + 8
    X['lat'] = X['N'] + width('N') + 8 - 16            # tens of degrees after N (2 blank places)
    X['E'] = X['lat'] + PDM + 8
    X['lon'] = X['E'] + width('W') + 8 - 8             # hundreds after E (1 blank place)
    assert X['lon'] + PDM < 386
    return X


def table_x():
    X = {'num': 14, 'name': 36}                       # the symbol at 0 (AGRAPH, 11 px)
    X['gha'] = X['name'] + NAMEW + 8 - 8               # hundreds of GHA after the longest name
    X['ns'] = X['gha'] + PDM + 4
    X['dec'] = X['ns'] + width('N') + 6 - 16
    X['hc'] = X['dec'] + PDM + 6 - 8                   # the sign of Hc
    X['zn'] = X['hc'] + PDM + 6
    assert X['zn'] + ZNW <= 398
    c = lambda a, b, t: round((a + b - width(t)) / 2)
    X['hGHA'] = c(X['gha'] + 8, X['gha'] + PDM, 'GHA')
    X['hDEC'] = c(X['ns'], X['dec'] + PDM, 'DEC')
    X['hHC'] = c(X['hc'] + 8, X['hc'] + PDM, 'HC')
    X['hZN'] = c(X['zn'], X['zn'] + ZNW, 'ZN')
    return X


def header(g, y, jd_reg, lat_reg, lon_reg, X, n_lab=22, e_lab=27):
    g.num(y, X['date'], jd_reg, 'PDTS')
    g.a(y, X['time'], 'RCL %s' % jd_reg, '0.5', '+', '1', 'MOD', '24', '×', 'XEQ "PHMS"'); g.txt(y, X['UT'], 'UT')
    g.txt(y, X['DR'], 'DR')
    g.a('"N"', 'STO 43', 'RCL %s' % lat_reg, 'X<0?', 'XEQ %d' % n_lab); g.a(y, X['N'], 'RCL 43', 'XEQ "PTXS"')
    g.a(y, X['lat'], 'RCL %s' % lat_reg, 'ABS', 'XEQ "PDMS"')
    g.a('"E"', 'STO 43', 'RCL %s' % lon_reg, 'X<0?', 'XEQ %d' % e_lab); g.a(y, X['E'], 'RCL 43', 'XEQ "PTXS"')
    g.a(y, X['lon'], 'RCL %s' % lon_reg, 'ABS', 'XEQ "PDMS"')


def hc_box(g, lab, x, w, pitch_reg='RCL 40'):
    """LBL lab: the Hc below the horizon, white on black (XOR box over the Hc field)."""
    g.a('LBL %d' % lab, 'WSIZE 16', '3', 'STO 32', 'GRMOD 32', '11111111111111#2', 'STO 32', pitch_reg, '1', '-', x, w, 'STO 33', 'R↓',
        'LBL 66', 'AGRAPH 32', 'DSE 33', 'GTO 66', '0', 'STO 32', 'GRMOD 32', 'WSIZE 64', 'RTN')


def alt_marks(g, HY, HS, ys_extra=()):
    """Altitude marks (sine scale) with the labels in the standard font at x 0, where there is room."""
    last = -99
    for v in (10, 20, 30, 45, 60, 90):
        y = HY + int(HS * math.sin(math.radians(v)))
        g.a(y, 15, 'PIXEL', y, 16, 'PIXEL', y, 17, 'PIXEL')
        if y - last >= 13:
            g.a(y - 6, 0, v, 'XEQ "PINS"'); last = y


# ---------------------------------------------------------------- ALMF / ALMS (genf.py)
def almf(short):
    g = Gen(); a, txt, num = g.a, g.txt, g.num
    T, X = top_x(), table_x()
    NAME = 'ALMS' if short else 'ALMF'
    ROWS, TOP, PITCH = 10, 193, 14
    NX, GX, NSX, DX, HX, ZX = X['name'], X['gha'], X['ns'], X['dec'], X['hc'], X['zn']
    a('LBL "%s"' % NAME, 'STO 12', 'R↓', 'STO 11', 'R↓', 'STO 10')
    for reg, lab in ((13, 'NTWA'), (14, 'RISE'), (15, 'TRAN'), (16, 'SET'), (17, 'NTWP')):
        a('XEQ 26', 'XEQ "%s"' % lab, 'STO %d' % reg)
    a('RCL 10', 'STO 90', 'RCL 11', 'STO 91', 'RCL 12', 'STO 92', 'XEQ "HCZI"', 'CLLCD')
    a('RCL 10', 'XEQ "SUNA"', 'STO 45', 'R↓', 'STO 46', 'R↓', 'STO 48', 'RCL 73', '15.99383', 'X<>Y', '÷', 'STO 29')
    a('XEQ "PHA2"', 'STO 18', 'X<>Y', 'STO 19')
    header(g, 226, 10, 11, 12, T)
    a('-221', '0', 'PIXEL')
    txt(207, NX, 'BODY'); txt(207, X['hGHA'], 'GHA'); txt(207, X['hDEC'], 'DEC'); txt(207, X['hHC'], 'HC'); txt(207, X['hZN'], 'ZN')
    a(TOP, NX, '"ARIES"', 'XEQ "PTXS"', TOP, GX, 'RCL 48', 'XEQ "PDMS"')
    a('%d' % (TOP - PITCH), 'STO 40', 'RCL 46', 'RCL 45', 'XEQ "HCZ"')
    a('RCL 40', '0', '"@"', 'XEQ "%s"' % SYM, 'RCL 40', NX, '"SUN"', 'XEQ "PTXS"', 'XEQ 60')
    a('2', 'STO 41')
    a('XEQ "MOO2"', 'STO 45', 'R↓', 'STO 46', 'R↓', 'STO 21', 'R↓', 'STO 22', 'RCL 46', 'RCL 45', 'XEQ "HCZ"', 'RCL 96', 'X>0?', 'XEQ 61')
    star = ['RCL 40', '0', '"*"', 'XEQ "%s"' % SYM, 'RCL 40', X['num'], 'RCL 82', 'XEQ "PINS"', 'RCL 82', 'XEQ "SNMU"', 'STO 43',
            'RCL 40', NX, 'RCL 43', 'XEQ "PTXS"', 'XEQ 60']
    if short:
        a('1.004', 'STO 24', 'LBL 16', 'RCL 24', 'IP', '90', '+', 'STO 43', 'XEQ IND 43', 'STO 42', 'XEQ "PLN3"', 'STO 45', 'X<>Y', 'STO 46', 'RCL 46', 'RCL 45', 'XEQ "HCZ"',
          'RCL 96', 'X>0?', 'GTO 15', 'ISG 24', 'GTO 16', 'GTO 14', 'LBL 15', 'XEQ 63', 'LBL 14')
        a('0', 'STO 24', '1.058', 'STO 42', 'LBL 17', '3', 'RCL 24', 'X≥Y?', 'GTO 19', 'RCL 42', 'IP', 'XEQ "SBRT"', 'STO 82', 'XEQ "SQK"', '0.15643', 'X>Y?', 'GTO 18',
          'XEQ "STR2"', 'STO 45', 'X<>Y', 'STO 46', 'RCL 46', 'RCL 45', 'XEQ "HCZ"', '10', 'RCL 96', 'X≤Y?', 'GTO 18', *star,
          '1', 'STO+ 41', '1', 'STO+ 24', 'LBL 18', 'ISG 42', 'GTO 17', 'LBL 19')
    else:
        a('1.004', 'STO 42', 'LBL 16', 'RCL 42', 'IP', 'XEQ "PLN3"', 'STO 45', 'X<>Y', 'STO 46', 'RCL 46', 'RCL 45', 'XEQ "HCZ"', 'RCL 96', 'X>0?', 'XEQ 63', 'ISG 42', 'GTO 16')
        a('1.058', 'STO 42', 'LBL 17', ROWS, 'RCL 41', 'X≥Y?', 'GTO 19', 'RCL 42', 'IP', 'XEQ "SBRT"', 'STO 82', 'XEQ "SQK"', '0.15643', 'X>Y?', 'GTO 18',
          'XEQ "STR2"', 'STO 45', 'X<>Y', 'STO 46', 'RCL 46', 'RCL 45', 'XEQ "HCZ"', '10', 'RCL 96', 'X≤Y?', 'GTO 18', *star,
          '1', 'STO+ 41', 'LBL 18', 'ISG 42', 'GTO 17', 'LBL 19')
    FY = TOP - PITCH * ROWS
    a('-%d' % (FY + 8), '0', 'PIXEL')
    y1, y2, y3 = FY - 6, FY - 20, FY - 34
    t1 = 2 + max(width(t) for t in ('NAUT TWI', 'RISE/SET', 'MER PASS')) + 8
    t2 = t1 + HMW + 8
    txt(y1, 2, 'NAUT TWI'); num(y1, t1, 13, 'PHMS'); num(y1, t2, 17, 'PHMS')
    txt(y2, 2, 'RISE/SET'); num(y2, t1, 14, 'PHMS'); num(y2, t2, 16, 'PHMS')
    txt(y3, 2, 'MER PASS'); num(y3, t1, 15, 'PHMS'); a(y3, t2, '"SD "', 'XEQ "PTXS"', 'RCL 29', 'XEQ "PF1S"')
    MX = 212
    assert t2 + width('SD 00.0') < MX and MX + width('MOON 100% WANING') < 398
    a('"WAXING"', 'STO 43', 'RCL 19', '14.765', 'X<Y?', 'XEQ 28', 'RCL 18', '99.5', 'X≤Y?', 'XEQ 23', 'RCL 18', '0.5', 'X>Y?', 'XEQ 24')
    a(y1, MX, '"MOON "', 'XEQ "PTXS"', 'RCL 18', 'XEQ "PINS"', '"% "', 'XEQ "PTXS"', 'RCL 43', 'XEQ "PTXS"')
    a(y2, MX, '"AGE "', 'XEQ "PTXS"', 'RCL 19', 'XEQ "PF1S"', '" DAYS"', 'XEQ "PTXS"')
    a(y3, MX, '"HP "', 'XEQ "PTXS"', 'RCL 21', 'XEQ "PF1S"', '" SD "', 'XEQ "PTXS"', 'RCL 22', 'XEQ "PF1S"')
    a('"S"', 'STO 43', 'FS? 11', 'XEQ 29', 'FS? 12', 'XEQ 65', 226, 388, 'RCL 43', 'XEQ "PTXS"')
    a('XEQ "WPLS"', 'RTN')
    a('LBL 26', 'RCL 10', '0.5', '-', 'IP', '0.5', '+', 'RCL 11', 'RCL 12', 'RTN')
    a('LBL 29', '"T"', 'STO 43', 'RTN', 'LBL 65', '"X"', 'STO 43', 'RTN')
    a('LBL 23', '"FULL"', 'STO 43', 'RTN', 'LBL 24', '"NEW"', 'STO 43', 'RTN')
    a('LBL 28', '"WANING"', 'STO 43', 'RTN', 'LBL 22', '"S"', 'STO 43', 'RTN', 'LBL 27', '"W"', 'STO 43', 'RTN')
    a('LBL 60', 'RCL 40', GX, 'RCL 45', 'XEQ "PDMS"',
      '"N"', 'STO 43', 'RCL 46', 'X<0?', 'XEQ 22', 'RCL 40', NSX, 'RCL 43', 'XEQ "PTXS"', 'RCL 40', DX, 'RCL 46', 'ABS', 'XEQ "PDMS"',
      'RCL 40', HX, 'RCL 96', 'XEQ "PDMS"', 'RCL 40', ZX, 'RCL 97', 'XEQ "PZNS"', 'RCL 96', 'X<0?', 'XEQ 64', PITCH, 'STO- 40', 'RTN')
    hc_box(g, 64, HX + 7, PDM - 6)
    a('LBL 61', 'RCL 40', '0', '"("', 'XEQ "%s"' % SYM, 'RCL 40', NX, '"MOON"', 'XEQ "PTXS"', 'XEQ 60', '1', 'STO+ 41', 'RTN')
    a('LBL 63', 'RCL 42', 'IP', '70', '+', 'STO 43', 'RCL 40', '0', 'XEQ IND 43', 'XEQ "%s"' % SYM, 'RCL 42', 'IP', '81', '+', 'STO 43',
      'RCL 40', NX, 'XEQ IND 43', 'XEQ "PTXS"', 'XEQ 60', '1', 'STO+ 41', 'RTN')
    for lab, t in ((71, '<'), (72, '>'), (73, '='), (74, '?'), (82, 'VENUS'), (83, 'MARS'), (84, 'JUPITER'), (85, 'SATURN')):
        a('LBL %d' % lab, '"%s"' % t, 'RTN')
    if short:
        for lab, pn in ((91, 1), (92, 3), (93, 2), (94, 4)):
            a('LBL %d' % lab, str(pn), 'RTN')
    a('END')
    return NAME, g.P


# ---------------------------------------------------------------- HALMV (genv.py)
def halmv():
    g = Gen(); a, txt = g.a, g.txt
    X0, CW = 176, 150
    HY, HS = (14, 200) if SMALL else (18, 196)      # big letters: the horizon 4 rows higher
    a('LBL "HALMV"', 'STO 12', 'R↓', 'STO 11', 'R↓', 'STO 10')
    a('RCL 10', 'STO 90', 'RCL 11', 'STO 91', 'RCL 12', 'STO 92', 'XEQ "HCZI"', 'CLLCD')
    a('0', '-%d' % (X0 - 4), 'PIXEL')
    a(HY, '18', CW + 1, 'XEQ "PHLS"')
    a('%d.%03d' % (HY, HY + HS), 'STO 47', 'LBL 12', 'RCL 47', 'IP', '17', 'PIXEL', 'ISG 47', 'GTO 12')
    xs = [16 + CW * k // 4 for k in range(5)]
    if SMALL:
        for v in (10, 20, 30, 45, 60, 90):
            y = HY + int(HS * math.sin(math.radians(v)))
            a(y, 15, 'PIXEL', y, 16, 'PIXEL', y - 2, 2, v, 'XEQ "PTNS"')
        lt = lambda x, l: a(5, x, '"%s"' % l, 'XEQ "PTXT"')
    else:
        alt_marks(g, HY, HS)
        xs = [min(max(x - width(l) // 2 + 1, 0), X0 - 6 - width(l)) for x, l in zip(xs, 'NESWN')]
        lt = lambda x, l: txt(4, x, l)
    a('0', 'STO 44', 'RCL 11', 'X<0?', 'GTO 23')
    for x, l in zip(xs, 'NESWN'): lt(x, l)
    a('GTO 24', 'LBL 23', '180', 'STO 44')
    for x, l in zip(xs, 'SWNES'): lt(x, l)
    a('LBL 24')
    a('RCL 10', 'XEQ "SUNA"', 'STO 45', 'R↓', 'STO 46', 'R↓', 'STO 48')
    a('XEQ "PHA2"', 'STO 18', 'X<>Y', 'STO 19')
    a('0', '3', 'XEQ "HCZQ"', '0', 'STO 47', 'LBL 14', 'XEQ 51', 'RCL 96', '1E-4', 'X<Y?', 'XEQ 15', '3', 'STO+ 47', '357', 'RCL 47', 'X≤Y?', 'GTO 14')
    # panel: date time UT | N lat E lon | ARIES | titles
    g.num(226, X0, 10, 'PDTS')
    tx = X0 + DTW + 8
    a(226, tx, 'RCL 10', '0.5', '+', '1', 'MOD', '24', '×', 'XEQ "PHMS"'); txt(226, tx + HMW + 8, 'UT')
    lat = X0 + width('N') + 8 - 16
    ex = lat + PDM + 8
    a('"N"', 'STO 43', 'RCL 11', 'X<0?', 'XEQ 22'); a(212, X0, 'RCL 43', 'XEQ "PTXS"'); a(212, lat, 'RCL 11', 'ABS', 'XEQ "PDMS"')
    a('"E"', 'STO 43', 'RCL 12', 'X<0?', 'XEQ 27'); a(212, ex, 'RCL 43', 'XEQ "PTXS"'); a(212, ex + width('W'), 'RCL 12', 'ABS', 'XEQ "PDMS"')
    assert ex + width('W') + PDM <= 398
    txt(198, X0, 'ARIES'); a(198, X0 + width('ARIES'), 'RCL 48', 'XEQ "PDMS"')
    ZX = 398 - ZNW
    HX = ZX - 6 - PDM                          # the Hc field (its sign at HX + 8)
    NM = X0 + 14
    txt(184, NM, 'BODY'); txt(184, round(HX + 8 + (PDM - 8 - width('HC')) / 2), 'HC'); txt(184, round(ZX + (ZNW - width('ZN')) / 2), 'ZN')
    a('170', 'STO 40')
    a('RCL 46', 'RCL 45', 'XEQ 52', 'RCL 96', 'X>0?', 'XEQ 16')
    a('RCL 40', X0, '"@"', 'XEQ "%s"' % SYM, 'RCL 40', NM, '"SUN"', 'XEQ "PTXS"', 'XEQ 60')
    a('1', 'STO 41')
    a('XEQ "MOO2"', 'STO 45', 'R↓', 'STO 46', 'RCL 46', 'RCL 45', 'XEQ 52', 'RCL 96', 'X>0?', 'XEQ 61')
    a('1.004', 'STO 42', 'LBL 62', 'RCL 42', 'IP', 'XEQ "PLN3"', 'STO 45', 'X<>Y', 'STO 46', 'RCL 46', 'RCL 45', 'XEQ 52', 'RCL 96', 'X>0?', 'XEQ 63', 'ISG 42', 'GTO 62')
    a('1.058', 'STO 42', 'LBL 17', '10', 'RCL 41', 'X≥Y?', 'GTO 19', 'RCL 42', 'IP', 'XEQ "SBRT"', 'STO 82', 'XEQ "SQK"', '0.15643', 'X>Y?', 'GTO 18',
      'XEQ "STR2"', 'STO 45', 'X<>Y', 'STO 46', 'RCL 46', 'RCL 45', 'XEQ 52', '10', 'RCL 96', 'X≤Y?', 'GTO 18',
      'XEQ 57', 'RCL 40', X0, '"*"', 'XEQ "%s"' % SYM,
      'RCL 82', 'XEQ "SNMU"', 'STO 43', 'RCL 40', NM, 'RCL 43', 'XEQ "PTXS"', 'XEQ 60',
      '1', 'STO+ 41', 'LBL 18', 'ISG 42', 'GTO 17', 'LBL 19')
    a('"WAXING"', 'STO 43', 'RCL 19', '14.765', 'X<Y?', 'XEQ 28', 'RCL 18', '99.5', 'X≤Y?', 'XEQ 25', 'RCL 18', '0.5', 'X>Y?', 'XEQ 30')
    a(24, X0, '"MOON "', 'XEQ "PTXS"', 'RCL 18', 'XEQ "PINS"', '"% "', 'XEQ "PTXS"', 'RCL 43', 'XEQ "PTXS"')
    a('"S"', 'STO 43', 'FS? 11', 'XEQ 29', 'FS? 12', 'XEQ 65', 226, 388, 'RCL 43', 'XEQ "PTXS"')
    a('XEQ "WPLS"', 'RTN')
    a('LBL 29', '"T"', 'STO 43', 'RTN', 'LBL 65', '"X"', 'STO 43', 'RTN')
    a('LBL 25', '"FULL"', 'STO 43', 'RTN', 'LBL 30', '"NEW"', 'STO 43', 'RTN')
    a('LBL 28', '"WANING"', 'STO 43', 'RTN', 'LBL 22', '"S"', 'STO 43', 'RTN', 'LBL 27', '"W"', 'STO 43', 'RTN')
    a('LBL 15', 'RCL 99', 'RCL 98', 'PIXEL', 'RCL 99', 'RCL 98', '1', '+', 'PIXEL', 'RCL 99', '1', '+', 'RCL 98', 'PIXEL', 'RCL 99', '1', '+', 'RCL 98', '1', '+', 'PIXEL', 'RTN')
    a('LBL 16', 'RCL 99', '6', '-', 'RCL 98', '6', '-', '"@"', 'XEQ "%s"' % SYM, 'RTN')
    a('LBL 51', 'XEQ "HCZR"', 'GTO 49')
    a('LBL 52', 'XEQ "HCZ"', 'LBL 49', 'RCL 97', 'RCL+ 44', '360', 'MOD', CW, '×', '360', '÷', '18', '+', 'IP', 'STO 98',
      'RCL "SHC"', HS, '×', HY, '+', 'IP', 'STO 99', 'RTN')
    a('LBL 57', 'RCL 99', '6', '-', 'RCL 98', '6', '-', '"*"', 'XEQ "%s"' % SYM, 'RCL 98', '8', '+', 'STO 43', 18 + CW - 20, 'RCL 43', 'X>Y?', 'XEQ 21',
      'RCL 99', '6', '-', 'RCL 43', 'RCL 82', 'XEQ "PINS"', 'RTN', 'LBL 21', '36', 'STO- 43', 'RTN')
    a('LBL 60', 'RCL 40', HX, 'RCL 96', 'XEQ "PDMS"', 'RCL 40', ZX, 'RCL 97', 'XEQ "PZNS"', 'RCL 96', 'X<0?', 'XEQ 64', '14', 'STO- 40', 'RTN')
    hc_box(g, 64, HX + 7, PDM - 6)
    a('LBL 61', 'RCL 99', '6', '-', 'RCL 98', '6', '-', '"("', 'XEQ "%s"' % SYM, 'RCL 40', X0, '"("', 'XEQ "%s"' % SYM,
      'RCL 40', NM, '"MOON"', 'XEQ "PTXS"', 'XEQ 60', '1', 'STO+ 41', 'RTN')
    a('LBL 63', 'RCL 42', 'IP', '70', '+', 'STO 43', 'RCL 99', '6', '-', 'RCL 98', '6', '-', 'XEQ IND 43', 'XEQ "%s"' % SYM,
      'RCL 40', X0, 'XEQ IND 43', 'XEQ "%s"' % SYM, 'RCL 42', 'IP', '81', '+', 'STO 43', 'RCL 40', NM, 'XEQ IND 43', 'XEQ "PTXS"',
      'XEQ 60', '1', 'STO+ 41', 'RTN')
    for lab, t in ((71, '<'), (72, '>'), (73, '='), (74, '?'), (82, 'VENUS'), (83, 'MARS'), (84, 'JUPITER'), (85, 'SATURN')):
        a('LBL %d' % lab, '"%s"' % t, 'RTN')
    a('END')
    return 'HALMV', g.P


# ---------------------------------------------------------------- HORZ (genh2.py, with the info line)
def horz():
    g = Gen(); a = g.a
    HS, rows = 196, 10
    a('LBL "HORZ"', 'STO 92', 'R↓', 'STO 91', 'R↓', 'STO 90', 'XEQ "HCZI"', 'CLLCD')
    a('16', '20', '376', 'XEQ "PHLS"')
    a('18.21203', 'STO 86', 'LBL 50', 'RCL 86', 'IP', '18', 'PIXEL', 'ISG 86', 'GTO 50')
    for c in (20, 51, 82, 113, 145, 176, 207, 238, 270, 301, 332, 363, 395):
        for y in (15, 14, 13): a(y, c, 'PIXEL')
    last = -99
    for v in (10, 20, 30, 45, 60, 90):
        y = 16 + int(HS * math.sin(math.radians(v)))
        for x in (15, 16, 17): a(y, x, 'PIXEL')
        if SMALL:
            a(y - 2, 2, v, 'XEQ "PTNS"')
        elif y - last >= 13:
            a(y - 6, 0, v, 'XEQ "PINS"'); last = y
    if SMALL:
        xs = (19, 112, 206, 300, 394)
        lt = lambda x, l: a(7, x, '"%s"' % l, 'XEQ "PTXT"')
    else:
        xs = [min(x + 3, 398 - width('W')) for x in (19, 112, 206, 300, 394)]
        lt = lambda x, l: g.txt(4, x, l)
    a('0', 'STO 44', 'RCL 91', 'X<0?', 'GTO 38')
    for x, l in zip(xs, 'NESWN'): lt(x, l)
    a('GTO 37', 'LBL 38', '180', 'STO 44')
    for x, l in zip(xs, 'SWNES'): lt(x, l)
    a('LBL 37', 'RCL 90', 'XEQ "SUNA"',
      '%d' % rows, 'ENTER', '3', 'NEWMAT', 'STO "HZT"', '0', 'STO 10',
      '0', '2', 'XEQ "HCZQ"', '0', 'STO 86', 'LBL 53', 'XEQ 51', 'RCL 96', '1E-4', 'X<Y?', 'XEQ 55', '2', 'STO+ 86', '358', 'RCL 86', 'X≤Y?', 'GTO 53',
      'RCL 77', 'RCL 81', 'XEQ 52', 'RCL 96', 'X>0?', 'XEQ 56', '0', 'XEQ 40',
      'XEQ "MOO2"', 'XEQ 52', 'RCL 96', 'X>0?', 'XEQ 47',
      '1.004', 'STO 11', 'LBL 45', 'RCL 11', 'IP', 'XEQ "PLN3"', 'XEQ 52', 'RCL 96', 'X>0?', 'XEQ 48', 'ISG 11', 'GTO 45',
      '1.058', 'STO 11', 'LBL 44', '%d' % rows, 'RCL 10', 'X≥Y?', 'GTO 42', 'RCL 11', 'IP', 'XEQ "SBRT"', 'STO 82', 'XEQ "SQK"', '0.15643', 'X>Y?', 'GTO 36', 'XEQ "STR2"', 'XEQ 52',
      '10', 'RCL 96', 'X>Y?', 'XEQ 43', 'LBL 36', 'ISG 11', 'GTO 44', 'LBL 42')
    DRX = 388 - width('S 89 59  W 179 59')     # a chained text must not end after 380 (ATEXT: next line)
    if SMALL:                                  # T / S and the DR position in the small font, as NAVFULL
        a('"S"', 'STO 15', 'FS? 11', 'XEQ 29', 'FS? 12', 'XEQ 65', '7', '2', 'RCL 15', 'XEQ "PTXT"')
        a('"N"', 'STO 43', 'RCL 91', 'X<0?', 'XEQ 59', '"E"', 'STO 39', 'RCL 92', 'X<0?', 'XEQ 60',
          '215', '326', 'RCL 43', 'XEQ "PTXT"', 'RCL 91', 'XEQ 54', '"  "', 'XEQ "PTXT"', 'RCL 39', 'XEQ "PTXT"', 'RCL 92', 'XEQ 54')
    else:
        a('"S"', 'STO 15', 'FS? 11', 'XEQ 29', 'FS? 12', 'XEQ 65', '4', '2', 'RCL 15', 'XEQ "PTXS"')
        a('"N"', 'STO 43', 'RCL 91', 'X<0?', 'XEQ 59', '"E"', 'STO 39', 'RCL 92', 'X<0?', 'XEQ 60',
          '212', DRX, 'RCL 43', 'XEQ "PTXS"', '" "', 'XEQ "PTXS"', 'RCL 91', 'XEQ 54', '"  "', 'XEQ "PTXS"', 'RCL 39', 'XEQ "PTXS"',
          '" "', 'XEQ "PTXS"', 'RCL 92', 'XEQ 54')
    UTX = 398 - width('00:00 UT')
    a('RCL 10', 'X=0?', 'RTN', '1', 'STO 42',
      'LBL 35', 'INDEX "HZT"', 'RCL 42', '1', 'STOIJ', 'RCLEL', 'J+', 'STO 13', 'RCLEL', 'J+', 'STO 97', 'RCLEL', 'STO 96',
      '224', '0', 'CLLCDxy',
      'RCL 13', 'X=0?', 'GTO 31', 'X<0?', 'GTO 32',
      'RCL 13', 'XEQ "SNMU"', 'STO 14', '227', '2', 'RCL 13', 'XEQ "PINS"', '" "', 'XEQ "PTXS"', 'RCL 14', 'XEQ "PTXS"', 'GTO 30',
      'LBL 32', 'RCL 13', 'CHS', '80', '+', 'STO 14', '227', '2', 'XEQ IND 14', 'XEQ "PTXS"', 'GTO 30',
      'LBL 31', '227', '2', '"SUN"', 'XEQ "PTXS"',
      'LBL 30', '"  ZN "', 'XEQ "PTXS"', 'RCL 97', 'XEQ "PF1S"', '"  HC "', 'XEQ "PTXS"', 'RCL 96', 'X<0?', 'XEQ 33', 'XEQ "PF1S"',
      '227', UTX, 'RCL 90', '0.5', '+', '1', 'MOD', '24', '×', 'XEQ "PHMS"', '" UT"', 'XEQ "PTXS"',
      'PAUSE 0', 'TICKS', '30', '+', 'STO 38',
      'LBL 41', 'KEY? 39', 'GTO 46', 'RCL 39', '85', 'X=Y?', 'RTN', 'RCL 39', '51', 'X=Y?', 'RTN', 'RCL 39', '61', 'X=Y?', 'RTN',
      'LBL 62', '1', 'STO+ 42', 'RCL 10', 'RCL 42', 'X>Y?', 'XEQ 34', 'GTO 35',
      'LBL 46', 'TICKS', 'RCL 38', 'X>Y?', 'GTO 41', 'GTO 62',
      'LBL 34', '1', 'STO 42', 'RTN',
      'LBL 33', 'R↓', '"-"', 'XEQ "PTXS"', 'RCL 96', 'RTN')
    a('LBL 29', '"T"', 'STO 15', 'RTN', 'LBL 65', '"X"', 'STO 15', 'RTN')
    a('LBL 59', '"S"', 'STO 43', 'RTN', 'LBL 60', '"W"', 'STO 39', 'RTN')
    # LBL 54: "dd mm" (rounded to the minute), the minutes with two digits
    if SMALL:
        a('LBL 54', 'ABS', '60', '×', '0.5', '+', 'IP', 'STO 37', '60', '÷', 'IP', 'XEQ "PTNS"', '" "', 'XEQ "PTXT"',
          'RCL 37', '60', 'MOD', 'XEQ "PTNS"', 'RTN')
    else:
        a('LBL 54', 'ABS', '60', '×', '0.5', '+', 'IP', 'STO 37', '60', '÷', 'IP', 'XEQ "PINS"', '" "', 'XEQ "PTXS"',
          'RCL 37', '60', 'MOD', 'STO 37', '10', '÷', 'IP', 'XEQ "PINS"', 'RCL 37', '10', 'MOD', 'XEQ "PINS"', 'RTN')
    a('LBL 40', 'STO 13', '1', 'STO+ 10', 'INDEX "HZT"', 'RCL 10', '1', 'STOIJ', 'RCL 13', 'STOEL', 'J+', 'RCL 97', 'STOEL', 'J+', 'RCL 96', 'STOEL', 'RTN')
    a('LBL 47', '241', 'RCL- 99', '6', '-', 'RCL 98', '6', '-', '"("', 'XEQ "%s"' % SYM, '-1', 'XEQ 40', 'RTN')
    a('LBL 48', 'RCL 11', 'IP', '70', '+', 'STO 14', '241', 'RCL- 99', '6', '-', 'RCL 98', '6', '-', 'XEQ IND 14', 'XEQ "%s"' % SYM,
      'RCL 11', 'IP', '1', '+', 'CHS', 'XEQ 40', 'RTN')
    a('LBL 43', 'XEQ 57', 'RCL 82', 'XEQ 40', 'RTN')
    for lab, s in ((71, '<'), (72, '>'), (73, '='), (74, '?')): a('LBL %d' % lab, '"%s"' % s, 'RTN')
    for lab, s in ((81, 'MOON'), (82, 'VENUS'), (83, 'MARS'), (84, 'JUPITER'), (85, 'SATURN')): a('LBL %d' % lab, '"%s"' % s, 'RTN')
    a('LBL 55', '241', 'RCL- 99', 'STO 36', 'RCL 98', 'PIXEL', 'RCL 36', 'RCL 98', '1', '+', 'PIXEL', 'RCL 36', '1', '+', 'RCL 98', 'PIXEL', 'RCL 36', '1', '+', 'RCL 98', '1', '+', 'PIXEL', 'RTN')
    a('LBL 51', 'XEQ "HCZR"', 'GTO 49')
    a('LBL 52', 'XEQ "HCZ"', 'LBL 49', 'RCL 97', 'RCL+ 44', '360', 'MOD', '375', '×', '360', '÷', '20', '+', 'IP', 'STO 98',
      '225', 'RCL "SHC"', HS, '×', '-', 'IP', 'STO 99', 'RTN')
    a('LBL 56', '241', 'RCL- 99', '6', '-', 'RCL 98', '6', '-', '"@"', 'XEQ "%s"' % SYM, 'RTN')
    a('LBL 57', '241', 'RCL- 99', '6', '-', 'RCL 98', '6', '-', '"*"', 'XEQ "%s"' % SYM,
      'RCL 98', '8', '+', 'STO 36', '380', 'RCL 36', 'X>Y?', 'XEQ 39',
      '241', 'RCL- 99', '6', '-', 'RCL 36', 'RCL 82', 'XEQ "PINS"', 'RTN',
      'LBL 39', '36', 'STO- 36', 'RTN')
    a('END')
    return 'HORZ', g.P


# ---------------------------------------------------------------- HALMH (genhh.py)
def halmh():
    g = Gen(); a, txt, num = g.a, g.txt, g.num
    T, X = top_x(), table_x()
    NX, GX, NSX, DX, HX, ZX = X['name'], X['gha'], X['ns'], X['dec'], X['hc'], X['zn']
    if SMALL:
        HY, HS, TOP = 129, 89, 107    # as NAVFULL; 6 table rows at most: Sun, Moon, a planet, 3 stars
    else:
        HY, HS, TOP = 132, 86, 102    # big letters under the horizon (row 118)
    a('LBL "HALMH"', 'STO 12', 'R↓', 'STO 11', 'R↓', 'STO 10')
    for reg, lab in ((13, 'NTWA'), (14, 'RISE'), (15, 'TRAN'), (16, 'SET'), (17, 'NTWP')):
        a('XEQ 26', 'XEQ "%s"' % lab, 'STO %d' % reg)
    a('RCL 10', 'STO 90', 'RCL 11', 'STO 91', 'RCL 12', 'STO 92', 'XEQ "HCZI"', 'CLLCD')
    a('RCL 10', 'XEQ "SUNA"', 'STO 45', 'R↓', 'STO 46', 'R↓', 'STO 48')
    a('XEQ "PHA2"', 'STO 18', 'X<>Y', 'STO 19')
    header(g, 226, 10, 11, 12, T)
    a(HY, '20', '376', 'XEQ "PHLS"')
    a('%d.%03d03' % (HY, HY + HS), 'STO 47', 'LBL 12', 'RCL 47', 'IP', '18', 'PIXEL', 'ISG 47', 'GTO 12')
    if SMALL:
        for v in (10, 20, 30, 45, 60, 90):
            y = HY + int(HS * math.sin(math.radians(v)))
            a(y, 15, 'PIXEL', y, 16, 'PIXEL', y, 17, 'PIXEL', y - 2, 2, v, 'XEQ "PTNS"')
    else:
        alt_marks(g, HY, HS)
    for c in (20, 51, 82, 113, 145, 176, 207, 238, 270, 301, 332, 363, 395):
        a(HY - 1, c, 'PIXEL', HY - 2, c, 'PIXEL')
    if SMALL:
        xs = (19, 112, 206, 300, 394)
        lt = lambda x, l: a(HY - 8, x, '"%s"' % l, 'XEQ "PTXT"')
    else:
        xs = [min(x + 3, 398 - width('W')) for x in (19, 112, 206, 300, 394)]
        lt = lambda x, l: txt(HY - 14, x, l)
    a('0', 'STO 44', 'RCL 11', 'X<0?', 'GTO 23')
    for x, l in zip(xs, 'NESWN'): lt(x, l)
    a('GTO 24', 'LBL 23', '180', 'STO 44')
    for x, l in zip(xs, 'SWNES'): lt(x, l)
    a('LBL 24')
    a('0', '3', 'XEQ "HCZQ"', '0', 'STO 47', 'LBL 13', 'XEQ 51', 'RCL 96', '1E-4', 'X<Y?', 'XEQ 15', '3', 'STO+ 47', '357', 'RCL 47', 'X≤Y?', 'GTO 13')
    a(TOP, 'STO 40')
    a('RCL 46', 'RCL 45', 'XEQ 52', 'RCL 96', 'X>0?', 'XEQ 16')
    a('RCL 40', '0', '"@"', 'XEQ "%s"' % SYM, 'RCL 40', NX, '"SUN"', 'XEQ "PTXS"', 'XEQ 60')
    a('XEQ "MOO2"', 'STO 45', 'R↓', 'STO 46', 'RCL 46', 'RCL 45', 'XEQ 52', 'RCL 96', 'X>0?', 'XEQ 61')
    a('1.004', 'STO 24', 'LBL 17', 'RCL 24', 'IP', '90', '+', 'STO 43', 'XEQ IND 43', 'STO 42', 'XEQ "PLN3"', 'STO 45', 'X<>Y', 'STO 46',
      'RCL 46', 'RCL 45', 'XEQ 52', 'RCL 96', 'X>0?', 'GTO 18', 'ISG 24', 'GTO 17', 'GTO 19', 'LBL 18', 'XEQ 63', 'LBL 19')
    a('0', 'STO 24', '1.058', 'STO 42', 'LBL 30', '3', 'RCL 24', 'X≥Y?', 'GTO 32',
      'RCL 42', 'IP', 'XEQ "SBRT"', 'STO 82', 'XEQ "SQK"', '0.15643', 'X>Y?', 'GTO 31', 'XEQ "STR2"', 'STO 45', 'X<>Y', 'STO 46', 'RCL 46', 'RCL 45', 'XEQ 52',
      '10', 'RCL 96', 'X≤Y?', 'GTO 31',
      'XEQ 57', 'RCL 40', '0', '"*"', 'XEQ "%s"' % SYM, 'RCL 40', X['num'], 'RCL 82', 'XEQ "PINS"',
      'RCL 82', 'XEQ "SNMU"', 'STO 43', 'RCL 40', NX, 'RCL 43', 'XEQ "PTXS"', 'XEQ 60',
      '1', 'STO+ 24', 'LBL 31', 'ISG 42', 'GTO 30', 'LBL 32')
    # footer: RISE SET MER | TWI and the Moon
    x = 2
    y1, y2 = (23, 9) if SMALL else (18, 4)
    for lab, reg in (('RISE', 14), ('SET', 16), ('MER', 15)):
        txt(y1, x, lab); x += width(lab) + 8; num(y1, x, reg, 'PHMS'); x += HMW + 16
    txt(y2, 2, 'TWI'); x = 2 + width('TWI') + 8; num(y2, x, 13, 'PHMS'); x += HMW + 8; num(y2, x, 17, 'PHMS'); x += HMW + 16
    assert x + width('MOON 100% WANING') <= 398
    a('"WAXING"', 'STO 43', 'RCL 19', '14.765', 'X<Y?', 'XEQ 28', 'RCL 18', '99.5', 'X≤Y?', 'XEQ 25', 'RCL 18', '0.5', 'X>Y?', 'XEQ 33')
    a(y2, x, '"MOON "', 'XEQ "PTXS"', 'RCL 18', 'XEQ "PINS"', '"% "', 'XEQ "PTXS"', 'RCL 43', 'XEQ "PTXS"')
    a('"S"', 'STO 43', 'FS? 11', 'XEQ 29', 'FS? 12', 'XEQ 65', 226, 388, 'RCL 43', 'XEQ "PTXS"')
    a('XEQ "WPLS"', 'RTN')
    a('LBL 26', 'RCL 10', '0.5', '-', 'IP', '0.5', '+', 'RCL 11', 'RCL 12', 'RTN')
    a('LBL 29', '"T"', 'STO 43', 'RTN', 'LBL 65', '"X"', 'STO 43', 'RTN')
    a('LBL 25', '"FULL"', 'STO 43', 'RTN', 'LBL 33', '"NEW"', 'STO 43', 'RTN', 'LBL 28', '"WANING"', 'STO 43', 'RTN')
    a('LBL 22', '"S"', 'STO 43', 'RTN', 'LBL 27', '"W"', 'STO 43', 'RTN')
    a('LBL 15', 'RCL 99', 'RCL 98', 'PIXEL', 'RCL 99', 'RCL 98', '1', '+', 'PIXEL', 'RCL 99', '1', '+', 'RCL 98', 'PIXEL', 'RCL 99', '1', '+', 'RCL 98', '1', '+', 'PIXEL', 'RTN')
    a('LBL 16', 'RCL 99', '6', '-', 'RCL 98', '6', '-', '"@"', 'XEQ "%s"' % SYM, 'RTN')
    a('LBL 51', 'XEQ "HCZR"', 'GTO 49')
    a('LBL 52', 'XEQ "HCZ"', 'LBL 49', 'RCL 97', 'RCL+ 44', '360', 'MOD', '375', '×', '360', '÷', '20', '+', 'IP', 'STO 98',
      'RCL "SHC"', HS, '×', HY, '+', 'IP', 'STO 99', 'RTN')
    a('LBL 57', 'RCL 99', '6', '-', 'RCL 98', '6', '-', '"*"', 'XEQ "%s"' % SYM, 'RCL 98', '8', '+', 'STO 43', '380', 'RCL 43', 'X>Y?', 'XEQ 21',
      'RCL 99', '6', '-', 'RCL 43', 'RCL 82', 'XEQ "PINS"', 'RTN', 'LBL 21', '36', 'STO- 43', 'RTN')
    a('LBL 60', 'RCL 40', GX, 'RCL 45', 'XEQ "PDMS"',
      '"N"', 'STO 43', 'RCL 46', 'X<0?', 'XEQ 22', 'RCL 40', NSX, 'RCL 43', 'XEQ "PTXS"', 'RCL 40', DX, 'RCL 46', 'ABS', 'XEQ "PDMS"',
      'RCL 40', HX, 'RCL 96', 'XEQ "PDMS"', 'RCL 40', ZX, 'RCL 97', 'XEQ "PZNS"', 'RCL 96', 'X<0?', 'XEQ 64', '14', 'STO- 40', 'RTN')
    hc_box(g, 64, HX + 7, PDM - 6)
    a('LBL 61', 'RCL 99', '6', '-', 'RCL 98', '6', '-', '"("', 'XEQ "%s"' % SYM,
      'RCL 40', '0', '"("', 'XEQ "%s"' % SYM, 'RCL 40', NX, '"MOON"', 'XEQ "PTXS"', 'XEQ 60', 'RTN')
    a('LBL 63', 'RCL 42', 'IP', '70', '+', 'STO 43', 'RCL 99', '6', '-', 'RCL 98', '6', '-', 'XEQ IND 43', 'XEQ "%s"' % SYM,
      'RCL 40', '0', 'XEQ IND 43', 'XEQ "%s"' % SYM, 'RCL 42', 'IP', '81', '+', 'STO 43', 'RCL 40', NX, 'XEQ IND 43', 'XEQ "PTXS"', 'XEQ 60', 'RTN')
    for lab, t in ((71, '<'), (72, '>'), (73, '='), (74, '?'), (82, 'VENUS'), (83, 'MARS'), (84, 'JUPITER'), (85, 'SATURN')):
        a('LBL %d' % lab, '"%s"' % t, 'RTN')
    for lab, pn in ((91, 1), (92, 3), (93, 2), (94, 4)):
        a('LBL %d' % lab, str(pn), 'RTN')
    a('END')
    return 'HALMH', g.P


# ---------------------------------------------------------------- ANIM and ALLSKY: the chart
def sky_chart(g, HY, lbl9, lbl10, HS=100):
    """Horizon across, its Zn ticks and N E S W under it; SMALL: as NAVFULL, the altitude axis up and
    down with its marks, the letters and OVER / UNDER HORIZON in the small font."""
    a = g.a
    a('-%d' % HY, '0', 'PIXEL')
    if SMALL:
        a('%d.%03d03' % (HY - HS, HY + HS), 'STO 26', 'LBL 08', 'RCL 26', 'IP', '18', 'PIXEL', 'ISG 26', 'GTO 08')
        for v in (10, 20, 30, 45, 60, 90):
            dy = int(HS * math.sin(math.radians(v)))
            for y in (HY + dy, HY - dy):
                a(y, 15, 'PIXEL', y, 16, 'PIXEL', y, 17, 'PIXEL', y - 2, 2, v, 'XEQ "PTNS"')
        for c in (20, 51, 82, 113, 145, 176, 207, 238, 270, 301, 332, 363, 395):
            a(HY - 1, c, 'PIXEL', HY - 2, c, 'PIXEL')
        xs = (19, 112, 206, 300, 394)
        a('RCL 44', 'X≠0?', 'GTO %02d' % lbl9)
        for x, l in zip(xs, 'NESWN'): a(HY - 8, x, '"%s"' % l, 'XEQ "PTXT"')
        a('GTO %02d' % lbl10, 'LBL %02d' % lbl9)
        for x, l in zip(xs, 'SWNES'): a(HY - 8, x, '"%s"' % l, 'XEQ "PTXT"')
        a('LBL %02d' % lbl10, HY + HS + 1, 150, '"OVER HORIZON"', 'XEQ "PTXT"', 2, 150, '"UNDER HORIZON"', 'XEQ "PTXT"')
        return
    for c in (20, 51, 82, 113, 145, 176, 207, 238, 270, 301, 332, 363, 395):
        a(HY - 1, c, 'PIXEL', HY - 2, c, 'PIXEL')
    xs = [min(x + 3, 398 - width('W')) for x in (19, 112, 206, 300, 394)]
    a('RCL 44', 'X≠0?', 'GTO %02d' % lbl9)
    for x, l in zip(xs, 'NESWN'): g.txt(HY - 14, x, l)
    a('GTO %02d' % lbl10, 'LBL %02d' % lbl9)
    for x, l in zip(xs, 'SWNES'): g.txt(HY - 14, x, l)
    a('LBL %02d' % lbl10)


def hanim():
    g = Gen(); a = g.a
    HY, HS = 118, 100
    a('LBL "HANIM"', 'STO 12', 'R↓', 'STO 11', 'R↓', 'STO 10')
    a('24', 'STO 14', '0.5', 'STO 15')
    a('RCL 11', 'STO 91', 'RCL 12', 'STO 92', 'XEQ "HCZI"')
    a('0', 'STO 44', 'RCL 11', 'X<0?', 'XEQ 44')
    a('CLLCD', 'XEQ 72')
    a('0', '2', 'XEQ "HCZQ"', '0', 'STO 47', 'LBL 13', 'XEQ "HCZR"', 'XEQ 48', 'XEQ 14',
      '2', 'STO+ 47', '358', 'RCL 47', 'X≤Y?', 'GTO 13')
    a('0', 'STO 13')
    a('LBL 01', 'RCL 13', 'RCL× 15', '24', '÷', 'RCL+ 10', 'STO 17', 'XEQ 71')
    a('RCL 17', 'XEQ "SUNF"', 'XEQ "HCZ"', 'STO 27', 'XEQ 48', 'RCL 99', 'STO 20', 'RCL 98', 'STO 21')
    a('XEQ "MOOQ"', 'XEQ "HCZ"', 'XEQ 48', 'RCL 99', 'STO 22', 'RCL 98', 'STO 23')
    a('"NIGHT"', 'STO 43', '-12', 'RCL 27', 'X>Y?', 'XEQ 02', 'RCL 27', 'X>0?', 'XEQ 03')
    a('224', '0', 'CLLCDxy')
    tx = 2 + DTW + 8
    a(227, 2, 'RCL 17', 'XEQ "PDTS"', 227, tx, 'RCL 17', '0.5', '+', '1', 'MOD', '24', '×', 'XEQ "PHMS"', '" UT"', 'XEQ "PTXS"')
    a(227, 200, 'RCL 13', '1', '+', 'XEQ "PINS"', '"/"', 'XEQ "PTXS"', 'RCL 14', 'XEQ "PINS"')
    a(227, 398 - width('TWILIGHT'), 'RCL 43', 'XEQ "PTXS"')
    a('RCL 20', '6', '-', 'RCL 21', '6', '-', '"@"', 'XEQ "%s"' % SYM, 'RCL 22', '6', '-', 'RCL 23', '6', '-', '"("', 'XEQ "%s"' % SYM)
    a('PAUSE 10')
    a('1', 'STO+ 13', 'RCL 14', 'RCL 13', 'X<Y?', 'GTO 01')
    a('XEQ "WPLS"', 'RTN')
    a('LBL 44', '180', 'STO 44', 'RTN')
    a('LBL 02', '"TWILIGHT"', 'STO 43', 'RTN', 'LBL 03', '"DAY"', 'STO 43', 'RTN')
    a('LBL 71', 'RCL 17', '2451545', '-', 'STO 25', '0.000800925925925926', '+', '36525', '÷', 'STO 54',
      'RCL 25', '360.98564736629', '×', '280.46061837', '+', '360', 'MOD', 'STO 80', 'RTN')
    a('LBL 72')
    sky_chart(g, HY, 9, 10)
    a('RTN')
    a('LBL 14', 'RCL 99', 'RCL 98', 'PIXEL', 'RCL 99', 'RCL 98', '1', '+', 'PIXEL', 'RCL 99', '1', '+', 'RCL 98', 'PIXEL',
      'RCL 99', '1', '+', 'RCL 98', '1', '+', 'PIXEL', 'RTN')
    a('LBL 48', 'RCL 97', 'RCL+ 44', '360', 'MOD', '375', '×', '360', '÷', '20', '+', 'IP', 'STO 98',
      'RCL "SHC"', HS, '×', HY, '+', 'IP', 'STO 99', 'RTN')
    a('END')
    return 'HANIM', g.P


def allsky():
    g = Gen(); a = g.a
    HY, HS = 118, 100
    a('LBL "ALLSKY"', 'STO 12', 'R↓', 'STO 11', 'R↓', 'STO 10')
    a('RCL 11', 'STO 91', 'RCL 12', 'STO 92', 'XEQ "HCZI"', 'CLLCD')
    a('0', 'STO 44', 'RCL 11', 'X<0?', 'XEQ 44')
    sky_chart(g, HY, 9, 10)
    a('RCL 10', 'XEQ "SUNA"', 'STO 45', 'R↓', 'STO 46')
    tx = 2 + DTW + 8
    a(227, 2, 'RCL 10', 'XEQ "PDTS"', 227, tx, 'RCL 10', '0.5', '+', '1', 'MOD', '24', '×', 'XEQ "PHMS"', '" UT"', 'XEQ "PTXS"')
    a('0', '3', 'XEQ "HCZQ"', '0', 'STO 47', 'LBL 13', 'XEQ "HCZR"', 'XEQ 48', 'XEQ 14',
      '3', 'STO+ 47', '357', 'RCL 47', 'X≤Y?', 'GTO 13')
    # the stars: catalogue + first-order precession, the star symbol only (no number)
    a('RCL 10', '2451545', '-', '365.25', '÷', '3600', '÷', 'STO 26', '1.058', 'STO 42',
      'LBL 20', 'INDEX "ST"', 'RCL 42', 'IP', '1', 'STOIJ', 'RCLEL', 'STO 22', 'J+', 'RCLEL', 'STO 23',
      'RCL 22', 'COS', '20.0431', '×', 'RCL× 26', 'RCL+ 23',
      'RCL 22', 'SIN', 'RCL 23', 'TAN', '×', '20.0431', '×', '46.1244', '+', 'RCL× 26', 'RCL+ 22', 'RCL 80', 'X<>Y', '-', '360', 'MOD',
      'XEQ "HCZ"', 'XEQ 48', *(['XEQ 15'] if SMALL else ['63', 'STO 43', 'XEQ 16']), 'ISG 42', 'GTO 20')
    a('1.004', 'STO 42', 'LBL 21', 'RCL 42', 'IP', 'XEQ "PLN3"', 'XEQ "HCZ"', 'XEQ 48', 'RCL 42', 'IP', '70', '+', 'STO 43', 'XEQ 16', 'ISG 42', 'GTO 21')
    a('XEQ "MOO2"', 'XEQ "HCZ"', 'XEQ 48', '62', 'STO 43', 'XEQ 16')
    a('RCL 46', 'RCL 45', 'XEQ "HCZ"', 'STO 27', 'XEQ 48', '61', 'STO 43', 'XEQ 16')
    a('"NIGHT"', 'STO 43', '-12', 'RCL 27', 'X>Y?', 'XEQ 22', 'RCL 27', 'X>0?', 'XEQ 23', 227, 398 - width('TWILIGHT'), 'RCL 43', 'XEQ "PTXS"')
    a('XEQ "WPLS"', 'RTN')
    a('LBL 44', '180', 'STO 44', 'RTN')
    a('LBL 22', '"TWILIGHT"', 'STO 43', 'RTN', 'LBL 23', '"DAY"', 'STO 43', 'RTN')
    a('LBL 48', 'RCL 97', 'RCL+ 44', '360', 'MOD', '375', '×', '360', '÷', '20', '+', 'IP', 'STO 98',
      'RCL "SHC"', HS, '×', HY, '+', 'IP', 'STO 99', 'RTN')
    a('LBL 14', 'RCL 99', 'RCL 98', 'PIXEL', 'RCL 99', 'RCL 98', '1', '+', 'PIXEL', 'RCL 99', '1', '+', 'RCL 98', 'PIXEL',
      'RCL 99', '1', '+', 'RCL 98', '1', '+', 'PIXEL', 'RTN')
    if SMALL:                          # a star: small star and its number (small font), as NAVFULL
        a('LBL 15', 'RCL 99', '2', '-', 'RCL 98', '2', '-', '"*"', 'XEQ "PTXT"', 'RCL 98', '5', '+', 'STO 28', '388', 'RCL 28', 'X>Y?', 'XEQ 17',
          'RCL 99', '2', '-', 'RCL 28', 'RCL 42', 'IP', 'XEQ "PTNS"', 'RTN', 'LBL 17', '17', 'STO- 28', 'RTN')
    a('LBL 16', 'RCL 99', '6', '-', 'RCL 98', '6', '-', 'XEQ IND 43', 'XEQ "%s"' % SYM, 'RTN')
    for lab, t in ((61, '@'), (62, '('), (63, '*'), (71, '<'), (72, '>'), (73, '='), (74, '?')):
        a('LBL %d' % lab, '"%s"' % t, 'RTN')
    a('END')
    return 'ALLSKY', g.P


def main():
    global SMALL
    for small, sub, views in ((True, '', (lambda: almf(False), lambda: almf(True), halmv, horz, halmh, hanim, allsky)),
                              (False, 'big', (lambda: almf(False), halmv))):
        SMALL = small
        d = os.path.join(OUT, sub)
        os.makedirs(d, exist_ok=True)
        for f in views:
            name, P = f()
            open(os.path.join(d, name + '.txt'), 'w', encoding='utf-8').write('\n'.join(P) + '\n')
            print('%s %d lines' % (os.path.relpath(os.path.join(d, name + '.txt'), ROOT), len(P)))


if __name__ == '__main__':
    main()
