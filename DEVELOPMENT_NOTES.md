# Development notes

Decisions and conventions for the C47_nav suite and the Almanac 47 app. Read this first
when you continue the work, whether you are a person or an AI assistant.

## The three versions

| Version | Where | What it is |
|---|---|---|
| C47 calculator programs | `programs/` (plain), `programs_rem/` (with REM comments), `listings/` (annotated) | The original. RPN programs for the SwissMicros C47 / R47. |
| PC reference viewer | `python/c47view.py` + `python/c47sim.py` | Runs the real `programs/*.txt` in a small RPN interpreter and shows the 400x240 screen. The reference for everything else. |
| Native Python | `python/native/` (`c47pc.py`, `c47astro.py`, `c47screen.py`, `c47font.py`, `c47data.py`) | Own calculations and drawing, no simulator. Must stay identical to the calculator, pixel for pixel. The model for the phone app. |

`tests/test_parity.py` compares the native Python version with the calculator programs
(ALMF, HALMV, HORZ frames, HORZS and every ALMT line). Run it after every change:

    python3 tests/test_parity.py 60

It has been passed with 75 dates and places (2025-2028, latitudes up to 72 N/S).

## Calculator program conventions

- Plain UTF-8 text, one command per line, no line numbers. Converted to `.p47` with
  `rejig file.txt -o file.p47`.
- No HP-42S compatibility commands (the `42...` ones). Use the C47 commands.
- Messages with `PAUSE` / `PROMPT`, not with key reading.
- Text is drawn with our own AGRAPH fonts: `PTXB` (5x7) and `PTXT` (3x5). Glyphs are
  drawn column by column with `AGRAPH`, word size 8 (the Sun symbol uses 12); WSIZE 64
  is restored at the end. `α→𝑥` needs WSIZE >= 8 for character codes up to 90.
- Symbols in PTXB: `*` star, `@` Sun, `(` Moon, `<` Venus, `>` Mars, `=` Jupiter, `?` Saturn.
- Stack interface of the text routines: Z = y, Y = x, X = string or number; returns
  Y = y, X = next x.
- Screen 400 x 240, origin bottom-left. `PIXEL` with a negative x (or y) draws a full
  vertical (horizontal) line.

## ALMT and the C47 PROMPT line

The C47 standard font is proportional (widths in `programs/CWID.txt` and
`c47screen.CHAR_W`; measured from photos of the test program `tools/tests_calc/TWRAP.txt`).
PROMPT lines are 400 px; a word that does not fit starts the next line, and spaces that
do not fit are carried to the next line as indentation. ALMT keeps the pixel width of
the line in R43, pads line 1 with spaces up to 400 px and places columns by pixels.
`c47screen.almt` does the same; `prompt_lines` models the break. The PC window places
each character at its C47 pixel position; the text export uses a fixed-column layout
(`almt_mono`).

## Almanac conventions

- Star numbers are the Nautical Almanac numbers 1-57; 58 = Polaris (our own choice).
  The list is in decreasing SHA order, as in the almanac. `SBRT` gives them by brightness.
- Table rule (ALMF, HALMV, ALMT): 10 rows. The Sun always; then the Moon and the
  planets if Hc > 0; then the brightest stars with Hc > 10 deg until the table is full.
  HORZ and HORZS show the same bodies (the Sun below the horizon is listed in the HORZ
  info loop but not drawn). The HORZ info loop is endless.
- Below the horizon (Hc < 0, in practice only the Sun): Hc white on black (XOR box) in ALMF/HALMV,
  line starts with `* ` in ALMT.
- Horizon charts: north latitude has S in the centre (N E S W N), south latitude has
  N in the centre (S W N E S), so the celestial equator is a symmetric arch.
- Times are UT (UT1). TT - UT1 = 69.2 s.
- Every screen carries "DOES NOT REPLACE THE NAUTICAL ALMANAC". The programs support
  the Nautical Almanac; they do not replace it.

## Speed (Sep 2026)

- SUNRISE iterates with SUNF (low-precision Sun, `c47astro.sun_fast`); event times
  within about 15 s of the full Sun. Screens show GHA/Dec from the full SUNA.
- SER: column 1 of every series matrix holds 30+k (k = power of tau); terms go to
  R30-R32 and are combined with tau at the end (Horner). MATA and MATP changed: the
  matrices must be rebuilt.
- PLAN keeps the Earth (R00-R02) for the tau in R03; MOON and TGET overwrite R03, so
  the cache is recomputed after them.
