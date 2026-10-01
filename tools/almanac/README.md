# Almanac tables (Method B, Chebyshev)

Precise GHA and Dec from JPL DE421 (ERFA, IAU 2006/2000A), for a limited period.
The series programs (SUNA, STAR, MOON, PLAN) stay the fallback and work for any date.

## 1. Make the coefficient tables (PC, internet)

    pip install numpy pyerfa jplephem==2.24 de421
    python3 c47_almanac_generator.py 2028-01-01 2029-01-01 > tables_2028.csv

`docs/C47_almanac_coefficients_2026-2027.xlsx` already holds 1 Sep 2026 - 31 Dec 2027.
TT - UT1: `DT_YEARS` (2000-2025, yearly) and `DT` (from 2025 on) in the script.

`tables_2026-10_2031-09.csv` holds 1 Oct 2026 - 1 Oct 2031 (made with DT = 69.2 s):
`python3 tools/build_navfull.py` turns it into `build/TBL_1.txt` (1 year, 8,441 numbers)
and `build/TBL_5.txt` (5 years, 41,882 numbers); `tools/build_free42.py` makes the Free42
versions (`build/free42/TBL_1.raw`, `TBL_5.raw`). DE421 ends in 2050.

### TBL_50: 2000-2050 for Free42 / Plus42 on a PC (not in the repository, about 18 MB)

Ready-made: `TBL_50.raw` and its SHA-256 are in the release
[tbl50-2000-2050](https://github.com/valdesvj/almanac47/releases/tag/tbl50-2000-2050).
To make it yourself:

    cd tools/almanac
    uv run --no-project --with numpy --with pyerfa --with "jplephem==2.24" --with de421 \
        python c47_almanac_generator.py 2000-01-01 2051-01-01 > tables_2000-2050.csv   # about 30 min
    cd ../.. && python3 tools/build_free42.py      # -> build/free42/TBL_50.txt and .raw (4.9 MB)

TT-UT1 follows the yearly values 2000-2025 in the script (`DT_YEARS`) and stays at `DT`
(69.2 s) from 2025 on. TBL_50 shows `TBL 01-01-2000 TO 31-12-2050`; its matrices need about
6.8 MB (a PC, not the DM42).

## 2. Turn a period into a C47 program

    python3 tab2c47.py 2026-09-26 2027-01-31                 # from the spreadsheet
    python3 tab2c47.py 2028-01-01 2028-03-31 --csv tables_2028.csv
    rejig TBL.txt -o TBL.p47

`programs/TBL.txt` is the current one: 26 Sep 2026 - 31 Jan 2027
(3054 numbers, 9202 lines; the Moon is 2064 of them).

## 3. On the calculator

1. Load `TBL` and run it once: `XEQ "TBL"`. It builds the matrices TSU TVE TMA TJU
   TSA TMO TAR and ends showing `TBL 26-09-2026 TO 31-01-2027`. The TBL program can
   then be deleted to free memory; the matrices stay.
2. Load `TGET` and use it: Y = JD (UT1), X = body (0 Sun, 1 Venus, 2 Mars,
   3 Jupiter, 4 Saturn, 5 Moon, 6 Aries), `XEQ "TGET"`:
   X = GHA, Y = Dec; Moon also Z = HP, T = SD (arcmin). X = -1 outside the table.

Each matrix starts with a header row: JD of the first block (0h UT1), block length
(days), number of blocks, number of terms. Then one row per block: GHA coefficients,
Dec coefficients, and for the Moon 4 HP coefficients.

Checked in the simulator (300 random times, 26 Sep 2026 - 31 Jan 2027): TGET equals a
NumPy evaluation of the spreadsheet to 0.00001'; it differs from the series by at most
0.005' (Sun), 0.023' (planets), 0.073' (Moon, the series' own error). About 265
program steps per call (Moon 400), against 2,000-12,000 for the series.

## 4. The screens use the tables automatically

With the tables loaded (flag 10, set by TBL) and the date inside the table period:
- SUNA takes the Sun's GHA/Dec and GHA Aries from the tables (the stars keep their
  series, with that GHA Aries);
- SUNG (used by the SUNRISE iterations) uses the tables and skips the series;
- MOO2 and PLN2 use the tables and set flag 11 (Moon from the tables).
Outside the period, or after CF 10, everything falls back to the series.

Every screen shows **T** (tables, flag 11) or **S** (series): ALMF and HALMV bottom
right, HORZ/HORZS bottom left, ALMT at the end of the first line. T means the Moon
and everything else except the stars came from the tables.

Program steps, series -> tables (simulator): ALMF 109,000 -> 44,000, HALMV
119,000 -> 54,000, HORZS 69,000 -> 30,000 (45-62 % fewer). Values change by at most
0.1' in the last digit (the series' own error).

TGET, SUNG and the switch need the programs TGET, TBL (run once) and the updated
SUNA, SUNRISE, MOON, PLAN and screens.

## FAST series (fastseries.py)

Not tables but a shorter formula for a few years: the Earth and planet series are fitted
to the FULL series (VSOP87) over the period with a quadratic plus the short-period terms.

    python3 fastseries.py 2026 5     # -> programs/MATF.txt and python/native/fast_series.json

Needs numpy. On the calculator: load NAVINIT_FAST and run INIT (or MATF after the FULL matrices). Each
period has its own coefficients; outside it the screens show X instead of T/S.
