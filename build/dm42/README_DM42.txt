ALMANAC 47 - DM42 BETA (C47 firmware on the DM42)
===================================================

The C47 on the DM42 has 64 KiB for programs, registers and matrices (the DM42n and the
R47 have 256 KiB). The full Almanac 47 does not fit there: the Moon and planet series alone
are about 45 KB. These beta builds keep the Sun and the 58 navigation stars.

  NAVINIT_DM42.txt   INIT: Sun series (FULL, valid 2000-2050), nutation, stars
  NAVINIT_DM42_5Y.txt  or this INIT: the same with the Sun's FAST series, valid 2026-2030 only
                     (90 numbers less in memory, about 1.4 KB; the same values in its period)
  NAVTXT_DM42.txt    text only: the almanac page in the registers, NAV ends in REGS
  NAV1_DM42.txt      no menu: straight to the ALMANAC screen after the inputs;
                     UP / DOWN one hour later / earlier (the screen stays while it computes),
                     + ends (screen and stack cleared); no ants
  NAV1T_DM42.txt     NAV1, and + ends with the text page of the hour shown (as NAVTXT:
                     registers R50 ..., the stack, REGS)
  NAV12_DM42.txt     menu 1 ALMANAC, 2 CHART, 3 TEXT. The biggest one: see MEMORY

The drawing builds use the 5 x 7 font of the first versions (PTXB) instead of the status-bar
font: about 3.4 KB less. No sky cache: each screen computes what it shows. No ants and no
SINKING box: the screen shown stays until the next one is drawn.

Not in these builds: the Moon, the planets, the Moon phase, the almanac tables (TBL).
The Sun and star values are the same as in the full builds (same series): the Moon and
planet places in the list of ten bodies are taken by the next stars.

LOADING (load INIT alone first: INIT and its matrices together need the most memory)
  The .p47 files are ready to load (converted with rejig); the .txt files are the same
  programs as text.
  1. load NAVINIT_DM42.p47, XEQ "INIT" -> MATRICES READY: SUN STARS 2000-2050
  2. delete INIT: GTO "INIT", CLP (the matrices stay)
  3. load ONE of NAVTXT_DM42, NAV1_DM42, NAV1T_DM42, NAV12_DM42 (all are called NAV), XEQ "NAV"
  INIT sets flag 81 when it is done: NAV then does not look for INIT. If INIT is still
  loaded and has not run, the first NAV runs it. If NAV stops with an undefined label at
  its start: SF 81 (the matrices are there) and XEQ "NAV" again.
  The CLK date format must be YYYY-MM-DD, as for the full version.

MEMORY (program sizes measured with rejig: the program bytes in the .p47 file; the .p47
file on disk is about 3 times bigger because it stores each byte as a decimal number)
  After INIT: matrices about 11 KB (667 numbers: Sun, nutation, stars; estimate).
                     program   with the matrices
  NAVINIT_DM42        8.5 KB   ~19 KB while it runs; delete it after use
  NAVINIT_DM42_5Y     7.7 KB   ~18 KB while it runs
  NAVTXT_DM42         6.6 KB   ~18 KB
  NAV1_DM42          11.9 KB   ~23 KB
  NAV1T_DM42         14.3 KB   ~26 KB
  NAV12_DM42         17.5 KB   ~29 KB
  (the full NAVALL for the C47 / R47: 40.5 KB of program)
  How much of the 64 KiB is left for programs after the firmware's own use is not known
  here: please report the free memory you see (and any crash) on the forum or on GitHub.

Built with: python3 tools/build_dm42.py
