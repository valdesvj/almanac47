#!/usr/bin/env python3
"""build_demo_atext.py - DEMOATX / DEMOATXS: the DEMOALM almanac page drawn with the new C47
command ATEXT (standardFont, built in). The standardFont is proportional (letters 5-14 px wide,
digits and the space 8 px), so every column is its own ATEXT at a fixed x: number and name, GHA,
N/S, then DEC HC ZN (only digits, spaces, '.' and '-': they line up); the footer in three columns,
each one ATEXT with the CR glyph. Every text goes through LBL 98, the N03 trick of Didier
(dlachieze): row of the base line, column, text -> XEQ 98 -> ⇄ zyxt, 4, -, x<>y, ATEXT Z.
DEMOATX: the symbols are characters of the C47 font (no AGRAPH); DEMOATXS: the symbols on the
page from a small AGRAPH font (PSYM). The bottom line time (TICKS) is made into text with STXT.

  XEQ "DEMO" -> the page; PAUSE 99 keeps it until a key.   python3 tools/build_demo_atext.py
  ATEXT r: Y = row of the bottom of the 20-row glyph box (base line 4 rows up), X = column.
"""
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [os.path.join(ROOT, 'python'), os.path.join(ROOT, 'python', 'native'), os.path.join(ROOT, 'tools')]
import build_demo as BD
import build_navfull as B
from c47screen import ip, jd_to_date


def fmt(name, v):
    """The text the number printers of PTXS print (c47screen.Screen), spaces for the padding."""
    if name == 'pinb':
        return str(ip(abs(v) + 0.5))
    if name == 'pf1':
        m = ip(abs(v) * 10 + 0.5); return '%d.%d' % (ip(m / 10), m % 10)
    if name == 'phm':
        if v > 98: return '--:--'
        m = ip(v * 60 + 0.5); return '%02d:%02d' % (ip(m / 60) % 24, m % 60)
    if name == 'pdm':
        t = ip(abs(v) * 600 + 0.5); d = ip(t / 600); t -= d * 600
        pad = (' ' if d <= 99 else '') + (' ' if d <= 9 else '')
        return '%s%s%d %d%d.%d' % (pad, '-' if v < 0 else ' ', d, ip(t / 100), ip(t / 10) % 10, t % 10)
    if name == 'pzn':
        t = ip(v * 10 + 0.5); t = 0 if t >= 3600 else t
        return '%03d.%d' % (ip(t / 10), t % 10)
    if name == 'pdat':
        d, m, y = jd_to_date(v); return '%02d-%02d-%04d' % (d, m, y)
    raise ValueError(name)


def width(s):
    from stdfont import STD, code
    return sum(sum(STD[code(c)][:3]) for c in s)


# the symbols from the C47 font instead of the PTXS ones (no AGRAPH): the Sun is STD_SUN (U+2299),
# the stars the asterisk, the Moon a parenthesis, the planets Greek letters (Saturn: h-bar)
SYMBOLS = {'@': '\u2299', '*': '*', '(': '(', '<': '\u03c6', '>': '\u03c3', '=': '\u03c8', '?': '\u0127'}
X0 = 13                                                  # the table lines start here, the symbols at x 0


def layout(items, gap=4):
    """The page was laid out for PTXS (digits 7 px); the standardFont is wider (digits 8 px).
    Every column start moves right as far as its row needs, the same shift for the whole column
    (x positions keep their order), so the columns stay aligned."""
    xs = sorted({x for y, x, s in items})
    shift = {x: 0 for x in xs}
    for _ in range(20):
        moved = False
        for y in {y for y, x, s in items}:
            row = sorted((x, s) for yy, x, s in items if yy == y)
            for (x0, s0), (x1, s1) in zip(row, row[1:]):
                need = x0 + shift[x0] + width(s0) + (0 if s1[:1] == ' ' else gap) - x1
                if need > shift[x1]:
                    shift[x1] = need; moved = True
        run = 0
        for x in xs:                              # a column never moves less than one on its left
            run = max(run, shift[x]); shift[x] = run
        if not moved:
            break
    return shift


