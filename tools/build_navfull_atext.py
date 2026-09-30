#!/usr/bin/env python3
"""build_navfull_atext.py - EXPERIMENTAL: NAVFULL with ATEXT for every text and number.

The views from tools/generators/atext/genviews_atx.py (programs/atext/): the same calculations
as NAVFULL, the columns and rows made for the C47's standard font. Only the body symbols (Sun,
Moon, planets, stars) keep the AGRAPH glyphs of the status-bar font: PSYM. The small 3 x 5 font
(PTXT, PTNS) is not in the build.

PTXS (and the number printers PINS PF1S PHMS PDMS PDTS PZNS) keep their stack, Z row of the
base line, Y column, X text or number:
  PTXS   the N03 trick of Didier (dlachieze): x<>(zyxt), 4, -, x<>y, ATEXT Z, then 4 back on the
         row (the next text follows at the returned place). The only ATEXT step of the build.
  number printers: the PTXS printers of NAVFULL, but each character is added to the string in
         variable ATX (+ joins two strings; flag 48 clear = the string starts) instead of drawn;
         one ATEXT for the whole number at the end. Padding = a space, as wide as a digit.
The NAV menu, INFO and the SINKING box stay as in NAVFULL with the columns of the top line for
the standard font.

  python3 tools/build_navfull_atext.py   -> build/atext/NAVFULL_ATX.txt (+ labels, src/), and the
                                            .p47 in build/p47/atext/ (tools/rejig47_atext.py)
"""
import os, sys, re, io, contextlib, shutil

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path[:0] = [HERE, os.path.join(HERE, 'generators'), os.path.join(HERE, 'generators', 'atext'), os.path.join(ROOT, 'python')]
import build_navfull as B
import navopt, gencache
import genviews_atx as V

OUT = os.path.join(ROOT, 'build', 'atext')
SRC = os.path.join(OUT, 'src')
P47 = os.path.join(ROOT, 'build', 'p47', 'atext')
SYMBOLS = '@(*<>=?'
ATX_VIEWS = ('ALMF', 'ALMS', 'HALMV', 'HORZ', 'HALMH', 'HANIM', 'ALLSKY')
FLAG = 48                               # clear: the string of a number printer starts


def sections(P):
    """{global label: its lines up to the next global label or the first glyph routine}."""
    out, cur = {}, None
    for l in P:
        m = re.fullmatch(r'LBL "(.+)"', l)
        if m:
            cur = m.group(1); out[cur] = []
        elif re.fullmatch(r'LBL (\d+)', l) and int(l[4:]) >= 33 and cur not in (None, 'PTXS'):
            cur = None
        if cur:
            out[cur].append(l)
    return out


def printers(font):
    """PTXS with ATEXT (the N03 trick) and the number printers building a string (variable ATX)."""
    S = sections(font)
    P = ['LBL "PTXS"',
         'REM "Z row of the base line, Y column, X text -> ATEXT (the N03 trick of Didier): the row 4 lower, then back"',
         'LBL 01', '⇄ zyxt', '4', '-', 'X<>Y', 'ATEXT Z', 'X<>Y', '4', '+', 'X<>Y', 'RTN',
         'REM "LBL 02: end of a number printer: the string ATX at the row R31, column R30"',
         'LBL 02', 'RCL 31', 'RCL 30', 'RCL "ATX"', 'GTO 01',
         'REM "LBL 03: character code X -> its text (LBL code), added to ATX (flag %d clear: ATX starts)"' % FLAG,
         'LBL 03', 'STO 32', 'XEQ IND 32',
         'LBL 09', 'FS? %d' % FLAG, 'GTO 26', 'STO "ATX"', 'SF %d' % FLAG, 'RTN',
         'LBL 26', 'RCL "ATX"', 'X<>Y', '+', 'STO "ATX"', 'RTN',
         'LBL 04', '48', '+', 'GTO 03',
         'REM "LBL 05: Z row, Y column, X number -> R31, R30, R34; a new string"',
         'LBL 05', 'STO 34', 'R↓', 'STO 30', 'R↓', 'STO 31', 'CF %d' % FLAG, 'RTN',
         'LBL 24', '32', 'GTO 03']
    for n in ('PINS', 'PF1S', 'PHMS', 'PDMS', 'PDTS', 'PZNS'):
        s = '\n'.join(S[n]) + '\n'
        s = re.sub(r'\n\d+\nSTO\+ 30\n', '\nXEQ 24\n', s)             # a blank place: a space
        assert 'AGRAPH' not in s and 'WSIZE' not in s and 'STO+ 30' not in s, n
        P += s.rstrip('\n').split('\n')
    h = [('GTO 25' if l == 'GTO 02' else l) for l in S['PHLS']]       # the line stays AGRAPH / PIXEL
    P += h + ['LBL 25', 'WSIZE 64', 'RCL 31', 'RCL 30', 'RTN']
    for c in ' -.0123456789:':
        P += ['LBL %d' % ord(c), '"%s"' % c, 'RTN']
    labs = [l for l in P if re.fullmatch(r'LBL \d+', l)]
    assert len(labs) == len(set(labs)), 'a local label twice in PTXS'
    return P + ['END']


