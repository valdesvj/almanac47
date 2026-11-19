#!/usr/bin/env python3
"""test_v240.py - the v2.4.0 release folder (build/v2.4.0/, tools/build_release_v240.py) is the next version:
  c47/     ALMA47.txt = LBL "ALMA47" + build_struct_src.build_next()[1:]; MOON47.txt, p47u/ = build/dev/next/'s;
           the p47u headers say Version 2.4.0; QUICKSTART and the labels file say v2.4.0 and the five prompts
  dm42/    NAVLITTLE.txt and MOON47.txt = build/dev/next/dm42/'s; README says v2.4.0
  free42/  NAVFULL, NAVLITTLE, MOON47 (.txt, .raw) = build/dev/next/free42/'s; README says v2.4.0
  r47/     the C47 ALMA47 with the R47 arrows (tests/test_r47_keys.py with REL=2.4.0: the screens)
  the prompts: TZ first and the clock / Medellin block in ALMA47, NAVLITTLE and Free42's NAVFULL / NAVLITTLE;
  the release notes and the manuals' sources say v2.4.0
The prompts in the firmware and in f42run: tests/test_struct_src.py, test_next_f42.py; the screens there too.
  python3 tests/test_v240.py"""
import filecmp, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [os.path.join(ROOT, 'tools')]
import build_struct_src as B                                                  # noqa: E402
import build_r47_v230 as R4                                                   # noqa: E402

REL = os.path.join(ROOT, 'build', 'v2.4.0')
NEXT = os.path.join(ROOT, 'build', 'dev', 'next')
bad = 0


def ok(cond, what):
    global bad
    bad += not cond
    print('  %s  %s' % ('ok  ' if cond else 'FAIL', what))


def lines(p):
    return [l.rstrip('\n') for l in open(p, encoding='utf-8') if l.strip()]


def text(*p):
    return open(os.path.join(*p), encoding='utf-8').read()


def same(a, b):
    return os.path.exists(a) and os.path.exists(b) and filecmp.cmp(a, b, shallow=False)


def has(L, seq):
    return any(L[i:i + len(seq)] == seq for i in range(len(L) - len(seq) + 1))


def main():
    print('== build/v2.4.0/ is the next version')
    L = B.build_next()
    A = lines(os.path.join(REL, 'c47', 'ALMA47.txt'))
    ok(A == ['LBL "ALMA47"'] + L[1:], 'c47/ALMA47.txt: the next build, %d steps' % len(L))
    for a, b in (('c47/MOON47.txt', 'MOON47.txt'), ('c47/p47u/ALMA47.p47u', 'ALMA47.p47u'),
                 ('c47/p47u/MOON47.p47u', 'MOON47.p47u'), ('dm42/NAVLITTLE.txt', 'dm42/ALMA47.txt'),
                 ('dm42/MOON47.txt', 'dm42/MOON47.txt'), ('free42/NAVFULL.txt', 'free42/NAVFULL.txt'),
                 ('free42/NAVLITTLE.txt', 'free42/NAVLITTLE.txt'), ('free42/MOON47.txt', 'free42/MOON47.txt'),
                 ('free42/NAVFULL.raw', 'free42/NAVFULL.raw'), ('free42/NAVLITTLE.raw', 'free42/NAVLITTLE.raw'),
                 ('free42/MOON47.raw', 'free42/MOON47.raw')):
        ok(same(os.path.join(REL, a), os.path.join(NEXT, b)), '%s = build/dev/next/%s' % (a, b))
    ok(lines(os.path.join(REL, 'r47', 'ALMA47.txt')) == R4.r47(A), 'r47/ALMA47.txt: the C47 one with the R47 arrows')
    c47 = ['"TZ HOURS  W -"', 'INPUT "TZ"', 'CLSTK', 'Date→ⅅ', 'Time→ℸ', 'ⅅℸ→J', 'RCL "TZ"', '24', '÷', '-', 'J→ⅅℸ']
    med = ['6.139', 'STO "LAT"', '-75.354', 'STO "LON"']
    for f in ('c47/ALMA47.txt', 'r47/ALMA47.txt', 'dm42/NAVLITTLE.txt'):
        P = lines(os.path.join(REL, f))
        ok(has(P, c47) and has(P, med) and P.index('INPUT "TZ"') < P.index('INPUT "DATE"'),
           '%s: TZ first, DATE / UTC from the clock - TZ, Medellin' % f)
    for f in ('free42/NAVFULL.txt', 'free42/NAVLITTLE.txt'):
        P = lines(os.path.join(REL, f))
        ok(has(P, ['XSTR "TZ HOURS  W -"', 'INPUT "TZ"']) and has(P, ['TIME', '→HR', 'RCL- "TZ"']) and has(P, med)
           and P.index('INPUT "TZ"') < P.index('INPUT "DATE"'), '%s: TZ first, TIME - TZ, Medellin' % f)
    for p in ('ALMA47', 'MOON47'):
        ok('@ Version: 2.4.0\n' in text(REL, 'c47', 'p47u', p + '.p47u'), 'p47u/%s.p47u: Version 2.4.0' % p)
    q = text(REL, 'c47', 'QUICKSTART.txt')
    ok(q.startswith('Almanac 47 v2.4.0 "Here and Now"') and 'TZ, DATE, UTC, LAT, LON' in q and 'Medellin' in q
       and 'v2.3.0.zip' not in q, 'QUICKSTART: v2.4.0, the five prompts, Medellin, the v2.4.0 zips')
    ok(text(REL, 'r47', 'QUICKSTART.txt').startswith('Almanac 47 v2.4.0 "Here and Now" - QUICK START, R47 KEYBOARD')
       and 'v2.4.0' in text(REL, 'r47', 'README_R47.txt'), 'r47/: QUICKSTART and README v2.4.0')
    ok(text(REL, 'c47', 'ALMA47_LABELS.txt').startswith('ALMA47 v2.4.0 "Here and Now"'), 'ALMA47_LABELS: v2.4.0')
    for d, f in (('dm42', 'README_DM42.txt'), ('free42', 'README_F42.txt')):
        t = text(REL, d, f)
        ok('v2.4.0' in t and 'Medellin' in t and 'TZ' in t, '%s/%s: the v2.4.0 note' % (d, f))
    ok('# Almanac 47 v2.4.0 "Here and Now"' in text(ROOT, 'RELEASE_NOTES_v2.4.0.md'), 'RELEASE_NOTES_v2.4.0.md')
    ok("VERSION = '2.4.0'" in text(ROOT, 'tools', 'generators', 'manual_nav.py')
       and 'version 2.4.0' in text(ROOT, 'tools', 'generators', 'build_port_manuals.py'), 'the manuals: v2.4.0')
    print('%d failed' % bad if bad else 'ALL OK')
    return bad


if __name__ == '__main__':
    sys.exit(1 if main() else 0)
