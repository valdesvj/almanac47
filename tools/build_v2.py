#!/usr/bin/env python3
"""build_v2.py - the release files of Almanac 47 v2.0.0, from the optimized pipeline (tools/build_navopt.py,
tools/navhopt.py, tools/regalloc.py; docs/OPTIMIZATIONS.md):

  build/NAVFULL.txt (.p47)        C47 / R47: the engine with Horner and n-vectors, the loops on ISG, the registers
                                  renumbered (R00-R45) and saved in local registers while NAV runs; menu 1 ALMANAC
                                  2 SPLIT 3 SKY 4 ANIM 5 ALLSKY 6 INFO 9 SNAP 0 END, ↑↓ ±1 HOUR; clean input prompts
  build/NAVINIT_FULL / _FAST, TBL_1 / TBL_5 (.p47)   the matrices and tables, only their message left on the stack
  build/dm42/NAVLITTLE.txt (.p47) DM42 with the C47 firmware: the same engine, prompts and register save
  build/free42/NAVFULL / NAVLITTLE / NAVINIT_* / TBL_* (.txt, .raw)   Free42 (DM42 stock firmware): the same
                                  screens; the registers renumbered and the user's REGS (and SIZE) saved in "NBAK"
NAVTXT (the text page) is not in v2.0.0.

  python3 tools/build_v2.py          then python3 tests/test_v2.py
"""
import contextlib, io, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path[:0] = [HERE, os.path.join(HERE, 'generators'), os.path.join(ROOT, 'python')]
import build_navopt as N                                                     # noqa: E402
import build_navhopt as H                                                    # noqa: E402
import navhopt                                                               # noqa: E402

B = N.B
OUT = os.path.join(ROOT, 'build')


def labels_file(path, full, short, title):
    m = [(b[5:-1], a[5:-1]) for a, b in zip(full, short) if a.startswith('LBL "')]
    with open(path, 'w', encoding='utf-8') as fh:
        fh.write('%s - program labels (NAV keeps its name)\n\n' % title)
        fh.write('\n'.join('%s  %s' % (s, l) for s, l in m) + '\n')


def c47():
    full, short = H.c47_rsave_split()
    B.write(os.path.join(OUT, 'NAVFULL.txt'), short)
    B.write(os.path.join(OUT, 'dev', 'src', 'NAVFULL.txt'), full)          # the same with the routine names (tests)
    labels_file(os.path.join(OUT, 'NAVFULL_LABELS.txt'), full, short, 'NAVFULL v2.0.0 (C47 / R47)')
    for k, L in N.inits().items():
        if not k.startswith('F42_'):
            B.write(os.path.join(OUT, 'NAVINIT_%s.txt' % k), L)
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
        L = navhopt.nav_regs(navhopt.inputs(navhopt.loops(L)))
        m = B.fixed_map('NAVLITTLE', L, keep=('NAV', 'INIT'))
        short = B.rename_keep(L, m, ('NAV', 'INIT'))
        init = N.init_clean(D.init_dm42())
    B.write(os.path.join(OUT, 'dm42', 'NAVLITTLE.txt'), short)
    labels_file(os.path.join(OUT, 'dm42', 'NAVLITTLE_LABELS.txt'), L, short, 'NAVLITTLE v2.0.0 (DM42 with the C47 firmware)')
    B.write(os.path.join(OUT, 'dm42', 'NAVINIT_LITTLE.txt'), init)
    return L


# Free42: the C47 menu; its PTXS has no ↑ ↓ ±: the strings use [ _ ` and PTXS gets those three glyphs from the
# C47 standardFont (the same columns and widths as GRFNT 21: the screens match the C47 ones); ↑ [ 91, ↓ _ 95, ± ` 96
F42_HINT = 'KEY A NUMBER    + MENU    [_ `1 HOUR'


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

    def post(L):
        L, info['k'] = navhopt.f42_regs(navhopt.f42_inputs(navhopt.loops(L)))
        return L
    short, named = N.free42(True, post=post, menu=menu)
    B.write(os.path.join(OUT, 'free42', 'NAVFULL.txt'), short)
    B.write(os.path.join(OUT, 'free42', 'dev', 'src', 'NAVFULL.txt'), named)
    labels_file(os.path.join(OUT, 'free42', 'NAVFULL_LABELS.txt'), named, short, 'NAVFULL v2.0.0 (Free42)')
    kfull = info['k']
    short, named, init = N.free42(True, post=post, menu=menu, little=True)
    B.write(os.path.join(OUT, 'free42', 'NAVLITTLE.txt'), short)
    B.write(os.path.join(OUT, 'free42', 'dev', 'src', 'NAVLITTLE.txt'), named)
    labels_file(os.path.join(OUT, 'free42', 'NAVLITTLE_LABELS.txt'), named, short, 'NAVLITTLE v2.0.0 (Free42)')
    B.write(os.path.join(OUT, 'free42', 'NAVINIT_LITTLE.txt'), init)
    for k, L in N.inits().items():
        if k.startswith('F42_'):
            B.write(os.path.join(OUT, 'free42', 'NAVINIT_%s.txt' % k[4:]), L)
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
