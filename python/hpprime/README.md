# Almanac 47 on the HP Prime

User manual: `docs/Almanac47_HPPrime_Manual.pdf`.

Two graphic views of the C47 suite for the HP Prime (G1/G2, firmware with the Python
app, 2.1.14567 or later), drawn through the calculator's `hpprime` module:

| Script | View | C47 original |
|---|---|---|
| `almview.py` | ALMANAC page: date / UT / DR, GHA Aries, BODY GHA DEC HC ZN for the Sun and the brightest navigation stars higher than 10 deg, naut. twilight, rise/set, mer. pass, Sun SD, Moon phase and age | ALMF ("vintage" view) |
| `skyview.py` | HORIZON chart: Hc up (sine scale), Zn across, celestial equator dotted, Sun and stars with their numbers; the top line shows ZN / HC of the selected body | HORZ |
| `main.py` | starts `almview` (the file the Python app runs) | |
| `hplib.py` | text, symbols, keys, main loop | |

All the numbers come from `../nav.py` + `../navdata.py` (same methods as the C47
programs SUNA, STAR, SUNRISE, PHAS, HCZ; `nav.almanac()` / `nav.bodies()`), the same
files as the text menu (`nav.py`, option 5 prints the same page as text). There is no Moon
position and no planets in `nav.py`, so the table is the Sun plus up to 8 stars (horizon:
Sun plus 9 stars), chosen like the C47: brightest first, only those higher than 10 deg.

Previews made on a PC (see below): `docs/HPPRIME_alm.png`, `docs/HPPRIME_sky.png`
(26 Sep 2026 14:57 UT, 25 20 N 055 12 E) and `docs/HPPRIME_sky_night.png`
(23 Sep 2026 03:00 UT, 30 N 0 E).

## Copy to the calculator

The six files go into one Python app:

    nav.py  navdata.py   (from python/)
    main.py  hplib.py  almview.py  skyview.py   (from python/hpprime/)

1. On the calculator: `Apps`, select **Python**, `Save` it as a new app, e.g. `Almanac47`
   (so the original Python app stays as it is).
2. With the **HP Connectivity Kit** (calculator on USB, or the HP Prime Virtual
   Calculator): open the new app under *Application Library* and drag the six `.py` files
   into it (replace its `main.py`). If your Kit version does not accept files dropped into
   an app, open each file in the app's `Symb` view (new file, same name) and paste the
   text from the Kit's editor.
3. Start the app (`Apps` -> `Almanac47`). `main.py` asks in the terminal, like the `nav.py`
   menu: Year, Month, Day, UT (hh:mm or hh:mm:ss), Lat, Lon.
   Lat/Lon: `25 20` = 25 deg 20', `25.5` = decimal degrees, `-` for S / W.
   UT: `14:57`, `14 57` or the C47 way `14.57` (hh.mm, `14.5730` with seconds).
   A typing slip shows `?` and asks again.
   From the app's shell: `import skyview` starts on the horizon chart, `hplib.run(0)` /
   `hplib.run(1)` start again.

## Keys

| Key | GETKEY code | Action |
|---|---|---|
| UP / DOWN | 2 / 12 | one hour later / earlier |
| ENTER | 30 | switch ALMANAC <-> HORIZON |
| LEFT / RIGHT | 7 / 8 | HORIZON: previous / next body for the top line (shown in red) |
| ESC | 4 | exit (ON also stops a Python program) |

## Size and memory

| File | Bytes |
|---|---|
| nav.py | 11710 |
| navdata.py | 6697 |
| hplib.py | 3053 |
| almview.py | 2119 |
| skyview.py | 2373 |
| main.py | 281 |
| **total** | **26233** |

The Prime's MicroPython heap is far larger than the NumWorks' (it has not been measured
here); the only big object is the coefficient data of `navdata.py` (about 15 KB of heap).
The stars are computed one by one and only the 9 or 10 rows shown are kept.

## The hpprime calls used, and where they come from

There is no official HP documentation of the `hpprime` module. What the scripts use:

