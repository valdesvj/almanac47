ALMANAC 47 v2.2.0 "Struct on Attack" LITTLE - the old DM42 with the C47 firmware
================================================================================

The C47 firmware on the old DM42 has 64 KiB for programs, registers and matrices (the DM42n and the
R47 have 256 KiB: they run the full ALMA47 of the main zip). The full Almanac 47 does not fit in
64 KiB: this version, made only for the old DM42, keeps the Sun and the 58 navigation stars.

  NAVINIT_LITTLE   the program NAVINIT, reduced: only the Sun series (FULL, valid 2000-2050), the
                   nutation and the stars (8.7 KB; the full NAVINIT is 28.5 or 57.8 KB)
  NAVLITTLE        the program ALMA47: no menu, straight to the ALMANAC screen after the inputs;
                   UP / DOWN one hour later / earlier (the screen stays while it computes),
                   9 SNAP, + ends (screen and stack cleared)
  MOON47           the Moon phase on its own, the DM42 build of the v2.2.0 MOON47

FIRMWARE: a C47 firmware for the DM42 with ATEXT, GRFNT and STRUCT. In the firmware sources
(c43 master of 10 Oct 2026) ATEXT and GRFNT are in all four DM42 packages, and STRUCT is in
PACKAGES 1, 2 and 3 (at most 10 IF, 10 DO and 10 REPEAT in a program, 10 open at once). PACKAGE 4,
the one in the release assets of 00.109.05.00a0.ALPHA, has ATEXT and GRFNT but NOT STRUCT: with it,
IF / DO / REPEAT only show that they are not available. Check PACKAGES.txt of your firmware.
With a firmware without STRUCT, keep the NAVLITTLE of v2.0.0 ("DM42 with the C47 firmware").

STRUCTURED PROGRAMMING ON THE LITTLE MEMORY
  The DM42 firmware keeps its tables for the STRUCT commands small: at most 10 IF, 10 DO and
  10 REPEAT in each program (partner numbers 1-10) and 10 structures open at once. The R47, the
  DM42n and the C47 take 255 of each and 63 open. So, for the old DM42:
    NAVLITTLE  written within the limit (its largest program has 6 IF, 2 DO, 1 REPEAT)
    MOON47     a build of its own: 10 IF, 5 DO, 6 REPEAT in its one program. The main MOON47 has
               17 IF; here 7 of them are a test and an XEQ of a small routine instead, so the same
               steps run and the page is the same pixel for pixel.
    ALMA47     (up to 23 IF in a program) is not for the old DM42 anyway: with its matrices it
               needs far more than 64 KiB.

NEW IN v2.2.0: written with the STRUCT commands (no GTO) and its routines ordered for the C47's
searches: about 57 % less of the time spent looking for labels and returns than v2.1.0 (C47
simulator), the same screen pixel for pixel. The names are those of the main zip: XEQ "NAVINIT",
XEQ "ALMA47". Your registers R00-R35 are still saved while it runs and given back at the end.

LOADING (load NAVINIT alone first: NAVINIT and its matrices together need the most memory)
  1. load NAVINIT_LITTLE.p47, XEQ "NAVINIT" -> MATRICES READY: SUN STARS 2000-2050
  2. delete it: GTO "NAVINIT", DELP (the matrices stay)
  3. load NAVLITTLE.p47, XEQ "ALMA47"
  NAVINIT sets flag 81 when it is done: ALMA47 then does not look for it. If NAVINIT is still
  loaded and has not run, the first ALMA47 runs it. If ALMA47 stops with an undefined label at
  its start: SF 81 (the matrices are there) and XEQ "ALMA47" again.
  DATE is asked in the CLK date format (YYYY.MMDD, DD.MMYYYY or MM.DDYYYY, as the message line
  shows), as in the full version.

Not in NAVLITTLE: the Moon, the planets, the menu, the sky cache. The Sun and star values are those
of the full version (same series).

MOON47: load MOON47.p47, XEQ "MOON47" (no NAVINIT). It asks nothing (the clock; if the clock is not
on UT: 4 STO "TZ" for UT+4). +/- north / south view, other keys end. About 4.5 KB; R03-R53.

MEMORY (program bytes, rejig): NAVINIT_LITTLE 8.7 KB (delete it after use), NAVLITTLE 7.3 KB,
MOON47 4.5 KB. NAVLITTLE and its matrices take about 31 KB.

CHECKED: in the C47 simulator pixel for pixel v2.1.0 (NAVLITTLE, 16 dates and places) and the main
MOON47 (16 dates); in the firmware simulator with no error. Not yet on an old DM42: please report
the free memory you see (and any problem) on the forum or on GitHub.

For the DM42 / DM42n with the stock firmware (Free42): keep v2.1.0.

Built with: python3 tools/build_release_c47.py (the STRUCT source: programs_struct/little/).
