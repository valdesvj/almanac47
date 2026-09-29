# C47_nav

Celestial navigation for the SwissMicros C47 / R47 calculator (RPN), with a PC
version and the base for a phone app (**Almanac 47**).

- **Install and run:** `QUICKSTART.txt` (load NAVFULL + NAVINIT, XEQ "INIT", delete the
  INIT program, XEQ "NAV"). NAV asks date, UT and DR once, computes the sky, then a
  graphic menu of 9 views (keys 1-9, + back, arrows one hour).
- **Text on the graphics screen:** `programs/FONTS.txt` - PTXT (3x5), PTXB (5x7) and
  PTXS (the C47 status-bar font), with number printers; usable on their own.
- **Calculator programs:** `programs/` (start with `NAV`), commented versions in
  `programs_rem/` and `listings/`. See `README.txt` and `PROGRAM_MAP.txt`.
- **PC, native Python:** `python/native/c47pc.py` (GTK window, PNG, text).
- **PC, reference viewer:** `python/c47view.py` runs the real calculator programs.
- **Other calculators:** `build/dm42/` (C47 on the old DM42, Sun and stars), `build/free42/`
  (the full NAV for the DM42 / DM42n stock Free42 firmware), `python/numworks/`,
  `python/hpprime/`. How the C47 and Free42 update the screen: `README.txt`, SCREEN UPDATE.
- **Manuals of the other calculators:** `docs/Almanac47_Free42_Manual.pdf`,
  `docs/Almanac47_NumWorks_Manual.pdf`, `docs/Almanac47_HPPrime_Manual.pdf`.
- **Manual:** `docs/C47_Nav_User_Manual.pdf` (part 1: NAV and the views, the map of the
  N01, N02 ... labels; part 2: each program with worked results).
- **C47 command reference:** `docs/reference/C47_Full_index.txt` (C47 team, GFDL).
- **Test:** `python3 tests/test_parity.py` (native Python = calculator, pixel for pixel).
- **Notes for further work:** `DEVELOPMENT_NOTES.md`.

Sun, Moon, planets and the 57 navigational stars (+ Polaris): GHA, Dec, Hc, Zn,
twilight, sunrise/sunset, meridian passage, Moon phase; almanac pages and horizon
charts drawn on the calculator screen.

## Author

By Victor Valdes (valdes.vj@gmail.com),

Thank you To the C43/C47 firmware developers and SwissMicros, and to @tangent for rejig, which made converting the .txt programs to .p47 easy. With the C47, the sky is the limit - literally. Written with the help of AI - Claude (Anthropic), Gemini (Google) and Grok (xAI) - brainstorming with them used up most of my daily and weekly credits. I used AI responsibly, as a cooperation: the AI helps, but I checked the results, and the work - and any mistakes in it - are mine.

## Licence

GNU General Public License v3.0 or later (`LICENSE`), for the whole project. Exceptions:
`docs/reference/C47_Full_index.txt` (C47 team, GFDL) and the PTXS glyph bitmaps from the C47
firmware (GPL-3.0, `programs/LICENSE-PTXS.txt`). See `NOTICE`.

**Does not replace the Nautical Almanac.**
