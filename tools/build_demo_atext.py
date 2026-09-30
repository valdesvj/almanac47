#!/usr/bin/env python3
"""build_demo_atext.py - DEMOATX: the DEMOALM almanac page drawn with the new C47 command
ATEXT (standardFont, built in): no AGRAPH, no font program; the symbols are characters of the
C47 font (Sun STD_SUN, stars *, Moon (, planets Greek letters). One ATEXT per line (the columns
made with spaces), the three footer lines in one ATEXT with the CR glyph; the two lines
across the page with PIXEL. The symbols (Sun, planet, stars)
are left out. The numbers are the same sample values as DEMOALM, as text; the bottom line
shows the time (TICKS) - the one number converted on the calculator (SF1 from STXT).

  XEQ "DEMO" -> the page; PAUSE 99 keeps it until a key.   python3 tools/build_demo_atext.py -> extras/DEMOATX.txt
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


def psym():
    """PSYM: the seven symbols of PTXS (Sun @, Moon (, star *, planets < > = ?) as a small AGRAPH
    font: the PTXS character loop and only these glyphs. Z row of the base line, Y column, X text."""
    L = [l.strip() for l in open(os.path.join(ROOT, 'programs', 'PTXS.txt'), encoding='utf-8') if l.strip()]
    head = L[:L.index('LBL 03')]
    out = [l.replace('"PTXS"', '"PSYM"') for l in head]
    for c in '@(*<=>?':
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
    xg = X0 + max(width(pre) for y, pre, f in rowsT) + 8          # where the numbers start
    for y, pre, f in rowsT:
        n = max(1, round((xg - X0 - width(pre)) / 8))
        lines.append((y, (X0, pre + ' ' * n + ' '.join(f)), []))
    # the header: BODY over the names, GHA DEC HC ZN centred over their numbers
    full = max(rowsT, key=lambda r: len(r[2]))[2]
    starts, x = [], xg
    for k, t in enumerate(full):
        starts.append((x, width(t))); x += width(t) + 8
    cols = [(starts[0], 'GHA'), (((starts[1][0]), starts[2][0] + starts[2][1] - starts[1][0]), 'DEC'),
            (starts[3], 'HC'), (starts[4], 'ZN')]
    hp = [(X0 + width('   '), 'BODY')] + [(round(c[0] + (c[1] - width(t)) / 2), t) for c, t in cols]
    lines[1] = (head, join(hp), [])
    # the footer: its three lines in one ATEXT, separated by the CR glyph (20 rows each)
    fl = []
    for y in foot:                                     # two blocks: times left, Moon right (same x)
        fl.append((join([(x, t) for yy, x, t, n, v in items if yy == y and x < 180])[1],
                   join([(x, t) for yy, x, t, n, v in items if yy == y and x >= 180])[1]))
    xr = max(width(l) for l, r in fl) + 16
    fl = [l + ' ' * max(1, round((xr - width(l)) / 8)) + r for l, r in fl]
    P = ['LBL "DEMO"', 'TICKS', 'STO 41', 'CLLCD', 'CLSTK', '-221', '0', 'PIXEL', '-61', '0', 'PIXEL']
    for y, (x, line), right in lines:
        P += ['"%s"' % line, 'STO 45', BD.num(y - 4), BD.num(x), 'ATEXT 45']
    for y, ch in syms:
        if symfont:                                    # the custom AGRAPH symbol (PSYM), base line y
            P += [BD.num(y), '0', '"%s"' % ch, 'XEQ "PSYM"']
        else:
            P += ['"%s"' % SYMBOLS[ch], 'STO 45', BD.num(y - 4), '0', 'ATEXT 45']
    P += ['"%s"' % '\u21b5'.join(fl), 'STO 45', '40', '2', 'ATEXT 45']
    # the time in the top right corner (the one number made into text on the calculator: SF1)
    P += ['TICKS', 'RCL- 41', '10', '÷', 'XEQ "SF1"', '" S"', '+', 'STO 45', str(top - 4), '350', 'ATEXT 45',
          'PAUSE 99', 'CLLCD', 'CLSTK', 'RTN', 'END']
    for y, (x, line), right in lines:
        print('%3d %3d |%s|' % (y - 4, x, line))
    print(' 40   2 |%s|' % '|\n        |'.join(fl))
    stxt = B.read('STXT')
    prog = P + stxt + (psym() if symfont else [])
    m = B.label_map(prog, keep=('DEMO',))
    return prog, B.rename_keep(prog, m, 'DEMO'), m


if __name__ == '__main__':
    for name, sf in (('DEMOATX', False), ('DEMOATXS', True)):      # symbols: C47 font / own AGRAPH font
        prog, short, m = build(sf)
        out = os.path.join(ROOT, 'extras', name + '.txt')
        open(out, 'w', encoding='utf-8').write('\n'.join(short) + '\n')
        print(out, len(short), 'lines')
