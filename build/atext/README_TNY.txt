NAVFULL_TNY - EXPERIMENTAL: NAVFULL_ATX with the C47 tinyFont instead of the small AGRAPH font

Needs a C47 firmware with ATEXT and GRFNT (GRFNT 10 = tinyFont, 20 = standard font; Jaco Mostert).
The chart axes, N E S W, OVER / UNDER HORIZON, the ALLSKY stars and the SKY DR line are written
with ATEXT in the tinyFont (PTTY text, PTNT whole number: 10 GRFNT DROP, ATEXT, 20 GRFNT DROP).
The small 3 x 5 AGRAPH font (PTXT, PTNS) is gone; only the body symbols stay AGRAPH (PSYM).
The tinyFont is 5 x 7 (6 columns per character, 8-row lines, nothing under the base line), so the
letters are bigger than the old 3 x 5 font; a few places moved (DR line, letters under the horizon,
OVER HORIZON inside the ANIM / ALLSKY chart).

.p47: tools/rejig47_atext.py (ATEXT item 1340, GRFNT item 1342 = bytes 133 62).
Test the firmware first with extras/TNYTST (one tiny line, one standard line).
Simulator: python/tinyfont.py from res/fonts/C47__TinyFont.ttf (tools/generators/mktiny.py).

NAVFULL_T21 - EXPERIMENTAL: as NAVFULL_TNY with all the text in GRFNT 21 (the standard font, one
column narrower per character) and the glyphs47 symbols: 12 rows in the tables (PSYB), 7 rows on the
charts (PSYS). CHART shows the star numbers again (37 ARCTURUS). NAV sets GRFNT 21 after the inputs
and 20 again on the way out (0 END, TEXT); R/S leaves font 21 set (20 GRFNT puts it back).
Views: programs/atext/t21/ (genviews_atx.py mode 't21'); preview docs/grfnt/NAVFULL_T21_views_sim.png.
