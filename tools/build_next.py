#!/usr/bin/env python3
"""build_next.py - the next version of ALMA47, apart from the v2.2.0 release (build/c47/, build/forum/ stay as they are).

From programs_struct/next/ (tools/build_struct_src.py build_next: the v2.2.0 source with these changes):
  - your stack (8 levels) and LASTx kept: saved at NAV's own level (LocR 09) and given back at the end
  - NAV's numbered registers in one block R07-R98 (tools/regblock.py); its end clears only that block (R-CLR 7.92):
    R00-R06 and R99 stay yours; the numbers R43-R98 and the DR R13 / R14 as in v2.2.0
  - on ALMANAC and SPLIT a key 1-8 picks that row's body: ALMA47 ends with Z its text (NAME Zn ddd.d Hc dd mm.m),
    Y its Zn, X its Hc on your stack (program PICK: N02 N03 N05 N07)

  build/dev/next/ALMA47.txt     the programs (NAV named ALMA47); NAVINIT is the release's (build/c47/NAVINIT_*.txt)
  build/dev/next/ALMA47.p47u    the same as a rejig source: the '@' header, a ';' comment on each global label
  build/dev/next/ALMA47.p47     with rejig (not in git)

  python3 tools/build_next.py
"""
import os, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path[:0] = [HERE]
import c47struct as C                                                         # noqa: E402
import build_struct_src as B                                                  # noqa: E402

OUT = os.path.join(ROOT, 'build', 'dev', 'next')
MAIN = 'ALMA47'
COL = 40

HEAD = """@ Index:   Celestial navigation almanac, sky charts, sight reduction
@ Author:  Victor Valdes
@ Version: next (after 2.2.0, not released)
@ Source:  https://github.com/valdesvj/almanac47
@ Tested:  C47 simulator (python/c47sim.py) only: every view pixel for pixel v2.2.0, the stack (4 levels) and LASTx
@ Tested:  kept, R00-R06 / R99 kept, keys 1-8 on ALMANAC and SPLIT give the bodies of the PC almanac (python/native)
@ Input:   NAVINIT of v2.2.0 run once. XEQ 'ALMA47' asks DATE, UTC, LAT, LON as v2.2.0
@ Output:  ALMANAC, key 1: Z 'SUN Zn 216.7 Hc 54 11.6' (2026-10-04 9:30 UT, 25 20 N 55 12 E), Y Zn, X Hc
@
@ As ALMA47 v2.2.0, and:
@   - your stack (X ... D with the 8-level stack) and LASTx are as before XEQ 'ALMA47' when it ends;
@   - it uses the registers R07-R98 and clears only those when it ends (R-CLR 7.92): R00-R06 and R99 stay yours;
@   - on ALMANAC and SPLIT a key 1-8 picks a body of the table (1 the Sun): ALMA47 ends with Z its text,
@     Y its Zn, X its Hc (decimal degrees) pushed on your stack.
@ The other keys as v2.2.0: + menu, up / down arrow one hour, 9 SNAP, 0 on the menu ends.
@ DOES NOT REPLACE THE NAUTICAL ALMANAC.
@
"""


def listing():
    L = B.build_next()
    assert L[0] == 'LBL "NAV"' and not any('"NAV"' in l for l in L[1:])
    return ['LBL "%s"' % MAIN] + L[1:]


def source(L):
    out = []
    for l in C.indent(L):
        s = l.strip()
        if s.startswith('LBL "'):
            g = s[5:-1]
            n, what = B.NEXT_NAV if g == MAIN else B.LABELS[g]
            l += ' ' * max(1, COL - len(l)) + '; %s - %s' % (MAIN if g == MAIN else n, what)
        out.append(l)
    return out


def main():
    os.makedirs(OUT, exist_ok=True)
    L = listing()
    open(os.path.join(OUT, 'ALMA47.txt'), 'w', encoding='utf-8').write('\n'.join(L) + '\n')
    P = source(L)
    assert [l.split(';')[0].strip() for l in P] == L
    open(os.path.join(OUT, 'ALMA47.p47u'), 'w', encoding='utf-8').write(HEAD + '\n'.join(P) + '\n')
    size = None
    if shutil.which('rejig'):
        subprocess.run(['rejig', '--validate=r47', '-o', os.path.join(OUT, 'ALMA47.p47'), os.path.join(OUT, 'ALMA47.txt')],
                       check=True)
        T = open(os.path.join(OUT, 'ALMA47.p47'), encoding='ascii').read().split('\n')
        size = T[T.index('PROGRAM') + 1]
    print('  build/dev/next/ALMA47.txt, ALMA47.p47u: %d steps; .p47 %s bytes' % (len(L), size or '? (no rejig)'))


if __name__ == '__main__':
    main()
