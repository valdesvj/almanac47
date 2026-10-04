#!/usr/bin/env python3
"""build_navhopt.py - DEV: NAVFULL_OPT and MOON47_OPT (tools/build_navopt.py) with the counted loops on ISG
(tools/navhopt.py), for the C47 and Free42. The matrices, NAVINIT and TBL are those of build/dev/opt/.

  build/dev/hopt/NAVFULL_HOPT.txt (.p47)           C47 / R47 (and the DM42 with the C47 firmware)
  build/dev/hopt/src/NAVFULL_HOPT.txt              the same with the original program names (tests)
  build/dev/hopt/free42/NAVFULL_HOPT.txt (.raw)    Free42 (src/: original names)
  build/dev/hopt/MOONFAST_HOPT.txt (.p47)          MOON47 (the program keeps its name MOON47)
  build/dev/hopt/free42/MOONFAST_HOPT.txt (.raw)

  python3 tools/build_navhopt.py          then python3 tests/test_navhopt.py (parity and statistics)
"""
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_navopt as N                                                     # noqa: E402
import navhopt                                                               # noqa: E402

OUT = os.path.join(N.ROOT, 'build', 'dev', 'hopt')


def c47():
    return N.c47(True, post=navhopt.loops)


def free42():
    return N.free42(True, post=navhopt.loops)


def moon47():
    import build_moon47 as M
    import moon47_opt
    plain, f42 = moon47_opt.build(M)
    return navhopt.moon(plain), navhopt.moon(f42)


def main():
    full, short = c47()
    N.B.write(os.path.join(OUT, 'src', 'NAVFULL_HOPT.txt'), full)
    N.B.write(os.path.join(OUT, 'NAVFULL_HOPT.txt'), short)
    short, named = free42()
    N.B.write(os.path.join(OUT, 'free42', 'NAVFULL_HOPT.txt'), short)
    N.B.write(os.path.join(OUT, 'free42', 'src', 'NAVFULL_HOPT.txt'), named)
    plain, f42 = moon47()
    N.B.write(os.path.join(OUT, 'MOONFAST_HOPT.txt'), plain)
    N.B.write(os.path.join(OUT, 'free42', 'MOONFAST_HOPT.txt'), f42)
    for f in ('NAVFULL_HOPT.txt', 'MOONFAST_HOPT.txt'):
        n = N.p47(os.path.join(OUT, f))
        print('%-32s %s' % ('build/dev/hopt/' + f, '.p47 %d bytes' % n if n else '(no rejig: no .p47)'))
        n = N.raw(os.path.join(OUT, 'free42', f))
        print('%-32s %s' % ('build/dev/hopt/free42/' + f, '.raw %d bytes' % n if n else '(no f42run: no .raw)'))


if __name__ == '__main__':
    main()
