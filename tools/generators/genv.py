#!/usr/bin/env python3
"""genv.py - HALMV: horizon chart on the left (sine altitude scale), panel on the right in
the status-bar font (PTXS): date, UT, DR, ARIES, then symbol + star number, HC, ZN for
the 10 bodies of ALMF (Sun always, Moon and planets above the horizon, brightest stars
higher than 10 deg), and the Moon phase. Writes programs/HALMV.txt"""
import math, os
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
P = []
def a(*xs):
    for x in xs: P.extend(str(x).split('\n'))
def txt(y, x, s): a(y, x, '"%s"' % s, 'XEQ "PTXS"')
X0 = 204                      # panel
HY, HS = 14, 200              # chart: horizon row, pixels for sin(Hc) = 1
a('LBL "HALMV"', 'STO 12', 'R↓', 'STO 11', 'R↓', 'STO 10')
a('RCL 10', 'STO 90', 'RCL 11', 'STO 91', 'RCL 12', 'STO 92', 'XEQ "HCZI"', 'CLLCD')
a('0', '-201', 'PIXEL')                                             # divider
a(HY, '18', '179', 'XEQ "PHLS"')                                    # horizon x 18..196
a('%d.%03d' % (HY, HY + HS), 'STO 47', 'LBL 12', 'RCL 47', 'IP', '17', 'PIXEL', 'ISG 47', 'GTO 12')
for v in (10, 20, 30, 45, 60, 90):                                  # altitude marks, sine scale
    y = HY + int(HS * math.sin(math.radians(v)))
    a(y, 15, 'PIXEL', y, 16, 'PIXEL', y - 2, 2, v, 'XEQ "PTNS"')
xs = [16, 60, 105, 149, 192]
a('0', 'STO 44', 'RCL 11', 'X<0?', 'GTO 23')
for x, l in zip(xs, 'NESWN'): a(5, x, '"%s"' % l, 'XEQ "PTXT"')
a('GTO 24', 'LBL 23', '180', 'STO 44')
for x, l in zip(xs, 'SWNES'): a(5, x, '"%s"' % l, 'XEQ "PTXT"')
a('LBL 24')
a('RCL 10', 'XEQ "SUNA"', 'STO 45', 'R↓', 'STO 46', 'R↓', 'STO 48')
a('XEQ "PHA2"', 'STO 18', 'X<>Y', 'STO 19')                         # Moon phase from the SUNA just run
# equator
a('0', '3', 'XEQ "HCZQ"', '0', 'STO 47', 'LBL 14', 'XEQ 51', 'RCL 96', '1E-4', 'X<Y?', 'XEQ 15', '3', 'STO+ 47', '357', 'RCL 47', 'X≤Y?', 'GTO 14')
# panel: date UT | DR | ARIES | titles
a(226, X0, 'RCL 10', 'XEQ "PDTS"')
a(226, X0 + 88, 'RCL 10', '0.5', '+', '1', 'MOD', '24', '×', 'XEQ "PHMS"'); txt(226, X0 + 129, 'UT')
a('"N"', 'STO 43', 'RCL 11', 'X<0?', 'XEQ 22'); a(212, X0, 'RCL 43', 'XEQ "PTXS"'); a(212, X0 + 2, 'RCL 11', 'ABS', 'XEQ "PDMS"')
a('"E"', 'STO 43', 'RCL 12', 'X<0?', 'XEQ 27'); a(212, X0 + 78, 'RCL 43', 'XEQ "PTXS"'); a(212, X0 + 80, 'RCL 12', 'ABS', 'XEQ "PDMS"')
txt(198, X0, 'ARIES'); a(198, X0 + 56, 'RCL 48', 'XEQ "PDMS"')
txt(184, X0 + 80, 'HC'); txt(184, X0 + 126, 'ZN')
a('170', 'STO 40')
a('RCL 46', 'RCL 45', 'XEQ 52', 'RCL 96', 'X>0?', 'XEQ 16')
a('RCL 40', X0, '"@"', 'XEQ "PTXS"', 'XEQ 60')
a('1', 'STO 41')
# Moon, if above the horizon
a('XEQ "MOO2"', 'STO 45', 'R↓', 'STO 46', 'RCL 46', 'RCL 45', 'XEQ 52', 'RCL 96', 'X>0?', 'XEQ 61')
# planets above the horizon
a('1.004', 'STO 42', 'LBL 62', 'RCL 42', 'IP', 'XEQ "PLN3"', 'STO 45', 'X<>Y', 'STO 46', 'RCL 46', 'RCL 45', 'XEQ 52', 'RCL 96', 'X>0?', 'XEQ 63', 'ISG 42', 'GTO 62')
# brightest stars higher than 10 deg until 10 bodies
a('1.058', 'STO 42', 'LBL 17', '10', 'RCL 41', 'X≥Y?', 'GTO 19', 'RCL 42', 'IP', 'XEQ "SBRT"', 'STO 82', 'XEQ "SQK"', '0.15643', 'X>Y?', 'GTO 18',
  'XEQ "STR2"', 'STO 45', 'X<>Y', 'STO 46', 'RCL 46', 'RCL 45', 'XEQ 52', '10', 'RCL 96', 'X≤Y?', 'GTO 18',
  'XEQ 57', 'RCL 40', X0, '"*"', 'XEQ "PTXS"', 'RCL 40', X0 + 16, 'RCL 82', 'XEQ "PINS"', 'XEQ 60',
  '1', 'STO+ 41', 'LBL 18', 'ISG 42', 'GTO 17', 'LBL 19')
