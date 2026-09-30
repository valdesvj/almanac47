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

NAVLITTLE draws with the 5 x 7 font of the first versions (PTXB) instead of the status-bar
font: about 3.4 KB less. No sky cache: the screen computes what it shows. No ants and no
SINKING box: the screen shown stays until the next one is drawn.

Not in NAVLITTLE: the Moon, the planets, the Moon phase. It reads the almanac tables when
they are loaded (TBL, flag 10) for the Sun and GHA Aries, but in 64 KiB only a very short
table can fit (make one with tools/almanac/tab2c47.py START END). The Sun
and star values are the same as in the full builds (same series): the Moon and planet places
in the list of ten bodies are taken by the next stars.

LOADING (load INIT alone first: INIT and its matrices together need the most memory)
  The .p47 files are ready to load (converted with rejig); the .txt files are the same
  programs as text.
  1. load NAVINIT_LITTLE.p47, XEQ "INIT" -> MATRICES READY: SUN STARS 2000-2050
  2. delete INIT: GTO "INIT", CLP (the matrices stay)
  3. load NAVLITTLE.p47, XEQ "NAV"
  INIT sets flag 81 when it is done: NAV then does not look for INIT. If INIT is still
  loaded and has not run, the first NAV runs it. If NAV stops with an undefined label at
  its start: SF 81 (the matrices are there) and XEQ "NAV" again.
  The CLK date format must be YYYY-MM-DD, as for the full version.

MEMORY (program sizes measured with rejig: the program bytes in the .p47 file; the .p47
file on disk is about 3 times bigger because it stores each byte as a decimal number)
  After INIT: matrices about 11 KB (667 numbers: Sun, nutation, stars; estimate).
                     program   with the matrices
  NAVINIT_LITTLE      8.5 KB   ~19 KB while it runs; delete it after use
  NAVLITTLE          11.9 KB   ~23 KB
  How much of the 64 KiB is left for programs after the firmware's own use is not known
  here: please report the free memory you see (and any crash) on the forum or on GitHub.

OTHER BUILDS (build/dm42/dev/, not in the release)
  NAVTXT_DM42      6.6 KB  text only: the almanac page in the registers, NAV ends in REGS
  NAV1T_DM42      14.3 KB  NAVLITTLE, and + ends with the text page of the hour shown
  NAV12_DM42      17.5 KB  menu 1 ALMANAC, 2 CHART, 3 TEXT
  NAVINIT_DM42_5Y  7.7 KB  INIT with the Sun's FAST series, valid 2026-2030 only
  build/dm42/dev/src/ has every build with the original label names.

The same NAVLITTLE for the DM42 / DM42n with the stock firmware (Free42): build/free42/.

Built with: python3 tools/build_dm42.py
