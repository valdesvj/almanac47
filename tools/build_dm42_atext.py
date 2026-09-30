#!/usr/bin/env python3
"""build_dm42_atext.py - EXPERIMENTAL: the DM42 / DM42n builds (C47 firmware) with ATEXT.

The text of the ALMANAC page (and of the NAV12 menu) is written with the C47's ATEXT command in
its standard font instead of the 5 x 7 AGRAPH font (PTXB). The text routines keep their names and
their stack (Z row of the base line, Y column, X text or number), so the views need no change
apart from the columns:

  PTXS   the N03 trick of Didier (dlachieze): x<>(zyxt), 4, -, x<>y, ATEXT Z; afterwards 4 is
         added back to the row, so the next text can follow at the returned place
  PINS PF1S PHMS PDMS PDTS PZNS   the same number printers as before, but each character is
         appended to a string (R18) instead of drawn; at the end one ATEXT for the whole number
  PSYM   the Sun, Moon, star and planet symbols stay the 5 x 7 AGRAPH glyphs (only those)
  PTXT   the small font of the bottom line stays as it is
  PTXB   NAV12 only: the chart view (HALMV) keeps the whole 5 x 7 font

The standard font is proportional (digits and the space 8 px, '.' 5 px, letters 5-14 px), so
every column is its own call at a fixed x: names, N/S and the other letters apart from the
numbers; a number printer always gives the same width (its padding is spaces of digit width).

  python3 tools/build_dm42_atext.py  -> build/dm42/atext/*.txt (+ .p47 with tools/rejig47_atext.py)
"""
import os, sys, re, io, contextlib

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path[:0] = [HERE, os.path.join(HERE, 'generators'), os.path.join(ROOT, 'python')]
import build_navfull as B
import build_dm42 as D
import navopt
from stdfont import STD, code

OUT = os.path.join(ROOT, 'build', 'dm42', 'atext')
SRC = os.path.join(OUT, 'src')
SYMBOLS = '@(*<>=?'                  # Sun, Moon, star, Venus, Mars, Jupiter, Saturn (PTXB glyphs)
NAMES = {v: k for k, v in D.PTXB_NAMES.items()}          # PTXS -> PTXB, PINS -> PINB ...


def width(t):
    return sum(sum(STD[code(c)][:3]) for c in t)


# ---------------------------------------------------------------- the columns (x in pixels)
# A number printer gives 4 character places for sign and degrees (pads, sign, 1-3 digits) and
# then ' mm.m': 9 places, 69 px. The degrees end at the 4th place, so their x is fixed.
F4 = 4 * 8                                  # sign and degrees
PDM = F4 + 8 + 16 + width('.') + 8          # the whole field
NAME = max(width(n) for n in __import__('c47data').STAR_NAME.values() if n)


def layout():
    X = {}
    # the top line (ALMF row 226, NAV12 menu row 206): date, time, UT, DR, N lat, E lon
    X['time'] = 2 + width('00-00-0000') + 8
    X['UT'] = X['time'] + width('00:00') + 8
    X['DR'] = X['UT'] + width('UT') + 8
    X['N'] = X['DR'] + width('DR') + 8
    X['lat'] = X['N'] + width('N') + 8 - 16          # tens of degrees after N (2 blank places)
    X['E'] = X['lat'] + PDM + 8
    X['lon'] = X['E'] + width('W') + 8 - 8           # hundreds after E (1 blank place)
    assert X['lon'] + PDM < 386, X
    # the table: symbol 1, star number 13, name 36, then GHA, N/S, DEC, HC, ZN
    X['num'], X['name'] = 13, 36
    X['gha'] = X['name'] + NAME + 8 - 8              # hundreds of GHA after the longest name
    X['ns'] = X['gha'] + PDM + 4
    X['dec'] = X['ns'] + width('N') + 6 - 16         # tens of DEC after N / S
    X['hc'] = X['dec'] + PDM + 6 - 8                 # the sign of Hc (tens and units follow)
    X['zn'] = X['hc'] + PDM + 6
    assert X['zn'] + width('000.0') <= 398, X
    X['hcbox'], X['hcw'] = X['hc'] + 8 - 1, PDM - 8 + 2         # the negative Hc, white on black
    # the header over the columns
    c = lambda a, b, t: round((a + b - width(t)) / 2)
    X['hGHA'] = c(X['gha'] + 8, X['gha'] + PDM, 'GHA')
    X['hDEC'] = c(X['ns'], X['dec'] + PDM, 'DEC')
    X['hHC'] = c(X['hc'] + 8, X['hc'] + PDM, 'HC')
    X['hZN'] = c(X['zn'], X['zn'] + width('000.0'), 'ZN')
    # the footer: labels, two times, then SD; the Moon block (here the DM42 note) at 196
    X['t1'] = 2 + max(width(t) for t in ('NAUT TWI', 'RISE/SET', 'MER PASS')) + 8
    X['t2'] = X['t1'] + width('00:00') + 8
    X['SD'] = X['t2']
    assert X['t2'] + width('00:00') < 196 and X['SD'] + width('SD 00.0') < 196
    assert 196 + width('NO MOON - NO PLANETS') <= 398
    return X


