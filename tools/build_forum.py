#!/usr/bin/env python3
"""build_forum.py - the files for the PROGRAMS folder of the C47 release (res/PROGRAMS, rejig sources .p47u).

The release's res/PROGRAMS/BUILD.md: one .p47u per program, named after its main label, with '@' header lines
(Index: the one field every program needs; Author, Version optional; Source, Tested, Input, Output and notes).

  build/forum/ALMA47.p47u   the STRUCT build (build/dev/struct_src/NAVFULL.txt, tools/build_struct_src.py) with its
                            main label NAV named ALMA47 (the file name is the main label; nothing calls it); indented, the STRUCT partner numbers written, comments after ';'
  build/forum/NAVINIT.p47u  build/NAVINIT_FAST.txt with its label INIT named NAVINIT (the file name is the main label)
  build/forum/MOON47.p47u   MOON47 on its own (build/dev/struct_src/MOON47.txt): ONE program, LBL "MOON47" its only
                            global label, STRUCT, no GTO; indented, the partner numbers written

  build/forum/NAVINIT_FULL.p47u  build/NAVINIT_FULL.txt the same way (2000-2050, about twice the memory; for the v2.2.0
                            release zip: its main label is NAVINIT too)

The comments are those of build/dev/struct_src/NAVFULL_COMMENTED.txt and MOON47_COMMENTED.txt (tools/struct_comments.py),
at the end of a step after ';': rejig drops them. A '#' line (or one that starts with ';') would become a REM step on the
calculator. The almanac tables TBL are not in v2.2.0.

  python3 tools/build_forum.py      -> build/forum/ALMA47.p47u, NAVINIT.p47u, NAVINIT_FULL.p47u, MOON47.p47u
"""
import os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path[:0] = [HERE]
import c47struct as C                                                         # noqa: E402
import build_struct_src as B                                                  # noqa: E402

OUT = os.path.join(ROOT, 'build', 'forum')
AUTHOR = 'Victor Valdes'
VERSION = '2.2.0'
SOURCE = 'https://github.com/valdesvj/almanac47'
MAIN = 'ALMA47'                   # NAV's name in the release (LBL "NAV" -> LBL "ALMA47"; no step calls it by name)

NAV_HEAD = """@ Index:   Celestial navigation almanac, sky charts, sight reduction
@ Author:  %(author)s
@ Version: %(version)s
@ Source:  %(source)s
@ Tested:  on the C47 by the author (Oct 2026): every view, the arrows, the timing
@ Tested:  C47 simulator (python/c47sim.py): every view pixel for pixel the reference build, 3 places and 16
@ Tested:  random dates 2000-2049, 65 S - 65 N, FULL and FAST matrices
@ Input:   NAVINIT run once. XEQ 'ALMA47' asks DATE (YYYY.MMDD), UTC (H.MM), LAT and LON (D.MM, S and W negative)
@ Output:  FAST, DATE 2030.1019, UTC 17.45, LAT -53.11, LON 48.01, key 1 (ALMANAC) then the up arrow (18:45 UT):
@ Output:  Sun GHA 105 01.7, Dec S 10 11.7, Hc -22 35.0, Zn 208.9; the stars Canopus, Rigil Kent, Rigel, Achernar ...
@
@ Almanac 47: celestial navigation on the C47 / R47. Sun, Moon, planets and 58 stars: GHA, Dec, Hc, Zn for your
@ dead-reckoning position, sunrise, sunset, twilight, meridian passage, the Moon's phase, and sky charts.
@ DOES NOT REPLACE THE NAUTICAL ALMANAC.
@
@ Needs a C47 / R47 firmware with ATEXT, GRFNT and the STRUCT commands (00.109.05.00a0.ALPHA of 5 Oct 2026 or later).
@ The old DM42 (64 KiB) has its own version, NAVLITTLE, in the release (DM42 firmware packages 1-3 have STRUCT).
@
@ Two files: ALMA47.p47u (the programs that stay on the calculator) and NAVINIT.p47u (builds the matrices once).
@ The comments after ';' say what each part and each routine does (rejig drops them: they take no memory).
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
@ Matrices: NAVINIT.p47u builds the FAST set (a series fitted to 2026-2030; an X in the top right corner marks a
@ date outside it). NAVINIT_FULL.p47u (Almanac 47 v2.2.0 release) builds the FULL set instead: VSOP87 and Meeus
@ series, 2000-2050, about twice the memory; its program is NAVINIT too, so load one of the two. The almanac tables
@ (TBL) of earlier versions are not part of v2.2.0 (they are in the source repository).
@
@ Written with the STRUCT commands (IF ELSE ENDIF, DO WHILE ENDDO, REPEAT UNTIL), no GTO; the series and the
@ 58 stars with the matrix functions; the screens with ATEXT, AGRAPH and PIXEL.
@
"""

