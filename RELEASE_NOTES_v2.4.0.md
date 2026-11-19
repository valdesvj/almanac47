# Almanac 47 v2.4.0 "Here and Now"

A release on top of v2.3.0 "Local Time". The programs now start from the calculator's own clock: press R/S at
each prompt and you get the sky now, where you are. On every build. The calculation, the screens and the keys
are those of v2.3.0.

## Five prompts, all with a default

`XEQ "ALMA47"` (or `XEQ "NAV"` on Free42) asks five values. **R/S keeps the value shown**:

| Prompt | The value shown | You type |
|---|---|---|
| **TZ** (new, first) | your last one; 0 the first time | the hours of your clock from UT, east +, west −: `-5` Colombia, `3` UTC+3, `5.5` India |
| **DATE** | the calculator's date **as UT** (the clock − TZ; the day before or after when UT is on another day) | another UT date |
| **UTC** | the calculator's time as UT, HH.MMSS | another UT time |
| **LAT** | your last latitude | another latitude |
| **LON** | your last longitude | another longitude |

With your TZ set once, **R/S five times = the sky now**. Set the calculator's clock (CLK menu) to your local
time. DATE and UTC are still in UT, so a sight taken at another moment is typed as before.

**Medellín:** before any position is stored, LAT and LON start at Medellín, Colombia (6° 13.9′ N, 75° 35.4′ W),
a small present from the author's town. As soon as you give your own position, the programs keep it.

TZ is the same variable as in v2.3.0: it also sets the local time of +/- (LT = UT + TZ) and MOON47's clock.

## Where

| Program | |
|---|---|
| ALMA47 (C47 / R47, DM42n with the C47 firmware) | the five prompts |
| NAVLITTLE (old DM42 with the C47 firmware) | the five prompts |
| NAVFULL, NAVLITTLE (Free42: DM42 / DM42n stock firmware, Free42, Plus42) | the five prompts; Free42's date is turned into Y.MMDD whatever your date format |
| MOON47 (every build) | unchanged: it asks nothing and reads the clock and TZ |

## Which zip

| Calculator | Zip |
|---|---|
| R47 (the arrows of the R47 keyboard) | `Almanac47_R47_v2.4.0.zip`: the same files, ALMA47 with ↑ / ↓ where the R47 has them (README_R47.txt) |
| C47, DM42n with the C47 firmware | `Almanac47_C47_R47_v2.4.0.zip`: ALMA47, NAVINIT_FAST / _FULL (v2.2.0's), MOON47 |
| Old DM42 (64 KiB) with the C47 firmware, packages 1–3 | `Almanac47_DM42_C47firmware_v2.4.0.zip`: NAVLITTLE, NAVINIT_LITTLE, MOON47 |
| DM42 / DM42n with the stock firmware, Free42, Plus42 | `Almanac47_Free42_DM42_v2.4.0.zip`: NAVFULL (big), NAVLITTLE (tiny), MOON47, their INITs, TBL_1 / TBL_5 |

The NAVINIT programs and their matrices are unchanged. If they are already built on your calculator, load only
the new ALMA47 / NAVLITTLE / NAV (and MOON47 if you like).

## Tested

- C47 firmware (PC simulator built from the firmware sources): ALMA47 and NAVLITTLE with nothing stored (the
  clock's date and UT, Medellín) and with a stored position and TZ = −5 (the position kept, UT = clock + 5 h).
- C47 simulator (python/c47sim.py): every page of ALMA47 pixel for pixel v2.3.0 at dates and places from 2000 to
  2050 (`tests/test_struct_src.py`).
- Free42 core (f42run, Free42 3.3.10): NAVFULL and NAVLITTLE with nothing stored and with stored values; the date
  formats MDY, DMY and YMD; UT on the day before and after (TZ 9, TZ −20); UT / LT as v2.3.0
  (`tests/test_next_f42.py`).
- R47 keyboard build: `tests/test_r47_keys.py`.
- These builds still need a run on the calculators: please report any problem.

Build: `python3 tools/build_release_v240.py` (with rejig for the .p47 files and the zips; the manuals first,
with `tools/generators/build_manual.py` and `build_port_manuals.py`). The R47 build is part of it.

**Does not replace the Nautical Almanac.**
