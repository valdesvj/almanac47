# genhh.py - HALMH: horizon chart on top (full width), almanac table below (short list:
# Sun, Moon, the first planet above the horizon in the order Venus, Jupiter, Mars, Saturn,
# the 3 brightest stars higher than 10 deg). Writes /home/claude/HALMH.txt
P = []
def a(*xs):
    for x in xs: P.extend(str(x).split('\n'))
def txt(y, x, s): a(y, x, '"%s"' % s, 'XEQ "PTXB"')
def num(y, x, reg, fn): a(y, x, 'RCL %s' % reg, 'XEQ "%s"' % fn)
GX, DX, HX, ZX = 112, 184, 256, 330
HY, HS = 118, 96                       # horizon row, pixels for 90 deg
a('LBL "HALMH"', 'STO 12', 'R↓', 'STO 11', 'R↓', 'STO 10')
for reg, lab in ((13, 'NTWA'), (14, 'RISE'), (15, 'TRAN'), (16, 'SET'), (17, 'NTWP')):
    a('XEQ 26', 'XEQ "%s"' % lab, 'STO %d' % reg)
a('RCL 10', 'STO 90', 'RCL 11', 'STO 91', 'RCL 12', 'STO 92', 'XEQ "HCZI"', 'CLLCD')
a('RCL 10', 'XEQ "SUNA"', 'STO 45', 'R↓', 'STO 46', 'R↓', 'STO 48', 'RCL 73', '15.99383', 'X<>Y', '÷', 'STO 29')
a('XEQ "PHA2"', 'STO 18', 'X<>Y', 'STO 19')
# line 1: date, UT, DR, GHA Aries (as ALMF)
num(229, 4, 10, 'PDAT')
a(229, 76, 'RCL 10', '0.5', '+', '1', 'MOD', '24', '×', 'XEQ "PHM"'); txt(229, 112, 'UT')
txt(229, 142, 'DR')
a('"N"', 'STO 43', 'RCL 11', 'X<0?', 'XEQ 22'); a(229, 160, 'RCL 43', 'XEQ "PTXB"'); a(229, 160, 'RCL 11', 'ABS', 'XEQ "PDM"')
a('"E"', 'STO 43', 'RCL 12', 'X<0?', 'XEQ 27'); a(229, 220, 'RCL 43', 'XEQ "PTXB"'); a(229, 226, 'RCL 12', 'ABS', 'XEQ "PDM"')
txt(229, 292, 'ARIES'); num(229, 328, 48, 'PDM')
# chart: horizon, Hc axis (dotted), ticks, labels 30 60 90, Zn ticks every 30 deg, letters
a(HY, '20', '376', 'XEQ "PHL"')
a('%d.%03d03' % (HY, HY + HS), 'STO 47', 'LBL 12', 'RCL 47', 'IP', '18', 'PIXEL', 'ISG 47', 'GTO 12')
for v in (30, 60, 90):
    y = HY + HS * v // 90
    a(y, 15, 'PIXEL', y, 16, 'PIXEL', y, 17, 'PIXEL', y - 3, 2, v, 'XEQ "PINB"')
for c in (20, 51, 82, 113, 145, 176, 207, 238, 270, 301, 332, 363, 395):
    a(HY - 1, c, 'PIXEL', HY - 2, c, 'PIXEL')
xs = (18, 111, 205, 299, 393)
a('0', 'STO 44', 'RCL 11', 'X<0?', 'GTO 23')
for x, l in zip(xs, 'NESWN'): txt(HY - 12, x, l)
a('GTO 24', 'LBL 23', '180', 'STO 44')
for x, l in zip(xs, 'SWNES'): txt(HY - 12, x, l)
a('LBL 24')
# celestial equator, dots every 3 deg of GHA
a('0', '3', 'XEQ "HCZQ"', '0', 'STO 47', 'LBL 13', 'XEQ 51', 'RCL 96', '1E-4', 'X<Y?', 'XEQ 15', '3', 'STO+ 47', '357', 'RCL 47', 'X≤Y?', 'GTO 13')
a('-102', '0', 'PIXEL')
txt(92, 34, 'BODY'); txt(92, GX + 36, 'GHA'); txt(92, DX + 36, 'DEC'); txt(92, HX + 42, 'HC'); txt(92, ZX + 18, 'ZN')
a('80', 'STO 40')
# Sun: table row always, symbol on the chart if above the horizon
a('RCL 46', 'RCL 45', 'XEQ 52', 'RCL 96', 'X>0?', 'XEQ 16')
a('RCL 40', '4', '"@"', 'XEQ "PTXB"', 'RCL 40', '34', '"SUN"', 'XEQ "PTXB"', 'XEQ 60')
# Moon, if above the horizon
a('XEQ "MOO2"', 'STO 45', 'R↓', 'STO 46', 'R↓', 'STO 21', 'R↓', 'STO 22', 'RCL 46', 'RCL 45', 'XEQ 52', 'RCL 96', 'X>0?', 'XEQ 61')
# the first planet above the horizon: Venus, Jupiter, Mars, Saturn (LBL 91-94)
a('1.004', 'STO 24', 'LBL 17', 'RCL 24', 'IP', '90', '+', 'STO 43', 'XEQ IND 43', 'STO 42', 'XEQ "PLN3"', 'STO 45', 'X<>Y', 'STO 46',
  'RCL 46', 'RCL 45', 'XEQ 52', 'RCL 96', 'X>0?', 'GTO 18', 'ISG 24', 'GTO 17', 'GTO 19', 'LBL 18', 'XEQ 63', 'LBL 19')
