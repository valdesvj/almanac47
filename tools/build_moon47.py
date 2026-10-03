#!/usr/bin/env python3
"""build_moon47.py - MOON47 for the C47 / R47: the Moon phase page as its own program.

Writes build/MOON47.txt (and build/MOON47.p47 with rejig, if it is on the PATH). Three programs in one file:
  MOON47  the page: no inputs and no INIT tables, the date and time from the calculator's clock (local time;
          minus the variable TZ, in hours, if it exists: 4 STO "TZ" for UT+4). Every number comes from the
          20 terms of python/moon47.py, the same steps. The +/- key switches the northern / southern view,
          any other key ends.
  M7TX    the ATEXT text and number printers of NAV (tools/atext_common.py), under their own names
          (M7TX M7IN M7F1 M7HM M7DT M7HL), so MOON47 does not need NAVFULL and does not clash with it.
  M7SY    the eight Moon phase symbols of glyphs47 (12 rows, AGRAPH).
Needs a C47 firmware with ATEXT and GRFNT (master on or after 30 Sep 2026).

Registers: 03 TZ, 05 loop, 06 JD (UT), 09 secant count, 50-53 secant, 54-57 the next phases, 58-61 their quarter, 10-14 D M M' F and T / E, 15 elongation at JD,
16 Sun-Moon angle, 17 Sun distance, 18 % lit, 19 HP, 20 SD, 23 last new Moon, 24 age, 25 phase number,
26 27 target and time of a phase, 28 south (0 / 1), 29 stack size, 37 38 40-48 work; 30-36 49 the printers.

  python3 tools/build_moon47.py
"""
import os, re, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..')
sys.path[:0] = [HERE, os.path.join(HERE, 'generators', 'atext'), os.path.join(HERE, 'generators'),
                os.path.join(ROOT, 'python')]
import moon47 as M47                                                        # noqa: E402

LUN, RATE = '29.530589', '12.190749'
RENAME = {'PX': 'M7PX', 'FBX': 'M7BX', 'PTXS': 'M7TX', 'PINS': 'M7IN', 'PF1S': 'M7F1', 'PHMS': 'M7HM', 'PDMS': 'M7DM', 'PDTS': 'M7DT',
          'PZNS': 'M7ZN', 'PHLS': 'M7HL', 'PTTY': 'M7TY', 'PTNT': 'M7NT', 'PSYB': 'M7SY'}
TX, IN, F1, HM, DT, HL, SY = (('XEQ "%s"' % RENAME[n]) for n in ('PTXS', 'PINS', 'PF1S', 'PHMS', 'PDTS', 'PHLS', 'PSYB'))


def code(d, m, mp, f):
    """One number for the multiples of D, M, M', F of a term (d 0-4, m -1..1, m' -2..3, f -2..2)."""
    return d * 1000 + (m + 1) * 100 + (mp + 2) * 10 + (f + 2)


def terms():
    out = []
    for d, m, mp, f, cl, cr in M47.TERMS:
        out += [str(code(d, m, mp, f)), str(cl), str(cr), 'XEQ 50']
    return out


