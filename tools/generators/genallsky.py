#!/usr/bin/env python3
"""genallsky.py - ALLSKY: the whole sky on one chart. The horizon runs across the middle:
upper half OVER HORIZON (Hc 0 to 90), lower half UNDER HORIZON (Hc 0 to -90), both with
the sine altitude scale; Zn across as on HORZ. Every body is drawn: Sun, Moon, planets
(big symbols) and all 58 stars (small star and number). Top line: date, UT and DAY /
TWILIGHT / NIGHT from the Sun's altitude (Sun above the horizon / above -12 deg / below).
IN: Z = JD (UT1), Y = lat (N+), X = lon (E+).
Sun SUNA, Moon MOO2, planets PLN3; stars from the catalogue with first-order precession
(within about 0.05 deg). Writes programs/ALLSKY.txt"""
import math, os
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
P = []
def a(*xs):
    for x in xs: P.extend(str(x).split('\n'))
HY, HS = 118, 100                     # horizon row, pixels for sin(Hc) = 1 (up and down)
a('LBL "ALLSKY"', 'STO 12', 'R↓', 'STO 11', 'R↓', 'STO 10')
a('RCL 11', 'STO 91', 'RCL 12', 'STO 92', 'XEQ "HCZI"', 'CLLCD')
a('0', 'STO 44', 'RCL 11', 'X<0?', 'XEQ 44')                        # south: chart centred on N
# chart: horizon (full width), Hc axis (dotted), altitude marks up and down, Zn ticks, letters
a('-%d' % HY, '0', 'PIXEL')
a('%d.%03d03' % (HY - HS, HY + HS), 'STO 26', 'LBL 08', 'RCL 26', 'IP', '18', 'PIXEL', 'ISG 26', 'GTO 08')
for v in (10, 20, 30, 45, 60, 90):
    dy = int(HS * math.sin(math.radians(v)))
    for y in (HY + dy, HY - dy):
        a(y, 15, 'PIXEL', y, 16, 'PIXEL', y, 17, 'PIXEL', y - 2, 2, v, 'XEQ "PTNS"')
for c in (20, 51, 82, 113, 145, 176, 207, 238, 270, 301, 332, 363, 395):
    a(HY - 1, c, 'PIXEL', HY - 2, c, 'PIXEL')
xs = (19, 112, 206, 300, 394)
a('RCL 44', 'X≠0?', 'GTO 09')
for x, l in zip(xs, 'NESWN'): a(HY - 8, x, '"%s"' % l, 'XEQ "PTXT"')
a('GTO 10', 'LBL 09')
for x, l in zip(xs, 'SWNES'): a(HY - 8, x, '"%s"' % l, 'XEQ "PTXT"')
a('LBL 10')
a(HY + HS + 1, 150, '"OVER HORIZON"', 'XEQ "PTXT"', 2, 150, '"UNDER HORIZON"', 'XEQ "PTXT"')
# Sun and Aries (SUNA), top line: date, UT
a('RCL 10', 'XEQ "SUNA"', 'STO 45', 'R↓', 'STO 46')
a(227, 2, 'RCL 10', 'XEQ "PDTS"', 227, 88, 'RCL 10', '0.5', '+', '1', 'MOD', '24', '×', 'XEQ "PHMS"', '" UT"', 'XEQ "PTXS"')
# celestial equator: a 2 x 2 dot every 3 deg of GHA, above and below the horizon
a('0', '3', 'XEQ "HCZQ"', '0', 'STO 47', 'LBL 13', 'XEQ "HCZR"', 'XEQ 48', 'XEQ 14',
  '3', 'STO+ 47', '357', 'RCL 47', 'X≤Y?', 'GTO 13')
