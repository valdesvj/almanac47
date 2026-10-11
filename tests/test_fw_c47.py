#!/usr/bin/env python3
"""test_fw_c47.py - the v2.2.0 C47 files (build/c47/, tools/build_release_c47.py) in the C47 firmware itself: the PC
simulator built from the firmware sources, headless with its script (--script).

  1. runs: ALMA47 (NAVINIT_FAST) each page, + menu, 0 end: no error, X = 0, the registers cleared (CLREGS);
     NAVLITTLE (NAVINIT_LITTLE): up, down, + end: no error, your registers kept; MOON47 and MOON47 for the old DM42
     (build/c47/dm42/) without TZ and with TZ = -5
  2. ephemeris: ALMA47 against JPL DE421 + ERFA, the reference and the limits of tests/test_ephem.py. Random instants
     (FULL 2000-2050, FAST 2026-2030) and positions: NAVINIT, ALMA47, the inputs, 1 ALMANAC, + and 0; then the cache
     ALMC is read: rows 1 Sun, 2 Moon, 3-6 Venus Mars Jupiter Saturn (GHA Dec Hc Zn), 7-64 the stars (-98: not asked,
     -99: below the horizon), 65 GHA Aries, Moon HP, SD; 67 JD, lat, lon. A planet within 1 deg of the Sun, or below
     -0.5 deg Hc (the quick position, by design) is not compared.

The key waits (DO / PAUSE n / KEY? r / WHILE / ENDDO) are replaced in a test copy by SNAP and the next key from TKEY.

  ~/.venvs/almanac47-ephem/bin/python tests/test_fw_c47.py [n instants per mode, default 20] [seed]
  C47SIM=/path/to/c47 (default ~/.cache/c47fw/c47, res/ next to it); ONLY=runs,FULL,FAST to choose
"""
import math, os, random, re, shutil, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [os.path.join(ROOT, 'tools'), os.path.join(ROOT, 'tests'), os.path.join(ROOT, 'python', 'native'),
                os.path.join(ROOT, 'tools', 'almanac')]
import test_fw                                                       # noqa: E402
from test_fw import ERRORS                                           # noqa: E402


def testcopy(src, dst):
    """test_fw.testcopy (the key waits), and SKY's wait: PAUSE n / KEY? r / IF (true when no key) -> SNAP, the next key
    of TKEY into r, flag 09 set when it is 0, FS?C 09 / IF."""
    test_fw.testcopy(src, dst)
    L = [l for l in open(dst, encoding='utf-8').read().split('\n') if l]
    out, i = [], 0
    while i < len(L):
        if (re.fullmatch(r'PAUSE \d+', L[i]) and i + 2 < len(L) and L[i + 1].startswith('KEY? ')
                and re.fullmatch(r'IF \d+', L[i + 2])):
            r = L[i + 1][5:]
            out += ['SNAP', 'RCL "TKEY"', '100', 'MOD', 'STO ' + r, 'RCL "TKEY"', '100', '÷', 'IP', 'STO "TKEY"',
                    'DROP', 'DROP', 'CF 09', 'RCL ' + r, 'X=0?', 'SF 09', 'DROP', 'FS?C 09']
            i += 2
            continue
        out.append(L[i]); i += 1
    open(dst, 'w', encoding='utf-8').write('\n'.join(out) + '\n')

SIM = os.environ.get('C47SIM', os.path.expanduser('~/.cache/c47fw/c47'))
RES = os.path.join(os.path.dirname(SIM), 'res')
C47 = os.path.join(ROOT, 'build', 'c47')
DM42 = os.path.join(C47, 'dm42')                 # the old DM42 (the simulator has STRUCT, 255 a program)
ONLY = os.environ.get('ONLY', 'runs,FULL,FAST').split(',')


def p47(src, d, name=None, copy=False):
    """src (a listing) into d as a .p47 (a test copy unless copy), converted with rejig."""
    dst = os.path.join(d, (name or os.path.basename(src)[:-4]) + '.txt')
    shutil.copy(src, dst) if copy else testcopy(src, dst)
    subprocess.run(['rejig', '-o', dst[:-4] + '.p47', dst], check=True, capture_output=True)
    return dst[:-4] + '.p47'


