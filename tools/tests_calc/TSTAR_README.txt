TSTAR: the 58 stars one by one (as NAV does now) against one matrix (branch struct-opt, Oct 2026)

Why: before the menu NAV computes the stars one at a time (CSQK: SQK for every star, then STR2 and Hc/Zn for
those that can be over the horizon): about 4.2 s on the C47 at every menu, whatever NAVINIT is loaded (FULL,
FAST or the tables). tools/navmat.py notes a matrix version that was 14 % slower in the simulator (2026-10-05).
TSTAR measures a new one on the calculator, built on the firmware's matrix functions:
  - the star vectors at J2000 and J2050 once (proper motion as a straight line: within 0.0006' of STR2);
  - per time one 4 x 3 matrix: precession, nutation, the ecliptic and back, with the aberration as a 4th row;
  - two matrix products (58 x 4) x (4 x 3): GHA / Dec, and Hc / Zn in the observer's north / east / zenith frame;
  - the angles by ∡ (atan2) of complex columns, ABS for the lengths, M.GETM / M.PUTM for the columns.
It computes all 58 stars every time (NAV now leaves the stars under the horizon out, and computes the rest of them
later, when ALLSKY asks).

How to run
  1. Load NAVFULL (the release or a build of build/dev/struct: they share the registers), run NAVINIT.
  2. Save your registers if you need them: TSTAR changes R00-R98 (NAV restores them only when NAV ends).
  3. Load TSTAR (rejig TSTAR.txt). 3 XEQ "TSTAR" (X = passes; 0 or less: 3). Run it twice, keep the second.
  4. Note R21-R30 and send them back with the calculator and firmware version.

  R21  ticks (1/10 s) of A, N passes: the stars one by one, as NAV before the menu
  R22  ticks of B, N passes: all 58 stars at once with matrices
  R23  ticks of B's set-up (once; in a real build NAVINIT would keep the two vector matrices)
  R26  R27  R28  R29   largest difference A - B over the 58 stars, arcmin: GHA, Dec, Hc, Zn (should be < 0.01)
  R30  stars A computed in full in one pass (the others were under SQK's horizon test)

Firmware PC simulator (master ef39ddb, 100 passes): R21 = 51, R22 = 12, R23 = 1, R30 = 21; differences GHA 0.0017'
(Polaris), Dec 0.0006', Hc 0.00015', Zn 0.0008'. The calculator weighs trigonometry more than the PC: R22 / R21
there decides whether NAV gets the matrix stars.

Place and time: 55.2 E, 25.3 N, JD 2461318.3 (2026-10-04 19:12 UT).
Regenerate: python3 tools/tests_calc/gen_tstar.py (copies NAV's constants and CSUN's LBL 99 from build/NAVFULL.txt)
