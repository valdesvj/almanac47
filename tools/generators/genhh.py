#!/usr/bin/env python3
"""genhh.py - HALMH: horizon chart on top (full width, sine altitude scale), short almanac
table below in the status-bar font (PTXS): Sun, Moon, the first planet above the horizon
in the order Venus, Jupiter, Mars, Saturn, the 3 brightest stars higher than 10 deg.
Footer: rise, set, meridian passage, ARIES; twilight and the Moon phase.
Writes programs/HALMH.txt"""
import math, os
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
P = []
def a(*xs):
    for x in xs: P.extend(str(x).split('\n'))
def txt(y, x, s): a(y, x, '"%s"' % s, 'XEQ "PTXS"')
def num(y, x, reg, fn): a(y, x, 'RCL %s' % reg, 'XEQ "%s"' % fn)
NX, GX, DX, HX, ZX = 36, 128, 196, 262, 338   # as ALMF: name (star number at 17), GHA, DEC, HC, ZN
HY, HS = 129, 89                       # horizon row, pixels for sin(Hc) = 1
TOP = 107                              # first table row
a('LBL "HALMH"', 'STO 12', 'R↓', 'STO 11', 'R↓', 'STO 10')
for reg, lab in ((13, 'NTWA'), (14, 'RISE'), (15, 'TRAN'), (16, 'SET'), (17, 'NTWP')):
    a('XEQ 26', 'XEQ "%s"' % lab, 'STO %d' % reg)
a('RCL 10', 'STO 90', 'RCL 11', 'STO 91', 'RCL 12', 'STO 92', 'XEQ "HCZI"', 'CLLCD')
a('RCL 10', 'XEQ "SUNA"', 'STO 45', 'R↓', 'STO 46', 'R↓', 'STO 48')
a('XEQ "PHA2"', 'STO 18', 'X<>Y', 'STO 19')
# header: date, UT, DR, T/S/X
num(226, 2, 10, 'PDTS')
a(226, 80, 'RCL 10', '0.5', '+', '1', 'MOD', '24', '×', 'XEQ "PHMS"'); txt(226, 116, 'UT')
a('"N"', 'STO 43', 'RCL 11', 'X<0?', 'XEQ 22'); a(226, 150, 'RCL 43', 'XEQ "PTXS"'); a(226, 152, 'RCL 11', 'ABS', 'XEQ "PDMS"')
a('"E"', 'STO 43', 'RCL 12', 'X<0?', 'XEQ 27'); a(226, 222, 'RCL 43', 'XEQ "PTXS"'); a(226, 224, 'RCL 12', 'ABS', 'XEQ "PDMS"')
# chart: horizon, Hc axis (dotted), altitude marks, Zn ticks every 30 deg, letters (small font)
a(HY, '20', '376', 'XEQ "PHLS"')
a('%d.%03d03' % (HY, HY + HS), 'STO 47', 'LBL 12', 'RCL 47', 'IP', '18', 'PIXEL', 'ISG 47', 'GTO 12')
for v in (10, 20, 30, 45, 60, 90):
    y = HY + int(HS * math.sin(math.radians(v)))
    a(y, 15, 'PIXEL', y, 16, 'PIXEL', y, 17, 'PIXEL', y - 2, 2, v, 'XEQ "PTNS"')
for c in (20, 51, 82, 113, 145, 176, 207, 238, 270, 301, 332, 363, 395):
    a(HY - 1, c, 'PIXEL', HY - 2, c, 'PIXEL')
