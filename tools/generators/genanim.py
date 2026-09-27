#!/usr/bin/env python3
"""genanim.py - HANIM: animation of the bodies on the horizon chart (as HORZ: sine altitude
scale, status-bar font). IN: Z = JD (UT1), Y = lat (N+), X = lon (E+).

  frames  R14 = 12      one frame per step, PAUSE 10 (1 s) after each frame
  step    R15 = 1       hours between frames
  (edit the lines "12 STO 14", "1 STO 15" and "PAUSE 10" in the program to change them)

Speed: the Sun, Moon and planets are calculated only twice, for the first and the last
frame (quick formulas: SUNF, MOOQ, PLNQ, within about 0.3 deg), and their SHA and Dec
interpolated in between; GHA Aries is exact for every frame. Stars: catalogue positions
(no precession, about 0.4 deg - under one chart pixel). The celestial equator does not
move on the chart: its dots are calculated once and kept in the matrix EQP.
Every frame shows only the bodies above the horizon: Sun, Moon and planets, then the
brightest stars until 10 bodies. Top line: date and UT of the frame, frame number.
Writes programs/HANIM.txt"""
import math, os
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
P = []
def a(*xs):
    for x in xs: P.extend(str(x).split('\n'))
HY, HS = 16, 196
a('LBL "HANIM"', 'STO 12', 'R↓', 'STO 11', 'R↓', 'STO 10')
a('12', 'STO 14', '1', 'STO 15')                                  # frames, hours per frame
a('RCL 11', 'STO 91', 'RCL 12', 'STO 92', 'XEQ "HCZI"', '-1', 'STO "PQK"')   # PQK: PLNQ Earth cache (normally set by SUNA)
a('0', 'STO 44', 'RCL 11', 'X<0?', 'XEQ 44')                        # south: chart centred on N
# Sun, Moon, planets at the first and the last frame: matrix ANB [SHA0 DEC0 SHA1 DEC1]
a('6', 'ENTER', '4', 'NEWMAT', 'STO "ANB"', '10', 'ENTER', '3', 'NEWMAT', 'STO "ANP"')
a('RCL 10', 'STO 17', '1', 'STO 20', 'XEQ 70')
a('RCL 14', '1', '-', 'RCL× 15', '24', '÷', 'RCL+ 10', 'STO 17', '3', 'STO 20', 'XEQ 70')
# celestial equator: dots every 2 deg of GHA, chart positions kept in EQP (fixed on the chart)
a('180', 'ENTER', '2', 'NEWMAT', 'STO "EQP"', '0', 'STO 29')
a('0', '2', 'XEQ "HCZQ"', '0', 'STO 47', 'LBL 13', 'XEQ "HCZR"', 'XEQ 48', 'RCL 96', '1E-4', 'X<Y?', 'XEQ 14',
  '2', 'STO+ 47', '358', 'RCL 47', 'X≤Y?', 'GTO 13')
# ---------------- frames
a('0', 'STO 13')
a('LBL 01', 'RCL 13', 'RCL× 15', '24', '÷', 'RCL+ 10', 'STO 17', 'XEQ 71')
a('RCL 13', 'RCL 14', '1', '-', '÷', 'STO 18', '0', 'STO 19')
# 1. positions first (the screen still shows the last frame): ANP rows [row, column, code]
#    code 61-66 Sun Moon Venus Mars Jupiter Saturn, 1-58 star number
a('1.006', 'STO 21', 'LBL 02', 'INDEX "ANB"', 'RCL 21', 'IP', '1', 'STOIJ', 'RCLEL', 'STO 22', 'J+', 'RCLEL', 'STO 23', 'J+',
  'RCLEL', 'RCL- 22', '540', '+', '360', 'MOD', '180', '-', 'RCL× 18', 'RCL+ 22', 'STO 24', 'J+',
  'RCLEL', 'RCL- 23', 'RCL× 18', 'RCL+ 23', 'RCL 80', 'RCL+ 24', '360', 'MOD', 'XEQ "HCZ"', 'XEQ 48',
  'RCL 96', 'X>0?', 'XEQ 03', 'ISG 21', 'GTO 02')