def clock(f42):
    """X: the JD (UT) of now: the clock (local time) minus TZ hours if the variable TZ exists."""
    if not f42:
        tz = ['0', 'STO 03', "SF 'IGN1ER'", 'RCL "TZ"', 'STO 03', "CF 'IGN1ER'"]
        return tz + ['Date→ⅅ', 'Time→ℸ', 'ⅅℸ→J', 'RCL 03', '24', '÷', '-']
    # Free42: DATE in the format of flags 67 (YMD: Y.MMDD), 31 (DMY: D.MMYYYY) or neither (MDY: M.DDYYYY),
    # TIME HH.MMSS; the JD with the Gregorian arithmetic (Meeus 7.1); flag 25 ignores the missing TZ
    tz = ['0', 'STO 03', 'SF 25', 'RCL "TZ"', 'STO 03', 'CF 25']
    return tz + ['DATE', 'FS? 67', 'GTO 07', 'FS? 31', 'GTO 08',
                 'ENTER', 'IP', 'STO 41', '-', '100', '×', 'ENTER', 'IP', 'STO 42', '-', '10000', '×', 'GTO 09',
                 'LBL 08', 'ENTER', 'IP', 'STO 42', '-', '100', '×', 'ENTER', 'IP', 'STO 41', '-', '10000', '×', 'GTO 09',
                 'LBL 07', 'ENTER', 'IP', 'X<>Y', 'FP', '100', '×', 'ENTER', 'IP', 'STO 41', '-', '100', '×', 'STO 42',
                 'R↓',
                 'LBL 09', '0.5', '+', 'IP', 'STO 43',                         # R43 year, R41 month, R42 day
                 'RCL 41', '3', 'X>Y?', 'XEQ 10',
                 'RCL 43', '100', '÷', 'IP', 'STO 44', '4', '÷', 'IP', 'RCL 44', '-', '2', '+',
                 'RCL 43', '4716', '+', '365.25', '×', 'IP', '+',
                 'RCL 41', '1', '+', '30.6001', '×', 'IP', '+', 'RCL 42', '+', '1524.5', '-',
                 'TIME', '→HR', 'RCL 03', '-', '24', '÷', '+']