def helper(d, setup, keys, extra=()):
    code = 0
    for k in reversed(keys):
        code = code * 100 + k
    P = ['LBL "TSET"', 'SF 81'] + setup + [str(code), 'STO "TKEY"', 'CLSTK', 'RTN'] + list(extra) + ['END']
    f = os.path.join(d, 'TSET.txt')
    open(f, 'w', encoding='utf-8').write('\n'.join(P) + '\n')
    subprocess.run(['rejig', '-o', f[:-4] + '.p47', f], check=True, capture_output=True)
    return f[:-4] + '.p47'


def sim(d, tcl):
    open(os.path.join(d, 't.tcl'), 'w').write('\n'.join(tcl) + '\n')
    r = subprocess.run([SIM, '--headless', '--reset', '--script', 't.tcl'], cwd=d, capture_output=True, text=True,
                       timeout=1800)
    out = [l for l in (r.stdout + r.stderr).split('\n') if l.strip() and not l.lstrip().startswith('refrsh')]
    err = [l for l in out if any(w in l for w in ERRORS + ('not enough', 'no data blocks'))
           and not l.startswith(('Exported', 'Overrode', 'Cleared'))]
    return out, err


def tmp():
    d = tempfile.mkdtemp()
    os.symlink(RES, os.path.join(d, 'res'))
    return d


STATES = {}


def state(init):
    """A saved calculator state with the matrices of NAVINIT and no program (NAVINIT run, then its program removed: the
    PROGRAMS block of the state file taken from an empty state), as on the calculator after GTO "NAVINIT", DELP.
    NAVINIT_FULL and ALMA47 do not fit in memory together."""
    if init in STATES:
        return STATES[init]
    d = tmp()
    f = p47(os.path.join(C47, init + '.txt'), d, copy=True)
    out, err = sim(d, ['readp %s' % f, 'xeq NAVINIT', 'savest %s/full.s47' % d])
    assert not err, err[:3]
    sim(d, ['savest %s/empty.s47' % d])

    def block(p):
        L = open(p, encoding='utf-8', errors='surrogateescape').read().split('\n')
        return L, L.index('PROGRAMS'), L.index('EQUATIONS')
    F_, a, b = block(d + '/full.s47')
    E_, c, e = block(d + '/empty.s47')
    open(d + '/clean.s47', 'w', encoding='utf-8', errors='surrogateescape').write('\n'.join(F_[:a] + E_[c:e] + F_[b:]))
    STATES[init] = d + '/clean.s47'
    return STATES[init]


INPUTS = ['2026.1004', 'STO "DATE"', '9.30', 'STO "UTC"', '25.20', 'STO "LAT"', '55.12', 'STO "LON"']


