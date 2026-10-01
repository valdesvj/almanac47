#!/usr/bin/env python3
"""mktiny.py - python/tinyfont.py: the C47 tinyFont (GRFNT 10) for the simulator's ATEXT.

The bitmaps come from the C47 font file res/fonts/C47__TinyFont.ttf rasterized by the C47's own
tool src/ttf2RasterFonts (FreeType), as the firmware build does. Every glyph box is 8 rows,
none below the base line; most characters are 5 x 7 with 6 columns of advance.
Same layout as stdfont.py: code: (cols before, cols, cols after, rows above, rows, rows below,
[rows top to bottom, bit (cols-1) = left column]).

  python3 tools/generators/mktiny.py rasterFontsData.c
"""
import os, re, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def glyphs(src, name):
    s = open(src, encoding='latin-1').read()
    s = s[s.index('const font_t %s' % name):]
    e = s.find('const font_t', 10)
    s = s[:e] if e > 0 else s
    G = {}
    for m in re.finditer(r'charCode=0x([0-9a-f]+), \.colsBeforeGlyph=\s*(\d+), \.colsGlyph=\s*(\d+), \.colsAfterGlyph=\s*(\d+), '
                         r'\.rowsAboveGlyph=\s*(\d+), \.rowsGlyph=\s*(\d+), \.rowsBelowGlyph=\s*(\d+).*?\.data="([^"]*)"', s, re.S):
        cb, cg, ca, ra, rg, rb = map(int, m.groups()[1:7])
        data = bytes(int(h, 16) for h in re.findall(r'\\x([0-9a-f]{2})', m.group(8)))
        stride = (cg + 7) // 8
        rows = []
        for r in range(rg):
            v = 0
            for c in range(cg):
                if data[r * stride + c // 8] >> (7 - c % 8) & 1:
                    v |= 1 << (cg - 1 - c)
            rows.append(v)
        G[int(m.group(1), 16)] = (cb, cg, ca, ra, rg, rb, rows)
    return G


if __name__ == '__main__':
    G = glyphs(sys.argv[1], 'tinyFont')
    with open(os.path.join(ROOT, 'python', 'tinyfont.py'), 'w', encoding='utf-8') as fh:
        fh.write('"""tinyfont.py - the C47 tinyFont (GRFNT 10), made by tools/generators/mktiny.py from\n'
                 'res/fonts/C47__TinyFont.ttf (rasterized with the C47 tool ttf2RasterFonts). Glyph boxes 8 rows high,\n'
                 'none below the base line. Same layout as stdfont.py (codes: stdfont.code)."""\n\nTINY = {\n')
        for k in sorted(G):
            fh.write('    0x%04x: %r,\n' % (k, G[k]))
        fh.write('}\n')
    print(len(G), 'glyphs')
