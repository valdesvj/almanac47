Structural optimizations of the C47 NAVFULL (branch struct-opt, Oct 2026)

One folder per step; each step is applied on top of the one before it. The release build/NAVFULL.txt and
programs/ do not change. Build them all again with:  python3 tools/build_struct.py

  1_tailcall/NAVFULL.txt   XEQ x + RTN -> GTO x (65 calls; not in NAV / N83 or towards them: LocR)
  2_order/NAVFULL.txt      + the programs reordered: most numbered jumps per label first
  3_callpos/NAVFULL.txt    + inside 14 programs, the blocks with the most calls (and named entries) per step first;
                           a block starts at a label after a RTN / GTO no test can skip, so it is entered only
                           through its labels; the entry block stays first, a block that runs into END stays last
  4_inline/NAVFULL.txt     + 27 calls (run 20 times or more on the counted pages) to routines of 1-6 steps replaced
                           by the steps; no call after a test unless the routine is one step

  5_equator/NAVFULL.txt    + the celestial equator with one dot in three, each dot one POINT (3 x 3 pixels around the
                           old 2 x 2 dot of four PIXEL): every 6 deg on SKY and ANIM (60 dots, were 180), every 9 deg
                           on SPLIT and ALLSKY (40, were 120); CEQQ computes them in blocks of 20 (was 30). The charts
                           look different (the dots lie on the old curve): Free42 and the Python versions not yet.
  6_anim/NAVFULL.txt       + ANIM's frames without the 1 s wait: PAUSE 10 -> PAUSE 0 (24 frames: 24 s less; each
                           frame still reaches the LCD). The PAUSE 0 of the SINKING box and of the bar after a key
                           stay: the C47 shows the screen only at a PAUSE or a key wait. Same pages as 5_equator.

Load one on the calculator like the release (NAVFULL.p47, then NAVINIT). Bytes: steps 1-3 24160 (as the release),
4_inline 24375, 5_equator and 6_anim 24290.

What the firmware does (c43 master ef39ddb, read 2026-10-07)
  GTO nn / XEQ nn   fnGoto scans labelList from the first program in memory to the label: cost = labels of the
                    earlier programs + labels before it in its own program. No step walk; distance does not matter.
  XEQ "NAME"        findNamedLabel compares the names of the global labels in labelList, then goToGlobalStep walks
                    the steps from the start of the program to the label (and defineFirstDisplayedStep walks again).
  RTN               fnReturn -> defineCurrentStep walks from the start of the caller's program to the return step:
                    cost = position of the XEQ in its program.
  RCL / STO "NAME"  reserved names (hash), then the last 3 names found (cache), then a scan of all named variables.

Where the time goes (perf, firmware PC sim, release NAVFULL, share of the program's CPU)
              RTN walk   named-call walk   label scan   name lookup
  ALMANAC       2.3 %         1.0 %           1.9 %         1.0 %
  SKY           3.6 %         2.2 %           3.3 %         0.8 %
  ANIM          3.0 %         1.3 %           3.2 %         1.9 %
  ALLSKY        3.0 %         1.3 %           2.9 %         1.2 %
So the structure can gain 6-10 % at most; the rest is the calculation (trigonometry first).

Measured, firmware PC sim (CPU user+sys, NAVINIT_FULL state, best of 3; menu only = sim start + state load)
  page                 release   1_tailcall   2_order   3_callpos   4_inline
  menu only            0.244 s     0.242       0.237      0.234       0.236
  ALMANAC + 15 hours   1.601       1.603       1.594      1.570       1.574
  SPLIT                0.284       0.284       0.284      0.276       0.281
  SKY                  0.299       0.295       0.297      0.288       0.292
  ANIM                 0.391       0.394       0.395      0.390       0.383
  ALLSKY               0.337       0.331       0.334      0.323       0.322
The wall-clock noise (+-0.02 s between runs) is as large as the gain; perf counts it better (share of the
program's CPU spent on the structure, 8000 samples/s, NAVINIT_FAST):
                 release: RTN walk  named walk  label scan  names  all  |  4_inline: same          samples
  ALMANAC +15 h            3.4 %      1.1 %       2.9 %    1.3 %  7.6 % |  2.0 0.6 2.0 1.4  5.5 %   9999 -> 9781
  SKY                      3.8        2.7         4.5      1.6    9.9   |  2.5 0.5 1.4 1.3  5.1     1832 -> 1767
  ANIM                     3.1        0.8         2.6      1.4    7.1   |  1.5 0.4 1.4 1.6  4.5     2544 -> 2498
  ALLSKY                   2.7        2.2         4.1      1.6    8.5   |  1.5 0.4 1.5 1.4  4.5     2110 -> 2048
So the four steps take 2-3.5 % off the program's CPU, about half of what the structure costs; the other half is
in the calls that remain. Every page of every step is pixel for pixel the release (NAVINIT_FAST and NAVINIT_FULL;
1 ALMANAC with the arrows, 2 SPLIT, 3 SKY, 4 ANIM, 5 ALLSKY, 6 INFO).
The real calculator may weigh the walks differently from the PC: time it there before a release.

Step 5. Estimated C47 time of the first view of a page (Python simulator counts, steps * 0.17 ms +
trig values * 5.8 ms, the TVEC figures; POINT counted as PIXEL), and the firmware PC sim's CPU of the page
(menu-only run subtracted):
  page      estimate 4_inline -> 5_equator     firmware sim CPU 4_inline -> 5_equator
  SKY       4.6 s -> 2.5 s  (-46 %)             0.053 -> 0.021 s  (-57 %)
  SPLIT     4.1 s -> 2.7 s  (-34 %)             0.041 -> 0.029 s  (-29 %)
  ANIM     14.1 s -> 10.8 s (-23 %)             0.152 -> 0.126 s  (-17 %)   (6_anim: + 24 s less of frame waits)
  ALLSKY    8.5 s -> 7.0 s  (-18 %)             0.081 -> 0.074 s  (-15 %)
ALMANAC, INFO, the menu and the hour arrows have no equator: unchanged (pixel for pixel the release).
The menu (the whole sky, about 12.4 s) and each hour arrow (about 8.7 s, SER alone 3 s) are now the long waits.

Not done yet
  - Free42 and the Python versions (c47sim needs POINT) of 5_equator, if it is kept.
  - NAVLITTLE (DM42) and MOON47: the same passes, once a step has shown it pays.
  - Names: worth it only in loops with many named RCL/STO and little calculation.
