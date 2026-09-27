#!/usr/bin/env python3
"""build_demo.py - DEMOALM: the almanac page (ALMF) with fixed sample data and the text
programs only - no navigation calculations. A demo of what AGRAPH and PIXEL can do.

  XEQ "DEMO"  ->  1 AGRAPH  2 PIXEL  0 END
    1  DALA draws the page with PTXS / PTXT: one AGRAPH per glyph column.
    2  DALP draws the same page with the same glyph data, dot by dot with PIXEL
       (PTXP / PTTP: each column's bits are tested and every lit dot is one PIXEL).
  The bottom line shows the time taken (TICKS) and how many AGRAPH or PIXEL calls.

Sample data: Dubai (N 25 12, E 55 18), 02-10-2026 18:00 UT, as calculated by ALMF.
Writes build/DEMOALM.txt (convert with rejig). PTXS and PTXP carry the C47 standardFont
glyphs: GPL-3.0 (programs/LICENSE-PTXS.txt).

  python3 tools/build_demo.py
"""
import os, re, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [os.path.join(ROOT, 'python'), os.path.join(ROOT, 'python', 'native'), os.path.join(ROOT, 'tools')]
import c47screen as S
from c47font import SMALL
import build_navfull as B

SAMPLE = (2026, 10, 2, 18.0, 25.2, 55.3)
NAMES_A = {'text': 'PTXS', 'small': 'PTXT', 'pdat': 'PDTS', 'phm': 'PHMS', 'pdm': 'PDMS', 'pzn': 'PZNS',
           'pinb': 'PINS', 'pf1': 'PF1S', 'hline': 'PHLS', 'ptns': 'PTNS'}
RENAME_S = (('PTXS', 'PTXP'), ('PINS', 'PINP'), ('PF1S', 'PF1P'), ('PHMS', 'PHMP'), ('PDMS', 'PDMP'),
            ('PDTS', 'PDTP'), ('PZNS', 'PZNP'), ('PHLS', 'PHLP'))
RENAME_T = (('PTXT', 'PTTP'), ('PTNS', 'PTNP'), ('"PT1"', '"PT1P"'))


LABEL_TEXT = {
 'DALA': 'page: the almanac page drawn with the AGRAPH fonts (menu option 1)',
 'DALP': 'page: the same page drawn with the PIXEL fonts (menu option 2)',
 'PTXS': 'FONT, big (status-bar font), AGRAPH: draw a string',
 'PINS': 'FONT, big, AGRAPH: whole number',
 'PF1S': 'FONT, big, AGRAPH: number with one decimal',
 'PHMS': 'FONT, big, AGRAPH: hh:mm from hours',
 'PDMS': 'FONT, big, AGRAPH: degrees and minutes ddd mm.m',
 'PDTS': 'FONT, big, AGRAPH: date dd-mm-yyyy from a Julian Date',
 'PZNS': 'FONT, big, AGRAPH: azimuth ddd.d',
 'PHLS': 'FONT, big, AGRAPH: horizontal line',
 'PTXT': 'FONT, small 3x5, AGRAPH: draw a string',
 'PTNS': 'FONT, small, AGRAPH: whole number',
 'PT1':  'FONT, small, AGRAPH: number with one decimal',
 'PTXP': 'FONT, big, PIXEL copy: draw a string dot by dot',
 'PINP': 'FONT, big, PIXEL copy: whole number',
 'PF1P': 'FONT, big, PIXEL copy: number with one decimal',
 'PHMP': 'FONT, big, PIXEL copy: hh:mm from hours',
 'PDMP': 'FONT, big, PIXEL copy: degrees and minutes ddd mm.m',
 'PDTP': 'FONT, big, PIXEL copy: date dd-mm-yyyy from a Julian Date',
 'PZNP': 'FONT, big, PIXEL copy: azimuth ddd.d',
 'PHLP': 'FONT, big, PIXEL copy: horizontal line',
 'PTTP': 'FONT, small, PIXEL copy: draw a string dot by dot',
 'PTNP': 'FONT, small, PIXEL copy: whole number',
 'PT1P': 'FONT, small, PIXEL copy: number with one decimal',
}


def num(v):
    if isinstance(v, int) or float(v).is_integer() and abs(v) < 1e6:
        return str(int(v))
    t = repr(float(v)).replace('e', 'E').replace('E+', 'E')
    return t.replace('E-0', 'E-').replace('E0', 'E')


def record():
    """Draw ALMF in Python and record every top-level drawing call."""
    calls, depth = [], [0]
    Scr = S.Screen

    def wrap(name):
        orig = getattr(Scr, name)

        def f(self, *a, **k):
            if depth[0] == 0:
                calls.append((name, a, k))
            depth[0] += 1
            try:
                return orig(self, *a, **k)
            finally:
                depth[0] -= 1
        return orig, f
    saved = {}
    for n in ('text', 'small', 'pdat', 'phm', 'pdm', 'pzn', 'pinb', 'pf1', 'hline', 'pixel', 'glyph'):
        saved[n], f = wrap(n)
        setattr(Scr, n, f)
    try:
        y, m, d, h, la, lo = SAMPLE
        from c47view import jd
        al = S.Almanac(jd(y, m, d, h), la, lo)
        rows = S.almf(al)[0]
    finally:
        for n, o in saved.items():
            setattr(Scr, n, o)
    return calls, rows