# Moon phase
a('"WAXING"', 'STO 43', 'RCL 19', '14.765', 'X<Y?', 'XEQ 28', 'RCL 18', '99.5', 'X≤Y?', 'XEQ 25', 'RCL 18', '0.5', 'X>Y?', 'XEQ 30')
a(24, X0, '"MOON "', 'XEQ "PTXS"', 'RCL 18', 'XEQ "PINS"', '"% "', 'XEQ "PTXS"', 'RCL 43', 'XEQ "PTXS"')
# T tables / S series / X outside the FAST period (flag 11 is set by MOO2: draw last)
a('"S"', 'STO 43', 'FS? 11', 'XEQ 29', 'FS? 12', 'XEQ 65', 226, 388, 'RCL 43', 'XEQ "PTXS"')
a(8, X0 + 24, '"DOES NOT REPLACE THE NAUTICAL ALMANAC"', 'XEQ "PTXT"')
a('3', 'STO 37', 'LBL 20', 'PAUSE 99', 'DSE 37', 'GTO 20', 'RTN')
# subroutines
a('LBL 29', '"T"', 'STO 43', 'RTN', 'LBL 65', '"X"', 'STO 43', 'RTN')
a('LBL 25', '"FULL"', 'STO 43', 'RTN', 'LBL 30', '"NEW"', 'STO 43', 'RTN')
a('LBL 28', '"WANING"', 'STO 43', 'RTN', 'LBL 22', '"S"', 'STO 43', 'RTN', 'LBL 27', '"W"', 'STO 43', 'RTN')
a('LBL 15', 'RCL 99', 'RCL 98', 'PIXEL', 'RCL 99', 'RCL 98', '1', '+', 'PIXEL', 'RCL 99', '1', '+', 'RCL 98', 'PIXEL', 'RCL 99', '1', '+', 'RCL 98', '1', '+', 'PIXEL', 'RTN')          # equator dot: 2 x 2 pixels
a('LBL 16', 'RCL 99', '6', '-', 'RCL 98', '6', '-', '"@"', 'XEQ "PTXS"', 'RTN')
# chart column R98 = IP(((Zn + R44) MOD 360) * 178/360 + 18), row R99 = IP(sin(Hc) * 200 + 14)
a('LBL 51', 'XEQ "HCZR"', 'GTO 49')
a('LBL 52', 'XEQ "HCZ"', 'LBL 49', 'RCL 97', 'RCL+ 44', '360', 'MOD', '178', '×', '360', '÷', '18', '+', 'IP', 'STO 98',
  'RCL "SHC"', HS, '×', HY, '+', 'IP', 'STO 99', 'RTN')
a('LBL 57', 'RCL 99', '6', '-', 'RCL 98', '6', '-', '"*"', 'XEQ "PTXS"', 'RCL 98', '8', '+', 'STO 43', '180', 'RCL 43', 'X>Y?', 'XEQ 21',
  'RCL 99', '6', '-', 'RCL 43', 'RCL 82', 'XEQ "PINS"', 'RTN', 'LBL 21', '32', 'STO- 43', 'RTN')
a('LBL 60', 'RCL 40', X0 + 44, 'RCL 96', 'XEQ "PDMS"', 'RCL 40', X0 + 120, 'RCL 97', 'XEQ "PZNS"', 'RCL 96', 'X<0?', 'XEQ 64', '14', 'STO- 40', 'RTN')
a('LBL 64', 'RCL 40', '5', '+', X0 + 52, '64', 'XEQ "PHLS"', 'RTN')             # below the horizon: struck through
a('LBL 61', 'RCL 99', '6', '-', 'RCL 98', '6', '-', '"("', 'XEQ "PTXS"', 'RCL 40', X0, '"("', 'XEQ "PTXS"', 'XEQ 60', '1', 'STO+ 41', 'RTN')
a('LBL 63', 'RCL 42', 'IP', '70', '+', 'STO 43', 'RCL 99', '6', '-', 'RCL 98', '6', '-', 'XEQ IND 43', 'XEQ "PTXS"',
  'RCL 40', X0, 'XEQ IND 43', 'XEQ "PTXS"', 'XEQ 60', '1', 'STO+ 41', 'RTN')
for lab, t in ((71, '<'), (72, '>'), (73, '='), (74, '?')): a('LBL %d' % lab, '"%s"' % t, 'RTN')
a('END')
open(os.path.join(ROOT, 'programs', 'HALMV.txt'), 'w').write('\n'.join(P) + '\n')
print(len(P))
