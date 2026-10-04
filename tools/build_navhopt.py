#!/usr/bin/env python3
"""build_navhopt.py - DEV: NAVFULL_OPT and MOON47_OPT (tools/build_navopt.py) with the counted loops on ISG
(tools/navhopt.py), for the C47 and Free42. The matrices, NAVINIT and TBL are those of build/dev/opt/.

  build/dev/hopt/NAVFULL_HOPT.txt (.p47)           C47 / R47 (and the DM42 with the C47 firmware)
  build/dev/hopt/src/NAVFULL_HOPT.txt              the same with the original program names (tests)
  build/dev/hopt/free42/NAVFULL_HOPT.txt (.raw)    Free42 (src/: original names)
  build/dev/hopt/MOONFAST_HOPT.txt (.p47)          MOON47 (the program keeps its name MOON47)
  build/dev/hopt/free42/MOONFAST_HOPT.txt (.raw)
  build/dev/hopt/NAVFULL_RSAVE.txt (.p47)          C47: NAVFULL_HOPT with its registers renumbered from R00
                                                   (R00-R45), saved at the start of NAV and restored at the end
  build/dev/hopt/src/NAVFULL_RSAVE.txt             the same with the original program names (tests)
  build/dev/hopt/NAVFULL_RSAVE_SPLIT.txt (.p47)    RSAVE with the menu 1 ALMANAC 2 SPLIT 3 SKY 4 ANIM 5 ALLSKY 6 INFO (no CHART)
  build/dev/hopt/NAVFULL_LOCR.txt (.p47)           C47: the values of each subroutine level in local registers, the
                                                   rest R00-R32 saved and restored; 7 internal labels numeric
  build/dev/hopt/NAVFULL_LOCR_SEQ.txt (.p47)       the same with the labels N01 .. N44 in order (NAVFULL_LOCR_SEQ_LABELS.txt)
  build/dev/hopt/MOONFAST_R31.txt (.p47)           C47: MOONFAST_HOPT with its registers renumbered into R00-R30
                                                   (tools/regalloc.py), saved in local registers at the start
                                                   and restored at the end: every register stays as it was
  build/dev/hopt/MOONFAST_LOCR.txt (.p47)          C47: every value in local registers (LocR) of the level that
                                                   uses it, but the key of KEY? (R00, saved and restored)
  build/dev/hopt/MOONFAST_HOPT_T / _R31_T / _LOCR_T.txt (.p47)   the same three with a timer for the real C47:
                                                   TICKS at the start and just before the first key wait; the
                                                   time to draw the page in "TDRW" (tenths of a second)

  python3 tools/build_navhopt.py          then python3 tests/test_navhopt.py (parity and statistics)
"""
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_navopt as N                                                     # noqa: E402
import navhopt                                                               # noqa: E402

OUT = os.path.join(N.ROOT, 'build', 'dev', 'hopt')


def c47():
    return N.c47(True, post=lambda L: navhopt.inputs(navhopt.loops(L)))


def c47_rsave():
    return N.c47(True, post=lambda L: navhopt.nav_regs(navhopt.inputs(navhopt.loops(L))))


def c47_rsave_split():
    """NAVFULL_RSAVE_SPLIT: RSAVE with the menu 1 ALMANAC 2 SPLIT 3 SKY 4 ANIM 5 ALLSKY 6 INFO (no CHART)."""
    return N.c47(True, post=lambda L: navhopt.nav_regs(navhopt.inputs(navhopt.loops(L))), menu=N.SPLIT2)


def c47_locr():
    """(long names, short labels, globals, locals) of NAVFULL_LOCR."""
    info = {}

    def post(L):
        out, info['k'], info['nloc'] = navhopt.nav_locr(navhopt.inputs(navhopt.loops(L)))
        return out
    full, short = N.c47(True, post=post)
    return full, short, info['k'], info['nloc']


def sequential(full):
    """Short labels N01, N02 ... in the order of the listing (NAV keeps its name): NAVFULL_LOCR_SEQ.
    Only the names differ from NAVFULL_LOCR (fixed map tools/labels/NAVFULL.map, with gaps)."""
    names = [l[5:-1] for l in full if l.startswith('LBL "') and l != 'LBL "NAV"']
    m = {n: 'N%02d' % (k + 1) for k, n in enumerate(names)}
    return N.B.rename(full, m), m


def free42():
    return N.free42(True, post=navhopt.loops)


def moon47():
    import build_moon47 as M
    import moon47_opt
    plain, f42 = moon47_opt.build(M)
    return navhopt.moon(plain), navhopt.moon(f42)


def moon_regs(local):
    """(listing, global registers, {entry: local registers}): R31 (local=False) or LOCR (no global register)."""
    if local:
        L, nloc, k = navhopt.moon_locr(moon47()[0])
        return L, k, nloc
    return navhopt.moon_regs(moon47()[0], local)


