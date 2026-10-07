#!/usr/bin/env python3
"""build_v2.py - the release files of Almanac 47 (v2.1.0 "Supercharger"), from the optimized pipeline
(tools/build_navopt.py, tools/navhopt.py, tools/regalloc.py, tools/navmat.py; docs/OPTIMIZATIONS.md):

  build/NAVFULL.txt (.p47)        C47 / R47: the engine with Horner and n-vectors, the loops on ISG, the registers
                                  renumbered, the frequent numbers in registers after them (R00-R98, cleared with
                                  CLREGS when NAV ends); ONE program, NAV its only global label, the routines local
                                  labels with their names (tools/local_labels.py); menu 1 ALMANAC
                                  2 SPLIT 3 SKY 4 ANIM 5 ALLSKY 6 INFO 0 END, ↑↓ ±1 HOUR, 9 SNAP; clean input prompts;
                                  the SINKING....ABOUT box (and the ants, flag 47) while each view is computed, the
                                  view shown when it is complete; SKY names a body every 2 s
  build/NAVINIT_FULL / _FAST, TBL_1 / TBL_5 (.p47)   the matrices and tables, only their message left on the stack
  build/dm42/NAVLITTLE.txt (.p47) DM42 with the C47 firmware: the same engine, prompts and register save; the
                                  ALMANAC screen drawn as it goes
  build/free42/NAVFULL / NAVLITTLE / NAVINIT_* / TBL_* (.txt, .raw)   Free42 (DM42 stock firmware): the same
                                  screens; the registers renumbered and the user's REGS (and SIZE) saved in "NBAK";
                                  NAVFULL: the box only at the start
NAVTXT (the text page) is not in v2.x. tools/navmat.py: the calculation and size passes of v2.1.0.

  python3 tools/build_v2.py          then python3 tests/test_v2.py
"""
import contextlib, io, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path[:0] = [HERE, os.path.join(HERE, 'generators'), os.path.join(ROOT, 'python')]
import build_navopt as N                                                     # noqa: E402
import navhopt                                                               # noqa: E402
import navmat                                                                # noqa: E402

B = N.B
OUT = os.path.join(ROOT, 'build')


# what the routines do in v2.0.0 where it differs from build_navfull.LABEL_TEXT (the menu numbers, the registers)
V2_TEXT = {
 'NAV':    'graphic menu (KEY?): asks DATE UTC LAT LON, keys 1-5 a view, 6 INFO, 9 SNAP, 0 ends; uses R00-R98 and '
           'clears them (CLREGS) at 0 (the only global label; INFO page inside)',
 'ALMF':   'view 1 ALMANAC: GHA, Dec, Hc, Zn table of Sun, Moon, planets, stars; twilight, rise/set, Moon',
 'HALMH':  'view 2 SPLIT: horizon chart on top, the bodies below (8 rows)',
 'HORZ':   'view 3 SKY: horizon chart, the name of each body in turn every 2 s (+ back to the menu, arrows one hour)',
 'HANIM':  'view 4 ANIM: the Sun and the Moon moving on the whole-sky chart (24 frames)',
 'ALLSKY': 'view 5 ALLSKY: whole sky, over the horizon above, under the horizon below',
 'HDR':    'header of a view: date, UT, DR latitude N/S, longitude E/W (X row, Y time, Z lat, T lon; tools/navmat.py)',
 'CMN':    'compass row N E S W N of a chart (X row)',
 'CMS':    'compass row S W N E S of a chart, south up (X row)',
}
HEADER = ('Label on the calculator, original name (sources, build/dev/src/, documentation), what it does.\n'
          'Only NAV keeps its name. TEXT = a text routine, SYMBOL = a body symbol drawn with AGRAPH: Z = row of the\n'
          'base line (0 = bottom), Y = column, X = text, number or symbol; returns Y = row, X = next column.\n'
          'The numbers missing here belong to routines of older versions.\n\n')


# the routines that draw a text, a number or a symbol (programs/atext/t21, glyphs47)
DRAW = ('PTXS', 'PDMS', 'PHMS', 'PDTS', 'PSYS', 'PSYB', 'PTNT', 'PTTY', 'PINS', 'PF1S', 'PZNS', 'PHLS')


