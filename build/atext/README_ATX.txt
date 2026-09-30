NAVFULL WITH ATEXT - EXPERIMENTAL (C47 / R47 with a firmware that has ATEXT)
============================================================================

NAVFULL_ATX.txt is NAVFULL with every text and number written by the C47's ATEXT command in
its standard font. Only the body symbols (Sun, Moon, planets, stars) keep the AGRAPH glyphs
of the status-bar font (PSYM). The small 3 x 5 font is gone. INIT: NAVINIT_FULL or
NAVINIT_FAST (build/), as for NAVFULL.

THE VIEWS (docs/NAVFULL_ATEXT_views.png)
  menu, 1 ALMANAC, 5 SMALL  as before, the columns made for the standard font
  2 CHART   the horizon 4 rows higher (the letters N E S W fit under it), altitude labels in the
            standard font; the panel without the star numbers (name only)
  4 SKY     the same, the DR position top right to the minute
  6 SPLIT   chart on top, the table (up to 6 bodies) without the ARIES row, 2 footer lines
  7 ANIM, 8 ALLSKY  no altitude axis, no OVER / UNDER HORIZON, no star numbers on ALLSKY
  9 INFO, 3 TEXT    as before

HOW THE TEXT IS WRITTEN
  PTXS keeps its stack (Z row of the base line, Y column, X text) and is the N03 trick of
  Didier (dlachieze): the stack turned for ATEXT, the row 4 lower (ATEXT takes the bottom of
  its 20-row glyph box), ATEXT Z, then 4 back, so a text can follow at the returned place.
  It is the only ATEXT step in the program.
  The number printers (PINS PF1S PHMS PDMS PDTS PZNS) are NAVFULL's, but each character is
  added to a string (variable ATX; flag 48) and the number is written with one ATEXT.
  The standard font is proportional (digits and space 8 px, '.' 5 px, letters 5 to 14 px):
  every column is its own call at a fixed x, numbers apart from letters.
  A chained text (drawn at the place the one before returned) must not start after x 380:
  ATEXT then goes to the next line.

SIZES (program bytes in the .p47 file) and simulator steps (INIT, sky and the view)
                  NAVFULL   NAVFULL_ATX
  program          42,130      34,136   (-19 %)
  1 ALMANAC        59,327      40,283
  2 CHART          68,831      51,619
  8 ALLSKY         71,000      52,642

CONVERTING: tools/rejig47_atext.py (rejig 0.34 does not know ATEXT: KTYP placeholder, then
the two bytes 133 60), or a rejig that knows ATEXT directly.

Built by tools/build_navfull_atext.py from tools/generators/atext/genviews_atx.py
(programs/atext/). Tested in the simulator (tests/test_navfull_atext.py), not yet on a
calculator.
