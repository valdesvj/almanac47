ALMANAC 47 LITTLE - the old DM42 with the C47 firmware
=====================================================

The C47 on the DM42 has 64 KiB for programs, registers and matrices (the DM42n and the
R47 have 256 KiB). The full Almanac 47 does not fit there: the Moon and planet series alone
are about 45 KB. NAVLITTLE keeps the Sun and the 58 navigation stars.

  NAVINIT_LITTLE.txt  INIT: Sun series (FULL, valid 2000-2050), nutation, stars
  NAVLITTLE.txt       NAV: no menu, straight to the ALMANAC screen after the inputs;
                      UP / DOWN one hour later / earlier (the screen stays while it
                      computes), + ends (screen and stack cleared)

The file name is the version: on the calculator the programs are called NAV and INIT, as in
the full version.

NAVLITTLE needs a C47 firmware with ATEXT and GRFNT: it draws the ALMANAC screen of NAVFULL
(Oct 2026), every text with ATEXT in GRFNT 21 (no tinyFont, no font of its own); the only glyphs
drawn are the symbols of the Sun and the star (glyphs47). The footer has the twilight, rise / set
and meridian passage of the Sun. No sky cache: the screen computes what it shows. No ants and no
SINKING box: the screen shown stays until the next one is drawn.

Not in NAVLITTLE: the Moon (no Moon line, no phase), the planets. It reads the almanac tables when
they are loaded (TBL, flag 10) for the Sun and GHA Aries, but in 64 KiB only a very short
table can fit (make one with tools/almanac/tab2c47.py START END). The Sun
and star values are the same as in the full builds (same series): the Moon and planet places
in the list of eight bodies are taken by the next stars.

LOADING (load INIT alone first: INIT and its matrices together need the most memory)
  The .p47 files are ready to load (converted with tools/rejig47_atext.py); the .txt files are the same
  programs as text.
  1. load NAVINIT_LITTLE.p47, XEQ "INIT" -> MATRICES READY: SUN STARS 2000-2050
  2. delete INIT: GTO "INIT", CLP (the matrices stay)
  3. load NAVLITTLE.p47, XEQ "NAV"
  INIT sets flag 81 when it is done: NAV then does not look for INIT. If INIT is still
  loaded and has not run, the first NAV runs it. If NAV stops with an undefined label at
  its start: SF 81 (the matrices are there) and XEQ "NAV" again.
  DATE is asked in the CLK date format (YYYY.MMDD, DD.MMYYYY or MM.DDYYYY, as the message line
  shows), as in the full version.

MEMORY (program sizes measured with rejig 0.34.1 and tools/rejig47_atext.py, Oct 2026: the
program bytes in the .p47 file; the .p47
file on disk is about 3 times bigger because it stores each byte as a decimal number)
  After INIT: matrices about 11 KB (667 numbers: Sun, nutation, stars; estimate).
                     program   with the matrices
  NAVINIT_LITTLE      8.5 KB   ~19 KB while it runs; delete it after use
  NAVLITTLE           7.9 KB   ~19 KB
  How much of the 64 KiB is left for programs after the firmware's own use is not known
  here: please report the free memory you see (and any crash) on the forum or on GitHub.

OTHER BUILDS (build/dm42/dev/, not in the release)
  NAVTXT_DM42      7.2 KB  text only: the almanac page in the registers, NAV ends in REGS
  NAV1T_DM42      10.2 KB  NAVLITTLE, and + ends with the text page of the hour shown
  NAV12_DM42      13.5 KB  menu 1 ALMANAC, 2 CHART (its labels in the tinyFont), 3 TEXT
  NAVINIT_DM42_5Y  7.7 KB  INIT with the Sun's FAST series, valid 2026-2030 only
  build/dm42/dev/src/ has every build with the original label names.

For the DM42 / DM42n with the stock firmware (Free42): build/free42/NAVLITTLE, the same screen
(no ATEXT there: its own AGRAPH fonts with the same pixels).

Built with: python3 tools/build_dm42.py
