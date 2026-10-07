TSTRUCT: does the program's structure change the speed on the C47? (branch struct-speed-test, Oct 2026)

An outside analysis proposed restructuring Almanac 47 for speed:
  1. global labels for shared routines (found "in O(1)" from a symbol table), local labels for private ones;
  2. "proximity": the firmware scans the program step by step for a local label and wraps past END,
     so frequent routines go to the top and loops are kept physically tight;
  3. no named variables in the heavy loops, numbered or local registers instead (pack and unpack).

Where v2 already is (docs/OPTIMIZATIONS.md):
  - Registers: tools/regalloc.py renumbers every value (R00-R45, saved with LocR at the start of NAV); the
    consts pass puts the most used numbers in registers after them (LocR 99). With R00-R98 taken, NAV's other
    own values became short names (navmat.names: V0, W0, ...; 5 bytes per RCL against 7). In NAVFULL that is
    about 370 named STO/RCL, 18 of them ALMC; the series and the nutation are matrix products already.
  - Labels: 72 global (hidden as N01 ...), 526 local. NAVFULL_LOCR (local registers per routine, dispatch
    entries) was built and left out: each LocR allocates memory on every call (build/dev/hopt/).
  - Claims 1 and 2 describe an HP-42S-style search. Whether the C47 firmware searches steps or a label table
    is the open question, and the PC simulator in python/c47sim.py cannot answer it: it counts every step the
    same. Only the C47 (or the DM42n with the C47 firmware, or the firmware's PC simulator) can.

So this branch measures before anything is moved. Nothing in programs/ or build/ changes.

How to run
  1. Load NAVFULL (or NAVLITTLE on the DM42n), run NAVINIT, then load TSTRUCT (rejig TSTRUCT.txt).
  2. 3000 XEQ "TSTRUCT" (X = passes; 0 or less: 3000). Run it twice, keep the second results.
  3. Note R21-R30 (ticks, 1/10 s). Send them back with the hardware and firmware version.

  R21  near GTO forward + near GTO back       R22  the same two GTOs over 1000 steps each
  R23  XEQ local label a few steps ahead       R24  XEQ local label 1000+ steps ahead
  R25  XEQ global label (another program)
  R26  RCL 02 DROP     R27  RCL "TV0" DROP     R28  RCL R.00 DROP
  R29  STO 02          R30  STO "TV0"

Reading it (pairs run the same number of steps; ± 1 tick is noise)
  R22 ≈ R21 and R24 ≈ R23   local labels come from a table: moving routines next to their callers gains
                            nothing (claim 2 does not hold).
  R22 >> R21                the firmware scans: then reordering routines by how often they run is worth a
                            dev build (tools/build_v2.py, with a call count from the simulator's count hook).
  R25 < R23                 global calls are cheaper: then claim 1 is worth a dev build.
  R27 - R26, R30 - R29      the cost of one name per access. Multiply by the named accesses per page
                            (the simulator's count hook gives them) to see if moving V0 ... to local
                            registers could pay back the LocR it needs.

Regenerate: python3 tools/tests_calc/gen_tstruct.py
