ALMANAC 47 LITTLE WITH ATEXT - EXPERIMENTAL (DM42 / DM42n with the C47 firmware)
================================================================================

The same builds as NAVLITTLE, NAV1T and NAV12, with every text and number written by the new
C47 command ATEXT in the calculator's own standard font. Only the symbols of the Sun and the
stars stay AGRAPH (the 5 x 7 glyphs, PSYM). No small font. The warning line is only in the NAV12
menu (NAVLITTLE and NAV1T have no menu, so they have none). Needs a C47 firmware with ATEXT.

  NAVLITTLE_ATX.txt  NAVLITTLE with ATEXT: the inputs, then the ALMANAC screen
  NAV1T_ATX.txt      NAV1T with ATEXT: + ends with the text page in the registers
  NAV12_ATX.txt      NAV12 with ATEXT: menu 1 ALMANAC 2 CHART 3 TEXT; the chart with its
                     altitude labels and N E S W in the standard font
  INIT: NAVINIT_LITTLE (build/dm42/), as for NAVLITTLE.
Screens: docs/DM42_ATEXT_almanac.png.

HOW THE TEXT IS WRITTEN (tools/atext_common.py)
  PTXS keeps its stack (Z row of the base line, Y column, X text) and is the N03 trick of
  Didier (dlachieze): the stack turned for ATEXT, the row 4 lower, ATEXT Z, then 4 back. It is
  the only ATEXT step. A whole string is one ATEXT.
  The number printers put the number together as text in R18 (first digit from a table, then
  alpha-IP and x->alpha, checked on the C47) and write it with one ATEXT.
  The standard font is proportional: every column is its own call at a fixed x, numbers apart
  from letters.

SIZES (program bytes in the .p47 file) and steps for one ALMANAC screen (simulator)
                   5 x 7 font   ATEXT
  NAVLITTLE          12,716      8,119   (-36 %)   23,256 -> 11,962 steps
                                                   (text routines 15,323 -> 4,289)
  NAV1T              15,216     10,619   (-30 %)
  NAV12              18,516     13,865   (-25 %)

CONVERTING
  rejig 0.34 does not know ATEXT yet: tools/rejig47_atext.py writes each ATEXT as KTYP (the
  same kind of step), converts with rejig and sets the two bytes to ATEXT's (133 60). A rejig
  that knows ATEXT converts the .txt files directly.

Built by tools/build_dm42_atext.py (views from programs/atext/big/). Tested in the simulator
only (tests/test_dm42_atext.py); not yet on a calculator. The values are the same as NAVLITTLE's.
