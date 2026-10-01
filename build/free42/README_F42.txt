ALMANAC 47 FOR FREE42 - SwissMicros DM42 / DM42n with the stock (Free42) firmware
================================================================================

Almanac 47 converted from the C47 to Free42 3.3 with the DM42 graphics extension (400 x 240).
Same names, same screens, same values as the C47 files: in the Free42 core the screens were
compared pixel by pixel with the C47 builds.

User manual: docs/Almanac47_Free42_Manual.pdf

FILES (the file name is the version: on the calculator the programs are NAV and INIT)
  NAVFULL.raw          NAV: all 9 views (as the C47 NAVFULL, without the almanac tables)
  NAVLITTLE.raw        NAV: Sun and 58 stars only, straight to the ALMANAC screen, UP / DOWN
                       one hour, + ends; no box, no ants. The ALMANAC screen as in NAVFULL
                       (header line with a line under it, the same fonts) with Sun and stars,
                       and the Moon line: % lit, the phase glyph and the age, from the mean
                       lunation (within about 14 hours of the true age). For little memory.
  NAVINIT_FULL.raw     INIT for NAVFULL: the series matrices, valid 2000-2050
  NAVINIT_FAST.raw     INIT for NAVFULL: fitted series 2026-2030 (smaller, faster)
  NAVINIT_LITTLE.raw   INIT for NAVLITTLE: Sun, nutation and stars, valid 2000-2050
  TBL_1.raw            almanac tables, 1 year (1 Oct 2026 - 30 Sep 2027), 97 KB
  TBL_5.raw            almanac tables, 5 years (1 Oct 2026 - 30 Sep 2031), 481 KB
                       Optional: load ONE, XEQ "TBL" once (it builds the matrices TSU ... TAR and
                       sets flag 10), then delete it. NAVFULL and NAVLITTLE then take the Sun, the
                       Moon, the planets and GHA Aries from the tables (JPL DE421) inside their
                       period, and the screens show T instead of S; CF 10 = the series again.
                       The matrices need about 135 KB (1 year) or 670 KB (5 years): for Free42 /
                       Plus42 on a PC or phone.
  *.txt                the same programs as text (Free42 on a PC or phone: Paste them into
                       a program in PRGM mode)
  NAVFULL_LABELS.txt, NAVLITTLE_LABELS.txt   the label maps (every routine except NAV is
                       N01, N02 ...; the numbers are fixed: tools/labels/F42_*.map)
  dev/NAVFULL_DRAW     NAVFULL with the Free42 screen update (each screen builds up as it is
                       drawn); dev/src/ has the programs with the original label names

LOADING (DM42n / DM42, stock firmware)
  1. Copy the .raw files to the calculator's disk (USB, the PROGRAMS folder).
  2. On the calculator: SETUP > Load Program, load NAVINIT_FULL.raw (or NAVINIT_FAST.raw;
     NAVINIT_LITTLE.raw for NAVLITTLE).
  3. XEQ "INIT": builds the matrices, shows MATRICES READY. Then delete INIT (GTO "INIT",
     CLP or the program catalogue): the matrices stay.
  4. Load NAVFULL.raw (or NAVLITTLE.raw). XEQ "NAV".
  NAV asks DATE in the calculator's date format (YMD: YYYY.MMDD, DMY: DD.MMYYYY, MDY: MM.DDYYYY;
  flags 67 / 31, only read; the hint shows it), UTC (HH.MMSS), LAT and LON (DD.MMm, south and
  west negative),
  like the C47 version, and works in the 400 x 240 graphics mode (GrMod 3). 0 on the menu
  (NAVLITTLE: +) ends NAV and sets the normal screen again (GrMod 0).
  The Free42 and Plus42 simulators on a PC run the programs but have no GrMod: they show
  only the top-left corner (131 x 16) of the screens.

KEYS (NAVFULL)
  1 - 9      a view on the menu          +          back to the menu
  UP / DOWN  one hour later / earlier    0          end
  3 TEXT     the almanac page in R50 ... (as on the C47), drawn with the small font;
             + back to the menu (Free42 has no register browser)
  The ants: flag 97 (the HP-42S flag 47 is a system flag). SF 97 and try a view.

SCREEN UPDATE
  Free42 shows every AGRAPH / PIXEL at once, so a program builds each screen up in front of
  you. The C47 shows its screen only at a PAUSE, when it waits for a key and at the end, so
  there the SINKING box stays until the finished screen appears in one piece.
  NAVFULL and NAVLITTLE do the same on the DM42: 0 STO "RefLCD" (no LCD refresh while NAV
  computes and draws), -1 STO "RefLCD" where the C47 program has PAUSE 0, before every key
  wait and pause. At the end NAV sets RefLCD 7 (normal) again.
  If you stop it with R/S or EXIT, the screen may stay frozen: key 7 STO "RefLCD".
  dev/NAVFULL_DRAW keeps the Free42 way (no RefLCD).

WHAT IS DIFFERENT FROM THE C47 VERSION (inside the programs, not on the screen)
  - AGRAPH draws the ALPHA register (8-pixel columns): the fonts are strings of column
    bytes; the drawing modes (OR, set, clear, XOR) are the HP-42S flags 34 and 35.
  - PIXEL, keys, pauses, TICKS, strings and the date input use Free42 functions (PX, KM,
    KQ, W1 / W10, TK, XSTR, APPEND, HEAD). No C47 date functions: the date is computed.
  - NAVFULL tested by the author on a DM42n (SwissMicros firmware DM42-3.26, Free42 3.3.10).
    NAVLITTLE is new: tested in the Free42 3.3.10 core (SwissMicros source) with the DM42
    graphics code (binary arithmetic), where its screens are the same as the C47 simulator
    pixel by pixel (tests/test_f42_little.py); not yet on a real calculator.
  - The texts: PTXS, an AGRAPH font with the glyphs and widths of the C47 font 21 (GRFNT 21);
    the symbols and Moon phases: PSYB / PSYS; the small texts: PTTY (the C47 tinyFont).

Built with: python3 tools/build_free42.py
Copyright 2026 Victor Valdes. GNU GPL v3 or later. It supports, and does not replace,
the Nautical Almanac: always cross-check the values.