def main_program(f42=False):
    # the minute mark ': ATEXT on the C47; on Free42 two boxes (LBL 47), because with it and the descenders of
    # ( and ) the AGRAPH font would be 17 rows high (two bands of 8). Same pixels: the standard font's '
    AP = ['XEQ 47'] if f42 else ['"\'"', TX]
    P = ['LBL "MOON47"',
         'REM "MOON47: the Moon phase now (clock, minus TZ hours if TZ exists); +/- north / south view; other keys end"']
    P += (['SIZE 100', 'DEG'] if f42 else ['SSIZE#', 'STO 29', 'SSIZE8', 'DEG', 'WSIZE 64'])
    P += clock(f42) + ['STO 06', '0', 'STO 28']
    P += (['3', 'STO "GrMod"', '0', 'STO "RefLCD"', 'XEQ 29'] if f42 else ['21', 'GRFNT', 'DROP', 'XEQ 29'])
    P += ['LBL 01', 'CLLCD', 'XEQ 30'] + (['-1', 'STO "RefLCD"'] if f42 else ['PAUSE 0'])
    P += (['LBL 02', 'GETKEY', '15', 'X=Y?', 'GTO 04'] if f42 else       # Free42: GETKEY waits; +/- is 15
          ['LBL 02', 'KEY? 39', 'GTO 02', 'RCL 39', '43', 'X=Y?', 'GTO 04'])
    P += (['CLLCD', '0', 'STO "GrMod"', '7', 'STO "RefLCD"', 'CLST', 'CLD', 'RTN'] if f42 else
          ['CLLCD', '20', 'GRFNT', 'DROP', 'RCL 29', '4', 'X=Y?', 'SSIZE4', 'CLSTK', 'RTN'])
    P += ['LBL 04', '1', 'RCL 28', '-', 'STO 28', 'GTO 01']
    if f42:
        P += ['LBL 10', '12', 'STO+ 41', '1', 'STO- 43', 'RTN',
              'REM "LBL 47: Y row of the base line, X column -> the minute mark (2 x 5 + 1 x 1 pixels); Y row, X next column"',
              'LBL 47', 'STO "AX"', 'STO "BX"', 'X<>Y', 'STO "AY"', '10', '+', 'STO "BY"', '2', 'STO "BW"', '5', 'STO "BH"',
              'XEQ "M7BX"', 'RCL "AX"', 'STO "BX"', 'RCL "AY"', '9', '+', 'STO "BY"', '1', 'STO "BW"', 'STO "BH"',
              'XEQ "M7BX"', 'RCL "AY"', 'RCL "AX"', '7', '+', 'RTN']
    P += [
         # ---------------------------------------------------------------- the numbers
         'REM "LBL 29: the numbers of the page (once); LBL 30 draws it (again after +/-)"',
         'LBL 29',
         'RCL 06', 'XEQ 41', 'STO 15',
         'RCL 22', 'COS', 'RCL 15', 'COS', '×', 'ACOS', 'STO 16',
         'RCL 11', 'COS', '0.016708', '×', '1.00014', 'X<>Y', '-',
         'RCL 11', '2', '×', 'COS', '0.000141', '×', '-', '149597870.7', '×', 'STO 17',
         'RCL 16', 'SIN', '×', 'STO 18',
         'RCL 41', 'RCL 17', 'RCL 16', 'COS', '×', '-', 'STO 19',
         'X↑2', 'RCL 18', 'X↑2', '+', 'SQRT', 'RCL 19', 'X<>Y', '÷', '1', '+', '50', '×', 'STO 18',
         '6378.14', 'RCL 41', '÷', 'ASIN', '60', '×', 'STO 19',
         '358473400', 'RCL 41', '÷', '60', '÷', 'STO 20',
         'RCL 06', 'RCL 15', RATE, '÷', '-', '1', '-', '0', 'XEQ 42', 'STO 23',
         'RCL 06', 'X<Y?', 'XEQ 31',
         'RCL 06', 'RCL 23', '-', 'STO 24',
         LUN, '÷', '8', '×', '0.5', '+', 'IP', '8', 'MOD', 'STO 25',
         'XEQ 75', 'RTN',
         # ---------------------------------------------------------------- the page
         'LBL 30',
         '226', '2', 'RCL 06', DT,
         '226', '79', 'RCL 06', '0.5', '+', '1', 'MOD', '24', '×', HM,
         '226', '118', '"UT"', TX,
         '-221', '0', 'PIXEL',
         'XEQ 70',
         '200', '168', 'RCL 25', '60', '+', 'STO 37', 'DROP', 'XEQ IND 37', TX,
         '183', '168', '"LIT "', TX, 'RCL 18', IN, '"%   AGE "', TX, 'RCL 24', F1, '" DAYS"', TX,
         '166', '168', '"HP "', TX, 'RCL 19', F1] + AP + ['"  SD "', TX, 'RCL 20', F1] + AP + [
         '156', '168', '230', HL,
         '139', '168', '"NEXT PHASES (UT)"', TX,
         'XEQ 45', 'XEQ 85',
         '6', '168', 'XEQ 32', TX,
         'RTN',
         'LBL 31', 'RCL 23', LUN, '-', '1', '-', '0', 'XEQ 42', 'STO 23', 'RTN',
         'LBL 32', 'RCL 28', 'X≠0?', 'GTO 34', 'DROP', '"AS SEEN FROM THE NORTH"', 'RTN',
         'LBL 34', 'DROP', '"AS SEEN FROM THE SOUTH"', 'RTN',
         'LBL 35', '1', 'CHS', 'STO× 27', 'RTN',
         # ---------------------------------------------------------------- the Moon
         'REM "LBL 41: JD (UT) in X -> X elongation 0-360; R41 distance km, R22 latitude, R11 M (deg)"',
         'LBL 41', '0.000798611', '+', '2451545', '-', '36525', '÷', 'STO 14',
         '445267.1114', '×', '297.8501921', '+', 'STO 10',
         'RCL 14', '35999.05029', '×', '357.5291092', '+', 'STO 11',
         'RCL 14', '477198.8675', '×', '134.9633964', '+', 'STO 12',
         'RCL 14', '483202.0175', '×', '93.272095', '+', 'STO 13',
         'RCL 14', '0.004817', '×', '1.914602', 'X<>Y', '-', 'RCL 11', 'SIN', '×',
         'RCL 11', '2', '×', 'SIN', '0.019993', '×', '+', 'RCL 11', '3', '×', 'SIN', '0.000289', '×', '+', 'STO 48',
         'RCL 14', '0.002516', '×', '1', 'X<>Y', '-', 'STO 14',
         '0', 'STO 40', 'STO 41'] + terms() + [
         'RCL 41', '1000', '÷', '385000.56', '+', 'STO 41',
         'RCL 13', 'SIN', '5.128189', '×', 'STO 22',
         'RCL 40', '1000000', '÷', 'RCL 10', '+', 'RCL 48', '-', '0.00569', '+', '360', 'MOD', 'RTN',
         'REM "LBL 50: Z the multiples (code), Y longitude 1e-6 deg, X distance 1e-3 km -> R40, R41"',
         'LBL 50', 'STO 43', 'R↓', 'STO 42', 'R↓', 'STO 44',
         '1000', '÷', 'IP', 'RCL 10', '×', 'STO 46',
         'RCL 44', '100', '÷', 'IP', '10', 'MOD', '1', '-', 'STO 45', 'RCL 11', '×', 'STO+ 46',
         'RCL 44', '10', '÷', 'IP', '10', 'MOD', '2', '-', 'RCL 12', '×', 'STO+ 46',
         'RCL 44', '10', 'MOD', '2', '-', 'RCL 13', '×', 'STO+ 46',
         'RCL 14', 'RCL 45', 'ABS', 'Y↑X', 'STO 47',
         'RCL 46', 'SIN', 'RCL 42', '×', 'RCL 47', '×', 'STO+ 40',
         'RCL 46', 'COS', 'RCL 43', '×', 'RCL 47', '×', 'STO+ 41', 'RTN',
         'REM "LBL 42: Y JD, X elongation (0 new, 90, 180 full, 270) -> X the JD of that phase from about Y on:"',
         'REM "the secant method from Y and the guess of the mean rate, three steps (R50 R51 t0 f0, R27 R52 t1 f1)"',
         'LBL 42', 'STO 26', 'R↓', 'STO 50', 'XEQ 41', 'RCL 26', 'X<>Y', '-', '360', 'MOD', 'STO 51',
         RATE, '÷', 'RCL 50', '+', 'STO 27', 'RCL 51', 'CHS', 'STO 51', '3', 'STO 09',
         'LBL 43', 'RCL 27', 'XEQ 41', 'RCL 26', '-', '180', '+', '360', 'MOD', '180', '-', 'STO 52',
         'RCL 51', 'X=Y?', 'GTO 44', '-', 'STO 53',
         'RCL 27', 'RCL 50', '-', 'RCL× 52', 'RCL÷ 53', 'RCL 27', 'STO 50', 'X<>Y', '-', 'STO 27',
         'RCL 52', 'STO 51', 'DSE 09', 'GTO 43',
         'LBL 44', 'RCL 27', 'RTN',
         # ---------------------------------------------------------------- the disc
         'REM "LBL 70: the disc, centre row 120 column 80, radius 62, column by column (moon47.disc_runs)"',
         'LBL 70', 'RCL 24', LUN, '÷', '360', '×', 'COS', 'X=0?', '1E-30', 'STO 26',
         '1', 'STO 27', 'RCL 24', LUN, '2', '÷', 'X<Y?', 'XEQ 35', 'RCL 28', 'X≠0?', 'XEQ 35',
         '-62', 'STO 40',
         'LBL 71', '62.3', 'X↑2', 'RCL 40', 'X↑2', '-', 'SQRT', 'IP', 'STO 41',
         '60.8', 'X↑2', 'RCL 40', 'X↑2', '-', '0', 'X>Y?', 'GTO 72', 'X<>Y', 'SQRT', 'IP', '1', '+',
         'LBL 72', 'RCL 41', 'XEQ 76',
         'RCL 27', 'RCL 40', '×', 'STO 42', '3844', 'RCL 42', 'RCL 26', '÷', 'X↑2', '-', 'STO 43',
         'RCL 26', 'X<0?', 'GTO 73',
         'RCL 42', 'X≤0?', 'GTO 74', 'RCL 43', 'X<0?', 'GTO 36', 'SQRT', 'IP', '1', '+', 'GTO 77',
         'LBL 36', '0', 'LBL 77', 'RCL 41', 'XEQ 76', 'GTO 74',
         'LBL 73', 'RCL 42', 'X<0?', 'GTO 78', '0', 'RCL 41', 'XEQ 76', 'GTO 74',
         'LBL 78', 'RCL 43', 'X≤0?', 'GTO 74', 'SQRT', 'IP', 'RCL 41', 'X>Y?', 'X<>Y', '0', 'X<>Y', 'XEQ 76',
         'LBL 74', '1', 'STO+ 40', '62', 'RCL 40', 'X≤Y?', 'GTO 71', 'RTN',
         'REM "LBL 76: Y a, X b -> the rows a <= |y| <= b of column 80 + R40 (both sides of row 120)"',
         'LBL 76', 'STO 45', 'X<>Y', 'STO 44', 'RCL 45', 'X<Y?', 'RTN',
         'RCL 44', 'X=0?', 'GTO 79',
         '120', 'RCL 44', '+', '120', 'RCL 45', '+', 'XEQ 81',
         '120', 'RCL 45', '-', '120', 'RCL 44', '-', 'XEQ 81', 'RTN',
         'LBL 79', '120', 'RCL 45', '-', '120', 'RCL 45', '+',
         'REM "LBL 81: Y first row, X last row: a run of column 80 + R40"',
         'LBL 81', 'STO 47', 'R↓', 'STO 46']
    if f42:                       # a box one column wide (M7BX: the FBX of build_free42, OR mode)
        P += ['RCL 46', 'STO "BY"', 'RCL 40', '80', '+', 'STO "BX"', '1', 'STO "BW"',
              'RCL 47', 'RCL 46', '-', '1', '+', 'STO "BH"', 'XEQ "M7BX"', 'RTN']
    else:                         # AGRAPH, up to 60 rows at a time
        P += ['LBL 82', 'RCL 47', 'RCL 46', '-', '1', '+', '60', 'X>Y?', 'X<>Y', 'STO 39',
              '2ˣ', '1', '-', 'SINT', 'STO 48', 'RCL 46', 'RCL 40', '80', '+', 'AGRAPH 48', 'DROP', 'DROP',
              'RCL 39', 'STO+ 46', 'RCL 46', 'RCL 47', 'X≥Y?', 'GTO 82', 'RTN']
    P += [
         # ---------------------------------------------------------------- the next phases
         'REM "LBL 75: the next four phases (UT) into R54-R57, their quarter into R58-R61"',
         'LBL 75', 'RCL 15', '90', '÷', 'IP', '1', '+', 'STO 38', '0', 'STO 05',
         'LBL 83', 'RCL 38', 'RCL 05', '+', '4', 'MOD', 'STO 37',
         'RCL 06', 'RCL 37', '90', '×', 'XEQ 42', 'STO 44',
         'RCL 06', 'X<>Y', 'X<Y?', 'XEQ 84',
         'RCL 05', '54', '+', 'STO 39', 'RCL 44', 'STO IND 39', '4', 'STO+ 39', 'RCL 37', 'STO IND 39',
         '1', 'STO+ 05', '4', 'RCL 05', 'X<Y?', 'GTO 83', 'RTN',
         'LBL 84', 'RCL 44', LUN, '+', '2', '-', 'RCL 37', '90', '×', 'XEQ 42', 'STO 44', 'RTN',
         'REM "LBL 45: the four phases: name, day-month (Meeus 7, from the JD) and time UT"',
         'LBL 45', '0', 'STO 05',
         'LBL 46', 'RCL 05', '54', '+', 'STO 39', 'RCL IND 39', 'STO 44', '4', 'STO+ 39', 'RCL IND 39', 'STO 37',
         '121', 'RCL 05', '16', '×', '-', 'STO 43',
         'RCL 43', '168', 'RCL 37', '2', '×', '60', '+', 'STO 42', 'DROP', 'XEQ IND 42', TX,
         'RCL 44', '0.5', '+', 'IP', 'STO 40', '1867216.25', '-', '36524.25', '÷', 'IP', 'STO 41',
         '4', '÷', 'IP', 'RCL 41', 'X<>Y', '-', 'RCL 40', '+', '1525', '+', 'STO 42',
         '122.1', '-', '365.25', '÷', 'IP', '365.25', '×', 'IP', 'STO 45',
         'RCL 42', 'X<>Y', '-', '30.6001', '÷', 'IP', 'STO 41',
         'RCL 42', 'RCL 45', '-', 'RCL 41', '30.6001', '×', 'IP', '-', 'STO 46',
         'RCL 41', '1', '-', 'STO 47', '12', 'X<Y?', 'STO- 47',
         'RCL 43', '300', 'RCL 46', 'XEQ 88', '"-"', TX, 'RCL 47', 'XEQ 88', '" "', TX,
         'RCL 44', '0.5', '+', '1', 'MOD', '24', '×', HM,
         '1', 'STO+ 05', '4', 'RCL 05', 'X<Y?', 'GTO 46', 'RTN',
         'REM "LBL 88: Z row, Y column, X 0-99 -> two digits (a 0 first under 10)"',
         'LBL 88', 'STO 48', 'DROP', 'RCL 48', '10', 'X≤Y?', 'GTO 39', 'DROP', 'DROP', '"0"', TX, 'GTO 40',
         'LBL 39', 'DROP', 'DROP', 'LBL 40', 'RCL 48', IN, 'RTN',
         # ---------------------------------------------------------------- the eight symbols
         'REM "LBL 85: the eight phase symbols, today\'s one inverted (XOR box 18 x 18)"',
         'LBL 85', '0', 'STO 05',
         'LBL 86', '26', 'RCL 05', '29', '×', '168', '+', 'RCL 05', '90', '+', 'STO 46', 'DROP', 'XEQ IND 46', SY,
         'RCL 05', 'RCL 25', 'X=Y?', 'XEQ 87',
         '1', 'STO+ 05', '8', 'RCL 05', 'X<Y?', 'GTO 86', 'RTN']
    if f42:
        P += ['LBL 87', '23', 'STO "BY"', 'RCL 05', '29', '×', '165', '+', 'STO "BX"', '18', 'STO "BW"', 'STO "BH"',
              'SF 34', 'SF 35', 'XEQ "M7BX"', 'CF 34', 'CF 35', 'RTN']
    else:
        P += ['LBL 87', '3', 'STO 46', 'GRMOD 46', '111111111111111111#2', 'STO 46',
              '23', 'RCL 05', '29', '×', '165', '+', '18', 'STO 47', 'R↓',
              'LBL 89', 'AGRAPH 46', 'DSE 47', 'GTO 89', 'DROP', 'DROP', '0', 'STO 46', 'GRMOD 46', 'RTN']
    # the texts: the phase names (60-67) and the symbols "0" - "7" (90-97)
    for k, name in enumerate(M47.NAMES):
        P += ['LBL %d' % (60 + k), '"%s"' % name, 'RTN']
    for k in range(8):
        P += ['LBL %d' % (90 + k), '"%d"' % k, 'RTN']
    return P + ['END']