def psym(font):
    """The status-bar glyphs of the symbols only, as the text routine PSYM."""
    i = font.index('LBL "PINS"')
    k = next(n for n in range(font.index('LBL "PHLS"'), len(font))
             if re.fullmatch(r'LBL (\d+)', font[n]) and int(font[n][4:]) >= 33)
    P = [('LBL "PSYM"' if l == 'LBL "PTXS"' else l) for l in font[:i] + font[k:]]
    return B.trim_font(P, set(SYMBOLS))


def nav_atx():
    """NAV of NAVFULL (gennav): the top line of the menu for the standard font, the SINKING box text centred."""
    L = B.read('NAV')
    T = V.top_x()
    s = '\n' + '\n'.join(L) + '\n'
    for a, b in (((206, 80), (206, T['time'])), ((206, 116, '"UT"'), (206, T['UT'], '"UT"')),
                 ((206, 150, '"DR"'), (206, T['DR'], '"DR"')), ((206, 174), (206, T['N'])), ((206, 176), (206, T['lat'])),
                 ((206, 244), (206, T['E'])), ((206, 246), (206, T['lon']))):
        a = '\n' + '\n'.join(map(str, a)) + '\n'; b = '\n' + '\n'.join(map(str, b)) + '\n'
        assert a in s, a
        s = s.replace(a, b)
    L = s.strip('\n').split('\n')
    import gennav
    k = L.index('"%s"' % gennav.BUSY)
    L[k - 1] = str(110 + (180 - V.width(gennav.BUSY)) // 2)
    return L


def build():
    progs = {n: B.read(n) for n in B.KEEP + ['NAV']}
    for n in ATX_VIEWS:
        with open(os.path.join(ROOT, 'programs', 'atext', n + '.txt'), encoding='utf-8') as fh:
            progs[n] = [l.rstrip('\n') for l in fh if l.strip()]
    progs['ALMT'] = B.almr(progs['ALMT'])
    progs['CACHE'] = gencache.program(True)
    progs['STXT'] = navopt.stxt(progs['STXT'])
    for n in gencache.VIEWS:
        progs[n] = gencache.swap(progs[n])
    font = navopt.pdts(navopt.phls(navopt.fonts(B.read('PTXS'))))
    progs['PTXS'] = printers(font)
    progs['PSYM'] = psym(font)
    nav = nav_atx()
    keep = [('PSYM' if n == 'PTXT' else n) for n in B.KEEP]
    need = B.closure(progs, [c for c in B.calls(nav) if c != 'INIT'])
    full = nav + [l for n in keep if n in need for l in progs[n]]
    called = set(B.calls(full))
    assert not called & {'PTXT', 'PTNS', 'PT1'}, called & {'PTXT', 'PTNS', 'PT1'}
    return full, sorted(need)


def main():
    full, need = build()
    B.write(os.path.join(SRC, 'NAVFULL_ATX.txt'), full)
    m = B.fixed_map('NAVFULL_ATX', full)
    B.write(os.path.join(OUT, 'NAVFULL_ATX.txt'), B.rename(full, m))
    with open(os.path.join(OUT, 'NAVFULL_ATX_LABELS.txt'), 'w', encoding='utf-8') as fh:
        fh.write('NAVFULL_ATX - program labels (NAV keeps its name; INIT: NAVINIT_FULL or NAVINIT_FAST)\n\n')
        fh.write('NAV     NAV     %s\n' % B.LABEL_TEXT['NAV'])
        fh.write('\n'.join('%s     %-7s %s' % (v, k, B.LABEL_TEXT.get(k, '')) for k, v in m.items()) + '\n')
    print('%-12s %7d %8d   %s' % (('NAVFULL_ATX',) + B.size(full) + (' '.join(need),)))
    return full


if __name__ == '__main__':
    main()
