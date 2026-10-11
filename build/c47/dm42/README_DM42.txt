ALMANAC 47 v2.2.0 "Struct on Attack" LITTLE - the old DM42 with the C47 firmware
================================================================================

The C47 firmware on the old DM42 has 64 KiB for programs, registers and matrices (the DM42n and the
R47 have 256 KiB: they run the full ALMA47 of the main zip). The full Almanac 47 does not fit in
64 KiB: NAVLITTLE keeps the Sun and the 58 navigation stars.

  NAVINIT_LITTLE   the program NAVINIT: Sun series (FULL, valid 2000-2050), nutation, stars
  NAVLITTLE        the program ALMA47: no menu, straight to the ALMANAC screen after the inputs;
                   UP / DOWN one hour later / earlier (the screen stays while it computes),
                   9 SNAP, + ends (screen and stack cleared)

NEW IN v2.2.0: written with the C47 STRUCT commands (IF / DO / REPEAT, no GTO), within the limits
of the DM42 build of the firmware (at most 10 IF, 10 DO and 10 REPEAT in each program, 10 open at
once), and its routines ordered for the C47's searches: about 57 % less of the time spent looking
for labels and returns than v2.1.0 (C47 simulator), the same screens pixel for pixel. The names
are those of the main zip: XEQ "NAVINIT", XEQ "ALMA47". Your registers R00-R35 are still saved
while it runs and given back at the end.
Firmware: a C47 firmware for the DM42 with ATEXT, GRFNT and STRUCT (00.109.05.00a0.ALPHA, 5 Oct
2026, or later).

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

MEMORY (program bytes, rejig): NAVINIT_LITTLE 8.7 KB (delete it after use), NAVLITTLE 7.3 KB
(v2.1.0: 7.2 KB). NAVLITTLE and its matrices take about 31 KB.

MOON47: the v2.2.0 MOON47 of the main zip has more than 10 IF in its one program, which the DM42
build of the firmware does not take. MOON47.p47 here is the v2.1.0 one (no STRUCT; the same page).

For the DM42 / DM42n with the stock firmware (Free42): keep v2.1.0.

Built with: python3 tools/build_release_c47.py (the STRUCT source: programs_struct/little/).
