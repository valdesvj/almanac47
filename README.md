# C47_nav

Celestial navigation for the SwissMicros C47 / R47 calculator (RPN), with a PC
version and the base for a phone app (**Almanac 47**).

- **Calculator programs:** `programs/` (start with `NAV`), commented versions in
  `programs_rem/` and `listings/`. See `README.txt` and `PROGRAM_MAP.txt`.
- **PC, native Python:** `python/native/c47pc.py` (GTK window, PNG, text).
- **PC, reference viewer:** `python/c47view.py` runs the real calculator programs.
- **Manual:** `docs/C47_Nav_User_Manual.pdf`.
- **Test:** `python3 tests/test_parity.py` (native Python = calculator, pixel for pixel).
- **Notes for further work:** `DEVELOPMENT_NOTES.md`.

Sun, Moon, planets and the 57 navigational stars (+ Polaris): GHA, Dec, Hc, Zn,
twilight, sunrise/sunset, meridian passage, Moon phase; almanac pages and horizon
charts drawn on the calculator screen.

**Does not replace the Nautical Almanac.**