def printers():
    import build_navfull as B, navopt
    import atext_common as AC
    return AC.printers(navopt.pdts(navopt.phls(navopt.fonts(B.read('PTXS')))), '49', False, 21)


def symbols():
    import glyphs47
    return glyphs47.program('PSYB', {k: glyphs47.BIG[k] for k in '01234567'}, ws=16)


def rename(P):
    out = []
    for l in P:
        for a, b in RENAME.items():
            l = l.replace('"%s"' % a, '"%s"' % b)
        out.append(l)
    return out


def check_labels(P):
    """Every program of P (up to END) defines each label once, and every XEQ / GTO n has its LBL n."""
    cur = []
    for l in P + ['END']:
        if l != 'END':
            cur.append(l); continue
        lbl = [x for x in cur if re.fullmatch(r'LBL (\d+|".+")', x)]
        dup = sorted({x for x in lbl if lbl.count(x) > 1})
        assert not dup, 'labels defined twice: %s' % dup
        miss = sorted({x.split()[1] for x in cur if re.fullmatch(r'(XEQ|GTO) \d+', x)} - {x.split()[1] for x in lbl})
        assert not miss, 'no LBL for %s' % miss
        cur = []


def build():
    P = main_program() + rename(printers()) + rename(symbols())
    check_labels(P)
    if P[-1] != 'END':
        P.append('END')
    return [l for l in P if not l.startswith('REM ')] , P


