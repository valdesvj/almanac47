#!/usr/bin/env python3
"""Write tools/tests_calc/TSTAR.txt: a C47 timing test of the 58 stars, one by one against one matrix (branch struct-opt).

A  the stars as NAV computes them before the menu (CSQK): SQK (quick sin Hc, 3 trig) for every star; for the
   stars that can be over the horizon STR2 (proper motion, precession, nutation, aberration: about 19 →REC / →POL)
   and Hc Zn from the star's vector (CSUN LBL 99, 2 →POL).
B  all 58 stars at once with the firmware's matrix functions: the star vectors at J2000 and J2050 (set up once),
   the vectors for T by one M × r and M + M, then one 4 x 3 matrix C4 per time (rows 1-3 the transpose of
   Rx(-eps) Rz(-dpsi) Rx(eps0) Rz(-z) Ry(theta) Rz(-zeta), row 4 the aberration vector in the same frame) and two
   products (58 x 4) x (4 x 3): one with Rz(GHA Aries) for GHA / Dec, one with the observer's north / east / zenith
   for Hc / Zn. The angles: atan2 of a complex column (∡), ABS for the length; M.GETM takes the columns out.
   Proper motion is a straight line between J2000 and J2050 (within 0.0006' of STR2 for 2000-2050, Python check
   in the branch); the aberration is added as a vector (second order: 0.00003').

The test sets NAV's constants (R43-R98, ALMC, the cache keys), a place and a time, runs HCZI and CSUN (the whole
sky, as NAV does before the menu), then times N passes of A and of B (N = X when X > 0, else 3), and compares
the 58 results of A (all stars computed) and B. Results (ticks are 1/10 s):

  R21  ticks of A, N passes          R22  ticks of B, N passes          R23  ticks of B's setup (once)
  R26  largest difference A - B: GHA, arcmin      R27  Dec      R28  Hc      R29  Zn
  R30  how many stars A computed in full (passed SQK's horizon test) in one pass

Load NAVFULL (any build of branch struct-opt or the release: they share the registers), run NAVINIT, then load
TSTAR. It changes NAV's registers R00-R98 (NAV puts them back only when NAV itself ends): save yours first.
The variables it makes start with T and are deleted at the end.
"""
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
NAV = os.path.join(ROOT, 'build', 'NAVFULL.txt')
PLACE = (55.2, 25.3)                  # longitude E, latitude N (R13, R14)
JD = 2461318.3                        # 2026-10-04 19:12 UT


def nav_setup():
    """NAV's constants and cache set-up, copied from the release (after the register save, before the menu)."""
    L = [l for l in open(NAV, encoding='utf-8').read().split('\n')]
    a = L.index('LBL "NAV"')
    i = L.index('STO R.98', a) + 1
    out = []
    while L[i] != 'XEQ 20':
        out.append(L[i])
        i += 1
    assert 'SSIZE8' in out and 'STO "ALMC"' in out
    return out


def hcz_vec():
    """CSUN's LBL 99 (Hc, Zn from the star's vector F4 F5 F6 -> R09, R05), copied from the release."""
    L = [l for l in open(NAV, encoding='utf-8').read().split('\n')]
    a = L.index('LBL "N64"')
    s = L.index('LBL 99', a)
    j = s
    while L[j] != 'RTN':
        j += 1
    return L[s:j + 1]


def rot(lbl, rows):
    """A 3 x 3 rotation matrix from the angle in X: c, s from →REC, then the nine elements row by row."""
    code = ['LBL %d' % lbl, '1', '→REC', 'STO "TCC"', 'X<>Y', 'STO "TSS"',
            '3', 'ENTER', 'NEWMAT', 'STO "TR"', 'INDEX "TR"', '1', 'ENTER', 'STOIJ']
    val = {'c': ['RCL "TCC"'], 's': ['RCL "TSS"'], '-s': ['RCL "TSS"', 'CHS'], '0': ['0'], '1': ['1']}
    for e in rows:
        code += val[e] + ['STOSEQ']
    return code + ['RCL "TR"', 'RTN']


def column(i, j, name):
    """Column j of the indexed matrix (58 rows) into the variable name."""
    return ['1', 'ENTER', str(j), 'STOIJ', '58', 'ENTER', '1', 'M.GETM', 'STO "%s"' % name]


