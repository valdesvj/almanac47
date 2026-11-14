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

MOON47 the same way (programs_struct/next/MOON47.txt, build_struct_src.build_moon(NEXT)): v2.2.0's MOON47 with your stack
(8 levels) and LASTx kept (LocR 09), its registers R07-R65 (v2.2.0's R03-R61 + 4) cleared at its end (R-CLR 7.59):
R00-R06 and R66-R99 stay yours.
  build/dev/next/MOON47.txt     the program
  build/dev/next/MOON47.p47u    the rejig source, the comments of build/forum/MOON47.p47u (their register numbers + 4)
  build/dev/next/MOON47.p47     with rejig (not in git)

  python3 tools/build_next.py
"""
import os, re, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path[:0] = [HERE]
import c47struct as C                                                         # noqa: E402
import build_struct_src as B                                                  # noqa: E402
import build_forum as F                                                       # noqa: E402

OUT = os.path.join(ROOT, 'build', 'dev', 'next')
MAIN = 'ALMA47'
COL = 40

HEAD = """@ Index:   Celestial navigation almanac, sky charts, sight reduction
@ Author:  Victor Valdes
@ Version: 2.3.0
@ Source:  https://github.com/valdesvj/almanac47
@ Tested:  C47 simulator (python/c47sim.py): every view pixel for pixel v2.2.0 but the new header, the stack and LASTx
@ Tested:  kept, R00-R06 / R99 kept, keys 1-8 on ALMANAC and SPLIT give the bodies of the PC almanac (python/native)
@ Input:   NAVINIT of v2.2.0 run once. XEQ 'ALMA47' asks DATE, UTC, LAT, LON as v2.2.0
@ Output:  ALMANAC, key 1: Z 'SUN Zn 216.7 Hc 54 11.6' (2026-10-04 9:30 UT, 25 20 N 55 12 E), Y Zn, X Hc
@
@@NARRATIVE@@
@ ---- Technical notes ----
@ As ALMA47 v2.2.0, and:
@   - your stack (X ... D with the 8-level stack) and LASTx are as before XEQ 'ALMA47' when it ends: saved with
@     LocR 9 / STOS R.00 (LASTx in R.08) and given back with RCLS R.00, the trick from the SwissMicros forum;
@   - it uses the registers R07-R98 and clears only those when it ends (R-CLR 7.92): R00-R06 and R99 stay yours;
@   - on ALMANAC and SPLIT a key 1-8 picks a body of the table (1 the Sun): ALMA47 ends with Z its text,
@     Y its Zn, X its Hc (decimal degrees) pushed on your stack.
@   - +/- on the menu or a view shows every time in UT or in local time, LT = UT + the variable TZ (the switch is
@     the variable TZLT, kept; ALMA47 makes TZ and TZLT 0 when they are missing). DATE and UTC are asked in UT.
@   - the header of every view: the date and time (UT / LT) on the left, the view's name inverted in the middle,
@     the position on the right (no DR); the menu's position moved the same way.
@ The other keys as v2.2.0: + menu, up / down arrow one hour, 9 SNAP, 0 on the menu ends.
@ DOES NOT REPLACE THE NAUTICAL ALMANAC.
@
"""

MOON_HEAD = """@ Index:   Moon phase, age and the next phases
@ Author:  Victor Valdes
@ Version: 2.3.0
@ Source:  https://github.com/valdesvj/almanac47
@ Tested:  C47 simulator (python/c47sim.py) only: the page pixel for pixel v2.2.0 (16 dates 2000-2050, time zones,
@ Tested:  north and south), the stack (4 levels) and LASTx kept, R00-R06 / R66-R99 kept, R07-R65 cleared
@ Input:   none: the date and time from the clock (UT; for a clock on local time UT+4: 4 STO 'TZ')
@ Output:  the page as v2.2.0 (clock 03-10-2026 12:00 UT: LAST QUARTER, 51 % lit, age 22.4 days, HP 59.2', SD 16.1')
@
@@NARRATIVE@@
@ ---- Technical notes ----
@ 2.3.0: +/- UT or LT. 2.2.2: the disc drawn with two AGRAPH words a column (the outline and the lit part merged, each half one word
@ 2^(b+1) - 2^a): the page in about 21 000 steps instead of 30 000 (3.6 s instead of 5.1 s), the same pixels.
@ As MOON47 v2.2.0, and:
@   - your stack (X ... D with the 8-level stack) and LASTx are as before XEQ 'MOON47' when it ends (LocR 9,
@     STOS R.00 / RCLS R.00, from the SwissMicros forum);
@   - it uses the registers R07-R65 and clears only those when it ends (R-CLR 7.59): R00-R06 and R66-R99 stay yours.
@ Keys: 0 turns the picture to the view from the south, +/- shows the times in UT or in LT = UT + TZ (the variable
@ TZLT keeps the choice), any other key ends. Its work matrices M7T, M7C, M7A, M7V,
@ M7W as v2.2.0 (M7T, M7C set to 0 at the end; TZ stays).
@ Needs a C47 / R47 firmware with ATEXT and the STRUCT commands (00.109.05.00a0.ALPHA of 5 Oct 2026 or later).
@
"""


def moon():
    """MOON47 of the next version: (listing, .p47u body). The comments of build/forum/MOON47.p47u, the register numbers
    in them moved as the code (+ 4)."""
    M = B.build_moon(B.NEXT)
    com = [re.sub(r'\bR(\d\d)\b', lambda m: 'R%02d' % (int(m.group(1)) + 4), l) if l.strip().startswith('REM ') else l
           for l in B.commented_moon(M)[3:]]
    return M, F.commented(com)


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


def narrative(head, name):
    """The '@' header with tools/forum/NAME.txt (what it does, how to use it, what it changes, the labels) in it."""
    lines = open(os.path.join(ROOT, 'tools', 'forum', name + '.txt'), encoding='utf-8').read().rstrip('\n').split('\n')
    text = '\n'.join('@ ' + l if l.strip() else '@' for l in lines) + '\n@'
    return head.replace('@@NARRATIVE@@', text)


def full(L):
    """ALMA47's steps with the comments of build_struct_src.commented (every program, routine and table; the
    next version's programs, PICK among them), after ';' as build_forum's; the main label's line as source()'s."""
    old = B.ORDER
    B.ORDER = B.NEXT_ORDER
    try:
        com = B.commented(['LBL "NAV"'] + L[1:])
    finally:
        B.ORDER = old
    out = F.commented(com[4:])
    while not out[0].strip():
        out.pop(0)
    out[0] = source(L)[0]
    assert [l.split(';')[0].strip() for l in out if l.strip()] == L
    return out


def main():
    os.makedirs(OUT, exist_ok=True)
    L = listing()
    open(os.path.join(OUT, 'ALMA47.txt'), 'w', encoding='utf-8').write('\n'.join(L) + '\n')
    P = full(L)
    open(os.path.join(OUT, 'ALMA47.p47u'), 'w', encoding='utf-8').write(narrative(HEAD, 'ALMA47') + '\n'.join(P) + '\n')
    M, MP = moon()
    open(os.path.join(OUT, 'MOON47.txt'), 'w', encoding='utf-8').write('\n'.join(M) + '\n')
    assert [l.split(';')[0].strip() for l in MP if l.strip()] == M
    open(os.path.join(OUT, 'MOON47.p47u'), 'w', encoding='utf-8').write(narrative(MOON_HEAD, 'MOON47') + '\n'.join(MP) + '\n')
    for name, n in (('ALMA47', len(L)), ('MOON47', len(M))):
        size = None
        if shutil.which('rejig'):
            subprocess.run(['rejig', '--validate=r47', '-o', os.path.join(OUT, name + '.p47'), os.path.join(OUT, name + '.txt')],
                           check=True)
            T = open(os.path.join(OUT, name + '.p47'), encoding='ascii').read().split('\n')
            size = T[T.index('PROGRAM') + 1]
        print('  build/dev/next/%s.txt, %s.p47u: %d steps; .p47 %s bytes' % (name, name, n, size or '? (no rejig)'))
    dm42()


def dm42():
    """the old DM42 with the C47 firmware: ALMA47 (NAVLITTLE, programs_struct/little/NAVLITTLE_221.txt: the stack kept,
    UT / LT on +/-) and MOON47 (the next version's, at most 10 structures a program) in build/dev/next/dm42/; NAVINIT:
    v2.2.0's build/dm42/NAVINIT_LITTLE.txt, unchanged"""
    import build_release_c47 as R
    d = os.path.join(OUT, 'dm42')
    os.makedirs(d, exist_ok=True)
    S, I = R.little(os.path.join(ROOT, 'programs_struct', 'little', 'NAVLITTLE_221.txt'))
    assert I == R.lines(os.path.join(R.DM42, 'NAVINIT_LITTLE.txt')), 'NAVINIT_LITTLE is the one of v2.2.0'
    M = R.moon_dm42(os.path.join(ROOT, 'programs_struct', 'next', 'MOON47.txt'), 4)
    for name, P in (('ALMA47', S), ('MOON47', M)):
        path = os.path.join(d, name + '.txt')
        open(path, 'w', encoding='utf-8').write('\n'.join(P) + '\n')
        size = None
        if shutil.which('rejig'):
            subprocess.run(['rejig', '--validate=r47', '-o', path[:-4] + '.p47', path], check=True)
            T = open(path[:-4] + '.p47', encoding='ascii').read().split('\n')
            size = T[T.index('PROGRAM') + 1]
        print('  build/dev/next/dm42/%s.txt: %d steps; .p47 %s bytes' % (name, len(P), size or '? (no rejig)'))


if __name__ == '__main__':
    main()