xs = (19, 112, 206, 300, 394)
a('0', 'STO 44', 'RCL 11', 'X<0?', 'GTO 23')
for x, l in zip(xs, 'NESWN'): a(HY - 8, x, '"%s"' % l, 'XEQ "PTXT"')
a('GTO 24', 'LBL 23', '180', 'STO 44')
for x, l in zip(xs, 'SWNES'): a(HY - 8, x, '"%s"' % l, 'XEQ "PTXT"')
a('LBL 24')
# celestial equator, dots every 3 deg of GHA
a('0', '3', 'XEQ "HCZQ"', '0', 'STO 47', 'LBL 13', 'XEQ 51', 'RCL 96', '1E-4', 'X<Y?', 'XEQ 15', '3', 'STO+ 47', '357', 'RCL 47', 'X≤Y?', 'GTO 13')
a(TOP, 'STO 40')
# Sun: table row always, symbol on the chart if above the horizon
a('RCL 46', 'RCL 45', 'XEQ 52', 'RCL 96', 'X>0?', 'XEQ 16')
a('RCL 40', '1', '"@"', 'XEQ "PTXS"', 'RCL 40', NX, '"SUN"', 'XEQ "PTXS"', 'XEQ 60')
# Moon, if above the horizon
a('XEQ "MOO2"', 'STO 45', 'R↓', 'STO 46', 'RCL 46', 'RCL 45', 'XEQ 52', 'RCL 96', 'X>0?', 'XEQ 61')
# the first planet above the horizon: Venus, Jupiter, Mars, Saturn (LBL 91-94)
a('1.004', 'STO 24', 'LBL 17', 'RCL 24', 'IP', '90', '+', 'STO 43', 'XEQ IND 43', 'STO 42', 'XEQ "PLN3"', 'STO 45', 'X<>Y', 'STO 46',
  'RCL 46', 'RCL 45', 'XEQ 52', 'RCL 96', 'X>0?', 'GTO 18', 'ISG 24', 'GTO 17', 'GTO 19', 'LBL 18', 'XEQ 63', 'LBL 19')
# the 3 brightest stars higher than 10 deg
a('0', 'STO 24', '1.058', 'STO 42', 'LBL 30', '3', 'RCL 24', 'X≥Y?', 'GTO 32',
  'RCL 42', 'IP', 'XEQ "SBRT"', 'STO 82', 'XEQ "SQK"', '0.15643', 'X>Y?', 'GTO 31', 'XEQ "STR2"', 'STO 45', 'X<>Y', 'STO 46', 'RCL 46', 'RCL 45', 'XEQ 52',
  '10', 'RCL 96', 'X≤Y?', 'GTO 31',
  'XEQ 57', 'RCL 40', '1', '"*"', 'XEQ "PTXS"', 'RCL 40', '17', 'RCL 82', 'XEQ "PINS"',
  'RCL 82', 'XEQ "SNMU"', 'STO 43', 'RCL 40', NX, 'RCL 43', 'XEQ "PTXS"', 'XEQ 60',
  '1', 'STO+ 24', 'LBL 31', 'ISG 42', 'GTO 30', 'LBL 32')
# footer: rise, set, meridian passage, ARIES | twilight, Moon
txt(23, 2, 'RISE'); num(23, 44, 14, 'PHMS'); txt(23, 92, 'SET'); num(23, 128, 16, 'PHMS')
txt(23, 176, 'MER'); num(23, 214, 15, 'PHMS'); txt(23, 262, 'ARIES'); num(23, 312, 48, 'PDMS')
txt(9, 2, 'TWI'); num(9, 36, 13, 'PHMS'); num(9, 78, 17, 'PHMS')
a('"WAXING"', 'STO 43', 'RCL 19', '14.765', 'X<Y?', 'XEQ 28', 'RCL 18', '99.5', 'X≤Y?', 'XEQ 25', 'RCL 18', '0.5', 'X>Y?', 'XEQ 33')
a(9, 176, '"MOON "', 'XEQ "PTXS"', 'RCL 18', 'XEQ "PINS"', '"% "', 'XEQ "PTXS"', 'RCL 43', 'XEQ "PTXS"')
# T tables / S series / X outside the FAST period (flag 11 is set by MOO2: draw last)
a('"S"', 'STO 43', 'FS? 11', 'XEQ 29', 'FS? 12', 'XEQ 65', 226, 388, 'RCL 43', 'XEQ "PTXS"')
a(1, 126, '"DOES NOT REPLACE THE NAUTICAL ALMANAC"', 'XEQ "PTXT"')
a('3', 'STO 37', 'LBL 20', 'PAUSE 99', 'DSE 37', 'GTO 20', 'RTN')
# subroutines
a('LBL 26', 'RCL 10', '0.5', '-', 'IP', '0.5', '+', 'RCL 11', 'RCL 12', 'RTN')
a('LBL 29', '"T"', 'STO 43', 'RTN', 'LBL 65', '"X"', 'STO 43', 'RTN')
a('LBL 25', '"FULL"', 'STO 43', 'RTN', 'LBL 33', '"NEW"', 'STO 43', 'RTN', 'LBL 28', '"WANING"', 'STO 43', 'RTN')
a('LBL 22', '"S"', 'STO 43', 'RTN', 'LBL 27', '"W"', 'STO 43', 'RTN')
a('LBL 15', 'RCL 99', 'RCL 98', 'PIXEL', 'RCL 99', 'RCL 98', '1', '+', 'PIXEL', 'RCL 99', '1', '+', 'RCL 98', 'PIXEL', 'RCL 99', '1', '+', 'RCL 98', '1', '+', 'PIXEL', 'RTN')          # equator dot: 2 x 2 pixels
a('LBL 16', 'RCL 99', '6', '-', 'RCL 98', '6', '-', '"@"', 'XEQ "PTXS"', 'RTN')
# HCZ, then chart column R98 = IP(((Zn + R44) MOD 360) * 375/360 + 20), row R99 = IP(sin(Hc) * 89 + 129)
a('LBL 51', 'XEQ "HCZR"', 'GTO 49')
a('LBL 52', 'XEQ "HCZ"', 'LBL 49', 'RCL 97', 'RCL+ 44', '360', 'MOD', '375', '×', '360', '÷', '20', '+', 'IP', 'STO 98',
  'RCL "SHC"', HS, '×', HY, '+', 'IP', 'STO 99', 'RTN')