def programs(L):
    """[(name, first line, END line)] of a named listing."""
    out, start, name = [], None, None
    for i, l in enumerate(L):
        m = re.fullmatch(r'LBL "(.+)"', l)
        if m and start is None:
            start, name = i, m.group(1)
        if l == 'END' and start is not None:
            out.append((name, start, i))
            start = None
    return out


def box_at_start(L):
    """NAV: the SINKING....ABOUT box (LBL 48) only the first time, before the menu; the views, the way back to the
    menu and the arrows show their own drawing (C47: live(); Free42 draws on the LCD as it goes)."""
    out, n = list(L), 0
    for name, a, b in reversed(programs(L)):
        if name == 'NAV':
            calls = [i for i in range(a, b) if L[i] == 'XEQ 48']
            for i in reversed(calls[1:]):
                del out[i]
                n += 1
    assert n > 1, 'build_v2: no XEQ 48 in NAV'
    return out


def live(L, views=('ALMF', 'HALMH', 'HORZ', 'HANIM', 'ALLSKY')):
    """C47: PAUSE 0 (the screen to the LCD, no wait) after every drawing call in the views, so a view appears while
    it is drawn, as on Free42. The C47 sends its screen to the LCD only at a PAUSE, a key or the end of the program
    (programming/input.c, lcd_refresh in fnPause). One per text and per body symbol, not per PIXEL."""
    out, n = list(L), 0
    calls = ['XEQ "%s"' % d for d in DRAW]
    for name, a, b in reversed(programs(L)):
        if name in views:
            for i in range(b - 1, a, -1):
                if L[i] in calls:
                    out.insert(i + 1, 'PAUSE 0')
                    n += 1
    assert n > 30, 'build_v2: few drawing calls (%d)' % n
    return out


def pi(L, name):
    """NAVINIT: the planet series' phase 3.14159265359 (VSOP87 prints π to 11 decimals) as the firmware's π."""
    return [name if l in ('3.14159265359', '𝜋', 'PI') else l for l in L]


def labels_file(path, full, short, title, text=None):
    """NAME_LABELS.txt: label, routine name and what it does (build_navfull.LABEL_TEXT, then V2_TEXT, then text)."""
    t = dict(B.LABEL_TEXT)
    t.update(V2_TEXT)
    t.update(text or {})
    m = [(b[5:-1], a[5:-1]) for a, b in zip(full, short) if a.startswith('LBL "')]
    t.update({l: 'steps shared by several routines (tools/navmat.py outline)' for s, l in m if re.fullmatch(r'OUT\d+', l)})
    with open(path, 'w', encoding='utf-8') as fh:
        fh.write('%s - program labels\n%s\n%s' % (title, '=' * (len(title) + 17), HEADER))
        fh.write('\n'.join('%-7s %-7s %s' % (s, l, t.get(l, '')) for s, l in m) + '\n')


HEADER_LOCAL = ('NAVFULL is ONE program: NAV is its only global label, every routine a local label with its name\n'
                '(LBL :SUNA:, tools/local_labels.py), so none of them is in the program menus. TEXT = a text routine,\n'
                'SYMBOL = a body symbol drawn with AGRAPH: Z = row of the base line (0 = bottom), Y = column,\n'
                'X = text, number or symbol; returns Y = row, X = next column. :L1: .. are inner labels (no name).\n\n')


# the C47 NAVFULL (v2.2.0) where LABEL_TEXT names registers of the separate programs
LOCAL_TEXT = {
 'HCZ':  'sight reduction: Y = Dec, X = GHA (and the DR: R13 longitude, R14 latitude) -> X = Hc, Y = Zn (also in R09, '
         'R05), sin Hc in "V4"',
 'CSTR': 'star from the cache: its values after the over-the-horizon test (:CSQK:)',
}


