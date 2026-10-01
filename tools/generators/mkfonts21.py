#!/usr/bin/env python3
"""mkfonts21.py - python/native/c47fonts21.py: the fonts of the new C47 screens (NAVFULL_T21) for
the native PC version, in the format of c47font.py (code: (advance, y offset, [(column, mask)]),
mask bit 0 = the row y + offset; text y = the base line):

  F21   the C47 standard font as GRFNT 21 draws it (one column less per character), ATEXT
  TINY  the C47 tinyFont (GRFNT 10), base line = the bottom of its 8-row box
  SYMB  the body symbols of 12 rows and the Moon phases '0'-'7' (glyphs47.BIG, PSYB)
  SYMS  the body symbols of 7 rows (glyphs47.SMALL, PSYS)

  python3 tools/generators/mkfonts21.py
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path[:0] = [os.path.join(ROOT, 'python'), os.path.join(HERE, 'atext')]
from stdfont import STD, code
from tinyfont import TINY
import glyphs47 as G


def from_atext(F, comp, base):
    out = {}
    for c, (cb, cg, ca, ra, rg, rb, rows) in F.items():
        if c > 0x7f:
            continue
        cols = []
        for k in range(cg):
            m = 0
            for r, v in enumerate(rows):                      # r = 0 top row
                if v >> (cg - 1 - k) & 1:
                    m |= 1 << (rg - 1 - r)
            if m:
                cols.append((cb + k, m))
        out[c] = (cb + cg + ca - comp, rb - base, cols)
    return out


def from_rows(glyphs, gap=2):
    out = {}
    for ch, rows in glyphs.items():
        cols = []
        for k, m in enumerate(G.columns(rows)):
            if m:
                cols.append((k, m))
        out[ord(ch)] = (max(len(r) for r in rows) + gap, 0, cols)
    return out


def main():
    F = {'F21': from_atext(STD, 1, 4), 'TINY': from_atext(TINY, 0, 0),
         'SYMB': from_rows(G.BIG), 'SYMS': from_rows(G.SMALL)}
    with open(os.path.join(ROOT, 'python', 'native', 'c47fonts21.py'), 'w', encoding='utf-8') as fh:
        fh.write('"""c47fonts21.py - made by tools/generators/mkfonts21.py: the fonts of the C47 screens of\n'
                 'NAVFULL_T21 (GRFNT 21 standard font, tinyFont, glyphs47 symbols) in the format of c47font.py:\n'
                 'code: (advance, y offset, [(column, mask)]), mask bit 0 = the row y + offset (y = base line)."""\n')
        for n, d in F.items():
            fh.write('\n%s = {\n' % n)
            for k in sorted(d):
                fh.write('    %d: %r,\n' % (k, d[k]))
            fh.write('}\n')
    print({n: len(d) for n, d in F.items()})


if __name__ == '__main__':
    main()