# the 3 brightest stars higher than 10 deg
a('0', 'STO 24', '1.058', 'STO 42', 'LBL 30', '3', 'RCL 24', 'X≥Y?', 'GTO 32',
  'RCL 42', 'IP', 'XEQ "SBRT"', 'STO 82', 'XEQ "SQK"', '0.15643', 'X>Y?', 'GTO 31', 'XEQ "STR2"', 'STO 45', 'X<>Y', 'STO 46', 'RCL 46', 'RCL 45', 'XEQ 52',
  '10', 'RCL 96', 'X≤Y?', 'GTO 31',
  'XEQ 57', 'RCL 40', '4', '"*"', 'XEQ "PTXB"', 'RCL 40', '16', 'RCL 82', 'XEQ "PINB"',
  'RCL 82', 'XEQ "SNMU"', 'STO 43', 'RCL 40', '34', 'RCL 43', 'XEQ "PTXB"', 'XEQ 60',
  '1', 'STO+ 24', 'LBL 31', 'ISG 42', 'GTO 30', 'LBL 32')
# Sun times and Moon on one line
txt(13, 4, 'TWI'); num(13, 26, 13, 'PHM')
txt(13, 62, 'RISE'); num(13, 90, 14, 'PHM')
txt(13, 126, 'MER'); num(13, 148, 15, 'PHM')
txt(13, 184, 'SET'); num(13, 206, 16, 'PHM')
txt(13, 242, 'TWI'); num(13, 264, 17, 'PHM')
a(13, 304, '"MOON "', 'XEQ "PTXB"', 'RCL 18', 'XEQ "PINB"', '"%"', 'XEQ "PTXB"')
a(2, 126, '"DOES NOT REPLACE THE NAUTICAL ALMANAC"', 'XEQ "PTXT"')
a('"S"', 'STO 43', 'FS? 11', 'XEQ 29', 'FS? 12', 'XEQ 65', 2, 392, 'RCL 43', 'XEQ "PTXT"')   # T = tables, S = series
a('3', 'STO 37', 'LBL 20', 'PAUSE 99', 'DSE 37', 'GTO 20', 'RTN')
# subroutines
a('LBL 26', 'RCL 10', '0.5', '-', 'IP', '0.5', '+', 'RCL 11', 'RCL 12', 'RTN')
a('LBL 29', '"T"', 'STO 43', 'RTN', 'LBL 65', '"X"', 'STO 43', 'RTN')
a('LBL 22', '"S"', 'STO 43', 'RTN', 'LBL 27', '"W"', 'STO 43', 'RTN')
a('LBL 15', 'RCL 99', 'RCL 98', 'PIXEL', 'RTN')
a('LBL 16', 'RCL 99', '3', '-', 'RCL 98', '5', '-', '"@"', 'XEQ "PTXB"', 'RTN')
# HCZ, then chart column R98 = IP(((Zn + R44) MOD 360) * 375/360 + 20), row R99 = IP(Hc * 96/90 + 118)
a('LBL 51', 'XEQ "HCZR"', 'GTO 49')
a('LBL 52', 'XEQ "HCZ"', 'LBL 49', 'RCL 97', 'RCL+ 44', '360', 'MOD', '375', '×', '360', '÷', '20', '+', 'IP', 'STO 98',
  'RCL 96', HS, '×', '90', '÷', HY, '+', 'IP', 'STO 99', 'RTN')
a('LBL 57', 'RCL 99', '3', '-', 'RCL 98', '3', '-', '"*"', 'XEQ "PTXB"', 'RCL 98', '6', '+', 'STO 43', '385', 'RCL 43', 'X>Y?', 'XEQ 21',
  'RCL 99', '3', '-', 'RCL 43', 'RCL 82', 'XEQ "PINB"', 'RTN', 'LBL 21', '22', 'STO- 43', 'RTN')
a('LBL 60', 'RCL 40', GX, 'RCL 45', 'XEQ "PDM"',
  '"N"', 'STO 43', 'RCL 46', 'X<0?', 'XEQ 22', 'RCL 40', DX, 'RCL 43', 'XEQ "PTXB"', 'RCL 40', DX, 'RCL 46', 'ABS', 'XEQ "PDM"',
  'RCL 40', HX, 'RCL 96', 'XEQ "PDM"', 'RCL 40', ZX, 'RCL 97', 'XEQ "PZN"', 'RCL 96', 'X<0?', 'XEQ 64', '11', 'STO- 40', 'RTN')
a('LBL 64', 'RCL 40', '1', '-', HX, '54', 'XEQ "PHL"', 'RTN')
a('LBL 61', 'RCL 99', '3', '-', 'RCL 98', '3', '-', '"("', 'XEQ "PTXB"',
  'RCL 40', '4', '"("', 'XEQ "PTXB"', 'RCL 40', '34', '"MOON"', 'XEQ "PTXB"', 'XEQ 60', 'RTN')
a('LBL 63', 'RCL 42', 'IP', '70', '+', 'STO 43', 'RCL 99', '3', '-', 'RCL 98', '3', '-', 'XEQ IND 43', 'XEQ "PTXB"',
  'RCL 40', '4', 'XEQ IND 43', 'XEQ "PTXB"', 'RCL 42', 'IP', '81', '+', 'STO 43', 'RCL 40', '34', 'XEQ IND 43', 'XEQ "PTXB"', 'XEQ 60', 'RTN')
for lab, t in ((71, '<'), (72, '>'), (73, '='), (74, '?'), (82, 'VENUS'), (83, 'MARS'), (84, 'JUPITER'), (85, 'SATURN')):
    a('LBL %d' % lab, '"%s"' % t, 'RTN')
for lab, pn in ((91, 1), (92, 3), (93, 2), (94, 4)):
    a('LBL %d' % lab, str(pn), 'RTN')
a('END')
open('/home/claude/HALMH.txt', 'w').write('\n'.join(P) + '\n')
print(len(P))