- PHAS scratch moved to R30-R33 R51 R53 R56 R57; screens call PHA2 after SUNA.
- PLN3 (screens): mean Keplerian elements (Standish 1800-2050) give a quick GHA/Dec
  (Hc error < 0.15 deg). Hc <= -1 deg: skip the series (49 % of cases, never a visible
  planet in 6,000 tests). Else one series pass with light time from the quick distance
  (differs from the two-pass PLN2 by 0.0002'). `c47astro.planet_quick`, `planet(s, p, lt)`.
- Steps before -> after (series): ALMT 81k -> 28k, ALMF 100k -> 48k, HALMV 110k -> 57k.

## Time on the calculator

TVEC (tools/tests_calc) measured about 5.8 ms per COS at 34 digits and about 0.17 ms per
other step, so time is counted in trig functions. /tmp-style estimate: steps*0.17 ms +
(trig + vector elements)*5.8 ms. Caches: HZS/HZC (HCZI), EQC/EQS/EQCH/EQSH (HCZQ/HCZR),
SZE SZZ SSTH SCTH SSE0 SCE0 SSEP SCEP SEK SPI (SUNA LBL 15), PQX PQY PQZ PQK (PLAN LBL 48),
vectors SV1 SV2 (SERT), MA10 MS10 MC10 MA7 MS7 (MOON LBL 20). Equator dots are drawn when
Hc > 1E-4 deg (C47 and Python) so the rotated LHA cannot flip a dot at Hc = 0.
Series matrices: rows [A tau^0, A tau^1, A tau^2, B, C], row 1 = header (VL: JD range in
columns 4-5). Moon tables: [d m mp f, sin coeff |m| = 0 1 2, cos coeff |m| = 0 1 2].
The simulator (python/c47sim.py) implements RCL of a named matrix, matrix x matrix,
matrix + matrix, COS/SIN of a matrix, DOT and X≠Y?.

## FULL and FAST series

Series matrices: row 1 = [terms, 0, 0, 0], then (30+k, A, B, C); SER reads the count.
FAST (MATF, `tools/almanac/fastseries.py START YEARS`): each Earth/planet series fitted to
the FULL series over the period (+-1 year margin) with 1, tau, tau^2 and the periodic terms
in order of size, tolerance 0.02' (distances: 0.02' seen from the Earth). VL header holds
the first and end JD; outside it SUNA sets flag 12 and the screens show X.
Python: `c47astro.use_series(json)`; tests: `test_parity.py N seed F`, `test_body.py N seed F`.

## Methods and accuracy

- Sun: VSOP87D Earth (truncated), FK5, IAU1980 nutation (10 terms), aberration.
- Stars: IAU2006 precession, proper motion, nutation, aberration.
- Moon: Meeus ch. 47 (60 + 60 terms) plus 55 correction terms fitted to JPL DE421.
  Max 0.12', 99 % under 0.07', rms 0.02'.
- Planets: VSOP87D truncated (Earth 93 terms, Venus 39, Mars 154, Jupiter 152,
  Saturn 239), light time with 2 passes, FK5, aberration, nutation. Max 0.065'.
- Validated against JPL DE421 + ERFA for 2025-2028. Check a wider range of years
  before a store release.

## Online check (PC only)

