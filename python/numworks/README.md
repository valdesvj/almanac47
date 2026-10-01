# Almanac 47 on the NumWorks

User manual: `docs/Almanac47_NumWorks_Manual.pdf`.

Two graphic views of the C47 suite for the NumWorks calculator (Epsilon MicroPython),
drawn with the calculator's own `kandinsky` module, keys read with `ion`:

| Script | View | C47 original |
|---|---|---|
| `almview.py` | ALMANAC page: the header line (date, UT, DR) with a line under it, GHA Aries, BODY GHA DEC HC ZN for the Sun and the brightest navigation stars higher than 10 deg, naut. twilight, rise/set, mer. pass, Sun SD, Moon phase with its glyph and age | ALMF ("vintage" view) |
| `skyview.py` | HORIZON chart: the same header line, Hc up (sine scale), Zn across, celestial equator dotted, Sun and stars with their numbers; the selected body has its name next to it (red); DAY / TWILIGHT / NIGHT at the bottom | HORZ |

All the numbers come from `../nav.py` + `../navdata.py` (same methods as the C47
programs SUNA, STAR, SUNRISE, PHAS, HCZ; `nav.almanac()` / `nav.bodies()`), the same
files as the text menu (`nav.py`, option 5 prints the same page as text). There is no Moon
position and no planets in `nav.py`, so both views show the Sun plus the same 7 stars
(`nav.NBODY` = 8 bodies, as the C47 views of Oct 2026), chosen like the C47: brightest
first, only those higher than 10 deg.

Previews made on a PC (see below): `docs/NUMWORKS_alm.png`, `docs/NUMWORKS_sky.png`
(26 Sep 2026 14:57 UT, 25 20 N 055 12 E) and `docs/NUMWORKS_sky_night.png`
(23 Sep 2026 03:00 UT, 30 N 0 E).

## Copy to the calculator

Five scripts go on the calculator, all at the top level of the script list:

    nav.py  navdata.py   (from python/)
    nwlib.py  almview.py  skyview.py   (from python/numworks/)

- **Epsilon (official):** on https://my.numworks.com create each script (Python ->
  new script, paste the file, keep the same name), then "Send to my calculator" with the
  calculator plugged in by USB (Chrome/Edge, WebUSB). The NumWorks online simulator on the
  same site runs them too.
- **Upsilon / Omega:** same files; send them with the Upsilon / Omega web installer's
  script manager, or with the workshop as above.

Run: open `almview.py` (or `skyview.py`) in the Python app and choose *Execute script*.
It asks, like the `nav.py` menu: Year, Month, Day, UT (hh:mm or hh:mm:ss), Lat, Lon.
Lat/Lon: `25 20` = 25 deg 20', `25.5` = decimal degrees, `-` for S / W.

## Keys

| Key | Action |
|---|---|
| UP / DOWN | one hour later / earlier |
| OK or EXE | switch ALMANAC <-> HORIZON |
| LEFT / RIGHT | HORIZON: the previous / next body above the horizon: its name next to it, in red |
| BACK | exit |

## Memory and size

| File | Bytes |
|---|---|
| nav.py | 11710 |
| navdata.py | 6697 |
| nwlib.py | 3467 |
| almview.py | 1838 |
| skyview.py | 2365 |
| **total** | **26077** |

Assumed limits (checked on the web, Sep 2026): the Python heap is 32 KB on Epsilon 13.2 up
to 18 (Omega issue #357) and 64 KB from Epsilon 19 (TI-Planet news "NumWorks v19: 64K heap
Python"); Omega/Upsilon have about 100 KB. The script store is shared by all scripts (about
32 KB on the N0100 / older Epsilon, more on newer models), so the five files are kept
under 27 KB, each far below 16 KB, with no big lists: the stars are computed one by one
and only the 9 or 10 rows shown are kept. Compiled size (mpy-cross, as an estimate of the
RAM for code): nav 7.2 KB, navdata 8.1 KB, the three view files 3.7 KB together; the
coefficient tuples of `navdata.py` take the largest part of the heap (about 15 KB at run
time). On a 32 KB heap (Epsilon before 19) this is close to the limit: if you get
`MemoryError`, update Epsilon (19 or later) or use Upsilon, and delete other scripts
that are imported in the same session.

The text is the 5x7 font of the C47 programs (PTXB), drawn with `fill_rect`, and the
Moon phase is one of eight 7x7 glyphs (`nwlib.MP`, the C47 phase glyphs at 7 rows). The view takes
about a second to draw on the calculator (not timed on a real one).

## PC preview and check

`pc_shim/` has stand-ins for `kandinsky` (draws into a Pillow image; the large font is
imitated with DejaVu Sans Mono) and `ion` (keys from a script), so the same files run on a PC:

    python3 python/numworks/pc_shim/run.py alm "2026 9 26 14:57 25_20 55_12" docs/NUMWORKS_alm.png
    python3 python/numworks/pc_shim/run.py sky "2026 9 26 14:57 25_20 55_12" docs/NUMWORKS_sky.png
    python3 python/numworks/pc_shim/run.py sky "2026 9 23 03:00 30 0" docs/NUMWORKS_sky_night.png
    python3 python/numworks/pc_shim/check.py

`check.py` compares every value on the screen with the text page of `nav.py` for the same
inputs, and with the C47 ALMANAC screen `docs/ALMF_preview.png` (23 Sep 2026 23:30 UT,
10 N 075 30 W: Aries, Sun, Arcturus, Vega, Altair, Antares, Fomalhaut, Deneb, twilight,
rise/set, mer pass, SD, Moon 92 % waxing, age 12.8): all identical.

## Limitations

- No Moon position, no planets (not in `nav.py`); Moon phase only.
- Time is UT1 (add DUT1 to UTC); the Sun's rise/set use the full Sun series, as `nav.py`.
- Not tested on a real NumWorks (written for the documented API: `fill_rect`,
  `draw_string(text, x, y, color, background)`, `color`, `ion.keydown`, `time.sleep`),
  and checked in a MicroPython (WebAssembly) interpreter with dummy drawing modules.
- BACK may stop the script with KeyboardInterrupt instead of the loop seeing the key; both
  end the program.

## Licence

Copyright 2026 Victor Valdes. GPL-3.0-or-later (see `LICENSE` and `NOTICE` at the top of
the repository).

**Supports, does not replace, the Nautical Almanac.**