def labels_local(path, full, title):
    """NAVFULL_LABELS.txt of the one-program build: each routine's local label and what it does."""
    t = dict(B.LABEL_TEXT)
    t.update(V2_TEXT)
    t.update(LOCAL_TEXT)
    names = [l[5:-1] for l in full if l.startswith('LBL "')]
    t.update({n: 'steps shared by several routines (tools/navmat.py outline)' for n in names if re.fullmatch(r'OUT\d+', n)})
    with open(path, 'w', encoding='utf-8') as fh:
        fh.write('%s - program labels\n%s\n%s' % (title, '=' * (len(title) + 17), HEADER_LOCAL))
        fh.write('\n'.join('%-9s %s' % ('NAV' if n == 'NAV' else ':%s:' % n, t.get(n, '')) for n in names) + '\n')


def c47():
    import local_labels
    full, short = N.c47(True, menu=N.SPLIT2,
                        post=lambda L: navmat.size(navhopt.nav_regs(navhopt.inputs(navhopt.loops(navmat.c47(L))))))
    # one program, the routines as local labels with their names, no register save: CLREGS at the end
    B.write(os.path.join(OUT, 'NAVFULL.txt'), local_labels.convert(full, ('NAV',), nav=True))
    B.write(os.path.join(OUT, 'dev', 'src', 'NAVFULL.txt'), full)          # global names, the registers saved (tests)
    labels_local(os.path.join(OUT, 'NAVFULL_LABELS.txt'), full, 'NAVFULL v2.2.0 (C47 / R47)')
    for k, L in N.inits().items():
        if not k.startswith('F42_'):
            B.write(os.path.join(OUT, 'NAVINIT_%s.txt' % k), pi(L, '𝜋'))
    for k, L in N.tbls().items():
        if not k.startswith('F42_') and k != 'TBL_50':
            B.write(os.path.join(OUT, k + '.txt'), L)
    return full


def dm42():
    """build/dm42/NAVLITTLE (DM42 with the C47 firmware) and NAVINIT_LITTLE: the optimized engine, the clean
    prompts, the registers renumbered and saved while NAV runs."""
    import build_dm42 as D
    with N.optimized(True), contextlib.redirect_stdout(io.StringIO()):
        nav, progs = D.builds()['NAVLITTLE']
        L, need = D.assemble(nav, progs)
        L = B.keywait(L)
        L = navmat.size(live(navhopt.nav_regs(navhopt.inputs(navhopt.loops(navmat.little(L)))), views=('ALMF',)))
        m = B.fixed_map('NAVLITTLE', L, keep=('NAV', 'INIT'))
        short = B.rename_keep(L, m, ('NAV', 'INIT'))
        init = N.init_clean(D.init_dm42())
    B.write(os.path.join(OUT, 'dm42', 'NAVLITTLE.txt'), short)
    little = dict(D.LABEL_TEXT, NAV='no menu: asks DATE UTC LAT LON, then the ALMANAC screen; up / down one hour, + ends; '
                  'your registers R00-R35 saved at the start and given back at the end')
    labels_file(os.path.join(OUT, 'dm42', 'NAVLITTLE_LABELS.txt'), L, short, 'NAVLITTLE v2.1.0 (DM42 with the C47 firmware)', little)
    B.write(os.path.join(OUT, 'dm42', 'NAVINIT_LITTLE.txt'), init)
    return L


# Free42: the C47 menu; its PTXS has no ↑ ↓ ±: the strings use [ _ ` and PTXS gets those three glyphs from the
# C47 standardFont (the same columns and widths as GRFNT 21: the screens match the C47 ones); ↑ [ 91, ↓ _ 95, ± ` 96;
# key 9 prints the screen (PRLCD) where the C47 has SNAP
F42_HINT = 'KEY A NUMBER   + MENU   [_ `1 HOUR   9 PRLCD'


def f42_glyphs():
    from stdfont import STD, code
    out = {}
    for ch, c in (('↑', 91), ('↓', 95), ('±', 96)):     # under 100 (a Free42 label is 00-99), as typed ('^' is 30 on Free42)
        cb, cg, ca, ra, rg, rb, rows = STD[code(ch)]
        px = {(cb + x, rb + rg - 5 - r) for r, v in enumerate(rows) for x in range(cg) if v >> (cg - 1 - x) & 1}
        assert min(y for x, y in px) >= 0
        cols = {}
        for x, y in px:
            cols[x] = cols.get(x, 0) | 1 << y
        out[c] = (cols, cb + cg + ca - 1)
    return out