def runs():
    bad = 0
    print('== ALMA47 in the C47 firmware (headless simulator): each page, + menu, 0 end')
    for k, name in ((72, '1 ALMANAC'), (73, '2 SPLIT'), (74, '3 SKY'), (62, '4 ANIM'), (63, '5 ALLSKY'), (64, '6 INFO'),
                    (54, '9 SNAP'), (51, 'up arrow')):
        d = tmp()
        files = [p47(os.path.join(C47, 'NAVINIT_FAST.txt'), d, copy=True), p47(os.path.join(C47, 'ALMA47.txt'), d),
                 helper(d, INPUTS, [k, 85, 82] if k != 51 else [51, 72, 85, 82])]
        tcl = ['readp %s' % f for f in files] + ['xeq NAVINIT', 'xeq TSET']
        tcl += ['reg %02d %d.25' % (r, 4000 + r) for r in range(100)] + ['xeq ALMA47'] + ['press R/S'] * 4
        tcl += ['puts "X=[reg X]"'] + ['puts "R%02d=[reg %02d]"' % (r, r) for r in range(100)]
        out, err = sim(d, tcl)
        regs = {m.group(1): m.group(2) for l in out for m in [re.match(r'R(\d\d)=(.*)', l)] if m}
        x = next((l[2:] for l in out if l.startswith('X=')), None)
        cleared = len(regs) == 100 and all(v.strip() in ('0', '0.') for v in regs.values())
        ok = not err and x == '0' and cleared
        bad += not ok
        print('  %-10s X=%s  registers %s  %s' % (name, x, 'cleared' if cleared else 'NOT CLEARED', err[:2] or 'no error'))
        shutil.rmtree(d, ignore_errors=True)
    print('== NAVLITTLE (the old DM42 with the C47 firmware): up, down, + end')
    d = tmp()
    files = [p47(os.path.join(DM42, 'NAVINIT_LITTLE.txt'), d, copy=True), p47(os.path.join(DM42, 'NAVLITTLE.txt'), d),
             helper(d, INPUTS, [51, 61, 85])]
    tcl = ['readp %s' % f for f in files] + ['xeq NAVINIT', 'xeq TSET'] + ['reg %02d %d.25' % (r, 4000 + r) for r in range(100)]
    tcl += ['xeq ALMA47'] + ['press R/S'] * 4 + ['puts "X=[reg X]"'] + ['puts "R%02d=[reg %02d]"' % (r, r) for r in range(100)]
    out, err = sim(d, tcl)
    regs = {m.group(1): m.group(2) for l in out for m in [re.match(r'R(\d\d)=(.*)', l)] if m}
    kept = len(regs) == 100 and all('.25' in v for v in regs.values())
    bad += not (not err and kept)
    print('  NAVLITTLE  registers %s  %s' % ('kept' if kept else 'CHANGED', err[:2] or 'no error'))
    print('== MOON47 and MOON47 for the old DM42: without TZ, with TZ = -5')
    for src, tz, setup in [(f, t, st) for f in (os.path.join(C47, 'MOON47.txt'), os.path.join(DM42, 'MOON47.txt'))
                           for t, st in (('none', []), ('-5', ['-5', 'STO "TZ"']))]:
        d = tmp()
        files = [p47(src, d), helper(d, setup, [43, 82])]
        out, err = sim(d, ['readp %s' % f for f in files] + ['xeq TSET', 'xeq MOON47', 'puts "TZ=[var TZ]"'])
        t = next((l[3:] for l in out if l.startswith('TZ=')), None)
        good = not err and t == ('0' if tz == 'none' else '-5')
        bad += not good
        print('  %-16s TZ before %-4s -> TZ %s  %s' % (os.path.relpath(src, ROOT)[-16:], tz, t, err[:2] or 'no error'))
    return bad


