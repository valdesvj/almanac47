ALMANAC 47 LITTLE WITH ATEXT - EXPERIMENTAL (DM42 / DM42n with the C47 firmware)
================================================================================

The same builds as NAVLITTLE, NAV1T and NAV12, but the text of the ALMANAC page (and of the
NAV12 menu) is written with the new C47 command ATEXT in the calculator's own standard font
instead of the 5 x 7 AGRAPH font. Needs a C47 firmware with ATEXT.

  NAVLITTLE_ATX.txt  NAVLITTLE with ATEXT: the inputs, then the ALMANAC screen
  NAV1T_ATX.txt      NAV1T with ATEXT: + ends with the text page in the registers
  NAV12_ATX.txt      NAV12 with ATEXT: menu 1 ALMANAC 2 CHART 3 TEXT; the chart keeps the
                     5 x 7 font (the standard font is too big for it)
  INIT: NAVINIT_LITTLE (build/dm42/), as for NAVLITTLE.

HOW THE TEXT IS WRITTEN
  PTXS (the text routine) keeps its stack: Z row of the base line, Y column, X text. Inside it
  is the N03 trick of Didier (dlachieze): the stack turned for ATEXT, the row 4 lower (ATEXT
  takes the bottom of its 20-row glyph box), ATEXT Z, then the row 4 higher again, so a text
  can follow at the returned place. It is the only ATEXT step in each program.
  The number printers (PINS PF1S PHMS PDMS PDTS PZNS) are the same routines as before, but
  every character is appended to a string (R18, with x→α) instead of drawn, and the number
  is written with one ATEXT at the end.
  The standard font is proportional: digits and the space are 8 px, '.' 5 px, letters 5 to
  14 px. So every column is its own call at a fixed x: names, N / S and the other letters
  apart from the numbers, and a number always has the same width (its padding is a space as
  wide as a digit).
  The symbols of the Sun, Moon, stars and planets stay the 5 x 7 AGRAPH glyphs (PSYM, or
  PTXB in NAV12), and the small font of the bottom line (PTXT) stays too.

SIZES (program bytes in the .p47 file) and steps for one ALMANAC screen (simulator)
                   5 x 7 font   ATEXT
  NAVLITTLE          12,716     10,482   (-18 %)   24,924 -> 19,706 steps
  NAV1T              15,216     12,982   (-15 %)
  NAV12              18,516     19,838   (+7 %: the chart keeps the 5 x 7 font as well)

CONVERTING
  rejig 0.34 does not know ATEXT yet: tools/rejig47_atext.py writes each ATEXT as KTYP
  (the same kind of step), converts with rejig and sets the two bytes to ATEXT's (133 60).
  A rejig that knows ATEXT converts the .txt files directly.

Tested in the simulator only (python/c47sim.py draws ATEXT like the C47 source); not yet on a
calculator. The values are the same as NAVLITTLE's.