def free42():
    """build/free42/: NAVFULL and NAVLITTLE with the C47 screens, NAVINIT_FULL / _FAST / _LITTLE, TBL_1 / _5."""
    import build_free42 as F
    F.GLYPHS['PTXS'] = f42_glyphs()
    menu = dict(N.SPLIT2, **N.C47_MENU)
    menu['HINT'] = F42_HINT
    info = {}

    def post(L, little=False):
        L, info['k'] = navhopt.f42_regs(navhopt.f42_inputs(navhopt.loops(navmat.free42(L, little))))
        return navmat.size42(L)
    short, named = N.free42(True, post=lambda L: box_at_start(post(L)), menu=menu)
    B.write(os.path.join(OUT, 'free42', 'NAVFULL.txt'), short)
    B.write(os.path.join(OUT, 'free42', 'dev', 'src', 'NAVFULL.txt'), named)
    labels_file(os.path.join(OUT, 'free42', 'NAVFULL_LABELS.txt'), named, short, 'NAVFULL v2.1.0 (Free42)',
                {'NAV': 'graphic menu (KEY?): asks DATE UTC LAT LON, keys 1-5 a view, 6 INFO, 9 SNAP (PRLCD), 0 ends; your '
                        'registers REGS and SIZE saved in NBAK and given back at 0 (the only named program; INFO page inside)'})
    kfull = info['k']
    short, named, init = N.free42(True, post=lambda L: post(L, True), menu=menu, little=True)
    B.write(os.path.join(OUT, 'free42', 'NAVLITTLE.txt'), short)
    B.write(os.path.join(OUT, 'free42', 'dev', 'src', 'NAVLITTLE.txt'), named)
    import build_dm42 as D
    labels_file(os.path.join(OUT, 'free42', 'NAVLITTLE_LABELS.txt'), named, short, 'NAVLITTLE v2.1.0 (Free42)',
                dict(D.LABEL_TEXT, NAV='no menu: asks DATE UTC LAT LON, then the ALMANAC screen; up / down one hour, '
                     '+ ends; REGS and SIZE saved in NBAK and given back'))
    B.write(os.path.join(OUT, 'free42', 'NAVINIT_LITTLE.txt'), init)
    for k, L in N.inits().items():
        if k.startswith('F42_'):
            B.write(os.path.join(OUT, 'free42', 'NAVINIT_%s.txt' % k[4:]), pi(L, 'PI'))
    for k, L in N.tbls().items():
        if k.startswith('F42_') and k != 'F42_TBL_50':
            B.write(os.path.join(OUT, 'free42', k[4:] + '.txt'), L)
    print('Free42: NAVFULL SIZE %d, NAVLITTLE SIZE %d' % (kfull, info['k']))


def sizes(files):
    for f in files:
        if f.endswith('.txt') and os.path.exists(f):
            if '/free42/' in f:
                n = N.raw(f)
                print('%-34s %s' % (os.path.relpath(f, ROOT), '.raw %d bytes' % n if n else '(no f42run)'))
            else:
                n = N.p47(f)
                print('%-34s %s' % (os.path.relpath(f, ROOT), '.p47 %d bytes' % n if n else '(no rejig)'))


def main():
    c47()
    dm42()
    free42()
    sizes([os.path.join(OUT, 'dm42', f) for f in ('NAVLITTLE.txt', 'NAVINIT_LITTLE.txt')])
    sizes([os.path.join(OUT, 'free42', f) for f in ('NAVFULL.txt', 'NAVLITTLE.txt', 'NAVINIT_FULL.txt', 'NAVINIT_FAST.txt',
                                                    'NAVINIT_LITTLE.txt', 'TBL_1.txt', 'TBL_5.txt')])
    sizes([os.path.join(OUT, f) for f in ('NAVFULL.txt', 'NAVINIT_FULL.txt', 'NAVINIT_FAST.txt', 'TBL_1.txt', 'TBL_5.txt')])


if __name__ == '__main__':
    main()
