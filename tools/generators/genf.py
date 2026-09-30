#!/usr/bin/env python3
"""genf.py - ALMF (and ALMS with 'short'): the almanac table in the C47 status-bar font
(PTXS, capitals 12 px, line pitch 14). ARIES is the first table row, then Sun, Moon (above
the horizon), planets above the horizon and the brightest stars higher than 10 deg:
10 rows in all, stars with their number. Sun and Moon data below the table, warning in
the small font.
ALMS (short): Sun, Moon, the first planet above the horizon in the order Venus, Jupiter,
Mars, Saturn, and the 3 brightest stars higher than 10 deg.
  python3 genf.py [short]      -> programs/ALMF.txt or programs/ALMS.txt"""
import os, sys
SHORT = len(sys.argv) > 1 and sys.argv[1] == 'short'
NAME = 'ALMS' if SHORT else 'ALMF'
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
P = []
def a(*xs):
    for x in xs: P.extend(str(x).split('\n'))
def txt(y, x, s): a(y, x, '"%s"' % s, 'XEQ "PTXS"')
def num(y, x, reg, fn): a(y, x, 'RCL %s' % reg, 'XEQ "%s"' % fn)
def hline(y): a('-%d' % y, '0', 'PIXEL')
NX, GX, DX, HX, ZX = 36, 128, 196, 262, 338   # name (star number at 17), GHA, DEC, HC, ZN
ROWS, TOP, PITCH = 10, 193, 14
a('LBL "%s"' % NAME, 'STO 12', 'R↓', 'STO 11', 'R↓', 'STO 10')
for reg, lab in ((13, 'NTWA'), (14, 'RISE'), (15, 'TRAN'), (16, 'SET'), (17, 'NTWP')):
    a('XEQ 26', 'XEQ "%s"' % lab, 'STO %d' % reg)
a('RCL 10', 'STO 90', 'RCL 11', 'STO 91', 'RCL 12', 'STO 92', 'XEQ "HCZI"', 'CLLCD')
a('RCL 10', 'XEQ "SUNA"', 'STO 45', 'R↓', 'STO 46', 'R↓', 'STO 48', 'RCL 73', '15.99383', 'X<>Y', '÷', 'STO 29')
a('XEQ "PHA2"', 'STO 18', 'X<>Y', 'STO 19')
# header: date, UT, DR, T/S/X
num(226, 2, 10, 'PDTS')
a(226, 80, 'RCL 10', '0.5', '+', '1', 'MOD', '24', '×', 'XEQ "PHMS"'); txt(226, 116, 'UT')
txt(226, 150, 'DR')
a('"N"', 'STO 43', 'RCL 11', 'X<0?', 'XEQ 22'); a(226, 174, 'RCL 43', 'XEQ "PTXS"'); a(226, 176, 'RCL 11', 'ABS', 'XEQ "PDMS"')
a('"E"', 'STO 43', 'RCL 12', 'X<0?', 'XEQ 27'); a(226, 244, 'RCL 43', 'XEQ "PTXS"'); a(226, 246, 'RCL 12', 'ABS', 'XEQ "PDMS"')
hline(221)
txt(207, NX, 'BODY'); txt(207, GX + 26, 'GHA'); txt(207, DX + 28, 'DEC'); txt(207, HX + 30, 'HC'); txt(207, ZX + 6, 'ZN')
# ARIES row (GHA only), then the Sun
a(TOP, NX, '"ARIES"', 'XEQ "PTXS"', TOP, GX, 'RCL 48', 'XEQ "PDMS"')
a('%d' % (TOP - PITCH), 'STO 40', 'RCL 46', 'RCL 45', 'XEQ "HCZ"')
a('RCL 40', '1', '"@"', 'XEQ "PTXS"', 'RCL 40', NX, '"SUN"', 'XEQ "PTXS"', 'XEQ 60')
a('2', 'STO 41')
# Moon, if above the horizon
a('XEQ "MOO2"', 'STO 45', 'R↓', 'STO 46', 'R↓', 'STO 21', 'R↓', 'STO 22', 'RCL 46', 'RCL 45', 'XEQ "HCZ"', 'RCL 96', 'X>0?', 'XEQ 61')
if SHORT:
    # the first planet above the horizon in the order Venus, Jupiter, Mars, Saturn (LBL 91-94)
    a('1.004', 'STO 24', 'LBL 16', 'RCL 24', 'IP', '90', '+', 'STO 43', 'XEQ IND 43', 'STO 42', 'XEQ "PLN3"', 'STO 45', 'X<>Y', 'STO 46', 'RCL 46', 'RCL 45', 'XEQ "HCZ"',
      'RCL 96', 'X>0?', 'GTO 15', 'ISG 24', 'GTO 16', 'GTO 14', 'LBL 15', 'XEQ 63', 'LBL 14')
    # the 3 brightest stars higher than 10 deg (count R24)
    a('0', 'STO 24', '1.058', 'STO 42', 'LBL 17', '3', 'RCL 24', 'X≥Y?', 'GTO 19', 'RCL 42', 'IP', 'XEQ "SBRT"', 'STO 82', 'XEQ "SQK"', '0.15643', 'X>Y?', 'GTO 18',
      'XEQ "STR2"', 'STO 45', 'X<>Y', 'STO 46', 'RCL 46', 'RCL 45', 'XEQ "HCZ"', '10', 'RCL 96', 'X≤Y?', 'GTO 18',
      'RCL 40', '1', '"*"', 'XEQ "PTXS"', 'RCL 40', '17', 'RCL 82', 'XEQ "PINS"', 'RCL 82', 'XEQ "SNMU"', 'STO 43', 'RCL 40', NX, 'RCL 43', 'XEQ "PTXS"', 'XEQ 60',
      '1', 'STO+ 41', '1', 'STO+ 24', 'LBL 18', 'ISG 42', 'GTO 17', 'LBL 19')
