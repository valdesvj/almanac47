#!/usr/bin/env python3
"""build_dm42_atext.py - EXPERIMENTAL: the DM42 / DM42n builds (C47 firmware) with ATEXT only.

NAVLITTLE_ATX, NAV1T_ATX and NAV12_ATX: every text and number is written with the C47's ATEXT
command in its standard font; only the symbols of the Sun and the stars stay AGRAPH (the 5 x 7
glyphs of PTXB, program PSYM). No small font, and the warning line only in the NAV12 menu (the
views have none).

The ALMANAC view and the NAV12 chart (no ARIES row, no Moon line, no note under the list) come from tools/generators/atext/genviews_atx.py (the
all-ATEXT variant, programs/atext/big/): the Moon, the planets and the Moon phase are taken out
as for the other DM42 builds (build_dm42.py). The text routines are those of atext_common.py:
PTXS is Didier's N03 trick (the only ATEXT step), the number printers put the number together
in R18 and write it with one ATEXT.

  python3 tools/build_dm42_atext.py  -> build/dm42/atext/*.txt (+ src/, labels); .p47 with tools/rejig47_atext.py
"""
import os, sys, re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path[:0] = [HERE, os.path.join(HERE, 'generators'), os.path.join(HERE, 'generators', 'atext'), os.path.join(ROOT, 'python')]
import build_navfull as B
import build_dm42 as D
import navopt
import atext_common as AC
import genviews_atx as V
import glyphs47

OUT = os.path.join(ROOT, 'build', 'dm42', 'atext')
SRC = os.path.join(OUT, 'src')
BIG = os.path.join(ROOT, 'programs', 'atext', 'big')
S = '18'                                # the text of a number printer (R18: free here, no Moon phase)


LABELS = {'PTXS': 'TEXT with ATEXT (standard font; Didier\'s N03 trick) and the number printers - Z row, Y column, X text or number',
         'PSYM': 'the AGRAPH symbols of the bodies - Z row, Y column, X symbol'}


def read_big(name):
    with open(os.path.join(BIG, name + '.txt'), encoding='utf-8') as fh:
        return [l.rstrip('\n') for l in fh if l.strip()]


def no_moon(A, name):
    """As build_dm42 does for the views: no Moon phase, no Moon and no planet rows."""
    if 'XEQ "PHA2"' in A:
        A = D.seq(A, ['XEQ "PHA2"', 'STO 18', 'X<>Y', 'STO 19'], [])
    i = A.index('XEQ "MOO2"')
    j = A.index('1.058', i)
    assert 'XEQ "PLN3"' in A[i:j] and A[j - 1].startswith('GTO '), name
    return A[:i] + A[j:]


def unused_locals(A, ind_targets=None):
    """Drop the subroutines nothing calls any more (Moon and planet rows, their names and words):
    a block LBL n ... RTN right after an RTN, whose label no XEQ / GTO uses. With an XEQ IND
    nothing is dropped, unless ind_targets lists the labels the indirect calls can reach."""
    while True:
        called = {l.split()[1] for l in A if re.fullmatch(r'(XEQ|GTO) \d+', l)} | {str(n) for n in ind_targets or ()}
        ind = ind_targets is None and any(re.fullmatch(r'(XEQ|GTO) IND \d+', l) for l in A)
        out, i, drop = [], 0, False
        while i < len(A):
            m = re.fullmatch(r'LBL (\d+)', A[i])
            if m and out and out[-1] == 'RTN' and m.group(1) not in called and not ind:
                j = A.index('RTN', i)
                i = j + 1; drop = True
                continue
            out.append(A[i]); i += 1
        if not drop:
            return out
        A = out


LUN, NEW0 = '29.530588861', '2451550.09766'      # mean lunation, mean new Moon of Jan 2000 (Meeus 49.1)


def moon_lines(MX=212, rows=(47, 33)):
    """EXPERIMENTAL (NAVLITTLE_PH): the Moon line without the Moon: its age from the mean lunation
    (within about 14 hours of the true one), the lit part (1 - cos)/2, the phase glyph (PSYB).
    rows: the MOON and AGE lines (47 33 standard font; the T21 footer of Free42 NAVLITTLE: 43 29)."""
    return ['RCL 10', NEW0, '-', LUN, 'MOD', 'STO 19',
            'RCL 19', LUN, '÷', '360', '×', 'COS', '1', 'X<>Y', '-', '50', '×', 'STO 21',
            '"WAXING"', 'STO 43', 'RCL 19', '14.765', 'X<Y?', 'XEQ 28', 'RCL 21', '99.5', 'X≤Y?', 'XEQ 23', 'RCL 21', '0.5', 'X>Y?', 'XEQ 24',
            str(rows[0]), str(MX), '"MOON "', 'XEQ "PTXS"', 'RCL 21', 'XEQ "PINS"', '"% "', 'XEQ "PTXS"', 'STO 25', 'R↓', 'STO 20',
            'RCL 19', LUN, '÷', '8', '×', '0.5', '+', 'IP', '8', 'MOD', '48', '+', 'STO 23',
            'RCL 20', 'RCL 25', 'XEQ IND 23', 'XEQ "PSYB"', '" "', 'XEQ "PTXS"', 'RCL 43', 'XEQ "PTXS"',
            str(rows[1]), str(MX), '"AGE "', 'XEQ "PTXS"', 'RCL 19', 'XEQ "PF1S"', '" DAYS"', 'XEQ "PTXS"']