def remap(L, pairs, where):
    """Replace every run a (two or more lines) by b; each run must be found."""
    s = '\n' + '\n'.join(L) + '\n'
    for a, b in pairs:
        a = '\n' + '\n'.join(map(str, a)) + '\n'
        b = '\n' + '\n'.join(map(str, b)) + '\n'
        assert a in s, (where, a)
        s = s.replace(a, b)
    return s.strip('\n').split('\n')


def top_line(row, X):
    return [((row, 80), (row, X['time'])), ((row, 116, '"UT"'), (row, X['UT'], '"UT"')),
            ((row, 150, '"DR"'), (row, X['DR'], '"DR"')), ((row, 174), (row, X['N'])), ((row, 176), (row, X['lat'])),
            ((row, 244), (row, X['E'])), ((row, 246), (row, X['lon']))]


def almf(L, X, sym):
    L = remap(L, top_line(226, X) + [
        # header and Aries
        ((207, 36, '"BODY"'), (207, X['name'], '"BODY"')), ((207, 154, '"GHA"'), (207, X['hGHA'], '"GHA"')),
        ((207, 224, '"DEC"'), (207, X['hDEC'], '"DEC"')), ((207, 292, '"HC"'), (207, X['hHC'], '"HC"')),
        ((207, 344, '"ZN"'), (207, X['hZN'], '"ZN"')), ((193, 36, '"ARIES"'), (193, X['name'], '"ARIES"')),
        ((193, 128), (193, X['gha'])),
        # the rows (RCL 40 = the row): number, name, GHA, N/S, DEC, Hc, Zn and the negative Hc box
        (('RCL 40', 17), ('RCL 40', X['num'])), (('RCL 40', 36), ('RCL 40', X['name'])),
        (('RCL 40', 128), ('RCL 40', X['gha'])), (('RCL 40', 196), ('RCL 40', X['ns'])),
        (('RCL 40', 198), ('RCL 40', X['dec'])), (('RCL 40', 262), ('RCL 40', X['hc'])),
        (('RCL 40', 338), ('RCL 40', X['zn'])),
        (('RCL 40', 1, '-', 268, 55), ('RCL 40', 1, '-', X['hcbox'], X['hcw'])),
        # the footer
        ((47, 80), (47, X['t1'])), ((47, 118), (47, X['t2'])), ((33, 80), (33, X['t1'])),
        ((33, 118), (33, X['t2'])), ((19, 80), (19, X['t1'])), ((19, 122, '"SD "'), (19, X['SD'], '"SD "')),
        # the symbols: the 5 x 7 glyphs
        (('"@"', 'XEQ "PTXS"'), ('"@"', 'XEQ "%s"' % sym)), (('"*"', 'XEQ "PTXS"'), ('"*"', 'XEQ "%s"' % sym)),
        (('"("', 'XEQ "PTXS"'), ('"("', 'XEQ "%s"' % sym)),
        (('RCL 40', 1, 'XEQ IND 43', 'XEQ "PTXS"'), ('RCL 40', 1, 'XEQ IND 43', 'XEQ "%s"' % sym))], 'ALMF')
    return L


def nav_menu(L, X):
    return remap(L, top_line(206, X), 'NAV')


def halmv(L):
    """The chart keeps the 5 x 7 font: its calls go to PTXB, PINB ... (the font's own names)."""
    out = []
    for l in L:
        m = re.fullmatch(r'XEQ "(.+)"', l)
        out.append('XEQ "%s"' % NAMES[m.group(1)] if m and m.group(1) in NAMES else l)
    return out


def ptxb_font():
    """The 5 x 7 font as the normal build has it (navopt), under PTXS names."""
    return navopt.pdts(navopt.phls(navopt.fonts(D.ptxb_as_ptxs())))


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


