#!/usr/bin/env python3
"""navopt_engine.py - DEV: the ephemeris engine of NAVFULL rewritten for fewer steps, fewer registers
and fewer trigonometric functions (tools/build_navopt.py builds NAVFULL with it).

Two ideas, applied to SUNA, NUT, SUNF, STR2, MOO2, MOOQ, PLN2, PLN3 / PLNQ and the sight reduction:

  Horner   every polynomial is a chain c_n, RCL× T, c_n-1, +, ... (no powers, no repeated T), with
           the constant divisors folded into the coefficients (x / 3600 -> x × c), and the nutation
           loop (10 rows, 420 steps) becomes two matrix products, like the Moon series: NU × [D M M'
           F Ω 0 0 0 0] -> SIN / COS of the 10 arguments, DOT with NU × [0 0 0 0 0 1 T 0 0] (sine
           amplitudes S0 + S1 T, themselves Horner) and NU × [0 0 0 0 0 0 0 1 T].
  n-vector a direction is a unit vector, a rotation of the frame is a turn in one coordinate plane:
           →POL (the angle and length in that plane), add the rotation angle, →REC. →REC gives the
           sine and the cosine of an angle together. So ecliptic -> equator (SUNA, MOO2, PLN2, SUNF,
           MOOQ, PLNQ), the precession of the stars (three turns: ζ, θ, z), the star to the ecliptic
           and back, the heliocentric L B R -> x y z of the planets, the orbit -> ecliptic of the
           mean elements, and HCZ (equator -> horizon: one turn by the latitude) need no SIN / COS /
           TAN / ASIN formula pairs and no stored sines and cosines.
  HCZ      the body's n-vector in the frame of the observer's meridian, from Dec and LHA: (cos δ cos
           LHA, cos δ sin LHA, sin δ). The turn by the latitude φ in the meridian plane gives the up
           component U = sin Hc and the north component N; east E = -cos δ sin LHA. Hc = asin U,
           Zn = atan2(E, N) = -atan2(cos δ sin LHA, N). Two →REC, one →POL, one →REC, ASIN, →POL.

The results are the same numbers as NAVFULL to the last digits the C47 keeps (tests/test_navopt.py:
the routines, every view pixel for pixel, FULL and FAST series, with the tables). The matrices (INIT)
are the same. Only the dev build uses this module; programs/ is unchanged.
"""
from decimal import Decimal, getcontext

getcontext().prec = 34


def c(expr, digits=34):
    """A constant to digits significant digits (the C47 keeps 34): c('2451545 - 69.2/86400')."""
    a, _, b = expr.partition('/')
    if ' - ' in a:
        x, y = a.split(' - ')
        v = Decimal(x) - Decimal(y) / Decimal(b)
    else:
        v = Decimal(a) / Decimal(b) if b else Decimal(a)
    v = +v.quantize(Decimal(1).scaleb(v.adjusted() - digits + 1)) if digits < 34 else v
    s = format(v.normalize(), 'f') if abs(v) >= Decimal('1E-6') else format(v.normalize(), 'E')
    return s.replace('E+', 'E')


def cut(L, old, new):
    """Replace the exact block old (lines) by new in the program L; fail if it is not there once."""
    s = '\n' + '\n'.join(L) + '\n'
    o = '\n' + '\n'.join(old) + '\n'
    assert s.count(o) == 1, 'navopt: block not found once: %r' % old[:6]
    return s.replace(o, '\n' + '\n'.join(new) + '\n' if new else '\n').strip('\n').split('\n')


def routine(L, name, end):
    """The lines of routine LBL "name" up to (not including) the line end."""
    i = L.index('LBL "%s"' % name)
    j = L.index(end, i + 1)
    return L[i:j]


