NAVLITTLE (DM42 with the C47 firmware): the structural steps, one folder per step (branch struct-opt, Oct 2026)

Built from the release build/dm42/NAVLITTLE.txt by  python3 tools/build_struct.py little  (each step on top of the
one before). NAVLITTLE has only the ALMANAC screen: the chart, ANIM and ALLSKY steps of NAVFULL do not apply.

  1_tailcall/NAVLITTLE.txt   XEQ x + RTN -> GTO x (7 calls; not in or towards the LocR programs)
  2_order/NAVLITTLE.txt      + the programs reordered: most numbered jumps per label first
  3_callpos/NAVLITTLE.txt    + inside 6 programs, the blocks with the most calls per step first
  4_inline/NAVLITTLE.txt     + 12 calls to routines of 1-6 steps replaced by the steps (+38 steps)
  5_stars/NAVLITTLE.txt      + the stars of the ALMANAC loop by matrix, as NAVFULL's step 11, made light for 64 KB:
                             no 58-row matrices per time. NAV makes the star vectors SXA SXD (7.4 KB) the first time
                             (from NAVINIT_LITTLE's ST: the release NAVINIT_LITTLE stays); each new time two 4 x 3
                             matrices, SXG (-> the GHA frame) and SXH (-> north / east / zenith); per star the table
                             looks at, its row x SXH gives sin Hc (no trig, in place of SQK) and, for the stars it
                             keeps, row x SXG and 4 →POL give GHA Dec Hc Zn (in place of STR2 + Hc / Zn).

Load: NAVINIT_LITTLE (release, build/dm42/), run INIT, then the NAVLITTLE.p47 of a folder.
Size: release 7173 bytes; steps 1-3 7173; 4_inline 7298; 5_stars 8934.

Checked (firmware PC simulator, NAVINIT_LITTLE): every step pixel for pixel the release, ALMANAC, +1 h, back,
-1 h, at 2026-10-04 25.2 N 55.2 E, 2031-03-15 33.5 S 18.25 E, 2004-06-21 60.1 N 24.55 E, 2045-12-01 55 S 140 E.

Memory, free on the 64 KB DM42 (the simulator's figure minus the 192 KB the old DM42 does not have; NAVINIT
program still loaded: deleting it after INIT gives about 8.6 KB more):
  release: loaded 28.4 KB, after NAV 26.4 KB
  5_stars: loaded 26.4 KB, first run while the star vectors are made 8.8 KB (once), each new time 14.3 KB, per
           star 15.8 KB, after NAV 16.5 KB (SXA SXD kept)
  (NAVFULL's step 11 layout, 58-row matrices per time, left only a few bytes free here: not used.)

CPU (firmware PC simulator, with start-up), release / 4_inline / 5_stars first run / 5_stars later runs:
  ALMANAC                     0.121 / 0.117 / 0.157 / 0.109 s
  ALMANAC + 15 hour arrows    0.827 / 0.797 / 0.659 / 0.602 s   (the arrows alone about 0.71 -> 0.49 s, -30 %)
To make the star vectors again (another catalogue): DELITM "SXK".