| Call | Used for | Source |
|---|---|---|
| `fillrect(G, x, y, w, h, edgecolor, fillcolor)`, colour `0xRRGGBB`, `G = 0` screen | background, rules, dots, symbols, inverted Hc | hp-prime-kit `docs/topics/micropython.md` (measured on a G2, fw 2.4.15515); PrimeFORTH `FORTH.py` |
| `eval('TEXTOUT_P("text",G0,x,y,font,RGB(r,g,b))')` | all text (font 1 small, 4 for the title lines) | hp-prime-kit `micropython.md` / `docs/start/05-python.md`; TEXTOUT_P syntax: HP Prime for All, Edward Shore tutorial part 6 |
| `eval('DIMGROB_P(G9,320,30)')` + TEXTOUT_P on G9 | measuring text widths (TEXTOUT_P returns the x after the text) | hp-prime-kit `interface.md` (grob to measure text) |
| `eval('GETKEY')`, `eval('WAIT(0.05)')` | keys (-1 = none), throttle | hp-prime-kit `interface.md` (key codes 0-50: Up 2, Esc 4, Left 7, Right 8, Down 12, Enter 30); udel.edu "HP Prime Programming" (`getkey` returns -1, `wait` in loops); PrimeFORTH |
| `input()` | date, UT, DR in the terminal | Neil Streeter, *Python Activities Book, HP Prime* (2025) |

The native `textout()` is not used: it has no font size or background parameter (noted in
the Py-41 project), so the text goes through PPL's `TEXTOUT_P`. There is no `time` module
on the Prime (hp-prime-kit), so the scripts wait with `WAIT`.

Links:
- https://github.com/Insoft-UK/hp-prime-kit (`docs/topics/micropython.md`, `docs/topics/interface.md`, `docs/start/05-python.md`)
- https://github.com/diemheych/PrimeFORTH (`FORTH.py`)
- https://udel.edu/~mm/hp/primePython/ and https://udel.edu/~mm/hp/primePython/upython.html
- https://literature.hpcalc.org/community/hpprime-python-activities.pdf
- https://en.hpprime.club/articles/prime-tutorial-by-edward-shore-part-6-textout/
- https://sites.google.com/site/olivier2smet2/home/py-41

## PC preview and check

`pc_shim/hpprime.py` stands in for the module: it draws G0 into a Pillow image and
understands the few PPL strings used here. The Prime fonts are imitated with DejaVu Sans
Condensed, so the preview's text widths are close to, not equal to, the calculator's
(the columns are right-aligned with the measured widths, so they adapt on the calculator).

    python3 python/hpprime/pc_shim/run.py alm "2026 9 26 14:57 25_20 55_12" docs/HPPRIME_alm.png
    python3 python/hpprime/pc_shim/run.py sky "2026 9 26 14:57 25_20 55_12" docs/HPPRIME_sky.png
    python3 python/hpprime/pc_shim/run.py sky "2026 9 23 03:00 30 0" docs/HPPRIME_sky_night.png
    python3 python/hpprime/pc_shim/check.py

Keys can follow the PNG name (`UP DOWN LEFT RIGHT ENTER ESC`); they are pressed before
the picture is taken. `check.py` rebuilds the screen lines from the TEXTOUT_P calls and
compares them with the text page of `nav.py` for the same inputs, and with the C47
ALMANAC screen `docs/ALMF_preview.png` (23 Sep 2026 23:30 UT, 10 N 075 30 W: Aries, Sun,
Arcturus, Vega, Altair, Antares, Fomalhaut, Deneb, twilight, rise/set, mer pass, SD,
Moon 92 % waxing, age 12.8): all identical.

## Limitations

- No Moon position, no planets (not in `nav.py`); Moon phase only.
- Time is UT1 (add DUT1 to UTC).
- Not tested on a real HP Prime or its virtual calculator. Checked on a PC with the
  stand-in, and in a MicroPython (WebAssembly) interpreter with a dummy `hpprime`.
  Unsure: that TEXTOUT_P's return value is the end x (if not, a fixed width is used and
  the right-aligned columns may be a few pixels off), the exact pixel size of fonts 1 and 4,
  and whether ESC reaches GETKEY in every firmware (ON always stops the program).
- An error while the views run is printed in the terminal (`ERROR: ...`) instead of
  closing the app. If it still closes without a message, see hp-prime-kit `micropython.md`
  ("mark-debugging").
- Oct 1, 2026: a user reported a crash. Fixed the likely causes: an input such as `14.57`
  for UT stopped the program (now accepted, and slips ask again); the program ran inside
  `import almview` (now `main.py` calls `hplib.run(0)`); GETKEY / TEXTOUT_P results are
  read as numbers whether they come as int, float or text.

## Licence

Copyright 2026 Victor Valdes. GPL-3.0-or-later (see `LICENSE` and `NOTICE` at the top of
the repository).

**Supports, does not replace, the Nautical Almanac.**
