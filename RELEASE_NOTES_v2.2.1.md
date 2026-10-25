# Almanac 47 v2.2.1

A small release on top of v2.2.0 "Struct on Attack". The pages and the results are those of v2.2.0 (C47 / R47, old
DM42) and v2.1.0 (Free42), pixel for pixel. What changes is what the programs leave behind when they end.

## Your stack is kept (the trick from the SwissMicros forum)

Every program now gives you back your stack and LASTx when it ends.

- **C47 / R47, DM42n and the old DM42 with the C47 firmware.** This uses the trick shared on the SwissMicros
  forum. At the start, `LocR 9` allocates nine local registers, `STOS R.00` stores the whole 8-level stack
  (X … D) in R.00–R.07, and `RCL L` / `STO R.08` keeps LASTx. At the end, `RCL R.08` / `STO L` and `RCLS R.00`
  put everything back. The local registers go away with the program's RTN. Each save or restore is one step,
  where v2.2.0 used eight STO / R↓ or RCL. NAVLITTLE on the old DM42 does the same with `LocR 45`: R.00–R.35 hold
  your registers, R.36–R.43 the stack and R.44 LASTx.
- **Free42 (DM42 / DM42n stock firmware, Free42 / Plus42).** Free42 has no STOS and no local registers. X, Y, Z,
  T and LASTX are saved in the variables S7X … S7L at the start. At the end they are put back with `STO ST L` and
  four RCL, and the variables are deleted. This covers the 4-level HP-42S stack.

## ALMA47 (C47 / R47)

- **Keys 1–8 on ALMANAC and SPLIT pick a body of the table** (1 is the Sun). ALMA47 ends with that body on your
  stack: Z its text (`SUN Zn 216.7 Hc 54 11.6`), Y Zn and X Hc in decimal degrees, ready for a sight reduction.
  Your own stack sits above them.
- **Registers:** ALMA47 uses only R07–R98 and clears only those when it ends (`R-CLR 7.92`). R00–R06 and R99
  stay yours. v2.2.0 cleared every register.

## MOON47 (C47 / R47, old DM42)

- Your stack and LASTx are kept.
- MOON47 uses R07–R65 and clears only those (`R-CLR 7.59`). R00–R06 and R66–R99 stay yours.

## Which zip

| Calculator | Zip |
|---|---|
| C47, R47, DM42n with the C47 firmware | `Almanac47_C47_R47_v2.2.1.zip`: ALMA47, NAVINIT_FAST / _FULL (v2.2.0's), MOON47 |
| Old DM42 (64 KiB) with the C47 firmware, packages 1–3 | `Almanac47_DM42_C47firmware_v2.2.1.zip`: NAVLITTLE, NAVINIT_LITTLE, MOON47 |
| DM42 / DM42n with the stock firmware, Free42, Plus42 | `Almanac47_Free42_DM42_v2.2.1.zip`: NAVFULL (big), NAVLITTLE (tiny), MOON47, their INITs, TBL_1 / TBL_5 |

The NAVINIT programs and their matrices are unchanged. If they are already built on your calculator, load only
the new ALMA47 / NAVLITTLE / NAV and MOON47.

## Tested

- C47 simulator: every view of ALMA47 is pixel for pixel v2.2.0 at 16 dates and places, with FULL and FAST.
  The stack and LASTx come back; R00–R06 and R99 are kept and R07–R98 cleared. Keys 1–8 give the bodies of the
  PC almanac. MOON47 was checked at 16 dates and time zones, north and south. Test: `tests/test_struct_src.py`.
- Old DM42: NAVLITTLE is pixel for pixel v2.1.0 at 16 dates and places, with the stack and your registers back.
  MOON47 stays within the 10 IF / DO / REPEAT a program and is pixel for pixel the STRUCT MOON47.
  Test: `tests/test_struct_src.py`, dm42_221.
- Free42 core (f42run, Free42 3.3.10): NAVFULL (the menu and all six views), NAVLITTLE and MOON47 are pixel for
  pixel v2.1.0, X Y Z T and LASTX come back, and no S7 variable is left. Test: `tests/test_v221_f42.py`.
- STOS / RCLS was run on a C47 (Oct 23, 2026). These builds still need a run on the calculators: please report
  any problem.

Build: `python3 tools/build_release_v221.py` (with rejig for the .p47 files and the zips; the manuals first,
with `tools/generators/build_manual.py` and `build_port_manuals.py`).

**Does not replace the Nautical Almanac.**
