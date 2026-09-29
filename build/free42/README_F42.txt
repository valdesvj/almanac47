ALMANAC 47 FOR FREE42 - SwissMicros DM42 / DM42n with the stock (Free42) firmware
================================================================================

The full Almanac 47 (all views, no almanac tables) converted from the C47 to Free42 3.3
with the DM42 graphics extension (400 x 240). Same menu, same screens, same values: in the
Free42 core the screens were compared pixel by pixel with the C47 build (menu, ALMANAC,
CHART, SMALL, SPLIT, ALLSKY, INFO identical; the text page identical line by line).

FILES
  NAVFULL_F42.raw        the program NAV and its routines (load on the calculator)
  NAVINIT_F42_FULL.raw   INIT: the series matrices, valid 2000-2050
  NAVINIT_F42_FAST.raw   INIT: fitted series 2026-2030 (smaller, faster)
  *.txt                  the same programs as text (Free42 on a PC or phone: Paste them
                         into a program in PRGM mode)
  NAVFULL_F42_LABELS.txt the label map (every routine except NAV is N01, N02 ...)

LOADING (DM42n / DM42, stock firmware)
  1. Copy the .raw files to the calculator's disk (USB, the PROGRAMS folder).
  2. On the calculator: SETUP > Load Program, load NAVINIT_F42_FULL.raw (or _FAST).
  3. XEQ "INIT": builds the matrices, shows MATRICES READY. Then delete INIT (GTO "INIT",
     CLP or the program catalogue): the matrices stay.
  4. Load NAVFULL_F42.raw. XEQ "NAV".
  NAV asks DATE (YYYY.MMDD), UTC (HH.MMSS), LAT and LON (DD.MMm, south and west negative),
  like the C47 version, and works in the 400 x 240 graphics mode (GrMod 3). 0 on the menu
  ends NAV and sets the normal screen again (GrMod 0).

KEYS
  1 - 9      a view on the menu          +          back to the menu
  UP / DOWN  one hour later / earlier    0          end
  3 TEXT     the almanac page in R50 ... (as on the C47), drawn with the small font;
             + back to the menu (Free42 has no register browser)
  The ants: flag 97 (the HP-42S flag 47 is a system flag). SF 97 and try a view.

WHAT IS DIFFERENT FROM THE C47 VERSION (inside the programs, not on the screen)
  - AGRAPH draws the ALPHA register (8-pixel columns): the fonts are strings of column
    bytes; the drawing modes (OR, set, clear, XOR) are the HP-42S flags 34 and 35.
  - PIXEL, keys, pauses, TICKS, strings and the date input use Free42 functions (PX, KM,
    KQ, W1 / W10, TK, XSTR, APPEND, HEAD). No C47 date functions: the date is computed.
  - Not tested yet on a real DM42 / DM42n: tested in the Free42 3.3.10 core (SwissMicros
    source) with the DM42 graphics code, in binary (double) arithmetic.

Built with: python3 tools/build_free42.py
Copyright 2026 Victor Valdes. GNU GPL v3 or later. It supports, and does not replace,
the Nautical Almanac: always cross-check the values.