def page(calls, names, label, title):
    """Calculator program that replays the recorded calls."""
    P = ['LBL "%s"' % label, 'TICKS', 'STO 41', 'CLLCD']
    used = set()
    for name, a, k in calls:
        if name == 'pixel':
            P += [num(a[0]), num(a[1]), 'PIXEL']
        elif name == 'glyph':
            font, ch, y, x = a
            P += [num(y), num(x), '"%s"' % ch, 'XEQ "%s"' % names['text']]
            used.add(ch)
        elif name in ('text', 'small'):
            y, x, s = a[:3]
            if name == 'small' and s == S.WARNING:
                continue                                     # the bottom line shows the timing instead
            fn = names['small'] if (name == 'small' or (len(a) > 3 and a[3] is SMALL)) else names['text']
            P += [num(y), num(x), '"%s"' % s, 'XEQ "%s"' % fn]
        elif name == 'hline':
            P += [num(a[0]), num(a[1]), num(a[2]), 'XEQ "%s"' % names['hline']]
        else:
            y, x, v = a
            P += [num(y), num(x), num(v), 'XEQ "%s"' % names[name]]
    # bottom line: "AGRAPH 3.2 S  DEMO, SAMPLE DATA"
    P += ['TICKS', 'RCL- 41', '10', '÷', 'STO 41',
          '1', '100', '"%s "' % title, 'XEQ "%s"' % names['small'], 'RCL 41', 'XEQ "%s"' % names['ptns1'],
          '" S   DEMO PAGE - SAMPLE DATA"', 'XEQ "%s"' % names['small'],
          '3', 'STO 42', 'LBL 01', 'PAUSE 99', 'DSE 42', 'GTO 01', 'RTN', 'END']
    return P


def pixel_font(lines, renames):
    """The same font with every AGRAPH replaced by a dot-by-dot PIXEL routine (LBL 99)."""
    s = '\n'.join(lines)
    for a, b in renames:
        s = s.replace(a, b)
    L = s.split('\n')
    out = []
    for l in L:
        if re.fullmatch(r'[01]+#2', l):
            out.append(str(int(l[:-2], 2)))                  # the column as an ordinary number
        elif l == 'AGRAPH 32':
            out.append('XEQ 99')
        else:
            out.append(l)
    assert out[-1] == 'END'
    out = out[:-1] + [
        # LBL 99: X = column, Y = row, R32 = the column's bits (bit 0 = row): one PIXEL per lit dot
        'LBL 99', 'STO 38', 'R↓', 'STO 40', 'STO 39', 'RCL 32', 'STO 37',
        'LBL 98', 'RCL 37', 'X=0?', 'GTO 97', '2', 'MOD', 'X=0?', 'GTO 96', 'RCL 39', 'RCL 38', 'PIXEL',
        'LBL 96', 'RCL 37', '2', '÷', 'IP', 'STO 37', '1', 'STO+ 39', 'GTO 98',
        'LBL 97', 'RCL 40', 'RCL 38', '1', '+', 'RTN', 'END']
    return out


def build():
    calls, rows = record()
    big = set(B.strings(B.read('ALMF')) + '0123456789-.: %@(*<>=?' + ''.join(c[1][2] for c in calls if c[0] == 'text'))
    small = set('0123456789.S AGRPHIXLDEMOTN-,' + S.WARNING)
    ptxs = B.trim_font(B.read('PTXS'), big)
    ptxt = B.trim_font(B.read('PTXT'), small)
    NA = dict(NAMES_A, ptns1='PT1')
    NP = {k: v for k, v in NAMES_A.items()}
    for a, b in RENAME_S + RENAME_T:
        a, b = a.strip('"'), b.strip('"')
        for k in NP:
            if NP[k] == a:
                NP[k] = b
    NP['ptns1'] = 'PT1P'
    menu = ['LBL "DEMO"', 'LBL 01', '"1 AGRAPH 2 PIXEL 0 END"', 'STO 43', 'PROMPT 43', 'STO 44', 'X=0?', 'RTN',
            '1', 'RCL 44', 'X=Y?', 'XEQ "DALA"', '2', 'RCL 44', 'X=Y?', 'XEQ "DALP"', 'GTO 01', 'END']
    prog = (menu + page(calls, NA, 'DALA', 'AGRAPH') + page(calls, NP, 'DALP', 'PIXEL')
            + ptxs + ptxt + pixel_font(ptxs, RENAME_S) + pixel_font(ptxt, RENAME_T))
    # only DEMO keeps its name; every other label becomes N01, N02 ... (table in DEMOALM_LABELS.txt)
    mapping = B.label_map(prog, keep=('DEMO',))
    renamed = B.rename_keep(prog, mapping, 'DEMO')
    out = os.path.join(ROOT, 'build', 'DEMOALM.txt')
    with open(out, 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(renamed) + '\n')
    with open(os.path.join(ROOT, 'build', 'DEMOALM_LABELS.txt'), 'w', encoding='utf-8') as fh:
        fh.write('DEMOALM: program labels on the calculator (left), original name, what it does.\n'
                 'Only DEMO keeps its name.\n\n')
        fh.write('\n'.join('%s  %-5s %s' % (v, k, LABEL_TEXT.get(k, '')) for k, v in mapping.items()) + '\n')
    return out, prog, rows, mapping, renamed


if __name__ == '__main__':
    out, prog, rows, mapping, renamed = build()
    print(out, len(renamed), 'lines,', len(mapping), 'labels renamed')