# stars: catalogue + first-order precession, small star and number
a('RCL 10', '2451545', '-', '365.25', '÷', '3600', '÷', 'STO 26', '1.058', 'STO 42',
  'LBL 20', 'INDEX "ST"', 'RCL 42', 'IP', '1', 'STOIJ', 'RCLEL', 'STO 22', 'J+', 'RCLEL', 'STO 23',
  'RCL 22', 'COS', '20.0431', '×', 'RCL× 26', 'RCL+ 23',
  'RCL 22', 'SIN', 'RCL 23', 'TAN', '×', '20.0431', '×', '46.1244', '+', 'RCL× 26', 'RCL+ 22', 'RCL 80', 'X<>Y', '-', '360', 'MOD',
  'XEQ "HCZ"', 'XEQ 48', 'XEQ 15', 'ISG 42', 'GTO 20')
# planets (PLN3), Moon (MOO2), Sun last (on top): big symbols
a('1.004', 'STO 42', 'LBL 21', 'RCL 42', 'IP', 'XEQ "PLN3"', 'XEQ "HCZ"', 'XEQ 48', 'RCL 42', 'IP', '70', '+', 'STO 43', 'XEQ 16', 'ISG 42', 'GTO 21')
a('XEQ "MOO2"', 'XEQ "HCZ"', 'XEQ 48', '62', 'STO 43', 'XEQ 16')
a('RCL 46', 'RCL 45', 'XEQ "HCZ"', 'STO 27', 'XEQ 48', '61', 'STO 43', 'XEQ 16')
# DAY (Sun above the horizon), TWILIGHT (above -12 deg), NIGHT
a('"NIGHT"', 'STO 43', '-12', 'RCL 27', 'X>Y?', 'XEQ 22', 'RCL 27', 'X>0?', 'XEQ 23', 227, 300, 'RCL 43', 'XEQ "PTXS"')
a('XEQ "WPLS"', 'RTN')                                         # hold until + (back to the menu)
# ---------------- subroutines
a('LBL 44', '180', 'STO 44', 'RTN')
a('LBL 22', '"TWILIGHT"', 'STO 43', 'RTN', 'LBL 23', '"DAY"', 'STO 43', 'RTN')
# LBL 48: chart column R98 = IP(((Zn + R44) MOD 360) * 375/360 + 20), row R99 = IP(sin(Hc) * 100 + 118)
a('LBL 48', 'RCL 97', 'RCL+ 44', '360', 'MOD', '375', '×', '360', '÷', '20', '+', 'IP', 'STO 98',
  'RCL "SHC"', HS, '×', HY, '+', 'IP', 'STO 99', 'RTN')
# LBL 14: equator dot, 2 x 2 pixels
a('LBL 14', 'RCL 99', 'RCL 98', 'PIXEL', 'RCL 99', 'RCL 98', '1', '+', 'PIXEL', 'RCL 99', '1', '+', 'RCL 98', 'PIXEL',
  'RCL 99', '1', '+', 'RCL 98', '1', '+', 'PIXEL', 'RTN')
# LBL 15: star R42 (small font): star centred, number to the right (left near the edge)
a('LBL 15', 'RCL 99', '2', '-', 'RCL 98', '2', '-', '"*"', 'XEQ "PTXT"', 'RCL 98', '5', '+', 'STO 28', '388', 'RCL 28', 'X>Y?', 'XEQ 17',
  'RCL 99', '2', '-', 'RCL 28', 'RCL 42', 'IP', 'XEQ "PTNS"', 'RTN', 'LBL 17', '17', 'STO- 28', 'RTN')
# LBL 16: body symbol (label R43) centred, big font
a('LBL 16', 'RCL 99', '6', '-', 'RCL 98', '6', '-', 'XEQ IND 43', 'XEQ "PTXS"', 'RTN')
for lab, t in ((61, '@'), (62, '('), (71, '<'), (72, '>'), (73, '='), (74, '?')):
    a('LBL %d' % lab, '"%s"' % t, 'RTN')
a('END')
open(os.path.join(ROOT, 'programs', 'ALLSKY.txt'), 'w').write('\n'.join(P) + '\n')
print(len(P))