def join(pieces, gap=1):
    """(x, text) pieces of a line -> (x of the line, one string): the number of spaces (8 px) that
    brings each piece nearest to its column, at least one between two pieces."""
    pieces = sorted(pieces)
    x0, line = pieces[0]
    pos = x0 + width(line)
    for x, t in pieces[1:]:
        n = max(gap, round((x - pos) / 8))
        line += ' ' * n + t
        pos += 8 * n + width(t)
    return x0, line


def psym(chars='@(*<=>?'):
    """PSYM: symbols of PTXS (Sun @, Moon (, star *, planets < > = ?) as a small AGRAPH font: the
    PTXS character loop and only the glyphs in chars (DEMOATXS: the ones on its page).
    Z row of the base line, Y column, X text."""
    L = [l.strip() for l in open(os.path.join(ROOT, 'programs', 'PTXS.txt'), encoding='utf-8') if l.strip()]
    head = L[:L.index('LBL 03')]
    out = [l.replace('"PTXS"', '"PSYM"') for l in head]
    for c in chars:
        i = L.index('LBL %d' % ord(c)); j = L.index('RTN', i)
        out += L[i:j + 1]
    return out + ['END']


def build(symfont=False):
    calls, rows = BD.record()
    items, lines, syms = [], [], []
    for name, a, k in calls:
        if name == 'glyph':
            syms.append((a[2], a[1]))                  # (row, PTXS symbol): one ATEXT each at x 0
            continue
        if name == 'pixel' or (name == 'small' and a[2] == BD.S.WARNING):
            continue                                   # lines across: PIXEL below
        items.append((a[0], a[1], (a[2] if name in ('text', 'small') else fmt(name, a[2])).strip(),
                      name, a[2]))
    ys = sorted({i[0] for i in items}, reverse=True)
    top, head, table, foot = ys[0], ys[1], [y for y in ys if 60 < y < ys[1]], [y for y in ys if y < 60]
    # the top line and the table header: words to their columns
    lines.append((top, join([(x, t) for y, x, t, n, v in items if y == top and x < 380]),
                  [t for y, x, t, n, v in items if y == top and x >= 380]))
    lines.append((head, join([(x - 14, t) for y, x, t, n, v in items if y == head]), []))
    # the table: star number and name, then the numbers in fixed columns (digits and spaces are
    # both 8 px, so the numbers line up in every line; N and S differ by 1 px)
    rowsT = []
    for y in table:
        row = sorted((x, t, n, v) for yy, x, t, n, v in items if yy == y)
        pre = [t for x, t, n, v in row if x < 100]
        pre = (('%2s ' % pre[0]) + ' '.join(pre[1:])) if pre[0].isdigit() else '   ' + ' '.join(pre)   # names line up
        num = [(n, v, t) for x, t, n, v in row if x >= 100]
        def dm(v, sign=False):
            t = ip(abs(v) * 600 + 0.5); d = ip(t / 600); m = (t - d * 600) / 10
            return ('-' if v < 0 else ' ' if sign else '') + '%3d %04.1f' % (d, m) if not sign else \
                   '%3s %04.1f' % (('-' if v < 0 else '') + str(d), m)
        f = [dm(num[0][1])]
        if len(num) > 1:
            f += [num[1][2], dm(num[2][1])[1:], dm(num[3][1], True), '%05.1f' % (ip(num[4][1] * 10 + 0.5) / 10)]
        rowsT.append((y, pre, f))
    # Every column is its own ATEXT at a fixed x (the standardFont is proportional: letters have
    # different widths, digits and the space are all 8 px). A row: number and name | GHA | N/S |
    # DEC HC ZN. Each text goes through LBL 98 (Didier's N03 trick): row of the base line, column,
    # text -> XEQ 98, which turns the stack for ATEXT Z.
    pieces = []                                        # (base line row, x, text)
    xg = X0 + max(width(pre) for y, pre, f in rowsT) + 8           # GHA
    wg = max(width(f[0]) for y, pre, f in rowsT)
    xns = xg + wg + 8                                              # N / S
    xd = xns + max(width('N'), width('S')) + 6                     # DEC HC ZN
    for y, pre, f in rowsT:
        pieces += [(y, X0, pre), (y, xg + wg - width(f[0]), f[0])]
        if len(f) > 1:
            pieces += [(y, xns, f[1]), (y, xd, ' '.join(f[2:]))]
    full = max(rowsT, key=lambda r: len(r[2]))[2]
    wdec, whc, wzn = width(full[2]), width(full[3]), width(full[4])
    cols = [((xg, wg), 'GHA'), ((xns, xd + wdec - xns), 'DEC'), ((xd + wdec + 8, whc), 'HC'),
            ((xd + wdec + whc + 16, wzn), 'ZN')]
    pieces.append((head, X0 + width('   '), 'BODY'))
    pieces += [(head, round(c[0] + (c[1] - width(t)) / 2), t) for c, t in cols]
    pieces.append((top, 2, join([(x, t) for y, x, t, n, v in items if y == top and x < 380])[1]))
    # the footer: three columns (labels, times, the Moon block), each one ATEXT with the CR glyph
    lab, val, rgt = [], [], []
    for y in foot:
        row = sorted((x, t) for yy, x, t, n, v in items if yy == y)
        lab.append(row[0][1])
        val.append(join([(x, t) for x, t in row[1:] if x < 180])[1])
        rgt.append(join([(x, t) for x, t in row if x >= 180])[1])
    xv = 2 + max(width(t) for t in lab) + 8
    xr = xv + max(width(t) for t in val) + 16
    CR = '↵'
    pieces += [(44, 2, CR.join(lab)), (44, xv, CR.join(val)), (44, xr, CR.join(rgt))]
    assert max(x + max(width(l) for l in t.split(CR)) for y, x, t in pieces) <= 400
    P = ['LBL "DEMO"', 'TICKS', 'STO 41', 'CLLCD', 'CLSTK', '-221', '0', 'PIXEL', '-61', '0', 'PIXEL']
    for y, x, t in pieces:
        P += [BD.num(y), BD.num(x), '"%s"' % t, 'XEQ 98']
    for y, ch in syms:
        if symfont:                                    # the custom AGRAPH symbol (PSYM), base line y
            P += [BD.num(y), '0', '"%s"' % ch, 'XEQ "PSYM"']
        else:
            P += [BD.num(y), '0', '"%s"' % SYMBOLS[ch], 'XEQ 98']
    # the time in the top right corner (the one number made into text on the calculator: SF1)
    P += ['TICKS', 'RCL- 41', '10', '÷', 'XEQ "SF1"', '" S"', '+', 'STO 45', str(top), '350', 'RCL 45', 'XEQ 98',
          'PAUSE 99', 'CLLCD', 'CLSTK', 'RTN',
          'REM "LBL 98 (the N03 trick of Didier): Z row of the base line, Y column, X text -> ATEXT"',
          'LBL 98', '⇄ zyxt', '4', '-', 'X<>Y', 'ATEXT Z', 'RTN', 'END']
    for y, x, t in sorted(pieces, key=lambda p: (-p[0], p[1])):
        print('%3d %3d |%s|' % (y, x, t.replace(CR, '|')))
    stxt = B.read('STXT')
    prog = P + stxt + (psym(''.join(sorted({ch for y, ch in syms}))) if symfont else [])
    m = B.label_map(prog, keep=('DEMO',))
    return prog, B.rename_keep(prog, m, 'DEMO'), m


if __name__ == '__main__':
    for name, sf in (('DEMOATX', False), ('DEMOATXS', True)):      # symbols: C47 font / own AGRAPH font
        prog, short, m = build(sf)
        out = os.path.join(ROOT, 'extras', name + '.txt')
        open(out, 'w', encoding='utf-8').write('\n'.join(short) + '\n')
        print(out, len(short), 'lines')