def lib_section(L, name):
    """The routine LBL "name" of build_free42.lib() up to the next global label, as one program."""
    i = L.index('LBL "%s"' % name)
    j = next((k for k in range(i + 1, len(L)) if L[k].startswith('LBL "')), len(L))
    return [l for l in L[i:j] if l != 'END'] + ['END']


def ptxs_with(F, keep, cs):
    """build_free42.font('PTXS') with the glyphs of cs from the C47 standard font, given to the font builder as
    if PTXS had them: NAV never writes ' ( ) as text, and in PTXS ( is the Moon's symbol. The builder then
    places their rows under the base line itself (as '%' and 'Q'). Only for MOON47: build_free42 is unchanged."""
    from stdfont import STD
    gc, rd = F.glyph_columns, F.B.read

    def columns(lines):
        g = gc(lines)
        for c in cs:
            cb, cg, ca, ra, rg, rb, rows = STD[ord(c)]
            cols = {}
            for r, v in enumerate(rows):
                y = rb + rg - 5 - r
                for x in range(cg):
                    if y >= 0 and v >> (cg - 1 - x) & 1:
                        cols[cb + x] = cols.get(cb + x, 0) | 1 << y
            g[ord(c)] = (cols, cb + cg + ca - 1)
        return g

    def read(name):
        L = rd(name)
        if name == 'PTXS':
            e = L.index('END')
            L = L[:e] + [x for c in cs if 'LBL %d' % ord(c) not in L for x in ('LBL %d' % ord(c), 'RTN')] + L[e:]
        return L
    F.glyph_columns, F.B.read = columns, read
    try:
        return F.font('PTXS', keep)[0]
    finally:
        F.glyph_columns, F.B.read = gc, rd


