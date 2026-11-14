# Almanac 47 v2.3.0 "Local Time"

A release on top of v2.2.1. Every time on the screens can now be shown in UT or in your local time, on every
build. On the C47 / R47 the views get a new header. The calculation and the results are those of v2.2.1.

## UT or local time on +/-

Press **+/-** (the change-sign key) on the menu or on any view: every time shown switches between UT and local
time, **LT = UT + TZ**.

- **TZ** is your time zone in hours east of Greenwich, a variable you store once: `3 STO "TZ"` for UTC+3,
  `-5 STO "TZ"` for UTC−5, `5.5` for UTC+5:30. MOON47 already used the same TZ.
- In LT the header shows the local date and time and `LT`. Rise, set, twilights and meridian passage are given
  in LT (the events of the UT day).
- The choice is the variable **TZLT** (0 UT, 1 LT). It stays for the next run.
- **Unchanged:** DATE and UTC are still asked in UT, and GHA, Dec, Hc and Zn do not change. Without TZ, the
  programs create TZ and TZLT with 0, so everything is in UT as before.

Where:

| Program | +/- | Other keys |
|---|---|---|
| ALMA47 (C47 / R47, DM42n with the C47 firmware) | on the menu and every view | as v2.2.1 |
| MOON47 (C47 / R47, old DM42, Free42) | the top line and the next phases | **0** turns to the view from the south (it was +/-) |
| NAVLITTLE (old DM42 with the C47 firmware) | redraws ALMANAC | as v2.2.1 |
| NAVFULL, NAVLITTLE (Free42: DM42 / DM42n stock firmware, Free42, Plus42) | on the menu and every view / ALMANAC | as v2.2.1 |

The PC version (`python3 python/native/c47pc.py --lt --tz 3`, key L) and the web app (its Times: UT / LT
button, key L) have the same switch.

## A new header on the C47 / R47

Every view of ALMA47 now starts with the same bar as NAV47 on the DM42n:

- the date and time on the left (UT or LT),
- the view's name in the middle, white on black (ALMANAC, SPLIT, SKY, ANIM, ALLSKY),
- the position on the right (the "DR" label is gone), and T / S at the end as before.

On the menu the position moved the same way. The old DM42 and Free42 keep their v2.2.1 header, with UT / LT.

## Which zip

| Calculator | Zip |
|---|---|
| C47, R47, DM42n with the C47 firmware | `Almanac47_C47_R47_v2.3.0.zip`: ALMA47, NAVINIT_FAST / _FULL (v2.2.0's), MOON47 |
| Old DM42 (64 KiB) with the C47 firmware, packages 1–3 | `Almanac47_DM42_C47firmware_v2.3.0.zip`: NAVLITTLE, NAVINIT_LITTLE, MOON47 |
| DM42 / DM42n with the stock firmware, Free42, Plus42 | `Almanac47_Free42_DM42_v2.3.0.zip`: NAVFULL (big), NAVLITTLE (tiny), MOON47, their INITs, TBL_1 / TBL_5 |

The NAVINIT programs and their matrices are unchanged. If they are already built on your calculator, load only
the new ALMA47 / NAVLITTLE / NAV and MOON47.

## Tested

- C47 simulator: every screen of ALMA47 is pixel for pixel v2.2.0, except the header, which is checked pixel for
  pixel too (the old position moved 42 columns, DR gone, the name box), at dates and places from 2000 to 2050.
  In LT the header and the sun times are those of the PC version; +/- on the menu and on the views. MOON47 in UT
  and LT, north and south. Test: `tests/test_struct_src.py` (pages, places, times, moon_next).
- Old DM42: NAVLITTLE in LT against the PC version, +/- switching. Test: `tests/test_struct_src.py`, dm42_221.
- Free42 core (f42run, Free42 3.3.10): NAVFULL's ALMANAC, SPLIT and ALLSKY in LT pixel for pixel the PC version,
  INFO as in UT, +/- on the menu and on a view, TZLT kept, and UT without TZ; NAVLITTLE the same; MOON47 north,
  south and LT. Tests: `tests/test_next_f42.py`, `tests/test_moon47_f42.py`.
- The web app and the PC version: `tests/test_web_calc.py` (identical in UT and LT).
- These builds still need a run on the calculators: please report any problem.

Build: `python3 tools/build_release_v230.py` (with rejig for the .p47 files and the zips; the manuals first,
with `tools/generators/build_manual.py` and `build_port_manuals.py`).

**Does not replace the Nautical Almanac.**
