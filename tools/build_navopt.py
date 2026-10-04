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
  build/dev/opt/NAVINIT_FULL / _FAST, TBL_1 / TBL_5 (and free42/): the release ones, only their message left
                                                   on the stack at the end

  python3 tools/build_navopt.py          then python3 tests/test_navopt.py (parity and statistics)
"""
import contextlib, io, os, re, shutil, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path[:0] = [HERE, os.path.join(HERE, 'generators'), os.path.join(HERE, 'generators', 'atext'),
                os.path.join(ROOT, 'python'), os.path.join(ROOT, 'python', 'native')]
import build_navfull as B                                                   # noqa: E402
import navopt_engine as E                                                   # noqa: E402
import gencache, gennav                                                     # noqa: E402

# the NAV menu without TEXT, numbered again: 1 ALMANAC 2 CHART 3 SKY 4 SPLIT 5 ANIM 6 ALLSKY 7 INFO, 0 END
NOTEXT = {'ITEMS': [i for i in gennav.ITEMS if i != 'TEXT'], 'VIEWS': [v for v in gennav.VIEWS if v != 'ALMT'],
          'ALL': list(range(1, len(gennav.ITEMS))), 'COMPACT': [1, 2, 3, 6, 7]}

OUT = os.path.join(ROOT, 'build', 'dev', 'opt')
F42RUN = os.path.join(ROOT, 'tools', 'f42', 'f42run')


@contextlib.contextmanager
def optimized(on=True):
    """B.read gives the optimized engine, the cache keeps θ and ε0, outputs and label maps in a temp folder
    (on=False: the release programs, the same way: the reference of the tests)."""
    read, out, labels, regs = B.read, B.OUT, B.LABELS, gencache.SUNREGS
    menu = {k: getattr(gennav, k) for k in NOTEXT}
    opt = E.programs(read) if on else {}
    tmp = tempfile.mkdtemp()
    shutil.copytree(labels, os.path.join(tmp, 'labels'))
    B.read = lambda name: list(opt[name]) if name in opt else read(name)
    B.OUT, B.LABELS = os.path.join(tmp, 'build'), os.path.join(tmp, 'labels')
    gencache.SUNREGS = E.SUNREGS if on else regs
    for k, v in (NOTEXT if on else menu).items():
        setattr(gennav, k, v)
    try:
        yield tmp
    finally:
        B.read, B.OUT, B.LABELS, gencache.SUNREGS = read, out, labels, regs
        for k, v in menu.items():
            setattr(gennav, k, v)


def keywait(L, wait='50'):
    """Every tight key wait LBL n / KEY? r / GTO n becomes LBL n / PAUSE 50 / KEY? r / GTO n. A key pressed during a
    PAUSE ends it only after its release (the C47: pauseKeyExit waits for the release; the PC simulator:
    PGM_KEY_PRESSED_WHILE_PAUSED until the release, and that release does not repaint the screen), and KEY? then
    reads it. In a bare KEY? loop the simulator repaints the stack over the drawing when the key is released.
    Not PAUSE 99: on the calculator its end sets the screen back to the normal display (SCRUPD_AUTO, refresh 1201)."""
    # SKY (HORZ): one body's line a second, keys read in between (TICKS + KEY? busy loop) -> PAUSE 10, KEY?;
    # no key: the next body (LBL 62), as when the second is over
    sky_old = ['PAUSE 0', 'TICKS', '10', '+', 'STO 38', 'LBL 41', 'KEY? 39', 'GTO 46']
    k = [n for n in range(len(L)) if L[n:n + len(sky_old)] == sky_old]
    assert len(k) == 1, 'keywait: the SKY loop changed'
    L = L[:k[0]] + ['PAUSE 10', 'KEY? 39', 'GTO 62'] + L[k[0] + len(sky_old):]
    out, i = [], 0
    while i < len(L):
        if re.fullmatch(r'LBL \d+', L[i]) and i + 2 < len(L) and L[i + 1].startswith('KEY? ') and L[i + 2] == 'GTO ' + L[i][4:]:
            if out and out[-1] == 'PAUSE 0':           # PAUSE 50 shows the screen itself (lcd_refresh at its start)
                out.pop()
            out += [L[i], 'PAUSE ' + wait, L[i + 1], L[i + 2]]
            i += 3
            continue
        out.append(L[i])
        i += 1
    return out


def prune(L):
    """Only the programs NAV reaches (XEQ / GTO "name"): without TEXT, ALMR and its text routines go."""
    progs, cur = [], []
    for l in L:
        cur.append(l)
        if l == 'END':
            progs.append(cur); cur = []
    P = {next(re.fullmatch(r'LBL "(.+)"', l).group(1) for l in p if l.startswith('LBL "')): p for p in progs}
    need = B.closure({n: p for n, p in P.items()}, ['NAV'])
    return [l for n, p in P.items() if n in need for l in p]


def init_clean(L):
    """NAVINIT: only the message on the stack at the end (MATRICES READY: ...), nothing else."""
    i = next(k for k in range(len(L)) if L[k] == 'STO "VAL"')
    j = L.index('RTN', i)
    assert L[i + 1].startswith('"MATRICES READY')
    return L[:i - 1] + ['CLSTK', L[i - 1], 'STO "VAL"', 'CLSTK', L[i + 1]] + L[j:]


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


def c47(on=True, wait='50'):
    """NAVFULL (named labels, short labels); on=False: the release one. wait: the PAUSE of the key waits
    (NAVFULL_OPT_PAUSE0 / _PAUSE1: PAUSE 0 / PAUSE 1, to compare on the calculator and in the simulator)."""
    with optimized(on) as tmp, contextlib.redirect_stdout(io.StringIO()):
        full = B.build()[0]
        short = open(os.path.join(tmp, 'build', 'NAVFULL.txt'), encoding='utf-8').read().split('\n')
        if on:                                     # without TEXT: the programs NAV still reaches; keys read in a PAUSE
            full = keywait(prune(full), wait)
            short = B.rename(full, B.fixed_map('NAVFULL', full))
    return full, [l for l in short if l]


def inits():
    """The release NAVINIT_FULL / _FAST (C47 and Free42) with only the message left on the stack."""
    import build_free42 as F
    out = {}
    for kind in ('FULL', 'FAST'):
        L = [l for l in open(os.path.join(ROOT, 'build', 'NAVINIT_%s.txt' % kind), encoding='utf-8').read().split('\n') if l]
        out[kind] = init_clean(L)
        out['F42_' + kind] = F.conv(out[kind], 'INIT')
    return out


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


def tbl_clean(L, clear):
    """TBL: only the message (TBL dd-mm-yyyy TO dd-mm-yyyy) left on the stack: clear before it."""
    i = L.index('SF 10')
    assert L[i + 1].startswith(('"TBL ', 'XSTR "TBL ')) and L[i + 2] == 'RTN'
    return L[:i + 1] + [clear] + L[i + 1:]


def tbls():
    """TBL_1 / TBL_5 of the release (C47 build/, Free42 build/free42/) with a clean stack at the end."""
    out = {}
    for name in ('TBL_1', 'TBL_5', 'TBL_50'):            # TBL_50: Free42 on a PC only (not in git)
        for d, key, clear in (('', name, 'CLSTK'), ('free42', 'F42_' + name, 'CLST')):
            src = os.path.join(ROOT, 'build', d, name + '.txt')
            if os.path.exists(src):
                L = [l for l in open(src, encoding='utf-8').read().split('\n') if l]
                out[key] = tbl_clean(L, clear)
    return out


def main():
    full, short = c47()
    B.write(os.path.join(OUT, 'src', 'NAVFULL_OPT.txt'), full)
    B.write(os.path.join(OUT, 'NAVFULL_OPT.txt'), short)
    for w in ('0', '1'):                           # to compare: the key waits with PAUSE 0 / PAUSE 1
        B.write(os.path.join(OUT, 'NAVFULL_OPT_PAUSE%s.txt' % w), c47(True, w)[1])
    short, named = free42()
    B.write(os.path.join(OUT, 'free42', 'NAVFULL_OPT.txt'), short)
    B.write(os.path.join(OUT, 'free42', 'src', 'NAVFULL_OPT.txt'), named)
    moon47()
    for k, L in inits().items():
        B.write(os.path.join(OUT, 'free42' if k.startswith('F42_') else '', 'NAVINIT_%s.txt' % k.replace('F42_', '')), L)
    for k, L in tbls().items():
        B.write(os.path.join(OUT, 'free42' if k.startswith('F42_') else '', k.replace('F42_', '') + '.txt'), L)
    for f in ('NAVFULL_OPT.txt', 'NAVFULL_OPT_PAUSE0.txt', 'NAVFULL_OPT_PAUSE1.txt', 'MOON47_OPT.txt', 'NAVINIT_FULL.txt', 'NAVINIT_FAST.txt',
              'TBL_1.txt', 'TBL_5.txt'):
        n = p47(os.path.join(OUT, f))
        print('%-28s %s' % ('build/dev/opt/' + f, '.p47 %d bytes' % n if n else '(no rejig: no .p47)'))
    for f in ('NAVFULL_OPT.txt', 'MOON47_OPT.txt', 'NAVINIT_FULL.txt', 'NAVINIT_FAST.txt', 'TBL_1.txt', 'TBL_5.txt', 'TBL_50.txt'):
        n = raw(os.path.join(OUT, 'free42', f))
        print('%-28s %s' % ('build/dev/opt/free42/' + f, '.raw %d bytes' % n if n else '(no f42run: no .raw)'))


if __name__ == '__main__':
    main()
