#!/usr/bin/env python3
"""build_forum.py - the two files for the PROGRAMS folder of the C47 release (res/PROGRAMS, rejig sources .p47u).

The release's res/PROGRAMS/BUILD.md: one .p47u per program, named after its main label, with '@' header lines
(Index: the one field every program needs; Author, Version optional; Source, Tested, Input, Output and notes).

  build/forum/ALMA47.p47u   the STRUCT build (build/dev/struct_src/NAVFULL.txt, tools/build_struct_src.py) with its
                            main label NAV named ALMA47 (the file name is the main label; nothing calls it); indented, the STRUCT partner numbers written, a '#' line under each global
                            label (its original name and job)
  build/forum/NAVINIT.p47u  build/NAVINIT_FAST.txt with its label INIT named NAVINIT (the file name is the main label)
  build/forum/MOON47.p47u   MOON47 on its own (build/dev/struct_src/MOON47.txt): ONE program, LBL "MOON47" its only
                            global label, STRUCT, no GTO; indented, the partner numbers written

Only the FAST matrices (2026-2030) are supplied: NAVINIT_FULL (2000-2050) and the almanac tables TBL need more memory.

  python3 tools/build_forum.py      -> build/forum/ALMA47.p47u, NAVINIT.p47u, MOON47.p47u
"""
import os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path[:0] = [HERE]
import c47struct as C                                                         # noqa: E402
import build_struct_src as B                                                  # noqa: E402

OUT = os.path.join(ROOT, 'build', 'forum')
AUTHOR = 'Victor Valdes'
VERSION = '2.2'
SOURCE = 'https://github.com/valdesvj/almanac47'
MAIN = 'ALMA47'                   # NAV's name in the release (LBL "NAV" -> LBL "ALMA47"; no step calls it by name)

NAV_HEAD = """@ Index:   Celestial navigation almanac, sky charts, sight reduction
@ Author:  %(author)s
@ Version: %(version)s
@ Source:  %(source)s
@ Tested:  C47 simulator (python/c47sim.py): every view pixel for pixel the v2 screens, 3 places and 16 random dates
@ Tested:  2000-2049, 65 S - 65 N, FULL and FAST matrices
@ Input:   NAVINIT run once. XEQ 'ALMA47' asks DATE (YYYY.MMDD), UTC (H.MM), LAT and LON (D.MM, S and W negative)
@ Output:  FAST, DATE 2030.1019, UTC 17.45, LAT -53.11, LON 48.01, key 1 (ALMANAC) then the up arrow (18:45 UT):
@ Output:  Sun GHA 105 01.7, Dec S 10 11.7, Hc -22 35.0, Zn 208.9; the stars Canopus, Rigil Kent, Rigel, Achernar ...
@
@ Almanac 47: celestial navigation on the C47 / R47. Sun, Moon, planets and 58 stars: GHA, Dec, Hc, Zn for your
@ dead-reckoning position, sunrise, sunset, twilight, meridian passage, the Moon's phase, and sky charts.
@ DOES NOT REPLACE THE NAUTICAL ALMANAC.
@
@ Needs a C47 / R47 firmware with ATEXT, GRFNT and the STRUCT commands (00.109.05.00a0.ALPHA of 5 Oct 2026 or later).
@
@ Two files: ALMA47.p47u (the programs that stay on the calculator) and NAVINIT.p47u (builds the matrices once).
@   1. Load both. XEQ 'NAVINIT': it ends with MATRICES READY: FAST 2026-2030.
@   2. Delete NAVINIT (GTO 'NAVINIT', DELP): the matrices stay. Do not use CLPALL (it deletes ALMA47 too).
@   3. XEQ 'ALMA47': date, UT and position once, then the menu:
@      1 ALMANAC  2 SPLIT  3 SKY  4 ANIM  5 ALLSKY  6 INFO  9 SNAP (a picture of the screen)  0 END.
@      In a view: + back to the menu, up / down arrow one hour later / earlier.
@
@ Only ALMA47 has a name; the other programs show as N01, N02 ... ALMA47 uses the numbered registers and the 8-level stack
@ and clears them when it ends (CLREGS, CLSTK): save your registers first. It keeps its named matrices between runs
@ (the sky of the last time and place: the same inputs again show the views at once).
@
@ Memory: only the FAST matrices are supplied (a fitted series, valid 2026-2030; an X in the top right corner marks
@ a date outside them). The full package also has NAVINIT_FULL (VSOP87 and Meeus series, 2000-2050, about twice
@ the memory) and the almanac tables TBL (1 or 5 years); they are left out here because of the memory they need.
@ All of them are in the source repository.
@
@ Written with the STRUCT commands (IF ELSE ENDIF, DO WHILE ENDDO, REPEAT UNTIL), no GTO; the series and the
@ 58 stars with the matrix functions; the screens with ATEXT, AGRAPH and PIXEL.
@
"""

