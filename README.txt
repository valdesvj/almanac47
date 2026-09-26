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
SUNRISE 90-99 (HORZ also 90-99)   PHAS 41-48   SNAM 49   ALM 01-09, 10-33, 40-41

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
Functions: jd(y,m,d,h)  sun(jd)  star(jd,n)  event(jd0,lat,lon,kind)  phase(jd)

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
      XEQ "NAV" -> "1 ALMANAC 2 HORIZON 3 INIT 0 END": key the number, R/S.
      1 = ALMF page, 2 = HALMV chart + data, 3 = run MATA and MATST (first time).
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
  Shows the Sun, the Moon, Venus, Mars, Jupiter and Saturn when above the horizon,
  and the 5 brightest stars higher than 10 deg (order by magnitude from SBRT).
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
  Shows one line at a time with PROMPT; R/S = next line; after the last line it
  starts over; EXIT to stop. Lines: date + UT, DR, GHA Aries, then for each body
  "NAME HC ... ZN ..." and "GHA ... DEC ..." (Moon also HP and SD), sun times,
  Sun SD, Moon phase and age, "DOES NOT REPLACE THE NAUTICAL ALMANAC".
  Bodies: same rule as ALMF/HALMV (Sun, Moon and planets above the horizon,
  brightest stars higher than 10 deg, 10 in all).
  Needs: SUNA STAR CHZ SUNRISE PHAS MOON PLAN SBRT SNMU STXT + matrices.
  Does NOT need PTXB, PTXT or any drawing program. About 81k steps before the
  first line; each further line is immediate.
STXT  number -> text: SDM (deg min), SNS, SEW, SZN, SHM, SF1, SINT, SDAT.
  Body names are in ALMT labels 80-85 (SUN MOON VENUS MARS JUPITER SATURN);
  if the C47 font has astronomical symbols they can be put there instead.

BELOW-HORIZON MARK (Hc < 0)
  ALMF / HALMV: the Hc value is underlined (54 px line, PHL, LBL 64).
  ALMT: the body line starts with "* " (LBL 92), e.g.  * SUN HC -55°39.9' ZN 311.0°
  Only the Sun can get it: Moon and planets are listed only when above the horizon.
  Cost: one X<0? test per row; the line itself (about 160 steps) only when Hc < 0.
  Previews: docs/ALMF_below_horizon.png, docs/HALMV_below_horizon.png

ALMANAC TABLES AND THE T / S SWITCH (Sep 2026)
  TBL   tables for 26-09-2026 to 31-01-2027 (Chebyshev, from JPL DE421). Run once:
        XEQ "TBL" builds the matrices and sets flag 10. It can then be deleted.
  TGET  Y = JD, X = body (0 Sun 1-4 planets 5 Moon 6 Aries) -> X GHA, Y Dec
        (Moon Z HP, T SD); X = -1 outside the table.
  With flag 10 set, SUNA, SUNRISE (via SUNG), MOO2 and PLN2 use the tables inside
  their period and the series outside it. The screens show T (tables) or S (series):
  ALMF/HALMV bottom right, HORZ/HORZS bottom left, ALMT end of the first line.
  Screens need about half the program steps with the tables. CF 10 = series only.
  New tables: tools/almanac/tab2c47.py (see tools/almanac/README.md).

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
  ALMF HALMV HORZ HORZS layouts and the ALMT lines), c47font.py (PTXB/PTXT fonts),
  c47data.py (coefficient tables). Copy the five files anywhere and run:
     python3 c47pc.py                                   (GTK 3 window)
     python3 c47pc.py --view ALMF --date 2026-09-25 --ut 18:30 --lat "25 20 N" --lon "55 12 E" --png almf.png
     python3 c47pc.py --view ALMT --date ... --lat ... --lon ...   (text lines)
  Checked against the calculator programs on 75 dates and places (latitudes to
  72 N/S, 2025-2028): every screen identical pixel for pixel, every ALMT line
  identical. A screen takes about 0.02 s.
  c47view.py (runs the real programs) stays in python/ as the reference.
  Version 1.1 (2026-09-26): menu Info with Help and About (version); --version.