# ---------------------------------------------------------------- the sight reduction (CHZ)
HCZ = ['LBL "HCZ"',                         # Y Dec, X GHA
       'RCL+ 92', 'X<>Y', '1', '→REC',        # Y sin δ, X cos δ, Z LHA
       'X<>Y', 'STO 98', 'R↓', '→REC',        # Y y = cos δ sin LHA, X x = cos δ cos LHA
       'RCL 98', 'X<>Y', '→POL',              # the meridian plane (x, z): Y angle, X length; Z y
       'X<>Y', 'RCL- 91', 'X<>Y', '→REC',     # turned by -φ: Y N, X U = sin Hc
       'STO "SHC"', 'ASIN', 'STO 96',
       'R↓', '→POL', 'X<>Y', 'CHS', '360', 'MOD', 'STO 97',      # Zn = -atan2(y, N)
       'RCL 96', 'RTN']
HCZ0 = ['LBL "HCZ0"',                       # Dec 0 (the celestial equator)
        'RCL+ 92', '1', '→REC', 'ENTER', 'RCL× "HZC"',
        'STO "SHC"', 'ASIN', 'STO 96',
        'R↓', 'RCL× "HZS"', 'CHS', '→POL', 'X<>Y', 'CHS', '360', 'MOD', 'STO 97',
        'RCL 96', 'RTN']
HCZQ = ['LBL "HCZQ"',
        '1', '→REC', 'STO "EQCH"', 'X<>Y', 'STO "EQSH"', 'R↓', 'R↓',
        'RCL+ 92', '1', '→REC', 'STO "EQC"', 'X<>Y', 'STO "EQS"', 'RTN']
HCZI = ['LBL "HCZI"', 'RCL 91', '1', '→REC', 'STO "HZC"', 'X<>Y', 'STO "HZS"', 'X<>Y', 'RTN']
DHA = ['LBL "DHA"', 'R↓', 'R↓', 'STO 92', 'R↓', 'STO 91', 'R↓', 'STO 97', 'R↓', 'STO 96',
       '1', '→REC', 'RCL 97', 'X<>Y', '→REC',          # Y E, X N, Z U = sin Hc
       'X<>Y', 'CHS', 'STO 95', 'R↓', 'X<>Y', '→POL',   # R95 y = -E; (N, U): Y angle, X length
       'X<>Y', 'RCL+ 91', 'X<>Y', '→REC',               # turned back by φ: Y z = sin δ, X x
       'RCL 95', 'X<>Y', '→POL', 'X<>Y', '360', 'MOD', 'STO 95',
       'R↓', '→POL', 'X<>Y', 'STO 94',
       'RCL 95', 'RCL- 92', '360', 'MOD', 'RCL 95', 'RCL 94', 'END']


def chz(L):
    L = cut(L, routine(L, 'HCZ', 'LBL "HCZ0"'), HCZ)
    L = cut(L, routine(L, 'HCZ0', 'LBL "HCZQ"'), HCZ0)
    L = cut(L, routine(L, 'HCZQ', 'LBL "HCZR"'), HCZQ)
    L = cut(L, ['RCL "EQS"', 'CHS', 'RCL "HZS"', 'RCL× "EQC"', 'CHS', '→POL', 'X<>Y', '360', '+', '360', 'MOD', 'STO 97'],
            ['RCL "EQS"', 'RCL "HZS"', 'RCL× "EQC"', 'CHS', '→POL', 'X<>Y', 'CHS', '360', 'MOD', 'STO 97'])
    L = cut(L, routine(L, 'HCZI', 'LBL "DHA"'), HCZI)
    i = L.index('LBL "DHA"')
    assert L[-1] == 'END'
    return L[:i] + DHA


def blk(s):
    """Lines from 'a|b|c' (the blocks below are written as in programs/, one step per |)."""
    return s.split('|')