def build_f42():
    """MOON47 for Free42 (DM42 / DM42n stock firmware): the main program with f42=True, converted as NAVFULL
    (build_free42.conv), the AGRAPH font of the T21 views (PTXS with the widths of GRFNT 21 and its number
    printers), the phase symbols, PX and FBX. GETKEY waits for the key: +/- (15) switches the view."""
    import build_free42 as F
    main = [l for l in main_program(f42=True) if not l.startswith('REM ')]
    chars = set(''.join(re.findall(r'^"([^"]*)"$', '\n'.join(main), re.M))) | set('0123456789-.: %\'')
    P = F.conv(main, 'MOON47')
    P += F.conv(ptxs_with(F, chars - {"'"}, "()"), 'PTXS')
    P += F.conv(F.font('PSYB', chars, F.psym('PSYB', True, '01234567'))[0], 'PSYB')
    lib = F.lib()
    P += lib_section(lib, 'PX') + lib_section(lib, 'FBX')
    P = rename(P)
    check_labels(P)
    return P


def main():
    plain, with_rem = build()
    out = os.path.join(ROOT, 'build', 'MOON47.txt')
    for f in (out, os.path.join(ROOT, 'build', 'dm42', 'MOON47.txt')):     # the DM42 runs the same C47 firmware
        open(f, 'w', encoding='utf-8').write('\n'.join(plain) + '\n')
    print('%s (and build/dm42/): %d steps' % (os.path.relpath(out, ROOT), sum(1 for l in plain if l != 'END')))
    r = os.environ.get('REJIG') or shutil.which('rejig')
    if r:
        for f in (out, os.path.join(ROOT, 'build', 'dm42', 'MOON47.txt')):
            subprocess.run([r, f, '-o', f[:-4] + '.p47'], check=True)
        print('%s: %d bytes' % (os.path.relpath(out[:-4] + '.p47', ROOT), os.path.getsize(out[:-4] + '.p47')))
    f42 = build_f42()
    out = os.path.join(ROOT, 'build', 'free42', 'MOON47.txt')
    open(out, 'w', encoding='utf-8').write('\n'.join(f42) + '\n')
    print('%s: %d steps' % (os.path.relpath(out, ROOT), sum(1 for l in f42 if l != 'END')))
    run = os.path.join(HERE, 'f42', 'f42run')
    if os.path.exists(run):
        raw = out[:-4] + '.raw'
        r = subprocess.run([run], input='paste %s\nexport %s\n' % (out, raw), text=True, capture_output=True)
        print('%s: %d bytes' % (os.path.relpath(raw, ROOT), os.path.getsize(raw)) if os.path.exists(raw) else r.stdout[-300:])


if __name__ == '__main__':
    main()
