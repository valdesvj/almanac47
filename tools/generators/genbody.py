# genbody.py - BODY: one body at a time. Writes /home/claude/BODY.txt
#
# IN : Z = JD (UT1), Y = lat (N+), X = lon (E+)
# 1. List of the bodies above the horizon (quick positions), text pages (PROMPT, two lines):
#    60 SUN, 61 MOON, 62 VENUS, 63 MARS, 64 JUPITER, 65 SATURN, stars by NA number
#    (brightest first, higher than 10 deg). Key a number on any page and R/S to choose it.
# 2. Legend page "BODY NO. ..." - key the number, R/S. Nothing keyed or 0: list again.
# 3. The chosen body in full precision: two text pages (GHA, Dec / Hc, Zn, SHA or SD, HP),
#    R/S: horizon chart on top with the body, its data below (3 x PAUSE 99), then the legend.
import json, math, os
HERE = os.path.dirname(os.path.abspath(__file__))
WID = {' ': 8, ':': 5, '.': 5, '%': 13, "'": 8, '-': 8, '/': 8, '*': 8, '°': 8,
       'A': 11, 'I': 6, 'J': 8, 'K': 11, 'L': 9, 'M': 12, 'N': 11, 'Q': 11, 'W': 12}
for c in '0123456789': WID[c] = 8
for c in 'BCDEFGHOPRSTUVXYZ': WID[c] = 10
def pxw(t): return sum(WID[c] for c in t)

P = []
def a(*xs):
    for x in xs:
        if isinstance(x, list): P.extend(x)
        else: P.extend(str(x).split('\n'))
def lit(t): a('"%s"' % t, 'XEQ 90', str(pxw(t)), 'STO+ 43')
def first(t): a('"%s"' % t, 'STO 20', str(pxw(t)), 'STO 43')
def num(steps, corr=-3):                         # formatted number: 8 px per char + corr
    a(steps.split('|')); a(str(corr), 'XEQ 76')
def rjn(steps, w, corr=-3):
    a(steps.split('|')); a(str(w), 'XEQ 94'); a(str(corr), 'XEQ 76')
def pad(px): a(str(px), 'XEQ 89')
def newline(): a('0', 'STO 43')