# ---------------------------------------------------------------- the Sun (SUNA, NUT, SUNF)
SUNA_OLD = blk('LBL "SUNA"|DEG|STO 70|69.2|86400|÷|+|2451545|-|36525|÷|STO 54|10|÷|STO 50|RAD|CF 12|INDEX "VL"|1|4|STOIJ|RCLEL|X≠0?|XEQ 14|XEQ "SERT"|RCL "VL"|XEQ "SER"|STO 71|RCL "VB"|XEQ "SER"|STO 72|RCL "VR"|XEQ "SER"|STO 73|DEG|RCL 71|57.295779513082320876798154814105|×|180|+|360|MOD|STO 74|RCL 72|57.295779513082320876798154814105|×|CHS|STO 75|RCL 74|RCL 54|1.397|×|-|COS|LASTX|SIN|-|0.03916|×|3600|÷|STO+ 75|0.09033|3600|÷|STO- 74|XEQ "NUT"|RCL 66|3600|÷|STO+ 74|20.4898|RCL÷ 73|3600|÷|STO- 74|84381.448|RCL 54|46.815|×|-|RCL+ 67|3600|÷|STO 76|RCL 75|SIN|RCL 76|COS|×|RCL 75|COS|RCL 76|SIN|×|RCL 74|SIN|×|+|ASIN|STO 77|RCL 74|SIN|RCL 76|COS|×|RCL 75|TAN|RCL 76|SIN|×|-|RCL 74|COS|→POL|X<>Y|STO 78|RCL 70|2451545|-|STO 79|360.98564736629|×|280.46061837|+|RCL 79|36525|÷|X↑2|0.000387933|×|+|RCL 66|3600|÷|RCL 76|COS|×|+|360|MOD|STO 80|RCL- 78|360|MOD|STO 81|XEQ 15')
SUNA_NEW = ['LBL "SUNA"', 'DEG', 'STO 70', c('2451545 - 69.2/86400'), '-', '36525', '÷', 'STO 54', '10', '÷', 'STO 50',
            'RAD', 'CF 12', 'INDEX "VL"', '1', '4', 'STOIJ', 'RCLEL', 'X≠0?', 'XEQ 14',
            'XEQ "SERT"', 'RCL "VL"', 'XEQ "SER"', '57.295779513082320876798154814105', '×', '180', '+', '360', 'MOD', 'STO 74',
            'RCL "VB"', 'XEQ "SER"', '-57.295779513082320876798154814105', '×', 'STO 75',
            'RCL "VR"', 'XEQ "SER"', 'STO 73', 'DEG',
            # FK5: a = λ - 1.397 T; →REC gives sin a and cos a together
            'RCL 74', '1.397', 'RCL× 54', '-', '1', '→REC', 'X<>Y', '-', '0.03916', '×', '3600', '÷', 'STO+ 75',
            '0.09033', '3600', '÷', 'STO- 74',
            'XEQ "NUT"', 'RCL 66', '20.4898', 'RCL÷ 73', '-', '3600', '÷', 'STO+ 74',      # nutation - aberration
            # mean obliquity ε0 (Horner) for the stars, true obliquity ε = ε0 + Δε
            '-46.815', 'RCL× 54', '84381.448', '+', 'STO 76', '3600', '÷', 'STO "SE0"', 'RCL 67', 'RCL+ 76', '3600', '÷', 'STO 76',
            # ecliptic (λ, β) -> equator: the n-vector turned by ε about the x axis
            'RCL 75', '1', '→REC', 'RCL 74', 'X<>Y', '→REC', 'STO 78', 'R↓', '→POL', 'X<>Y', 'RCL+ 76', 'X<>Y', '→REC',
            'RCL 78', '→POL', 'X<>Y', 'STO 78', 'R↓', '→POL', 'X<>Y', 'STO 77',
            # GMST (Horner in d = JD - 2451545) + equation of the equinoxes
            'RCL 70', '2451545', '-', 'ENTER', 'ENTER', c('0.000387933/1334075625', 16), '×', '360.98564736629', '+', '×',
            '280.46061837', '+', 'RCL 66', '3600', '÷', 'RCL 76', 'COS', '×', '+', '360', 'MOD', 'STO 80',
            'RCL- 78', '360', 'MOD', 'STO 81', 'XEQ 15']
