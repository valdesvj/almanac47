#!/usr/bin/env python3
"""mkstdfont.py - python/stdfont.py: the C47 standardFont (ATEXT, GRFNT 20 and 21) for the simulator.

The bitmaps come from the firmware build's src/generated/rasterFontsData.c (C43 source, GPL v3), read
with mktiny.glyphs, the same layout as tinyfont.py. The header and code() of stdfont.py are kept, and
the glyph names of the comments where a glyph had one; a new glyph gets uXXXX (its C47 code).
Run it, and mktiny.py, after a firmware update changes the fonts (Oct 6 2026: 101 glyphs redrawn,
among them 7 g p, 173 new, 42 gone).

  python3 tools/generators/mkstdfont.py rasterFontsData.c
"""
import os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import mktiny                                              # noqa: E402

OUT = os.path.join(ROOT, 'python', 'stdfont.py')


if __name__ == '__main__':
    G = mktiny.glyphs(sys.argv[1], 'standardFont')
    old = open(OUT, encoding='utf-8').read()
    head = old[:old.index('STD = {')]
    names = dict((int(k, 16), n) for k, n in re.findall(r'^    0x([0-9a-f]+): .*  # (.*)$', old, re.M))
    with open(OUT, 'w', encoding='utf-8') as fh:
        fh.write(head + 'STD = {\n')
        for k in sorted(G):
            fh.write('    0x%04x: %r,  # %s\n' % (k, G[k], names.get(k, 'u%04X' % k)))
        fh.write('}\n')
    print(len(G), 'glyphs')
