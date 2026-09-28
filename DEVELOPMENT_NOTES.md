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
- Below the horizon (Hc < 0, in practice only the Sun): Hc underlined in ALMF/HALMV,
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
Named copies go to `build/dev/` for the tests; `build/NAVFULL_LABELS.txt` is the table.
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