L15_OLD = blk('LBL 15|RCL 54|0.01801828|×|0.2988499|+|RCL× 54|2306.083227|+|RCL× 54|2.650545|+|3600|÷|STO "SZE"|RCL 54|0.01826837|×|1.0927348|+|RCL× 54|2306.077181|+|RCL× 54|-2.650545|+|3600|÷|STO "SZZ"|RCL 54|-0.04182264|×|-0.4294934|+|RCL× 54|2004.191903|+|RCL× 54|3600|÷|STO 93|SIN|STO "SSTH"|RCL 93|COS|STO "SCTH"|RCL 76|RCL 67|3600|÷|-|STO 93|SIN|STO "SSE0"|RCL 93|COS|STO "SCE0"|RCL 76|SIN|STO "SSEP"|RCL 76|COS|STO "SCEP"|RCL 54|-0.000042037|×|0.016708634|+|STO "SEK"|RCL 54|1.71946|×|102.93735|+|STO "SPI"|-1|STO "PQK"|RTN')
L15_NEW = ['LBL 15',                    # precession angles ζ z θ (Horner); the stars turn by them, no sines kept
           '0.01801828', 'RCL× 54', '0.2988499', '+', 'RCL× 54', '2306.083227', '+', 'RCL× 54', '2.650545', '+', '3600', '÷', 'STO "SZE"',
           '0.01826837', 'RCL× 54', '1.0927348', '+', 'RCL× 54', '2306.077181', '+', 'RCL× 54', '-2.650545', '+', '3600', '÷', 'STO "SZZ"',
           '-0.04182264', 'RCL× 54', '-0.4294934', '+', 'RCL× 54', '2004.191903', '+', 'RCL× 54', '3600', '÷', 'STO "STH"',
           '-0.000042037', 'RCL× 54', '0.016708634', '+', 'STO "SEK"', '1.71946', 'RCL× 54', '102.93735', '+', 'STO "SPI"',
           '-1', 'STO "PQK"', 'RTN']
NUT_OLD = blk('LBL "NUT"|RCL 54|445267.11148|×|297.85036|+|STO 60|RCL 54|35999.05034|×|357.52772|+|STO 61|RCL 54|477198.867398|×|134.96298|+|STO 62|RCL 54|483202.017538|×|93.27191|+|STO 63|RCL 54|1934.136261|×|CHS|125.04452|+|STO 64|0|STO 66|STO 67|10|STO 55|INDEX "NU"|1|1|STOIJ|LBL 13|RCLEL|J+|RCL× 60|RCLEL|J+|RCL× 61|+|RCLEL|J+|RCL× 62|+|RCLEL|J+|RCL× 63|+|RCLEL|J+|RCL× 64|+|STO 65|RCLEL|J+|RCLEL|J+|RCL× 54|+|RCL 65|SIN|×|STO+ 66|RCLEL|J+|RCLEL|J+|RCL× 54|+|RCL 65|COS|×|STO+ 67|DSE 55|GTO 13|RCL 66|1E-4|×|STO 66|RCL 67|1E-4|×|STO 67')
NUT_NEW = ['LBL "NUT"',                 # NU (10 x 9): d m m' f Ω, S0 S1 C0 C1 per row
           '9', 'ENTER', '1', 'NEWMAT', 'STO "NV"', 'STO "NW"', 'INDEX "NV"',
           '445267.11148', 'RCL× 54', '297.85036', '+', 'STO 60', 'STOEL', 'J+',
           '35999.05034', 'RCL× 54', '357.52772', '+', 'STO 61', 'STOEL', 'J+',
           '477198.867398', 'RCL× 54', '134.96298', '+', 'STO 62', 'STOEL', 'J+',
           '483202.017538', 'RCL× 54', '93.27191', '+', 'STO 63', 'STOEL', 'J+',
           '-1934.136261', 'RCL× 54', '125.04452', '+', 'STOEL',
           'INDEX "NW"', '6', '1', 'STOIJ', '1', 'STOEL', 'J+', 'RCL 54', 'STOEL',          # [0 0 0 0 0 1 T 0 0]
           'RCL "NU"', 'RCL "NV"', '×', 'STO "NV"', 'SIN',                                  # the 10 arguments
           'RCL "NU"', 'RCL "NW"', '×', 'DOT', '1E-4', '×', 'STO 66',                       # Σ (S0 + S1 T) sin
           'INDEX "NW"', '6', '1', 'STOIJ', '0', 'STOEL', 'J+', '0', 'STOEL', 'J+', '1', 'STOEL', 'J+', 'RCL 54', 'STOEL',
           'RCL "NV"', 'COS', 'RCL "NU"', 'RCL "NW"', '×', 'DOT', '1E-4', '×', 'STO 67']      # Σ (C0 + C1 T) cos