a('LBL 57', 'RCL 99', '6', '-', 'RCL 98', '6', '-', '"*"', 'XEQ "PTXS"', 'RCL 98', '8', '+', 'STO 43', '380', 'RCL 43', 'X>Y?', 'XEQ 21',
  'RCL 99', '6', '-', 'RCL 43', 'RCL 82', 'XEQ "PINS"', 'RTN', 'LBL 21', '32', 'STO- 43', 'RTN')
a('LBL 60', 'RCL 40', GX, 'RCL 45', 'XEQ "PDMS"',
  '"N"', 'STO 43', 'RCL 46', 'X<0?', 'XEQ 22', 'RCL 40', DX, 'RCL 43', 'XEQ "PTXS"', 'RCL 40', DX + 2, 'RCL 46', 'ABS', 'XEQ "PDMS"',
  'RCL 40', HX, 'RCL 96', 'XEQ "PDMS"', 'RCL 40', ZX, 'RCL 97', 'XEQ "PZNS"', 'RCL 96', 'X<0?', 'XEQ 64', '14', 'STO- 40', 'RTN')
a('LBL 64', 'RCL 40', '5', '+', HX + 7, '56', 'XEQ "PHLS"', 'RTN')
a('LBL 61', 'RCL 99', '6', '-', 'RCL 98', '6', '-', '"("', 'XEQ "PTXS"',
  'RCL 40', '1', '"("', 'XEQ "PTXS"', 'RCL 40', NX, '"MOON"', 'XEQ "PTXS"', 'XEQ 60', 'RTN')
a('LBL 63', 'RCL 42', 'IP', '70', '+', 'STO 43', 'RCL 99', '6', '-', 'RCL 98', '6', '-', 'XEQ IND 43', 'XEQ "PTXS"',
  'RCL 40', '1', 'XEQ IND 43', 'XEQ "PTXS"', 'RCL 42', 'IP', '81', '+', 'STO 43', 'RCL 40', NX, 'XEQ IND 43', 'XEQ "PTXS"', 'XEQ 60', 'RTN')
for lab, t in ((71, '<'), (72, '>'), (73, '='), (74, '?'), (82, 'VENUS'), (83, 'MARS'), (84, 'JUPITER'), (85, 'SATURN')):
    a('LBL %d' % lab, '"%s"' % t, 'RTN')
for lab, pn in ((91, 1), (92, 3), (93, 2), (94, 4)):
    a('LBL %d' % lab, str(pn), 'RTN')
a('END')
open(os.path.join(ROOT, 'programs', 'HALMH.txt'), 'w').write('\n'.join(P) + '\n')
print(len(P))