def dms(x):
    m = round(abs(x) * 60)
    return '%s%d.%02d' % ('-' if x < 0 else '', m // 60, m % 60)


def ephem(mode, init, j1, j2, n, rnd):
    import erfa
    import test_ephem as T
    import c47astro as A
    G = T.G
    st = T.Stat()
    for k in range(n):
        j = rnd.uniform(j1, j2)
        y, mo, dd, fd = erfa.jd2cal(j, 0.0)
        mins = int(round(fd * 1440)) % 1440
        j = A.jd(int(y), int(mo), int(dd)) + mins / 1440.0
        lat = round(rnd.uniform(-60, 60) * 60) / 60
        lon = round(rnd.uniform(-180, 180) * 60) / 60
        inp = ['%d.%02d%02d' % (y, mo, dd), 'STO "DATE"', '%d.%02d' % (mins // 60, mins % 60), 'STO "UTC"',
               dms(lat), 'STO "LAT"', dms(lon), 'STO "LON"']
        st0 = state(init)
        d = tmp()
        files = [p47(os.path.join(C47, 'ALMA47.txt'), d),
                 helper(d, inp, [72, 85, 82], ['LBL "RD"', 'INDEX "ALMC"', 'RCL 00', 'RCL 01', 'STOIJ', 'RCLEL', 'RTN'])]
        tcl = ['loadst %s' % st0] + ['readp %s' % f for f in files] + ['xeq TSET', 'xeq ALMA47'] + ['press R/S'] * 4
        for r in list(range(1, 65)) + [65, 67]:
            for c in range(1, 5):
                tcl += ['reg 00 %d' % r, 'reg 01 %d' % c, 'xeq RD', 'puts "A%d_%d=[reg X]"' % (r, c)]
        out, err = sim(d, tcl)
        shutil.rmtree(d, ignore_errors=True)
        v = {}
        for l in out:
            m = re.match(r'A(\d+)_(\d)=(\S+)', l)
            if m:
                try:
                    v[(int(m.group(1)), int(m.group(2)))] = float(m.group(3))
                except ValueError:
                    pass
        if err or abs(v.get((67, 1), 0) - j) > 1e-6:
            print('  %s %s: %s' % (mode, ' '.join(inp[::2]), err[:2] or 'ALMC row 67 is not the instant'))
            st.add('RUNS (failed)', 99)
            continue

        def hz(row, g, dc):
            h2, z2 = A.hcz(lat, lon, dc, g)
            st.add('Hc (all bodies)', (v[(row, 3)] - h2) * 60)
            st.add('Zn (all bodies) x cos Hc', T.wrap(v[(row, 4)] - z2) * A.dcos(h2))
        g, dc, r = G.apparent('sun', j)
        st.add('SUN GHA', T.wrap(v[(1, 1)] - g)); st.add('SUN Dec', (v[(1, 2)] - dc) * 60); hz(1, g, dc)
        st.add('ARIES GHA', T.wrap(v[(65, 1)] - G.gha_aries(j)))
        gs, ds = g, dc
        g, dc, r = G.apparent('moon', j)
        st.add('MOON GHA', T.wrap(v[(2, 1)] - g)); st.add('MOON Dec', (v[(2, 2)] - dc) * 60); hz(2, g, dc)
        st.add('MOON HP', v[(65, 2)] - math.degrees(math.asin(G.REQ / r)) * 60)
        st.add('MOON SD', v[(65, 3)] - math.degrees(math.asin(0.272481 * G.REQ / r)) * 60)
        for p, name in T.PLANETS.items():
            g, dc, r = G.apparent(name, j)
            if A.dsin(dc) * A.dsin(ds) + A.dcos(dc) * A.dcos(ds) * A.dcos(g - gs) > A.dcos(1.0) or v[(2 + p, 3)] < -0.5:
                continue
            st.add('%s GHA' % name.upper(), T.wrap(v[(2 + p, 1)] - g)); st.add('%s Dec' % name.upper(), (v[(2 + p, 2)] - dc) * 60)
            hz(2 + p, g, dc)
        for s in range(1, 59):
            if v.get((6 + s, 3), -98) in (-98, -99):
                continue
            g2, d2 = T.ref_star(s, j)
            st.add('STARS GHA x cos Dec', T.wrap(v[(6 + s, 1)] - g2) * A.dcos(d2))
            st.add('STARS Dec', (v[(6 + s, 2)] - d2) * 60)
            hz(6 + s, g2, d2)
        print('  %s %d/%d %s' % (mode, k + 1, n, ' '.join(inp[::2])), flush=True)
    print('== %s: %d instants (ALMA47 in the C47 firmware against DE421 + ERFA)' % (mode, n))
    return st.show(T.limit_of)


def main():
    if not os.path.exists(SIM):
        print('no C47 simulator (%s): set C47SIM' % SIM)
        return 0
    n = int(sys.argv[1]) if sys.argv[1:] else 20
    rnd = random.Random(int(sys.argv[2]) if sys.argv[2:] else 2026)
    bad = runs() if 'runs' in ONLY else 0
    if 'FULL' in ONLY or 'FAST' in ONLY:
        import c47astro as A
        if 'FULL' in ONLY:
            bad += ephem('FULL 2000-2050', 'NAVINIT_FULL', A.jd(2000, 1, 1), A.jd(2050, 12, 31), n, rnd)
        if 'FAST' in ONLY:
            period = A.use_series(os.path.join(ROOT, 'python', 'native', 'fast_series.json'))
            j1, j2 = A.FAST_JD
            A.use_series(None)                 # the reference is ERFA; c47astro gives only jd, hcz, dsin / dcos here
            bad += ephem('FAST %s' % period, 'NAVINIT_FAST', j1 + 1, j2 - 1, n, rnd)
    print('%d failed / over the limit' % bad)
    return bad


if __name__ == '__main__':
    sys.exit(1 if main() else 0)