SUNF_OLD = blk('STO 53|RCL 51|-0.0000004|×|23.439|+|STO 52|SIN|RCL 53|SIN|×|ASIN|RCL 52|COS|RCL 53|SIN|×|RCL 53|COS|→POL|R↓')
SUNF_NEW = ['1', '→REC', 'X<>Y', '-0.0000004', 'RCL× 51', '23.439', '+', 'X<>Y', '→REC',     # (sin λ) turned by ε
            'X<>Y', 'STO 52', 'R↓', 'X<>Y', '→POL', 'X<>Y', 'RCL 52', 'ASIN', 'X<>Y']


def suna(L):
    L = cut(L, SUNA_OLD, SUNA_NEW)
    L = cut(L, L15_OLD, L15_NEW)
    L = cut(L, NUT_OLD, NUT_NEW)
    return cut(L, SUNF_OLD, SUNF_NEW)


# ---------------------------------------------------------------- the stars (STR2)
STR2_OLD_END = 'LBL "SQK"'
STR2_NEW = ['LBL "STR2"', 'DEG', 'INDEX "ST"', 'RCL 82', '1', 'STOIJ',
            'RCLEL', 'J+', 'STO 83', 'RCLEL', 'J+', 'STO 84',                      # RA, Dec (J2000)
            'RCLEL', 'J+', 'RCL× 54', '36000', '÷', 'RCL 84', 'COS', '÷', 'STO+ 83',  # proper motion (mas / year; 100 T years)
            'RCLEL', 'RCL× 54', '36000', '÷', 'STO+ 84',
            # the n-vector, turned by ζ (about z), θ (about y), z (about z): precession
            'RCL 84', '1', '→REC', 'X<>Y', 'STO 84', 'R↓',
            'RCL 83', 'RCL+ "SZE"', 'X<>Y', '→REC', 'X<>Y', 'STO 83', 'R↓',
            'RCL 84', 'X<>Y', '→POL', 'X<>Y', 'RCL+ "STH"', 'X<>Y', '→REC', 'X<>Y', 'STO 84', 'R↓',
            'RCL 83', 'X<>Y', '→POL', 'X<>Y', 'RCL+ "SZZ"', 'X<>Y', '→REC',
            # to the ecliptic of date: turned by -ε0 about x; λ, sin β, cos β
            'STO 85', 'R↓', 'RCL 84', 'X<>Y', '→POL', 'X<>Y', 'RCL- "SE0"', 'X<>Y', '→REC',
            'RCL 85', '→POL', 'X<>Y', 'STO 83', 'R↓', 'STO 86', 'X<>Y', 'STO 85', 'ASIN', 'STO 84',
            # annual aberration (e, perihelion: SEK, SPI) and nutation in longitude
            'RCL "SPI"', 'RCL- 83', 'RCL "SEK"', '→REC', 'RCL 74', 'RCL- 83', '1', '→REC',
            'X<>Y', 'STO 87', 'R↓', '-', 'RCL÷ 86', '20.49552', '×', 'RCL+ 66', '3600', '÷', 'STO+ 83',
            'R↓', 'RCL- 87', 'RCL× 85', '0.0056932', '×', 'STO+ 84',
            # back to the equator: turned by ε (true obliquity); SHA, Dec, GHA
            'RCL 84', '1', '→REC', 'RCL 83', 'X<>Y', '→REC', 'STO 85', 'R↓', '→POL', 'X<>Y', 'RCL+ 76', 'X<>Y', '→REC',
            'RCL 85', '→POL', 'X<>Y', 'CHS', '360', 'MOD', 'STO 89', 'R↓', '→POL', 'X<>Y',
            'RCL 89', 'X<>Y', 'RCL 89', 'RCL+ 80', '360', 'MOD', 'RTN']


def star(L):
    return cut(L, routine(L, 'STR2', STR2_OLD_END), STR2_NEW)


