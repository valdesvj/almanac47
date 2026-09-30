#!/usr/bin/env python3
"""build_demo_atext.py - DEMOATX: the DEMOALM almanac page drawn with the new C47 command
ATEXT (standardFont, built in): no AGRAPH, no font program. The symbols (Sun, planet, stars)
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
    from stdfont import STD
    return sum(sum(STD[ord(c) if ord(c) < 128 else 0x8000 + ord(c)][:3]) for c in s)


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
                need = x0 + shift[x0] + width(s0) + gap - x1
                if need > shift[x1]:
                    shift[x1] = need; moved = True
        run = 0
        for x in xs:                              # a column never moves less than one on its left
            run = max(run, shift[x]); shift[x] = run
        if not moved:
            break
    return shift


def build():
    calls, rows = BD.record()
    P = ['LBL "DEMO"', 'TICKS', 'STO 41', 'CLLCD', 'CLSTK']
    items = []
    for name, a, k in calls:
        if name == 'pixel':
            P += [BD.num(a[0]), BD.num(a[1]), 'PIXEL']
            continue
        if name == 'glyph' or (name == 'small' and a[2] == BD.S.WARNING):
            continue                                   # symbols left out; the bottom line shows the time
        t = a[2] if name in ('text', 'small') else fmt(name, a[2])
        n = len(t) - len(t.lstrip(' '))              # right-aligned numbers: the padding becomes x
        items.append((a[0], a[1] + 7 * n, t[n:]))
    out = []
    for lo, hi, left in ((220, 999, 0), (60, 220, -14), (-1, 60, 0)):     # top line, table, footer
        grp = [(y, x, s) for y, x, s in items if lo < y <= hi and x < 380]  # table: the symbol column is gone
        shift = layout(grp)
        for y, x, s in grp:
            out.append((y, x + shift[x] + left, s))
        out += [(y, 398 - width(s), s) for y, x, s in items if lo < y <= hi and x >= 380]   # S / T at the right edge
        print('rows %d-%d right edge %d' % (lo, hi, max(x + shift[x] + left + width(s) for y, x, s in grp)))
    for y, x, s in out:
        P += ['"%s"' % s, 'STO 45', BD.num(y - 4), BD.num(x), 'ATEXT 45']
    P += ['TICKS', 'RCL- 41', '10', '÷', 'XEQ "SF1"', 'STO 46',
          '"ATEXT "', 'RCL 46', '+', '" S - DEMO PAGE, SAMPLE DATA"', '+', 'STO 45', '0', '2', 'ATEXT 45',
          'PAUSE 99', 'CLLCD', 'CLSTK', 'RTN', 'END']
    stxt = B.read('STXT')
    need = B.closure({'STXT': stxt}, ['SF1'])
    prog = P + stxt
    m = B.label_map(prog, keep=('DEMO',))
    return prog, B.rename_keep(prog, m, 'DEMO'), m


if __name__ == '__main__':
    prog, short, m = build()
    out = os.path.join(ROOT, 'extras', 'DEMOATX.txt')
    open(out, 'w', encoding='utf-8').write('\n'.join(short) + '\n')
    print(out, len(short), 'lines', m)