INIT_HEAD = """@ Index:   Matrices for ALMA47, valid 2026-2030
@ Author:  %(author)s
@ Version: %(version)s
@ Source:  %(source)s
@ Tested:  on the C47 by the author (Oct 2026); C47 simulator: ends with MATRICES READY: FAST 2026-2030
@ Input:   none
@ Output:  the matrices ALMA47 reads (Sun, Moon, planets, nutation, the star catalogue ST, the cache ALMC)
@ Output:  and the message MATRICES READY: FAST 2026-2030
@
@ Run once with ALMA47 loaded (XEQ 'NAVINIT'), then delete it (GTO 'NAVINIT', DELP): the matrices stay.
@ Run it again only for a new period.
@
@ Memory: this is the FAST set, a series fitted to 2026-2030 (smaller and faster). NAVINIT_FULL.p47u builds the
@ FULL set (2000-2050, about twice the memory) under the same program name: load one of the two.
@
"""

INIT_FULL_HEAD = """@ Index:   Matrices for ALMA47, valid 2000-2050 (FULL)
@ Author:  %(author)s
@ Version: %(version)s
@ Source:  %(source)s
@ Tested:  C47 simulator (python/c47sim.py): ends with MATRICES READY: FULL 2000-2050; ALMA47's views pixel for
@ Tested:  pixel the reference build at 16 random dates 2000-2049
@ Input:   none
@ Output:  the matrices ALMA47 reads (Sun, Moon, planets, nutation, the star catalogue ST, the cache ALMC)
@ Output:  and the message MATRICES READY: FULL 2000-2050
@
@ Run once with ALMA47 loaded (XEQ 'NAVINIT'), then delete it (GTO 'NAVINIT', DELP): the matrices stay.
@
@ Memory: the FULL set, VSOP87 (the Earth and the planets) and Meeus (the Moon) series valid 2000-2050: about
@ twice the memory of the FAST set (NAVINIT.p47u, 2026-2030). The program is called NAVINIT too (this file is
@ NAVINIT_FULL so that both can sit in one folder): load one of the two. Not in the PROGRAMS folder of the
@ firmware release, which has the FAST set only.
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
@ The old DM42 has a MOON47 of its own in the release (10 IF a program: the DM42 firmware's limit).
@ One program, MOON47 the only global label (the text printers and the phase symbols are numbered routines in it);
@ written with IF ELSE ENDIF, DO WHILE ENDDO, REPEAT UNTIL, no GTO.
@
"""


COL = 24                          # the column of the ';' comments


def commented(lines):
    """A listing with REM "..." lines for a .p47u: the comments go at the end of the step that follows them, after ';'.
    rejig drops an end-of-line ';' comment; a '#' line or a line that starts with ';' becomes a REM step on the
    calculator (memory, and steps every RTN walks), so no comment has a line of its own. A row of '=' (a new program)
    is a blank line."""
    out, notes, glob = [], [], False
    for l in lines:
        s = l.strip()
        if s.startswith('REM "') and glob:                     # the name and job of a global label: on its line
            out[-1] += (' - ' if ';' in out[-1] else ' ' * max(1, COL - len(out[-1])) + '; ') + s[5:-1]
        elif s.startswith('REM "'):
            t = s[5:-1]
            if set(t) == {'='}:
                out.append('')
            else:
                notes.append(t)
        elif s:
            out.append(l + (' ' * max(1, COL - len(l)) + '; ' + ' - '.join(notes) if notes else ''))
            notes = []
        else:
            out.append(l)
        glob = s.startswith('LBL "')
    assert not notes
    return out