else:
    # planets above the horizon
    a('1.004', 'STO 42', 'LBL 16', 'RCL 42', 'IP', 'XEQ "PLN3"', 'STO 45', 'X<>Y', 'STO 46', 'RCL 46', 'RCL 45', 'XEQ "HCZ"', 'RCL 96', 'X>0?', 'XEQ 63', 'ISG 42', 'GTO 16')
    # brightest stars higher than 10 deg until the table has ROWS rows
    a('1.058', 'STO 42', 'LBL 17', ROWS, 'RCL 41', 'X≥Y?', 'GTO 19', 'RCL 42', 'IP', 'XEQ "SBRT"', 'STO 82', 'XEQ "SQK"', '0.15643', 'X>Y?', 'GTO 18',
      'XEQ "STR2"', 'STO 45', 'X<>Y', 'STO 46', 'RCL 46', 'RCL 45', 'XEQ "HCZ"', '10', 'RCL 96', 'X≤Y?', 'GTO 18',
      'RCL 40', '1', '"*"', 'XEQ "PTXS"', 'RCL 40', '17', 'RCL 82', 'XEQ "PINS"', 'RCL 82', 'XEQ "SNMU"', 'STO 43', 'RCL 40', NX, 'RCL 43', 'XEQ "PTXS"', 'XEQ 60',
      '1', 'STO+ 41', 'LBL 18', 'ISG 42', 'GTO 17', 'LBL 19')
