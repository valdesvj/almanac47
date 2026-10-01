#!/usr/bin/env python3
"""glydemo.py - extras/GLYDEM.txt: a DEMO of the CHART view with fixed values (no calculation) to
judge on the calculator: GRFNT 21 (compressed) for the panel with the star numbers back, the
tinyFont (GRFNT 10) for the chart axes and labels, and the new body glyphs of glyphs47.py
(BIG in the panel, SMALL on the chart). Then a sheet of all the glyphs. R/S or a key: next screen.
Values: 26 Sep 2026 14:57 UT, 25 20 N 055 12 E (python/native almanac).
    python3 tools/generators/atext/glydemo.py"""
import os, sys, math
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path[:0] = [HERE, os.path.join(ROOT, 'python'), os.path.join(ROOT, 'python', 'native')]
import glyphs47 as G
import c47screen as S
from c47view import jd
from stdfont import STD, code

def width(t, fid):
    if fid == 10:
        from tinyfont import TINY
        return sum(sum(TINY[code(c)][:3]) for c in t)
    return sum(sum(STD[code(c)][:3]) - (1 if fid == 21 else 0) for c in t)

P = []
a = P.extend
font = [20]
def grfnt(n):
    if font[0] != n:
        a([str(n), 'GRFNT', 'DROP']); font[0] = n
def text(y, x, t, fid):
    """y = base line; the standard font has 4 rows under it, the tinyFont none."""
    grfnt(fid)
    a(['"%s"' % t, 'STO 00', 'DROP', str(y - (0 if fid == 10 else 4)), str(x), 'ATEXT 00', 'DROP', 'DROP'])
def sym(y, x, ch, big):
    a([str(y), str(x), '"%s"' % ch, 'XEQ "%s"' % ('PSYB' if big else 'PSYS'), 'DROP', 'DROP'])
def dm(v):
    s = '-' if v < 0 else ''
    v = abs(v); d = int(v); m = round((v - d) * 60, 1)
    if m >= 60: d, m = d + 1, 0.0
    return '%s%d %04.1f' % (s, d, m)

al = S.Almanac(jd(2026, 9, 26, 14 + 57 / 60), 25 + 20 / 60, 55.2)
rows = al.bodies()
CH = {0: '@', -1: '(', -2: '<', -3: '>', -4: '=', -5: '?'}

a(['LBL "GLYDEM"', 'REM "DEMO, no calculation: CHART with GRFNT 21 + tinyFont + the new glyphs; then the glyph sheet"', 'CLLCD'])
# --- chart: axes, ticks, labels (tinyFont), equator dots, bodies (small glyphs, star numbers in the tinyFont)
HY, HS, CW, X0 = 14, 200, 150, 176
a(['0', '-%d' % (X0 - 4), 'PIXEL'])                                     # the line between chart and panel
a(['%d.%03d' % (HY, HY + HS), 'STO 01', 'LBL 10', 'RCL 01', 'IP', '17', 'PIXEL', 'DROP', 'DROP', 'ISG 01', 'GTO 10'])
a(['18.168', 'STO 01', 'LBL 11', '%d' % HY, 'RCL 01', 'IP', 'PIXEL', 'DROP', 'DROP', 'ISG 01', 'GTO 11'])
for v in (10, 20, 30, 45, 60, 90):
    y = HY + int(HS * math.sin(math.radians(v)))
    a([str(y), '15', 'PIXEL', 'DROP', 'DROP', str(y), '16', 'PIXEL', 'DROP', 'DROP'])
    text(y - 3, 2, str(v), 10)
xs = [16 + CW * k // 4 for k in range(5)]
for x, l in zip(xs, 'NESWN'):
    text(4, x, l, 10)
# the celestial equator: dots (hour angle every 4 degrees, above the horizon)
lat = math.radians(al.lat)
for t in range(0, 360, 4):
    h = math.radians(t)
    sh = math.cos(lat) * math.cos(h)
    if sh <= 0: continue
    zn = math.degrees(math.atan2(-math.sin(h), -math.sin(lat) * math.cos(h))) % 360
    x, y = int(18 + zn * CW / 360), int(HY + sh * HS)
    a([str(y), str(x), 'PIXEL', 'DROP', 'DROP'])
for ident, g, d, hc, zn in rows:
    if hc <= 0: continue
    cx, cy = int(18 + zn * CW / 360), int(HY + math.sin(math.radians(hc)) * HS)
    sym(cy - 3, cx - 3, CH.get(ident, '*'), False)
    if ident > 0:
        w = width(str(ident), 10)
        text(cy - 3, cx + 5 if cx + 5 + w <= 170 else cx - 5 - w, str(ident), 10)
# --- panel: GRFNT 21, big glyphs, star numbers back
text(226, X0, '26-09-2026 14:57 UT', 21)
text(212, X0, 'N 25 20.0 E 055 12.0', 21)
NM = X0 + 14
text(188, NM, 'BODY', 21); text(188, 398 - width('ZN', 21) - 6, 'ZN', 21); text(188, 398 - width('000.0', 21) - 8 - width('-00 00.0', 21) + 20, 'HC', 21)
y = 174
for ident, g, d, hc, zn in rows:
    sym(y, X0, CH.get(ident, '*'), True)
    name = S.body_name(ident)
    text(y, NM, ('%d %s' % (ident, name)) if ident > 0 else name, 21)
    z = '%05.1f' % zn; h = dm(hc)
    zx = 398 - width(z, 21); hx = zx - 8 - width(h, 21)
    text(y, hx, h, 21); text(y, zx, z, 21)
    y -= 14
text(226, 388, 'S', 21)
grfnt(20)
a(['PAUSE 99'])
# --- the glyph sheet
a(['CLLCD'])
text(226, 2, 'GLYPHS 12 ROWS (FONT 21) AND 7 ROWS (FONT 10)', 21)
names = {'@': 'SUN', '(': 'MOON', '*': 'STAR', '<': 'VENUS', '>': 'MARS', '=': 'JUPITER', '?': 'SATURN'}
x = 4
for ch in G.BIG:
    sym(180, x, ch, True)
    sym(140, x, ch, False)
    text(120, x, names[ch], 10)
    x += 56
for i, (ch, t) in enumerate((('@', 'SUN'), ('(', 'MOON'), ('*', '37 ARCTURUS'), ('?', 'SATURN'))):
    xx = 4 + (i % 2) * 200; yy = 90 - (i // 2) * 16
    sym(yy, xx, ch, True); text(yy, xx + 14, t, 21)
text(50, 4, 'TINY: 10 20 30 45 60 90  N E S W  51 42 37', 10)
text(30, 4, 'A KEY: END', 10)
grfnt(20)
a(['PAUSE 99', 'RTN', 'END'])
P += G.program('PSYB', G.BIG) + G.program('PSYS', G.SMALL)
open(os.path.join(ROOT, 'extras', 'GLYDEM.txt'), 'w', encoding='utf-8').write('\n'.join(P) + '\n')
print('extras/GLYDEM.txt', len(P), 'lines')
