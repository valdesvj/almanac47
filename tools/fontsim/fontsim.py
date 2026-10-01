"""fontsim.py - an APPROXIMATE look at the ATEXT fonts of GRFNT (codes from Jaco Mostert's GRFNTS demo).
Glyphs: the C47 TTFs rasterized by ttf2RasterFonts. How 21 22 23 31 32 41 are drawn is a guess from the
C43 display code (compress = 1 column less per character, bold = double strike, enlarged = rows doubled
except 4 rows, half = 2x2 pixels to 1)."""
import sys, os
sys.path.insert(0, '/home/claude/C47_nav/tools/generators'); sys.path[:0] = ['/home/claude/C47_nav/python', '/home/claude/C47_nav/python/native']
import mktiny
from stdfont import code
from PIL import Image
SRC = '/tmp/fnt/raster.c'
F = {n: mktiny.glyphs(SRC, n) for n in ('tinyFont', 'standardFont', 'numericFont', 'numericFontBold')}
SPEC = {10: ('tinyFont', 0, 0, 0, 0), 20: ('standardFont', 0, 0, 0, 0), 21: ('standardFont', 1, 0, 0, 0),
        22: ('standardFont', 0, 1, 0, 0), 23: ('standardFont', 0, 0, 1, 0),
        30: ('numericFont', 0, 0, 0, 0), 31: ('numericFont', 1, 0, 0, 0), 32: ('numericFont', 0, 0, 0, 1),
        40: ('numericFontBold', 0, 0, 0, 0), 41: ('numericFontBold', 1, 0, 0, 0)}

def glyph(G, ch):
    c = code(ch)
    if c in G: return G[c]
    if ch.upper() != ch and code(ch.upper()) in G: return G[code(ch.upper())]
    return G.get(0x3f) or next(iter(G.values()))

def width(text, fid):
    name, comp, bold, enl, half = SPEC[fid]; G = F[name]; w = 0
    for ch in text:
        cb, cg, ca = glyph(G, ch)[:3]; adv = cb + cg + ca - comp + bold
        w += adv // 2 if half else adv
    return w

def draw(pix, x, y, text, fid):
    """y = bottom row of the glyph boxes (as ATEXT), rows counted from the bottom; returns the next x."""
    name, comp, bold, enl, half = SPEC[fid]; G = F[name]
    for ch in text:
        cb, cg, ca, ra, rg, rb, rows = glyph(G, ch)
        pts = []
        for r, v in enumerate(rows):
            for c in range(cg):
                if v >> (cg - 1 - c) & 1:
                    pts.append((rb + rg - 1 - r, cb + c))
        if enl:     # each row twice except 4 of them: 20 -> 36 rows
            m, yy = {}, 0
            for r in range(rb + rg + ra):
                m[r] = [yy] if r in (3, 6, 9, 12) else [yy, yy + 1]
                yy += len(m[r])
            pts = [(q, c) for (r, c) in pts for q in m[r]]
        if half:
            pts = list({(r // 2, c // 2) for r, c in pts})
        if bold:
            pts += [(r, c + 1) for r, c in pts]
        for r, c in pts:
            pix.add((y + r, x + c))
        adv = cb + cg + ca - comp + bold
        x += adv // 2 if half else adv
    return x

def save(pix, path, scale=2, base=None):
    im = base.copy() if base else Image.new('L', (400, 240), 235)
    for (r, c) in pix:
        if 0 <= r < 240 and 0 <= c < 400: im.putpixel((c, 239 - r), 20)
    im.resize((400 * scale, 240 * scale), Image.NEAREST).save(path)
