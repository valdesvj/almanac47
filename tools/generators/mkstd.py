#!/usr/bin/env python3
"""mkstd.py - PTXS: the C47 status-bar font (standardFont, bold, capitals 12 px high)
as a text-drawing program, same calls as PTXB with other names:

  PTXB -> PTXS   PINB -> PINS   PF1 -> PF1S   PHM -> PHMS   PDM -> PDMS
  PDAT -> PDTS   PZN -> PZNS    PHL -> PHLS

Y = row of the base line (0 = bottom), X = column, then the string or number.
Glyphs are the calculator's own standardFont bitmaps (C43 source, rasterFontsData.c);
the symbols @ (Sun), ( (Moon), * (star), < > = ? (planets) are the PTXB ones scaled
to 12 rows. Every column is one AGRAPH, WSIZE 14 (13 rows + sign bit; nothing reaches the line above
with a line pitch of 14).

  python3 mkstd.py [rasterFontsData.c]   -> programs/PTXS.txt, python/native/c47fonts2.py
"""
import os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, 'python', 'native'))
import c47font                                             # noqa: E402

SRC = sys.argv[1] if len(sys.argv) > 1 else '/tmp/c43m/src/generated/rasterFontsData.c'
CHARS = ' %-./0123456789:ABCDEFGHIJKLMNOPQRSTUVWXYZ'
SYMBOLS = '@(*<>=?'
WS = 14


def std_glyphs():
    s = open(SRC, encoding='latin-1').read()
    s = s[s.index('const font_t standardFont'):]
    G = {}
    for m in re.finditer(r'charCode=0x([0-9a-f]+), \.colsBeforeGlyph=\s*(\d+), \.colsGlyph=\s*(\d+), \.colsAfterGlyph=\s*(\d+), '
                         r'\.rowsAboveGlyph=\s*(\d+), \.rowsGlyph=\s*(\d+), \.rowsBelowGlyph=\s*(\d+).*?\.data="([^"]*)"', s, re.S):
        code = int(m.group(1), 16)
        cb, cg, ca, ra, rg, rb = map(int, m.groups()[1:7])
        data = bytes(int(h, 16) for h in re.findall(r'\\x([0-9a-f]{2})', m.group(8)))
        G[code] = (cb, cg, ca, ra, rg, rb, data)
    return G


def columns_std(g):
    """(advance, [(column, bits)]) with bit 0 = base line (rowsBelowGlyph 4)."""
    cb, cg, ca, ra, rg, rb, data = g
    stride = (cg + 7) // 8
    cols = []
    for c in range(cg):
        v = 0
        for r in range(rg):
            if data[r * stride + c // 8] >> (7 - c % 8) & 1:
                bit = (rb - 4) + (rg - 1 - r)
                if 0 <= bit < WS - 1:
                    v |= 1 << bit
        if v:
            cols.append((cb + c, v))
    return cb + cg + ca, cols


def columns_sym(code):
    """PTXB symbol scaled to 12 rows (nearest neighbour), same proportions."""
    adv, yoff, cols = c47font.BIG[code]
    h = max(max(v for _, v in cols).bit_length(), 7)
    ncols = (max(c for c, _ in cols) + 1) if cols else 0
    nw = round(ncols * 12 / h)
    src = dict(cols)
    out = []
    for c in range(nw):
        v0 = src.get(int(c * ncols / nw), 0)
        v = 0
        for r in range(12):
            if v0 >> int(r * h / 12) & 1:
                v |= 1 << r
        if v:
            out.append((c, v))
    if code != 42:                                    # bold (as the text): OR with the column before
        d = dict(out)
        out = [(c, d.get(c, 0) | d.get(c - 1, 0)) for c in range(nw + 1) if d.get(c, 0) | d.get(c - 1, 0)]
        nw += 1
    return nw + 3, out


def glyph_prog(code, adv, cols):
    L = ['LBL %d' % code, 'RCL 31', 'RCL 30']
    x = 0
    for c, v in cols:
        if c > x:
            L += [str(c - x), '+']
        L += ['%s#2' % bin(v)[2:], 'STO 32', 'R↓', 'AGRAPH 32']
        x = c + 1
    L += [str(adv - x), '+', 'STO 30', 'RTN'] if adv > x else ['STO 30', 'RTN']
    return L


def main():
    G = std_glyphs()
    ptxb = [l.rstrip('\n') for l in open(os.path.join(ROOT, 'programs', 'PTXB.txt'), encoding='utf-8') if l.strip()]
    frame = ptxb[:ptxb.index('LBL 37')]                 # framework and PHL, up to the glyphs
    s = '\n'.join(frame)
    for a, b in (('PTXB', 'PTXS'), ('PINB', 'PINS'), ('"PF1"', '"PF1S"'), ('"PHM"', '"PHMS"'),
                 ('"PDM"', '"PDMS"'), ('"PDAT"', '"PDTS"'), ('"PZN"', '"PZNS"'), ('"PHL"', '"PHLS"')):
        s = s.replace(a, b)
    s = s.replace('WSIZE 8', 'WSIZE %d' % WS, 2)            # PTXS and the number setup; PHLS keeps 8
    s = s.replace('LBL 32\n6\nSTO+ 30', 'LBL 32\n8\nSTO+ 30')      # space: 8 px
    assert s.count('\n6\nSTO+ 30') == 2                             # PDM padding for 1-2 digit degrees
    s = s.replace('\n6\nSTO+ 30', '\n8\nSTO+ 30')
    L = ['LBL "PTXS"' if l == 'LBL "PTXS"' else l for l in s.split('\n')]
    font = {}
    for ch in CHARS:
        if ch == ' ':
            continue
        adv, cols = columns_std(G[ord(ch)])
        font[ord(ch)] = (adv, 0, cols)
        L += glyph_prog(ord(ch), adv, cols)
    for ch in SYMBOLS:
        adv, cols = columns_sym(ord(ch))
        font[ord(ch)] = (adv, 0, cols)
        L += glyph_prog(ord(ch), adv, cols)
    L.append('END')
    out = os.path.join(ROOT, 'programs', 'PTXS.txt')
    open(out, 'w', encoding='utf-8').write('\n'.join(L) + '\n')
    font[32] = (8, 0, [])
    with open(os.path.join(ROOT, 'python', 'native', 'c47fonts2.py'), 'w') as fh:
        fh.write('"""c47fonts2.py - PTXS (C47 status-bar font) as used by the calculator program.\n'
                 'code: (advance, y offset, [(column, bit mask), ...]); bit 0 = base line."""\nSTD = {\n')
        for c in sorted(font):
            fh.write('    %d: %r,  # %r\n' % (c, font[c], chr(c)))
        fh.write('}\n')
    print(out, len(L), 'lines')


if __name__ == '__main__':
    main()
