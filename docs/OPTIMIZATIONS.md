# Almanac 47 v2.0.0 — the optimizations

What changed under the hood between v1.1 and v2.0.0. Every change keeps the results the same: each page is
compared pixel for pixel with the version before (tests listed at the end).

| | v1.1 (release before v2) | v2.0.0 |
|---|---|---|
| C47 NAVFULL program | 9 694 steps, 36 603 bytes (.p47) | 8 017 steps, 31 114 bytes |
| Steps run, 6 pages (C47 simulator) | 174 129 | 160 463 (−7.8 %) |
| Numbered registers used by NAV | all 100 (yours were overwritten) | R00–R45 (46), saved and restored: yours come back |
| DM42 NAVLITTLE (C47 firmware) | 2 173 steps, 8 047 bytes, 87 registers | 2 141 steps, 7 878 bytes, R00–R29, saved and restored |
| Free42 NAVFULL | 11 553 steps, .raw 35 457 bytes, SIZE 100 | 9 244 steps, .raw 28 396 bytes, SIZE 46 while NAV runs, your REGS and SIZE back |
| Free42 NAVLITTLE | 3 066 steps, .raw 9 106 bytes, SIZE 100 | 2 923 steps, .raw 8 699 bytes, SIZE 30 while NAV runs |

The menu changed too: 1 ALMANAC, 2 SPLIT, 3 SKY, 4 ANIM, 5 ALLSKY, 6 INFO, 9 SNAP (PRLCD on Free42), 0 END,
↑↓ ±1 HOUR. CHART and TEXT are gone (NAVTXT is not in v2.0.0).

## 1. The calculations (the engine: SUNA, STAR, MOON, PLAN, CHZ)

`tools/navopt_engine.py` rewrites the engine routines as exact blocks; `tools/build_navopt.py` builds the files
with them. Steps run per routine against v1.1: −29 % to −57 %.

* **Horner's method for every polynomial.** A polynomial in T (or τ = T/10) is evaluated as
  `((c4 T + c3) T + c2) T + c1) T + c0` with `RCL×` and `+`: no powers, no `Y↑X`, one register.
  This covers the mean elements of the Moon and the planets, precession (ζ, z, θ), the eccentricity, the
  obliquity, sidereal time, and the series of the Sun and the planets. VSOP87 is Σ A cos(B + Cτ) τᵏ:
  the terms of each power k are summed first (SER), then the powers are combined by Horner.
* **n-vectors.** A direction is kept as its unit vector (cos φ cos λ, cos φ sin λ, sin φ), and a rotation of
  the frame is a turn in one coordinate plane: `→POL` (angle and length in that plane), add the rotation
  angle, `→REC`. On the C47 `→REC` gives the sine and the cosine of an angle together. This covers ecliptic →
  equator (SUNA, MOO2, PLN2, SUNF, MOOQ, PLNQ), the precession of the stars (three turns: ζ, θ, z), the star
  to the ecliptic and back, the planets' L B R → x y z, and HCZ: the body's vector in the observer's meridian
  frame (cos δ cos LHA, cos δ sin LHA, sin δ), one turn by the latitude, then Hc = asin(up), Zn from the north
  and east components. No SIN / COS / TAN / ASIN formula pairs, no stored sines and cosines.