def timed(L):
    """A timing copy: TICKS at the start (in "T0"), and before the label of the first key wait (PAUSE 50) the
    time since then in "TDRW" (1/10 s; the stack as it was: STO, DROP)."""
    L = list(L)
    i = L.index('LBL "MOON47"') + 1
    L[i:i] = ['TICKS', 'STO "T0"', 'DROP']
    p = L.index('PAUSE 50')
    assert L[p - 1].startswith('LBL ')
    L[p - 1:p - 1] = ['TICKS', 'RCL "T0"', '-', 'STO "TDRW"', 'DROP']
    return L


def main():
    full, short = c47()
    N.B.write(os.path.join(OUT, 'src', 'NAVFULL_HOPT.txt'), full)
    N.B.write(os.path.join(OUT, 'NAVFULL_HOPT.txt'), short)
    full, short = c47_rsave()
    N.B.write(os.path.join(OUT, 'src', 'NAVFULL_RSAVE.txt'), full)
    N.B.write(os.path.join(OUT, 'NAVFULL_RSAVE.txt'), short)
    full, short = c47_rsave_split()
    N.B.write(os.path.join(OUT, 'src', 'NAVFULL_RSAVE_SPLIT.txt'), full)
    N.B.write(os.path.join(OUT, 'NAVFULL_RSAVE_SPLIT.txt'), short)
    full, short, k, nloc = c47_locr()
    N.B.write(os.path.join(OUT, 'src', 'NAVFULL_LOCR.txt'), full)
    N.B.write(os.path.join(OUT, 'NAVFULL_LOCR.txt'), short)
    print('build/dev/hopt/NAVFULL_LOCR.txt: globals R00-R%02d (saved and restored), %d local registers in %d routines, '
          '%d global labels' % (k - 1, sum(nloc.values()), len(nloc), sum(1 for l in full if l.startswith('LBL "'))))
    seq, m = sequential(full)
    N.B.write(os.path.join(OUT, 'NAVFULL_LOCR_SEQ.txt'), seq)
    with open(os.path.join(OUT, 'NAVFULL_LOCR_SEQ_LABELS.txt'), 'w', encoding='utf-8') as fh:
        fh.write('NAVFULL_LOCR_SEQ (C47) - program labels in order (NAV keeps its name)\n\n')
        fh.write('\n'.join('%s  %s' % (v, k) for k, v in m.items()) + '\n')
    short, named = free42()
    N.B.write(os.path.join(OUT, 'free42', 'NAVFULL_HOPT.txt'), short)
    N.B.write(os.path.join(OUT, 'free42', 'src', 'NAVFULL_HOPT.txt'), named)
    plain, f42 = moon47()
    N.B.write(os.path.join(OUT, 'MOONFAST_HOPT.txt'), plain)
    N.B.write(os.path.join(OUT, 'free42', 'MOONFAST_HOPT.txt'), f42)
    for name, local in (('MOONFAST_R31', False), ('MOONFAST_LOCR', True)):
        L, n, nloc = moon_regs(local)
        N.B.write(os.path.join(OUT, name + '.txt'), L)
        print('build/dev/hopt/%s.txt: %s, %d local registers in %d routines'
              % (name, 'globals R00-R%02d' % (n - 1) if n else 'no global register', sum(nloc.values()), len(nloc)))
    for name in ('MOONFAST_HOPT', 'MOONFAST_R31', 'MOONFAST_LOCR'):
        L = [l for l in open(os.path.join(OUT, name + '.txt'), encoding='utf-8').read().split('\n') if l]
        N.B.write(os.path.join(OUT, name + '_T.txt'), timed(L))
    for f in ('NAVFULL_HOPT.txt', 'NAVFULL_RSAVE.txt', 'NAVFULL_RSAVE_SPLIT.txt', 'NAVFULL_LOCR.txt', 'NAVFULL_LOCR_SEQ.txt', 'MOONFAST_HOPT.txt', 'MOONFAST_R31.txt', 'MOONFAST_LOCR.txt',
              'MOONFAST_HOPT_T.txt', 'MOONFAST_R31_T.txt', 'MOONFAST_LOCR_T.txt'):
        n = N.p47(os.path.join(OUT, f))
        print('%-32s %s' % ('build/dev/hopt/' + f, '.p47 %d bytes' % n if n else '(no rejig: no .p47)'))
        if os.path.exists(os.path.join(OUT, 'free42', f)):
            n = N.raw(os.path.join(OUT, 'free42', f))
            print('%-32s %s' % ('build/dev/hopt/free42/' + f, '.raw %d bytes' % n if n else '(no f42run: no .raw)'))


if __name__ == '__main__':
    main()
