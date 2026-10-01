#!/usr/bin/env python3
"""build_navfull_atext.py - EXPERIMENTAL: NAVFULL with ATEXT for the texts and numbers.

The views from tools/generators/atext/genviews_atx.py (programs/atext/): the same calculations
as NAVFULL, the columns and rows made for the C47's standard font. The body symbols (Sun, Moon,
planets, stars) keep the AGRAPH glyphs of the status-bar font (PSYM); the charts keep NAVFULL's
look with the small 3 x 5 font (PTXT, PTNS) for the axes, N E S W, OVER / UNDER HORIZON, the
ALLSKY stars and the SKY DR line. The warning line only in the menu and INFO (and on the TEXT
page in the registers), not on the views.

The text routines (atext_common.py) keep their stack, Z row of the base line, Y column, X text
or number: PTXS is the N03 trick of Didier (dlachieze), the only ATEXT step; the number printers
put the number together in R49 (alpha-IP / x->alpha) and write it with one ATEXT.

  python3 tools/build_navfull_atext.py   -> build/atext/NAVFULL_ATX.txt (+ labels, src/);
                                            .p47: tools/rejig47_atext.py
"""
import os, sys, re, io, contextlib, shutil

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path[:0] = [HERE, os.path.join(HERE, 'generators'), os.path.join(HERE, 'generators', 'atext'), os.path.join(ROOT, 'python')]
import build_navfull as B
import navopt, gencache
import genviews_atx as V
import atext_common as AC

OUT = os.path.join(ROOT, 'build', 'atext')
SRC = os.path.join(OUT, 'src')
P47 = os.path.join(ROOT, 'build', 'p47', 'atext')
SYMBOLS = '@(*<>=?'
ATX_VIEWS = ('ALMF', 'HALMV', 'HORZ', 'HALMH', 'HANIM', 'ALLSKY')


LABELS = {'PTTY': 'text in the tinyFont (GRFNT 10) - Z row of the base line, Y column, X text',
          'PTNT': 'whole number in the tinyFont - Z row, Y column, X number',
          'PTXS': 'TEXT with ATEXT (standard font; Didier\'s N03 trick) and the number printers - Z row, Y column, X text or number',
         'PSYM': 'the AGRAPH symbols of the bodies - Z row, Y column, X symbol'}


ITEMS = ['ALMANAC', 'CHART', 'TEXT', 'SKY', 'SPLIT', 'ANIM', 'ALLSKY', 'INFO']      # no 5 SMALL: renumbered
VIEWS = ['ALMF', 'HALMV', 'ALMT', 'HORZ', 'HALMH', 'HANIM', 'ALLSKY', None]


def nav_atx():
    """NAV (gennav) with the menu of NAVFULL_ATX (8 items, no SMALL), the top line of the menu for
    the standard font, the SINKING box text centred."""
    import gennav
    old = gennav.ITEMS, gennav.VIEWS
    gennav.ITEMS, gennav.VIEWS = ITEMS, VIEWS
    try:
        L = [str(l) for l in gennav.program(gennav.inputs(), list(range(1, len(ITEMS) + 1)))]
    finally:
        gennav.ITEMS, gennav.VIEWS = old
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


def build(tiny=False):
    """tiny: NAVFULL_TNY, the small AGRAPH font (PTXT, PTNS) replaced by the C47 tinyFont with
    ATEXT (GRFNT 10: PTTY, PTNT); the views from programs/atext/tiny/."""
    progs = {n: B.read(n) for n in B.KEEP if n != 'ALMS'}
    for n in ATX_VIEWS:
        with open(os.path.join(ROOT, 'programs', 'atext', 'tiny' if tiny else '', n + '.txt'), encoding='utf-8') as fh:
            progs[n] = [l.rstrip('\n') for l in fh if l.strip()]
    progs['ALMT'] = B.almr(progs['ALMT'])
    progs['CACHE'] = gencache.program(True)
    progs['STXT'] = navopt.stxt(progs['STXT'])
    for n in gencache.VIEWS:
        if n in progs:
            progs[n] = gencache.swap(progs[n])
    font = navopt.pdts(navopt.phls(navopt.fonts(B.read('PTXS'))))
    progs['PTXS'] = AC.printers(font, '49', tiny)            # R49: free while a view draws (SBRT / SNMU use it before)
    progs['PSYM'] = AC.symbols(font, SYMBOLS)
    # the small font: chart axes and letters, OVER / UNDER HORIZON, the ALLSKY stars, T S X, the SKY DR line
    small = set('0123456789 NESWTSX*' + 'OVER HORIZON' + 'UNDER HORIZON')
    progs['PTXT'] = B.trim_font(navopt.fonts(B.read('PTXT')), small)
    if tiny:
        del progs['PTXT']
    nav = nav_atx()
    keep = B.KEEP[:B.KEEP.index('PTXT') + 1] + ['PSYM'] + B.KEEP[B.KEEP.index('PTXT') + 1:]
    need = B.closure(progs, [c for c in B.calls(nav) if c != 'INIT'])
    full = nav + [l for n in keep if n in need for l in progs[n]]
    assert not (tiny and {'PTXT', 'PTNS'} & set(B.calls(full)))
    return full, sorted(need)


def main(tiny=False):
    name = 'NAVFULL_TNY' if tiny else 'NAVFULL_ATX'
    full, need = build(tiny)
    B.write(os.path.join(SRC, name + '.txt'), full)
    m = B.fixed_map(name, full)
    B.write(os.path.join(OUT, name + '.txt'), B.rename(full, m))
    with open(os.path.join(OUT, name + '_LABELS.txt'), 'w', encoding='utf-8') as fh:
        fh.write('%s - program labels (NAV keeps its name; INIT: NAVINIT_FULL or NAVINIT_FAST)\n\n' % name)
        fh.write('NAV     NAV     %s\n' % B.LABEL_TEXT['NAV'])
        fh.write('\n'.join('%s     %-7s %s' % (v, k, LABELS.get(k, B.LABEL_TEXT.get(k, ''))) for k, v in m.items()) + '\n')
    print('%-12s %7d %8d   %s' % ((name,) + B.size(full) + (' '.join(need),)))
    return full


if __name__ == '__main__':
    main()
    main(tiny=True)