`python/native/jplcheck.py`: link "Check against JPL (online)" under the screen, menu Info, or
`c47pc.py --check`. Opens a window with every value of the C47 method (tables or series,
as on the screens) beside the JPL value and the difference, with T/S per body.
Asks JPL Horizons (DE440) for apparent geocentric RA/Dec of Sun, Moon, planets and the
Greenwich apparent sidereal time, and lists the differences with our calculations
(arcmin). JPL reads the time as UTC, we use UT1: GHA includes DUT1 (up to 0.23').
Written against the documented Horizons output; the parser was tested offline only
(JPL is not reachable from the build workspace) - confirm on first real use.

## Almanac tables (Method B)

`tools/almanac/` (generator, `tab2c47.py`), `programs/TBL.txt` (26 Sep 2026 - 31 Jan
2027), `programs/TGET.txt`. Flag 10 = tables loaded (TBL sets it; CF 10 = series).
Switch: SUNA (end, LBL 45), SUNG (SUNRISE iterations), MOO2 (sets/clears flag 11),
PLN2 (SHA = GHA - GHA Aries, HP 0). Screens show T (flag 11) or S. Python mirrors it
(`c47tables.py`, Almanac(..., tables)); `tests/test_parity.py N seed T` checks it.
Chart positions in Python use 34-digit decimals (chart_x/chart_y) like the C47, so
dots exactly on the horizon match. `tools/js/c47engine.js` lacks SF/FS? (reference only).

## Minimum calculator set

`tools/build_navfull.py` writes `build/NAVFULL.txt` (resident: NAV with 4 options, ALMF,
HALMV, ALMT, HORZ and what they call; fonts trimmed to the printed characters), `build/NAVINIT_FULL.txt` / `build/NAVINIT_FAST.txt` (matrix builders + INIT, zero elements dropped, run once and delete) and
`build/TBL.txt`. Checked in the simulator (`tests/test_navfull.py`): identical screens, HORZ frames, ALMT pages
and step counts to the full set, with and without tables. Rebuild after changing any program.
`build/NAVFULL_NOTBL.txt` is made by `no_tables()` in the same script: exact blocks are cut
(TGET, flag 10/11 hooks, the "T" letter) and the build fails if a block is not found, so a
change in SUNA/MOON/PLAN/BODY/screens around those hooks needs `no_tables()` updated.
`tests/test_notbl.py` compares it with NAVFULL view by view in the simulator (FULL and FAST).

## Ideas tried and dropped (PC version)

- Diurnal paths (parallels of declination) on the horizon charts: too busy with 9-10
  bodies. Tested on the calculator as well: +2 % to +12 % steps.
- Twilight bar above the charts: dropped.

## The phone app: Almanac 47

- Name: **Almanac 47** (store title "Almanac 47 - Celestial Nav"). No "C47", "R47",
  "SwissMicros" or "HP" in the name or icon; mention the calculator only in the
  description, with the "not affiliated" line.
- Plan: port `python/native/` to JavaScript (canvas LCD), check it pixel for pixel
  against the Python version, package with Capacitor for Android (Android Studio) and
  later iOS (needs a Mac). Fully offline, no network permission, no data collected.
- `tools/js/c47engine.js` is a JavaScript port of the RPN simulator (checked identical
  on 12 cases). It is a reference, not the app.
- Price: $0.99 from the first release (Google Play does not allow free -> paid later).
- Store and About texts: `docs/APP_STORE_TEXT.txt`, `docs/APP_ABOUT.txt`.
- Spirit: the app gives what the almanac and the sight reduction tables give (GHA,
  Dec, Hc, Zn, times). The sight, the corrections, the intercept and the plot stay with
  the navigator. It does not turn a sextant reading into a position, on purpose.
  Phones do not belong on the bridge; the About text recommends a DM42n or an R47,
  the sextant and the Nautical Almanac.

## Generators

`tools/generators/` holds the Python scripts that wrote most of the program files
(fonts, screens, Moon and planet programs, REM listings). See the README there.

## Status-bar font and sine charts (Sep 2026)

`tools/generators/mkstd.py` reads the C47 standardFont bitmaps from the C43 source
(`src/generated/rasterFontsData.c`) and writes `programs/PTXS.txt` plus
`python/native/c47fonts2.py` (the same glyphs for the Python version). Views are generated
by genf.py (ALMF, ALMS with `short`), genv.py (HALMV), genhh.py (HALMH), genh2.py
(HORZ, HORZS), genbody.py (BODY) and write straight to `programs/`. Chart rows use
`RCL "SHC"` (sin Hc kept by HCZ/HCZ0/HCZR); Python mirrors this with `Almanac.hczs`,
`chart_ys` and `sine_ticks`. The T/S/X letter is drawn last because MOO2 sets flag 11.

## Hidden program names (Sep 2026)

`build_navfull.py` writes the NAVFULL builds with every global label except NAV renamed to
N01... (`label_map`, `rename`: only LBL/XEQ/GTO, never variable names in STO/RCL/INDEX/INPUT).
Named copies go to `build/dev/src/` for the tests; `build/NAVFULL_LABELS.txt` is the table.
`tests/test_labels.py` runs every NAV option on both and compares. NAVINIT is one program
INIT with the builders as LBL 01-04.

## AGRAPH and GRMOD (Sep 2026)
- Command reference: `docs/reference/C47_Full_index.txt` (C47 team, GFDL, 04/08/2026).
- AGRAPH draws according to the graphics mode: 0 OR, 1 SET, 2 OFF, 3 XOR. The index lists the
  reserved variable GRAMOD; the C47 documentation also has the commands GRMOD (set the mode) and
  GRMOD# (recall it), which are the ones to use. `STO "GRAMOD"` had no visible effect (GMOD).
- GMOD2 sets the mode with `3 STO 03 GRMOD 03` (works whether GRMOD reads the number or the
  register) and shows GRMOD# after the drawing (VIEW would wipe the graphics).
- The reference says AGRAPH "will be redesigned and should not be used in programming".
- Tested on the C47 (GMOD2): GRMOD 3 works as XOR. Solid block XOR 'A' = inverted 'A'
  (without a frame it looks like an ant); 'A' XOR 'A' = blank; XOR on blank = normal 'A'.
- Use: white-on-black values (e.g. Sun Hc negative in the almanac) instead of an underline:
  draw a box with margin in OR, the text in XOR, then GRMOD 0 again. Recipe in programs/FONTS.txt.
- BIGA (extras/BIGA.txt, tools/generators/genbiga.py): writes an 'A' scaled x8 (40 x 56) in the
  centre, then XORs its own cell: the 'A' turns into a bug. One AGRAPH column can be up to 63
  pixels (literal must be positive in WSIZE 64).
- BIGANT (extras/BIGANT.txt): the biggest, full screen height: 'A' scaled x34 (170 x 238), each
  column drawn in 4 bands of 60 rows (one AGRAPH per band). genbiga.py simulates it for the preview.
- The fonts use the default OR mode only.

## Hc below the horizon: inverted (Sep 2026)
- ALMF, ALMS, HALMH, HALMV: a negative Hc is shown white on black instead of struck through.
  LBL 64 in each: WSIZE 16, `3 STO 32 GRMOD 32` (XOR), then 55 AGRAPH columns of 14 pixels
  (11111111111111#2) from row y-1, column HX+6 (HALMV X0+126), `0 STO 32 GRMOD 32`, WSIZE 64.
  R32 (PTXS scratch) holds the mode for GRMOD, R33 the column counter.
- c47sim.py: GRMOD and AGRAPH in XOR mode; c47screen.py: Screen.xor_box. Parity tests pass.
- Previews: docs/ALMF_sun_below.png, docs/HALMV_sun_below.png. Not yet tested on the calculator.

## Graphic menu with KEY? (Sep 2026)
- NAV (tools/generators/gennav.py): the menu is drawn with PTXS, KEY? 39 waits for a key; digit =
  (7 - row) x 3 + column - 1 for keycodes 52-54 / 62-64 / 72-74, 0 = 82 ends; the item is inverted
  (GRMOD 3) for 0.3 s, then DATE UTC LAT LON (INPUT) and the view. The PROMPT menu is gone.
- WPLS: waits for + (keycode 85). ALMF ALMS HALMV HALMH ALLSKY HANIM BODY hold with WPLS instead
  of 3 x PAUSE 99; HORZ: any key = next body, + = back. ALMT (TEXT) still uses PROMPT pages.
- PTXS has '+' now (mkstd.py). Bottom of the menu in PTXS: the key hint and the warning.
- c47sim: KEY? records a frame; no key left ends the run (StopIteration). Engine feeds HORZ keys.
- Keycodes assumed (soft keys = row 1); check on the calculator (extras/MENUG shows unknown codes).
- DATE UTC LAT LON are asked once at the start (LBL 20); LBL 21 computes JD + R"DH"/24, lat, lon
  for each view. WPLS returns on + (85), up arrow (51), down arrow (61); NAV (LBL 05) adds or
  subtracts one hour in "DH" and draws the view "VW" again. HORZ returns on + or an arrow too.
  Arrow keycodes assumed (51/61, left of 7 and 4); test_navfull checks ALMF at +0 +1 0 -1 h.

## NAV + INIT in one file, compact build (Sep 2026)
- DELP "label" deletes a program (C47 command index, DELETE menu). NAVALL_FAST / NAVCOMP_FAST:
  NAV starts with FS? 81 / XEQ "INIT" / DELP "INIT" / SF 81; NAV and INIT keep their names.
- Compact: menu 1 2 4 9 (gennav.COMPACT, one column); programs found by closure() over XEQ/GTO;
  fonts trimmed to the characters of those programs. The menu highlight is now one LBL 6d per
  item (row and column set there, LBL 41 draws the XOR box).
- c47sim: DELP recorded (c.deleted). test_navfull runs both files: INIT deleted, flag 81, views
  equal to the FAST engine. DELP on the real C47 (from a running program) still to be checked.

## Menu header and text-only build (Sep 2026)
- Menu: ALMANAC 47, VALID + variable VAL (INIT stores "2000-2050" or the FAST period), date, UT
  and DR position (from LBL 21, so the arrows' hours show). Items moved down (TOP 176, pitch 28).
  An INIT run before this change has no VAL: run INIT again or "2026-2030" STO "VAL".
- NAVTXT_FAST: NAV + ALMR + INIT. ALMR = ALMT with LBL 91 storing R20 in R50+ (STO IND 79)
  and the line break of each page stored separately; no PROMPT, no drawing. test_navfull
  checks the lines against the ALMT pages.
- Split again (Sep 28): NAV+INIT in one file (15-19 k lines) gave "invalid data" in rejig. Now
  NAVALL / NAVCOMP / NAVTXT hold NAV and the programs (NAV still runs INIT and deletes it);
  INIT is loaded from NAVINIT_FAST (or _FULL). If NAVALL still fails, the only new steps against
  NAVFULL_NOTBL are FS? 81 / XEQ "INIT" / DELP "INIT" / SF 81 at the start of NAV.
- NAVALL/NAVCOMP/NAVTXT still "invalid corrupted data" when loading. Common new steps in all
  three: DELP "INIT", XEQ "INIT" (a program not in the file), FS?/SF 81, and "" (NAVTXT).
  Now: no DELP (INIT deleted by hand), INIT called by name through R49 (XEQ IND 49), no "".
- On the C47 the arrows redrew the view but the stack came back over it when the key was
  released (holding the arrow kept the drawing). NAV now waits PAUSE 3 after an arrow before
  drawing again (LBL 08), so the release happens before the new drawing.
- Arrow: "COMPUTING +1 HOUR" / "-1 HOUR" shown with AVIEW 49 before PAUSE 3, so the key release
  shows that message instead of the bare stack; the view then clears and draws again.
- AVIEW message replaced by ants: after + or an arrow NAV clears the screen and draws 6 ants
  (10 x 14, random places, RAN#) 0.1 s apart (LBL 48/47) while the key is released, then the
  view or the menu. c47sim: RAN#.
- TEXT (3) in the graphic NAV = NAVTXT: ALMR replaces ALMT in every build (gennav.text_steps:
  R50-R78 blanked, ALMR, lines to the stack and lettered registers), then REGS and NAV ends.
  Menu: UP / DOWN change the hour (LBL 22/23, ants, menu drawn again). programs/ALMT.txt (PROMPT
  pages) stays for the PC tools; after its last page it returns (RTN).
- SKY (HORZ): the info line cycles by itself (TICKS, 3 s per body; KEY? polled: other key = next,
  + / arrows = back to NAV); R/S stopped the program. UT top right (PHMS, row 227, col 336),
  DR position in the small font under it (row 215, minutes rounded). Python horz() the same.
- Any key now leaves a view (WPLS returns on every key, SKY too): NAV LBL 05 draws the same
  view again for keys other than + and the arrows (the release would leave the stack there);
  other keys on the menu draw the menu again (LBL 26). c47sim: keyskip = KEY? without a key goes
  on (SKY's timed loop), a frame each time the screen changed.
- KEYTEST on the C47 (Sep 28): KT1 (KEY? loop, keys ignored) - the stack comes back when the
  key is released; KT2 (PAUSE only, key pressed during the pause) - the band stays. So the redraw
  comes with a key caught by KEY? (on its release), not with every key. Hence NAV: after KEY?
  a pause (with the ants) for the release, then draw again.
- Real C47: after the last INPUT (LON) a key had to be pressed before the menu showed. NAV now
  waits PAUSE 3 after the inputs (the R/S release), then draws the menu. KEYTEST KT3 logs the
  key codes KEY? returns (R01-R08) and TICKS (R11-R18), to compare hardware and simulator.
- Real C47 (KEYTEST again, Sep 28 evening): KT1 shows the stack until a key is pressed, then the
  band; KT2 shows the band, a key during PAUSE ends it (stack). So on the hardware the screen is
  sent to the display at a PAUSE or a key, not while a KEY? loop runs (the PC simulator of the C47
  showed it at once). Fix: PAUSE 1 after drawing, before every KEY? wait (menu, WPLS, SKY loop).
  KT4 = KT1 with PAUSE 1. c47sim: PAUSE 1 makes no frame.
- With PAUSE 1 the real C47 shows every screen and the stack does not come back on a key
  release (that was the PC simulator). Removed: the ants, the pause after the inputs and after
  the arrows, the redraw on other keys. Views wait for + / arrows (WPLS, SKY), other keys are
  ignored and the screen stays; the menu ignores other keys too.
- Sky cache (9eae8a8) reverted, then put back (the user times it on the calculator).
- Ants: 20 after + / arrows (ANTS). Menu: 3 ants walk up (R21-R26, 3 px per step, rows 24-186,
  a new column at the bottom) while KEY? waits: LBL 27 erases each (XOR again), moves, draws,
  PAUSE 1, back to KEY?. LBL 42 draws one ant, LBL 50/51 XOR on/off. docs/NAV_menu_ants.gif.
- Menu key 1-9: the highlight, then the 20 ants (XEQ 48) instead of PAUSE 3; they stay on the
  display while the view computes (no frame of their own in c47sim: PAUSE 1).
- Sky cache (tools/generators/gencache.py -> programs/CACHE.txt, in every NAV build): the views
  ALMF ALMS HALMV HALMH HORZ ALLSKY ALMR call CSUN CMOO CPLN CSTR CPHA and CNTA CRIS CTRN CSET
  CNTP instead of SUNA MOO2 PLN3 STR2 PHA2 NTWA RISE TRAN SET NTWP (build_navfull swaps the
  XEQs; the programs/ views are unchanged). CSUN compares JD, R91, R92 with the key in matrix
  ALMC (row 67); a new key runs CALC: SUNA, PHA2, MOO2, PLN3 1-4, STR2 for every star SQK
  passes (0.15643, the views' own test; the others get Hc -99), HCZ for each, all into ALMC
  (71 x 4, NAV and INIT make it). CSUN then restores R73 R77 R80 R81 and flag 12 (flag 11 in
  CMOO), what the views, SQK and HORZ read after SUNA. Sun times: own key (noon JD, lat, lon).
  Simulator: ALMF 38,500 steps with a new time (29,500 before), 24,700 from the cache. Steps
  are mostly the fonts (AGRAPH); the series steps (matrix COS / DOT) are few but slow on the
  C47, so the real gain is larger than the step count says - to be timed on the calculator.
  c47sim: STOEL keeps the Decimal (the C47 real matrix keeps 34 digits; the key compare is exact).
- Sky cache, native matrix version: STOSEQ / RCLSEQ / J- / I+ (c47sim has them), rows read Dec
  then J- GHA so the stack is right without variables. Also cached: SQK -> CSQK (1/0) and HCZ ->
  CHCZ (Hc Zn R96 R97, SHC = SIN Hc from the row last read, KR; other inputs go to the real HCZ).
  Stars are lazy: CALC marks them -98; CSQK computes a star (SQK, STR2, HCZ) the first time a
  view asks; -99 = below. Rows 71-73 restore what SQK and STR2 read after SUNA (R54 R66 R73 R74
  R77 R80 R81, SCTH SPI SSTH SZE SZZ). Trig + series matrix ops per screen (simulator):
  ALMF 787 before -> 798 at a new time, 13 from the cache; HALMV 858 -> 258 (the chart's
  equator dots); ALMS 549 -> 8; HORZ 961 -> 378. AGRAPH (the fonts) unchanged.
- Walking ants on the menu removed (user); the ants after a key stay (ANTS, 0.1 s each).
- NAV computes the sky before the menu (LBL 28: HCZI, CSUN, CNTA, CSQK for every star) after
  the inputs and after a menu arrow; the views then only read the cache.
- tools/navopt.py (NAV builds only; programs/ stay the reference): fonts - a column equal to
  the one just drawn is only AGRAPH 32 (99 of 376 PTXS columns); PHLS of 400 px = one PIXEL
  with a negative row; PDTS and SDAT with J→ⅅℸ DAY MONTH YEAR; STXT appends numbers with αIP
  and separators with x→α into R38 once the string exists (the first piece still via the digit
  labels: no "" string). NAV's date: x→ⅅ ⅅ→J (JD 0 h = JDN - 0.5), date format YYYY-MM-DD.
- ALMR (TEXT view): no CWID pixel widths and no padding to PROMPT pixel columns (REGS shows one
  register per line): CWID is no longer in NAVTXT.
- CEQQ / CEQR: the charts' celestial equator dots (HCZQ/HCZR) cached in ALMQ 300 x 3 (Hc, sin Hc,
  Zn): rows 1-120 step 3 (CHART SPLIT ALLSKY), 121-300 step 2 (SKY); key lat, lon, start per step.
- Simulator steps from the cache (before -> now): ALMF 24,200 -> 22,200; ALMR 19,400 -> 11,700;
  HALMV 29,000 -> 25,400; HORZ 40,600 -> 37,000 (incl. its timed wait); menu -2,400 (lines).
- extras/NATTEST.txt checks x→ⅅ ⅅ→J J→ⅅℸ DAY MONTH YEAR αIP x→α on the calculator (REGS).
  c47sim implements them (x→ⅅ reads YYYY.MMDD).
- Checked on the calculator (Sep 2026): NATTEST OK (x→ⅅ ⅅ→J J→ⅅℸ DAY MONTH YEAR αIP x→α).
  AGRAPH with a stack register works: after pattern R↓ the pattern is in D on the default
  8-level stack (T was 0: "Invalid input data"). rejig writes stack registers by name only
  ("AGRAPH D"; ST.T / ST T do not load, 103 became the variable "g").
- Fonts in the NAV builds: pattern R↓ AGRAPH D (3 steps) and AGRAPH D for a repeated column.
  NAV saves the stack size (SSIZE# -> "SSZ"), sets SSIZE8, and puts SSIZE4 back on 0 / TEXT
  (LBL 08). c47sim (4 levels) reads AGRAPH D from T, the same value after R↓.
  ALMF from the cache 22,200 -> 20,000 steps.
- Ants off by default (easter egg): ANTS = 0 in gennav.py, the step after LBL 48 in NAV
  (line 431 NAVFULL / NAVFULL_NOTBL, 438 NAVALL, 292 NAVCOMP). LBL 48 returns at once for 0
  (X=0? RTN); any other number = that many ants, 0.1 s each, after a number, + or an arrow.
  The menu highlight gets its own PAUSE 1 so it shows while the view computes.
- Docs (Sep 29): manual rebuilt (tools/generators/build_manual.py + manual_nav.py -> docs/):
  part 1 NAV, the menu, the views with current screens (c47pc --plain --no-bezel), speed notes,
  the N-label map of NAVFULL without the font routines; part 2 the programs (PTXS names, WPLS).
  PROGRAM_MAP.txt from tools/progmap.py. annot.py: anchors for the current ALMF/HALMV/NAV,
  skips the licence files. c47pc 1.3 (help: Hc white on black).
- Inputs: PROMPT with the format ("DATE YYYY.MMDD", "UT HH.MMSS", "LAT DD.MMm  S -",
  "LON DDD.MMm  W -", text in R38) and the value in use recalled into X (R/S keeps it); flag 82
  = the four variables exist (the first NAV stores 0 in them). 0 on the menu: CLLCD, stack size
  back, CLSTK. TEXT: stack size back before the lines go onto the stack (it pushed onto them).
  Tests set flag 82 and answer the four prompts with None.
- Inputs back to INPUT (the PROMPT version is gone, no flag 82); before them AVIEW 38 shows the
  formats in the message line: "DATE YYYY.MMDD  UT HH.MMSS  LAT DD.MMm  LON DDD.MMm  S W -".
- Busy box (LBL 52, BUSY = 'SINKING....ABOUT', the internet joke): 180 x 30 px in the middle,
  cleared with GRMOD 2 (OFF, c47sim has it), double frame, PTXS text, PAUSE 1; it stays on the
  display while the calculator works. LBL 48 = the box, then the ants (count = the step after
  LBL 48, 0 by default). Shown after LON (CLLCD first), after a menu number, + and the arrows.
  docs/NAV_busy_box.png.
- Menu: BODY removed from the NAV builds (programs/BODY.txt and the PC version keep it);
  7 ANIM, 8 ALLSKY, 9 INFO (LBL 18 in NAV: repository, copyright, GPL, no warranty, cross-check,
  the ants hint; held by WPLS). CWID no longer in the NAV builds. Compact: 1 2 4 8 9.
  NAVFULL 12,951 -> 11,825 lines.
- Ants: flag 47 set (SF 47) gives ANTS_FLAG = 20 ants without editing NAV (LBL 48: 0, FS? 47, 20,
  STO 49); the step after LBL 48 still works too. INFO says only THE ANTS ARE WAITING FOR A FLAG.
- Estimate, if the firmware could print text on the graphics screen (only the symbols and the
  ants kept as AGRAPH): the fonts are 2,284 of 11,828 NAVFULL lines (symbols about 290), so
  about 1,950 lines less; font steps per screen from the cache: ALMF 89 %, ALMS 89 %, HALMH 59 %,
  HALMV 42 %, ALLSKY 35 % -> ALMF about 5 times faster, the chart views 1.4-1.7 times.
- Screen update (Sep 29), C47 and Free42:
  C47: the screen goes to the LCD only at a PAUSE, a key press or the end (not in a KEY? loop).
  PAUSE 0 (the reference allows 0-98 ticks) does it with no wait: tested on the C47 by Victor
  (build/test/NAVFULL_NOTBL_P0 on branch pause0-test), faster, the SINKING box stays. NAV now
  uses PAUSE 0 everywhere a screen is shown (gennav SHOW, genh2/HORZ, WPLS); the ants keep
  PAUSE 1 (walking speed). c47sim: PAUSE 0 is a display update like PAUSE 1 (no frame).
  C47_Full_index.txt has no RefLCD-like command; it says AGRAPH "will be redesigned and should
  not be used in programming" - NAV depends on AGRAPH: check it after firmware updates.
  Free42 (DM42 / DM42n stock firmware): AGRAPH and PIXEL call flush_display(), the DM42 layer
  puts every drawing on the LCD at once -> the screen builds up; the box is cleared by the
  next view's CLLCD at once. RefLCD (DM42 virtual variable): 0 = no LCD refresh, -1 = one
  refresh, 7 = normal. tools/build_free42.py rlcd -> NAVFULL_F42_RLCD: RefLCD 0 in NAV, RF
  (-1 STO "RefLCD", FUNC 00) where the C47 has PAUSE 0 / 1, before key waits (menu, WPLS) and at
  the start of the pauses (Wn), RefLCD 7 at the end. f42run models RefLCD: lcd FILE, film
  PREFIX N (a capture every N x 1024 steps): the normal build shows 44 screens during a menu ->
  CHART change, the RLCD build 3 (menu, highlight, box) and then the finished chart.
  Free42 on a PC / phone: 131 x 16 only (graphics_mode() is 0 outside the ARM build), so only
  the top left of the 400 x 240 screen is drawn; Plus42 has SETDS but no GrMod.
- Builds reorganized (Sep 30): build/ keeps NAVFULL (all views + TBL option, for more RAM
  later), NAVTXT, NAVINIT_FULL, NAVINIT_FAST, TBL; build/dev/ NAVFULL_NOTBL, NAVALL,
  NAVCOMP, TBL_OCT2026; build/dm42/ NAVLITTLE (was NAV1_DM42) + NAVINIT_LITTLE (was
  NAVINIT_DM42), the rest in build/dm42/dev/; build/free42/ NAVFULL (was NAVFULL_F42_RLCD),
  NAVLITTLE (new), NAVINIT_FULL / _FAST / _LITTLE, dev/NAVFULL_DRAW (was NAVFULL_F42);
  DEMOALM to extras/. Every dev/src/ holds the builds with the original label names.
  Short labels: fixed maps tools/labels/<build>.map (F42_* for Free42), read by the builds;
  fixed_map() in build_navfull.py gives a new routine the next free number, never reuses one.
  The maps were written from the v1.1.0 builds, so the labels did not change.
- NAVTXT reads TBL (Sep 30): built from the table programs (TGET, the hooks in SUNA / MOON /
  PLAN, the T letter), no longer from no_tables(); TGET is N59 in NAVTXT.map. Checked in the
  simulator (test_navfull.py): with TBL the page equals ALMT with TBL, T after ARIES, about
  15 % fewer steps; without TBL the page equals the series.
- Free42 NAVLITTLE (Sep 30): nav_little() converts the DM42 NAV1 (build_dm42.nav1_program)
  as nav() does for the menu NAV (SIZE 100, GrMod 3 / 0, RefLCD 0 / 7, INPUT); the fonts: PTXB
  glyphs as AGRAPH strings - its '@' (the Sun) starts 2 rows below the base line (RCL 31 2 -,
  WSIZE 12): glyph_columns records it (YOFF) and font() shifts every glyph up 2 rows.
  tests/test_f42_little.py: f42run against c47sim, 3 dates / places (south, west), start,
  +1 h, -1 h: identical. f42run "num": a leading - is now keyed as +/- after the digits (before,
  +/- negated the old X and the number was entered positive).
- ATEXT (Sep 30, announced for the C47): c47sim draws it with python/stdfont.py (standardFont from
  the C43 source rasterFontsData.c; widths checked to the pixel on the ATEXTing screen). Found on
  that screen: every glyph box 20 rows (4 below the base line), CR = 20 rows down at the start
  column, a glyph past x 400 goes to the next line, after the text x > 380 = next line, below the
  bottom the returned Y is 0, and a negative Y is drawn at -Y (the V test). 15 + 6 pixels differ
  out of 12,656 (single dots). c47sim also got DROP and GRMOD without a register (mode from X).
- ATEXT from the C47 source (screen.c fnAText / _doShowString, Sep 30): after each character a
  while loop takes every CR (U+21B5, code 0xA1B5) or LF that follows: several CRs, also "↵↵", each
  go one line down. A CR as the FIRST character is not checked by that loop: it is drawn as a
  character. Wrap only when x > 380 and the next character would pass 400. X and Y are used as
  |X| |Y|, and ATEXT adds the offset to the next position to X and Y (a negative one grows in
  magnitude). c47sim follows this code now; C64_ATEXT no longer starts a string with a CR.
- Tables for 1 and 5 years (Sep 30): c47_almanac_generator.py 2026-10-01 2031-10-02 (55 s) ->
  tools/almanac/tables_2026-10_2031-09.csv; build_navfull.tables() writes build/TBL_1.txt (8,441
  numbers, 25,364 lines) and TBL_5.txt (41,882 numbers, 125,687 lines); build/TBL.txt (4 months)
  is now build/dev/TBL_4M.txt (the tests). All NAV builds read the tables when loaded: the DM42 /
  NAVLITTLE builds now include TGET, and their SUNA sets flag 11 itself (no Moon there: T for the
  Sun from the tables); the Free42 builds include TGET, flag 11 -> 91 (HP-42S 11 = auto-exec).
  Free42 TBL_1.raw 97 KB, TBL_5.raw 481 KB; f42run imports TBL_5.raw and runs it in 0.4 s.
  tests/test_f42_tables.py: NAVFULL and NAVLITTLE, Free42 = C47 pixel for pixel with TBL_1 and
  TBL_5; with the tables the values match the FULL series to 0.1' (one digit here and there).
  C47: TBL_1 as .p47 is 111 KB of program plus 135 KB of matrices: it does not fit in 256 KiB.
- build_free42.py: raw_files() was defined after the __main__ block (NameError when run).


## Sep 30, 2026 - DEMOATX aligned, Didier's N03 trick

- On the calculator the one-string-per-line DEMOATX did not line up: the standardFont is
  proportional (N 11 px, S 10, names of any width; digits and the space 8 px). Now every column
  is its own ATEXT at a fixed x, through LBL 98 = the N03 trick of Didier (dlachieze):
  ⇄ zyxt, 4, -, x<>y, ATEXT Z. DEMOATX 670 steps, DEMOATXS 1,282.
- c47sim: ATEXT with a stack register (ATEXT Z) and the shuffle ⇄ (⇄ zyxt).
- For rejig (no ATEXT yet): the only ATEXT is in LBL 98; convert a copy with VIEW Z there.