def nav():
    """build_struct_src's commented listing, the REM lines as ';' comments, NAV named ALMA47."""
    L = B.build()
    com = B.commented(L)
    i = com.index('REM "program NAV"')                     # the listing's own title lines go: the '@' header says it
    out = []
    for l in commented(com[i - 1:]):
        if l.startswith('LBL "NAV"'):
            l = l.replace('LBL "NAV"', 'LBL "%s"' % MAIN, 1).replace('; program NAV - NAV - ', '; %s - ' % MAIN, 1)
        out.append(re.sub(r'; program (\w+) - \1 - ', r'; program \1 - ', l))
    assert [l.split(';')[0].strip() for l in out if l.strip()] == ['LBL "%s"' % MAIN] + L[1:]
    assert not any('"NAV"' in l for l in L[1:])                 # nothing calls NAV by name
    return out


MATRICES = ['The matrices (each a series, its rows the terms):',
            '  VL VB VR     the Earth for the Sun (L B R; FULL: VSOP87, FAST: fitted to 2026-2030)',
            '  EEL EEB EER  the Earth for the planets; VNL.. Venus, MAL.. Mars, JUL.. Jupiter, SAL.. Saturn (L B R)',
            '  ML MB        the Moon: longitude and distance, latitude (Meeus ch. 47); MCL MCB extra terms fitted to JPL DE421',
            '  NU           nutation;  ST the star catalogue (58 stars: RA, Dec, proper motion)']


def navinit(kind):
    """build/NAVINIT_<kind>.txt, its label INIT named NAVINIT, a ';' comment on each matrix routine."""
    L = [l for l in open(os.path.join(ROOT, 'build', 'NAVINIT_%s.txt' % kind), encoding='utf-8').read().split('\n') if l.strip()]
    assert L[0] == 'LBL "INIT"' and L.count('LBL "INIT"') == 1 and not any('"INIT"' in l for l in L[1:])
    out = ['LBL "NAVINIT"' + ' ' * (COL - 13) + '; NAVINIT - builds the matrices of ALMA47 (%s), then the cache ALMC and '
           'the message' % kind]
    for j, l in enumerate(L[1:], 1):
        m = re.fullmatch(r'LBL (\d\d)', l)
        if m:
            names, k = [], j + 1
            while k < len(L) and not L[k].startswith('LBL '):
                n = re.fullmatch(r'STO "(\w+)"', L[k])
                if n and n.group(1) not in names:
                    names.append(n.group(1))
                k += 1
            l += ' ' * (COL - len(l)) + '; routine %s: builds %s' % (m.group(1), ' '.join(names))
        out.append(l)
    return out


def moon():
    """build_struct_src's commented MOON47, the REM lines as ';' comments."""
    com = B.commented_moon(B.build_moon())
    return commented(com[3:])


def main():
    os.makedirs(OUT, exist_ok=True)
    f = {'author': AUTHOR, 'version': VERSION, 'source': SOURCE}
    for fname, head, body in (('%s.p47u' % MAIN, NAV_HEAD, nav()), ('NAVINIT.p47u', INIT_HEAD, navinit('FAST')),
                              ('NAVINIT_FULL.p47u', INIT_FULL_HEAD, navinit('FULL')), ('MOON47.p47u', MOON_HEAD, moon())):
        p = os.path.join(OUT, fname)
        if fname.startswith('NAVINIT'):
            head = head + ''.join('@ %s\n' % m for m in MATRICES) + '@\n'
        open(p, 'w', encoding='utf-8').write(head % f + '\n'.join(body) + '\n')
        print('  %s: %d steps, %d with a comment' % (p[len(ROOT) + 1:], sum(1 for l in body if l.strip()),
                                                    sum(1 for l in body if ';' in l)))


if __name__ == '__main__':
    main()
