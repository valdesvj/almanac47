#!/usr/bin/env python3
"""build_navopt.py - DEV: NAVFULL with the optimized ephemeris engine (tools/navopt_engine.py: Horner,
n-vectors, the nutation as matrix products, HCZ by n-vectors), for the C47 and Free42, and MOON47 the same way.

The release pipelines run unchanged (build_navfull.build, build_free42.build, build_moon47) with the
optimized SUNA, STAR, MOON, PLAN and CHZ in place of programs/, the sky cache keeping θ and ε0
(gencache.SUNREGS), the outputs in a temporary folder and the label maps of tools/labels copied, so
build/, tools/labels/ and programs/ are not touched. The matrices are the same: load NAVINIT_FULL or
NAVINIT_FAST of the release (C47: build/, Free42: build/free42/).

  build/dev/opt/NAVFULL_OPT.txt (.p47)            C47 / R47 (and the DM42 with the C47 firmware)
  build/dev/opt/src/NAVFULL_OPT.txt                the same with the original program names (tests)
  build/dev/opt/free42/NAVFULL_OPT.txt (.raw)      Free42 (DM42 / DM42n stock firmware)
  build/dev/opt/MOON47_OPT.txt (.p47), free42/MOON47_OPT.txt (.raw)

  python3 tools/build_navopt.py          then python3 tests/test_navopt.py (parity and statistics)
"""
import contextlib, io, os, shutil, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path[:0] = [HERE, os.path.join(HERE, 'generators'), os.path.join(HERE, 'generators', 'atext'),
                os.path.join(ROOT, 'python'), os.path.join(ROOT, 'python', 'native')]
import build_navfull as B                                                   # noqa: E402
import navopt_engine as E                                                   # noqa: E402
import gencache                                                             # noqa: E402

OUT = os.path.join(ROOT, 'build', 'dev', 'opt')
F42RUN = os.path.join(ROOT, 'tools', 'f42', 'f42run')


@contextlib.contextmanager
def optimized(on=True):
    """B.read gives the optimized engine, the cache keeps θ and ε0, outputs and label maps in a temp folder
    (on=False: the release programs, the same way: the reference of the tests)."""
    read, out, labels, regs = B.read, B.OUT, B.LABELS, gencache.SUNREGS
    opt = E.programs(read) if on else {}
    tmp = tempfile.mkdtemp()
    shutil.copytree(labels, os.path.join(tmp, 'labels'))
    B.read = lambda name: list(opt[name]) if name in opt else read(name)
    B.OUT, B.LABELS = os.path.join(tmp, 'build'), os.path.join(tmp, 'labels')
    gencache.SUNREGS = E.SUNREGS if on else regs
    try:
        yield tmp
    finally:
        B.read, B.OUT, B.LABELS, gencache.SUNREGS = read, out, labels, regs


def p47(path):
    """FILE.p47 next to FILE.txt (tools/rejig47_atext.py); the program size in bytes, or None."""
    if not (os.environ.get('REJIG') or shutil.which('rejig')):
        return None
    import rejig47_atext
    with contextlib.redirect_stdout(io.StringIO()):
        rejig47_atext.convert(path)
    return program_bytes(path[:-4] + '.p47')


def program_bytes(path):
    L = open(path, encoding='ascii').read().split('\n')
    return int(L[L.index('PROGRAM') + 1])


def raw(path):
    """FILE.raw next to FILE.txt with tools/f42/f42run (paste, export); its size, or None."""
    if not os.path.exists(F42RUN):
        return None
    subprocess.run([F42RUN], input='paste %s\nexport %s\n' % (path, path[:-4] + '.raw'), text=True,
                   capture_output=True, timeout=3600)
    return os.path.getsize(path[:-4] + '.raw')


def c47(on=True):
    """NAVFULL (named labels, short labels); on=False: the release one."""
    with optimized(on) as tmp, contextlib.redirect_stdout(io.StringIO()):
        full = B.build()[0]
        short = open(os.path.join(tmp, 'build', 'NAVFULL.txt'), encoding='utf-8').read().split('\n')
    return full, [l for l in short if l]


def free42(on=True):
    """NAVFULL for Free42 (short labels, named labels); on=False: the release one."""
    import build_free42 as F
    keep = F.OUT, F.DEV, F.SRC, F.tbl50
    with optimized(on) as tmp, contextlib.redirect_stdout(io.StringIO()):
        F.OUT = os.path.join(tmp, 'free42'); F.DEV = os.path.join(F.OUT, 'dev'); F.SRC = os.path.join(F.DEV, 'src')
        F.tbl50 = lambda: None
        try:
            F.build(rlcd=True)
        finally:
            F.OUT, F.DEV, F.SRC, F.tbl50 = keep
        short = open(os.path.join(tmp, 'free42', 'NAVFULL.txt'), encoding='utf-8').read().split('\n')
        named = open(os.path.join(tmp, 'free42', 'dev', 'src', 'NAVFULL.txt'), encoding='utf-8').read().split('\n')
    return [l for l in short if l], [l for l in named if l]


def moon47():
    import build_moon47 as M
    import moon47_opt
    plain, f42 = moon47_opt.build(M)
    B.write(os.path.join(OUT, 'MOON47_OPT.txt'), plain)
    B.write(os.path.join(OUT, 'free42', 'MOON47_OPT.txt'), f42)


def main():
    full, short = c47()
    B.write(os.path.join(OUT, 'src', 'NAVFULL_OPT.txt'), full)
    B.write(os.path.join(OUT, 'NAVFULL_OPT.txt'), short)
    short, named = free42()
    B.write(os.path.join(OUT, 'free42', 'NAVFULL_OPT.txt'), short)
    B.write(os.path.join(OUT, 'free42', 'src', 'NAVFULL_OPT.txt'), named)
    moon47()
    for f in ('NAVFULL_OPT.txt', 'MOON47_OPT.txt'):
        n = p47(os.path.join(OUT, f))
        print('%-28s %s' % ('build/dev/opt/' + f, '.p47 %d bytes' % n if n else '(no rejig: no .p47)'))
    for f in ('NAVFULL_OPT.txt', 'MOON47_OPT.txt'):
        n = raw(os.path.join(OUT, 'free42', f))
        print('%-28s %s' % ('build/dev/opt/free42/' + f, '.raw %d bytes' % n if n else '(no f42run: no .raw)'))


if __name__ == '__main__':
    main()