# ---------------------------------------------------------------- the Moon (MOO2, MOOQ)
MOO2_OLD = blk('RCL 39|SIN|RCL 76|COS|×|RCL 39|COS|RCL 76|SIN|×|RCL 38|SIN|×|+|ASIN|STO 08|RCL 38|SIN|RCL 76|COS|×|RCL 39|TAN|RCL 76|SIN|×|-|RCL 38|COS|→POL|X<>Y|RCL 80|X<>Y|-|360|+|360|MOD|STO 06|6378.14|RCL÷ 07|ASIN|60|×|STO 05|358473400|RCL÷ 07|60|÷|STO 04|RCL 04|RCL 05')
MOO2_NEW = ['RCL 39', '1', '→REC', 'RCL 38', 'X<>Y', '→REC', 'STO 06', 'R↓', '→POL', 'X<>Y', 'RCL+ 76', 'X<>Y', '→REC',
            'RCL 06', '→POL', 'X<>Y', 'RCL 80', 'X<>Y', '-', '360', 'MOD', 'STO 06', 'R↓', '→POL', 'X<>Y', 'STO 08',
            '6378.14', 'RCL÷ 07', 'ASIN', '60', '×', 'STO 05', '358473400', 'RCL÷ 07', '60', '÷', 'STO 04', 'RCL 05']
MOOQ_OLD = blk('STO 52|SIN|23.4393|COS|×|RCL 52|COS|23.4393|SIN|×|RCL 51|SIN|×|+|ASIN|STO 53|RCL 51|SIN|23.4393|COS|×|RCL 52|TAN|23.4393|SIN|×|-|RCL 51|COS|→POL|X<>Y|RCL 80|X<>Y|-|360|MOD|RCL 53|X<>Y|RTN')
MOOQ_NEW = ['1', '→REC', 'RCL 51', 'X<>Y', '→REC', 'STO 52', 'R↓', '→POL', 'X<>Y', '23.4393', '+', 'X<>Y', '→REC',
            'RCL 52', '→POL', 'X<>Y', 'RCL 80', 'X<>Y', '-', '360', 'MOD', 'STO 52', 'R↓', '→POL', 'X<>Y', 'RCL 52', 'RTN']


def moon(L):
    return cut(cut(L, MOO2_OLD, MOO2_NEW), MOOQ_OLD, MOOQ_NEW)


# ---------------------------------------------------------------- the planets (PLN2, PLN3, PLNQ)
EARTH_OLD = blk('RCL "EEL"|XEQ "SER"|STO 00|RCL "EEB"|XEQ "SER"|STO 01|RCL "EER"|XEQ "SER"|STO 02')
EARTH_NEW = ['RCL "EEL"', 'XEQ "SER"', 'STO 00', 'RCL "EEB"', 'XEQ "SER"', 'RCL "EER"', 'XEQ "SER"',       # L B R
             '→REC', 'RCL 00', 'X<>Y', '→REC', 'STO 00', 'R↓', 'STO 01', 'R↓', 'STO 02']               # -> x y z
PASS_OLD = blk('XEQ IND 39|RCL 06|RCL 05|COS|×|RCL 04|COS|×|RCL 02|RCL 01|COS|×|RCL 00|COS|×|-|STO 35|RCL 06|RCL 05|COS|×|RCL 04|SIN|×|RCL 02|RCL 01|COS|×|RCL 00|SIN|×|-|STO 36|RCL 06|RCL 05|SIN|×|RCL 02|RCL 01|SIN|×|-|STO 37|RCL 35|X↑2|RCL 36|X↑2|+|RCL 37|X↑2|+|0.5|Y↑X|STO 34|0.0057755183|×|STO 08|DSE 07|GTO 30|DEG|RCL 36|RCL 35|→POL|STO 38|X<>Y|360|+|360|MOD|STO 39|RCL 37|RCL 38|→POL|X<>Y|STO 38')
PASS_NEW = ['XEQ IND 39', 'RCL 05', 'RCL 06', '→REC', 'RCL 04', 'X<>Y', '→REC',                   # planet x y z
            'RCL- 00', 'STO 35', 'R↓', 'RCL- 01', 'STO 36', 'R↓', 'RCL- 02', 'STO 37',             # minus the Earth
            'RCL 36', 'RCL 35', '→POL', 'RCL 37', 'X<>Y', '→POL', 'STO 34', '0.0057755183', '×', 'STO 08',
            'DSE 07', 'GTO 30', 'DEG',
            'RCL 36', 'RCL 35', '→POL', 'X<>Y', '360', 'MOD', 'STO 39', 'R↓', 'RCL 37', 'X<>Y', '→POL', 'X<>Y', 'STO 38']