def views(moon=False):
    """ALMF and HALMV in ATEXT for the DM42 (no Moon, no planets); moon: the Moon line of
    moon_lines() instead of the note NO MOON - NO PLANETS."""
    A = read_big('ALMF')
    note_x = 398 - V.width('NO MOON - NO PLANETS')
    A = D.cut(A, '"WAXING"', '"S"', moon_lines() if moon else ['47', str(note_x), '"NO MOON - NO PLANETS"', 'XEQ "PTXS"',
                                                                '33', str(note_x), '"DM42 BETA"', 'XEQ "PTXS"'])
    if moon:
        k = A.index('END')
        A[k:k] = [x for d in range(8) for x in ('LBL %d' % (48 + d), '"%d"' % d, 'RTN')]
    A = unused_locals(no_moon(A, 'ALMF'))
    H = read_big('HALMV')
    H = unused_locals(no_moon(H, 'HALMV'))
    for L in (A, H):
        assert not any(l in ('XEQ "MOO2"', 'XEQ "PLN3"', 'XEQ "PHA2"', 'XEQ "PTXT"') for l in L)
    return A, H


def nav_menu(L):
    """NAV12: the top line of the menu for the standard font."""
    T = V.top_x()
    s = '\n' + '\n'.join(L) + '\n'
    for a, b in (((206, 80), (206, T['time'])), ((206, 116, '"UT"'), (206, T['UT'], '"UT"')),
                 ((206, 150, '"DR"'), (206, T['DR'], '"DR"')), ((206, 174), (206, T['N'])), ((206, 176), (206, T['lat'])),
                 ((206, 244), (206, T['E'])), ((206, 246), (206, T['lon']))):
        a = '\n' + '\n'.join(map(str, a)) + '\n'; b = '\n' + '\n'.join(map(str, b)) + '\n'
        assert a in s, a
        s = s.replace(a, b)
    return s.strip('\n').split('\n')


def assemble(nav, p):
    q = dict(p)
    font = navopt.pdts(navopt.phls(navopt.fonts(D.ptxb_as_ptxs())))
    q['PTXS'] = AC.printers(font, S)
    q['PSYM'] = AC.symbols(font, '@*')                        # the Sun and a star, 5 x 7 glyphs
    q['PSYB'] = glyphs47.program('PSYB', glyphs47.PHASES, ws=16)   # NAVLITTLE_PH: the Moon phases
    keep = B.KEEP[:B.KEEP.index('PTXT')] + ['PSYM', 'PSYB'] + B.KEEP[B.KEEP.index('PTXT') + 1:]
    need = B.closure(q, [c for c in B.calls(nav) if c != 'INIT'])
    assert 'PTXT' not in need, 'the small font is still called'
    return nav + [l for n in keep if n in need for l in q[n]], sorted(need)


def main():
    A, H = views()
    builds = D.builds()
    res = {}
    AM, _ = views(moon=True)
    for name in ('NAVLITTLE', 'NAV1T_DM42', 'NAV12_DM42', 'NAVLITTLE_PH'):
        nav, p = builds[name.replace('_PH', '')]
        p = dict(p)
        p['ALMF'] = AM if name.endswith('_PH') else A
        if name == 'NAV12_DM42':
            p['HALMV'] = H
            nav = nav_menu(nav)
        L, need = assemble(nav, p)
        atx = name if name.endswith('_PH') else name.replace('_DM42', '') + '_ATX'
        B.write(os.path.join(SRC, atx + '.txt'), L)
        m = B.fixed_map(atx, L, keep=('NAV', 'INIT'))
        B.write(os.path.join(OUT, atx + '.txt'), B.rename_keep(L, m, ('NAV', 'INIT')))
        with open(os.path.join(OUT, atx + '_LABELS.txt'), 'w', encoding='utf-8') as fh:
            fh.write('%s - program labels (NAV keeps its name; INIT is NAVINIT_LITTLE)\n\n' % atx)
            fh.write('NAV     NAV     %s\n' % B.LABEL_TEXT['NAV'])
            fh.write('\n'.join('%s     %-7s %s' % (v, k, LABELS.get(k, B.LABEL_TEXT.get(k, ''))) for k, v in m.items()) + '\n')
        res[atx] = (L, need)
    print('%-13s %7s %8s' % ('file', 'lines', 'bytes'))
    for name, (L, need) in res.items():
        print('%-13s %7d %8d   %s' % ((name,) + B.size(L) + (' '.join(need),)))
    return res


if __name__ == '__main__':
    main()
