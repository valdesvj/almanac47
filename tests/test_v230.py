#!/usr/bin/env python3
"""test_v230.py - the v2.3.0 release folder (build/v2.3.0/, tools/build_release_v230.py) is the next version:
  c47/     ALMA47.txt = LBL "ALMA47" + build_struct_src.build_next()[1:]; MOON47.txt, p47u/ = build/dev/next/'s;
           the p47u headers say Version 2.3.0; QUICKSTART and the labels file say v2.3.0 and +/-
  dm42/    NAVLITTLE.txt and MOON47.txt = build/dev/next/dm42/ALMA47.txt and MOON47.txt; README says v2.3.0
  free42/  NAVFULL, NAVLITTLE, MOON47 (.txt, .raw) = build/dev/next/free42/'s; README says v2.3.0
  the release notes and the manuals' sources say v2.3.0
The screens themselves: tests/test_struct_src.py, test_next_f42.py, test_moon47_f42.py, test_web_calc.py.
  python3 tests/test_v230.py"""
import filecmp, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [os.path.join(ROOT, 'tools')]
import build_struct_src as B                                                  # noqa: E402

REL = os.path.join(ROOT, 'build', 'v2.3.0')
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


def main():
    print('== build/v2.3.0/ is the next version')
    L = B.build_next()
    ok(lines(os.path.join(REL, 'c47', 'ALMA47.txt')) == ['LBL "ALMA47"'] + L[1:],
       'c47/ALMA47.txt: the next build, %d steps' % len(L))
    for a, b in (('c47/MOON47.txt', 'MOON47.txt'), ('c47/p47u/ALMA47.p47u', 'ALMA47.p47u'),
                 ('c47/p47u/MOON47.p47u', 'MOON47.p47u'), ('dm42/NAVLITTLE.txt', 'dm42/ALMA47.txt'),
                 ('dm42/MOON47.txt', 'dm42/MOON47.txt'), ('free42/NAVFULL.txt', 'free42/NAVFULL.txt'),
                 ('free42/NAVLITTLE.txt', 'free42/NAVLITTLE.txt'), ('free42/MOON47.txt', 'free42/MOON47.txt'),
                 ('free42/NAVFULL.raw', 'free42/NAVFULL.raw'), ('free42/NAVLITTLE.raw', 'free42/NAVLITTLE.raw'),
                 ('free42/MOON47.raw', 'free42/MOON47.raw')):
        ok(same(os.path.join(REL, a), os.path.join(NEXT, b)), '%s = build/dev/next/%s' % (a, b))
    for p in ('ALMA47', 'MOON47'):
        ok('@ Version: 2.3.0\n' in text(REL, 'c47', 'p47u', p + '.p47u'), 'p47u/%s.p47u: Version 2.3.0' % p)
    q = text(REL, 'c47', 'QUICKSTART.txt')
    ok(q.startswith('Almanac 47 v2.3.0 "Local Time"') and '+/- (the change-sign key)' in q and 'STO "TZ"' in q
       and 'v2.2.1.zip' not in q, 'QUICKSTART: v2.3.0, +/-, TZ, the v2.3.0 zips')
    ok(text(REL, 'c47', 'ALMA47_LABELS.txt').startswith('ALMA47 v2.3.0 "Local Time"'), 'ALMA47_LABELS: v2.3.0')
    for d, f in (('dm42', 'README_DM42.txt'), ('free42', 'README_F42.txt')):
        t = text(REL, d, f)
        ok('v2.3.0' in t and '+/-' in t and 'TZ' in t, '%s/%s: the v2.3.0 note' % (d, f))
    ok('# Almanac 47 v2.3.0' in text(ROOT, 'RELEASE_NOTES_v2.3.0.md'), 'RELEASE_NOTES_v2.3.0.md')
    ok("VERSION = '2.3.0'" in text(ROOT, 'tools', 'generators', 'manual_nav.py')
       and 'version 2.3.0' in text(ROOT, 'tools', 'generators', 'build_port_manuals.py'), 'the manuals: v2.3.0')
    ok(os.path.exists(os.path.join(ROOT, 'docs', 'c47', 'ALMF_LT.png')), 'docs/c47/ALMF_LT.png')
    print('%d failed' % bad if bad else 'ALL OK')
    return bad


if __name__ == '__main__':
    sys.exit(1 if main() else 0)