TAIL_OLD = blk('RCL 39|RCL 54|1.397|×|-|STO 35|COS|RCL 35|SIN|+|RCL 38|TAN|×|0.03916|×|0.09033|-|3600|÷|STO+ 39|RCL 35|COS|RCL 35|SIN|-|0.03916|×|3600|÷|STO+ 38|RCL 00|57.29577951308232|×|180|+|STO 35|RCL 54|-0.000042037|×|0.016708634|+|STO 36|RCL 54|1.71946|×|102.93735|+|STO 37|RCL 35|RCL- 39|COS|-20.49552|×|RCL 37|RCL- 39|COS|RCL× 36|20.49552|×|+|RCL 38|COS|÷|RCL+ 66|3600|÷|STO+ 39|RCL 35|RCL- 39|SIN|RCL 37|RCL- 39|SIN|RCL× 36|-|RCL 38|SIN|×|-20.49552|×|3600|÷|STO+ 38|RCL 38|SIN|RCL 76|COS|×|RCL 38|COS|RCL 76|SIN|×|RCL 39|SIN|×|+|ASIN|STO 06|RCL 39|SIN|RCL 76|COS|×|RCL 38|TAN|RCL 76|SIN|×|-|RCL 39|COS|→POL|X<>Y|360|+|360|MOD|STO 05|RCL 80|RCL- 05|360|+|360|MOD|STO 04|360|RCL- 05|360|MOD|STO 05|8.794|RCL÷ 34|60|÷|STO 07|RCL 07|RCL 05')
TAIL_NEW = [# FK5: a = λ - 1.397 T, sin a and cos a from →REC
            'RCL 39', '1.397', 'RCL× 54', '-', '1', '→REC', 'STO 35', 'X<>Y', 'STO- 35', '+', 'RCL 38', 'TAN', '×',
            '0.03916', '×', '0.09033', '-', '3600', '÷', 'STO+ 39', 'RCL 35', '0.03916', '×', '3600', '÷', 'STO+ 38',
            # aberration: the Sun's longitude from the Earth's x y, e and perihelion from SUNA (SEK, SPI)
            'RCL 38', '1', '→REC', 'STO 37', 'X<>Y', 'STO 36', 'RCL 01', 'RCL 00', '→POL', 'X<>Y', '180', '+', 'STO 35',
            'RCL "SPI"', 'RCL- 39', 'RCL "SEK"', '→REC', 'RCL 35', 'RCL- 39', '1', '→REC',
            'X<>Y', 'R↓', '-', 'RCL÷ 37', '20.49552', '×', 'RCL+ 66', '3600', '÷', 'STO+ 39',
            # in latitude with the corrected longitude (as PLN2 of the release)
            'RCL "SPI"', 'RCL- 39', 'RCL "SEK"', '→REC', 'RCL 35', 'RCL- 39', '1', '→REC',
            'R↓', 'STO 35', 'R↓', 'R↓', 'RCL- 35', 'RCL× 36', '0.0056932', '×', 'STO+ 38',
            # ecliptic -> equator: the n-vector turned by ε
            'RCL 38', '1', '→REC', 'RCL 39', 'X<>Y', '→REC', 'STO 35', 'R↓', '→POL', 'X<>Y', 'RCL+ 76', 'X<>Y', '→REC',
            'RCL 35', '→POL', 'X<>Y', '360', 'MOD', 'STO 05', 'R↓', '→POL', 'X<>Y', 'STO 06',
            'RCL 80', 'RCL- 05', '360', 'MOD', 'STO 04', '360', 'RCL- 05', '360', 'MOD', 'STO 05',
            '8.794', 'RCL÷ 34', '60', '÷', 'STO 07', 'RCL 05']
