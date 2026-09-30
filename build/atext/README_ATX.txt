NAVFULL WITH ATEXT - EXPERIMENTAL (C47 / R47 with a firmware that has ATEXT)
============================================================================

NAVFULL_ATX.txt is NAVFULL with the texts and numbers of the screens written by the C47's
ATEXT command in its standard font. INIT: NAVINIT_FULL or NAVINIT_FAST (build/), as for NAVFULL.
  - the body symbols (Sun, Moon, planets, stars) keep the AGRAPH glyphs of the status-bar font
    (PSYM)
  - the charts keep NAVFULL's look: axes, altitude marks, N E S W, OVER / UNDER HORIZON, the
    ALLSKY stars with their numbers and the SKY DR line in the small font (PTXT)
  - the warning line only in the menu and in INFO (and on the TEXT page in the registers),
    not on the views
Screens: docs/NAVFULL_ATEXT_views.png.

HOW THE TEXT IS WRITTEN (tools/atext_common.py)
  PTXS keeps its stack (Z row of the base line, Y column, X text) and is the N03 trick of
  Didier (dlachieze): the stack turned for ATEXT, the row 4 lower (ATEXT takes the bottom of
  its 20-row glyph box), ATEXT Z, then 4 back, so a text can follow at the returned place.
  It is the only ATEXT step in the program. A whole string is one ATEXT.
  The number printers (PINS PF1S PHMS PDMS PDTS PZNS) put the number together as text in R49:
  the first digit from a small table, then whole numbers appended with alpha-IP and signs with
  x->alpha (both checked on the C47: NATTEST); then one ATEXT. Same text as before.
  The standard font is proportional (digits and space 8 px, '.' 5 px, letters 5 to 14 px):
  every column is its own call at a fixed x, numbers apart from letters. A chained text
  (drawn at the place the one before returned) must not start after x 380: ATEXT then goes to
  the next line.

SIZES (program bytes in the .p47 file) and simulator steps (INIT not counted)
                        NAVFULL   NAVFULL_ATX
  program                42,130      36,915   (-12 %; the small font stays for the charts)
  menu + 1 ALMANAC       52,787      27,300   text routines 30,987 -> 5,721 steps

CONVERTING: tools/rejig47_atext.py (rejig 0.34 does not know ATEXT: KTYP placeholder, then
the two bytes 133 60), or a rejig that knows ATEXT directly.

Built by tools/build_navfull_atext.py from tools/generators/atext/genviews_atx.py
(programs/atext/). Tested in the simulator (tests/test_navfull_atext.py), not yet on a
calculator.
