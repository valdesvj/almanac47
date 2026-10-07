C47 CELESTIAL NAVIGATION PACKAGE
================================
Sun, Aries, 57 navigation stars + Polaris, sunrise/sunset/twilight.
Apparent geocentric positions, almanac accuracy (better than 0.1').
Time argument: UT1. For a sight timed in UTC, add DUT1 (< 0.9 s).

FILES
-----
programs/   plain UTF-8, one command per line (HP-42S / Free42 names)
  SUNA.txt     Sun + Aries.            Y: -   X: JD(UT1)
               -> X = GHA Sun, Y = Dec Sun, Z = GHA Aries
  MATA.txt     builds matrices VL, VB, VR, NU for SUNA (run once)
  STAR.txt     stars.                  Y: JD(UT1)   X: star number 1-58
               -> X = GHA star, Y = Dec, Z = SHA        (calls SUNA)
  MATST.txt    builds star catalogue matrix ST (run once)
  SUNRISE.txt  Z: JD at 0h UT   Y: latitude (N+)   X: longitude (E+, W-)
               XEQ RISE / SET        sunrise / sunset (upper limb, -0 50')
               XEQ CTWA / CTWP       civil twilight am / pm (-6 deg)
               XEQ NTWA / NTWP       nautical twilight am / pm (-12 deg)
               XEQ TRAN              meridian passage
               -> X = UT in decimal hours (99 = no event)   (calls SUNA)
  PHAS.txt     Moon phase.             X: JD(UT1)
               -> X = % illuminated, Y = age in days since new moon (calls SUNA)
  HORZ.txt     sky chart.  Z: JD(UT1)  Y: lat (N+)  X: lon (E+)
               Zn axis across (N E S W N), Hc axis up (30 60 90), celestial
               equator dotted, Sun and all stars above the horizon with numbers.
               South latitude: chart centred on N (S W N E S) so the equator arch is whole.
               After drawing, a pixel-text line at the top shows one object at a time
               ("SUN ZN 118.3 HC 39.1", "18 ZN 124.0 HC 19.7"), PAUSE 30 each, then
               the next (top strip cleared with CLLCDxy). No AVIEW/PROMPT: they leave
               graphics mode on the C47. Needs SUNA + STAR (entry STR2) + CHZ + PTXT + PTXB.
               Text with PTXT (AGRAPH font), star/sun symbols with PTXB; 400x240 screen.
  HORZS.txt    same chart as HORZ without the object list: draws, holds the chart
               about 30 s (3 x PAUSE 99), then ends.
               Same inputs (Z JD, Y lat, X lon); needs SUNA + STAR (STR2) + CHZ + PTXT + PTXB.
  HPLT.txt     dot plot with the C47's own statistics plot (PLSTAT).
               Z: JD(UT1)  Y: lat  X: lon. CLΣ, then Σ+ with x = Zn, y = Hc for the Sun
               and every star above the horizon, then PLSTAT and PLTFCNS to view.
               Needs SUNA + STAR (STR2) + CHZ. Overwrites the statistics data.
  CHZ.txt      sight-reduction formulas (global labels, one program):
               XEQ CHZ  T: lat  Z: lon  Y: Dec  X: GHA  -> X = Hc, Y = Zn
               XEQ HCZ  same, lat in R91, lon in R92 (subroutine used by HORZ,
                        HORZS, HPLT)                       -> X = Hc, Y = Zn
               XEQ DHA  inverse. T: lat  Z: lon  Y: Hc  X: Zn
                        -> X = Dec, Y = LHA, Z = GHA  (SHA = GHA - GHA Aries)
               Registers R91-R92 (lat, lon), R94 Dec, R95 LHA, R96 Hc, R97 Zn.
  PTXT.txt     draw text with AGRAPH columns, small 3x5 font. Also PTNS (integer),
               PT1 (one decimal), same stack Z = y, Y = x, X = value.  Z: y  Y: x  X: "STRING"
               (bottom-left of text, C47 origin bottom-left) -> Y = y, X = next x.
               0-9 A-Z space + - . / :   * = star symbol, @ = sun symbol.
               Native C47 string commands (alpha-LENG, alpha->x). Registers R30-R33.
  PTXB.txt     same with big 5x7 font (also %). Extra entries, same stack:
               PHL horizontal line (Z = y, Y = x, X = length),
               PINB whole number, PDM deg+min, PZN ddd.d, PHM hh:mm,
               PF1 one decimal, PDAT (X = JD -> DD-MM-YYYY). Registers R30-R36.
  PTDEMO / PTBDEMO / PTFULL   demo screens (small font, big font, full page).
  SNMU.txt     X: star number -> X = name in capitals (no display; used by screens)
  SNAM.txt     X: star number -> name string stored in R38 and shown with AVIEW 38
  ALM.txt      Method B: Chebyshev tables (see PDF), optional
rtf/        SUNA, MATA, ALM in RTF (numbered lines)
docs/
  C47_GHA_Dec_Almanac.pdf   theory, formulas, check values, Chebyshev tables
  C47_almanac_coefficients_2026-2027.xlsx   Chebyshev coefficients
  STAR_list.txt             star numbers with SHA/Dec for 23 Sep 2026
  (generator moved to tools/almanac/)

SETUP ORDER
-----------
1. Load: SUNA MATA STAR MATST CHZ SUNRISE PHAS SNMU PTXB PTXT
         then the screens HORZ HORZS HPLT HALM HALMV ALMF (and SUNSD, SNAM).
2. XEQ MATA   (creates VL, VB, VR, NU)
3. XEQ MATST  (creates ST)
4. MATA and MATST may be deleted afterwards. Never delete the matrices.
5. Save the whole state (I/O menu, SAVEST) so one LOADST restores everything.
convert_all.sh (in programs/) converts every .txt to .p47 with your converter.

MAIN SCREENS   (all: Z = JD(UT1)  Y = lat N+  X = lon E+)
  HALMV  chart left, data right: date/UT, DR, Aries, Sun GHA/Dec/SD,
         Sun + 9 stars Hc/Zn, twilight, rise/set, mer pass, Moon
  ALMF   full-page almanac: Sun + 9 stars GHA, Dec, Hc, Zn + times + Moon
  HALM   chart top, table bottom

CHECK VALUES (23 Sep 2026, 12:00 UT, JD 2461307)
------------------------------------------------
2461307 XEQ SUNA           GHA Sun 1.9069849 (1 54.42')
                           Dec    -0.1931700 (S 0 11.59')
                           Aries 182.3525029 (182 21.15')
2461307 ENTER 18 XEQ STAR  Sirius GHA 80.7700 (80 46.2')
                           Dec -16.7490 (S 16 44.9')  SHA 258 25.0'
2461306.5 ENTER 10 ENTER 0 XEQ RISE  -> 5.8191 h (5:49:09 UT)
2461307 XEQ PHAS          -> 89.1 % illuminated, age 12.36 d

REGISTERS USED
--------------
SUNA 50-55, 60-67, 70-81   STAR 56-59, 68-69, 82-89
SUNRISE 90-99 (HORZ also 90-99)   PHAS 30-33 51 53 56 57 (scratch)   SNAM 49   ALM 01-09, 10-33, 40-41

NOTES
-----
- Coefficients never need updating; SUNA accuracy tested 2000-2050
  (GHA <= 0.016', Dec <= 0.007'). Stars <= 0.003' (Polaris 0.04' in SHA).
- SUNA contains dT = 69.2 s (line 4); effect on the Sun is negligible.
- Chebyshev tables (ALM / PDF / xlsx) cover 1 Sep 2026 - 31 Dec 2027 only.
- The C47 does not treat ->DEG or flag 77 like the HP-42S; SUNA avoids both.

PYTHON / NUMWORKS VERSION (python/)
----------------------------------
nav.py + navdata.py: same methods and data as SUNA, STAR, SUNRISE, PHAS.
Computer: put both files in one folder, run  python nav.py
NumWorks: copy both scripts to the calculator (my.numworks.com workshop),
open nav.py; if the menu does not start, type  menu()  in the shell.
The menu asks year, month, day and UT (hh:mm:ss) and computes the JD itself.
Option 5 prints the ALMANAC page (Sun + brightest stars: GHA Dec Hc Zn, twilight,
rise/set, mer pass, SD, Moon phase). Lat/Lon: 25 20 = 25 deg 20', or decimal.
Functions: jd(y,m,d,h)  sun(jd)  star(jd,n)  event(jd0,lat,lon,kind)  phase(jd)
           hcz(lat,lon,dec,gha)  bodies(jd,lat,lon)  almanac(jd,lat,lon)  page(...)
HP Prime graphic views (ALMANAC page, horizon chart): python/hpprime/README.md

PIXEL TEXT AND HALF-SCREEN SIGHT PLANNER
---------------------------------------
PTXT  small 3x5 font    PTXB  big 5x7 font  (Z=y  Y=x  X="STRING")
      both return Y=y X=next x. * draws a star, @ draws the sun.
PTXB also has  PINB (whole number)  PDM (deg min.m)  PZN (ddd.d)
      same stack: Z=y Y=x X=number.  Registers 30-36.
SNMU  X=star number -> X=name in capitals (no display).
PTFULL / PTBDEMO / PTDEMO  demo screens.

HALM  half screen horizon + half screen almanac
      Z=JD  Y=lat (N+)  X=lon (E+)   XEQ "HALM"
      Needs SUNA, MATA matrices, STAR, MATST matrix, CHZ, SNMU, PTXB.
      Top: Hc/Zn chart, dotted celestial equator, sun and stars.
      Bottom: sun + up to 9 stars, Hc 15-75 deg, one per 40 deg of Zn.
      Registers 20-28, 37, 40-47 (+ those of SUNA, STAR, CHZ, PTXB).

HALMV  vertical split: chart left, data right
      Z=JD  Y=lat (N+)  X=lon (E+)   XEQ "HALMV"
      Right side: DR, UT, GHA Aries, Sun GHA/Dec, Sun + 9 stars Hc/Zn,
      sunrise, sunset, nautical twilight AM/PM, meridian passage, Moon.
      Needs the HALM programs plus SUNRISE and PHAS.
      Registers 10-28, 37, 40-48 (+ those of the called programs).
      PTXB extra: PHM (hh:mm, 99 -> --:--), PF1 (one decimal),
      PDAT (X=JD -> DD-MM-YYYY).

ALMF  full-screen almanac page (no chart)
      Z=JD  Y=lat (N+)  X=lon (E+)   XEQ "ALMF"
      DR, UT, GHA Aries; Sun + 9 stars with GHA, Dec, Hc, Zn;
      twilight, rise/set, mer pass, Moon. Same programs/registers as HALMV.

SUNSD  X=JD -> X = Sun semi-diameter in arc minutes (959.63"/R, R from SUNA R73).
       ALMF and HALMV also show SUN SD (register R29).

extras/  DM42/Free42 graphics tests (AGDEMO_DM42, AGTEST_DM42 - do NOT use the
         C47 converter on these) and AGTEST_C47 (PIXEL test).

NAV   start program with prompts (does not change any other program)
      XEQ "NAV" -> graphic menu (1 ALMANAC ... 9 ALLSKY, 0 END): press the number key; + goes back to the menu.
      1 = ALMF page, 2 = HALMV chart + data, 3 = build the matrices (first time),
      4 = ALMT text almanac, 5 = HORZ sky chart with the info line (endless, R/S stops),
      6 = ALMS short almanac, 7 = HALMH chart on top + short table, 8 = BODY one body.
      Then it asks (INPUT, R/S keeps the value shown):
        DATE  YYYY.MMDD   e.g. 2026.0923
        UTC   HH.MMSS     e.g. 23.3000
        LAT   DD.MM       degrees.minutes, S negative   e.g. 10.00
        LON   DDD.MM      degrees.minutes, W negative   e.g. -75.30
      Values stay in the variables DATE UTC LAT LON for the next run.
      Registers R01-R08, R38, R39.

SPEED (Sep 2026): PTXB/PTXT draw each glyph column with one AGRAPH (WSIZE 8,
sun WSIZE 12) instead of one PIXEL per dot; the word size is set back to 64 at the end.
Separators use one PIXEL with a negative coordinate (full line) or PHL.
SUNRISE converges to 0.0003 h (about 1 s). HALMV ~81k steps, ALMF ~71k (was ~130k).
HORZ/HORZS use PTXT/PTXB too: HORZ ~79k steps (was ~132k), HORZS ~44k (was ~63k),
and each program is about 1000 lines shorter.

MOON AND PLANETS (series, any year 2000-2050)
--------------------------------------------
MATM   run once: Moon matrices ML MB MCL MCB (Meeus ch.47 + fitted terms)
MATP   run once: planet matrices (VSOP87D truncated) EEL.. VNL.. MAL.. JUL.. SAL..
       MATM and MATP can be deleted afterwards (MATP is a large program).
MOON   X = JD (UT1) -> X = GHA, Y = Dec, Z = HP ('), T = SD (')
       accuracy vs JPL 2000-2050: max 0.12', 99% < 0.07', rms 0.02'; HP 0.01'
PLAN   Y = JD (UT1), X = 1 Venus 2 Mars 3 Jupiter 4 Saturn
       -> X = GHA, Y = Dec, Z = SHA, T = HP (')      accuracy max 0.065'
       Registers R00-R09, R34-R39 (MOON R00-R09, R35-R39) + those of SUNA.
Check 23 Sep 2026 19:00 UT (JD 2461307.29167):
  Moon    GHA 319 40.7  Dec S 13 20.6  HP 55.92  SD 15.24   (JPL 319 40.8 / S 13 20.6)
  Venus   GHA  75 19.5  Dec S 19 44.9      Mars    GHA 167 56.9  Dec N 21 32.9
  Jupiter GHA 146 45.2  Dec N 15 54.3      Saturn  GHA 275 25.4  Dec N  2 18.3
ALM (Chebyshev tables) stays more accurate for Sep 2026 - Dec 2027 (0.002').

HORZ / HORZS with Moon and planets (Sep 2026)
  Same bodies as ALMF, HALMV and ALMT: the Sun always, the Moon and planets above the
  horizon, then the brightest stars higher than 10 deg (SBRT order) until 10 bodies.
  The Sun below the horizon is not drawn; its info line shows HC with a minus sign.
  HORZ repeats the info lines without end (after the last, the first again); R/S or
  EXIT stops it.
  Symbols: Sun circle with dot, Moon crescent, Venus, Mars, Jupiter, Saturn signs, star + number.
  HORZ info line: SUN / MOON / VENUS ... / "18 SIRIUS"  ZN ... HC ...   (PAUSE 30 each)
  Needs also MOON, PLAN (entries MOO2, PLN2), SBRT and the MATM / MATP matrices.
  About 72k steps (HORZ) / 69k (HORZS).
  PTXB symbol characters: ( Moon  < Venus  > Mars  = Jupiter  ? Saturn  * star  @ Sun
SBRT   X = k -> X = star number of the k-th brightest navigation star.

ALMF / HALMV with Moon and planets (Sep 2026)
  ALMF: same table rule as HALMV (10 rows): Sun, then Moon and planets above the
        horizon, then the brightest stars higher than 10 deg; Moon HP and SD bottom block.
  Both screens end with the line DOES NOT REPLACE THE NAUTICAL ALMANAC (HALMV uses PTXT).
  HALMV: table = Sun, then Moon and planets above the horizon, then brightest stars
        (> 10 deg) until 10 rows; their symbols on the chart; Moon HP and SD bottom line.
  Both now need MOON, PLAN, SBRT and the MATM / MATP matrices too.
  About 100k (ALMF) / 110k (HALMV) steps.
  NAV option 3 now builds all matrices (MATA, MATST, MATM, MATP).

TEXT ALMANAC (no drawing) - ALMT
  Z = JD (UT1), Y = lat (N+), X = lon (E+)  XEQ "ALMT"   (or NAV option 4)
  Shows one page at a time with PROMPT: two lines. Pages: date, UT, DR / GHA Aries
  and T or S; one page per body (name, HC, ZN / GHA, DEC in columns); Sun (twilight,
  rise/set / mer pass, SD); Moon (%, phase, age / HP, SD); the warning. R/S = next
  page; after the last page it starts over; EXIT to stop. Example: docs/ALMT_example.txt. Lines: date + UT, DR, GHA Aries, then for each body
  "NAME HC ... ZN ..." and "GHA ... DEC ..." (Moon also HP and SD), sun times,
  Sun SD, Moon phase and age, "DOES NOT REPLACE THE NAUTICAL ALMANAC".
  Bodies: same rule as ALMF/HALMV (Sun, Moon and planets above the horizon,
  brightest stars higher than 10 deg, 10 in all).
  Line break: the C47 font is proportional (letters 6-12 px, digits and space 8 px,
  . and : 5 px) and PROMPT breaks at a space when the next word does not fit in
  400 px. ALMT counts the pixel width of each line in R43 (CWID gives the width of
  each letter of the star names) and pads line 1 with spaces up to 400 px, so line 2
  always starts at the left edge. Columns are placed by pixels (HC at 136 px, second
  column of the Sun and Moon pages at 180 px); with 8 px spaces they can move by up
  to 7 px from page to page.
  Needs: SUNA STAR CHZ SUNRISE PHAS MOON PLAN SBRT SNMU STXT CWID + matrices.
  Does NOT need PTXB, PTXT or any drawing program. About 28k steps before the
  first line (17k with the tables); each further line is immediate.
STXT  number -> text: SDM (deg min), SNS, SEW, SZN, SHM, SF1, SINT, SDAT.
  Body names are in ALMT labels 80-85 (SUN MOON VENUS MARS JUPITER SATURN);
  if the C47 font has astronomical symbols they can be put there instead.

BELOW-HORIZON MARK (Hc < 0)
  ALMF / HALMV: the Hc value is shown white on black (XOR box, GRMOD 3, LBL 64); it was underlined before.
  ALMT: the body line starts with "* " (LBL 92), e.g.  * SUN HC -55°39.9' ZN 311.0°
  Only the Sun can get it: Moon and planets are listed only when above the horizon.
  Cost: one X<0? test per row; the line itself (about 160 steps) only when Hc < 0.
  Previews: docs/ALMF_below_horizon.png, docs/HALMV_below_horizon.png

SHORT VIEWS (Sep 2026) - ALMS and HALMH, NAV options 6 and 7 (NAVFULL: 5 and 6)
  Body list: Sun; Moon if above the horizon; the first planet above the horizon in
  the order Venus, Jupiter, Mars, Saturn; the 3 brightest stars higher than 10 deg.
  ALMS  = ALMF layout with that list.  HALMH = horizon chart across the top (full
  width, Hc 90 deg = 96 px) and the same table below, Sun times and Moon % on one line.
  Steps, average of 20 cases 2025-2050 (series): ALMF 46.6k -> ALMS 32.6k,
  HALMV 56.3k -> HALMH 43.3k. Previews: docs/ALMS_preview.png, docs/HALMH_preview.png

ONE BODY (Sep 2026) - BODY, NAV option 8 (NAVFULL: 7)
  1. A list of the bodies above the horizon, text pages: 60 SUN, 61 MOON, 62 VENUS,
     63 MARS, 64 JUPITER, 65 SATURN, then the stars by Nautical Almanac number,
     brightest first (higher than 10 deg). R/S = next page. Key a number on any page
     and R/S to choose it.
  2. The legend page: key the number, R/S (nothing or 0 shows the list again).
  3. Two text pages: name, date, GHA, Dec / Hc, Zn and SHA (stars, planets), SD (Sun)
     or HP and SD (Moon). R/S: the horizon chart with the body and its data. Then the
     legend again for the next body. EXIT stops.
  Numbers only: a single letter S would be both Sun and Saturn.
  Steps (average, series): list 6.6k; result Sun 3.2k, star 3.5k, Venus 6.4k,
  Mars/Jupiter 8.5k, Saturn 11.2k, Moon 10.3k; chart 12.3k.
  PC: python3 python/native/c47pc.py --lat .. --lon .. --body 18 [--png sirius.png]
  Preview: docs/BODY_preview.png

TIME (Sep 2026): on the C47 the trigonometric functions take most of the time (about
6 ms each at 34 digits, measured with tools/tests_calc/TVEC; an ordinary step about
0.2 ms). The programs now avoid repeating them:
  - HCZ keeps sin/cos of the latitude (HCZI, once per screen): 6 trig functions
    instead of 14; the celestial equator on the charts uses HCZQ/HCZR (LHA rotated by
    the step, no COS/SIN per dot).
  - STR2 uses constants computed once per page in SUNA (precession, obliquity,
    aberration): about 25 instead of 45; the screens skip stars whose catalogue
    altitude is below 9 deg (SQK, 3 trig functions) before the full calculation.
  - The Sun/planet series (SER) and the Moon terms use the matrix functions
    (matrix x vector, COS/SIN of a vector, DOT) instead of a loop per term.
  - PLN3: the Earth from mean elements once per page; shorter heliocentric routine.
  Estimated seconds per screen (simulator counts x measured costs), FULL / FAST:
                 before    now
     ALMT        19.1      10.7 / 9.1
     ALMF        22.3      13.9 / 12.3
     HALMV       33.4      16.6 / 14.9
     HORZ        35.9      14.7 / 13.1
  Values shown are unchanged (all parity tests). Matrix layouts changed: load the new
  NAVINIT_FULL or NAVINIT_FAST and run INIT again. FULL matrices now hold about 5,700 numbers (was 4,300);
  FAST about 3,100.

FULL OR FAST SERIES (Sep 2026) - NAVINIT_FULL or NAVINIT_FAST (load one, XEQ "INIT")
  FULL: VSOP87 truncated (MATA, MATP), any date 2000-2050.
  FAST: a series fitted to 2026-2030 only (MATF, tools/almanac/fastseries.py): a
        quadratic for all slow effects plus the short-period terms. 677 terms -> 185,
        about a third of the memory for these matrices. Checked against JPL DE421
        over 2026-2030, max error (GHA / Dec): Sun 0.016' / 0.013', Venus 0.082' /
        0.042', Mars 0.033' / 0.034', Jupiter 0.010' / 0.022', Saturn 0.045' / 0.026'.
        Steps (average 2026-2030): ALMT 28.6k -> 24.2k, ALMF 47.4k -> 43.1k,
        HALMV 57.1k -> 52.8k, HORZ 50.7k -> 46.4k.
        Outside its years SUNA sets flag 12 and the screens show X instead of T/S:
        run INIT again (FULL) or load a new MATF (python3 tools/almanac/fastseries.py
        2031 5). The coefficients differ for every period.
  The series matrices now carry their number of terms in row 1 (SER reads it), so
  SUNA and PLAN work with either set. Rebuild the matrices after loading these programs.
  PC: c47pc.py --fast

THE FILES FOR THE CALCULATORS - build/ (python3 tools/build_navfull.py, build_dm42.py,
build_free42.py)
  Only NAV (and INIT) keep their names: every other program label is N01, N02 ... The
  numbers come from fixed maps, tools/labels/<build>.map (one line "N01 SUNA" each): a new
  routine gets the next free number and a number is never reused, so the labels stay the
  same from one version to the next. build/.../<build>_LABELS.txt lists them. The same
  programs with the original names are in the dev/src/ folders (used by the tests);
  tests/test_labels.py checks that both work alike. The file name is the version: the
  program on the calculator is always NAV (and INIT), so two versions can be kept.

  build/        C47 / R47 / DM42n with the C47 firmware (with ATEXT and GRFNT). Every C47 build
                draws the screens of Oct 2026 (programs/atext/t21/): the text with ATEXT in
                GRFNT 21 and the tinyFont (GRFNT 10) on the charts, the body symbols from glyphs47
                (PSYB, PSYS: the only AGRAPH font left). .p47: tools/rejig47_atext.py.
                FIRMWARE: these builds and build/dm42/ need C47 / R47 firmware 00.109.05.00a0.ALPHA
                (5 Oct 2026) or later, or one built from master on or after 30 Sep 2026 (ATEXT
                29 Sep, GRFNT 30 Sep). On the older public firmware 00.109.04.00b0 they stop with
                "Non-programmable command": use Almanac47_C47_R47_fw0400b0_v1.1.0.zip (v1.1.0
                release). build/free42/ runs on the stock DM42 / DM42n firmware.
    MOON47.txt       MOON47: the Moon phase on its own (no NAV, no INIT, about 4.8 KB): the date and time
                     from the clock (minus TZ hours if the variable TZ exists; the top line shows the
                     clock: UT TZ=0, or LT TZ=+4), the phase as a disc, % lit,
                     age, HP, SD, the next four phases (UT), the 8 phase symbols; +/- north / south view,
                     other keys end. Same page in build/dm42/, build/free42/ (.raw), python/numworks/,
                     python/hpprime/ and on the PC (python/moon47.py; the MOON view of python/native).
                     All written by tools/build_moon47.py from python/moon47.py (20 terms of Meeus 47,
                     phases within 4 minutes, HP 0.03'; the 20 terms as matrices, on the C47 with one
                     complex eˣ for their cos and sin); tests/test_moon47*.py.
    NAVFULL.txt      NAV v2.1.0: 1 ALMANAC 2 SPLIT 3 SKY 4 ANIM 5 ALLSKY 6 INFO, 9 = SNAP, 0 END
                     (↑↓ ±1 hour), the sky cache, the SINKING box, the ants (flag 47), and the
                     almanac tables (TBL) when they are loaded. Your registers are kept: R00-R98
                     saved in NAV's local registers at the start, given back at 0. Written by
                     tools/build_v2.py (Horner, n-vectors, ISG loops, registers renumbered; v2.1.0:
                     tools/navmat.py, docs/OPTIMIZATIONS.md section 7). NAVTXT (text only) is not in v2.x.
    NAVINIT_FULL.txt INIT: VSOP87 series, valid 2000-2050 (MATA MATST MATM MATP as LBL 01-04)
    NAVINIT_FAST.txt INIT: fitted series, valid 2026-2030 (MATN MATST MATM MATF), smaller
                     Load ONE of them, XEQ "INIT" once, delete INIT (GTO "INIT", DELP); the
                     matrices stay. Zero elements are not stored: a new matrix starts with zeros.
    TBL_1.txt        almanac tables, 1 year (1 Oct 2026 - 30 Sep 2027): 8,441 numbers
    TBL_5.txt        almanac tables, 5 years (1 Oct 2026 - 30 Sep 2031): 41,882 numbers
                     Chebyshev coefficients fitted to JPL DE421 (tools/almanac/). Load ONE,
                     XEQ "TBL" once (flag 10), delete the program; the matrices stay. Every NAV
                     reads them when they are there (T on the screens): NAVFULL, NAVLITTLE
                     (Sun and GHA Aries) and the Free42 versions; outside the table period, or
                     after CF 10, the series. Memory (16 bytes a number): TBL_1 about 135 KB of
                     matrices, TBL_5 about 670 KB - too much for the C47's 256 KiB together with
                     NAV and INIT: they are meant for Free42 / Plus42 on a PC or phone. On the C47
                     only a short table can fit (4 months already filled it next to NAVFULL and
                     the matrices; build/dev/TBL_OCT2026 is one month; make one with
                     tools/almanac/tab2c47.py START END).
    build/dev/       NAVFULL_NOTBL (NAVFULL without the tables), NAVALL (all views, NAV runs
                     INIT itself), NAVCOMP (compact menu 1 2 4 8 9), TBL_4M (26 Sep 2026 - 31 Jan
                     2027, the tests), TBL_OCT2026 (27 Sep - 31 Oct 2026)
  build/dm42/   old DM42 with the C47 firmware (64 KiB): Sun and 58 stars only
    NAVLITTLE.txt    NAV: straight to the ALMANAC screen, UP / DOWN one hour, + ends;
                     the T21 ALMANAC view, Sun and stars only (no Moon), ATEXT in GRFNT 21 and
                     the Sun and star glyphs; no box, no ants, no cache; 7.9 KB
    NAVINIT_LITTLE.txt  INIT: Sun series (FULL, 2000-2050), nutation, stars
    build/dm42/dev/  NAV1T_DM42, NAV12_DM42, NAVTXT_DM42, NAVINIT_DM42_5Y
  build/free42/ DM42 / DM42n with the stock firmware (Free42): .raw files and .txt listings
    NAVFULL          as the C47 NAVFULL without the tables; the screen appears complete, as on
                     the C47 (RefLCD). build/free42/dev/NAVFULL_DRAW: the screen builds up.
    NAVLITTLE        NAV straight to the ALMANAC screen in the style of Oct 2026 (as NAVFULL:
                     header line, PTXS = the widths of GRFNT 21): the Sun and the stars, no Moon,
                     the same screen as the C47 NAVLITTLE; .raw 8.9 KB
                     Free42 has no ATEXT: its builds keep AGRAPH fonts with the same pixels.
    NAVINIT_FULL, NAVINIT_FAST, NAVINIT_LITTLE   the INITs, as above
    TBL_1, TBL_5     the almanac tables as above (.raw 97 KB and 481 KB); flag 11 of the C47
                     programs is flag 91 here (11 is auto-execution on the HP-42S)
  Left out: HORZS, HPLT, HALM, ALM, SNAM, SUNSD, font demos.
  Checks: tests/test_v2.py (v2.x against the release before it, Free42 against the C47, the
  registers kept), tests/test_labels.py, test_navfull.py, test_notbl.py,
  test_f42_little.py (Free42 NAVLITTLE against the same view in the C47 simulator, pixel by
  pixel: start, +1 h, -1 h on 3 dates),
  test_f42_tables.py (NAVFULL and NAVLITTLE with TBL_1 / TBL_5, Free42 against the C47),
  test_navfull_atext.py (NAVFULL: every view in the simulator, the texts given to ATEXT),
  test_dm42_atext.py (NAVLITTLE, NAV1T_DM42, NAV12_DM42).

STATUS-BAR FONT AND SINE ALTITUDE SCALE (Sep 2026)
  PTXS (tools/generators/mkstd.py) is the C47's own status-bar font (standardFont, bold
  capitals 12 px) as a drawing program, same calls as PTXB with S names:
  PTXS PINS PF1S PHMS PDMS PDTS PZNS PHLS. The symbols @ ( * < > = ? are the PTXB ones
  scaled to 12 rows and made bold. WSIZE 14 (13 rows + sign bit); line pitch 14 px.
  Narrow spacing: one blank column less after every glyph than on the C47 (digits and
  space 7 px, letters 8-11 px) - still clear, and the star numbers fit again.
  All pixel views use it (ALMT uses PROMPT, which already draws this font):
    ALMF   ARIES row + 9 bodies, stars with their number; NAUT TWI, RISE/SET, MER PASS,
           Sun SD and the Moon below.
    ALMS   ARIES, Sun, Moon, 1 planet, 3 stars (same layout).
    HALMV  chart 18..168 on the left; panel from x 176: date/UT, DR, ARIES, then symbol,
           star number, name, HC, ZN of 10 bodies, Moon phase.
    HALMH  chart on top; table rows as ALMF (with star numbers), no titles; footer
           RISE SET MER ARIES / TWI MOON.
    HORZ   info line in the big font (clears y 224 and up); bodies and star numbers big.
    BODY   chart bigger (horizon y 86); rows GHA DEC / HC ZN / SHA ARIES (SD, HP SD).
  Axis letters and altitude marks use the small font PTXT.
  Charts: sine altitude scale, height = sin(Hc) x scale: 0-30 deg takes half the height,
  90 deg stays at the top, nothing is cut. Marks 10 20 30 45 60 90. HCZ, HCZ0 and HCZR
  keep sin Hc in "SHC" (the value before ASIN): no extra trig.
  Celestial equator: each dot is 2 x 2 pixels (four PIXEL), easier to see.
  NAVFULL grows by 234 lines (the font +470, the views shorter).

ANIMATION (Sep 2026) - HANIM, NAV option 9 (NAVFULL: 8 ANIM)
  IN: Z = JD, Y = lat, X = lon (NAV asks date, UTC, lat, lon as for the other views).
  The Sun and the Moon on the whole-sky chart of ALLSKY: horizon across the middle,
  OVER HORIZON above, UNDER HORIZON below (sine scale both ways). Every half hour for
  24 frames (12 hours), PAUSE 10 (1 s) after each; the last frame stays (PAUSE 99).
  The chart is drawn once and the screen is not cleared: every frame adds the Sun and
  the Moon, above or below the horizon, so their paths build up through setting and
  rising. Only the top line is cleared (CLLCDxy) and rewritten: date and UT of the frame,
  frame number, DAY / TWILIGHT / NIGHT (Sun above the horizon / above -12 deg / below).
  Change it by editing three program lines: "24 STO 14" (frames), "0.5 STO 15" (hours
  per frame; 1 = a whole day in 24 frames), "PAUSE 10" (tenths of a second per frame).
  Every frame: Sun (SUNF) and Moon (MOOQ, geocentric, within about 0.3 deg) for its own
  time, GHA Aries exact. No matrices.
  About 62,000 steps in all (chart and equator once, then about 1,800 steps and
  25 trigonometric functions per frame: roughly 0.5 s on USB power plus the 1 s pause).
  PC: c47pc.py view ANIM (window: Frames, Step h, Frame ms, Play; Save PNG = animated
  PNG) or  --view ANIM --png anim.png --frames 24 --step 0.5 --frame-ms 1000
  Check: python3 tests/test_anim.py (calculator program vs Python, frame by frame).

WHOLE SKY (Sep 2026) - ALLSKY, NAV option 10 (NAVFULL: 9 ALLSKY)
  IN: Z = JD, Y = lat, X = lon. The horizon runs across the middle of the screen: the
  upper half is OVER HORIZON (Hc 0 to 90), the lower half UNDER HORIZON (Hc 0 to -90),
  both with the sine altitude scale; Zn across as on HORZ. Every body is drawn: Sun,
  Moon, planets (big symbols) and all 58 stars (small star and number); the celestial
  equator dotted in full. Top line: date, UT and DAY (Sun above the horizon), TWILIGHT
  (Sun above -12 deg) or NIGHT.
  Sun SUNA, Moon MOO2, planets PLN3; stars from the catalogue with first-order precession
  (within about 0.05 deg, 9 trig each). About 32,000 steps and 1,100 trigonometric
  functions: roughly 12 s on USB power (estimate), like HORZ.

AGRAPH / PIXEL DEMO (Sep 2026) - extras/DEMOALM.txt (python3 tools/build_demo.py)
  No navigation programs: the almanac page ALMF with fixed sample data (Dubai,
  02-10-2026 18:00 UT) and the text programs. XEQ "DEMO" -> 1 AGRAPH 2 PIXEL 0 END.
    1  DALA  the page with PTXS/PTXT: one AGRAPH per glyph column (2,925 AGRAPH calls).
    2  DALP  the same page and glyph data drawn dot by dot: each column's bits are tested
             and every lit dot is one PIXEL (19,372 PIXEL calls).
  The bottom line shows the time measured with TICKS. Simulator estimate (USB power):
  AGRAPH about 4 s, PIXEL about 90 s. 6,690 lines; GPL-3.0 (contains PTXS).
  extras/DEMOALM_rem.txt (python3 tools/annotate_demo.py): the same program with ~2,000 REM
  comments - every drawing call (row, column, what it prints), the font routines, a picture
  of every character, and the PIXEL routine LBL 99 line by line. Same steps, same pages.
  Labels: only DEMO keeps its name; the pages and font routines are N01-N24, and in the
  commented file each one says what it does and whether it is a FONT routine
  (table: extras/DEMOALM_LABELS.txt).

ATEXT (coming C47 command, Sep 2026) - extras/C64_ATEXT.txt, extras/DEMOATX.txt, extras/THANKS_ATEXT.txt
  ATEXT r draws the string in register r in the C47 standardFont: Y = row of the bottom of the
  20-row glyph box (base line 4 rows up), X = column; it leaves the Y and X of the next character.
  The CR glyph starts a new line 20 rows down at the start column (several CRs = several lines,
  but a CR as the first character of the string is drawn, not a line break); GRMOD 0 sets, 1 clears the
  glyph box first, 2 clears, 3 flips. AGRAPH stays, for own fonts and symbols.
  The simulator (python/c47sim.py, font python/stdfont.py) draws ATEXT like the C47: the
  ATEXTing demonstration (Jaco Mostert) gives the calculator's screen to 15 of 12,656 pixels
  (tests/test_atext.py).
  C64_ATEXT: the C64 tribute with ATEXT: about 560 bytes instead of 3,750 (no 8 x 8 font; the
  text is in the C47 font). DEMOATX (python3 tools/build_demo_atext.py): the DEMOALM page with
  ATEXT, no AGRAPH; the symbols are characters of the C47 font (the Sun STD_SUN U+2299, the
  stars *, the Moon (, the planets Greek letters: Venus phi, Mars sigma, Jupiter psi, Saturn h-bar),
  one ATEXT each at x 0. DEMOATXS: the same with the symbols from an own AGRAPH font instead
  (PSYM: only the three symbols on the page, Sun, Saturn and star, 36 AGRAPH).
  The standardFont is proportional (letters 5-14 px, digits and the space 8 px), so one string per
  line did not line up: now every column is its own ATEXT at a fixed x (number and name, GHA, N/S,
  DEC HC ZN), the footer in three columns with the CR glyph. Every text goes through LBL 98, the
  N03 trick of Didier (dlachieze): row, column, text, XEQ 98 -> ⇄ zyxt, 4, -, x<>y, ATEXT Z.
  The two lines across with PIXEL, the time top right. DEMOATX 670 steps, DEMOATXS 1,282,
  against 23,000 for the AGRAPH page (.p47: 7.9 KB and 10.4 KB against 72.8 KB). Both need a firmware
  with ATEXT. rejig does not know ATEXT yet: convert a copy with VIEW Z in LBL 98 and change
  that one step to ATEXT Z on the calculator.
  THANKS_ATEXT (XEQ "THANKS"): a thank-you to Jaco Mostert for ATEXT, in the C64 style: the boot
  screen, 10 PRINT "THANK YOU JACO " typed letter by letter with the cursor, 20 GOTO 10, RUN, then
  the screen fills with THANK YOU JACO, BREAK IN 10, READY. and the cursor blinks until a key.
  The text with ATEXT (CR for the lines), the dark border with AGRAPH, the cursor with XOR (GRMOD 3).

MOON WORD (Sep 2026)
  ALMF, HALMV and ALMT show FULL when the Moon is shown 100 %, NEW at 0 %,
  otherwise WAXING (age under 14.765 d) or WANING.

ALMANAC TABLES AND THE T / S SWITCH (Sep 2026)
  TBL   tables for 26-09-2026 to 31-01-2027 (Chebyshev, from JPL DE421). Run once:
        XEQ "TBL" builds the matrices and sets flag 10. It can then be deleted.
  TGET  Y = JD, X = body (0 Sun 1-4 planets 5 Moon 6 Aries) -> X GHA, Y Dec
        (Moon Z HP, T SD); X = -1 outside the table.
  With flag 10 set, SUNA, SUNRISE (via SUNG), MOO2 and PLN2 use the tables inside
  their period and the series outside it. The screens show T (tables) or S (series):
  ALMF/HALMV bottom right, HORZ/HORZS bottom left, ALMT end of the first line.
  Screens need fewer program steps with the tables. CF 10 = series only.
  New tables: tools/almanac/tab2c47.py (see tools/almanac/README.md).

SPEED-UPS (Sep 2026)
  1. SUNRISE iterations use SUNF, a low-precision Sun (Astronomical Almanac
     formula, 0.01 deg) instead of 13 full SUNA runs. Event times stay within
     about 15 s of the full Sun (in about 1 % of cases the minute shown changes
     by one). GHA and Dec on every screen still come from the full SUNA.
  2. SER (all VSOP series) adds each term to R30+k (column 1 of the series
     matrices holds 30+k) and multiplies by the powers of tau once at the end:
     about 25 % fewer steps per term, same values to 34 digits.
  3. PLAN computes the Earth once for the four planets (R03 = tau of R00-R02).
  4. ALMF, HALMV and ALMT call PHA2 (Moon phase) right after their own SUNA
     instead of PHAS running SUNA again.
  5. The screens call PLN3 for the planets: a quick position from mean orbital
     elements (within 0.2 deg). A planet with Hc below -1 deg is not computed
     further (it is not shown; about half of all cases). Otherwise the series run
     once, with the light time from the quick distance (was: two passes).
     Planet GHA/Dec change by at most 0.0002'. ALMT first page: 42k -> 28k steps
     on average (2025-2050).
  Steps (Cape Town, 23 Nov 2026 09:00 UT), before -> after:
     series:  ALMT first page 81k -> 29k, ALMF 100k -> 48k, HALMV 110k -> 57k,
              HORZ 76k -> 51k
     tables:  ALMT 20k -> 17k, ALMF 36k, HALMV 45k (almost unchanged)
  Rebuild the matrices after loading the new MATA/MATP (NAV option 3, or
  NAVINIT_FULL/FAST + XEQ "INIT"): the old matrices do not work with the new SER.

PC VIEWER - python/c47view.py (+ c47sim.py)
  Shows ALMF, HALMV, HORZ, HORZS and ALMT on a PC exactly as on the C47: it runs
  the real programs/*.txt in a small RPN interpreter and draws the 400x240 screen.
  Window (GTK 3):  python3 c47view.py
     date, UT, lat, lon at the top; pick the view; Run; R/S (Enter/Space) = next
     HORZ object or next ALMT line; Save PNG; "LCD colours" on/off.
  PNG only:        python3 c47view.py --view HALMV --date 2026-09-25 --ut 18:30 \
                          --lat "25 20 N" --lon "55 12 E" --png halmv.png
     --scale 4, --plain (black on white), --no-bezel, --all-frames (HORZ).
  Text:            python3 c47view.py --view ALMT --date ... --lat ... --lon ...
  Window needs PyGObject + cairo + GTK 3
     Arch: pacman -S python-gobject python-cairo gtk3
     Debian/Ubuntu: apt install python3-gi python3-gi-cairo gir1.2-gtk-3.0
  PNG and text need only Python 3. Keep the python/ and programs/ folders side by side.
  ALMT in the window uses a PC monospace font (the C47 font is not available).

PC VERSION, NATIVE PYTHON - python/native/c47pc.py
  Same screens and window as c47view.py, but with its own calculations: no C47
  programs and no simulator. Files: c47pc.py (window / PNG / text), c47astro.py
  (Sun, stars, Moon, planets, rise/set/twilight, Moon phase, Hc/Zn - same methods
  and coefficients as SUNA STAR MOON PLAN SUNRISE PHAS CHZ), c47screen.py (the
  ALMF HALMV HORZ HORZS layouts and the ALMT lines), c47screen21.py (the screens of Oct
  2026), c47font.py c47fonts2.py c47fonts21.py (fonts), c47data.py (coefficient tables),
  c47tables.py, jplcheck.py. Copy the files of python/native/ anywhere and run:
     python3 c47pc.py                                   (GTK 3 window)
     python3 c47pc.py --view ALMF --date 2026-09-25 --ut 18:30 --lat "25 20 N" --lon "55 12 E" --png almf.png
     python3 c47pc.py --view ALMT --date ... --lat ... --lon ...   (text lines)
  Checked against the calculator programs on 75 dates and places (latitudes to
  72 N/S, 2025-2028): every screen identical pixel for pixel, every ALMT line
  identical. A screen takes about 0.02 s.
  c47view.py (runs the real programs) stays in python/ as the reference.
  Version 1.1 (2026-09-26): menu Info with Help and About (version); --version.
  Check against JPL (online, optional): link under the screen or menu Info opens a
  window with every C47 value beside JPL Horizons and the difference; --check prints it.
  Almanac tables: box "Almanac tables" (TBL.txt), --tables FILE, --series.
  Sep 30, 2026: the default tables are build/TBL_5.txt (1 Oct 2026 - 30 Sep 2031), then
  build/TBL_1.txt, then the old 4-month programs/TBL.txt (or TBL_5/TBL_1/TBL.txt next to c47pc.py).
  Version 1.4 (2026-10-01): the views ALMANAC CHART TEXT SKY SPLIT ANIM ALLSKY MOON (the old
  names ALMF HALMV ALMT HORZ HALMH still work), drawn as the C47 screens of Oct 2026
  (c47screen21.py; tests/test_parity21.py: identical to NAVFULL in the simulator). MOON
  (the phase disc, % lit, age, HP, SD, the next four phases) is a view of the PC only.
  Version 1.5 (2026-10-01): - / + step the UT (keys or buttons next to Now UTC) by 1 s to
  999 days (1 h by default); hold the key to watch the sky move.

SEPTEMBER 29, 2026 - NAV AS IT IS NOW
  NAV asks DATE (in the CLK date format: YYYY.MMDD, DD.MMYYYY or MM.DDYYYY, as the message line
  shows; read with x→ⅅ ⅅ→J), UTC, LAT, LON once,
  computes the sky (matrix ALMC; the charts' equator in ALMQ) and shows a graphic menu (KEY?):
  1-8 a view, 9 SNAP, + back to the menu, up / down arrow one hour later / earlier, 0 end.
  Views only draw from the cache; a new hour computes again. Faster drawing in the NAV files
  (tools/navopt.py): font columns read from stack register D (8-level stack, set by NAV and
  restored at the end), full-width lines with PIXEL, dates with J→ⅅℸ DAY MONTH YEAR, number
  text with αIP / x→α. The Hc of a body below the horizon is white on black.
  On the real C47 the screen is shown at a PAUSE or a key: NAV makes a PAUSE 0 after drawing
  (it shows the screen with no wait; PAUSE 1 did the same with 0.1 s). SCREEN UPDATE below.
  Details: DEVELOPMENT_NOTES.md; every view and the N-label map: docs/C47_Nav_User_Manual.pdf.
  Menu now: 1 ALMANAC 2 CHART 3 TEXT 4 SKY 5 SPLIT 6 ANIM 7 ALLSKY 8 INFO, 9 = SNAP (screenshot of
  the menu or of any view; Free42: PRLCD), 0 END (BODY and SMALL left out of the NAV files;
  programs/BODY.txt and ALMS.txt still work on their own). The warning (cross-check with the
  almanac) only on the menu and INFO. While the calculator works a box says
  SINKING....ABOUT.

SCREEN UPDATE - C47 AND FREE42 (DM42 / DM42n)
----------------------------------------------
Both calculators draw with PIXEL and AGRAPH; they differ in WHEN the drawing reaches the LCD.
  C47     draws in memory and sends the screen to the LCD only at a PAUSE, a key press or the
          end of the program - not while a KEY? loop waits. NAV shows each screen with PAUSE 0
          (0 ticks: the screen with no wait; tested on the C47, faster than the PAUSE 1 of
          before). So a view appears complete, in one piece, and the SINKING box stays on the
          LCD until the new screen is ready. Holding a key while a view draws makes the C47
          update the LCD at every key event: then it draws step by step.
          The C47 has no command to switch the LCD update on or off (C47_Full_index.txt): a
          screen that should build up in steps needs a PAUSE 0 after each step.
  Free42  (the stock firmware of the DM42 / DM42n) sends every AGRAPH and PIXEL to the LCD at
          once, so the screen builds up in front of you (the stars of SKY appear one by one)
          and the SINKING box is cleared as soon as the next view starts drawing.
          The DM42 variable RefLCD switches the LCD update: 0 STO "RefLCD" = no update, -1 STO
          "RefLCD" = update once, 7 = normal. build/free42/NAVFULL and NAVLITTLE use it to behave
          like the C47 (the screen complete, at once); dev/NAVFULL_DRAW keeps the Free42 way.
          Free42 on a PC or phone has only the 131 x 16 HP-42S screen (no GrMod 3): NAV runs,
          but only the top left corner of each screen is shown.

