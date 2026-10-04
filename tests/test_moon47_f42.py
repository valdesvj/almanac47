#!/usr/bin/env python3
"""MOON47 for Free42 (build/free42/MOON47.txt, tools/build_moon47.py) in f42run (tools/f42: the Free42 core with
the DM42 400 x 240 screen) against the MOON47 page of python/moon47.py, pixel for pixel: the clock set with
F42_DATE / F42_TIME, the date formats YMD, DMY and MDY of Free42, TZ, north and south (+/-, key 15), then
another key ends.      python3 tests/test_moon47_f42.py   (needs tools/f42/f42run)"""
import os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [os.path.join(ROOT, 'python'), os.path.join(ROOT, 'python', 'native')]
import moon47 as M47, c47screen21 as V
F42 = os.path.join(ROOT, 'tools', 'f42', 'f42run')
PROG = os.path.join(ROOT, 'build', 'free42', 'MOON47.txt')


def frames(y, m, d, hh, mi, fmt, tz):
    """The two screens of MOON47 (north, then south after +/-) with the clock at y-m-d hh:mi local time."""
    t = tempfile.mkdtemp()
    setup = os.path.join(t, 'setup.txt')
    open(setup, 'w').write('\n'.join(['LBL "SETUP"', fmt] + (['%s' % tz, 'STO "TZ"'] if tz is not None else [])
                                     + ['RTN', 'END']) + '\n')
    cmd = ['paste ' + setup, 'paste ' + PROG, 'xeq SETUP', 'xeq MOON47', 'shot %s/s0.pbm' % t,
           'key 15', 'shot %s/s1.pbm' % t, 'key 37', 'msg']
    env = dict(os.environ, F42_DATE='%04d%02d%02d' % (y, m, d), F42_TIME='%02d%02d0000' % (hh, mi))
    r = subprocess.run([F42], input='\n'.join(cmd) + '\n', text=True, capture_output=True, timeout=600, env=env)
    out = []
    for k in range(2):
        rows = open('%s/s%d.pbm' % (t, k)).read().split('\n')[2:242]
        out.append({(x, yy) for yy, row in enumerate(rows) for x, c in enumerate(row) if c == '1'})
    return out, r.stdout + r.stderr


def main():
    if not os.path.exists(F42):
        print('no tools/f42/f42run: sh tools/f42/setup.sh'); return
    cases = [(2026, 10, 3, 12, 0, 'YMD', None), (2026, 10, 10, 19, 0, 'DMY', 4), (2027, 1, 21, 22, 30, 'MDY', -5),
             (2049, 3, 16, 21, 51, 'YMD', None), (2016, 2, 29, 5, 23, 'DMY', None),
             (2028, 6, 6, 1, 42, 'YMD', 5.5), (2029, 2, 28, 15, 30, 'MDY', -9.5)]
    bad = 0
    for y, m, d, hh, mi, fmt, tz in cases:
        j = M47.julian(y, m, d, hh + mi / 60.0) - (tz or 0) / 24.0
        mine, log = frames(y, m, d, hh, mi, fmt, tz)
        ref = [V.moon47_screen(j, False, tz or 0)[0], V.moon47_screen(j, True, tz or 0)[0]]
        diffs = [len(a ^ b) for a, b in zip(mine, ref)]
        ok = not any(diffs)
        bad += not ok
        print('%04d-%02d-%02d %02d:%02d %s tz %-4s diff %s %s' % (y, m, d, hh, mi, fmt, tz, diffs, 'OK' if ok else 'DIFFERENT'))
        if not ok:
            print(log[-600:])
    print('%d different' % bad)
    sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()