INIT_HEAD = """@ Index:   Matrices for ALMA47, valid 2026-2030
@ Author:  %(author)s
@ Version: %(version)s
@ Source:  %(source)s
@ Tested:  C47 simulator (python/c47sim.py): ends with MATRICES READY: FAST 2026-2030; ALMA47's views then as v2
@ Input:   none
@ Output:  the matrices ALMA47 reads (Sun, Moon, planets, nutation, the star catalogue ST, the caches ALMC, ALMQ)
@ Output:  and the message MATRICES READY: FAST 2026-2030
@
@ Run once with ALMA47 loaded (XEQ 'NAVINIT'), then delete it (GTO 'NAVINIT', DELP): the matrices stay.
@ Run it again only for a new period.
@
@ Memory: this is the FAST set, a series fitted to 2026-2030 (smaller and faster). The full package also has
@ NAVINIT_FULL (VSOP87 and Meeus series, 2000-2050, about twice the memory) and the almanac tables TBL (1 or 5
@ years); they are not supplied here because of the memory they need. All of them are in the source repository.
@
"""

MOON_HEAD = """@ Index:   Moon phase, age and the next phases
@ Author:  %(author)s
@ Version: %(version)s
@ Source:  %(source)s
@ Tested:  C47 simulator (python/c47sim.py): the page pixel for pixel the Python reference (python/moon47.py),
@ Tested:  16 dates 2000-2050, time zones, north and south (and the three-program version checked on the firmware)
@ Input:   none: the date and time from the clock (UT; for a clock on local time UT+4: 4 STO 'TZ')
@ Output:  clock 03-10-2026 12:00 UT: LAST QUARTER, 51 %% lit, age 22.4 days, HP 59.2', SD 16.1';
@ Output:  next phases (UT) 03-10 13:25 last quarter, 10-10 15:50 new, 18-10 16:13 first quarter, 26-10 04:13 full
@
@ MOON47: the Moon phase on its own, from the calculator's clock. The phase as a disc, %% lit, age, horizontal
@ parallax HP and semi-diameter SD, the next four phases (UT) with their symbols.
@ Keys: +/- turns the picture to the view from the south, any other key ends.
@ 20 terms of Meeus ch. 47 (phases within 4 minutes, HP 0.03'); the terms as matrices, their cos and sin from one
@ complex e^x. Needs no other program and no NAVINIT; ends with a clear stack. It changes the registers R03-R53
@ (save yours first); its work matrices M7T, M7C, M7A, M7V, M7W are set to 0 at the end (TZ stays).
@
@ Needs a C47 / R47 firmware with ATEXT and the STRUCT commands (00.109.05.00a0.ALPHA of 5 Oct 2026 or later).
@ One program, MOON47 the only global label (the text printers and the phase symbols are numbered routines in it);
@ written with IF ELSE ENDIF, DO WHILE ENDDO, REPEAT UNTIL, no GTO.
@
"""


def nav():
    L = B.build()
    out = []
    for name, P in zip(B.ORDER, C.split(L)):
        for l in C.indent(P):
            out.append(l)
            m = re.fullmatch(r'\s*LBL "(\w+)"', l)
            if m:
                n, what = B.LABELS[m.group(1)]
                if m.group(1) == 'NAV':
                    out[-1] = 'LBL "%s"' % MAIN
                    n = MAIN
                out.append(l[:len(l) - len(l.lstrip())] + '  # %s - %s' % (n, what))
    assert [l.strip() for l in out if not l.strip().startswith('#')] == ['LBL "%s"' % MAIN] + L[1:]
    assert not any('"NAV"' in l for l in L[1:])                 # nothing calls NAV by name
    return out


def navinit():
    L = [l for l in open(os.path.join(ROOT, 'build', 'NAVINIT_FAST.txt'), encoding='utf-8').read().split('\n') if l.strip()]
    assert L[0] == 'LBL "INIT"' and L.count('LBL "INIT"') == 1 and not any('"INIT"' in l for l in L[1:])
    return ['LBL "NAVINIT"'] + L[1:]


def moon():
    return C.indent(B.build_moon())


def main():
    os.makedirs(OUT, exist_ok=True)
    f = {'author': AUTHOR, 'version': VERSION, 'source': SOURCE}
    for fname, head, body in (('%s.p47u' % MAIN, NAV_HEAD, nav()), ('NAVINIT.p47u', INIT_HEAD, navinit()),
                              ('MOON47.p47u', MOON_HEAD, moon())):
        p = os.path.join(OUT, fname)
        open(p, 'w', encoding='utf-8').write(head % f + '\n'.join(body) + '\n')
        print('  %s: %d steps' % (p[len(ROOT) + 1:], sum(1 for l in body if l.strip() and not l.strip().startswith('#'))))


if __name__ == '__main__':
    main()
