#!/usr/bin/env python3
"""test_hcz.py - NAV's sight reduction HCZ (tools/navopt_engine.py, the routine NAV uses: Y Dec, X GHA, R91 lat,
R92 lon E+ -> X = R96 Hc, R97 Zn, "SHC" sin Hc) in the C47 firmware itself, against the textbook formulas:
200 random positions and bodies, the poles, the zenith, the horizon.

It also runs tests/hcz/HCZ2.txt, the same routine written with unit n-vectors (DOT, CROSS, UNITV), and compares
the two: steps, bytes, time per call. HCZ2 gives the same Hc and Zn, but takes twice the steps and 1.4 times the
time, and its Zn is undefined at a pole (the north vector is zero there): HCZ stays.

  C47SIM=/path/to/c47 python3 tests/test_hcz.py   (default ~/c47sim-patched/src47/build.sim/src/c47-gtk/c47)
"""
import math, os, random, re, shutil, subprocess, sys, tempfile, time
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [os.path.join(ROOT, 'tools')]
import build_navopt as N                                             # noqa: E402
import navopt_engine as E                                            # noqa: E402

SIM = os.environ.get('C47SIM', os.path.expanduser('~/c47sim-patched/src47/build.sim/src/c47-gtk/c47'))
RES = os.path.join(os.path.dirname(SIM).split('/build.sim/')[0], 'res') if '/build.sim/' in SIM else os.path.join(os.path.dirname(SIM), 'res')
LIMIT = 1e-9          # arcminutes: both against the formulas in double precision


def ref(lat, lon, dec, gha):
    """Hc, Zn (degrees) by the textbook formulas; at a pole Zn follows the meridian convention of HCZ."""
    r = math.radians
    lha = r(gha + lon)
    sh = math.sin(r(lat)) * math.sin(r(dec)) + math.cos(r(lat)) * math.cos(r(dec)) * math.cos(lha)
    hc = math.degrees(math.asin(max(-1.0, min(1.0, sh))))
    zn = math.degrees(math.atan2(-math.cos(r(dec)) * math.sin(lha),
                                 math.cos(r(lat)) * math.sin(r(dec)) - math.sin(r(lat)) * math.cos(r(dec)) * math.cos(lha))) % 360
    return hc, zn


def dz(a, b):
    return abs((a - b + 180) % 360 - 180)


def sim(d, files, tcl):
    for f in files:
        N.p47(f)
    open(os.path.join(d, 't.tcl'), 'w').write('\n'.join(['readp %s' % f[:-4] + '.p47' for f in files] + tcl) + '\n')
    r = subprocess.run([SIM, '--headless', '--reset', '--script', 't.tcl'], cwd=d, capture_output=True, text=True, timeout=1800)
    return r.stdout + r.stderr