a('1.058', 'STO 42', 'LBL 04', '10', 'RCL 19', 'X≥Y?', 'GTO 05', 'RCL 42', 'IP', 'XEQ "SBRT"', 'STO 82', 'XEQ "SQK"',
  '0', 'X≥Y?', 'GTO 06', 'INDEX "ST"', 'RCL 82', '1', 'STOIJ', 'RCLEL', 'J+', 'RCLEL', 'X<>Y', 'RCL 80', 'X<>Y', '-',
  'XEQ "HCZ"', 'XEQ 48', 'RCL 82', 'XEQ 16', 'LBL 06', 'ISG 42', 'GTO 04', 'LBL 05')
# 2. draw: background, top line, the bodies
a('CLLCD', 'XEQ 72')
a(227, 2, 'RCL 17', 'XEQ "PDTS"', 227, 88, 'RCL 17', '0.5', '+', '1', 'MOD', '24', '×', 'XEQ "PHMS"', '" UT"', 'XEQ "PTXS"')
a(227, 330, 'RCL 13', '1', '+', 'XEQ "PINS"', '"/"', 'XEQ "PTXS"', 'RCL 14', 'XEQ "PINS"')
a('RCL 19', 'X=0?', 'GTO 07', 'STO 21', 'INDEX "ANP"', '1', '1', 'STOIJ',
  'LBL 12', 'RCLEL', 'STO 99', 'J+', 'RCLEL', 'STO 98', 'J+', 'RCLEL', 'STO 43', 'J+', 'XEQ 17', 'DSE 21', 'GTO 12', 'LBL 07')
a('PAUSE 10')                                                       # frame time: 10 = 1 s
a('1', 'STO+ 13', 'RCL 14', 'RCL 13', 'X<Y?', 'GTO 01')
a('PAUSE 99', 'RTN')                                                # hold the last frame
# ---------------- subroutines
a('LBL 44', '180', 'STO 44', 'RTN')
# LBL 70: Sun, Moon, planets at JD R17 into ANB columns R20, R20+1 (SHA, Dec)
a('LBL 70', 'XEQ 71', 'RCL 17', 'XEQ "SUNF"', '1', 'XEQ 73', 'XEQ "MOOQ"', '2', 'XEQ 73',
  '1.004', 'STO 21', 'LBL 74', 'RCL 21', 'IP', 'XEQ "PLNQ"', 'RCL 21', 'IP', '2', '+', 'XEQ 73', 'ISG 21', 'GTO 74', 'RTN')
# LBL 73: X = row, Y = GHA, Z = Dec -> ANB(row, R20) = SHA, (row, R20+1) = Dec
a('LBL 73', 'STO 25', 'R↓', 'RCL- 80', '360', 'MOD', 'STO 26', 'R↓', 'STO 27',
  'INDEX "ANB"', 'RCL 25', 'RCL 20', 'STOIJ', 'RCL 26', 'STOEL', 'J+', 'RCL 27', 'STOEL', 'RTN')
# LBL 71: time of JD R17 for MOOQ / PLNQ / SQK: R54 = T (centuries TT), R80 = GHA Aries (mean)
a('LBL 71', 'RCL 17', '2451545', '-', 'STO 25', '0.000800925925925926', '+', '36525', '÷', 'STO 54',
  'RCL 25', '360.98564736629', '×', '280.46061837', '+', '360', 'MOD', 'STO 80', 'RTN')
# LBL 72: chart background: horizon, Hc axis, altitude marks (sine scale), Zn ticks, letters, equator
a('LBL 72', '-%d' % HY, '0', 'PIXEL')                                # horizon: full-width line
a('18.21203', 'STO 26', 'LBL 08', 'RCL 26', 'IP', '18', 'PIXEL', 'ISG 26', 'GTO 08')
for v in (10, 20, 30, 45, 60, 90):
    y = HY + int(HS * math.sin(math.radians(v)))
    a(y, 15, 'PIXEL', y, 16, 'PIXEL', y, 17, 'PIXEL', y - 2, 2, v, 'XEQ "PTNS"')
