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

## Almanac conventions

- Star numbers are the Nautical Almanac numbers 1-57; 58 = Polaris (our own choice).
  The list is in decreasing SHA order, as in the almanac. `SBRT` gives them by brightness.
- Table rule (ALMF, HALMV, ALMT): 10 rows. The Sun always; then the Moon and the
  planets if Hc > 0; then the brightest stars with Hc > 10 deg until the table is full.
  HORZ shows the 5 brightest stars above 10 deg.
- Below the horizon (Hc < 0, in practice only the Sun): Hc underlined in ALMF/HALMV,
  line starts with `* ` in ALMT.
- Horizon charts: north latitude has S in the centre (N E S W N), south latitude has
  N in the centre (S W N E S), so the celestial equator is a symmetric arch.
- Times are UT (UT1). TT - UT1 = 69.2 s.
- Every screen carries "DOES NOT REPLACE THE NAUTICAL ALMANAC". The programs support
  the Nautical Almanac; they do not replace it.

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