def main():
    if not os.path.exists(SIM):
        print('test_hcz: no C47 simulator at %s (C47SIM=...)' % SIM)
        return 0
    d = tempfile.mkdtemp()
    os.symlink(RES, os.path.join(d, 'res'))
    hcz = os.path.join(d, 'HCZ.txt')
    open(hcz, 'w').write('\n'.join(E.HCZ + ['END']) + '\n')
    hcz2 = os.path.join(d, 'HCZ2.txt')
    shutil.copy(os.path.join(ROOT, 'tests', 'hcz', 'HCZ2.txt'), hcz2)
    rnd = random.Random(47)
    cases = [(rnd.uniform(-80, 80), rnd.uniform(-180, 180), rnd.uniform(-60, 60), rnd.uniform(0, 360)) for _ in range(200)]
    cases += [(0, 0, 0, 0), (45, 10, 45, 350), (30, 20, -10, 340), (-60, -170, -25, 90), (10, 0, 80, 180)]
    poles = [(90, 10, 20, 100), (-90, 10, -20, 100)]
    T = ['LBL "TC"', 'DEG']
    for i, (la, lo, de, gh) in enumerate(cases + poles):
        T += [repr(la), 'STO 91', repr(lo), 'STO 92']
        for p, name in (('A', 'HCZ'), ('C', 'HCZ2')):
            T += [repr(de), repr(gh), 'XEQ "%s"' % name, 'RCL 96', 'STO "%s%d"' % (p, i), 'RCL 97', 'STO "%s%d"' % (chr(ord(p) + 1), i)]
    T += ['RTN', 'END']
    tc = os.path.join(d, 'TC.txt')
    open(tc, 'w').write('\n'.join(T) + '\n')
    out = sim(d, [hcz, hcz2, tc], ['xeq TC'] + ['puts "%s%d=[var %s%d]"' % (c, i, c, i)
                                                  for i in range(len(cases) + len(poles)) for c in 'ABCD'])
    v = {m.group(1): float(m.group(2)) for m in re.finditer(r'^([ABCD]\d+)=(\S+)', out, re.M)}
    err = [l for l in out.split('\n') if 'In function' in l]
    bad = len(err)
    w = [0.0] * 4
    for i, c in enumerate(cases):
        hc, zn = ref(*c)
        w = [max(w[0], abs(v['A%d' % i] - hc)), max(w[1], dz(v['B%d' % i], zn) * math.cos(math.radians(hc))),
             max(w[2], abs(v['C%d' % i] - hc)), max(w[3], dz(v['D%d' % i], zn) * math.cos(math.radians(hc)))]
    w = [x * 60 for x in w]
    print('== HCZ (NAV) and HCZ2 (unit n-vectors) in the C47 firmware: %d cases against the formulas' % len(cases))
    print("  HCZ   Hc max %.1e'  Zn x cos Hc max %.1e'" % (w[0], w[1]))
    print("  HCZ2  Hc max %.1e'  Zn x cos Hc max %.1e'" % (w[2], w[3]))
    bad += w[0] > LIMIT or w[1] > LIMIT
    for k, (la, lo, de, gh) in enumerate(poles):
        i = len(cases) + k
        hc, conv = ref(la, lo, de, gh)          # at a pole the formula gives 180 + LHA (north) or -LHA (south), as HCZ
        okh = abs(v['A%d' % i] - hc) * 60 < LIMIT
        okz = dz(v['B%d' % i], conv) * 60 < 1e-6
        bad += not (okh and okz)
        print('  pole %+d: HCZ Hc %.4f Zn %.4f (%s) | HCZ2 Hc %.4f Zn %.4f' % (la, v['A%d' % i], v['B%d' % i],
              'OK' if okh and okz else 'BAD', v['C%d' % i], v['D%d' % i]))
    # cost: steps, bytes, time per call
    steps = lambda f: sum(1 for l in open(f, encoding='utf-8') if l.strip() and not l.startswith(('LBL "', 'REM', 'END')))
    plain2 = os.path.join(d, 'HCZ2P.txt')
    open(plain2, 'w').write(''.join(l for l in open(hcz2, encoding='utf-8') if not l.startswith('REM')))
    b1, b2 = N.p47(hcz), N.p47(plain2)

    def per_call(body, reps=300):
        L = ['LBL "TL"', 'DEG', '33.5', 'STO 91', '-18.4', 'STO 92', str(reps), 'STO 01', 'LBL 01'] + body + ['DSE 01', 'GTO 01', 'RTN', 'END']
        tl = os.path.join(d, 'TL.txt')
        open(tl, 'w').write('\n'.join(L) + '\n')
        best = 1e9
        for _ in range(3):
            t = time.time()
            sim(d, [hcz, hcz2, tl], ['xeq TL'])
            best = min(best, time.time() - t)
        return best
    t0 = per_call(['21.3', '157.2', 'DROP', 'DROP'])
    t1 = (per_call(['21.3', '157.2', 'XEQ "HCZ"', 'DROP']) - t0) / 300 * 1000
    t2 = (per_call(['21.3', '157.2', 'XEQ "HCZ2"', 'DROP']) - t0) / 300 * 1000
    print('  cost: HCZ %d steps %d bytes %.2f ms per call | HCZ2 %d steps %d bytes %.2f ms per call (PC simulator)'
          % (steps(hcz), b1, t1, steps(plain2), b2, t2))
    print('%d failed' % bad)
    shutil.rmtree(d, ignore_errors=True)
    return bad


if __name__ == '__main__':
    sys.exit(1 if main() else 0)
