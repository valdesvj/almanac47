Structural optimizations of the C47 NAVFULL (branch struct-opt, Oct 2026)

One folder per step; each step is applied on top of the one before it. The release build/NAVFULL.txt and
programs/ do not change. Build them all again with:  python3 tools/build_struct.py

  1_tailcall/NAVFULL.txt   XEQ x + RTN -> GTO x (65 calls; not in NAV / N83 or towards them: LocR)
  2_order/NAVFULL.txt      1_tailcall with the programs reordered: most numbered jumps per label first

Load one on the calculator like the release (NAVFULL.p47, then NAVINIT). Same size as the release (24160 bytes).

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

Measured (firmware PC sim, NAVINIT_FULL state, CPU user+sys, best of 3, the menu-only run subtracted)
  page                 release   1_tailcall   2_order
  ALMANAC + 15 hours   1.384 s     1.373       1.361    (-1.7 %)
  SPLIT                0.050       0.056       0.050
  SKY                  0.066       0.065       0.060
  ANIM                 0.180       0.162       0.155
  ALLSKY               0.108       0.098       0.100
Noise about +-0.005 s: only the ALMANAC row is firm. Every page of both steps is pixel for pixel the release
(NAVINIT_FAST and NAVINIT_FULL; 1 ALMANAC with the arrows, 2 SPLIT, 3 SKY, 4 ANIM, 5 ALLSKY, 6 INFO).
The real calculator may weigh the walks differently from the PC: time it there before a release.

Not done yet
  - Moving the hot XEQ steps near the top of their programs (the RTN walk, the largest part).
  - Inlining tiny routines called in loops.
  - NAVLITTLE (DM42) and MOON47: the same passes, once a step has shown it pays.
  - Names: worth it only in loops with many named RCL/STO and little calculation.
