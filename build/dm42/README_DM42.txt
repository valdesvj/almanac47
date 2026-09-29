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
                     UP / DOWN one hour later / earlier (SINKING box while it computes),
                     + ends (screen and stack cleared); no ants

Not in these builds: the Moon, the planets, the Moon phase, the almanac tables (TBL).
The Sun and star values are the same as in the full builds (same series): the Moon and
planet places in the list of ten bodies are taken by the next stars.

LOADING (load INIT alone first: INIT and its matrices together need the most memory)
  1. rejig NAVINIT_DM42.txt, load it, XEQ "INIT" -> MATRICES READY: SUN STARS 2000-2050
  2. delete INIT: GTO "INIT", CLP (the matrices stay)
  3. load NAVTXT_DM42 or NAV1_DM42 (one of them, both are called NAV), XEQ "NAV"
  If INIT is still loaded, the first NAV runs it (flag 81); CF 81 before a new INIT.
  The CLK date format must be YYYY-MM-DD, as for the full version.

MEMORY (estimate from the .p47 file sizes, not measured on a DM42)
  NAVINIT_DM42 about 28 KB while it runs, + its matrices about 11 KB; delete it after use.
  After INIT: matrices about 11 KB (667 numbers: Sun, nutation, stars).
  NAVTXT_DM42 about 21 KB  -> about 32 KB in all
  NAV1_DM42   about 42 KB  -> about 53 KB in all (tight in 64 KiB: try NAVTXT first)
  Please report the free memory you see (and any crash) on the forum or on GitHub.

Built with: python3 tools/build_dm42.py