for c in (20, 51, 82, 113, 145, 176, 207, 238, 270, 301, 332, 363, 395):
    a(15, c, 'PIXEL', 14, c, 'PIXEL', 13, c, 'PIXEL')
xs = (19, 112, 206, 300, 394)
a('RCL 44', 'X≠0?', 'GTO 09')
for x, l in zip(xs, 'NESWN'): a(7, x, '"%s"' % l, 'XEQ "PTXT"')
a('GTO 10', 'LBL 09')
for x, l in zip(xs, 'SWNES'): a(7, x, '"%s"' % l, 'XEQ "PTXT"')
a('LBL 10', 'RCL 29', 'X=0?', 'RTN', 'STO 27', 'INDEX "EQP"', '1', '1', 'STOIJ',
  'LBL 11', 'RCLEL', 'STO 28', 'J+', 'RCLEL', 'STO 26', 'J+',
  'RCL 28', 'RCL 26', 'PIXEL', 'RCL 28', 'RCL 26', '1', '+', 'PIXEL', 'RCL 28', '1', '+', 'RCL 26', 'PIXEL',
  'RCL 28', '1', '+', 'RCL 26', '1', '+', 'PIXEL', 'DSE 27', 'GTO 11', 'RTN')
# LBL 14: keep an equator dot (R99 row, R98 column) in EQP
a('LBL 14', '1', 'STO+ 29', 'INDEX "EQP"', 'RCL 29', '1', 'STOIJ', 'RCL 99', 'STOEL', 'J+', 'RCL 98', 'STOEL', 'RTN')
# LBL 48: chart column R98 = IP(((Zn + R44) MOD 360) * 375/360 + 20), row R99 = IP(sin(Hc) * 196 + 16)
a('LBL 48', 'RCL 97', 'RCL+ 44', '360', 'MOD', '375', '×', '360', '÷', '20', '+', 'IP', 'STO 98',
  'RCL "SHC"', HS, '×', HY, '+', 'IP', 'STO 99', 'RTN')
# LBL 03: record body R21 (1 Sun, 2 Moon, 3-6 Venus Mars Jupiter Saturn): code 60 + R21
a('LBL 03', 'RCL 21', 'IP', '60', '+')
# LBL 16: record code X at row R99, column R98 (ANP row R19 + 1)
a('LBL 16', 'STO 43', '1', 'STO+ 19', 'INDEX "ANP"', 'RCL 19', '1', 'STOIJ', 'RCL 99', 'STOEL', 'J+', 'RCL 98', 'STOEL', 'J+', 'RCL 43', 'STOEL', 'RTN')
# LBL 17: draw code R43 at R99, R98: symbol centred; stars with their number (left near the edge)
a('LBL 17', '60', 'RCL 43', 'X>Y?', 'GTO 18', 'RCL 99', '6', '-', 'RCL 98', '6', '-', '"*"', 'XEQ "PTXS"', 'RCL 98', '8', '+', 'STO 26', '380', 'RCL 26', 'X>Y?', 'XEQ 15',
  'RCL 99', '6', '-', 'RCL 26', 'RCL 43', 'XEQ "PINS"', 'RTN', 'LBL 15', '32', 'STO- 26', 'RTN',
  'LBL 18', 'RCL 99', '6', '-', 'RCL 98', '6', '-', 'XEQ IND 43', 'XEQ "PTXS"', 'RTN')
for lab, t in ((61, '@'), (62, '('), (63, '<'), (64, '>'), (65, '='), (66, '?')):
    a('LBL %d' % lab, '"%s"' % t, 'RTN')
a('END')
open(os.path.join(ROOT, 'programs', 'HANIM.txt'), 'w').write('\n'.join(P) + '\n')
print(len(P))