def program():
    P = ['LBL "TSTAR"', 'REM "58 stars: A one by one (SQK STR2), B one matrix. X = passes (3). Ticks R21 R22 R23,"',
         'REM "differences arcmin R26 GHA R27 Dec R28 Hc R29 Zn, R30 stars of A in full. Load NAVFULL, run NAVINIT."',
         'X>0?', 'GTO 01', '3', 'LBL 01', 'STO "TN"', 'DEG']
    P += nav_setup()
    P += ['%g' % PLACE[0], 'STO 13', '%g' % PLACE[1], 'STO 14', repr(JD), 'STO 17',
          'XEQ "N36"', 'RCL 17', 'XEQ "N64"']
    # B's set-up, once: the star vectors at J2000 and J2050 -> TSA0, and per century TSD (column 4: 1 and 0)
    P += ['REM "B set-up: star vectors J2000, J2050"', 'TICKS', 'STO "TT0"', 'XEQ 10',
          'TICKS', 'RCL- "TT0"', 'STO "TR3"']
    # A, N passes
    P += ['REM "A: N passes, one star at a time"', '0', 'STO "TW"', 'RCL "TN"', 'STO "TC"', 'TICKS', 'STO "TT0"',
          'LBL 02', 'XEQ 50', '1', 'STO- "TC"', 'RCL "TC"', 'X>0?', 'GTO 02',
          'TICKS', 'RCL- "TT0"', 'STO "TR1"', 'RCL "TF"', 'STO "TF1"']
    # B, N passes
    P += ['REM "B: N passes, all stars at once"', 'RCL "TN"', 'STO "TC"', 'TICKS', 'STO "TT0"',
          'LBL 03', 'XEQ 20', '1', 'STO- "TC"', 'RCL "TC"', 'X>0?', 'GTO 03',
          'TICKS', 'RCL- "TT0"', 'STO "TR2"']
    # the check: A for every star into TRA, B into TRB, the largest difference of each column
    P += ['REM "check: A for all 58 stars against B"', '58', 'ENTER', '4', 'NEWMAT', 'STO "TRA"', 'STO "TRB"',
          '1', 'STO "TW"', 'XEQ 50', 'INDEX "TRB"']
    for j, name in enumerate(('TB1', 'TB2', 'TB3', 'TB4'), 1):
        P += ['1', 'ENTER', str(j), 'STOIJ', 'RCL "%s"' % name, 'M.PUTM']
    P += ['RCL "TRA"', 'RCL "TRB"', '-', 'SIN', 'STO "TE"', 'INDEX "TE"']
    for j, reg in ((1, 26), (2, 27), (3, 28), (4, 29)):
        P += column(1, j, 'TX1') + ['RCL "TX1"', 'RNORM', 'ASIN', '60', '×', 'STO "TD%d"' % j]
    # results to R21-R30, the T variables deleted
    P += ['RCL "TR1"', 'STO 21', 'RCL "TR2"', 'STO 22', 'RCL "TR3"', 'STO 23',
          'RCL "TD1"', 'STO 26', 'RCL "TD2"', 'STO 27', 'RCL "TD3"', 'STO 28', 'RCL "TD4"', 'STO 29',
          'RCL "TF1"', 'STO 30']
    for v in ('TF1', 'TN', 'TT0', 'TR1', 'TR2', 'TR3', 'TW', 'TC', 'TK', 'TF', 'TGA', 'TDE', 'TCC', 'TSS', 'TR', 'TSA0',
              'TS50', 'TSD', 'TSA', 'TQ', 'TMT', 'TV', 'TC4', 'TG', 'TH', 'TE', 'TX1', 'TX2', 'TB1', 'TB2', 'TB3',
              'TB4', 'TRA', 'TRB', 'TD1', 'TD2', 'TD3', 'TD4', 'TT', 'TA', 'TD', 'TPA', 'TPD', 'TAA', 'TDD', 'TCD',
              'TSZ', 'TX', 'TY', 'TZ'):
        P += ['DELITM "%s"' % v]
    P += ['RCL 21', 'RTN']

    # LBL 10: the star vectors (x y z 1) at t = 0 and 50 years from the catalogue ST (RA, Dec, pm RA, pm Dec), as
    # STR2: a = a0 + pa t / 3600000 / cos d0, d = d0 + pd t / 3600000
    P += ['LBL 10', '58', 'ENTER', '4', 'NEWMAT', 'STO "TSA0"', 'STO "TS50"', '1', 'STO "TK"',
          'LBL 11', 'INDEX "ST"', 'RCL "TK"', '1', 'STOIJ', 'RCLEL', 'STO "TA"', 'J+', 'RCLEL', 'STO "TD"',
          'J+', 'RCLEL', 'STO "TPA"', 'J+', 'RCLEL', 'STO "TPD"',
          '0', 'XEQ 12', 'INDEX "TSA0"', 'XEQ 13', '50', 'XEQ 12', 'INDEX "TS50"', 'XEQ 13',
          '1', 'STO+ "TK"', '58', 'RCL "TK"', 'X≤Y?', 'GTO 11',
          'RCL "TS50"', 'RCL "TSA0"', '-', '2', '×', 'STO "TSD"', 'RTN',
          'LBL 12', 'STO "TT"', 'RCL× "TPD"', '3600000', '÷', 'RCL+ "TD"', 'STO "TDD"',
          'RCL "TPA"', 'RCL× "TT"', '3600000', '÷', 'RCL "TD"', 'COS', '÷', 'RCL+ "TA"', 'STO "TAA"',
          'RCL "TDD"', '1', '→REC', 'STO "TCD"', 'X<>Y', 'STO "TSZ"',
          'RCL "TAA"', 'RCL "TCD"', '→REC', 'STO "TX"', 'X<>Y', 'STO "TY"', 'RTN',
          'LBL 13', 'RCL "TK"', '1', 'STOIJ', 'RCL "TX"', 'STOSEQ', 'RCL "TY"', 'STOSEQ', 'RCL "TSZ"', 'STOSEQ',
          '1', 'STOSEQ', 'RTN']

    # LBL 20: B, one pass
    P += ['LBL 20', 'RCL "TSD"', 'RCL× 03', 'RCL "TSA0"', '+', 'STO "TSA"', 'XEQ 30',
          'RCL 02', 'XEQ 73', '[M]⊤', 'RCL "TC4"', 'X<>Y', '×', 'STO "TG"',
          'XEQ 40', 'RCL "TC4"', 'X<>Y', '×', 'STO "TH"',
          'RCL "TSA"', 'RCL "TG"', '×', 'STO "TE"', 'INDEX "TE"']
    P += column(1, 1, 'TX1') + column(1, 2, 'TX2')
    P += ['RCL "TX1"', 'RCL "TX2"', 'COMPLEX', 'STO "TX2"', '∡', 'CHS', 'RCL 45', 'MOD', 'STO "TB1"',
          'RCL "TX2"', 'ABS', 'STO "TX2"']
    P += column(1, 3, 'TX1')
    P += ['RCL "TX2"', 'RCL "TX1"', 'COMPLEX', '∡', 'STO "TB2"',
          'RCL "TSA"', 'RCL "TH"', '×', 'STO "TE"', 'INDEX "TE"']
    P += column(1, 1, 'TX1') + column(1, 2, 'TX2')
    P += ['RCL "TX1"', 'RCL "TX2"', 'COMPLEX', 'STO "TX2"', '∡', 'RCL 45', 'MOD', 'STO "TB4"',
          'RCL "TX2"', 'ABS', 'STO "TX2"']
    P += column(1, 3, 'TX1')
    P += ['RCL "TX2"', 'RCL "TX1"', 'COMPLEX', '∡', 'STO "TB3"', 'RTN']

    # LBL 30: C4 = [M transposed; w transposed], M = Q Rx(eps0) Rz(-z) Ry(theta) Rz(-zeta), Q = Rx(-eps) Rz(-dpsi),
    # w = Q v, v = kappa (sin sun - e sin pi, -cos sun + e cos pi, 0) in radians (kappa = 20.49552")
    # every rotation helper leaves values on the stack: the product so far is kept in TMT, not on the stack
    times = lambda: ['RCL "TMT"', 'X<>Y', '×', 'STO "TMT"']
    P += ['LBL 30', 'RCL 00', 'CHS', 'XEQ 71', 'STO "TMT"', 'RCL 04', 'RCL÷ 54', 'CHS', 'XEQ 73'] + times() + \
         ['STO "TQ"', 'RCL "U4"', 'XEQ 71'] + times() + ['RCL "U6"', 'CHS', 'XEQ 73'] + times() + \
         ['RCL "U7"', 'XEQ 72'] + times() + ['RCL "U5"', 'CHS', 'XEQ 73'] + times() + ['[M]⊤', 'STO "TMT"',
          '3', 'ENTER', '1', 'NEWMAT', 'STO "TV"', 'INDEX "TV"', '1', 'ENTER', 'STOIJ',
          'RCL "W5"', 'RCL "U8"', '→REC', 'STO "TX"', 'X<>Y', 'STO "TY"',          # e cos pi, e sin pi
          'RCL 15', '1', '→REC', 'STO "TZ"', 'X<>Y',                                 # cos sun, sin sun
          'RCL- "TY"', '20.49552', 'RCL÷ 54', 'deg→rad', 'STO "TT"', '×', 'STOSEQ',
          'RCL "TX"', 'RCL- "TZ"', 'RCL× "TT"', 'STOSEQ', '0', 'STOSEQ',
          'RCL "TQ"', 'RCL "TV"', '×', '[M]⊤', 'STO "TV"',
          '4', 'ENTER', '3', 'NEWMAT', 'STO "TC4"', 'INDEX "TC4"', '1', 'ENTER', 'STOIJ', 'RCL "TMT"', 'M.PUTM',
          '4', 'ENTER', '1', 'STOIJ', 'RCL "TV"', 'M.PUTM', 'RTN']
    # LBL 40: H = columns north, east, zenith (cos / sin of the latitude V6 W1, of GHA Aries + longitude G2 G3)
    P += ['LBL 40', '3', 'ENTER', 'NEWMAT', 'STO "TR"', 'INDEX "TR"', '1', 'ENTER', 'STOIJ',
          'RCL "W1"', 'RCL× "G2"', 'CHS', 'STOSEQ', 'RCL "G3"', 'CHS', 'STOSEQ', 'RCL "V6"', 'RCL× "G2"', 'STOSEQ',
          'RCL "W1"', 'RCL× "G3"', 'CHS', 'STOSEQ', 'RCL "G2"', 'STOSEQ', 'RCL "V6"', 'RCL× "G3"', 'STOSEQ',
          'RCL "V6"', 'STOSEQ', '0', 'STOSEQ', 'RCL "W1"', 'STOSEQ', 'RCL "TR"', 'RTN']
    P += rot(71, ['1', '0', '0', '0', 'c', 's', '0', '-s', 'c'])
    P += rot(72, ['c', '0', '-s', '0', '1', '0', 's', '0', 'c'])
    P += rot(73, ['c', 's', '0', '-s', 'c', '0', '0', '0', '1'])

    # LBL 50: A, one pass over the 58 stars, as CSQK (TW = 1: every star in full, results into TRA)
    P += ['LBL 50', '1', 'STO "TK"', '0', 'STO "TF"',
          'LBL 51', 'RCL "TK"', 'XEQ "N23"', 'RCL "TW"', 'X≠0?', 'GTO 53', 'DROP', 'RCL 92', 'X>Y?', 'GTO 54',
          'LBL 53', '1', 'STO+ "TF"', 'RCL "TK"', 'STO 22', 'XEQ "N22"', 'STO "TGA"', 'X<>Y', 'STO "TDE"',
          'RCL "F5"', 'RCL "F4"', 'RCL "F6"', 'XEQ 99', 'RCL "TW"', 'X≠0?', 'XEQ 55',
          'LBL 54', '1', 'STO+ "TK"', '58', 'RCL "TK"', 'X≤Y?', 'GTO 51', 'RTN',
          'LBL 55', 'INDEX "TRA"', 'RCL "TK"', '1', 'STOIJ', 'RCL "TGA"', 'STOSEQ', 'RCL "TDE"', 'STOSEQ',
          'RCL 09', 'STOSEQ', 'RCL 05', 'STOSEQ', 'RTN']
    P += hcz_vec()
    P += ['END']
    return P


def main():
    P = program()
    names = set(re.findall(r'"(T\w+)"', '\n'.join(P)))
    assert all(len(n) <= 7 for n in names), [n for n in names if len(n) > 7]
    out = os.path.join(HERE, 'TSTAR.txt')
    open(out, 'w', encoding='utf-8').write('\n'.join(P) + '\n')
    print(out, len(P), 'steps')


if __name__ == '__main__':
    main()