LEG1 = 'BODY NO.  STARS 1-58  SUN 60  MOON 61'
LEG2 = 'VENUS 62  MARS 63  JUPITER 64  SATURN 65'
w = pxw(LEG1)
LEG1P = LEG1 + ' ' * ((400 - w) // 8)

a('LBL "BODY"', 'STO 12', 'R↓', 'STO 11', 'R↓', 'STO 10', 'RCL 10', 'STO 90', 'RCL 11', 'STO 91', 'RCL 12', 'STO 92', 'XEQ "HCZI"')
# ---------------- 1. list of the bodies above the horizon
a('LBL 01', '-1', 'STO 21', '0', 'STO 43', 'RCL 10', 'XEQ "SUNA"')
a('RCL 77', 'RCL 81', 'XEQ "HCZ"', 'RCL 96', 'X>0?', 'XEQ 11')                          # Sun (exact)
a('XEQ "MOOQ"', 'XEQ "HCZ"', '-1', 'RCL 96', 'X>Y?', 'XEQ 12', 'RCL 21', 'X≥0?', 'GTO 05')   # Moon (quick)
a('1.004', 'STO 23', 'LBL 02', 'RCL 23', 'IP', 'XEQ "PLNQ"', 'XEQ "HCZ"', '-1', 'RCL 96', 'X>Y?', 'XEQ 13',
  'RCL 21', 'X≥0?', 'GTO 05', 'ISG 23', 'GTO 02')                                          # planets (quick)
a('1.058', 'STO 23', 'LBL 03', 'RCL 23', 'IP', 'XEQ "SBRT"', 'STO 82', 'INDEX "ST"', 'RCL 82', '1', 'STOIJ',
  'RCLEL', 'J+', 'RCLEL', 'X<>Y', 'RCL 80', 'X<>Y', '-', 'XEQ "HCZ"', '9', 'RCL 96', 'X>Y?', 'XEQ 14',
  'RCL 21', 'X≥0?', 'GTO 05', 'ISG 23', 'GTO 03')                                          # stars (catalogue)
a('RCL 43', 'X≠0?', 'XEQ 45', 'RCL 21', 'X≥0?', 'GTO 05')
# ---------------- 2. legend: key the body number
a('LBL 04', '"%s"' % LEG1P[:24], 'STO 20', '"%s"' % LEG1P[24:], 'XEQ 90', '"%s"' % LEG2[:22], 'XEQ 90',
  '"%s"' % LEG2[22:], 'XEQ 90', '-1', 'PROMPT 20', 'STO 21')
# validate: 1-58 or 60-65, whole number; else the list again
a('LBL 05', 'RCL 21', 'FP', 'X≠0?', 'GTO 01', 'RCL 21', '60', 'X≤Y?', 'GTO 06',
  'RCL 21', '1', 'X>Y?', 'GTO 01', 'RCL 21', '58', 'X<Y?', 'GTO 01', 'GTO 07',
  'LBL 06', 'RCL 21', '65', 'X<Y?', 'GTO 01')
# ---------------- 3. the body in full precision
a('LBL 07', 'RCL 21', 'STO 13', '0', 'STO 16', 'STO 17', 'RCL 10', 'XEQ "SUNA"')
a('"S"', 'STO 25', 'FC? 10', 'GTO 15', 'RCL 10', '6', 'XEQ "TGET"', 'X≥0?', 'XEQ 59', 'LBL 15', 'FS? 12', 'XEQ 65')   # T = tables
a('RCL 13', '60', 'X>Y?', 'GTO 16', 'X=Y?', 'GTO 17', '61', 'RCL 13', 'X=Y?', 'GTO 18')
# planets 62-65
a('RCL 13', '61', '-', 'XEQ "PLN2"', 'STO 14', 'R↓', 'STO 15', 'R↓', 'STO 16', 'GTO 19')
a('LBL 16', 'RCL 13', 'STO 82', 'XEQ "STR2"', 'STO 14', 'R↓', 'STO 15', 'R↓', 'STO 16', 'GTO 19')    # star
a('LBL 17', 'RCL 81', 'STO 14', 'RCL 77', 'STO 15', 'RCL 73', '15.99383', 'X<>Y', '÷', 'STO 17', 'GTO 19')  # Sun
a('LBL 18', 'XEQ "MOO2"', 'STO 14', 'R↓', 'STO 15', 'R↓', 'STO 16', 'R↓', 'STO 17')                # Moon
a('LBL 19', 'RCL 15', 'RCL 14', 'XEQ "HCZ"', 'RCL 96', 'STO 18', 'RCL 97', 'STO 19')
# text page 1: name, date, UT  |  GHA, Dec
a('RCL 13', 'XEQ 47', 'XEQ 68'); lit('  '); num('RCL 10|XEQ "SDAT"', 0); lit(' ')
num('RCL 10|0.5|+|1|MOD|24|×|XEQ "SHM"'); lit(' UT'); pad(400)
newline(); lit('GHA '); num('RCL 14|XEQ "SDM"'); lit('  DEC ')
a('"N"', 'STO 26', 'RCL 15', 'X<0?', 'XEQ 99', 'RCL 26', 'XEQ 90'); lit(' '); num('RCL 15|ABS|XEQ "SDM"'); a('XEQ 91')
# text page 2: Hc, Zn  |  SHA (stars, planets), SD (Sun), HP SD (Moon), T/S
first('HC '); num('RCL 18|XEQ "SDM"'); lit('  ZN '); num('RCL 19|XEQ "SZN"'); pad(400)
newline()
a('RCL 13', '60', 'X>Y?', 'GTO 20', 'X=Y?', 'GTO 21', '61', 'RCL 13', 'X=Y?', 'GTO 22')
a('LBL 20'); lit('SHA '); num('RCL 16|XEQ "SDM"'); a('GTO 23')
a('LBL 21'); lit('SUN SD '); num('RCL 17|XEQ "SF1"'); lit("'"); a('GTO 23')
a('LBL 22'); lit('HP '); num('RCL 16|XEQ "SF1"'); lit("'  SD "); num('RCL 17|XEQ "SF1"'); lit("'")
a('LBL 23'); lit('  '); a('RCL 25', 'XEQ 90', 'XEQ 91')
# ---------------- chart on top (sine altitude scale), the body's data below, status-bar font (PTXS)
HY, HS = 86, 132
def txt(y, x, s): a(y, x, '"%s"' % s, 'XEQ "PTXS"')
a('CLLCD')
a(226, 2, 'RCL 10', 'XEQ "PDTS"')
a(226, 88, 'RCL 10', '0.5', '+', '1', 'MOD', '24', '×', 'XEQ "PHMS"'); txt(226, 129, 'UT')
a('"N"', 'STO 26', 'RCL 11', 'X<0?', 'XEQ 99'); a(226, 162, 'RCL 26', 'XEQ "PTXS"'); a(226, 164, 'RCL 11', 'ABS', 'XEQ "PDMS"')
a('"E"', 'STO 26', 'RCL 12', 'X<0?', 'XEQ 98'); a(226, 244, 'RCL 26', 'XEQ "PTXS"'); a(226, 246, 'RCL 12', 'ABS', 'XEQ "PDMS"')
a(226, 388, 'RCL 25', 'XEQ "PTXS"')
a(HY, '20', '376', 'XEQ "PHLS"')
a('%d.%03d03' % (HY, HY + HS), 'STO 47', 'LBL 57', 'RCL 47', 'IP', '18', 'PIXEL', 'ISG 47', 'GTO 57')
for v in (10, 20, 30, 45, 60, 90):
    y = HY + int(HS * math.sin(math.radians(v)))
    a(y, 15, 'PIXEL', y, 16, 'PIXEL', y, 17, 'PIXEL', y - 2, 2, v, 'XEQ "PTNS"')
for c in (20, 51, 82, 113, 145, 176, 207, 238, 270, 301, 332, 363, 395):
    a(HY - 1, c, 'PIXEL', HY - 2, c, 'PIXEL')
xs = (19, 112, 206, 300, 394)
a('0', 'STO 44', 'RCL 11', 'X<0?', 'GTO 24')
for x, l in zip(xs, 'NESWN'): a(HY - 8, x, '"%s"' % l, 'XEQ "PTXT"')
a('GTO 25', 'LBL 24', '180', 'STO 44')
for x, l in zip(xs, 'SWNES'): a(HY - 8, x, '"%s"' % l, 'XEQ "PTXT"')
a('LBL 25')
a('0', '6', 'XEQ "HCZQ"', '0', 'STO 47', 'LBL 58', 'XEQ 51', 'RCL 96', '1E-4', 'X<Y?', 'XEQ 56', '6', 'STO+ 47', '354', 'RCL 47', 'X≤Y?', 'GTO 58')   # equator: a dot every 6 deg (speed)
a('RCL 15', 'RCL 14', 'XEQ 55', 'RCL 96', 'X>0?', 'XEQ 60')       # the body on the chart
# data below: symbol + name | GHA DEC | HC ZN | SHA ARIES / SD / HP SD
a('RCL 13', 'XEQ 38', 'STO 26', '62', '2', 'RCL 26', 'XEQ "PTXS"', 'RCL 13', 'XEQ 47', 'STO 26', '62', '20', 'RCL 26', 'XEQ "PTXS"')
txt(47, 2, 'GHA'); a(47, 40, 'RCL 14', 'XEQ "PDMS"')
txt(47, 184, 'DEC'); a('"N"', 'STO 26', 'RCL 15', 'X<0?', 'XEQ 99'); a(47, 220, 'RCL 26', 'XEQ "PTXS"'); a(47, 222, 'RCL 15', 'ABS', 'XEQ "PDMS"')
txt(33, 2, 'HC'); a(33, 40, 'RCL 18', 'XEQ "PDMS"')
txt(33, 184, 'ZN'); a(33, 230, 'RCL 19', 'XEQ "PZNS"')
a('RCL 13', '60', 'X>Y?', 'GTO 26', 'X=Y?', 'GTO 27', '61', 'RCL 13', 'X=Y?', 'GTO 28')
a('LBL 26'); txt(19, 2, 'SHA'); a(19, 40, 'RCL 16', 'XEQ "PDMS"'); txt(19, 184, 'ARIES'); a(19, 232, 'RCL 80', 'XEQ "PDMS"'); a('GTO 29')
a('LBL 27'); txt(19, 2, 'SD'); a(19, 40, 'RCL 17', 'XEQ "PF1S"'); txt(19, 184, 'ARIES'); a(19, 232, 'RCL 80', 'XEQ "PDMS"'); a('GTO 29')
a('LBL 28'); txt(19, 2, 'HP'); a(19, 40, 'RCL 16', 'XEQ "PF1S"'); txt(19, 184, 'SD'); a(19, 230, 'RCL 17', 'XEQ "PF1S"')
a('LBL 29')
a(2, 126, '"DOES NOT REPLACE THE NAUTICAL ALMANAC"', 'XEQ "PTXT"')
a('XEQ "WPLS"', 'GTO 04')                                      # hold until +, then the list again
# ---------------- subroutines: list
a('LBL 11', '60', 'XEQ 36', 'XEQ 40', 'RTN')
a('LBL 12', '61', 'XEQ 36', 'XEQ 40', 'RTN')
a('LBL 13', 'RCL 23', 'IP', '61', '+', 'XEQ 36', 'XEQ 40', 'RTN')
a('LBL 14', 'RCL 82', 'XEQ 36', 'XEQ 40', 'RTN')
# entry "NN NAME" for body code X
a('LBL 36', 'STO 24', 'XEQ "SINT"', '" "', '+', 'STO 26', 'RCL 24', 'XEQ 37', 'RCL 26', 'X<>Y', '+', 'RTN')
# name for body code X: stars SNMU, 60-65 LBL 30-35
a('LBL 37', '60', 'X<>Y', 'X<Y?', 'GTO "SNMU"', '30', '-', 'STO 24', 'GTO IND 24')
for lab, t in ((30, 'SUN'), (31, 'MOON'), (32, 'VENUS'), (33, 'MARS'), (34, 'JUPITER'), (35, 'SATURN')):
    a('LBL %d' % lab, '"%s"' % t, 'RTN')
# symbol for body code X: * star, @ Sun, ( Moon, < > = ? planets (LBL 50-55)
a('LBL 38', '60', 'X<>Y', 'X<Y?', 'GTO 39', '20', '+', 'STO 24', 'GTO IND 24', 'LBL 39', '"*"', 'RTN')
for lab, t in ((80, '@'), (81, '('), (82, '<'), (83, '>'), (84, '='), (85, '?')):
    a('LBL %d' % lab, '"%s"' % t, 'RTN')
# name as shown on the result: "18 SIRIUS" for stars, "SUN", "MOON", planet names
a('LBL 47', '60', 'X<>Y', 'X<Y?', 'GTO 36', 'GTO 37')
# add entry X to the page (R20, width R43, line R22); full page: PROMPT (LBL 45)
a('LBL 40', 'STO 26', 'STO 44', '0', 'STO 29', 'LBL 41', 'αLENG 44', 'X=0?', 'GTO 42', 'α→𝑥 44', 'XEQ "CWID"', 'STO+ 29', 'GTO 41',
  'LBL 42', 'RCL 43', 'X≠0?', 'GTO 43', 'RCL 26', 'STO 20', 'RCL 29', 'STO 43', '1', 'STO 22', 'RTN',
  'LBL 43', 'RCL 43', '16', '+', 'RCL+ 29', '400', 'X<>Y', 'X≤Y?', 'GTO 44',
  '2', 'RCL 22', 'X=Y?', 'GTO 46', '400', 'XEQ 89', '2', 'STO 22', 'RCL 26', 'XEQ 90', 'RCL 29', 'STO 43', 'RTN',
  'LBL 46', 'XEQ 45', 'RCL 26', 'STO 20', 'RCL 29', 'STO 43', '1', 'STO 22', 'RTN',
  'LBL 44', '"  "', 'XEQ 90', '16', 'STO+ 43', 'RCL 26', 'XEQ 90', 'RCL 29', 'STO+ 43', 'RTN')
a('LBL 45', '-1', 'PROMPT 20', 'STO 21', '0', 'STO 43', 'RTN')
# ---------------- subroutines: chart
a('LBL 51', 'XEQ "HCZR"', 'GTO 49')
a('LBL 55', 'XEQ "HCZ"', 'LBL 49', 'RCL 97', 'RCL+ 44', '360', 'MOD', '375', '×', '360', '÷', '20', '+', 'IP', 'STO 98',
  'RCL "SHC"', HS, '×', HY, '+', 'IP', 'STO 99', 'RTN')
a('LBL 56', 'RCL 99', 'RCL 98', 'PIXEL', 'RCL 99', 'RCL 98', '1', '+', 'PIXEL', 'RCL 99', '1', '+', 'RCL 98', 'PIXEL', 'RCL 99', '1', '+', 'RCL 98', '1', '+', 'PIXEL', 'RTN')          # equator dot: 2 x 2 pixels
a('LBL 60', 'RCL 13', '60', 'X=Y?', 'GTO 61', 'RCL 13', 'XEQ 38', 'STO 26', 'RCL 99', '6', '-', 'RCL 98', '6', '-', 'RCL 26', 'XEQ "PTXS"',
  'RCL 13', '59', 'X<Y?', 'RTN', 'RCL 98', '8', '+', 'STO 26', '380', 'RCL 26', 'X>Y?', 'XEQ 62',
  'RCL 99', '6', '-', 'RCL 26', 'RCL 13', 'XEQ "PINS"', 'RTN', 'LBL 62', '32', 'STO- 26', 'RTN',
  'LBL 61', 'RCL 99', '6', '-', 'RCL 98', '6', '-', '"@"', 'XEQ "PTXS"', 'RTN')
a('LBL 59', '"T"', 'STO 25', 'RTN', 'LBL 65', '"X"', 'STO 25', 'RTN')
a('LBL 99', '"S"', 'STO 26', 'RTN', 'LBL 98', '"W"', 'STO 26', 'RTN')
# ---------------- subroutines: text lines (as ALMT)
a('LBL 90', 'STO 27', 'RCL 20', 'RCL 27', '+', 'STO 20', 'RTN')
a('LBL 91', 'PROMPT 20', 'RTN')
a('LBL 76', 'STO+ 43', 'R↓', 'STO 27', 'αLENG 27', '8', '×', 'STO+ 43', 'RCL 27', 'XEQ 90', 'RTN')
a('LBL 68', 'STO 20', 'STO 44', '0', 'STO 43', 'LBL 67', 'αLENG 44', 'X=0?', 'RTN', 'α→𝑥 44', 'XEQ "CWID"', 'STO+ 43', 'GTO 67')
a('LBL 89', 'STO 28', 'LBL 73', 'RCL 43', '8', '+', 'RCL 28', 'X<Y?', 'RTN', '" "', 'XEQ 90', '8', 'STO+ 43', 'GTO 73')
a('LBL 94', 'STO 28', 'R↓', 'STO 27', 'LBL 97', 'αLENG 27', 'RCL 28', 'X≤Y?', 'GTO 96',
  '" "', 'RCL 27', '+', 'STO 27', 'GTO 97', 'LBL 96', 'RCL 27', 'RTN')
a('END')
open(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'programs', 'BODY.txt'), 'w').write('\n'.join(P) + '\n')
print(len(P), repr(LEG1P), pxw(LEG1P), pxw(LEG2))
