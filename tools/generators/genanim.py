#!/usr/bin/env python3
"""genanim.py - HANIM: animation of the Sun and the Moon on the whole-sky chart of ALLSKY:
horizon across the middle, OVER HORIZON above, UNDER HORIZON below (sine altitude scale
both ways), status-bar font. IN: Z = JD (UT1), Y = lat (N+), X = lon (E+).

  frames  R14 = 24      one frame per step, PAUSE 10 (1 s) after each frame
  step    R15 = 0.5     hours between frames
  (edit the lines "24 STO 14", "0.5 STO 15" and "PAUSE 10" in the program to change them)

Every frame: Sun (SUNF) and Moon (MOOQ, geocentric) calculated for its own time, GHA Aries
exact; both drawn above or below the horizon. The chart is drawn once and the screen is not
cleared: every frame adds the Sun and the Moon, so their paths build up (trail), through
setting and rising. Only the top line is cleared and rewritten: date and UT of the frame,
frame number, DAY / TWILIGHT / NIGHT from the Sun's altitude. No matrices.
Writes programs/HANIM.txt"""
import math, os
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
P = []
def a(*xs):
    for x in xs: P.extend(str(x).split('\n'))
HY, HS = 118, 100                     # horizon row, pixels for sin(Hc) = 1 (up and down)
a('LBL "HANIM"', 'STO 12', 'R↓', 'STO 11', 'R↓', 'STO 10')
a('24', 'STO 14', '0.5', 'STO 15')                                 # frames, hours per frame
a('RCL 11', 'STO 91', 'RCL 12', 'STO 92', 'XEQ "HCZI"')
a('0', 'STO 44', 'RCL 11', 'X<0?', 'XEQ 44')                        # south: chart centred on N
a('CLLCD', 'XEQ 72')                                                # chart drawn once
# celestial equator: a 2 x 2 dot every 2 deg of GHA, above and below the horizon
a('0', '2', 'XEQ "HCZQ"', '0', 'STO 47', 'LBL 13', 'XEQ "HCZR"', 'XEQ 48', 'XEQ 14',
  '2', 'STO+ 47', '358', 'RCL 47', 'X≤Y?', 'GTO 13')
a('0', 'STO 13')
a('LBL 01', 'RCL 13', 'RCL× 15', '24', '÷', 'RCL+ 10', 'STO 17', 'XEQ 71')
# 1. positions first (the screen still shows the last frame): Sun R20 R21 (Hc R27), Moon R22 R23
a('RCL 17', 'XEQ "SUNF"', 'XEQ "HCZ"', 'STO 27', 'XEQ 48', 'RCL 99', 'STO 20', 'RCL 98', 'STO 21')
a('XEQ "MOOQ"', 'XEQ "HCZ"', 'XEQ 48', 'RCL 99', 'STO 22', 'RCL 98', 'STO 23')
a('"NIGHT"', 'STO 43', '-12', 'RCL 27', 'X>Y?', 'XEQ 02', 'RCL 27', 'X>0?', 'XEQ 03')
# 2. draw: top line, then the Sun and Moon over the earlier frames
a('224', '0', 'CLLCDxy')                                            # clear only the top line; the Sun and Moon stay (trail)
a(227, 2, 'RCL 17', 'XEQ "PDTS"', 227, 88, 'RCL 17', '0.5', '+', '1', 'MOD', '24', '×', 'XEQ "PHMS"', '" UT"', 'XEQ "PTXS"')
a(227, 200, 'RCL 13', '1', '+', 'XEQ "PINS"', '"/"', 'XEQ "PTXS"', 'RCL 14', 'XEQ "PINS"')
a(227, 300, 'RCL 43', 'XEQ "PTXS"')
a('RCL 20', '6', '-', 'RCL 21', '6', '-', '"@"', 'XEQ "PTXS"', 'RCL 22', '6', '-', 'RCL 23', '6', '-', '"("', 'XEQ "PTXS"')
a('PAUSE 10')                                                       # frame time: 10 = 1 s
a('1', 'STO+ 13', 'RCL 14', 'RCL 13', 'X<Y?', 'GTO 01')
a('PAUSE 99', 'RTN')                                                # hold the last frame
# ---------------- subroutines
a('LBL 44', '180', 'STO 44', 'RTN')
a('LBL 02', '"TWILIGHT"', 'STO 43', 'RTN', 'LBL 03', '"DAY"', 'STO 43', 'RTN')
# LBL 71: time of JD R17 for MOOQ: R54 = T (centuries TT), R80 = GHA Aries (mean)
a('LBL 71', 'RCL 17', '2451545', '-', 'STO 25', '0.000800925925925926', '+', '36525', '÷', 'STO 54',
  'RCL 25', '360.98564736629', '×', '280.46061837', '+', '360', 'MOD', 'STO 80', 'RTN')
# LBL 72: chart as ALLSKY: horizon (full width), Hc axis (dotted), altitude marks up and down,
# Zn ticks, letters, OVER HORIZON / UNDER HORIZON
a('LBL 72', '-%d' % HY, '0', 'PIXEL')
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
a('LBL 10', HY + HS + 1, 150, '"OVER HORIZON"', 'XEQ "PTXT"', 2, 150, '"UNDER HORIZON"', 'XEQ "PTXT"', 'RTN')
# LBL 14: equator dot, 2 x 2 pixels at R99, R98
a('LBL 14', 'RCL 99', 'RCL 98', 'PIXEL', 'RCL 99', 'RCL 98', '1', '+', 'PIXEL', 'RCL 99', '1', '+', 'RCL 98', 'PIXEL',
  'RCL 99', '1', '+', 'RCL 98', '1', '+', 'PIXEL', 'RTN')
# LBL 48: chart column R98 = IP(((Zn + R44) MOD 360) * 375/360 + 20), row R99 = IP(sin(Hc) * 100 + 118)
a('LBL 48', 'RCL 97', 'RCL+ 44', '360', 'MOD', '375', '×', '360', '÷', '20', '+', 'IP', 'STO 98',
  'RCL "SHC"', HS, '×', HY, '+', 'IP', 'STO 99', 'RTN')
a('END')
open(os.path.join(ROOT, 'programs', 'HANIM.txt'), 'w').write('\n'.join(P) + '\n')
print(len(P))
