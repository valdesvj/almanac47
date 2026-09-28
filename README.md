# C47_nav

Celestial navigation for the SwissMicros C47 / R47 calculator (RPN), with a PC
version and the base for a phone app (**Almanac 47**).

- **Install and run:** `QUICKSTART.txt` (load NAVFULL + NAVINIT, XEQ "INIT", delete the
  INIT programs, XEQ "NAV").
- **Text on the graphics screen:** `programs/FONTS.txt` - PTXT (3x5), PTXB (5x7) and
  PTXS (the C47 status-bar font), with number printers; usable on their own.
- **Calculator programs:** `programs/` (start with `NAV`), commented versions in
  `programs_rem/` and `listings/`. See `README.txt` and `PROGRAM_MAP.txt`.
- **PC, native Python:** `python/native/c47pc.py` (GTK window, PNG, text).
- **PC, reference viewer:** `python/c47view.py` runs the real calculator programs.
- **Manual:** `docs/C47_Nav_User_Manual.pdf`.
- **C47 command reference:** `docs/reference/C47_Full_index.txt` (C47 team, GFDL).
- **Test:** `python3 tests/test_parity.py` (native Python = calculator, pixel for pixel).
- **Notes for further work:** `DEVELOPMENT_NOTES.md`.

Sun, Moon, planets and the 57 navigational stars (+ Polaris): GHA, Dec, Hc, Zn,
twilight, sunrise/sunset, meridian passage, Moon phase; almanac pages and horizon
charts drawn on the calculator screen.

## Licence

The calculator programs (`programs/`, `programs_rem/`, `listings/`, `rtf/`) are
MIT-licensed, see the `LICENSE` file in each folder, except PTXS (and the combined
`build/NAVFULL*.txt`), which is GPL-3.0 because its glyphs come from the C47 firmware's
font (`programs/LICENSE-PTXS.txt`). Everything else is
Copyright (c) 2026 Victorio Valdes, all rights reserved. See `NOTICE`.

**Does not replace the Nautical Almanac.**
