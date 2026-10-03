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
RENAME = {'PTXS': 'M7TX', 'PINS': 'M7IN', 'PF1S': 'M7F1', 'PHMS': 'M7HM', 'PDMS': 'M7DM', 'PDTS': 'M7DT',
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


def main_program():
    P = ['LBL "MOON47"',
         'REM "MOON47: the Moon phase now (clock, minus TZ hours if TZ exists); +/- north / south view; other keys end"',
         'SSIZE#', 'STO 29', 'SSIZE8', 'DEG', 'WSIZE 64',
         '0', 'STO 03', "SF 'IGN1ER'", 'RCL "TZ"', 'STO 03', "CF 'IGN1ER'",
         '0', 'STO 28',
         'Date→ⅅ', 'Time→ℸ', 'ⅅℸ→J', 'RCL 03', '24', '÷', '-', 'STO 06',
         '21', 'GRFNT', 'DROP', 'XEQ 29',
         'LBL 01', 'CLLCD', 'XEQ 30', 'PAUSE 0',
         'LBL 02', 'KEY? 39', 'GTO 02',
         'RCL 39', '43', 'X=Y?', 'GTO 04',
         'CLLCD', '20', 'GRFNT', 'DROP', 'RCL 29', '4', 'X=Y?', 'SSIZE4', 'CLSTK', 'RTN',
         'LBL 04', '1', 'RCL 28', '-', 'STO 28', 'GTO 01',
         # ---------------------------------------------------------------- the page
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
         'LBL 30',
         # header
         '226', '2', 'RCL 06', DT,
         '226', '79', 'RCL 06', '0.5', '+', '1', 'MOD', '24', '×', HM,
         '226', '118', '"UT"', TX,
         '-221', '0', 'PIXEL',
         'XEQ 70',
         '200', '168', 'RCL 25', '60', '+', 'STO 37', 'DROP', 'XEQ IND 37', TX,
         '183', '168', '"LIT "', TX, 'RCL 18', IN, '"%   AGE "', TX, 'RCL 24', F1, '" DAYS"', TX,
         '166', '168', '"HP "', TX, 'RCL 19', F1, '"\'  SD "', TX, 'RCL 20', F1, '"\'"', TX,
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
         'REM "LBL 81: Y first row, X last row -> AGRAPH up to 60 rows at a time"',
         'LBL 81', 'STO 47', 'R↓', 'STO 46',
         'LBL 82', 'RCL 47', 'RCL 46', '-', '1', '+', '60', 'X>Y?', 'X<>Y', 'STO 39',
         '2ˣ', '1', '-', 'SINT', 'STO 48', 'RCL 46', 'RCL 40', '80', '+', 'AGRAPH 48', 'DROP', 'DROP',
         'RCL 39', 'STO+ 46', 'RCL 46', 'RCL 47', 'X≥Y?', 'GTO 82', 'RTN',
         # ---------------------------------------------------------------- the next phases
         'REM "LBL 75: the next four phases (UT): the next quarter after the elongation, then the others"',
         'LBL 75', 'RCL 15', '90', '÷', 'IP', '1', '+', 'STO 38', '0', 'STO 05',
         'LBL 83', 'RCL 38', 'RCL 05', '+', '4', 'MOD', 'STO 37',
         'RCL 06', 'RCL 37', '90', '×', 'XEQ 42', 'STO 44',
         'RCL 06', 'X<>Y', 'X<Y?', 'XEQ 84',
         'RCL 05', '54', '+', 'STO 39', 'RCL 44', 'STO IND 39', '4', 'STO+ 39', 'RCL 37', 'STO IND 39',
         '1', 'STO+ 05', '4', 'RCL 05', 'X<Y?', 'GTO 83', 'RTN',
         'REM "LBL 45: the four phases from R54-R61: name, date and time UT"',
         'LBL 45', '0', 'STO 05',
         'LBL 46', 'RCL 05', '54', '+', 'STO 39', 'RCL IND 39', 'STO 44', '4', 'STO+ 39', 'RCL IND 39', 'STO 37',
         '121', 'RCL 05', '16', '×', '-', 'STO 43',
         'RCL 43', '168', 'RCL 37', '2', '×', '60', '+', 'STO 42', 'DROP', 'XEQ IND 42', TX,
         'RCL 44', 'J→ⅅℸ', 'R↓', 'STO 40', 'DAY', 'XEQ 88', '"-"', '+', 'RCL 40', 'MONTH', 'XEQ 88', '+', '" "', '+',
         'STO 41', 'RCL 43', '300', 'RCL 41', TX,
         'RCL 44', '0.5', '+', '1', 'MOD', '24', '×', HM,
         '1', 'STO+ 05', '4', 'RCL 05', 'X<Y?', 'GTO 46', 'RTN',
         'LBL 84', 'RCL 44', LUN, '+', '2', '-', 'RCL 37', '90', '×', 'XEQ 42', 'STO 44', 'RTN',
         'REM "LBL 88: X 0-99 -> two digits as text"',
         'LBL 88', 'STO 45', '10', '÷', 'IP', '90', '+', 'STO 46', 'DROP',
         'RCL 45', '10', 'MOD', '90', '+', 'STO 45', 'DROP', 'XEQ IND 46', 'XEQ IND 45', '+', 'RTN',
         # ---------------------------------------------------------------- the eight symbols
         'REM "LBL 85: the eight phase symbols, today\'s one inverted (XOR box 18 x 18)"',
         'LBL 85', '0', 'STO 05',
         'LBL 86', '26', 'RCL 05', '29', '×', '168', '+', 'RCL 05', '90', '+', 'STO 46', 'DROP', 'XEQ IND 46', SY,
         'RCL 05', 'RCL 25', 'X=Y?', 'XEQ 87',
         '1', 'STO+ 05', '8', 'RCL 05', 'X<Y?', 'GTO 86', 'RTN',
         'LBL 87', '3', 'STO 46', 'GRMOD 46', '111111111111111111#2', 'STO 46',
         '23', 'RCL 05', '29', '×', '165', '+', '18', 'STO 47', 'R↓',
         'LBL 89', 'AGRAPH 46', 'DSE 47', 'GTO 89', 'DROP', 'DROP', '0', 'STO 46', 'GRMOD 46', 'RTN']
    # the texts: the phase names (60-67) and the digits (90-99)
    for k, name in enumerate(M47.NAMES):
        P += ['LBL %d' % (60 + k), '"%s"' % name, 'RTN']
    for k in range(10):
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


def main():
    plain, with_rem = build()
    out = os.path.join(ROOT, 'build', 'MOON47.txt')
    open(out, 'w', encoding='utf-8').write('\n'.join(plain) + '\n')
    print('%s: %d steps' % (os.path.relpath(out, ROOT), sum(1 for l in plain if l != 'END')))
    r = os.environ.get('REJIG') or shutil.which('rejig')
    if r:
        p47 = out[:-4] + '.p47'
        subprocess.run([r, out, '-o', p47], check=True)
        print('%s: %d bytes' % (os.path.relpath(p47, ROOT), os.path.getsize(p47)))


if __name__ == '__main__':
    main()