* **Nutation as matrix products.** The nutation loop (10 terms, 420 steps) becomes two matrix products, like the
  Moon series: NU × [D M M' F Ω …] → SIN / COS of the 10 arguments, then DOT with the amplitudes S0 + S1 T
  (Horner) for Δψ and Δε.
* **The sky cache keeps θ and ε₀** (sidereal time and mean obliquity), so the views do not compute them again.
* **The loops on ISG** (`tools/navhopt.py`, `loops`). The horizon and sky sweeps of SPLIT, SKY, ANIM and ALLSKY
  counted by hand: `s STO+ r`, `f`, `RCL r`, `X≤Y?`, `GTO` (6 steps per pass). Now they are `ISG r`,
  `GTO` with a control number `0.fffss`: 2 steps per pass, 2–4.5 % fewer steps per page.

## 2. The registers (`tools/regalloc.py`)

v1.1 NAVFULL used every numbered register. Each routine had its own fixed numbers, so values that are never
needed at the same time still took different registers. v2 renumbers them automatically:

1. **Flow.** One node per program line; `GTO`, the skip after a test, `XEQ` (a call with the callee's
   summary), `XEQ IND` tables (k + `STO r` / `XEQ IND r`: the run of labels from k) and `RTN` back to the callers.
2. **Summaries.** For every routine, MUST (registers written on every path to its RTN; a call kills them) and
   USE (registers it may read before writing them).
3. **Liveness per register.** At a routine's RTN, live = what is live after any of its calls, so the routine's
   temporaries never take the register of a value its caller keeps across the call.
4. **Webs.** Reaching definitions join every read with the writes that can reach it. One web is one value,
   whatever its old register number, and a web can get a different number from the other webs of its old register.
5. **Fresh entries.** NAV and the six pages read no register before writing it (checked in the simulator), so no
   value flows into them. Without this, a read behind a data test (HANIM erases the text of the frame before)
   looks live all the way back to the start of NAV.
6. **Colouring.** Two webs conflict when one is written while the other is live. DSatur colours the conflict
   graph; the colour is the new register number.

Result: NAVFULL needs **46 registers (R00–R45)**, NAVLITTLE **30** (R00–R29). The floor is set by ANIM: HANIM keeps 9
values while MOON runs with the Sun's results and TGET (the tables lookup) its 13 temporaries.

**Your registers are kept:**

* **C47 / DM42:** at the start NAV does `LocR 46` and `RCL 00`, `STO R.00`, … `RCL 45`, `STO R.45` (into its
  own local registers). When NAV ends (key 0) it copies them back. That is 92 steps once per session; the pages
  are not slower (±0 %).
* **Free42 / DM42 stock firmware:** `RCL "REGS"`, `STO "NBAK"` (the whole register matrix) before `SIZE 46`,
  and `RCL "NBAK"`, `STO "REGS"` at the end. STO "REGS" gives the SIZE back too. Flag 25 guards both, so a
  calculator with SIZE 0 does not stop NAV.
* **If NAV is interrupted** (EXIT, R/S, an error) the restore does not run: R00–R45 keep NAV's values.

**Not in v2.0.0:** local registers inside every routine (LocR per call) and hidden labels behind dispatch
entries (one visible entry per program, `GTO IND X`). They are in build/dev/hopt/ (NAVFULL_LOCR, _LOCR_SEQ):
33 global registers and 45 visible labels, but each `LocR` allocates memory on every call (54 per page in
the simulator) and is still untested on the real calculator.

## 3. The input prompts

At each `INPUT` the stack is cleared, and Y holds only the format of that input: `DATE YYYY.MMDD` (or
`DD.MMYYYY` / `MM.DDYYYY`, following the calculator), `UT HH.MMSS`, `LAT DD.MMm  S -`, `LON DDD.MMm  W -`.
In v1.1 the stack showed 999 (from the start of NAV), the long format text of all four inputs (cut on the
screen), and the inputs before.

## 4. Firmware facts found on the way (C47 master b8707a818)

* `KEY?` refuses a local register ("out of range", fnKey). NAV's key register stays global.
* `RCL "name"` of a missing variable stops a program even with IGN1ER set (_executeOp does not look at
  IGN1ER). `0`, `STO+ "name"` creates a missing variable with 0, because STO+ may make a new variable
  (isFunctionAllowingNewVariable). MOON47 now uses this for TZ (branch fix-moon47-tz).
* `GRMOD r` is written by rejig as `GRMOD` and the number r: GRMOD takes X, and the number lands on the stack.
  Harmless where it is used (X already holds the mode); MOON47's local build writes `GRMOD` alone.
* A second `LocR` on the same level keeps the values and only resizes (allocateLocalRegisters). Every `XEQ`,
  even to a local label, starts a new level with no local registers. `RTN` after a `GTO` returns to the last
  `XEQ`, or ends the program.
* Indirect addressing never reaches a local register (values address globals, the stack, lettered registers
  and named variables).
* A long text shown with AVIEW on firmware before 2 Oct 2026 can show the not-found glyph box (fixed in master
  1051962f2). v2 has no AVIEW in the prompts.
* Free42: numeric labels are 00–99, and `^` is character 30 there. The Free42 PTXS gets ↑ ↓ ± as glyphs 91 `[`,
  95 `_`, 96 `` ` `` from the C47 standard font, so the Free42 menu matches the C47 one pixel for pixel.

## 5. The Python versions

`python/nav.py` (NumWorks, HP Prime) and `python/native/c47astro.py` (the reference the tests draw with):

* **Horner in the series:** `_ser` sums the terms of each power of τ, then combines the powers by Horner, as the
  C47 SER does, with no `tau ** k` per term (the same values to 2 × 10⁻¹³).
* **The observer's n-vector:** `nav.hcz` keeps the sine and cosine of the latitude from the last call (one place,
  many bodies), as the C47 HCZI.
* The full n-vector form brings nothing in Python: there is no `→REC` that gives a sine and a cosine in one step.

## 6. How it was tested

* `tests/test_v2.py`: C47 NAVFULL v2 against the release before it (branch main), every page they share, pixel
  for pixel (FULL, FAST, tables), every register R00–R99 kept, a clear stack; DM42 NAVLITTLE the same; Free42
  NAVFULL and NAVLITTLE against the C47 screens (f42run); Free42 SIZE 25 and R00–R24 the same after NAV.
* `tests/test_navopt.py` (engine values against v1.1, every routine) and `tests/test_navhopt.py` (OPT / HOPT /
  RSAVE / LOCR, registers kept).
* The C47 firmware itself: the PC simulator built from master (headless, `--script`), every page of NAV with
  no error and all 100 registers kept; the input prompts captured from its screen.
* `python3 tools/c47check.py`: every step is a C47 command allowed in programs.

## 7. After v2.0.0: the same calculation, faster and smaller (`tools/navmat.py`, branch safe-opt)

Every hour is still computed in full, as in v2.0.0 (the hour stepping of the series, tried on branch
c47-matrix, was slower on the calculator). `tools/build_v2.py` applies the passes; `ALM_PASSES=deg,tget,...`
builds a subset for measurements.

**The calculation** (on the named listing, before `regalloc` renumbers the registers):

| pass | what | C47 | Free42 |
|---|---|---|---|
| deg | `rad→deg` (`→DEG`) in place of `× 57.29577…` (an 18-byte number); the Moon's parallax factor `358473400 × 6378.14 ÷` as one number | yes | `→DEG` only |
| ceq | the equator dots of the charts on whole complex vectors, 30 at a time (`EQ2` / `EQ3` in place of `ALMQ` and its element reads) | yes | no: Free42 makes no element copies |
| tget | the tables: T₀…Tₙ₋₁ once per call, each quantity one `M.GETM` (`GETM`) and a `DOT` | yes | yes |
| hcz | Hc and Zn from the body's direction vector: 2 trigonometric functions in place of HCZ's 6 | yes | yes |
| margs | the arguments of a Moon series (`ML × MA10`) once for its SIN and COS sums | yes | yes |
| cexp | the cos and sin of a series' whole argument vector as one complex `eˣ(i A)`, then `Re` / `Im` | yes | no: no `Re` / `Im`, 4-level stack |
| views | the header of every view (date, UT, DR, latitude, longitude) and the compass row of the charts as routines `HDR`, `CMN`, `CMS` | yes | yes (`LSTO` locals) |

Why `cexp`: the C47 computes SIN and COS at 75 digits and `eˣ` at 39 (still more than the 34 a number keeps).
30 vectors of 200 elements: SIN + COS 1.05 s → 0.44 s, COS alone 0.69 s → 0.47 s; cos 60° differs by 3 × 10⁻³⁴.
The complex constants i and iπ/180 are `C1` and `C2`, made when NAV starts (`RCL×` keeps the stack depth).

**The size** (after `regalloc`):

* `strip`: no REM, no code NAV cannot reach (STAR, PLAN, CHZ, DHA, HCZ0, CTWA / CTWP, …). DHA (Hc Zn → Dec
  GHA) is a separate program (`programs/CHZ.txt`). On Free42 an `XEQ` of a routine that returns by `RTNYES` /
  `RTNNO` is a test (the SKY key wait).
* `consts`: the most used numbers (1 2 360 0 16 …) in registers after the program's own: NAV stores them after
  saving your registers (C47: `LocR 99`, R00–R98 given back; Free42: a larger `SIZE`, REGS kept in NBAK).
* `names`: NAV's own variables named a letter and a digit (V0, V1, …), the most used first; the inputs and the
  matrices of NAVINIT and the tables keep their names.
* `outline`: repeated runs of steps as local or shared subroutines (`OUTn`); never across `LocR` / `LSTO`, a
  label, a return or a test.
* NAVINIT: the planet series' phase `3.14159265359` is the firmware's π.

**MOON47** (`tools/build_moon47.py` `release()`): the 20 Moon terms as matrices (`tools/moon47_opt.py`, until
now only a dev build), on the C47 their cos and sin by one complex `eˣ`, then `strip` and `outline`. C47 5 795 →
4 836 bytes, Free42 .raw 6 837 → 6 122; the C47 firmware runs the page and two north / south switches in 966 CPU
samples against 1 274 (−24 %), the same screens (`tests/test_moon47_c47.py`, `_f42.py`, and the firmware).

**Results** (bytes; C47 free memory after INIT and a NAV run, `MEM#`):

| | v2.0.0 | safe-opt | c47-size (hour stepping) |
|---|---|---|---|
| C47 NAVFULL | 31 098 | 24 160 | 28 948 |
| DM42 NAVLITTLE | 7 950 | 7 173 | 7 982 |
| Free42 NAVFULL | 28 334 | 23 321 | — |
| Free42 NAVLITTLE | 8 699 | 7 780 | — |
| C47 free memory after NAV (FULL) | 100 468 | 118 880 | 112 104 |

Speed in the C47 firmware (PC simulator, CPU samples at 4 kHz; a page is the mean of 4 visits; about ± 5 %):

| | start | ALMANAC | SPLIT | SKY | ANIM | ALLSKY | per hour |
|---|---|---|---|---|---|---|---|
| FULL v2.0.0 | 1095 | 81 | 211 | 249 | 588 | 419 | 497 |
| FULL safe-opt | 904 | 97 | 193 | 238 | 624 | 366 | 375 |
| FULL c47-size | 969 | 80 | 186 | 231 | 626 | 372 | 385 |
| FAST v2.0.0 | 887 | 100 | 238 | 256 | 642 | 449 | 368 |
| FAST safe-opt | 772 | 106 | 198 | 226 | 642 | 384 | 295 |
| FAST c47-size | 811 | 77 | 196 | 240 | 665 | 413 | 278 |

The PC simulator showed c47-matrix faster than v2.0.0, and the calculator showed it slower: the timings on the
calculator decide.

Checked: the C47 firmware pixel for pixel against v2.0.0 (NAVFULL 54 screens, NAVLITTLE 18), the ALMC cache
(292 values) the same to 7 × 10⁻¹⁷ degrees; the build's own values in the C47 firmware against JPL DE421 + ERFA
(the reference and limits of `tests/test_ephem.py`, 30 random instants each: FULL 2000–2050, FAST 2026–2030 and
the October 2026 table): all within the limits, largest Moon GHA 0.09′, planets 0.065′, stars 0.0024′, Hc / Zn
0.08′; every test suite above, Free42 against the C47 screens and SKY /
ANIM against v2.0.0, `tools/c47check.py` on master 224e5e95d.