L50_OLD_END = 'LBL 60'
L50_NEW = ['LBL 50', '60', '+', 'STO 52', 'XEQ IND 52', 'RCL 33', 'RCL- 51', 'STO 52',          # M = L - ϖ
           'RCL 31', '57.29577951308232', '×', 'STO 69', 'RCL 52',                              # Kepler: E = M + e° sin E
           'SIN', 'RCL× 69', 'RCL+ 52', 'SIN', 'RCL× 69', 'RCL+ 52', 'SIN', 'RCL× 69', 'RCL+ 52', 'SIN', 'RCL× 69', 'RCL+ 52',
           'RCL 30', '→REC', 'RCL 30', 'RCL× 31', '-', 'X<>Y', '1', 'RCL 31', 'X↑2', '-', 'SQRT', '×',   # in the orbit
           'X<>Y', '→POL', 'X<>Y', 'RCL+ 51', 'RCL- 53', 'X<>Y', '→REC',                        # r, argument of latitude u
           'X<>Y', 'RCL 32', 'X<>Y', '→REC', 'X<>Y', 'STO 30', 'R↓',                             # turned by I about x
           'X<>Y', '→POL', 'X<>Y', 'RCL+ 53', 'X<>Y', '→REC', 'STO 31', 'X<>Y', 'STO 33', 'RTN']   # by Ω about z
L49_OLD = blk('RCL "PQX"|STO 56|RCL "PQY"|STO 57|RCL "PQZ"|STO 58|RCL 59|XEQ 50|RCL 31|RCL- 56|STO 31|RCL 33|RCL- 57|STO 33|RCL 30|RCL- 58|STO 30|RCL 31|X↑2|RCL 33|X↑2|+|RCL 30|X↑2|+|0.5|Y↑X|STO 58|RCL 33|RCL 31|→POL|STO 56|X<>Y|RCL 54|1.3969713|×|+|STO 57|RCL 30|RCL 56|→POL|X<>Y|STO 56|RCL 56|SIN|23.4393|COS|×|RCL 56|COS|23.4393|SIN|×|RCL 57|SIN|×|+|ASIN|STO 52|RCL 57|SIN|23.4393|COS|×|RCL 56|TAN|23.4393|SIN|×|-|RCL 57|COS|→POL|X<>Y|RCL 80|X<>Y|-|360|MOD|STO 53|RTN')
L49_NEW = ['RCL 59', 'XEQ 50', 'RCL 33', 'RCL- "PQY"', 'RCL 31', 'RCL- "PQX"', '→POL',              # geocentric x y
           'X<>Y', '1.3969713', 'RCL× 54', '+', 'X<>Y', '→REC', 'STO 56', 'R↓',                    # precession in longitude
           'RCL 30', 'RCL- "PQZ"', 'X<>Y', '→POL', 'X<>Y', '23.4393', '+', 'X<>Y', '→REC',         # turned by ε
           'RCL 56', '→POL', 'X<>Y', 'RCL 80', 'X<>Y', '-', '360', 'MOD', 'STO 53',
           'R↓', '→POL', 'STO 58', 'X<>Y', 'STO 52', 'RTN']                                       # Dec, distance


def plan(L):
    L = cut(L, EARTH_OLD, EARTH_NEW)
    L = cut(L, PASS_OLD, PASS_NEW)
    L = cut(L, TAIL_OLD, TAIL_NEW)
    i = L.index('LBL 50')
    L = L[:i] + L50_NEW + L[L.index(L50_OLD_END, i):]
    L = cut(L, ['0', 'RCL× 54', '0', '+', 'STO 53'], ['0', 'STO 53'])          # Ω of the Earth-Moon barycentre
    return cut(L, L49_OLD, L49_NEW)


# the CACHE: what SUNA leaves for the stars computed later (CSQK): θ and ε0 instead of the four sines
SUNREGS = ['73', '77', '80', '81', '54', '66', '74', '"STH"', '"SPI"', '"SE0"', '"SZE"', '"SZZ"']


OPT = {'CHZ': chz, 'SUNA': suna, 'STAR': star, 'MOON': moon, 'PLAN': plan}


def programs(read):
    """{name: optimized lines} for the programs this module changes; read(name) gives the original."""
    return {n: f(read(n)) for n, f in OPT.items()}
