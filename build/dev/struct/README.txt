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
                           on SPLIT and ALLSKY (40, were 120); CEQQ computes them in blocks of 10 (was 30). The charts
                           look different (the dots lie on the old curve): Free42 and the Python versions not yet.
  6_anim/NAVFULL.txt       + ANIM's frames without the 1 s wait: PAUSE 10 -> PAUSE 0 (24 frames: 24 s less; each
                           frame still reaches the LCD). The PAUSE 0 of the SINKING box and of the bar after a key
                           stay: the C47 shows the screen only at a PAUSE or a key wait. Same pages as 5_equator.
  7_animq/NAVFULL.txt      + ANIM's quick Sun (SUNF) and Moon (MOOQ) only at frames 0, 12 and 23 (a 3 x 4 matrix);
                           each other frame is one product (Lagrange weights 1 x 3) x (3 x 4), GHA without the
                           Earth's turn (w = 360.98564736629 deg/day) and Dec. Error against every frame computed:
                           Sun 0.000000 deg, Moon 0.0007 deg (a pixel is about 1 deg). ANIM pixel for pixel 6_anim
                           (first run, +1 h, -2 h: the last screen keeps every frame's symbols).
  8_mstars/                + the 58 stars at once with matrices (TSTAR's part B) in place of one by one: CALC, right
                           after the Sun, computes GHA Dec Hc Zn of every star (two products (58 x 4) x (4 x 3), ∡ of
                           complex columns) into ALMC's star rows with M.PUTM; CSQK compares the exact Hc with SQK's
                           limit (8.99974 deg). NEEDS ITS OWN NAVINIT_FULL / NAVINIT_FAST (this folder): LBL 05 makes
                           SXA (star vectors J2000) and SXD (per century) from ST, once (+428 bytes). Pages pixel for
                           pixel 7_animq: 6 dates and places 2004-2045, 55 S - 60 N, FULL; and FAST.
  9_allsky/NAVFULL.txt     + ALLSKY reads its 58 stars from the cache (CSTR GHA / Dec, CHCZ Hc / Zn: step 8's exact
                           values) in place of its own quick ones (catalogue + linear precession + the full HCZ,
                           about 9 trig values a star). Uses step 8's NAVINIT. ALLSKY calls CSUN first, so the cache
                           is the hour shown (arrows checked: the same hour gives the same screen). Stars move by at
                           most a pixel (38-163 pixels of a screen, 4 places); every other page as 8_mstars.
  10_selfinit/NAVFULL.txt  + NAV makes the star vectors SXA SXD itself the first time it runs (from NAVINIT's catalogue
                           ST, the code of step 8's NAVINIT) and keeps them, like the cache ALMC: the RELEASE NAVINIT
                           stays. The test: 0 STO+ "SXK" (STO+ makes a missing variable with 0; RCL would stop NAV);
                           SXK = 0: make them, SXK = 1. Pages pixel for pixel 9_allsky (4 places, every page). First
                           run: about 2 s more on the C47 (estimate; sim 0.193 -> 0.243 s), later runs as step 9.
                           To make them again (another NAVINIT catalogue): DELITM "SXK".
  11_hybrid/NAVFULL.txt    + the stars: at each new time only the matrices (the 4 x 3 matrix, about 9 trig values, and
                           the two products, kept as SXE and SXH), the star rows marked "not computed" as in the
                           release; "over the horizon?" from SXH's zenith component (sin Hc, no trig); the angles
                           (4 →POL) only for the stars a page asks for; ALLSKY fills all 58 at once (∡ on columns).
                           Release NAVINIT. Pages pixel for pixel 10_selfinit (4 places + FAST/TBL, hour arrows on
                           ALMANAC, SKY, ALLSKY). Cache after an hour arrow on ALMANAC: 6 stars computed, 13 marked
                           below, 39 not asked (step 10: all 58 every time).
  12_labels/NAVFULL.txt    + numbered labels inside a program, names only between programs: the 9 XEQ / GTO "name" towards
                           a global label of the same program (N17-N20, N28, N76, N99) -> XEQ / GTO nn, the number right
                           after the global label (7 labels); the 2 routines nothing calls (N64's LBL 94 since step 11,
                           N24's LBL 97 since step 4, 14 steps) removed; the 33 RTN just before END removed (END returns
                           like RTN: both fnReturn). Pages pixel for pixel 11_hybrid (4 places + FAST/TBL, hour arrows);
                           CPU the same within the noise (sim +-0.01 s a page).
  13_renumber/NAVFULL.txt  + inside every program the numbered labels in the order they appear: 01, 02, 03 ... In the
                           11 programs with XEQ / GTO IND the 228 labels those reach keep their numbers: the number is
                           the data (star 1-58, character codes, digit + 48, body + 70 / 81 / 90 with NAV's constants
                           R71 = 90 ...); the other labels skip them. Only easier to read: XEQ / GTO nn cost the labels
                           before it in the table, not its number. Same bytes; pages pixel for pixel 12_labels.
                           (The test harness found NAV's input routine as XEQ 20: now by its "DATE YYYY.MMDD" prompt.)
  14_clean/NAVFULL.txt     + the program N22 / N23 (STR2, SQK: no call left since step 11, 160 steps) and N24's entry
                           (LBL "N24" XEQ "N15": the callers use N25) removed; the names N20 N76 N99 removed (their
                           numbered label stays, step 12). 70 global labels (were 76) in the XEQ menu; labels 01, 02 ...
                           again. Pages pixel for pixel 13_renumber.
  15_noregs/NAVFULL.txt    + NAV keeps none of your registers: no LocR 99 and no copies at the start and the end (397 steps);
                           CLREGS and CLSTK when NAV ends (as v2.2.0). Pages pixel for pixel 14_clean; checked: R00 R98
                           and the stack are 0 after key 0 (step 14 gave them back).
  16_group/NAVFULL.txt     + a TEST: the programs that only one program calls go into it (labels 00, 01 ... of the group,
                           the IND tables keep their numbers, at most 100): NAV + ANIM ALLSKY, CSUN (N64) + RISE.. PLN2
                           PHA2 MSTAR, OUT8 + SBRT, OUT4 + OUT1-3. 24 programs (were 34), 55 global labels (were 70).
                           Pages pixel for pixel 15_noregs. SLOWER: page CPU minus the menu (sim, best of 3), 15 -> 16:
                           ALMANAC+15 h 1.193 -> 1.226 s, ANIM 0.075 -> 0.083, ALLSKY 0.052 -> 0.068; NAV + views alone:
                           ANIM +12 %, ALLSKY +30 %; the CSUN group alone: ALMANAC +2 %. Every RTN walks from the
                           start of the bigger program (fnReturn -> defineCurrentStep).
  17_topbar/NAVFULL.txt    15_noregs (not 16) + the top bar as  08-10-2026 12:30 UT DR   N 40 24.0   W 3 42.0 : DR,
                           latitude and longitude one text (x→α / αIP in HDR's R.04) and one ATEXT at column 143, the
                           letter right before its degrees, no padding, three spaces between the groups. And the sky
                           cache ALMC kept between runs of NAV: made only when it is missing or not 73 x 4 (0 STO+
                           "ALMC" creates it, MATR? 42DIM#); its key (JD, lat, lon) decides. Firmware sim: NAV twice
                           with the same inputs -> the sky computed once (15: twice), the second ALMANAC page pixel for
                           pixel the first; a new time or a new place computes again. Pages = 15 except the top bar.
  18_hourglass/NAVFULL.txt + the firmware's hourglass (U+231B, standard font, one ATEXT) in the top bar at column 370,
                           left of T / S / X, together with the SINKING box (NAV LBL 13, 4 steps): on the menu or the
                           old view while the box is there; it goes with the box (the new view or the menu clears the
                           screen). Firmware sim: the finished pages = 17_topbar.
  19_struct/NAVFULL.txt    + the C47 STRUCT commands (IF ELSE ENDIF, DO WHILE ENDDO, REPEAT UNTIL; c43 structured.c,
                           docs/appnotes/sources/AN0007_STRUCT) in place of the GTO decisions and loops. C47 / R47 only
                           (Free42 has no STRUCT; the old-hardware DM42 build of the firmware allows 10 structures of a
                           kind per program, so not NAVLITTLE either). NAV's main part by hand: the menu's key loop is
                           one DO ... ENDDO with the end key tested before its WHILE, the keys decoded by arithmetic
                           (arrows (56 - key) / 5 = +1 / -1; a view when |column - 3| <= 1 and |row - 6.5| = 0.5, view
                           (7 - row) * 3 + column - 1, its box at column 202 - 28 * view), a view and its hour arrows one
                           more DO ... ENDDO: no GTO left in NAV. The other programs by the rules of tools/c47struct.py
                           (each result checked as VALID checks it, no structure entered from outside): if, if-else,
                           loop (REPEAT ... T' UNTIL, or DO ... T WHILE ENDDO when T has no opposite: ISG DSE KEY?),
                           while, break (a second WHILE in a DO: the firmware takes it, fnWhile goes past the nearest
                           ENDDO of its number), all-of (T1 GTO x ... T2 GTO x ... RTN -> nested IF, x after the ENDIFs),
                           dup (a shared tail of at most 5 steps copied in place of the GTO), thread, dead steps.
                           GTO nn for decisions and loops 196 -> 38, tail calls (a GTO no test skips, to a routine that
                           ends with RTN) 58 -> 23; numbered labels 553 -> 424; 263 structure steps (68 IF, 13 ELSE, 32
                           DO, 38 WHILE, 6 REPEAT); 8318 -> 8337 steps (the tails copied). The partner numbers are written
                           into the file ("IF 01", rejig with the STRUCT patch): the C47 checks only the last program of a
                           file as it loads. Key wait: DO / PAUSE 50 / KEY? r / WHILE / ENDDO.
                           Python sim (tests/test_struct.py): every page, the hour arrows and the menu's keys pixel for
                           pixel 18_hourglass, the stack clear at the end. Left: PTXS 9, HORZ 7, CSUN 4, PHA2 4, HALMH 3,
                           and 1-2 in ALMF, PLN2, TGET, WPLS, HANIM, ALLSKY, RISE: jumps into a block another way reaches
                           too, loops with two ways back.
  20_layout/NAVFULL.txt    + the same steps in another order, for the searches the firmware makes: each program's blocks
                           (a block starts at a label after a step that always leaves, at structure depth 0) and the
                           programs ordered by what the pages run (build_struct.profile: the Python sim on the six pages
                           with the hour arrows and the menu's arrows). A block or program costs every search that passes
                           over it: its labels for each GTO / XEQ nn landing later (fnGoto scans the labels from the first
                           program), its structure steps for each STRUCT jump later (structFindPartner; ENDDO / UNTIL scan
                           twice), its global labels for each named call later, its steps for each return to and named
                           call into a later place of the same program (fnReturn and goToGlobalStep walk from the
                           program's start; a named call twice). Adjacent blocks / programs swap while the total falls.
                           NAV stays first and starts with LBL "NAV"; every program starts with one of its global labels
                           (the cheapest); labels 01, 02 ... and the structure numbers again in the new order.
                           Model of that search work on the profiled pages (labels + structure steps + walks):
                             18_hourglass 8.12 M, 19_struct 7.82 M, 20_layout 5.64 M (-31 % against 18).
                           Steps run 409919 -> 430059 (+4.9 %: mostly the WHILE after each loop test, which the firmware
                           runs with its test as one action); jumps: GTO 26667 -> 3192, ENDDO 17997, UNTIL 1052 back.
                           Pages pixel for pixel 18_hourglass (tests/test_struct.py).
  21_pixel/NAVFULL.txt     + the horizontal line routine N57 (PHLS) in PIXEL line mode for every line: one PIXEL with
                           Y < 0 draws the whole row (fnPixel), then the columns outside the line are switched off (AGRAPH
                           in GRMOD 2, one column a step) in place of one AGRAPH for each column of the line. The horizon
                           of SKY and SPLIT (376 columns from column 20): 376 -> 24 AGRAPH, about 1400 steps less a view
                           (SKY 29709 -> 28325, SPLIT 31553 -> 30169, sim, first view). The full rows (top bar, ALMANAC's
                           table rule, the menu, the horizon of ANIM and ALLSKY) were PIXEL lines already; the altitude
                           axes are dotted (a PIXEL every 3 rows): no line mode for them. Pages pixel for pixel.
  22_calls/NAVFULL.txt     + fewer calls and labels: a text that starts with a digit is CLα r + αIP r (was 48 + STO r +
                           XEQ IND r into the table LBL 48 "0" RTN ... LBL 57 "9" RTN: a label search and a return each
                           digit; the table goes); calls to plain routines replaced by their steps (c47struct.inline: a
                           routine with one caller, of 2 steps, or of up to 6 steps called 10 times or more on the
                           profiled pages; no call after a test unless the routine is one step): 52 calls, 28 routines
                           gone. Numbered labels 424 -> 386 (553 in 18_hourglass).
  23_box/NAVFULL.txt       + the SINKING box (drawn at each view and each hour arrow) with one AGRAPH a column in GRMOD 1
                           at WSIZE 30 (fnAGraph writes the pattern, 0 bits white): it was a clear of 180 columns in
                           GRMOD 2 and then the frame in GRMOD 0: 360 -> 180 AGRAPH a box. Checked pixel for pixel on a
                           random screen (tests/test_struct.py), R03 R04 R07 and GRMOD left as before.
  24_layout/NAVFULL.txt    + 20_layout's ordering again on the new steps.
                           Python sim, the six pages with an hour arrow each, after a first run (the star vectors and the
                           sky cache made): steps run 18_hourglass 199769, 21_pixel 208561, 24_layout 186261 (-6.8 %
                           against 18); search work (labels + structure steps + walks, all pages and arrows) 8.12 M ->
                           4.52 M (-44 %). Trig values unchanged (2876): the calculations already use the matrix
                           commands where they pay (stars 8-11, the equator CEQQ, ANIM's Sun and Moon 7).
  25_hcz/NAVFULL.txt       + HCZ (N32) with 4 trigonometric functions (was 6): the turn by the latitude with cos B / sin B
                           that HCZI (N36) keeps in V6 / W1 for every view (NAV calls it before the menu's sky). ANIM
                           computes it for the Sun and the Moon at every frame.
  26_anim/NAVFULL.txt      + ANIM's celestial equator from the charts' cache (CEQQ / CEQR, the 60 dots of SKY, kept for
                           the place) in place of HCZQ / HCZR (2 trigonometric functions a dot); HCZQ, HCZR gone.
  27_header/NAVFULL.txt    + HDR builds its 'DR   N 25 20.0   E 55 12.0' text once a run and keeps it in HT (NAV stores a
                           number there as it starts, STRI? tells HDR to build it, NAV deletes HT as it ends): about 95
                           steps less each top bar (every view, every ANIM frame).
  28_text/NAVFULL.txt      + PTXS (N50) written in place at its 56 calls whose row, column and text are one step each: the
                           text, the row less 4, the column, ATEXT Z, the row given back (no named call, no return).
  29_unroll/NAVFULL.txt    + the SINKING box's frame (176 columns) 8 AGRAPH a round, the menu's highlight bar (170) 10 a
                           round: one DSE / WHILE / ENDDO for 8 or 10 columns.
                           Sim, six pages + an hour arrow after a first run: steps 18_hourglass 199769, 24_layout 186265,
                           29_unroll 162636 (-18.6 % against 18); trig values 2876 -> 2527; ANIM alone 31032 -> 24535 steps.
                           Search work 8.12 M (18) -> 3.98 M. tests/test_struct.py: every step from 20 on built again,
                           the box and the bar pixel for pixel on a random screen, and 8 random dates and places (pages
                           1-5, FULL and FAST) pixel for pixel 18_hourglass.
                           FIXED in 19_struct (so in every step after it): a 'break' rule moved a block between a loop's
                           ENDDO and the code after it, so the loop's normal end ran that block too: on ALMANAC the
                           planets' loop drew a line it should not (when no planet was above the horizon at its end).
                           Found with random dates; the three fixed places of the tests had not shown it.
  30_named/NAVFULL.txt     + calls by name written in place (c47struct-like plain code that can move to another program,
                           at most 10 steps or one caller): N92 (azimuth to column, 660 calls a run of the pages), N36,
                           N67, N66, N70, N26, N97, N93, N91, N86, N87, N88, N94 gone as names. 31_layout: the order again.
  32_format/NAVFULL.txt    + an unpadded integer is CLα + αIP (αIP appends the whole integer part; the routine took 1-3
                           digits one by one: 31 -> 4 steps), the year of a date one αIP.
  33_dots, 34_dots         + the celestial equator of ANIM, ALLSKY, SKY and SPLIT on whole columns: CEQQ's cached
                           [Hc, sin Hc, Zn] taken a column at a time (M.GETM), the screen column and row of every dot at
                           once (+, MOD, ×, ÷, IP element by element; c47sim: IP on a matrix), side by side in QP, then
                           RCLSEQ RCLSEQ POINT a dot (SKY, SPLIT: RCLSEQ Hc, X<Y? 1E-4, else J+ J+). Was a call by name
                           to CEQR and one to the view's routine a dot. The routines left without a caller go
                           (c47struct.prune). 35_layout: the order again.
  36_menu/NAVFULL.txt      + the menu no longer runs CSQK over the 58 stars (its answer was dropped: it only filled the
                           stars' rows of the cache ahead of the pages, which ask CSQK for their own stars). 37_layout.
                           Sim, warm, one view each (no arrow), steps 18_hourglass -> 37_layout: ALMANAC 13800 -> 9036,
                           SPLIT 17738 -> 10372, SKY 15626 -> 7742, ANIM 31032 -> 19407, ALLSKY 23650 -> 15557; six
                           pages + an hour arrow each: 199769 -> 131253 (-34 %); trig values 2876 -> 2587 (the pages now
                           compute their own stars: +20 on ALMANAC, SPLIT, SKY; the menu none). Search work 8.12 M ->
                           2.91 M. 8865 steps in the file (8318 in 18: the routines written in place).

Load one on the calculator like the release (NAVFULL.p47, then NAVINIT). Bytes: steps 1-3 24160 (as the release),
4_inline 24375, 5_equator and 6_anim 24290, 7_animq 24912, 8_mstars 26316, 9_allsky 26246, 10_selfinit 26702, 11_hybrid 26961,
12_labels and 13_renumber 26866, 14_clean 26484, 15_noregs 25691, 16_group 25569, 17_topbar 25907, 18_hourglass 25926;
19_struct to 37_layout: rejig with the STRUCT patch (rejig_C47_items_2920-2939, AN0007) was not at hand when they
were made.

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

Step 7. ANIM: estimate 10.8 s -> 7.9 s (-27 %; SUNF + MOOQ 3.8 s -> 0.5 s); firmware sim CPU of the page
0.106 -> 0.072 s (-32 %). The other pages: unchanged.

The stars (tools/tests_calc/TSTAR.txt): one matrix for all 58 against one by one, to time on the calculator
before NAV changes; firmware PC sim 12 against 51 ticks.

Step 8. Firmware PC sim CPU (with start-up), 7_animq -> 8_mstars: menu FULL 0.236 -> 0.197 s, FAST 0.210 -> 0.173 s;
ALMANAC + 15 hours FULL 1.563 -> 1.484 s, FAST 1.246 -> 1.145 s. Trig on the C47 (counted): menu about 615 -> 241,
but an hour arrow about 171 -> 241 (7 computes only the stars the table asks for; 8 always all 58): time the
arrows on the calculator. If they are slower: the over-the-horizon test from the zenith component (no trig) and
the angles only for the stars a view asks for.

Step 9. ALLSKY + 4 hour arrows, firmware sim CPU of the views 0.614 -> 0.445 s (-28 %); on the C47 about 460
trig values less per ALLSKY view (estimate 7.0 -> about 4.5 s).

Variable names: the matrix code's temporary variables start with Y. They started with T until 2026-10-07: with
the almanac tables loaded, "TSA" (the Saturn table) was overwritten and deleted (steps 8-10 stopped before the
menu). Steps 8-10 and TSTAR fixed; checked with NAVINIT_FAST + TBL (the tables intact, pages as 7_animq).

Step 11. Firmware sim CPU of the page (vectors kept), release / 7 / 10 / 11: ALMANAC + 15 hour arrows 1.364 /
1.325 / 1.256 / 1.178 s; SKY + 5 arrows 0.641 / 0.461 / 0.436 / 0.416 s; ALLSKY + 4 arrows (11 with N99) 0.622 (10)
/ 0.649 (11) s, total with start-up. Stars per hour arrow on ALMANAC on the C47 (counted): 7 about 300 trig values,
10 about 241, 11 about 33.

Not done yet
  - Free42 and the Python versions of 5_equator, if it is kept (c47sim runs POINT since 19_struct).
  - NAVLITTLE (DM42) and MOON47: the same passes, once a step has shown it pays.
  - 19_struct / 20_layout: the 38 GTO left (by hand), the timing on the C47 (the model weighs a label, a structure step
    and a walked step alike; the firmware may not), tests/test_fw.py in the firmware (it knows the STRUCT key wait).
  - Names: worth it only in loops with many named RCL/STO and little calculation.