def printers():
    """PTXS with ATEXT (the N03 trick) and the number printers building a string (R18)."""
    S = sections(ptxb_font())
    P = ['LBL "PTXS"',
         'REM "Z row of the base line, Y column, X text -> ATEXT (the N03 trick of Didier): the row 4 lower, then back"',
         'LBL 01', '⇄ zyxt', '4', '-', 'X<>Y', 'ATEXT Z', 'X<>Y', '4', '+', 'X<>Y', 'RTN',
         'REM "LBL 02: end of a number printer: the string R18 at the row R31, column R30"',
         'LBL 02', 'RCL 31', 'RCL 30', 'RCL 18', 'GTO 01',
         'REM "LBL 03: character code X -> its text (LBL code), appended to R18 (R21 = 0: R18 starts)"',
         'LBL 03', 'STO 32', 'XEQ IND 32',
         'LBL 09', 'STO 22', 'RCL 21', 'X=0?', 'GTO 26', 'RCL 22', 'x→α 18', 'RTN',
         'LBL 26', 'RCL 22', 'STO 18', '1', 'STO 21', 'RTN',
         'LBL 04', '48', '+', 'GTO 03',
         'REM "LBL 05: Z row, Y column, X number -> R31, R30, R34; an empty string"',
         'LBL 05', 'STO 34', 'R↓', 'STO 30', 'R↓', 'STO 31', '0', 'STO 21', 'RTN',
         'LBL 24', '32', 'GTO 03']
    for n in ('PINS', 'PF1S', 'PHMS', 'PDMS', 'PDTS', 'PZNS'):
        body = S[n]
        s = '\n'.join(body) + '\n'
        s = s.replace('\n6\nSTO+ 30\n', '\nXEQ 24\n')         # a blank place: a space
        body = s.rstrip('\n').split('\n')
        assert 'AGRAPH' not in s and 'WSIZE' not in s and 'STO+ 30' not in s, n
        P += body
    h = S['PHLS']                                              # the horizontal line stays AGRAPH / PIXEL
    h = [('GTO 25' if l == 'GTO 02' else l) for l in h]
    P += h + ['LBL 25', 'WSIZE 64', 'RCL 31', 'RCL 30', 'RTN']
    for c in ' -.0123456789:':
        P += ['LBL %d' % ord(c), '"%s"' % c, 'RTN']
    return P + ['END']


def psym(name):
    """The 5 x 7 glyphs of the symbols only, as their own text routine name (PSYM)."""
    S = ptxb_font()
    i = S.index('LBL "PINS"')
    j = S.index('LBL "PHLS"')
    k = next(n for n in range(j, len(S)) if re.fullmatch(r'LBL (\d+)', S[n]) and int(S[n][4:]) >= 33)
    P = S[:i] + S[k:]
    P = [('LBL "%s"' % name if l == 'LBL "PTXS"' else l) for l in P]
    return B.trim_font(P, set(SYMBOLS))


def assemble(nav, p, chart):
    need = B.closure(p, [c for c in B.calls(nav) if c != 'INIT'])
    q = dict(p)
    q['PTXS'] = printers()
    q['PTXT'] = B.trim_font(navopt.fonts(B.read('PTXT')), set(B.WARNING + 'TSX NEWZHC-.0123456789'))
    if chart:                                                   # the whole 5 x 7 font for HALMV
        big = set(''.join(''.join(B.strings(q[n])) for n in need if n not in ('PTXS', 'PTXT'))
                  + '0123456789-.: %' + SYMBOLS)
        f = ptxb_font()
        f = [re.sub(r'^(LBL|XEQ|GTO) "(.+)"$', lambda m: '%s "%s"' % (m.group(1), NAMES.get(m.group(2), m.group(2))), l)
             for l in f]
        q['PTXB'] = B.trim_font(f, big)
    else:
        q['PSYM'] = psym('PSYM')
    keep = B.KEEP[:B.KEEP.index('PTXT') + 1] + (['PTXB'] if chart else ['PSYM']) + B.KEEP[B.KEEP.index('PTXT') + 1:]
    need = B.closure(q, [c for c in B.calls(nav) if c != 'INIT'])
    return nav + [l for n in keep if n in need for l in q[n]], sorted(need)


def main():
    X = layout()
    builds = D.builds()
    res = {}
    for name in ('NAVLITTLE', 'NAV1T_DM42', 'NAV12_DM42'):
        nav, p = builds[name]
        chart = name == 'NAV12_DM42'
        p = dict(p)
        p['ALMF'] = almf(p['ALMF'], X, 'PTXB' if chart else 'PSYM')
        if chart:
            p['HALMV'] = halmv(p['HALMV'])
            nav = nav_menu(nav, X)
        L, need = assemble(nav, p, chart)
        atx = name.replace('_DM42', '') + '_ATX'
        B.write(os.path.join(SRC, atx + '.txt'), L)
        m = B.fixed_map(atx, L, keep=('NAV', 'INIT'))
        B.write(os.path.join(OUT, atx + '.txt'), B.rename_keep(L, m, ('NAV', 'INIT')))
        with open(os.path.join(OUT, atx + '_LABELS.txt'), 'w', encoding='utf-8') as fh:
            fh.write('%s - program labels (NAV keeps its name; INIT is NAVINIT_LITTLE)\n\n' % atx)
            fh.write('NAV     NAV     %s\n' % B.LABEL_TEXT['NAV'])
            fh.write('\n'.join('%s     %-7s %s' % (v, k, B.LABEL_TEXT.get(k, '')) for k, v in m.items()) + '\n')
        res[atx] = (L, need)
    print('columns:', X)
    print('%-13s %7s %8s' % ('file', 'lines', 'bytes'))
    for name, (L, need) in res.items():
        print('%-13s %7d %8d   %s' % ((name,) + B.size(L) + (' '.join(need),)))
    return res


if __name__ == '__main__':
    main()