FY = TOP - PITCH * ROWS          # 53: line under the table, then three lines
hline(FY + 8)
y1, y2, y3 = FY - 6, FY - 20, FY - 34
txt(y1, 2, 'NAUT TWI'); num(y1, 80, 13, 'PHMS'); num(y1, 118, 17, 'PHMS')
txt(y2, 2, 'RISE/SET'); num(y2, 80, 14, 'PHMS'); num(y2, 118, 16, 'PHMS')
txt(y3, 2, 'MER PASS'); num(y3, 80, 15, 'PHMS'); a(y3, 122, '"SD "', 'XEQ "PTXS"', 'RCL 29', 'XEQ "PF1S"')
a('"WAXING"', 'STO 43', 'RCL 19', '14.765', 'X<Y?', 'XEQ 28', 'RCL 18', '99.5', 'X≤Y?', 'XEQ 23', 'RCL 18', '0.5', 'X>Y?', 'XEQ 24')
a(y1, 196, '"MOON "', 'XEQ "PTXS"', 'RCL 18', 'XEQ "PINS"', '"% "', 'XEQ "PTXS"', 'RCL 43', 'XEQ "PTXS"')
a(y2, 196, '"AGE "', 'XEQ "PTXS"', 'RCL 19', 'XEQ "PF1S"', '" DAYS"', 'XEQ "PTXS"')
a(y3, 196, '"HP "', 'XEQ "PTXS"', 'RCL 21', 'XEQ "PF1S"', '" SD "', 'XEQ "PTXS"', 'RCL 22', 'XEQ "PF1S"')
# T tables / S series / X outside the FAST period (flag 11 is set by MOO2: draw last)
a('"S"', 'STO 43', 'FS? 11', 'XEQ 29', 'FS? 12', 'XEQ 65', 226, 388, 'RCL 43', 'XEQ "PTXS"')
a('XEQ "WPLS"', 'RTN')                                         # hold until + (back to the menu)
a('LBL 26', 'RCL 10', '0.5', '-', 'IP', '0.5', '+', 'RCL 11', 'RCL 12', 'RTN')
a('LBL 29', '"T"', 'STO 43', 'RTN', 'LBL 65', '"X"', 'STO 43', 'RTN')
a('LBL 23', '"FULL"', 'STO 43', 'RTN', 'LBL 24', '"NEW"', 'STO 43', 'RTN')
a('LBL 28', '"WANING"', 'STO 43', 'RTN', 'LBL 22', '"S"', 'STO 43', 'RTN', 'LBL 27', '"W"', 'STO 43', 'RTN')
a('LBL 60', 'RCL 40', GX, 'RCL 45', 'XEQ "PDMS"',
  '"N"', 'STO 43', 'RCL 46', 'X<0?', 'XEQ 22', 'RCL 40', DX, 'RCL 43', 'XEQ "PTXS"', 'RCL 40', DX + 2, 'RCL 46', 'ABS', 'XEQ "PDMS"',
  'RCL 40', HX, 'RCL 96', 'XEQ "PDMS"', 'RCL 40', ZX, 'RCL 97', 'XEQ "PZNS"', 'RCL 96', 'X<0?', 'XEQ 64', PITCH, 'STO- 40', 'RTN')
a('LBL 64', 'WSIZE 16', '3', 'STO 32', 'GRMOD 32', '11111111111111#2', 'STO 32', 'RCL 40', '1', '-', HX + 6, '55', 'STO 33', 'R↓',
  'LBL 66', 'AGRAPH 32', 'DSE 33', 'GTO 66', '0', 'STO 32', 'GRMOD 32', 'WSIZE 64', 'RTN')   # below the horizon: Hc inverted (XOR box)
a('LBL 61', 'RCL 40', '1', '"("', 'XEQ "PTXS"', 'RCL 40', NX, '"MOON"', 'XEQ "PTXS"', 'XEQ 60', '1', 'STO+ 41', 'RTN')
a('LBL 63', 'RCL 42', 'IP', '70', '+', 'STO 43', 'RCL 40', '1', 'XEQ IND 43', 'XEQ "PTXS"', 'RCL 42', 'IP', '81', '+', 'STO 43', 'RCL 40', NX, 'XEQ IND 43', 'XEQ "PTXS"', 'XEQ 60', '1', 'STO+ 41', 'RTN')
for lab, t in ((71, '<'), (72, '>'), (73, '='), (74, '?'), (82, 'VENUS'), (83, 'MARS'), (84, 'JUPITER'), (85, 'SATURN')):
    a('LBL %d' % lab, '"%s"' % t, 'RTN')
if SHORT:
    for lab, pn in ((91, 1), (92, 3), (93, 2), (94, 4)):
        a('LBL %d' % lab, str(pn), 'RTN')
a('END')
open(os.path.join(ROOT, 'programs', NAME + '.txt'), 'w').write('\n'.join(P) + '\n')
print(len(P))
