#!/usr/bin/env python3
"""build/v2.2.1/ is the build (tools/build_release_v221.py): the C47 / R47 ALMA47 and MOON47 of programs_struct/next/,
the old DM42 NAVLITTLE and MOON47, the Free42 NAVFULL / NAVLITTLE / MOON47 of v2.1.0 with the stack kept; every
program saves your stack at its start and gives it back at its end; the 2.2.1 headers.
The screens, the stack and the keys 1-8: tests/test_struct_src.py (C47, DM42) and tests/test_v221_f42.py (Free42).
      python3 tests/test_v221.py"""
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [os.path.join(ROOT, 'tools'), os.path.join(ROOT, 'python')]
import build_release_v221 as V                                               # noqa: E402
import build_release_c47 as R                                                # noqa: E402
import build_struct_src as B                                                 # noqa: E402
BAD = []


def ok(cond, what):
    print('  %s  %s' % ('ok  ' if cond else 'FAIL', what))
    if not cond:
        BAD.append(what)


def get(*p):
    return V.lines(os.path.join(V.OUT, *p))


def main():
    print('== build/v2.2.1/')
    L = B.build_next()
    a = get('c47', 'ALMA47.txt')
    ok(a == ['LBL "ALMA47"'] + L[1:], 'c47/ALMA47.txt: programs_struct/next/ (NAV named ALMA47), %d steps' % len(a))
    ok(a[1:5] == ['LocR 09', 'STOS R.00', 'RCL L', 'STO R.08'] and a.count('RCLS R.00') == 2,
       'ALMA47: LocR 9, STOS R.00, LASTx in R.08 at the start; RCLS R.00 at its two ends (0, a key 1-8)')
    ok('XEQ "N02"' in a and 'LBL "N05"' in a, 'ALMA47: the keys 1-8 on ALMANAC / SPLIT (N02 the table rows, N05 a key)')
    m = get('c47', 'MOON47.txt')
    ok(m == B.build_moon(B.NEXT) and 'STOS R.00' in m and 'RCLS R.00' in m, 'c47/MOON47.txt: programs_struct/next/MOON47.txt')
    for n in ('ALMA47', 'MOON47'):
        h = get('c47', 'p47u', n + '.p47u')
        ok('@ Version: 2.2.1' in h and any('forum' in l for l in h if l.startswith('@')),
           'c47/p47u/%s.p47u: Version 2.2.1, the forum trick in the header' % n)
    ok(get('c47', 'ALMA47_LABELS.txt')[0].startswith('ALMA47 v2.2.1'), 'c47/ALMA47_LABELS.txt: v2.2.1')
    S, I = R.little(V.LITTLE)
    ok(get('dm42', 'NAVLITTLE.txt') == S and 'STOS R.36' in S and 'RCLS R.36' in S,
       'dm42/NAVLITTLE.txt: programs_struct/little/NAVLITTLE_221.txt (STOS R.36 / RCLS R.36), %d steps' % len(S))
    ok(I == V.lines(os.path.join(R.DM42, 'NAVINIT_LITTLE.txt')), 'NAVINIT_LITTLE: the one of v2.2.0 (build/c47/dm42/)')
    d = get('dm42', 'MOON47.txt')
    ok(d == R.moon_dm42(V.MOON_NEXT, 4) and 'STOS R.00' in d, 'dm42/MOON47.txt: moon_dm42 of programs_struct/next/MOON47.txt')
    for n, label in (('NAVFULL', 'NAV'), ('NAVLITTLE', 'NAV'), ('MOON47', 'MOON47')):
        f = get('free42', n + '.txt')
        old = V.lines(os.path.join(ROOT, 'build', 'free42', n + '.txt'))
        i = f.index('LBL "%s"' % label)
        ok(f == V.f42_stack(old, label) and f[i + 1:i + 11] == V.F42_SAVE and len(f) == len(old) + 21
           and os.path.exists(os.path.join(V.F42, n + '.raw')),
           'free42/%s.txt (+ .raw): v2.1.0 with X Y Z T and LASTX saved (S7X ... S7L) and given back' % n)
    print('\n%s' % ('ALL PASSED' if not BAD else '%d FAILED' % len(BAD)))
    return 1 if BAD else 0


if __name__ == '__main__':
    sys.exit(main())
